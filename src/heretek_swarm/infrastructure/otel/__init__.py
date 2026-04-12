"""
OpenTelemetry (OTel) Infrastructure.

Provides distributed tracing, metrics collection, and structured logging
for the Heretek Swarm based on OpenTelemetry standards.
"""

from heretek_swarm.infrastructure.otel.logging import (
    LoggingConfig,
    get_log_config,
    init_logging,
)
from heretek_swarm.infrastructure.otel.metrics import (
    MetricsCollector,
    MetricsConfig,
    get_meter,
    init_metrics,
    record_metric,
)
from heretek_swarm.infrastructure.otel.tracing import (
    SpanAttributes,
    SpanKind,
    SpanNames,
    SpanStatus,
    TraceState,
    TracingConfig,
    create_span,
    create_tracing_config,
    get_current_span,
    get_trace_context,
    get_tracer,
    init_tracing,
    set_span_attribute,
    set_span_attributes,
    span_context,
    with_span,
)

__all__ = [
    # Logging
    "LoggingConfig",
    "MetricsCollector",
    # Metrics
    "MetricsConfig",
    # Tracing
    "SpanAttributes",
    "SpanKind",
    "SpanNames",
    "SpanStatus",
    "TraceState",
    "TracingConfig",
    "create_span",
    "create_tracing_config",
    "get_current_span",
    "get_log_config",
    "get_meter",
    "get_trace_context",
    "get_tracer",
    "init_logging",
    "init_metrics",
    "init_tracing",
    "record_metric",
    "set_span_attribute",
    "set_span_attributes",
    "span_context",
    "with_span",
]
