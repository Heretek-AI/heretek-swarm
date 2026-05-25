"""Tests for TierCircuitBreaker and ActorSupervisor integration.

Covers:
- TierCircuitBreaker.record_failure opens circuit after >=5 failures in 60s
- is_open returns True after threshold, False before
- reset clears open circuit
- Sliding window — old failures expire, circuit auto-closes
- Tier classification from agent_id prefix (classify_tier)
- Contract test: mock ActorSupervisor with 5 rapid _attempt_restart failures
  for same tier — verify circuit_open log signal and restart blocked
"""

from __future__ import annotations

import asyncio
import time
from unittest.mock import MagicMock, AsyncMock, patch

import pytest
import structlog
from structlog.testing import capture_logs

from heretek_swarm.actors.circuit_breaker import TierCircuitBreaker, TIER_MAP
from heretek_swarm.actors.supervisor import ActorSupervisor

pytestmark = [pytest.mark.unit]


# ---------------------------------------------------------------------------
# Tier classification
# ---------------------------------------------------------------------------

class TestClassifyTier:
    """classify_tier() maps agent_id prefixes to tier labels."""

    def test_triad_agents(self) -> None:
        assert TierCircuitBreaker.classify_tier("alpha-1") == "triad"
        assert TierCircuitBreaker.classify_tier("beta_primary") == "triad"
        assert TierCircuitBreaker.classify_tier("charlie") == "triad"
        assert TierCircuitBreaker.classify_tier("steward-main") == "triad"

    def test_analyst_agents(self) -> None:
        assert TierCircuitBreaker.classify_tier("historian-archival") == "analyst"
        assert TierCircuitBreaker.classify_tier("metis-reasoner") == "analyst"
        assert TierCircuitBreaker.classify_tier("empath-1") == "analyst"

    def test_specialist_agents(self) -> None:
        assert TierCircuitBreaker.classify_tier("coder-primary") == "specialist"
        # architect is also mapped to 'specialist'
        assert TierCircuitBreaker.classify_tier("architect-main") == "specialist"

    def test_core_agents(self) -> None:
        assert TierCircuitBreaker.classify_tier("sentinel-1") == "core"
        assert TierCircuitBreaker.classify_tier("sentinel_prime-2") == "core"
        assert TierCircuitBreaker.classify_tier("arbiter-1") == "core"

    def test_coordination_agents(self) -> None:
        assert TierCircuitBreaker.classify_tier("nexus-1") == "coordination"
        assert TierCircuitBreaker.classify_tier("coordinator") == "coordination"
        assert TierCircuitBreaker.classify_tier("catalyst-1") == "coordination"
        assert TierCircuitBreaker.classify_tier("chronos-1") == "coordination"

    def test_unknown_prefix_falls_back_to_agent_id(self) -> None:
        assert TierCircuitBreaker.classify_tier("unknown-agent-42") == "unknown-agent-42"


# ---------------------------------------------------------------------------
# TierCircuitBreaker – record_failure & is_open
# ---------------------------------------------------------------------------

class TestRecordFailureAndIsOpen:
    """Core behaviour: record_failure opens circuit after threshold."""

    def test_below_threshold_circuit_closed(self) -> None:
        cb = TierCircuitBreaker(failure_threshold=5, window_seconds=60)
        for _ in range(4):
            opened = cb.record_failure("triad")
            assert not opened
        assert not cb.is_open("triad")

    def test_at_threshold_circuit_opens(self) -> None:
        cb = TierCircuitBreaker(failure_threshold=5, window_seconds=60)
        for _ in range(4):
            cb.record_failure("triad")
        # 5th failure should return True (circuit just opened)
        assert cb.record_failure("triad") is True
        assert cb.is_open("triad")

    def test_above_threshold_returns_false_after_opening(self) -> None:
        """After circuit is open, further record_failure calls return False
        (not a *new* opening)."""
        cb = TierCircuitBreaker(failure_threshold=5, window_seconds=60)
        for _ in range(5):
            cb.record_failure("triad")
        # 6th failure — circuit was already open
        assert cb.record_failure("triad") is False

    def test_is_open_false_for_unknown_tier(self) -> None:
        cb = TierCircuitBreaker(failure_threshold=5, window_seconds=60)
        assert not cb.is_open("nonexistent")


# ---------------------------------------------------------------------------
# TierCircuitBreaker – reset
# ---------------------------------------------------------------------------

