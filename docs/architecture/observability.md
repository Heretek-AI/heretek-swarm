# Observability Documentation

## Overview

The Observability System provides comprehensive monitoring, metrics collection, and distributed tracing for the Heretek Swarm framework. It enables real-time system health monitoring, performance analysis, and debugging through OpenTelemetry-based instrumentation.

## Core Architecture

### Observability Components

The observability system consists of three main components:

1. **Metrics Collection**: Prometheus-compatible metrics for system monitoring
2. **Distributed Tracing**: OpenTelemetry-based tracing for request flows
3. **Structured Logging**: Structured logging with correlation IDs

```
┌─────────────────────────────────────────────────┐
│         Observability System                   │
│                                               │
│  ┌──────────────┐  ┌──────────────┐        │
│  │   Metrics     │  │   Tracing    │        │
│  │              │  │              │        │
│  │ - Counters   │  │ - Spans      │        │
│  │ - Gauges     │  │ - Traces     │        │
│  │ - Histograms │  │ - Context    │        │
│  └──────────────┘  └──────────────┘        │
│                                               │
│  ┌──────────────────────────────────────────┐   │
│  │        Structured Logging             │   │
│  │  - Correlation IDs                  │   │
│  │  - Structured JSON                  │   │
│  │  - Contextual information            │   │
│  └──────────────────────────────────────────┘   │
│                                               │
│  ┌──────────────────────────────────────────┐   │
│  │        Exporters                     │   │
│  │  - Prometheus                      │   │
│  │  - OTLP/GRPC                      │   │
│  │  - Console                        │   │
│  └──────────────────────────────────────────┘   │
└─────────────────────────────────────────────────┘
```

## Metrics Collection

### SwarmMetrics

**Location**: [`src/observability/metrics.py`](../src/observability/metrics.py)

The [`SwarmMetrics`](../src/observability/metrics.py:84) class provides Prometheus-compatible metrics for monitoring system health.

### Metric Types

#### Counters

Monotonically increasing values for counting events:

```python
# Agent message counter
agent_message_counter = meter.create_counter(
    "agent_messages_total",
    description="Total messages processed by agents"
)

agent_message_counter.add(
    1,
    {
        "agent_id": "alpha",
        "message_type": "task"
    }
)
```

#### Gauges

Point-in-time values for monitoring current state:

```python
# Agent gauge
agent_gauge = meter.create_gauge(
    "active_agents",
    description="Number of active agents"
)

agent_gauge.set(5, {"state": "active"})
```

#### Histograms

Distributions of values for performance analysis:

```python
# Execution time histogram
execution_histogram = meter.create_histogram(
    "agent_execution_duration_seconds",
    description="Agent execution duration"
)

execution_histogram.record(
    0.5,
    {"agent_id": "alpha", "operation": "process"}
)
```

### Standard Metrics

#### Agent Metrics

```python
# Messages processed
agent_messages_total: Counter

# Errors encountered
agent_errors_total: Counter

# Active agents
active_agents: Gauge

# Execution duration
agent_execution_duration_seconds: Histogram
```

#### Workflow Metrics

```python
# Workflows executed
workflows_total: Counter

# Workflow duration
workflow_duration_seconds: Histogram

# Active workflows
active_workflows: Gauge

# Phase durations
workflow_phase_duration_seconds: Histogram
```

#### Consensus Metrics

```python
# Consensus rounds
consensus_rounds_total: Counter

# Consensus duration
consensus_duration_seconds: Histogram

# Votes cast
consensus_votes_total: Counter

# Red flags raised
consensus_red_flags_total: Counter
```

#### Memory Metrics

```python
# Memory operations
memory_operations_total: Counter

# Memory size
memory_size_bytes: Gauge

# Query duration
memory_query_duration_seconds: Histogram
```

### Configuration

```python
from src.observability.metrics import MetricsConfig, init_metrics

# Configure metrics
config = MetricsConfig(
    service_name="heretek-swarm",
    prometheus_port=9090,
    enable_prometheus=True
)

# Initialize metrics
meter = init_metrics(config)

# Get metrics instance
metrics = SwarmMetrics()
```

### Prometheus Integration

Metrics are exposed on port 9090 by default:

```bash
# Access metrics endpoint
curl http://localhost:9090/metrics

# Example output
# HELP agent_messages_total Total messages processed by agents
# TYPE agent_messages_total counter
agent_messages_total{agent_id="alpha",message_type="task"} 1234
agent_messages_total{agent_id="beta",message_type="task"} 5678
```

