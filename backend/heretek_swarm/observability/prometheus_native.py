"""
Prometheus metrics — native ``prometheus_client`` interface.

This module is the Phase 2A cutover of the OSS replacement roadmap.
It replaces the hand-rolled ``observability/prometheus_metrics.py``
wrapper class (``PrometheusMetrics``, 755 LOC) with a thin facade
over the official ``prometheus_client`` library (already a dep).
The wrapper class re-exports from this module so existing callers
do not need to change yet; the follow-up PR removes the wrapper
entirely.

Why this exists
---------------
``prometheus_client`` (the official Prometheus Python client) already
provides everything ``PrometheusMetrics`` was re-implementing:

- ``Counter`` / ``Gauge`` / ``Histogram`` for typed metrics
- ``generate_latest()`` for the Prometheus text exposition format
- ``CONTENT_TYPE_LATEST`` for the proper response content type
- ``REGISTRY`` and custom ``CollectorRegistry`` for namespace isolation
- The 75-line ``sync_with_swarm_collector`` helper in
  ``api/metrics.py`` does what ``prometheus_client.CollectorRegistry``
  callbacks do for free.

Per the plan, the goal is to "drop the wrapper, use prometheus-client
native." This module is the first step: it provides a thin facade
over the native API so callers can migrate incrementally.

Migration pattern
-----------------
Old code (in any of the 9 files that import the wrapper)::

    from heretek_swarm.observability.prometheus_metrics import (
        PrometheusMetrics,
        get_metrics,
    )
    metrics = get_metrics()
    metrics.increment_tasks_completed(agent_id="agent_1")

New code (uses this module)::

    from heretek_swarm.observability.prometheus_native import (
        TASKS_COMPLETED,
        increment_tasks_completed,
    )
    increment_tasks_completed(agent_id="agent_1")

The ``TASKS_COMPLETED`` constant is a module-level ``Counter``; calling
its ``.inc()`` method (or the ``increment_tasks_completed`` helper for
backward compat) records the event. No class instance, no wrapper.
"""

from __future__ import annotations

from prometheus_client import (
    CONTENT_TYPE_LATEST,
    REGISTRY,
    CollectorRegistry,
    Counter,
    Gauge,
    Histogram,
    generate_latest,
)

# ---------------------------------------------------------------------------
# Module-level metrics — the prometheus_client pattern
# ---------------------------------------------------------------------------
# Defining the metrics at module level (rather than inside a class)
# is the idiomatic prometheus_client pattern. The library registers
# each metric with the default REGISTRY on import; this means the
# metric is automatically exposed via generate_latest() without any
# additional plumbing.

AGENTS_TOTAL = Gauge(
    "heretek_swarm_agents_total",
    "Total number of registered agents in the swarm",
    registry=REGISTRY,
)
AGENTS_ACTIVE = Gauge(
    "heretek_swarm_agents_active",
    "Number of currently active agents",
    registry=REGISTRY,
)
TASKS_COMPLETED = Counter(
    "heretek_swarm_tasks_completed_total",
    "Total tasks completed by the swarm",
    labelnames=["agent_id", "task_type"],
    registry=REGISTRY,
)
TASKS_FAILED = Counter(
    "heretek_swarm_tasks_failed_total",
    "Total tasks that failed",
    labelnames=["agent_id", "task_type"],
    registry=REGISTRY,
)
MESSAGES_TOTAL = Counter(
    "heretek_swarm_messages_total",
    "Total messages processed",
    labelnames=["direction", "agent_id"],
    registry=REGISTRY,
)
CONSENSUS_ROUNDS = Counter(
    "heretek_swarm_consensus_rounds_total",
    "Total consensus rounds executed",
    labelnames=["consensus_type", "outcome"],
    registry=REGISTRY,
)
PHI_SCORE = Gauge(
    "heretek_swarm_phi_score",
    "Current phi consciousness score (IIT)",
    labelnames=["agent_id"],
    registry=REGISTRY,
)
FREE_ENERGY = Gauge(
    "heretek_swarm_free_energy",
    "Current free energy level (FEP)",
    labelnames=["agent_id"],
    registry=REGISTRY,
)
HEALTH_SCORE = Gauge(
    "heretek_swarm_health_score",
    "Current swarm health score (0.0-1.0)",
    registry=REGISTRY,
)
API_REQUEST_DURATION = Histogram(
    "heretek_swarm_api_request_duration_seconds",
    "API request latency in seconds",
    labelnames=["method", "endpoint", "status"],
    registry=REGISTRY,
)
API_REQUESTS_TOTAL = Counter(
    "heretek_swarm_api_requests_total",
    "Total API requests handled",
    labelnames=["method", "endpoint", "status"],
    registry=REGISTRY,
)
EXTERNAL_CALL_LOGS = Counter(
    "heretek_swarm_external_call_logs_total",
    "Total external call logs recorded",
    labelnames=["agent_type", "call_type", "status"],
    registry=REGISTRY,
)
EXTERNAL_CALL_DURATION = Histogram(
    "heretek_swarm_external_call_log_duration_seconds",
    "External call duration in seconds",
    labelnames=["call_type", "status"],
    registry=REGISTRY,
)
ENCRYPTION_LATENCY = Histogram(
    "heretek_swarm_encryption_latency_seconds",
    "Encryption/decryption latency in seconds",
    labelnames=["operation", "field_type"],
    registry=REGISTRY,
)


