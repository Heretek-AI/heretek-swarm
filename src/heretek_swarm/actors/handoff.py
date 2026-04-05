"""
Agent Handoff Mechanism for Heretek Swarm

Provides seamless agent-to-agent handoff with context transfer.
Reference: PraisonAI agent handoffs pattern, MetaGPT RoleContext
"""

import asyncio
import uuid
from datetime import datetime
from typing import Any, Dict, Optional
from dataclasses import dataclass, field

import structlog

logger = structlog.get_logger(__name__)


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


class AgentHandoff:
    """
    Seamless agent-to-agent handoff mechanism.
    
    Enables context transfer between agents for specialized task handling.
    """
    
    def __init__(self, historian):
        """
        Initialize handoff mechanism.
        
        Args:
            historian: Historian agent for logging handoffs
        """
        self.historian = historian
        self._active_handoffs: Dict[str, HandoffContext] = {}
    
    async def execute_handoff(
        self,
        from_agent_id: str,
        to_agent_id: str,
        context: Dict[str, Any],
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
        """
        handoff_id = str(uuid.uuid4())
        timestamp = datetime.utcnow().isoformat()
        
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
            
            # Log handoff to historian
            if self.historian:
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
    
    async def complete_handoff(
        self,
        handoff_id: str,
        result: Dict[str, Any]
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
        
        context_package = self._active_handoffs[handoff_id]
        
        # Log completion to historian
        if self.historian:
            await self.historian.log_event(
                event_type="handoff_completed",
                data={
                    "handoff_id": handoff_id,
                    "result": result,
                    "timestamp": datetime.utcnow().isoformat()
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
                handoff_id=handoff_id
            )
            return False
        
        # Log cancellation
        if self.historian:
            await self.historian.log_event(
                event_type="handoff_cancelled",
                data={
                    "handoff_id": handoff_id,
                    "timestamp": datetime.utcnow().isoformat()
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
    
    async def should_handoff(self, context: Dict[str, Any]) -> bool:
        """Determine if handoff should occur"""
        raise NotImplementedError
    
    async def select_destination(self, context: Dict[str, Any]) -> str:
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
        task_type = context.get("task_type")
        return task_type in self.TASK_AGENTS
    
    async def select_destination(self, context: Dict[str, Any]) -> str:
        """Select destination based on task type"""
        task_type = context.get("task_type")
        return self.TASK_AGENTS.get(task_type, "steward")


class PerformanceStrategy(HandoffStrategy):
    """Handoff based on agent performance metrics"""
    
    PERFORMANCE_THRESHOLD = 0.7  # 70% success rate threshold
    
    async def should_handoff(self, context: Dict[str, Any]) -> bool:
        """Check if agent performance is below threshold"""
        success_rate = context.get("success_rate", 1.0)
        return success_rate < self.PERFORMANCE_THRESHOLD
    
    async def select_destination(self, context: Dict[str, Any]) -> str:
        """Select best performing agent"""
        agent_performance = context.get("agent_performance", {})
        
        # Find agent with highest success rate
        best_agent = max(
            agent_performance.items(),
            key=lambda x: x[1].get("success_rate", 0.0)
        )
        
        return best_agent[0] if best_agent else "steward"


class LoadBalancingStrategy(HandoffStrategy):
    """Handoff based on current agent load"""
    
    MAX_CONCURRENT_TASKS = 5
    
    async def should_handoff(self, context: Dict[str, Any]) -> bool:
        """Check if agent is overloaded"""
        current_tasks = context.get("current_tasks", 0)
        return current_tasks >= self.MAX_CONCURRENT_TASKS
    
    async def select_destination(self, context: Dict[str, Any]) -> str:
        """Select least loaded agent"""
        agent_load = context.get("agent_load", {})
        
        # Find agent with lowest task count
        least_loaded = min(
            agent_load.items(),
            key=lambda x: x[1].get("task_count", 0)
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
        context: Dict[str, Any],
        reason: str = "automatic"
    ) -> Optional[HandoffResult]:
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
