"""
OpenTelemetry instrumentation for Heretek Swarm.

Agent Gamma - QA and Validation Lead
Provides distributed tracing for agent-to-agent communication and task execution.
"""

import time
from collections.abc import Callable
from contextlib import contextmanager
from dataclasses import dataclass
from functools import wraps
from typing import Any, TypeVar

from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
from opentelemetry.trace import Status, StatusCode

# Type variable for decorated functions
F = TypeVar("F", bound=Callable[..., Any])


# ============== CONFIGURATION ==============

@dataclass
class TracingConfig:
    """Configuration for OpenTelemetry tracing."""
    service_name: str = "heretek-swarm"
    service_version: str = "0.1.0"
    environment: str = "development"
    otlp_endpoint: str | None = None  # e.g., "http://localhost:4317"
    console_export: bool = True
    sample_rate: float = 1.0  # 100% sampling for dev


# ============== TRACER INITIALIZATION ==============

_tracer: trace.Tracer | None = None
_config: TracingConfig | None = None


def init_tracing(config: TracingConfig | None = None) -> trace.Tracer:
    """
    Initialize OpenTelemetry tracing.
    
    Args:
        config: Tracing configuration. Uses defaults if not provided.
    
    Returns:
        Configured tracer instance.
    """
    global _tracer, _config
    
    if _tracer is not None:
        return _tracer
    
    config = config or TracingConfig()
    _config = config
    
    # Create resource with service metadata
    resource = Resource.create({
        "service.name": config.service_name,
        "service.version": config.service_version,
        "deployment.environment": config.environment,
    })
    
    # Create tracer provider
    provider = TracerProvider(resource=resource)
    
    # Add exporters
    if config.otlp_endpoint:
        otlp_exporter = OTLPSpanExporter(endpoint=config.otlp_endpoint)
        provider.add_span_processor(BatchSpanProcessor(otlp_exporter))
    
    if config.console_export:
        console_exporter = ConsoleSpanExporter()
        provider.add_span_processor(BatchSpanProcessor(console_exporter))
    
    # Set global tracer provider
    trace.set_tracer_provider(provider)
    
    _tracer = trace.get_tracer(
        config.service_name,
        config.service_version,
    )
    
    return _tracer


def get_tracer() -> trace.Tracer:
    """Get the configured tracer, initializing if needed."""
    global _tracer
    if _tracer is None:
        _tracer = init_tracing()
    return _tracer


# ============== SPAN ATTRIBUTES ==============

class SpanAttributes:
    """Standard span attribute names for consistency."""
    
    # Agent attributes
    AGENT_ID = "agent.id"
    AGENT_TYPE = "agent.type"
    AGENT_CAPABILITIES = "agent.capabilities"
    AGENT_REPUTATION = "agent.reputation"
    
    # Message attributes
    MESSAGE_ID = "message.id"
    MESSAGE_TYPE = "message.type"
    MESSAGE_SENDER = "message.sender_id"
    MESSAGE_RECEIVER = "message.receiver_id"
    MESSAGE_CORRELATION_ID = "message.correlation_id"
    MESSAGE_LATENCY_MS = "message.latency_ms"
    
    # Task attributes
    TASK_ID = "task.id"
    TASK_TYPE = "task.type"
    TASK_STATUS = "task.status"
    TASK_COMPLEXITY = "task.complexity"
    
    # Consensus attributes
    CONSENSUS_ID = "consensus.id"
    CONSENSUS_ROUND = "consensus.round"
    CONSENSUS_VOTE = "consensus.vote"
    CONSENSUS_OUTCOME = "consensus.outcome"
    
    # State attributes
    STATE_CHECKPOINT_ID = "state.checkpoint_id"
    STATE_OPERATION = "state.operation"
    STATE_ROLLBACK = "state.rollback"
    
    # Performance attributes
    LATENCY_BASELINE_MS = "latency.baseline_ms"
    LATENCY_EXCEEDED = "latency.exceeded"


