"""Contract tests for ``AutonomousSwarm.run_routed_task()``.

Verifies that the routed-task processing path correctly:

1. Gets the Steward agent from the supervisor registry — raises RuntimeError
   if not found (same pattern as ``run_deliberation()``)
2. Calls ``steward.route_to_agent(agent_name, task_type, task_data)``
3. Returns a failed status dict when ``route_to_agent()`` returns empty string
4. Sleeps for ``min(timeout, 30)`` seconds for async mailbox processing
   (same sleep pattern as ``run_deliberation()``)
5. Logs the routed event to Historian via ``historian.log_event()``
6. Returns a dispatched status dict on success
7. Gracefully handles missing Historian (logs warning, still returns dispatch
   status)

Uses ``MagicMock`` versions of Steward and Historian to avoid spinning up
real actors. Follows the same mock-heavy pattern from
``test_main_loop_s03.py`` and ``test_heartbeat_bus.py``.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from heretek_swarm.runtime.main_loop import AutonomousSwarm

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_steward_mock(route_result: str = "msg-abc123") -> MagicMock:
    """Build a MagicMock that looks like a StewardAgent.

    The mock's ``route_to_agent()`` returns the provided result string (a
    message ID on success, empty string on failure).
    """
    steward = MagicMock()
    steward.route_to_agent = AsyncMock(return_value=route_result)
    return steward


def _make_historian_mock() -> MagicMock:
    """Build a MagicMock that looks like a HistorianAgent.

    The mock's ``log_event()`` is an AsyncMock so callers can assert it was
    called with expected arguments.
    """
    historian = MagicMock()
    historian.log_event = AsyncMock(return_value="evt-xyz789")
    return historian


def _make_swarm_with_actors(
    actors: dict[str, MagicMock],
) -> AutonomousSwarm:
    """Create an ``AutonomousSwarm`` (``no_infra=True``) and replace its
    supervisor.actors with the provided mock dict.

    Returns the swarm for method calls.
    """
    swarm = AutonomousSwarm(no_infra=True)
    swarm.supervisor = MagicMock()
    swarm.supervisor.actors = actors
    return swarm


# ---------------------------------------------------------------------------
# Contract 1 — RuntimeError when Steward is absent
# ---------------------------------------------------------------------------


class TestContractRaisesWhenStewardMissing:
    """``run_routed_task()`` raises ``RuntimeError`` when Steward is not in
    the actor registry."""

    @staticmethod
    async def test_raises_on_missing_steward() -> None:
        swarm = _make_swarm_with_actors({})

        with pytest.raises(RuntimeError, match="Steward agent not found"):
            await swarm.run_routed_task(
                agent_name="coder",
                task_type="code_analysis",
                task_data={"prompt": "analyze this"},
            )

    @staticmethod
    async def test_raises_on_none_supervisor() -> None:
        """When supervisor is None, .actors access raises AttributeError
        (same behavior as ``run_deliberation()``)."""
        swarm = AutonomousSwarm(no_infra=True)
        swarm.supervisor = None

        with pytest.raises(AttributeError):
            await swarm.run_routed_task(
                agent_name="coder",
                task_type="code_analysis",
                task_data={"prompt": "analyze this"},
            )


# ---------------------------------------------------------------------------
# Contract 2 — Dispatch success path
# ---------------------------------------------------------------------------


class TestContractDispatchSuccess:
    """When ``route_to_agent()`` succeeds, ``run_routed_task()`` returns a
    dispatched status dict and logs the event to Historian."""

    @staticmethod
    async def test_returns_dispatched_on_success() -> None:
        steward = _make_steward_mock(route_result="msg-coder-001")
        historian = _make_historian_mock()
        swarm = _make_swarm_with_actors(
            {"steward": steward, "historian": historian}
        )

        result = await swarm.run_routed_task(
            agent_name="coder",
            task_type="code_analysis",
            task_data={"prompt": "analyze this code"},
            timeout=0.01,
        )

        assert result["status"] == "dispatched"
        assert result["target_agent"] == "coder"
        assert result["task_type"] == "code_analysis"
        assert result["message_id"] == "msg-coder-001"

    @staticmethod
    async def test_calls_steward_route_to_agent() -> None:
        steward = _make_steward_mock()
        historian = _make_historian_mock()
        swarm = _make_swarm_with_actors(
            {"steward": steward, "historian": historian}
        )

        await swarm.run_routed_task(
            agent_name="coder",
            task_type="code_analysis",
            task_data={"prompt": "hello"},
            timeout=0.01,
        )

        steward.route_to_agent.assert_awaited_once_with(
            agent_name="coder",
            task_type="code_analysis",
            task_data={"prompt": "hello"},
        )

    @staticmethod
    async def test_logs_to_historian_on_success() -> None:
        steward = _make_steward_mock(route_result="msg-42")
        historian = _make_historian_mock()
        swarm = _make_swarm_with_actors(
            {"steward": steward, "historian": historian}
        )

        await swarm.run_routed_task(
            agent_name="explorer",
            task_type="discovery",
            task_data={"query": "latest AI news"},
            timeout=0.01,
        )

        historian.log_event.assert_awaited_once_with(
            "routed_task",
            "main_loop",
            {
                "target_agent": "explorer",
                "task_type": "discovery",
                "message_id": "msg-42",
            },
        )


# ---------------------------------------------------------------------------
# Contract 3 — Dispatch failure path
# ---------------------------------------------------------------------------


class TestContractDispatchFailure:
    """When ``route_to_agent()`` returns an empty string, ``run_routed_task()``
    returns a failed status dict."""

    @staticmethod
    async def test_returns_failed_on_empty_result() -> None:
        steward = _make_steward_mock(route_result="")
        historian = _make_historian_mock()
        swarm = _make_swarm_with_actors(
            {"steward": steward, "historian": historian}
        )

        result = await swarm.run_routed_task(
            agent_name="coder",
            task_type="code_analysis",
            task_data={},
            timeout=0.01,
        )

        assert result["status"] == "failed"
        assert result["error"] == "route_to_agent returned empty"

    @staticmethod
    async def test_does_not_log_to_historian_on_failure() -> None:
        """When route_to_agent returns empty, the method returns early and
        does NOT log to Historian."""
        steward = _make_steward_mock(route_result="")
        historian = _make_historian_mock()
        swarm = _make_swarm_with_actors(
            {"steward": steward, "historian": historian}
        )

        await swarm.run_routed_task(
            agent_name="coder",
            task_type="code_analysis",
            task_data={},
            timeout=0.01,
        )

        historian.log_event.assert_not_called()


# ---------------------------------------------------------------------------
# Contract 4 — Graceful handling when Historian is absent
# ---------------------------------------------------------------------------


class TestContractHandlesMissingHistorian:
    """``run_routed_task()`` gracefully handles missing Historian — still
    returns dispatch status without raising."""

    @staticmethod
    async def test_returns_dispatched_without_historian() -> None:
        """When Historian is not in the registry, the method still returns
        a dispatched result with no error."""
        steward = _make_steward_mock(route_result="msg-ok")
        swarm = _make_swarm_with_actors({"steward": steward})

        result = await swarm.run_routed_task(
            agent_name="coder",
            task_type="code_analysis",
            task_data={},
            timeout=0.01,
        )

        assert result["status"] == "dispatched"
        assert result["message_id"] == "msg-ok"

    @staticmethod
    async def test_historian_absent_no_raise() -> None:
        """Missing Historian does not raise — the method handles it
        gracefully and returns the dispatch result."""
        steward = _make_steward_mock(route_result="msg-coder-001")
        # No historian in the registry
        swarm = _make_swarm_with_actors({"steward": steward})

        result = await swarm.run_routed_task(
            agent_name="coder",
            task_type="code_analysis",
            task_data={},
            timeout=0.01,
        )

        assert result["status"] == "dispatched"
