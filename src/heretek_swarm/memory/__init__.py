"""
Heretek Swarm Memory Package

This package provides dual-tier memory architecture with:
- Ephemeral memory layer (fast, session-based with TTL)
- Persistent memory layer (long-term vector storage with mem0)
- Memory lineage tracking
- Memory Manager with importance-based decay
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

# Re-export from memory package for test compatibility
# Note: Using explicit imports to avoid shadowing
import memory.base
import memory.ephemeral
import memory.persistent
import memory.unified
import memory.embeddings

MemoryResult = getattr(memory.base, 'MemoryResult', None)
MemoryTier = getattr(memory.base, 'MemoryTier', None)
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
    # Types
    "MemoryTier",
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
]