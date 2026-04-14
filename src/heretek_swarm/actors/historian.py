"""
Historian Agent - Memory and context provider for the Triad.

The Historian provides:
- Long-term memory storage and retrieval
- Context provision for deliberations
- Historical pattern recognition
- Knowledge synthesis from past executions
- Lineage tracking for decisions

Features:
- LRU cache with configurable max size for context and patterns
- Cache eviction when limits are reached
"""

from collections import OrderedDict
from datetime import UTC, datetime
from typing import Any

import structlog
from swarms import Agent

from heretek_swarm.actors.base import ActorMessage, AgentActor
from heretek_swarm.actors.mixins import (
    DeliberationMixin,
    HealthReportingMixin,
    LearningMixin,
    MemoryMixin,
    PatternMixin,
    ValidationMixin,
)

# Session 44: Collective Learning Integration
from heretek_swarm.collective.learning import PatternExtractor

# Session 44: Consensus Integration
from heretek_swarm.consensus.swarm_deliberation import SwarmDeliberationEngine
from heretek_swarm.knowledge.unified_access import KnowledgeQueryResult, UnifiedKnowledgeAccess

# Session 44: Memory Optimization Integration
from heretek_swarm.memory.access_patterns import AccessPatternAnalyzer
from heretek_swarm.memory.base import DualTierMemory, MemoryEntry

# Session 44: Zero-Trust Validation
from heretek_swarm.security.zero_trust import ZeroTrustValidator

logger = structlog.get_logger("HistorianAgent")


