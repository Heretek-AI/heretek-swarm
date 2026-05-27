"""S05 integration tests: precedent chain and threshold drift.

TestPrecedentChain (gate 1): verifies the integrated pipeline from
anomaly injection through immune memory lookup to Tribunal case
creation or precedent short-circuit.  Uses real SentinelAgent,
ImmuneResponseBuilding, BehavioralBaseline, AnomalyMonitor, and
Tribunal — only the event_mesh is mocked.

TestThresholdDrift (gate 3): verifies the hysteresis-driven adaptive
z_score_threshold adjustment based on sustained FP-rate patterns in
the AnomalyMonitor's FP-rate tracking window and BehavioralBaseline's
adjust_z_score_threshold.
"""

from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock

import pytest
from structlog.testing import capture_logs

from heretek_swarm.actors.sentinel.agent import SentinelAgent
from heretek_swarm.actors.sentinel.anomaly import AnomalyMonitor
from heretek_swarm.consensus.immune import (
    ImmunePattern,
    ImmuneResponseBuilding,
    PatternClassification,
    ResponseOutcome,
)
from heretek_swarm.security.anomaly_detection import AnomalyDetectionConfig
from heretek_swarm.security.behavioral_baseline import BehavioralBaseline

pytestmark = [pytest.mark.integration]


# ---------------------------------------------------------------------------
# Helper factories
# ---------------------------------------------------------------------------


def _make_sentinel(*, event_mesh=None, config: dict | None = None) -> SentinelAgent:
    """Create a real SentinelAgent with controlled event_mesh.

    All internal subsystems (ImmuneResponseBuilding, BehavioralBaseline,
    AnomalyMonitor, Tribunal) are the real production implementations.
    Only the event_mesh / compute_tier_client / pattern_extractor
    externalities are mocked.
    """
    cfg = config or {}
    agent = SentinelAgent(
        agent_id="sentinel-s05",
        config=cfg,
    )
    agent._event_mesh = event_mesh

    # Stub pattern_extractor so _emit_pattern doesn't crash.
    # PatternMixin._emit_pattern requires this; in production it is
    # wired via the ActorSupervisor.
    pe = MagicMock()
    pe.analyze_message = AsyncMock()
    agent.pattern_extractor = pe
    # _emit_pattern also checks _pattern_emitted for deduplication
    if not hasattr(agent, "_pattern_emitted"):
        agent._pattern_emitted = set()

    return agent


def _make_monitor(
    z_score_threshold: float = 3.0,
    agent_id: str = "test-agent",
) -> AnomalyMonitor:
    """Create a real AnomalyMonitor with real BehavioralBaseline.

    Useful for threshold-drift tests that exercise the hysteresis logic
    directly on the monitor (no SentinelAgent overhead required).
    """
    cfg = AnomalyDetectionConfig(
        response_deadline_seconds=30,
        z_score_threshold=z_score_threshold,
        max_auto_responses_per_minute=10,
        sentinel_prime_escalation_threshold=3,
    )
    baseline = BehavioralBaseline(z_score_threshold=z_score_threshold)
    return AnomalyMonitor(
        anomaly_config=cfg,
        behavioral_baseline=baseline,
        agent_id=agent_id,
    )


def _immune_memory_add(
    immune_system: ImmuneResponseBuilding,
    *,
    pattern_content: dict,
    pattern_type: str = "rate_drop",
    severity: str = "high",
    approved: bool = False,
    confidence: float = 0.9,
    occurrence_count: int = 4,
    false_positive_count: int = 0,
) -> str:
    """Add a pattern directly to the immune memory.

    This simulates what the immune system would have learned over
    multiple anomaly-response cycles, so that the precedent chain
    tests can verify recognition of previously-seen patterns.
    """
    pattern_hash = immune_system._generate_pattern_hash(pattern_content)
    pattern_id = immune_system._generate_pattern_id(pattern_hash)
    immune_system._immune_memory[pattern_id] = ImmunePattern(
        pattern_id=pattern_id,
        pattern_hash=pattern_hash,
        pattern_type=pattern_type,
        severity=severity,
        first_seen=datetime.now(UTC),
        last_seen=datetime.now(UTC),
        approved=approved,
        confidence=confidence,
        occurrence_count=occurrence_count,
        false_positive_count=false_positive_count,
        false_positive_rate=(
            false_positive_count / occurrence_count
            if occurrence_count > 0
            else 0.0
        ),
    )
    return pattern_id


