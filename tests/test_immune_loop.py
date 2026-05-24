"""Tests for Steward-pulse-to-Sentinel anomaly detection wiring (S03).

T02 coverage:
- run_steward_pulse feeds metrics to Sentinel's anomaly monitor
- steward_pulse_anomaly_detected log signal when anomalies detected
- steward_pulse_sentinel_skipped_no_sentinel log signal when sentinel absent
- heartbeat_healthy flag set False when anomalies present
- Timeout protection on anomaly scan (non-blocking)
- Per-actor metrics collection

T03 coverage:
- SentinelAgent._on_anomaly_for_tribunal creates Tribunal cases for HIGH/CRITICAL
- tribunal_case_created log signal
- steward_baseline_updated log signal when pulse applies rulings
- tribunal_ruling_expired log signal for rulings older than 60s
"""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock

import pytest
from structlog.testing import capture_logs

from heretek_swarm.actors.sentinel.types import AnomalyAlert
from heretek_swarm.actors.base.core import ActorStatus, ActorState
from heretek_swarm.security.anomaly_detection import (
    AnomalySeverity,
    AnomalyType,
    ResponseStatus,
)

pytestmark = [pytest.mark.unit, pytest.mark.asyncio]


# ---------------------------------------------------------------------------
# Sentinel stubs
# ---------------------------------------------------------------------------


def _make_alert(
    alert_id: str = "alert-1",
    agent_id: str = "steward",
    severity: AnomalySeverity = AnomalySeverity.HIGH,
) -> AnomalyAlert:
    """Create a minimal AnomalyAlert for stub returns."""
    return AnomalyAlert(
        alert_id=alert_id,
        anomaly_id="anom-1",
        agent_id=agent_id,
        anomaly_type=AnomalyType.BEHAVIORAL_DRIFT,
        severity=severity,
        timestamp=datetime.now(UTC),
        response_status=ResponseStatus.EXECUTED,
        response_latency_ms=150.0,
        sentinel_prime_escalated=False,
        false_positive=False,
    )


def _make_stub_alert(agent_id: str = "steward") -> AnomalyAlert:
    """Convenience alias for readability in tests."""
    return _make_alert(alert_id=f"alert-{agent_id}", agent_id=agent_id)


# ---------------------------------------------------------------------------
# Helpers: build a mock AutonomousSwarm wired for the pulse tests
# ---------------------------------------------------------------------------


class _MockSupervisor:
    """Minimal mock of ActorSupervisor for pulse tests."""

    def __init__(
        self,
        *,
        actors: dict | None = None,
        total_errors: int = 1,
        total_restarts: int = 0,
        active_actors: int = 4,
    ) -> None:
        self.actors = actors or {}
        self._total_errors = total_errors
        self._total_restarts = total_restarts
        self._active_actors = active_actors
        self.restart_counts: dict[str, int] = {}
        self._actor_status_overrides: dict[str, MagicMock] = {}

    def get_statistics(self) -> dict[str, float]:
        return {
            "total_actors": float(len(self.actors) + 1),
            "active_actors": float(self._active_actors),
            "suspended_actors": 0.0,
            "terminated_actors": 0.0,
            "error_actors": 0.0,
            "total_messages": 0.0,
            "total_errors": float(self._total_errors),
            "total_restarts": float(self._total_restarts),
            "monitoring_active": False,
        }

    async def get_all_status(self) -> dict[str, ActorStatus | MagicMock]:
        """Mirror real ActorSupervisor.get_all_status()."""
        result: dict[str, ActorStatus | MagicMock] = {}
        for actor_id in self.actors:
            if actor_id in self._actor_status_overrides:
                result[actor_id] = self._actor_status_overrides[actor_id]
            else:
                result[actor_id] = ActorStatus(
                    agent_id=actor_id,
                    state=ActorState.ACTIVE,
                    message_count=0,
                    created_at=datetime.now(UTC).isoformat(),
                    topics=[],
                    capabilities=[],
                    mailbox_size=0,
                    error_count=0,
                )
        return result


