"""
Base models for State Management System.

Provides type-safe data structures for agent state, message lineage,
and state transitions with complete validation.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Set
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, field_validator


class StateStatus(str, Enum):
    """Status of a state"""
    ACTIVE = "active"
    SUSPENDED = "suspended"
    COMPLETED = "completed"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"


class TransitionType(str, Enum):
    """Types of state transitions"""
    INITIALIZE = "initialize"
    UPDATE = "update"
    SNAPSHOT = "snapshot"
    ROLLBACK = "rollback"
    FORK = "fork"
    MERGE = "merge"
    COMPLETE = "complete"
    FAIL = "fail"


class MessageType(str, Enum):
    """Types of messages in the system"""
    TASK = "task"
    QUERY = "query"
    RESPONSE = "response"
    COMMAND = "command"
    EVENT = "event"
    ERROR = "error"
    HEARTBEAT = "heartbeat"
    ACKNOWLEDGMENT = "acknowledgment"


class MessageLineage(BaseModel):
    """
    Tracks the provenance and lineage of a message.
    
    Records parent-child relationships and complete message history
    for debugging, replay, and audit purposes.
    """
    
    # Identity
    message_id: UUID = Field(default_factory=uuid4, description="Unique message ID")
    conversation_id: UUID = Field(..., description="Conversation/session ID")
    
    # Parentage
    parent_message_id: Optional[UUID] = Field(None, description="Direct parent")
    root_message_id: UUID = Field(..., description="Root of conversation tree")
    
    # Ancestry chain (for quick lookups)
    ancestor_ids: List[UUID] = Field(default_factory=list, description="All ancestors")
    depth: int = Field(default=0, ge=0, description="Depth in conversation tree")
    
    # Message metadata
    message_type: MessageType = Field(default=MessageType.TASK)
    sender_agent_id: str = Field(..., description="Sending agent")
    receiver_agent_id: Optional[str] = Field(None, description="Receiving agent")
    
    # Content hash for integrity
    content_hash: str = Field(..., description="SHA256 hash of content")
    content_size_bytes: int = Field(..., ge=0)
    
    # Timestamps
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    delivered_at: Optional[datetime] = Field(None)
    processed_at: Optional[datetime] = Field(None)
    
    # State
    is_branch_point: bool = Field(default=False, description="Can fork from here")
    child_count: int = Field(default=0, ge=0)
    
    # Metadata
    correlation_id: Optional[UUID] = Field(None, description="Correlates related messages")
    tags: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    class Config:
        json_encoders = {
            datetime: datetime.isoformat,
            UUID: str,
        }


class StateTransition(BaseModel):
    """
    Records a state transition with before/after state and trigger.
    
    Enables complete audit trail and rollback capabilities.
    """
    
    # Identity
    transition_id: UUID = Field(default_factory=uuid4)
    state_id: UUID = Field(..., description="State being transitioned")
    
    # Transition details
    transition_type: TransitionType = Field(..., description="Type of transition")
    triggered_by: str = Field(..., description="Agent or system that triggered")
    trigger_reason: Optional[str] = Field(None, description="Why this transition")
    
    # State changes
    previous_state_hash: Optional[str] = Field(None, description="Hash of state before")
    new_state_hash: str = Field(..., description="Hash of state after")
    delta: Dict[str, Any] = Field(default_factory=dict, description="Changes made")
    
    # Associated message
    message_id: Optional[UUID] = Field(None, description="Message that triggered this")
    
    # Timestamps
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    duration_ms: Optional[float] = Field(None, description="Transition duration")
    
    # Rollback info
    can_rollback: bool = Field(default=True)
    rollback_data: Optional[Dict[str, Any]] = Field(None, description="Data needed for rollback")
    
    # Metadata
    tags: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    class Config:
        json_encoders = {
            datetime: datetime.isoformat,
            UUID: str,
        }


class AgentState(BaseModel):
    """
    Complete state of a single agent.
    
    Includes working memory, current task, and all context needed
    for the agent to resume from any point.
    """
    
    # Identity
    agent_id: str = Field(..., description="Unique agent identifier")
    agent_type: str = Field(..., description="Type/class of agent")
    
    # Current state
    status: StateStatus = Field(default=StateStatus.ACTIVE)
    current_task: Optional[str] = Field(None, description="Current task description")
    current_task_id: Optional[UUID] = Field(None)
    
    # Working memory
    working_memory: Dict[str, Any] = Field(default_factory=dict)
    context: Dict[str, Any] = Field(default_factory=dict)
    
    # Conversation tracking
    conversation_ids: Set[UUID] = Field(default_factory=set)
    active_conversation_id: Optional[UUID] = Field(None)
    
    # Relationships
    parent_agent_id: Optional[str] = Field(None)
    child_agent_ids: Set[str] = Field(default_factory=set)
    
    # Metrics
    messages_sent: int = Field(default=0, ge=0)
    messages_received: int = Field(default=0, ge=0)
    tasks_completed: int = Field(default=0, ge=0)
    tasks_failed: int = Field(default=0, ge=0)
    
    # Timestamps
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    last_active_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    # Versioning
    version: int = Field(default=1, ge=1)
    state_hash: Optional[str] = Field(None, description="Hash of current state")
    
    def compute_hash(self) -> str:
        """Compute hash of current state"""
        import hashlib
        import json
        
        state_dict = self.model_dump(
            exclude={"state_hash", "updated_at", "last_active_at"}
        )
        state_json = json.dumps(state_dict, sort_keys=True, default=str)
        return hashlib.sha256(state_json.encode()).hexdigest()
    
    def touch(self) -> "AgentState":
        """Update timestamps"""
        self.updated_at = datetime.now(timezone.utc)
        self.last_active_at = datetime.now(timezone.utc)
        self.state_hash = self.compute_hash()
        return self
    
    class Config:
        json_encoders = {
            datetime: datetime.isoformat,
            UUID: str,
            set: list,
        }


class ConversationState(BaseModel):
    """
    State of a conversation between agents.
    
    Tracks all participants, message history, and conversation context.
    """
    
    # Identity
    conversation_id: UUID = Field(default_factory=uuid4)
    
    # Participants
    initiator_agent_id: str = Field(..., description="Agent that started conversation")
    participant_ids: Set[str] = Field(default_factory=set)
    
    # State
    status: StateStatus = Field(default=StateStatus.ACTIVE)
    topic: Optional[str] = Field(None, description="Conversation topic")
    goal: Optional[str] = Field(None, description="Conversation goal")
    
    # Messages
    root_message_id: Optional[UUID] = Field(None, description="First message")
    latest_message_id: Optional[UUID] = Field(None, description="Most recent message")
    message_count: int = Field(default=0, ge=0)
    
    # Context
    context: Dict[str, Any] = Field(default_factory=dict)
    decisions: List[Dict[str, Any]] = Field(default_factory=list)
    artifacts: List[Dict[str, Any]] = Field(default_factory=list)
    
    # Timestamps
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: Optional[datetime] = Field(None)
    
    # Versioning
    version: int = Field(default=1, ge=1)
    
    class Config:
        json_encoders = {
            datetime: datetime.isoformat,
            UUID: str,
            set: list,
        }


class SystemState(BaseModel):
    """
    Global state of the entire multi-agent system.
    
    Aggregates agent states, tracks system-wide metrics, and
    maintains global configuration.
    """
    
    # Identity
    system_id: str = Field(default="heretek-swarm")
    
    # Agents
    active_agents: Set[str] = Field(default_factory=set)
    suspended_agents: Set[str] = Field(default_factory=set)
    
    # Conversations
    active_conversations: Set[UUID] = Field(default_factory=set)
    completed_conversations: Set[UUID] = Field(default_factory=set)
    
    # Metrics
    total_messages: int = Field(default=0, ge=0)
    total_tasks: int = Field(default=0, ge=0)
    completed_tasks: int = Field(default=0, ge=0)
    failed_tasks: int = Field(default=0, ge=0)
    
    # Global context
    global_context: Dict[str, Any] = Field(default_factory=dict)
    configuration: Dict[str, Any] = Field(default_factory=dict)
    
    # Health
    healthy: bool = Field(default=True)
    error_count: int = Field(default=0, ge=0)
    last_error: Optional[str] = Field(None)
    last_error_at: Optional[datetime] = Field(None)
    
    # Timestamps
    started_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    # Versioning
    version: int = Field(default=1, ge=1)
    snapshot_id: Optional[UUID] = Field(None, description="Latest snapshot")
    
    class Config:
        json_encoders = {
            datetime: datetime.isoformat,
            UUID: str,
            set: list,
        }


class StateSnapshot(BaseModel):
    """
    Complete snapshot of system state at a point in time.
    
    Can be used for rollback, recovery, or analysis.
    """
    
    # Identity
    snapshot_id: UUID = Field(default_factory=uuid4)
    snapshot_type: str = Field(default="full", description="full, incremental, partial")
    
    # Scope
    scope: str = Field(default="system", description="system, agent, conversation")
    scope_ids: List[str] = Field(default_factory=list, description="IDs in scope")
    
    # State data
    system_state: Optional[SystemState] = Field(None)
    agent_states: Dict[str, AgentState] = Field(default_factory=dict)
    conversation_states: Dict[str, ConversationState] = Field(default_factory=dict)
    
    # Message lineage at snapshot time
    message_lineage: Dict[str, MessageLineage] = Field(default_factory=dict)
    
    # Metadata
    parent_snapshot_id: Optional[UUID] = Field(None, description="Previous snapshot")
    trigger: str = Field(..., description="What triggered snapshot")
    description: Optional[str] = Field(None)
    
    # Integrity
    state_hash: str = Field(default="", description="Hash of snapshot data")
    size_bytes: int = Field(default=0, ge=0)
    
    # Timestamps
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    # Retention
    expires_at: Optional[datetime] = Field(None)
    is_persistent: bool = Field(default=True)
    
    def compute_hash(self) -> str:
        """Compute hash of snapshot data"""
        import hashlib
        import json
        
        snapshot_dict = self.model_dump(exclude={"state_hash"})
        snapshot_json = json.dumps(snapshot_dict, sort_keys=True, default=str)
        return hashlib.sha256(snapshot_json.encode()).hexdigest()
    
    class Config:
        json_encoders = {
            datetime: datetime.isoformat,
            UUID: str,
        }


class StateDiff(BaseModel):
    """
    Difference between two states.
    
    Used for incremental snapshots and state synchronization.
    """
    
    # Identity
    diff_id: UUID = Field(default_factory=uuid4)
    from_snapshot_id: UUID = Field(..., description="Source snapshot")
    to_snapshot_id: UUID = Field(..., description="Target snapshot")
    
    # Changes
    added_agents: Dict[str, AgentState] = Field(default_factory=dict)
    modified_agents: Dict[str, Dict[str, Any]] = Field(default_factory=dict)
    removed_agents: Set[str] = Field(default_factory=set)
    
    added_conversations: Dict[str, ConversationState] = Field(default_factory=dict)
    modified_conversations: Dict[str, Dict[str, Any]] = Field(default_factory=dict)
    removed_conversations: Set[str] = Field(default_factory=set)
    
    # Messages
    added_messages: Dict[str, MessageLineage] = Field(default_factory=dict)
    
    # Metadata
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    size_bytes: int = Field(default=0, ge=0)
    
    class Config:
        json_encoders = {
            datetime: datetime.isoformat,
            UUID: str,
            set: list,
        }
