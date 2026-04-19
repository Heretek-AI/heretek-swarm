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
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

import structlog

from heretek_swarm.actors.base import ActorMessage
from heretek_swarm.actors.mixins import DeliberationMixin, LearningMixin, MemoryMixin, PatternMixin

# Session 44: Collective Learning Integration

# Session 44: Consensus Integration

# Session 44: Memory Optimization Integration

# Session 44: Zero-Trust Validation


logger = structlog.get_logger(__name__)


@dataclass
class HandoffContext:
    """Context package transferred during agent handoff"""
    source: str
    destination: str
    context: dict[str, Any]
    timestamp: str
    handoff_id: str


@dataclass
class HandoffResult:
    """Result of agent handoff operation"""
    success: bool
    handoff_id: str
    error: str | None = None


class HandoffValidator:
    """
    Validates handoff parameters before execution.

    Provides Pydantic-style validation for handoff requests.
    """

    MAX_CONTEXT_SIZE = 10000  # Maximum context size in bytes
    MAX_HANDOFFS_PER_MINUTE = 10  # Rate limiting
    REQUIRED_FIELDS: set[str] = frozenset({"from_agent_id", "to_agent_id", "context"})

    @classmethod
    def validate(cls, from_agent_id: str, to_agent_id: str, context: dict[str, Any]) -> None:
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
    def _validate_fields(cls, from_agent_id: str, to_agent_id: str, context: dict[str, Any]) -> None:
        """Validate required fields are present."""
        if not from_agent_id or not isinstance(from_agent_id, str):
            raise ValueError("from_agent_id must be a non-empty string")

        if not to_agent_id or not isinstance(to_agent_id, str):
            raise ValueError("to_agent_id must be a non-empty string")

        if not context or not isinstance(context, dict):
            raise ValueError("context must be a non-empty dictionary")

    @classmethod
    def _validate_context_size(cls, context: dict[str, Any]) -> None:
        """Validate context size is within limits."""
        context_size = sys.getsizeof(str(context))
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
        self._active_handoffs: dict[str, HandoffContext] = {}
        self._handoff_timestamps: list[datetime] = []  # For rate limiting
        self._validator = HandoffValidator()

    async def execute_handoff(
        self,
        from_agent_id: str,
        to_agent_id: str,
        context: dict[str, Any],
        reason: str = "task_specialization"
    ) -> HandoffResult:
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
                success=False,
                handoff_id="",
                error=f"Validation failed: {e!s}"
            )

        # Rate limiting check
        try:
            self._check_rate_limit()
        except ValueError as e:
            logger.error("handoff_rate_limit_exceeded", error=str(e))
            return HandoffResult(
                success=False,
                handoff_id="",
                error=str(e)
            )

        # P2-1 fix: Use timezone-aware datetime
        handoff_id = str(uuid.uuid4())
        timestamp = datetime.now(UTC).isoformat()

        # Check active handoffs limit (P0-11 fix)
        if len(self._active_handoffs) >= self.MAX_ACTIVE_HANDOFFS:
            logger.error(
                "handoff_limit_exceeded",
                active_count=len(self._active_handoffs),
                max_allowed=self.MAX_ACTIVE_HANDOFFS
            )
            return HandoffResult(
                success=False,
                handoff_id="",
                error=f"Maximum active handoffs exceeded ({self.MAX_ACTIVE_HANDOFFS})"
            )

        # Prepare context package
        context_package = HandoffContext(
            source=from_agent_id,
            destination=to_agent_id,
            context=context,
            timestamp=timestamp,
            handoff_id=handoff_id
        )

        logger.info(
            "handoff_initiated",
            handoff_id=handoff_id,
            from_agent=from_agent_id,
            to_agent=to_agent_id,
            reason=reason
        )

        try:
            # Store active handoff
            self._active_handoffs[handoff_id] = context_package

            # CRITICAL FIX: Actually transfer context to destination agent
            # Get actor registry and send context to destination
            from heretek_swarm.actors.supervisor import get_supervisor
            supervisor = get_supervisor()
            if supervisor and to_agent_id in supervisor.actors:
                destination_actor = supervisor.actors[to_agent_id]
                # Send handoff message with full context
                await destination_actor.put_message(
                    ActorMessage(
                        sender=from_agent_id,
                        message_type="handoff_request",
                        content={
                            "handoff_id": handoff_id,
                            "from_agent": from_agent_id,
                            "context": context,
                            "reason": reason,
                            "timestamp": timestamp,
                        },
                        timestamp=timestamp,
                        correlation_id=handoff_id,
                    )
                )
                logger.info(
                    "handoff_context_transferred",
                    handoff_id=handoff_id,
                    to_agent=to_agent_id
                )
            else:
                logger.warning(
                    "handoff_destination_not_found",
                    handoff_id=handoff_id,
                    to_agent=to_agent_id
                )

            # Log handoff to historian (P1-4: Check method existence)
            if self.historian and hasattr(self.historian, "log_event"):
                await self.historian.log_event(
                    event_type="agent_handoff",
                    data={
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
                handoff_id=handoff_id,
                status="success"
            )

            return HandoffResult(
                success=True,
                handoff_id=handoff_id,
                error=None
            )

        except Exception as e:
            logger.error(
                "handoff_failed",
                handoff_id=handoff_id,
                error=str(e)
            )

            return HandoffResult(
                success=False,
                handoff_id=handoff_id,
                error=str(e)
            )

    def _check_rate_limit(self) -> None:
        """
        Check rate limiting for handoffs.

        Raises:
            ValueError: If rate limit exceeded
        """
        # P2-1 fix: Use timezone-aware datetime
        now = datetime.now(UTC)
        one_minute_ago = now.replace(microsecond=0)

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

    async def complete_handoff(
        self,
        handoff_id: str,
        result: dict[str, Any]
    ) -> bool:
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
                handoff_id=handoff_id
            )
            return False

        self._active_handoffs[handoff_id]

        # Log completion to historian
        # P1-4: Check method existence
        if self.historian and hasattr(self.historian, "log_event"):
            await self.historian.log_event(
                # P2-1 fix: Use timezone-aware datetime
                event_type="handoff_completed",
                data={
                    "handoff_id": handoff_id,
                    "result": result,
                    "timestamp": datetime.now(UTC).isoformat()
                }
            )

        # Remove from active handoffs
        del self._active_handoffs[handoff_id]

        logger.info(
            "handoff_completed",
            handoff_id=handoff_id,
            status="success"
        )

        return True

    def get_active_handoffs(self) -> dict[str, HandoffContext]:
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
                handoff_id=handoff_id
            )
            return False

        # Log cancellation
        # P1-4: Check method existence
        if self.historian and hasattr(self.historian, "log_event"):
            # P2-1 fix: Use timezone-aware datetime
            await self.historian.log_event(
                event_type="handoff_cancelled",
                data={
                    "handoff_id": handoff_id,
                    "timestamp": datetime.now(UTC).isoformat()
                }
            )

        # Remove from active handoffs
        del self._active_handoffs[handoff_id]

        logger.info(
            "handoff_cancelled",
            handoff_id=handoff_id,
            status="success"
        )

        return True