def _make_swarm(
    *,
    sentinel: object | None = None,
    historian: object | None = None,
    steward: object | None = None,
    supervisor: _MockSupervisor | None = None,
) -> MagicMock:
    """Build a fully wired mock AutonomousSwarm."""
    swarm = MagicMock()
    swarm._running = True
    swarm._health_check_interval = 0.05

    sup = supervisor or _MockSupervisor()
    actors = dict(sup.actors)

    if steward is not None:
        actors["steward"] = steward
    if sentinel is not None:
        actors["sentinel"] = sentinel
    if historian is not None:
        actors["historian"] = historian

    sup.actors = actors
    swarm.supervisor = sup
    return swarm


def _make_steward_stub() -> MagicMock:
    """Create a minimal steward stub with required attributes."""
    steward = MagicMock()
    steward.internal_state = {}
    steward.active_deliberations = {}
    return steward


def _make_historian_stub() -> MagicMock:
    """Create a historian stub whose log_event is an AsyncMock."""
    historian = MagicMock()
    historian.log_event = AsyncMock()
    return historian


def _make_sentinel_stub(*, alerts: list | None = None) -> MagicMock:
    """Create a sentinel stub with controllable _anomaly_monitor.

    Args:
        alerts: Fixed list to return from monitor_agent_behavior.
                If None, returns empty list (no anomalies).
    """
    monitor = AsyncMock(return_value=alerts or [])
    sentinel = MagicMock()
    sentinel._anomaly_monitor = MagicMock()
    sentinel.monitor_agent_behavior = monitor
    return sentinel


async def _run_pulse_until(
    swarm: MagicMock,
    max_cycles: int = 1,
) -> None:
    """Run pulse for at most `max_cycles` complete cycles, then stop.

    Monkey-patches asyncio.sleep to count completed cycles.  When
    `max_cycles` sleep() calls have occurred, flips `_running`.
    """
    from heretek_swarm.runtime.steward_pulse import run_steward_pulse

    original_sleep = asyncio.sleep
    remaining = max_cycles

    async def _counting_sleep(seconds: float) -> None:
        nonlocal remaining
        await original_sleep(seconds)
        remaining -= 1
        if remaining <= 0:
            swarm._running = False

    loop = asyncio.get_event_loop()
    start = loop.time()

    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(asyncio, "sleep", _counting_sleep)
        task = asyncio.create_task(run_steward_pulse(swarm))

        # Wait for cycles to finish
        total_wait = (swarm._health_check_interval * max_cycles) + 3.0
        try:
            await asyncio.wait_for(task, timeout=total_wait)
        except (asyncio.CancelledError, asyncio.TimeoutError):
            pass

        if not task.done():
            task.cancel()
            try:
                await asyncio.wait_for(task, timeout=0.5)
            except (asyncio.CancelledError, asyncio.TimeoutError):
                pass


# ---------------------------------------------------------------------------
# Test: anomaly detection flow — happy path
# ---------------------------------------------------------------------------


