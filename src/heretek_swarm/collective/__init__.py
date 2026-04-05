"""
Agent Society Module

Provides collective intelligence capabilities for Heretek Swarm including:
- Hierarchical agent coordination
- Collective decision-making
- Emergent behavior detection
- Shared collective memory
- Swarm optimization algorithms
"""

from .society import (
    AgentSociety,
    CollectiveMemory,
    CollectiveTask,
    CollectiveResult,
    CollectiveTaskType,
    SocietyRole,
    EmergentBehavior,
    AgentContribution,
)

__all__ = [
    "AgentSociety",
    "CollectiveMemory",
    "CollectiveTask",
    "CollectiveResult",
    "CollectiveTaskType",
    "SocietyRole",
    "EmergentBehavior",
    "AgentContribution",
]
