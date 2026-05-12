"""
Legacy State Models for Heretek Swarm.

These models provide the lineage tracking, snapshot, and state management
interfaces expected by tests and legacy code.

These are compatibility shims that wrap the actual repository implementations.
"""

import hashlib
import json
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any
from uuid import UUID, uuid4


class StateStatus(Enum):
    """Agent state status enumeration."""
    ACTIVE = "active"
    IDLE = "idle"
    SUSPENDED = "suspended"
    TERMINATED = "terminated"
    COMPLETED = "completed"


class TransitionType(Enum):
    """State transition type enumeration."""
    CREATED = "created"
    UPDATED = "updated"
    ACTIVATED = "activated"
    SUSPENDED = "suspended"
    TERMINATED = "terminated"
    RESTORED = "restored"


class MessageType(Enum):
    """Message type enumeration."""
    USER = "user"
    AGENT = "agent"
    SYSTEM = "system"


@dataclass
class SystemState:
    """
    System-wide state container.

    Attributes:
        system_id: Unique system identifier
        active_agents: Number of currently active agents
        total_messages: Total messages processed
        uptime_seconds: System uptime in seconds
        last_heartbeat: Last heartbeat timestamp
    """
    system_id: str = "default"
    active_agents: int = 0
    total_messages: int = 0
    uptime_seconds: float = 0.0
    last_heartbeat: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class StateSnapshot:
    """
    Represents a point-in-time state snapshot.

    Used for state versioning and rollback capabilities.

    Attributes:
        snapshot_id: Unique checkpoint identifier
        agent_id: Associated agent ID (or "system")
        state: State data at snapshot
        version: Snapshot version
        created_at: Creation timestamp
        trigger: What triggered this snapshot
        description: Description of snapshot
        system_state: SystemState at snapshot time
        agent_states: Dict of agent_id -> AgentState at snapshot time
        metadata: Optional metadata
    """
    snapshot_id: UUID = field(default_factory=uuid4)
    agent_id: str = "system"
    state: dict[str, Any] = field(default_factory=dict)
    version: int = 1
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    trigger: str = "manual"
    description: str = ""
    system_state: SystemState | None = None
    agent_states: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class StateTransition:
    """Represents a state change event."""
    transition_id: UUID = field(default_factory=uuid4)
    agent_id: str = ""
    from_status: StateStatus = StateStatus.IDLE
    to_status: StateStatus = StateStatus.ACTIVE
    transition_type: TransitionType = TransitionType.CREATED
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class MessageLineage:
    """
    Tracks message ancestry for conversation flows.

    Attributes:
        message_id: Unique message identifier
        conversation_id: Conversation this message belongs to
        parent_message_id: Parent message (if reply)
        root_message_id: Root message of conversation
        ancestor_ids: List of all ancestor message IDs
        depth: Depth in conversation tree (0 = root)
        sender_agent_id: Agent that sent this message
        content_hash: Hash of message content
        content_size_bytes: Size of content in bytes
        child_count: Number of direct replies
    """
    message_id: UUID = field(default_factory=uuid4)
    conversation_id: UUID | None = None
    root_message_id: UUID | None = None
    sender_agent_id: str = ""
    receiver_agent_id: str | None = None
    content_hash: str = ""
    content_size_bytes: int = 0
    parent_message_id: UUID | None = None
    ancestor_ids: list[UUID] = field(default_factory=list)
    depth: int = 0
    child_count: int = 0
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def __post_init__(self) -> None:
        if self.parent_message_id and self.parent_message_id not in self.ancestor_ids:
            self.ancestor_ids.append(self.parent_message_id)


