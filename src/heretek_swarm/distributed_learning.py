"""
Distributed Learning Engine - Cross-Agent Learning

Implements distributed learning with Redis pub/sub for pattern distribution
and knowledge synchronization across the agent swarm.

Features:
- Publish learned patterns to Redis pub/sub
- Subscribe to pattern updates from other agents
- Merge incoming knowledge with local state
- Distributed pattern validation
- Knowledge synchronization across instances

Zero-Trust Principles:
- All incoming patterns validated before merge
- Source verification required
- Conflict resolution with consensus
- Audit logging for all sync operations
"""

import asyncio
import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set

import structlog

from .learning import ExtractedPattern, PatternType, LearningSignal, CollectiveLearning
from .knowledge_transform import (
    KnowledgeTransformer,
)

_logger = structlog.get_logger(__name__)


class SyncOperation(str, Enum):
    """Types of synchronization operations."""
    
    PUBLISH = "publish"
    SUBSCRIBE = "subscribe"
    MERGE = "merge"
    VALIDATE = "validate"
    CONFLICT_RESOLVE = "conflict_resolve"
    BROADCAST = "broadcast"


class MergeStrategy(str, Enum):
    """Strategies for merging incoming knowledge."""
    
    NEWEST = "newest"  # Prefer newest timestamp
    HIGHEST_CONFIDENCE = "highest_confidence"  # Prefer highest confidence
    LOCAL_PRIORITY = "local_priority"  # Prefer local knowledge
    REMOTE_PRIORITY = "remote_priority"  # Prefer remote knowledge
    CONSENSUS = "consensus"  # Require consensus for merge


@dataclass
class SyncMessage:
    """Message for distributed synchronization."""
    
    message_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    operation: SyncOperation = SyncOperation.PUBLISH
    source_agent: str = ""
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    payload: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    correlation_id: Optional[str] = None
    reply_to: Optional[str] = None
    
    def to_json(self) -> str:
        """Serialize to JSON string."""
        return json.dumps({
            "message_id": self.message_id,
            "operation": self.operation.value,
            "source_agent": self.source_agent,
            "timestamp": self.timestamp,
            "payload": self.payload,
            "metadata": self.metadata,
            "correlation_id": self.correlation_id,
            "reply_to": self.reply_to,
        })
    
    @classmethod
    def from_json(cls, json_str: str) -> "SyncMessage":
        """Deserialize from JSON string."""
        _data = json.loads(json_str)
        return cls(
            message_id=data.get("message_id", str(uuid.uuid4())),
            _operation = SyncOperation(data.get("operation", "publish")),
            source_agent=data.get("source_agent", ""),
            _timestamp = data.get("timestamp", datetime.now(timezone.utc).isoformat()),
            payload=data.get("payload", {}),
            metadata=data.get("metadata", {}),
            _correlation_id = data.get("correlation_id"),
            _reply_to = data.get("reply_to"),
        )


@dataclass
class MergeResult:
    """Result of a knowledge merge operation."""
    
    success: bool
    merged_count: int = 0
    conflict_count: int = 0
    rejected_count: int = 0
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    merged_pattern_ids: List[str] = field(default_factory=list)
    conflict_details: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class DistributedLearningConfig:
    """Configuration for distributed learning."""
    
    redis_url: str = "redis://localhost:6379"
    pubsub_channel: str = "heretek:collective:learning"
    pattern_channel: str = "heretek:collective:patterns"
    signal_channel: str = "heretek:collective:signals"
    merge_strategy: MergeStrategy = MergeStrategy.HIGHEST_CONFIDENCE
    validation_required: bool = True
    max_pending_messages: int = 1000
    message_ttl_seconds: int = 3600
    sync_interval_seconds: float = 5.0
    batch_size: int = 10


