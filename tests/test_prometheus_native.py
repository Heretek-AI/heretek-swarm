"""Tests for the Phase 2A prometheus-client native cutover."""

from __future__ import annotations

from heretek_swarm.observability.prometheus_native import (
    AGENTS_ACTIVE,
    AGENTS_TOTAL,
    API_REQUEST_DURATION,
    API_REQUESTS_TOTAL,
    CONSENSUS_ROUNDS,
    ENCRYPTION_LATENCY,
    EXTERNAL_CALL_DURATION,
    EXTERNAL_CALL_LOGS,
    FREE_ENERGY,
    HEALTH_SCORE,
    MESSAGES_TOTAL,
    PHI_SCORE,
    TASKS_COMPLETED,
    TASKS_FAILED,
    build_test_registry,
    export_prometheus,
    increment_consensus_rounds,
    increment_external_call_logs,
    increment_messages,
    increment_tasks_completed,
    increment_tasks_failed,
    record_api_request,
    record_encryption_latency,
    record_external_call_duration,
    record_free_energy,
    record_health_score,
    record_phi_score,
)
from prometheus_client import (
    CONTENT_TYPE_LATEST,
    REGISTRY,
    CollectorRegistry,
)

# Module-level smoke tests (the test_registry approach lets multiple
# tests touch the metrics without duplicate-timeseries errors).


def test_module_metrics_are_registered():
    """All module-level metrics are Counter / Gauge / Histogram instances.

    Note: prometheus_client strips the conventional ``_total`` suffix
    from Counter names internally (``tasks_completed_total`` →
    ``tasks_completed``). The wire format still emits ``_total``;
    only the in-process ``._name`` is the stripped form.
    """
    assert AGENTS_TOTAL._name == "heretek_swarm_agents_total"
    assert AGENTS_ACTIVE._name == "heretek_swarm_agents_active"
    assert TASKS_COMPLETED._name == "heretek_swarm_tasks_completed"  # _total stripped
    assert TASKS_FAILED._name == "heretek_swarm_tasks_failed"  # _total stripped
    assert MESSAGES_TOTAL._name == "heretek_swarm_messages"  # _total stripped
    assert CONSENSUS_ROUNDS._name == "heretek_swarm_consensus_rounds"  # _total stripped
    assert PHI_SCORE._name == "heretek_swarm_phi_score"
    assert FREE_ENERGY._name == "heretek_swarm_free_energy"
    assert HEALTH_SCORE._name == "heretek_swarm_health_score"
    assert API_REQUEST_DURATION._name == "heretek_swarm_api_request_duration_seconds"
    assert API_REQUESTS_TOTAL._name == "heretek_swarm_api_requests"  # _total stripped
    assert EXTERNAL_CALL_LOGS._name == "heretek_swarm_external_call_logs"  # _total stripped
    assert EXTERNAL_CALL_DURATION._name == "heretek_swarm_external_call_log_duration_seconds"
    assert ENCRYPTION_LATENCY._name == "heretek_swarm_encryption_latency_seconds"


def test_increment_tasks_completed_increments_counter():
    """increment_tasks_completed() increments the TASKS_COMPLETED counter."""
    before = TASKS_COMPLETED.labels(agent_id="test-1", task_type="unit")._value.get()
    increment_tasks_completed(agent_id="test-1", task_type="unit")
    after = TASKS_COMPLETED.labels(agent_id="test-1", task_type="unit")._value.get()
    assert after == before + 1


def test_increment_tasks_failed_increments_counter():
    """increment_tasks_failed() increments the TASKS_FAILED counter."""
    before = TASKS_FAILED.labels(agent_id="test-2", task_type="unit")._value.get()
    increment_tasks_failed(agent_id="test-2", task_type="unit")
    after = TASKS_FAILED.labels(agent_id="test-2", task_type="unit")._value.get()
    assert after == before + 1


def test_increment_messages_increments_counter():
    """increment_messages() increments the MESSAGES_TOTAL counter."""
    before = MESSAGES_TOTAL.labels(direction="sent", agent_id="test-3")._value.get()
    increment_messages(direction="sent", agent_id="test-3")
    after = MESSAGES_TOTAL.labels(direction="sent", agent_id="test-3")._value.get()
    assert after == before + 1


