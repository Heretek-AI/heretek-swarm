"""
Backward-compatible wrapper for AgentActor base class.

This module re-exports all classes and methods from the split modules:
- heretek_swarm.actors.base.core
- heretek_swarm.actors.base.state_management
- heretek_swarm.actors.base.message_handling

All existing imports will continue to work after the split.
"""

# Re-export from core module
from heretek_swarm.actors.base.core import (
    ActorMessage,
    ActorState,
    ActorStatus,
    AgentActor,
)

# Re-export message handling methods (bound to AgentActor)
from heretek_swarm.actors.base.message_handling import (
    AgentActorMessageHandling,
)

# Re-export state management methods (bound to AgentActor)
from heretek_swarm.actors.base.state_management import (
    AgentActorStateManagement,
)

__all__ = [
    "ActorMessage",
    "ActorState",
    "ActorStatus",
    "AgentActor",
    "AgentActorMessageHandling",
    "AgentActorStateManagement",
]
