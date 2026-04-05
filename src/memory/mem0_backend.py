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
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

import structlog
from pydantic import BaseModel, Field

from .base import MemoryEntry, MemoryQuery, MemoryResult, MemoryTier, MemoryType

logger = structlog.get_logger()


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
        api_key = self.openai_api_key or os.getenv("OPENAI_API_KEY")

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

    def __init__(
        self,
        config: Optional[Mem0Config] = None,
    ):
        self.config = config or Mem0Config()
        self._memory = None
        self._initialized = False

        # Performance tracking
        self._operation_times: List[float] = []
        self._max_samples = 1000

    def _track_latency(self, elapsed_ms: float) -> None:
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
                vector_store=self.config.vector_store_provider,
                llm_model=self.config.llm_model,
            )

        except ImportError:
            logger.warning(
                "mem0_not_installed",
                message="pip install mem0ai to use mem0 backend",
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

    async def store(
        self,
        entry: MemoryEntry,
    ) -> str:
        """
        Store a memory entry using mem0.

        Args:
            entry: Memory entry to store

        Returns:
            Memory ID from mem0
        """
        if not self._initialized:
            await self.initialize()

        start_time = datetime.utcnow()

        try:
            # Store in mem0 with agent_id as user_id
            result = self._memory.add(
                entry.content,
                user_id=entry.agent_id,
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

            elapsed_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
            self._track_latency(elapsed_ms)

            # Extract memory ID from result
            memory_id = result.get("id", str(entry.id))

            logger.debug(
                "mem0_memory_stored",
                memory_id=memory_id,
                agent_id=entry.agent_id,
                elapsed_ms=elapsed_ms,
            )

            return memory_id

        except Exception as e:
            logger.error(
                "mem0_store_failed",
                entry_id=str(entry.id),
                error=str(e),
            )
            raise

    async def store_batch(
        self,
        entries: List[MemoryEntry],
    ) -> List[str]:
        """Store multiple entries efficiently"""
        if not entries:
            return []

        memory_ids = []
        for entry in entries:
            memory_id = await self.store(entry)
            memory_ids.append(memory_id)

        return memory_ids

    async def search(
        self,
        query: MemoryQuery,
    ) -> MemoryResult:
        """
        Search memories using mem0 semantic search.

        Args:
            query: Search query with filters

        Returns:
            MemoryResult with matching entries
        """
        if not self._initialized:
            await self.initialize()

        start_time = datetime.utcnow()

        try:
            # Build mem0 search parameters
            results = []

            if query.query_text:
                # Semantic search with mem0
                for agent_id in (query.agent_ids or ["default"]):
                    search_results = self._memory.search(
                        query.query_text,
                        user_id=agent_id,
                        limit=query.limit,
                    )

                    for result in search_results.get("results", []):
                        entry = self._mem0_result_to_entry(result, agent_id)
                        results.append(entry)

            # Sort by score/importance
            results.sort(key=lambda e: e.importance_score, reverse=True)

            # Apply pagination
            total_count = len(results)
            paginated = results[query.offset:query.offset + query.limit]

            elapsed_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
            self._track_latency(elapsed_ms)

            logger.debug(
                "mem0_search_completed",
                query=query.query_text,
                total_count=total_count,
                returned_count=len(paginated),
                elapsed_ms=elapsed_ms,
            )

            return MemoryResult(
                entries=paginated,
                total_count=total_count,
                offset=query.offset,
                limit=query.limit,
            )

        except Exception as e:
            logger.error(
                "mem0_search_failed",
                query=query.query_text,
                error=str(e),
            )
            raise

    async def get_all(
        self,
        agent_id: str,
    ) -> List[MemoryEntry]:
        """
        Get all memories for an agent.

        Args:
            agent_id: Agent to get memories for

        Returns:
            List of memory entries
        """
        if not self._initialized:
            await self.initialize()

        start_time = datetime.utcnow()

        try:
            results = self._memory.get_all(user_id=agent_id)

            entries = []
            for result in results.get("results", []):
                entry = self._mem0_result_to_entry(result, agent_id)
                entries.append(entry)

            elapsed_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
            self._track_latency(elapsed_ms)

            logger.debug(
                "mem0_get_all_completed",
                agent_id=agent_id,
                count=len(entries),
                elapsed_ms=elapsed_ms,
            )

            return entries

        except Exception as e:
            logger.error(
                "mem0_get_all_failed",
                agent_id=agent_id,
                error=str(e),
            )
            raise

    async def delete(
        self,
        memory_id: str,
    ) -> bool:
        """
        Delete a memory by ID.

        Args:
            memory_id: Memory ID to delete

        Returns:
            True if deleted successfully
        """
        if not self._initialized:
            await self.initialize()

        start_time = datetime.utcnow()

        try:
            self._memory.delete(memory_id)

            elapsed_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
            self._track_latency(elapsed_ms)

            logger.debug(
                "mem0_memory_deleted",
                memory_id=memory_id,
                elapsed_ms=elapsed_ms,
            )

            return True

        except Exception as e:
            logger.error(
                "mem0_delete_failed",
                memory_id=memory_id,
                error=str(e),
            )
            return False

    def _mem0_result_to_entry(
        self,
        result: dict,
        agent_id: str,
    ) -> MemoryEntry:
        """Convert mem0 result to MemoryEntry"""
        metadata = result.get("metadata", {})

        return MemoryEntry(
            id=UUID(metadata.get("heretek_id", str(uuid4()))),
            agent_id=agent_id,
            session_id=UUID(metadata["session_id"]) if metadata.get("session_id") else None,
            content=result.get("memory", ""),
            content_type="text/plain",
            metadata={k: v for k, v in metadata.items()
                     if k not in ["memory_type", "session_id", "tags", "importance_score",
                                  "parent_id", "source_agent", "heretek_id"]},
            memory_type=MemoryType(metadata.get("memory_type", "semantic")),
            tier=MemoryTier.PERSISTENT,
            tags=metadata.get("tags", []),
            parent_id=UUID(metadata["parent_id"]) if metadata.get("parent_id") else None,
            source_agent=metadata.get("source_agent"),
            created_at=datetime.fromisoformat(result["created_at"]) if result.get("created_at") else datetime.utcnow(),
            updated_at=datetime.fromisoformat(result["updated_at"]) if result.get("updated_at") else datetime.utcnow(),
            importance_score=metadata.get("importance_score", 0.5),
        )

    def get_latency_stats(self) -> Dict[str, float]:
        """Get latency statistics"""
        if not self._operation_times:
            return {"p50": 0, "p95": 0, "p99": 0, "avg": 0}

        sorted_times = sorted(self._operation_times)
        count = len(sorted_times)

        return {
            "p50": sorted_times[int(count * 0.5)],
            "p95": sorted_times[int(count * 0.95)],
            "p99": sorted_times[int(count * 0.99)],
            "avg": sum(sorted_times) / count,
        }
