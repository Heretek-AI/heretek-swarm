"""
Heretek Swarm WebSocket Endpoints

Provides WebSocket connections for:
- Execution updates: Real-time status of agent executions
- A2A messages: Agent-to-agent message stream monitoring
- Agent events: Live agent state change notifications
"""

import asyncio
import json
import os
from typing import Any, Dict, Optional
from datetime import datetime

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException
import structlog

from heretek_swarm.gateway import EventMesh

logger = structlog.get_logger("api.websockets")

# Create WebSocket router
router = APIRouter()

# Connection manager for tracking active WebSocket connections
class ConnectionManager:
    """Manages WebSocket connections for broadcasting."""
    
    def __init__(self):
        self.active_connections: Dict[str, set[WebSocket]] = {}
        self.execution_watchers: Dict[str, set[WebSocket]] = {}
        self.a2a_listeners: set[WebSocket] = set()
        self.dashboard_listeners: set[WebSocket] = set()
        self.observability_listeners: set[WebSocket] = set()
    
    async def connect_execution(self, websocket: WebSocket, execution_id: str):
        """Connect to execution updates channel."""
        await websocket.accept()
        if execution_id not in self.execution_watchers:
            self.execution_watchers[execution_id] = set()
        self.execution_watchers[execution_id].add(websocket)
        logger.info("WebSocket connected to execution", execution_id=execution_id)
    
    def disconnect_execution(self, websocket: WebSocket, execution_id: str):
        """Disconnect from execution updates."""
        if execution_id in self.execution_watchers:
            self.execution_watchers[execution_id].discard(websocket)
            if not self.execution_watchers[execution_id]:
                del self.execution_watchers[execution_id]
    
    async def connect_a2a(self, websocket: WebSocket):
        """Connect to A2A message stream."""
        await websocket.accept()
        self.a2a_listeners.add(websocket)
        logger.info("WebSocket connected to A2A stream")
    
    def disconnect_a2a(self, websocket: WebSocket):
        """Disconnect from A2A message stream."""
        self.a2a_listeners.discard(websocket)
    
    async def connect_dashboard(self, websocket: WebSocket):
        """Connect to dashboard updates channel."""
        await websocket.accept()
        self.dashboard_listeners.add(websocket)
        logger.info("WebSocket connected to dashboard")
    
    def disconnect_dashboard(self, websocket: WebSocket):
        """Disconnect from dashboard updates."""
        self.dashboard_listeners.discard(websocket)
    
    async def connect_observability(self, websocket: WebSocket):
        """Connect to observability updates channel."""
        await websocket.accept()
        self.observability_listeners.add(websocket)
        logger.info("WebSocket connected to observability")
    
    def disconnect_observability(self, websocket: WebSocket):
        """Disconnect from observability updates."""
        self.observability_listeners.discard(websocket)
    
    async def broadcast_execution(self, execution_id: str, data: Dict[str, Any]):
        """Broadcast execution update to all watchers."""
        if execution_id in self.execution_watchers:
            disconnected = set()
            for websocket in self.execution_watchers[execution_id]:
                try:
                    await websocket.send_json(data)
                except Exception:
                    disconnected.add(websocket)
            # Clean up disconnected
            for ws in disconnected:
                self.execution_watchers[execution_id].discard(ws)
    
    async def broadcast_a2a(self, data: Dict[str, Any]):
        """Broadcast A2A message to all listeners."""
        disconnected = set()
        for websocket in self.a2a_listeners:
            try:
                await websocket.send_json(data)
            except Exception:
                disconnected.add(websocket)
        for ws in disconnected:
            self.a2a_listeners.discard(ws)
    
    async def broadcast_dashboard(self, data: Dict[str, Any]):
        """Broadcast dashboard update to all listeners."""
        disconnected = set()
        for websocket in self.dashboard_listeners:
            try:
                await websocket.send_json(data)
            except Exception:
                disconnected.add(websocket)
        for ws in disconnected:
            self.dashboard_listeners.discard(ws)
    
    async def broadcast_observability(self, data: Dict[str, Any]):
        """Broadcast observability update to all listeners."""
        disconnected = set()
        for websocket in self.observability_listeners:
            try:
                await websocket.send_json(data)
            except Exception:
                disconnected.add(websocket)
        for ws in disconnected:
            self.observability_listeners.discard(ws)


# Global connection manager
manager = ConnectionManager()


# =============================================================================
# Execution Updates WebSocket
# =============================================================================

