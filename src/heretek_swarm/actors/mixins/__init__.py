"""
Mixins package for shared actor behaviors.

Provides extracted mixin classes for common actor functionalities:
- DeliberationMixin: Swarm deliberation consensus methods
- PatternMixin: Collective pattern emission/consumption
- MemoryMixin: Memory access tracking and tier management
- LearningMixin: Collective learning status reporting
"""

from heretek_swarm.actors.mixins.deliberation import DeliberationMixin
from heretek_swarm.actors.mixins.learning import LearningMixin
from heretek_swarm.actors.mixins.memory import MemoryMixin
from heretek_swarm.actors.mixins.pattern import PatternMixin

__all__ = [
    "DeliberationMixin",
    "PatternMixin",
    "MemoryMixin",
    "LearningMixin",
]
