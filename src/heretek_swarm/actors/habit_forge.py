"""
Habit-Forge Agent - Backward Compatibility Module.

This module exists for backward compatibility. All exports have been moved to
the habit_forge/ directory. Import from the new location:

    from heretek_swarm.actors.habit_forge import HabitForgeAgent, HabitStage, ...

Or import directly from specific modules:

    from heretek_swarm.actors.habit_forge.agent import HabitForgeAgent
    from heretek_swarm.actors.habit_forge.types import (
        HabitStage,
        ReinforcementType,
        Habit,
        BehavioralPattern,
    )
    from heretek_swarm.actors.habit_forge.tracking import HabitForgeTrackingMixin
    from heretek_swarm.actors.habit_forge.streaks import HabitForgeStreaksMixin

This module will be removed in a future version.
"""

# Re-export everything from the new module structure for backward compatibility
from heretek_swarm.actors.habit_forge import (
    BehavioralPattern,
    Habit,
    HabitForgeAgent,
    HabitForgeStreaksMixin,
    HabitForgeTrackingMixin,
    HabitStage,
    ReinforcementType,
    calculate_longest_streak,
    get_stage_for_adherence,
    is_within_streak_threshold,
    should_reset_streak,
    summarize_habit_progress,
    validate_habit_fields,
)

__all__ = [
    "BehavioralPattern",
    "Habit",
    "HabitForgeAgent",
    "HabitForgeStreaksMixin",
    "HabitForgeTrackingMixin",
    "HabitStage",
    "ReinforcementType",
    "calculate_longest_streak",
    "get_stage_for_adherence",
    "is_within_streak_threshold",
    "should_reset_streak",
    "summarize_habit_progress",
    "validate_habit_fields",
]
