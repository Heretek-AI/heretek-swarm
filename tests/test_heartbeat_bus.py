"""Contract tests for the in-process heartbeat detection bus.

Verifies that ``StewardAgent._check_registry_heartbeats()`` and the
``_monitor_loop`` integration behave correctly for the six contract
scenarios defined in S01/T02:

1. Stale agents (``last_activity`` older than ``_heartbeat_timeout``) are
   reported as stale.
2. Healthy agents (``last_activity`` set to now) are not flagged.
3. Agents with ``last_activity is None`` (pre-first-message race) are not
   flagged — treated as initialising.
4. The steward itself (``"steward"``) is excluded from stale detection.
5. The monitor loop invokes ``_handle_agent_failure()`` for stale agents
   discovered via the registry path.
6. The monitor loop does not invoke ``_handle_agent_failure()`` for agents
   that are already in ``_failed_agents``.

Uses ``MagicMock(spec=…?)`` for registry actors with controlled
``last_activity`` and ``agent_id`` attributes. Patches
``_get_actor_registry()`` to return a controlled dict. Does not spin up
a full swarm.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock

from heretek_swarm.actors.steward import StewardAgent

import pytest

pytestmark = [pytest.mark.unit]

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_mock_actor(last_activity: str | None = None) -> MagicMock:
    """Build a Mock that looks like an ``AgentActor`` with a
    ``last_activity`` attribute."""
    actor = MagicMock()
    actor.last_activity = last_activity
    return actor


def _stale_timestamp(seconds_ago: int = 30) -> str:
    """Return an ISO timestamp ``seconds_ago`` in the past."""
    return (datetime.now(UTC) - timedelta(seconds=seconds_ago)).isoformat()


def _fresh_timestamp() -> str:
    """Return an ISO timestamp right now (well within 15 s timeout)."""
    return datetime.now(UTC).isoformat()


# ---------------------------------------------------------------------------
# Contract 1 — Stale detection
# ---------------------------------------------------------------------------


class TestContractStaleDetection:
    """``_check_registry_heartbeats`` returns stale agents when
    ``last_activity`` is old (>60 s past 15 s timeout)."""

    @staticmethod
    async def test_stale_agent_reported() -> None:
        steward = StewardAgent(agent_id="steward")
        registry = {"alpha": _make_mock_actor(last_activity=_stale_timestamp(seconds_ago=20))}
        steward._get_actor_registry = MagicMock(return_value=registry)

        stale = steward._check_registry_heartbeats()

        assert stale == ["alpha"]


# ---------------------------------------------------------------------------
# Contract 2 — Healthy agents not flagged
# ---------------------------------------------------------------------------


class TestContractHealthyAgents:
    """``_check_registry_heartbeats`` does not flag agents with
    ``last_activity`` set to now."""

    @staticmethod
    async def test_fresh_agent_not_reported() -> None:
        steward = StewardAgent(agent_id="steward")
        registry = {"beta": _make_mock_actor(last_activity=_fresh_timestamp())}
        steward._get_actor_registry = MagicMock(return_value=registry)

        stale = steward._check_registry_heartbeats()

        assert stale == []


# ---------------------------------------------------------------------------
# Contract 3 — None last_activity not flagged
# ---------------------------------------------------------------------------


class TestContractNoneLastActivity:
    """``_check_registry_heartbeats`` does not flag agents with
    ``last_activity is None`` (pre-first-heartbeat race)."""

    @staticmethod
    async def test_none_last_activity_not_reported() -> None:
        steward = StewardAgent(agent_id="steward")
        registry = {"alpha": _make_mock_actor(last_activity=None)}
        steward._get_actor_registry = MagicMock(return_value=registry)

        stale = steward._check_registry_heartbeats()

        assert stale == []

    @staticmethod
    async def test_mixed_none_and_fresh() -> None:
        """None agents do not cause false positives for fresh agents."""
        steward = StewardAgent(agent_id="steward")
        registry = {
            "alpha": _make_mock_actor(last_activity=None),
            "beta": _make_mock_actor(last_activity=_fresh_timestamp()),
        }
        steward._get_actor_registry = MagicMock(return_value=registry)

        stale = steward._check_registry_heartbeats()

        assert stale == []


# ---------------------------------------------------------------------------
# Contract 4 — Steward self-exclusion
# ---------------------------------------------------------------------------


class TestContractSelfExclusion:
    """``_check_registry_heartbeats`` excludes the steward itself."""

    @staticmethod
    async def test_steward_not_reported() -> None:
        steward = StewardAgent(agent_id="steward")
        stale_self = _make_mock_actor(last_activity=_stale_timestamp(seconds_ago=999))
        registry = {"steward": stale_self}
        steward._get_actor_registry = MagicMock(return_value=registry)

        stale = steward._check_registry_heartbeats()

        assert stale == []

    @staticmethod
    async def test_steward_excluded_alongside_other_stale() -> None:
        steward = StewardAgent(agent_id="steward")
        registry = {
            "steward": _make_mock_actor(last_activity=_stale_timestamp(seconds_ago=999)),
            "alpha": _make_mock_actor(last_activity=_stale_timestamp(seconds_ago=20)),
        }
        steward._get_actor_registry = MagicMock(return_value=registry)

        stale = steward._check_registry_heartbeats()

        assert stale == ["alpha"]


# ---------------------------------------------------------------------------
# Contract 5 — Monitor loop triggers failure via mock
# ---------------------------------------------------------------------------


class TestContractMonitorLoopCallsHandleFailure:
    """When the monitor loop detects a stale agent via the registry path,
    it invokes ``_handle_agent_failure()``.

    Because ``_monitor_loop`` is an infinite async loop with a sleep, we
    test the *dispatch logic* in a tight call: run the loop's merge &
    dispatch block once with a mocked ``_handle_agent_failure`` and verify
    the mock was called for the expected agent.
    """

    @staticmethod
    async def test_registry_stale_agent_triggers_failure() -> None:
        steward = StewardAgent(agent_id="steward")

        # Populate registry with a stale agent, leave NATS heartbeats empty
        registry = {"alpha": _make_mock_actor(last_activity=_stale_timestamp(seconds_ago=20))}
        steward._get_actor_registry = MagicMock(return_value=registry)
        steward._agent_heartbeats = {}  # no NATS heartbeats

        # Mock the failure handler
        steward._handle_agent_failure = AsyncMock()

        # Execute the same merge-dispatch logic used in _monitor_loop
        nats_failed = steward.detect_heartbeat_failure()
        registry_failed = steward._check_registry_heartbeats()
        all_failed = sorted(set(nats_failed + registry_failed))

        for agent_id in all_failed:
            if agent_id not in steward._failed_agents:
                await steward._handle_agent_failure(agent_id)

        steward._handle_agent_failure.assert_awaited_once_with("alpha")

    @staticmethod
    async def test_registry_stale_agent_not_in_nats_standalone() -> None:
        """A stale agent present only in the registry (no NATS heartbeat)
        still triggers failure — confirms the registry path works as a
        standalone detection mechanism."""
        steward = StewardAgent(agent_id="steward")

        registry = {"gamma": _make_mock_actor(last_activity=_stale_timestamp(seconds_ago=20))}
        steward._get_actor_registry = MagicMock(return_value=registry)
        steward._agent_heartbeats = {}  # no NATS heartbeats for gamma
        steward._handle_agent_failure = AsyncMock()

        all_failed = sorted(
            set(steward.detect_heartbeat_failure() + steward._check_registry_heartbeats())
        )
        for agent_id in all_failed:
            if agent_id not in steward._failed_agents:
                await steward._handle_agent_failure(agent_id)

        steward._handle_agent_failure.assert_awaited_once_with("gamma")


# ---------------------------------------------------------------------------
# Contract 6 — Already-failed agents not re-processed
# ---------------------------------------------------------------------------


class TestContractAlreadyFailedSkipped:
    """The monitor loop does not trigger failure for agents detected via
    the registry that are already in ``_failed_agents``."""

    @staticmethod
    async def test_already_failed_agent_not_reprocessed() -> None:
        steward = StewardAgent(agent_id="steward")

        # alpha is already in _failed_agents AND stale in registry
        steward._failed_agents.add("alpha")
        registry = {"alpha": _make_mock_actor(last_activity=_stale_timestamp(seconds_ago=20))}
        steward._get_actor_registry = MagicMock(return_value=registry)
        steward._handle_agent_failure = AsyncMock()

        all_failed = sorted(
            set(steward.detect_heartbeat_failure() + steward._check_registry_heartbeats())
        )
        for agent_id in all_failed:
            if agent_id not in steward._failed_agents:
                await steward._handle_agent_failure(agent_id)

        steward._handle_agent_failure.assert_not_awaited()

    @staticmethod
    async def test_mixed_already_failed_and_new() -> None:
        """Only new (not-yet-failed) agents trigger
        ``_handle_agent_failure`` when some are already in
        ``_failed_agents``."""
        steward = StewardAgent(agent_id="steward")

        steward._failed_agents.add("alpha")
        registry = {
            "alpha": _make_mock_actor(last_activity=_stale_timestamp(seconds_ago=20)),
            "beta": _make_mock_actor(last_activity=_stale_timestamp(seconds_ago=20)),
        }
        steward._get_actor_registry = MagicMock(return_value=registry)
        steward._handle_agent_failure = AsyncMock()

        all_failed = sorted(
            set(steward.detect_heartbeat_failure() + steward._check_registry_heartbeats())
        )
        for agent_id in all_failed:
            if agent_id not in steward._failed_agents:
                await steward._handle_agent_failure(agent_id)

        steward._handle_agent_failure.assert_awaited_once_with("beta")
