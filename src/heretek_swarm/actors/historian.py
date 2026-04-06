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

import asyncio
import logging
from collections import OrderedDict
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

import structlog
from swarms import Agent

from heretek_swarm.actors.base import AgentActor, ActorMessage
from heretek_swarm.memory.base import DualTierMemory, MemoryEntry, MemoryQuery

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
    
    def __contains__(self, key: str) -> bool:
        """Check if key is in cache."""
        return key in self._cache
    
    def __len__(self) -> int:
        """Return number of cached items."""
        return len(self._cache)
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get cache statistics."""
        total = self.hits + self.misses
        hit_rate = (self.hits / total * 100) if total > 0 else 0.0
        return {
            "size": len(self._cache),
            "max_size": self.max_size,
            "hits": self.hits,
            "misses": self.misses,
            "hit_rate_percent": round(hit_rate, 2),
        }


class HistorianAgent(AgentActor):
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
        swarms_agent: Optional[Agent] = None,
        memory_system: Optional[DualTierMemory] = None,
        context_window: int = 10,
        context_cache_max_size: int = 100,
        pattern_cache_max_size: int = 50,
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
        self.context_window = context_window

        # Historian-specific state with LRU caches
        self.decision_lineage: Dict[str, List[str]] = {}
        self.pattern_cache = LRUCache(max_size=pattern_cache_max_size)
        self.context_cache = LRUCache(max_size=context_cache_max_size)

        logger.info(f"[{self.agent_id}] Historian agent initialized")

    async def initialize(self) -> None:
        """Initialize the Historian agent."""
        # Initialize memory system
        await self.memory_system.initialize()

        # Register message handlers
        self.register_handler("store_memory", self._handle_store_memory)
        self.register_handler("retrieve_context", self._handle_retrieve_context)
        self.register_handler("query_history", self._handle_query_history)
        self.register_handler("track_lineage", self._handle_track_lineage)
        self.register_handler("pattern_match", self._handle_pattern_match)

        logger.info(f"[{self.agent_id}] Historian initialization complete")

    async def process_message(self, message: ActorMessage) -> None:
        """Process incoming messages."""
        handler = self._message_handlers.get(message.message_type)
        if handler:
            await handler(message)
        else:
            logger.warning(
                f"[{self.agent_id}] Unhandled message type: {message.message_type}"
            )

    async def _handle_store_memory(self, message: ActorMessage) -> None:
        """Handle memory storage requests."""
        content = message.content.get("content")
        metadata = message.content.get("metadata", {})
        ttl = message.content.get("ttl")
        persistent = message.content.get("persistent", False)

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
        """Handle context retrieval requests."""
        topic = message.content.get("topic")
        filters = message.content.get("filters", {})
        window_size = message.content.get("window_size", self.context_window)

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
        """Handle history query requests."""
        query_text = message.content.get("query_text")
        filters = message.content.get("filters", {})
        limit = message.content.get("limit", 10)

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
        """Handle lineage tracking requests."""
        decision_id = message.content.get("decision_id")
        parent_ids = message.content.get("parent_ids", [])

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
        """Handle pattern matching requests."""
        current_situation = message.content.get("situation")

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

    async def store_memory(
        self,
        content: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None,
        ttl: Optional[int] = None,
        persistent: bool = False,
        lineage: Optional[List[str]] = None,
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
        full_metadata = {
            **(metadata or {}),
            "agent_id": self.agent_id,
            "stored_at": datetime.utcnow().isoformat(),
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
        filters: Optional[Dict[str, Any]] = None,
        window_size: int = 10,
    ) -> List[Dict[str, Any]]:
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
        query_text: Optional[str] = None,
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
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
        parent_ids: List[str],
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

        logger.debug(
            f"[{self.agent_id}] Tracked lineage for {decision_id}: {parent_ids}"
        )

    async def get_lineage(self, decision_id: str) -> List[str]:
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
    ) -> List[Dict[str, Any]]:
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
            matched.append({
                "situation": entry.content,
                "metadata": entry.metadata,
                "similarity": 0.8,  # Would use actual similarity in full implementation
            })

        # Cache results (with automatic LRU eviction)
        self.pattern_cache.set(situation, matched)

        logger.debug(
            f"[{self.agent_id}] Matched {len(matched)} patterns for: {situation} (cache size: {len(self.pattern_cache)})"
        )

        return matched

    async def provide_deliberation_context(
        self,
        deliberation_id: str,
        topic: str,
    ) -> Dict[str, Any]:
        """
        Provide comprehensive context for a deliberation.

        Args:
            deliberation_id: Deliberation identifier
            topic: Deliberation topic

        Returns:
            Context dictionary with relevant memories and patterns
        """
        logger.info(
            f"[{self.agent_id}] Providing context for deliberation: {deliberation_id}"
        )

        # Retrieve relevant context
        context_entries = await self.retrieve_context(
            topic=topic,
            window_size=self.context_window,
        )

        # Match patterns
        patterns = await self.match_patterns(topic)

        # Get lineage if exists
        lineage = await self.get_lineage(deliberation_id)

        context = {
            "deliberation_id": deliberation_id,
            "topic": topic,
            "relevant_memories": context_entries,
            "matched_patterns": patterns,
            "lineage": lineage,
            "provided_at": datetime.utcnow().isoformat(),
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
    ) -> Dict[str, Any]:
        """
        Synthesize knowledge from historical executions.

        Args:
            topic: Topic to synthesize
            limit: Maximum memories to consider

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
                synthesis = await self.run_with_llm(prompt=synthesis_prompt)

                return {
                    "topic": topic,
                    "summary": synthesis,
                    "source_count": len(results),
                    "confidence": 0.8,
                    "synthesized_at": datetime.utcnow().isoformat(),
                }
            except Exception as e:
                logger.error(f"[{self.agent_id}] Synthesis error: {e}")

        # Fallback synthesis
        return {
            "topic": topic,
            "summary": f"Found {len(results)} relevant memories",
            "source_count": len(results),
            "confidence": 0.5,
            "synthesized_at": datetime.utcnow().isoformat(),
        }

    def get_memory_statistics(self) -> Dict[str, Any]:
        """Get memory system statistics."""
        memory_stats = self.memory_system.get_statistics()

        return {
            "total_memories": memory_stats.get("combined_total", 0),
            "decision_lineages": len(self.decision_lineage),
            "pattern_cache": self.pattern_cache.get_statistics(),
            "context_cache": self.context_cache.get_statistics(),
            "memory_details": memory_stats,
        }

    async def cleanup(self) -> None:
        """Cleanup resources."""
        await self.memory_system.close()
        logger.info(f"[{self.agent_id}] Historian cleanup complete")
