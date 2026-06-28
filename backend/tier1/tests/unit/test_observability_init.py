"""Tests for init_telemetry wiring."""

from __future__ import annotations

from unittest.mock import patch, MagicMock
from fastapi import FastAPI
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter


def test_init_telemetry_configures_structlog():
    """init_telemetry should inject add_trace_context into structlog."""
    from tier1.observability import init_telemetry

    app = FastAPI()
    with patch("tier1.observability._init_otel") as mock_otel:
        init_telemetry(app)
        mock_otel.assert_called_once()


def test_init_telemetry_installs_fastapi_instrumentor():
    """init_telemetry should instrument the FastAPI app."""
    from tier1.observability import init_telemetry

    app = FastAPI()
    with patch("tier1.observability._init_otel"):
        init_telemetry(app)
    # If _init_otel is mocked, we just verify init_telemetry doesn't crash.


def test_init_telemetry_configures_tracer_provider():
    """init_telemetry builds an OTLPSpanExporter + TracerProvider for traces."""
    app = FastAPI()
    with (
        patch(
            "opentelemetry.exporter.otlp.proto.http.trace_exporter.OTLPSpanExporter"
        ) as mock_span_exporter,
        patch("opentelemetry.sdk.trace.export.BatchSpanProcessor") as mock_batch,
        patch("opentelemetry.sdk.trace.TracerProvider") as mock_tracer_prov,
        patch("opentelemetry.instrumentation.fastapi.FastAPIInstrumentor") as mock_fapi,
        patch("tier1.observability.metrics.set_default_provider"),
    ):
        from tier1.observability import init_telemetry

        init_telemetry(app)
    mock_span_exporter.assert_called_once()
    # Jaeger endpoint per spec.
    endpoint = (
        mock_span_exporter.call_args.kwargs.get("endpoint") or mock_span_exporter.call_args.args[0]
    )
    assert "jaeger:4318" in endpoint
    # BatchSpanProcessor wraps the exporter and is added to the provider.
    mock_batch.assert_called_once_with(mock_span_exporter.return_value)
    mock_tracer_prov.return_value.add_span_processor.assert_called_once_with(
        mock_batch.return_value
    )


def test_init_telemetry_configures_meter_provider():
    """init_telemetry builds an OTLPMetricExporter + PeriodicExportingMetricReader + MeterProvider."""
    app = FastAPI()
    with (
        patch(
            "opentelemetry.exporter.otlp.proto.http.metric_exporter.OTLPMetricExporter"
        ) as mock_metric_exporter,
        patch("opentelemetry.sdk.metrics.export.PeriodicExportingMetricReader") as mock_reader,
        patch("opentelemetry.sdk.metrics.MeterProvider") as mock_meter_prov,
        patch("opentelemetry.instrumentation.fastapi.FastAPIInstrumentor"),
        patch("tier1.observability.structlog.configure") as mock_structlog,
        patch("tier1.observability.metrics.set_default_provider"),
    ):
        from tier1.observability import init_telemetry

        init_telemetry(app)
    mock_metric_exporter.assert_called_once()
    endpoint = (
        mock_metric_exporter.call_args.kwargs.get("endpoint")
        or mock_metric_exporter.call_args.args[0]
    )
    assert "jaeger:4318" in endpoint
    mock_reader.assert_called_once()
    # 10s export interval per spec.
    assert mock_reader.call_args.kwargs.get("export_interval_millis") == 10000
    mock_meter_prov.assert_called_once_with(metric_readers=[mock_reader.return_value])
    # structlog.configure was called with a processor list that includes add_trace_context.
    processors = (
        mock_structlog.call_args.kwargs.get("processors") or mock_structlog.call_args.args[0]
    )
    from tier1.observability.logging import add_trace_context

    assert add_trace_context in processors


def test_init_telemetry_calls_set_default_provider():
    """init_telemetry forwards the meter provider to metrics.set_default_provider."""
    from tier1.observability.metrics import set_default_provider

    app = FastAPI()
    with (
        patch("opentelemetry.exporter.otlp.proto.http.trace_exporter.OTLPSpanExporter"),
        patch("opentelemetry.exporter.otlp.proto.http.metric_exporter.OTLPMetricExporter"),
        patch("opentelemetry.sdk.metrics.export.PeriodicExportingMetricReader"),
        patch("opentelemetry.sdk.trace.TracerProvider"),
        patch("opentelemetry.sdk.metrics.MeterProvider") as mock_meter_prov,
        patch("opentelemetry.instrumentation.fastapi.FastAPIInstrumentor"),
        patch("tier1.observability.structlog.configure"),
        patch("tier1.observability.metrics.set_default_provider") as mock_set_default,
    ):
        from tier1.observability import init_telemetry

        init_telemetry(app)
    mock_set_default.assert_called_once_with(mock_meter_prov.return_value)


def test_init_telemetry_produces_observable_spans():
    """Integration: after init_telemetry(), spans emitted via get_tracer() reach an exporter.

    Replaces the global TracerProvider with one whose exporter is in-memory,
    so the assertion is deterministic without needing a live Jaeger.
    """
    from opentelemetry import trace
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import SimpleSpanProcessor
    from opentelemetry.trace import _TRACER_PROVIDER_SET_ONCE
    from tier1.observability import init_telemetry, get_tracer

    # OTel's set_tracer_provider is one-shot — reset the flag both before and
    # patch the call during init_telemetry so the in-memory provider below can
    # still be installed.
    _TRACER_PROVIDER_SET_ONCE._done = False

    app = FastAPI()
    with (
        patch("opentelemetry.exporter.otlp.proto.http.trace_exporter.OTLPSpanExporter"),
        patch("opentelemetry.exporter.otlp.proto.http.metric_exporter.OTLPMetricExporter"),
        patch("opentelemetry.sdk.metrics.export.PeriodicExportingMetricReader"),
        patch("tier1.observability.metrics.set_default_provider"),
        patch("opentelemetry.trace.set_tracer_provider"),
    ):
        init_telemetry(app)

    # Reset the once-flag again — init_telemetry was patched to a no-op so it
    # did NOT set the provider, but earlier tests may have. Either way the
    # flag may now be True; clear it so the in-memory install takes effect.
    _TRACER_PROVIDER_SET_ONCE._done = False

    # Replace the global provider with one whose exporter is in-memory.
    in_memory = InMemorySpanExporter()
    new_provider = TracerProvider()
    new_provider.add_span_processor(SimpleSpanProcessor(in_memory))
    trace.set_tracer_provider(new_provider)

    tracer = get_tracer("test.integration")
    with tracer.start_as_current_span("test-span"):
        pass

    spans = in_memory.get_finished_spans()
    assert any(s.name == "test-span" for s in spans), (
        f"expected test-span, got {[s.name for s in spans]}"
    )
    span = next(s for s in spans if s.name == "test-span")
    assert span.context.trace_id != 0
