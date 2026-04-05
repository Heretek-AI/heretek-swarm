"""
EventMesh - WebSocket Connection Manager for Heretek Swarm

Provides null-safe broadcast and targeted messaging for A2A protocol.
Reference: MiniMax Audit Lines 11-30 (EventMesh bug fix)
"""

import asyncio
from typing import Dict, Optional, Set
from fastapi import WebSocket
import structlog

logger = structlog.get_logger(__name__)


class EventMesh:
    """
    WebSocket connection manager with null safety and error handling.
    
    Fixes the critical null reference bug from OpenClaw:
    - Filters dead connections before broadcast
    - Try/catch on all send operations
    - Automatic cleanup of failed connections
    """
    
    def __init__(self):
        self.clients: Dict[str, WebSocket] = {}
        self._lock = asyncio.Lock()
    
    @property
    def client_count(self) -> int:
        """Get number of connected clients."""
        return len(self.clients)
    
    async def register(self, client_id: str, websocket: WebSocket) -> None:
        """
        Register a new client connection.
        
        Args:
            client_id: Unique client identifier
            websocket: WebSocket connection
        """
        async with self._lock:
            self.clients[client_id] = websocket
            logger.info("client_registered", client_id=client_id, total=self.client_count)
    
    async def unregister(self, client_id: str) -> None:
        """
        Unregister client and cleanup.
        
        Args:
            client_id: Client to remove
        """
        async with self._lock:
            if client_id in self.clients:
                del self.clients[client_id]
                logger.info("client_unregistered", client_id=client_id, total=self.client_count)
    
    async def broadcast(self, message: bytes) -> Dict[str, int]:
        """
        Broadcast message to all connected clients with null safety.
        
        CRITICAL FIX: Filters dead connections before sending, wraps in try/catch.
        
        Args:
            message: Message bytes to broadcast
            
        Returns:
            Dict with success/failure counts
        """
        # Filter to active connections ONLY (null-safe)
        async with self._lock:
            active_clients = {
                cid: ws for cid, ws in self.clients.items()
                if ws is not None and not ws.client_state.disconnecting
            }
        
        if not active_clients:
            logger.debug("broadcast_no_clients")
            return {"sent": 0, "failed": 0}
        
        sent = 0
        failed = 0
        to_remove = []
        
        # Send to all active clients
        for client_id, websocket in active_clients.items():
            try:
                await websocket.send_bytes(message)
                sent += 1
            except Exception as e:
                logger.error("broadcast_send_failed", client_id=client_id, error=str(e))
                failed += 1
                to_remove.append(client_id)
        
        # Cleanup failed connections
        for client_id in to_remove:
            await self.unregister(client_id)
        
        logger.debug("broadcast_complete", sent=sent, failed=failed, active=len(active_clients))
        return {"sent": sent, "failed": failed}
    
    async def broadcast_json(self, data: dict) -> Dict[str, int]:
        """
        Broadcast JSON message to all clients.
        
        Args:
            data: Dict to send as JSON
            
        Returns:
            Dict with success/failure counts
        """
        import json
        message = json.dumps(data).encode('utf-8')
        return await self.broadcast(message)
    
    async def send_to(self, client_id: str, message: bytes) -> bool:
        """
        Send message to specific client.
        
        Args:
            client_id: Target client
            message: Message bytes
            
        Returns:
            True if sent successfully
        """
        websocket = self.clients.get(client_id)
        
        if websocket is None:
            logger.warning("send_to_client_not_found", client_id=client_id)
            return False
        
        try:
            await websocket.send_bytes(message)
            logger.debug("send_to_success", client_id=client_id)
            return True
        except Exception as e:
            logger.error("send_to_failed", client_id=client_id, error=str(e))
            await self.unregister(client_id)
            return False
    
    async def send_to_json(self, client_id: str, data: dict) -> bool:
        """
        Send JSON message to specific client.
        
        Args:
            client_id: Target client
            data: Dict to send as JSON
            
        Returns:
            True if sent successfully
        """
        import json
        message = json.dumps(data).encode('utf-8')
        return await self.send_to(client_id, message)
    
    def get_client_ids(self) -> Set[str]:
        """Get set of all connected client IDs."""
        return set(self.clients.keys())
    
    async def close_all(self) -> None:
        """Close all connections and cleanup."""
        async with self._lock:
            for client_id, websocket in list(self.clients.items()):
                try:
                    await websocket.close()
                except Exception:
                    pass
            self.clients.clear()
        
        logger.info("eventmesh_closed_all", initial_count=len(self.clients))