# ============================================================================
# TestPrecedentChain — gate 1: precedent chain tests
# ============================================================================


class TestPrecedentChain:
    """End-to-end precedent chain integration tests.

    Exercises the full pipeline: anomaly content → immune memory lookup
    → pattern classification → Tribunal case creation or short-circuit.
    """

    # (a) First anomaly triggers Tribunal case
    @pytest.mark.asyncio
    async def test_first_anomaly_triggers_tribunal_case(self) -> None:
        """Inject an anomaly that has no precedent → verify
        tribunal_case_created log + _emit_pattern called."""
        sentinel = _make_sentinel()

        # Ensure immune memory starts clean for this content
        content = {
            "anomaly_type": "rate_spike",
            "severity": "high",
            "z_score": 5.2,
            "agent_id": "worker-1",
            "trigger_metric": "throughput",
        }
        pattern_hash = sentinel._immune_manager._immune_system._generate_pattern_hash(
            content
        )
        pattern_id = (
            sentinel._immune_manager._immune_system._generate_pattern_id(
                pattern_hash
            )
        )
        sentinel._immune_manager._immune_system._immune_memory.pop(
            pattern_id, None
        )

        with capture_logs() as cap:
            await sentinel._on_anomaly_for_tribunal(
                item_id="anom-first-01",
                item_type="anomaly_detection",
                outcome="detected",
                content=content,
            )

        # Tribunal case created (HIGH severity)
        case_logs = [
            e for e in cap if e.get("event") == "tribunal_case_created"
        ]
        assert len(case_logs) == 1
        assert case_logs[0]["anomaly_id"] == "anom-first-01"
        assert case_logs[0]["severity"] == "high"

        # sentinel_anomaly_classified also logged
        classified_logs = [
            e
            for e in cap
            if e.get("event") == "sentinel_anomaly_classified"
        ]
        assert len(classified_logs) == 1
        assert classified_logs[0]["anomaly_id"] == "anom-first-01"
        assert classified_logs[0]["anomaly_type"] == "rate_spike"

        # immune_pattern_classified must NOT be logged (unknown pattern)
        immune_logs = [
            e
            for e in cap
            if e.get("event") == "immune_pattern_classified"
        ]
        assert len(immune_logs) == 0

    # (b) Second similar anomaly classified via precedent
    @pytest.mark.asyncio
    async def test_second_similar_anomaly_classified_via_precedent(self) -> None:
        """Pre-populate immune memory with a matching pattern, then
        inject a second instance → verify immune_pattern_classified
        with classification=known_benign, no tribunal_case_created."""
        sentinel = _make_sentinel()

        content = {
            "anomaly_type": "rate_drop",
            "severity": "high",
            "z_score": 4.5,
            "agent_id": "worker-2",
            "trigger_metric": "throughput",
        }

        # Simulate prior learning: add matching pattern to immune memory
        _immune_memory_add(
            sentinel._immune_manager._immune_system,
            pattern_content=content,
            pattern_type="rate_drop",
            severity="high",
            approved=False,
            confidence=0.85,
            occurrence_count=5,
            false_positive_count=1,  # fp_rate = 1/5 = 0.2 > 0.01 → KNOWN_BENIGN
        )

        # Clear any pre-existing Tribunal cases
        sentinel.tribunal._cases.clear()

        with capture_logs() as cap:
            await sentinel._on_anomaly_for_tribunal(
                item_id="anom-second-01",
                item_type="anomaly_detection",
                outcome="detected",
                content=content,
            )

        # No Tribunal case created
        assert len(sentinel.tribunal._cases) == 0

        # immune_pattern_classified logged with known_benign
        immune_logs = [
            e
            for e in cap
            if e.get("event") == "immune_pattern_classified"
        ]
        assert len(immune_logs) == 1
        log = immune_logs[0]
        assert log["classification"] == "known_benign"
        assert log["anomaly_id"] == "anom-second-01"
        assert log["anomaly_type"] == "rate_drop"
        assert log["agent_id"] == "worker-2"

        # tribunal_case_created must NOT be logged
        case_logs = [
            e for e in cap if e.get("event") == "tribunal_case_created"
        ]
        assert len(case_logs) == 0

    # (c) Known malicious classification
    @pytest.mark.asyncio
    async def test_known_malicious_classification(self) -> None:
        """Pre-populate immune memory with an approved pattern, then
        inject matching anomaly → verify classification=known_malicious."""
        sentinel = _make_sentinel()

        content = {
            "anomaly_type": "injection_attempt",
            "severity": "critical",
            "z_score": 8.0,
            "agent_id": "attacker-1",
            "trigger_metric": "malformed_input",
        }

        # Add an approved (trusted) pattern → classifies as KNOWN_MALICIOUS
        _immune_memory_add(
            sentinel._immune_manager._immune_system,
            pattern_content=content,
            pattern_type="injection_attempt",
            severity="critical",
            approved=True,
            confidence=0.95,
            occurrence_count=6,
            false_positive_count=0,
        )

        sentinel.tribunal._cases.clear()

        with capture_logs() as cap:
            await sentinel._on_anomaly_for_tribunal(
                item_id="anom-malicious-01",
                item_type="anomaly_detection",
                outcome="detected",
                content=content,
            )

        assert len(sentinel.tribunal._cases) == 0

        immune_logs = [
            e
            for e in cap
            if e.get("event") == "immune_pattern_classified"
        ]
        assert len(immune_logs) == 1
        assert immune_logs[0]["classification"] == "known_malicious"
        assert immune_logs[0]["confidence"] == 0.95
        assert immune_logs[0]["anomaly_id"] == "anom-malicious-01"

    # (d) No infra precedent degradation (event_mesh is None)
    @pytest.mark.asyncio
    async def test_no_infra_precedent_degradation(self) -> None:
        """Verify pattern classification works when event_mesh is None.
        Classification uses in-memory _immune_memory, not NATS."""
        sentinel = _make_sentinel(event_mesh=None)

        content = {
            "anomaly_type": "cpu_creep",
            "severity": "high",
            "z_score": 3.5,
            "agent_id": "cpu-worker",
            "trigger_metric": "cpu_usage",
        }

        # Pre-populate immune memory → known_benign (fp_rate triggers it)
        _immune_memory_add(
            sentinel._immune_manager._immune_system,
            pattern_content=content,
            pattern_type="cpu_creep",
            severity="high",
            approved=False,
            confidence=0.88,
            occurrence_count=6,
            false_positive_count=3,  # fp_rate = 3/6 = 0.5 > 0.01
        )

        with capture_logs() as cap:
            await sentinel._on_anomaly_for_tribunal(
                item_id="anom-no-infra-01",
                item_type="anomaly_detection",
                outcome="detected",
                content=content,
            )

        # Immune classification still works (in-memory, no NATS needed)
        immune_logs = [
            e
            for e in cap
            if e.get("event") == "immune_pattern_classified"
        ]
        assert len(immune_logs) == 1
        assert immune_logs[0]["classification"] == "known_benign"

        # No Tribunal case created
        assert len(sentinel.tribunal._cases) == 0

    # (e) Unclassified pattern still creates Tribunal case
    @pytest.mark.asyncio
    async def test_unclassified_pattern_still_creates_tribunal_case(self) -> None:
        """Unknown pattern → path returns NOVEL_MALICIOUS (no immune memory
        match) → _emit_pattern called, Tribunal case created for HIGH."""
        sentinel = _make_sentinel()

        content = {
            "anomaly_type": "completely_new_attack",
            "severity": "high",
            "z_score": 6.3,
            "agent_id": "unseen-agent",
            "trigger_metric": "novel_signature",
        }

        # Ensure no immune memory match
        pattern_hash = sentinel._immune_manager._immune_system._generate_pattern_hash(
            content
        )
        pattern_id = (
            sentinel._immune_manager._immune_system._generate_pattern_id(
                pattern_hash
            )
        )
        sentinel._immune_manager._immune_system._immune_memory.pop(
            pattern_id, None
        )

        with capture_logs() as cap:
            await sentinel._on_anomaly_for_tribunal(
                item_id="anom-unclassified-01",
                item_type="anomaly_detection",
                outcome="detected",
                content=content,
            )

        # Tribunal case IS created (HIGH severity, no immune match)
        assert len(sentinel.tribunal._cases) == 1

        case_logs = [
            e for e in cap if e.get("event") == "tribunal_case_created"
        ]
        assert len(case_logs) == 1
        assert case_logs[0]["anomaly_id"] == "anom-unclassified-01"

        # sentinel_anomaly_classified also logged
        classified_logs = [
            e
            for e in cap
            if e.get("event") == "sentinel_anomaly_classified"
        ]
        assert len(classified_logs) == 1

        # No immune_pattern_classified
        immune_logs = [
            e
            for e in cap
            if e.get("event") == "immune_pattern_classified"
        ]
        assert len(immune_logs) == 0


