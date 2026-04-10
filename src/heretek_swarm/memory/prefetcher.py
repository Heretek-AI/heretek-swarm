"""
Intelligent Memory Pre-fetcher for Heretek Swarm

This module provides intelligent pre-fetching capabilities:
- Pre-fetch likely-needed memories based on access patterns
- LRU/LFU cache optimization
- Background pre-fetch scheduling
- Pre-fetch hit/miss tracking

Reference: EXPANSION_ROADMAP.md Session 43 - Memory Optimization
"""

import asyncio
import time
from collections import OrderedDict
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

import structlog

_logger = structlog.get_logger(__name__)


# =============================================================================
# Pre-fetch Types and Enums
# =============================================================================

class PreFetchStrategy(str, Enum):
    """Pre-fetching strategies."""
    LRU = "lru"              # Least Recently Used
    LFU = "lfu"              # Least Frequently Used
    PATTERN = "pattern"      # Pattern-based prediction
    AGENT = "agent"          # Agent behavior-based
    HYBRID = "hybrid"        # Combined strategy


class PreFetchPriority(str, Enum):
    """Pre-fetch priority levels."""
    CRITICAL = "critical"    # Highest priority, immediate
    HIGH = "high"            # High priority, next batch
    NORMAL = "normal"        # Standard priority
    LOW = "low"              # Low priority, background
    IDLE = "idle"            # Only when system idle


@dataclass
class PreFetchRequest:
    """
    A pre-fetch request.
    
    Attributes:
        memory_id: Memory identifier to pre-fetch
        priority: Pre-fetch priority
        reason: Reason for pre-fetch
        predicted_access_time: When memory is expected to be accessed
        confidence: Prediction confidence (0-1)
        strategy: Strategy that triggered this pre-fetch
        agent_id: Agent that may access this memory
        created_at: Request creation timestamp
    """
    memory_id: str
    priority: PreFetchPriority
    reason: str
    predicted_access_time: Optional[str] = None
    confidence: float = 0.0
    strategy: PreFetchStrategy = PreFetchStrategy.PATTERN
    agent_id: Optional[str] = None
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "memory_id": self.memory_id,
            "priority": self.priority.value,
            "reason": self.reason,
            "predicted_access_time": self.predicted_access_time,
            "confidence": self.confidence,
            "strategy": self.strategy.value,
            "agent_id": self.agent_id,
            "created_at": self.created_at,
        }


@dataclass
class PreFetchResult:
    """
    Result of a pre-fetch operation.
    
    Attributes:
        memory_id: Memory identifier
        success: Whether pre-fetch succeeded
        latency_ms: Time taken for pre-fetch
        cache_hit: Whether memory was already in cache
        strategy: Strategy used
        was_used: Whether the pre-fetched memory was actually accessed
    """
    memory_id: str
    success: bool
    latency_ms: float
    cache_hit: bool = False
    strategy: PreFetchStrategy = PreFetchStrategy.PATTERN
    was_used: bool = False
    error: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "memory_id": self.memory_id,
            "success": self.success,
            "latency_ms": self.latency_ms,
            "cache_hit": self.cache_hit,
            "strategy": self.strategy.value,
            "was_used": self.was_used,
            "error": self.error,
        }


@dataclass
class CacheStatistics:
    """
    Cache statistics for monitoring.
    
    Attributes:
        total_size: Current cache size
        max_size: Maximum cache size
        utilization: Cache utilization (0-1)
        hit_count: Total cache hits
        miss_count: Total cache misses
        hit_rate: Cache hit rate (0-1)
        pre_fetch_count: Total pre-fetches
        pre_fetch_hit_rate: Pre-fetch effectiveness
        eviction_count: Total evictions
        avg_latency_ms: Average access latency
    """
    total_size: int = 0
    max_size: int = 0
    utilization: float = 0.0
    hit_count: int = 0
    miss_count: int = 0
    hit_rate: float = 0.0
    pre_fetch_count: int = 0
    pre_fetch_hit_rate: float = 0.0
    eviction_count: int = 0
    avg_latency_ms: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "size": {
                "total": self.total_size,
                "max": self.max_size,
                "utilization": self.utilization,
            },
            "performance": {
                "hit_count": self.hit_count,
                "miss_count": self.miss_count,
                "hit_rate": self.hit_rate,
                "avg_latency_ms": self.avg_latency_ms,
            },
            "prefetch": {
                "count": self.pre_fetch_count,
                "hit_rate": self.pre_fetch_hit_rate,
            },
            "evictions": self.eviction_count,
        }