## Distributed Tracing

### TracingConfig

**Location**: [`src/observability/tracing.py`](../src/observability/tracing.py)

Configuration for OpenTelemetry tracing.

```python
@dataclass
class TracingConfig:
    """Configuration for OpenTelemetry tracing."""
    service_name: str = "heretek-swarm"
    service_version: str = "0.1.0"
    environment: str = "development"
    otlp_endpoint: str | None = None  # e.g., "http://localhost:4317"
    console_export: bool = True
    sample_rate: float = 1.0  # 100% sampling for dev
```

### Initialization

```python
from src.observability.tracing import init_tracing, TracingConfig

# Configure tracing
config = TracingConfig(
    service_name="heretek-swarm",
    service_version="0.1.0",
    environment="production",
    otlp_endpoint="http://localhost:4317",
    console_export=False,
    sample_rate=0.1  # 10% sampling for production
)

# Initialize tracing
tracer = init_tracing(config)
```

### Creating Spans

```python
from src.observability.tracing import get_tracer

# Get tracer
tracer = get_tracer()

# Create a span
with tracer.start_as_current_span("agent.process_message") as span:
    span.set_attribute("agent.id", "alpha")
    span.set_attribute("message.type", "task")
    
    # Do work
    result = await process_message()
    
    span.set_attribute("result.success", result.success)
```

### Span Attributes

Standard attributes for spans:

```python
# Agent attributes
span.set_attribute("agent.id", "alpha")
span.set_attribute("agent.name", "Alpha Agent")
span.set_attribute("agent.state", "active")

# Message attributes
span.set_attribute("message.id", "msg-123")
span.set_attribute("message.type", "task")
span.set_attribute("message.sender", "beta")

# Workflow attributes
span.set_attribute("workflow.id", "wf-456")
span.set_attribute("workflow.phase", "analysis")
span.set_attribute("workflow.topic", "deployment")
```

### Span Events

```python
# Add events to span
span.add_event(
    "message_received",
    {
        "message_id": "msg-123",
        "timestamp": "2024-01-01T00:00:00Z"
    }
)

span.add_event(
    "processing_started",
    {"timestamp": "2024-01-01T00:00:01Z"}
)

span.add_event(
    "processing_completed",
    {
        "timestamp": "2024-01-01T00:00:05Z",
        "duration_ms": 4000
    }
)
```

### Span Links

Link related spans:

```python
# Link to parent span
parent_span = tracer.start_span("parent")
child_span = tracer.start_span(
    "child",
    links=[trace.Link(parent_span.context)]
)
```

### Decorators

Use decorators for automatic tracing:

```python
from src.observability.tracing import traced

@traced
async def process_message(message):
    """Automatically traced function"""
    # Function logic here
    return result

@traced(name="custom.operation")
async def custom_operation(arg1, arg2):
    """Custom span name"""
    # Function logic here
    return result
```

### Context Managers

Use context managers for manual tracing:

```python
from src.observability.tracing import trace_operation

async with trace_operation("agent.execute", agent_id="alpha"):
    # Traced operation
    result = await execute()

# Span automatically closed with duration
```

## Structured Logging

### Configuration

```python
import structlog

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer(),
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

# Get logger
logger = structlog.get_logger("AgentActor")
```

### Logging with Context

```python
# Log with context
logger.info(
    "Agent spawned",
    extra={
        "agent_id": "alpha",
        "name": "Alpha Agent",
        "topics": ["analysis", "decisions"]
    }
)

# Log with correlation ID
logger.info(
    "Processing message",
    extra={
        "correlation_id": "corr-123",
        "message_id": "msg-456",
        "agent_id": "alpha"
    }
)
```

### Log Levels

```python
logger.debug("Detailed debug information")
logger.info("General information")
logger.warning("Warning condition")
logger.error("Error condition", exc_info=True)
logger.critical("Critical condition")
```

## Usage Examples

### Basic Metrics

```python
from src.observability.metrics import SwarmMetrics

# Get metrics instance
metrics = SwarmMetrics()

# Record agent activity
metrics.agent_messages.add(
    1,
    {"agent_id": "alpha", "message_type": "task"}
)

# Record execution time
metrics.agent_execution_duration.record(
    0.5,
    {"agent_id": "alpha", "operation": "process"}
)

# Update active agents
metrics.active_agents.set(5)
```

### Basic Tracing

