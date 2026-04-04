"""
Observability package for Heretek Swarm.

Provides OpenTelemetry-based distributed tracing and metrics collection.
"""

from .tracing import (
    LATENCY_BASELINE_MS,
    SpanAttributes,
    TracingConfig,
    get_tracer,
    init_tracing,
    record_vote,
    trace_consensus_round,
    trace_message_flow,
    track_latency,
    traced,
    traced_agent_method,
)
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

__all__ = [
    # Tracing
    "init_tracing",
    "get_tracer",
    "traced",
    "traced_agent_method",
    "track_latency",
    "trace_message_flow",
    "trace_consensus_round",
    "record_vote",
    "TracingConfig",
    "SpanAttributes",
    "LATENCY_BASELINE_MS",
    # Metrics
    "init_metrics",
    "get_meter",
    "SwarmMetrics",
    "MetricsConfig",
    "record_message_sent",
    "record_message_latency",
    "record_task_completion",
    "record_consensus_round",
    "record_state_rollback",
]
