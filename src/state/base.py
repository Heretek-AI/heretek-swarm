"""
Base models for State Management System.

Provides type-safe data structures for agent state, message lineage,
and state transitions with complete validation.
"""

from datetime import UTC, datetime
from enum import StrEnum
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class StateStatus(StrEnum):
    """Status of a state"""
    ACTIVE = "active"
    SUSPENDED = "suspended"
    COMPLETED = "completed"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"


class TransitionType(StrEnum):
    """Types of state transitions"""
    INITIALIZE = "initialize"
    UPDATE = "update"
    SNAPSHOT = "snapshot"
    ROLLBACK = "rollback"
    FORK = "fork"
    MERGE = "merge"
    COMPLETE = "complete"
    FAIL = "fail"


class MessageType(StrEnum):
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
    parent_message_id: UUID | None = Field(None, description="Direct parent")
    root_message_id: UUID = Field(..., description="Root of conversation tree")

    # Ancestry chain (for quick lookups)
    ancestor_ids: list[UUID] = Field(default_factory=list, description="All ancestors")
    depth: int = Field(default=0, ge=0, description="Depth in conversation tree")

    # Message metadata
    message_type: MessageType = Field(default=MessageType.TASK)
    sender_agent_id: str = Field(..., description="Sending agent")
    receiver_agent_id: str | None = Field(None, description="Receiving agent")

    # Content hash for integrity
    content_hash: str = Field(..., description="SHA256 hash of content")
    content_size_bytes: int = Field(..., ge=0)

    # Timestamps
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    delivered_at: datetime | None = Field(None)
    processed_at: datetime | None = Field(None)

    # State
    is_branch_point: bool = Field(default=False, description="Can fork from here")
    child_count: int = Field(default=0, ge=0)

    # Metadata
    correlation_id: UUID | None = Field(None, description="Correlates related messages")
    tags: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

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
    trigger_reason: str | None = Field(None, description="Why this transition")

    # State changes
    previous_state_hash: str | None = Field(None, description="Hash of state before")
    new_state_hash: str = Field(..., description="Hash of state after")
    delta: dict[str, Any] = Field(default_factory=dict, description="Changes made")

    # Associated message
    message_id: UUID | None = Field(None, description="Message that triggered this")

    # Timestamps
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    duration_ms: float | None = Field(None, description="Transition duration")

    # Rollback info
    can_rollback: bool = Field(default=True)
    rollback_data: dict[str, Any] | None = Field(None, description="Data needed for rollback")

    # Metadata
    tags: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

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
    current_task: str | None = Field(None, description="Current task description")
    current_task_id: UUID | None = Field(None)

    # Working memory
    working_memory: dict[str, Any] = Field(default_factory=dict)
    context: dict[str, Any] = Field(default_factory=dict)

    # Conversation tracking
    conversation_ids: set[UUID] = Field(default_factory=set)
    active_conversation_id: UUID | None = Field(None)

    # Relationships
    parent_agent_id: str | None = Field(None)
    child_agent_ids: set[str] = Field(default_factory=set)

    # Metrics
    messages_sent: int = Field(default=0, ge=0)
    messages_received: int = Field(default=0, ge=0)
    tasks_completed: int = Field(default=0, ge=0)
    tasks_failed: int = Field(default=0, ge=0)

    # Timestamps
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    last_active_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    # Versioning
    version: int = Field(default=1, ge=1)
    state_hash: str | None = Field(None, description="Hash of current state")

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
        self.updated_at = datetime.now(UTC)
        self.last_active_at = datetime.now(UTC)
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
    participant_ids: set[str] = Field(default_factory=set)

    # State
    status: StateStatus = Field(default=StateStatus.ACTIVE)
    topic: str | None = Field(None, description="Conversation topic")
    goal: str | None = Field(None, description="Conversation goal")

    # Messages
    root_message_id: UUID | None = Field(None, description="First message")
    latest_message_id: UUID | None = Field(None, description="Most recent message")
    message_count: int = Field(default=0, ge=0)

    # Context
    context: dict[str, Any] = Field(default_factory=dict)
    decisions: list[dict[str, Any]] = Field(default_factory=list)
    artifacts: list[dict[str, Any]] = Field(default_factory=list)

    # Timestamps
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    completed_at: datetime | None = Field(None)

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
    active_agents: set[str] = Field(default_factory=set)
    suspended_agents: set[str] = Field(default_factory=set)

    # Conversations
    active_conversations: set[UUID] = Field(default_factory=set)
    completed_conversations: set[UUID] = Field(default_factory=set)

    # Metrics
    total_messages: int = Field(default=0, ge=0)
    total_tasks: int = Field(default=0, ge=0)
    completed_tasks: int = Field(default=0, ge=0)
    failed_tasks: int = Field(default=0, ge=0)

    # Global context
    global_context: dict[str, Any] = Field(default_factory=dict)
    configuration: dict[str, Any] = Field(default_factory=dict)

    # Health
    healthy: bool = Field(default=True)
    error_count: int = Field(default=0, ge=0)
    last_error: str | None = Field(None)
    last_error_at: datetime | None = Field(None)

    # Timestamps
    started_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    # Versioning
    version: int = Field(default=1, ge=1)
    snapshot_id: UUID | None = Field(None, description="Latest snapshot")

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
    scope_ids: list[str] = Field(default_factory=list, description="IDs in scope")

    # State data
    system_state: SystemState | None = Field(None)
    agent_states: dict[str, AgentState] = Field(default_factory=dict)
    conversation_states: dict[str, ConversationState] = Field(default_factory=dict)

    # Message lineage at snapshot time
    message_lineage: dict[str, MessageLineage] = Field(default_factory=dict)

    # Metadata
    parent_snapshot_id: UUID | None = Field(None, description="Previous snapshot")
    trigger: str = Field(..., description="What triggered snapshot")
    description: str | None = Field(None)

    # Integrity
    state_hash: str = Field(default="", description="Hash of snapshot data")
    size_bytes: int = Field(default=0, ge=0)

    # Timestamps
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    # Retention
    expires_at: datetime | None = Field(None)
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
    added_agents: dict[str, AgentState] = Field(default_factory=dict)
    modified_agents: dict[str, dict[str, Any]] = Field(default_factory=dict)
    removed_agents: set[str] = Field(default_factory=set)

    added_conversations: dict[str, ConversationState] = Field(default_factory=dict)
    modified_conversations: dict[str, dict[str, Any]] = Field(default_factory=dict)
    removed_conversations: set[str] = Field(default_factory=set)

    # Messages
    added_messages: dict[str, MessageLineage] = Field(default_factory=dict)

    # Metadata
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    size_bytes: int = Field(default=0, ge=0)

    class Config:
        json_encoders = {
            datetime: datetime.isoformat,
            UUID: str,
            set: list,
        }
