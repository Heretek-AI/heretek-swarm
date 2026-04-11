"""
Re-export tools.examples for heretek_swarm.tools.examples compatibility.
"""

from tools.examples import (
    ConsensusVoteTool,
    HealthCheckTool,
    LegacyWrapperTool,
    MemorySearchTool,
)

__all__ = [
    "ConsensusVoteTool",
    "HealthCheckTool",
    "LegacyWrapperTool",
    "MemorySearchTool",
]
