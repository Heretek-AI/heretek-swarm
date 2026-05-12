"""
Chronos Module - Temporal & Scheduling Specialist.

This module has been refactored from a single chronos.py file into
a package with separate components:

- types.py: Type definitions (ScheduleStatus, RecurrenceType, Priority,
            ScheduledTask, Deadline)
- scheduler.py: ChronosSchedulerMixin with 5 scheduling methods
- handlers.py: ChronosHandlersMixin with 10 message handlers
- agent.py: ChronosAgent class

For backward compatibility, all public exports are available from this module.

INTG-04: Time perception & dilation integration included.
"""

from __future__ import annotations

# Re-export types from types.py
from heretek_swarm.actors.chronos.types import (
    Deadline,
    Priority,
    RecurrenceType,
    ScheduleStatus,
    ScheduledTask,
    Tick,
)

# Re-export agent from agent.py
from heretek_swarm.actors.chronos.agent import ChronosAgent

# Re-export mixins
from heretek_swarm.actors.chronos.handlers import ChronosHandlersMixin
from heretek_swarm.actors.chronos.scheduler import ChronosSchedulerMixin

__all__ = [
    # Enums
    "ScheduleStatus",
    "RecurrenceType",
    "Priority",
    # Dataclasses
    "ScheduledTask",
    "Deadline",
    "Tick",
    # Agent
    "ChronosAgent",
    # Mixins
    "ChronosSchedulerMixin",
    "ChronosHandlersMixin",
]
