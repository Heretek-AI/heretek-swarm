# State Management System Documentation

## Overview

The State Management System provides unified state management for multi-agent systems, integrating lineage tracking, snapshots, and state transitions. It enables complete provenance tracking, state rollback capabilities, and automatic recovery.

## Core Architecture

### StateManager

**Location**: [`src/state/manager.py`](../src/state/manager.py)

The [`StateManager`](../src/state/manager.py:55) class provides comprehensive state management with:

- **Agent State Lifecycle**: Track agent states throughout their lifecycle
- **Conversation State**: Manage conversation state and context
- **Message Lineage**: Complete provenance tracking for all messages
- **Snapshots & Rollback**: Capture and restore system states
- **State Transitions**: Track all state changes with history
- **Automatic Recovery**: Self-healing from failures

### System Architecture

```
┌─────────────────────────────────────────────────────┐
│              StateManager                          │
│                                                   │
│  ┌──────────────┐  ┌──────────────┐            │
│  │ Lineage      │  │ Snapshots    │            │
│  │ Tracker      │  │ Manager      │            │
│  └──────────────┘  └──────────────┘            │
│                                                   │
│  ┌──────────────────────────────────────────────┐   │
│  │           State Storage                     │   │
│  │                                          │   │
│  │  ┌──────────┐  ┌────────────┐           │   │
│  │  │ Agents   │  │Conversations│           │   │
│  │  └──────────┘  └────────────┘           │   │
│  │  ┌──────────────────────────────────┐      │   │
│  │  │     System State              │      │   │
│  │  └──────────────────────────────────┘      │   │
│  └──────────────────────────────────────────────┘   │
│                                                   │
│  ┌──────────────────────────────────────────────┐   │
│  │        Transition History                  │   │
│  └──────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────┘
```

## Data Structures

### StateStatus

```python
class StateStatus(str, Enum):
    """Status of a state"""
    ACTIVE = "active"
    SUSPENDED = "suspended"
    COMPLETED = "completed"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"
```

### TransitionType

```python
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
```

### MessageLineage

```python
class MessageLineage(BaseModel):
    """Tracks the provenance and lineage of a message."""
    
    # Identity
    message_id: UUID              # Unique message ID
    conversation_id: UUID          # Conversation/session ID
    
    # Parentage
    parent_message_id: Optional[UUID]  # Direct parent
    root_message_id: UUID               # Root of conversation tree
    
    # Ancestry chain
    ancestor_ids: List[UUID]      # All ancestors
    depth: int                   # Depth in conversation tree
    
    # Message metadata
    message_type: MessageType     # Type of message
    sender_agent_id: str         # Sending agent
    receiver_agent_id: Optional[str]  # Receiving agent
    
    # Content hash for integrity
    content_hash: str            # SHA256 hash of content
    content_size_bytes: int      # Size in bytes
    
    # Timestamps
    created_at: datetime         # Creation timestamp
    delivered_at: Optional[datetime]  # Delivery timestamp
    processed_at: Optional[datetime]  # Processing timestamp
    
    # State
    is_branch_point: bool        # Can fork from here
    child_count: int            # Number of children
    
    # Metadata
    correlation_id: Optional[UUID]  # Correlates related messages
    tags: List[str]            # Search tags
    metadata: Dict[str, Any]    # Additional metadata
```

### StateTransition

```python
class StateTransition(BaseModel):
    """Represents a state transition."""
    
    transition_id: UUID         # Unique transition ID
    state_id: UUID             # State being transitioned
    from_status: StateStatus    # Previous status
    to_status: StateStatus      # New status
    transition_type: TransitionType  # Type of transition
    
    # Context
    agent_id: Optional[str]     # Agent that caused transition
    conversation_id: Optional[UUID]  # Related conversation
    
    # Timestamps
    timestamp: datetime         # When transition occurred
    duration_ms: float        # Transition duration
    
    # Details
    reason: Optional[str]      # Reason for transition
    metadata: Dict[str, Any]   # Additional metadata
```

### AgentState

```python
class AgentState(BaseModel):
    """State of an individual agent."""
    
    agent_id: str             # Agent identifier
    status: StateStatus       # Current status
    created_at: datetime      # Creation timestamp
    updated_at: datetime      # Last update timestamp
    
    # State data
    internal_state: Dict[str, Any]  # Internal agent state
    message_count: int               # Messages processed
    error_count: int                # Errors encountered
    
    # Relationships
    conversations: List[UUID]   # Active conversations
    
    # Metadata
    tags: List[str]            # Search tags
    metadata: Dict[str, Any]    # Additional metadata
```

### ConversationState

```python
class ConversationState(BaseModel):
    """State of a conversation."""
    
    conversation_id: UUID       # Unique conversation ID
    status: StateStatus        # Current status
    created_at: datetime       # Creation timestamp
    updated_at: datetime       # Last update timestamp
    
    # Participants
    participants: List[str]    # Participating agent IDs
    
    # Messages
    message_count: int         # Total messages
    root_message_id: UUID      # Root message of conversation
    
    # State
    context: Dict[str, Any]    # Conversation context
    metadata: Dict[str, Any]    # Additional metadata
```

