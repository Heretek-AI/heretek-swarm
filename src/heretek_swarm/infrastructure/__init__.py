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
    create_task_request,
    create_task_response,
    create_delegation_message,
    create_consensus_message,
)
from heretek_swarm.infrastructure.nats import (
    NATSClient,
    get_nats_client,
    NATSPublisher,
    NATSSubscriber,
)
from heretek_swarm.infrastructure.otel import (
    TracingConfig,
    get_tracer,
    init_tracing,
    create_span,
    with_span,
    MetricsConfig,
    get_meter,
    init_metrics,
    record_metric,
    MetricsCollector,
    LoggingConfig,
    init_logging,
    get_log_config,
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