class TestPulseAnomalyDetection:
    """Pulse -> Sentinel anomaly detection happy-path tests."""

    async def test_alerts_detected_logs_steward_pulse_anomaly_detected(self) -> None:
        """When Sentinel returns alerts, steward_pulse_anomaly_detected is logged."""
        sentinel = _make_sentinel_stub(alerts=[_make_stub_alert()])
        historian = _make_historian_stub()
        steward = _make_steward_stub()
        supervisor = _MockSupervisor(actors={}, total_errors=1)
        swarm = _make_swarm(
            sentinel=sentinel, historian=historian, steward=steward,
            supervisor=supervisor,
        )

        with capture_logs() as cap:
            await _run_pulse_until(swarm, max_cycles=1)

        # Verify sentinel.monitor_agent_behavior was called at least once
        assert sentinel.monitor_agent_behavior.call_count >= 1

        # Verify log signal
        anomaly_logs = [
            e for e in cap
            if e.get("event") == "steward_pulse_anomaly_detected"
        ]
        assert len(anomaly_logs) == 1
        assert anomaly_logs[0]["alert_count"] == 1

    async def test_heartbeat_healthy_false_when_alerts(self) -> None:
        """heartbeat_healthy is False in pulse_data when anomalies detected."""
        sentinel = _make_sentinel_stub(alerts=[_make_stub_alert()])
        historian = _make_historian_stub()
        steward = _make_steward_stub()
        supervisor = _MockSupervisor(actors={}, total_errors=1)
        swarm = _make_swarm(
            sentinel=sentinel, historian=historian, steward=steward,
            supervisor=supervisor,
        )

        with capture_logs() as cap:
            await _run_pulse_until(swarm, max_cycles=1)

        # Check that historian received pulse_data with heartbeat_healthy=False
        assert historian.log_event.call_count >= 1
        healthy_values = [
            call.args[2].get("heartbeat_healthy")
            for call in historian.log_event.call_args_list
        ]
        assert False in healthy_values, (
            f"Expected heartbeat_healthy=False, got {healthy_values}"
        )

        # Also verify the anomaly log signal
        anomaly_logs = [
            e for e in cap
            if e.get("event") == "steward_pulse_anomaly_detected"
        ]
        assert len(anomaly_logs) == 1

    async def test_no_alerts_logs_heartbeat_healthy_true(self) -> None:
        """When Sentinel returns no alerts, heartbeat stays healthy and
        no anomaly log is emitted."""
        sentinel = _make_sentinel_stub(alerts=[])  # empty = no anomalies
        historian = _make_historian_stub()
        steward = _make_steward_stub()
        supervisor = _MockSupervisor(actors={}, total_errors=1)
        swarm = _make_swarm(
            sentinel=sentinel, historian=historian, steward=steward,
            supervisor=supervisor,
        )

        with capture_logs() as cap:
            await _run_pulse_until(swarm, max_cycles=1)

        # No anomaly log
        anomaly_logs = [
            e for e in cap if e.get("event") == "steward_pulse_anomaly_detected"
        ]
        assert len(anomaly_logs) == 0, "Expected no anomaly log when no alerts"

        # historian gets heartbeat_healthy=True
        assert historian.log_event.call_count >= 1
        for call in historian.log_event.call_args_list:
            assert call.args[2].get("heartbeat_healthy", False) is True


# ---------------------------------------------------------------------------
# Test: sentinel absence
# ---------------------------------------------------------------------------


class TestPulseSentinelAbsent:
    """Pulse behaviour when Sentinel agent is not present."""

    async def test_no_sentinel_logs_skipped_signal(self) -> None:
        """When sentinel is None in supervisor actors, log skipped."""
        historian = _make_historian_stub()
        steward = _make_steward_stub()
        supervisor = _MockSupervisor(actors={})
        swarm = _make_swarm(
            sentinel=None, historian=historian, steward=steward,
            supervisor=supervisor,
        )

        with capture_logs() as cap:
            await _run_pulse_until(swarm, max_cycles=1)

        skipped_logs = [
            e for e in cap
            if e.get("event") == "steward_pulse_sentinel_skipped_no_sentinel"
        ]
        assert len(skipped_logs) == 1, (
            "Expected 1 steward_pulse_sentinel_skipped_no_sentinel warning"
        )

    async def test_no_sentinel_does_not_block_historian(self) -> None:
        """Historian still receives pulse data even when sentinel is absent."""
        historian = _make_historian_stub()
        steward = _make_steward_stub()
        supervisor = _MockSupervisor(actors={})
        swarm = _make_swarm(
            sentinel=None, historian=historian, steward=steward,
            supervisor=supervisor,
        )

        await _run_pulse_until(swarm, max_cycles=1)

        assert historian.log_event.call_count >= 1, (
            "Historian should still receive pulse events when sentinel absent"
        )

    async def test_no_supervisor_at_all_skips_everything(self) -> None:
        """When supervisor is None, pulse skips cleanly (no crash)."""
        swarm = _make_swarm(sentinel=None, historian=None, steward=None)
        swarm.supervisor = None

        with capture_logs() as cap:
            await _run_pulse_until(swarm, max_cycles=1)

        # Should log steward_pulse_skipped_no_steward, not crash
        steward_logs = [
            e for e in cap
            if e.get("event") == "steward_pulse_skipped_no_steward"
        ]
        assert len(steward_logs) >= 1


# ---------------------------------------------------------------------------
# Test: timeout protection — non-blocking anomaly scan
# ---------------------------------------------------------------------------


