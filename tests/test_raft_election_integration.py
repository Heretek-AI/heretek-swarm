"""
Integration tests for the full RAFT election lifecycle in the steward pulse.

Verifies the complete chain:
  heartbeat timeout → election → leader elected → new steward spawned

Key surfaces (mapped from M002/S03/T04):
1. Steward kill triggers election and spawns new steward
2. --no-infra flag suppresses election machinery
3. Election failure logs ``tribunal_election_failed`` and no steward is spawned
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock

import pytest

pytestmark = [pytest.mark.integration]

from heretek_swarm.runtime.steward_pulse import (
    HEARTBEAT_TIMEOUT,
    _check_heartbeat_timeout,
    run_steward_pulse,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _stale_timestamp(seconds_ago: int = 20) -> str:
    """Return an ISO timestamp ``seconds_ago`` in the past."""
    return (datetime.now(UTC) - timedelta(seconds=seconds_ago)).isoformat()


def _make_steward_mock(
    last_heartbeat: str | None = None,
    last_seen_heartbeat: str | None = None,
) -> MagicMock:
    """Build a mock steward agent with heartbeat internal_state."""
    steward = MagicMock()
    steward.internal_state = {}
    if last_heartbeat is not None:
        steward.internal_state["_last_heartbeat"] = last_heartbeat
    if last_seen_heartbeat is not None:
        steward.internal_state["_last_seen_heartbeat"] = last_seen_heartbeat
    return steward


def _make_sentinel_mock() -> MagicMock:
    """Build a mock sentinel with S03 election logging methods."""
    sentinel = MagicMock()
    sentinel.log_election_started = MagicMock()
    sentinel.log_leader_elected = MagicMock()
    sentinel.log_election_failed = MagicMock()
    return sentinel


def _make_election_mgr_mock(trigger_result: str | None = "alpha") -> MagicMock:
    """Build a mock ElectionManager that returns ``trigger_result`` from
    ``trigger_election()``."""
    mgr = MagicMock()
    mgr.trigger_election = AsyncMock(return_value=trigger_result)
    mgr._max_cycles = 3
    # Five governance nodes so get_status returns realistic vote_count
    mgr.get_status = MagicMock(
        return_value={
            "nodes": {
                "steward": {"term": 1},
                "alpha": {"term": 1},
                "beta": {"term": 1},
                "charlie": {"term": 1},
                "sentinel": {"term": 1},
            },
            "leader_id": trigger_result,
            "cycle_count": 0,
        }
    )
    return mgr


def _make_swarm_mock(
    supervisor: MagicMock | None = None,
    election_mgr: MagicMock | None = None,
    no_infra: bool = False,
) -> MagicMock:
    """Build a mock AutonomousSwarm with mock supervisor and election manager."""
    swarm = MagicMock()
    swarm.supervisor = supervisor
    swarm._election_manager = election_mgr
    swarm._no_infra = no_infra
    swarm._running = False
    swarm._health_check_interval = 30
    return swarm


# ---------------------------------------------------------------------------
# Test: Steward kill → election → new steward
# ---------------------------------------------------------------------------


class TestStewardKillTriggersElectionNewStewardSpawns:
    """Full election lifecycle: heartbeat timeout triggers election, leader
    elected, old steward terminated, new steward spawned."""

    @pytest.mark.asyncio
    @staticmethod
    async def test_full_election_chain() -> None:
        """Verify the complete chain from heartbeat timeout to new steward."""
        stale = _stale_timestamp(seconds_ago=20)

        # Mock steward with a stale heartbeat and prior cursor
        steward = _make_steward_mock(
            last_heartbeat=stale,
            last_seen_heartbeat=stale,
        )

        # Mock sentinel for election log assertions
        sentinel = _make_sentinel_mock()

        # Mock supervisor with terminate/spawn
        supervisor = MagicMock()
        supervisor.actors = {"steward": steward, "sentinel": sentinel}
        supervisor.terminate_actor = AsyncMock()
        supervisor.spawn_actor = AsyncMock()

        # Mock ElectionManager — election succeeds with "alpha" as leader
        election_mgr = _make_election_mgr_mock(trigger_result="alpha")

        swarm = _make_swarm_mock(supervisor=supervisor, election_mgr=election_mgr)

        # Trigger the heartbeat timeout check
        await _check_heartbeat_timeout(swarm, steward)

        # --- Assert: raft_election_started logged ---
        sentinel.log_election_started.assert_called_once()

        # --- Assert: raft_leader_elected logged ---
        sentinel.log_leader_elected.assert_called_once_with(
            leader_id="alpha",
            term=1,
            vote_count=5,
        )

        # --- Assert: old steward terminated ---
        supervisor.terminate_actor.assert_called_once_with("steward")

        # --- Assert: new steward spawned ---
        supervisor.spawn_actor.assert_called_once()
        call_args = supervisor.spawn_actor.call_args
        # First positional arg is StewardAgent class
        from heretek_swarm.actors.triad.agent import StewardAgent

        assert call_args[0][0] is StewardAgent, (
            f"Expected StewardAgent class, got {call_args[0][0]}"
        )
        assert call_args[0][1] == "steward", (
            f"Expected agent_id='steward', got {call_args[0][1]}"
        )

    @pytest.mark.asyncio
    @staticmethod
    async def test_leader_can_be_any_governance_agent() -> None:
        """The elected leader must be a governance-tier agent ID."""
        governance_ids = {"steward", "alpha", "beta", "charlie", "sentinel"}

        for leader_id in governance_ids:
            stale = _stale_timestamp(seconds_ago=20)
            steward = _make_steward_mock(
                last_heartbeat=stale,
                last_seen_heartbeat=stale,
            )
            sentinel = _make_sentinel_mock()
            supervisor = MagicMock()
            supervisor.actors = {"steward": steward, "sentinel": sentinel}
            supervisor.terminate_actor = AsyncMock()
            supervisor.spawn_actor = AsyncMock()

            election_mgr = _make_election_mgr_mock(trigger_result=leader_id)
            swarm = _make_swarm_mock(supervisor=supervisor, election_mgr=election_mgr)

            await _check_heartbeat_timeout(swarm, steward)

            # Leader elected log must reference the governor
            sentinel.log_leader_elected.assert_called_once()
            (_, kwargs) = sentinel.log_leader_elected.call_args
            assert kwargs["leader_id"] == leader_id

    @pytest.mark.asyncio
    @staticmethod
    async def test_sentinel_missing_falls_back_to_logger() -> None:
        """When sentinel is not in the supervisor actors, the code falls
        back to direct structlog calls (no crash)."""
        stale = _stale_timestamp(seconds_ago=20)
        steward = _make_steward_mock(
            last_heartbeat=stale,
            last_seen_heartbeat=stale,
        )
        supervisor = MagicMock()
        supervisor.actors = {"steward": steward}  # no sentinel
        supervisor.terminate_actor = AsyncMock()
        supervisor.spawn_actor = AsyncMock()

        election_mgr = _make_election_mgr_mock(trigger_result="alpha")
        swarm = _make_swarm_mock(supervisor=supervisor, election_mgr=election_mgr)

        # Should not raise — uses logger.info fallback
        await _check_heartbeat_timeout(swarm, steward)

        # New steward still spawned despite missing sentinel
        supervisor.spawn_actor.assert_called_once()

    @pytest.mark.asyncio
    @staticmethod
    async def test_sentinel_without_log_methods_falls_back() -> None:
        """When sentinel exists but lacks S03 log methods, fallback to
        direct structlog (no AttributeError)."""
        stale = _stale_timestamp(seconds_ago=20)
        steward = _make_steward_mock(
            last_heartbeat=stale,
            last_seen_heartbeat=stale,
        )
        sentinel = MagicMock()  # no log_election_* methods
        # Remove any auto-created methods
        del sentinel.log_election_started
        supervisor = MagicMock()
        supervisor.actors = {"steward": steward, "sentinel": sentinel}
        supervisor.terminate_actor = AsyncMock()
        supervisor.spawn_actor = AsyncMock()

        election_mgr = _make_election_mgr_mock(trigger_result="alpha")
        swarm = _make_swarm_mock(supervisor=supervisor, election_mgr=election_mgr)

        # Should not raise — hasattr checks protect
        await _check_heartbeat_timeout(swarm, steward)

        supervisor.spawn_actor.assert_called_once()

    @pytest.mark.asyncio
    @staticmethod
    async def test_terminate_failure_does_not_block_spawn() -> None:
        """If terminate_actor raises, spawn_actor should still be called
        (election proceeds despite cleanup error)."""
        stale = _stale_timestamp(seconds_ago=20)
        steward = _make_steward_mock(
            last_heartbeat=stale,
            last_seen_heartbeat=stale,
        )
        sentinel = _make_sentinel_mock()
        supervisor = MagicMock()
        supervisor.actors = {"steward": steward, "sentinel": sentinel}
        supervisor.terminate_actor = AsyncMock(
            side_effect=RuntimeError("terminate boom")
        )
        supervisor.spawn_actor = AsyncMock()

        election_mgr = _make_election_mgr_mock(trigger_result="alpha")
        swarm = _make_swarm_mock(supervisor=supervisor, election_mgr=election_mgr)

        # Should not raise — exception is caught and logged
        await _check_heartbeat_timeout(swarm, steward)

        supervisor.terminate_actor.assert_called_once()
        supervisor.spawn_actor.assert_called_once()


# ---------------------------------------------------------------------------
# Test: --no-infra skips election
# ---------------------------------------------------------------------------


class TestNoInfraSkipsElection:
    """When ``--no-infra`` is set, election machinery is absent."""

    @pytest.mark.asyncio
    @staticmethod
    async def test_no_election_manager_returns_early() -> None:
        """With ``_election_manager=None``, timeout check returns immediately."""
        steward = _make_steward_mock(
            last_heartbeat=_stale_timestamp(seconds_ago=20),
            last_seen_heartbeat=_stale_timestamp(seconds_ago=20),
        )
        swarm = _make_swarm_mock(election_mgr=None)

        # Should return immediately without error
        await _check_heartbeat_timeout(swarm, steward)

        # No election logic executed (no crash, no side effects)
        # internal_state cursor not modified since we bail before that
        # (the first guard returns before any state mutation)

    @pytest.mark.asyncio
    @staticmethod
    async def test_missing_election_manager_attribute_safe() -> None:
        """If ``_election_manager`` attribute itself is missing, bail
        gracefully (defensive — should not happen but guards exist)."""
        swarm = MagicMock()
        swarm.supervisor = None
        # Completely remove _election_manager attribute
        del swarm._election_manager

        steward = _make_steward_mock()

        # hasattr check protects
        await _check_heartbeat_timeout(swarm, steward)

    @pytest.mark.asyncio
    @staticmethod
    async def test_supervisor_none_safe() -> None:
        """If supervisor is None and _election_manager is None, bail."""
        steward = _make_steward_mock()
        swarm = _make_swarm_mock(supervisor=None, election_mgr=None)

        await _check_heartbeat_timeout(swarm, steward)


# ---------------------------------------------------------------------------
# Test: Election failure
# ---------------------------------------------------------------------------


class TestElectionFailsLogsTribunalElectionFailed:
    """When no leader emerges, ``tribunal_election_failed`` is logged."""

    @pytest.mark.asyncio
    @staticmethod
    async def test_election_failure_logs_tribunal_election_failed() -> None:
        """Mock trigger_election() → None; verify tribunal_election_failed
        log and no steward spawned."""
        stale = _stale_timestamp(seconds_ago=20)
        steward = _make_steward_mock(
            last_heartbeat=stale,
            last_seen_heartbeat=stale,
        )
        sentinel = _make_sentinel_mock()
        supervisor = MagicMock()
        supervisor.actors = {"steward": steward, "sentinel": sentinel}
        supervisor.terminate_actor = AsyncMock()
        supervisor.spawn_actor = AsyncMock()

        election_mgr = _make_election_mgr_mock(trigger_result=None)
        swarm = _make_swarm_mock(supervisor=supervisor, election_mgr=election_mgr)

        await _check_heartbeat_timeout(swarm, steward)

        # Election was started
        sentinel.log_election_started.assert_called_once()

        # Failure logged
        sentinel.log_election_failed.assert_called_once_with(cycles=3)

        # No steward was terminated or spawned
        supervisor.terminate_actor.assert_not_called()
        supervisor.spawn_actor.assert_not_called()

    @pytest.mark.asyncio
    @staticmethod
    async def test_election_failure_sentinel_missing_fallback() -> None:
        """Without sentinel, failure message falls back to logger.error."""
        stale = _stale_timestamp(seconds_ago=20)
        steward = _make_steward_mock(
            last_heartbeat=stale,
            last_seen_heartbeat=stale,
        )
        supervisor = MagicMock()
        supervisor.actors = {"steward": steward}  # no sentinel
        supervisor.terminate_actor = AsyncMock()
        supervisor.spawn_actor = AsyncMock()

        election_mgr = _make_election_mgr_mock(trigger_result=None)
        swarm = _make_swarm_mock(supervisor=supervisor, election_mgr=election_mgr)

        # Should not raise
        await _check_heartbeat_timeout(swarm, steward)

        supervisor.spawn_actor.assert_not_called()

    @pytest.mark.asyncio
    @staticmethod
    async def test_election_trigger_exception_graceful() -> None:
        """If trigger_election() raises, the exception is caught and no
        crash propagates."""
        stale = _stale_timestamp(seconds_ago=20)
        steward = _make_steward_mock(
            last_heartbeat=stale,
            last_seen_heartbeat=stale,
        )
        sentinel = _make_sentinel_mock()
        supervisor = MagicMock()
        supervisor.actors = {"steward": steward, "sentinel": sentinel}
        supervisor.terminate_actor = AsyncMock()
        supervisor.spawn_actor = AsyncMock()

        election_mgr = _make_election_mgr_mock()
        election_mgr.trigger_election = AsyncMock(
            side_effect=RuntimeError("election boom")
        )
        swarm = _make_swarm_mock(supervisor=supervisor, election_mgr=election_mgr)

        # Should not raise — exception is caught and logged
        await _check_heartbeat_timeout(swarm, steward)

        # No spawn since leader is None after exception
        supervisor.spawn_actor.assert_not_called()


# ---------------------------------------------------------------------------
# Test: Cursor update after timeout
# ---------------------------------------------------------------------------


class TestCursorUpdateAfterTimeout:
    """The heartbeat cursor is updated after timeout detection to prevent
    re-triggering on every pulse."""

    @pytest.mark.asyncio
    @staticmethod
    async def test_last_seen_heartbeat_updated_after_timeout() -> None:
        """After a timeout is detected and election runs, _last_seen_heartbeat
        is updated to the current _last_heartbeat value to prevent
        re-triggering."""
        stale = _stale_timestamp(seconds_ago=20)
        steward = _make_steward_mock(
            last_heartbeat=stale,
            last_seen_heartbeat=stale,
        )
        sentinel = _make_sentinel_mock()
        supervisor = MagicMock()
        supervisor.actors = {"steward": steward, "sentinel": sentinel}
        supervisor.terminate_actor = AsyncMock()
        supervisor.spawn_actor = AsyncMock()

        election_mgr = _make_election_mgr_mock(trigger_result="beta")
        swarm = _make_swarm_mock(supervisor=supervisor, election_mgr=election_mgr)

        await _check_heartbeat_timeout(swarm, steward)

        # Cursor must be updated so the next pulse won't re-trigger
        assert steward.internal_state["_last_seen_heartbeat"] == stale


# ---------------------------------------------------------------------------
# Test: Fresh heartbeat — no election
# ---------------------------------------------------------------------------


class TestFreshHeartbeatNoElection:
    """When the heartbeat is fresh, no election is triggered."""

    @pytest.mark.asyncio
    @staticmethod
    async def test_fresh_heartbeat_updates_cursor_no_election() -> None:
        """A fresh heartbeat (within timeout) updates the cursor and does
        not trigger an election."""
        fresh = (datetime.now(UTC) - timedelta(seconds=2)).isoformat()
        prev_seen = (datetime.now(UTC) - timedelta(seconds=4)).isoformat()

        steward = _make_steward_mock(
            last_heartbeat=fresh,
            last_seen_heartbeat=prev_seen,
        )

        election_mgr = _make_election_mgr_mock()
        swarm = _make_swarm_mock(election_mgr=election_mgr)

        await _check_heartbeat_timeout(swarm, steward)

        # Cursor updated to fresh heartbeat value
        assert steward.internal_state["_last_seen_heartbeat"] == fresh

        # No election triggered
        election_mgr.trigger_election.assert_not_called()

    @pytest.mark.asyncio
    @staticmethod
    async def test_first_pulse_seeds_cursor_no_election() -> None:
        """On the first pulse (_last_seen_heartbeat is not set), the cursor
        is seeded and no election is triggered."""
        stale = _stale_timestamp(seconds_ago=20)
        # _last_seen_heartbeat is not set — simulating first pulse
        steward = _make_steward_mock(
            last_heartbeat=stale,
            last_seen_heartbeat=None,
        )

        election_mgr = _make_election_mgr_mock()
        swarm = _make_swarm_mock(election_mgr=election_mgr)

        await _check_heartbeat_timeout(swarm, steward)

        # Cursor seeded with current _last_heartbeat
        assert steward.internal_state["_last_seen_heartbeat"] == stale

        # No election triggered
        election_mgr.trigger_election.assert_not_called()

    @pytest.mark.asyncio
    @staticmethod
    async def test_no_heartbeat_yet_seeds_no_election() -> None:
        """If _last_heartbeat is None (no heartbeat recorded yet), bail."""
        steward = _make_steward_mock(
            last_heartbeat=None,
            last_seen_heartbeat=None,
        )

        election_mgr = _make_election_mgr_mock()
        swarm = _make_swarm_mock(election_mgr=election_mgr)

        await _check_heartbeat_timeout(swarm, steward)

        election_mgr.trigger_election.assert_not_called()


# ---------------------------------------------------------------------------
# Test: Malformed timestamps
# ---------------------------------------------------------------------------


class TestMalformedTimestamps:
    """Malformed timestamps are handled defensively."""

    @pytest.mark.asyncio
    @staticmethod
    async def test_malformed_last_heartbeat_bails_gracefully() -> None:
        """If _last_heartbeat cannot be parsed as ISO, bail without crash."""
        steward = _make_steward_mock(
            last_heartbeat="not-a-valid-date",
            last_seen_heartbeat="not-a-valid-date",
        )
        election_mgr = _make_election_mgr_mock()
        swarm = _make_swarm_mock(election_mgr=election_mgr)

        await _check_heartbeat_timeout(swarm, steward)

        # No election triggered
        election_mgr.trigger_election.assert_not_called()

    @pytest.mark.asyncio
    @staticmethod
    async def test_malformed_prev_seen_bails_gracefully() -> None:
        """If _last_seen_heartbeat cannot be parsed, bail without crash."""
        stale = _stale_timestamp(seconds_ago=20)
        steward = _make_steward_mock(
            last_heartbeat=stale,
            last_seen_heartbeat="garbage-timestamp",
        )
        election_mgr = _make_election_mgr_mock()
        swarm = _make_swarm_mock(election_mgr=election_mgr)

        await _check_heartbeat_timeout(swarm, steward)

        election_mgr.trigger_election.assert_not_called()
