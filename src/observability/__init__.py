"""
Observability package for Heretek Swarm.

Provides OpenTelemetry-based distributed tracing and metrics collection.
"""

from .metrics import (
    MetricsConfig,
    SwarmMetrics,
    get_meter,
    init_metrics,
    record_consensus_round,
    record_message_latency,
    record_message_sent,
    record_state_rollback,
    record_task_completion,
)
from .tracing import (
    LATENCY_BASELINE_MS,
    SpanAttributes,
    TracingConfig,
    get_tracer,
    init_tracing,
    record_vote,
    trace_consensus_round,
    trace_message_flow,
    traced,
    traced_agent_method,
    track_latency,
)

__all__ = [
    "LATENCY_BASELINE_MS",
    "MetricsConfig",
    "SpanAttributes",
    "SwarmMetrics",
    "TracingConfig",
    "get_meter",
    "get_tracer",
    # Metrics
    "init_metrics",
    # Tracing
    "init_tracing",
    "record_consensus_round",
    "record_message_latency",
    "record_message_sent",
    "record_state_rollback",
    "record_task_completion",
    "record_vote",
    "trace_consensus_round",
    "trace_message_flow",
    "traced",
    "traced_agent_method",
    "track_latency",
]
