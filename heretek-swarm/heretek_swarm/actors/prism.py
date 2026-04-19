"""
Prism Agent - Backward Compatibility Module.

This module exists for backward compatibility. All exports have been moved to
the prism/ directory. Import from the new location:

    from heretek_swarm.actors.prism import PrismAgent, PerspectiveType, ...

Or import directly from specific modules:

    from heretek_swarm.actors.prism.agent import PrismAgent
    from heretek_swarm.actors.prism.types import PerspectiveType, BiasType, ...
    from heretek_swarm.actors.prism.transforms import PrismTransforms

This module will be removed in a future version.
"""

# Re-export everything from the new module structure for backward compatibility
from heretek_swarm.actors.prism import (
    AnalyticalFramework,
    BiasDetection,
    BiasType,
    Perspective,
    PerspectiveType,
    PrismAgent,
    PrismTransforms,
    apply_framework_fallback,
    detect_biases_heuristic,
    generate_heuristic_perspective,
    generate_reframe_fallback,
    generate_stakeholder_map_fallback,
    get_framework_prompt,
)

__all__ = [
    "PerspectiveType",
    "BiasType",
    "AnalyticalFramework",
    "Perspective",
    "BiasDetection",
    "PrismAgent",
    "PrismTransforms",
    "generate_heuristic_perspective",
    "detect_biases_heuristic",
    "get_framework_prompt",
    "apply_framework_fallback",
    "generate_stakeholder_map_fallback",
    "generate_reframe_fallback",
]
