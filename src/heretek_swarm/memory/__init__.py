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

__all__ = [
    # Base classes
    "MemorySystem",
    "MemoryEntry",
    "MemoryQuery",
    "EphemeralMemory",
    "BasePersistentMemory",
    "DualTierMemory",
    # Mem0 integration
    "Mem0Config",
    "PersistentMemory",
    "create_memory_store",
    # Eliza-style memory manager
    "ElizaMemoryEntry",
    "MemoryManager",
    "MemoryManagerConfig",
    "create_memory_manager",
]