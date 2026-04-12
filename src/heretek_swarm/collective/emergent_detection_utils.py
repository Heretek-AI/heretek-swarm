"""Utility functions for emergent detection."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .emergent_detection import (
        AgentBehaviorSnapshot,
        CollectiveBehavior,
        EmergenceLevel,
        EmergentPattern,
        EmergentPatternClass,
    )


def calculate_window_metrics(window: list[AgentBehaviorSnapshot]) -> dict[str, float]:
    """Calculate metrics for a temporal window of agent snapshots."""
    if not window:
        return {}

    return {
        "avg_success_rate": sum(s.success_rate for s in window) / len(window),
        "avg_interaction_count": sum(s.interaction_count for s in window) / len(window),
        "unique_agents": len({s.agent_id for s in window}),
        "total_interactions": sum(s.interaction_count for s in window),
    }


def calculate_shift_score(
    prev_metrics: dict[str, float],
    curr_metrics: dict[str, float],
) -> float:
    """Calculate the shift score between two metric sets."""
    if not prev_metrics or not curr_metrics:
        return 0.0

    shifts = []
    for key in prev_metrics:
        if key in curr_metrics and prev_metrics[key] != 0:
            change = abs(curr_metrics[key] - prev_metrics[key]) / prev_metrics[key]
            shifts.append(change)

    if not shifts:
        return 0.0

    return sum(shifts) / len(shifts)


def classify_emergence_level(score: float) -> EmergenceLevel:
    """Classify the emergence level based on score."""
    if score >= 0.8:
        return EmergenceLevel.CRITICAL
    if score >= 0.6:
        return EmergenceLevel.STRONG
    if score >= 0.4:
        return EmergenceLevel.MODERATE
    return EmergenceLevel.WEAK


def measure_collective_capability(behaviors: list[CollectiveBehavior]) -> float:
    """Measure collective capability from behaviors."""
    if not behaviors:
        return 0.0

    weighted_sum = sum(b.coherence * b.intensity for b in behaviors)
    return weighted_sum / len(behaviors)


def calculate_temporal_span(behaviors: list[CollectiveBehavior]) -> float:
    """Calculate the temporal span of behaviors in seconds."""
    if not behaviors:
        return 0.0

    times = []
    for b in behaviors:
        times.append(datetime.fromisoformat(b.start_time))
        if b.end_time:
            times.append(datetime.fromisoformat(b.end_time))

    if len(times) < 2:
        return 0.0

    return (max(times) - min(times)).total_seconds()


def calculate_statistical_significance(pattern: EmergentPattern) -> float:
    """Calculate statistical significance of an emergent pattern."""
    n_agents = len(pattern.participating_agents)
    emergence_score = pattern.emergence_score

    significance = 1.0 / (n_agents * (1.0 - emergence_score + 0.01))
    return min(significance, 1.0)


def calculate_confidence(pattern: EmergentPattern) -> float:
    """Calculate confidence score for an emergent pattern."""
    factors = []
    factors.append(pattern.emergence_score)
    agent_factor = min(len(pattern.participating_agents) / 10.0, 1.0)
    factors.append(agent_factor)
    factors.append(1.0 if pattern.is_validated else 0.5)
    ratio_factor = min(pattern.emergence_ratio / 2.0, 1.0) if pattern.emergence_ratio > 0 else 0
    factors.append(ratio_factor)

    return sum(factors) / len(factors)


def calculate_impact_score(pattern: EmergentPattern) -> float:
    """Calculate impact score for an emergent pattern."""
    level_impact = {
        EmergenceLevel.WEAK: 0.2,
        EmergenceLevel.MODERATE: 0.4,
        EmergenceLevel.STRONG: 0.6,
        EmergenceLevel.CRITICAL: 0.8,
    }
    base_impact = level_impact.get(pattern.emergence_level, 0.2)

    positive_patterns = [
        EmergentPatternClass.COORDINATION,
        EmergentPatternClass.OPTIMIZATION,
        EmergentPatternClass.INNOVATION,
        EmergentPatternClass.SELF_ORGANIZATION,
        EmergentPatternClass.ADAPTATION,
    ]

    negative_patterns = [
        EmergentPatternClass.CASCADE,
        EmergentPatternClass.PHASE_TRANSITION,
    ]

    if pattern.pattern_class in positive_patterns:
        class_modifier = 1.0
    elif pattern.pattern_class in negative_patterns:
        class_modifier = -0.5
    elif pattern.pattern_class == EmergentPatternClass.RESONANCE:
        if pattern.emergence_ratio > 1.5:
            class_modifier = 0.8
        elif pattern.emergence_ratio < 0.5:
            class_modifier = -0.3
        else:
            class_modifier = 0.3
    else:
        class_modifier = 0.0

    confidence_modifier = pattern.confidence * 0.2
    frequency_modifier = min(0.2, pattern.frequency * 0.02)

    impact = (base_impact * class_modifier) + confidence_modifier + frequency_modifier
    return max(-1.0, min(1.0, impact))


def generate_recommended_action(pattern: EmergentPattern) -> str | None:
    """Generate recommended action based on impact score."""
    impact_score = calculate_impact_score(pattern)

    if impact_score >= 0.7:
        return "REINFORCE: High-value emergent pattern detected. Consider reinforcing conditions that enabled this behavior."
    if impact_score >= 0.3:
        return "MONITOR: Beneficial pattern detected. Document conditions for future replication."
    if impact_score >= -0.3:
        return "OBSERVE: Neutral emergence. Continue monitoring for changes."
    if impact_score >= -0.7:
        return "INVESTIGATE: Potentially harmful pattern. Analyze root causes and consider intervention."
    return "ALERT: Harmful emergent pattern detected. Immediate intervention recommended."