"""
Re-export tools.examples for heretek_swarm.tools.examples compatibility.
"""

from tools.examples import (
    MemorySearchTool,
    HealthCheckTool,
    ConsensusVoteTool,
    LegacyWrapperTool,
)

__all__ = [
    "MemorySearchTool",
    "HealthCheckTool",
    "ConsensusVoteTool",
    "LegacyWrapperTool",
]