@dataclass
class LRUCacheEntry:
    """Entry in LRU cache with metadata."""
    memory_id: str
    data: Any
    access_count: int = 1
    last_access: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    size_bytes: int = 0


# =============================================================================
# LRU Cache Implementation
# =============================================================================

class LRUCache:
    """
    Least Recently Used (LRU) Cache with pre-fetch support.
    
    Features:
    - O(1) get and put operations
    - Automatic eviction when full
    - Access count tracking for LFU hybrid
    - Size-based eviction
    """
    
    def __init__(self, _max_size: int) -> None:
        """
        Initialize LRU cache.
        
        Args:
            max_size: Maximum number of entries
        """
        self.max_size = max_size
        self._cache: OrderedDict[str, LRUCacheEntry] = OrderedDict()
        self._hit_count = 0
        self._miss_count = 0
        self._eviction_count = 0
        self._total_latency_ms = 0.0
        
        logger.info(f"lru_cache_initialized", max_size=max_size)
    
    def get(self, _memory_id: str) -> Optional[Any]:
        """
        Get item from cache.
        
        Args:
            memory_id: Memory identifier
            
        Returns:
            Cached data or None
        """
        _start_time = time.time()
        
        if memory_id not in self._cache:
            self._miss_count += 1
            return None
        
        # Move to end (most recently used)
        self._cache.move_to_end(memory_id)
        _entry = self._cache[memory_id]
        entry.access_count += 1
        entry.last_access = datetime.now(timezone.utc).isoformat()
        
        self._hit_count += 1
        _latency_ms = (time.time() - start_time) * 1000
        self._total_latency_ms += latency_ms
        
        return entry.data
    
    def put(self, _memory_id: str, _data: Any, _size_bytes: int) -> Optional[str]:
        """
        Put item in cache.
        
        Args:
            memory_id: Memory identifier
            data: Data to cache
            size_bytes: Size in bytes
            
        Returns:
            Evicted memory_id if eviction occurred
        """
        _evicted = None
        
        if memory_id in self._cache:
            # Update existing
            self._cache.move_to_end(memory_id)
            _entry = self._cache[memory_id]
            entry.data = data
            entry.access_count += 1
            entry.last_access = datetime.now(timezone.utc).isoformat()
            entry.size_bytes = size_bytes
        else:
            # Add new
            if len(self._cache) >= self.max_size:
                # Evict least recently used
                evicted_id, _ = self._cache.popitem(last=False)
                _evicted = evicted_id
                self._eviction_count += 1
            
            _entry = LRUCacheEntry(
                _memory_id = memory_id,
                _data = data,
                _size_bytes = size_bytes,
            )
            self._cache[memory_id] = entry
        
        return evicted
    
    def remove(self, _memory_id: str) -> bool:
        """Remove item from cache."""
        if memory_id in self._cache:
            del self._cache[memory_id]
            return True
        return False
    
    def contains(self, _memory_id: str) -> bool:
        """Check if memory_id is in cache."""
        return memory_id in self._cache
    
    def clear(self) -> None:
        """Clear all entries."""
        self._cache.clear()
    
    def get_statistics(self) -> CacheStatistics:
        """Get cache statistics."""
        _total_ops = self._hit_count + self._miss_count
        _hit_rate = self._hit_count / total_ops if total_ops > 0 else 0.0
        _avg_latency = self._total_latency_ms / total_ops if total_ops > 0 else 0.0
        
        return CacheStatistics(
            _total_size = len(self._cache),
            max_size=self.max_size,
            _utilization = len(self._cache) / self.max_size if self.max_size > 0 else 0.0,
            _hit_count = self._hit_count,
            _miss_count = self._miss_count,
            _hit_rate = hit_rate,
            _eviction_count = self._eviction_count,
            _avg_latency_ms = avg_latency,
        )
    
    def get_entries_by_frequency(self) -> List[LRUCacheEntry]:
        """Get entries sorted by access frequency."""
        return sorted(
            self._cache.values(),
            key=lambda e: e.access_count,
            _reverse = True,
        )
    
    def get_least_recently_used(self, _count: int) -> List[str]:
        """Get least recently used memory IDs."""
        return list(self._cache.keys())[:count]


