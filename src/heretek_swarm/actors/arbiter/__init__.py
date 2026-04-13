"""
Arbiter subpackage - Split module for arbiter agent.

Modules:
- core: Core arbitration logic, conflict detection, enums, dataclasses
- handlers: Event handlers and responses
- strategies: Resolution strategies
- constants: Constants for the arbiter
"""

from .core import (
    ConflictType,
    ConflictSeverity,
    ResolutionStrategy,
    ResolutionStatus,
    Conflict,
    Relationship,
    ArbitrationReport,
    ArbiterAgent,
)

# Alias for backwards compatibility
ArbitrationStrategy = ResolutionStrategy

__all__ = [
    "ConflictType",
    "ConflictSeverity",
    "ResolutionStrategy",
    "ResolutionStatus",
    "ArbitrationStrategy",
    "Conflict",
    "Relationship",
    "ArbitrationReport",
    "ArbiterAgent",
]