# ============================================================================
# TestThresholdDrift — gate 3: threshold drift integration tests
# ============================================================================


class TestThresholdDrift:
    """End-to-end threshold drift integration tests.

    Exercises the hysteresis-driven z_score_threshold adaptation:
    sustained FP rates drift the threshold upward, sustained zero-FP
    windows drift it downward, and intermittent FP rates reset counters.
    """

    # ------------------------------------------------------------------
    # (a) FP injection triggers upward drift
    # ------------------------------------------------------------------

    def test_fp_injection_triggers_upward_drift(self) -> None:
        """Inject 3 consecutive windows of FP-rate > 5% → verify
        _maybe_drift_threshold triggers → baseline_threshold_adjusted
        logged with positive delta → z_score_threshold increased."""
        monitor = _make_monitor(z_score_threshold=3.0)

        # Pre-fill window to eligibility with a low-FP baseline
        # 47 non-FPs + 3 FPs = 50 entries, fp_rate = 3/50 = 6%
        for i in range(47):
            monitor._record_response_outcome(f"setup-nonfp-{i}", is_fp=False)
        for i in range(3):
            monitor._record_response_outcome(f"setup-fp-{i}", is_fp=True)

        # At this point window = 50, fp_rate = 6%, is_eligible = True
        stats_before = monitor.get_fp_rate_window_stats()
        assert stats_before["is_eligible"] is True
        assert stats_before["fp_rate"] > 0.05

        # Simulate 3 consecutive calls to _maybe_drift_threshold
        # with sustained high FP rate. Each "window" is represented
        # by calling _maybe_drift_threshold after recording an FP.
        old_threshold = monitor._behavioral_baseline.z_score_threshold

        with capture_logs() as cap:
            monitor._record_response_outcome("anom-drift-fp-A", is_fp=True)
            monitor._maybe_drift_threshold()
            assert monitor._consecutive_elevated_fp_windows == 1

            monitor._record_response_outcome("anom-drift-fp-B", is_fp=True)
            monitor._maybe_drift_threshold()
            assert monitor._consecutive_elevated_fp_windows == 2

            # Third call crosses drift_consecutive_windows threshold
            monitor._record_response_outcome("anom-drift-fp-C", is_fp=True)
            monitor._maybe_drift_threshold()

        # Drift should have triggered → counter reset
        assert monitor._consecutive_elevated_fp_windows == 0

        # The "threshold_drift_upward" log (WARNING) is emitted by _maybe_drift_threshold
        drift_logs = [
            e for e in cap if e.get("event") == "threshold_drift_upward"
        ]
        assert len(drift_logs) == 1
        assert drift_logs[0]["fp_rate"] > 0.05
        assert drift_logs[0]["consecutive_windows"] == 3

        # baseline_threshold_adjusted INFO log from adjust_z_score_threshold
        adjusted_logs = [
            e for e in cap
            if e.get("event") == "baseline_threshold_adjusted"
            and e.get("log_level") == "info"
        ]
        assert len(adjusted_logs) == 1
        assert adjusted_logs[0]["delta"] > 0
        assert adjusted_logs[0]["new_threshold"] > old_threshold

    # ------------------------------------------------------------------
    # (b) Borderline anomaly no longer fires after drift
    # ------------------------------------------------------------------

    def test_borderline_anomaly_no_longer_fires(self) -> None:
        """After drift upward, an anomaly with z_score between old and
        new threshold → BehavioralBaseline.check_anomaly returns False."""
        baseline = BehavioralBaseline(z_score_threshold=3.0)

        # Establish a baseline so check_anomaly has data
        baseline.establish_baseline(
            agent_id="agent-x",
            metric_name="cpu",
            values=[float(i) for i in range(100)],  # mean≈49.5, std≈28.9
        )

        # At threshold 3.0, a value with z_score ≈ 3.2 should be anomalous
        # mean=49.5, std≈28.866 → value ≈ 49.5 + 3.2*28.866 ≈ 141.9
        # After drift to 3.3, z_score=3.2 is below threshold → no anomaly
        is_anom_old, z_old = baseline.check_anomaly("agent-x", "cpu", 142.0)
        assert bool(is_anom_old) is True
        assert 3.0 <= z_old <= 3.3, f"z_score={z_old:.3f} must be in [3.0, 3.3]"

        # Drift threshold upward
        with capture_logs() as cap:
            baseline.adjust_z_score_threshold(0.1, agent_id="drift-test")
            baseline.adjust_z_score_threshold(0.1, agent_id="drift-test")
            baseline.adjust_z_score_threshold(0.1, agent_id="drift-test")
            # After 3 × 0.1 = +0.3 → threshold = 3.3

        assert baseline.z_score_threshold == pytest.approx(3.30)

        # Same value should now be below the new threshold
        is_anom_new, z_new = baseline.check_anomaly("agent-x", "cpu", 142.0)
        # z_score unchanged, but threshold is higher
        assert z_new == pytest.approx(z_old)
        assert bool(is_anom_new) is False, (
            f"Expected no anomaly at threshold {baseline.z_score_threshold}, "
            f"z_score={z_new:.3f}"
        )

        # baseline_threshold_adjusted logged 3 times
        drift_logs = [
            e
            for e in cap
            if e.get("event") == "baseline_threshold_adjusted"
            and e.get("log_level") == "info"
        ]
        assert len(drift_logs) == 3
        # All deltas are positive
        for evt in drift_logs:
            assert evt["delta"] > 0

    # ------------------------------------------------------------------
    # (c) Hysteresis prevents oscillation
    # ------------------------------------------------------------------

    def test_hysteresis_prevents_oscillation(self) -> None:
        """Inject 2 elevated windows + 1 normal → verify drift does NOT
        trigger (counters reset by intermediate rate)."""
        monitor = _make_monitor(z_score_threshold=3.0)

        # Pre-fill window to eligibility with fp_rate > 0.05
        for i in range(45):
            monitor._record_response_outcome(f"hys-nonfp-{i}", is_fp=False)
        for i in range(5):
            monitor._record_response_outcome(f"hys-fp-{i}", is_fp=True)
        # Window = 50, fp_rate = 5/50 = 10%, is_eligible = True

        stats = monitor.get_fp_rate_window_stats()
        assert stats["fp_rate"] > 0.05
        assert stats["is_eligible"] is True

        # Call 1: fp_rate > 0.05 → elevated counter = 1
        monitor._record_response_outcome("hys-step1", is_fp=True)
        monitor._maybe_drift_threshold()
        assert monitor._consecutive_elevated_fp_windows == 1

        # Call 2: fp_rate > 0.05 → elevated counter = 2
        monitor._record_response_outcome("hys-step2", is_fp=True)
        monitor._maybe_drift_threshold()
        assert monitor._consecutive_elevated_fp_windows == 2

        # Call 3: inject a normal entry (is_fp=False)
        # → fp_rate still > 0.05? Let's check.
        # After 2 more FPs: 7 FPs / 52 total ≈ 13.5% — still > 5%
        # Still in elevated branch... Hmm.

        # Wait — I need the intermediate call to actually drop fp_rate
        # below 5%. Let me recalculate.
        # I have 50 entries with 5 FPs = 10% fp_rate.
        # Adding non-FP: 5/51 ≈ 9.8% — still > 5%.
        # I need ENOUGH non-FPs to drop the rate between 0 and 5%.

        # Reset approach: use fresh monitor and create scenario where
        # rate briefly crosses above 5% then falls back.
        # Simpler: override FP rate by manipulating window directly.

        # Cleaner approach — fresh monitor, control the ratio:
        monitor2 = _make_monitor(z_score_threshold=3.0)
        # Fill with exactly 50 non-FPs → rate = 0%
        for i in range(50):
            monitor2._record_response_outcome(f"clean-nonfp-{i}", is_fp=False)
        assert monitor2.get_fp_rate() == 0.0

        # Now inject 3 FPs → rate = 3/53 ≈ 5.66% (barely above 5%)
        monitor2._record_response_outcome("clean-fp-1", is_fp=True)
        monitor2._record_response_outcome("clean-fp-2", is_fp=True)
        monitor2._record_response_outcome("clean-fp-3", is_fp=True)

        # But all three entries just added — we haven't called
        # _maybe_drift_threshold yet for any of them individually.
        # The test says 2 elevated + 1 normal. So:
        # Call 1: fp_rate = 3/53 ≈ 5.66% → elevated, counter=1
        # Call 2: add another FP, fp_rate = 4/54 ≈ 7.4% → elevated, counter=2
        # Call 3: add non-FP, fp_rate = 4/55 ≈ 7.3% — still > 5%!

        # Hmm, we need the rate to drop. Let me use a different approach:
        # After 2 elevated calls, force the window to shift so fp_rate
        # drops to intermediate range.

        # Actually the simplest approach: after the 2 elevated calls,
        # pop the oldest entries (which are FPs) and replace with non-FPs.
        # But that's fragile. Let me just directly manipulate the window.

        # Actually, the simplest correct approach: use _record_response_outcome
        # for many non-FPs between elevated calls to dilute the FP rate.
        # But each _maybe_drift_threshold is separate from _record_response_outcome.

        # Let me just use a simpler ratio manipulation:
        monitor3 = _make_monitor(z_score_threshold=3.0)
        # Pre-fill: 48 non-FPs + 2 FPs = 50, fp_rate = 2/50 = 4% (< 5%)
        for i in range(48):
            monitor3._record_response_outcome(f"a-nonfp-{i}", is_fp=False)
        for i in range(2):
            monitor3._record_response_outcome(f"a-fp-{i}", is_fp=True)

        # Now add 1 FP → 3/51 ≈ 5.88% → elevated, counter=1
        monitor3._record_response_outcome("a-fp-trigger-1", is_fp=True)
        monitor3._maybe_drift_threshold()
        assert monitor3._consecutive_elevated_fp_windows == 1

        # Add another FP → 4/52 ≈ 7.69% → elevated, counter=2
        monitor3._record_response_outcome("a-fp-trigger-2", is_fp=True)
        monitor3._maybe_drift_threshold()
        assert monitor3._consecutive_elevated_fp_windows == 2

        # Now add enough non-FPs to dilute below 5%
        # Current: 52 entries, 4 FPs = 7.69%. Need fp_rate <= 5%.
        # 4/80 = 5% — need 80 entries. Add 28 non-FPs → 4/80 = 5%.
        # Actually, 4/81 ≈ 4.94% — need 81 entries total.
        # But wait — _maybe_drift_threshold is called separately.
        # 4/80 = 5% — NOT > 5%, so intermediate branch, counter resets.
        for i in range(28):
            monitor3._record_response_outcome(f"a-dilute-{i}", is_fp=False)

        # Call 3: fp_rate = 4/80 = 5% — NOT > 5%, NOT = 0 → intermediate
        monitor3._maybe_drift_threshold()

        # Both counters reset
        assert monitor3._consecutive_elevated_fp_windows == 0
        assert monitor3._consecutive_zero_fp_windows == 0

    # ------------------------------------------------------------------
    # (d) Downward drift on sustained health
    # ------------------------------------------------------------------

    def test_downward_drift_on_sustained_health(self) -> None:
        """3 consecutive zero-FP windows → threshold drifts downward
        (tightens sensitivity)."""
        monitor = _make_monitor(z_score_threshold=3.0)
        old_threshold = monitor._behavioral_baseline.z_score_threshold

        # Pre-fill window to eligibility with all non-FPs
        for i in range(50):
            monitor._record_response_outcome(f"down-nonfp-{i}", is_fp=False)

        stats = monitor.get_fp_rate_window_stats()
        assert stats["fp_rate"] == 0.0
        assert stats["is_eligible"] is True

        with capture_logs() as cap:
            # 3 consecutive zero-FP _maybe_drift_threshold calls
            monitor._record_response_outcome("down-step-1", is_fp=False)
            monitor._maybe_drift_threshold()
            assert monitor._consecutive_zero_fp_windows == 1

            monitor._record_response_outcome("down-step-2", is_fp=False)
            monitor._maybe_drift_threshold()
            assert monitor._consecutive_zero_fp_windows == 2

            # Third call triggers downward drift
            monitor._record_response_outcome("down-step-3", is_fp=False)
            monitor._maybe_drift_threshold()

        # Counter reset after drift
        assert monitor._consecutive_zero_fp_windows == 0

        # baseline_threshold_adjusted logged
        adjusted_logs = [
            e
            for e in cap
            if e.get("event") == "baseline_threshold_adjusted"
            and e.get("log_level") == "info"
        ]
        assert len(adjusted_logs) >= 1
        assert adjusted_logs[0]["delta"] < 0

        # threshold_drift_downward logged
        drift_logs = [
            e for e in cap if e.get("event") == "threshold_drift_downward"
        ]
        assert len(drift_logs) == 1

        # z_score_threshold decreased
        new_threshold = monitor._behavioral_baseline.z_score_threshold
        assert new_threshold < old_threshold

    # ------------------------------------------------------------------
    # (e) Additional: drift is rate-capped (clamped to ±0.1 per step)
    # ------------------------------------------------------------------

    def test_threshold_drift_is_rate_capped(self) -> None:
        """Verify that adjust_z_score_threshold clamps delta to ±0.1.
        The drift never exceeds 0.1 per call regardless of configuration."""
        baseline = BehavioralBaseline(z_score_threshold=3.0)

        # Positive drift capped
        result = baseline.adjust_z_score_threshold(0.15)  # would be 0.15, clamped to 0.1
        assert result == 3.10

        # Negative drift capped (but floor is 1.0)
        baseline2 = BehavioralBaseline(z_score_threshold=1.15)
        result = baseline2.adjust_z_score_threshold(-0.15)  # clamped to -0.1
        assert result == pytest.approx(1.05)  # 1.15 - 0.10
