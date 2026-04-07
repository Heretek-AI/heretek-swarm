"""
Heretek Swarm State Package

Provides state persistence, management, and lineage tracking.
"""

from heretek_swarm.state.repository import (
    StateRepository,
    AgentStateRecord,
    StateCheckpoint,
    ConcurrencyError,
)

from state.base import (
    StateSnapshot,
    MessageLineage,
    StateTransition,
    AgentState,
    ConversationState,
    SystemState,
    StateStatus,
    TransitionType,
    MessageType,
)

from state.manager import (
    LineageTracker,
    LineageConfig,
    SnapshotManager,
    StateManager,
    StateConfig,
)

from state.snapshots import (
    SnapshotConfig,
)

from state.lineage import (
    LineageConfig,
    LineageNode,
    LineageTracker as LineageTrackerAlt,
)

__all__ = [
    # Repository
    "StateRepository",
    "AgentStateRecord",
    "StateCheckpoint",
    "ConcurrencyError",
    # Base models
    "StateSnapshot",
    "MessageLineage",
    "StateTransition",
    "AgentState",
    "ConversationState",
    "SystemState",
    "StateStatus",
    "TransitionType",
    "MessageType",
    # Managers
    "LineageTracker",
    "LineageConfig",
    "SnapshotManager",
    "StateManager",
    "StateConfig",
    "SnapshotConfig",
    "LineageNode",
]
