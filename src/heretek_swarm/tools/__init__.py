"""
Heretek Swarm Tools Package

Re-exports tools from src/tools for heretek_swarm namespace compatibility.
This module provides backward compatibility for imports referencing heretek_swarm.tools.
"""

from tools.base import (
    BaseTool,
    SimpleTool,
    ToolContext,
    ToolExecutionError,
    ToolExecutionResult,
    ToolMetadata,
    ToolStatus,
)
from tools.examples import (
    ConsensusVoteTool,
    HealthCheckTool,
    MemorySearchTool,
)
from tools.registry import (
    ToolRegistry,
    ToolRegistryConfig,
    ToolRegistryEntry,
    get_registry,
    initialize_registry,
)

__all__ = [
    # Base classes
    "BaseTool",
    "SimpleTool",
    "ToolContext",
    "ToolExecutionError",
    "ToolExecutionResult",
    "ToolMetadata",
    "ToolStatus",
    # Registry
    "ToolRegistry",
    "ToolRegistryConfig",
    "ToolRegistryEntry",
    "get_registry",
    "initialize_registry",
    # Example tools
    "MemorySearchTool",
    "HealthCheckTool",
    "ConsensusVoteTool",
]

__version__ = "0.1.0"