@router.websocket("/ws/executions/{execution_id}")
async def execution_websocket(websocket: WebSocket, execution_id: str):
    """
    WebSocket endpoint for real-time execution updates.
    
    Clients connect to receive live updates about agent execution progress.
    Messages are sent as JSON with the following structure:
    {
        "execution_id": "...",
        "status": "running|completed|failed",
        "progress": 0.75,
        "message": "Processing step 3 of 4",
        "timestamp": "2024-01-01T12:00:00Z"
    }
    
    Args:
        execution_id: Unique execution identifier
        
    Example:
        ```javascript
        const ws = new WebSocket("ws://localhost:8000/ws/executions/exec-123");
        ws.onmessage = (event) => {
            const update = JSON.parse(event.data);
            console.log(`Progress: ${update.progress * 100}%`);
        };
        ```
    """
    await manager.connect_execution(websocket, execution_id)
    
    try:
        # Send initial connection confirmation
        await websocket.send_json({
            "type": "connected",
            "execution_id": execution_id,
            "timestamp": datetime.utcnow().isoformat(),
        })
        
        # Track execution state in memory (simplified - in production use Redis)
        execution_state = {
            "execution_id": execution_id,
            "status": "running",
            "progress": 0.0,
            "message": "Initializing",
            "started_at": datetime.utcnow().isoformat(),
        }
        
        # Store in memory for retrieval
        _execution_store[execution_id] = execution_state
        
        # Keep connection alive and send periodic updates
        # In production, this would listen to actual execution events
        while True:
            try:
                # Wait for messages from client (e.g., pause, cancel)
                data = await asyncio.wait_for(websocket.receive_text(), timeout=30.0)
                message = json.loads(data)
                
                # Handle client commands
                if message.get("command") == "cancel":
                    execution_state["status"] = "cancelled"
                    execution_state["message"] = "Cancelled by client"
                    await manager.broadcast_execution(execution_id, execution_state)
                    break
                    
            except asyncio.TimeoutError:
                # Send heartbeat/update
                await websocket.send_json({
                    "type": "heartbeat",
                    "timestamp": datetime.utcnow().isoformat(),
                })
                
    except WebSocketDisconnect:
        logger.info("WebSocket disconnected", execution_id=execution_id)
    except Exception as e:
        logger.error("WebSocket error", execution_id=execution_id, error=str(e))
    finally:
        manager.disconnect_execution(websocket, execution_id)


# In-memory execution store (use Redis in production)
_execution_store: Dict[str, Dict[str, Any]] = {}


async def get_execution_update(execution_id: str) -> Dict[str, Any]:
    """
    Get current execution state.
    
    Args:
        execution_id: Unique execution identifier
        
    Returns:
        Current execution state or default
    """
    return _execution_store.get(execution_id, {
        "execution_id": execution_id,
        "status": "unknown",
        "message": "Execution not found",
    })


# =============================================================================
# A2A Protocol WebSocket
# =============================================================================

@router.websocket("/ws/a2a")
async def a2a_websocket(websocket: WebSocket):
    """
    WebSocket endpoint for A2A protocol message stream.
    
    This endpoint provides real-time monitoring of agent-to-agent messages.
    All A2A messages are broadcast to connected clients.
    
    Message format:
    {
        "type": "message|request|response|error",
        "from": "agent-id",
        "to": "agent-id",
        "payload": {...},
        "timestamp": "2024-01-01T12:00:00Z"
    }
    
    Example:
        ```javascript
        const ws = new WebSocket("ws://localhost:8000/ws/a2a");
        ws.onmessage = (event) => {
            const msg = JSON.parse(event.data);
            console.log(`A2A: ${msg.from} -> ${msg.to}`);
        };
        ```
    """
    await manager.connect_a2a(websocket)
    
    # Try to use Redis pub/sub if available, fallback to simulation
    try:
        import redis.asyncio as redis
        
        redis_url = os.environ.get("REDIS_URL", "redis://localhost:6379")
        r = redis.from_url(redis_url)
        
        # Create pub/sub for A2A messages
        pubsub = r.pubsub()
        await pubsub.subscribe("a2a:messages")
        
        try:
            # Listen for messages
            async for message in pubsub.listen():
                if message["type"] == "message":
                    data = json.loads(message["data"])
                    await websocket.send_json(data)
                    
        except WebSocketDisconnect:
            pass
        finally:
            await pubsub.unsubscribe("a2a:messages")
            await r.close()
            
    except Exception as e:
        logger.warning("Redis not available for A2A, using fallback", error=str(e))
        
        # Fallback: simulate A2A messages (for development)
        try:
            while True:
                # Send periodic heartbeat to keep connection alive
                await websocket.send_json({
                    "type": "heartbeat",
                    "timestamp": datetime.utcnow().isoformat(),
                })
                await asyncio.sleep(30)
                
        except WebSocketDisconnect:
            pass
    finally:
        manager.disconnect_a2a(websocket)


# =============================================================================
# Agent Events WebSocket
# =============================================================================

@router.websocket("/ws/agents/{agent_id}/events")
async def agent_events_websocket(websocket: WebSocket, agent_id: str):
    """
    WebSocket endpoint for agent-specific event stream.
    
    Provides real-time events for a specific agent including:
    - State changes
    - Message receipts
    - Tool executions
    - Errors
    
    Args:
        agent_id: Unique agent identifier
        
    Message format:
    {
        "event": "state_changed|message_received|tool_executed|error",
        "agent_id": "agent-id",
        "data": {...},
        "timestamp": "2024-01-01T12:00:00Z"
    }
    """
    await websocket.accept()
    
    logger.info("Agent events WebSocket connected", agent_id=agent_id)
    
    try:
        # Keep connection alive and stream events
        while True:
            try:
                # Wait for client messages
                data = await asyncio.wait_for(websocket.receive_text(), timeout=60.0)
                message = json.loads(data)
                
                # Handle subscription/unsubscription to event types
                if message.get("action") == "subscribe":
                    event_type = message.get("event_type")
                    logger.info("Subscribed to event", agent_id=agent_id, event_type=event_type)
                    
            except asyncio.TimeoutError:
                # Send heartbeat
                await websocket.send_json({
                    "type": "heartbeat",
                    "timestamp": datetime.utcnow().isoformat(),
                })
                
    except WebSocketDisconnect:
        logger.info("Agent events WebSocket disconnected", agent_id=agent_id)
    except Exception as e:
        logger.error("Agent events WebSocket error", agent_id=agent_id, error=str(e))


