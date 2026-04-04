"""
State Management System for Heretek Swarm

Provides comprehensive state management including:
- Message lineage tracking
- State snapshots with versioning
- Rollback and replay capabilities
- Distributed state synchronization

Integrates with the Dual-Tier Memory System for persistence.
"""

from .base import (
    StateSnapshot,
    MessageLineage,
    StateTransition,
    AgentState,
    ConversationState,
    SystemState
)
from .lineage import LineageTracker, LineageConfig
from .snapshots import SnapshotManager, SnapshotConfig
from .manager import StateManager, StateConfig

__all__ = [
    "StateSnapshot",
    "MessageLineage",
    "StateTransition",
    "AgentState",
    "ConversationState",
    "SystemState",
    "LineageTracker",
    "LineageConfig",
    "SnapshotManager",
    "SnapshotConfig",
    "StateManager",
    "StateConfig",
]

__version__ = "0.1.0"
