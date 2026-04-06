"""
Heretek Swarm Memory Package

This package provides dual-tier memory architecture with:
- Ephemeral memory layer (fast, session-based with TTL)
- Persistent memory layer (long-term vector storage with mem0)
- Memory lineage tracking
- Memory Manager with importance-based decay
- Memory optimization (Session 43): Access patterns, pre-fetching, compression, tiering
"""

from heretek_swarm.memory.base import (
    DualTierMemory,
    EphemeralMemory,
    MemoryEntry,
    MemoryQuery,
    MemorySystem,
    PersistentMemory as BasePersistentMemory,
)

from heretek_swarm.memory.persistent import (
    Mem0Config,
    PersistentMemory,
    create_memory_store,
)

from heretek_swarm.memory.eliza_memory import (
    ElizaMemoryEntry,
    MemoryManager,
    MemoryManagerConfig,
    create_memory_manager,
)

# Session 43: Memory Optimization Modules
from heretek_swarm.memory.access_patterns import (
    AccessPatternAnalyzer,
    AccessPattern,
    AccessTier,
    MemoryAccessProfile,
    AccessStatistics,
    AccessPatternReport,
)

from heretek_swarm.memory.prefetcher import (
    IntelligentPrefetcher,
    PreFetchStrategy,
    PreFetchPriority,
    LRUCache,
    LFUCache,
    PreFetchRequest,
    PreFetchResult,
)

from heretek_swarm.memory.compression import (
    ColdDataCompressor,
    CompressionAlgorithm,
    CompressionLevel,
    CompressionConfig,
    CompressedMemory,
    CompressionResult,
    DecompressionResult,
)

from heretek_swarm.memory.tiering import (
    MemoryTieringSystem,
    MemoryTier,
    TierConfig,
    MigrationPolicy,
    MigrationRecord,
    TieredMemory,
    TieringStatistics,
)

# Re-export from memory package for test compatibility
# Note: Using explicit imports to avoid shadowing
import memory.base
import memory.ephemeral
import memory.persistent
import memory.unified
import memory.embeddings

MemoryResult = getattr(memory.base, 'MemoryResult', None)
MemoryTier_Base = getattr(memory.base, 'MemoryTier', None)
MemoryType = getattr(memory.base, 'MemoryType', None)
EphemeralMemoryStore = getattr(memory.ephemeral, 'EphemeralMemoryStore', None)
EphemeralConfig = getattr(memory.ephemeral, 'EphemeralConfig', None)
PersistentMemoryStore = getattr(memory.persistent, 'PersistentMemoryStore', None)
PersistentConfig = getattr(memory.persistent, 'PersistentConfig', None)
DualTierMemorySystem = getattr(memory.unified, 'DualTierMemorySystem', None)
DualTierConfig = getattr(memory.unified, 'DualTierConfig', None)
EmbeddingService = getattr(memory.embeddings, 'EmbeddingService', None)
EmbeddingConfig = getattr(memory.embeddings, 'EmbeddingConfig', None)

__all__ = [
    # Base classes
    "MemorySystem",
    "MemoryEntry",
    "MemoryQuery",
    "MemoryResult",
    "EphemeralMemory",
    "BasePersistentMemory",
    "DualTierMemory",
    # Types (base)
    "MemoryTier_Base",
    "MemoryType",
    # Mem0 integration
    "Mem0Config",
    "PersistentMemory",
    "PersistentConfig",
    "create_memory_store",
    # Memory stores (for tests)
    "EphemeralMemoryStore",
    "EphemeralConfig",
    "PersistentMemoryStore",
    "DualTierMemorySystem",
    "DualTierConfig",
    # Embeddings
    "EmbeddingService",
    "EmbeddingConfig",
    # Eliza-style memory manager
    "ElizaMemoryEntry",
    "MemoryManager",
    "MemoryManagerConfig",
    "create_memory_manager",
    # Session 43: Memory Optimization
    "AccessPatternAnalyzer",
    "AccessPattern",
    "AccessTier",
    "MemoryAccessProfile",
    "AccessStatistics",
    "AccessPatternReport",
    "IntelligentPrefetcher",
    "PreFetchStrategy",
    "PreFetchPriority",
    "LRUCache",
    "LFUCache",
    "PreFetchRequest",
    "PreFetchResult",
    "ColdDataCompressor",
    "CompressionAlgorithm",
    "CompressionLevel",
    "CompressionConfig",
    "CompressedMemory",
    "CompressionResult",
    "DecompressionResult",
    "MemoryTieringSystem",
    "MemoryTier",
    "TierConfig",
    "MigrationPolicy",
    "MigrationRecord",
    "TieredMemory",
    "TieringStatistics",
]