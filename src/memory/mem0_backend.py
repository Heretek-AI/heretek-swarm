"""
mem0 Backend Integration for Heretek Swarm.

Provides integration with mem0ai for production-ready long-term memory.
mem0 provides:
- +26% accuracy over OpenAI Memory
- 91% faster responses
- 90% lower token usage
- Multi-level memory (User, Session, Agent)

This adapter integrates mem0 with the existing Heretek Swarm memory interface.
"""

import os
from datetime import datetime, timezone
from typing import Dict, List, Optional
from uuid import UUID, uuid4

import structlog
from pydantic import BaseModel, Field

from .base import MemoryEntry, MemoryQuery, MemoryResult, MemoryTier, MemoryType

_logger = structlog.get_logger()


class Mem0Config(BaseModel):
    """Configuration for mem0 backend"""

    # Vector store configuration
    vector_store_provider: str = Field(default="qdrant")
    qdrant_host: str = Field(default="localhost")
    qdrant_port: int = Field(default=6333)
    qdrant_collection: str = Field(default="heretek_memories")

    # LLM configuration
    llm_provider: str = Field(default="openai")
    llm_model: str = Field(default="gpt-4o-mini")
    openai_api_key: Optional[str] = Field(default=None)

    # Embedder configuration
    embedder_provider: str = Field(default="openai")
    embedder_model: str = Field(default="text-embedding-3-small")

    # History database
    history_db_path: str = Field(default="/data/mem0_history.db")

    def get_mem0_config(self) -> dict:
        """Convert to mem0 configuration format"""
        _api_key = self.openai_api_key or os.getenv("OPENAI_API_KEY")

        return {
            "vector_store": {
                "provider": self.vector_store_provider,
                "config": {
                    "host": self.qdrant_host,
                    "port": self.qdrant_port,
                    "collection_name": self.qdrant_collection,
                }
            },
            "llm": {
                "provider": self.llm_provider,
                "config": {
                    "model": self.llm_model,
                    "api_key": api_key,
                }
            },
            "embedder": {
                "provider": self.embedder_provider,
                "config": {
                    "model": self.embedder_model,
                }
            },
            "history_db_path": self.history_db_path,
        }


