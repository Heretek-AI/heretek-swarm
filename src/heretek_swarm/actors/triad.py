"""
Backward-Compatible Wrapper for Triad Agents.

This module re-exports all classes from the extracted triad module:
- TriadAgent: Base class for all Triad agents
- StewardAgent: Coordinator and governance agent
- AlphaAgent: Primary decision maker and analyst
- BetaAgent: Secondary analyst and validator
- CharlieAgent: Tertiary perspective and challenger

All existing imports will continue to work after the extraction.
"""

# Re-export all classes from the extracted module
from heretek_swarm.actors.triad import (
    AlphaAgent,
    BetaAgent,
    CharlieAgent,
    StewardAgent,
    TriadAgent,
)

__all__ = [
    "TriadAgent",
    "StewardAgent",
    "AlphaAgent",
    "BetaAgent",
    "CharlieAgent",
]