### SystemState

```python
class SystemState(BaseModel):
    """Overall system state."""
    
    system_id: UUID           # Unique system ID
    status: StateStatus       # Current status
    created_at: datetime      # Creation timestamp
    updated_at: datetime      # Last update timestamp
    
    # Counts
    agent_count: int          # Total agents
    conversation_count: int    # Total conversations
    message_count: int        # Total messages
    
    # Health
    health_score: float       # System health (0.0-1.0)
    uptime_seconds: float     # System uptime
    
    # Metadata
    metadata: Dict[str, Any]  # Additional metadata
```

## Core Components

### StateManager

**Location**: [`src/state/manager.py`](../src/state/manager.py:55)

The main state management class.

**Features**:
- Unified state management
- Lineage tracking integration
- Snapshot and rollback support
- Automatic recovery
- State synchronization

**Key Methods**:

#### Initialization

```python
from src.state.manager import StateManager, StateConfig

# Create state manager
config = StateConfig(
    max_agents=1000,
    max_conversations_per_agent=100,
    state_sync_interval_seconds=60,
    auto_recovery_enabled=True
)

state_manager = StateManager(config)

# Initialize
await state_manager.initialize()
```

#### Agent State Management

```python
# Register agent
await state_manager.register_agent(
    agent_id="alpha",
    initial_state={"role": "analyst"}
)

# Update agent state
await state_manager.update_agent_state(
    agent_id="alpha",
    updates={"status": "active", "task": "analyzing"}
)

# Get agent state
agent_state = state_manager.get_agent_state("alpha")

# Unregister agent
await state_manager.unregister_agent("alpha")
```

#### Conversation State Management

```python
# Create conversation
conversation_id = await state_manager.create_conversation(
    participants=["alpha", "beta", "charlie"],
    context={"topic": "deployment decision"}
)

# Update conversation
await state_manager.update_conversation(
    conversation_id=conversation_id,
    updates={"status": "in_progress"}
)

# Get conversation state
conv_state = state_manager.get_conversation_state(conversation_id)

# Close conversation
await state_manager.close_conversation(conversation_id)
```

#### Message Lineage Tracking

```python
# Track message
lineage = await state_manager.track_message(
    message_id=uuid4(),
    conversation_id=conversation_id,
    parent_message_id=parent_id,
    sender_agent_id="alpha",
    receiver_agent_id="beta",
    message_type=MessageType.TASK,
    content={"data": "message content"}
)

# Get message lineage
lineage = state_manager.get_message_lineage(message_id)

# Get conversation tree
tree = state_manager.get_conversation_tree(conversation_id)
```

#### State Transitions

```python
# Record transition
await state_manager.record_transition(
    state_id=agent_id,
    from_status=StateStatus.SUSPENDED,
    to_status=StateStatus.ACTIVE,
    transition_type=TransitionType.UPDATE,
    agent_id="alpha",
    reason="Resumed from suspension"
)

# Get transition history
history = state_manager.get_transition_history(
    state_id=agent_id,
    limit=10
)
```

#### Snapshots

```python
# Create snapshot
snapshot_id = await state_manager.create_snapshot(
    scope="system",
    trigger="pre_deployment",
    metadata={"deployment_id": "deploy-123"}
)

# List snapshots
snapshots = await state_manager.list_snapshots(scope="system")

# Restore from snapshot
await state_manager.restore_snapshot(snapshot_id)

# Delete snapshot
await state_manager.delete_snapshot(snapshot_id)
```

#### Rollback

```python
# Rollback to specific state
await state_manager.rollback_to_state(
    state_id=agent_id,
    target_state_id=target_id,
    reason="Error in processing"
)

# Rollback to snapshot
await state_manager.rollback_to_snapshot(
    snapshot_id=snapshot_id,
    reason="Deployment failed"
)
```

### LineageTracker

**Location**: [`src/state/lineage.py`](../src/state/lineage.py)

Tracks message lineage and provenance.

**Features**:
- Complete message ancestry tracking
- Conversation tree construction
- Branch point identification
- Lineage queries and traversal

**Example**:

```python
from src.state.lineage import LineageTracker, LineageConfig

# Create tracker
config = LineageConfig(
    max_depth=100,
    max_branches=1000
)

tracker = LineageTracker(config)

# Track message
await tracker.track_message(lineage_data)

# Get ancestry
ancestry = await tracker.get_ancestry(message_id)

# Get descendants
descendants = await tracker.get_descendants(message_id)

# Find common ancestor
common = await tracker.find_common_ancestor(msg1_id, msg2_id)
```

### SnapshotManager

**Location**: [`src/state/snapshots.py`](../src/state/snapshots.py)

Manages state snapshots.

