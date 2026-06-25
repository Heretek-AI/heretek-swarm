"""Tests for OTel metric instruments."""

from __future__ import annotations

from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import InMemoryMetricReader

from tier1.observability.metrics import (
    get_meter,
    record_provider_call,
    record_consensus_outcome,
    record_agent_tokens,
    record_deliberation_latency,
    record_deliberation_rounds,
    toggle_circuit_state,
)


def _setup_provider():
    reader = InMemoryMetricReader()
    provider = MeterProvider(metric_readers=[reader])
    return provider, reader


def test_get_meter_returns_meter():
    provider, _ = _setup_provider()
    meter = get_meter("test", provider=provider)
    assert meter is not None


def test_record_provider_call():
    provider, reader = _setup_provider()
    get_meter("test", provider=provider)
    record_provider_call("minimax", 0.5, provider=provider)
    record_provider_call("minimax", 1.0, provider=provider)
    metrics = reader.get_metrics_data()
    assert len(metrics.resource_metrics) > 0


def test_record_consensus_outcome():
    provider, reader = _setup_provider()
    get_meter("test", provider=provider)
    record_consensus_outcome("approved", provider=provider)
    record_consensus_outcome("no-consensus", provider=provider)
    metrics = reader.get_metrics_data()
    assert len(metrics.resource_metrics) > 0


def test_record_agent_tokens():
    provider, reader = _setup_provider()
    get_meter("test", provider=provider)
    record_agent_tokens("alpha", 42, provider=provider)
    metrics = reader.get_metrics_data()
    assert len(metrics.resource_metrics) > 0


def test_record_deliberation_latency():
    provider, reader = _setup_provider()
    get_meter("test", provider=provider)
    record_deliberation_latency(5.0, provider=provider)
    metrics = reader.get_metrics_data()
    assert len(metrics.resource_metrics) > 0


def test_record_deliberation_rounds():
    provider, reader = _setup_provider()
    get_meter("test", provider=provider)
    record_deliberation_rounds(2, provider=provider)
    metrics = reader.get_metrics_data()
    assert len(metrics.resource_metrics) > 0


def test_toggle_circuit_state():
    provider, reader = _setup_provider()
    get_meter("test", provider=provider)
    toggle_circuit_state("minimax", +1, provider=provider)
    toggle_circuit_state("minimax", -1, provider=provider)
    metrics = reader.get_metrics_data()
    assert len(metrics.resource_metrics) > 0
