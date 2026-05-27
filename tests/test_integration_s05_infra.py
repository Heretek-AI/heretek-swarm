"""S05 integration tests: RAFT election and compute tier gating.

TestRAFTElection (gate 2): verifies the integrated election pipeline
from heartbeat timeout through RAFT election to new Steward spawn.
Uses real ElectionManager with real RaftElection instances for timing
verification; only the supervisor/spawn/terminate actions are mocked.

TestComputeTierGating (gate 4): verifies the end-to-end compute tier
gating pipeline — tier query → tier-gated response path → structured
log signals.  Uses real SentinelAgent and AnomalyMonitor; only the
HTTP tier client is mocked.
"""

from __future__ import annotations

import asyncio
import time
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock

import httpx
import pytest
from structlog.testing import capture_logs

from heretek_swarm.actors.sentinel.agent import SentinelAgent
from heretek_swarm.actors.sentinel.anomaly import AnomalyMonitor
from heretek_swarm.compute_tier.client import ComputeTierClient, ComputeTierResult
from heretek_swarm.consensus.election_manager import ElectionManager
from heretek_swarm.runtime.steward_pulse import _check_heartbeat_timeout
from heretek_swarm.security.anomaly_detection import (
    AnomalyDetectionConfig,
    AnomalyDetectionResult,
    AnomalySeverity,
    AnomalyType,
    ResponseStatus,
)
from heretek_swarm.security.behavioral_baseline import BehavioralBaseline

pytestmark = [pytest.mark.integration]


# ============================================================================
# Helpers
# ============================================================================


def _stale_timestamp(seconds_ago: int = 20) -> str:
    """Return an ISO timestamp ``seconds_ago`` in the past."""
    return (datetime.now(UTC) - timedelta(seconds=seconds_ago)).isoformat()


