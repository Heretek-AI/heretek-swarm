"""
Heretek Swarm State Package

Compatibility shim for test imports.
Re-exports from src/state/ package.
"""

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
    "StateSnapshot",
    "MessageLineage",
    "StateTransition",
    "AgentState",
    "ConversationState",
    "SystemState",
    "StateStatus",
    "TransitionType",
    "MessageType",
    "LineageTracker",
    "LineageConfig",
    "SnapshotManager",
    "SnapshotConfig",
    "StateManager",
    "StateConfig",
    "LineageNode",
]
