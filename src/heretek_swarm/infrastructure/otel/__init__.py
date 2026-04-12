"""
OpenTelemetry (OTel) Infrastructure.

Provides distributed tracing, metrics collection, and structured logging
for the Heretek Swarm based on OpenTelemetry standards.
"""

from heretek_swarm.infrastructure.otel.tracing import (
    TracingConfig,
    get_tracer,
    init_tracing,
    create_span,
    with_span,
)
from heretek_swarm.infrastructure.otel.metrics import (
    MetricsConfig,
    get_meter,
    init_metrics,
    record_metric,
    MetricsCollector,
)
from heretek_swarm.infrastructure.otel.logging import (
    LoggingConfig,
    init_logging,
    get_log_config,
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