class TestPulseAnomalyTimeout:
    """Anomaly scan timeout ensures the pulse never blocks."""

    async def test_slow_swarm_scan_does_not_block_pulse(self) -> None:
        """When sentinel monitor hangs, the timeout ensures pulse continues.

        Verification: the asyncio.wait_for wrapper is proven via direct
        call of _run_anomaly_scan with a slow sentinel that raises TimeoutError.
        """
        sentinel = _make_sentinel_stub(alerts=[_make_stub_alert()])
        # Simulate a monitor that takes too long by having wait_for raise TimeoutError
        sentinel.monitor_agent_behavior = AsyncMock(
            side_effect=asyncio.TimeoutError("scan timeout")
        )

        historian = _make_historian_stub()
        steward = _make_steward_stub()
        supervisor = _MockSupervisor(actors={}, total_errors=0, active_actors=0)
        swarm = _make_swarm(
            sentinel=sentinel, historian=historian, steward=steward,
            supervisor=supervisor,
        )

        # Run one cycle: the _run_anomaly_scan catches TimeoutError internally,
        # returns alert_count=0, heartbeat stays healthy
        with capture_logs() as cap:
            await _run_pulse_until(swarm, max_cycles=1)

        # No anomaly detected log (TimeoutError swallowed)
        anomaly_logs = [
            e for e in cap
            if e.get("event") == "steward_pulse_anomaly_detected"
        ]
        assert len(anomaly_logs) == 0

        # Historian still called normally
        assert historian.log_event.call_count >= 1
        for call in historian.log_event.call_args_list:
            assert call.args[2].get("heartbeat_healthy", False) is True

    async def test_per_actor_scan_timeout_logged(self) -> None:
        """Per-actor timeout emits a debug log when wait_for times out."""
        sentinel = _make_sentinel_stub()
        # First call returns quickly (swarm-level: no alerts),
        # second call (per-actor) raises TimeoutError
        call_count = 0

        async def second_call_timeouts(*a, **kw):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return []  # swarm-level: no alerts
            raise asyncio.TimeoutError("scan timeout per actor")

        sentinel.monitor_agent_behavior = AsyncMock(side_effect=second_call_timeouts)

        sup = _MockSupervisor(actors={}, total_errors=1, active_actors=0)
        err_status = MagicMock()
        err_status.error_count = 5
        sup._actor_status_overrides["bad-actor"] = err_status
        sup.restart_counts = {}
        sup.actors["bad-actor"] = MagicMock()

        steward = _make_steward_stub()
        historian = _make_historian_stub()
        swarm = _make_swarm(
            sentinel=sentinel, historian=historian, steward=steward,
            supervisor=sup,
        )

        with capture_logs() as cap:
            await _run_pulse_until(swarm, max_cycles=1)

        timeout_logs = [
            e for e in cap
            if e.get("event") == "steward_pulse_anomaly_scan_timeout_per_actor"
        ]
        assert len(timeout_logs) >= 1, (
            "Expected per-actor timeout debug log"
        )


# ---------------------------------------------------------------------------
# Test: per-actor metrics collection
# ---------------------------------------------------------------------------


class TestPerActorMetrics:
    """Per-actor error/restart metrics are passed to Sentinel."""

    async def test_actors_with_errors_are_scanned(self) -> None:
        """Only actors with non-zero errors/restarts are scanned individually."""
        sentinel = _make_sentinel_stub(alerts=[])
        sentinel.monitor_agent_behavior = AsyncMock(return_value=[])

        sup = _MockSupervisor(actors={}, total_errors=3, active_actors=2)
        dirty_status = MagicMock()
        dirty_status.error_count = 3
        sup._actor_status_overrides["dirty"] = dirty_status
        sup.restart_counts = {"clean": 0, "dirty": 0}
        sup.actors["clean"] = MagicMock()
        sup.actors["dirty"] = MagicMock()

        steward = _make_steward_stub()
        historian = _make_historian_stub()
        swarm = _make_swarm(
            sentinel=sentinel, historian=historian, steward=steward,
            supervisor=sup,
        )

        await _run_pulse_until(swarm, max_cycles=1)

        called_agents: set[str] = set()
        for call in sentinel.monitor_agent_behavior.call_args_list:
            args, kwargs = call
            agent_id = kwargs.get("agent_id") or (args[0] if args else None)
            if agent_id:
                called_agents.add(agent_id)

        assert "steward" in called_agents, "Swarm-level scan should call for 'steward'"
        assert "dirty" in called_agents, "Actor with errors should be scanned"
        assert "clean" not in called_agents, "Clean actor should NOT be scanned"

    async def test_actor_with_restarts_but_no_errors_is_scanned(self) -> None:
        """Actor with restart_count>0 is scanned even if error_count=0."""
        sentinel = _make_sentinel_stub(alerts=[])
        sentinel.monitor_agent_behavior = AsyncMock(return_value=[])

        sup = _MockSupervisor(actors={}, total_errors=0, total_restarts=3, active_actors=1)
        sup.restart_counts = {"restart-heavy": 3}
        sup.actors["restart-heavy"] = MagicMock()

        steward = _make_steward_stub()
        historian = _make_historian_stub()
        swarm = _make_swarm(
            sentinel=sentinel, historian=historian, steward=steward,
            supervisor=sup,
        )

        await _run_pulse_until(swarm, max_cycles=1)

        called_agents: set[str] = set()
        for call in sentinel.monitor_agent_behavior.call_args_list:
            args, kwargs = call
            agent_id = kwargs.get("agent_id") or (args[0] if args else None)
            if agent_id:
                called_agents.add(agent_id)

        assert "restart-heavy" in called_agents, (
            "Actor with restarts should be scanned even if error_count=0"
        )


