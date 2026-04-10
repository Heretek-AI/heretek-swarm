"""
Agent Handoff Mechanism for Heretek Swarm

Provides seamless agent-to-agent handoff with context transfer.
Reference: PraisonAI agent handoffs pattern, MetaGPT RoleContext

Features:
- Input validation for all handoff parameters
- Rate limiting to prevent abuse
- Context size limits
- Maximum active handoffs limit
"""

import sys
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Set
from dataclasses import dataclass

import structlog
from heretek_swarm.actors.base import ActorMessage

# Session 44: Collective Learning Integration
from heretek_swarm.collective.learning import PatternType

# Session 44: Consensus Integration
from heretek_swarm.consensus.swarm_deliberation import Position

# Session 44: Memory Optimization Integration
from heretek_swarm.memory.access_patterns import AccessTier

# Session 44: Zero-Trust Validation


_logger = structlog.get_logger(__name__)


@dataclass
class HandoffContext:
    """Context package transferred during agent handoff"""
    source: str
    destination: str
    context: Dict[str, Any]
    timestamp: str
    handoff_id: str


@dataclass
class HandoffResult:
    """Result of agent handoff operation"""
    success: bool
    handoff_id: str
    error: Optional[str] = None


class HandoffValidator:
    """
    Validates handoff parameters before execution.
    
    Provides Pydantic-style validation for handoff requests.
    """
    
    MAX_CONTEXT_SIZE = 10000  # Maximum context size in bytes
    MAX_HANDOFFS_PER_MINUTE = 10  # Rate limiting
    REQUIRED_FIELDS: Set[str] = frozenset({"from_agent_id", "to_agent_id", "context"})
    
    @classmethod
    def validate(cls, from_agent_id: str, to_agent_id: str, context: Dict[str, Any]) -> None:
        """
        Validate handoff parameters.
        
        Args:
            from_agent_id: Source agent ID
            to_agent_id: Destination agent ID
            context: Context to transfer
            
        Raises:
            ValueError: If validation fails
        """
        cls._validate_fields(from_agent_id, to_agent_id, context)
        cls._validate_context_size(context)
        cls._validate_agent_ids(from_agent_id, to_agent_id)
    
    @classmethod
    def _validate_fields(cls, from_agent_id: str, to_agent_id: str, context: Dict[str, Any]) -> None:
        """Validate required fields are present."""
        if not from_agent_id or not isinstance(from_agent_id, str):
            raise ValueError("from_agent_id must be a non-empty string")
        
        if not to_agent_id or not isinstance(to_agent_id, str):
            raise ValueError("to_agent_id must be a non-empty string")
        
        if not context or not isinstance(context, dict):
            raise ValueError("context must be a non-empty dictionary")
    
    @classmethod
    def _validate_context_size(cls, context: Dict[str, Any]) -> None:
        """Validate context size is within limits."""
        _context_size = sys.getsizeof(str(context))
        if context_size > cls.MAX_CONTEXT_SIZE:
            raise ValueError(
                f"Context size ({context_size} bytes) exceeds maximum allowed ({cls.MAX_CONTEXT_SIZE} bytes)"
            )
    
    @classmethod
    def _validate_agent_ids(cls, from_agent_id: str, to_agent_id: str) -> None:
        """Validate agent IDs are different."""
        if from_agent_id == to_agent_id:
            raise ValueError("from_agent_id and to_agent_id must be different")