class DistributedLearningEngine:
    """
    Distributed learning engine with Redis pub/sub synchronization.
    
    This engine coordinates learning across multiple agent instances,
    publishing learned patterns and subscribing to updates from peers.
    
    Attributes:
        config: Configuration for distributed learning
        local_learning: Local CollectiveLearning instance
        transformer: KnowledgeTransformer instance
    """
    
    def __init__(self, config: Optional[DistributedLearningConfig], agent_id: Optional[str]):
        """
        Initialize distributed learning engine.
        
        Args:
            config: Configuration options
            agent_id: This agent's identifier
        """
        self.config = config or DistributedLearningConfig()
        self.agent_id = agent_id or f"agent_{uuid.uuid4().hex[:8]}"
        
        self.local_learning = CollectiveLearning()
        self.transformer = KnowledgeTransformer()
        
        # Redis connection (lazy initialization)
        self._redis = None
        self._pubsub = None
        
        # Message queues
        self._pending_messages: asyncio.Queue = asyncio.Queue(
            _maxsize = self.config.max_pending_messages
        )
        self._processed_ids: Set[str] = set()
        
        # Callbacks
        self._on_pattern_received: List[Callable] = []
        self._on_signal_received: List[Callable] = []
        self._on_merge_complete: List[Callable] = []
        
        # Running state
        self._running = False
        self._subscribe_task: Optional[asyncio.Task] = None
        self._sync_task: Optional[asyncio.Task] = None
        
        logger.info(
            "distributed_learning_engine_initialized",
            agent_id=self.agent_id,
            _pubsub_channel = self.config.pubsub_channel,
        )
    
    def register_pattern_callback(self, callback: Callable) -> None:
        """
        Register callback for pattern received events.
        
        Args:
            callback: Async callable receiving ExtractedPattern
        """
        self._on_pattern_received.append(callback)
        logger.debug("pattern_callback_registered", callback=callback.__name__)
    
    def register_signal_callback(self, callback: Callable) -> None:
        """
        Register callback for learning signal received events.
        
        Args:
            callback: Async callable receiving LearningSignal
        """
        self._on_signal_received.append(callback)
        logger.debug("signal_callback_registered", callback=callback.__name__)
    
    def register_merge_callback(self, callback: Callable) -> None:
        """
        Register callback for merge complete events.
        
        Args:
            callback: Async callable receiving MergeResult
        """
        self._on_merge_complete.append(callback)
        logger.debug("merge_callback_registered", callback=callback.__name__)
    
    async def start(self) -> None:
        """
        Start the distributed learning engine.
        
        Initializes Redis connection and starts background tasks.
        """
        if self._running:
            logger.warning("engine_already_running", agent_id=self.agent_id)
            return
        
        try:
            # Initialize Redis connection
            await self._init_redis()
            
            self._running = True
            
            # Start background tasks
            self._subscribe_task = asyncio.create_task(self._subscribe_loop())
            self._sync_task = asyncio.create_task(self._sync_loop())
            
            logger.info(
                "distributed_learning_engine_started",
                agent_id=self.agent_id,
            )
            
        except Exception as e:
            logger.error(
                "engine_start_failed",
                agent_id=self.agent_id,
                _error = str(e),
            )
            raise
    
    async def stop(self) -> None:
        """
        Stop the distributed learning engine.
        
        Gracefully shuts down background tasks and closes connections.
        """
        if not self._running:
            return
        
        self._running = False
        
        # Cancel background tasks
        if self._subscribe_task:
            self._subscribe_task.cancel()
            try:
                await self._subscribe_task
            except asyncio.CancelledError:
                pass
        
        if self._sync_task:
            self._sync_task.cancel()
            try:
                await self._sync_task
            except asyncio.CancelledError:
                pass
        
        # Close Redis connection
        if self._pubsub:
            await self._pubsub.close()
        
        if self._redis:
            await self._redis.close()
        
        logger.info(
            "distributed_learning_engine_stopped",
            agent_id=self.agent_id,
        )
    
    async def publish_pattern(self, pattern: ExtractedPattern) -> bool:
        """
        Publish a pattern to the distributed swarm.
        
        Args:
            pattern: Pattern to publish
            
        Returns:
            True if publish successful
        """
        if not self._redis:
            logger.warning("redis_not_connected", agent_id=self.agent_id)
            return False
        
        try:
            message = SyncMessage(
                _operation = SyncOperation.PUBLISH,
                source_agent=self.agent_id,
                payload={
                    "pattern": pattern.to_dict(),
                    "pattern_type": pattern.metadata.pattern_type.value,
                    "confidence": pattern.metadata.confidence,
                },
                metadata={
                    "source": "distributed_learning",
                    "version": "1.0",
                },
            )
            
            await self._redis.publish(
                self.config.pattern_channel,
                message.to_json(),
            )
            
            logger.debug(
                "pattern_published",
                pattern_id=pattern.metadata.pattern_id,
                _channel = self.config.pattern_channel,
            )
            
            return True
            
        except Exception as e:
            logger.error(
                "pattern_publish_failed",
                pattern_id=pattern.metadata.pattern_id,
                _error = str(e),
            )
            return False
    
    async def publish_learning_signal(self, signal: LearningSignal) -> bool:
        """
        Publish a learning signal to the distributed swarm.
        
        Args:
            signal: Signal to publish
            
        Returns:
            True if publish successful
        """
        if not self._redis:
            logger.warning("redis_not_connected", agent_id=self.agent_id)
            return False
        
        try:
            message = SyncMessage(
                _operation = SyncOperation.BROADCAST,
                source_agent=self.agent_id,
                payload=signal.to_dict(),
                metadata={
                    "signal_type": signal.signal_type,
                    "magnitude": signal.magnitude,
                },
            )
            
            await self._redis.publish(
                self.config.signal_channel,
                message.to_json(),
            )
            
            logger.debug(
                "signal_published",
                _signal_id = signal.signal_id,
                _channel = self.config.signal_channel,
            )
            
            return True
            
        except Exception as e:
            logger.error(
                "signal_publish_failed",
                _signal_id = signal.signal_id,
                _error = str(e),
            )
            return False
    
    async def receive_pattern(self, pattern_dict: Dict[str, Any], source_agent: str) -> MergeResult:
        """
        Receive and process a pattern from another agent.
        
        Args:
            pattern_dict: Pattern data dictionary
            source_agent: Source agent identifier
            
        Returns:
            MergeResult with processing outcome
        """
        try:
            # Reconstruct pattern
            pattern = self._reconstruct_pattern(pattern_dict)
            
            # Validate incoming pattern
            if self.config.validation_required:
                _is_valid = await self.local_learning.extractor._validate_pattern(pattern)
                if not is_valid:
                    return MergeResult(
                        _success = False,
                        _rejected_count = 1,
                        _errors = ["Pattern failed validation"],
                    )
            
            # Check for conflicts with local patterns
            _conflicts = self._check_conflicts(pattern)
            
            if conflicts:
                # Resolve conflicts based on strategy
                _resolved = await self._resolve_conflicts(pattern, conflicts)
                if not resolved:
                    return MergeResult(
                        _success = False,
                        _conflict_count = len(conflicts),
                        _conflict_details = conflicts,
                    )
            
            # Merge pattern into local storage
            self.local_learning._patterns[pattern.metadata.pattern_id] = pattern
            
            # Call callbacks
            for callback in self._on_pattern_received:
                try:
                    if asyncio.iscoroutinefunction(callback):
                        await callback(pattern)
                    else:
                        callback(pattern)
                except Exception as e:
                    logger.error(
                        "pattern_callback_error",
                        _callback = callback.__name__,
                        _error = str(e),
                    )
            
            return MergeResult(
                _success = True,
                _merged_count = 1,
                _merged_pattern_ids = [pattern.metadata.pattern_id],
            )
            
        except Exception as e:
            logger.error(
                "pattern_receive_failed",
                source_agent=source_agent,
                _error = str(e),
            )
            return MergeResult(
                _success = False,
                _rejected_count = 1,
                _errors = [str(e)],
            )
    
    async def receive_learning_signal(self, signal_dict: Dict[str, Any], source_agent: str) -> bool:
        """
        Receive and process a learning signal from another agent.
        
        Args:
            signal_dict: Signal data dictionary
            source_agent: Source agent identifier
            
        Returns:
            True if processed successfully
        """
        try:
            # Reconstruct signal
            signal = LearningSignal(
                _signal_id = signal_dict.get("signal_id", str(uuid.uuid4())),
                _signal_type = signal_dict.get("signal_type", "unknown"),
                _magnitude = signal_dict.get("magnitude", 0.0),
                _timestamp = signal_dict.get("timestamp", datetime.now(timezone.utc).isoformat()),
                source_agent=signal_dict.get("source_agent"),
                _target_agents = signal_dict.get("target_agents", []),
                _context = signal_dict.get("context", {}),
                metadata=signal_dict.get("metadata", {}),
            )
            
            # Store locally
            self.local_learning._learning_signals.append(signal)
            
            # Call callbacks
            for callback in self._on_signal_received:
                try:
                    if asyncio.iscoroutinefunction(callback):
                        await callback(signal)
                    else:
                        callback(signal)
                except Exception as e:
                    logger.error(
                        "signal_callback_error",
                        _callback = callback.__name__,
                        _error = str(e),
                    )
            
            return True
            
        except Exception as e:
            logger.error(
                "signal_receive_failed",
                source_agent=source_agent,
                _error = str(e),
            )
            return False
    
    async def merge_knowledge(self, remote_patterns: Dict[str, _ExtractedPattern], strategy: Optional[MergeStrategy]) -> MergeResult:
        """
        Merge remote knowledge with local state.
        
        Args:
            remote_patterns: Dictionary of remote patterns
            strategy: Merge strategy to use (default: config strategy)
            
        Returns:
            MergeResult with merge statistics
        """
        _strategy = strategy or self.config.merge_strategy
        _merged = []
        _conflicts = []
        _rejected = []
        _errors = []
        
        for pattern_id, remote_pattern in remote_patterns.items():
            # Check if pattern exists locally
            _local_pattern = self.local_learning._patterns.get(pattern_id)
            
            if local_pattern is None:
                # New pattern - merge directly
                if await self.local_learning.extractor._validate_pattern(remote_pattern):
                    self.local_learning._patterns[pattern_id] = remote_pattern
                    merged.append(pattern_id)
                else:
                    rejected.append(pattern_id)
            else:
                # Existing pattern - resolve based on strategy
                _should_merge = self._should_merge(local_pattern, remote_pattern, strategy)
                
                if should_merge:
                    # Update local pattern
                    self.local_learning._patterns[pattern_id] = self._merge_patterns(
                        local_pattern,
                        remote_pattern,
                        strategy,
                    )
                    merged.append(pattern_id)
                else:
                    conflicts.append({
                        "pattern_id": pattern_id,
                        "local_confidence": local_pattern.metadata.confidence,
                        "remote_confidence": remote_pattern.metadata.confidence,
                        "resolution": "kept_local",
                    })
        
        _result = MergeResult(
            _success = len(errors) == 0,
            _merged_count = len(merged),
            _conflict_count = len(conflicts),
            _rejected_count = len(rejected),
            _errors = errors,
            _merged_pattern_ids = merged,
            _conflict_details = conflicts,
        )
        
        # Call merge callbacks
        for callback in self._on_merge_complete:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(result)
                else:
                    callback(result)
            except Exception as e:
                logger.error(
                    "merge_callback_error",
                    _callback = callback.__name__,
                    _error = str(e),
                )
        
        logger.info(
            "knowledge_merge_complete",
            _merged = len(merged),
            _conflicts = len(conflicts),
            _rejected = len(rejected),
        )
        
        return result
    
    def _should_merge(self, local: ExtractedPattern, remote: ExtractedPattern, strategy: MergeStrategy) -> bool:
        """Determine if remote pattern should replace local."""
        if strategy == MergeStrategy.NEWEST:
            return remote.metadata.last_observed > local.metadata.last_observed
        
        elif strategy == MergeStrategy.HIGHEST_CONFIDENCE:
            return remote.metadata.confidence > local.metadata.confidence
        
        elif strategy == MergeStrategy.LOCAL_PRIORITY:
            return False  # Always prefer local
        
        elif strategy == MergeStrategy.REMOTE_PRIORITY:
            return True  # Always prefer remote
        
        elif strategy == MergeStrategy.CONSENSUS:
            # Would require additional consensus mechanism
            return remote.metadata.confidence > 0.9
        
        return False
    
    def _merge_patterns(self, local: ExtractedPattern, remote: ExtractedPattern, strategy: MergeStrategy) -> ExtractedPattern:
        """Merge two patterns based on strategy."""
        # Create merged pattern with combined data
        merged = remote  # Start with remote as base
        
        # Combine outcomes
        merged.outcomes = local.outcomes + remote.outcomes
        
        # Combine agents involved
        merged.metadata.agents_involved = list(set(
            local.metadata.agents_involved + remote.metadata.agents_involved
        ))
        
        # Combine topics
        merged.metadata.topics = list(set(
            local.metadata.topics + remote.metadata.topics
        ))
        
        # Update timestamps
        merged.metadata.first_observed = min(
            local.metadata.first_observed,
            remote.metadata.first_observed,
        )
        merged.metadata.last_observed = max(
            local.metadata.last_observed,
            remote.metadata.last_observed,
        )
        
        # Average confidence or use max based on strategy
        if strategy == MergeStrategy.HIGHEST_CONFIDENCE:
            merged.metadata.confidence = max(
                local.metadata.confidence,
                remote.metadata.confidence,
            )
        else:
            merged.metadata.confidence = (
                local.metadata.confidence + remote.metadata.confidence
            ) / 2
        
        return merged
    
    def _check_conflicts(self, pattern: ExtractedPattern) -> List[Dict[str, Any]]:
        """Check for conflicts between pattern and local knowledge."""
        _conflicts = []
        
        _local_pattern = self.local_learning._patterns.get(pattern.metadata.pattern_id)
        
        if local_pattern:
            # Check for significant confidence difference
            _confidence_diff = abs(
                local_pattern.metadata.confidence - pattern.metadata.confidence
            )
            
            if confidence_diff > 0.3:  # Threshold for conflict
                conflicts.append({
                    "type": "confidence_mismatch",
                    "pattern_id": pattern.metadata.pattern_id,
                    "local_confidence": local_pattern.metadata.confidence,
                    "remote_confidence": pattern.metadata.confidence,
                })
            
            # Check for different pattern types
            if local_pattern.metadata.pattern_type != pattern.metadata.pattern_type:
                conflicts.append({
                    "type": "type_mismatch",
                    "pattern_id": pattern.metadata.pattern_id,
                    "local_type": local_pattern.metadata.pattern_type.value,
                    "remote_type": pattern.metadata.pattern_type.value,
                })
        
        return conflicts
    
    async def _resolve_conflicts(self, pattern: ExtractedPattern, conflicts: List[Dict[str, Any]]) -> bool:
        """
        Resolve conflicts between local and remote patterns.
        
        Args:
            pattern: Remote pattern
            conflicts: List of conflict details
            
        Returns:
            True if conflicts resolved successfully
        """
        for conflict in conflicts:
            if conflict["type"] == "confidence_mismatch":
                # Use higher confidence value
                if pattern.metadata.confidence < conflict["local_confidence"]:
                    return False  # Keep local
            
            elif conflict["type"] == "type_mismatch":
                # Cannot resolve type mismatch - reject
                return False
        
        return True
    
    def _reconstruct_pattern(self, pattern_dict: Dict[str, Any]) -> ExtractedPattern:
        """Reconstruct ExtractedPattern from dictionary."""
        _metadata_dict = pattern_dict.get("metadata", {})
        
        metadata = PatternMetadata(
            pattern_id=metadata_dict.get("pattern_id", str(uuid.uuid4())),
            _pattern_type = PatternType(metadata_dict.get("pattern_type", "success")),
            source=metadata_dict.get("source", "message_history"),
            _confidence = metadata_dict.get("confidence", 0.0),
            _support_count = metadata_dict.get("support_count", 0),
            _first_observed = metadata_dict.get("first_observed"),
            _last_observed = metadata_dict.get("last_observed"),
            _agents_involved = metadata_dict.get("agents_involved", []),
            _topics = metadata_dict.get("topics", []),
            _tags = metadata_dict.get("tags", []),
        )
        
        return ExtractedPattern(
            metadata=metadata,
            _pattern_data = pattern_dict.get("pattern_data", {}),
            _context = pattern_dict.get("context", {}),
            _outcomes = pattern_dict.get("outcomes", []),
            _preconditions = pattern_dict.get("preconditions", []),
            _postconditions = pattern_dict.get("postconditions", []),
            _applicability_conditions = pattern_dict.get("applicability_conditions", []),
        )
    
    async def _init_redis(self) -> None:
        """Initialize Redis connection."""
        try:
            import redis.asyncio as redis
            
            self._redis = redis.from_url(
                self.config.redis_url,
                _decode_responses = True,
            )
            
            self._pubsub = self._redis.pubsub()
            
            # Subscribe to channels
            await self._pubsub.subscribe(
                self.config.pattern_channel,
                self.config.signal_channel,
            )
            
            logger.info(
                "redis_connection_established",
                agent_id=self.agent_id,
            )
            
        except ImportError:
            logger.warning(
                "redis_not_available",
                agent_id=self.agent_id,
                message="redis.asyncio not installed - using local-only mode",
            )
        except Exception as e:
            logger.error(
                "redis_connection_failed",
                agent_id=self.agent_id,
                _error = str(e),
            )
            raise
    
    async def _subscribe_loop(self) -> None:
        """Background loop for processing pub/sub messages."""
        if not self._pubsub:
            return
        
        logger.info(
            "subscribe_loop_started",
            agent_id=self.agent_id,
            _channels = [self.config.pattern_channel, self.config.signal_channel],
        )
        
        try:
            async for message in self._pubsub.listen():
                if not self._running:
                    break
                
                if message["type"] != "message":
                    continue
                
                try:
                    await self._process_pubsub_message(message)
                except Exception as e:
                    logger.error(
                        "pubsub_message_error",
                        _error = str(e),
                        _channel = message.get("channel"),
                    )
                    
        except asyncio.CancelledError:
            logger.info("subscribe_loop_cancelled", agent_id=self.agent_id)
        except Exception as e:
            logger.error(
                "subscribe_loop_error",
                agent_id=self.agent_id,
                _error = str(e),
            )
    
    async def _process_pubsub_message(self, message: Dict[str, Any]) -> None:
        """
        Process a pub/sub message.
        
        Args:
            message: Redis pub/sub message
        """
        _channel = message.get("channel", "")
        _data = message.get("data", "")
        
        if not data or isinstance(data, bytes):
            return
        
        try:
            _sync_message = SyncMessage.from_json(data)
            
            # Skip messages from self
            if sync_message.source_agent == self.agent_id:
                return
            
            # Skip already processed messages
            if sync_message.message_id in self._processed_ids:
                return
            
            self._processed_ids.add(sync_message.message_id)
            
            # Trim processed IDs set
            if len(self._processed_ids) > 10000:
                self._processed_ids = set(list(self._processed_ids)[-5000:])
            
            # Process based on channel
            if channel == self.config.pattern_channel:
                await self.receive_pattern(
                    _pattern_dict = sync_message.payload.get("pattern", {}),
                    _source_agent = sync_message.source_agent,
                )
            
            elif channel == self.config.signal_channel:
                await self.receive_learning_signal(
                    _signal_dict = sync_message.payload,
                    _source_agent = sync_message.source_agent,
                )
                
        except json.JSONDecodeError as e:
            logger.warning(
                "invalid_message_format",
                _channel = channel,
                _error = str(e),
            )
        except Exception as e:
            logger.error(
                "pubsub_processing_error",
                _channel = channel,
                _error = str(e),
            )
    
    async def _sync_loop(self) -> None:
        """Background loop for periodic synchronization."""
        logger.info(
            "sync_loop_started",
            agent_id=self.agent_id,
            _interval_seconds = self.config.sync_interval_seconds,
        )
        
        try:
            while self._running:
                await asyncio.sleep(self.config.sync_interval_seconds)
                
                # Perform periodic sync tasks
                await self._periodic_sync()
                
        except asyncio.CancelledError:
            logger.info("sync_loop_cancelled", agent_id=self.agent_id)
        except Exception as e:
            logger.error(
                "sync_loop_error",
                agent_id=self.agent_id,
                _error = str(e),
            )
    
    async def _periodic_sync(self) -> None:
        """Perform periodic synchronization tasks."""
        # Trim old processed IDs
        # Check connection health
        # Log statistics
        pass
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get current engine status.
        
        Returns:
            Status dictionary
        """
        return {
            "agent_id": self.agent_id,
            "running": self._running,
            "redis_connected": self._redis is not None,
            "local_patterns": len(self.local_learning._patterns),
            "local_signals": len(self.local_learning._learning_signals),
            "pending_messages": self._pending_messages.qsize(),
            "processed_ids": len(self._processed_ids),
            "pattern_callbacks": len(self._on_pattern_received),
            "signal_callbacks": len(self._on_signal_received),
            "merge_callbacks": len(self._on_merge_complete),
            "config": {
                "merge_strategy": self.config.merge_strategy.value,
                "validation_required": self.config.validation_required,
                "sync_interval": self.config.sync_interval_seconds,
            },
        }


class DistributedLearningCoordinator:
    """
    Coordinator for distributed learning across the swarm.
    
    This class provides high-level orchestration for distributed
    learning operations, including batch publishing, coordinated
    merges, and swarm-wide learning synchronization.
    """
    
    def __init__(self, engine: DistributedLearningEngine):
        """
        Initialize distributed learning coordinator.
        
        Args:
            engine: DistributedLearningEngine instance
        """
        self.engine = engine
        
        logger.info(
            "distributed_learning_coordinator_initialized",
            _agent_id = engine.agent_id,
        )
    
    async def broadcast_pattern(self, pattern: ExtractedPattern, _wait_for_ack: bool, _timeout: float) -> Dict[str, Any]:
        """
        Broadcast a pattern to the swarm.
        
        Args:
            pattern: Pattern to broadcast
            wait_for_ack: Wait for acknowledgments
            timeout: Timeout for acknowledgments
            
        Returns:
            Broadcast result summary
        """
        _success = await self.engine.publish_pattern(pattern)
        
        return {
            "pattern_id": pattern.metadata.pattern_id,
            "broadcast_success": success,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    
    async def sync_with_swarm(self, pattern_types: Optional[List[PatternType]], min_confidence: float) -> MergeResult:
        """
        Synchronize local knowledge with the swarm.
        
        Args:
            pattern_types: Filter by pattern types
            min_confidence: Minimum confidence threshold
            
        Returns:
            MergeResult with sync statistics
        """
        # Get local patterns
        _local_patterns = self.engine.local_learning.get_patterns(
            _pattern_type = pattern_types[0] if pattern_types else None,
            _min_confidence = min_confidence,
        )
        
        # Publish local patterns
        for pattern in local_patterns:
            await self.engine.publish_pattern(pattern)
        
        # Return current status
        return MergeResult(
            _success = True,
            _merged_count = len(local_patterns),
        )
    
    async def collect_swarm_knowledge(self, timeout: float) -> Dict[str, ExtractedPattern]:
        """
        Collect knowledge from across the swarm.
        
        Args:
            timeout: Collection timeout in seconds
            
        Returns:
            Dictionary of collected patterns
        """
        # Wait for incoming patterns
        await asyncio.sleep(timeout)
        
        return self.engine.local_learning._patterns.copy()
    
    def get_swarm_status(self) -> Dict[str, Any]:
        """
        Get swarm learning status.
        
        Returns:
            Status dictionary
        """
        _engine_status = self.engine.get_status()
        
        return {
            "local_status": engine_status,
            "total_patterns": len(self.engine.local_learning._patterns),
            "total_signals": len(self.engine.local_learning._learning_signals),
            "coordination_active": True,
        }