# ============== TRACING DECORATORS ==============

def traced(
    name: str | None = None,
    kind: trace.SpanKind = trace.SpanKind.INTERNAL,
    attributes: dict[str, Any] | None = None,
) -> Callable[[F], F]:
    """
    Decorator to trace a function as a span.
    
    Args:
        name: Span name. Defaults to function name.
        kind: Span kind (INTERNAL, CLIENT, SERVER, PRODUCER, CONSUMER).
        attributes: Static attributes to add to span.
    
    Returns:
        Decorated function.
    """
    def decorator(func: F) -> F:
        span_name = name or func.__name__
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            tracer = get_tracer()
            with tracer.start_as_current_span(
                span_name,
                kind=kind,
                attributes=attributes,
            ) as span:
                try:
                    result = func(*args, **kwargs)
                    span.set_status(Status(StatusCode.OK))
                    return result
                except Exception as e:
                    span.set_status(Status(StatusCode.ERROR, str(e)))
                    span.record_exception(e)
                    raise
        
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            tracer = get_tracer()
            with tracer.start_as_current_span(
                span_name,
                kind=kind,
                attributes=attributes,
            ) as span:
                try:
                    result = await func(*args, **kwargs)
                    span.set_status(Status(StatusCode.OK))
                    return result
                except Exception as e:
                    span.set_status(Status(StatusCode.ERROR, str(e)))
                    span.record_exception(e)
                    raise
        
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper  # type: ignore
        return sync_wrapper  # type: ignore
    
    return decorator


def traced_agent_method(
    operation: str,
) -> Callable[[F], F]:
    """
    Decorator for agent methods with standard agent attributes.
    
    Args:
        operation: Name of the operation (e.g., "send_message", "execute_task").
    
    Returns:
        Decorated method.
    """
    def decorator(func: F) -> F:
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            tracer = get_tracer()
            agent_id = getattr(self, "agent_id", "unknown")
            agent_type = getattr(self, "agent_type", "unknown")
            
            with tracer.start_as_current_span(
                f"agent.{agent_type}.{operation}",
                kind=trace.SpanKind.INTERNAL,
                attributes={
                    SpanAttributes.AGENT_ID: agent_id,
                    SpanAttributes.AGENT_TYPE: agent_type,
                    "operation": operation,
                },
            ) as span:
                try:
                    result = func(self, *args, **kwargs)
                    span.set_status(Status(StatusCode.OK))
                    return result
                except Exception as e:
                    span.set_status(Status(StatusCode.ERROR, str(e)))
                    span.record_exception(e)
                    raise
        
        @wraps(func)
        async def async_wrapper(self, *args, **kwargs):
            tracer = get_tracer()
            agent_id = getattr(self, "agent_id", "unknown")
            agent_type = getattr(self, "agent_type", "unknown")
            
            with tracer.start_as_current_span(
                f"agent.{agent_type}.{operation}",
                kind=trace.SpanKind.INTERNAL,
                attributes={
                    SpanAttributes.AGENT_ID: agent_id,
                    SpanAttributes.AGENT_TYPE: agent_type,
                    "operation": operation,
                },
            ) as span:
                try:
                    result = await func(self, *args, **kwargs)
                    span.set_status(Status(StatusCode.OK))
                    return result
                except Exception as e:
                    span.set_status(Status(StatusCode.ERROR, str(e)))
                    span.record_exception(e)
                    raise
        
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper  # type: ignore
        return wrapper  # type: ignore
    
    return decorator


# ============== LATENCY TRACKING ==============

LATENCY_BASELINE_MS = 100  # <100ms requirement


