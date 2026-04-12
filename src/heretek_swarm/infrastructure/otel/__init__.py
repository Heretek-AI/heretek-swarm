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
    TracingConfig,
    create_span,
    get_tracer,
    init_tracing,
    with_span,
)

__all__ = [
    # Tracing
    "TracingConfig",
    "get_tracer",
    "init_tracing",
    "create_span",
    "with_span",
    # Metrics
    "MetricsConfig",
    "get_meter",
    "init_metrics",
    "record_metric",
    "MetricsCollector",
    # Logging
    "LoggingConfig",
    "init_logging",
    "get_log_config",
]
