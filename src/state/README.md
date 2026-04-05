# State Management System

A comprehensive state management system for multi-agent AI systems, providing message lineage tracking, state snapshots, and rollback capabilities.

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                  State Manager                           │
│  ┌─────────────────────────────────────────────────┐    │
│  │            Unified State API                     │    │
│  └─────────────────────────────────────────────────┘    │
│                                                          │
│  ┌─────────────────┐  ┌─────────────────┐              │
│  │   Lineage       │  │   Snapshots     │              │
│  │   Tracker       │  │   Manager       │              │
│  └─────────────────┘  └─────────────────┘              │
│         │                     │                          │
│         └─────────┬───────────┘                          │
│                   │                                      │
│  ┌────────────────▼────────────────┐                    │
│  │       State Storage             │                    │
│  │  (In-Memory + Dual-Tier Memory) │                    │
│  └─────────────────────────────────┘                    │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

## Features

- **Message Lineage Tracking**: Complete provenance for all messages with ancestry queries
- **State Snapshots**: Full and incremental snapshots with compression
- **Rollback Capability**: Restore system to any previous snapshot
- **Agent State Management**: Lifecycle management for agent states
- **Conversation Tracking**: Multi-agent conversation state with history
- **Transition Recording**: Audit trail of all state changes
- **Branch Point Detection**: Identify where conversations diverge
- **Integrity Verification**: Verify message chain integrity

## Installation

```bash
pip install heretek-swarm
```

## Quick Start

```python
from heretek_swarm.state import StateManager, StateConfig
import asyncio

async def main():
    # Initialize state manager
    config = StateConfig(
        snapshots=SnapshotConfig(
            storage_path="/var/lib/heretek/snapshots",
            auto_snapshot_enabled=True,
            auto_snapshot_interval_minutes=30
        )
    )
    
    state = StateManager(config)
    await state.initialize()
    
    # Register agents
    agent1 = await state.register_agent(
        agent_id="coordinator",
        agent_type="coordinator"
    )
    
    agent2 = await state.register_agent(
        agent_id="worker-1",
        agent_type="worker",
        parent_agent_id="coordinator"
    )
    
    # Start a conversation
    conv = await state.start_conversation(
        initiator_agent_id="coordinator",
        participant_ids={"coordinator", "worker-1"},
        topic="Data Analysis Task"
    )
    
    # Record messages with lineage
    msg1 = await state.record_message(
        conversation_id=conv.conversation_id,
        sender_agent_id="coordinator",
        content="Please analyze the dataset",
        receiver_agent_id="worker-1"
    )
    
    msg2 = await state.record_message(
        conversation_id=conv.conversation_id,
        sender_agent_id="worker-1",
        content="Analysis complete. Found 3 patterns.",
        receiver_agent_id="coordinator",
        parent_message_id=msg1.message_id
    )
    
    # Query lineage
    ancestry = await state.lineage.get_ancestry(msg2.message_id)
    print(f"Message chain length: {len(ancestry)}")
    
    # Create snapshot
    snapshot = await state.create_snapshot(
        trigger="checkpoint",
        description="After analysis complete"
    )
    
    # Complete conversation
    await state.complete_conversation(conv.conversation_id)
    
    # Get statistics
    stats = state.get_stats()
    print(f"Agents: {stats['agents']['active']}")
    print(f"Messages tracked: {stats['lineage']['total_messages']}")
    
    # Cleanup
    await state.shutdown()

asyncio.run(main())
```

## Core Components

### LineageTracker

Tracks message provenance and relationships.

```python
from heretek_swarm.state import LineageTracker, LineageConfig

config = LineageConfig(
    max_lineage_depth=100,
    cache_size=10000,
    enable_branching=True
)

tracker = LineageTracker(config)

# Record a message
lineage = await tracker.record_message(
    content="Task request",
    conversation_id=conv_id,
    sender_agent_id="agent-1",
    receiver_agent_id="agent-2"
)

# Get ancestry
ancestry = await tracker.get_ancestry(message_id)

# Find branch points
branches = await tracker.find_branch_points(conversation_id)
```

### SnapshotManager

Manages state snapshots with rollback support.

```python
from heretek_swarm.state import SnapshotManager, SnapshotConfig

config = SnapshotConfig(
    storage_path="/var/lib/heretek/snapshots",
    max_snapshots=100,
    compress_snapshots=True,
    auto_snapshot_enabled=True,
    auto_snapshot_interval_minutes=60
)

manager = SnapshotManager(config)
await manager.initialize()

# Create snapshot
snapshot = await manager.create_snapshot(
    system_state=system,
    agent_states=agents,
    trigger="manual",
    description="Pre-deployment checkpoint"
)

# List snapshots
snapshots = await manager.list_snapshots(scope="system")

# Compute diff
diff = await manager.compute_diff(snapshot1_id, snapshot2_id)

# Cleanup
await manager.shutdown()
```

### StateManager

Unified state management combining all components.