def test_increment_consensus_rounds_increments_counter():
    """increment_consensus_rounds() increments CONSENSUS_ROUNDS counter."""
    before = CONSENSUS_ROUNDS.labels(consensus_type="deliberation", outcome="success")._value.get()
    increment_consensus_rounds(consensus_type="deliberation", outcome="success")
    after = CONSENSUS_ROUNDS.labels(consensus_type="deliberation", outcome="success")._value.get()
    assert after == before + 1


def test_record_phi_score_sets_gauge():
    """record_phi_score() sets the PHI_SCORE gauge."""
    record_phi_score(agent_id="test-4", score=0.87)
    assert PHI_SCORE.labels(agent_id="test-4")._value.get() == 0.87


def test_record_free_energy_sets_gauge():
    """record_free_energy() sets the FREE_ENERGY gauge."""
    record_free_energy(agent_id="test-5", score=0.42)
    assert FREE_ENERGY.labels(agent_id="test-5")._value.get() == 0.42


def test_record_health_score_sets_gauge():
    """record_health_score() sets the HEALTH_SCORE gauge."""
    record_health_score(0.95)
    assert HEALTH_SCORE._value.get() == 0.95


def test_record_api_request_increments_counter_and_observers_histogram():
    """record_api_request() increments counter and observes duration."""
    counter_before = API_REQUESTS_TOTAL.labels(method="GET", endpoint="/x", status="200")._value.get()
    record_api_request(method="GET", endpoint="/x", status=200, duration=0.05)
    counter_after = API_REQUESTS_TOTAL.labels(method="GET", endpoint="/x", status="200")._value.get()
    assert counter_after == counter_before + 1
    # Histogram count increased (via observe). We don't assert the
    # specific bucket because Histogram._sum and _count are tracked
    # internally by prometheus_client.
    assert API_REQUEST_DURATION.labels(method="GET", endpoint="/x", status="200")._sum.get() >= 0.05


def test_increment_external_call_logs_increments_counter():
    """increment_external_call_logs() increments the EXTERNAL_CALL_LOGS counter."""
    before = EXTERNAL_CALL_LOGS.labels(
        agent_type="executor", call_type="tool", status="200"
    )._value.get()
    increment_external_call_logs(agent_type="executor", call_type="tool", status=200)
    after = EXTERNAL_CALL_LOGS.labels(
        agent_type="executor", call_type="tool", status="200"
    )._value.get()
    assert after == before + 1


def test_record_external_call_duration_observes_histogram():
    """record_external_call_duration() observes into the histogram."""
    label = EXTERNAL_CALL_DURATION.labels(call_type="tool", status="200")
    before_sum = label._sum.get()
    record_external_call_duration(call_type="tool", status=200, duration_seconds=0.1)
    after_sum = label._sum.get()
    assert after_sum >= before_sum + 0.1


def test_record_encryption_latency_observes_histogram():
    """record_encryption_latency() observes into the histogram."""
    label = ENCRYPTION_LATENCY.labels(operation="encrypt", field_type="body")
    before_sum = label._sum.get()
    record_encryption_latency(operation="encrypt", field_type="body", duration_seconds=0.001)
    after_sum = label._sum.get()
    assert after_sum >= before_sum + 0.001


def test_export_prometheus_returns_prometheus_text():
    """export_prometheus() returns (bytes, content_type) in Prometheus format."""
    body, ctype = export_prometheus()
    assert isinstance(body, bytes)
    assert ctype == CONTENT_TYPE_LATEST
    # Body should contain the help/type lines for our metrics.
    text = body.decode("utf-8")
    assert "# HELP heretek_swarm_agents_total" in text
    assert "# TYPE heretek_swarm_agents_total gauge" in text
    assert "heretek_swarm_tasks_completed_total" in text
    assert "heretek_swarm_phi_score" in text


def test_build_test_registry_returns_fresh_collector():
    """build_test_registry() returns a fresh CollectorRegistry for tests."""
    reg = build_test_registry()
    assert isinstance(reg, CollectorRegistry)
    assert reg is not REGISTRY  # Sanity: it's a fresh one, not the default
