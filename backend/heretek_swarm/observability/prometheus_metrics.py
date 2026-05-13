"""
Prometheus Metrics for Heretek Swarm

Provides Prometheus-compatible metrics for autonomous 24/7 operation monitoring.

Metrics:
- heretek_swarm_agents_total (Gauge): Total number of registered agents
- heretek_swarm_agents_active (Gauge): Number of currently active agents
- heretek_swarm_tasks_completed_total (Counter): Total tasks completed
- heretek_swarm_tasks_failed_total (Counter): Total tasks failed
- heretek_swarm_messages_total (Counter): Total messages processed
- heretek_swarm_consensus_rounds_total (Counter): Total consensus rounds
- heretek_swarm_phi_score (Gauge): Current phi consciousness score
- heretek_swarm_free_energy (Gauge): Current free energy level
- heretek_swarm_api_request_duration_seconds (Histogram): API request latency
- heretek_swarm_api_requests_total (Counter): Total API requests
- heretek_swarm_external_call_logs_total (Counter): Total external call logs
- heretek_swarm_external_call_log_duration_seconds (Histogram): External call duration
- heretek_swarm_encryption_latency_seconds (Histogram): Encryption/decryption latency

Usage:
    from heretek_swarm.observability.prometheus_metrics import (
        PrometheusMetrics,
        get_metrics,
        increment_tasks_completed,
        record_api_request,
        increment_external_call_logs,
        record_encryption_latency,
    )

    # Get singleton metrics instance
    metrics = get_metrics()

    # Record task completion
    increment_tasks_completed(agent_id="agent_1")

    # Record API request
    record_api_request(method="GET", endpoint="/api/agents", status=200, duration=0.05)

    # Record external call log
    increment_external_call_logs(agent_type="executor", call_type="tool", status=200)

    # Record encryption latency
    record_encryption_latency(operation="encrypt", field_type="body", duration_seconds=0.001)

    # Export metrics in Prometheus format
    from starlette.responses import PlainTextResponse
    return PlainTextResponse(get_metrics().export_prometheus())
"""

import structlog

logger = structlog.get_logger("prometheus_metrics")

import time  # noqa: E402

from prometheus_client import (  # noqa: E402
    CONTENT_TYPE_LATEST,
    REGISTRY,
    CollectorRegistry,
    Counter,
    Gauge,
    Histogram,
    generate_latest,
)

# Default registry (use default to allow automatic metric collection)
DEFAULT_REGISTRY = REGISTRY

# ============================================================================
# Custom Registry for Heretek Swarm
# ============================================================================

# Create a dedicated registry for the swarm metrics
# This allows us to isolate metrics and avoid conflicts
_swarm_registry = CollectorRegistry()

# ============================================================================
# Agent Metrics (Gauges)
# ============================================================================

heretek_swarm_agents_total = Gauge(
    "heretek_swarm_agents_total",
    "Total number of registered agents in the swarm",
    ["agent_type"],
    registry=_swarm_registry,
)

heretek_swarm_agents_active = Gauge(
    "heretek_swarm_agents_active",
    "Number of currently active agents",
    ["agent_type"],
    registry=_swarm_registry,
)

heretek_swarm_phi_score = Gauge(
    "heretek_swarm_phi_score",
    "Current consciousness phi score (IIT integration measure)",
    ["agent_id"],
    registry=_swarm_registry,
)

heretek_swarm_free_energy = Gauge(
    "heretek_swarm_free_energy",
    "Current free energy level (FEP measure)",
    ["agent_id"],
    registry=_swarm_registry,
)

# ============================================================================
# Task Metrics (Counters)
# ============================================================================

heretek_swarm_tasks_completed_total = Counter(
    "heretek_swarm_tasks_completed_total",
    "Total number of tasks completed",
    ["agent_id", "task_type"],
    registry=_swarm_registry,
)

heretek_swarm_tasks_failed_total = Counter(
    "heretek_swarm_tasks_failed_total",
    "Total number of tasks failed",
    ["agent_id", "task_type"],
    registry=_swarm_registry,
)

# ============================================================================
# Message Metrics (Counters)
# ============================================================================

heretek_swarm_messages_total = Counter(
    "heretek_swarm_messages_total",
    "Total number of messages processed",
    ["direction", "message_type"],
    registry=_swarm_registry,
)

# ============================================================================
# Consensus Metrics (Counters)
# ============================================================================

heretek_swarm_consensus_rounds_total = Counter(
    "heretek_swarm_consensus_rounds_total",
    "Total number of consensus rounds completed",
    ["consensus_type", "outcome"],
    registry=_swarm_registry,
)

