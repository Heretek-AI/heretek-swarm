"""
Observability API - LLM Tracing and Agent Monitoring

Provides endpoints for:
- LLM call traces
- Tool call traces
- Agent message traces
- Real-time streaming via WebSocket
"""

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect
import structlog

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/api/observability", tags=["observability"])


# In-memory trace storage (in production, use database)
_traces: Dict[str, List[Dict]] = {}


class TraceEvent:
    """A trace event for observability."""

    def __init__(
        self,
        event_type: str,
        agent_id: str,
        data: Dict[str, Any],
        timestamp: Optional[datetime] = None,
        duration: Optional[float] = None,
    ):
        self.id = f"{event_type}-{agent_id}-{datetime.utcnow().timestamp()}"
        self.event_type = event_type  # 'llm_call', 'tool_call', 'agent_message'
        self.agent_id = agent_id
        self.data = data
        self.timestamp = timestamp or datetime.utcnow()
        self.duration = duration

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "type": self.event_type,
            "agent_id": self.agent_id,
            "timestamp": self.timestamp.isoformat(),
            "duration": self.duration,
            "data": self.data,
        }


class ConnectionManager:
    """Manage WebSocket connections for real-time trace streaming."""

    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket, agent_id: str):
        """Handle new WebSocket connection."""
        self.active_connections[agent_id] = websocket
        logger.info("websocket_connected", agent_id=agent_id)

    async def disconnect(self, websocket: WebSocket, agent_id: str):
        """Handle WebSocket disconnection."""
        if agent_id in self.active_connections:
            del self.active_connections[agent_id]
            logger.info("websocket_disconnected", agent_id=agent_id)

    async def broadcast_trace(self, trace: TraceEvent, agent_id: str):
        """Broadcast trace to all connections for an agent."""
        if agent_id in self.active_connections:
            websocket = self.active_connections[agent_id]
            try:
                await websocket.send_json(trace.to_dict())
            except Exception as e:
                logger.error("websocket_send_failed", agent_id=agent_id, error=str(e))


connection_manager = ConnectionManager()


@router.get("/traces")
async def get_traces(
    agent_id: Optional[str] = None,
    event_type: Optional[str] = None,
    start_time: Optional[str] = None,
    end_time: Optional[str] = None,
    limit: int = Query(default=100, ge=1, le=1000),
) -> Dict[str, Any]:
    """
    Get trace events with optional filtering.

    Args:
        agent_id: Filter by agent ID
        event_type: Filter by event type ('llm_call', 'tool_call', 'agent_message')
        start_time: Filter by start time (ISO format)
        end_time: Filter by end time (ISO format)
        limit: Maximum number of events to return

    Returns:
        Dict with traces and metadata
    """
    # Filter traces
    filtered_traces = []

    for trace_id, traces in _traces.items():
        for trace in traces:
            # Apply filters
            if agent_id and trace.agent_id != agent_id:
                continue

            if event_type and trace.event_type != event_type:
                continue

            if start_time:
                trace_time = datetime.fromisoformat(trace.timestamp)
                start_dt = datetime.fromisoformat(start_time)
                if trace_time < start_dt:
                    continue

            if end_time:
                trace_time = datetime.fromisoformat(trace.timestamp)
                end_dt = datetime.fromisoformat(end_time)
                if trace_time > end_dt:
                    continue

            filtered_traces.append(trace)

            # Apply limit
            if len(filtered_traces) >= limit:
                break

    return {
        "events": [trace.to_dict() for trace in filtered_traces],
        "total": len(filtered_traces),
        "filtered": len(_traces.get(agent_id, [])) - len(filtered_traces),
    }


@router.get("/traces/{trace_id}")
async def get_trace(trace_id: str) -> Dict[str, Any]:
    """
    Get a specific trace by ID.

    Args:
        trace_id: Trace event ID

    Returns:
        Dict with trace details
    """
    # Search for trace across all agents
    for agent_traces in _traces.values():
        for trace in agent_traces:
            if trace.id == trace_id:
                return trace.to_dict()

    return {"error": "Trace not found"}