**Features**:
- State capture and restoration
- Snapshot metadata
- Automatic cleanup
- Compression and storage

**Example**:

```python
from src.state.snapshots import SnapshotManager, SnapshotConfig

# Create manager
config = SnapshotConfig(
    max_snapshots=100,
    retention_days=30,
    auto_snapshot_interval=3600
)

manager = SnapshotManager(config)

# Create snapshot
snapshot = await manager.create_snapshot(
    scope="system",
    state_data=system_state,
    trigger="manual",
    metadata={"reason": "Before deployment"}
)

# Restore snapshot
state = await manager.restore_snapshot(snapshot.snapshot_id)

# List snapshots
snapshots = await manager.list_snapshots(scope="system")
```

## Usage Examples

### Basic Usage

```python
from src.state.manager import StateManager

# Create state manager
state_manager = StateManager()

# Initialize
await state_manager.initialize()

# Register agent
await state_manager.register_agent(
    agent_id="alpha",
    initial_state={"role": "analyst"}
)

# Create conversation
conv_id = await state_manager.create_conversation(
    participants=["alpha", "beta"],
    context={"topic": "analysis"}
)

# Track message
await state_manager.track_message(
    message_id=uuid4(),
    conversation_id=conv_id,
    sender_agent_id="alpha",
    receiver_agent_id="beta",
    message_type=MessageType.TASK,
    content={"task": "analyze data"}
)

# Get state
agent_state = state_manager.get_agent_state("alpha")
```

### With Snapshots

```python
# Create snapshot before critical operation
snapshot_id = await state_manager.create_snapshot(
    scope="system",
    trigger="pre_deployment"
)

# Perform operation
try:
    await perform_deployment()
except Exception as e:
    # Rollback on failure
    await state_manager.rollback_to_snapshot(snapshot_id)
    logger.error(f"Deployment failed, rolled back: {e}")
```

### With Lineage Tracking

```python
# Track complete message flow
for message in message_stream:
    await state_manager.track_message(
        message_id=message.id,
        conversation_id=message.conversation_id,
        parent_message_id=message.parent_id,
        sender_agent_id=message.sender,
        receiver_agent_id=message.receiver,
        message_type=MessageType.TASK,
        content=message.content
    )

# Get conversation tree
tree = state_manager.get_conversation_tree(conversation_id)

# Analyze flow
for node in tree:
    print(f"Message {node.message_id} from {node.sender}")
```

### With State Transitions

```python
# Record agent lifecycle transitions
await state_manager.register_agent("alpha")
await state_manager.record_transition(
    state_id="alpha",
    from_status=StateStatus.SUSPENDED,
    to_status=StateStatus.ACTIVE,
    transition_type=TransitionType.UPDATE
)

# Get transition history
history = state_manager.get_transition_history("alpha")
for transition in history:
    print(f"{transition.from_status} -> {transition.to_status}")
```

## Best Practices

### 1. State Design

- Keep state minimal and focused
- Use structured state data
- Document state schema
- Version state structures

### 2. Lineage Tracking

- Track all messages consistently
- Use meaningful correlation IDs
- Maintain conversation boundaries
- Clean up old lineage data

### 3. Snapshots

- Create snapshots before critical operations
- Use descriptive triggers
- Implement retention policies
- Compress large snapshots

### 4. Transitions

- Record all state changes
- Include meaningful reasons
- Use appropriate transition types
- Monitor transition patterns

### 5. Recovery

- Enable automatic recovery
- Set appropriate timeouts
- Monitor recovery events
- Test rollback procedures

## Performance Considerations

### Memory Usage

- State storage grows with agent count
- Lineage tracking can be memory-intensive
- Snapshots consume significant memory
- Implement cleanup policies

### Query Performance

- Index frequently queried fields
- Use pagination for large result sets
- Cache common queries
- Optimize lineage queries

### Persistence

- Batch state changes
- Use efficient serialization
- Compress snapshot data
- Implement incremental updates

## Troubleshooting

### Common Issues

1. **State Not Found**
   - Verify state ID
   - Check if state was deleted
   - Review state lifecycle

2. **Lineage Too Deep**
   - Implement depth limits
   - Prune old lineage data
   - Use pagination

3. **Snapshot Too Large**
   - Compress snapshot data
   - Exclude unnecessary fields
   - Use incremental snapshots

4. **Recovery Fails**
   - Check snapshot integrity
   - Verify state consistency
   - Review recovery logs

## API Reference

### StateManager

See [`src/state/manager.py`](../src/state/manager.py) for complete API documentation.

### LineageTracker

See [`src/state/lineage.py`](../src/state/lineage.py) for complete API documentation.

### SnapshotManager

See [`src/state/snapshots.py`](../src/state/snapshots.py) for complete API documentation.

## See Also

- [Actors System](./actors-system.md)
- [Memory System](./memory-system.md)
- [Orchestration System](./orchestration-system.md)
- [Tools System](./tools-system.md)
