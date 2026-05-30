# Memory System

**Version:** 2.1.0  
**Date:** 2026-06-10
**Session:** M001 Complete

Dual-tier memory architecture with PostgreSQL, Redis, and Qdrant vector storage using mem0 integration.

---

## Table of Contents

1. [PersistentMemory / Mem0Backend](#persistentmemory--mem0backend)
2. [Memory Base Models](#memory-base-models)
3. [Memory Architecture](#memory-architecture)
4. [Usage Examples](#usage-examples)

---

## PersistentMemory / Mem0Backend

**File:** [`backend/heretek_swarm/memory/persistent.py`](../backend/heretek_swarm/memory/persistent.py)

Persistent memory backend using mem0 SDK for semantic search and retrieval.

```python
class Mem0Backend:
    """Vector memory backend with mem0 integration."""
    
    async def initialize(self) -> None:
        """Initialize connections to Qdrant and OpenAI."""
        
    async def store(self, entry: MemoryEntry) -> str:
        """Store memory entry."""
        
    async def search(self, query: MemoryQuery) -> MemoryResult:
        """Search memories by query."""
        
    async def shutdown(self) -> None:
        """Cleanup connections."""
```

### Features

- **Vector Embeddings**: OpenAI embeddings for semantic search
- **Qdrant Storage**: High-performance vector database
- **mem0 Integration**: Memory management framework
- **Async Operations**: Non-blocking I/O operations

### Configuration

```python
# Environment variables
QDRANT_HOST = "localhost"
QDRANT_PORT = 6333
OPENAI_API_KEY = "sk-..."
MEM0_COLLECTION = "heretek-swarm"
```

### Storage Flow

1. **Initialize**: Connect to Qdrant and OpenAI
2. **Embed**: Generate vector embedding via OpenAI
3. **Store**: Insert into Qdrant collection
4. **Search**: Query with similarity search
5. **Shutdown**: Cleanup connections

---

## Memory Base Models

**File:** [`backend/heretek_swarm/memory/base.py`](../backend/heretek_swarm/memory/base.py)

Core memory models and interfaces for the dual-tier architecture.

### MemoryEntry

```python
class MemoryEntry(BaseModel):
    """Memory entry model."""
    id: UUID
    agent_id: str
    content: str
    memory_type: MemoryType
    tier: MemoryTier
    metadata: Dict[str, Any]
```

### MemoryType Enum

```python
class MemoryType(str, Enum):
    EPISODIC = "episodic"      # Event-based memories
    SEMANTIC = "semantic"      # Knowledge/fact-based
    PROCEDURAL = "procedural"  # How-to/skill memories
```

### MemoryTier Enum

```python
class MemoryTier(str, Enum):
    EPHEMERAL = "ephemeral"    # Redis-cached, short-term
    PERSISTENT = "persistent"  # PostgreSQL, long-term
    VECTOR = "vector"          # Qdrant, semantic search
```

### MemoryQuery

```python
class MemoryQuery(BaseModel):
    """Memory search query."""
    query_text: Optional[str]
    agent_ids: List[str]
    memory_types: List[MemoryType]
    limit: int
```

### MemoryResult

```python
class MemoryResult(BaseModel):
    """Memory search result."""
    entries: List[MemoryEntry]
    scores: List[float]
    total: int
```

---

## Memory Architecture

### Dual-Tier Design

```
┌─────────────────────────────────────────────────────────┐
│                    Application Layer                     │
└─────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────┐
│              PersistentMemory (mem0 SDK)               │
│     (backend/heretek_swarm/memory/persistent.py)        │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐     │
│  │   Embed     │  │   Store     │  │   Search    │     │
│  └─────────────┘  └─────────────┘  └─────────────┘     │
└─────────────────────────────────────────────────────────┘
                          │
        ┌─────────────────┼─────────────────┐
        ▼                 ▼                 ▼
┌───────────────┐ ┌───────────────┐ ┌───────────────┐
│    Redis      │ │  PostgreSQL   │ │    Qdrant     │
│  (Ephemeral)  │ │ (Persistent)  │ │   (Vector)    │
└───────────────┘ └───────────────┘ └───────────────┘
```

### Tier Characteristics

| Tier | Storage | Use Case | TTL |
|------|---------|----------|-----|
| Ephemeral | Redis | Session data, recent context | Configurable |
| Persistent | PostgreSQL | Decision history, lineage | Permanent |
| Vector | Qdrant | Semantic search, similarity | Permanent |

### Historian Agent Integration

The [`HistorianAgent`](./AGENT_REFERENCE.md#historianagent) manages all memory operations:

```python
# Store memory
await historian.store_memory(content="Decision made", metadata={...})

# Search memory
results = await historian.search_memory(query="previous decisions")

# Get lineage
lineage = await historian.get_lineage(decision_id="uuid")
```

---

## Usage Examples

### Storing Memory

```python
from heretek_swarm.memory.base import MemoryEntry, MemoryType, MemoryTier

# Create memory entry
entry = MemoryEntry(
    id=uuid.uuid4(),
    agent_id="steward-001",
    content="Deliberation completed with consensus",
    memory_type=MemoryType.EPISODIC,
    tier=MemoryTier.PERSISTENT,
    metadata={
        "deliberation_id": "delib-123",
        "participants": ["alpha", "beta", "charlie"],
        "outcome": "consensus",
    }
)

# Store via Historian
await historian._handle_store_memory(ActorMessage(
    sender_id="steward-001",
    target_id="historian-001",
    message_type="store_memory",
    content=entry.model_dump(),
))
```

### Searching Memory

```python
# Search by text
query = MemoryQuery(
    query_text="deliberation outcomes",
    agent_ids=["steward-001"],
    memory_types=[MemoryType.EPISODIC],
    limit=10,
)

results = await mem0_backend.search(query)
print(f"Found {results.total} memories")
for entry, score in zip(results.entries, results.scores):
    print(f"Score: {score:.2f} - {entry.content}")
```

### Getting Decision Lineage

```python
# Track decision lineage
lineage_request = {
    "decision_id": "decision-uuid",
    "parent_ids": ["parent-1", "parent-2"],
}

lineage = await historian._handle_get_lineage(ActorMessage(
    sender_id="steward-001",
    target_id="historian-001",
    message_type="get_lineage",
    content=lineage_request,
))
```

---

## Database Schema

### swarm_memories Table

```sql
CREATE TABLE swarm_memories (
    id UUID PRIMARY KEY,
    agent_id VARCHAR(255) NOT NULL,
    content TEXT NOT NULL,
    memory_type VARCHAR(50) NOT NULL,
    tier VARCHAR(50) NOT NULL,
    metadata JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    parent_ids UUID[]
);

CREATE INDEX idx_memories_agent ON swarm_memories(agent_id);
CREATE INDEX idx_memories_type ON swarm_memories(memory_type);
CREATE INDEX idx_memories_tier ON swarm_memories(tier);
CREATE INDEX idx_memories_created ON swarm_memories(created_at);
CREATE INDEX idx_memories_parents ON swarm_memories USING GIN(parent_ids);
```

---

## Performance Considerations

### Caching Strategy

- **Hot Data**: Redis cache for frequently accessed memories
- **Warm Data**: PostgreSQL for persistent storage
- **Cold Data**: Qdrant for archival semantic search

### Indexing

- Agent ID index for fast lookups
- Memory type index for filtering
- Created_at index for time-based queries
- GIN index for parent_ids array

### Connection Pooling

```python
# PostgreSQL pool settings
DB_POOL_SIZE = 20
DB_MAX_OVERFLOW = 10
DB_POOL_TIMEOUT = 30

# Redis pool settings
REDIS_POOL_SIZE = 10
REDIS_MAX_CONNECTIONS = 20

# Qdrant settings
QDRANT_TIMEOUT = 30
QDRANT_RETRIES = 3
```

---

## See Also

- [Core Actors System](./CORE_ACTORS.md) - Agent base classes
- [Agent Reference](./AGENT_REFERENCE.md) - HistorianAgent details
- [Deployment Guide](./DEPLOYMENT.md) - Database setup instructions