class AgentHandoff:
    """
    Seamless agent-to-agent handoff mechanism.
    
    Enables context transfer between agents for specialized task handling.
    """
    
    MAX_ACTIVE_HANDOFFS = 100  # Maximum concurrent handoffs
    
    def __init__(self, historian):
        """
        Initialize handoff mechanism.
        
        Args:
            historian: Historian agent for logging handoffs
        """
        self.historian = historian
        self._active_handoffs: Dict[str, HandoffContext] = {}
        self._handoff_timestamps: List[datetime] = []  # For rate limiting
        self._validator = HandoffValidator()
    
    async def execute_handoff(self, from_agent_id: str, to_agent_id: str, context: Dict[str, Any], reason: str) -> HandoffResult:
        """
        Execute handoff between two agents.
        
        Args:
            from_agent_id: Source agent ID
            to_agent_id: Destination agent ID
            context: Context to transfer
            reason: Reason for handoff
            
        Returns:
            HandoffResult with success status and handoff ID
            
        Raises:
            ValueError: If validation fails
        """
        # Validate handoff request
        try:
            self._validator.validate(from_agent_id, to_agent_id, context)
        except ValueError as e:
            logger.error("handoff_validation_failed", error=str(e))
            return HandoffResult(
                _success = False,
                _handoff_id = "",
                error=f"Validation failed: {str(e)}"
            )
        
        # Rate limiting check
        try:
            self._check_rate_limit()
        except ValueError as e:
            logger.error("handoff_rate_limit_exceeded", error=str(e))
            return HandoffResult(
                _success = False,
                _handoff_id = "",
                error=str(e)
            )
        
        # P2-1 fix: Use timezone-aware datetime
        _handoff_id = str(uuid.uuid4())
        _timestamp = datetime.now(timezone.utc).isoformat()
        
        # Check active handoffs limit (P0-11 fix)
        if len(self._active_handoffs) >= self.MAX_ACTIVE_HANDOFFS:
            logger.error(
                "handoff_limit_exceeded",
                _active_count = len(self._active_handoffs),
                _max_allowed = self.MAX_ACTIVE_HANDOFFS
            )
            return HandoffResult(
                _success = False,
                _handoff_id = "",
                error=f"Maximum active handoffs exceeded ({self.MAX_ACTIVE_HANDOFFS})"
            )
        
        # Prepare context package
        _context_package = HandoffContext(
            _source = from_agent_id,
            _destination = to_agent_id,
            _context = context,
            _timestamp = timestamp,
            _handoff_id = handoff_id
        )
        
        logger.info(
            "handoff_initiated",
            _handoff_id = handoff_id,
            _from_agent = from_agent_id,
            _to_agent = to_agent_id,
            _reason = reason
        )
        
        try:
            # Store active handoff
            self._active_handoffs[handoff_id] = context_package
            
            # CRITICAL FIX: Actually transfer context to destination agent
            # Get actor registry and send context to destination
            from heretek_swarm.actors.supervisor import get_supervisor
            _supervisor = get_supervisor()
            if supervisor and to_agent_id in supervisor.actors:
                _destination_actor = supervisor.actors[to_agent_id]
                # Send handoff message with full context
                await destination_actor.put_message(
                    ActorMessage(
                        _sender = from_agent_id,
                        _message_type = "handoff_request",
                        _content = {
                            "handoff_id": handoff_id,
                            "from_agent": from_agent_id,
                            "context": context,
                            "reason": reason,
                            "timestamp": timestamp,
                        },
                        _timestamp = timestamp,
                        _correlation_id = handoff_id,
                    )
                )
                logger.info(
                    "handoff_context_transferred",
                    _handoff_id = handoff_id,
                    _to_agent = to_agent_id
                )
            else:
                logger.warning(
                    "handoff_destination_not_found",
                    _handoff_id = handoff_id,
                    _to_agent = to_agent_id
                )
            
            # Log handoff to historian (P1-4: Check method existence)
            if self.historian and hasattr(self.historian, 'log_event'):
                await self.historian.log_event(
                    _event_type = "agent_handoff",
                    _data = {
                        "handoff_id": handoff_id,
                        "from_agent": from_agent_id,
                        "to_agent": to_agent_id,
                        "reason": reason,
                        "timestamp": timestamp,
                        "context_keys": list(context.keys())
                    }
                )
            
            logger.info(
                "handoff_completed",
                _handoff_id = handoff_id,
                _status = "success"
            )
            
            return HandoffResult(
                _success = True,
                _handoff_id = handoff_id,
                error=None
            )
            
        except Exception as e:
            logger.error(
                "handoff_failed",
                _handoff_id = handoff_id,
                error=str(e)
            )
            
            return HandoffResult(
                _success = False,
                _handoff_id = handoff_id,
                error=str(e)
            )
    
    def _check_rate_limit(self) -> None:
        """
        Check rate limiting for handoffs.
        
        Raises:
            ValueError: If rate limit exceeded
        """
        # P2-1 fix: Use timezone-aware datetime
        now = datetime.now(timezone.utc)
        _one_minute_ago = now.replace(microsecond=0)
        
        # Remove timestamps older than 1 minute
        self._handoff_timestamps = [
            ts for ts in self._handoff_timestamps
            if ts > one_minute_ago
        ]
        
        # Check if limit exceeded
        if len(self._handoff_timestamps) >= HandoffValidator.MAX_HANDOFFS_PER_MINUTE:
            raise ValueError(
                f"Rate limit exceeded: maximum {HandoffValidator.MAX_HANDOFFS_PER_MINUTE} handoffs per minute"
            )
        
        # Record this handoff
        self._handoff_timestamps.append(now)
    
    async def complete_handoff(self, handoff_id: str, result: Dict[str, Any]) -> bool:
        """
        Complete an active handoff with results.
        
        Args:
            handoff_id: Handoff ID to complete
            result: Result data from destination agent
            
        Returns:
            True if handoff completed successfully
        """
        if handoff_id not in self._active_handoffs:
            logger.warning(
                "handoff_not_found",
                _handoff_id = handoff_id
            )
            return False
        
        _context_package = self._active_handoffs[handoff_id]
        
        # Log completion to historian
        # P1-4: Check method existence
        if self.historian and hasattr(self.historian, 'log_event'):
            await self.historian.log_event(
                # P2-1 fix: Use timezone-aware datetime
                _event_type = "handoff_completed",
                _data = {
                    "handoff_id": handoff_id,
                    "result": result,
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
            )
        
        # Remove from active handoffs
        del self._active_handoffs[handoff_id]
        
        logger.info(
            "handoff_completed",
            _handoff_id = handoff_id,
            _status = "success"
        )
        
        return True
    
    def get_active_handoffs(self) -> Dict[str, HandoffContext]:
        """
        Get all currently active handoffs.
        
        Returns:
            Dictionary of active handoff contexts
        """
        return self._active_handoffs.copy()
    
    async def cancel_handoff(self, handoff_id: str) -> bool:
        """
        Cancel an active handoff.
        
        Args:
            handoff_id: Handoff ID to cancel
            
        Returns:
            True if handoff was cancelled
        """
        if handoff_id not in self._active_handoffs:
            logger.warning(
                "handoff_not_found",
                _handoff_id = handoff_id
            )
            return False
        
        # Log cancellation
        # P1-4: Check method existence
        if self.historian and hasattr(self.historian, 'log_event'):
            # P2-1 fix: Use timezone-aware datetime
            await self.historian.log_event(
                _event_type = "handoff_cancelled",
                _data = {
                    "handoff_id": handoff_id,
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
            )
        
        # Remove from active handoffs
        del self._active_handoffs[handoff_id]
        
        logger.info(
            "handoff_cancelled",
            _handoff_id = handoff_id,
            _status = "success"
        )
        
        return True


# =============================================================================
# Handoff Strategies
# =============================================================================

class HandoffStrategy:
    """Base class for handoff strategies"""
    
    async def should_handoff(self, _context: Dict[str, Any]) -> bool:
        """Determine if handoff should occur"""
        raise NotImplementedError
    
    async def select_destination(self, _context: Dict[str, Any]) -> str:
        """Select destination agent for handoff"""
        raise NotImplementedError


class TaskTypeStrategy(HandoffStrategy):
    """Handoff based on task type"""
    
    TASK_AGENTS = {
        "code_generation": "coder",
        "analysis": "alpha",
        "validation": "beta",
        "research": "explorer",
        "creative": "dreamer",
        "memory": "historian",
        "safety": "sentinel",
    }
    
    async def should_handoff(self, context: Dict[str, Any]) -> bool:
        """Check if task type matches a specialized agent"""
        _task_type = context.get("task_type")
        return task_type in self.TASK_AGENTS
    
    async def select_destination(self, context: Dict[str, Any]) -> str:
        """Select destination based on task type"""
        _task_type = context.get("task_type")
        return self.TASK_AGENTS.get(task_type, "steward")


class PerformanceStrategy(HandoffStrategy):
    """Handoff based on agent performance metrics"""
    
    PERFORMANCE_THRESHOLD = 0.7  # 70% success rate threshold
    
    async def should_handoff(self, context: Dict[str, Any]) -> bool:
        """Check if agent performance is below threshold"""
        _success_rate = context.get("success_rate", 1.0)
        return success_rate < self.PERFORMANCE_THRESHOLD
    
    async def select_destination(self, context: Dict[str, Any]) -> str:
        """Select best performing agent"""
        _agent_performance = context.get("agent_performance", {})
        
        # P1-5 fix: Handle empty dict
        if not agent_performance:
            logger.warning("No agent performance data available, defaulting to steward")
            return "steward"
        
        # Find agent with highest success rate
        _best_agent = max(
            agent_performance.items(),
            key=lambda x: x[1].get("success_rate", 0.0)
        )
        
        return best_agent[0] if best_agent else "steward"


class LoadBalancingStrategy(HandoffStrategy):
    """Handoff based on current agent load"""
    
    MAX_CONCURRENT_TASKS = 5
    
    async def should_handoff(self, context: Dict[str, Any]) -> bool:
        """Check if agent is overloaded"""
        _current_tasks = context.get("current_tasks", 0)
        return current_tasks >= self.MAX_CONCURRENT_TASKS
    
    async def select_destination(self, context: Dict[str, Any]) -> str:
        """Select least loaded agent"""
        _agent_load = context.get("agent_load", {})
        
        # P1-5 fix: Handle empty dict
        if not agent_load:
            logger.warning("No agent load data available, defaulting to steward")
            return "steward"
        
        # Find agent with lowest task count
        _least_loaded = min(
            agent_load.items(),
            _key = lambda x: x[1].get("task_count", 0)
        )
        
        return least_loaded[0] if least_loaded else "steward"


class HandoffOrchestrator:
    """
    Orchestrates agent handoffs using configurable strategies.
    
    Manages the handoff lifecycle and ensures proper context transfer.
    """
    
    def __init__(self, handoff: AgentHandoff):
        """
        Initialize orchestrator.
        
        Args:
            handoff: AgentHandoff instance
        """
        self.handoff = handoff
        self.strategy: Optional[HandoffStrategy] = None
        self._strategy_map = {
            "task_type": TaskTypeStrategy(),
            "performance": PerformanceStrategy(),
            "load_balancing": LoadBalancingStrategy(),
        }
    
    def set_strategy(self, strategy_name: str) -> bool:
        """
        Set the handoff strategy.
        
        Args:
            strategy_name: Name of strategy to use
            
        Returns:
            True if strategy was set successfully
        """
        if strategy_name not in self._strategy_map:
            logger.warning(
                "strategy_not_found",
                strategy=strategy_name,
                _available = list(self._strategy_map.keys())
            )
            return False
        
        self.strategy = self._strategy_map[strategy_name]
        logger.info(
            "strategy_set",
            strategy=strategy_name
        )
        return True
    

    # =========================================================================
    # Session 44: Collective Learning Integration Methods
    # =========================================================================

    async def _emit_pattern(self, item_id: str, item_type: str, outcome: str, content: Dict[str, Any]) -> None:
        """Emit pattern for collective learning."""
        if not self.pattern_extractor:
            return
        
        if item_id in self._pattern_emitted:
            return
        
        try:
            await self.pattern_extractor.analyze_message(
                _message_id = f"{item_type}_{item_id}",
                _sender = self.agent_id,
                _recipient = "broadcast",
                _message_type = f"{item_type}_completion",
                _content = content,
                _timestamp = datetime.now(timezone.utc).isoformat(),
            )
            
            self._pattern_emitted.add(item_id)
            logger.info(f"{item_type}_pattern_emitted", item_id=item_id, outcome=outcome)
        except Exception as e:
            logger.warning("failed_to_emit_pattern", item_id=item_id, error=str(e))

    async def _consume_patterns(self, pattern_types: Optional[List[PatternType]]) -> List[Dict[str, Any]]:
        """Consume patterns from collective learning."""
        if not self.pattern_extractor:
            return []
        
        try:
            _patterns = await self.pattern_extractor.extract_patterns(
                _time_window_hours = 24,
                _pattern_types = pattern_types or [PatternType.SUCCESS, PatternType.DECISION],
            )
            return [p.to_dict() for p in patterns if p.metadata.confidence >= 0.7]
        except Exception as e:
            logger.warning("failed_to_consume_patterns", error=str(e))
            return []

    # =========================================================================
    # Session 44: Consensus Deliberation Integration Methods
    # =========================================================================

    async def _initiate_deliberation(self, item_id: str, proposal: str, participating_agents: List[str], domain: str) -> Optional[str]:
        """Initiate swarm deliberation."""
        if not self.deliberation_engine:
            return None
        
        try:
            _deliberation_id = f"delib_{item_id}"
            self.deliberation_engine.start_deliberation(
                _deliberation_id = deliberation_id,
                _proposal = proposal[:200],
                _participants = participating_agents,
                _domain = domain,
            )
            self._active_deliberations[item_id] = deliberation_id
            
            logger.info("deliberation_initiated", deliberation_id=deliberation_id, item_id=item_id)
            return deliberation_id
        except Exception as e:
            logger.error("failed_to_initiate_deliberation", item_id=item_id, error=str(e))
            return None

    async def _submit_deliberation_position(self, item_id: str, agent_id: str, position: Position, confidence: float, argument: str) -> bool:
        """Submit agent position in deliberation."""
        if not self.deliberation_engine:
            return False
        
        _deliberation_id = self._active_deliberations.get(item_id)
        if not deliberation_id:
            return False
        
        try:
            _success = self.deliberation_engine.submit_position(
                _deliberation_id = deliberation_id,
                agent_id=agent_id,
                _position = position,
                _confidence = confidence,
                _argument = argument,
            )
            
            if success and self.access_analyzer:
                self.access_analyzer.record_access(
                    _memory_id = f"delib_{deliberation_id}_{agent_id}",
                    _access_type = "write",
                    agent_id=agent_id,
                )
            
            return success
        except Exception as e:
            logger.error("failed_to_submit_deliberation_position", error=str(e))
            return False

    async def _finalize_deliberation(self, item_id: str) -> Optional[Any]:
        """Finalize deliberation and apply result."""
        if not self.deliberation_engine:
            return None
        
        _deliberation_id = self._active_deliberations.get(item_id)
        if not deliberation_id:
            return None
        
        try:
            _result = self.deliberation_engine.finalize_deliberation(deliberation_id)
            
            if result:
                self.deliberation_engine.cleanup_deliberation(deliberation_id)
                del self._active_deliberations[item_id]
                logger.info("deliberation_finalized", deliberation_id=deliberation_id)
            
            return result
        except Exception as e:
            logger.error("failed_to_finalize_deliberation", error=str(e))
            return None

    # =========================================================================
    # Session 44: Memory Optimization Integration Methods
    # =========================================================================

    def _track_memory_access(self, item_id: str, item_type: str, access_type: str) -> None:
        """Track memory access patterns."""
        if not self.access_analyzer:
            return
        
        _memory_id = f"{item_type}_{item_id}"
        self.access_analyzer.record_access(
            _memory_id = memory_id,
            _access_type = access_type,
            agent_id=self.agent_id,
        )

    def _get_memory_tier(self, item_id: str, item_type: str) -> AccessTier:
        """Get memory tier classification."""
        if not self.access_analyzer:
            return AccessTier.COLD
        
        _memory_id = f"{item_type}_{item_id}"
        _profile = self.access_analyzer.get_profile(memory_id)
        return profile.tier if profile else AccessTier.COLD

    async def _prefetch_relevant(self, agent_id: str, item_type: str) -> List[str]:
        """Prefetch items an agent is likely to need."""
        if not self.access_analyzer:
            return []
        
        try:
            _predicted_memories = self.access_analyzer.predict_agent_access(agent_id)
            return [
                mem.replace(f"{item_type}_", "")
                for mem in predicted_memories
                if mem.startswith(f"{item_type}_")
            ]
        except Exception as e:
            logger.warning("failed_to_prefetch", agent_id=agent_id, error=str(e))
            return []

    def get_learning_status(self) -> Dict[str, Any]:
        """Get collective learning and memory optimization status."""
        return {
            "agent_id": self.agent_id,
            "collective_learning": {
                "patterns_extracted": len(self.pattern_extractor._validated_patterns) if self.pattern_extractor else 0,
                "message_cache_size": len(self.pattern_extractor._message_cache) if self.pattern_extractor else 0,
            },
            "consensus": {
                "active_deliberations": len(self._active_deliberations),
                "deliberation_engine_stats": self.deliberation_engine.get_statistics() if self.deliberation_engine else {},
            },
            "memory_optimization": {
                "access_statistics": self.access_analyzer.get_statistics().to_dict() if self.access_analyzer else {},
            },
        }


    async def evaluate_and_handoff(self, from_agent_id: str, context: Dict[str, Any], reason: str) -> Optional[HandoffResult]:
        """
        Evaluate if handoff is needed and execute if so.
        
        Args:
            from_agent_id: Current agent ID
            context: Current execution context
            reason: Reason for handoff evaluation
            
        Returns:
            HandoffResult if handoff was executed, None otherwise
        """
        if not self.strategy:
            logger.warning("no_strategy_set")
            return None
        
        # Evaluate if handoff should occur
        _should_handoff = await self.strategy.should_handoff(context)
        
        if not should_handoff:
            return None
        
        # Select destination agent
        _to_agent_id = await self.strategy.select_destination(context)
        
        if to_agent_id == from_agent_id:
            logger.warning(
                "handoff_same_agent",
                _agent_id = from_agent_id
            )
            return None
        
        # Execute handoff
        return await self.handoff.execute_handoff(
            _from_agent_id = from_agent_id,
            _to_agent_id = to_agent_id,
            _context = context,
            _reason = reason
        )
