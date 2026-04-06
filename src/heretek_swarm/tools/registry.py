"""
Re-export tools.registry for heretek_swarm.tools.registry compatibility.
"""

from tools.registry import (
    ToolRegistry,
    ToolRegistryConfig,
    ToolRegistryEntry,
    get_registry,
    initialize_registry,
)

__all__ = [
    "ToolRegistry",
    "ToolRegistryConfig",
    "ToolRegistryEntry",
    "get_registry",
    "initialize_registry",
]
