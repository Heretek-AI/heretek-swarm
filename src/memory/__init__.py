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

from .base import EmbeddingVector, MemoryEntry, MemoryQuery, MemoryResult
from .embeddings import EmbeddingService
from .ephemeral import EphemeralMemoryStore
from .persistent import PersistentMemoryStore
from .unified import DualTierMemorySystem

# mem0 backend integration
try:
    from .mem0_backend import Mem0Backend, Mem0Config
    MEM0_AVAILABLE = True
except ImportError:
    MEM0_AVAILABLE = False
    _Mem0Backend = None
    _Mem0Config = None

__all__ = [
    "MemoryEntry",
    "MemoryQuery",
    "MemoryResult",
    "EmbeddingVector",
    "EphemeralMemoryStore",
    "PersistentMemoryStore",
    "DualTierMemorySystem",
    "EmbeddingService",
    "Mem0Backend",
    "Mem0Config",
    "MEM0_AVAILABLE",
]

__version__ = "0.1.0"
