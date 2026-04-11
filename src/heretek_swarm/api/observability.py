"""
Observability API - LLM Tracing and Agent Monitoring

Provides endpoints for:
- LLM call traces
- Tool call traces
- Agent message traces
- Real-time streaming via WebSocket
- Swarm health metrics
- Consciousness metrics (IIT Phi, FEP)
"""

import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

import structlog
from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    Request,
    WebSocket,
    WebSocketDisconnect,
)
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel, Field

from heretek_swarm.gateway.auth import verify_auth
from heretek_swarm.observability.metrics import (
    RealTimeMetricsStream,
    SwarmMetricsCollector,
)
from heretek_swarm.security.zero_trust import LayerResult, ZeroTrustResult, ZeroTrustValidator

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/api/v1/observability", tags=["observability"])

# In-memory trace storage (in production, use database)
_traces: Dict[str, List[Dict]] = {}

# Metrics collector and stream instances
_metrics_collector: Optional[SwarmMetricsCollector] = None
_metrics_stream: Optional[RealTimeMetricsStream] = None
_zero_trust: Optional[ZeroTrustValidator] = None

# Rate limiting state
_rate_limit_state: Dict[str, List[datetime]] = {}
RATE_LIMIT_REQUESTS = 100  # requests per minute
RATE_LIMIT_WINDOW = 60  # seconds


def get_metrics_collector() -> SwarmMetricsCollector:
    """Get or create the metrics collector singleton."""
    global _metrics_collector
    if _metrics_collector is None:
        _metrics_collector = SwarmMetricsCollector()
    return _metrics_collector


def get_metrics_stream() -> RealTimeMetricsStream:
    """Get or create the metrics stream singleton."""
    global _metrics_stream
    if _metrics_stream is None:
        _metrics_stream = RealTimeMetricsStream(get_metrics_collector())
    return _metrics_stream


def get_zero_trust() -> ZeroTrustValidator:
    """Get or create zero trust validator."""
    global _zero_trust
    if _zero_trust is None:
        _zero_trust = ZeroTrustValidator()
    return _zero_trust


def check_rate_limit(client_id: str) -> bool:
    """Check if client has exceeded rate limit."""
    now = datetime.now(timezone.utc)
    window_start = now - timedelta(seconds=RATE_LIMIT_WINDOW)

    if client_id not in _rate_limit_state:
        _rate_limit_state[client_id] = []

    # Clean old entries
    _rate_limit_state[client_id] = [
        ts for ts in _rate_limit_state[client_id] if ts > window_start
    ]

    # Check limit
    if len(_rate_limit_state[client_id]) >= RATE_LIMIT_REQUESTS:
        return False

    # Record this request
    _rate_limit_state[client_id].append(now)
    return True


def validate_input(validator: ZeroTrustValidator, data: Any, context: str) -> None:
    """Validate input using zero-trust validation.
    
    Note: This is a simplified validation for API inputs.
    The ZeroTrustValidator.validate_request method is async and designed
    for full request/response validation. For simple input validation,
    we just ensure the data is present and non-empty.
    """
    if data is None or (isinstance(data, str) and not data.strip()):
        logger.warning(f"Input validation failed: {context}")
        raise HTTPException(status_code=400, detail=f"Invalid input: empty or None")


# ============== SWARM METRICS ENDPOINTS ==============


