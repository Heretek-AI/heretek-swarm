"""
Chronos Agent - Temporal & Scheduling Specialist.

Backward-compatibility shim for chronos.py.
All imports are re-exported from the chronos/ module directory.

INTG-04: Time perception & dilation integration preserved.
"""

# Re-export everything from the module directory for backward compatibility
from heretek_swarm.actors.chronos import (
    # Enums
    Priority,
    RecurrenceType,
    ScheduleStatus,
    # Dataclasses
    Deadline,
    ScheduledTask,
    # Agent
    ChronosAgent,
    # Mixins
    ChronosHandlersMixin,
    ChronosSchedulerMixin,
)

__all__ = [
    # Enums
    "ScheduleStatus",
    "RecurrenceType",
    "Priority",
    # Dataclasses
    "ScheduledTask",
    "Deadline",
    # Agent
    "ChronosAgent",
    # Mixins
    "ChronosSchedulerMixin",
    "ChronosHandlersMixin",
]
