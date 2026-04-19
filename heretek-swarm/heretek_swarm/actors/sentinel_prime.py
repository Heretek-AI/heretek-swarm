"""
Sentinel-Prime Agent - Security Commander & Threat Response.

Backward-compatibility shim for sentinel_prime.py.
All imports are re-exported from the sentinel_prime/ module directory.

SAFE-02: External threat detection integration preserved.
"""

# Re-export everything from the module directory for backward compatibility
from heretek_swarm.actors.sentinel_prime import (
    # Enums
    IncidentStatus,
    ResponseAction,
    ThreatLevel,
    ThreatType,
    # Dataclasses
    ThreatIndicator,
    SecurityIncident,
    ThreatReport,
    # Agent
    SentinelPrimeAgent,
    # Mixins
    SentinelPrimeHelpers,
    SentinelPrimeHandlers,
)

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