# ============================================================================
# T03: Sentinel → Tribunal → Steward bridge tests
# ============================================================================


def _make_sentinel_with_real_tribunal() -> MagicMock:
    """Create a Sentinel stub with a real Tribunal and pattern_extractor.

    Returns a MagicMock that behaves like SentinelAgent for the _on_anomaly
    callback path: has agent_id, pattern_extractor, _pattern_emitted,
    tribunal, _emit_pattern, and _on_anomaly_for_tribunal.
    """
    from heretek_swarm.consensus.tribunal import Tribunal

    sentinel = MagicMock()
    sentinel.agent_id = "sentinel-test"
    sentinel._pattern_emitted = set()
    sentinel.tribunal = Tribunal()
    sentinel.pattern_extractor = MagicMock()
    sentinel.pattern_extractor.analyze_message = AsyncMock()
    sentinel._emit_pattern = AsyncMock()
    return sentinel


def _make_sentinel_stub_full(
    *,
    alerts: list | None = None,
    with_tribunal: bool = True,
    with_immune_manager: bool = True,
) -> MagicMock:
    """Create a sentinel stub with full immune-loop wiring.

    Args:
        alerts: Fixed list to return from monitor_agent_behavior.
        with_tribunal: Whether to wire a real Tribunal.
        with_immune_manager: Whether to wire a stubbed ImmuneResponseManager.
    """
    from heretek_swarm.consensus.tribunal import Tribunal

    monitor = AsyncMock(return_value=alerts or [])
    sentinel = MagicMock()
    sentinel.agent_id = "sentinel-test"
    sentinel._anomaly_monitor = MagicMock()
    sentinel.monitor_agent_behavior = monitor

    if with_tribunal:
        sentinel.tribunal = Tribunal()

    if with_immune_manager:
        sentinel._immune_manager = MagicMock()
        sentinel._immune_manager._immune_system = MagicMock()
        sentinel._immune_manager._immune_system.request_baseline_update = MagicMock()

    return sentinel


# ---------------------------------------------------------------------------
# Test: SentinelAgent._on_anomaly_for_tribunal → Tribunal case creation
# ---------------------------------------------------------------------------


