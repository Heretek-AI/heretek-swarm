"""Tests for the ``Tick`` type and ``ChronosSchedulerMixin.generate_ticks()``.

Covers five scenarios:

1. Empty task queue returns ``[]``.
2. A single due PENDING task produces one ``Tick`` and the source task
   advances to ACTIVE.
3. Multiple due tasks return ticks ordered by ``scheduled_at``.
4. PENDING tasks that are *not yet due* are left in the queue and not
   emitted as ticks.
5. Already-ACTIVE or COMPLETED tasks are not emitted and stay in the
   queue (``_run_scheduler`` decides their life cycle).
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock

import pytest

from heretek_swarm.actors.chronos.scheduler import ChronosSchedulerMixin
from heretek_swarm.actors.chronos.types import (
    ScheduleStatus,
    ScheduledTask,
    Tick,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_mixin(**overrides: object) -> ChronosSchedulerMixin:
    """Build a ``ChronosSchedulerMixin`` instance with mock collaborators.

    Patches ``_task_queue`` and ``_tasks`` so that ``generate_ticks()``
    can operate without a full ``ChronosAgent``.
    """
    mixin = ChronosSchedulerMixin.__new__(ChronosSchedulerMixin)
    mixin._task_queue = overrides.pop("_task_queue", [])
    mixin._tasks = overrides.pop("_tasks", {})
    mixin.agent_id = overrides.pop("agent_id", "test-chronos")

    # Allow consumers to patch additional attributes
    for key, value in overrides.items():
        setattr(mixin, key, value)

    # Satisfy typing — ChronosSchedulerMixin has __init__ via cooperative MRO
    object.__init__(mixin)

    return mixin


def _make_task(
    task_id: str,
    scheduled_at: datetime | None = None,
    status: ScheduleStatus = ScheduleStatus.PENDING,
    target_agents: list[str] | None = None,
    action: str = "test_action",
) -> ScheduledTask:
    """Create a ``ScheduledTask`` with minimal fields for testing."""
    return ScheduledTask(
        task_id=task_id,
        name=f"Task {task_id}",
        description="",
        scheduled_at=scheduled_at or datetime.now(UTC),
        status=status,
        target_agents=target_agents if target_agents is not None else ["alpha"],
        action=action,
    )


_NOW = datetime.now(UTC)
_FIVE_SECS_AGO = _NOW - timedelta(seconds=5)
_IN_TEN_SECS = _NOW + timedelta(seconds=10)


# =========================================================================
# Tick type
# =========================================================================


class TestTickDataclass:
    """Structural checks for the ``Tick`` dataclass."""

    @staticmethod
    def test_tick_fields() -> None:
        tick = Tick(
            tick_id="tick-1",
            agent_id="alpha",
            action="ping",
            scheduled_at=_NOW,
            status=ScheduleStatus.PENDING,
        )
        assert tick.tick_id == "tick-1"
        assert tick.agent_id == "alpha"
        assert tick.action == "ping"
        assert tick.status == ScheduleStatus.PENDING

    @staticmethod
    def test_tick_default_status() -> None:
        tick = Tick(tick_id="t-1", agent_id="a", action="x", scheduled_at=_NOW)
        assert tick.status == ScheduleStatus.PENDING

    @staticmethod
    def test_tick_to_dict() -> None:
        tick = Tick(
            tick_id="tick-1",
            agent_id="alpha",
            action="ping",
            scheduled_at=_NOW,
            status=ScheduleStatus.PENDING,
        )
        d = tick.to_dict()
        assert d["tick_id"] == "tick-1"
        assert d["agent_id"] == "alpha"
        assert d["action"] == "ping"
        assert d["status"] == "pending"
        assert "scheduled_at" in d


# =========================================================================
# Contract 1 — Empty queue
# =========================================================================


class TestEmptyQueue:
    """``generate_ticks()`` returns ``[]`` when the queue is empty."""

    @staticmethod
    async def test_empty_queue_returns_empty_list() -> None:
        mixin = _make_mixin()
        ticks = await mixin.generate_ticks()
        assert ticks == []


# =========================================================================
# Contract 2 — Single due task
# =========================================================================


class TestSingleDueTask:
    """A single PENDING due task produces one Tick and is advanced to
    ACTIVE."""

    @staticmethod
    async def test_single_due_task_produces_tick() -> None:
        task = _make_task("t1", scheduled_at=_FIVE_SECS_AGO)
        mixin = _make_mixin(
            _task_queue=[(_FIVE_SECS_AGO, "t1")],
            _tasks={"t1": task},
        )

        ticks = await mixin.generate_ticks()

        assert len(ticks) == 1
        assert ticks[0].tick_id == "t1"
        assert ticks[0].agent_id == "alpha"
        assert ticks[0].action == "test_action"
        assert ticks[0].status == ScheduleStatus.PENDING
        # Source task must advance to ACTIVE
        assert task.status == ScheduleStatus.ACTIVE
        # Task removed from queue
        assert mixin._task_queue == []

    @staticmethod
    async def test_single_due_task_falls_back_to_self_agent_id() -> None:
        """When ``target_agents`` is empty, the tick's ``agent_id`` falls
        back to the mixin's ``agent_id``."""
        task = _make_task("t2", scheduled_at=_FIVE_SECS_AGO, target_agents=[])
        mixin = _make_mixin(
            agent_id="chronos-1",
            _task_queue=[(_FIVE_SECS_AGO, "t2")],
            _tasks={"t2": task},
        )

        ticks = await mixin.generate_ticks()
        assert len(ticks) == 1
        assert ticks[0].agent_id == "chronos-1"