class Mem0Backend:
    """
    mem0-backed persistent memory store.

    This provides production-ready long-term memory with:
    - Intelligent memory extraction
    - Vector-based semantic search
    - Memory consolidation and deduplication
    - Multi-level memory support (user, session, agent)

    Integration with Heretek Swarm:
    - Wraps mem0.Memory with our MemoryEntry interface
    - Maps agent_id to mem0 user_id
    - Preserves metadata and memory types
    """

    def __init__(self, _config: Optional[Mem0Config]):
        self.config = config or Mem0Config()
        self._memory = None
        self._initialized = False

        # Performance tracking
        self._operation_times: List[float] = []
        self._max_samples = 1000

    def _track_latency(self, _elapsed_ms: float) -> None:
        """Track operation latency"""
        self._operation_times.append(elapsed_ms)
        if len(self._operation_times) > self._max_samples:
            self._operation_times = self._operation_times[-self._max_samples:]

    async def initialize(self) -> None:
        """Initialize mem0 connection"""
        if self._initialized:
            return

        try:
            from mem0 import Memory

            self._memory = Memory.from_config(self.config.get_mem0_config())
            self._initialized = True

            logger.info(
                "mem0_backend_initialized",
                _vector_store = self.config.vector_store_provider,
                _llm_model = self.config.llm_model,
            )

        except ImportError:
            logger.warning(
                "mem0_not_installed",
                _message = "pip install mem0ai to use mem0 backend",
            )
            raise
        except Exception as e:
            logger.error("mem0_initialization_failed", error=str(e))
            raise

    async def shutdown(self) -> None:
        """Shutdown mem0 connection"""
        self._memory = None
        self._initialized = False
        logger.info("mem0_backend_shutdown")

    async def store(self, _entry: MemoryEntry) -> str:
        """
        Store a memory entry using mem0.

        Args:
            entry: Memory entry to store

        Returns:
            Memory ID from mem0
        """
        if not self._initialized:
            await self.initialize()

        _start_time = datetime.now(timezone.utc)

        try:
            # Store in mem0 with agent_id as user_id
            _result = self._memory.add(
                entry.content,
                _user_id = entry.agent_id,
                metadata={
                    "memory_type": entry.memory_type.value,
                    "session_id": str(entry.session_id) if entry.session_id else None,
                    "tags": entry.tags,
                    "importance_score": entry.importance_score,
                    "parent_id": str(entry.parent_id) if entry.parent_id else None,
                    "source_agent": entry.source_agent,
                    "heretek_id": str(entry.id),
                    **entry.metadata,
                }
            )

            _elapsed_ms = (datetime.now(timezone.utc) - start_time).total_seconds() * 1000
            self._track_latency(elapsed_ms)

            # Extract memory ID from result
            _memory_id = result.get("id", str(entry.id))

            logger.debug(
                "mem0_memory_stored",
                _memory_id = memory_id,
                agent_id=entry.agent_id,
                _elapsed_ms = elapsed_ms,
            )

            return memory_id

        except Exception as e:
            logger.error(
                "mem0_store_failed",
                _entry_id = str(entry.id),
                _error = str(e),
            )
            raise

    async def store_batch(self, _entries: List[MemoryEntry]) -> List[str]:
        """Store multiple entries efficiently"""
        if not entries:
            return []

        _memory_ids = []
        for entry in entries:
            _memory_id = await self.store(entry)
            memory_ids.append(memory_id)

        return memory_ids

    async def search(self, _query: MemoryQuery) -> MemoryResult:
        """
        Search memories using mem0 semantic search.

        Args:
            query: Search query with filters

        Returns:
            MemoryResult with matching entries
        """
        if not self._initialized:
            await self.initialize()

        _start_time = datetime.now(timezone.utc)

        try:
            # Build mem0 search parameters
            _results = []

            if query.query_text:
                # Semantic search with mem0
                for agent_id in (query.agent_ids or ["default"]):
                    _search_results = self._memory.search(
                        query.query_text,
                        _user_id = agent_id,
                        _limit = query.limit,
                    )

                    for result in search_results.get("results", []):
                        _entry = self._mem0_result_to_entry(result, agent_id)
                        results.append(entry)

            # Sort by score/importance
            results.sort(key=lambda e: e.importance_score, reverse=True)

            # Apply pagination
            _total_count = len(results)
            _paginated = results[query.offset:query.offset + query.limit]

            _elapsed_ms = (datetime.now(timezone.utc) - start_time).total_seconds() * 1000
            self._track_latency(elapsed_ms)

            logger.debug(
                "mem0_search_completed",
                _query = query.query_text,
                _total_count = total_count,
                _returned_count = len(paginated),
                _elapsed_ms = elapsed_ms,
            )

            return MemoryResult(
                _entries = paginated,
                _total_count = total_count,
                _offset = query.offset,
                _limit = query.limit,
            )

        except Exception as e:
            logger.error(
                "mem0_search_failed",
                _query = query.query_text,
                _error = str(e),
            )
            raise

    async def get_all(self, _agent_id: str) -> List[MemoryEntry]:
        """
        Get all memories for an agent.

        Args:
            agent_id: Agent to get memories for

        Returns:
            List of memory entries
        """
        if not self._initialized:
            await self.initialize()

        _start_time = datetime.now(timezone.utc)

        try:
            _results = self._memory.get_all(user_id=agent_id)

            _entries = []
            for result in results.get("results", []):
                _entry = self._mem0_result_to_entry(result, agent_id)
                entries.append(entry)

            _elapsed_ms = (datetime.now(timezone.utc) - start_time).total_seconds() * 1000
            self._track_latency(elapsed_ms)

            logger.debug(
                "mem0_get_all_completed",
                _agent_id = agent_id,
                _count = len(entries),
                _elapsed_ms = elapsed_ms,
            )

            return entries

        except Exception as e:
            logger.error(
                "mem0_get_all_failed",
                _agent_id = agent_id,
                _error = str(e),
            )
            raise

    async def delete(self, _memory_id: str) -> bool:
        """
        Delete a memory by ID.

        Args:
            memory_id: Memory ID to delete

        Returns:
            True if deleted successfully
        """
        if not self._initialized:
            await self.initialize()

        _start_time = datetime.now(timezone.utc)

        try:
            self._memory.delete(memory_id)

            _elapsed_ms = (datetime.now(timezone.utc) - start_time).total_seconds() * 1000
            self._track_latency(elapsed_ms)

            logger.debug(
                "mem0_memory_deleted",
                _memory_id = memory_id,
                _elapsed_ms = elapsed_ms,
            )

            return True

        except Exception as e:
            logger.error(
                "mem0_delete_failed",
                _memory_id = memory_id,
                _error = str(e),
            )
            return False

    def _mem0_result_to_entry(self, _result: dict, _agent_id: str) -> MemoryEntry:
        """Convert mem0 result to MemoryEntry"""
        _metadata = result.get("metadata", {})

        return MemoryEntry(
            _id = UUID(metadata.get("heretek_id", str(uuid4()))),
            _agent_id = agent_id,
            _session_id = UUID(metadata["session_id"]) if metadata.get("session_id") else None,
            _content = result.get("memory", ""),
            _content_type = "text/plain",
            _metadata = {k: v for k, v in metadata.items()
                     if k not in ["memory_type", "session_id", "tags", "importance_score",
                                  "parent_id", "source_agent", "heretek_id"]},
            _memory_type = MemoryType(metadata.get("memory_type", "semantic")),
            _tier = MemoryTier.PERSISTENT,
            _tags = metadata.get("tags", []),
            _parent_id = UUID(metadata["parent_id"]) if metadata.get("parent_id") else None,
            _source_agent = metadata.get("source_agent"),
            _created_at = datetime.fromisoformat(result["created_at"]) if result.get("created_at") else datetime.now(timezone.utc),
            _updated_at = datetime.fromisoformat(result["updated_at"]) if result.get("updated_at") else datetime.now(timezone.utc),
            _importance_score = metadata.get("importance_score", 0.5),
        )

    def get_latency_stats(self) -> Dict[str, float]:
        """Get latency statistics"""
        if not self._operation_times:
            return {"p50": 0, "p95": 0, "p99": 0, "avg": 0}

        _sorted_times = sorted(self._operation_times)
        _count = len(sorted_times)

        return {
            "p50": sorted_times[int(count * 0.5)],
            "p95": sorted_times[int(count * 0.95)],
            "p99": sorted_times[int(count * 0.99)],
            "avg": sum(sorted_times) / count,
        }