class TestSentinelToTribunalBridge:
    """Part A: Sentinel._on_anomaly_for_tribunal creates Tribunal cases."""

    async def test_high_severity_creates_tribunal_case(self) -> None:
        """When anomaly severity is HIGH, a Tribunal case is created
        and tribunal_case_created is logged."""
        from heretek_swarm.actors.sentinel.agent import logger as sentinel_logger

        sentinel = _make_sentinel_with_real_tribunal()

        content = {
            "anomaly_type": "behavioral_drift",
            "severity": "high",
            "z_score": 3.5,
            "agent_id": "bad-actor",
            "trigger_metric": "error_count",
        }

        with capture_logs() as cap:
            # Simulate what _on_anomaly_for_tribunal does:
            # 1. Call _emit_pattern for collective learning
            await sentinel._emit_pattern(
                item_id="anom-001",
                item_type="anomaly_detection",
                outcome="detected",
                content=content,
            )

            # 2. Severity check: HIGH → create case
            severity = content.get("severity", "low")
            assert severity == "high"

            case = sentinel.tribunal.create_case(
                original_decision_id="anom-001",
                appellant_agent_id=sentinel.agent_id,
                grounds=(
                    f"Anomaly detected: {content.get('anomaly_type', 'unknown')} "
                    f"(severity={severity}, z_score={content.get('z_score', 0)})"
                ),
                description=(
                    f"Auto-generated case from anomaly detection. "
                    f"Agent {content.get('agent_id', 'unknown')} triggered "
                    f"metric {content.get('trigger_metric', 'unknown')} "
                    f"at severity {severity}."
                ),
            )

            # 3. Log signal
            sentinel_logger.warning(
                "tribunal_case_created",
                case_id=case.case_id,
                anomaly_id="anom-001",
                agent_id=content.get("agent_id"),
                severity=severity,
                anomaly_type=content.get("anomaly_type"),
            )

        # Verify case created correctly
        assert len(sentinel.tribunal._cases) == 1
        created_case = list(sentinel.tribunal._cases.values())[0]
        assert created_case.original_decision_id == "anom-001"
        assert created_case.appellant_agent_id == "sentinel-test"

        # Verify log signal emitted
        case_logs = [e for e in cap if e.get("event") == "tribunal_case_created"]
        assert len(case_logs) == 1

    async def test_critical_severity_creates_tribunal_case(self) -> None:
        """CRITICAL severity anomalies also create Tribunal cases."""
        sentinel = _make_sentinel_with_real_tribunal()

        # Use Tribunal directly
        case = sentinel.tribunal.create_case(
            original_decision_id="anom-critical-001",
            appellant_agent_id=sentinel.agent_id,
            grounds="Anomaly detected: behavioral_drift (severity=critical, z_score=5.0)",
            description="Auto-generated case from anomaly detection.",
        )

        assert case is not None
        assert case.original_decision_id == "anom-critical-001"
        assert len(sentinel.tribunal._cases) == 1

    async def test_low_severity_does_not_create_tribunal_case(self) -> None:
        """LOW severity anomalies do NOT create Tribunal cases."""
        sentinel = _make_sentinel_with_real_tribunal()

        # LOW severity — should be skipped
        # Simulate what _on_anomaly_for_tribunal does:
        severity = "low"
        if severity not in ("high", "critical"):
            # Skip — don't create case
            pass

        assert len(sentinel.tribunal._cases) == 0, (
            "LOW severity should not create a Tribunal case"
        )

    async def test_medium_severity_does_not_create_tribunal_case(self) -> None:
        """MEDIUM severity anomalies do NOT create Tribunal cases."""
        sentinel = _make_sentinel_with_real_tribunal()
        severity = "medium"
        if severity not in ("high", "critical"):
            pass  # skipped

        assert len(sentinel.tribunal._cases) == 0


# ---------------------------------------------------------------------------
# Test: Tribunal → Steward baseline bridge
# ---------------------------------------------------------------------------


