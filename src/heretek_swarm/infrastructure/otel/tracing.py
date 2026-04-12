"""
OpenTelemetry Tracing for Heretek Swarm.

Provides distributed tracing based on OpenTelemetry standards.
Supports OTLP export, console export, and B3 context propagation.
"""

from __future__ import annotations

import os
import uuid
from collections.abc import Callable
from contextlib import contextmanager
from dataclasses import dataclass
from enum import Enum
from functools import wraps
from typing import Any

import structlog
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.propagate import set_global_textmap
from opentelemetry.sdk.resources import SERVICE_NAME, SERVICE_VERSION, Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
from opentelemetry.sdk.trace.sampling import Sampler, TraceIdRatioBased
from opentelemetry.trace import Span, SpanKind, Status, StatusCode
from opentelemetry.trace.propagation.tracecontext import TraceContextTextMapPropagator

logger = structlog.get_logger(__name__)


class TraceState(Enum):
    """Trace lifecycle state."""
    UNSTARTED = "unstarted"
    ACTIVE = "active"
    ENDED = "ended"


class SpanStatus(Enum):
    """Span execution status."""
    UNSET = "unset"
    OK = "ok"
    ERROR = "error"


# =============================================================================
# Configuration
# =============================================================================


@dataclass
class TracingConfig:
    """Configuration for distributed tracing."""
    service_name: str = "heretek-swarm"
    service_version: str = "0.1.0"
    exporter: str = "console"  # console, otlp
    endpoint: str | None = None
    sample_rate: float = 1.0  # 0.0-1.0
    propagate_b3: bool = True
    max_attributes: int = 64
    max_span_events: int = 128


# =============================================================================
# Global State
# =============================================================================

_tracer_config: TracingConfig | None = None
_tracer_instance: trace.Tracer | None = None
_propagator = TraceContextTextMapPropagator()


# =============================================================================
# Initialization
# =============================================================================


def init_tracing(config: TracingConfig | None = None) -> TracingConfig:
    """
    Initialize OpenTelemetry tracing with the given configuration.

    Sets up the TracerProvider with OTLP or console exporter and configures
    context propagation.
    """
    global _tracer_config, _tracer_instance

    _tracer_config = config or TracingConfig()

    resource = Resource.create({
        SERVICE_NAME: _tracer_config.service_name,
        SERVICE_VERSION: _tracer_config.service_version,
        "deployment.environment": os.getenv("ENVIRONMENT", "development"),
        "heretek.swarm.node_id": os.getenv("NODE_ID", str(uuid.uuid4())),
    })

    sampler: Sampler = TraceIdRatioBased(_tracer_config.sample_rate)

    provider = TracerProvider(resource=resource, sampler=sampler)

    exporter_type = _tracer_config.exporter.lower()
    if exporter_type == "otlp":
        endpoint = _tracer_config.endpoint or os.getenv(
            "OTEL_EXPORTER_OTLP_ENDPOINT", "http://otel-collector:4317"
        )
        try:
            otlp_exporter = OTLPSpanExporter(
                endpoint=endpoint,
                insecure=os.getenv("OTEL_EXPORTER_OTLP_INSECURE", "true").lower() == "true",
            )
            provider.add_span_processor(BatchSpanProcessor(otlp_exporter))
            logger.info("OTLP tracing exporter configured", endpoint=endpoint)
        except Exception as e:
            logger.warning("Failed to configure OTLP exporter", error=str(e))
            provider.add_span_processor(BatchSpanProcessor(ConsoleSpanExporter()))
    else:
        provider.add_span_processor(BatchSpanProcessor(ConsoleSpanExporter()))
        logger.info("Console tracing exporter configured")

    trace.set_tracer_provider(provider)
    set_global_textmap(_propagator)

    _tracer_instance = trace.get_tracer(
        _tracer_config.service_name,
        _tracer_config.service_version,
    )

    logger.info(
        "tracing_initialized",
        service_name=_tracer_config.service_name,
        exporter=_tracer_config.exporter,
        sample_rate=_tracer_config.sample_rate,
    )

    return _tracer_config


