"""
Nexus Module - External Integration Specialist.

This module provides the NexusAgent for managing external API integrations,
webhooks, and protocol translation.

For backward compatibility, this module re-exports from the new package structure.
Import paths like `from heretek_swarm.actors.nexus import NexusAgent` continue to work.

Author: Heretek Swarm Collective
Date: 2026-04-17
Version: 1.0.0
"""

from __future__ import annotations

# Re-export types for backward compatibility
from heretek_swarm.actors.nexus.types import (
    ApiResponse,
    ConnectionStatus,
    ExternalConnection,
    ProtocolType,
    WebhookConfig,
)

# Re-export agent class for backward compatibility
from heretek_swarm.actors.nexus.agent import NexusAgent

# Re-export routing helpers
from heretek_swarm.actors.nexus.routing import NexusRoutingHelpers

__all__ = [
    # Types
    "ApiResponse",
    "ConnectionStatus",
    "ExternalConnection",
    "ProtocolType",
    "WebhookConfig",
    # Classes
    "NexusAgent",
    "NexusRoutingHelpers",
]