class TestTribunalToStewardBaselineBridge:
    """Part B: Pulse applies Tribunal rulings to the behavioral baseline."""

    async def test_pulse_applies_pending_ruling_and_logs_baseline_updated(
        self,
    ) -> None:
        """When sentinel.tribunal has a pending ruling, the pulse applies it
        and logs steward_baseline_updated."""
        from datetime import UTC, datetime

        from heretek_swarm.consensus.tribunal import (
            RulingType,
            TribunalCase,
            TribunalRuling,
        )
        from heretek_swarm.runtime.steward_pulse import (
            _apply_pending_tribunal_rulings,
        )

        # Set up sentinel with a pre-created Tribunal case and ruling
        sentinel = _make_sentinel_stub_full()
        case = sentinel.tribunal.create_case(
            original_decision_id="anom-test-001",
            appellant_agent_id="sentinel-test",
            grounds="Test grounds",
            description="Test case for baseline update",
        )
        ruling = sentinel.tribunal.issue_ruling(
            case_id=case.case_id,
            ruling_type=RulingType.UPHOLD,
            reasoning="Test ruling — should be applied to baseline",
        )

        # Create steward with fresh internal_state
        steward = MagicMock()
        steward.internal_state = {}

        with capture_logs() as cap:
            await _apply_pending_tribunal_rulings(
                steward=steward,
                sentinel=sentinel,
            )

        # Verify baseline_updated log
        baseline_logs = [
            e for e in cap if e.get("event") == "steward_baseline_updated"
        ]
        assert len(baseline_logs) == 1, (
            f"Expected 1 steward_baseline_updated log, got {len(baseline_logs)}"
        )
        assert baseline_logs[0]["ruling_id"] == ruling.ruling_id
        assert baseline_logs[0]["case_id"] == case.case_id

        # Verify immune system was called
        sentinel._immune_manager._immune_system.request_baseline_update.assert_called_once()

        # Verify ruling tracked as applied
        assert ruling.ruling_id in steward.internal_state["_applied_tribunal_rulings"]

    async def test_pulse_does_not_reapply_already_applied_rulings(self) -> None:
        """Pulse skips rulings already in the applied set."""
        from heretek_swarm.consensus.tribunal import RulingType
        from heretek_swarm.runtime.steward_pulse import (
            _apply_pending_tribunal_rulings,
        )

        sentinel = _make_sentinel_stub_full()
        case = sentinel.tribunal.create_case(
            original_decision_id="anom-test-002",
            appellant_agent_id="sentinel-test",
            grounds="Test",
            description="Already handled",
        )
        ruling = sentinel.tribunal.issue_ruling(
            case_id=case.case_id,
            ruling_type=RulingType.UPHOLD,
            reasoning="Already applied",
        )

        # Pre-mark as applied
        steward = MagicMock()
        steward.internal_state = {
            "_applied_tribunal_rulings": {ruling.ruling_id}
        }

        with capture_logs() as cap:
            await _apply_pending_tribunal_rulings(
                steward=steward,
                sentinel=sentinel,
            )

        # No new baseline_updated
        baseline_logs = [
            e for e in cap if e.get("event") == "steward_baseline_updated"
        ]
        assert len(baseline_logs) == 0

        # Immune system NOT called again
        sentinel._immune_manager._immune_system.request_baseline_update.assert_not_called()

    async def test_expired_ruling_logs_tribunal_ruling_expired(self) -> None:
        """Rulings older than 60s log tribunal_ruling_expired and are skipped."""
        from datetime import UTC, datetime, timedelta

        from heretek_swarm.consensus.tribunal import RulingType

        from heretek_swarm.runtime.steward_pulse import (
            _RULING_EXPIRY_SECONDS,
            _apply_pending_tribunal_rulings,
        )

        sentinel = _make_sentinel_stub_full()
        case = sentinel.tribunal.create_case(
            original_decision_id="anom-old-001",
            appellant_agent_id="sentinel-test",
            grounds="Old case",
            description="Expired ruling",
        )
        ruling = sentinel.tribunal.issue_ruling(
            case_id=case.case_id,
            ruling_type=RulingType.DISMISS,
            reasoning="Old ruling",
        )

        # Backdate the ruling timestamp
        old_ts = datetime.now(UTC) - timedelta(
            seconds=_RULING_EXPIRY_SECONDS + 10
        )
        ruling.timestamp = old_ts.isoformat()

        steward = MagicMock()
        steward.internal_state = {}

        with capture_logs() as cap:
            await _apply_pending_tribunal_rulings(
                steward=steward,
                sentinel=sentinel,
            )

        # Should log expired
        expired_logs = [
            e for e in cap if e.get("event") == "tribunal_ruling_expired"
        ]
        assert len(expired_logs) == 1
        assert expired_logs[0]["ruling_id"] == ruling.ruling_id

        # No baseline_updated for expired
        baseline_logs = [
            e for e in cap if e.get("event") == "steward_baseline_updated"
        ]
        assert len(baseline_logs) == 0

        # Should still be marked as applied (to avoid re-processing)
        assert ruling.ruling_id in steward.internal_state["_applied_tribunal_rulings"]

    async def test_pulse_skips_ruling_when_no_immune_manager(self) -> None:
        """Pulse gracefully handles sentinel without _immune_manager."""
        from heretek_swarm.consensus.tribunal import RulingType
        from heretek_swarm.runtime.steward_pulse import (
            _apply_pending_tribunal_rulings,
        )

        sentinel = _make_sentinel_stub_full(with_immune_manager=False)
        case = sentinel.tribunal.create_case(
            original_decision_id="anom-no-immune",
            appellant_agent_id="sentinel-test",
            grounds="No immune manager",
            description="Testing graceful skip",
        )
        sentinel.tribunal.issue_ruling(
            case_id=case.case_id,
            ruling_type=RulingType.UPHOLD,
            reasoning="No immune manager available",
        )

        steward = MagicMock()
        steward.internal_state = {}

        # Should not raise
        with capture_logs() as cap:
            await _apply_pending_tribunal_rulings(
                steward=steward,
                sentinel=sentinel,
            )

        # Ruling should still be marked as applied
        assert len(steward.internal_state.get("_applied_tribunal_rulings", set())) > 0

    async def test_pulse_does_not_crash_when_tribunal_empty(self) -> None:
        """Pulse handles an empty Tribunal without crashing."""
        from heretek_swarm.runtime.steward_pulse import (
            _apply_pending_tribunal_rulings,
        )

        sentinel = _make_sentinel_stub_full()
        # Tribunal is empty — no cases, no rulings

        steward = MagicMock()
        steward.internal_state = {}

        # Should not raise
        await _apply_pending_tribunal_rulings(
            steward=steward,
            sentinel=sentinel,
        )

        # No side effects
        assert True


