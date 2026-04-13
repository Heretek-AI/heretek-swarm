"""
Arbiter Agent - Conflict Resolution & Dispute Mediation.

The Arbiter provides:
- Inter-agent conflict detection and resolution
- Dispute mediation and arbitration
- Consensus facilitation
- Resource contention management
- Priority-based task arbitration
- Relationship health monitoring

The Arbiter is the "peacekeeper" of the Collective, ensuring harmonious
multi-agent coordination and resolving conflicts before they escalate.

This module provides backwards-compatible imports from submodules:
- actors.arbiter.core: Core arbitration logic, enums, dataclasses
- actors.arbiter.handlers: Message handlers
- actors.arbiter.strategies: Resolution strategies
"""

# Re-export core components for backwards compatibility
from heretek_swarm.actors.arbiter.core import (
    # Agent class
    ArbiterAgent,
    ArbitrationReport,
    # Dataclasses
    Conflict,
    ConflictSeverity,
    # Enums
    ConflictType,
    Relationship,
    ResolutionStatus,
    ResolutionStrategy,
)

# Resolution strategy enum is also exported directly for convenience
# (originally defined in core but used as ArbitrationStrategy in some places)
ArbitrationStrategy = ResolutionStrategy

__all__ = [
    # Enums
    "ConflictType",
    "ConflictSeverity",
    "ResolutionStrategy",
    "ResolutionStatus",
    "ArbitrationStrategy",
    # Dataclasses
    "Conflict",
    "Relationship",
    "ArbitrationReport",
    # Agent class
    "ArbiterAgent",
]
