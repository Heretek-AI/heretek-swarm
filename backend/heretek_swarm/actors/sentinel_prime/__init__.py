"""
Sentinel-Prime Module - Security Commander & Threat Response.

This module has been refactored from a single sentinel_prime.py file into
a package with separate components:

- types.py: Type definitions (ThreatLevel, ThreatType, IncidentStatus, 
            ResponseAction, ThreatIndicator, SecurityIncident, ThreatReport)
- helpers.py: SentinelPrimeHelpers mixin with 16 utility methods
- handlers.py: SentinelPrimeHandlers mixin with 17 message handlers
- agent.py: SentinelPrimeAgent class

For backward compatibility, all public exports are available from this module.

SAFE-02: External threat detection integration included.
"""

from __future__ import annotations

# Re-export types from types.py
from heretek_swarm.actors.sentinel_prime.types import (
    IncidentStatus,
    ResponseAction,
    SecurityIncident,
    ThreatIndicator,
    ThreatLevel,
    ThreatReport,
    ThreatType,
)

# Re-export agent from agent.py
from heretek_swarm.actors.sentinel_prime.agent import SentinelPrimeAgent

# Re-export mixins
from heretek_swarm.actors.sentinel_prime.helpers import SentinelPrimeHelpers
from heretek_swarm.actors.sentinel_prime.handlers import SentinelPrimeHandlers

__all__ = [
    # Enums
    "ThreatLevel",
    "ThreatType",
    "IncidentStatus",
    "ResponseAction",
    # Dataclasses
    "ThreatIndicator",
    "SecurityIncident",
    "ThreatReport",
    # Agent
    "SentinelPrimeAgent",
    # Mixins
    "SentinelPrimeHelpers",
    "SentinelPrimeHandlers",
]