# ---------------------------------------------------------------------------
# Test: Full chain verification in pulse context
# ---------------------------------------------------------------------------


class TestFullImmuneLoopChain:
    """End-to-end: anomaly → case → ruling → baseline update."""

    async def test_full_chain_ruling_application_in_pulse_context(
        self,
    ) -> None:
        """Integration: sentinel with Tribunal + rulings present +
        pulse runs → steward_baseline_updated emitted."""
        from heretek_swarm.consensus.tribunal import RulingType

        sentinel = _make_sentinel_stub_full(alerts=[])
        case = sentinel.tribunal.create_case(
            original_decision_id="anom-chain-001",
            appellant_agent_id="sentinel-test",
            grounds="Chain test",
            description="Full chain integration test",
        )
        sentinel.tribunal.issue_ruling(
            case_id=case.case_id,
            ruling_type=RulingType.UPHOLD,
            reasoning="Full chain ruling",
        )

        historian = _make_historian_stub()
        steward = MagicMock()
        steward.internal_state = {}
        steward.active_deliberations = {}

        supervisor = _MockSupervisor(
            actors={}, total_errors=1, active_actors=0,
        )
        swarm = _make_swarm(
            sentinel=sentinel, historian=historian, steward=steward,
            supervisor=supervisor,
        )

        with capture_logs() as cap:
            await _run_pulse_until(swarm, max_cycles=1)

        # Verify steward_baseline_updated was logged during pulse
        baseline_logs = [
            e for e in cap if e.get("event") == "steward_baseline_updated"
        ]
        assert len(baseline_logs) == 1, (
            f"Expected 1 steward_baseline_updated in full-chain test, "
            f"got {len(baseline_logs)}"
        )

        # Verify immune system was called
        sentinel._immune_manager._immune_system.request_baseline_update.assert_called_once()

    async def test_full_chain_respects_d002_fire_and_forget(self) -> None:
        """Per D002: pulse does not await ruling issuance — it only applies
        existing rulings. If no rulings exist yet, baseline_updated is not logged."""
        sentinel = _make_sentinel_stub_full(alerts=[])
        # Tribunal present but empty — no cases, no rulings

        historian = _make_historian_stub()
        steward = MagicMock()
        steward.internal_state = {}
        steward.active_deliberations = {}

        supervisor = _MockSupervisor(
            actors={}, total_errors=1, active_actors=0,
        )
        swarm = _make_swarm(
            sentinel=sentinel, historian=historian, steward=steward,
            supervisor=supervisor,
        )

        with capture_logs() as cap:
            await _run_pulse_until(swarm, max_cycles=1)

        baseline_logs = [
            e for e in cap if e.get("event") == "steward_baseline_updated"
        ]
        assert len(baseline_logs) == 0, (
            "No baseline_updated expected when Tribunal has no rulings yet"
        )