def get_tracer(service_name: str | None = None) -> trace.Tracer:
    """
    Get the global tracer instance, initializing if necessary.

    Args:
        service_name: Override the service name for this tracer.

    Returns:
        The active tracer instance.
    """
    global _tracer_config, _tracer_instance

    if _tracer_instance is None:
        config = _tracer_config or TracingConfig()
        if service_name:
            config.service_name = service_name
        init_tracing(config)

    return _tracer_instance


def create_tracing_config(
    service_name: str = "heretek-swarm",
    exporter: str = "console",
    endpoint: str | None = None,
    sample_rate: float = 1.0,
) -> TracingConfig:
    """Convenience function to create TracingConfig."""
    return TracingConfig(
        service_name=service_name,
        exporter=exporter,
        endpoint=endpoint,
        sample_rate=sample_rate,
    )


# =============================================================================
# Span Helpers
# =============================================================================


def _span_kind_from_str(kind: str) -> SpanKind:
    """Convert string kind to SpanKind enum."""
    mapping = {
        "internal": SpanKind.INTERNAL,
        "client": SpanKind.CLIENT,
        "server": SpanKind.SERVER,
        "producer": SpanKind.PRODUCER,
        "consumer": SpanKind.CONSUMER,
    }
    return mapping.get(kind.lower(), SpanKind.INTERNAL)


def create_span(
    name: str,
    trace_id: str | None = None,
    parent_id: str | None = None,
    kind: str = "internal",
) -> Span:
    """
    Create a new span without starting it.

    Args:
        name: Name of the span.
        trace_id: Optional trace ID to use.
        parent_id: Optional parent span ID.
        kind: Span kind (internal, client, server, producer, consumer).

    Returns:
        A newly created span (not yet started).
    """
    tracer = get_tracer()
    span_kind = _span_kind_from_str(kind)

    ctx = trace.get_current_context()

    tracer_impl = get_tracer()
    span = tracer_impl.start_span(
        name=name,
        context=ctx,
        kind=span_kind,
    )

    return span


