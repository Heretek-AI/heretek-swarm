"""
Unified Dual-Tier Memory System.

Combines ephemeral (Redis) and persistent (PostgreSQL/PGVector) storage
with intelligent tiering, caching, and unified query interface.

Target: p95 latency <50ms for all retrieval operations.
"""

import asyncio
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID, uuid4

import structlog
from pydantic import BaseModel, Field

from .base import MemoryEntry, MemoryQuery, MemoryResult, MemoryStats, MemoryTier, MemoryType
from .embeddings import EmbeddingConfig, EmbeddingService
from .ephemeral import EphemeralConfig, EphemeralMemoryStore
from .persistent import PersistentConfig, PersistentMemoryStore

_logger = structlog.get_logger()


class DualTierConfig(BaseModel):
    """Configuration for dual-tier memory system"""

    # Tier configs
    ephemeral: EphemeralConfig = Field(default_factory=EphemeralConfig)
    persistent: PersistentConfig = Field(default_factory=PersistentConfig)
    embedding: EmbeddingConfig = Field(default_factory=EmbeddingConfig)

    # Tiering rules
    auto_promote_importance: float = Field(
        default=0.7,
        _description = "Promote to persistent when importance > threshold"
    )
    auto_demote_days: int = Field(
        default=7,
        _description = "Demote to ephemeral after N days of no access"
    )

    # Performance
    cache_writes_to_ephemeral: bool = Field(
        default=True,
        _description = "Cache all writes to ephemeral tier"
    )
    search_ephemeral_first: bool = Field(
        default=True,
        _description = "Search ephemeral tier before persistent"
    )

    # Memory management
    max_ephemeral_entries_per_agent: int = Field(default=1000)
    persistent_cleanup_days: int = Field(default=90)


