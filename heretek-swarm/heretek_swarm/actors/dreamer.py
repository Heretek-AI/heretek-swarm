"""
Dreamer Agent - Backward Compatibility Module.

This module exists for backward compatibility. All exports have been moved to
the dreamer/ directory. Import from the new location:

    from heretek_swarm.actors.dreamer import DreamerAgent, CreativityTechnique, ...

Or import directly from specific modules:

    from heretek_swarm.actors.dreamer.agent import DreamerAgent
    from heretek_swarm.actors.dreamer.types import (
        CreativityTechnique,
        IdeaCategory,
        NoveltyLevel,
        CreativeIdea,
        CreativeSession,
    )
    from heretek_swarm.actors.dreamer.generators import DreamerGeneratorsMixin

This module will be removed in a future version.
"""

# Re-export everything from the new module structure for backward compatibility
from heretek_swarm.actors.dreamer import (
    CreativityTechnique,
    CreativeIdea,
    CreativeSession,
    DreamerAgent,
    DreamerGeneratorsMixin,
    IdeaCategory,
    InnovationReport,
    NoveltyLevel,
    calculate_innovation_score,
    get_technique_prompt,
)

__all__ = [
    "CreativityTechnique",
    "CreativeIdea",
    "CreativeSession",
    "DreamerAgent",
    "DreamerGeneratorsMixin",
    "IdeaCategory",
    "InnovationReport",
    "NoveltyLevel",
    "calculate_innovation_score",
    "get_technique_prompt",
]
