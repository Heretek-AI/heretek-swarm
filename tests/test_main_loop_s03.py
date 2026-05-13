"""Contract tests for ``AutonomousSwarm._process_scheduled_tasks()``.

Verifies that the scheduled-tasks processing path correctly:

1. Gets due ticks from the Chronos actor
2. Routes each tick to its target agent via ``put_message()``
3. Logs the cycle event to the Historian actor
4. Gracefully handles missing Chronos or Historian in the registry
5. Gracefully handles missing target agents for a tick

Uses ``MagicMock`` versions of Chronos and Historian to avoid spinning up
real actors. Follows the same mock-heavy pattern from
``test_heartbeat_bus.py``.
"""

from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock

from heretek_swarm.actors.chronos.types import ScheduleStatus, Tick
from heretek_swarm.runtime.main_loop import AutonomousSwarm

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_chronos_mock(ticks: list[Tick] | None = None) -> MagicMock:
    """Build a MagicMock that looks like a ChronosAgent.

    The mock's ``generate_ticks()`` returns the provided ticks (or an empty
    list by default).
    """
    chronos = MagicMock()
    chronos.generate_ticks = AsyncMock(return_value=ticks or [])
    return chronos


def _make_historian_mock() -> MagicMock:
    """Build a MagicMock that looks like a HistorianAgent.

    The mock's ``log_event()`` is an AsyncMock so callers can assert it was
    called with expected arguments.
    """
    historian = MagicMock()
    historian.log_event = AsyncMock()
    return historian


def _make_target_actor_mock() -> MagicMock:
    """Build a MagicMock that looks like a target AgentActor.

    The mock's ``put_message()`` is an AsyncMock.
    """
    actor = MagicMock()
    actor.put_message = AsyncMock()
    return actor


def _make_tick(
    agent_id: str = "alpha",
    action: str = "scheduled_task",
    tick_id: str | None = None,
) -> Tick:
    """Create a ``Tick`` with reasonable defaults for testing."""
    return Tick(
        tick_id=tick_id or f"tick-{agent_id}-{datetime.now(UTC).timestamp():.0f}",
        agent_id=agent_id,
        action=action,
        scheduled_at=datetime.now(UTC),
        status=ScheduleStatus.PENDING,
    )


def _make_swarm_with_actors(
    actors: dict[str, MagicMock],
) -> AutonomousSwarm:
    """Create an ``AutonomousSwarm`` (``no_infra=True``) and replace its
    supervisor.actors with the provided mock dict.

    Returns the swarm for method calls.
    """
    swarm = AutonomousSwarm(no_infra=True)
    # We don't call swarm.initialize() because that would try to spawn real
    # actors. Instead we set up the supervisor with mocked actors directly.
    swarm.supervisor = MagicMock()
    swarm.supervisor.actors = actors
    return swarm


# ---------------------------------------------------------------------------
# Contract 1 — Chronos.generate_ticks() is called
# ---------------------------------------------------------------------------


class TestContractCallsChronosGenerateTicks:
    """``_process_scheduled_tasks()`` calls ``chronos.generate_ticks()``."""

    @staticmethod
    async def test_calls_generate_ticks() -> None:
        chronos = _make_chronos_mock()
        swarm = _make_swarm_with_actors({"chronos": chronos})

        await swarm._process_scheduled_tasks()

        chronos.generate_ticks.assert_awaited_once()


# ---------------------------------------------------------------------------
# Contract 2 — Ticks routed to target agents via put_message
# ---------------------------------------------------------------------------


class TestContractTicksRoutedToTargetAgents:
    """Returned ticks are routed to their target agents via
    ``put_message()``."""

    @staticmethod
    async def test_single_tick_routed() -> None:
        alpha = _make_target_actor_mock()
        tick = _make_tick(agent_id="alpha", action="do_work")
        chronos = _make_chronos_mock(ticks=[tick])
        swarm = _make_swarm_with_actors({"chronos": chronos, "alpha": alpha})

        await swarm._process_scheduled_tasks()

        alpha.put_message.assert_awaited_once()
        (msg,) = alpha.put_message.await_args[0]
        assert msg.sender == "chronos"
        assert msg.message_type == "do_work"
        assert msg.recipient == "alpha"

    @staticmethod
    async def test_multiple_ticks_routed_to_different_agents() -> None:
        alpha = _make_target_actor_mock()
        beta = _make_target_actor_mock()
        tick_a = _make_tick(agent_id="alpha", action="task_a")
        tick_b = _make_tick(agent_id="beta", action="task_b")
        chronos = _make_chronos_mock(ticks=[tick_a, tick_b])
        swarm = _make_swarm_with_actors({"chronos": chronos, "alpha": alpha, "beta": beta})

        await swarm._process_scheduled_tasks()

        alpha.put_message.assert_awaited_once()
        beta.put_message.assert_awaited_once()
        (msg_a,) = alpha.put_message.await_args[0]
        (msg_b,) = beta.put_message.await_args[0]
        assert msg_a.message_type == "task_a"
        assert msg_b.message_type == "task_b"


