"""
Persistent Memory Store with mem0 Integration.

Provides long-term storage with semantic search using mem0's unified memory API.
Supports multiple vector stores (Qdrant, PostgreSQL, Chroma) and LLM providers.

Reference: mem0ai library for unified memory management
"""

import os
from dataclasses import dataclass, field
from typing import Any, Optional

import structlog

logger = structlog.get_logger("PersistentMemory")


@dataclass
class Mem0Config:
    """Configuration for mem0 memory store."""

    # Vector store provider
    vector_store_provider: str = "qdrant"

    # Qdrant configuration
    qdrant_host: str = field(default_factory=lambda: os.getenv("QDRANT_HOST", "localhost"))
    qdrant_port: int = field(default_factory=lambda: int(os.getenv("QDRANT_PORT", "6333")))
    qdrant_collection: str = "heretek_swarm_memories"

    # LLM provider
    llm_provider: str = "openai"
    llm_model: str = field(default_factory=lambda: os.getenv("LLM_MODEL", "gpt-4o-mini"))
    openai_api_key: Optional[str] = field(default_factory=lambda: os.getenv("OPENAI_API_KEY"))

    # Embedder configuration
    embedder_provider: str = "openai"
    embedder_model: str = field(default_factory=lambda: os.getenv("EMBEDDER_MODEL", "text-embedding-3-small"))

    # PostgreSQL fallback (if using pgvector)
    postgres_host: str = field(default_factory=lambda: os.getenv("POSTGRES_HOST", "localhost"))
    postgres_port: int = field(default_factory=lambda: int(os.getenv("POSTGRES_PORT", "5432")))
    postgres_user: str = field(default_factory=lambda: os.getenv("POSTGRES_USER", "heretek"))
    postgres_password: str = field(default_factory=lambda: os.getenv("POSTGRES_PASSWORD", "heretek"))
    postgres_database: str = field(default_factory=lambda: os.getenv("POSTGRES_DB", "heretek"))

    def to_dict(self) -> dict[str, Any]:
        """Convert config to mem0 format."""
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
                    "api_key": self.openai_api_key,
                }
            },
            "embedder": {
                "provider": self.embedder_provider,
                "config": {
                    "model": self.embedder_model,
                }
            }
        }


