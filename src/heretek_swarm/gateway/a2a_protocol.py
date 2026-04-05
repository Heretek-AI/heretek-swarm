"""
A2A Protocol - Agent-to-Agent Messaging Protocol

Implements the A2A (Agent-to-Agent) protocol for inter-agent communication
over WebSocket connections on port 18789.

Message Types:
- HANDSHAKE: Connection initialization
- DISCOVERY: Service/agent discovery
- MESSAGE: Standard agent message
- STATUS: Status updates
- PROPOSAL: Triad proposals
- VOTE: Triad voting
- DECISION: Final decisions
- ERROR: Error notifications
"""

import asyncio
import json
import logging
import uuid
from typing import Dict, Any, Optional, List, Set
from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime

import structlog
from starlette.websockets import WebSocket, WebSocketState
from starlette.applications import Starlette
from starlette.routing import Route
from starlette.requests import Request
from starlette.responses import JSONResponse

logger = structlog.get_logger(__name__)


# Message type constants
class MessageType(str, Enum):
    """A2A Protocol message types."""
    HANDSHAKE = "handshake"
    DISCOVERY = "discovery"
    MESSAGE = "message"
    STATUS = "status"
    PROPOSAL = "proposal"
    VOTE = "vote"
    DECISION = "decision"
    ERROR = "error"


# Protocol constants
PROTOCOL_VERSION = "2.0"
DEFAULT_PORT = 18789
REDIS_CHANNEL_PREFIX = "a2a:messages"


@dataclass
class A2AMessage:
    """Structured A2A message."""
    msg_type: str
    sender_id: str
    sender_type: str
    payload: Dict[str, Any]
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    message_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    correlation_id: Optional[str] = None


