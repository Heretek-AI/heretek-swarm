"""
Heretek Swarm Gateway Module

Provides agent-to-agent communication infrastructure:
- EventMesh: Message bus with null-safety handling
- A2A Protocol: WebSocket-based messaging protocol on port 18789
- Auth: API key authentication for secure connections
"""

from heretek_swarm.gateway.event_mesh import EventMesh, ClientConnection, AgentInfo, ConnectionState
from heretek_swarm.gateway.a2a_protocol import A2AProtocol, MessageType, MESSAGE_TYPES, PROTOCOL_VERSION
from heretek_swarm.gateway.auth import (
    APIKeyManager,
    AuthMiddleware,
    WebSocketAuthMiddleware,
    AuthLevel,
    AuthResult,
    get_key_manager,
    get_auth_middleware
)

__all__ = [
    # EventMesh
    "EventMesh",
    "ClientConnection", 
    "AgentInfo",
    "ConnectionState",
    # A2A Protocol
    "A2AProtocol",
    "MessageType",
    "MESSAGE_TYPES",
    "PROTOCOL_VERSION",
    # Auth
    "APIKeyManager",
    "AuthMiddleware",
    "WebSocketAuthMiddleware",
    "AuthLevel",
    "AuthResult",
    "get_key_manager",
    "get_auth_middleware",
]