class PersistentMemory:
    """
    Persistent memory store using mem0 for semantic memory management.

    Features:
    - Long-term storage with semantic embeddings
    - Vector similarity search via configurable provider
    - Automatic memory organization and retrieval
    - Support for multiple users/agents

    Note: Requires Qdrant or other vector store to be running.
    """

    def __init__(
        self,
        config: Optional[Mem0Config] = None,
        user_id: str = "default",
    ) -> None:
        """
        Initialize persistent memory store.

        Args:
            config: Mem0 configuration
            user_id: Default user identifier for memories
        """
        self.config = config or Mem0Config()
        self.user_id = user_id
        self._memory = None
        self._initialized = False

    async def initialize(self) -> None:
        """Initialize the mem0 memory instance."""
        if self._initialized:
            return

        try:
            from mem0 import Memory

            self._memory = Memory.from_config(self.config.to_dict())
            self._initialized = True

            logger.info(
                "persistent_memory_initialized",
                provider=self.config.vector_store_provider,
                collection=self.config.qdrant_collection,
            )

        except ImportError:
            logger.error("mem0 package not installed. Install with: pip install mem0ai")
            raise
        except Exception as e:
            logger.error("failed_to_initialize_memory", error=str(e))
            raise

    async def store(
        self,
        content: str,
        user_id: Optional[str] = None,
        agent_id: Optional[str] = None,
        metadata: Optional[dict[str, Any]] = None,
    ) -> str:
        """
        Store a memory entry with semantic embedding.

        Args:
            content: Memory content text
            user_id: User identifier (defaults to self.user_id)
            agent_id: Agent identifier for the memory
            metadata: Additional metadata

        Returns:
            Memory ID if successful, empty string otherwise
        """
        if not self._initialized:
            await self.initialize()

        user_id = user_id or self.user_id
        meta = {"agent_id": agent_id} if agent_id else {}
        if metadata:
            meta.update(metadata)

        try:
            result = self._memory.add(
                content,
                user_id=user_id,
                metadata=meta,
            )
            memory_id = result.get("id", "")
            logger.debug(
                "memory_stored",
                memory_id=memory_id,
                user_id=user_id,
                agent_id=agent_id,
            )
            return memory_id

        except Exception as e:
            logger.error("memory_store_failed", error=str(e))
            return ""

    async def store_batch(
        self,
        memories: list[dict[str, Any]],
        user_id: Optional[str] = None,
    ) -> list[str]:
        """
        Store multiple memories efficiently.

        Args:
            memories: List of memory dicts with 'content', optional 'agent_id', 'metadata'
            user_id: User identifier (defaults to self.user_id)

        Returns:
            List of memory IDs
        """
        if not self._initialized:
            await self.initialize()

        user_id = user_id or self.user_id
        memory_ids = []

        for mem in memories:
            content = mem.get("content", "")
            agent_id = mem.get("agent_id")
            metadata = mem.get("metadata", {})

            if agent_id:
                metadata = {"agent_id": agent_id, **metadata}

            try:
                result = self._memory.add(
                    content,
                    user_id=user_id,
                    metadata=metadata,
                )
                memory_ids.append(result.get("id", ""))
            except Exception as e:
                logger.warning("batch_memory_store_failed", error=str(e))
                memory_ids.append("")

        logger.debug("batch_memory_stored", count=len(memory_ids))
        return memory_ids

    async def search(
        self,
        query: str,
        user_id: Optional[str] = None,
        agent_id: Optional[str] = None,
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        """
        Search memories using semantic similarity.

        Args:
            query: Search query text
            user_id: User identifier (defaults to self.user_id)
            agent_id: Optional agent filter
            limit: Maximum results to return

        Returns:
            List of memory entries with scores
        """
        if not self._initialized:
            await self.initialize()

        user_id = user_id or self.user_id

        try:
            filters = {}
            if agent_id:
                filters["agent_id"] = agent_id

            results = self._memory.search(
                query=query,
                user_id=user_id,
                limit=limit,
            )

            # Filter by agent_id if specified (mem0 doesn't support this directly)
            if agent_id:
                results = [r for r in results if r.get("metadata", {}).get("agent_id") == agent_id]

            logger.debug(
                "memory_searched",
                query=query[:50],
                results=len(results),
                user_id=user_id,
            )
            return results

        except Exception as e:
            logger.error("memory_search_failed", error=str(e))
            return []

    async def get_all(
        self,
        user_id: Optional[str] = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        """
        Get all memories for a user.

        Args:
            user_id: User identifier (defaults to self.user_id)
            limit: Maximum results to return

        Returns:
            List of all memory entries
        """
        if not self._initialized:
            await self.initialize()

        user_id = user_id or self.user_id

        try:
            results = self._memory.get_all(user_id=user_id)
            logger.debug("memory_get_all", count=len(results), user_id=user_id)
            return results[:limit]

        except Exception as e:
            logger.error("memory_get_all_failed", error=str(e))
            return []

    async def get(self, memory_id: str) -> Optional[dict[str, Any]]:
        """
        Get a specific memory by ID.

        Args:
            memory_id: Memory identifier

        Returns:
            Memory entry or None if not found
        """
        if not self._initialized:
            await self.initialize()

        try:
            result = self._memory.get(memory_id)
            return result if result else None

        except Exception as e:
            logger.error("memory_get_failed", memory_id=memory_id, error=str(e))
            return None

    async def delete(self, memory_id: str) -> bool:
        """
        Delete a memory entry.

        Args:
            memory_id: Memory identifier

        Returns:
            True if deleted successfully
        """
        if not self._initialized:
            await self.initialize()

        try:
            self._memory.delete(memory_id)
            logger.debug("memory_deleted", memory_id=memory_id)
            return True

        except Exception as e:
            logger.error("memory_delete_failed", memory_id=memory_id, error=str(e))
            return False

    async def update(
        self,
        memory_id: str,
        content: Optional[str] = None,
        metadata: Optional[dict[str, Any]] = None,
    ) -> bool:
        """
        Update a memory entry.

        Args:
            memory_id: Memory identifier
            content: New content (optional)
            metadata: New metadata (optional)

        Returns:
            True if updated successfully
        """
        if not self._initialized:
            await self.initialize()

        try:
            # Get existing memory
            existing = await self.get(memory_id)
            if not existing:
                return False

            # Update fields
            if content:
                existing["content"] = content
            if metadata:
                existing["metadata"] = {**existing.get("metadata", {}), **metadata}

            # Re-add to update (mem0 doesn't have direct update)
            self._memory.delete(memory_id)
            result = self._memory.add(
                existing["content"],
                user_id=existing.get("user_id", self.user_id),
                metadata=existing.get("metadata", {}),
            )

            logger.debug("memory_updated", memory_id=memory_id)
            return bool(result.get("id"))

        except Exception as e:
            logger.error("memory_update_failed", memory_id=memory_id, error=str(e))
            return False

    async def close(self) -> None:
        """Close the memory store and release resources."""
        self._initialized = False
        self._memory = None
        logger.info("persistent_memory_closed")

    def is_initialized(self) -> bool:
        """Check if memory store is initialized."""
        return self._initialized


async def create_memory_store(
    provider: str = "qdrant",
    user_id: str = "default",
) -> PersistentMemory:
    """
    Factory function to create a persistent memory store.

    Args:
        provider: Vector store provider (qdrant, postgres, chroma)
        user_id: Default user identifier

    Returns:
        Configured PersistentMemory instance
    """
    config = Mem0Config(vector_store_provider=provider)
    memory = PersistentMemory(config=config, user_id=user_id)
    await memory.initialize()
    return memory