class TestReset:
    """reset() clears the open circuit and failure window."""

    def test_reset_closes_circuit(self) -> None:
        cb = TierCircuitBreaker(failure_threshold=3, window_seconds=60)
        for _ in range(3):
            cb.record_failure("triad")
        assert cb.is_open("triad")

        cb.reset("triad")
        assert not cb.is_open("triad")

    def test_reset_clears_window(self) -> None:
        cb = TierCircuitBreaker(failure_threshold=3, window_seconds=60)
        for _ in range(5):
            cb.record_failure("triad")

        cb.reset("triad")
        # After reset, a fresh failure should NOT open the circuit
        assert cb.record_failure("triad") is False
        assert not cb.is_open("triad")

    def test_reset_idempotent(self) -> None:
        cb = TierCircuitBreaker()
        cb.reset("nonexistent")  # Should not raise
        assert not cb.is_open("nonexistent")


# ---------------------------------------------------------------------------
# TierCircuitBreaker – sliding window expiry
# ---------------------------------------------------------------------------

class TestSlidingWindowExpiry:
    """Old failures expire from the window; circuit auto-closes."""

    @pytest.mark.slow
    def test_old_failures_expire_circuit_auto_closes(self) -> None:
        """After window_seconds have passed, the circuit auto-closes
        on the next is_open() check."""
        cb = TierCircuitBreaker(failure_threshold=3, window_seconds=1)
        for _ in range(3):
            cb.record_failure("triad")
        assert cb.is_open("triad")

        # Wait for the window to expire.
        time.sleep(1.1)

        # is_open should auto-close after lazy eviction.
        assert not cb.is_open("triad")

    def test_record_failure_evicts_expired_before_counting(self) -> None:
        """When recording a failure, expired timestamps are evicted first,
        so a burst spaced out by the window doesn't trip the circuit."""
        cb = TierCircuitBreaker(failure_threshold=3, window_seconds=0.5)
        # Record 2 failures.
        cb.record_failure("triad")
        cb.record_failure("triad")

        # Wait for them to expire.
        time.sleep(1.0)

        # New failure — expired ones are evicted, so count starts at 1.
        opened = cb.record_failure("triad")
        assert not opened
        assert not cb.is_open("triad")


# ---------------------------------------------------------------------------
# Contract test: ActorSupervisor integration
# ---------------------------------------------------------------------------

