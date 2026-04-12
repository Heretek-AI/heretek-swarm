"""
Heretek Swarm Infrastructure Module.

Provides foundational infrastructure for the swarm:
- A2A: Agent-to-Agent protocol for structured inter-agent communication
- NATS: Event mesh for pub/sub messaging
- OTel: OpenTelemetry for distributed tracing, metrics, and logging
"""

from heretek_swarm.infrastructure.a2a import (
    A2AMessage,
    A2AMessageType,
    A2AProtocol,
    AgentCapability,
    MessagePriority,
    create_consensus_message,
    create_delegation_message,
    create_task_request,
    create_task_response,
)
from heretek_swarm.infrastructure.nats import (
    NATSClient,
    NATSPublisher,
    NATSSubscriber,
    get_nats_client,
)
from heretek_swarm.infrastructure.otel import (
    LoggingConfig,
    MetricsCollector,
    MetricsConfig,
    TracingConfig,
    create_span,
    get_log_config,
    get_meter,
    get_tracer,
    init_logging,
    init_metrics,
    init_tracing,
    record_metric,
    with_span,
)

__all__ = [
    # A2A Protocol
    "A2AMessage",
    "A2AMessageType",
    "A2AProtocol",
    "AgentCapability",
    "MessagePriority",
    "create_task_request",
    "create_task_response",
    "create_delegation_message",
    "create_consensus_message",
    # NATS Event Mesh
    "NATSClient",
    "get_nats_client",
    "NATSPublisher",
    "NATSSubscriber",
    # OpenTelemetry
    "TracingConfig",
    "get_tracer",
    "init_tracing",
    "create_span",
    "with_span",
    "MetricsConfig",
    "get_meter",
    "init_metrics",
    "record_metric",
    "MetricsCollector",
    "LoggingConfig",
    "init_logging",
    "get_log_config",
]