@dataclass
class AgentState:
    """
    Represents an agent's runtime state.

    Attributes:
        agent_id: Unique agent identifier
        agent_type: Type of agent (worker, coordinator, etc.)
        status: Current operational status
        version: State version for optimistic locking
        created_at: When state was first created
        updated_at: When state was last modified
        working_memory: Agent's current working memory
        metadata: Additional metadata
    """
    agent_id: str
    agent_type: str = "worker"
    status: StateStatus = StateStatus.ACTIVE
    version: int = 1
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    working_memory: dict[str, Any] = field(default_factory=dict)
    context: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)

    def touch(self) -> None:
        """Update the timestamp to mark state as accessed."""
        self.updated_at = datetime.now(UTC)

    def transition_to(self, new_status: StateStatus) -> StateTransition:
        """Create a transition record for status change."""
        return StateTransition(
            agent_id=self.agent_id,
            from_status=self.status,
            to_status=new_status,
            transition_type=TransitionType.UPDATED,
        )

    def compute_hash(self) -> str:
        """Compute a hash of the current state for comparison."""
        import hashlib
        state_str = json.dumps(self.working_memory, sort_keys=True)
        return hashlib.sha256(state_str.encode()).hexdigest()[:16]


@dataclass
class ConversationState:
    """
    Tracks the state of a multi-agent conversation.

    Attributes:
        conversation_id: Unique conversation identifier
        initiator_agent_id: Agent that initiated the conversation
        status: Current conversation status
        participant_ids: List of participating agent IDs
        message_count: Total messages in conversation
        version: State version
        decisions: List of decisions made in conversation
        topic: Conversation topic/subject
    """
    conversation_id: UUID = field(default_factory=uuid4)
    initiator_agent_id: str = ""
    status: StateStatus = StateStatus.ACTIVE
    participant_ids: list[str] = field(default_factory=list)
    message_count: int = 0
    version: int = 1
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    decisions: list[dict[str, Any]] = field(default_factory=list)
    topic: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def add_participant(self, agent_id: str) -> None:
        """Add a participant to the conversation."""
        if agent_id not in self.participant_ids:
            self.participant_ids.append(agent_id)

    def remove_participant(self, agent_id: str) -> None:
        """Remove a participant from the conversation."""
        if agent_id in self.participant_ids:
            self.participant_ids.remove(agent_id)


# Configuration dataclasses

@dataclass
class LineageConfig:
    """Configuration for lineage tracking."""
    max_lineage_depth: int = 100
    cache_size: int = 1000
    enable_persistence: bool = True


@dataclass
class SnapshotConfig:
    """Configuration for snapshot management."""
    storage_path: str = "./snapshots"
    max_snapshots: int = 50
    auto_snapshot_enabled: bool = True
    auto_cleanup_enabled: bool = True
    snapshot_interval_seconds: int = 300


@dataclass
class StateConfig:
    """Configuration for state management."""
    lineage: LineageConfig = field(default_factory=LineageConfig)
    snapshots: SnapshotConfig = field(default_factory=SnapshotConfig)
    max_agents: int = 1000
    auto_recovery_enabled: bool = True


# Manager stubs (minimal implementations for test compatibility)

class LineageNode:
    """
    Represents a node in the message lineage tree.

    Used to track message relationships in conversations.
    """
    node_id: UUID
    message_id: UUID
    parent_id: UUID | None
    children: list["LineageNode"] = field(default_factory=list)
    depth: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)