class LRUCache:
    """
    LRU Cache implementation with configurable max size.

    Provides automatic eviction of least-recently-used items when capacity is exceeded.
    """

    def __init__(self, max_size: int = 100):
        """
        Initialize LRU cache.

        Args:
            max_size: Maximum number of items to cache (default: 100)
        """
        self._cache: OrderedDict[str, Any] = OrderedDict()
        self.max_size = max_size
        self.hits = 0
        self.misses = 0

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get item from cache.

        Args:
            key: Cache key
            default: Default value if not found

        Returns:
            Cached value or default
        """
        if key not in self._cache:
            self.misses += 1
            return default

        # Move to end (most recently used)
        self._cache.move_to_end(key)
        self.hits += 1
        return self._cache[key]

    def set(self, key: str, value: Any) -> None:
        """
        Set item in cache.

        Args:
            key: Cache key
            value: Value to cache
        """
        if key in self._cache:
            self._cache.move_to_end(key)
            self._cache[key] = value
        else:
            if len(self._cache) >= self.max_size:
                # Evict least recently used
                self._cache.popitem(last=False)
            self._cache[key] = value

    def clear(self) -> None:
        """Clear all cached items."""
        self._cache.clear()
        self.hits = 0
        self.misses = 0

    def invalidate(self, key: str) -> bool:
        """
        Invalidate a specific cache entry.

        Args:
            key: Cache key to invalidate

        Returns:
            True if key was found and removed, False otherwise
        """
        if key in self._cache:
            del self._cache[key]
            return True
        return False

    def invalidate_pattern(self, pattern: str) -> int:
        """
        Invalidate all cache entries matching a pattern.

        Args:
            pattern: Glob-style pattern (* matches any string)

        Returns:
            Number of entries invalidated
        """
        import fnmatch

        keys_to_remove = [key for key in self._cache if fnmatch.fnmatch(key, pattern)]
        for key in keys_to_remove:
            del self._cache[key]
        return len(keys_to_remove)

    def __contains__(self, key: str) -> bool:
        """Check if key is in cache."""
        return key in self._cache

    def __len__(self) -> int:
        """Return number of cached items."""
        return len(self._cache)

    def get_statistics(self) -> dict[str, Any]:
        """Get cache statistics."""
        total = self.hits + self.misses
        hit_rate = (self.hits / total * 100) if total > 0 else 0.0
        return {
            "size": len(self._cache),
            "max_size": self.max_size,
            "hits": self.hits,
            "misses": self.misses,
            "hit_rate_percent": round(hit_rate, 2),
            "invalidations": getattr(self, "_invalidation_count", 0),
        }


class HistorianAgent(
    HealthReportingMixin,
    ValidationMixin,
    DeliberationMixin,
    PatternMixin,
    MemoryMixin,
    LearningMixin,
    AgentActor,
):
    """
    Historian Agent - Memory and context provider.

    The Historian is the memory specialist for the Triad:
    - Stores and retrieves long-term memories
    - Provides context for current deliberations
    - Recognizes historical patterns
    - Synthesizes knowledge from past executions
    - Tracks decision lineage
    """

    def __init__(
        self,
        agent_id: str = "historian",
        name: str = "Historian",
        description: str = "Memory and context provider for the Triad",
        swarms_agent: Agent | None = None,
        memory_system: DualTierMemory | None = None,
        context_window: int = 10,
        context_cache_max_size: int = 100,
        pattern_cache_max_size: int = 50,
        pattern_extractor: PatternExtractor | None = None,
        deliberation_engine: SwarmDeliberationEngine | None = None,
        access_analyzer: AccessPatternAnalyzer | None = None,
        zero_trust_validator: ZeroTrustValidator | None = None,
        **kwargs,
    ) -> None:
        """
        Initialize the Historian agent.

        Args:
            agent_id: Unique identifier
            name: Human-readable name
            description: Agent description
            swarms_agent: Optional Swarms Agent for LLM capabilities
            memory_system: Optional dual-tier memory system
            context_window: Number of recent memories to include as context
            context_cache_max_size: Maximum context cache entries (default: 100)
            pattern_cache_max_size: Maximum pattern cache entries (default: 50)
            **kwargs: Additional arguments
        """
        super().__init__(
            agent_id=agent_id,
            name=name,
            description=description,
            topics=["triad", "memory", "context", "history", "lineage"],
            capabilities=[
                "memory-storage",
                "memory-retrieval",
                "context-provision",
                "pattern-recognition",
                "lineage-tracking",
            ],
            swarms_agent=swarms_agent,
            **kwargs,
        )

        self.memory_system = memory_system or DualTierMemory()
        self.rag_pipeline = kwargs.get("rag_pipeline")
        self.context_window = context_window

        # Historian-specific state with LRU caches
        self.decision_lineage: dict[str, list[str]] = {}
        self.pattern_cache = LRUCache(max_size=pattern_cache_max_size)
        self.context_cache = LRUCache(max_size=context_cache_max_size)

        # Unified knowledge access layer
        self.knowledge_access: UnifiedKnowledgeAccess | None = None

        # Session 44: Collective Learning Integration
        self.pattern_extractor = pattern_extractor or PatternExtractor(
            min_support=3, min_confidence=0.6
        )

        # Session 44: Consensus Integration
        self.deliberation_engine = deliberation_engine or SwarmDeliberationEngine(
            max_rounds=5, consensus_threshold=0.75, min_participants=2
        )

        # Session 44: Memory Optimization Integration
        self.access_analyzer = access_analyzer or AccessPatternAnalyzer()

        # Session 44: Zero-Trust Validation
        self.zero_trust_validator = zero_trust_validator or ZeroTrustValidator()

        # Session 44: Integration state
        self._active_deliberations: dict[str, str] = {}
        self._pattern_emitted: Set[str] = set()

        logger.info(f"[{self.agent_id}] Historian agent initialized")

    async def initialize(self) -> None:
        """Initialize the Historian agent."""
        # Initialize memory system
        await self.memory_system.initialize()

        # Initialize unified knowledge access layer
        if self.rag_pipeline:
            self.knowledge_access = UnifiedKnowledgeAccess(
                memory_system=self.memory_system,
                rag_pipeline=self.rag_pipeline,
            )
            logger.info(f"[{self.agent_id}] Unified knowledge access initialized")
        else:
            self.knowledge_access = UnifiedKnowledgeAccess(
                memory_system=self.memory_system,
                rag_pipeline=None,
            )
            logger.info(f"[{self.agent_id}] Knowledge access initialized (memory only)")

        # Register message handlers
        self.register_handler("store_memory", self._handle_store_memory)
        self.register_handler("retrieve_context", self._handle_retrieve_context)
        self.register_handler("query_history", self._handle_query_history)
        self.register_handler("track_lineage", self._handle_track_lineage)
        self.register_handler("pattern_match", self._handle_pattern_match)
        self.register_handler("unified_query", self._handle_unified_query)

        logger.info(f"[{self.agent_id}] Historian initialization complete")

    async def process_message(self, message: ActorMessage) -> None:
        """Process incoming messages."""
        handler = self._message_handlers.get(message.message_type)
        if handler:
            try:
                await handler(message)
            except Exception as e:
                logger.error(
                    f"[{self.agent_id}] Error processing message {message.message_type}: {e}",
                    exc_info=True,
                )
                self.error_count += 1
                # Send error response if reply_to is specified
                if message.content.get("reply_to"):
                    await self.send(
                        topic=message.content["reply_to"],
                        content={
                            "message_type": "error_response",
                            "error": str(e),
                            "original_message_type": message.message_type,
                        },
                        correlation_id=message.correlation_id,
                    )
        else:
            logger.warning(f"[{self.agent_id}] Unhandled message type: {message.message_type}")

    async def _handle_store_memory(self, message: ActorMessage) -> None:
        """Handle memory storage requests with validation."""
        # P2-7 fix: Validate input before processing
        try:
            validated = self._validate_message_content("store_memory", message.content)
            if validated:
                content = validated.content
                metadata = validated.metadata
                ttl = validated.ttl
                persistent = validated.persistent
            else:
                # Fallback to unvalidated access
                content = message.content.get("content")
                metadata = message.content.get("metadata", {})
                ttl = message.content.get("ttl")
                persistent = message.content.get("persistent", False)
        except ValueError as e:
            logger.error(f"[{self.agent_id}] Store memory validation failed: {e}")
            return

        logger.debug(f"[{self.agent_id}] Storing memory")

        entry = await self.store_memory(
            content=content,
            metadata=metadata,
            ttl=ttl,
            persistent=persistent,
        )

        reply_topic = message.content.get("reply_to", "memory")
        await self.send(
            topic=reply_topic,
            content={
                "message_type": "store_memory_response",
                "memory_id": entry.id,
                "created_at": entry.created_at,
                "persistent": persistent,
            },
            correlation_id=message.correlation_id,
        )

    async def _handle_retrieve_context(self, message: ActorMessage) -> None:
        """Handle context retrieval requests with validation."""
        # P2-7 fix: Validate input before processing
        try:
            validated = self._validate_message_content("retrieve_context", message.content)
            if validated:
                # Extract topic from filters or use default
                topic = (
                    validated.filters.get("topic")
                    if hasattr(validated, "filters")
                    else message.content.get("topic")
                )
                filters = (
                    validated.filters
                    if hasattr(validated, "filters")
                    else message.content.get("filters", {})
                )
                window_size = (
                    validated.limit
                    if hasattr(validated, "limit")
                    else message.content.get("window_size", self.context_window)
                )
            else:
                # Fallback to unvalidated access
                topic = message.content.get("topic")
                filters = message.content.get("filters", {})
                window_size = message.content.get("window_size", self.context_window)
        except ValueError as e:
            logger.error(f"[{self.agent_id}] Retrieve context validation failed: {e}")
            return

        logger.debug(f"[{self.agent_id}] Retrieving context for: {topic}")

        context = await self.retrieve_context(
            topic=topic,
            filters=filters,
            window_size=window_size,
        )

        reply_topic = message.content.get("reply_to", "context")
        await self.send(
            topic=reply_topic,
            content={
                "message_type": "retrieve_context_response",
                "topic": topic,
                "context": context,
                "context_size": len(context),
            },
            correlation_id=message.correlation_id,
        )

    async def _handle_query_history(self, message: ActorMessage) -> None:
        """Handle history query requests with validation."""
        # P2-7 fix: Validate input before processing
        try:
            validated = self._validate_message_content("query_history", message.content)
            if validated:
                query_text = validated.query_text
                filters = validated.filters
                limit = validated.limit
            else:
                # Fallback to unvalidated access
                query_text = message.content.get("query_text")
                filters = message.content.get("filters", {})
                limit = message.content.get("limit", 10)
        except ValueError as e:
            logger.error(f"[{self.agent_id}] Query history validation failed: {e}")
            return

        logger.debug(f"[{self.agent_id}] Querying history: {query_text}")

        results = await self.query_history(
            query_text=query_text,
            filters=filters,
            limit=limit,
        )

        reply_topic = message.content.get("reply_to", "history")
        await self.send(
            topic=reply_topic,
            content={
                "message_type": "query_history_response",
                "query": query_text,
                "results": results,
                "result_count": len(results),
            },
            correlation_id=message.correlation_id,
        )

    async def _handle_track_lineage(self, message: ActorMessage) -> None:
        """Handle lineage tracking requests with validation."""
        # P2-7 fix: Validate input before processing
        try:
            validated = self._validate_message_content("track_lineage", message.content)
            if validated:
                decision_id = validated.decision_id
                parent_ids = validated.parent_ids
            else:
                # Fallback to unvalidated access
                decision_id = message.content.get("decision_id")
                parent_ids = message.content.get("parent_ids", [])
        except ValueError as e:
            logger.error(f"[{self.agent_id}] Track lineage validation failed: {e}")
            return

        logger.debug(f"[{self.agent_id}] Tracking lineage for: {decision_id}")

        await self.track_decision_lineage(
            decision_id=decision_id,
            parent_ids=parent_ids,
        )

        reply_topic = message.content.get("reply_to", "lineage")
        await self.send(
            topic=reply_topic,
            content={
                "message_type": "track_lineage_response",
                "decision_id": decision_id,
                "parent_ids": parent_ids,
            },
            correlation_id=message.correlation_id,
        )

    async def _handle_pattern_match(self, message: ActorMessage) -> None:
        """Handle pattern matching requests with validation."""
        # P2-7 fix: Validate input before processing
        try:
            validated = self._validate_message_content("pattern_match", message.content)
            if validated:
                current_situation = (
                    validated.query_text
                    if hasattr(validated, "query_text")
                    else message.content.get("situation")
                )
            else:
                # Fallback to unvalidated access
                current_situation = message.content.get("situation")
        except ValueError as e:
            logger.error(f"[{self.agent_id}] Pattern match validation failed: {e}")
            return

        logger.debug(f"[{self.agent_id}] Matching patterns for: {current_situation}")

        patterns = await self.match_patterns(current_situation)

        reply_topic = message.content.get("reply_to", "patterns")
        await self.send(
            topic=reply_topic,
            content={
                "message_type": "pattern_match_response",
                "situation": current_situation,
                "matched_patterns": patterns,
                "pattern_count": len(patterns),
            },
            correlation_id=message.correlation_id,
        )

    async def _handle_unified_query(self, message: ActorMessage) -> None:
        """Handle unified knowledge query requests using the knowledge access layer."""
        try:
            query_text = message.content.get("query")
            sources = message.content.get("sources", ["memory", "rag"])
            limit = message.content.get("limit", 10)
            rerank = message.content.get("rerank", True)
            diversity_lambda = message.content.get("diversity_lambda", 0.5)
            filters = message.content.get("filters", {})

            if not query_text:
                logger.error(f"[{self.agent_id}] Unified query requires query text")
                return

            logger.debug(f"[{self.agent_id}] Executing unified query: {query_text[:50]}")

            # Execute unified query
            result = await self.knowledge_access.query(
                query=query_text,
                sources=sources,
                limit=limit,
                rerank=rerank,
                diversity_lambda=diversity_lambda,
                filters=filters,
            )

            # Send response
            reply_topic = message.content.get("reply_to", "knowledge")
            await self.send(
                topic=reply_topic,
                content={
                    "message_type": "unified_query_response",
                    "query": query_text,
                    "results": result.to_dict(),
                    "entry_count": len(result.entries),
                    "total_results": result.total_results,
                    "query_time_ms": result.query_time_ms,
                    "reranking_applied": result.reranking_applied,
                },
                correlation_id=message.correlation_id,
            )

        except Exception as e:
            logger.error(f"[{self.agent_id}] Unified query error: {e}", exc_info=True)
            if message.content.get("reply_to"):
                await self.send(
                    topic=message.content["reply_to"],
                    content={
                        "message_type": "error_response",
                        "error": str(e),
                    },
                    correlation_id=message.correlation_id,
                )

    async def unified_query(
        self,
        query: str,
        sources: list[str] | None = None,
        limit: int = 10,
        rerank: bool = True,
        diversity_lambda: float = 0.5,
        filters: dict[str, Any] | None = None,
    ) -> KnowledgeQueryResult:
        """
        Execute a unified knowledge query.

        Args:
            query: Search query string
            sources: List of sources (memory, rag)
            limit: Maximum results
            rerank: Apply MMR reranking
            diversity_lambda: MMR diversity parameter
            filters: Additional filters

        Returns:
            KnowledgeQueryResult with merged and reranked entries
        """
        if not self.knowledge_access:
            logger.warning(f"[{self.agent_id}] Knowledge access not initialized")
            return KnowledgeQueryResult(entries=[], total_results=0)

        return await self.knowledge_access.query(
            query=query,
            sources=sources or ["memory", "rag"],
            limit=limit,
            rerank=rerank,
            diversity_lambda=diversity_lambda,
            filters=filters or {},
        )

    async def store_memory(
        self,
        content: dict[str, Any],
        metadata: dict[str, Any] | None = None,
        ttl: int | None = None,
        persistent: bool = False,
        lineage: list[str] | None = None,
    ) -> MemoryEntry:
        """
        Store a memory.

        Args:
            content: Memory content
            metadata: Additional metadata
            ttl: Time to live in seconds
            persistent: Store in persistent tier
            lineage: Parent memory IDs

        Returns:
            Stored memory entry
        """
        # Add agent metadata
        # P2-1 fix: Use timezone-aware datetime
        full_metadata = {
            **(metadata or {}),
            "agent_id": self.agent_id,
            "stored_at": datetime.now(UTC).isoformat(),
        }

        entry = await self.memory_system.store(
            content=content,
            metadata=full_metadata,
            ttl=ttl,
            lineage=lineage,
            persistent=persistent,
        )

        logger.debug(f"[{self.agent_id}] Stored memory {entry.id}")

        return entry

    async def retrieve_context(
        self,
        topic: str,
        filters: dict[str, Any] | None = None,
        window_size: int = 10,
    ) -> list[dict[str, Any]]:
        """
        Retrieve context for a topic.

        Args:
            topic: Topic to retrieve context for
            filters: Additional filters
            window_size: Number of recent memories

        Returns:
            List of context entries
        """
        # Check cache first
        cache_key = f"{topic}:{window_size}"
        cached = self.context_cache.get(cache_key)
        if cached is not None:
            logger.debug(f"[{self.agent_id}] Context cache hit for: {topic}")
            return cached

        # Build query filters
        query_filters = filters or {}
        if topic:
            query_filters["topic"] = topic

        # Query memory
        results = await self.memory_system.query(
            filters=query_filters,
            limit=window_size,
        )

        # Update cache (with automatic LRU eviction)
        context = [
            {
                "content": e.content,
                "metadata": e.metadata,
                "created_at": e.created_at,
            }
            for e in results
        ]
        self.context_cache.set(cache_key, context)

        logger.debug(
            f"[{self.agent_id}] Retrieved {len(context)} context entries for: {topic} (cache size: {len(self.context_cache)})"
        )

        return context

    async def query_history(
        self,
        query_text: str | None = None,
        filters: dict[str, Any] | None = None,
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        """
        Query historical memories.

        Args:
            query_text: Text to search for
            filters: Metadata filters
            limit: Maximum results

        Returns:
            List of matching memories
        """
        results = await self.memory_system.query(
            query_text=query_text,
            filters=filters,
            limit=limit,
        )

        return [
            {
                "id": e.id,
                "content": e.content,
                "metadata": e.metadata,
                "created_at": e.created_at,
                "lineage": e.lineage,
            }
            for e in results
        ]

    async def track_decision_lineage(
        self,
        decision_id: str,
        parent_ids: list[str],
    ) -> None:
        """
        Track lineage for a decision.

        Args:
            decision_id: Decision identifier
            parent_ids: Parent memory/decision IDs
        """
        self.decision_lineage[decision_id] = parent_ids

        # Also store in memory
        await self.store_memory(
            content={
                "type": "lineage",
                "decision_id": decision_id,
                "parent_ids": parent_ids,
            },
            metadata={
                "lineage": True,
                "decision_id": decision_id,
            },
            persistent=True,
        )

        logger.debug(f"[{self.agent_id}] Tracked lineage for {decision_id}: {parent_ids}")

    async def get_lineage(self, decision_id: str) -> list[str]:
        """
        Get lineage for a decision.

        Args:
            decision_id: Decision identifier

        Returns:
            List of parent IDs
        """
        return self.decision_lineage.get(decision_id, [])

    async def match_patterns(
        self,
        situation: str,
        threshold: float = 0.7,
    ) -> list[dict[str, Any]]:
        """
        Match current situation against historical patterns.

        Args:
            situation: Current situation description
            threshold: Similarity threshold

        Returns:
            List of matched patterns
        """
        # Check cache first
        cached = self.pattern_cache.get(situation)
        if cached is not None:
            return cached

        matched = []

        # Query for similar situations
        results = await self.memory_system.query(
            query_text=situation,
            filters={"type": "situation"},
            limit=5,
        )

        for entry in results:
            # Compute actual similarity using text comparison
            similarity = self._compute_similarity(situation, str(entry.content))
            if similarity >= threshold:
                matched.append(
                    {
                        "situation": entry.content,
                        "metadata": entry.metadata,
                        "similarity": similarity,
                    }
                )

        # Cache results (with automatic LRU eviction)
        self.pattern_cache.set(situation, matched)

        logger.debug(
            f"[{self.agent_id}] Matched {len(matched)} patterns for: {situation} (cache size: {len(self.pattern_cache)})"
        )

        return matched

    def _compute_similarity(self, text1: str, text2: str) -> float:
        """
        Compute similarity between two texts using cosine similarity on character n-grams.

        Args:
            text1: First text
            text2: Second text

        Returns:
            Similarity score between 0.0 and 1.0
        """

        # Simple cosine similarity using character 2-grams
        def get_ngrams(text: str, n: int = 2) -> dict[str, int]:
            """Get character n-grams with frequencies."""
            text = text.lower().strip()
            ngrams = {}
            for i in range(len(text) - n + 1):
                ngram = text[i : i + n]
                ngrams[ngram] = ngrams.get(ngram, 0) + 1
            return ngrams

        def cosine_similarity(vec1: dict[str, int], vec2: dict[str, int]) -> float:
            """Compute cosine similarity between two frequency vectors."""
            # Get all unique keys
            all_keys = set(vec1.keys()) | set(vec2.keys())

            # Compute dot product and magnitudes
            dot_product = 0.0
            mag1 = 0.0
            mag2 = 0.0

            for key in all_keys:
                v1 = vec1.get(key, 0)
                v2 = vec2.get(key, 0)
                dot_product += v1 * v2
                mag1 += v1 * v1
                mag2 += v2 * v2

            if mag1 == 0 or mag2 == 0:
                return 0.0

            return dot_product / (mag1**0.5 * mag2**0.5)

        # Get n-grams for both texts
        ngrams1 = get_ngrams(text1)
        ngrams2 = get_ngrams(text2)

        return cosine_similarity(ngrams1, ngrams2)

    async def provide_deliberation_context(
        self,
        deliberation_id: str,
        topic: str,
    ) -> dict[str, Any]:
        """
        Provide comprehensive context for a deliberation.

        Args:
            deliberation_id: Deliberation identifier
            topic: Deliberation topic

        Returns:
            Context dictionary with relevant memories and patterns
        """
        logger.info(f"[{self.agent_id}] Providing context for deliberation: {deliberation_id}")

        # Retrieve relevant context
        context_entries = await self.retrieve_context(
            topic=topic,
            window_size=self.context_window,
        )

        # Match patterns
        patterns = await self.match_patterns(topic)

        # Get lineage if exists
        lineage = await self.get_lineage(deliberation_id)

        # P2-1 fix: Use timezone-aware datetime
        context = {
            "deliberation_id": deliberation_id,
            "topic": topic,
            "relevant_memories": context_entries,
            "matched_patterns": patterns,
            "lineage": lineage,
            "provided_at": datetime.now(UTC).isoformat(),
        }

        # Store context provision in memory
        await self.store_memory(
            content={
                "type": "context_provision",
                "deliberation_id": deliberation_id,
                "context": context,
            },
            metadata={
                "deliberation_id": deliberation_id,
                "topic": topic,
            },
            persistent=True,
        )

        return context

    async def synthesize_knowledge(
        self,
        topic: str,
        limit: int = 20,
        timeout: int = 60,
    ) -> dict[str, Any]:
        """
        Synthesize knowledge from historical executions.

        Args:
            topic: Topic to synthesize
            limit: Maximum memories to consider
            timeout: LLM call timeout in seconds (default: 60)

        Returns:
            Synthesized knowledge summary
        """
        logger.info(f"[{self.agent_id}] Synthesizing knowledge for: {topic}")

        # Retrieve relevant memories
        results = await self.memory_system.query(
            query_text=topic,
            limit=limit,
        )

        if not results:
            return {
                "topic": topic,
                "summary": "No relevant memories found",
                "confidence": 0.0,
            }

        # Synthesize (would use LLM in full implementation)
        if self.swarms_agent:
            try:
                memory_texts = [str(e.content) for e in results]
                synthesis_prompt = f"Synthesize knowledge from these memories: {memory_texts}"
                # P0-14 fix: Add timeout to LLM call
                synthesis = await self.run_with_llm(prompt=synthesis_prompt, timeout=timeout)

                # P2-1 fix: Use timezone-aware datetime
                return {
                    "topic": topic,
                    "summary": synthesis,
                    "source_count": len(results),
                    "confidence": 0.8,
                    "synthesized_at": datetime.now(UTC).isoformat(),
                }
            except TimeoutError:
                # P2-1 fix: Use timezone-aware datetime
                logger.error(f"[{self.agent_id}] Synthesis timed out after {timeout}s")
                return {
                    "topic": topic,
                    "summary": f"Synthesis timed out after {timeout}s",
                    "source_count": len(results),
                    "confidence": 0.0,
                    "error": "timeout",
                    "synthesized_at": datetime.now(UTC).isoformat(),
                }
            except Exception as e:
                logger.error(f"[{self.agent_id}] Synthesis error: {e}")

        # Fallback synthesis
        # P2-1 fix: Use timezone-aware datetime
        return {
            "topic": topic,
            "summary": f"Found {len(results)} relevant memories",
            "source_count": len(results),
            "confidence": 0.5,
            "synthesized_at": datetime.now(UTC).isoformat(),
        }

    def get_memory_statistics(self) -> dict[str, Any]:
        """Get memory system statistics."""
        memory_stats = self.memory_system.get_statistics()

        return {
            "total_memories": memory_stats.get("combined_total", 0),
            "decision_lineages": len(self.decision_lineage),
            "pattern_cache": self.pattern_cache.get_statistics(),
            "context_cache": self.context_cache.get_statistics(),
            "memory_details": memory_stats,
        }

    # Session 44: Collective Learning, Consensus Deliberation, and Memory Optimization
    # integration methods now provided by DeliberationMixin, LearningMixin, MemoryMixin, and PatternMixin.

    async def cleanup(self) -> None:
        """Cleanup resources."""
        await self.memory_system.close()
        logger.info(f"[{self.agent_id}] Historian cleanup complete")