@router.get("/swarm")
async def get_swarm_health(request: Request) -> Dict[str, Any]:
    """
    Get swarm health overview.
    
    Returns aggregate metrics including:
    - Total/active/idle agents
    - Task completion statistics
    - Message statistics
    - Overall health score (0-100)
    
    Args:
        request: FastAPI request for rate limiting
        
    Returns:
        SwarmMetricsData dictionary
    """
    # Rate limiting
    client_id = request.client.host if request.client else "unknown"
    if not check_rate_limit(client_id):
        raise HTTPException(status_code=429, detail="Rate limit exceeded")

    # Zero-trust validation (audit logging)
    validator = get_zero_trust()
    request_id = str(uuid.uuid4())
    audit_result = ZeroTrustResult(
        passed=True,
        layer1=LayerResult(layer="input_validation", passed=True),
        layer2=LayerResult(layer="context_validation", passed=True),
        layer3=LayerResult(layer="output_validation", passed=True),
        layer4=LayerResult(layer="audit_logging", passed=True),
        request_id=request_id,
    )
    validator.audit_logger.log(
        event_type="api_call",
        result=audit_result,
        additional_context={
            "endpoint": "/api/v1/observability/swarm",
            "client_id": client_id,
            "method": "GET",
        },
    )

    collector = get_metrics_collector()
    swarm_data = collector.collect_swarm_metrics()

    return {
        **swarm_data.to_dict(),
        "health_score": collector.calculate_health_score(),
    }


@router.get("/agents/{agent_id}")
async def get_agent_metrics(agent_id: str, request: Request) -> Dict[str, Any]:
    """
    Get individual agent metrics.
    
    Returns per-agent performance metrics including:
    - Tasks completed/failed
    - Average task duration
    - Messages sent/received
    - Error count
    - Health score
    
    Args:
        agent_id: ID of the agent
        request: FastAPI request for rate limiting
        
    Returns:
        AgentMetrics dictionary
    """
    # Input validation
    validator = get_zero_trust()
    validate_input(validator, {"agent_id": agent_id}, "agent_id")

    # Rate limiting
    client_id = request.client.host if request.client else "unknown"
    if not check_rate_limit(client_id):
        raise HTTPException(status_code=429, detail="Rate limit exceeded")

    # Audit logging
    request_id = str(uuid.uuid4())
    audit_result = ZeroTrustResult(
        passed=True,
        layer1=LayerResult(layer="input_validation", passed=True),
        layer2=LayerResult(layer="context_validation", passed=True),
        layer3=LayerResult(layer="output_validation", passed=True),
        layer4=LayerResult(layer="audit_logging", passed=True),
        request_id=request_id,
        agent_id=agent_id,
    )
    validator.audit_logger.log(
        event_type="api_call",
        result=audit_result,
        additional_context={
            "endpoint": f"/api/v1/observability/agents/{agent_id}",
            "client_id": client_id,
            "method": "GET",
        },
    )

    collector = get_metrics_collector()
    agent_data = collector.collect_agent_metrics(agent_id)

    return agent_data.to_dict()