class LineageTracker:
    """Tracks message lineage for conversations."""

    def __init__(self, config: LineageConfig | None = None) -> None:
        self.config = config or LineageConfig()
        self._lineages: dict[UUID, MessageLineage] = {}
        self._content_hashes: dict[str, UUID] = {}
        self._last_conversation_id: UUID | None = None

    async def record_message(
        self,
        content: str,
        conversation_id: UUID,
        sender_agent_id: str,
        receiver_agent_id: str | None = None,
        parent_message_id: UUID | None = None,
    ) -> MessageLineage:
        """Record a message and create its lineage entry."""
        content_hash = hashlib.sha256(content.encode()).hexdigest()[:16]

        # Generate message_id first so we can use it as root_id for root messages
        message_id = uuid4()

        # Determine depth and root
        if parent_message_id:
            parent = self._lineages.get(parent_message_id)
            if parent:
                depth = parent.depth + 1
                root_id = parent.root_message_id
                ancestor_ids = list(parent.ancestor_ids) + [parent_message_id]
            else:
                depth = 0
                root_id = message_id
                ancestor_ids = []
        else:
            depth = 0
            root_id = message_id
            ancestor_ids = []

        lineage = MessageLineage(
            message_id=message_id,
            conversation_id=conversation_id,
            root_message_id=root_id,
            sender_agent_id=sender_agent_id,
            receiver_agent_id=receiver_agent_id,
            content_hash=content_hash,
            content_size_bytes=len(content.encode()),
            parent_message_id=parent_message_id,
            ancestor_ids=ancestor_ids,
            depth=depth,
        )

        self._lineages[lineage.message_id] = lineage
        self._content_hashes[content_hash] = lineage.message_id
        self._last_conversation_id = conversation_id

        # Update child_count on parent
        if parent_message_id:
            parent = self._lineages.get(parent_message_id)
            if parent:
                parent.child_count += 1

        return lineage

    async def get_ancestry(self, message_id: UUID) -> list[MessageLineage]:
        """Get the full ancestry chain for a message."""
        lineage = self._lineages.get(message_id)
        if not lineage:
            return []

        ancestry = []
        current = lineage
        while current.parent_message_id:
            parent = self._lineages.get(current.parent_message_id)
            if parent:
                ancestry.insert(0, parent)
                current = parent
            else:
                break

        ancestry.append(lineage)
        return ancestry

    async def get_descendants(self, message_id: UUID) -> list[MessageLineage]:
        """Get all descendants of a message."""
        descendants = []
        to_visit = [message_id]
        visited: set[UUID] = set()

        while to_visit:
            current_id = to_visit.pop()
            if current_id in visited:
                continue
            visited.add(current_id)

            for lineage in self._lineages.values():
                if lineage.parent_message_id == current_id:
                    descendants.append(lineage)
                    to_visit.append(lineage.message_id)

        return descendants

    async def find_branch_points(self, conversation_id: UUID) -> list[MessageLineage]:
        """Find messages that have multiple children (branch points)."""
        branch_points = []
        for lineage in self._lineages.values():
            if lineage.conversation_id != conversation_id:
                continue
            if lineage.child_count > 1:
                branch_points.append(lineage)
        return branch_points

    async def verify_integrity(self, conversation_id: UUID) -> dict[str, Any]:
        """Verify the integrity of a conversation's lineage."""
        valid = True
        errors: list[str] = []

        for lineage in self._lineages.values():
            if lineage.conversation_id != conversation_id:
                continue

            if lineage.parent_message_id:
                parent = self._lineages.get(lineage.parent_message_id)
                if not parent:
                    valid = False
                    errors.append(f"Missing parent for {lineage.message_id}")

                if lineage.depth != parent.depth + 1:
                    valid = False
                    errors.append(f"Invalid depth for {lineage.message_id}")

        return {"valid": valid, "errors": errors}

    async def get_stats(self, conversation_id: UUID | None = None) -> dict[str, int]:
        """Get statistics about tracked messages."""
        cid = conversation_id or self._last_conversation_id
        if not cid:
            return {"total_messages": 0, "active_messages": 0, "max_depth": 0}
        messages = [l for l in self._lineages.values() if l.conversation_id == cid]

        return {
            "total_messages": len(messages),
            "active_messages": len(messages),  # All messages are "active"
            "max_depth": max((l.depth for l in messages), default=0),
        }


