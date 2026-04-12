"""
MemoryMixin - Memory access and tier management methods.

This mixin provides methods for memory access patterns, tier management,
and prefetching functionality.

Methods:
    _track_memory_access: Track memory access for optimization
    _get_memory_tier: Get appropriate memory tier for access
    _prefetch_relevant: Prefetch relevant memories
    _get_memory_stats: Get memory usage statistics

Version: 1.44.0
"""

import asyncio
from enum import StrEnum
from typing import Any

import structlog

logger = structlog.get_logger("MemoryMixin")


class AccessTier(StrEnum):
    """Memory access tiers based on frequency and recency."""

    HOT = "hot"      # Frequently accessed, recent
    WARM = "warm"    # Moderately accessed
    COLD = "cold"    # Rarely accessed
    ARCHIVE = "archive"  # Historical/archived data


class MemoryMixin:
    """
    Mixin providing memory access and tier management methods.

    Actors with this mixin can track memory access patterns,
    manage memory tiers, and prefetch relevant memories.
    """

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Initialize memory state."""
        super().__init__(*args, **kwargs)
        self._memory_access_count: dict[str, int] = {}
        self._memory_last_access: dict[str, float] = {}
        self._memory_tier_cache: dict[str, AccessTier] = {}
        self._prefetch_queue: asyncio.Queue[dict[str, Any]] | None = None
        self._prefetch_in_progress: bool = False

    async def _track_memory_access(
        self,
        memory_key: str,
        access_type: str = "read",
    ) -> None:
        """
        Track memory access for optimization.

        Args:
            memory_key: The memory being accessed
            access_type: Type of access (read, write, delete)
        """
        current_time = asyncio.get_event_loop().time()

        # Increment access count
        self._memory_access_count[memory_key] = (
            self._memory_access_count.get(memory_key, 0) + 1
        )

        # Update last access time
        self._memory_last_access[memory_key] = current_time

        # Invalidate tier cache
        if memory_key in self._memory_tier_cache:
            del self._memory_tier_cache[memory_key]

        logger.debug(
            "memory_access_tracked",
            memory_key=memory_key,
            access_type=access_type,
            access_count=self._memory_access_count[memory_key],
            agent_id=self.agent_id,
        )

    def _get_memory_tier(
        self,
        memory_key: str,
        hot_threshold: int = 10,
        warm_threshold: int = 3,
    ) -> AccessTier:
        """
        Get appropriate memory tier based on access patterns.

        Args:
            memory_key: The memory to tier
            hot_threshold: Access count for HOT tier
            warm_threshold: Access count for WARM tier

        Returns:
            Appropriate access tier
        """
        # Check cache first
        if memory_key in self._memory_tier_cache:
            return self._memory_tier_cache[memory_key]

        access_count = self._memory_access_count.get(memory_key, 0)
        last_access = self._memory_last_access.get(memory_key, 0)
        current_time = asyncio.get_event_loop().time()

        # Calculate recency score (0.0 - 1.0)
        time_since_access = current_time - last_access
        recency_score = max(0.0, 1.0 - (time_since_access / 3600))  # Decay over 1 hour

        # Calculate frequency score (0.0 - 1.0)
        frequency_score = min(1.0, access_count / hot_threshold)

        # Combined score
        (recency_score + frequency_score) / 2

        if access_count >= hot_threshold and recency_score > 0.7:
            tier = AccessTier.HOT
        elif access_count >= warm_threshold:
            tier = AccessTier.WARM
        elif access_count > 0:
            tier = AccessTier.COLD
        else:
            tier = AccessTier.ARCHIVE

        self._memory_tier_cache[memory_key] = tier

        logger.debug(
            "memory_tier_assigned",
            memory_key=memory_key,
            tier=tier.value,
            access_count=access_count,
            recency_score=recency_score,
            agent_id=self.agent_id,
        )

        return tier

    async def _prefetch_relevant(
        self,
        context: dict[str, Any],
        limit: int = 5,
    ) -> list[dict[str, Any]]:
        """
        Prefetch relevant memories based on context.

        Args:
            context: Current context for relevance matching
            limit: Maximum number of memories to prefetch

        Returns:
            List of prefetched memory entries
        """
        if self._prefetch_in_progress:
            return []

        self._prefetch_in_progress = True
        prefetched: list[dict[str, Any]] = []

        try:
            # Simple relevance: match by tags or keywords
            context.get("tags", [])
            context.get("keywords", [])

            for memory_key, tier in self._memory_tier_cache.items():
                if tier == AccessTier.HOT or tier == AccessTier.WARM:
                    prefetched.append({
                        "memory_key": memory_key,
                        "tier": tier.value,
                        "access_count": self._memory_access_count.get(memory_key, 0),
                    })

                if len(prefetched) >= limit:
                    break

            logger.info(
                "memories_prefetched",
                count=len(prefetched),
                agent_id=self.agent_id,
            )

        finally:
            self._prefetch_in_progress = False

        return prefetched

    def _get_memory_stats(self) -> dict[str, Any]:
        """
        Get memory usage statistics.

        Returns:
            Statistics about memory access patterns
        """
        total_accesses = sum(self._memory_access_count.values())
        tier_counts = {tier.value: 0 for tier in AccessTier}

        for memory_key in self._memory_access_count:
            tier = self._get_memory_tier(memory_key)
            tier_counts[tier.value] += 1

        return {
            "total_memories_accessed": len(self._memory_access_count),
            "total_accesses": total_accesses,
            "tier_distribution": tier_counts,
            "avg_accesses_per_memory": (
                total_accesses / len(self._memory_access_count)
                if self._memory_access_count else 0.0
            ),
            "prefetch_in_progress": self._prefetch_in_progress,
            "agent_id": self.agent_id,
        }

    def _clear_memory_stats(self) -> None:
        """Clear memory access statistics."""
        self._memory_access_count.clear()
        self._memory_last_access.clear()
        self._memory_tier_cache.clear()
        logger.info("memory_stats_cleared", agent_id=self.agent_id)

    @property
    def memory_access_count(self) -> int:
        """Get total number of memory accesses."""
        return sum(self._memory_access_count.values())

    @property
    def hot_memory_count(self) -> int:
        """Get count of memories in HOT tier."""
        return sum(
            1 for key in self._memory_access_count
            if self._get_memory_tier(key) == AccessTier.HOT
        )
