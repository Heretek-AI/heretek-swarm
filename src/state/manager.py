"""
State Management System.

Unified state management integrating lineage tracking, snapshots,
and state transitions for the multi-agent system.
"""

import asyncio
import hashlib
import json
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Set
from uuid import UUID, uuid4

import structlog
from pydantic import BaseModel, Field

from .base import (
    StateSnapshot,
    StateDiff,
    StateTransition,
    StateStatus,
    TransitionType,
    AgentState,
    ConversationState,
    SystemState,
    MessageLineage,
    MessageType
)
from .lineage import LineageTracker, LineageConfig
from .snapshots import SnapshotManager, SnapshotConfig

logger = structlog.get_logger()


class StateConfig(BaseModel):
    """Configuration for state management"""
    
    # Subsystem configs
    lineage: LineageConfig = Field(default_factory=LineageConfig)
    snapshots: SnapshotConfig = Field(default_factory=SnapshotConfig)
    
    # State management
    max_agents: int = Field(default=1000, ge=1)
    max_conversations_per_agent: int = Field(default=100, ge=1)
    state_sync_interval_seconds: int = Field(default=60)
    
    # Recovery
    auto_recovery_enabled: bool = Field(default=True)
    recovery_timeout_seconds: int = Field(default=300)
    
    # Persistence
    persist_state_changes: bool = Field(default=True)
    batch_persist_size: int = Field(default=50)