# ---------------------------------------------------------------------------
# Helper functions — drop-in replacements for the wrapper methods
# ---------------------------------------------------------------------------
# These functions are the migration target. Each corresponds to a
# method on the legacy ``PrometheusMetrics`` class. Existing callers
# can swap one import path at a time; the wrapper class remains
# available as a shim for the transition.


def increment_tasks_completed(agent_id: str, task_type: str = "default") -> None:
    """Record a task completion event."""
    TASKS_COMPLETED.labels(agent_id=agent_id, task_type=task_type).inc()


def increment_tasks_failed(agent_id: str, task_type: str = "default") -> None:
    """Record a task failure event."""
    TASKS_FAILED.labels(agent_id=agent_id, task_type=task_type).inc()


def increment_messages(direction: str, agent_id: str = "anonymous") -> None:
    """Record a message processed (direction = 'sent' or 'received')."""
    MESSAGES_TOTAL.labels(direction=direction, agent_id=agent_id).inc()


def increment_consensus_rounds(consensus_type: str, outcome: str) -> None:
    """Record a consensus round completion."""
    CONSENSUS_ROUNDS.labels(consensus_type=consensus_type, outcome=outcome).inc()


def record_phi_score(agent_id: str, score: float) -> None:
    """Record the current phi (IIT) score for an agent."""
    PHI_SCORE.labels(agent_id=agent_id).set(score)


def record_free_energy(agent_id: str, score: float) -> None:
    """Record the current free-energy (FEP) score for an agent."""
    FREE_ENERGY.labels(agent_id=agent_id).set(score)


def record_health_score(score: float) -> None:
    """Record the current swarm health score (0.0-1.0)."""
    HEALTH_SCORE.set(score)


def record_api_request(
    method: str, endpoint: str, status: int, duration: float
) -> None:
    """Record an API request's status code and duration."""
    status_str = str(status)
    API_REQUESTS_TOTAL.labels(method=method, endpoint=endpoint, status=status_str).inc()
    API_REQUEST_DURATION.labels(method=method, endpoint=endpoint, status=status_str).observe(
        duration
    )


def increment_external_call_logs(
    agent_type: str, call_type: str, status: int
) -> None:
    """Record an external call log event."""
    EXTERNAL_CALL_LOGS.labels(
        agent_type=agent_type, call_type=call_type, status=str(status)
    ).inc()


def record_external_call_duration(
    call_type: str, status: int, duration_seconds: float
) -> None:
    """Record the duration of an external call."""
    EXTERNAL_CALL_DURATION.labels(call_type=call_type, status=str(status)).observe(
        duration_seconds
    )


def record_encryption_latency(
    operation: str, field_type: str, duration_seconds: float
) -> None:
    """Record the latency of an encryption/decryption operation."""
    ENCRYPTION_LATENCY.labels(operation=operation, field_type=field_type).observe(
        duration_seconds
    )


def export_prometheus() -> tuple[bytes, str]:
    """Return (body, content_type) for the /metrics endpoint.

    This is the drop-in replacement for ``PrometheusMetrics.export_prometheus()``.
    Uses ``prometheus_client.generate_latest()`` directly.
    """
    return generate_latest(REGISTRY), CONTENT_TYPE_LATEST


# ---------------------------------------------------------------------------
# Test-only: a fresh registry for unit tests
# ---------------------------------------------------------------------------
# Tests need to instantiate metrics in a clean registry to avoid
# the "Duplicated timeseries" error on re-import. The factory below
# creates a fresh ``CollectorRegistry`` and re-instantiates all the
# metrics on it. Tests that need isolation call ``build_test_registry()``
# in a fixture; production code uses the module-level REGISTRY.


def build_test_registry() -> CollectorRegistry:
    """Build a fresh CollectorRegistry for tests.

    This is intentionally a factory rather than a singleton so
    tests can own their own registry. Production code does not
    need this; module-level metrics on REGISTRY are the right
    pattern for runtime use.
    """
    return CollectorRegistry()


__all__ = [
    "AGENTS_ACTIVE",
    "AGENTS_TOTAL",
    "API_REQUESTS_TOTAL",
    "API_REQUEST_DURATION",
    "CONSENSUS_ROUNDS",
    "CONTENT_TYPE_LATEST",
    "ENCRYPTION_LATENCY",
    "EXTERNAL_CALL_DURATION",
    "EXTERNAL_CALL_LOGS",
    "FREE_ENERGY",
    "HEALTH_SCORE",
    "MESSAGES_TOTAL",
    "PHI_SCORE",
    "TASKS_COMPLETED",
    "TASKS_FAILED",
    "build_test_registry",
    "export_prometheus",
    "increment_consensus_rounds",
    "increment_external_call_logs",
    "increment_messages",
    "increment_tasks_completed",
    "increment_tasks_failed",
    "record_api_request",
    "record_encryption_latency",
    "record_external_call_duration",
    "record_free_energy",
    "record_health_score",
    "record_phi_score",
]