# =============================================================================
# Handoff Strategies
# =============================================================================

class HandoffStrategy:
    """Base class for handoff strategies"""

    async def should_handoff(self, context: dict[str, Any]) -> bool:
        """Determine if handoff should occur"""
        raise NotImplementedError

    async def select_destination(self, context: dict[str, Any]) -> str:
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

    async def should_handoff(self, context: dict[str, Any]) -> bool:
        """Check if task type matches a specialized agent"""
        task_type = context.get("task_type")
        return task_type in self.TASK_AGENTS

    async def select_destination(self, context: dict[str, Any]) -> str:
        """Select destination based on task type"""
        task_type = context.get("task_type")
        return self.TASK_AGENTS.get(task_type, "steward")


class PerformanceStrategy(HandoffStrategy):
    """Handoff based on agent performance metrics"""

    PERFORMANCE_THRESHOLD = 0.7  # 70% success rate threshold

    async def should_handoff(self, context: dict[str, Any]) -> bool:
        """Check if agent performance is below threshold"""
        success_rate = context.get("success_rate", 1.0)
        return success_rate < self.PERFORMANCE_THRESHOLD

    async def select_destination(self, context: dict[str, Any]) -> str:
        """Select best performing agent"""
        agent_performance = context.get("agent_performance", {})

        # P1-5 fix: Handle empty dict
        if not agent_performance:
            logger.warning("No agent performance data available, defaulting to steward")
            return "steward"

        # Find agent with highest success rate
        best_agent = max(
            agent_performance.items(),
            key=lambda x: x[1].get("success_rate", 0.0)
        )

        return best_agent[0] if best_agent else "steward"


class LoadBalancingStrategy(HandoffStrategy):
    """Handoff based on current agent load"""

    MAX_CONCURRENT_TASKS = 5

    async def should_handoff(self, context: dict[str, Any]) -> bool:
        """Check if agent is overloaded"""
        current_tasks = context.get("current_tasks", 0)
        return current_tasks >= self.MAX_CONCURRENT_TASKS

    async def select_destination(self, context: dict[str, Any]) -> str:
        """Select least loaded agent"""
        agent_load = context.get("agent_load", {})

        # P1-5 fix: Handle empty dict
        if not agent_load:
            logger.warning("No agent load data available, defaulting to steward")
            return "steward"

        # Find agent with lowest task count
        least_loaded = min(
            agent_load.items(),
            key=lambda x: x[1].get("task_count", 0)
        )

        return least_loaded[0] if least_loaded else "steward"


class HandoffOrchestrator(PatternMixin, DeliberationMixin, MemoryMixin, LearningMixin):
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
        self.strategy: HandoffStrategy | None = None
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
                available=list(self._strategy_map.keys())
            )
            return False

        self.strategy = self._strategy_map[strategy_name]
        logger.info(
            "strategy_set",
            strategy=strategy_name
        )
        return True


    async def evaluate_and_handoff(
        self,
        from_agent_id: str,
        context: dict[str, Any],
        reason: str = "automatic"
    ) -> HandoffResult | None:
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
        should_handoff = await self.strategy.should_handoff(context)

        if not should_handoff:
            return None

        # Select destination agent
        to_agent_id = await self.strategy.select_destination(context)

        if to_agent_id == from_agent_id:
            logger.warning(
                "handoff_same_agent",
                agent_id=from_agent_id
            )
            return None

        # Execute handoff
        return await self.handoff.execute_handoff(
            from_agent_id=from_agent_id,
            to_agent_id=to_agent_id,
            context=context,
            reason=reason
        )