# =============================================================================
# Dashboard WebSocket
# =============================================================================

@router.websocket("/ws/dashboard")
async def dashboard_websocket(websocket: WebSocket):
    """
    WebSocket endpoint for real-time dashboard updates.
    
    Broadcasts:
    - Agent status changes
    - Memory statistics
    - A2A messages
    - Consensus state
    - System health
    
    Message format:
    {
        "type": "agent_update|agent_spawned|agent_terminated|a2a_message|memory_update|consensus_update|health_update",
        "data": {...},
        "timestamp": "2024-01-01T12:00:00Z"
    }
    """
    await manager.connect_dashboard(websocket)
    
    logger.info("Dashboard WebSocket connected")
    
    try:
        # Keep connection alive and stream updates
        while True:
            try:
                # Wait for client messages (heartbeat, subscriptions)
                data = await asyncio.wait_for(websocket.receive_text(), timeout=60.0)
                message = json.loads(data)
                
                # Handle client requests
                if message.get("action") == "ping":
                    await websocket.send_json({
                        "type": "pong",
                        "timestamp": datetime.utcnow().isoformat(),
                    })
                    
            except asyncio.TimeoutError:
                # Send heartbeat
                await websocket.send_json({
                    "type": "heartbeat",
                    "timestamp": datetime.utcnow().isoformat(),
                })
                await asyncio.sleep(30)
                
    except WebSocketDisconnect:
        logger.info("Dashboard WebSocket disconnected")
    except Exception as e:
        logger.error("Dashboard WebSocket error", error=str(e))
    finally:
        manager.disconnect_dashboard(websocket)


# =============================================================================
# Observability WebSocket
# =============================================================================

@router.websocket("/ws/observability")
async def observability_websocket(websocket: WebSocket):
    """
    WebSocket endpoint for real-time observability updates.
    
    Broadcasts:
    - LLM traces
    - Agent executions
    - Performance metrics
    - Error logs
    
    Message format:
    {
        "type": "new_trace|execution_update|new_execution|metric_update|new_error",
        "data": {...},
        "timestamp": "2024-01-01T12:00:00Z"
    }
    """
    await manager.connect_observability(websocket)
    
    logger.info("Observability WebSocket connected")
    
    try:
        # Keep connection alive and stream updates
        while True:
            try:
                # Wait for client messages (heartbeat, subscriptions)
                data = await asyncio.wait_for(websocket.receive_text(), timeout=60.0)
                message = json.loads(data)
                
                # Handle client requests
                if message.get("action") == "ping":
                    await websocket.send_json({
                        "type": "pong",
                        "timestamp": datetime.utcnow().isoformat(),
                    })
                    
            except asyncio.TimeoutError:
                # Send heartbeat
                await websocket.send_json({
                    "type": "heartbeat",
                    "timestamp": datetime.utcnow().isoformat(),
                })
                await asyncio.sleep(30)
                
    except WebSocketDisconnect:
        logger.info("Observability WebSocket disconnected")
    except Exception as e:
        logger.error("Observability WebSocket error", error=str(e))
    finally:
        manager.disconnect_observability(websocket)


# =============================================================================
# Agent State Stream WebSocket
# =============================================================================

@router.websocket("/ws/agents")
async def all_agents_websocket(websocket: WebSocket):
    """
    WebSocket endpoint for all agent state updates.
    
    Broadcasts state changes for all agents to connected clients.
    Useful for dashboards and monitoring.
    
    Message format:
    {
        "event": "agent_spawned|agent_terminated|agent_state_changed",
        "agent_id": "agent-id",
        "state": "active|suspended|terminated|error",
        "timestamp": "2024-01-01T12:00:00Z"
    }
    """
    await websocket.accept()
    
    logger.info("All agents WebSocket connected")
    
    # Track this connection for broadcasting
    all_agent_listeners = set([websocket])
    
    try:
        while True:
            try:
                data = await asyncio.wait_for(websocket.receive_text(), timeout=60.0)
                message = json.loads(data)
                
            except asyncio.TimeoutError:
                await websocket.send_json({
                    "type": "heartbeat",
                    "timestamp": datetime.utcnow().isoformat(),
                })
                
    except WebSocketDisconnect:
        logger.info("All agents WebSocket disconnected")
    except Exception as e:
        logger.error("All agents WebSocket error", error=str(e))


# Export router
__all__ = ["router", "manager"]