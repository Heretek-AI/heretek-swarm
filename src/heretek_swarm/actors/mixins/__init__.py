"""
Actors Mixins Package

Provides shared behavior mixins for actor classes. These mixins extract
common functionality that was previously duplicated across all actor classes.

Mixins:
    DeliberationMixin: Methods for deliberation and consensus participation
    PatternMixin: Pattern emission and consumption methods
    MemoryMixin: Memory access and tier management
    LearningMixin: Learning status and adaptation methods

Usage:
    ```python
    from heretek_swarm.actors.mixins import (
        DeliberationMixin,
        PatternMixin,
        MemoryMixin,
        LearningMixin,
    )

    class MyAgent(DeliberationMixin, PatternMixin, MemoryMixin, LearningMixin):
        pass
    ```

Version: 1.44.0
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