# ============================================================================
# API Metrics (Histogram + Counter)
# ============================================================================

heretek_swarm_api_request_duration_seconds = Histogram(
    "heretek_swarm_api_request_duration_seconds",
    "API request latency in seconds",
    ["method", "endpoint", "status"],
    buckets=(0.005, 0.01, 0.025, 0.05, 0.075, 0.1, 0.25, 0.5, 0.75, 1.0, 2.5, 5.0, 7.5, 10.0),
    registry=_swarm_registry,
)

heretek_swarm_api_requests_total = Counter(
    "heretek_swarm_api_requests_total",
    "Total number of API requests",
    ["method", "endpoint", "status"],
    registry=_swarm_registry,
)

# ============================================================================
# ExternalCallLog Model Metrics
# ============================================================================

heretek_swarm_external_call_logs_total = Counter(
    "heretek_swarm_external_call_logs_total",
    "Total number of external call logs recorded",
    ["agent_type", "call_type", "status"],
    registry=_swarm_registry,
)

heretek_swarm_external_call_log_duration_seconds = Histogram(
    "heretek_swarm_external_call_log_duration_seconds",
    "Duration of external API calls in seconds",
    ["agent_type", "call_type", "method"],
    buckets=(0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0),
    registry=_swarm_registry,
)

heretek_swarm_encryption_latency_seconds = Histogram(
    "heretek_swarm_encryption_latency_seconds",
    "Latency of Fernet encryption/decryption operations in seconds",
    ["operation", "field_type"],
    buckets=(0.0001, 0.0005, 0.001, 0.005, 0.01, 0.025, 0.05, 0.1),
    registry=_swarm_registry,
)

# ============================================================================
# Health Metrics (Gauges)
# ============================================================================

heretek_swarm_health_score = Gauge(
    "heretek_swarm_health_score",
    "Overall swarm health score (0-100)",
    registry=_swarm_registry,
)

heretek_swarm_uptime_seconds = Gauge(
    "heretek_swarm_uptime_seconds",
    "Swarm uptime in seconds",
    registry=_swarm_registry,
)