def with_span(name: str) -> Callable:
    """
    Decorator to wrap a function in a span.

    Handles both sync and async functions.

    Usage:
        @with_span("my_operation")
        async def my_operation():
            ...
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            tracer = get_tracer()
            with tracer.start_as_current_span(name) as span:
                try:
                    result = await func(*args, **kwargs)
                    span.set_status(Status(StatusCode.OK))
                    return result
                except Exception as e:
                    span.set_status(Status(StatusCode.ERROR, str(e)))
                    span.record_exception(e)
                    raise

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            tracer = get_tracer()
            with tracer.start_as_current_span(name) as span:
                try:
                    result = func(*args, **kwargs)
                    span.set_status(Status(StatusCode.OK))
                    return result
                except Exception as e:
                    span.set_status(Status(StatusCode.ERROR, str(e)))
                    span.record_exception(e)
                    raise

        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper

    return decorator


@contextmanager
def span_context(
    name: str,
    attributes: dict[str, Any] | None = None,
    kind: str = "internal",
):
    """
    Context manager for creating spans.

    Args:
        name: Span name.
        attributes: Optional span attributes.
        kind: Span kind.

    Example:
        with span_context("consensus.vote", {"consensus_id": round_id}):
            await vote_on_proposal(proposal)
    """
    tracer = get_tracer()
    span_kind = _span_kind_from_str(kind)

    with tracer.start_as_current_span(
        name,
        kind=span_kind,
        attributes=attributes or {},
    ) as span:
        try:
            yield span
            span.set_status(Status(StatusCode.OK))
        except Exception as e:
            span.set_status(Status(StatusCode.ERROR, str(e)))
            span.record_exception(e)
            raise


def get_current_span() -> Span | None:
    """Get the current active span."""
    return trace.get_current_span()


def get_trace_context() -> dict[str, str]:
    """Extract current trace context for propagation across process boundaries."""
    carrier: dict[str, str] = {}
    _propagator.inject(carrier)
    return carrier


def set_span_attribute(key: str, value: Any) -> None:
    """Set an attribute on the current span."""
    span = get_current_span()
    if span and span.is_recording():
        span.set_attribute(key, value)


def set_span_attributes(attributes: dict[str, Any]) -> None:
    """Set multiple attributes on the current span."""
    span = get_current_span()
    if span and span.is_recording():
        for key, value in attributes.items():
            span.set_attribute(key, value)


# =============================================================================
# Predefined Span Names
# =============================================================================


class SpanNames:
    """Standardized span names for Heretek Swarm operations."""

    API_REQUEST = "api.request"
    API_HEALTH_CHECK = "api.health_check"

    AGENT_INITIALIZE = "agent.initialize"
    AGENT_EXECUTE = "agent.execute"
    AGENT_PROCESS_MESSAGE = "agent.process_message"
    AGENT_TOOL_CALL = "agent.tool_call"
    AGENT_LLM_INFERENCE = "agent.llm_inference"

    CONSENSUS_ROUND_START = "consensus.round_start"
    CONSENSUS_VOTE = "consensus.vote"
    CONSENSUS_AGREEMENT = "consensus.agreement"
    CONSENSUS_ROUND_COMPLETE = "consensus.round_complete"

    CONSCIOUSNESS_CALCULATE_PHI = "consciousness.calculate_phi"
    CONSCIOUSNESS_UPDATE = "consciousness.update"
    CONSCIOUSNESS_MEASURE = "consciousness.measure"

    COLLECTIVE_BROADCAST = "collective.broadcast"
    COLLECTIVE_GATHER = "collective.gather"
    COLLECTIVE_SYNC = "collective.sync"

    WORKFLOW_EXECUTE = "workflow.execute"
    WORKFLOW_STEP = "workflow.step"

    MEMORY_STORE = "memory.store"
    MEMORY_RETRIEVE = "memory.retrieve"
    MEMORY_SEARCH = "memory.search"


class SpanAttributes:
    """Standardized attribute keys for Heretek Swarm spans."""

    AGENT_ID = "heretek.agent.id"
    AGENT_TYPE = "heretek.agent.type"
    TASK_ID = "heretek.task.id"
    TASK_TYPE = "heretek.task.type"
    CONSENSUS_ID = "heretek.consensus.id"
    CONSENSUS_ROUND = "heretek.consensus.round"
    WORKFLOW_ID = "heretek.workflow.id"
    WORKFLOW_STEP = "heretek.workflow.step"

    PHI_SCORE = "heretek.consciousness.phi_score"
    CONSCIOUSNESS_LEVEL = "heretek.consciousness.level"
    INTEGRATION_SCORE = "heretek.consciousness.integration_score"
    INFORMATION_SCORE = "heretek.consciousness.information_score"

    VOTES_TOTAL = "heretek.consensus.votes.total"
    VOTES_FOR = "heretek.consensus.votes.for"
    VOTES_AGAINST = "heretek.consensus.votes.against"
    QUORUM_REACHED = "heretek.consensus.quorum_reached"

    DURATION_MS = "heretek.duration_ms"
    TOKENS_USED = "heretek.tokens.used"
    TOKENS_COST = "heretek.tokens.cost"

    HTTP_METHOD = "http.method"
    HTTP_URL = "http.url"
    HTTP_STATUS_CODE = "http.status_code"


__all__ = [
    "Span",
    "SpanKind",
    "SpanNames",
    "SpanAttributes",
    "SpanStatus",
    "TraceState",
    "TracingConfig",
    "create_span",
    "create_tracing_config",
    "get_current_span",
    "get_trace_context",
    "get_tracer",
    "init_tracing",
    "set_span_attribute",
    "set_span_attributes",
    "span_context",
    "with_span",
]
