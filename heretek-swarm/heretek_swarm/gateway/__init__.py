"""
Heretek Swarm Gateway

EventMesh + A2A Protocol Server for agent communication.
"""

from .a2a_server import A2AServer, AgentInfo, MessageType
from .auth import generate_api_key, get_api_key_from_env, optional_auth, verify_auth
from .event_mesh import EventMesh
from .nats_event_mesh import (
    ActorBridgeConfig,
    NATSEventMesh,
    NATStoActorBridge,
    get_nats_bridge,
    init_nats_bridge,
    shutdown_nats_bridge,
)

__all__ = [
    "A2AServer",
    "AgentInfo",
    "EventMesh",
    "MessageType",
    "generate_api_key",
    "get_api_key_from_env",
    "optional_auth",
    "verify_auth",
    # NATS bridge
    "NATSEventMesh",
    "NATStoActorBridge",
    "ActorBridgeConfig",
    "get_nats_bridge",
    "init_nats_bridge",
    "shutdown_nats_bridge",
]
