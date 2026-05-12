"""
Plugins Module - Extensible plugin system for Heretek Swarm

This module provides a plugin architecture inspired by elizaOS.
Plugins can extend swarm functionality without modifying core code.

Components:
- Plugin base class
- Plugin runtime for lifecycle management
- Plugin discovery and loading
- Plugin execution and message handling
"""

from .manager import (
    Plugin,
    PluginMetadata,
    PluginRuntime,
    PluginState,
    get_plugin_runtime,
    load_plugin_from_file,
)
from .consciousness import ConsciousnessPlugin
from .liberation import LiberationPlugin

__all__ = [
    "Plugin",
    "PluginMetadata",
    "PluginRuntime",
    "PluginState",
    "get_plugin_runtime",
    "load_plugin_from_file",
    "ConsciousnessPlugin",
    "LiberationPlugin",
]