class SnapshotManager:
    """Manages state snapshots for rollback."""

    def __init__(self, config: SnapshotConfig | None = None) -> None:
        self.config = config or SnapshotConfig()
        self._snapshots: dict[str, list[StateSnapshot]] = {}
        self._system_snapshots: list[StateSnapshot] = []

    async def initialize(self) -> None:
        """Initialize the snapshot manager.

        This is a stub/placeholder method.

        What needs to be implemented:
        - Initialize underlying storage (database, file system, etc.)
        - Set up snapshot cleanup scheduled task
        - Restore any pending snapshots from previous sessions

        Returns:
            None
        """
        pass

    async def shutdown(self) -> None:
        """Shutdown the snapshot manager.

        This is a stub/placeholder method.

        What needs to be implemented:
        - Gracefully close underlying storage connections
        - Flush any pending snapshots to disk
        - Cancel any scheduled cleanup tasks

        Returns:
            None
        """
        pass

    async def create_snapshot(
        self,
        agent_states: dict[str, AgentState] | None = None,
        system_state: SystemState | None = None,
        trigger: str = "manual",
        description: str = "",
    ) -> StateSnapshot:
        """Create a new snapshot with system and agent state."""
        if system_state is None:
            system_state = SystemState()
        agent_states_dict = {}
        if agent_states:
            for agent_id, state in agent_states.items():
                agent_states_dict[agent_id] = state.working_memory

        snapshot = StateSnapshot(
            agent_id="system",
            state={
                "system": system_state.__dict__,
                "agents": agent_states_dict,
            },
            version=len(self._system_snapshots) + 1,
            trigger=trigger,
            description=description,
            system_state=system_state,
            agent_states=agent_states_dict,
            metadata={
                "trigger": trigger,
                "description": description,
                "system_state": system_state.__dict__,
                "agent_states": agent_states_dict,
            },
        )
        self._system_snapshots.append(snapshot)
        return snapshot

    async def get_snapshot(self, snapshot_id: UUID) -> StateSnapshot | None:
        """Get a snapshot by ID."""
        for snap in self._system_snapshots:
            if snap.snapshot_id == snapshot_id:
                return snap
        return None

    async def list_snapshots(self) -> list[StateSnapshot]:
        """List all snapshots."""
        return sorted(self._system_snapshots, key=lambda s: s.created_at)

    async def delete_snapshot(self, snapshot_id: UUID) -> bool:
        """Delete a snapshot by ID."""
        for i, snap in enumerate(self._system_snapshots):
            if snap.snapshot_id == snapshot_id:
                del self._system_snapshots[i]
                return True
        return False

    async def compute_diff(self, snapshot1_id: UUID, snapshot2_id: UUID) -> dict[str, Any]:
        """Compute diff between two snapshots."""
        snap1 = await self.get_snapshot(snapshot1_id)
        snap2 = await self.get_snapshot(snapshot2_id)

        if not snap1 or not snap2:
            return {"error": "Snapshot not found"}

        diff = {
            "added": {},
            "removed": {},
            "changed": {},
        }

        s1_agents = snap1.state.get("agents", {})
        s2_agents = snap2.state.get("agents", {})

        for agent_id in s2_agents:
            if agent_id not in s1_agents:
                diff["added"][agent_id] = s2_agents[agent_id]
            elif s1_agents[agent_id] != s2_agents[agent_id]:
                diff["changed"][agent_id] = {
                    "from": s1_agents[agent_id],
                    "to": s2_agents[agent_id],
                }

        for agent_id in s1_agents:
            if agent_id not in s2_agents:
                diff["removed"][agent_id] = s1_agents[agent_id]

        return diff


