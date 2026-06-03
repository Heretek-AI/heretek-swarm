"""
Immune-response system — anomaly detection and pattern preservation.

This module re-exports the public surface of the immune-response
engine from its historical location. The engine is anomaly detection
and pattern learning, not a consensus algorithm; it was previously
sitting in :mod:`heretek_swarm.consensus.immune` (PLAN.md §1.12
"4 consensus algorithms + immune" — immune is misfiled).

Phase 2.5 of PLAN.md moves it under the security umbrella where the
Sentinel / Sentinel-Prime / Arbiter mixins already consume it
(:mod:`heretek_swarm.actors.sentinel.immune`,
:mod:`heretek_swarm.actors.sentinel.anomaly`,
:mod:`heretek_swarm.actors.sentinel.agent`).

Backwards compatibility is preserved: ``from
heretek_swarm.consensus.immune import …`` keeps working because the
original module is now a thin re-export shim.
"""

from __future__ import annotations

from heretek_swarm.consensus.immune import (  # noqa: F401
    AnomalyResponse,
    ImmuneLearningResult,
    ImmunePattern,
    ImmuneQuorum,
    ImmuneResponse,
    ImmuneResponseBuilding,
    ImmuneResponseEngine,
    ImmuneStatus,
    NovelPatternPreservation,
    PatternClassification,
    ResponseAction,
    ResponseOutcome,
)

__all__ = [
    "AnomalyResponse",
    "ImmuneLearningResult",
    "ImmunePattern",
    "ImmuneQuorum",
    "ImmuneResponse",
    "ImmuneResponseBuilding",
    "ImmuneResponseEngine",
    "ImmuneStatus",
    "NovelPatternPreservation",
    "PatternClassification",
    "ResponseAction",
    "ResponseOutcome",
]