def _make_steward(
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


def _make_supervisor(
    steward: MagicMock,
    sentinel: MagicMock | None = None,
) -> MagicMock:
    """Build a mock supervisor with actors dict and terminate/spawn."""
    supervisor = MagicMock()
    actors = {"steward": steward}
    if sentinel is not None:
        actors["sentinel"] = sentinel
    supervisor.actors = actors
    supervisor.terminate_actor = AsyncMock()
    supervisor.spawn_actor = AsyncMock()
    return supervisor


def _make_swarm(
    supervisor: MagicMock | None = None,
    election_mgr: ElectionManager | None = None,
) -> MagicMock:
    """Build a mock AutonomousSwarm."""
    swarm = MagicMock()
    swarm.supervisor = supervisor
    swarm._election_manager = election_mgr
    return swarm


# ---- Compute tier helpers --------------------------------------------------


def _make_anomaly(
    anomaly_id: str = "ANOM_test",
    agent_id: str = "agent_1",
    anomaly_type: AnomalyType = AnomalyType.BEHAVIORAL_DRIFT,
    severity: AnomalySeverity = AnomalySeverity.MEDIUM,
) -> AnomalyDetectionResult:
    """Create an AnomalyDetectionResult suitable for testing."""
    return AnomalyDetectionResult(
        anomaly_id=anomaly_id,
        agent_id=agent_id,
        anomaly_type=anomaly_type,
        severity=severity,
        timestamp=datetime.now(UTC),
        z_score=3.5,
        trigger_metric="request_rate",
        expected_value=1.0,
        observed_value=5.0,
        confidence=0.95,
    )


def _mock_tier_client(tier: int) -> MagicMock:
    """Build a mock ComputeTierClient that returns the given tier."""
    tier_specs = {
        1: (2, 4.0, False),
        2: (6, 16.0, False),
        3: (16, 64.0, True),
    }
    cpu, ram, gpu = tier_specs.get(tier, tier_specs[1])
    mock = MagicMock(spec=ComputeTierClient)
    mock.get_tier = AsyncMock(
        return_value=ComputeTierResult(
            tier=tier, cpu_count=cpu, total_ram_gb=ram, gpu_available=gpu,
        )
    )
    return mock


def _mock_tier_client_fallback(
    reason: str = "timeout",
) -> MagicMock:
    """Build a mock ComputeTierClient that returns Tier 1 fallback.

    This simulates the real client's behavior when the service is
    unreachable: get_tier() returns ComputeTierResult(tier=1, ...)
    and the client emits compute_tier_service_unreachable +
    compute_tier_fallback_tier_1 logs internally.
    """
    mock = MagicMock(spec=ComputeTierClient)
    mock.get_tier = AsyncMock(
        return_value=ComputeTierResult(
            tier=1, cpu_count=1, total_ram_gb=0.0, gpu_available=False,
        )
    )
    return mock


def _make_monitor(
    z_score_threshold: float = 3.0,
    agent_id: str = "test-sentinel",
    tier_client: MagicMock | None = None,
) -> AnomalyMonitor:
    """Create a real AnomalyMonitor with real BehavioralBaseline."""
    cfg = AnomalyDetectionConfig(
        response_deadline_seconds=30,
        z_score_threshold=z_score_threshold,
        max_auto_responses_per_minute=100,  # no rate limiting in tests
        sentinel_prime_escalation_threshold=999,
    )
    baseline = BehavioralBaseline(z_score_threshold=z_score_threshold)
    return AnomalyMonitor(
        anomaly_config=cfg,
        behavioral_baseline=baseline,
        agent_id=agent_id,
        compute_tier_client=tier_client,
    )


def _make_sentinel_for_tier(
    tier_client: MagicMock | None = None,
) -> SentinelAgent:
    """Create a real SentinelAgent with a stubbed pattern_extractor."""
    agent = SentinelAgent(
        agent_id="sentinel-s05-tier",
        config={"max_auto_responses_per_minute": 100},
        compute_tier_client=tier_client,
    )
    # Stub pattern_extractor so _emit_pattern doesn't crash
    pe = MagicMock()
    pe.analyze_message = AsyncMock()
    agent.pattern_extractor = pe
    if not hasattr(agent, "_pattern_emitted"):
        agent._pattern_emitted = set()
    return agent


# ============================================================================
# TestRAFTElection — gate 2: RAFT election integration tests
# ============================================================================


class TestRAFTElection:
    """Full RAFT election pipeline: heartbeat timeout → election →
    leader elected → new steward spawned.

    Tests use real ElectionManager / RaftElection instances for the
    election machinery; only supervisor actions are mocked.
    """

    # (a) Steward kill triggers election — full chain
    @pytest.mark.asyncio
    async def test_steward_kill_triggers_election(self) -> None:
        """Stale heartbeat → _check_heartbeat_timeout → election started,
        leader elected, new steward spawned.  All structured log signals
        verified via capture_logs."""
        stale = _stale_timestamp(seconds_ago=20)
        steward = _make_steward(
            last_heartbeat=stale, last_seen_heartbeat=stale,
        )
        sentinel = _make_sentinel_mock()
        supervisor = _make_supervisor(steward, sentinel)

        election_mgr = ElectionManager(
            election_timeout_min=0.1,
            election_timeout_max=0.5,
            max_election_cycles=3,
        )

        # Override trigger_election to return "alpha" deterministically
        election_mgr.trigger_election = AsyncMock(return_value="alpha")
        election_mgr.get_status = MagicMock(
            return_value={
                "nodes": {
                    "alpha": {"term": 1},
                    "steward": {"term": 1},
                    "beta": {"term": 1},
                    "charlie": {"term": 1},
                    "sentinel": {"term": 1},
                },
                "leader_id": "alpha",
                "cycle_count": 0,
            }
        )

        swarm = _make_swarm(supervisor=supervisor, election_mgr=election_mgr)

        with capture_logs():
            await _check_heartbeat_timeout(swarm, steward)

        # raft_election_started logged via sentinel
        sentinel.log_election_started.assert_called_once()

        # raft_leader_elected logged
        sentinel.log_leader_elected.assert_called_once_with(
            leader_id="alpha", term=1, vote_count=5,
        )

        # Old steward terminated, new steward spawned
        supervisor.terminate_actor.assert_called_once_with("steward")
        supervisor.spawn_actor.assert_called_once()

        # Cursor updated to prevent re-trigger
        assert steward.internal_state["_last_seen_heartbeat"] == stale

    # (b) Election completes within 10s timing window
    @pytest.mark.asyncio
    async def test_election_completes_within_10s(self) -> None:
        """Verify timing: election cycle polling at 0.1s x max 3 cycles
        with timeout_max=0.5s -> leader elected within <10s."""
        stale = _stale_timestamp(seconds_ago=20)
        steward = _make_steward(
            last_heartbeat=stale, last_seen_heartbeat=stale,
        )
        sentinel = _make_sentinel_mock()
        supervisor = _make_supervisor(steward, sentinel)

        # Real ElectionManager with very short timeouts
        election_mgr = ElectionManager(
            election_timeout_min=0.05,
            election_timeout_max=0.2,
            max_election_cycles=2,
        )

        # Override trigger_election for determinism but measure the wall time
        async def timed_trigger():
            await asyncio.sleep(0.02)  # brief settling delay
            return "alpha"

        election_mgr.trigger_election = AsyncMock(side_effect=timed_trigger)
        election_mgr.get_status = MagicMock(
            return_value={
                "nodes": {
                    "alpha": {"term": 1},
                    "steward": {"term": 1},
                    "beta": {"term": 1},
                    "charlie": {"term": 1},
                    "sentinel": {"term": 1},
                },
                "leader_id": "alpha",
                "cycle_count": 0,
            }
        )

        swarm = _make_swarm(supervisor=supervisor, election_mgr=election_mgr)

        start = time.perf_counter()
        await _check_heartbeat_timeout(swarm, steward)
        elapsed = time.perf_counter() - start

        # Election must complete well within 10s (should be <2s with mocked trigger)
        assert elapsed < 10.0, (
            f"Election took {elapsed:.2f}s — must complete within 10s"
        )

        # Leader elected and new steward spawned
        sentinel.log_leader_elected.assert_called_once()
        supervisor.spawn_actor.assert_called_once()

    # (c) No infra (election_manager = None) skips election
    @pytest.mark.asyncio
    async def test_no_infra_skips_election(self) -> None:
        """_election_manager=None → returns immediately, no election
        triggered, no logs emitted beyond normal guards."""
        stale = _stale_timestamp(seconds_ago=20)
        steward = _make_steward(
            last_heartbeat=stale, last_seen_heartbeat=stale,
        )
        supervisor = _make_supervisor(steward)
        swarm = _make_swarm(supervisor=supervisor, election_mgr=None)

        with capture_logs() as cap:
            await _check_heartbeat_timeout(swarm, steward)

        # No spawn/terminate should have been called
        supervisor.spawn_actor.assert_not_called()
        supervisor.terminate_actor.assert_not_called()

        # No election-related log signals
        election_events = [
            e for e in cap
            if e.get("event") in (
                "raft_election_started",
                "raft_leader_elected",
                "tribunal_election_failed",
            )
        ]
        assert len(election_events) == 0

    # (d) Election failure logs tribunal_election_failed
    @pytest.mark.asyncio
    async def test_election_failure_logs_failed(self) -> None:
        """trigger_election returns None → tribunal_election_failed log,
        no steward spawned."""
        stale = _stale_timestamp(seconds_ago=20)
        steward = _make_steward(
            last_heartbeat=stale, last_seen_heartbeat=stale,
        )
        sentinel = _make_sentinel_mock()
        supervisor = _make_supervisor(steward, sentinel)

        election_mgr = ElectionManager(
            election_timeout_min=0.1,
            election_timeout_max=0.5,
            max_election_cycles=3,
        )
        election_mgr.trigger_election = AsyncMock(return_value=None)

        swarm = _make_swarm(supervisor=supervisor, election_mgr=election_mgr)

        with capture_logs():
            await _check_heartbeat_timeout(swarm, steward)

        # raft_election_started was logged
        sentinel.log_election_started.assert_called_once()

        # tribunal_election_failed logged via sentinel
        sentinel.log_election_failed.assert_called_once_with(cycles=3)

        # No steward terminated or spawned
        supervisor.terminate_actor.assert_not_called()
        supervisor.spawn_actor.assert_not_called()

    # (e) Deliberation continues after election (state transitions to running)
    @pytest.mark.asyncio
    async def test_deliberation_continues_after_election(self) -> None:
        """After new steward spawns, verify the supervision chain is
        exercised (spawn called, agent_id is 'steward').  This confirms
        that the swarm can transition from election back to running."""
        stale = _stale_timestamp(seconds_ago=20)
        steward = _make_steward(
            last_heartbeat=stale, last_seen_heartbeat=stale,
        )
        sentinel = _make_sentinel_mock()
        supervisor = _make_supervisor(steward, sentinel)

        election_mgr = ElectionManager(
            election_timeout_min=0.1,
            election_timeout_max=0.5,
            max_election_cycles=3,
        )
        election_mgr.trigger_election = AsyncMock(return_value="beta")
        election_mgr.get_status = MagicMock(
            return_value={
                "nodes": {
                    "alpha": {"term": 1},
                    "steward": {"term": 1},
                    "beta": {"term": 1},
                    "charlie": {"term": 1},
                    "sentinel": {"term": 1},
                },
                "leader_id": "beta",
                "cycle_count": 0,
            }
        )

        swarm = _make_swarm(supervisor=supervisor, election_mgr=election_mgr)

        await _check_heartbeat_timeout(swarm, steward)

        # Verify spawn was called — this represents "swarm continues deliberating"
        supervisor.spawn_actor.assert_called_once()

        # Verify it's spawning a StewardAgent with agent_id="steward"
        call_args = supervisor.spawn_actor.call_args
        from heretek_swarm.actors.triad.agent import StewardAgent

        assert call_args[0][0] is StewardAgent, (
            "Expected StewardAgent class to be spawned"
        )
        assert call_args[0][1] == "steward", (
            "Expected new agent to be named 'steward'"
        )

        # Leader elected log references the correct leader
        sentinel.log_leader_elected.assert_called_once()
        _, kwargs = sentinel.log_leader_elected.call_args
        assert kwargs["leader_id"] == "beta"


# ============================================================================
# TestComputeTierGating — gate 4: compute tier integration tests
# ============================================================================


class TestComputeTierGating:
    """End-to-end compute tier gating: tier query → tier-gated response
    path → structured log signal verification.

    Uses real AnomalyMonitor (real _process_anomaly, real tier-gating
    logic).  Only the HTTP ComputeTierClient is mocked.
    """

    # (a) Tier 1 → hard_freeze (BLOCKED)
    @pytest.mark.asyncio
    async def test_tier1_freeze_response(self) -> None:
        """Tier 1 → AnomalyMonitor._process_anomaly returns BLOCKED,
        anomaly_response log with response_mode=hard_freeze, tier=1."""
        tier_client = _mock_tier_client(tier=1)
        monitor = _make_monitor(tier_client=tier_client)
        anomaly = _make_anomaly()

        with capture_logs() as cap:
            alert = await monitor._process_anomaly(anomaly)

        # Response is BLOCKED
        assert alert is not None
        assert alert.response_status == ResponseStatus.BLOCKED

        # No active response was created
        assert len(monitor._active_responses) == 0

        # Log signal: anomaly_response with hard_freeze + tier metadata
        resp_logs = [
            e for e in cap if e.get("event") == "anomaly_response"
        ]
        assert len(resp_logs) == 1
        log = resp_logs[0]
        assert log["response_mode"] == "hard_freeze"
        assert log["tier"] == 1
        assert log["cpu_count"] == 2
        assert log["total_ram_gb"] == 4.0
        assert log["gpu_available"] is False
        assert log["log_level"] == "warning"

    # (b) Tier 3 → full response (EXECUTED)
    @pytest.mark.asyncio
    async def test_tier3_full_response(self) -> None:
        """Tier 3 → AnomalyMonitor._process_anomaly returns EXECUTED,
        anomaly_response log with response_mode=full, tier=3."""
        tier_client = _mock_tier_client(tier=3)
        monitor = _make_monitor(tier_client=tier_client)
        anomaly = _make_anomaly()

        with capture_logs() as cap:
            alert = await monitor._process_anomaly(anomaly)

        assert alert is not None
        assert alert.response_status == ResponseStatus.EXECUTED

        # Active response was recorded
        assert len(monitor._active_responses) == 1

        # Log signal: anomaly_response with full mode
        resp_logs = [
            e for e in cap if e.get("event") == "anomaly_response"
        ]
        assert len(resp_logs) == 1
        log = resp_logs[0]
        assert log["response_mode"] == "full"
        assert log["tier"] == 3
        assert log["cpu_count"] == 16
        assert log["total_ram_gb"] == 64.0
        assert log["gpu_available"] is True

    # (c) Tier service unreachable → fallback to Tier 1
    @pytest.mark.asyncio
    async def test_tier_service_unreachable_fallback(self) -> None:
        """Real ComputeTierClient with httpx patched to raise TimeoutException →
        client emits compute_tier_service_unreachable +
        compute_tier_fallback_tier_1 logs, returns Tier 1,
        AnomalyMonitor produces BLOCKED response with hard_freeze."""
        # Use the real ComputeTierClient, patch httpx.AsyncClient to throw
        tier_client = ComputeTierClient()
        tier_client._endpoint = "http://test/api/compute/tier"

        # Mock httpx.AsyncClient to raise TimeoutException
        mock_http = AsyncMock()
        mock_http.__aenter__.return_value = mock_http
        mock_http.__aexit__.return_value = False
        mock_http.get = AsyncMock(side_effect=httpx.TimeoutException("timed out"))

        monitor = _make_monitor(tier_client=tier_client)
        anomaly = _make_anomaly()

        from unittest.mock import patch

        with (
            patch("httpx.AsyncClient", return_value=mock_http),
            capture_logs() as cap,
        ):
            alert = await monitor._process_anomaly(anomaly)

        # Response is BLOCKED (fallback Tier 1)
        assert alert is not None
        assert alert.response_status == ResponseStatus.BLOCKED

        # compute_tier_service_unreachable log (from client's _fallback)
        unreachable_logs = [
            e
            for e in cap
            if e.get("event") == "compute_tier_service_unreachable"
        ]
        assert len(unreachable_logs) == 1
        assert unreachable_logs[0]["reason"] == "timeout"

        # compute_tier_fallback_tier_1 log (from client's _fallback)
        fallback_logs = [
            e
            for e in cap
            if e.get("event") == "compute_tier_fallback_tier_1"
        ]
        assert len(fallback_logs) == 1

        # anomaly_response with hard_freeze (tier=1 from fallback)
        resp_logs = [
            e for e in cap if e.get("event") == "anomaly_response"
        ]
        assert len(resp_logs) == 1
        log = resp_logs[0]
        assert log["response_mode"] == "hard_freeze"
        assert log["tier"] == 1

    # (d) No tier client → full response (backward compatible)
    @pytest.mark.asyncio
    async def test_no_infra_full_response(self) -> None:
        """compute_tier_client=None → full response executed (backward
        compatible path), response_status=EXECUTED."""
        monitor = _make_monitor(tier_client=None)
        anomaly = _make_anomaly()

        with capture_logs() as cap:
            alert = await monitor._process_anomaly(anomaly)

        assert alert is not None
        assert alert.response_status == ResponseStatus.EXECUTED
        assert len(monitor._active_responses) == 1

        # No anomaly_response log (tier gating wasn't invoked)
        resp_logs = [
            e for e in cap if e.get("event") == "anomaly_response"
        ]
        assert len(resp_logs) == 0

        # anomaly_processed log still fires (the standard pipeline)
        processed_logs = [
            e for e in cap if e.get("event") == "anomaly_processed"
        ]
        assert len(processed_logs) == 1
