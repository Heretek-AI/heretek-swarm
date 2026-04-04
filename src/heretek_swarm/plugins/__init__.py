"""
Heretek Swarm Plugins Package

This package provides plugin implementations for the Heretek Swarm system:
- Consciousness Plugin (GWT/AST) - Global Workspace Theory and Attention Schema
- Liberation Plugin - Transparent security auditing
"""

from heretek_swarm.plugins.consciousness import (
    AttentionSchema,
    AttentionSchemaManager,
    ConsciousnessMetrics,
    ConsciousnessPlugin,
    ConsciousnessState,
    GlobalWorkspace,
    GlobalWorkspaceItem,
)
from heretek_swarm.plugins.liberation import (
    AnomalyResult,
    LiberationPlugin,
    LiberationShield,
    SecurityEvent,
    SecurityEventType,
    Severity,
    ThreatAnalysis,
)

__all__ = [
    # Consciousness Plugin
    "ConsciousnessPlugin",
    "ConsciousnessState",
    "ConsciousnessMetrics",
    "GlobalWorkspace",
    "GlobalWorkspaceItem",
    "AttentionSchema",
    "AttentionSchemaManager",
    # Liberation Plugin
    "LiberationPlugin",
    "LiberationShield",
    "SecurityEventType",
    "SecurityEvent",
    "Severity",
    "ThreatAnalysis",
    "AnomalyResult",
]
