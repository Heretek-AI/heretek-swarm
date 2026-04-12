"""
NATS Event Mesh Infrastructure.

Provides event-driven communication for the Heretek Swarm using NATS.

Topics:
- agents.*.messages - Agent-to-agent messaging
- agents.*.events - Agent lifecycle events
- consensus.* - Consensus deliberations
- consciousness.* - Consciousness metrics
- swarm.* - Swarm-wide events
"""

from heretek_swarm.infrastructure.nats.client import NATSClient, get_nats_client
from heretek_swarm.infrastructure.nats.publisher import NATSPublisher
from heretek_swarm.infrastructure.nats.subscriber import NATSSubscriber

__all__ = [
    "NATSClient",
    "get_nats_client",
    "NATSPublisher",
    "NATSSubscriber",
]