# =============================================================================
# LFU Cache Implementation
# =============================================================================

class LFUCache:
    """
    Least Frequently Used (LFU) Cache.
    
    Features:
    - Tracks access frequency
    - Evicts least frequently used on overflow
    - Handles frequency ties with LRU
    """
    
    def __init__(self, _max_size: int) -> None:
        """
        Initialize LFU cache.
        
        Args:
            max_size: Maximum number of entries
        """
        self.max_size = max_size
        self._cache: Dict[str, LRUCacheEntry] = {}
        self._frequency_map: Dict[int, OrderedDict[str, None]] = defaultdict(OrderedDict)
        self._min_frequency = 0
        self._hit_count = 0
        self._miss_count = 0
        self._eviction_count = 0
        
        logger.info(f"lfu_cache_initialized", max_size=max_size)
    
    def get(self, _memory_id: str) -> Optional[Any]:
        """Get item from cache with frequency update."""
        if memory_id not in self._cache:
            self._miss_count += 1
            return None
        
        _entry = self._cache[memory_id]
        _old_freq = entry.access_count
        
        # Remove from old frequency bucket
        self._frequency_map[old_freq].pop(memory_id)
        if not self._frequency_map[old_freq]:
            del self._frequency_map[old_freq]
            if self._min_frequency == old_freq:
                self._min_frequency += 1
        
        # Update frequency and add to new bucket
        entry.access_count += 1
        self._frequency_map[entry.access_count][memory_id] = None
        
        self._hit_count += 1
        
        return entry.data
    
    def put(self, _memory_id: str, _data: Any, _size_bytes: int) -> Optional[str]:
        """Put item in cache with frequency tracking."""
        _evicted = None
        
        if memory_id in self._cache:
            # Update existing
            _entry = self._cache[memory_id]
            _old_freq = entry.access_count
            self._frequency_map[old_freq].pop(memory_id)
            if not self._frequency_map[old_freq]:
                del self._frequency_map[old_freq]
            
            entry.data = data
            entry.access_count += 1
            entry.size_bytes = size_bytes
            self._cache[memory_id] = entry
            self._frequency_map[entry.access_count][memory_id] = None
            self._min_frequency = min(self._min_frequency, entry.access_count)
        else:
            # Add new
            if len(self._cache) >= self.max_size:
                # Evict least frequently used
                _lfu_bucket = self._frequency_map[self._min_frequency]
                evicted_id, _ = lfu_bucket.popitem(last=False)
                if not lfu_bucket:
                    del self._frequency_map[self._min_frequency]
                
                del self._cache[evicted_id]
                _evicted = evicted_id
                self._eviction_count += 1
            
            _entry = LRUCacheEntry(
                _memory_id = memory_id,
                _data = data,
                _size_bytes = size_bytes,
            )
            self._cache[memory_id] = entry
            self._frequency_map[1][memory_id] = None
            self._min_frequency = 1
        
        return evicted
    
    def get_statistics(self) -> CacheStatistics:
        """Get cache statistics."""
        _total_ops = self._hit_count + self._miss_count
        _hit_rate = self._hit_count / total_ops if total_ops > 0 else 0.0
        
        return CacheStatistics(
            _total_size = len(self._cache),
            max_size=self.max_size,
            _utilization = len(self._cache) / self.max_size if self.max_size > 0 else 0.0,
            _hit_count = self._hit_count,
            _miss_count = self._miss_count,
            _hit_rate = hit_rate,
            _eviction_count = self._eviction_count,
        )


# =============================================================================
# Pre-fetch Scheduler
# =============================================================================

