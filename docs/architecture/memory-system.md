# Memory System Documentation

## Overview

The Memory System provides a dual-tier architecture for managing both short-term working memory and long-term persistent storage. It supports automatic tiering, semantic search via vector embeddings, memory lineage tracking, and state snapshot/rollback capabilities.

## Core Architecture

### Dual-Tier Design

The memory system consists of two layers:

1. **Ephemeral Memory Layer**: Fast, session-based working memory with TTL (Time-To-Live)
2. **Persistent Memory Layer**: Long-term vector-based storage with semantic search

```
┌─────────────────────────────────────────┐
│         Memory System Interface         │
│         (DualTierMemory)               │
└──────────────┬──────────────────────────┘
               │
       ┌───────┴───────┐
       │               │
       ▼               ▼
┌──────────────┐  ┌──────────────┐
│  Ephemeral   │  │  Persistent  │
│   Memory     │  │   Memory     │
│              │  │              │
│ - Fast       │  │ - Long-term  │
│ - TTL-based  │  │ - Vector DB  │
│ - Session    │  │ - Semantic   │
└──────────────┘  └──────────────┘
```

### Key Features

- **Automatic Tiering**: Automatically routes memories to appropriate tier
- **Semantic Search**: Vector-based similarity search for relevant memories
- **Memory Lineage**: Tracks parent-child relationships for provenance
- **TTL Management**: Automatic expiration of ephemeral memories
- **State Snapshots**: Capture and restore memory states
- **Rollback Support**: Revert to previous memory states

## Data Structures

### MemoryEntry

```python
@dataclass
class MemoryEntry:
    """A single memory entry."""
    
    id: str                      # Unique identifier
    content: Dict[str, Any]       # Memory content
    metadata: Dict[str, Any]      # Additional metadata
    created_at: str               # Creation timestamp
    expires_at: Optional[str]     # Expiration timestamp (ephemeral)
    lineage: List[str]            # Parent IDs for provenance
    embedding: Optional[List[float]] # Vector embedding
```

### MemoryQuery

```python
@dataclass
class MemoryQuery:
    """Memory query parameters."""
    
    query_text: Optional[str] = None           # Text to search for
    filters: Optional[Dict[str, Any]] = None   # Metadata filters
    limit: int = 10                            # Maximum results
    similarity_threshold: float = 0.7           # Minimum similarity
    include_expired: bool = False               # Include expired entries
```

## Core Components

### MemorySystem (Abstract Base)

**Location**: [`src/heretek_swarm/memory/base.py`](../src/heretek_swarm/memory/base.py)

The [`MemorySystem`](../src/heretek_swarm/memory/base.py:69) is the abstract base class for all memory implementations.

**Core Methods**:

- [`initialize()`](../src/heretek_swarm/memory/base.py:89): Initialize the memory system
- [`store()`](../src/heretek_swarm/memory/base.py:94): Store a memory entry
- [`retrieve()`](../src/heretek_swarm/memory/base.py:116): Retrieve a memory by ID
- [`query()`](../src/heretek_swarm/memory/base.py:129): Query memory entries
- [`delete()`](../src/heretek_swarm/memory/base.py:142): Delete a memory entry
- [`clear()`](../src/heretek_swarm/memory/base.py): Clear all memories

### Ephemeral Memory

**Location**: [`src/memory/ephemeral.py`](../src/memory/ephemeral.py)

Fast, in-memory storage with TTL support.

**Features**:
- In-memory storage for speed
- TTL-based expiration
- Automatic cleanup of expired entries
- Metadata filtering
- Lineage tracking

**Example**:

```python
from heretek_swarm.memory import EphemeralMemory

memory = EphemeralMemory()
await memory.initialize()

# Store with TTL (1 hour)
entry = await memory.store(
    content={"key": "value"},
    metadata={"type": "working_memory"},
    ttl=3600
)

# Retrieve
retrieved = await memory.retrieve(entry.id)

# Query
results = await memory.query(
    filters={"type": "working_memory"},
    limit=10
)
```

