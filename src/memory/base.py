"""
Base data models for the Dual-Tier Memory System.

Provides Pydantic models for type-safe memory operations with
complete validation and serialization support.
"""

from datetime import UTC, datetime
from enum import StrEnum
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, field_validator


class MemoryTier(StrEnum):
    """Memory tier classification"""
    EPHEMERAL = "ephemeral"  # Redis - short-term, TTL-based
    PERSISTENT = "persistent"  # PostgreSQL/PGVector - long-term


class MemoryType(StrEnum):
    """Types of memory entries"""
    EPISODIC = "episodic"  # Event-based memories
    SEMANTIC = "semantic"  # Facts and knowledge
    PROCEDURAL = "procedural"  # Skills and procedures
    WORKING = "working"  # Current task context


class EmbeddingVector(BaseModel):
    """Vector embedding with metadata"""
    vector: list[float] = Field(..., min_length=1, description="Embedding vector")
    dimensions: int = Field(..., gt=0, description="Vector dimensions")
    model: str = Field(..., description="Embedding model used")
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    @field_validator("vector")
    @classmethod
    def validate_vector_length(cls, v: list[float]) -> list[float]:
        if len(v) == 0:
            raise ValueError("Vector cannot be empty")
        return v


class MemoryEntry(BaseModel):
    """A single memory entry in the system"""

    id: UUID = Field(default_factory=uuid4, description="Unique identifier")
    agent_id: str = Field(..., min_length=1, description="Owner agent ID")
    session_id: UUID | None = Field(None, description="Session context")

    # Content
    content: str = Field(..., min_length=1, description="Memory content")
    content_type: str = Field(default="text/plain", description="MIME type")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional metadata")

    # Classification
    memory_type: MemoryType = Field(default=MemoryType.EPISODIC)
    tier: MemoryTier = Field(default=MemoryTier.PERSISTENT)
    tags: list[str] = Field(default_factory=list, description="Searchable tags")

    # Embedding (lazy-loaded)
    embedding: EmbeddingVector | None = Field(None, description="Vector embedding")

    # Lineage tracking
    parent_id: UUID | None = Field(None, description="Parent memory entry")
    source_agent: str | None = Field(None, description="Source agent if derived")

    # Timestamps
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    expires_at: datetime | None = Field(None, description="TTL for ephemeral memory")
    accessed_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    access_count: int = Field(default=0, ge=0)

    # Importance scoring
    importance_score: float = Field(default=0.5, ge=0.0, le=1.0)
    relevance_score: float | None = Field(None, ge=0.0, le=1.0)

    class Config:
        json_encoders = {
            datetime: datetime.isoformat,
            UUID: str,
        }

    def touch(self) -> "MemoryEntry":
        """Update access timestamp and increment counter"""
        self.accessed_at = datetime.now(UTC)
        self.access_count += 1
        return self

    def is_expired(self) -> bool:
        """Check if memory entry has expired"""
        if self.expires_at is None:
            return False
        return datetime.now(UTC) > self.expires_at


class MemoryQuery(BaseModel):
    """Query parameters for memory search"""

    query_text: str | None = Field(None, description="Text search query")
    query_vector: list[float] | None = Field(None, description="Vector similarity query")

    # Filters
    agent_ids: list[str] | None = Field(None, description="Filter by agent IDs")
    session_id: UUID | None = Field(None, description="Filter by session")
    memory_types: list[MemoryType] | None = Field(None, description="Filter by type")
    tags: list[str] | None = Field(None, description="Filter by tags")

    # Time range
    start_time: datetime | None = Field(None, description="Start of time range")
    end_time: datetime | None = Field(None, description="End of time range")

    # Search parameters
    limit: int = Field(default=10, gt=0, le=1000, description="Max results")
    offset: int = Field(default=0, ge=0, description="Pagination offset")
    min_score: float = Field(default=0.0, ge=0.0, le=1.0, description="Minimum relevance score")

    # Tier selection
    tiers: list[MemoryTier] = Field(
        default=[MemoryTier.EPHEMERAL, MemoryTier.PERSISTENT],
        description="Memory tiers to search"
    )

    # Ranking
    include_metadata: bool = Field(default=True)
    include_embeddings: bool = Field(default=False)
    sort_by: str = Field(default="relevance", description="Sort field: relevance, created_at, importance")

    @field_validator("query_vector")
    @classmethod
    def validate_query_vector(cls, v: list[float] | None) -> list[float] | None:
        if v is not None and len(v) == 0:
            raise ValueError("Query vector cannot be empty")
        return v


class MemoryResult(BaseModel):
    """Result from memory query"""

    entries: list[MemoryEntry] = Field(default_factory=list, description="Matching entries")
    total_count: int = Field(default=0, ge=0, description="Total matching count")
    query_time_ms: float = Field(..., ge=0, description="Query execution time in ms")
    tier: MemoryTier = Field(..., description="Source tier")

    # Similarity scores (for vector search)
    scores: list[float] | None = Field(None, description="Similarity scores per entry")

    # Pagination
    has_more: bool = Field(default=False)
    next_offset: int | None = Field(None)

    class Config:
        json_encoders = {
            datetime: datetime.isoformat,
            UUID: str,
        }


class MemoryStats(BaseModel):
    """Statistics for memory system"""

    # Entry counts
    total_entries: int = Field(default=0, ge=0)
    entries_by_type: dict[MemoryType, int] = Field(default_factory=dict)
    entries_by_agent: dict[str, int] = Field(default_factory=dict)

    # Tier stats
    ephemeral_entries: int = Field(default=0, ge=0)
    persistent_entries: int = Field(default=0, ge=0)

    # Performance metrics
    avg_query_time_ms: float = Field(default=0.0, ge=0)
    p50_query_time_ms: float = Field(default=0.0, ge=0)
    p95_query_time_ms: float = Field(default=0.0, ge=0)
    p99_query_time_ms: float = Field(default=0.0, ge=0)

    # Storage
    total_size_bytes: int = Field(default=0, ge=0)
    index_size_bytes: int = Field(default=0, ge=0)

    # Health
    redis_connected: bool = Field(default=False)
    postgres_connected: bool = Field(default=False)
    embedding_service_healthy: bool = Field(default=False)

    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