@dataclass
class PreFetchSchedule:
    """Scheduled pre-fetch task."""
    memory_id: str
    scheduled_time: str
    priority: PreFetchPriority
    strategy: PreFetchStrategy
    agent_id: Optional[str] = None
    confidence: float = 0.0
    executed: bool = False
    result: Optional[PreFetchResult] = None


class PreFetchScheduler:
    """
    Background pre-fetch scheduler.
    
    Features:
    - Time-based scheduling
    - Priority queue management
    - Background execution
    - Rate limiting
    """
    
    def __init__(self, _max_pending: int, _max_concurrent: int, _rate_limit_per_second: float) -> None:
        """
        Initialize pre-fetch scheduler.
        
        Args:
            max_pending: Maximum pending pre-fetches
            max_concurrent: Maximum concurrent pre-fetches
            rate_limit_per_second: Rate limit for pre-fetches
        """
        self.max_pending = max_pending
        self.max_concurrent = max_concurrent
        self.rate_limit_per_second = rate_limit_per_second
        
        self._pending_queue: List[PreFetchSchedule] = []
        self._running_count = 0
        self._last_execution_time: Optional[datetime] = None
        self._executed_count = 0
        self._skipped_count = 0
        
        self._running = False
        self._task: Optional[asyncio.Task] = None
        
        logger.info(
            "prefetch_scheduler_initialized",
            max_pending=max_pending,
            max_concurrent=max_concurrent,
        )
    
    def schedule(self, _memory_id: str, _delay_seconds: float, _priority: PreFetchPriority, _strategy: PreFetchStrategy, _agent_id: Optional[str], _confidence: float) -> bool:
        """
        Schedule a pre-fetch.
        
        Args:
            memory_id: Memory to pre-fetch
            delay_seconds: Delay before execution
            priority: Pre-fetch priority
            strategy: Strategy used
            agent_id: Associated agent
            confidence: Prediction confidence
            
        Returns:
            True if scheduled successfully
        """
        if len(self._pending_queue) >= self.max_pending:
            logger.warning("prefetch_queue_full")
            self._skipped_count += 1
            return False
        
        scheduled_time = (
            datetime.now(timezone.utc) + timedelta(seconds=delay_seconds)
        ).isoformat()
        
        schedule = PreFetchSchedule(
            _memory_id = memory_id,
            scheduled_time=scheduled_time,
            _priority = priority,
            _strategy = strategy,
            _agent_id = agent_id,
            _confidence = confidence,
        )
        
        self._pending_queue.append(schedule)
        self._pending_queue.sort(
            key=lambda s: (
                self._priority_value(s.priority),
                s.scheduled_time,
                -s.confidence,
            )
        )
        
        return True
    
    def _priority_value(self, _priority: PreFetchPriority) -> int:
        """Convert priority to numeric value for sorting."""
        return {
            PreFetchPriority.CRITICAL: 0,
            PreFetchPriority.HIGH: 1,
            PreFetchPriority.NORMAL: 2,
            PreFetchPriority.LOW: 3,
            PreFetchPriority.IDLE: 4,
        }.get(priority, 2)
    
    async def start(self) -> None:
        """Start the background scheduler."""
        self._running = True
        self._task = asyncio.create_task(self._run_scheduler())
        logger.info("prefetch_scheduler_started")
    
    async def stop(self) -> None:
        """Stop the background scheduler."""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("prefetch_scheduler_stopped")
    
    async def _run_scheduler(self) -> None:
        """Background scheduler loop."""
        while self._running:
            try:
                await self._process_queue()
                await asyncio.sleep(0.1)  # 100ms tick
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("prefetch_scheduler_error", error=str(e))
                await asyncio.sleep(1.0)
    
    async def _process_queue(self) -> None:
        """Process pending pre-fetches."""
        now = datetime.now(timezone.utc)
        
        # Check rate limit
        if self._last_execution_time:
            _elapsed = (now - self._last_execution_time).total_seconds()
            _min_interval = 1.0 / self.rate_limit_per_second
            if elapsed < min_interval:
                return
        
        # Find ready pre-fetches
        _ready = []
        for schedule in self._pending_queue:
            if schedule.executed:
                continue
            
            _scheduled_time = datetime.fromisoformat(schedule.scheduled_time)
            if scheduled_time <= now:
                ready.append(schedule)
        
        # Execute ready pre-fetches up to concurrent limit
        for schedule in ready[:self.max_concurrent - self._running_count]:
            if self._running_count >= self.max_concurrent:
                break
            
            schedule.executed = True
            self._running_count += 1
            
            # Execute asynchronously
            asyncio.create_task(self._execute_prefetch(schedule))
        
        # Clean up executed from queue
        self._pending_queue = [s for s in self._pending_queue if not s.executed]
    
    async def _execute_prefetch(self, _schedule: PreFetchSchedule) -> None:
        """Execute a single pre-fetch."""
        try:
            # This would be called by the main Prefetcher
            # For now, just track execution
            self._executed_count += 1
            self._last_execution_time = datetime.now(timezone.utc)
            self._running_count -= 1
            
            logger.debug(
                "prefetch_executed",
                _memory_id = schedule.memory_id,
                _priority = schedule.priority.value,
            )
        except Exception as e:
            logger.error("prefetch_execution_error", error=str(e))
            self._running_count -= 1
    
    def get_stats(self) -> Dict[str, Any]:
        """Get scheduler statistics."""
        return {
            "pending_count": len(self._pending_queue),
            "running_count": self._running_count,
            "executed_count": self._executed_count,
            "skipped_count": self._skipped_count,
            "rate_limit": self.rate_limit_per_second,
        }


