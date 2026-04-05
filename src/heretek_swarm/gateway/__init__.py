"""
Heretek Swarm Gateway

EventMesh + A2A Protocol Server for agent communication.
"""

from .event_mesh import EventMesh
from .a2a_server import A2AServer, MessageType, AgentInfo
from .auth import verify_auth, optional_auth, get_api_key_from_env, generate_api_key

__all__ = [
    "EventMesh",
    "A2AServer",
    "MessageType",
    "AgentInfo",
    "verify_auth",
    "optional_auth",
    "get_api_key_from_env",
    "generate_api_key",
]