```python
from heretek_swarm.state import StateManager, StateConfig

config = StateConfig(
    max_agents=1000,
    auto_recovery_enabled=True,
    state_sync_interval_seconds=60
)

state = StateManager(config)
await state.initialize()

# Agent management
agent = await state.register_agent("agent-1", "worker")
agent = await state.update_agent_state("agent-1", {"task": "new"})
agents = await state.get_active_agents()

# Conversation management
conv = await state.start_conversation("agent-1", topic="Task")
await state.update_conversation_state(conv.conversation_id, 
    decision={"action": "approved", "by": "agent-1"}
)
await state.complete_conversation(conv.conversation_id)

# Snapshots
snapshot = await state.create_snapshot(trigger="checkpoint")
success = await state.rollback_to_snapshot(snapshot.snapshot_id)

# Cleanup
await state.shutdown()
```

## State Models

### AgentState

```python
class AgentState:
    agent_id: str
    agent_type: str
    status: StateStatus  # ACTIVE, SUSPENDED, COMPLETED, FAILED
    
    working_memory: Dict[str, Any]
    context: Dict[str, Any]
    
    conversation_ids: Set[UUID]
    active_conversation_id: Optional[UUID]
    
    parent_agent_id: Optional[str]
    child_agent_ids: Set[str]
    
    messages_sent: int
    messages_received: int
    tasks_completed: int
    tasks_failed: int
    
    version: int
    state_hash: str
```

### ConversationState

```python
class ConversationState:
    conversation_id: UUID
    initiator_agent_id: str
    participant_ids: Set[str]
    
    status: StateStatus
    topic: Optional[str]
    goal: Optional[str]
    
    root_message_id: Optional[UUID]
    latest_message_id: Optional[UUID]
    message_count: int
    
    context: Dict[str, Any]
    decisions: List[Dict[str, Any]]
    artifacts: List[Dict[str, Any]]
    
    version: int
```

### MessageLineage

```python
class MessageLineage:
    message_id: UUID
    conversation_id: UUID
    
    parent_message_id: Optional[UUID]
    root_message_id: UUID
    ancestor_ids: List[UUID]
    depth: int
    
    message_type: MessageType
    sender_agent_id: str
    receiver_agent_id: Optional[str]
    
    content_hash: str
    content_size_bytes: int
    
    is_branch_point: bool
    child_count: int
```

## API Reference

### StateManager Methods

| Method | Description |
|--------|-------------|
| `register_agent()` | Register a new agent |
| `get_agent_state()` | Get agent's current state |
| `update_agent_state()` | Update agent state |
| `update_agent_status()` | Change agent status |
| `deregister_agent()` | Remove agent |
| `start_conversation()` | Start new conversation |
| `get_conversation_state()` | Get conversation state |
| `update_conversation_state()` | Update conversation |
| `complete_conversation()` | End conversation |
| `record_message()` | Record message with lineage |
| `create_snapshot()` | Create state snapshot |
| `rollback_to_snapshot()` | Restore from snapshot |
| `get_stats()` | Get system statistics |

## Performance

| Operation | Target | Typical |
|-----------|--------|---------|
| State Update | <5ms | 1-3ms |
| Message Recording | <10ms | 3-8ms |
| Snapshot Creation | <500ms | 100-300ms |
| Rollback | <1s | 200-500ms |
| Lineage Query | <50ms | 10-30ms |

## Testing

```bash
# Run tests
pytest tests/state/ -v

# Run with coverage
pytest tests/state/ --cov=src/state --cov-report=html
```

## Configuration Options

### StateConfig

| Option | Default | Description |
|--------|---------|-------------|
| `max_agents` | 1000 | Maximum concurrent agents |
| `max_conversations_per_agent` | 100 | Conversations per agent |
| `state_sync_interval_seconds` | 60 | Auto-sync interval |
| `auto_recovery_enabled` | true | Enable auto recovery |
| `recovery_timeout_seconds` | 300 | Recovery timeout |
| `persist_state_changes` | true | Persist to memory system |

### LineageConfig

| Option | Default | Description |
|--------|---------|-------------|
| `max_lineage_depth` | 100 | Max message depth |
| `max_children_per_node` | 100 | Max branches per message |
| `max_lineage_entries` | 100000 | Max tracked messages |
| `cache_size` | 10000 | LRU cache size |
| `enable_branching` | true | Track branch points |
| `enable_replay` | true | Support message replay |

### SnapshotConfig

| Option | Default | Description |
|--------|---------|-------------|
| `storage_path` | /var/lib/heretek/snapshots | Snapshot storage |
| `max_snapshots` | 100 | Maximum snapshots |
| `max_snapshot_size_mb` | 100 | Max size per snapshot |
| `default_retention_days` | 30 | Retention period |
| `compress_snapshots` | true | GZIP compression |
| `auto_snapshot_enabled` | true | Automatic snapshots |
| `auto_snapshot_interval_minutes` | 60 | Auto snapshot interval |
| `max_rollback_depth` | 10 | Max versions to rollback |

## License

Apache 2.0