# ---------------------------------------------------------------------------
# Contract 3 — Historian receives log events
# ---------------------------------------------------------------------------


class TestContractHistorianLogEvents:
    """Historian receives ``cycle_scheduled_tasks`` and the cycle-level
    ``cycle_complete`` events."""

    @staticmethod
    async def test_historian_receives_scheduled_tasks_event() -> None:
        chronos = _make_chronos_mock(ticks=[_make_tick()])
        historian = _make_historian_mock()
        alpha = _make_target_actor_mock()
        swarm = _make_swarm_with_actors(
            {"chronos": chronos, "historian": historian, "alpha": alpha}
        )

        await swarm._process_scheduled_tasks()

        historian.log_event.assert_awaited_once_with(
            "cycle_scheduled_tasks",
            "main_loop",
            {"tick_count": 1},
        )

    @staticmethod
    async def test_historian_receives_cycle_complete_event() -> None:
        """``_process_cycle()`` logs ``cycle_complete`` to historian after
        processing scheduled tasks."""
        chronos = _make_chronos_mock()
        historian = _make_historian_mock()
        swarm = _make_swarm_with_actors({"chronos": chronos, "historian": historian})

        await swarm._process_cycle()

        historian.log_event.assert_any_call("cycle_complete", "main_loop", {})

    @staticmethod
    async def test_empty_ticks_still_logged() -> None:
        """Historian is notified even when no ticks are due."""
        chronos = _make_chronos_mock(ticks=[])
        historian = _make_historian_mock()
        swarm = _make_swarm_with_actors({"chronos": chronos, "historian": historian})

        await swarm._process_scheduled_tasks()

        historian.log_event.assert_awaited_once_with(
            "cycle_scheduled_tasks",
            "main_loop",
            {"tick_count": 0},
        )


# ---------------------------------------------------------------------------
# Contract 4 — Graceful handling when Chronos or Historian is None
# ---------------------------------------------------------------------------


class TestContractHandlesMissingChronosOrHistorian:
    """``_process_scheduled_tasks()`` handles None Chronos/Historian."""

    @staticmethod
    async def test_no_chronos_does_not_raise() -> None:
        """When ``chronos`` is not in the registry, the method logs a
        warning and returns without error."""
        swarm = _make_swarm_with_actors({})

        # Should not raise
        await swarm._process_scheduled_tasks()

    @staticmethod
    async def test_chronos_present_historian_absent() -> None:
        """When Chronos is present but Historian is not, ticks are still
        routed and no error is raised."""
        alpha = _make_target_actor_mock()
        tick = _make_tick(agent_id="alpha")
        chronos = _make_chronos_mock(ticks=[tick])
        swarm = _make_swarm_with_actors({"chronos": chronos, "alpha": alpha})

        await swarm._process_scheduled_tasks()

        # Tick should still be routed
        alpha.put_message.assert_awaited_once()

    @staticmethod
    async def test_no_supervisor_does_not_raise() -> None:
        """When supervisor is None (not yet initialized), the method logs a
        warning and returns without error."""
        swarm = AutonomousSwarm(no_infra=True)
        swarm.supervisor = None

        await swarm._process_scheduled_tasks()


# ---------------------------------------------------------------------------
# Contract 5 — Missing target agent for a tick
# ---------------------------------------------------------------------------


class TestContractHandlesMissingTargetAgent:
    """When the target agent for a tick is not in the registry, the tick is
    skipped with a warning."""

    @staticmethod
    async def test_missing_target_skipped_gracefully() -> None:
        """A tick targeting a missing agent is skipped, and the remaining
        ticks are still processed."""
        alpha = _make_target_actor_mock()
        tick_good = _make_tick(agent_id="alpha", action="good")
        tick_bad = _make_tick(agent_id="nonexistent", action="bad")
        chronos = _make_chronos_mock(ticks=[tick_good, tick_bad])
        swarm = _make_swarm_with_actors({"chronos": chronos, "alpha": alpha})

        await swarm._process_scheduled_tasks()

        # The valid tick should still be routed
        alpha.put_message.assert_awaited_once()
        (msg,) = alpha.put_message.await_args[0]
        assert msg.message_type == "good"

    @staticmethod
    async def test_all_targets_missing_still_logs() -> None:
        """When all ticks target missing agents, no ``put_message`` calls
        are made but the historian event is still logged."""
        historian = _make_historian_mock()
        tick = _make_tick(agent_id="ghost")
        chronos = _make_chronos_mock(ticks=[tick])
        swarm = _make_swarm_with_actors({"chronos": chronos, "historian": historian})

        await swarm._process_scheduled_tasks()

        historian.log_event.assert_awaited_once()
