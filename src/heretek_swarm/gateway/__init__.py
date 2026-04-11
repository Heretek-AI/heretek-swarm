"""
Heretek Swarm Gateway

EventMesh + A2A Protocol Server for agent communication.
"""

from .a2a_server import A2AServer, AgentInfo, MessageType
from .auth import generate_api_key, get_api_key_from_env, optional_auth, verify_auth
from .event_mesh import EventMesh

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