class TestActorSupervisorCircuitBreaker:
    """Verify circuit breaker integration in _attempt_restart()."""

    @pytest.mark.asyncio
    async def test_circuit_breaker_created_in_init(self) -> None:
        supervisor = ActorSupervisor(name="test-sup", max_restarts=3)
        assert supervisor._circuit_breaker is not None  # noqa: SLF001
        assert isinstance(supervisor._circuit_breaker, TierCircuitBreaker)  # noqa: SLF001

    @pytest.mark.asyncio
    async def test_restart_blocked_when_circuit_open(self) -> None:
        """When the circuit is open for a tier, _attempt_restart logs
        circuit_broken_restart_blocked and returns early without restarting."""
        supervisor = ActorSupervisor(name="test-sup", max_restarts=3)

        # Manually open the circuit for 'triad'
        supervisor._circuit_breaker._open_circuits.add("triad")  # noqa: SLF001

        # Register a mock actor in the triad tier so _attempt_restart finds it
        mock_actor = MagicMock()
        mock_actor.get_status.return_value = MagicMock(state="ERROR")
        # We need a valid terminate() method
        mock_actor.terminate = AsyncMock()
        supervisor.actors["alpha-1"] = mock_actor
        supervisor.restart_counts["alpha-1"] = 0
        supervisor.actor_configs["alpha-1"] = MagicMock()

        with capture_logs() as cap:
            await supervisor._attempt_restart("alpha-1")  # noqa: SLF001

        blocked_logs = [
            e for e in cap
            if e.get("event") == "circuit_broken_restart_blocked"
        ]
        assert len(blocked_logs) == 1
        assert blocked_logs[0]["extra"]["tier"] == "triad"
        assert blocked_logs[0]["extra"]["actor_id"] == "alpha-1"

        # The mock should NOT have been terminated (restart was blocked)
        mock_actor.terminate.assert_not_called()

    @pytest.mark.asyncio
    async def test_circuit_open_logged_after_five_restart_failures(self) -> None:
        """Five failed restarts in the same tier log circuit_open signal."""
        supervisor = ActorSupervisor(name="test-sup", max_restarts=5)

        tier = "triad"

        # Create a mock actor with a known config whose spawn() will fail.
        for i in range(5):
            actor_id = f"alpha-{i}"
            mock_actor = MagicMock()
            # terminate() must succeed so we reach the except block
            mock_actor.terminate = AsyncMock()
            supervisor.actors[actor_id] = mock_actor
            supervisor.restart_counts[actor_id] = 0
            # Create a config whose spawn() raises.
            config = MagicMock()
            config.class_ref = MagicMock()
            # Make the spawned actor fail at spawn()
            config.class_ref.return_value = MagicMock()
            config.class_ref.return_value.spawn = AsyncMock(
                side_effect=RuntimeError("simulated failure")
            )
            config.init_kwargs = {"agent_id": actor_id}
            supervisor.actor_configs[actor_id] = config

        with capture_logs() as cap:
            # Trigger 5 failed restarts on the same tier.
            for i in range(5):
                actor_id = f"alpha-{i}"
                await supervisor._attempt_restart(actor_id)  # noqa: SLF001

        # The 5th failure should trigger circuit_open.
        circuit_open_logs = [
            e for e in cap
            if e.get("event") == "circuit_open"
        ]
        assert len(circuit_open_logs) == 1
        assert circuit_open_logs[0]["extra"]["tier"] == tier
        assert circuit_open_logs[0]["extra"]["failure_count"] == 5
        assert circuit_open_logs[0]["extra"]["threshold"] == 5

        # Verify the circuit is open now.
        assert supervisor._circuit_breaker.is_open(tier)  # noqa: SLF001

        # A 6th restart attempt should be blocked.
        mock_actor6 = MagicMock()
        mock_actor6.terminate = AsyncMock()
        supervisor.actors["alpha-6"] = mock_actor6
        supervisor.restart_counts["alpha-6"] = 0
        config6 = MagicMock()
        config6.class_ref = MagicMock()
        config6.class_ref.return_value = MagicMock()
        config6.class_ref.return_value.spawn = AsyncMock(
            side_effect=RuntimeError("simulated failure")
        )
        config6.init_kwargs = {"agent_id": "alpha-6"}
        supervisor.actor_configs["alpha-6"] = config6

        with capture_logs() as cap2:
            await supervisor._attempt_restart("alpha-6")  # noqa: SLF001

        blocked = [
            e for e in cap2
            if e.get("event") == "circuit_broken_restart_blocked"
        ]
        assert len(blocked) == 1
        mock_actor6.terminate.assert_not_called()

    @pytest.mark.asyncio
    async def test_restart_proceeds_when_circuit_is_closed(self) -> None:
        """When circuit is closed and restart succeeds, no blocking occurs."""
        supervisor = ActorSupervisor(name="test-sup", max_restarts=3)

        mock_actor = MagicMock()
        mock_actor.terminate = AsyncMock()
        supervisor.actors["coder-1"] = mock_actor
        supervisor.restart_counts["coder-1"] = 0

        config = MagicMock()
        # spawn() succeeds
        new_instance = MagicMock()
        new_instance.spawn = AsyncMock()
        config.class_ref = MagicMock(return_value=new_instance)
        config.init_kwargs = {"agent_id": "coder-1"}
        supervisor.actor_configs["coder-1"] = config

        with capture_logs() as cap:
            await supervisor._attempt_restart("coder-1")  # noqa: SLF001

        # No blocking log should appear
        blocked = [
            e for e in cap
            if e.get("event") == "circuit_broken_restart_blocked"
        ]
        assert len(blocked) == 0

        # Actor should have been terminated and re-spawned
        mock_actor.terminate.assert_called_once()

    @pytest.mark.asyncio
    async def test_restart_single_failure_does_not_open_circuit(self) -> None:
        """A single restart failure increments the window but doesn't open."""
        supervisor = ActorSupervisor(name="test-sup", max_restarts=3)

        mock_actor = MagicMock()
        mock_actor.terminate = AsyncMock()
        supervisor.actors["beta-1"] = mock_actor
        supervisor.restart_counts["beta-1"] = 0

        config = MagicMock()
        config.class_ref = MagicMock()
        config.class_ref.return_value = MagicMock()
        config.class_ref.return_value.spawn = AsyncMock(
            side_effect=RuntimeError("simulated failure")
        )
        config.init_kwargs = {"agent_id": "beta-1"}
        supervisor.actor_configs["beta-1"] = config

        with capture_logs() as cap:
            await supervisor._attempt_restart("beta-1")  # noqa: SLF001

        # circuit_open should NOT be logged.
        open_logs = [
            e for e in cap
            if e.get("event") == "circuit_open"
        ]
        assert len(open_logs) == 0
        assert not supervisor._circuit_breaker.is_open("triad")  # noqa: SLF001