class StateManager:
    """Manages agent state lifecycle."""

    def __init__(self, config: StateConfig | None = None) -> None:
        self.config = config or StateConfig()
        self._states: dict[str, AgentState] = {}
        self._conversations: dict[UUID, ConversationState] = {}
        self._lineage_tracker = LineageTracker(self.config.lineage)
        self._snapshot_manager = SnapshotManager(self.config.snapshots)

    async def initialize(self) -> None:
        """Initialize the state manager.

        State is managed in-memory via _states dict. No external storage to initialize.
        """
        pass

    async def shutdown(self) -> None:
        """Shutdown the state manager."""
        from heretek_swarm.infrastructure.otel.logging import get_logger
        logger = get_logger(__name__)
        logger.info("state_manager_shutdown")

    async def register_agent(self, agent_id: str, agent_type: str = "worker") -> AgentState:
        """Register a new agent."""
        state = AgentState(agent_id=agent_id, agent_type=agent_type)
        self._states[agent_id] = state
        return state

    async def update_agent_state(self, agent_id: str, **kwargs: Any) -> AgentState | None:
        """Update an agent's state."""
        return await self.update_state(agent_id, **kwargs)

    async def start_conversation(
        self,
        initiator_agent_id: str,
        participant_ids: list[str] | None = None,
        topic: str = "",
    ) -> ConversationState:
        """Start a new conversation."""
        conv = ConversationState(
            initiator_agent_id=initiator_agent_id,
            participant_ids=participant_ids or [initiator_agent_id],
            topic=topic,
        )
        self._conversations[conv.conversation_id] = conv
        return conv

    async def record_message(
        self,
        conversation_id: UUID,
        sender_agent_id: str,
        content: str,
        receiver_agent_id: str | None = None,
        parent_message_id: UUID | None = None,
    ) -> MessageLineage:
        """Record a message in a conversation."""
        lineage = await self._lineage_tracker.record_message(
            content=content,
            conversation_id=conversation_id,
            sender_agent_id=sender_agent_id,
            receiver_agent_id=receiver_agent_id,
            parent_message_id=parent_message_id,
        )
        return lineage

    async def create_snapshot(self, trigger: str = "manual", description: str = "") -> StateSnapshot:
        """Create a snapshot of current state."""
        system_state = SystemState(active_agents=len(self._states))
        return await self._snapshot_manager.create_snapshot(
            system_state=system_state,
            agent_states=self._states,
            trigger=trigger,
            description=description,
        )

    async def rollback_to_snapshot(self, snapshot_id: UUID) -> bool:
        """Rollback to a previous snapshot."""
        snapshot = await self._snapshot_manager.get_snapshot(snapshot_id)
        if not snapshot:
            return False

        # Restore agent states from snapshot
        agent_states_data = snapshot.state.get("agents", {})
        self._states.clear()
        for agent_id, state_data in agent_states_data.items():
            state = AgentState(
                agent_id=agent_id,
                agent_type=state_data.get("agent_type", "worker"),
                status=StateStatus(state_data.get("status", "active")),
                version=state_data.get("version", 1),
            )
            self._states[agent_id] = state
        return True

    async def get_stats(self) -> dict[str, Any]:
        """Get system-wide statistics."""
        return {
            "agents": {
                "total": len(self._states),
                "active": len([s for s in self._states.values() if s.status == StateStatus.ACTIVE]),
            },
            "conversations": {
                "total": len(self._conversations),
            },
        }

    def create_state(self, agent_id: str, agent_type: str = "worker") -> AgentState:
        """Create a new agent state."""
        state = AgentState(agent_id=agent_id, agent_type=agent_type)
        self._states[agent_id] = state
        return state

    def get_state(self, agent_id: str) -> AgentState | None:
        """Get an agent's state."""
        return self._states.get(agent_id)

    async def update_state(self, agent_id: str, **kwargs: Any) -> AgentState | None:
        """Update an agent's state."""
        state = self._states.get(agent_id)
        if not state:
            return None
        for key, value in kwargs.items():
            if hasattr(state, key):
                setattr(state, key, value)
        state.touch()
        return state

    async def get_active_agents(self) -> list[AgentState]:
        """Get all active agents."""
        return [s for s in self._states.values() if s.status == StateStatus.ACTIVE]

    @property
    def lineage(self) -> LineageTracker:
        """Get the lineage tracker for message ancestry."""
        return self._lineage_tracker

    async def complete_conversation(self, conversation_id: UUID) -> ConversationState | None:
        """Complete a conversation."""
        conv = self._conversations.get(conversation_id)
        if not conv:
            return None
        conv.status = StateStatus.COMPLETED
        return conv
