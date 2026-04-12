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
    "LoggingConfig",
    "MessagePriority",
    "MetricsCollector",
    "MetricsConfig",
    # NATS Event Mesh
    "NATSClient",
    "NATSPublisher",
    "NATSSubscriber",
    # OpenTelemetry
    "TracingConfig",
    "create_consensus_message",
    "create_delegation_message",
    "create_span",
    "create_task_request",
    "create_task_response",
    "get_log_config",
    "get_meter",
    "get_nats_client",
    "get_tracer",
    "init_logging",
    "init_metrics",
    "init_tracing",
    "record_metric",
    "with_span",
]
