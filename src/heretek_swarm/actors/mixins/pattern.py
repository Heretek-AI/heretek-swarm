"""
PatternMixin - Pattern emission and consumption methods.

This mixin provides methods for emitting and consuming patterns
in the collective learning system.

Methods:
    _emit_pattern: Emit a pattern to the pattern library
    _consume_patterns: Consume relevant patterns from the library
    _get_pattern_confidence: Get confidence score for a pattern
    _update_pattern_relevance: Update pattern relevance scores

Version: 1.44.0
"""

import asyncio
from typing import TYPE_CHECKING, Any

import structlog

if TYPE_CHECKING:
    from heretek_swarm.collective.learning import ExtractedPattern, PatternType

logger = structlog.get_logger("PatternMixin")


class PatternMixin:
    """
    Mixin providing pattern emission and consumption methods.

    Actors with this mixin can emit patterns to the collective
    pattern library and consume relevant patterns.
    """

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Initialize pattern state."""
        super().__init__(*args, **kwargs)
        self._emitted_patterns: list[str] = []
        self._consumed_patterns: dict[str, float] = {}
        self._pattern_confidence_threshold: float = 0.7

    async def _emit_pattern(
        self,
        pattern_type: "PatternType",
        pattern_data: dict[str, Any],
        confidence: float = 0.5,
        context: dict[str, Any] | None = None,
        tags: list[str] | None = None,
    ) -> str:
        """
        Emit a pattern to the collective pattern library.

        Args:
            pattern_type: Type of pattern being emitted
            pattern_data: The pattern data
            confidence: Confidence score (0.0-1.0)
            context: Optional context for the pattern
            tags: Optional tags for categorization

        Returns:
            pattern_id: Unique identifier for the emitted pattern
        """
        pattern_id = f"pattern_{self.agent_id}_{asyncio.get_event_loop().time():.0f}"

        pattern_record = {
            "pattern_id": pattern_id,
            "pattern_type": pattern_type.value if hasattr(pattern_type, "value") else pattern_type,
            "pattern_data": pattern_data,
            "confidence": confidence,
            "context": context or {},
            "tags": tags or [],
            "emitted_by": self.agent_id,
            "emitted_at": asyncio.get_event_loop().time(),
        }

        self._emitted_patterns.append(pattern_id)

        logger.info(
            "pattern_emitted",
            pattern_id=pattern_id,
            pattern_type=pattern_type,
            confidence=confidence,
            agent_id=self.agent_id,
        )

        return pattern_id

    async def _consume_patterns(
        self,
        pattern_type: "PatternType | None" = None,
        min_confidence: float | None = None,
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        """
        Consume relevant patterns from the pattern library.

        Args:
            pattern_type: Optional filter by pattern type
            min_confidence: Minimum confidence threshold
            limit: Maximum number of patterns to return

        Returns:
            List of relevant patterns
        """
        threshold = min_confidence or self._pattern_confidence_threshold

        consumed: list[dict[str, Any]] = []
        for pattern_id, confidence in self._consumed_patterns.items():
            if confidence >= threshold:
                consumed.append({
                    "pattern_id": pattern_id,
                    "confidence": confidence,
                    "relevance": self._consumed_patterns.get(pattern_id, 0.0),
                })

        consumed.sort(key=lambda x: x["relevance"], reverse=True)
        return consumed[:limit]

    def _get_pattern_confidence(self, pattern_id: str) -> float:
        """
        Get confidence score for a pattern.

        Args:
            pattern_id: The pattern to check

        Returns:
            Confidence score (0.0-1.0)
        """
        return self._consumed_patterns.get(pattern_id, 0.0)

    async def _update_pattern_relevance(
        self,
        pattern_id: str,
        relevance_delta: float,
    ) -> None:
        """
        Update pattern relevance score.

        Args:
            pattern_id: The pattern to update
            relevance_delta: Change in relevance (-1.0 to 1.0)
        """
        current = self._consumed_patterns.get(pattern_id, 0.5)
        new_relevance = max(0.0, min(1.0, current + relevance_delta))
        self._consumed_patterns[pattern_id] = new_relevance

        logger.debug(
            "pattern_relevance_updated",
            pattern_id=pattern_id,
            old_relevance=current,
            new_relevance=new_relevance,
            agent_id=self.agent_id,
        )

    def _get_pattern_stats(self) -> dict[str, Any]:
        """
        Get pattern emission and consumption statistics.

        Returns:
            Statistics about pattern activity
        """
        return {
            "emitted_count": len(self._emitted_patterns),
            "consumed_count": len(self._consumed_patterns),
            "avg_consumed_confidence": (
                sum(self._consumed_patterns.values()) / len(self._consumed_patterns)
                if self._consumed_patterns else 0.0
            ),
            "confidence_threshold": self._pattern_confidence_threshold,
            "agent_id": self.agent_id,
        }

    @property
    def pattern_emission_count(self) -> int:
        """Get number of patterns emitted by this actor."""
        return len(self._emitted_patterns)

    @property
    def pattern_consumption_count(self) -> int:
        """Get number of patterns consumed by this actor."""
        return len(self._consumed_patterns)