```python
from src.observability.tracing import get_tracer

tracer = get_tracer()

# Trace workflow execution
with tracer.start_as_current_span("workflow.execute") as span:
    span.set_attribute("workflow.id", "wf-123")
    span.set_attribute("workflow.topic", "deployment")
    
    # Research phase
    with tracer.start_as_current_span("workflow.research") as research_span:
        research_span.set_attribute("phase", "research")
        await execute_research()
    
    # Analysis phase
    with tracer.start_as_current_span("workflow.analysis") as analysis_span:
        analysis_span.set_attribute("phase", "analysis")
        await execute_analysis()
```

### Integration with Actors

```python
from src.observability.tracing import traced, get_tracer
from src.observability.metrics import SwarmMetrics

class MyAgent(AgentActor):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.tracer = get_tracer()
        self.metrics = SwarmMetrics()
    
    @traced
    async def process_message(self, message):
        """Process message with automatic tracing"""
        # Record metrics
        self.metrics.agent_messages.add(
            1,
            {"agent_id": self.agent_id, "message_type": message.message_type}
        )
        
        # Process message
        result = await self.handle_message(message)
        
        # Record result
        self.metrics.agent_errors.add(
            1 if not result.success else 0,
            {"agent_id": self.agent_id}
        )
        
        return result
```

### Integration with Workflows

```python
from src.observability.tracing import trace_operation

class HeavySwarmWorkflow:
    async def execute(self, topic, context):
        """Execute workflow with tracing"""
        workflow_id = str(uuid4())
        
        with trace_operation("workflow.execute", workflow_id=workflow_id) as ctx:
            ctx.span.set_attribute("workflow.topic", topic)
            
            # Research phase
            with trace_operation("workflow.research") as research_ctx:
                research_result = await self._execute_research_phase(topic, context)
                research_ctx.span.set_attribute("phase.duration_ms", research_result.duration_ms)
            
            # Analysis phase
            with trace_operation("workflow.analysis") as analysis_ctx:
                analysis_result = await self._execute_analysis_phase(research_result.output, topic)
                analysis_ctx.span.set_attribute("phase.duration_ms", analysis_result.duration_ms)
            
            # ... continue with other phases
```

## Best Practices

### 1. Metrics

- Use descriptive metric names
- Include relevant labels/attributes
- Use appropriate metric types
- Monitor metric cardinality
- Set up alerts on key metrics

### 2. Tracing

- Use meaningful span names
- Add relevant attributes
- Include correlation IDs
- Keep spans focused
- Use sampling in production

### 3. Logging

- Use structured logging
- Include correlation IDs
- Add contextual information
- Use appropriate log levels
- Avoid sensitive data

### 4. Performance

- Monitor metric overhead
- Use sampling for tracing
- Optimize logging
- Batch metric exports
- Cache frequently accessed data

### 5. Integration

- Correlate metrics, traces, and logs
- Use consistent IDs across systems
- Include business context
- Monitor end-to-end flows
- Set up dashboards

## Performance Considerations

### Metrics Overhead

- Counter increment: <1μs
- Gauge update: <1μs
- Histogram record: 1-10μs
- Export interval: 15-60s

### Tracing Overhead

- Span creation: 1-5μs
- Attribute setting: <1μs
- Event recording: 1-3μs
- Sampling reduces overhead significantly

### Logging Overhead

- JSON rendering: 10-100μs
- Context binding: <1μs
- Log emission: 1-10μs
- Structured logging adds ~10-20% overhead

## Troubleshooting

### Common Issues

1. **Metrics Not Appearing**
   - Check Prometheus endpoint
   - Verify metrics are being recorded
   - Check exporter configuration
   - Review service discovery

2. **Traces Not Collected**
   - Verify OTLP endpoint
   - Check sampling configuration
   - Review span attributes
   - Check network connectivity

3. **High Overhead**
   - Reduce sampling rate
   - Optimize logging
   - Batch metric exports
   - Review span attributes

4. **Missing Correlation**
   - Ensure correlation IDs are propagated
   - Check context propagation
   - Verify span links
   - Review distributed context

## API Reference

### SwarmMetrics

See [`src/observability/metrics.py`](../src/observability/metrics.py) for complete API documentation.

### Tracing Functions

See [`src/observability/tracing.py`](../src/observability/tracing.py) for complete API documentation.

## See Also

- [Actors System](./actors-system.md)
- [Orchestration System](./orchestration-system.md)
- [State Management](./state-management.md)
- [Tools System](./tools-system.md)