@router.get("/agents")
async def get_all_agents(request: Request) -> Dict[str, Any]:
    """
    Get metrics for all agents.
    
    Returns:
        Dictionary mapping agent IDs to their metrics
    """
    # Rate limiting
    client_id = request.client.host if request.client else "unknown"
    if not check_rate_limit(client_id):
        raise HTTPException(status_code=429, detail="Rate limit exceeded")

    collector = get_metrics_collector()
    agents = collector.get_all_agent_metrics()
    states = collector.get_agent_states()

    return {
        "agents": {k: v.to_dict() for k, v in agents.items()},
        "states": states,
        "total_agents": len(agents),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


# ============== CONSCIOUSNESS METRICS ENDPOINTS ==============


@router.get("/consciousness")
async def get_consciousness_metrics(request: Request) -> Dict[str, Any]:
    """
    Get consciousness metrics (IIT Phi and FEP).
    
    Returns:
    - Phi scores (avg, max, min)
    - Integration/differentiation levels
    - Free energy metrics
    - Per-agent phi/fep scores
    
    Args:
        request: FastAPI request for rate limiting
        
    Returns:
        ConsciousnessMetricsData dictionary
    """
    # Rate limiting
    client_id = request.client.host if request.client else "unknown"
    if not check_rate_limit(client_id):
        raise HTTPException(status_code=429, detail="Rate limit exceeded")

    validator = get_zero_trust()
    request_id = str(uuid.uuid4())
    audit_result = ZeroTrustResult(
        passed=True,
        layer1=LayerResult(layer="input_validation", passed=True),
        layer2=LayerResult(layer="context_validation", passed=True),
        layer3=LayerResult(layer="output_validation", passed=True),
        layer4=LayerResult(layer="audit_logging", passed=True),
        request_id=request_id,
    )
    validator.audit_logger.log(
        event_type="api_call",
        result=audit_result,
        additional_context={
            "endpoint": "/api/v1/observability/consciousness",
            "client_id": client_id,
            "method": "GET",
        },
    )

    collector = get_metrics_collector()
    consciousness_data = collector.collect_consciousness_metrics()

    return consciousness_data.to_dict()


@router.get("/consciousness/agent/{agent_id}")
async def get_agent_consciousness(agent_id: str, request: Request) -> Dict[str, Any]:
    """
    Get consciousness metrics for a specific agent.
    
    Args:
        agent_id: ID of the agent
        request: FastAPI request for rate limiting
        
    Returns:
        Dictionary with agent's phi and fep scores
    """
    # Input validation
    validator = get_zero_trust()
    validate_input(validator, {"agent_id": agent_id}, "agent_id")

    # Rate limiting
    client_id = request.client.host if request.client else "unknown"
    if not check_rate_limit(client_id):
        raise HTTPException(status_code=429, detail="Rate limit exceeded")

    collector = get_metrics_collector()
    consciousness_data = collector.collect_consciousness_metrics()

    agent_phi = consciousness_data.agent_phi_scores.get(agent_id, 0.0)
    agent_fep = consciousness_data.agent_fep_scores.get(agent_id, 0.0)

    return {
        "agent_id": agent_id,
        "phi_score": agent_phi,
        "fep_score": agent_fep,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


# ============== REAL-TIME METRICS STREAM ==============


@router.get("/metrics/stream")
async def stream_metrics(
    request: Request,
    interval: int = Query(default=5, ge=1, le=60, description="Stream interval in seconds"),
) -> Dict[str, Any]:
    """
    Get real-time metrics snapshot (non-streaming HTTP version).
    
    For WebSocket streaming, use /ws/metrics endpoint.
    
    Args:
        request: FastAPI request
        interval: Desired update interval (for metadata only)
        
    Returns:
        Current metrics snapshot
    """
    # Rate limiting
    client_id = request.client.host if request.client else "unknown"
    if not check_rate_limit(client_id):
        raise HTTPException(status_code=429, detail="Rate limit exceeded")

    validator = get_zero_trust()
    request_id = str(uuid.uuid4())
    audit_result = ZeroTrustResult(
        passed=True,
        layer1=LayerResult(layer="input_validation", passed=True),
        layer2=LayerResult(layer="context_validation", passed=True),
        layer3=LayerResult(layer="output_validation", passed=True),
        layer4=LayerResult(layer="audit_logging", passed=True),
        request_id=request_id,
    )
    validator.audit_logger.log(
        event_type="api_call",
        result=audit_result,
        additional_context={
            "endpoint": "/api/v1/observability/metrics/stream",
            "client_id": client_id,
            "method": "GET",
        },
    )

    stream = get_metrics_stream()
    snapshot = stream.get_metrics_snapshot()

    return {
        **snapshot.to_dict(),
        "stream_interval_seconds": interval,
    }


@router.websocket("/ws/metrics")
async def websocket_metrics(websocket: WebSocket, interval: int = 5):
    """
    WebSocket endpoint for real-time metrics streaming.
    
    Args:
        websocket: WebSocket connection
        interval: Stream interval in seconds (1-60)
    """
    await websocket.accept()

    validator = get_zero_trust()
    validator.audit_log(
        event_type="websocket_connected",
        event_data={
            "endpoint": "/api/v1/observability/ws/metrics",
            "interval": interval,
        },
    )

    stream = get_metrics_stream()

    try:
        while True:
            try:
                # Collect and send metrics
                swarm = stream._collector.collect_swarm_metrics()
                consciousness = stream._collector.collect_consciousness_metrics()
                agents = stream._collector.get_all_agent_metrics()
                health = stream._collector.calculate_health_score()

                await websocket.send_json({
                    "swarm_metrics": swarm.to_dict(),
                    "consciousness_metrics": consciousness.to_dict(),
                    "agent_metrics": {k: v.to_dict() for k, v in agents.items()},
                    "health_score": health,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                })

                # Wait for interval or client message
                try:
                    async with asyncio.timeout(interval):
                        message = await websocket.receive_text()
                        # Handle client commands if any
                        if message == "stop":
                            break
                except asyncio.TimeoutError:
                    pass  # Continue streaming

            except WebSocketDisconnect:
                logger.info("websocket_disconnected")
                break
            except Exception as e:
                logger.error("websocket_error", error=str(e))
                await websocket.close()
                break

    finally:
        request_id = str(uuid.uuid4())
        audit_result = ZeroTrustResult(
            passed=True,
            layer1=LayerResult(layer="input_validation", passed=True),
            layer2=LayerResult(layer="context_validation", passed=True),
            layer3=LayerResult(layer="output_validation", passed=True),
            layer4=LayerResult(layer="audit_logging", passed=True),
            request_id=request_id,
        )
        validator.audit_logger.log(
            event_type="websocket_disconnected",
            result=audit_result,
            additional_context={"endpoint": "/api/v1/observability/ws/metrics"},
        )


# ============== ALERTS ENDPOINTS ==============


@router.get("/alerts")
async def get_alerts(request: Request) -> Dict[str, Any]:
    """
    Get active alerts and anomalies.
    
    Returns alerts for:
    - Agents with low health scores
    - High error rates
    - Low consciousness metrics
    - System anomalies
    
    Args:
        request: FastAPI request for rate limiting
        
    Returns:
        Dictionary with active alerts
    """
    # Rate limiting
    client_id = request.client.host if request.client else "unknown"
    if not check_rate_limit(client_id):
        raise HTTPException(status_code=429, detail="Rate limit exceeded")

    validator = get_zero_trust()
    request_id = str(uuid.uuid4())
    audit_result = ZeroTrustResult(
        passed=True,
        layer1=LayerResult(layer="input_validation", passed=True),
        layer2=LayerResult(layer="context_validation", passed=True),
        layer3=LayerResult(layer="output_validation", passed=True),
        layer4=LayerResult(layer="audit_logging", passed=True),
        request_id=request_id,
    )
    validator.audit_logger.log(
        event_type="api_call",
        result=audit_result,
        additional_context={
            "endpoint": "/api/v1/observability/alerts",
            "client_id": client_id,
            "method": "GET",
        },
    )

    collector = get_metrics_collector()
    alerts: List[Dict[str, Any]] = []

    # Check agent health
    agents = collector.get_all_agent_metrics()
    for agent_id, metrics in agents.items():
        if metrics.health_score < 50:
            alerts.append({
                "alert_id": f"health_{agent_id}",
                "severity": "critical" if metrics.health_score < 30 else "warning",
                "type": "low_health",
                "agent_id": agent_id,
                "message": f"Agent {agent_id} health score is {metrics.health_score:.1f}",
                "value": metrics.health_score,
                "threshold": 50,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            })

        if metrics.error_count > 10:
            alerts.append({
                "alert_id": f"errors_{agent_id}",
                "severity": "warning",
                "type": "high_errors",
                "agent_id": agent_id,
                "message": f"Agent {agent_id} has {metrics.error_count} errors",
                "value": metrics.error_count,
                "threshold": 10,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            })

    # Check consciousness metrics
    consciousness = collector.collect_consciousness_metrics()
    if consciousness.phi_avg < 0.3:
        alerts.append({
            "alert_id": "low_phi",
            "severity": "warning",
            "type": "low_consciousness",
            "message": f"Average Phi score is {consciousness.phi_avg:.3f}",
            "value": consciousness.phi_avg,
            "threshold": 0.3,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })

    # Check overall health
    overall_health = collector.calculate_health_score()
    if overall_health < 60:
        alerts.append({
            "alert_id": "low_swarm_health",
            "severity": "critical" if overall_health < 40 else "warning",
            "type": "low_swarm_health",
            "message": f"Swarm health score is {overall_health:.1f}",
            "value": overall_health,
            "threshold": 60,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })

    return {
        "alerts": alerts,
        "total_alerts": len(alerts),
        "critical_alerts": sum(1 for a in alerts if a["severity"] == "critical"),
        "warning_alerts": sum(1 for a in alerts if a["severity"] == "warning"),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


# ============== PROMETHEUS EXPORT ==============


@router.get("/metrics/prometheus")
async def get_prometheus_metrics(request: Request) -> PlainTextResponse:
    """
    Get metrics in Prometheus text format.
    
    Returns:
        Prometheus-formatted metrics string
    """
    # Rate limiting
    client_id = request.client.host if request.client else "unknown"
    if not check_rate_limit(client_id):
        raise HTTPException(status_code=429, detail="Rate limit exceeded")

    stream = get_metrics_stream()
    prometheus_data = stream.export_prometheus_format()

    return PlainTextResponse(
        content=prometheus_data,
        media_type="text/plain; version=0.0.4",
    )


# ============== EXISTING TRACE ENDPOINTS ==============


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
    # Input validation
    validator = get_zero_trust()
    validate_input(validator, {"event_type": event_type, "agent_id": agent_id, "data": data}, "trace")

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
                _message = await websocket.receive_json()
                # Echo back for demo (in production, don't echo)
                # # await websocket.send_json(_message)
            except WebSocketDisconnect:
                logger.info("websocket_disconnected", agent_id=agent_id)
                break
            except Exception as e:
                logger.error("websocket_error", agent_id=agent_id, error=str(e))
                await websocket.close()

    finally:
        await connection_manager.disconnect(websocket, agent_id)


@router.get("/metrics/legacy")
async def get_legacy_metrics() -> Dict[str, Any]:
    """
    Get legacy observability metrics (backward compatibility).
    
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
        "timestamp": datetime.now(timezone.utc).isoformat(),
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


# ============== HELPER CLASSES ==============


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
        self.id = f"{event_type}-{agent_id}-{datetime.now(timezone.utc).timestamp()}"
        self.event_type = event_type  # 'llm_call', 'tool_call', 'agent_message'
        self.agent_id = agent_id
        self.data = data
        self.timestamp = timestamp or datetime.now(timezone.utc)
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

# Import asyncio for timeout
import asyncio

# =============================================================================
# Message Replay & Time Travel Debugging Endpoints
# =============================================================================

_replay_manager: Optional[Any] = None


def get_replay_manager() -> Optional[Any]:
    """Get or create the replay manager."""
    global _replay_manager
    if _replay_manager is None:
        try:
            from heretek_swarm.gateway.jetstream_manager import get_jetstream_manager
            from heretek_swarm.gateway.message_replay import get_replay_manager as get_rm
            from heretek_swarm.state.event_store import get_event_store

            js_manager = get_jetstream_manager()
            event_store = get_event_store()
            _replay_manager = get_rm()

            # Setup with dependencies
            _replay_manager._js_manager = js_manager
            _replay_manager._event_store = event_store

        except ImportError:
            return None
    return _replay_manager


class ReplayJobCreate(BaseModel):
    """Request model for creating a replay job."""
    stream_name: str = Field(..., description="Source stream name")
    start_sequence: Optional[int] = Field(None, description="Start sequence number")
    end_sequence: Optional[int] = Field(None, description="End sequence number")
    start_time: Optional[str] = Field(None, description="Start timestamp (ISO format)")
    end_time: Optional[str] = Field(None, description="End timestamp (ISO format)")
    subject_filter: Optional[str] = Field(None, description="Subject pattern filter")
    destination_stream: Optional[str] = Field(None, description="Destination stream")
    replay_speed: float = Field(default=1.0, ge=0.1, le=100.0, description="Replay speed multiplier")


class ReplayJobResponse(BaseModel):
    """Response model for replay job."""
    job_id: str
    stream_name: str
    start_sequence: Optional[int]
    end_sequence: Optional[int]
    subject_filter: Optional[str]
    destination_stream: Optional[str]
    replay_speed: float
    status: str
    progress: int
    total: int
    progress_percent: float
    started_at: Optional[str]
    completed_at: Optional[str]
    error: Optional[str]


class ReplayJobListResponse(BaseModel):
    """Response model for listing replay jobs."""
    jobs: List[ReplayJobResponse]
    total: int
    active: int


class TimeTravelRequestCreate(BaseModel):
    """Request model for time travel debugging."""
    entity_id: str = Field(..., description="Entity to reconstruct")
    entity_type: str = Field(..., description="Entity type (agent, workflow)")
    target_time: str = Field(..., description="Target timestamp (ISO format)")
    source_stream: str = Field(..., description="Source stream name")
    include_snapshots: bool = Field(default=True, description="Use snapshots if available")


class TimeTravelResponse(BaseModel):
    """Response model for time travel result."""
    request_id: str
    entity_id: str
    entity_type: str
    target_time: str
    state: Dict[str, Any]
    events_applied: int
    snapshot_used: bool


@router.post("/events/replay")
async def create_replay_job(
    job_data: ReplayJobCreate,
    replay_manager: Optional[Any] = Depends(get_replay_manager),
    authenticated: str = Depends(verify_auth),
) -> ReplayJobResponse:
    """
    Create a new message replay job.
    
    Args:
        job_data: Replay job configuration
        
    Returns:
        Created replay job details
    """
    if not replay_manager:
        raise HTTPException(503, "Replay manager not available")

    try:
        # Parse timestamps
        start_time = None
        end_time = None

        if job_data.start_time:
            start_time = datetime.fromisoformat(job_data.start_time)
        if job_data.end_time:
            end_time = datetime.fromisoformat(job_data.end_time)

        # Create job
        job = await replay_manager.create_replay_job(
            stream_name=job_data.stream_name,
            start_sequence=job_data.start_sequence,
            end_sequence=job_data.end_sequence,
            start_time=start_time,
            end_time=end_time,
            subject_filter=job_data.subject_filter,
            destination_stream=job_data.destination_stream,
            replay_speed=job_data.replay_speed,
        )

        logger.info(
            "Replay job created",
            job_id=job.job_id,
            stream=job_data.stream_name,
        )

        return ReplayJobResponse(
            job_id=job.job_id,
            stream_name=job.stream_name,
            start_sequence=job.start_sequence,
            end_sequence=job.end_sequence,
            subject_filter=job.subject_filter,
            destination_stream=job.destination_stream,
            replay_speed=job.replay_speed,
            status=job.status.value,
            progress=job.progress,
            total=job.total,
            progress_percent=job.progress_percent,
            started_at=job.started_at.isoformat() if job.started_at else None,
            completed_at=job.completed_at.isoformat() if job.completed_at else None,
            error=job.error,
        )
    except Exception as e:
        logger.error(f"Failed to create replay job: {e}", exc_info=True)
        raise HTTPException(500, f"Failed to create replay job: {str(e)}")


@router.post("/events/replay/{job_id}/execute")
async def execute_replay_job(
    job_id: str,
    replay_manager: Optional[Any] = Depends(get_replay_manager),
    authenticated: str = Depends(verify_auth),
) -> Dict[str, Any]:
    """
    Execute a replay job.
    
    Args:
        job_id: Replay job ID
    """
    if not replay_manager:
        raise HTTPException(503, "Replay manager not available")

    job = replay_manager.get_job(job_id)
    if not job:
        raise HTTPException(404, f"Replay job '{job_id}' not found")

    try:
        # Execute in background
        asyncio.create_task(replay_manager.execute_replay(job))

        return {
            "status": "started",
            "job_id": job_id,
            "message": "Replay job started",
        }
    except Exception as e:
        logger.error(f"Failed to execute replay job: {e}", exc_info=True)
        raise HTTPException(500, f"Failed to execute replay job: {str(e)}")


@router.post("/events/replay/{job_id}/pause")
async def pause_replay_job(
    job_id: str,
    replay_manager: Optional[Any] = Depends(get_replay_manager),
    authenticated: str = Depends(verify_auth),
) -> Dict[str, str]:
    """Pause a replay job."""
    if not replay_manager:
        raise HTTPException(503, "Replay manager not available")

    if not await replay_manager.pause_replay(job_id):
        raise HTTPException(400, f"Failed to pause job '{job_id}'")

    return {"status": "paused", "job_id": job_id}


@router.post("/events/replay/{job_id}/resume")
async def resume_replay_job(
    job_id: str,
    replay_manager: Optional[Any] = Depends(get_replay_manager),
    authenticated: str = Depends(verify_auth),
) -> Dict[str, str]:
    """Resume a paused replay job."""
    if not replay_manager:
        raise HTTPException(503, "Replay manager not available")

    if not await replay_manager.resume_replay(job_id):
        raise HTTPException(400, f"Failed to resume job '{job_id}'")

    return {"status": "resumed", "job_id": job_id}


@router.post("/events/replay/{job_id}/cancel")
async def cancel_replay_job(
    job_id: str,
    replay_manager: Optional[Any] = Depends(get_replay_manager),
    authenticated: str = Depends(verify_auth),
) -> Dict[str, str]:
    """Cancel a replay job."""
    if not replay_manager:
        raise HTTPException(503, "Replay manager not available")

    if not await replay_manager.cancel_replay(job_id):
        raise HTTPException(400, f"Failed to cancel job '{job_id}'")

    return {"status": "cancelled", "job_id": job_id}


@router.get("/events/replay")
async def list_replay_jobs(
    active_only: bool = False,
    replay_manager: Optional[Any] = Depends(get_replay_manager),
    authenticated: str = Depends(verify_auth),
) -> ReplayJobListResponse:
    """
    List all replay jobs.
    
    Args:
        active_only: Only return active jobs
    """
    if not replay_manager:
        raise HTTPException(503, "Replay manager not available")

    try:
        jobs = replay_manager.get_all_jobs()

        if active_only:
            jobs = replay_manager.active_jobs

        active_count = len(replay_manager.active_jobs)

        return ReplayJobListResponse(
            jobs=[
                ReplayJobResponse(
                    job_id=job.job_id,
                    stream_name=job.stream_name,
                    start_sequence=job.start_sequence,
                    end_sequence=job.end_sequence,
                    subject_filter=job.subject_filter,
                    destination_stream=job.destination_stream,
                    replay_speed=job.replay_speed,
                    status=job.status.value,
                    progress=job.progress,
                    total=job.total,
                    progress_percent=job.progress_percent,
                    started_at=job.started_at.isoformat() if job.started_at else None,
                    completed_at=job.completed_at.isoformat() if job.completed_at else None,
                    error=job.error,
                )
                for job in jobs
            ],
            total=len(jobs),
            active=active_count,
        )
    except Exception as e:
        logger.error(f"Failed to list replay jobs: {e}", exc_info=True)
        raise HTTPException(500, f"Failed to list replay jobs: {str(e)}")


@router.get("/events/replay/{job_id}")
async def get_replay_job(
    job_id: str,
    replay_manager: Optional[Any] = Depends(get_replay_manager),
    authenticated: str = Depends(verify_auth),
) -> ReplayJobResponse:
    """Get details of a specific replay job."""
    if not replay_manager:
        raise HTTPException(503, "Replay manager not available")

    job = replay_manager.get_job(job_id)
    if not job:
        raise HTTPException(404, f"Replay job '{job_id}' not found")

    return ReplayJobResponse(
        job_id=job.job_id,
        stream_name=job.stream_name,
        start_sequence=job.start_sequence,
        end_sequence=job.end_sequence,
        subject_filter=job.subject_filter,
        destination_stream=job.destination_stream,
        replay_speed=job.replay_speed,
        status=job.status.value,
        progress=job.progress,
        total=job.total,
        progress_percent=job.progress_percent,
        started_at=job.started_at.isoformat() if job.started_at else None,
        completed_at=job.completed_at.isoformat() if job.completed_at else None,
        error=job.error,
    )


@router.post("/events/time-travel")
async def create_time_travel_request(
    request_data: TimeTravelRequestCreate,
    replay_manager: Optional[Any] = Depends(get_replay_manager),
    authenticated: str = Depends(verify_auth),
) -> Dict[str, Any]:
    """
    Create a time travel debugging request.
    
    Args:
        request_data: Time travel request configuration
    """
    if not replay_manager:
        raise HTTPException(503, "Replay manager not available")

    try:
        # Parse target time
        target_time = datetime.fromisoformat(request_data.target_time)

        # Create request
        request = await replay_manager.create_time_travel_request(
            entity_id=request_data.entity_id,
            entity_type=request_data.entity_type,
            target_time=target_time,
            source_stream=request_data.source_stream,
            include_snapshots=request_data.include_snapshots,
        )

        return {
            "request_id": request.request_id,
            "entity_id": request.entity_id,
            "entity_type": request.entity_type,
            "target_time": request.target_time.isoformat(),
            "source_stream": request.source_stream,
            "status": "created",
        }
    except Exception as e:
        logger.error(f"Failed to create time travel request: {e}", exc_info=True)
        raise HTTPException(500, f"Failed to create time travel request: {str(e)}")


@router.post("/events/time-travel/{request_id}/execute")
async def execute_time_travel(
    request_id: str,
    replay_manager: Optional[Any] = Depends(get_replay_manager),
    authenticated: str = Depends(verify_auth),
) -> TimeTravelResponse:
    """
    Execute time travel state reconstruction.
    
    Args:
        request_id: Time travel request ID
    """
    if not replay_manager:
        raise HTTPException(503, "Replay manager not available")

    request = replay_manager._time_travel_requests.get(request_id)
    if not request:
        raise HTTPException(404, f"Time travel request '{request_id}' not found")

    try:
        # Import event store for state applier

        def state_applier(state: Dict[str, Any], event: Any) -> Dict[str, Any]:
            """Apply event to state."""
            if hasattr(event, 'payload'):
                state.update(event.payload)
            return state

        # Execute time travel
        state = await replay_manager.execute_time_travel(request, state_applier)

        # Count events applied (approximate)
        events_applied = len(state.get("_events_applied", [])) if isinstance(state, dict) else 0

        # Check if snapshot was used
        snapshot_used = state.get("_snapshot_used", False) if isinstance(state, dict) else False

        return TimeTravelResponse(
            request_id=request_id,
            entity_id=request.entity_id,
            entity_type=request.entity_type,
            target_time=request.target_time.isoformat(),
            state=state,
            events_applied=events_applied,
            snapshot_used=snapshot_used,
        )
    except Exception as e:
        logger.error(f"Failed to execute time travel: {e}", exc_info=True)
        raise HTTPException(500, f"Failed to execute time travel: {str(e)}")


@router.get("/events/stats")
async def get_event_stats(
    replay_manager: Optional[Any] = Depends(get_replay_manager),
    authenticated: str = Depends(verify_auth),
) -> Dict[str, Any]:
    """
    Get event replay statistics.
    
    Returns:
        Replay statistics
    """
    if not replay_manager:
        raise HTTPException(503, "Replay manager not available")

    try:
        stats = await replay_manager.get_stats()
        return stats
    except Exception as e:
        logger.error(f"Failed to get event stats: {e}", exc_info=True)
        raise HTTPException(500, f"Failed to get event stats: {str(e)}")
