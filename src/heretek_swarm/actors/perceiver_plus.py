"""
Perceiver+ Agent - Backward Compatibility Module.

This module exists for backward compatibility. All exports have been moved to
the perceiver_plus/ directory. Import from the new location:

    from heretek_swarm.actors.perceiver_plus import PerceiverPlusAgent, AnalyticsType, ...

Or import directly from specific modules:

    from heretek_swarm.actors.perceiver_plus.agent import PerceiverPlusAgent
    from heretek_swarm.actors.perceiver_plus.types import (
        AnalyticsType,
        DataModality,
        StatisticalTest,
        AnalyticsResult,
        TrendAnalysis,
        CorrelationMatrix,
    )
    from heretek_swarm.actors.perceiver_plus.analytics import (
        PerceiverAnalyticsMixin,
        PerceiverAnalyticsMixinImpl,
    )

This module will be removed in a future version.
"""

# Re-export everything from the new module structure for backward compatibility
from heretek_swarm.actors.perceiver_plus import (
    AnalyticsResult,
    AnalyticsType,
    CorrelationMatrix,
    DataModality,
    PerceiverAnalyticsMixin,
    PerceiverAnalyticsMixinImpl,
    PerceiverPlusAgent,
    StatisticalTest,
    TrendAnalysis,
)

__all__ = [
    # Agent
    "PerceiverPlusAgent",
    # Types (enums and data classes)
    "AnalyticsResult",
    "AnalyticsType",
    "CorrelationMatrix",
    "DataModality",
    "StatisticalTest",
    "TrendAnalysis",
    # Mixins
    "PerceiverAnalyticsMixin",
    "PerceiverAnalyticsMixinImpl",
]