class PrometheusMetrics:
    """
    Prometheus metrics collector for Heretek Swarm.

    Provides a high-level interface for recording metrics and exporting
    them in Prometheus text format.

    Example:
        metrics = PrometheusMetrics()

        # Record agent activity
        metrics.record_agent_registration("agent_1", "executor")
        metrics.record_agent_active("agent_1", "executor")

        # Record task completion
        metrics.record_task_completed("agent_1", "executor", "analysis")

        # Get Prometheus format output
        output = metrics.export_prometheus()
    """

    def __init__(self, registry=None):
        """
        Initialize the Prometheus metrics collector.

        Args:
            registry: Optional custom registry. Defaults to _swarm_registry.
        """
        self._registry = registry or _swarm_registry
        self._start_time = time.time()
        self._agent_types: dict[str, str] = {}  # agent_id -> agent_type

    def record_agent_registration(self, agent_id: str, agent_type: str = "unknown") -> None:
        """Record a new agent registration."""
        self._agent_types[agent_id] = agent_type
        heretek_swarm_agents_total.labels(agent_type=agent_type).inc()

    def record_agent_active(self, _agent_id: str, agent_type: str = "unknown") -> None:
        """Record an agent becoming active."""
        heretek_swarm_agents_active.labels(agent_type=agent_type).inc()

    def record_agent_inactive(self, _agent_id: str, agent_type: str = "unknown") -> None:
        """Record an agent becoming inactive."""
        heretek_swarm_agents_active.labels(agent_type=agent_type).dec()

    def record_agent_unregistration(self, agent_id: str) -> None:
        """Record an agent unregistration."""
        agent_type = self._agent_types.pop(agent_id, "unknown")
        heretek_swarm_agents_total.labels(agent_type=agent_type).dec()
        heretek_swarm_agents_active.labels(agent_type=agent_type).dec(
            max(heretek_swarm_agents_active.labels(agent_type=agent_type)._value.get(), 0)  # noqa: SLF001
        )

    def record_task_completed(
        self, agent_id: str, agent_type: str = "unknown", task_type: str = "general"  # noqa: ARG002
    ) -> None:
        """Record a task completion."""
        heretek_swarm_tasks_completed_total.labels(agent_id=agent_id, task_type=task_type).inc()

    def record_task_failed(
        self, agent_id: str, agent_type: str = "unknown", task_type: str = "general"  # noqa: ARG002
    ) -> None:
        """Record a task failure."""
        heretek_swarm_tasks_failed_total.labels(agent_id=agent_id, task_type=task_type).inc()

    def record_message_sent(self, message_type: str = "general") -> None:
        """Record a sent message."""
        heretek_swarm_messages_total.labels(direction="sent", message_type=message_type).inc()

    def record_message_received(self, message_type: str = "general") -> None:
        """Record a received message."""
        heretek_swarm_messages_total.labels(direction="received", message_type=message_type).inc()

    def record_consensus_round(
        self, consensus_type: str = "deliberation", outcome: str = "success"
    ) -> None:
        """Record a consensus round."""
        heretek_swarm_consensus_rounds_total.labels(
            consensus_type=consensus_type, outcome=outcome
        ).inc()

    def record_phi_score(self, agent_id: str, score: float) -> None:
        """Record a consciousness phi score."""
        heretek_swarm_phi_score.labels(agent_id=agent_id).set(score)

    def record_free_energy(self, agent_id: str, energy: float) -> None:
        """Record a free energy level."""
        heretek_swarm_free_energy.labels(agent_id=agent_id).set(energy)

    def record_api_request(self, method: str, endpoint: str, status: int, duration: float) -> None:
        """Record an API request with latency."""
        # Normalize endpoint to avoid high cardinality
        normalized_endpoint = self._normalize_endpoint(endpoint)

        heretek_swarm_api_request_duration_seconds.labels(
            method=method, endpoint=normalized_endpoint, status=str(status)
        ).observe(duration)

        heretek_swarm_api_requests_total.labels(
            method=method, endpoint=normalized_endpoint, status=str(status)
        ).inc()

    def record_external_call_log(
        self,
        agent_type: str = "unknown",
        call_type: str = "general",
        status: int | None = None,
        duration_seconds: float | None = None,
    ) -> None:
        """
        Record an external call log entry.

        Args:
            agent_type: Type of agent making the call
            call_type: Type of external call (e.g., 'tool', 'api', 'mcp')
            status: HTTP status code of the response
            duration_seconds: Duration of the external call
        """
        status_label = str(status) if status is not None else "unknown"
        heretek_swarm_external_call_logs_total.labels(
            agent_type=agent_type,
            call_type=call_type,
            status=status_label,
        ).inc()

        if duration_seconds is not None:
            heretek_swarm_external_call_log_duration_seconds.labels(
                agent_type=agent_type,
                call_type=call_type,
                method="UNKNOWN",  # Method tracked separately in call log
            ).observe(duration_seconds)

    def record_encryption_latency(
        self,
        operation: str = "encrypt",
        field_type: str = "body",
        duration_seconds: float | None = None,
    ) -> None:
        """
        Record encryption/decryption latency.

        Args:
            operation: Type of operation ('encrypt' or 'decrypt')
            field_type: Type of field being encrypted ('body', 'headers', 'response')
            duration_seconds: Duration of the encryption operation
        """
        if duration_seconds is not None:
            heretek_swarm_encryption_latency_seconds.labels(
                operation=operation,
                field_type=field_type,
            ).observe(duration_seconds)

    def record_health_score(self, score: float) -> None:
        """Record the overall health score."""
        heretek_swarm_health_score.set(score)

    def update_uptime(self) -> None:
        """Update the uptime gauge."""
        uptime = time.time() - self._start_time
        heretek_swarm_uptime_seconds.set(uptime)

    def _normalize_endpoint(self, endpoint: str) -> str:
        """
        Normalize endpoint to reduce cardinality.

        Replaces dynamic path segments (UUIDs, IDs) with placeholders.
        """
        import re

        # Replace UUIDs
        endpoint = re.sub(
            r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}",
            "{id}",
            endpoint,
            flags=re.IGNORECASE,
        )

        # Replace numeric IDs
        return re.sub(r"/\d+(?=/|$)", "/{id}", endpoint)

    def export_prometheus(self) -> bytes:
        """
        Export all metrics in Prometheus text format.

        Returns:
            Metrics in Prometheus text exposition format.
        """
        self.update_uptime()
        return generate_latest(self._registry)

    def get_content_type(self) -> str:
        """Get the Prometheus content type."""
        return CONTENT_TYPE_LATEST

    def reset(self) -> None:
        """Reset all metrics to their initial state."""
        # Note: Prometheus counters cannot be reset directly
        # In production, you would create a new registry
        self._start_time = time.time()
        self._agent_types.clear()


# ============================================================================
# Global Metrics Instance (Singleton Pattern)
# ============================================================================

_metrics_instance: PrometheusMetrics | None = None


