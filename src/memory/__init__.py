"""
Dual-Tier Memory System for Heretek Swarm

Provides a two-layer memory architecture:
- Ephemeral (Redis): Fast, short-term working memory with TTL
- Persistent (PostgreSQL/PGVector): Long-term storage with semantic search

Target: p95 latency <50ms for retrieval operations
"""

from .base import MemoryEntry, MemoryQuery, MemoryResult, EmbeddingVector
from .ephemeral import EphemeralMemoryStore
from .persistent import PersistentMemoryStore
from .unified import DualTierMemorySystem
from .embeddings import EmbeddingService

__all__ = [
    "MemoryEntry",
    "MemoryQuery",
    "MemoryResult",
    "EmbeddingVector",
    "EphemeralMemoryStore",
    "PersistentMemoryStore",
    "DualTierMemorySystem",
    "EmbeddingService",
]

__version__ = "0.1.0"