class StateManager:
    """
    Unified State Management System.
    
    Features:
    - Agent state lifecycle management
    - Conversation state tracking
    - Message lineage with full provenance
    - Snapshots and rollback
    - State transitions and history
    - Automatic recovery
    
    Integration:
    - Persists to Dual-Tier Memory System
    - Tracks all state changes with lineage
    - Enables replay and debugging
    """
    
    def __init__(self, config: Optional[StateConfig] = None):
        self.config = config or StateConfig()
        
        # Initialize subsystems
        self.lineage = LineageTracker(self.config.lineage)
        self.snapshots = SnapshotManager(self.config.snapshots)
        
        # State storage
        self._agents: Dict[str, AgentState] = {}
        self._conversations: Dict[str, ConversationState] = {}
        self._system: Optional[SystemState] = None
        
        # Transition history
        self._transitions: List[StateTransition] = []
        self._max_transitions = 10000
        
        # Indexing
        self._agent_conversations: Dict[str, Set[str]] = {}
        
        # Background tasks
        self._sync_task: Optional[asyncio.Task] = None
        self._running = False
        
        # Metrics
        self._state_changes = 0
        self._rollbacks = 0
        self._recoveries = 0
    
    async def initialize(self, initial_system_state: Optional[SystemState] = None) -> None:
        """Initialize state manager"""
        # Initialize subsystems
        await self.snapshots.initialize()
        
        # Set initial system state
        if initial_system_state:
            self._system = initial_system_state
        else:
            self._system = SystemState()
        
        # Try to restore from latest snapshot
        latest = await self.snapshots.get_latest_snapshot(scope="system")
        if latest:
            await self._restore_from_snapshot(latest)
            logger.info(
                "state_restored_from_snapshot",
                snapshot_id=str(latest.snapshot_id)
            )
        
        # Start background sync
        self._running = True
        self._sync_task = asyncio.create_task(self._state_sync_loop())
        
        logger.info(
            "state_manager_initialized",
            agents=len(self._agents),
            conversations=len(self._conversations)
        )
    
    async def shutdown(self) -> None:
        """Shutdown state manager"""
        self._running = False
        
        # Create final snapshot
        await self.create_snapshot(trigger="shutdown")
        
        # Shutdown subsystems
        if self._sync_task:
            self._sync_task.cancel()
            try:
                await self._sync_task
            except asyncio.CancelledError:
                pass
        
        await self.snapshots.shutdown()
        
        logger.info("state_manager_shutdown")
    
    # Agent State Management
    
    async def register_agent(
        self,
        agent_id: str,
        agent_type: str,
        parent_agent_id: Optional[str] = None,
        initial_state: Optional[Dict[str, Any]] = None
    ) -> AgentState:
        """Register a new agent"""
        if len(self._agents) >= self.config.max_agents:
            raise RuntimeError("Maximum agents limit reached")
        
        if agent_id in self._agents:
            raise ValueError(f"Agent {agent_id} already registered")
        
        # Create agent state
        agent = AgentState(
            agent_id=agent_id,
            agent_type=agent_type,
            parent_agent_id=parent_agent_id,
            working_memory=initial_state or {},
            status=StateStatus.ACTIVE
        )
        
        agent.state_hash = agent.compute_hash()
        
        # Store
        self._agents[agent_id] = agent
        self._agent_conversations[agent_id] = set()
        
        # Track parent relationship
        if parent_agent_id and parent_agent_id in self._agents:
            self._agents[parent_agent_id].child_agent_ids.add(agent_id)
        
        # Record transition
        await self._record_transition(
            transition_type=TransitionType.INITIALIZE,
            agent_id=agent_id,
            changes={"action": "agent_registered", "agent_type": agent_type}
        )
        
        logger.info(
            "agent_registered",
            agent_id=agent_id,
            agent_type=agent_type
        )
        
        return agent
    
    async def get_agent_state(self, agent_id: str) -> Optional[AgentState]:
        """Get current state of an agent"""
        return self._agents.get(agent_id)
    
    async def update_agent_state(
        self,
        agent_id: str,
        updates: Dict[str, Any],
        working_memory_updates: Optional[Dict[str, Any]] = None,
        context_updates: Optional[Dict[str, Any]] = None
    ) -> Optional[AgentState]:
        """Update agent state"""
        agent = self._agents.get(agent_id)
        if not agent:
            return None
        
        # Apply updates
        if working_memory_updates:
            agent.working_memory.update(working_memory_updates)
        
        if context_updates:
            agent.context.update(context_updates)
        
        agent.touch()
        agent.state_hash = agent.compute_hash()
        
        # Record transition
        await self._record_transition(
            transition_type=TransitionType.UPDATE,
            agent_id=agent_id,
            changes=updates
        )
        
        self._state_changes += 1
        
        return agent
    
    async def update_agent_status(
        self,
        agent_id: str,
        status: StateStatus,
        current_task: Optional[str] = None
    ) -> Optional[AgentState]:
        """Update agent status"""
        agent = self._agents.get(agent_id)
        if not agent:
            return None
        
        old_status = agent.status
        agent.status = status
        agent.current_task = current_task
        agent.touch()
        
        # Record transition
        await self._record_transition(
            transition_type=TransitionType.UPDATE,
            agent_id=agent_id,
            changes={
                "status_change": f"{old_status.value} -> {status.value}",
                "current_task": current_task
            }
        )
        
        return agent
    
    async def deregister_agent(self, agent_id: str) -> bool:
        """Deregister an agent"""
        agent = self._agents.get(agent_id)
        if not agent:
            return False
        
        # Update parent's children
        if agent.parent_agent_id and agent.parent_agent_id in self._agents:
            self._agents[agent.parent_agent_id].child_agent_ids.discard(agent_id)
        
        # Mark children as orphaned or reassign
        for child_id in agent.child_agent_ids:
            if child_id in self._agents:
                self._agents[child_id].parent_agent_id = None
        
        # Remove
        del self._agents[agent_id]
        del self._agent_conversations[agent_id]
        
        # Record transition
        await self._record_transition(
            transition_type=TransitionType.UPDATE,
            agent_id=agent_id,
            changes={"action": "agent_deregistered"}
        )
        
        return True
    
    # Conversation State Management
    
    async def start_conversation(
        self,
        initiator_agent_id: str,
        participant_ids: Optional[Set[str]] = None,
        topic: Optional[str] = None,
        goal: Optional[str] = None
    ) -> ConversationState:
        """Start a new conversation"""
        if initiator_agent_id not in self._agents:
            raise ValueError(f"Initiator agent {initiator_agent_id} not registered")
        
        # Create conversation
        conversation = ConversationState(
            conversation_id=uuid4(),
            initiator_agent_id=initiator_agent_id,
            participant_ids=participant_ids or {initiator_agent_id},
            topic=topic,
            goal=goal,
            status=StateStatus.ACTIVE
        )
        
        conv_id = str(conversation.conversation_id)
        
        # Store
        self._conversations[conv_id] = conversation
        
        # Update agent conversation tracking
        for agent_id in conversation.participant_ids:
            if agent_id in self._agent_conversations:
                self._agent_conversations[agent_id].add(conv_id)
        
        # Update agent state
        if initiator_agent_id in self._agents:
            self._agents[initiator_agent_id].conversation_ids.add(
                conversation.conversation_id
            )
            self._agents[initiator_agent_id].active_conversation_id = (
                conversation.conversation_id
            )
        
        # Record transition
        await self._record_transition(
            transition_type=TransitionType.INITIALIZE,
            conversation_id=conv_id,
            changes={
                "action": "conversation_started",
                "initiator": initiator_agent_id
            }
        )
        
        logger.info(
            "conversation_started",
            conversation_id=conv_id,
            initiator=initiator_agent_id,
            participants=list(conversation.participant_ids)
        )
        
        return conversation
    
    async def get_conversation_state(
        self,
        conversation_id: UUID
    ) -> Optional[ConversationState]:
        """Get conversation state"""
        return self._conversations.get(str(conversation_id))
    
    async def update_conversation_state(
        self,
        conversation_id: UUID,
        context_updates: Optional[Dict[str, Any]] = None,
        decision: Optional[Dict[str, Any]] = None,
        artifact: Optional[Dict[str, Any]] = None
    ) -> Optional[ConversationState]:
        """Update conversation state"""
        conv = self._conversations.get(str(conversation_id))
        if not conv:
            return None
        
        if context_updates:
            conv.context.update(context_updates)
        
        if decision:
            conv.decisions.append(decision)
        
        if artifact:
            conv.artifacts.append(artifact)
        
        conv.updated_at = datetime.now(timezone.utc)
        conv.version += 1
        
        return conv
    
    async def complete_conversation(
        self,
        conversation_id: UUID
    ) -> Optional[ConversationState]:
        """Mark conversation as completed"""
        conv = self._conversations.get(str(conversation_id))
        if not conv:
            return None
        
        conv.status = StateStatus.COMPLETED
        conv.completed_at = datetime.now(timezone.utc)
        
        # Update participants
        for agent_id in conv.participant_ids:
            if agent_id in self._agents:
                agent = self._agents[agent_id]
                agent.conversation_ids.discard(conversation_id)
                
                if agent.active_conversation_id == conversation_id:
                    agent.active_conversation_id = None
        
        # Record transition
        await self._record_transition(
            transition_type=TransitionType.COMPLETE,
            conversation_id=str(conversation_id),
            changes={"action": "conversation_completed"}
        )
        
        return conv
    
    # Message Tracking
    
    async def record_message(
        self,
        conversation_id: UUID,
        sender_agent_id: str,
        content: Any,
        message_type: MessageType = MessageType.TASK,
        receiver_agent_id: Optional[str] = None,
        parent_message_id: Optional[UUID] = None
    ) -> MessageLineage:
        """Record a message with lineage tracking"""
        # Update conversation
        conv = self._conversations.get(str(conversation_id))
        if conv:
            conv.message_count += 1
            conv.updated_at = datetime.now(timezone.utc)
        
        # Update agent metrics
        if sender_agent_id in self._agents:
            self._agents[sender_agent_id].messages_sent += 1
        
        if receiver_agent_id and receiver_agent_id in self._agents:
            self._agents[receiver_agent_id].messages_received += 1
        
        # Record lineage
        lineage = await self.lineage.record_message(
            content=content,
            conversation_id=conversation_id,
            sender_agent_id=sender_agent_id,
            receiver_agent_id=receiver_agent_id,
            message_type=message_type,
            parent_message_id=parent_message_id
        )
        
        # Update conversation root/latest
        if conv:
            if parent_message_id is None:
                conv.root_message_id = lineage.message_id
            conv.latest_message_id = lineage.message_id
        
        return lineage
    
    # Snapshot Management
    
    async def create_snapshot(
        self,
        scope: str = "system",
        trigger: str = "manual",
        description: Optional[str] = None
    ) -> StateSnapshot:
        """Create a state snapshot"""
        # Convert message lineage
        lineage_data = {}
        for msg_id, node in self.lineage._nodes.items():
            lineage_data[str(msg_id)] = node.lineage.model_dump()
        
        return await self.snapshots.create_snapshot(
            system_state=self._system,
            agent_states=self._agents,
            conversation_states=self._conversations,
            message_lineage=lineage_data,
            scope=scope,
            trigger=trigger,
            description=description
        )
    
    async def rollback_to_snapshot(
        self,
        snapshot_id: UUID
    ) -> bool:
        """Rollback to a previous snapshot"""
        snapshot = await self.snapshots.get_snapshot(snapshot_id)
        if not snapshot:
            return False
        
        # Verify we can rollback (not too many versions ahead)
        current_version = self._system.version if self._system else 0
        snapshot_version = snapshot.system_state.version if snapshot.system_state else 0
        
        if current_version - snapshot_version > self.config.snapshots.max_rollback_depth:
            logger.warning(
                "rollback_too_far",
                current_version=current_version,
                snapshot_version=snapshot_version,
                max_depth=self.config.snapshots.max_rollback_depth
            )
            return False
        
        await self._restore_from_snapshot(snapshot)
        
        # Record transition
        await self._record_transition(
            transition_type=TransitionType.ROLLBACK,
            changes={
                "snapshot_id": str(snapshot_id),
                "from_version": current_version,
                "to_version": snapshot_version
            }
        )
        
        self._rollbacks += 1
        
        logger.info(
            "state_rolled_back",
            snapshot_id=str(snapshot_id),
            to_version=snapshot_version
        )
        
        return True
    
    async def _restore_from_snapshot(self, snapshot: StateSnapshot) -> None:
        """Restore state from a snapshot"""
        # Restore system state
        if snapshot.system_state:
            self._system = snapshot.system_state
        
        # Restore agent states
        self._agents = dict(snapshot.agent_states)
        
        # Restore conversation states
        self._conversations = dict(snapshot.conversation_states)
        
        # Rebuild indices
        self._agent_conversations = {}
        for agent_id, agent in self._agents.items():
            self._agent_conversations[agent_id] = {
                str(cid) for cid in agent.conversation_ids
            }
        
        # Restore lineage
        self.lineage._nodes = {}
        for msg_id_str, lineage_dict in snapshot.message_lineage.items():
            lineage = MessageLineage(**lineage_dict)
            from .lineage import LineageNode
            self.lineage._nodes[lineage.message_id] = LineageNode(lineage)
    
    # Transition Tracking
    
    async def _record_transition(
        self,
        transition_type: TransitionType,
        agent_id: Optional[str] = None,
        conversation_id: Optional[str] = None,
        changes: Optional[Dict[str, Any]] = None
    ) -> None:
        """Record a state transition"""
        # Generate a state_id from agent_id or conversation_id for tracking
        state_id_str = agent_id or conversation_id or "system"
        state_id = uuid4()  # Generate a unique state ID for this transition
        
        transition = StateTransition(
            transition_id=uuid4(),
            state_id=state_id,
            transition_type=transition_type,
            triggered_by=agent_id or "system",
            trigger_reason=changes.get("reason") if changes else None,
            previous_state_hash=None,  # Could compute hash of previous state if needed
            new_state_hash=hashlib.sha256(json.dumps(changes or {}, sort_keys=True).encode()).hexdigest(),
            delta=changes or {},
            message_id=None,  # Could link to message if available
            can_rollback=True,
            rollback_data=changes if changes else None,
        )
        
        self._transitions.append(transition)
        
        # Trim if too many
        if len(self._transitions) > self._max_transitions:
            self._transitions = self._transitions[-self._max_transitions:]
    
    def get_transition_history(
        self,
        agent_id: Optional[str] = None,
        conversation_id: Optional[str] = None,
        limit: int = 100
    ) -> List[StateTransition]:
        """Get transition history"""
        transitions = self._transitions
        
        if agent_id:
            transitions = [t for t in transitions if t.agent_id == agent_id]
        
        if conversation_id:
            transitions = [t for t in transitions if t.conversation_id == conversation_id]
        
        return transitions[-limit:]
    
    # Background Tasks
    
    async def _state_sync_loop(self) -> None:
        """Background task for periodic state synchronization"""
        while self._running:
            try:
                await asyncio.sleep(self.config.state_sync_interval_seconds)
                
                # Auto-snapshot if enabled
                if self.config.persist_state_changes:
                    await self.create_snapshot(
                        trigger="auto_sync",
                        description="Periodic state sync"
                    )
            
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("state_sync_failed", error=str(e))
    
    # Query Operations
    
    async def get_agent_conversations(
        self,
        agent_id: str,
        active_only: bool = True
    ) -> List[ConversationState]:
        """Get conversations for an agent"""
        conv_ids = self._agent_conversations.get(agent_id, set())
        
        conversations = []
        for conv_id in conv_ids:
            conv = self._conversations.get(conv_id)
            if conv:
                if not active_only or conv.status == StateStatus.ACTIVE:
                    conversations.append(conv)
        
        return conversations
    
    async def get_system_state(self) -> Optional[SystemState]:
        """Get current system state"""
        return self._system
    
    async def get_active_agents(self) -> List[AgentState]:
        """Get all active agents"""
        return [
            agent for agent in self._agents.values()
            if agent.status == StateStatus.ACTIVE
        ]
    
    # Statistics
    
    def get_stats(self) -> Dict[str, Any]:
        """Get state management statistics"""
        snapshot_stats = self.snapshots.get_stats()
        lineage_stats = self.lineage.get_stats()
        
        return {
            "agents": {
                "total": len(self._agents),
                "active": sum(
                    1 for a in self._agents.values()
                    if a.status == StateStatus.ACTIVE
                )
            },
            "conversations": {
                "total": len(self._conversations),
                "active": sum(
                    1 for c in self._conversations.values()
                    if c.status == StateStatus.ACTIVE
                )
            },
            "state_changes": self._state_changes,
            "rollbacks": self._rollbacks,
            "recoveries": self._recoveries,
            "transitions_tracked": len(self._transitions),
            "snapshots": snapshot_stats,
            "lineage": lineage_stats
        }
