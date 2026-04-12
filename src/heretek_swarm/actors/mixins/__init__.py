"""Actor mixins for reusable functionality.

These mixins extract common patterns from actor files to reduce duplication.
"""

from .deliberation import DeliberationMixin
from .health_reporting import HealthReportingMixin
from .learning import LearningMixin
from .memory import MemoryMixin
from .memory_access import MemoryAccessMixin
from .pattern import PatternMixin
from .pattern_consumer import PatternConsumerMixin
from .tribunal import TribunalMixin

__all__ = [
    "DeliberationMixin",
    "HealthReportingMixin",
    "LearningMixin",
    "MemoryMixin",
    "MemoryAccessMixin",
    "PatternMixin",
    "PatternConsumerMixin",
    "TribunalMixin",
]