# =============================================================================
# Intelligent Pre-fetcher
# =============================================================================

class IntelligentPrefetcher:
    """
    Intelligent Memory Pre-fetcher
    
    Combines multiple strategies for optimal pre-fetching:
    - LRU/LFU cache optimization
    - Pattern-based prediction
    - Agent behavior analysis
    - Background scheduling
    
    Features:
    - Configurable cache sizes
    - Multiple pre-fetch strategies
    - Hit/miss tracking
    - Adaptive pre-fetching
    """
    
    def __init__(self, _cache_size: int, _prefetch_threshold: float, _strategy: PreFetchStrategy, _enable_background: bool) -> None:
        """
        Initialize the intelligent pre-fetcher.
        
        Args:
            cache_size: Maximum cache size
            prefetch_threshold: Confidence threshold for pre-fetching
            strategy: Default pre-fetch strategy
            enable_background: Enable background scheduling
        """
        self.cache_size = cache_size
        self.prefetch_threshold = prefetch_threshold
        self.default_strategy = strategy
        
        # Cache layers
        self._lru_cache = LRUCache(max_size=cache_size)
        self._lfu_cache = LFUCache(max_size=cache_size // 2)
        
        # Pre-fetch tracking
        self._prefetch_requests: List[PreFetchRequest] = []
        self._prefetch_results: List[PreFetchResult] = []
        self._prefetch_hits = 0
        self._prefetch_misses = 0
        
        # Memory access patterns (for pattern-based pre-fetching)
        self._access_patterns: Dict[str, List[str]] = defaultdict(list)
        self._sequential_access_window = 10
        
        # Scheduler
        self._scheduler = PreFetchScheduler() if enable_background else None
        self._scheduler_running = False
        
        # Statistics
        self._total_accesses = 0
        self._total_latency_ms = 0.0
        
        logger.info(
            "intelligent_prefetcher_initialized",
            _cache_size = cache_size,
            _strategy = strategy.value,
        )
    
    async def initialize(self) -> None:
        """Initialize the pre-fetcher."""
        if self._scheduler and not self._scheduler_running:
            await self._scheduler.start()
            self._scheduler_running = True
        logger.info("intelligent_prefetcher_initialized")
    
    async def shutdown(self) -> None:
        """Shutdown the pre-fetcher."""
        if self._scheduler and self._scheduler_running:
            await self._scheduler.stop()
            self._scheduler_running = False
        logger.info("intelligent_prefetcher_shutdown")
    
    def record_access(self, _memory_id: str, _agent_id: Optional[str]) -> Tuple[bool, float]:
        """
        Record a memory access and trigger pre-fetching.
        
        Args:
            memory_id: Accessed memory ID
            agent_id: Accessing agent ID
            
        Returns:
            Tuple of (cache_hit, latency_ms)
        """
        _start_time = time.time()
        
        # Check cache
        _cache_hit = self._lru_cache.contains(memory_id)
        
        if cache_hit:
            _data = self._lru_cache.get(memory_id)
            self._lru_cache.put(memory_id, data)  # Update LRU
        else:
            self._lru_cache.put(memory_id, None)  # Placeholder
        
        self._total_accesses += 1
        _latency_ms = (time.time() - start_time) * 1000
        self._total_latency_ms += latency_ms
        
        # Update access patterns
        self._update_access_pattern(memory_id, agent_id)
        
        # Trigger pre-fetching
        if cache_hit:
            self._trigger_prefetch(memory_id, agent_id)
        
        return cache_hit, latency_ms
    
    def _update_access_pattern(self, _memory_id: str, _agent_id: Optional[str]) -> None:
        """Update access pattern tracking."""
        # Track sequential access patterns
        for key in list(self._access_patterns.keys()):
            _pattern = self._access_patterns[key]
            if len(pattern) >= self._sequential_access_window:
                pattern.pop(0)
        
        if agent_id:
            self._access_patterns[agent_id].append(memory_id)
    
    def _trigger_prefetch(self, _accessed_memory_id: str, _agent_id: Optional[str]) -> None:
        """Trigger pre-fetching based on access patterns."""
        # Pattern-based pre-fetch
        if agent_id and len(self._access_patterns[agent_id]) >= 2:
            _pattern = self._access_patterns[agent_id]
            
            # Predict next memory based on sequential pattern
            _predicted = self._predict_next_memory(pattern)
            
            if predicted and not self._lru_cache.contains(predicted):
                self._request_prefetch(
                    _memory_id = predicted,
                    _priority = PreFetchPriority.NORMAL,
                    _strategy = PreFetchStrategy.PATTERN,
                    _agent_id = agent_id,
                    _confidence = 0.7,
                    _reason = f"Sequential pattern prediction after {accessed_memory_id}",
                )
        
        # Agent-based pre-fetch
        if agent_id:
            # Pre-fetch other memories commonly accessed by this agent
            _agent_memories = set(self._access_patterns[agent_id])
            for related_memory in agent_memories:
                if not self._lru_cache.contains(related_memory):
                    self._request_prefetch(
                        _memory_id = related_memory,
                        _priority = PreFetchPriority.LOW,
                        _strategy = PreFetchStrategy.AGENT,
                        _agent_id = agent_id,
                        _confidence = 0.5,
                        _reason = f"Agent {agent_id} frequently accesses",
                    )
    
    def _predict_next_memory(self, _pattern: List[str]) -> Optional[str]:
        """Predict next memory based on access pattern."""
        if len(pattern) < 2:
            return None
        
        # Simple prediction: most common next memory
        _next_memories = []
        for i in range(len(pattern) - 1):
            if pattern[i] == pattern[-1]:
                next_memories.append(pattern[i + 1])
        
        if not next_memories:
            return None
        
        # Return most common next memory
        from collections import Counter
        _counter = Counter(next_memories)
        return counter.most_common(1)[0][0]
    
    def _request_prefetch(self, _memory_id: str, _priority: PreFetchPriority, _strategy: PreFetchStrategy, _agent_id: Optional[str], _confidence: float, _reason: str) -> None:
        """Request a pre-fetch."""
        _request = PreFetchRequest(
            _memory_id = memory_id,
            _priority = priority,
            _reason = reason,
            _confidence = confidence,
            _strategy = strategy,
            _agent_id = agent_id,
        )
        
        self._prefetch_requests.append(request)
        
        # Limit request history
        if len(self._prefetch_requests) > 1000:
            self._prefetch_requests = self._prefetch_requests[-1000:]
        
        # Schedule if background enabled
        if self._scheduler and confidence >= self.prefetch_threshold:
            _delay = {
                PreFetchPriority.CRITICAL: 0.0,
                PreFetchPriority.HIGH: 0.5,
                PreFetchPriority.NORMAL: 1.0,
                PreFetchPriority.LOW: 5.0,
                PreFetchPriority.IDLE: 30.0,
            }.get(priority, 1.0)
            
            self._scheduler.schedule(
                _memory_id = memory_id,
                _delay_seconds = delay,
                _priority = priority,
                _strategy = strategy,
                _agent_id = agent_id,
                _confidence = confidence,
            )
    
    def prefetch(self, _memory_id: str, _data: Any, _size_bytes: int) -> PreFetchResult:
        """
        Pre-fetch memory data into cache.
        
        Args:
            memory_id: Memory identifier
            data: Data to cache
            size_bytes: Data size in bytes
            
        Returns:
            Pre-fetch result
        """
        _start_time = time.time()
        
        _cache_hit = self._lru_cache.contains(memory_id)
        _evicted = self._lru_cache.put(memory_id, data, size_bytes)
        
        # Also add to LFU for hybrid strategy
        self._lfu_cache.put(memory_id, data, size_bytes)
        
        _latency_ms = (time.time() - start_time) * 1000
        
        _result = PreFetchResult(
            _memory_id = memory_id,
            _success = True,
            _latency_ms = latency_ms,
            _cache_hit = cache_hit,
        )
        
        self._prefetch_results.append(result)
        if len(self._prefetch_results) > 1000:
            self._prefetch_results = self._prefetch_results[-1000:]
        
        if cache_hit:
            self._prefetch_hits += 1
        else:
            self._prefetch_misses += 1
        
        return result
    
    def get(self, _memory_id: str) -> Optional[Any]:
        """Get memory from cache."""
        return self._lru_cache.get(memory_id)
    
    def contains(self, _memory_id: str) -> bool:
        """Check if memory is in cache."""
        return self._lru_cache.contains(memory_id)
    
    def evict(self, _memory_id: str) -> bool:
        """Evict memory from cache."""
        _removed_lru = self._lru_cache.remove(memory_id)
        self._lfu_cache.get(memory_id)  # This won't remove but access tracking
        return removed_lru
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get comprehensive statistics."""
        _lru_stats = self._lru_cache.get_statistics()
        _lfu_stats = self._lfu_cache.get_statistics()
        
        _total_prefetch = self._prefetch_hits + self._prefetch_misses
        _prefetch_hit_rate = (
            self._prefetch_hits / total_prefetch if total_prefetch > 0 else 0.0
        )
        
        _avg_latency = (
            self._total_latency_ms / self._total_accesses
            if self._total_accesses > 0 else 0.0
        )
        
        _scheduler_stats = self._scheduler.get_stats() if self._scheduler else {}
        
        return {
            "lru_cache": lru_stats.to_dict(),
            "lfu_cache": lfu_stats.to_dict(),
            "prefetch": {
                "total_requests": len(self._prefetch_requests),
                "total_results": len(self._prefetch_results),
                "hits": self._prefetch_hits,
                "misses": self._prefetch_misses,
                "hit_rate": prefetch_hit_rate,
            },
            "access": {
                "total_accesses": self._total_accesses,
                "avg_latency_ms": avg_latency,
            },
            "scheduler": scheduler_stats,
        }
    
    def get_prefetch_recommendations(self) -> List[PreFetchRequest]:
        """Get pre-fetch recommendations based on current patterns."""
        _recommendations = []
        
        # Find memories that should be pre-fetched
        for agent_id, pattern in self._access_patterns.items():
            if len(pattern) >= 2:
                _predicted = self._predict_next_memory(pattern)
                if predicted and not self._lru_cache.contains(predicted):
                    recommendations.append(
                        PreFetchRequest(
                            _memory_id = predicted,
                            _priority = PreFetchPriority.NORMAL,
                            _reason = f"Predicted next access for agent {agent_id}",
                            _confidence = 0.7,
                            _strategy = PreFetchStrategy.PATTERN,
                            _agent_id = agent_id,
                        )
                    )
        
        return recommendations[:20]  # Limit recommendations
    
    def clear(self) -> None:
        """Clear all caches and tracking."""
        self._lru_cache.clear()
        self._lfu_cache._cache.clear()
        self._access_patterns.clear()
        self._prefetch_requests.clear()
        self._prefetch_results.clear()
        logger.info("intelligent_prefetcher_cleared")


# Import defaultdict for frequency map
from collections import defaultdict
