"""
EventMesh - Agent-to-Agent Communication Bus

This module provides the EventMesh class for managing WebSocket connections
between agents in the Heretek Swarm, with null-safety handling to prevent
crashes from disconnected clients.

Reference: OpenClaw v2.0 gateway implementation
"""

import logging
import asyncio
import uuid
from typing import List, Optional, Dict, Any, Callable
from dataclasses import dataclass, field
from enum import Enum

import structlog

logger = structlog.get_logger(__name__)


class ConnectionState(Enum):
    """WebSocket connection states."""
    CONNECTING = "connecting"
    OPEN = "open"
    CLOSING = "closing"
    CLOSED = "closed"


@dataclass
class AgentInfo:
    """Information about a connected agent."""
    agent_id: str
    agent_type: str
    capabilities: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    connected_at: float = field(default_factory=lambda: asyncio.get_event_loop().time())


@dataclass
class ClientConnection:
    """Wrapper for WebSocket connections with state tracking."""
    websocket: Any
    agent_info: AgentInfo
    connection_state: ConnectionState = ConnectionState.OPEN
    
    @property
    def is_connected(self) -> bool:
        """Check if client is still connected and ready."""
        return (
            self.websocket is not None
            and self.connection_state == ConnectionState.OPEN
        )


class EventMesh:
    """
    EventMesh - Central message bus for agent-to-agent communication.
    
    Manages WebSocket connections with null-safety handling to prevent
    crashes from disconnected or null clients.
    
    Features:
    - Automatic cleanup of disconnected clients
    - Broadcast messaging with error handling
    - Targeted message delivery
    - Connection state tracking
    """
    
    def __init__(self, max_clients: int = 100):
        """
        Initialize EventMesh.
        
        Args:
            max_clients: Maximum number of concurrent connections
        """
        self.max_clients = max_clients
        self._clients: Dict[str, ClientConnection] = {}
        self._message_handlers: Dict[str, Callable] = {}
        self._lock = asyncio.Lock()
        
        logger.info(
            "event_mesh_initialized",
            max_clients=max_clients,
            component="EventMesh"
        )
    
    @property
    def clients(self) -> List[ClientConnection]:
        """Get list of active clients."""
        return list(self._clients.values())
    
    @property
    def client_count(self) -> int:
        """Get number of connected clients."""
        return len(self._clients)
    
    def _filter_active_clients(self) -> List[ClientConnection]:
        """
        Filter out disconnected or null clients.
        
        This is the critical fix for the null reference bug - we filter
        before every broadcast to ensure only valid clients receive messages.
        
        Returns:
            List of active ClientConnection objects
        """
        active = []
        for client_id, client in self._clients.items():
            if client is None:
                logger.warning("event_mesh_null_client_removed", client_id=client_id)
                continue
            if client.websocket is None:
                logger.warning("event_mesh_websocket_null_removed", client_id=client_id)
                continue
            if client.connection_state != ConnectionState.OPEN:
                logger.debug(
                    "event_mesh_inactive_client_skipped",
                    client_id=client_id,
                    state=client.connection_state.value
                )
                continue
            active.append(client)
        return active
    
    async def register(
        self,
        websocket: Any,
        agent_type: str,
        capabilities: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Register a new client connection.
        
        Args:
            websocket: WebSocket connection
            agent_type: Type of agent (e.g., "steward", "historian")
            capabilities: List of agent capabilities
            metadata: Additional agent metadata
            
        Returns:
            Unique client ID
        """
        async with self._lock:
            if len(self._clients) >= self.max_clients:
                logger.error("event_mesh_max_clients_reached", max=self.max_clients)
                raise RuntimeError(f"Maximum clients ({self.max_clients}) reached")
            
            client_id = str(uuid.uuid4())
            
            agent_info = AgentInfo(
                agent_id=client_id,
                agent_type=agent_type,
                capabilities=capabilities or [],
                metadata=metadata or {}
            )
            
            client_connection = ClientConnection(
                websocket=websocket,
                agent_info=agent_info,
                connection_state=ConnectionState.OPEN
            )
            
            self._clients[client_id] = client_connection
            
            logger.info(
                "event_mesh_client_registered",
                client_id=client_id,
                agent_type=agent_type,
                total_clients=len(self._clients)
            )
            
            return client_id
    
    async def unregister(self, client_id: str) -> bool:
        """
        Unregister a client connection with proper cleanup.
        
        Args:
            client_id: ID of client to remove
            
        Returns:
            True if client was removed, False if not found
        """
        async with self._lock:
            if client_id not in self._clients:
                logger.warning("event_mesh_client_not_found", client_id=client_id)
                return False
            
            client = self._clients.pop(client_id)
            
            # Clear websocket reference
            if client is not None:
                client.websocket = None
                client.connection_state = ConnectionState.CLOSED
            
            logger.info(
                "event_mesh_client_unregistered",
                client_id=client_id,
                agent_type=client.agent_info.agent_type if client else "unknown",
                remaining_clients=len(self._clients)
            )
            
            return True
    
    async def update_state(self, client_id: str, state: ConnectionState) -> bool:
        """
        Update connection state for a client.
        
        Args:
            client_id: ID of client to update
            state: New connection state
            
        Returns:
            True if updated, False if not found
        """
        async with self._lock:
            if client_id not in self._clients:
                return False
            
            client = self._clients[client_id]
            if client:
                client.connection_state = state
            
            logger.debug(
                "event_mesh_state_updated",
                client_id=client_id,
                state=state.value
            )
            return True
    
    async def broadcast(self, message: Dict[str, Any], exclude: Optional[List[str]] = None) -> int:
        """
        Broadcast message to all connected clients.
        
        Filters out null/disconnected clients before sending to prevent crashes.
        
        Args:
            message: Message to broadcast (will be JSON serialized)
            exclude: List of client IDs to exclude from broadcast
            
        Returns:
            Number of clients message was sent to
        """
        import json
        
        # Filter active clients first - this is the null-safety fix
        active_clients = self._filter_active_clients()
        
        exclude_set = set(exclude or [])
        target_clients = [
            c for c in active_clients 
            if c.agent_info.agent_id not in exclude_set
        ]
        
        if not target_clients:
            logger.debug("event_mesh_no_active_clients")
            return 0
        
        message_str = json.dumps(message)
        sent_count = 0
        
        for client in target_clients:
            try:
                if client.websocket is not None:
                    await client.websocket.send(message_str)
                    sent_count += 1
            except Exception as e:
                logger.error(
                    "event_mesh_broadcast_send_failed",
                    client_id=client.agent_info.agent_id,
                    agent_type=client.agent_info.agent_type,
                    error=str(e)
                )
                # Don't remove here - let cleanup handle it on next operation
        
        logger.info(
            "event_mesh_broadcast_completed",
            total_active=len(active_clients),
            sent_to=sent_count,
            excluded=len(exclude_set),
            message_type=message.get("type", "unknown")
        )
        
        return sent_count
    
    async def send_to(
        self,
        client_id: str,
        message: Dict[str, Any],
        raise_on_error: bool = False
    ) -> bool:
        """
        Send message to a specific client.
        
        Args:
            client_id: Target client ID
            message: Message to send
            raise_on_error: If True, raise exception on send failure
            
        Returns:
            True if sent successfully, False otherwise
        """
        import json
        
        async with self._lock:
            if client_id not in self._clients:
                logger.warning("event_mesh_send_client_not_found", client_id=client_id)
                return False
            
            client = self._clients[client_id]
            
            # Null check
            if client is None or client.websocket is None:
                logger.warning("event_mesh_send_client_null", client_id=client_id)
                return False
            
            # State check
            if client.connection_state != ConnectionState.OPEN:
                logger.warning(
                    "event_mesh_send_client_not_open",
                    client_id=client_id,
                    state=client.connection_state.value
                )
                return False
            
            try:
                await client.websocket.send(json.dumps(message))
                logger.debug(
                    "event_mesh_send_success",
                    client_id=client_id,
                    message_type=message.get("type", "unknown")
                )
                return True
            except Exception as e:
                logger.error(
                    "event_mesh_send_failed",
                    client_id=client_id,
                    error=str(e)
                )
                if raise_on_error:
                    raise
                return False
    
    def get_agent_info(self, client_id: str) -> Optional[AgentInfo]:
        """Get agent info for a client."""
        client = self._clients.get(client_id)
        return client.agent_info if client else None
    
    def get_all_agents(self) -> List[AgentInfo]:
        """Get info for all connected agents."""
        return [
            client.agent_info 
            for client in self._clients.values() 
            if client is not None
        ]
    
    def get_agents_by_type(self, agent_type: str) -> List[AgentInfo]:
        """Get all agents of a specific type."""
        return [
            client.agent_info 
            for client in self._clients.values()
            if client is not None and client.agent_info.agent_type == agent_type
        ]
    
    def register_handler(self, message_type: str, handler: Callable) -> None:
        """Register a handler for a specific message type."""
        self._message_handlers[message_type] = handler
        logger.debug("event_mesh_handler_registered", message_type=message_type)
    
    async def cleanup_stale_connections(self) -> int:
        """
        Remove stale connections from the client list.
        
        Returns:
            Number of connections cleaned up
        """
        async with self._lock:
            stale_ids = []
            for client_id, client in self._clients.items():
                if client is None or client.websocket is None:
                    stale_ids.append(client_id)
                elif client.connection_state == ConnectionState.CLOSED:
                    stale_ids.append(client_id)
            
            for client_id in stale_ids:
                self._clients.pop(client_id, None)
            
            if stale_ids:
                logger.info("event_mesh_cleanup_completed", removed=len(stale_ids))
            
            return len(stale_ids)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get EventMesh statistics."""
        return {
            "total_clients": len(self._clients),
            "max_clients": self.max_clients,
            "active_clients": len(self._filter_active_clients()),
            "agent_types": self._get_agent_type_counts(),
        }
    
    def _get_agent_type_counts(self) -> Dict[str, int]:
        """Get count of agents by type."""
        counts: Dict[str, int] = {}
        for client in self._clients.values():
            if client:
                agent_type = client.agent_info.agent_type
                counts[agent_type] = counts.get(agent_type, 0) + 1
        return counts