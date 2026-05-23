"""Unit tests for ``StewardAgent._check_registry_heartbeats()``.

Tests the in-process heartbeat bus that reads ``last_activity`` from actor
registry entries instead of relying on NATS heartbeat messages.

Key test surfaces (mapped from MEM034/T01 constraints):
1. Normal stale detection — ``last_activity`` older than timeout
2. ``None`` handling — agents with no ``last_activity`` (initialising) are
   treated as alive
3. Self-exclusion — ``"steward"`` is never reported as stale
4. Registry unavailable (``_get_actor_registry`` returns ``None``)
5. Malformed timestamps treated as stale (safe side)
6. NATS path (``detect_heartbeat_failure``) remains unchanged
7. Merged path in ``_monitor_loop`` deduplicates NATS + registry results
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock

from heretek_swarm.actors.steward import StewardAgent

import pytest

pytestmark = [pytest.mark.unit]

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_mock_actor(
    last_activity: str | None = None,
) -> MagicMock:
    """Build a ``MagicMock`` that looks like an ``AgentActor`` with a
    ``last_activity`` attribute."""
    actor = MagicMock()
    actor.last_activity = last_activity
    return actor


def _stale_timestamp(seconds_ago: int = 30) -> str:
    """Return an ISO timestamp ``seconds_ago`` in the past."""
    return (datetime.now(UTC) - timedelta(seconds=seconds_ago)).isoformat()


def _fresh_timestamp() -> str:
    """Return an ISO timestamp right now (well within timeout)."""
    return datetime.now(UTC).isoformat()


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestCheckRegistryHeartbeats:
    """``StewardAgent._check_registry_heartbeats()`` detection logic."""

    # -- Happy path: stale detection -----------------------------------

    @staticmethod
    async def test_detects_stale_agent() -> None:
        """An actor whose ``last_activity`` is older than
        ``_heartbeat_timeout`` (15s) is reported as stale."""
        steward = StewardAgent(agent_id="steward")
        stale_actor = _make_mock_actor(last_activity=_stale_timestamp(seconds_ago=20))
        registry = {"alpha": stale_actor}

        # Override _get_actor_registry to return our controlled registry
        steward._get_actor_registry = MagicMock(return_value=registry)  # type: ignore[method-assign]

        stale = steward._check_registry_heartbeats()

        assert stale == ["alpha"]

    @staticmethod
    async def test_skips_fresh_agents() -> None:
        """An actor whose ``last_activity`` is within the timeout is not
        reported as stale."""
        steward = StewardAgent(agent_id="steward")
        fresh_actor = _make_mock_actor(last_activity=_fresh_timestamp())
        registry = {"beta": fresh_actor}

        steward._get_actor_registry = MagicMock(return_value=registry)  # type: ignore[method-assign]

        stale = steward._check_registry_heartbeats()

        assert stale == []

    @staticmethod
    async def test_mixed_stale_and_fresh() -> None:
        """Only stale agents are returned when the registry contains a
        mix of stale and fresh entries."""
        steward = StewardAgent(agent_id="steward")
        registry = {
            "alpha": _make_mock_actor(last_activity=_stale_timestamp(seconds_ago=20)),
            "beta": _make_mock_actor(last_activity=_fresh_timestamp()),
            "gamma": _make_mock_actor(last_activity=_stale_timestamp(seconds_ago=60)),
        }
        steward._get_actor_registry = MagicMock(return_value=registry)  # type: ignore[method-assign]

        stale = steward._check_registry_heartbeats()

        assert stale == ["alpha", "gamma"]

    # -- None / initialising -------------------------------------------

    @staticmethod
    async def test_skips_none_last_activity() -> None:
        """Actors whose ``last_activity`` is ``None`` (initialising) are not
        reported as stale — avoids race on first heartbeat."""
        steward = StewardAgent(agent_id="steward")
        registry = {
            "alpha": _make_mock_actor(last_activity=None),
            "beta": _make_mock_actor(last_activity=_fresh_timestamp()),
        }
        steward._get_actor_registry = MagicMock(return_value=registry)  # type: ignore[method-assign]

        stale = steward._check_registry_heartbeats()

        assert stale == []  # alpha is initialising, beta is fresh

    @staticmethod
    async def test_all_none_returns_empty() -> None:
        """When every agent has ``last_activity=None``, the result is
        empty — all are assumed to be initialising."""
        steward = StewardAgent(agent_id="steward")
        registry = {
            "alpha": _make_mock_actor(last_activity=None),
            "beta": _make_mock_actor(last_activity=None),
        }
        steward._get_actor_registry = MagicMock(return_value=registry)  # type: ignore[method-assign]

        stale = steward._check_registry_heartbeats()

        assert stale == []

    # -- Self-exclusion ------------------------------------------------

    @staticmethod
    async def test_excludes_steward_self() -> None:
        """The steward's own agent ID (``"steward"``) is excluded even if
        its ``last_activity`` is stale."""
        steward = StewardAgent(agent_id="steward")
        stale_self = _make_mock_actor(last_activity=_stale_timestamp(seconds_ago=999))
        registry = {"steward": stale_self}
        steward._get_actor_registry = MagicMock(return_value=registry)  # type: ignore[method-assign]

        stale = steward._check_registry_heartbeats()

        assert stale == []

    @staticmethod
    async def test_self_excluded_alongside_other_stale() -> None:
        """When the steward AND other actors are stale, only the non-self
        actors appear in the result."""
        steward = StewardAgent(agent_id="steward")
        registry = {
            "steward": _make_mock_actor(last_activity=_stale_timestamp(seconds_ago=999)),
            "alpha": _make_mock_actor(last_activity=_stale_timestamp(seconds_ago=20)),
        }
        steward._get_actor_registry = MagicMock(return_value=registry)  # type: ignore[method-assign]

        stale = steward._check_registry_heartbeats()

        assert stale == ["alpha"]

    # -- Registry unavailable ------------------------------------------

    @staticmethod
    async def test_returns_empty_when_registry_unavailable() -> None:
        """If ``_get_actor_registry()`` returns ``None``, an empty list is
        returned (graceful degradation)."""
        steward = StewardAgent(agent_id="steward")
        steward._get_actor_registry = MagicMock(return_value=None)  # type: ignore[method-assign]

        stale = steward._check_registry_heartbeats()

        assert stale == []

    # -- Malformed timestamps ------------------------------------------

    @staticmethod
    async def test_treats_malformed_timestamp_as_stale() -> None:
        """A ``last_activity`` string that cannot be parsed as ISO format
        is treated as stale (safe side)."""
        steward = StewardAgent(agent_id="steward")
        bad_actor = _make_mock_actor(last_activity="not-a-date")
        registry = {"alpha": bad_actor}
        steward._get_actor_registry = MagicMock(return_value=registry)  # type: ignore[method-assign]

        stale = steward._check_registry_heartbeats()

        assert stale == ["alpha"]

    # -- Deterministic ordering ----------------------------------------

    @staticmethod
    async def test_returns_sorted_results() -> None:
        """Returned list is sorted alphabetically for deterministic
        ordering."""
        steward = StewardAgent(agent_id="steward")
        registry = {
            "zebra": _make_mock_actor(last_activity=_stale_timestamp(seconds_ago=20)),
            "alpha": _make_mock_actor(last_activity=_stale_timestamp(seconds_ago=20)),
            "beta": _make_mock_actor(last_activity=_stale_timestamp(seconds_ago=20)),
        }
        steward._get_actor_registry = MagicMock(return_value=registry)  # type: ignore[method-assign]

        stale = steward._check_registry_heartbeats()

        assert stale == ["alpha", "beta", "zebra"]

    # -- Configurable timeout ------------------------------------------

    @staticmethod
    async def test_respects_custom_heartbeat_timeout() -> None:
        """A ``_heartbeat_timeout`` of 5 seconds means timestamps older
        than 5s are stale; ones within are fresh."""
        steward = StewardAgent(agent_id="steward")
        steward._heartbeat_timeout = 5.0
        registry = {
            "alpha": _make_mock_actor(last_activity=_stale_timestamp(seconds_ago=6)),
            "beta": _make_mock_actor(last_activity=_stale_timestamp(seconds_ago=3)),
        }
        steward._get_actor_registry = MagicMock(return_value=registry)  # type: ignore[method-assign]

        stale = steward._check_registry_heartbeats()

        assert stale == ["alpha"]  # only alpha is beyond 5s


class TestNatsHeartbeatPath:
    """``StewardAgent.detect_heartbeat_failure()`` — verifies the NATS path
    is not broken by the registry changes."""

    @staticmethod
    async def test_detect_heartbeat_failure_unchanged() -> None:
        """``detect_heartbeat_failure`` still works when
        ``_agent_heartbeats`` is populated (NATS path unaffected)."""
        steward = StewardAgent(agent_id="steward")
        steward._agent_heartbeats = {
            "alpha": _stale_timestamp(seconds_ago=30),
            "beta": _fresh_timestamp(),
        }

        failed = steward.detect_heartbeat_failure()

        assert failed == ["alpha"]

    @staticmethod
    async def test_empty_heartbeats_returns_empty() -> None:
        steward = StewardAgent(agent_id="steward")
        assert steward.detect_heartbeat_failure() == []


class TestMonitorLoopRegistryIntegration:
    """Verifies key integration aspects of the ``_monitor_loop`` changes.

    Because ``_monitor_loop`` is an infinite async loop with sleeps, we test
    the *merge behaviour* rather than running the loop itself.
    """

    @staticmethod
    async def test_merge_deduplicates_nats_and_registry() -> None:
        """When the same agent appears as stale in both NATS and registry
        paths, it is only handled once."""
        steward = StewardAgent(agent_id="steward")
        steward._heartbeat_timeout = 15.0

        # NATS path: alpha and beta are stale
        steward._agent_heartbeats = {
            "alpha": _stale_timestamp(seconds_ago=30),
            "beta": _stale_timestamp(seconds_ago=30),
        }
        # Registry path: alpha and gamma are stale
        registry = {
            "alpha": _make_mock_actor(last_activity=_stale_timestamp(seconds_ago=30)),
            "gamma": _make_mock_actor(last_activity=_stale_timestamp(seconds_ago=30)),
        }
        steward._get_actor_registry = MagicMock(return_value=registry)  # type: ignore[method-assign]

        nats_failed = steward.detect_heartbeat_failure()
        registry_failed = steward._check_registry_heartbeats()
        all_failed = sorted(set(nats_failed + registry_failed))

        assert all_failed == ["alpha", "beta", "gamma"]
        # alpha appears in both, but only once in the merged set
        assert len(nats_failed) == 2
        assert len(registry_failed) == 2
        assert len(all_failed) == 3

    @staticmethod
    async def test_failed_agents_deduplication() -> None:
        """Agents already in ``_failed_agents`` are not re-processed by
        the ``_monitor_loop`` merge logic."""
        steward = StewardAgent(agent_id="steward")
        steward._heartbeat_timeout = 15.0


        steward._failed_agents.add("alpha")
        steward._agent_heartbeats = {"alpha": _stale_timestamp(seconds_ago=30)}
        registry = {"alpha": _make_mock_actor(last_activity=_stale_timestamp(seconds_ago=30))}
        steward._get_actor_registry = MagicMock(return_value=registry)  # type: ignore[method-assign]

        nats_failed = steward.detect_heartbeat_failure()
        registry_failed = steward._check_registry_heartbeats()
        all_failed = sorted(set(nats_failed + registry_failed))

        # alpha appears in both lists, but the loop would skip it because
        # `_handle_agent_failure` checks `_failed_agents` at the top
        new_failures = [a for a in all_failed if a not in steward._failed_agents]

        assert "alpha" in all_failed
        assert "alpha" not in new_failures