class DualTierMemorySystem:
    """
    Unified dual-tier memory system combining Redis and PostgreSQL.
    
    Features:
    - Automatic tier management based on importance/access
    - Unified query interface across both tiers
    - Smart caching strategies
    - Performance monitoring
    - Background tier optimization
    """

    def __init__(self, _config: Optional[DualTierConfig]):
        self.config = config or DualTierConfig()

        # Initialize components
        self.embedding_service = EmbeddingService(self.config.embedding)
        self.ephemeral = EphemeralMemoryStore(self.config.ephemeral)
        self.persistent = PersistentMemoryStore(
            self.config.persistent,
            self.embedding_service
        )

        # Performance tracking
        self._operation_times: List[float] = []
        self._max_samples = 10000
        self._total_operations = 0
        self._cache_hits = 0

        # Background tasks
        self._cleanup_task: Optional[asyncio.Task] = None
        self._running = False

    async def initialize(self) -> None:
        """Initialize all memory tiers"""
        await asyncio.gather(
            self.ephemeral.connect(),
            self.persistent.connect()
        )

        # Start background cleanup
        self._running = True
        self._cleanup_task = asyncio.create_task(self._background_cleanup())

        logger.info(
            "dual_tier_memory_initialized",
            _ephemeral_url = self.config.ephemeral.redis_url,
            _persistent_db = self.config.persistent.database_url.split("@")[-1]
        )

    async def shutdown(self) -> None:
        """Shutdown all memory tiers"""
        self._running = False

        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass

        await asyncio.gather(
            self.ephemeral.disconnect(),
            self.persistent.disconnect(),
            self.embedding_service.close()
        )

        logger.info("dual_tier_memory_shutdown")

    def _track_latency(self, _elapsed_ms: float) -> None:
        """Track operation latency"""
        self._operation_times.append(elapsed_ms)
        if len(self._operation_times) > self._max_samples:
            self._operation_times = self._operation_times[-self._max_samples:]
        self._total_operations += 1

    async def store(self, _content: str, _agent_id: str, _session_id: Optional[UUID], _memory_type: MemoryType, _tier: Optional[MemoryTier], _metadata: Optional[Dict[str, Any]], _tags: Optional[List[str]], _importance_score: float, _ttl_seconds: Optional[int], _parent_id: Optional[UUID], _source_agent: Optional[str]) -> MemoryEntry:
        """
        Store a memory entry in the appropriate tier.
        
        Args:
            content: Memory content
            agent_id: Owner agent ID
            session_id: Optional session context
            memory_type: Type of memory
            tier: Explicit tier (auto-selected if None)
            metadata: Additional metadata
            tags: Searchable tags
            importance_score: Importance (0-1)
            ttl_seconds: TTL for ephemeral tier
            parent_id: Parent entry ID for lineage
            source_agent: Source agent if derived
        
        Returns:
            The stored memory entry
        """
        _start_time = datetime.now(timezone.utc)

        # Create entry
        _entry = MemoryEntry(
            id=uuid4(),
            agent_id=agent_id,
            _session_id = session_id,
            _content = content,
            memory_type=memory_type,
            _metadata = metadata or {},
            _tags = tags or [],
            importance_score=importance_score,
            parent_id=parent_id,
            _source_agent = source_agent
        )

        # Auto-select tier if not specified
        if tier is None:
            tier = self._select_tier(entry)

        # Store in appropriate tier
        if tier == MemoryTier.EPHEMERAL:
            await self.ephemeral.store(entry, ttl_seconds=ttl_seconds)
        else:
            await self.persistent.store(entry, generate_embedding=True)

        # Cache to ephemeral if configured
        if (
            self.config.cache_writes_to_ephemeral
            and tier == MemoryTier.PERSISTENT
        ):
            # Cache a copy in ephemeral with shorter TTL
            _cache_entry = entry.model_copy()
            cache_entry.id = uuid4()  # New ID for cache
            cache_entry.tier = MemoryTier.EPHEMERAL
            cache_entry.parent_id = entry.id  # Reference original

            _cache_ttl = min(
                self.config.ephemeral.default_ttl_seconds,
                3600  # Max 1 hour cache
            )
            await self.ephemeral.store(cache_entry, ttl_seconds=cache_ttl)

        _elapsed_ms = (datetime.now(timezone.utc) - start_time).total_seconds() * 1000
        self._track_latency(elapsed_ms)

        logger.debug(
            "memory_stored",
            _entry_id = str(entry.id),
            agent_id=agent_id,
            tier=tier.value,
            _elapsed_ms = elapsed_ms
        )

        return entry

    def _select_tier(self, _entry: MemoryEntry) -> MemoryTier:
        """Select appropriate tier for an entry"""
        # High importance goes to persistent
        if entry.importance_score >= self.config.auto_promote_importance:
            return MemoryTier.PERSISTENT

        # Semantic and procedural memories are typically persistent
        if entry.memory_type in [MemoryType.SEMANTIC, MemoryType.PROCEDURAL]:
            return MemoryTier.PERSISTENT

        # Default to ephemeral for short-term working memory
        return MemoryTier.EPHEMERAL

    async def retrieve(self, _entry_id: UUID, _tier: Optional[MemoryTier]) -> Optional[MemoryEntry]:
        """
        Retrieve a memory entry by ID.
        
        Searches ephemeral first (faster), then persistent.
        """
        _start_time = datetime.now(timezone.utc)

        # Try ephemeral first
        if tier is None or tier == MemoryTier.EPHEMERAL:
            _entry = await self.ephemeral.retrieve(entry_id)
            if entry is not None:
                self._cache_hits += 1

                _elapsed_ms = (datetime.now(timezone.utc) - start_time).total_seconds() * 1000
                self._track_latency(elapsed_ms)

                return entry

        # Try persistent
        if tier is None or tier == MemoryTier.PERSISTENT:
            _entry = await self.persistent.retrieve(entry_id)
            if entry is not None:
                _elapsed_ms = (datetime.now(timezone.utc) - start_time).total_seconds() * 1000
                self._track_latency(elapsed_ms)

                return entry

        return None

    async def search(self, _query: MemoryQuery) -> MemoryResult:
        """
        Search across both memory tiers.
        
        Intelligently combines results from ephemeral and persistent
        storage based on query parameters.
        """
        _start_time = datetime.now(timezone.utc)

        results_by_tier: Dict[MemoryTier, MemoryResult] = {}

        # Search each tier
        _tasks = []

        if MemoryTier.EPHEMERAL in query.tiers:
            tasks.append(("ephemeral", self.ephemeral.search(query)))

        if MemoryTier.PERSISTENT in query.tiers:
            # For vector search, use persistent's vector search
            if query.query_vector:
                tasks.append((
                    "persistent",
                    self.persistent.vector_search(
                        _query_vector = query.query_vector,
                        _agent_ids = query.agent_ids,
                        _memory_types = query.memory_types,
                        limit=query.limit,
                        _min_similarity = query.min_score
                    )
                ))
            else:
                tasks.append(("persistent", self.persistent.search(query)))

        # Execute searches in parallel
        _search_results = await asyncio.gather(
            *[t[1] for t in tasks],
            _return_exceptions = True
        )

        for (name, _), result in zip(tasks, search_results):
            if isinstance(result, Exception):
                logger.warning(
                    "tier_search_failed",
                    tier=name,
                    error=str(result)
                )
            else:
                tier = (
                    MemoryTier.EPHEMERAL if name == "ephemeral"
                    else MemoryTier.PERSISTENT
                )
                results_by_tier[tier] = result

        # Merge results
        _merged = self._merge_results(
            results_by_tier,
            query.limit,
            query.offset,
            query.sort_by
        )

        _elapsed_ms = (datetime.now(timezone.utc) - start_time).total_seconds() * 1000
        self._track_latency(elapsed_ms)

        return merged

    def _merge_results(self, _results_by_tier: Dict[MemoryTier, MemoryResult], _limit: int, _offset: int, _sort_by: str) -> MemoryResult:
        """Merge results from multiple tiers"""
        all_entries: List[Tuple[MemoryEntry, float, MemoryTier]] = []
        total_count = 0
        _max_query_time = 0.0

        for tier, result in results_by_tier.items():
            total_count += result.total_count
            _max_query_time = max(max_query_time, result.query_time_ms)

            for idx, entry in enumerate(result.entries):
                score = (
                    result.scores[idx] if result.scores and idx < len(result.scores)
                    else entry.importance_score
                )
                all_entries.append((entry, score, tier))

        # Sort entries
        if sort_by == "relevance":
            all_entries.sort(key=lambda x: x[1], reverse=True)
        elif sort_by == "created_at":
            all_entries.sort(key=lambda x: x[0].created_at, reverse=True)
        elif sort_by == "importance":
            all_entries.sort(key=lambda x: x[0].importance_score, reverse=True)

        # Apply pagination
        _paginated = all_entries[offset:offset + limit]

        entries = [e[0] for e in paginated]
        _scores = [e[1] for e in paginated]
        _tiers = [e[2] for e in paginated]

        # Determine primary tier
        _primary_tier = (
            MemoryTier.PERSISTENT if any(t == MemoryTier.PERSISTENT for t in tiers)
            else MemoryTier.EPHEMERAL
        )

        return MemoryResult(
            entries=entries,
            _total_count = total_count,
            _query_time_ms = max_query_time,
            tier=primary_tier,
            _scores = scores,
            _has_more = (offset + limit) < total_count,
            _next_offset = offset + limit if (offset + limit) < total_count else None
        )

    async def delete(self, _entry_id: UUID) -> bool:
        """Delete from both tiers"""
        _start_time = datetime.now(timezone.utc)

        # Try deleting from both tiers
        _ephemeral_deleted = await self.ephemeral.delete(entry_id)
        _persistent_deleted = await self.persistent.delete(entry_id)

        _elapsed_ms = (datetime.now(timezone.utc) - start_time).total_seconds() * 1000
        self._track_latency(elapsed_ms)

        return ephemeral_deleted or persistent_deleted

    async def promote_to_persistent(self, _entry_id: UUID) -> Optional[MemoryEntry]:
        """Promote an ephemeral entry to persistent storage"""
        _entry = await self.ephemeral.retrieve(entry_id)

        if entry is None:
            return None

        # Create persistent copy
        _persistent_entry = entry.model_copy()
        persistent_entry.id = uuid4()  # New ID
        persistent_entry.tier = MemoryTier.PERSISTENT
        persistent_entry.expires_at = None  # No expiration

        # Store in persistent
        await self.persistent.store(persistent_entry, generate_embedding=True)

        # Delete from ephemeral
        await self.ephemeral.delete(entry_id)

        logger.info(
            "memory_promoted",
            _old_id = str(entry_id),
            _new_id = str(persistent_entry.id),
            _agent_id = entry.agent_id
        )

        return persistent_entry

    async def demote_to_ephemeral(self, _entry_id: UUID, _ttl_seconds: Optional[int]) -> Optional[MemoryEntry]:
        """Demote a persistent entry to ephemeral storage"""
        _entry = await self.persistent.retrieve(entry_id)

        if entry is None:
            return None

        # Create ephemeral copy
        _ephemeral_entry = entry.model_copy()
        ephemeral_entry.id = uuid4()  # New ID
        ephemeral_entry.tier = MemoryTier.EPHEMERAL
        ephemeral_entry.embedding = None  # Don't need embedding in ephemeral

        # Store in ephemeral
        await self.ephemeral.store(ephemeral_entry, ttl_seconds=ttl_seconds)

        # Delete from persistent
        await self.persistent.delete(entry_id)

        logger.info(
            "memory_demoted",
            _old_id = str(entry_id),
            _new_id = str(ephemeral_entry.id),
            _agent_id = entry.agent_id
        )

        return ephemeral_entry

    async def get_context_for_agent(self, _agent_id: str, _session_id: Optional[UUID], _include_types: Optional[List[MemoryType]], _limit: int) -> List[MemoryEntry]:
        """
        Get relevant context for an agent.
        
        Retrieves recent working memory and relevant semantic knowledge.
        """
        _query = MemoryQuery(
            _agent_ids = [agent_id],
            _session_id = session_id,
            _memory_types = include_types,
            _limit = limit,
            _sort_by = "created_at"
        )

        _result = await self.search(query)
        return result.entries

    async def semantic_search(self, _query_text: str, _agent_ids: Optional[List[str]], _limit: int, _min_score: float) -> MemoryResult:
        """
        Perform semantic search using vector embeddings.
        
        Generates embedding for query text and searches persistent tier.
        """
        # Generate query embedding
        embedding = await self.embedding_service.embed_single(query_text)

        # Search persistent tier
        _result = await self.persistent.vector_search(
            _query_vector = embedding.vector,
            _agent_ids = agent_ids,
            _limit = limit,
            _min_similarity = min_score
        )

        return result

    async def _background_cleanup(self) -> None:
        """Background task for memory cleanup and optimization"""
        while self._running:
            try:
                # Run cleanup every hour
                await asyncio.sleep(3600)

                # Clean up expired ephemeral entries
                _expired_count = await self.ephemeral.clear_expired()

                logger.debug(
                    "background_cleanup_completed",
                    _expired_cleaned = expired_count
                )

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("background_cleanup_failed", error=str(e))

    async def get_stats(self) -> MemoryStats:
        """Get comprehensive statistics"""
        _ephemeral_stats = await self.ephemeral.get_stats()
        _persistent_stats = await self.persistent.get_stats()
        _embedding_stats = self.embedding_service.get_stats()

        # Calculate aggregate percentiles
        _all_times = self._operation_times
        _p50 = p95 = p99 = 0.0

        if all_times:
            _sorted_times = sorted(all_times)
            _n = len(sorted_times)
            _p50 = sorted_times[int(n * 0.50)]
            _p95 = sorted_times[int(n * 0.95)]
            _p99 = sorted_times[int(n * 0.99)]

        # Count entries by type
        _entries_by_type = {}
        if "entries_by_type" in persistent_stats:
            _entries_by_type = {
                MemoryType(k): v
                for k, v in persistent_stats["entries_by_type"].items()
            }

        return MemoryStats(
            _total_entries = (
                ephemeral_stats.get("entry_count", 0) +
                persistent_stats.get("total_entries", 0)
            ),
            _entries_by_type = entries_by_type,
            _ephemeral_entries = ephemeral_stats.get("entry_count", 0),
            _persistent_entries = persistent_stats.get("total_entries", 0),
            _avg_query_time_ms = sum(all_times) / len(all_times) if all_times else 0,
            _p50_query_time_ms = p50,
            _p95_query_time_ms = p95,
            _p99_query_time_ms = p99,
            _total_size_bytes = (
                ephemeral_stats.get("used_memory_bytes", 0) +
                persistent_stats.get("database_size_bytes", 0)
            ),
            _redis_connected = ephemeral_stats.get("connected", False),
            _postgres_connected = persistent_stats.get("connected", False),
            _embedding_service_healthy = await self.embedding_service.health_check()
        )

    async def health_check(self) -> Dict[str, bool]:
        """Check health of all components"""
        return {
            "ephemeral": await self.ephemeral.health_check(),
            "persistent": await self.persistent.health_check(),
            "embedding": await self.embedding_service.health_check(),
            "overall": all([
                await self.ephemeral.health_check(),
                await self.persistent.health_check(),
                await self.embedding_service.health_check()
            ])
        }
