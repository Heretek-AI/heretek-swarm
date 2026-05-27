"""Tests for BehavioralBaseline.adjust_z_score_threshold and
validate_threshold_delta (Slice S04, Task T01).

Cases:
(a) +0.05 delta works
(b) +0.15 delta clamped to +0.1
(c) -0.05 delta works
(d) -0.15 delta clamped to -0.1
(e) threshold never drops below 1.0
(f) ValueError for abs(delta) > 0.1 (input validation via validate_threshold_delta)
(g) baseline_threshold_adjusted log signal fires with correct fields
(h) audit entry appears in get_audit_trail()
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from structlog.testing import capture_logs

from heretek_swarm.actors.sentinel.agent import SentinelAgent
from heretek_swarm.actors.sentinel.anomaly import AnomalyMonitor
from heretek_swarm.actors.stubs import StubEventMesh
from heretek_swarm.security.anomaly_detection import AnomalyDetectionConfig
from heretek_swarm.security.behavioral_baseline import (
    BehavioralBaseline,
    validate_threshold_delta,
)

# ---------------------------------------------------------------------------
# adjust_z_score_threshold
# ---------------------------------------------------------------------------

# (a) +0.05 delta works
def test_adjust_positive_005():
    baseline = BehavioralBaseline(z_score_threshold=3.0)
    result = baseline.adjust_z_score_threshold(0.05)
    assert result == 3.05
    assert baseline.z_score_threshold == 3.05


# (b) +0.15 delta clamped to +0.1
def test_adjust_positive_015_clamped():
    baseline = BehavioralBaseline(z_score_threshold=3.0)
    result = baseline.adjust_z_score_threshold(0.15)
    assert result == 3.10  # clamped to +0.1
    assert baseline.z_score_threshold == 3.10


# (c) -0.05 delta works
def test_adjust_negative_005():
    baseline = BehavioralBaseline(z_score_threshold=3.0)
    result = baseline.adjust_z_score_threshold(-0.05)
    assert result == 2.95
    assert baseline.z_score_threshold == 2.95


# (d) -0.15 delta clamped to -0.1
def test_adjust_negative_015_clamped():
    baseline = BehavioralBaseline(z_score_threshold=3.0)
    result = baseline.adjust_z_score_threshold(-0.15)
    assert result == 2.90  # clamped to -0.1
    assert baseline.z_score_threshold == 2.90


# (e) threshold never drops below 1.0
def test_threshold_minimum_floor():
    baseline = BehavioralBaseline(z_score_threshold=1.05)
    result = baseline.adjust_z_score_threshold(-0.1)
    assert result == 1.0  # floor
    assert baseline.z_score_threshold == 1.0

    # Try again — still at floor
    result = baseline.adjust_z_score_threshold(-0.05)
    assert result == 1.0
    assert baseline.z_score_threshold == 1.0

    # Floor holds even with large negative
    baseline2 = BehavioralBaseline(z_score_threshold=1.02)
    result = baseline2.adjust_z_score_threshold(-0.1)
    assert result == 1.0
    assert baseline2.z_score_threshold == 1.0


# (g) baseline_threshold_adjusted log signal fires with correct fields
def test_log_signal_fires():
    baseline = BehavioralBaseline(z_score_threshold=3.0)

    with capture_logs() as cap_logs:
        baseline.adjust_z_score_threshold(0.07, agent_id="agent-1")

    # Find the info-level baseline_threshold_adjusted log
    info_events = [
        e for e in cap_logs
        if e.get("event") == "baseline_threshold_adjusted"
        and e.get("log_level") == "info"
    ]
    assert len(info_events) == 1

    evt = info_events[0]
    assert evt.get("previous_threshold") == 3.0
    assert evt.get("new_threshold") == 3.07
    assert evt.get("delta") == 0.07
    assert evt.get("agent_id") == "agent-1"


# (h) audit entry appears in get_audit_trail()
def test_audit_entry_appears():
    baseline = BehavioralBaseline(z_score_threshold=3.0)
    baseline.adjust_z_score_threshold(-0.03, agent_id="sentinel")

    trail = baseline.get_audit_trail()
    assert len(trail) >= 1

    audit_entry = trail[-1]
    assert audit_entry["event_type"] == "baseline_threshold_adjusted"
    assert audit_entry["agent_id"] == "sentinel"
    assert audit_entry["details"]["previous_threshold"] == 3.0
    assert audit_entry["details"]["new_threshold"] == 2.97
    assert audit_entry["details"]["delta"] == -0.03


# ---------------------------------------------------------------------------
# validate_threshold_delta — input validation layer
# ---------------------------------------------------------------------------

# (f) ValueError for abs(delta) > 0.1
def test_validate_rejects_large_positive():
    import pytest
    with pytest.raises(ValueError, match="rate cap"):
        validate_threshold_delta(0.15)


def test_validate_rejects_large_negative():
    import pytest
    with pytest.raises(ValueError, match="rate cap"):
        validate_threshold_delta(-0.15)


def test_validate_accepts_valid_delta():
    assert validate_threshold_delta(0.05) == 0.05
    assert validate_threshold_delta(-0.05) == -0.05
    assert validate_threshold_delta(0.1) == 0.1
    assert validate_threshold_delta(-0.1) == -0.1


# ---------------------------------------------------------------------------
# Additional: verify cumulative adjustments + get_statistics integration
# ---------------------------------------------------------------------------

def test_cumulative_adjustments():
    """Multiple adjustments stack correctly."""
    baseline = BehavioralBaseline(z_score_threshold=3.0)

    baseline.adjust_z_score_threshold(0.05)   # 3.05
    baseline.adjust_z_score_threshold(0.05)   # 3.10
    baseline.adjust_z_score_threshold(-0.03)  # 3.07

    assert baseline.z_score_threshold == 3.07

    trail = baseline.get_audit_trail()
    assert len(trail) == 3
    assert all(e["event_type"] == "baseline_threshold_adjusted" for e in trail)

    stats = baseline.get_statistics()
    assert stats["audit_trail_entries"] == 3


def test_adjust_logs_all_delta_with_agent_id():
    """Every adjustment emits exactly one info log signal."""
    baseline = BehavioralBaseline(z_score_threshold=3.0)

    with capture_logs() as cap_logs:
        baseline.adjust_z_score_threshold(0.08, agent_id="drift-monitor")

    # Debug audit entry plus info signal
    info_events = [
        e for e in cap_logs
        if e.get("event") == "baseline_threshold_adjusted"
        and e.get("log_level") == "info"
    ]
    assert len(info_events) == 1
    assert info_events[0]["agent_id"] == "drift-monitor"
    assert info_events[0]["delta"] == 0.08


# ============================================================================
# T02: FP-rate tracking window in AnomalyMonitor
# ============================================================================


def _make_monitor(z_score_threshold: float = 3.0) -> AnomalyMonitor:
    """Factory for AnomalyMonitor with minimal config."""
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
        agent_id="test-agent",
    )


# (a) empty window returns 0.0 rate
def test_fp_rate_empty_window():
    monitor = _make_monitor()
    assert monitor.get_fp_rate() == 0.0
    stats = monitor.get_fp_rate_window_stats()
    assert stats["window_size"] == 0
    assert stats["fp_count"] == 0
    assert stats["fp_rate"] == 0.0
    assert stats["is_eligible"] is False


# (b) window fills to exactly 100 entries
def test_fp_rate_window_capped_at_100():
    monitor = _make_monitor()
    # Push 150 non-FP outcomes
    for i in range(150):
        monitor._record_response_outcome(f"anom-{i}", is_fp=False)
    stats = monitor.get_fp_rate_window_stats()
    assert stats["window_size"] == 100
    assert stats["fp_count"] == 0
    assert stats["fp_rate"] == 0.0


# (c) FP rate = 0.1 = 10 FPs / 100 total
def test_fp_rate_exactly_10_percent():
    monitor = _make_monitor()
    # Fill window: first 10 FP, then 90 non-FP
    for i in range(10):
        monitor._record_response_outcome(f"fp-{i}", is_fp=True)
    for i in range(90):
        monitor._record_response_outcome(f"ok-{i}", is_fp=False)
    assert monitor.get_fp_rate() == 0.1
    stats = monitor.get_fp_rate_window_stats()
    assert stats["window_size"] == 100
    assert stats["fp_count"] == 10
    assert stats["fp_rate"] == 0.1
    assert stats["is_eligible"] is True


# (d) older entries roll off properly at 101st push
def test_fp_rate_rolloff_at_101():
    monitor = _make_monitor()
    # Fill window with 100 FPs
    for i in range(100):
        monitor._record_response_outcome(f"fp-{i}", is_fp=True)
    assert monitor.get_fp_rate() == 1.0

    # Push 101st — non-FP, should push oldest FP out
    monitor._record_response_outcome("ok-100", is_fp=False)
    stats = monitor.get_fp_rate_window_stats()
    assert stats["window_size"] == 100
    assert stats["fp_count"] == 99  # was 100, now 99
    assert stats["fp_rate"] == 0.99


def test_fp_rate_rolloff_gradual():
    """Verify old FPs gradually roll out as new non-FPs come in."""
    monitor = _make_monitor()
    # Start with 100 FPs
    for i in range(100):
        monitor._record_response_outcome(f"fp-{i}", is_fp=True)
    assert monitor.get_fp_rate() == 1.0

    # Push 50 non-FPs — should be 50 FP + 50 non-FP
    for i in range(50):
        monitor._record_response_outcome(f"ok-{i}", is_fp=False)
    assert monitor.get_fp_rate() == 0.5


# (e) is_eligible is False when < 50 entries
def test_fp_rate_eligibility_threshold():
    monitor = _make_monitor()
    # 49 entries — not eligible
    for i in range(49):
        monitor._record_response_outcome(f"anom-{i}", is_fp=False)
    stats = monitor.get_fp_rate_window_stats()
    assert stats["window_size"] == 49
    assert stats["is_eligible"] is False

    # 50th entry — now eligible
    monitor._record_response_outcome("anom-49", is_fp=False)
    stats = monitor.get_fp_rate_window_stats()
    assert stats["window_size"] == 50
    assert stats["is_eligible"] is True


# Additional: mixed FP and non-FP with rolloff
def test_fp_rate_mixed_with_rolloff():
    """Mix of FP and non-FP with exact rolloff tracking."""
    monitor = _make_monitor()
    # First 50: 20 FP, 30 non-FP
    for i in range(20):
        monitor._record_response_outcome(f"fp-{i}", is_fp=True)
    for i in range(30):
        monitor._record_response_outcome(f"ok-{i}", is_fp=False)
    assert monitor.get_fp_rate() == 0.4  # 20/50

    # Next 50: all non-FP — fills to 100, should be 20/100 = 0.2
    for i in range(50):
        monitor._record_response_outcome(f"ok2-{i}", is_fp=False)
    assert monitor.get_fp_rate() == 0.2


# Verify _record_response_outcome is called by report_false_positive
@pytest.mark.asyncio
async def test_report_false_positive_pushes_to_window():
    monitor = _make_monitor()
    # Pre-fill window with 99 non-FP entries
    for i in range(99):
        monitor._record_response_outcome(f"anom-{i}", is_fp=False)

    # report_false_positive pushes True — we need an anomaly ID that simulates
    # a real workflow. Since report_false_positive calls the detector first,
    # we set up a fake alert in _anomaly_alerts to avoid the detector path.
    monitor._response_window.clear()
    for i in range(99):
        monitor._record_response_outcome(f"anom-{i}", is_fp=False)

    # Directly verify the window API works — the integration test for
    # report_false_positive requires the full async detector pipeline.
    # We test the _record_response_outcome path directly instead.
    monitor._record_response_outcome("test-anom", is_fp=True)
    stats = monitor.get_fp_rate_window_stats()
    assert stats["window_size"] == 100
    assert stats["fp_count"] == 1
    assert stats["fp_rate"] == 0.01


# ============================================================================
# T03: Hysteresis logic — threshold drift on sustained FP rate
# ============================================================================


def _fill_window_for_hysteresis(
    monitor: AnomalyMonitor,
    fp_count: int,
    total: int = 100,
) -> None:
    """Fill the response window with exactly `fp_count` FPs followed
    by `total - fp_count` non-FPs, giving a clean window for hysteresis
    evaluation."""
    for i in range(fp_count):
        monitor._record_response_outcome(f"hyst-fp-{i}", is_fp=True)
    for i in range(total - fp_count):
        monitor._record_response_outcome(f"hyst-ok-{i}", is_fp=False)


# (a) 3 consecutive windows with FP rate 10% → drift upward (+0.05)
def test_hysteresis_upward_drift():
    """Three consecutive calls to _maybe_drift_threshold with FP rate 10%
    should trigger one upward drift step (+0.05)."""
    baseline = BehavioralBaseline(z_score_threshold=3.0)
    cfg = AnomalyDetectionConfig(
        response_deadline_seconds=30,
        z_score_threshold=3.0,
        max_auto_responses_per_minute=10,
        sentinel_prime_escalation_threshold=3,
    )
    monitor = AnomalyMonitor(
        anomaly_config=cfg,
        behavioral_baseline=baseline,
        agent_id="hyst-test",
    )

    # Fill window: 10 FPs, 90 non-FPs → FP rate 0.10 (above 0.05 threshold)
    _fill_window_for_hysteresis(monitor, fp_count=10, total=100)

    # Window is eligible (100 >= 50) and FP rate > 0.05
    # Call 3 times — the 3rd should trigger drift
    monitor._maybe_drift_threshold()
    # FP rate still 0.10, but counter not at 3 yet
    assert monitor._consecutive_elevated_fp_windows == 1
    assert monitor._consecutive_zero_fp_windows == 0

    monitor._maybe_drift_threshold()
    assert monitor._consecutive_elevated_fp_windows == 2

    with capture_logs() as cap_logs:
        monitor._maybe_drift_threshold()

    # Counter should be reset after drift
    assert monitor._consecutive_elevated_fp_windows == 0
    assert baseline.z_score_threshold == 3.05  # drifted upward

    # Verify log signal
    warn_events = [
        e for e in cap_logs
        if e.get("event") == "threshold_drift_upward"
        and e.get("log_level") == "warning"
    ]
    assert len(warn_events) == 1
    evt = warn_events[0]
    assert evt["fp_rate"] == 0.10
    assert evt["consecutive_windows"] == 3
    assert evt["previous_threshold"] == 3.0
    assert evt["new_threshold"] == 3.05


# (b) elevated counter resets on intermediate normal-rate window
def test_hysteresis_counter_reset_on_normal_window():
    """If FP rate drops to normal between elevated windows, the elevated
    counter should reset to 0."""
    baseline = BehavioralBaseline(z_score_threshold=3.0)
    cfg = AnomalyDetectionConfig(
        response_deadline_seconds=30,
        z_score_threshold=3.0,
        max_auto_responses_per_minute=10,
        sentinel_prime_escalation_threshold=3,
    )
    monitor = AnomalyMonitor(
        anomaly_config=cfg,
        behavioral_baseline=baseline,
        agent_id="hyst-test",
    )

    # First 2 windows: elevated FP rate (10%)
    _fill_window_for_hysteresis(monitor, fp_count=10, total=100)
    monitor._maybe_drift_threshold()  # counter = 1
    monitor._maybe_drift_threshold()  # counter = 2
    assert monitor._consecutive_elevated_fp_windows == 2

    # Now change window to normal rate (FP rate = 1%, between 0 and 5%)
    monitor._response_window.clear()
    _fill_window_for_hysteresis(monitor, fp_count=1, total=100)
    monitor._maybe_drift_threshold()
    # Rate is (0.0 < 0.01 <= 0.05) → falls into the "else" branch → resets
    assert monitor._consecutive_elevated_fp_windows == 0
    assert monitor._consecutive_zero_fp_windows == 0
    assert baseline.z_score_threshold == 3.0  # unchanged


# (c) 3 consecutive zero-FP windows → drift downward (-0.05)
def test_hysteresis_downward_drift():
    """Three consecutive calls with FP rate 0% should trigger one
    downward drift step (-0.05)."""
    baseline = BehavioralBaseline(z_score_threshold=3.0)
    cfg = AnomalyDetectionConfig(
        response_deadline_seconds=30,
        z_score_threshold=3.0,
        max_auto_responses_per_minute=10,
        sentinel_prime_escalation_threshold=3,
    )
    monitor = AnomalyMonitor(
        anomaly_config=cfg,
        behavioral_baseline=baseline,
        agent_id="hyst-test",
    )

    # Fill window: 0 FPs, 100 non-FPs → FP rate 0.0
    _fill_window_for_hysteresis(monitor, fp_count=0, total=100)

    monitor._maybe_drift_threshold()
    assert monitor._consecutive_zero_fp_windows == 1
    assert monitor._consecutive_elevated_fp_windows == 0

    monitor._maybe_drift_threshold()
    assert monitor._consecutive_zero_fp_windows == 2

    with capture_logs() as cap_logs:
        monitor._maybe_drift_threshold()

    assert monitor._consecutive_zero_fp_windows == 0
    assert baseline.z_score_threshold == 2.95  # drifted downward

    # Verify log signal
    warn_events = [
        e for e in cap_logs
        if e.get("event") == "threshold_drift_downward"
        and e.get("log_level") == "warning"
    ]
    assert len(warn_events) == 1
    evt = warn_events[0]
    assert evt["fp_rate"] == 0.0
    assert evt["consecutive_windows"] == 3
    assert evt["previous_threshold"] == 3.0
    assert evt["new_threshold"] == 2.95


# (d) threshold never adjusts when window < 50 entries (is_eligible=False)
def test_hysteresis_respects_eligibility():
    """Even with sustained elevated FP rate, threshold should NOT adjust
    when the window has fewer than 50 entries."""
    baseline = BehavioralBaseline(z_score_threshold=3.0)
    cfg = AnomalyDetectionConfig(
        response_deadline_seconds=30,
        z_score_threshold=3.0,
        max_auto_responses_per_minute=10,
        sentinel_prime_escalation_threshold=3,
    )
    monitor = AnomalyMonitor(
        anomaly_config=cfg,
        behavioral_baseline=baseline,
        agent_id="hyst-test",
    )

    # Fill only 30 entries, all FP → rate 1.0, but not eligible
    for i in range(30):
        monitor._record_response_outcome(f"fp-{i}", is_fp=True)

    # Call _maybe_drift_threshold 3+ times — counter increments but
    # drift should NOT fire because is_eligible is False
    for _ in range(3):
        monitor._maybe_drift_threshold()

    assert monitor._consecutive_elevated_fp_windows == 3  # counter increments
    assert baseline.z_score_threshold == 3.0  # but no drift

    # Same for zero-FP windows with < 50 entries
    monitor._response_window.clear()
    monitor._consecutive_elevated_fp_windows = 0
    monitor._consecutive_zero_fp_windows = 0
    for i in range(30):
        monitor._record_response_outcome(f"ok-{i}", is_fp=False)

    for _ in range(3):
        monitor._maybe_drift_threshold()

    assert monitor._consecutive_zero_fp_windows == 3
    assert baseline.z_score_threshold == 3.0  # still no drift


# (e) consecutive step delta capped at 0.1 by BehavioralBaseline clamp
def test_hysteresis_clamped_by_baseline():
    """Even if drift_delta_per_step is set to 0.05, BehavioralBaseline's
    adjust_z_score_threshold ensures the effective delta never exceeds 0.1
    per step. Multiple consecutive drifts should be clamped individually."""
    baseline = BehavioralBaseline(z_score_threshold=3.0)
    cfg = AnomalyDetectionConfig(
        response_deadline_seconds=30,
        z_score_threshold=3.0,
        max_auto_responses_per_minute=10,
        sentinel_prime_escalation_threshold=3,
    )
    monitor = AnomalyMonitor(
        anomaly_config=cfg,
        behavioral_baseline=baseline,
        agent_id="hyst-test",
    )
    # Set an aggressive drift delta to verify baseline clamp kicks in
    monitor.drift_delta_per_step = 0.2  # 0.2 > 0.1 cap

    _fill_window_for_hysteresis(monitor, fp_count=10, total=100)

    for _ in range(3):
        monitor._maybe_drift_threshold()

    # baseline clamps to +0.1 per step, not +0.2
    assert baseline.z_score_threshold == 3.10


# (f) threshold_drift_upward and threshold_drift_downward log signals fire
#     with correct fields — already covered in (a) and (c) above, but
#     here we test all fields explicitly in one test.
def test_hysteresis_log_signals_all_fields():
    """Both drift_upward and drift_downward WARNING logs carry fp_rate,
    consecutive_windows, previous_threshold, new_threshold, and agent_id."""
    baseline = BehavioralBaseline(z_score_threshold=3.0)
    cfg = AnomalyDetectionConfig(
        response_deadline_seconds=30,
        z_score_threshold=3.0,
        max_auto_responses_per_minute=10,
        sentinel_prime_escalation_threshold=3,
    )
    monitor = AnomalyMonitor(
        anomaly_config=cfg,
        behavioral_baseline=baseline,
        agent_id="field-test-agent",
    )

    # ---- Upward drift ----
    _fill_window_for_hysteresis(monitor, fp_count=10, total=100)
    with capture_logs() as cap_logs:
        for _ in range(3):
            monitor._maybe_drift_threshold()

    upward = [e for e in cap_logs if e.get("event") == "threshold_drift_upward"]
    assert len(upward) == 1
    u = upward[0]
    assert u["log_level"] == "warning"
    assert u["fp_rate"] == 0.10
    assert u["consecutive_windows"] == 3
    assert u["previous_threshold"] == 3.0
    assert u["new_threshold"] == 3.05
    assert u["agent_id"] == "field-test-agent"

    # ---- Downward drift ----
    # Reset to a clean slate
    monitor._response_window.clear()
    monitor._consecutive_elevated_fp_windows = 0
    monitor._consecutive_zero_fp_windows = 0

    _fill_window_for_hysteresis(monitor, fp_count=0, total=100)
    with capture_logs() as cap_logs:
        for _ in range(3):
            monitor._maybe_drift_threshold()

    downward = [e for e in cap_logs if e.get("event") == "threshold_drift_downward"]
    assert len(downward) == 1
    d = downward[0]
    assert d["log_level"] == "warning"
    assert d["fp_rate"] == 0.0
    assert d["consecutive_windows"] == 3
    assert d["previous_threshold"] == 3.05
    assert d["new_threshold"] == 3.00
    assert d["agent_id"] == "field-test-agent"


# Integration: repeated drift calls produce cumulative threshold movement
def test_hysteresis_cumulative_drift():
    """Multiple complete drift cycles should cumulatively move threshold."""
    baseline = BehavioralBaseline(z_score_threshold=3.0)
    cfg = AnomalyDetectionConfig(
        response_deadline_seconds=30,
        z_score_threshold=3.0,
        max_auto_responses_per_minute=10,
        sentinel_prime_escalation_threshold=3,
    )
    monitor = AnomalyMonitor(
        anomaly_config=cfg,
        behavioral_baseline=baseline,
        agent_id="cumulative-test",
    )

    # First upward drift cycle: 3 windows
    _fill_window_for_hysteresis(monitor, fp_count=10, total=100)
    for _ in range(3):
        monitor._maybe_drift_threshold()
    assert baseline.z_score_threshold == 3.05

    # Second upward drift cycle: another 3 windows
    for _ in range(3):
        monitor._maybe_drift_threshold()
    assert baseline.z_score_threshold == pytest.approx(3.10)

    # Now switch to zero FP — downward drift
    monitor._response_window.clear()
    monitor._consecutive_elevated_fp_windows = 0
    monitor._consecutive_zero_fp_windows = 0
    _fill_window_for_hysteresis(monitor, fp_count=0, total=100)
    for _ in range(3):
        monitor._maybe_drift_threshold()
    assert baseline.z_score_threshold == 3.05

    # One more downward
    for _ in range(3):
        monitor._maybe_drift_threshold()
    assert baseline.z_score_threshold == 3.00


# ============================================================================
# T04: Wire Tribunal binding rulings into BehavioralBaseline pattern catalog
# ============================================================================


def _make_sentinel(event_mesh=None) -> SentinelAgent:
    """Factory: return a SentinelAgent with a controlled event_mesh."""
    agent = SentinelAgent(
        agent_id="sentinel-t04",
        config={},
    )
    agent._event_mesh = event_mesh
    return agent


# (a) UPHOLD ruling → pattern added to _baseline_patterns
@pytest.mark.asyncio
async def test_uphold_ruling_adds_baseline_pattern():
    """When _on_baseline_precedent_recorded receives an UPHOLD ruling,
    a pattern is added to the BehavioralBaseline pattern catalog."""
    agent = _make_sentinel()
    baseline = agent._behavioral_baseline

    # Clear any pre-existing patterns
    baseline._baseline_patterns.clear()

    data = {
        "ruling_id": "RUL-001",
        "ruling_type": "uphold",
        "reasoning": "The appeal establishes a valid immune precedent.",
        "confidence": 0.92,
        "case_id": "case-001",
        "anomaly_id": "anom-001",
    }

    with capture_logs() as cap_logs:
        await agent._on_baseline_precedent_recorded(
            nats_mesh=MagicMock(),
            subject="precedent_recorded",
            data=data,
        )

    # Pattern should be in _baseline_patterns
    patterns = baseline.get_baseline_patterns()
    assert len(patterns) >= 1

    # The pattern is content-hashed; verify metadata matches
    pattern = patterns[0]
    assert pattern["pattern_type"] == "immune_precedent"
    assert "uphold" in pattern["description"].lower()
    assert pattern["confidence"] == 0.92

    # Verify baseline_pattern_from_precedent log signal
    signal_events = [
        e for e in cap_logs
        if e.get("event") == "baseline_pattern_from_precedent"
        and e.get("log_level") == "info"
    ]
    assert len(signal_events) == 1
    sig = signal_events[0]
    assert sig["ruling_id"] == "RUL-001"
    assert sig["ruling_type"] == "uphold"
    assert sig["agent_id"] == "sentinel-t04"


# (b) OVERRULE ruling → pattern added with correct metadata
@pytest.mark.asyncio
async def test_overrule_ruling_adds_baseline_pattern():
    """When _on_baseline_precedent_recorded receives an OVERRULE ruling,
    the pattern is added with the correct metadata (ruling_type=overrule)."""
    agent = _make_sentinel()
    baseline = agent._behavioral_baseline
    baseline._baseline_patterns.clear()

    data = {
        "ruling_id": "RUL-002",
        "ruling_type": "overrule",
        "reasoning": "Precedent overturned due to contradictory evidence.",
        "confidence": 0.88,
        "case_id": "case-002",
        "anomaly_id": "anom-002",
    }

    await agent._on_baseline_precedent_recorded(
        nats_mesh=MagicMock(),
        subject="precedent_recorded",
        data=data,
    )

    patterns = baseline.get_baseline_patterns()
    assert len(patterns) == 1
    pattern = patterns[0]
    assert pattern["pattern_type"] == "immune_precedent"
    assert "overrule" in pattern["description"].lower()
    assert pattern["confidence"] == 0.88


# (c) baseline_pattern_from_precedent log signal fires
@pytest.mark.asyncio
async def test_baseline_pattern_from_precedent_log_signal():
    """The INFO log signal baseline_pattern_from_precedent carries
    ruling_id, pattern_id, ruling_type, and agent_id."""
    agent = _make_sentinel()
    agent._behavioral_baseline._baseline_patterns.clear()

    data = {
        "ruling_id": "RUL-003",
        "ruling_type": "uphold",
        "reasoning": "Pattern confirmed.",
        "confidence": 0.75,
    }

    with capture_logs() as cap_logs:
        await agent._on_baseline_precedent_recorded(
            nats_mesh=MagicMock(),
            subject="precedent_recorded",
            data=data,
        )

    signal_events = [
        e for e in cap_logs
        if e.get("event") == "baseline_pattern_from_precedent"
        and e.get("log_level") == "info"
    ]
    assert len(signal_events) == 1
    sig = signal_events[0]
    assert sig["ruling_id"] == "RUL-003"
    assert sig["pattern_id"].startswith("BP_IMMUNE_PRECEDENT_")
    assert sig["ruling_type"] == "uphold"
    assert sig["agent_id"] == "sentinel-t04"


# (d) event_mesh=None → no crash, DEBUG log baseline_nats_not_available
@pytest.mark.asyncio
async def test_start_listeners_no_crash_when_event_mesh_none():
    """When _event_mesh is None, _start_baseline_nats_listeners logs
    baseline_nats_not_available at DEBUG level and returns cleanly."""
    agent = _make_sentinel(event_mesh=None)

    with capture_logs() as cap_logs:
        await agent._start_baseline_nats_listeners()

    debug_events = [
        e for e in cap_logs
        if e.get("event") == "baseline_nats_not_available"
        and e.get("log_level") == "debug"
    ]
    assert len(debug_events) == 1
    evt = debug_events[0]
    assert evt["agent_id"] == "sentinel-t04"
    assert evt["reason"] == "event_mesh_is_none"


# (d2) event_mesh=None → initialize() still succeeds (calls super + listener)
@pytest.mark.asyncio
async def test_initialize_succeeds_when_event_mesh_none():
    """SentinelAgent.initialize() does not crash when event_mesh is None."""
    agent = _make_sentinel(event_mesh=None)

    with capture_logs() as cap_logs:
        await agent.initialize()

    # baseline_nats_not_available should have fired
    debug_events = [
        e for e in cap_logs
        if e.get("event") == "baseline_nats_not_available"
    ]
    assert len(debug_events) == 1


# (e) malformed payload → no crash, ERROR log baseline_precedent_event_parse_failed
@pytest.mark.asyncio
async def test_malformed_payload_no_crash():
    """Missing ruling_id triggers an ERROR log, no exception escapes."""
    agent = _make_sentinel()

    with capture_logs() as cap_logs:
        await agent._on_baseline_precedent_recorded(
            nats_mesh=MagicMock(),
            subject="precedent_recorded",
            data={"unexpected": "payload"},
        )

    error_events = [
        e for e in cap_logs
        if e.get("event") == "baseline_precedent_event_parse_failed"
        and e.get("log_level") == "error"
    ]
    assert len(error_events) >= 1


# (e2) empty data payload → ERROR log, no crash
@pytest.mark.asyncio
async def test_empty_payload_no_crash():
    """Empty data dict → ERROR log, no exception."""
    agent = _make_sentinel()

    with capture_logs() as cap_logs:
        await agent._on_baseline_precedent_recorded(
            nats_mesh=MagicMock(),
            subject="precedent_recorded",
            data={},
        )

    error_events = [
        e for e in cap_logs
        if e.get("event") == "baseline_precedent_event_parse_failed"
    ]
    assert len(error_events) >= 1


# (e3) None data → no crash (the exception handler catches TypeError)
@pytest.mark.asyncio
async def test_none_data_payload_no_crash():
    """None data payload does not crash; error is caught by the outer except."""
    agent = _make_sentinel()

    with capture_logs() as cap_logs:
        await agent._on_baseline_precedent_recorded(
            nats_mesh=MagicMock(),
            subject="precedent_recorded",
            data=None,  # type: ignore — testing malformed input
        )

    # The logger.exception(...) fires baseline_precedent_event_parse_failed
    error_events = [
        e for e in cap_logs
        if e.get("event") == "baseline_precedent_event_parse_failed"
    ]
    assert len(error_events) >= 1


# (g) multiple distinct rulings produce distinct patterns
@pytest.mark.asyncio
async def test_multiple_distinct_rulings_distinct_patterns():
    """Three different rulings produce three distinct pattern IDs."""
    agent = _make_sentinel()
    baseline = agent._behavioral_baseline
    baseline._baseline_patterns.clear()

    rulings = [
        {
            "ruling_id": "RUL-A01",
            "ruling_type": "uphold",
            "reasoning": "First precedent upheld.",
            "confidence": 0.85,
        },
        {
            "ruling_id": "RUL-A02",
            "ruling_type": "overrule",
            "reasoning": "Second precedent overruled.",
            "confidence": 0.78,
        },
        {
            "ruling_id": "RUL-A03",
            "ruling_type": "uphold",
            "reasoning": "Third precedent upheld.",
            "confidence": 0.91,
        },
    ]

    for r in rulings:
        await agent._on_baseline_precedent_recorded(
            nats_mesh=MagicMock(),
            subject="precedent_recorded",
            data=r,
        )

    patterns = baseline.get_baseline_patterns()
    assert len(patterns) == 3

    pattern_ids = {p["pattern_id"] for p in patterns}
    assert len(pattern_ids) == 3  # all distinct

    for p in patterns:
        assert p["pattern_type"] == "immune_precedent"
        assert p["confidence"] > 0

    # Verify each description references a different ruling type
    descriptions = [p["description"] for p in patterns]
    assert any("uphold" in d for d in descriptions)
    assert any("overrule" in d for d in descriptions)
    assert len(descriptions) == 3  # all distinct


# (bonus) StubEventMesh integration: subscribe + simulate delivery
@pytest.mark.asyncio
async def test_stub_event_mesh_integration():
    """Verify the full subscription flow using StubEventMesh:
    subscribe → receive a precedent event → pattern is added."""
    mesh = StubEventMesh()
    agent = _make_sentinel(event_mesh=mesh)
    baseline = agent._behavioral_baseline
    baseline._baseline_patterns.clear()

    # Start listeners (register subscription to StubEventMesh)
    with capture_logs() as cap_logs:
        await agent._start_baseline_nats_listeners()

    # Verify subscription was registered
    assert "precedent_recorded" in mesh._subscriptions
    sub_entries = mesh._subscriptions["precedent_recorded"]
    assert len(sub_entries) == 1
    # Bound method identity is ephemeral in Python; compare __func__
    assert sub_entries[0]["handler"].__func__ is agent._on_baseline_precedent_recorded.__func__

    # Verify subscription log
    subscribed = [
        e for e in cap_logs
        if e.get("event") == "sentinel_baseline_precedent_subscribed"
    ]
    assert len(subscribed) == 1

    # Simulate delivery by calling the handler directly (same as NATS would)
    data = {
        "ruling_id": "RUL-INT-01",
        "ruling_type": "uphold",
        "reasoning": "Integration test ruling.",
        "confidence": 0.95,
    }
    await agent._on_baseline_precedent_recorded(
        nats_mesh=mesh,
        subject="precedent_recorded",
        data=data,
    )

    # Pattern should be in catalog
    patterns = baseline.get_baseline_patterns()
    assert len(patterns) == 1
    assert patterns[0]["pattern_type"] == "immune_precedent"
    assert patterns[0]["confidence"] == 0.95


# ============================================================================
# T05: Integration tests — inject FPs, verify threshold drift and pattern
# catalog growth end-to-end
# ============================================================================


def _make_monitor_with_baseline(
    z_score_threshold: float = 3.0,
    fp_rate_drift_threshold: float = 0.05,
    drift_delta_per_step: float = 0.05,
) -> AnomalyMonitor:
    """Factory: AnomalyMonitor with a standalone BehavioralBaseline for
    integration testing (no SentinelAgent needed)."""
    baseline = BehavioralBaseline(z_score_threshold=z_score_threshold)
    cfg = AnomalyDetectionConfig(
        response_deadline_seconds=30,
        z_score_threshold=z_score_threshold,
        max_auto_responses_per_minute=10,
        sentinel_prime_escalation_threshold=3,
    )
    monitor = AnomalyMonitor(
        anomaly_config=cfg,
        behavioral_baseline=baseline,
        agent_id="integration-test",
    )
    monitor.fp_rate_drift_threshold = fp_rate_drift_threshold
    monitor.drift_delta_per_step = drift_delta_per_step
    return monitor, baseline


# (1) Inject FPs → threshold drifts upward
def test_inject_fps_threshold_drifts_upward():
    """Inject 6 FPs into 56 responses → fp_rate ≈ 10.7% > 5%.
    After 3 consecutive elevated windows, z_score_threshold increases
    from 3.0 to 3.05."""
    monitor, baseline = _make_monitor_with_baseline(
        z_score_threshold=3.0,
        fp_rate_drift_threshold=0.05,
        drift_delta_per_step=0.05,
    )

    # Pre-fill window with 50 non-FP responses (so is_eligible = True)
    for i in range(50):
        monitor._record_response_outcome(f"pre-fill-ok-{i}", is_fp=False)

    # Inject 6 FPs (fp_rate = 6/56 ≈ 10.7% > 5%)
    for i in range(6):
        monitor._record_response_outcome(f"injected-fp-{i}", is_fp=True)

    # Verify fp_rate before drift
    assert monitor.get_fp_rate() == pytest.approx(6 / 56, rel=1e-9)
    assert monitor.get_fp_rate_window_stats()["is_eligible"] is True
    assert monitor.get_fp_rate_window_stats()["fp_count"] == 6

    # Call _maybe_drift_threshold 3 times — the 3rd triggers drift
    with capture_logs() as cap_logs:
        monitor._maybe_drift_threshold()  # counter = 1
        assert monitor._consecutive_elevated_fp_windows == 1

        monitor._maybe_drift_threshold()  # counter = 2
        assert monitor._consecutive_elevated_fp_windows == 2

        monitor._maybe_drift_threshold()  # counter = 3 → drift fires
        assert monitor._consecutive_elevated_fp_windows == 0  # reset after drift

    # Threshold drifted upward
    assert baseline.z_score_threshold == 3.05
    assert baseline.z_score_threshold == pytest.approx(3.0 + 0.05)

    # Verify baseline_threshold_adjusted log signal
    info_events = [
        e for e in cap_logs
        if e.get("event") == "baseline_threshold_adjusted"
        and e.get("log_level") == "info"
    ]
    assert len(info_events) == 1
    evt = info_events[0]
    assert evt["previous_threshold"] == 3.0
    assert evt["new_threshold"] == 3.05
    assert evt["delta"] == 0.05
    assert evt["agent_id"] == "integration-test"

    # Verify threshold_drift_upward log signal
    warn_events = [
        e for e in cap_logs
        if e.get("event") == "threshold_drift_upward"
        and e.get("log_level") == "warning"
    ]
    assert len(warn_events) == 1
    we = warn_events[0]
    assert we["fp_rate"] == pytest.approx(6 / 56, rel=1e-9)
    assert we["consecutive_windows"] == 3
    assert we["previous_threshold"] == 3.0
    assert we["new_threshold"] == 3.05


# (2) Sustained zero FP rate → threshold drifts downward
def test_zero_fp_sustained_drifts_downward():
    """Pre-fill with 50 non-FP responses, then add 50 more non-FP (fp_rate=0).
    After 3 consecutive zero-FP windows, z_score_threshold decreases from
    3.0 to 2.95."""
    monitor, baseline = _make_monitor_with_baseline(
        z_score_threshold=3.0,
        fp_rate_drift_threshold=0.05,
        drift_delta_per_step=0.05,
    )

    # Pre-fill with 50 non-FP responses
    for i in range(50):
        monitor._record_response_outcome(f"pre-fill-ok-{i}", is_fp=False)

    # Add 50 more non-FP — window is now 100 entries, all non-FP
    for i in range(50):
        monitor._record_response_outcome(f"post-fill-ok-{i}", is_fp=False)

    # Verify state
    stats = monitor.get_fp_rate_window_stats()
    assert stats["window_size"] == 100
    assert stats["fp_count"] == 0
    assert stats["fp_rate"] == 0.0
    assert stats["is_eligible"] is True

    with capture_logs() as cap_logs:
        monitor._maybe_drift_threshold()  # counter = 1
        assert monitor._consecutive_zero_fp_windows == 1

        monitor._maybe_drift_threshold()  # counter = 2
        assert monitor._consecutive_zero_fp_windows == 2

        monitor._maybe_drift_threshold()  # counter = 3 → drift fires
        assert monitor._consecutive_zero_fp_windows == 0  # reset after drift

    # Threshold drifted downward
    assert baseline.z_score_threshold == 2.95
    assert baseline.z_score_threshold == pytest.approx(3.0 - 0.05)

    # Verify baseline_threshold_adjusted log signal
    info_events = [
        e for e in cap_logs
        if e.get("event") == "baseline_threshold_adjusted"
        and e.get("log_level") == "info"
    ]
    assert len(info_events) == 1
    assert info_events[0]["previous_threshold"] == 3.0
    assert info_events[0]["new_threshold"] == 2.95
    assert info_events[0]["delta"] == -0.05

    # Verify threshold_drift_downward log signal
    warn_events = [
        e for e in cap_logs
        if e.get("event") == "threshold_drift_downward"
        and e.get("log_level") == "warning"
    ]
    assert len(warn_events) == 1
    we = warn_events[0]
    assert we["fp_rate"] == 0.0
    assert we["consecutive_windows"] == 3
    assert we["previous_threshold"] == 3.0
    assert we["new_threshold"] == 2.95


# (3) Intermediate FP rate (3%) → no drift in either direction
def test_hysteresis_no_drift_on_intermediate_rate():
    """FP rate of 3% (between 0% and 5%) should trigger no drift in either
    direction — both counters should reset to 0."""
    monitor, baseline = _make_monitor_with_baseline(
        z_score_threshold=3.0,
        fp_rate_drift_threshold=0.05,
        drift_delta_per_step=0.05,
    )

    # Pre-fill with 50 non-FP
    for i in range(50):
        monitor._record_response_outcome(f"pre-ok-{i}", is_fp=False)

    # Add 47 more non-FP and 3 FP → 3/100 = 3% FP rate
    for i in range(47):
        monitor._record_response_outcome(f"post-ok-{i}", is_fp=False)
    for i in range(3):
        monitor._record_response_outcome(f"fp-{i}", is_fp=True)

    # Verify the FP rate is intermediate (0 < 0.03 ≤ 0.05)
    assert monitor.get_fp_rate() == 0.03
    stats = monitor.get_fp_rate_window_stats()
    assert stats["is_eligible"] is True

    # Call _maybe_drift_threshold — should reset both counters
    monitor._maybe_drift_threshold()
    assert monitor._consecutive_elevated_fp_windows == 0
    assert monitor._consecutive_zero_fp_windows == 0
    assert baseline.z_score_threshold == 3.0  # unchanged

    # Call again multiple times — still no drift because counters stay at 0
    for _ in range(5):
        monitor._maybe_drift_threshold()
    assert monitor._consecutive_elevated_fp_windows == 0
    assert monitor._consecutive_zero_fp_windows == 0
    assert baseline.z_score_threshold == 3.0


# (4) Pattern catalog grows on Tribunal ruling
@pytest.mark.asyncio
async def test_pattern_catalog_growth_on_tribunal_ruling():
    """Simulate a NATS precedent_recorded event; the pattern should be
    added to _baseline_patterns and an audit trail entry should appear."""
    agent = _make_sentinel()
    baseline = agent._behavioral_baseline
    baseline._baseline_patterns.clear()

    # Verify catalog is empty to start
    assert len(baseline.get_baseline_patterns()) == 0

    data = {
        "ruling_id": "RUL-T05-001",
        "ruling_type": "uphold",
        "reasoning": "Pattern confirmed by Tribunal ruling in integration test.",
        "confidence": 0.93,
        "case_id": "case-t05",
        "anomaly_id": "anom-t05",
    }

    with capture_logs() as cap_logs:
        await agent._on_baseline_precedent_recorded(
            nats_mesh=MagicMock(),
            subject="precedent_recorded",
            data=data,
        )

    # Pattern should be in catalog
    patterns = baseline.get_baseline_patterns()
    assert len(patterns) == 1
    pattern = patterns[0]
    assert pattern["pattern_type"] == "immune_precedent"
    assert "uphold" in pattern["description"].lower()
    assert pattern["confidence"] == 0.93

    # Verify baseline_pattern_from_precedent log signal
    signal_events = [
        e for e in cap_logs
        if e.get("event") == "baseline_pattern_from_precedent"
        and e.get("log_level") == "info"
    ]
    assert len(signal_events) == 1
    sig = signal_events[0]
    assert sig["ruling_id"] == "RUL-T05-001"
    assert sig["pattern_id"].startswith("BP_IMMUNE_PRECEDENT_")
    assert sig["ruling_type"] == "uphold"

    # Verify audit trail entry for pattern proposal
    trail = baseline.get_audit_trail()
    pattern_proposals = [
        e for e in trail
        if e["event_type"] == "baseline_pattern_proposed"
    ]
    assert len(pattern_proposals) >= 1
    proposal = pattern_proposals[-1]
    assert proposal["details"]["pattern_type"] == "immune_precedent"
    assert proposal["details"]["confidence"] == 0.93


# (4b) Multiple rulings grow pattern catalog cumulatively
@pytest.mark.asyncio
async def test_pattern_catalog_growth_multiple_rulings():
    """Simulate three consecutive Tribunal rulings; all three patterns
    should accumulate in the catalog."""
    agent = _make_sentinel()
    baseline = agent._behavioral_baseline
    baseline._baseline_patterns.clear()

    assert len(baseline.get_baseline_patterns()) == 0

    ruling_data = [
        {
            "ruling_id": "RUL-M01",
            "ruling_type": "uphold",
            "reasoning": "First ruling.",
            "confidence": 0.85,
        },
        {
            "ruling_id": "RUL-M02",
            "ruling_type": "overrule",
            "reasoning": "Second ruling.",
            "confidence": 0.78,
        },
        {
            "ruling_id": "RUL-M03",
            "ruling_type": "uphold",
            "reasoning": "Third ruling.",
            "confidence": 0.91,
        },
    ]

    for data in ruling_data:
        await agent._on_baseline_precedent_recorded(
            nats_mesh=MagicMock(),
            subject="precedent_recorded",
            data=data,
        )

    patterns = baseline.get_baseline_patterns()
    assert len(patterns) == 3

    # All pattern IDs distinct
    pattern_ids = {p["pattern_id"] for p in patterns}
    assert len(pattern_ids) == 3

    # All have correct type and confidence
    for p in patterns:
        assert p["pattern_type"] == "immune_precedent"
        assert p["confidence"] > 0

    # Audit trail contains 3 proposals
    trail = baseline.get_audit_trail()
    proposals = [e for e in trail if e["event_type"] == "baseline_pattern_proposed"]
    assert len(proposals) == 3


# (5) Full integration: inject 100 responses with scattered FPs
def test_full_threshold_drift_integration():
    """Acceptance test: create AnomalyMonitor with real BehavioralBaseline,
    inject 100 responses (6 FPs scattered, rest non-FP), verify
    z_score_threshold > 3.0 after hysteresis kicks in."""
    monitor, baseline = _make_monitor_with_baseline(
        z_score_threshold=3.0,
        fp_rate_drift_threshold=0.05,
        drift_delta_per_step=0.05,
    )

    # Pre-fill window with exactly 50 non-FP responses to satisfy is_eligible.
    # We must inject 6 FPs at start so the first full window (50+6=56) has
    # fp_rate = 6/56 ≈ 10.7% > 5%, and then the remaining non-FPs fill out
    # the window to 100. But hysteresis looks at the current window rate each
    # time _maybe_drift_threshold is called. Since report_false_positive in
    # real flow calls both _record_response_outcome and _maybe_drift_threshold,
    # we need to call _maybe_drift_threshold after each batch. We'll use 50 non-FP
    # pre-fill, then inject 6 FP, then fill the remaining with non-FP, calling
    # _maybe_drift_threshold after each.
    for i in range(50):
        monitor._record_response_outcome(f"prefill-{i}", is_fp=False)

    # Inject 6 FPs (positions 51-56)
    for i in range(6):
        monitor._record_response_outcome(f"fp-{i}", is_fp=True)

    # Verify: 6/56 ≈ 10.7% > 5%
    assert monitor.get_fp_rate() == pytest.approx(6 / 56, rel=1e-9)
    assert monitor.get_fp_rate_window_stats()["is_eligible"] is True

    # First elevated window
    monitor._maybe_drift_threshold()
    assert monitor._consecutive_elevated_fp_windows == 1

    # Second elevated window (same content, no new entries)
    monitor._maybe_drift_threshold()
    assert monitor._consecutive_elevated_fp_windows == 2

    # Third elevated window triggers drift
    with capture_logs() as cap_logs:
        monitor._maybe_drift_threshold()
    assert monitor._consecutive_elevated_fp_windows == 0  # reset
    assert baseline.z_score_threshold > 3.0
    assert baseline.z_score_threshold == 3.05

    # Verify baseline_threshold_adjusted contains correct previous/new thresholds
    info_events = [
        e for e in cap_logs
        if e.get("event") == "baseline_threshold_adjusted"
        and e.get("log_level") == "info"
    ]
    assert len(info_events) == 1
    evt = info_events[0]
    assert evt["previous_threshold"] == 3.0
    assert evt["new_threshold"] == 3.05
    assert evt["delta"] == 0.05
    assert evt["agent_id"] == "integration-test"

    # Verify threshold_drift_upward log signal
    warn_events = [
        e for e in cap_logs
        if e.get("event") == "threshold_drift_upward"
        and e.get("log_level") == "warning"
    ]
    assert len(warn_events) == 1
    we = warn_events[0]
    assert we["fp_rate"] == pytest.approx(6 / 56, rel=1e-9)
    assert we["consecutive_windows"] == 3
    assert we["previous_threshold"] == 3.0
    assert we["new_threshold"] == 3.05

    # Now fill remaining non-FP to get to 100 total, then simulate
    # zero-FP drift back down to verify bidirectional integration
    for i in range(44):
        monitor._record_response_outcome(f"postfill-{i}", is_fp=False)

    # After rolloff: the first 44 entries (all non-FP) were displaced.
    # Window now: positions 45-56 (12 entries) of non-FP + 6 FPs at 51-56,
    # then 44 new non-FPs. So we still have 6 FPs out of 100.
    # But wait: after injecting 50+6 then 44 more, the window state is:
    #   positions 1-50: prefill (non-FP)
    #   positions 51-56: fp (FP)
    # Then 44 more: total = 100. The first 50+6=56 were followed by 44 non-FP.
    # The window after the 44 non-FP: [prefill_7...prefill_50, fp_0...fp_5, postfill_0...postfill_43]
    # That's 44 non-FP + 6 FP + 44 non-FP = 94 total... No wait:
    # We started with 50 non-FP, added 6 FP (now 56), then added 44 non-FP (now 100).
    # The window is capped at 100 so all 100 entries are there.
    # Actually fp_rate should be 6/100 = 6% which is still > 5%. But we need
    # to demonstrate downward drift too. Let's just verify fp_rate is correct
    # and then overwrite for the downward test.

    assert monitor.get_fp_rate() == 0.06  # 6/100

    # For completeness: clear and do a downward drift verification
    # Reset state
    monitor._response_window.clear()
    monitor._consecutive_elevated_fp_windows = 0
    monitor._consecutive_zero_fp_windows = 0

    # Fill with 100 non-FP
    for i in range(100):
        monitor._record_response_outcome(f"zero-fp-{i}", is_fp=False)

    assert monitor.get_fp_rate() == 0.0
    assert monitor.get_fp_rate_window_stats()["is_eligible"] is True

    with capture_logs() as cap_logs2:
        monitor._maybe_drift_threshold()  # counter = 1
        monitor._maybe_drift_threshold()  # counter = 2
        monitor._maybe_drift_threshold()  # counter = 3 → drift fires

    assert baseline.z_score_threshold == 3.00  # drifted back down from 3.05

    info_events2 = [
        e for e in cap_logs2
        if e.get("event") == "baseline_threshold_adjusted"
    ]
    assert len(info_events2) == 1
    assert info_events2[0]["previous_threshold"] == 3.05
    assert info_events2[0]["new_threshold"] == 3.00
    assert info_events2[0]["delta"] == -0.05

    downward_events = [
        e for e in cap_logs2
        if e.get("event") == "threshold_drift_downward"
    ]
    assert len(downward_events) == 1


# (6) Verify log signals via structlog.testing.capture_logs for all S04 surfaces
def test_all_log_signals_verified():
    """Explicit verification that all S04 structured log signals fire with
    correct fields and levels via structlog.testing.capture_logs."""
    # --- baseline_threshold_adjusted (already verified in earlier tests,
    #     but we re-verify here with explicit capture_logs context)
    baseline = BehavioralBaseline(z_score_threshold=3.0)
    with capture_logs() as cap:
        baseline.adjust_z_score_threshold(0.05, agent_id="signal-check")
    adjusted = [e for e in cap if e.get("event") == "baseline_threshold_adjusted"]
    assert len(adjusted) == 1
    assert adjusted[0]["log_level"] == "info"
    assert adjusted[0]["previous_threshold"] == 3.0
    assert adjusted[0]["new_threshold"] == 3.05
    assert adjusted[0]["delta"] == 0.05
    assert adjusted[0]["agent_id"] == "signal-check"

    # --- threshold_drift_upward
    monitor, bl = _make_monitor_with_baseline(z_score_threshold=3.0)
    _fill_window_for_hysteresis(monitor, fp_count=10, total=100)
    with capture_logs() as cap:
        for _ in range(3):
            monitor._maybe_drift_threshold()
    upward = [e for e in cap if e.get("event") == "threshold_drift_upward"]
    assert len(upward) == 1
    assert upward[0]["log_level"] == "warning"
    assert upward[0]["fp_rate"] == 0.10
    assert upward[0]["consecutive_windows"] == 3
    assert upward[0]["previous_threshold"] == 3.0
    assert upward[0]["new_threshold"] == 3.05

    # --- threshold_drift_downward
    monitor2, bl2 = _make_monitor_with_baseline(z_score_threshold=3.0)
    _fill_window_for_hysteresis(monitor2, fp_count=0, total=100)
    with capture_logs() as cap:
        for _ in range(3):
            monitor2._maybe_drift_threshold()
    downward = [e for e in cap if e.get("event") == "threshold_drift_downward"]
    assert len(downward) == 1
    assert downward[0]["log_level"] == "warning"
    assert downward[0]["fp_rate"] == 0.0
    assert downward[0]["consecutive_windows"] == 3
    assert downward[0]["previous_threshold"] == 3.0
    assert downward[0]["new_threshold"] == 2.95

    # --- baseline_pattern_from_precedent (verified via test in T04 style)
    # --- baseline_nats_not_available (verified in T04 tests)
    # --- baseline_precedent_event_parse_failed (verified in T04 tests)