def get_metrics() -> PrometheusMetrics:
    """
    Get the global Prometheus metrics instance.

    Returns:
        The singleton PrometheusMetrics instance.
    """
    global _metrics_instance
    if _metrics_instance is None:
        _metrics_instance = PrometheusMetrics()
    return _metrics_instance


def reset_metrics() -> None:
    """Reset the global metrics instance."""
    global _metrics_instance
    _metrics_instance = None


# ============================================================================
# Convenience Functions
# ============================================================================


def increment_tasks_completed(agent_id: str, task_type: str = "general") -> None:
    """Convenience function to increment completed tasks counter."""
    metrics = get_metrics()
    agent_type = metrics._agent_types.get(agent_id, "unknown")  # noqa: SLF001
    metrics.record_task_completed(agent_id, agent_type, task_type)


def increment_tasks_failed(agent_id: str, task_type: str = "general") -> None:
    """Convenience function to increment failed tasks counter."""
    metrics = get_metrics()
    agent_type = metrics._agent_types.get(agent_id, "unknown")  # noqa: SLF001
    metrics.record_task_failed(agent_id, agent_type, task_type)


def increment_messages_sent(message_type: str = "general") -> None:
    """Convenience function to increment sent messages counter."""
    get_metrics().record_message_sent(message_type)


def increment_messages_received(message_type: str = "general") -> None:
    """Convenience function to increment received messages counter."""
    get_metrics().record_message_received(message_type)


def increment_consensus_rounds(
    consensus_type: str = "deliberation", outcome: str = "success"
) -> None:
    """Convenience function to increment consensus rounds counter."""
    get_metrics().record_consensus_round(consensus_type, outcome)


def set_phi_score(agent_id: str, score: float) -> None:
    """Convenience function to set phi consciousness score."""
    get_metrics().record_phi_score(agent_id, score)


def set_free_energy(agent_id: str, energy: float) -> None:
    """Convenience function to set free energy level."""
    get_metrics().record_free_energy(agent_id, energy)


def record_api_request(method: str, endpoint: str, status: int, duration: float) -> None:
    """Convenience function to record an API request."""
    get_metrics().record_api_request(method, endpoint, status, duration)


def update_health_score(score: float) -> None:
    """Convenience function to update the health score."""
    get_metrics().record_health_score(score)


def increment_external_call_logs(
    agent_type: str = "unknown",
    call_type: str = "general",
    status: int | None = None,
    duration_seconds: float | None = None,
) -> None:
    """
    Convenience function to record an external call log entry.

    Args:
        agent_type: Type of agent making the call
        call_type: Type of external call (e.g., 'tool', 'api', 'mcp')
        status: HTTP status code of the response
        duration_seconds: Duration of the external call
    """
    get_metrics().record_external_call_log(
        agent_type=agent_type,
        call_type=call_type,
        status=status,
        duration_seconds=duration_seconds,
    )


def record_encryption_latency(
    operation: str = "encrypt",
    field_type: str = "body",
    duration_seconds: float | None = None,
) -> None:
    """
    Convenience function to record encryption/decryption latency.

    Args:
        operation: Type of operation ('encrypt' or 'decrypt')
        field_type: Type of field being encrypted ('body', 'headers', 'response')
        duration_seconds: Duration of the encryption operation
    """
    get_metrics().record_encryption_latency(
        operation=operation,
        field_type=field_type,
        duration_seconds=duration_seconds,
    )


# ============================================================================
# FastAPI Middleware Helper
# ============================================================================


def setup_metrics_middleware(app) -> None:
    """
    Setup Prometheus metrics middleware for FastAPI.

    This function adds middleware that automatically records
    request metrics for all API endpoints.

    Args:
        app: FastAPI application instance

    Example:
        from fastapi import FastAPI
        from heretek_swarm.observability.prometheus_metrics import setup_metrics_middleware

        app = FastAPI()
        setup_metrics_middleware(app)
    """
    import time

    from starlette.middleware.base import BaseHTTPMiddleware
    from starlette.requests import Request

    class PrometheusMiddleware(BaseHTTPMiddleware):
        async def dispatch(self, request: Request, call_next):
            # Skip metrics endpoint itself
            if request.url.path == "/metrics":
                return await call_next(request)

            start_time = time.perf_counter()

            response = await call_next(request)

            duration = time.perf_counter() - start_time

            # Record the request
            try:
                record_api_request(
                    method=request.method,
                    endpoint=request.url.path,
                    status=response.status_code,
                    duration=duration,
                )
            except Exception as e:
                # Don't let metrics collection break the app
                logger.debug("prometheus_metrics_collection_failed", error=str(e))

            return response

    app.add_middleware(PrometheusMiddleware)
