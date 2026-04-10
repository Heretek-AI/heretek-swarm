"""
Heretek Swarm State Package

Provides state persistence, management, and lineage tracking.

IMPORTANT: This package imports legacy state modules from src/state/.
These legacy modules (base.py, manager.py, snapshots.py, lineage.py)
provide the lineage tracking and snapshot functionality.
"""

import sys
from pathlib import Path

# Add parent src/ to path for legacy state modules
_legacy_state_path = Path(__file__).parent.parent.parent
if str(_legacy_state_path) not in sys.path:
    sys.path.insert(0, str(_legacy_state_path))

import structlog

logger = structlog.get_logger("state.init")

from heretek_swarm.state.repository import (
    StateRepository,
    AgentStateRecord,
    StateCheckpoint,
    ConcurrencyError,
)

# Import from src/state/ (legacy location)
try:
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
except ImportError as e:
    # Fallback: try importing directly from sibling module
    from heretek_swarm.state.repository import StateRepository
    logger = structlog.get_logger("state.init")
    logger.warning("legacy_state_import_fallback", error=str(e))
    StateSnapshot = MessageLineage = StateTransition = AgentState = ConversationState = SystemState = StateStatus = TransitionType = MessageType = None

try:
    from state.manager import (
        LineageTracker,
        LineageConfig,
        SnapshotManager,
        StateManager,
        StateConfig,
    )
except ImportError:
    LineageTracker = LineageConfig = SnapshotManager = StateManager = StateConfig = None

try:
    from state.snapshots import (
        SnapshotConfig,
    )
except ImportError:
    SnapshotConfig = None

try:
    from state.lineage import (
        LineageConfig,
        LineageNode,
    )
except ImportError:
    LineageConfig = LineageNode = None

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
