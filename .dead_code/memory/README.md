# Dual-Tier Memory System

A high-performance, dual-tier memory system for multi-agent AI systems, combining Redis (ephemeral) and PostgreSQL/PGVector (persistent) storage.

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│              Dual-Tier Memory System                     │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  ┌──────────────────┐      ┌──────────────────┐         │
│  │   Ephemeral      │      │   Persistent     │         │
│  │   (Redis)        │      │   (PostgreSQL)   │         │
│  │                  │      │   + PGVector     │         │
│  │  - Working Mem   │      │  - Long-term     │         │
│  │  - TTL-based     │      │  - Semantic      │         │
│  │  - Fast (<10ms)  │      │  - Vector Search │         │
│  └──────────────────┘      └──────────────────┘         │
│           │                         │                    │
│           └─────────┬───────────────┘                    │
│                     │                                    │
│            ┌────────▼────────┐                          │
│            │ Embedding       │                          │
│            │ Service         │                          │
│            │ (LiteLLM)       │                          │
│            └─────────────────┘                          │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

## Features

- **Two-Layer Architecture**: Ephemeral (Redis) for fast working memory, Persistent (PostgreSQL/PGVector) for long-term storage
- **Semantic Search**: Vector similarity search using PGVector
- **Automatic Tiering**: Smart placement based on importance and access patterns
- **Performance Optimized**: p95 latency <50ms target
- **Lineage Tracking**: Complete message provenance
- **TTL Management**: Automatic expiration for ephemeral memory
- **Connection Pooling**: Efficient resource utilization

## Installation

```bash
pip install heretek-swarm[memory]
```

## Quick Start

```python
from heretek_swarm.memory import DualTierMemorySystem, DualTierConfig
import asyncio

async def main():
    # Initialize system
    config = DualTierConfig(
        ephemeral=EphemeralConfig(
            redis_url="redis://localhost:6379/0"
        ),
        persistent=PersistentConfig(
            database_url="postgresql+asyncpg://user:pass@localhost:5432/heretek"
        )
    )
    
    memory = DualTierMemorySystem(config)
    await memory.initialize()
    
    # Store memory
    entry = await memory.store(
        content="Agent completed analysis task",
        agent_id="agent-alpha",
        memory_type=MemoryType.EPISODIC,
        tags=["task", "completion"]
    )
    
    # Retrieve context
    context = await memory.get_context_for_agent(
        agent_id="agent-alpha",
        limit=10
    )
    
    # Search
    results = await memory.search(
        MemoryQuery(
            query_text="analysis",
            agent_ids=["agent-alpha"]
        )
    )
    
    # Cleanup
    await memory.shutdown()

asyncio.run(main())
```

## Configuration

### Ephemeral Tier (Redis)

```python
EphemeralConfig(
    redis_url="redis://localhost:6379/0",
    default_ttl_seconds=3600,  # 1 hour
    max_ttl_seconds=86400,     # 24 hours max
    key_prefix="heretek:memory"
)
```

### Persistent Tier (PostgreSQL)

```python
PersistentConfig(
    database_url="postgresql+asyncpg://user:pass@localhost:5432/heretek",
    pool_size=10,
    max_overflow=20,
    query_timeout=10.0
)
```

### Embedding Service

```python
EmbeddingConfig(
    litellm_base_url="http://localhost:4000",
    default_model="text-embedding-3-small",
    dimensions=1536,
    cache_ttl_seconds=86400
)
```

## Memory Types

- **EPISODIC**: Event-based memories (what happened)
- **SEMANTIC**: Facts and knowledge (what is true)
- **PROCEDURAL**: Skills and procedures (how to do things)
- **WORKING**: Current task context (active state)

## API Reference

### DualTierMemorySystem

#### `store(content, agent_id, ...) -> MemoryEntry`
Store a new memory entry.

#### `retrieve(entry_id) -> Optional[MemoryEntry]`
Retrieve a memory by ID.

#### `search(query) -> MemoryResult`
Search across both tiers.

#### `get_context_for_agent(agent_id, ...) -> List[MemoryEntry]`
Get relevant context for an agent.

#### `semantic_search(query_text, ...) -> MemoryResult`
Perform semantic vector search.

#### `promote_to_persistent(entry_id) -> Optional[MemoryEntry]`
Promote ephemeral entry to persistent storage.

#### `demote_to_ephemeral(entry_id) -> Optional[MemoryEntry]`
Demote persistent entry to ephemeral storage.

### MemoryQuery

```python
MemoryQuery(
    query_text="search query",
    query_vector=[0.1, 0.2, ...],
    agent_ids=["agent-1"],
    memory_types=[MemoryType.EPISODIC],
    tags=["important"],
    start_time=datetime(...),
    end_time=datetime(...),
    limit=10,
    offset=0,
    sort_by="relevance"
)
```

## Performance Targets

| Metric | Target | Typical |
|--------|--------|---------|
| Ephemeral Read | <10ms | 2-5ms |
| Persistent Read | <50ms | 10-30ms |
| Semantic Search | <50ms | 20-40ms |
| Batch Store (100) | <500ms | 200-400ms |

## Testing

```bash
# Run tests
pytest tests/memory/ -v

# Run with coverage
pytest tests/memory/ --cov=src/memory --cov-report=html
```

## Requirements

- Python 3.11+
- Redis 6.0+
- PostgreSQL 14+ with PGVector extension
- LiteLLM for embeddings

## License

Apache 2.0
