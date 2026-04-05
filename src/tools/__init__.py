"""
Heretek Swarm Tools Package

Python-native tools for the Swarms framework with:
- Type-safe inputs/outputs
- Automatic validation
- Performance monitoring
- Dynamic discovery and registration
"""

from .base import (
    BaseTool,
    SimpleTool,
    ToolContext,
    ToolExecutionError,
    ToolExecutionResult,
    ToolMetadata,
    ToolStatus,
)
from .registry import (
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
]

__version__ = "0.1.0"
