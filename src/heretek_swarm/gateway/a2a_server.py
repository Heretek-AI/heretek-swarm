"""
A2A Protocol Server - Agent-to-Agent Communication

WebSocket RPC server on port 18789 for inter-agent communication.
Implements handshake, discovery, messaging, and consensus protocols.

Reference: OpenClaw A2A Protocol + MiniMax Audit
"""

import os
import json
import asyncio
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
from fastapi import WebSocket, WebSocketDisconnect
import structlog

from .event_mesh import EventMesh

logger = structlog.get_logger(__name__)


class MessageType(str, Enum):
    """A2A message types."""
    HANDSHAKE = "handshake"
    DISCOVERY = "discovery"
    MESSAGE = "message"
    STATUS = "status"
    PROPOSAL = "proposal"
    VOTE = "vote"
    DECISION = "decision"
    ERROR = "error"


@dataclass
class AgentInfo:
    """Connected agent information."""
    id: str
    websocket: WebSocket
    connected_at: datetime = field(default_factory=datetime.utcnow)
    last_activity: datetime = field(default_factory=datetime.utcnow)
    status: str = "idle"
    metadata: Dict[str, Any] = field(default_factory=dict)


class A2AServer:
    """
    Agent-to-Agent communication server.
    
    Runs on port 18789, manages agent connections and message routing.
    """
    
    def __init__(self, event_mesh: EventMesh):
        self.event_mesh = event_mesh
        self.agents: Dict[str, AgentInfo] = {}
        self._lock = asyncio.Lock()
        self._message_log: List[Dict] = []
        self._max_log_size = 1000
    
    async def handle_connection(self, websocket: WebSocket, agent_id: str) -> None:
        """
        Handle new agent connection.
        
        Args:
            websocket: WebSocket connection
            agent_id: Agent identifier
        """
        # Accept connection
        await websocket.accept()
        logger.info("a2a_connection_accepted", agent_id=agent_id)
        
        # Register agent
        agent_info = AgentInfo(id=agent_id, websocket=websocket)
        async with self._lock:
            self.agents[agent_id] = agent_info
        
        await self.event_mesh.register(agent_id, websocket)
        
        # Send handshake response
        await websocket.send_json({
            "type": MessageType.HANDSHAKE.value,
            "status": "ok",
            "agent_id": agent_id,
            "timestamp": datetime.utcnow().isoformat(),
            "server": "heretek-swarm-a2a"
        })
        
        # Log connection
        self._log_message({
            "type": "connection",
            "agent_id": agent_id,
            "action": "connected",
            "timestamp": datetime.utcnow().isoformat()
        })
        
        try:
            # Message loop
            while True:
                try:
                    data = await websocket.receive_json()
                    await self._handle_message(agent_id, data)
                except json.JSONDecodeError as e:
                    logger.error("a2a_invalid_json", agent_id=agent_id, error=str(e))
                    await websocket.send_json({
                        "type": MessageType.ERROR.value,
                        "error": f"Invalid JSON: {str(e)}"
                    })
        except WebSocketDisconnect:
            logger.info("a2a_agent_disconnected", agent_id=agent_id)
        finally:
            await self._cleanup_agent(agent_id)
    
    async def _handle_message(self, agent_id: str, data: dict) -> None:
        """
        Handle incoming message from agent.
        
        Args:
            agent_id: Sending agent
            data: Message data
        """
        msg_type = data.get("type", "message")
        logger.debug("a2a_message_received", agent_id=agent_id, type=msg_type)
        
        # Update last activity
        async with self._lock:
            if agent_id in self.agents:
                self.agents[agent_id].last_activity = datetime.utcnow()
        
        # Route by message type
        if msg_type == MessageType.HANDSHAKE.value:
            await self._handle_handshake(agent_id, data)
        elif msg_type == MessageType.DISCOVERY.value:
            await self._handle_discovery(agent_id, data)
        elif msg_type == MessageType.MESSAGE.value:
            await self._handle_message_broadcast(agent_id, data)
        elif msg_type == MessageType.PROPOSAL.value:
            await self._handle_proposal(agent_id, data)
        elif msg_type == MessageType.VOTE.value:
            await self._handle_vote(agent_id, data)
        else:
            logger.warning("a2a_unknown_message_type", type=msg_type)
    
    async def _handle_handshake(self, agent_id: str, data: dict) -> None:
        """Handle handshake message."""
        logger.info("a2a_handshake", agent_id=agent_id)
        # Already handled in connection setup
    
    async def _handle_discovery(self, agent_id: str, data: dict) -> None:
        """
        Handle discovery request - return list of all agents.
        
        Args:
            agent_id: Requesting agent
            data: Request data
        """
        async with self._lock:
            agents_list = [
                {
                    "id": aid,
                    "status": info.status,
                    "connected_at": info.connected_at.isoformat(),
                    "last_activity": info.last_activity.isoformat()
                }
                for aid, info in self.agents.items()
            ]
        
        response = {
            "type": MessageType.DISCOVERY.value,
            "agents": agents_list,
            "count": len(agents_list),
            "timestamp": datetime.utcnow().isoformat()
        }
        
        await self.event_mesh.send_to_json(agent_id, response)
    
    async def _handle_message_broadcast(self, sender_id: str, data: dict) -> None:
        """
        Handle message broadcast to all agents.
        
        Args:
            sender_id: Sending agent
            data: Message with content
        """
        message = {
            "type": MessageType.MESSAGE.value,
            "from": sender_id,
            "content": data.get("content"),
            "metadata": data.get("metadata", {}),
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Broadcast to all except sender
        await self.event_mesh.broadcast_json(message)
        
        # Log message
        self._log_message(message)
    
    async def _handle_proposal(self, agent_id: str, data: dict) -> None:
        """
        Handle consensus proposal.
        
        Args:
            agent_id: Proposing agent
            data: Proposal data
        """
        proposal = {
            "type": MessageType.PROPOSAL.value,
            "id": data.get("id", f"proposal_{datetime.utcnow().timestamp()}"),
            "from": agent_id,
            "action": data.get("action"),
            "details": data.get("details", {}),
            "timestamp": datetime.utcnow().isoformat()
        }
        
        logger.info("a2a_proposal_created", proposal_id=proposal["id"], agent_id=agent_id)
        
        # Broadcast to all agents
        await self.event_mesh.broadcast_json(proposal)
        
        # Log
        self._log_message(proposal)
    
    async def _handle_vote(self, agent_id: str, data: dict) -> None:
        """
        Handle consensus vote.
        
        Args:
            agent_id: Voting agent
            data: Vote data
        """
        vote = {
            "type": MessageType.VOTE.value,
            "proposal_id": data.get("proposal_id"),
            "from": agent_id,
            "vote": data.get("vote"),  # "yes", "no", "abstain"
            "reason": data.get("reason", ""),
            "timestamp": datetime.utcnow().isoformat()
        }
        
        logger.info("a2a_vote_cast", proposal_id=vote["proposal_id"], vote=vote["vote"])
        
        # Broadcast vote
        await self.event_mesh.broadcast_json(vote)
        
        # Log
        self._log_message(vote)
    
    async def _cleanup_agent(self, agent_id: str) -> None:
        """
        Cleanup agent connection.
        
        Args:
            agent_id: Agent to cleanup
        """
        async with self._lock:
            if agent_id in self.agents:
                del self.agents[agent_id]
        
        await self.event_mesh.unregister(agent_id)
        
        # Log disconnection
        self._log_message({
            "type": "connection",
            "agent_id": agent_id,
            "action": "disconnected",
            "timestamp": datetime.utcnow().isoformat()
        })
    
    def _log_message(self, message: dict) -> None:
        """
        Log message to internal log with size limit.
        
        Args:
            message: Message to log
        """
        self._message_log.append(message)
        
        # Trim if over limit
        if len(self._message_log) > self._max_log_size:
            self._message_log = self._message_log[-self._max_log_size:]
    
    def get_message_log(self, limit: int = 100) -> List[Dict]:
        """Get recent message log."""
        return self._message_log[-limit:]
    
    def get_statistics(self) -> dict:
        """Get server statistics."""
        return {
            "connected_agents": len(self.agents),
            "agent_ids": list(self.agents.keys()),
            "message_log_size": len(self._message_log),
            "uptime": "active"
        }