# =========================================================================
# Contract 3 — Multiple due tasks ordered by scheduled_at
# =========================================================================


class TestMultipleDueTasks:
    """Multiple due PENDING tasks produce ticks ordered by
    ``scheduled_at``."""

    @staticmethod
    async def test_ticks_sorted_by_scheduled_at() -> None:
        later = _NOW
        earlier = _NOW - timedelta(minutes=5)
        task_a = _make_task("a", scheduled_at=earlier)
        task_b = _make_task("b", scheduled_at=later)

        # Queue in reverse order to verify sorting
        mixin = _make_mixin(
            _task_queue=[(later, "b"), (earlier, "a")],
            _tasks={"a": task_a, "b": task_b},
        )

        ticks = await mixin.generate_ticks()

        assert len(ticks) == 2
        assert ticks[0].tick_id == "a"
        assert ticks[1].tick_id == "b"
        # Source tasks advanced
        assert task_a.status == ScheduleStatus.ACTIVE
        assert task_b.status == ScheduleStatus.ACTIVE
        # Queue drained
        assert mixin._task_queue == []


# =========================================================================
# Contract 4 — Not-yet-due tasks stay in queue
# =========================================================================


class TestPendingNotDueTasks:
    """PENDING tasks that are not yet due are left in the queue."""

    @staticmethod
    async def test_future_tasks_remain_in_queue() -> None:
        task = _make_task("future", scheduled_at=_IN_TEN_SECS)
        mixin = _make_mixin(
            _task_queue=[(_IN_TEN_SECS, "future")],
            _tasks={"future": task},
        )

        ticks = await mixin.generate_ticks()

        assert ticks == []
        assert task.status == ScheduleStatus.PENDING  # unchanged
        assert mixin._task_queue == [(_IN_TEN_SECS, "future")]


# =========================================================================
# Contract 5 — Already-ACTIVE or COMPLETED tasks stay in queue
# =========================================================================


class TestNonPendingTasksNotEmitted:
    """Already-ACTIVE or COMPLETED tasks are not emitted as ticks and
    stay in the queue for ``_run_scheduler`` to handle."""

    @staticmethod
    async def test_active_task_not_emitted() -> None:
        task = _make_task("active", scheduled_at=_FIVE_SECS_AGO, status=ScheduleStatus.ACTIVE)
        mixin = _make_mixin(
            _task_queue=[(_FIVE_SECS_AGO, "active")],
            _tasks={"active": task},
        )

        ticks = await mixin.generate_ticks()

        assert ticks == []
        # Still in queue — the scheduler loop owns ACTIVE tasks
        assert mixin._task_queue == [(_FIVE_SECS_AGO, "active")]

    @staticmethod
    async def test_completed_task_not_emitted() -> None:
        task = _make_task("done", scheduled_at=_FIVE_SECS_AGO, status=ScheduleStatus.COMPLETED)
        mixin = _make_mixin(
            _task_queue=[(_FIVE_SECS_AGO, "done")],
            _tasks={"done": task},
        )

        ticks = await mixin.generate_ticks()

        assert ticks == []
        assert mixin._task_queue == [(_FIVE_SECS_AGO, "done")]

    @staticmethod
    async def test_paused_task_not_emitted() -> None:
        task = _make_task("paused", scheduled_at=_FIVE_SECS_AGO, status=ScheduleStatus.PAUSED)
        mixin = _make_mixin(
            _task_queue=[(_FIVE_SECS_AGO, "paused")],
            _tasks={"paused": task},
        )

        ticks = await mixin.generate_ticks()

        assert ticks == []
        assert mixin._task_queue == [(_FIVE_SECS_AGO, "paused")]
