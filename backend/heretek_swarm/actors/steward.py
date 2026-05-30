"""Steward Agent — thin re-export stub.
All implementation lives in the triad subpackage."""

from heretek_swarm.actors.triad import (  # noqa: F401
    AlphaAgent,
    BetaAgent,
    CharlieAgent,
    StewardAgent,
    TriadAgent,
)

# Preserved module-level constant for backward compatibility
_SYSTEM_RECOVERY_TOPIC = "system.recovery"
