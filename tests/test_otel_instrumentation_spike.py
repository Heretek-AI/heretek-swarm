"""Tests for the Phase 2A.5 OTel instrumentation completion spike."""

from __future__ import annotations

from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor

from heretek_swarm.infrastructure.otel.otel_instrumentation_spike import (
    run_dry_spike,
)


def test_dry_spike_passes():
    """The OTel instrumentation API surface is valid."""
    run_dry_spike()


def test_fastapi_instrumentor_is_importable():
    """FastAPIInstrumentor is importable from opentelemetry.instrumentation.fastapi."""
    assert FastAPIInstrumentor is not None
    assert callable(FastAPIInstrumentor.instrument_app)


def test_httpx_instrumentor_is_importable():
    """HTTPXClientInstrumentor is importable from opentelemetry.instrumentation.httpx."""
    assert HTTPXClientInstrumentor is not None
    instrumentor = HTTPXClientInstrumentor()
    assert callable(instrumentor.instrument)
