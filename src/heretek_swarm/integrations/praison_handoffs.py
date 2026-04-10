"""
Agent Handoffs - PraisonAI Pattern Implementation

Enables seamless task transfer between agents with context preservation.
Reference: PraisonAI agent handoff patterns
"""

from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
import asyncio
import structlog

_logger = structlog.get_logger(__name__)


class HandoffStatus(Enum):
    """Status of agent handoff."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class HandoffContext:
    """Context transferred during handoff."""
    task_id: str
    source_agent: str
    target_agent: str
    task_description: str
    context_data: Dict[str, Any] = field(default_factory=dict)
    conversation_history: List[Dict] = field(default_factory=list)
    attachments: List[str] = field(default_factory=list)
    priority: str = "normal"  # low, normal, high, critical
    deadline: Optional[datetime] = None
    status: HandoffStatus = HandoffStatus.PENDING
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: Optional[datetime] = None
    result: Optional[Any] = None
    error: Optional[str] = None


class AgentHandoff:
    """
    Manages agent-to-agent task handoffs.
    
    Pattern stolen from PraisonAI:
    - Context preservation during transfer
    - Conversation history handoff
    - Status tracking and callbacks
    - Priority-based queueing
    """
    
    def __init__(self):
        self._handoffs: Dict[str, HandoffContext] = {}
        self._pending_queue: List[str] = []
        self._callbacks: Dict[str, Callable] = {}
        self._a2a_server = None
    
    def set_a2a_server(self, _server) -> None:
        """Set A2A server for inter-agent communication."""
        self._a2a_server = server
    
    def register_callback(self, _event: str, _callback: Callable[[HandoffContext], _Any]) -> None:
        """
        Register callback for handoff events.
        
        Args:
            event: Event type (created, started, completed, failed)
            callback: Callback function
        """
        self._callbacks[event] = callback
        logger.debug("handoff_callback_registered", event=event)
    
    async def create_handoff(self, _task_id: str, _source_agent: str, _target_agent: str, _task_description: str, _context_data: Optional[Dict], _conversation_history: Optional[List[Dict]], _priority: str, _deadline: Optional[datetime]) -> str:
        """
        Create a new agent handoff.
        
        Args:
            task_id: Unique task identifier
            source_agent: Agent handing off
            target_agent: Agent receiving task
            task_description: Task description
            context_data: Additional context data
            conversation_history: Previous conversation
            priority: Task priority
            deadline: Optional deadline
            
        Returns:
            Handoff ID
        """
        _handoff_id = f"handoff_{task_id}_{datetime.now(timezone.utc).timestamp()}"
        
        _context = HandoffContext(
            _task_id = task_id,
            _source_agent = source_agent,
            _target_agent = target_agent,
            _task_description = task_description,
            _context_data = context_data or {},
            _conversation_history = conversation_history or [],
            priority=priority,
            deadline=deadline,
        )
        
        self._handoffs[handoff_id] = context
        self._pending_queue.append(handoff_id)
        
        logger.info(
            "handoff_created",
            _handoff_id = handoff_id,
            source=source_agent,
            target=target_agent,
            priority=priority,
        )
        
        # Trigger callback
        if "created" in self._callbacks:
            await self._execute_callback("created", context)
        
        # Send to target agent via A2A
        if self._a2a_server:
            await self._notify_target_agent(handoff_id, context)
        
        return handoff_id
    
    async def accept_handoff(self, _handoff_id: str, _agent_id: str) -> bool:
        """
        Accept a handoff (called by target agent).
        
        Args:
            handoff_id: Handoff to accept
            agent_id: Accepting agent ID
            
        Returns:
            True if accepted
        """
        if handoff_id not in self._handoffs:
            logger.warning("handoff_not_found", handoff_id=handoff_id)
            return False
        
        _context = self._handoffs[handoff_id]
        
        if context.target_agent != agent_id:
            logger.warning(
                "handoff_wrong_agent",
                _handoff_id = handoff_id,
                _expected = context.target_agent,
                _actual = agent_id,
            )
            return False
        
        context.status = HandoffStatus.IN_PROGRESS
        
        if handoff_id in self._pending_queue:
            self._pending_queue.remove(handoff_id)
        
        logger.info("handoff_accepted", handoff_id=handoff_id, agent=agent_id)
        
        if "started" in self._callbacks:
            await self._execute_callback("started", context)
        
        return True
    
    async def complete_handoff(self, _handoff_id: str, _result: Any, _agent_id: str) -> bool:
        """
        Complete a handoff with result.
        
        Args:
            handoff_id: Handoff to complete
            result: Task result
            agent_id: Completing agent ID
            
        Returns:
            True if completed
        """
        if handoff_id not in self._handoffs:
            return False
        
        _context = self._handoffs[handoff_id]
        
        if context.target_agent != agent_id:
            return False
        
        context.status = HandoffStatus.COMPLETED
        context.completed_at = datetime.now(timezone.utc)
        context.result = result
        
        logger.info(
            "handoff_completed",
            _handoff_id = handoff_id,
            _agent = agent_id,
        )
        
        if "completed" in self._callbacks:
            await self._execute_callback("completed", context)
        
        # Notify source agent
        if self._a2a_server:
            await self._notify_source_agent(handoff_id, context, result)
        
        return True
    
    async def fail_handoff(self, _handoff_id: str, _error: str, _agent_id: str) -> bool:
        """
        Mark handoff as failed.
        
        Args:
            handoff_id: Handoff to fail
            error: Error message
            agent_id: Failing agent ID
            
        Returns:
            True if failed
        """
        if handoff_id not in self._handoffs:
            return False
        
        _context = self._handoffs[handoff_id]
        context.status = HandoffStatus.FAILED
        context.error = error
        context.completed_at = datetime.now(timezone.utc)
        
        logger.error(
            "handoff_failed",
            _handoff_id = handoff_id,
            _agent = agent_id,
            error=error,
        )
        
        if "failed" in self._callbacks:
            await self._execute_callback("failed", context)
        
        return True
    
    def get_handoff(self, _handoff_id: str) -> Optional[HandoffContext]:
        """Get handoff by ID."""
        return self._handoffs.get(handoff_id)
    
    def get_pending_handoffs(self, _agent_id: str) -> List[HandoffContext]:
        """Get pending handoffs for an agent."""
        return [
            h for h in self._handoffs.values()
            if h.target_agent == agent_id and h.status == HandoffStatus.PENDING
        ]
    
    def get_active_handoffs(self, _agent_id: str) -> List[HandoffContext]:
        """Get active handoffs for an agent."""
        return [
            h for h in self._handoffs.values()
            if h.target_agent == agent_id and h.status == HandoffStatus.IN_PROGRESS
        ]
    
    def get_handoff_history(self, _agent_id: str) -> List[HandoffContext]:
        """Get completed/failed handoff history."""
        return [
            h for h in self._handoffs.values()
            if (h.source_agent == agent_id or h.target_agent == agent_id)
            and h.status in [HandoffStatus.COMPLETED, HandoffStatus.FAILED]
        ]
    
    async def _notify_target_agent(self, _handoff_id: str, _context: HandoffContext) -> None:
        """Notify target agent of new handoff via A2A."""
        if not self._a2a_server:
            return
        
        _message = {
            "type": "handoff_request",
            "handoff_id": handoff_id,
            "source_agent": context.source_agent,
            "task_description": context.task_description,
            "priority": context.priority,
            "deadline": context.deadline.isoformat() if context.deadline else None,
        }
        
        await self._a2a_server.event_mesh.send_to_json(
            context.target_agent,
            message,
        )
    
    async def _notify_source_agent(self, _handoff_id: str, _context: HandoffContext, _result: Any) -> None:
        """Notify source agent of handoff completion."""
        if not self._a2a_server:
            return
        
        _message = {
            "type": "handoff_complete",
            "handoff_id": handoff_id,
            "target_agent": context.target_agent,
            "status": context.status.value,
            "result": result,
        }
        
        await self._a2a_server.event_mesh.send_to_json(
            context.source_agent,
            message,
        )
    
    async def _execute_callback(self, _event: str, _context: HandoffContext) -> None:
        """Execute callback with error handling."""
        try:
            _callback = self._callbacks.get(event)
            if callback:
                if asyncio.iscoroutinefunction(callback):
                    await callback(context)
                else:
                    callback(context)
        except Exception as e:
            logger.error(
                "handoff_callback_error",
                _event = event,
                _error = str(e),
            )
    
    def get_statistics(self) -> Dict:
        """Get handoff statistics."""
        return {
            "total_handoffs": len(self._handoffs),
            "pending": len(self._pending_queue),
            "in_progress": sum(
                1 for h in self._handoffs.values()
                if h.status == HandoffStatus.IN_PROGRESS
            ),
            "completed": sum(
                1 for h in self._handoffs.values()
                if h.status == HandoffStatus.COMPLETED
            ),
            "failed": sum(
                1 for h in self._handoffs.values()
                if h.status == HandoffStatus.FAILED
            ),
        }


# Global handoff manager
_handoff_manager = AgentHandoff()


def create_handoff_sync(_task_id: str, _source_agent: str, _target_agent: str, _task_description: str, _**kwargs) -> str:
    """Synchronous wrapper for create_handoff."""
    import asyncio
    _loop = asyncio.get_event_loop()
    return loop.run_until_complete(
        handoff_manager.create_handoff(
            _task_id = task_id,
            _source_agent = source_agent,
            _target_agent = target_agent,
            _task_description = task_description,
            **kwargs,
        )
    )