@contextmanager
def track_latency(
    operation: str,
    baseline_ms: float = LATENCY_BASELINE_MS,
    attributes: dict[str, Any] | None = None,
):
    """
    Context manager to track latency and flag if baseline exceeded.
    
    Args:
        operation: Name of the operation being tracked.
        baseline_ms: Latency baseline in milliseconds.
        attributes: Additional span attributes.
    
    Yields:
        Span for adding additional attributes.
    """
    tracer = get_tracer()
    attrs = attributes or {}
    attrs[SpanAttributes.LATENCY_BASELINE_MS] = baseline_ms
    
    start_time = time.perf_counter()
    
    with tracer.start_as_current_span(
        f"latency.{operation}",
        attributes=attrs,
    ) as span:
        try:
            yield span
            
            elapsed_ms = (time.perf_counter() - start_time) * 1000
            span.set_attribute(SpanAttributes.MESSAGE_LATENCY_MS, elapsed_ms)
            
            if elapsed_ms > baseline_ms:
                span.set_attribute(SpanAttributes.LATENCY_EXCEEDED, True)
                span.add_event(
                    "latency_baseline_exceeded",
                    attributes={
                        "actual_ms": elapsed_ms,
                        "baseline_ms": baseline_ms,
                        "overage_ms": elapsed_ms - baseline_ms,
                    },
                )
                # Flag for refactoring
                span.set_status(
                    Status(StatusCode.ERROR, f"Latency {elapsed_ms:.2f}ms exceeds baseline {baseline_ms}ms")
                )
            else:
                span.set_attribute(SpanAttributes.LATENCY_EXCEEDED, False)
                span.set_status(Status(StatusCode.OK))
                
        except Exception as e:
            elapsed_ms = (time.perf_counter() - start_time) * 1000
            span.set_attribute(SpanAttributes.MESSAGE_LATENCY_MS, elapsed_ms)
            span.set_status(Status(StatusCode.ERROR, str(e)))
            span.record_exception(e)
            raise


def trace_message_flow(
    sender_id: str,
    receiver_id: str,
    message_type: str,
    correlation_id: str | None = None,
) -> trace.Span:
    """
    Create a span for A2A message flow tracing.
    
    Args:
        sender_id: ID of the sending agent.
        receiver_id: ID of the receiving agent.
        message_type: Type of message being sent.
        correlation_id: Optional correlation ID for tracking related messages.
    
    Returns:
        Span for the message flow.
    """
    tracer = get_tracer()
    
    attributes = {
        SpanAttributes.MESSAGE_SENDER: sender_id,
        SpanAttributes.MESSAGE_RECEIVER: receiver_id,
        SpanAttributes.MESSAGE_TYPE: message_type,
    }
    
    if correlation_id:
        attributes[SpanAttributes.MESSAGE_CORRELATION_ID] = correlation_id
    
    return tracer.start_as_current_span(
        f"message.{message_type}",
        kind=trace.SpanKind.PRODUCER,
        attributes=attributes,
    )


# ============== CONSENSUS TRACING ==============

def trace_consensus_round(
    consensus_id: str,
    round_number: int,
    participants: list[str],
) -> trace.Span:
    """
    Create a span for consensus round tracing.
    
    Args:
        consensus_id: ID of the consensus session.
        round_number: Current round number.
        participants: List of participating agent IDs.
    
    Returns:
        Span for the consensus round.
    """
    tracer = get_tracer()
    
    return tracer.start_as_current_span(
        f"consensus.round_{round_number}",
        kind=trace.SpanKind.INTERNAL,
        attributes={
            SpanAttributes.CONSENSUS_ID: consensus_id,
            SpanAttributes.CONSENSUS_ROUND: round_number,
            "consensus.participants": ",".join(participants),
        },
    )


def record_vote(
    agent_id: str,
    vote: str,
    reasoning: str | None = None,
) -> None:
    """
    Record a consensus vote in the current span.
    
    Args:
        agent_id: ID of the voting agent.
        vote: The vote value (approve, reject, abstain).
        reasoning: Optional reasoning for the vote.
    """
    current_span = trace.get_current_span()
    
    current_span.add_event(
        "consensus_vote",
        attributes={
            SpanAttributes.AGENT_ID: agent_id,
            SpanAttributes.CONSENSUS_VOTE: vote,
            "vote.reasoning": reasoning or "",
        },
    )