# ============================================================================
# T04: Circuit breaker integration test — restart storm prevention contract
# ============================================================================


_SPECIALIST_AGENTS = [
    f"coder-{i}" for i in range(6)
]


class TestCircuitBreakerIntegration:
    """T04 Part B: 5 agents in same tier, forced restart failures → circuit
    opens on 5th failure → 6th blocked.  Contract test for restart storm
    prevention per the slice acceptance criteria."""

    @pytest.mark.asyncio
    async def test_five_same_tier_failures_opens_circuit_and_blocks_sixth(
        self,
    ) -> None:
        """Spawn 5 agents in 'specialist' tier, _attempt_restart all with
        forced failure.  Circuit opens on 5th.  6th restart blocked."""
        supervisor = ActorSupervisor(name="test-sup-t04", max_restarts=5)

        tier = "specialist"
        agent_ids = _SPECIALIST_AGENTS[:5]  # 5 agents in specialist tier
        agent_6 = _SPECIALIST_AGENTS[5]

        # Register 5 stub agents with failing spawn configs
        for agent_id in agent_ids:
            mock_actor = MagicMock()
            mock_actor.terminate = AsyncMock()
            supervisor.actors[agent_id] = mock_actor
            supervisor.restart_counts[agent_id] = 0
            config = MagicMock()
            config.class_ref = MagicMock()
            config.class_ref.return_value = MagicMock()
            config.class_ref.return_value.spawn = AsyncMock(
                side_effect=RuntimeError("simulated failure")
            )
            config.init_kwargs = {"agent_id": agent_id}
            supervisor.actor_configs[agent_id] = config

        # Trigger 5 restarts — each fails
        circuit_open_logs: list[dict] = []
        for i, agent_id in enumerate(agent_ids):
            with capture_logs() as cap:
                await supervisor._attempt_restart(agent_id)  # noqa: SLF001

            open_events = [e for e in cap if e.get("event") == "circuit_open"]
            circuit_open_logs.extend(open_events)

            if i < 4:
                assert len(open_events) == 0, (
                    f"Restart {i+1}: circuit should not open yet"
                )

        # 5th failure → circuit_open emitted
        assert len(circuit_open_logs) == 1, (
            f"Expected 1 circuit_open after 5th failure, "
            f"got {len(circuit_open_logs)}"
        )
        assert circuit_open_logs[0]["extra"]["tier"] == tier
        assert circuit_open_logs[0]["extra"]["failure_count"] >= 5
        assert circuit_open_logs[0]["extra"]["threshold"] == 5

        # Circuit is open
        assert supervisor._circuit_breaker.is_open(tier)  # noqa: SLF001

        # ── 6th restart attempt — must be blocked ──
        mock_actor6 = MagicMock()
        mock_actor6.terminate = AsyncMock()
        supervisor.actors[agent_6] = mock_actor6
        supervisor.restart_counts[agent_6] = 0
        config6 = MagicMock()
        config6.class_ref = MagicMock()
        config6.class_ref.return_value = MagicMock()
        config6.class_ref.return_value.spawn = AsyncMock(
            side_effect=RuntimeError("simulated failure")
        )
        config6.init_kwargs = {"agent_id": agent_6}
        supervisor.actor_configs[agent_6] = config6

        with capture_logs() as cap6:
            await supervisor._attempt_restart(agent_6)  # noqa: SLF001

        blocked = [
            e for e in cap6
            if e.get("event") == "circuit_broken_restart_blocked"
        ]
        assert len(blocked) == 1, (
            f"6th restart attempt should be blocked, got {len(blocked)} blocked events"
        )
        assert blocked[0]["extra"]["tier"] == tier
        assert blocked[0]["extra"]["actor_id"] == agent_6

        # 6th agent must not be terminated (restart path short-circuited)
        mock_actor6.terminate.assert_not_called()

    @pytest.mark.asyncio
    async def test_circuit_open_metadata_matches_expectations(self) -> None:
        """The circuit_open log signal carries all required metadata:
        tier, failure_count, window_seconds, threshold, supervisor."""
        supervisor = ActorSupervisor(name="test-sup-meta", max_restarts=5)

        tier = "core"
        agent_ids = ["sentinel-1", "sentinel-2", "sentinel_prime-1", "arbiter-1", "sentinel-3"]

        for agent_id in agent_ids:
            mock_actor = MagicMock()
            mock_actor.terminate = AsyncMock()
            supervisor.actors[agent_id] = mock_actor
            supervisor.restart_counts[agent_id] = 0
            config = MagicMock()
            config.class_ref = MagicMock()
            config.class_ref.return_value = MagicMock()
            config.class_ref.return_value.spawn = AsyncMock(
                side_effect=RuntimeError("simulated failure")
            )
            config.init_kwargs = {"agent_id": agent_id}
            supervisor.actor_configs[agent_id] = config

        circuit_open_logs: list[dict] = []
        for agent_id in agent_ids:
            with capture_logs() as cap:
                await supervisor._attempt_restart(agent_id)  # noqa: SLF001
            circuit_open_logs.extend(
                [e for e in cap if e.get("event") == "circuit_open"]
            )

        assert len(circuit_open_logs) == 1
        log = circuit_open_logs[0]
        assert log["extra"]["tier"] == tier
        assert log["extra"]["failure_count"] >= 5
        assert log["extra"]["window_seconds"] == 60
        assert log["extra"]["threshold"] == 5
        assert log["extra"]["supervisor"] == "test-sup-meta"

    @pytest.mark.asyncio
    async def test_circuit_breaker_pauses_restarts_but_not_other_tiers(
        self,
    ) -> None:
        """When 'specialist' tier circuit is open, agents in 'analyst'
        tier can still restart normally."""
        supervisor = ActorSupervisor(name="test-sup-isolated", max_restarts=5)

        # Open the circuit for specialist tier
        specialist_ids = [f"coder-{i}" for i in range(5)]
        for agent_id in specialist_ids:
            mock_actor = MagicMock()
            mock_actor.terminate = AsyncMock()
            supervisor.actors[agent_id] = mock_actor
            supervisor.restart_counts[agent_id] = 0
            config = MagicMock()
            config.class_ref = MagicMock()
            config.class_ref.return_value = MagicMock()
            config.class_ref.return_value.spawn = AsyncMock(
                side_effect=RuntimeError("simulated failure")
            )
            config.init_kwargs = {"agent_id": agent_id}
            supervisor.actor_configs[agent_id] = config

        # Trigger 5 failures for specialist tier
        for agent_id in specialist_ids:
            await supervisor._attempt_restart(agent_id)  # noqa: SLF001

        assert supervisor._circuit_breaker.is_open("specialist")  # noqa: SLF001

        # Analyst tier: circuit is still closed
        assert not supervisor._circuit_breaker.is_open("analyst")  # noqa: SLF001

        # Attempt restart in analyst tier — should proceed
        mock_historian = MagicMock()
        mock_historian.terminate = AsyncMock()
        supervisor.actors["historian-1"] = mock_historian
        supervisor.restart_counts["historian-1"] = 0
        config_h = MagicMock()
        new_historian = MagicMock()
        new_historian.spawn = AsyncMock()
        config_h.class_ref = MagicMock(return_value=new_historian)
        config_h.init_kwargs = {"agent_id": "historian-1"}
        supervisor.actor_configs["historian-1"] = config_h

        with capture_logs() as cap:
            await supervisor._attempt_restart("historian-1")  # noqa: SLF001

        blocked = [
            e for e in cap
            if e.get("event") == "circuit_broken_restart_blocked"
        ]
        assert len(blocked) == 0, (
            "Analyst tier should NOT be blocked when specialist circuit is open"
        )
        mock_historian.terminate.assert_called_once()

    @pytest.mark.asyncio
    async def test_circuit_blocked_restart_does_not_increment_restart_count(
        self,
    ) -> None:
        """When circuit blocks a restart, the agent's restart_count is unchanged."""
        supervisor = ActorSupervisor(name="test-sup-count", max_restarts=5)

        # Setup: register agent and open its circuit manually
        mock_actor = MagicMock()
        mock_actor.terminate = AsyncMock()
        supervisor.actors["alpha-1"] = mock_actor
        supervisor.restart_counts["alpha-1"] = 2  # already restarted twice

        supervisor._circuit_breaker._open_circuits.add("triad")  # noqa: SLF001

        # Attempt restart → blocked
        await supervisor._attempt_restart("alpha-1")  # noqa: SLF001

        # restart_count unchanged
        assert supervisor.restart_counts["alpha-1"] == 2

        # actor not terminated
        mock_actor.terminate.assert_not_called()