class A2AProtocol:
    """
    A2A Protocol Handler for agent-to-agent messaging.
    
    Handles WebSocket connections, message routing, and protocol compliance.
    Implements handshake flow, discovery endpoints, and Redis pub/sub logging.
    """
    
    def __init__(
        self,
        event_mesh,
        port: int = DEFAULT_PORT,
        redis_client=None,
        auth_required: bool = True
    ):
        """
        Initialize A2A Protocol.
        
        Args:
            event_mesh: EventMesh instance for message broadcasting
            port: WebSocket server port (default 18789)
            redis_client: Optional Redis client for pub/sub logging
            auth_required: Whether authentication is required
        """
        self.event_mesh = event_mesh
        self.port = port
        self.redis_client = redis_client
        self.auth_required = auth_required
        
        # Connection state
        self._connections: Dict[str, WebSocket] = {}
        self._authenticated: Set[str] = set()
        self._agent_registry: Dict[str, Dict[str, Any]] = {}
        
        # Server state
        self._server = None
        self._running = False
        
        logger.info(
            "a2a_protocol_initialized",
            port=port,
            redis_enabled=redis_client is not None,
            auth_required=auth_required
        )
    
    # ============== WebSocket Server ==============
    
    async def start_server(self) -> None:
        """Start the WebSocket server."""
        from starlette.routing import Route, WebSocketRoute
        
        async def websocket_endpoint(ws: WebSocket):
            await self._handle_connection(ws)
        
        routes = [
            Route("/ws", websocket_endpoint),
            Route("/health", self._health_check),
        ]
        
        app = Starlette(routes=routes)
        
        import uvicorn
        config = uvicorn.Config(
            app,
            host="0.0.0.0",
            port=self.port,
            log_level="info"
        )
        self._server = uvicorn.Server(config)
        
        logger.info("a2a_server_starting", port=self.port)
        
        config.setup()
        self._running = True
        
        # Run server
        asyncio.create_task(self._server.serve())
        
        logger.info("a2a_server_started", port=self.port)
    
    async def stop_server(self) -> None:
        """Stop the WebSocket server."""
        self._running = False
        if self._server:
            self._server.should_exit = True
        logger.info("a2a_server_stopped")
    
    async def _health_check(self, request: Request) -> JSONResponse:
        """Health check endpoint."""
        return JSONResponse({
            "status": "healthy",
            "protocol": "A2A",
            "version": PROTOCOL_VERSION,
            "connections": len(self._connections),
            "agents": len(self._agent_registry)
        })
    
    # ============== Connection Handling ==============
    
    async def _handle_connection(self, websocket: WebSocket) -> None:
        """
        Handle incoming WebSocket connection.
        
        Implements:
        - Authentication check
        - Handshake flow
        - Message loop
        - Cleanup on disconnect
        """
        client_id = None
        
        try:
            await websocket.accept()
            logger.info("a2a_connection_accepted", remote=websocket.client.host if websocket.client else "unknown")
            
            # Message loop
            async for raw_message in websocket.iter_json():
                if raw_message is None:
                    continue
                
                msg_type = raw_message.get("type")
                
                # Handle handshake first
                if msg_type == MessageType.HANDSHAKE:
                    client_id = await self._handle_handshake(websocket, raw_message)
                    continue
                
                # Check authentication for other messages
                if self.auth_required and client_id not in self._authenticated:
                    await self._send_error(
                        websocket,
                        "Not authenticated - complete handshake first"
                    )
                    continue
                
                # Route message based on type
                await self._route_message(websocket, client_id, raw_message)
                
        except Exception as e:
            logger.error("a2a_connection_error", error=str(e), client_id=client_id)
            
        finally:
            # Cleanup
            if client_id:
                await self._cleanup_connection(client_id)
    
    async def _handle_handshake(
        self,
        websocket: WebSocket,
        message: Dict[str, Any]
    ) -> str:
        """
        Handle handshake message.
        
        Flow:
        1. Client sends: {"type": "handshake", "agent": "steward"}
        2. Server validates and responds:
           {"type": "handshake", "status": "ok", "agent_id": "..."}
        """
        agent_type = message.get("agent", "unknown")
        capabilities = message.get("capabilities", [])
        metadata = message.get("metadata", {})
        
        # Register with EventMesh
        client_id = await self.event_mesh.register(
            websocket=websocket,
            agent_type=agent_type,
            capabilities=capabilities,
            metadata=metadata
        )
        
        # Track connection
        self._connections[client_id] = websocket
        self._authenticated.add(client_id)
        
        # Register in agent registry
        self._agent_registry[client_id] = {
            "agent_id": client_id,
            "agent_type": agent_type,
            "capabilities": capabilities,
            "metadata": metadata,
            "connected_at": datetime.utcnow().isoformat()
        }
        
        # Send handshake response
        response = {
            "type": "handshake",
            "status": "ok",
            "agent_id": client_id,
            "agent_type": agent_type,
            "protocol_version": PROTOCOL_VERSION,
            "capabilities": ["broadcast", "discovery", "messaging"]
        }
        
        await websocket.send_json(response)
        
        # Log to Redis
        await self._log_message(
            MessageType.HANDSHAKE.value,
            client_id,
            agent_type,
            {"status": "connected"}
        )
        
        logger.info(
            "a2a_handshake_completed",
            client_id=client_id,
            agent_type=agent_type
        )
        
        # Broadcast discovery to other agents
        await self._broadcast_discovery(client_id, agent_type)
        
        return client_id
    
    async def _broadcast_discovery(self, client_id: str, agent_type: str) -> None:
        """Broadcast new agent discovery to all connected agents."""
        discovery_msg = {
            "type": "discovery",
            "action": "agent_joined",
            "agent_id": client_id,
            "agent_type": agent_type,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        await self.event_mesh.broadcast(
            discovery_msg,
            exclude=[client_id]
        )
    
    async def _route_message(
        self,
        websocket: WebSocket,
        client_id: str,
        message: Dict[str, Any]
    ) -> None:
        """Route message to appropriate handler."""
        msg_type = message.get("type", "unknown")
        
        handler_map = {
            MessageType.DISCOVERY: self._handle_discovery,
            MessageType.MESSAGE: self._handle_agent_message,
            MessageType.STATUS: self._handle_status,
            MessageType.PROPOSAL: self._handle_proposal,
            MessageType.VOTE: self._handle_vote,
            MessageType.DECISION: self._handle_decision,
        }
        
        handler = handler_map.get(msg_type)
        if handler:
            await handler(client_id, message)
        else:
            logger.warning("a2a_unknown_message_type", type=msg_type)
    
    # ============== Message Handlers ==============
    
    async def _handle_discovery(
        self,
        client_id: str,
        message: Dict[str, Any]
    ) -> None:
        """Handle discovery request - return list of all agents."""
        action = message.get("action", "list_agents")
        
        if action == "list_agents":
            # Return all registered agents
            response = {
                "type": "discovery",
                "action": "agent_list",
                "agents": list(self._agent_registry.values()),
                "count": len(self._agent_registry)
            }
            await self.event_mesh.send_to(client_id, response)
            
        elif action == "by_type":
            # Filter by agent type
            agent_type = message.get("agent_type")
            filtered = [
                a for a in self._agent_registry.values()
                if a["agent_type"] == agent_type
            ]
            response = {
                "type": "discovery",
                "action": "agent_list",
                "agents": filtered,
                "count": len(filtered)
            }
            await self.event_mesh.send_to(client_id, response)
        
        # Log to Redis
        await self._log_message(
            MessageType.DISCOVERY.value,
            client_id,
            self._get_agent_type(client_id),
            message
        )
    
    async def _handle_agent_message(
        self,
        client_id: str,
        message: Dict[str, Any]
    ) -> None:
        """Handle standard agent-to-agent message."""
        target_id = message.get("target")
        content = message.get("content", {})
        
        if target_id:
            # Direct message
            await self.event_mesh.send_to(target_id, message)
        else:
            # Broadcast
            await self.event_mesh.broadcast(message, exclude=[client_id])
        
        # Log to Redis
        await self._log_message(
            MessageType.MESSAGE.value,
            client_id,
            self._get_agent_type(client_id),
            content
        )
    
    async def _handle_status(
        self,
        client_id: str,
        message: Dict[str, Any]
    ) -> None:
        """Handle status update message."""
        status = message.get("status", {})
        
        # Update agent registry with status
        if client_id in self._agent_registry:
            self._agent_registry[client_id]["status"] = status
        
        # Broadcast to all
        await self.event_mesh.broadcast(message, exclude=[client_id])
        
        await self._log_message(
            MessageType.STATUS.value,
            client_id,
            self._get_agent_type(client_id),
            status
        )
    
    async def _handle_proposal(
        self,
        client_id: str,
        message: Dict[str, Any]
    ) -> None:
        """Handle triad proposal message."""
        proposal_id = message.get("proposal_id")
        
        # Broadcast proposal to all agents
        await self.event_mesh.broadcast(message, exclude=[client_id])
        
        logger.info(
            "a2a_proposal_received",
            client_id=client_id,
            proposal_id=proposal_id
        )
        
        await self._log_message(
            MessageType.PROPOSAL.value,
            client_id,
            self._get_agent_type(client_id),
            message
        )
    
    async def _handle_vote(
        self,
        client_id: str,
        message: Dict[str, Any]
    ) -> None:
        """Handle triad vote message."""
        vote = message.get("vote")
        proposal_id = message.get("proposal_id")
        
        await self.event_mesh.broadcast(message, exclude=[client_id])
        
        logger.info(
            "a2a_vote_received",
            client_id=client_id,
            proposal_id=proposal_id,
            vote=vote
        )
        
        await self._log_message(
            MessageType.VOTE.value,
            client_id,
            self._get_agent_type(client_id),
            message
        )
    
    async def _handle_decision(
        self,
        client_id: str,
        message: Dict[str, Any]
    ) -> None:
        """Handle final decision message."""
        decision = message.get("decision")
        proposal_id = message.get("proposal_id")
        
        await self.event_mesh.broadcast(message)
        
        logger.info(
            "a2a_decision_made",
            client_id=client_id,
            proposal_id=proposal_id,
            decision=decision
        )
        
        await self._log_message(
            MessageType.DECISION.value,
            client_id,
            self._get_agent_type(client_id),
            message
        )
    
    async def _send_error(self, websocket: WebSocket, error_msg: str) -> None:
        """Send error message to client."""
        await websocket.send_json({
            "type": "error",
            "message": error_msg,
            "timestamp": datetime.utcnow().isoformat()
        })
    
    async def _cleanup_connection(self, client_id: str) -> None:
        """Clean up connection state on disconnect."""
        # Remove from connections
        self._connections.pop(client_id, None)
        
        # Remove from authenticated set
        self._authenticated.discard(client_id)
        
        # Remove from registry
        agent_info = self._agent_registry.pop(client_id, {})
        
        # Unregister from EventMesh
        await self.event_mesh.unregister(client_id)
        
        logger.info(
            "a2a_connection_cleaned",
            client_id=client_id,
            agent_type=agent_info.get("agent_type", "unknown")
        )
        
        # Broadcast disconnect
        discovery_msg = {
            "type": "discovery",
            "action": "agent_left",
            "agent_id": client_id,
            "agent_type": agent_info.get("agent_type", "unknown"),
            "timestamp": datetime.utcnow().isoformat()
        }
        await self.event_mesh.broadcast(discovery_msg)
    
    # ============== Redis Logging ==============
    
    async def _log_message(
        self,
        msg_type: str,
        sender_id: str,
        sender_type: str,
        payload: Dict[str, Any]
    ) -> None:
        """Log message to Redis pub/sub if available."""
        if not self.redis_client:
            return
        
        try:
            channel = f"{REDIS_CHANNEL_PREFIX}:{msg_type}"
            message_data = {
                "type": msg_type,
                "sender_id": sender_id,
                "sender_type": sender_type,
                "payload": payload,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            await self.redis_client.publish(channel, json.dumps(message_data))
            
        except Exception as e:
            logger.error("a2a_redis_log_failed", error=str(e))
    
    # ============== Helpers ==============
    
    def _get_agent_type(self, client_id: str) -> str:
        """Get agent type for client ID."""
        agent = self._agent_registry.get(client_id, {})
        return agent.get("agent_type", "unknown")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get A2A Protocol statistics."""
        return {
            "connections": len(self._connections),
            "authenticated": len(self._authenticated),
            "registered_agents": len(self._agent_registry),
            "agent_types": self._count_agent_types(),
            "port": self.port,
            "running": self._running
        }
    
    def _count_agent_types(self) -> Dict[str, int]:
        """Count agents by type."""
        counts: Dict[str, int] = {}
        for agent in self._agent_registry.values():
            atype = agent.get("agent_type", "unknown")
            counts[atype] = counts.get(atype, 0) + 1
        return counts


# ============== Protocol Constants ==============

MESSAGE_TYPES = {
    "HANDSHAKE": "handshake",
    "DISCOVERY": "discovery",
    "MESSAGE": "message",
    "STATUS": "status",
    "PROPOSAL": "proposal",
    "VOTE": "vote",
    "DECISION": "decision",
    "ERROR": "error"
}