### Persistent Memory

**Location**: [`src/memory/persistent.py`](../src/memory/persistent.py)

Long-term storage with vector embeddings for semantic search.

**Features**:
- Vector-based storage (PGVector)
- Semantic similarity search
- Persistent across sessions
- Metadata indexing
- Lineage tracking

**Example**:

```python
from heretek_swarm.memory import PersistentMemory

memory = PersistentMemory(
    connection_string="postgresql://user:pass@localhost/db"
)
await memory.initialize()

# Store persistently
entry = await memory.store(
    content={"key": "value"},
    metadata={"type": "long_term_memory"},
    persistent=True
)

# Semantic search
results = await memory.query(
    query_text="similar content",
    similarity_threshold=0.8,
    limit=5
)
```

### DualTierMemory

**Location**: [`src/memory/unified.py`](../src/memory/unified.py)

Unified interface that automatically routes memories to appropriate tier.

**Features**:
- Automatic tier selection
- Transparent fallback
- Unified query interface
- Cross-tier search
- Intelligent caching

**Example**:

```python
from heretek_swarm.memory import DualTierMemory

memory = DualTierMemory()
await memory.initialize()

# Store with TTL (goes to ephemeral)
entry1 = await memory.store(
    content={"session_data": "value"},
    metadata={"type": "session"},
    ttl=3600
)

# Store persistently (goes to persistent)
entry2 = await memory.store(
    content={"important_data": "value"},
    metadata={"type": "important"},
    persistent=True
)

# Query searches both tiers
results = await memory.query(
    query_text="data",
    limit=10
)
```

## Memory Lineage

### Tracking Provenance

Memory lineage tracks the parent-child relationships between memories:

```python
# Store parent memory
parent = await memory.store(
    content={"original": "data"},
    metadata={"type": "original"}
)

# Store child memory with lineage
child = await memory.store(
    content={"derived": "data"},
    metadata={"type": "derived"},
    lineage=[parent.id]
)

# Retrieve lineage
lineage = await memory.get_lineage(child.id)
# Returns: [parent.id, child.id]
```

### Lineage Benefits

- **Provenance Tracking**: Trace how memories were created
- **Debugging**: Understand memory flow
- **Rollback**: Revert to previous states
- **Audit**: Complete history of changes

## State Snapshots

### Creating Snapshots

Capture the entire memory state at a point in time:

```python
# Create snapshot
snapshot_id = await memory.create_snapshot(
    name="pre-deployment",
    metadata={"reason": "before deployment"}
)

# List snapshots
snapshots = await memory.list_snapshots()

# Restore snapshot
await memory.restore_snapshot(snapshot_id)
```

### Snapshot Benefits

- **State Preservation**: Save memory state before critical operations
- **Rollback**: Revert to previous states if needed
- **Testing**: Test different scenarios with clean states
- **Debugging**: Investigate issues by restoring previous states

## Query Operations

### Metadata Filtering

Filter memories by metadata:

```python
results = await memory.query(
    filters={
        "type": "working_memory",
        "source": "alpha",
        "priority": {"$gte": 5}
    },
    limit=10
)
```

### Semantic Search

Search by semantic similarity:

```python
results = await memory.query(
    query_text="deployment decision",
    similarity_threshold=0.8,
    limit=5
)
```

### Hybrid Queries

Combine semantic search with metadata filters:

```python
results = await memory.query(
    query_text="decision",
    filters={"type": "decision"},
    similarity_threshold=0.7,
    limit=10
)
```

## TTL Management

### Setting TTL

Set time-to-live for ephemeral memories:

```python
# Store with TTL (1 hour)
entry = await memory.store(
    content={"temp": "data"},
    ttl=3600  # 1 hour in seconds
)

# Update TTL
await memory.update_ttl(entry.id, ttl=7200)  # Extend to 2 hours
```

### Automatic Cleanup

Expired memories are automatically cleaned up:

```python
# Manually trigger cleanup
await memory.cleanup_expired()

# Get expired count
count = await memory.count_expired()
```

## Usage Examples

### Basic Usage

```python
from heretek_swarm.memory import DualTierMemory

# Initialize
memory = DualTierMemory()
await memory.initialize()

# Store memory
entry = await memory.store(
    content={"key": "value"},
    metadata={"type": "working_memory"},
    ttl=3600
)

# Retrieve
retrieved = await memory.retrieve(entry.id)

# Query
results = await memory.query(
    filters={"type": "working_memory"},
    limit=10
)

# Delete
await memory.delete(entry.id)
```

### Integration with Actors

```python
from heretek_swarm.actors.base import AgentActor
from heretek_swarm.memory import DualTierMemory

class MyAgent(AgentActor):
    async def initialize(self):
        # Initialize memory
        self.memory = DualTierMemory()
        await self.memory.initialize()
        
    async def process_message(self, message):
        # Store in memory
        await self.memory.store(
            content=message.content,
            metadata={"source": message.sender}
        )
        
        # Query memory
        results = await self.memory.query(
            filters={"source": message.sender}
        )
```

### Integration with Historian

```python
from heretek_swarm.actors.historian import HistorianAgent

historian = HistorianAgent()
await historian.spawn()

# Store deliberation context
await historian.store_context(
    deliberation_id="delib-1",
    context={"topic": "deployment", "votes": {...}}
)

# Retrieve context
context = await historian.get_context("delib-1")
```

## Best Practices

### 1. Memory Tier Selection

- Use ephemeral for: Session data, temporary calculations, working memory
- Use persistent for: Important decisions, historical data, long-term patterns

### 2. TTL Management

- Set appropriate TTL for ephemeral memories
- Monitor memory usage
- Implement cleanup schedules
- Use lineage for related memories

### 3. Metadata Design

- Use consistent metadata schemas
- Include relevant search fields
- Use hierarchical metadata when appropriate
- Document metadata conventions

### 4. Query Optimization

- Use specific filters when possible
- Set appropriate similarity thresholds
- Limit result sets
- Use indexes for frequently queried fields

### 5. Memory Cleanup

- Regularly clean expired memories
- Implement retention policies
- Archive old memories if needed
- Monitor memory usage

## Performance Considerations

### Ephemeral Memory

- Fast access (in-memory)
- Limited by available RAM
- Automatic expiration
- No persistence

### Persistent Memory

- Slower access (disk/network)
- Scales to large datasets
- Persistent across restarts
- Semantic search capability

### Query Performance

- Metadata filtering: Fast
- Semantic search: Slower but more powerful
- Hybrid queries: Balanced
- Result limiting: Important for performance

## Troubleshooting

### Common Issues

1. **Memory Not Found**
   - Check if memory expired (ephemeral)
   - Verify memory ID
   - Check if memory was deleted

2. **Slow Queries**
   - Add metadata filters
   - Reduce similarity threshold
   - Limit result set
   - Add indexes

3. **High Memory Usage**
   - Clean expired memories
   - Reduce TTL values
   - Archive old memories
   - Monitor memory growth

4. **Connection Issues**
   - Check database connection
   - Verify connection string
   - Check network connectivity
   - Review database logs

## API Reference

### MemorySystem

See [`src/heretek_swarm/memory/base.py`](../src/heretek_swarm/memory/base.py) for complete API documentation.

### EphemeralMemory

See [`src/memory/ephemeral.py`](../src/memory/ephemeral.py) for complete API documentation.

### PersistentMemory

See [`src/memory/persistent.py`](../src/memory/persistent.py) for complete API documentation.

### DualTierMemory

See [`src/memory/unified.py`](../src/memory/unified.py) for complete API documentation.

## See Also

- [Actors System](./actors-system.md)
- [Consensus Mechanism](./consensus-mechanism.md)
- [HeavySwarm Workflow](./orchestration.md)
- [State Management](./state.md)
