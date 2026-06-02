"""
Heretek Swarm Memory Package

This package provides the memory subsystem built on Cognee (knowledge graph +
vector memory engine) plus access-pattern optimization and intelligent pre-fetching.

Public modules:
    cognee_reader   — Read-only async client for Cognee's search API.
    cognee_writer   — Write-path async client for Cognee's add/cognify API.
    access_patterns — Access pattern analysis, tier classification, reporting.
    prefetcher      — LRU/LFU caches and pattern-based pre-fetch scheduling.
    eliza_memory    — Importance-decay memory manager (elizaOS pattern).
"""

from __future__ import annotations

import structlog

# ---------------------------------------------------------------------------
# Access-pattern analysis & tiering
# ---------------------------------------------------------------------------
from heretek_swarm.memory.access_patterns import (
    AccessPattern,
    AccessPatternAnalyzer,
    AccessPatternReport,
    AccessStatistics,
    AccessTier,
    MemoryAccessProfile,
    MemoryAccessRecord,
)

# ---------------------------------------------------------------------------
# Cognee-backed read/write clients
# ---------------------------------------------------------------------------
from heretek_swarm.memory.cognee_reader import CogneeMemoryReader
from heretek_swarm.memory.cognee_writer import CogneeMemoryWriter

# ---------------------------------------------------------------------------
# Eliza-style importance-decay memory manager
# ---------------------------------------------------------------------------
from heretek_swarm.memory.eliza_memory import (
    ElizaMemoryEntry,
    MemoryManager,
    MemoryManagerConfig,
    create_memory_manager,
)

# ---------------------------------------------------------------------------
# Intelligent pre-fetching & caching
# ---------------------------------------------------------------------------
from heretek_swarm.memory.prefetcher import (
    IntelligentPrefetcher,
    LFUCache,
    LRUCache,
    PreFetchPriority,
    PreFetchRequest,
    PreFetchResult,
    PreFetchScheduler,
    PreFetchStrategy,
)

logger = structlog.get_logger(__name__)

__all__ = [
    # Access-pattern analysis
    "AccessPattern",
    "AccessPatternAnalyzer",
    "AccessPatternReport",
    "AccessStatistics",
    "AccessTier",
    # Cognee-backed clients
    "CogneeMemoryReader",
    "CogneeMemoryWriter",
    # Eliza-style memory manager
    "ElizaMemoryEntry",
    # Pre-fetching & caching
    "IntelligentPrefetcher",
    "LFUCache",
    "LRUCache",
    "MemoryAccessProfile",
    "MemoryAccessRecord",
    "MemoryManager",
    "MemoryManagerConfig",
    "PreFetchPriority",
    "PreFetchRequest",
    "PreFetchResult",
    "PreFetchScheduler",
    "PreFetchStrategy",
    "create_memory_manager",
]
