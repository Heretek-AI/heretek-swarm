"""
Dual-Tier Memory System for Heretek Swarm

Provides a two-layer memory architecture:
- Ephemeral (Redis): Fast, short-term working memory with TTL
- Persistent (PostgreSQL/PGVector): Long-term storage with semantic search
- mem0 Backend: Production-ready long-term memory with semantic search

Target: p95 latency <50ms for retrieval operations

mem0 provides:
- +26% accuracy over OpenAI Memory
- 91% faster responses
- 90% lower token usage
"""

from .base import EmbeddingVector, MemoryEntry, MemoryQuery, MemoryResult, MemoryTier, MemoryType
from .embeddings import EmbeddingConfig, EmbeddingService
from .ephemeral import EphemeralConfig, EphemeralMemoryStore
from .persistent import PersistentMemoryStore
from .unified import DualTierConfig, DualTierMemorySystem

# mem0 backend integration
try:
    from .mem0_backend import Mem0Backend, Mem0Config
    MEM0_AVAILABLE = True
except ImportError:
    MEM0_AVAILABLE = False
    Mem0Backend = None
    Mem0Config = None

__all__ = [
    "MEM0_AVAILABLE",
    "DualTierMemorySystem",
    "EmbeddingService",
    "EmbeddingVector",
    "EphemeralMemoryStore",
    "Mem0Backend",
    "Mem0Config",
    "MemoryEntry",
    "MemoryQuery",
    "MemoryResult",
    "PersistentMemoryStore",
]

__version__ = "0.1.0"