@router.post("/traces")
async def create_trace(
    event_type: str,
    agent_id: str,
    data: Dict[str, Any],
    duration: Optional[float] = None,
) -> Dict[str, Any]:
    """
    Create a new trace event.

    Args:
        event_type: Type of event ('llm_call', 'tool_call', 'agent_message')
        agent_id: Agent ID
        data: Event data
        duration: Duration in milliseconds

    Returns:
        Dict with created trace
    """
    trace = TraceEvent(
        event_type=event_type,
        agent_id=agent_id,
        data=data,
        duration=duration,
    )

    # Store in memory (in production, use database)
    if agent_id not in _traces:
        _traces[agent_id] = []

    _traces[agent_id].append(trace)

    # Broadcast to WebSocket connections
    await connection_manager.broadcast_trace(trace, agent_id)

    logger.info(
        "trace_created",
        trace_id=trace.id,
        event_type=event_type,
        agent_id=agent_id,
    )

    return trace.to_dict()


@router.websocket("/ws/traces/{agent_id}")
async def websocket_traces(websocket: WebSocket, agent_id: str):
    """
    WebSocket endpoint for real-time trace streaming.

    Args:
        websocket: WebSocket connection
        agent_id: Agent ID to stream traces for
    """
    await connection_manager.connect(websocket, agent_id)

    try:
        # Send recent traces on connect
        if agent_id in _traces:
            recent_traces = _traces[agent_id][-100:]  # Last 100 traces
            for trace in recent_traces:
                await websocket.send_json(trace.to_dict())

        # Stream new traces as they arrive
        while True:
            try:
                message = await websocket.receive_json()
                # Echo back for demo (in production, don't echo)
                # await websocket.send_json(message)
            except WebSocketDisconnect:
                logger.info("websocket_disconnected", agent_id=agent_id)
                break
            except Exception as e:
                logger.error("websocket_error", agent_id=agent_id, error=str(e))
                await websocket.close()

    finally:
        await connection_manager.disconnect(websocket, agent_id)


@router.get("/metrics")
async def get_metrics() -> Dict[str, Any]:
    """
    Get observability metrics.

    Returns:
        Dict with trace statistics
    """
    total_events = 0
    events_by_type: Dict[str, int] = {}
    events_by_agent: Dict[str, int] = {}

    for agent_traces in _traces.values():
        for trace in agent_traces:
            total_events += 1
            events_by_type[trace.event_type] = events_by_type.get(trace.event_type, 0) + 1
            events_by_agent[trace.agent_id] = events_by_agent.get(trace.agent_id, 0) + 1

    # Calculate metrics
    avg_duration = 0
    if total_events > 0:
        total_duration = sum(trace.duration or 0 for traces in _traces.values() for trace in traces)
        avg_duration = total_duration / total_events

    return {
        "total_events": total_events,
        "events_by_type": events_by_type,
        "events_by_agent": events_by_agent,
        "average_duration_ms": round(avg_duration, 2),
        "active_connections": len(connection_manager.active_connections),
        "timestamp": datetime.utcnow().isoformat(),
    }


@router.delete("/traces/{agent_id}")
async def clear_traces(agent_id: str) -> Dict[str, Any]:
    """
    Clear all traces for an agent.

    Args:
        agent_id: Agent ID to clear traces for

    Returns:
        Dict with deletion confirmation
    """
    if agent_id in _traces:
        count = len(_traces[agent_id])
        del _traces[agent_id]
        logger.info("traces_cleared", agent_id=agent_id, count=count)
    else:
        count = 0

    return {
        "agent_id": agent_id,
        "cleared": count,
        "message": f"Cleared {count} traces for agent {agent_id}",
    }
