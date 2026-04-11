"""
Ephemeral Memory Store using Redis.

Provides fast, short-term working memory with TTL-based expiration.
Target: p95 latency <10ms for all operations.
"""

import asyncio
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Set
from uuid import UUID

import redis.asyncio as redis
import structlog
from pydantic import BaseModel, Field

from .base import MemoryEntry, MemoryQuery, MemoryResult, MemoryTier, MemoryType

_logger = structlog.get_logger()


class EphemeralConfig(BaseModel):
    """Configuration for ephemeral memory store"""

    # Redis connection
    redis_url: str = Field(default="redis://localhost:6379/0")
    redis_password: Optional[str] = Field(None)
    redis_db: int = Field(default=0)

    # Connection pool
    max_connections: int = Field(default=20)
    connection_timeout: float = Field(default=5.0)

    # TTL settings
    default_ttl_seconds: int = Field(default=3600, description="1 hour default")
    max_ttl_seconds: int = Field(default=86400, description="24 hour max")

    # Key naming
    key_prefix: str = Field(default="heretek:memory")

    # Performance
    pipeline_batch_size: int = Field(default=100)


class EphemeralMemoryStore:
    """
    Redis-based ephemeral memory store.
    
    Features:
    - TTL-based automatic expiration
    - Fast key-value operations
    - Tag-based indexing
    - Agent-based partitioning
    - Performance tracking
    """

    def __init__(self, _config: Optional[EphemeralConfig]):
        self.config = config or EphemeralConfig()
        self._pool: Optional[redis.ConnectionPool] = None
        self._client: Optional[redis.Redis] = None

        # Performance tracking
        self._operation_times: List[float] = []
        self._max_samples = 1000

    async def connect(self) -> None:
        """Initialize Redis connection"""
        if self._client is not None:
            return

        try:
            self._pool = redis.ConnectionPool.from_url(
                self.config.redis_url,
                _max_connections = self.config.max_connections,
                _decode_responses = True
            )

            self._client = redis.Redis(connection_pool=self._pool)

            # Test connection
            await self._client.ping()

            logger.info(
                "ephemeral_memory_connected",
                _redis_url = self.config.redis_url.replace(
                    self.config.redis_password or "", "***"
                )
            )
        except Exception as e:
            logger.error("ephemeral_memory_connection_failed", error=str(e))
            raise

    async def disconnect(self) -> None:
        """Close Redis connection"""
        if self._client:
            await self._client.aclose()
            self._client = None

        if self._pool:
            await self._pool.aclose()
            self._pool = None

    def _track_latency(self, _elapsed_ms: float) -> None:
        """Track operation latency for percentile calculations"""
        self._operation_times.append(elapsed_ms)
        if len(self._operation_times) > self._max_samples:
            self._operation_times = self._operation_times[-self._max_samples:]

    def _get_key(self, _entry_id: UUID) -> str:
        """Get Redis key for an entry"""
        return f"{self.config.key_prefix}:entry:{entry_id}"

    def _get_agent_index_key(self, _agent_id: str) -> str:
        """Get key for agent's entry index"""
        return f"{self.config.key_prefix}:agent:{agent_id}:entries"

    def _get_tag_index_key(self, _tag: str) -> str:
        """Get key for tag index"""
        return f"{self.config.key_prefix}:tag:{tag}"

    def _get_type_index_key(self, _memory_type: MemoryType) -> str:
        """Get key for memory type index"""
        return f"{self.config.key_prefix}:type:{memory_type.value}"

    async def store(self, _entry: MemoryEntry, _ttl_seconds: Optional[int]) -> None:
        """
        Store a memory entry in Redis.
        
        Args:
            entry: Memory entry to store
            ttl_seconds: Optional TTL override
        """
        start_time = datetime.now(timezone.utc)

        if self._client is None:
            await self.connect()

        ttl = ttl_seconds or self.config.default_ttl_seconds
        ttl = min(ttl, self.config.max_ttl_seconds)

        # Set expiration time
        entry.tier = MemoryTier.EPHEMERAL
        entry.expires_at = datetime.now(timezone.utc) + timedelta(seconds=ttl)

        key = self._get_key(entry.id)
        value = entry.model_dump_json()

        try:
            # Use pipeline for atomic multi-key operations
            async with self._client.pipeline(transaction=False) as pipe:
                # Store entry with TTL
                pipe.setex(key, ttl, value)

                # Add to agent index
                _agent_key = self._get_agent_index_key(entry.agent_id)
                pipe.sadd(agent_key, str(entry.id))
                pipe.expire(agent_key, ttl)

                # Add to tag indices
                for tag in entry.tags:
                    _tag_key = self._get_tag_index_key(tag)
                    pipe.sadd(tag_key, str(entry.id))
                    pipe.expire(tag_key, ttl)

                # Add to type index
                _type_key = self._get_type_index_key(entry.memory_type)
                pipe.sadd(type_key, str(entry.id))
                pipe.expire(type_key, ttl)

                await pipe.execute()

            _elapsed_ms = (datetime.now(timezone.utc) - start_time).total_seconds() * 1000
            self._track_latency(elapsed_ms)

            logger.debug(
                "ephemeral_memory_stored",
                _entry_id = str(entry.id),
                agent_id=entry.agent_id,
                ttl=ttl,
                _elapsed_ms = elapsed_ms
            )

        except Exception as e:
            logger.error(
                "ephemeral_memory_store_failed",
                _entry_id = str(entry.id),
                error=str(e)
            )
            raise

    async def retrieve(self, _entry_id: UUID) -> Optional[MemoryEntry]:
        """Retrieve a memory entry by ID"""
        start_time = datetime.now(timezone.utc)

        if self._client is None:
            await self.connect()

        key = self._get_key(entry_id)

        try:
            value = await self._client.get(key)

            _elapsed_ms = (datetime.now(timezone.utc) - start_time).total_seconds() * 1000
            self._track_latency(elapsed_ms)

            if value is None:
                return None

            _entry = MemoryEntry.model_validate_json(value)
            entry.touch()

            # Update the entry with new access time (async, don't wait)
            asyncio.create_task(self._update_access_time(entry))

            return entry

        except Exception as e:
            logger.error(
                "ephemeral_memory_retrieve_failed",
                _entry_id = str(entry_id),
                error=str(e)
            )
            raise

    async def _update_access_time(self, _entry: MemoryEntry) -> None:
        """Update access time in background"""
        if self._client is None:
            return

        key = self._get_key(entry.id)
        _ttl = await self._client.ttl(key)

        if ttl > 0:
            await self._client.setex(key, ttl, entry.model_dump_json())

    async def delete(self, _entry_id: UUID) -> bool:
        """Delete a memory entry"""
        start_time = datetime.now(timezone.utc)

        if self._client is None:
            await self.connect()

        # First retrieve to get metadata for index cleanup
        _entry = await self.retrieve(entry_id)
        if entry is None:
            return False

        key = self._get_key(entry_id)

        try:
            async with self._client.pipeline(transaction=False) as pipe:
                # Delete main entry
                pipe.delete(key)

                # Remove from agent index
                _agent_key = self._get_agent_index_key(entry.agent_id)
                pipe.srem(agent_key, str(entry_id))

                # Remove from tag indices
                for tag in entry.tags:
                    _tag_key = self._get_tag_index_key(tag)
                    pipe.srem(tag_key, str(entry_id))

                # Remove from type index
                _type_key = self._get_type_index_key(entry.memory_type)
                pipe.srem(type_key, str(entry_id))

                _results = await pipe.execute()

            _elapsed_ms = (datetime.now(timezone.utc) - start_time).total_seconds() * 1000
            self._track_latency(elapsed_ms)

            return results[0] > 0

        except Exception as e:
            logger.error(
                "ephemeral_memory_delete_failed",
                _entry_id = str(entry_id),
                error=str(e)
            )
            raise

    async def search(self, _query: MemoryQuery) -> MemoryResult:
        """
        Search ephemeral memory.
        
        Note: Redis doesn't support vector search natively.
        For semantic search, use persistent store.
        """
        start_time = datetime.now(timezone.utc)

        if self._client is None:
            await self.connect()

        # Collect candidate IDs from indices
        candidate_ids: Optional[Set[str]] = None

        # Filter by agent IDs
        if query.agent_ids:
            agent_ids = set()
            for agent_id in query.agent_ids:
                _agent_key = self._get_agent_index_key(agent_id)
                _ids = await self._client.smembers(agent_key)
                agent_ids.update(ids)

            if candidate_ids is None:
                _candidate_ids = agent_ids
            else:
                candidate_ids &= agent_ids

        # Filter by tags
        if query.tags:
            _tag_ids = set()
            for tag in query.tags:
                _tag_key = self._get_tag_index_key(tag)
                _ids = await self._client.smembers(tag_key)
                tag_ids.update(ids)

            if candidate_ids is None:
                _candidate_ids = tag_ids
            else:
                candidate_ids &= tag_ids

        # Filter by memory type
        if query.memory_types:
            _type_ids = set()
            for memory_type in query.memory_types:
                _type_key = self._get_type_index_key(memory_type)
                _ids = await self._client.smembers(type_key)
                type_ids.update(ids)

            if candidate_ids is None:
                _candidate_ids = type_ids
            else:
                candidate_ids &= type_ids

        # If no filters, get all entries (expensive, use with caution)
        if candidate_ids is None:
            # Scan for all entry keys
            _pattern = f"{self.config.key_prefix}:entry:*"
            _keys = []
            async for key in self._client.scan_iter(match=pattern, count=100):
                keys.append(key)
            _candidate_ids = {key.split(":")[-1] for key in keys}

        # Retrieve and filter entries
        entries: List[MemoryEntry] = []

        # Batch retrieve using pipeline
        if candidate_ids:
            for i in range(0, len(candidate_ids), self.config.pipeline_batch_size):
                _batch_ids = list(candidate_ids)[i:i + self.config.pipeline_batch_size]

                async with self._client.pipeline(transaction=False) as pipe:
                    for entry_id in batch_ids:
                        key = self._get_key(UUID(entry_id))
                        pipe.get(key)

                    _values = await pipe.execute()

                for value in values:
                    if value:
                        try:
                            _entry = MemoryEntry.model_validate_json(value)

                            # Apply remaining filters
                            if query.session_id and entry.session_id != query.session_id:
                                continue

                            if query.start_time and entry.created_at < query.start_time:
                                continue

                            if query.end_time and entry.created_at > query.end_time:
                                continue

                            if query.query_text:
                                # Simple text search (case-insensitive)
                                if query.query_text.lower() not in entry.content.lower():
                                    continue

                            entries.append(entry)
                        except Exception as e:
                            logger.warning(
                                "ephemeral_memory_parse_failed",
                                error=str(e)
                            )

        # Sort entries
        if query.sort_by == "created_at":
            entries.sort(key=lambda e: e.created_at, reverse=True)
        elif query.sort_by == "importance":
            entries.sort(key=lambda e: e.importance_score, reverse=True)
        else:
            # Default: sort by recency of access
            entries.sort(key=lambda e: e.accessed_at, reverse=True)

        # Apply pagination
        _total_count = len(entries)
        entries = entries[query.offset:query.offset + query.limit]

        _elapsed_ms = (datetime.now(timezone.utc) - start_time).total_seconds() * 1000
        self._track_latency(elapsed_ms)

        return MemoryResult(
            entries=entries,
            _total_count = total_count,
            _query_time_ms = elapsed_ms,
            _tier = MemoryTier.EPHEMERAL,
            _has_more = (query.offset + query.limit) < total_count,
            _next_offset = query.offset + query.limit if (query.offset + query.limit) < total_count else None
        )

    async def get_by_agent(self, _agent_id: str, _limit: int) -> List[MemoryEntry]:
        """Get all entries for an agent"""
        _query = MemoryQuery(
            _agent_ids = [agent_id],
            _limit = limit,
            _sort_by = "created_at"
        )
        _result = await self.search(query)
        return result.entries

    async def clear_expired(self) -> int:
        """Clear expired entries (cleanup, though Redis handles TTL automatically)"""
        # Redis handles TTL automatically, but we can clean up empty sets
        if self._client is None:
            await self.connect()

        _pattern = f"{self.config.key_prefix}:agent:*:entries"
        _cleaned = 0

        async for key in self._client.scan_iter(match=pattern, count=100):
            _count = await self._client.scard(key)
            if count == 0:
                await self._client.delete(key)
                cleaned += 1

        return cleaned

    async def get_stats(self) -> Dict[str, Any]:
        """Get statistics for the ephemeral store"""
        if self._client is None:
            await self.connect()

        # Count entries
        _pattern = f"{self.config.key_prefix}:entry:*"
        _entry_count = 0
        async for _ in self._client.scan_iter(match=pattern, count=100):
            entry_count += 1

        # Calculate latency percentiles
        _p50 = p95 = p99 = 0.0
        if self._operation_times:
            _sorted_times = sorted(self._operation_times)
            _n = len(sorted_times)
            _p50 = sorted_times[int(n * 0.50)]
            _p95 = sorted_times[int(n * 0.95)]
            _p99 = sorted_times[int(n * 0.99)]

        # Get Redis info
        _info = await self._client.info("memory")
        _used_memory = info.get("used_memory", 0)

        return {
            "tier": MemoryTier.EPHEMERAL.value,
            "entry_count": entry_count,
            "used_memory_bytes": used_memory,
            "p50_latency_ms": p50,
            "p95_latency_ms": p95,
            "p99_latency_ms": p99,
            "connected": True,
        }

    async def health_check(self) -> bool:
        """Check if Redis is healthy"""
        try:
            if self._client is None:
                await self.connect()

            await self._client.ping()
            return True
        except Exception as e:
            logger.error("ephemeral_memory_health_check_failed", error=str(e))
            return False
