"""
OpenTelemetry Distributed Tracing for Heretek Swarm.

Provides distributed tracing across:
- API requests
- Agent operations
- Consensus rounds
- Consciousness calculations

Span attributes:
- agent_id: Unique agent identifier
- task_id: Current task being executed
- consensus_id: Consensus round identifier
- phi_score: Consciousness measurement value
"""

import os
from typing import Optional, Callable, Any, Dict
from contextlib import contextmanager
from functools import wraps
import time
import uuid

from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
from opentelemetry.sdk.resources import Resource, SERVICE_NAME, SERVICE_VERSION
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.trace import Status, StatusCode, Span
from opentelemetry.trace.propagation.tracecontext import TraceContextTextMapPropagator
from opentelemetry.context import Context
from opentelemetry.propagate import set_global_textmap
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
import structlog

_logger = structlog.get_logger("observability.tracing")

# Global tracer instance
_tracer: Optional[trace.Tracer] = None
_propagator = TraceContextTextMapPropagator()


def initialize_tracing(_service_name: str, _service_version: str, _otlp_endpoint: Optional[str], _enable_console_export: bool) -> trace.Tracer:
    """
    Initialize OpenTelemetry tracing with OTLP exporter.
    
    Args:
        service_name: Name of the service for tracing
        service_version: Version of the service
        otlp_endpoint: OTLP collector endpoint (defaults to OTEL_EXPORTER_OTLP_ENDPOINT env)
        enable_console_export: Enable console export for debugging
        
    Returns:
        Configured tracer instance
    """
    global _tracer
    
    # Create resource with service information
    _resource = Resource.create({
        SERVICE_NAME: service_name,
        SERVICE_VERSION: service_version,
        "deployment.environment": os.getenv("ENVIRONMENT", "development"),
        "heretek.swarm.node_id": os.getenv("NODE_ID", str(uuid.uuid4())),
    })
    
    # Create tracer provider
    _provider = TracerProvider(resource=resource)
    
    # Configure OTLP exporter if endpoint provided
    if otlp_endpoint is None:
        _otlp_endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://otel-collector:4317")
    
    # Add OTLP exporter for production
    if otlp_endpoint and not enable_console_export:
        try:
            _otlp_exporter = OTLPSpanExporter(
                _endpoint = otlp_endpoint,
                _insecure = os.getenv("OTEL_EXPORTER_OTLP_INSECURE", "true").lower() == "true",
            )
            provider.add_span_processor(BatchSpanProcessor(otlp_exporter))
            logger.info("OTLP tracing configured", endpoint=otlp_endpoint)
        except Exception as e:
            logger.warning("Failed to configure OTLP exporter", error=str(e))
    
    # Add console exporter for debugging
    if enable_console_export or os.getenv("OTEL_DEBUG", "false").lower() == "true":
        _console_exporter = ConsoleSpanExporter()
        provider.add_span_processor(BatchSpanProcessor(console_exporter))
        logger.info("Console tracing export enabled")
    
    # Set global tracer provider
    trace.set_tracer_provider(provider)
    
    # Configure trace context propagation
    set_global_textmap(_propagator)
    
    # Get tracer instance
    _tracer = trace.get_tracer(service_name, service_version)
    
    logger.info(
        "OpenTelemetry tracing initialized",
        _service = service_name,
        _version = service_version,
        _otlp_endpoint = otlp_endpoint,
    )
    
    return _tracer


def get_tracer() -> trace.Tracer:
    """Get the global tracer instance, initializing if necessary."""
    global _tracer
    if _tracer is None:
        _tracer = initialize_tracing()
    return _tracer


