"""
OpenTelemetry Tracing for Heretek Swarm.

Provides distributed tracing based on OpenTelemetry standards.
"""

from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from functools import wraps
from typing import Any, Callable
from uuid import uuid4

import structlog

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


@dataclass
class TracingConfig:
    """Configuration for distributed tracing."""
    service_name: str = "heretek-swarm"
    exporter: str = "console"  # console, otlp, jaeger, zipkin
    endpoint: str | None = None
    sample_rate: float = 1.0  # 0.0-1.0
    propagate_b3: bool = True
    max_attributes: int = 64
    max_span_events: int = 128


@dataclass
class Span:
    """
    Represents a trace span.
    
    Spans are the building blocks of distributed traces,
    capturing timing, attributes, and relationships.
    """
    name: str = ""  # No default, must be provided
    trace_id: str = field(default_factory=lambda: uuid4().hex[:32])
    span_id: str = field(default_factory=lambda: uuid4().hex[:16])
    parent_id: str | None = None
    service_name: str = "heretek-swarm"
    state: TraceState = TraceState.UNSTARTED
    status: SpanStatus = SpanStatus.UNSET
    start_time: datetime | None = None
    end_time: datetime | None = None
    attributes: dict[str, Any] = field(default_factory=dict)
    events: list[dict[str, Any]] = field(default_factory=list)
    kind: str = "internal"  # internal, client, server, producer, consumer
    
    @property
    def duration_ms(self) -> float:
        """Calculate span duration in milliseconds."""
        if self.start_time and self.end_time:
            return (self.end_time - self.start_time).total_seconds() * 1000
        return 0.0
    
    def add_attribute(self, key: str, value: Any) -> None:
        """Add an attribute to the span."""
        if len(self.attributes) < 64:  # max_attributes
            self.attributes[key] = value
    
    def add_event(self, name: str, attributes: dict[str, Any] | None = None) -> None:
        """Add an event to the span."""
        if len(self.events) < 128:  # max_span_events
            self.events.append({
                "name": name,
                "timestamp": datetime.utcnow().isoformat(),
                "attributes": attributes or {},
            })
    
    def set_status(self, status: SpanStatus, description: str | None = None) -> None:
        """Set span status."""
        self.status = status
        if description:
            self.add_attribute("status.description", description)
    
    def record_exception(self, exception: Exception) -> None:
        """Record an exception in the span."""
        self.add_event("exception", {
            "exception.type": type(exception).__name__,
            "exception.message": str(exception),
        })
        self.set_status(SpanStatus.ERROR, str(exception))
    
    def to_dict(self) -> dict[str, Any]:
        """Convert span to dictionary."""
        return {
            "trace_id": self.trace_id,
            "span_id": self.span_id,
            "parent_id": self.parent_id,
            "name": self.name,
            "service_name": self.service_name,
            "kind": self.kind,
            "status": self.status.value,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "duration_ms": self.duration_ms,
            "attributes": self.attributes,
            "events": self.events,
        }


# =============================================================================
# Global State
# =============================================================================

_tracer_config: TracingConfig | None = None
_active_spans: dict[str, Span] = {}
_span_counter = 0


def init_tracing(config: TracingConfig | None = None) -> TracingConfig:
    """Initialize tracing with configuration."""
    global _tracer_config
    _tracer_config = config or TracingConfig()
    
    logger.info(
        "tracing_initialized",
        service_name=_tracer_config.service_name,
        exporter=_tracer_config.exporter,
        sample_rate=_tracer_config.sample_rate,
    )
    
    return _tracer_config


def get_tracer(service_name: str | None = None) -> "Tracer":
    """Get a tracer instance."""
    global _tracer_config
    config = _tracer_config or TracingConfig()
    
    if service_name:
        config.service_name = service_name
    
    return Tracer(config)


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


class Tracer:
    """
    OpenTelemetry-compatible tracer.
    
    Provides span creation and management for distributed tracing.
    """
    
    def __init__(self, config: TracingConfig):
        self.config = config
        self._spans: list[Span] = []
    
    @contextmanager
    def start_as_current_span(
        self,
        name: str,
        parent: Span | None = None,
        kind: str = "internal",
        attributes: dict[str, Any] | None = None,
    ):
        """
        Start a span as the current span.
        
        Usage:
            with tracer.start_as_current_span("operation") as span:
                span.add_attribute("user_id", "123")
                # do work
        """
        global _span_counter
        _span_counter += 1
        
        trace_id = parent.trace_id if parent else uuid4().hex[:32]
        span = Span(
            name=name,
            trace_id=trace_id,
            parent_id=parent.span_id if parent else None,
            service_name=self.config.service_name,
            kind=kind,
        )
        
        if attributes:
            for key, value in attributes.items():
                span.add_attribute(key, value)
        
        span.start_time = datetime.utcnow()
        span.state = TraceState.ACTIVE
        
        # Store in active spans
        _active_spans[span.span_id] = span
        self._spans.append(span)
        
        logger.debug("span_started", name=name, span_id=span.span_id)
        
        try:
            yield span
            span.set_status(SpanStatus.OK)
        except Exception as e:
            span.record_exception(e)
            raise
        finally:
            span.end_time = datetime.utcnow()
            span.state = TraceState.ENDED
            
            # Export span
            self._export_span(span)
            
            # Remove from active
            _active_spans.pop(span.span_id, None)
    
    def _export_span(self, span: Span) -> None:
        """Export a completed span."""
        if self.config.exporter == "console":
            logger.info(
                "span_completed",
                **span.to_dict(),
            )
        # Additional exporters would go here
    
    def create_span(
        self,
        name: str,
        parent_trace_id: str | None = None,
        parent_id: str | None = None,
        kind: str = "internal",
    ) -> Span:
        """Create a new span without starting it."""
        return Span(
            name=name,
            trace_id=parent_trace_id or uuid4().hex[:32],
            parent_id=parent_id,
            service_name=self.config.service_name,
            kind=kind,
        )
    
    def get_active_span(self) -> Span | None:
        """Get the currently active span."""
        if _active_spans:
            return list(_active_spans.values())[-1]
        return None


def create_span(
    name: str,
    trace_id: str | None = None,
    parent_id: str | None = None,
) -> Span:
    """Create a span in the global tracer."""
    global _tracer_config
    config = _tracer_config or TracingConfig()
    
    tracer = get_tracer(config.service_name)
    return tracer.create_span(name, trace_id, parent_id)


def with_span(name: str) -> Callable:
    """
    Decorator to wrap a function in a span.
    
    Usage:
        @with_span("my_operation")
        async def my_operation():
            ...
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            tracer = get_tracer()
            with tracer.start_as_current_span(name) as span:
                span.add_attribute("function", func.__name__)
                return await func(*args, **kwargs)
        return wrapper
    return decorator


__all__ = [
    "Span",
    "SpanStatus",
    "TraceState",
    "TracingConfig",
    "Tracer",
    "create_span",
    "create_tracing_config",
    "get_tracer",
    "init_tracing",
    "with_span",
]