def create_span(_name: str, _attributes: Optional[Dict[str, _Any]], _kind: trace.SpanKind) -> Callable:
    """
    Decorator to create a span around a function.
    
    Args:
        name: Span name
        attributes: Optional span attributes
        kind: Span kind (INTERNAL, SERVER, CLIENT, PRODUCER, CONSUMER)
        
    Example:
        @create_span("agent.execute_task", {"agent_id": "agent-1"})
        async def execute_task(_task: Task):
            ...
    """
    def decorator(_func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(_*args, _**kwargs):
            _tracer = get_tracer()
            with tracer.start_as_current_span(
                name,
                _kind = kind,
                _attributes = attributes or {},
            ) as span:
                try:
                    _result = await func(*args, **kwargs)
                    span.set_status(Status(StatusCode.OK))
                    return result
                except Exception as e:
                    span.set_status(Status(StatusCode.ERROR, str(e)))
                    span.record_exception(e)
                    raise
        
        @wraps(func)
        def sync_wrapper(_*args, _**kwargs):
            _tracer = get_tracer()
            with tracer.start_as_current_span(
                name,
                _kind = kind,
                _attributes = attributes or {},
            ) as span:
                try:
                    _result = func(*args, **kwargs)
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
def span_context(_name: str, _attributes: Optional[Dict[str, _Any]], _kind: trace.SpanKind):
    """
    Context manager for creating spans.
    
    Args:
        name: Span name
        attributes: Optional span attributes
        kind: Span kind
        
    Example:
        with span_context("consensus.vote", {"consensus_id": round_id}):
            await vote_on_proposal(proposal)
    """
    _tracer = get_tracer()
    with tracer.start_as_current_span(
        name,
        _kind = kind,
        _attributes = attributes or {},
    ) as span:
        try:
            yield span
            span.set_status(Status(StatusCode.OK))
        except Exception as e:
            span.set_status(Status(StatusCode.ERROR, str(e)))
            span.record_exception(e)
            raise


def get_current_span() -> Optional[Span]:
    """Get the current active span."""
    return trace.get_current_span()


def get_trace_context() -> Dict[str, str]:
    """Extract current trace context for propagation."""
    carrier: Dict[str, str] = {}
    _propagator.inject(carrier)
    return carrier


def set_span_attribute(_key: str, _value: Any) -> None:
    """Set an attribute on the current span."""
    _span = get_current_span()
    if span and span.is_recording():
        span.set_attribute(key, value)


def set_span_attributes(_attributes: Dict[str, _Any]) -> None:
    """Set multiple attributes on the current span."""
    _span = get_current_span()
    if span and span.is_recording():
        for key, value in attributes.items():
            span.set_attribute(key, value)


# =============================================================================
# Predefined Span Names for Heretek Swarm
# =============================================================================

class SpanNames:
    """Standardized span names for Heretek Swarm operations."""
    
    # API spans
    API_REQUEST = "api.request"
    API_HEALTH_CHECK = "api.health_check"
    
    # Agent spans
    AGENT_INITIALIZE = "agent.initialize"
    AGENT_EXECUTE = "agent.execute"
    AGENT_PROCESS_MESSAGE = "agent.process_message"
    AGENT_TOOL_CALL = "agent.tool_call"
    AGENT_LLM_INFERENCE = "agent.llm_inference"
    
    # Consensus spans
    CONSENSUS_ROUND_START = "consensus.round_start"
    CONSENSUS_VOTE = "consensus.vote"
    CONSENSUS_AGREEMENT = "consensus.agreement"
    CONSENSUS_ROUND_COMPLETE = "consensus.round_complete"
    
    # Consciousness spans
    CONSCIOUSNESS_CALCULATE_PHI = "consciousness.calculate_phi"
    CONSCIOUSNESS_UPDATE = "consciousness.update"
    CONSCIOUSNESS_MEASURE = "consciousness.measure"
    
    # Collective spans
    COLLECTIVE_BROADCAST = "collective.broadcast"
    COLLECTIVE_GATHER = "collective.gather"
    COLLECTIVE_SYNC = "collective.sync"
    
    # Workflow spans
    WORKFLOW_EXECUTE = "workflow.execute"
    WORKFLOW_STEP = "workflow.step"
    
    # Memory spans
    MEMORY_STORE = "memory.store"
    MEMORY_RETRIEVE = "memory.retrieve"
    MEMORY_SEARCH = "memory.search"


# =============================================================================
# Span Attribute Keys
# =============================================================================

class SpanAttributes:
    """Standardized attribute keys for Heretek Swarm spans."""
    
    # Entity identifiers
    AGENT_ID = "heretek.agent.id"
    AGENT_TYPE = "heretek.agent.type"
    TASK_ID = "heretek.task.id"
    TASK_TYPE = "heretek.task.type"
    CONSENSUS_ID = "heretek.consensus.id"
    CONSENSUS_ROUND = "heretek.consensus.round"
    WORKFLOW_ID = "heretek.workflow.id"
    WORKFLOW_STEP = "heretek.workflow.step"
    
    # Consciousness metrics
    PHI_SCORE = "heretek.consciousness.phi_score"
    CONSCIOUSNESS_LEVEL = "heretek.consciousness.level"
    INTEGRATION_SCORE = "heretek.consciousness.integration_score"
    INFORMATION_SCORE = "heretek.consciousness.information_score"
    
    # Consensus metrics
    VOTES_TOTAL = "heretek.consensus.votes.total"
    VOTES_FOR = "heretek.consensus.votes.for"
    VOTES_AGAINST = "heretek.consensus.votes.against"
    QUORUM_REACHED = "heretek.consensus.quorum_reached"
    
    # Performance metrics
    DURATION_MS = "heretek.duration_ms"
    TOKENS_USED = "heretek.tokens.used"
    TOKENS_COST = "heretek.tokens.cost"
    
    # HTTP metrics
    HTTP_METHOD = "http.method"
    HTTP_URL = "http.url"
    HTTP_STATUS_CODE = "http.status_code"


# =============================================================================
# Starlette Middleware for HTTP Tracing
# =============================================================================

class TelemetryMiddleware(BaseHTTPMiddleware):
    """
    Starlette middleware for automatic HTTP request tracing.
    
    Features:
    - Automatic span creation for each request
    - HTTP method, URL, and status code attributes
    - Request/response timing
    - Trace context propagation
    """
    
    async def dispatch(self, _request: Request, _call_next: Callable) -> Response:
        """Process request with tracing."""
        _tracer = get_tracer()
        
        # Extract trace context from incoming headers
        _ctx = _propagator.extract(carrier=dict(request.headers))
        
        # Get client IP for attribute
        client_ip = request.client.host if request.client else "unknown"
        
        # Create span for this request
        _span_name = f"{request.method} {request.url.path}"
        
        with tracer.start_as_current_span(
            span_name,
            _context = ctx,
            _kind = trace.SpanKind.SERVER,
            _attributes = {
                SpanAttributes.HTTP_METHOD: request.method,
                SpanAttributes.HTTP_URL: str(request.url),
                "http.client_ip": client_ip,
                "http.user_agent": request.headers.get("user-agent", "unknown"),
                "http.scheme": request.url.scheme,
                "http.host": request.url.hostname or "unknown",
                "http.target": request.url.path,
            },
        ) as span:
            # Add trace ID to request state for correlation
            if span.is_recording():
                request.state.trace_id = format(span.get_span_context().trace_id, '032x')
            
            _start_time = time.perf_counter()
            
            try:
                _response = await call_next(request)
                
                # Add response attributes
                _duration_ms = (time.perf_counter() - start_time) * 1000
                
                span.set_attribute(SpanAttributes.HTTP_STATUS_CODE, response.status_code)
                span.set_attribute(SpanAttributes.DURATION_MS, duration_ms)
                
                if response.status_code >= 400:
                    span.set_status(Status(StatusCode.ERROR))
                else:
                    span.set_status(Status(StatusCode.OK))
                
                # Add trace ID to response headers
                response.headers["X-Trace-ID"] = request.state.trace_id
                
                return response
                
            except Exception as e:
                _duration_ms = (time.perf_counter() - start_time) * 1000
                span.set_attribute(SpanAttributes.DURATION_MS, duration_ms)
                span.set_status(Status(StatusCode.ERROR, str(e)))
                span.record_exception(e)
                raise


def setup_telemetry_middleware(_app):
    """
    Add telemetry middleware to FastAPI/Starlette application.
    
    Args:
        app: FastAPI or Starlette application instance
    """
    # Initialize tracing first
    initialize_tracing()
    
    # Add middleware
    app.add_middleware(TelemetryMiddleware)
    
    logger.info("Telemetry middleware configured")


# =============================================================================
# Context Propagation Helpers
# =============================================================================

async def propagate_trace_context(_coro):
    """
    Execute coroutine with trace context propagation.
    
    Ensures child spans are linked to the current trace.
    """
    _tracer = get_tracer()
    _ctx = trace.get_current_context()
    
    with tracer.start_as_current_span(
        "propagated.task",
        _context = ctx,
        _kind = trace.SpanKind.INTERNAL,
    ):
        return await coro


# =============================================================================
# Shutdown
# =============================================================================

async def shutdown_tracing():
    """Shutdown tracing provider and flush spans."""
    _provider = trace.get_tracer_provider()
    if hasattr(provider, 'shutdown'):
        await provider.shutdown()
    logger.info("Tracing shutdown complete")
