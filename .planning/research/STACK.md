# Technology Stack Research: The Collective

**Project:** The Collective (23-agent autonomous swarm)
**Researched:** 2026-04-13
**Confidence:** MEDIUM (official docs verified, some ecosystem patterns inferred)

---

## Executive Summary

The Collective requires a stack that supports 23 concurrently operating agents with persistent state, inter-agent messaging, consensus protocols, and zero-trust validation. The recommended stack uses **Python 3.11+** with **FastAPI** for async agent APIs, **Pydantic v2** for message schemas, **SQLAlchemy 2.0** with asyncpg for state persistence, and **Alembic** for migrations. This stack is proven in high-concurrency AI workloads (LangChain, AutoGPT, etc.) and provides the async foundation needed for agent concurrency.

---

## Recommended Stack

### Core Language

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| Python | 3.11+ | Runtime | Required for task tasks, structural pattern matching, superior async ecosystem for AI agents |
| python-multipart | 0.0.9+ | Form parsing | Agent message attachments if needed |

**Rationale:** Python dominates AI/agent ecosystems. 3.11 brings significant async performance improvements (`task tasks` module), and 3.12+ offers even better async debuggability. The `task tasks` group in 3.11 enables structured concurrency patterns ideal for managing 23 agent lifecycles.

### Web Framework

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| FastAPI | 0.115+ | Async API framework | Native async, Pydantic integration, OpenAPI auto-docs, uvicorn ASGI |
| uvicorn | 0.32+ | ASGI server | Production-grade async server with hot reload |

**Rationale:** FastAPI's async-first design is critical for 23-agent concurrency. Each agent can expose endpoints for messaging, and FastAPI handles concurrent request handling without blocking. The Pydantic v2 integration is seamless.

**Performance:** FastAPI handles ~10K+ concurrent connections with proper async handlers. For 23 agents, this is well within capacity even with heavy inter-agent messaging.

### Data Validation

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| Pydantic | 2.10+ | Message schemas | Rust-powered validation (550M downloads/month), ~8,000 packages depend on it |
| email-validator | 2.2+ | Email validation | Required for agent contact schemas |

**Rationale:** Pydantic v2's Rust-powered core provides ~10x faster validation vs v1. Critical for high-throughput inter-agent messaging. Strict mode supports zero-trust validation requirements.

**Key v2 Patterns:**
```python
from pydantic import BaseModel, Field, field_validator

class AgentMessage(BaseModel):
    sender_id: str = Field(..., min_length=1, max_length=64)
    recipient_id: str | None = Field(None, description="Broadcast if None")
    content: dict[str, Any]
    priority: Literal["low", "normal", "high", "critical"] = "normal"
    consensus_required: bool = False

    @field_validator("sender_id", "recipient_id")
    @classmethod
    def validate_agent_id(cls, v: str) -> str:
        if not v.replace("-", "").replace("_", "").isalnum():
            raise ValueError("Agent IDs must be alphanumeric with dashes/underscores")
        return v
```

### Database

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| PostgreSQL | 16+ | Primary datastore | JSONB support for flexible agent state, excellent async driver support, row-level security for tenant isolation |
| SQLAlchemy | 2.0.49+ | ORM/async ORM | Unified tutorial, native async support, asyncpg driver |
| alembic | 1.14+ | Migrations | Auto-generating migrations, branching for multi-agent schema evolution |
| asyncpg | 0.30+ | Async PostgreSQL driver | Non-blocking driver required for FastAPI concurrency |

**Rationale:** PostgreSQL's JSONB is ideal for agent state that varies by agent type. SQLAlchemy 2.0's async ORM eliminates the threadpool bottleneck that would cripple 23-agent concurrency.

**Critical Pattern - Async Session Management:**
```python
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

engine = create_async_engine(
    "postgresql+asyncpg://user:pass@localhost/the_collective",
    pool_size=50,  # Support 23 agents + overhead
    max_overflow=20,
    pool_pre_ping=True,  # Validate connections
)

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,  # Critical for agent state access after commit
)

async def get_agent_session() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session
```

### Infrastructure

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| Redis | 7.4+ | Pub/sub, rate limiting | Inter-agent messaging, consensus coordination, distributed locks |
| APScheduler | 3.11+ | Job scheduling | Chronos agent time management, heartbeat monitoring |

---

## Technology Integration with 6-Tier Architecture

### Tier Mapping

| Tier | Agents | Technology Pattern |
|------|--------|-------------------|
| Core Governance | Steward, Alpha, Beta, Charlie | FastAPI deps with agent context, SQLAlchemy sessions per request |
| Support | Historian, Metis, Empath, Perceiver, Echo | PostgreSQL JSONB for knowledge graphs, Redis for vector cache |
| Exploration | Explorer, Examiner, Dreamer, Coder | Background tasks for long-running operations, asyncpg for concurrent queries |
| Safety | Sentinel, Sentinel-Prime, Arbiter | Zero-trust validation on all messages, Redis pub/sub for threat alerts |
| Coordination | Coordinator, Nexus, Catalyst, Chronos | Redis pub/sub for inter-tier messaging, APScheduler for Chronos |
| Enhancement | Prism, Habit-Forge, Perceiver+ | Event-driven updates, habit tracking in PostgreSQL |

### Inter-Agent Messaging Pattern

```python
# Agent message router using FastAPI + Redis pub/sub
class AgentMessageRouter:
    def __init__(self, redis: Redis):
        self.redis = redis
        self.pubsub = redis.pubsub()

    async def broadcast(self, sender: str, message: AgentMessage):
        """Broadcast to all agents or specific tier"""
        channel = f"agent:{sender}:broadcast"
        await self.redis.publish(channel, message.model_dump_json())

    async def send(self, sender: str, recipient: str, message: AgentMessage):
        """Direct agent-to-agent message"""
        channel = f"agent:{recipient}:inbox"
        await self.redis.publish(channel, message.model_dump_json())

    async def subscribe(self, agent_id: str):
        """Subscribe agent to its inbox + system announcements"""
        await self.pubsub.subscribe(
            f"agent:{agent_id}:inbox",
            "system:announcements"
        )
```

### Consensus Protocol Pattern

```python
# Consensus state stored in PostgreSQL
class ConsensusVote(BaseModel):
    proposal_id: str
    voter_id: str
    vote: Literal["accept", "reject", "abstain"]
    reasoning: str | None
    timestamp: datetime

class ConsensusState(BaseModel):
    proposal_id: str
    required_votes: int  # e.g., 23 for unanimous, 12 for majority
    votes: list[ConsensusVote]
    status: Literal["pending", "approved", "rejected", "expired"]
    deadline: datetime

# Store in PostgreSQL JSONB for flexibility
async def record_vote(session: AsyncSession, vote: ConsensusVote):
    # Append to consensus proposal JSONB array
    stmt = text("""
        UPDATE consensus_proposals
        SET votes = votes || :vote::jsonb,
            updated_at = NOW()
        WHERE proposal_id = :proposal_id
    """)
    await session.execute(stmt, {"vote": vote.model_dump_json(), "proposal_id": vote.proposal_id})
```

---

## Version Constraints

| Package | Minimum | Recommended | Why |
|---------|---------|-------------|-----|
| Python | 3.11 | 3.12+ | task tasks group for structured concurrency, better async debug |
| FastAPI | 0.110+ | 0.115+ | Improved async handling, dependency caching |
| Pydantic | 2.10+ | 2.10+ | Rust core, strict mode, validator improvements |
| SQLAlchemy | 2.0.30+ | 2.0.49 | Stable async ORM, connection pool improvements |
| Alembic | 1.14+ | 1.14+ | SQLAlchemy 2.0 support |
| asyncpg | 0.30+ | 0.30+ | PostgreSQL 16 compatibility |
| uvicorn | 0.30+ | 0.32+ | ASGI lifespan events, hot reload improvements |
| Redis | 7.2+ | 7.4+ | Pub/sub ACL support, vector search (future) |

---

## Performance Characteristics

### Expected Throughput (23 Agents)

| Operation | Expected RPS | Notes |
|-----------|-------------|-------|
| Agent heartbeat | ~230/sec | 10 heartbeat/sec per agent |
| Inter-agent messages | ~1,000/sec | Burst traffic for consensus |
| State persistence | ~100/sec | Batch writes via SQLAlchemy |
| Query operations | ~500/sec | Read-heavy workload |

### Concurrency Limits

- **uvicorn workers:** Start with 4 workers, scale based on CPU. Each worker handles ~10K concurrent connections.
- **PostgreSQL connections:** Pool size of 50 handles 23 agents comfortably with headroom.
- **Redis connections:** One connection per agent subscriber + pub overhead (~50 connections).

### Memory Profile

- Each agent instance: ~50-100MB depending on model context
- PostgreSQL (with JSONB): ~500MB for 23 agents with moderate state
- Redis: ~100MB for pub/sub + consensus state
- **Total baseline:** ~2-3GB RAM

---

## Known Pitfalls

### Critical Pitfalls

**1. Async Session Lifecycle**
- **Problem:** SQLAlchemy AsyncSession closes after commit by default in some configurations
- **Consequence:** "AsyncSession closed" errors when accessing agent state after commit
- **Fix:** Use `expire_on_commit=False` and keep session context tight

**2. Structured Concurrency Mismanagement**
- **Problem:** Creating unbounded task tasks groups can leak resources
- **Consequence:** Agents hang on shutdown, zombie connections
- **Fix:** Use `task tasks.group()` with proper cancellation and timeout

**3. Pydantic Strict Mode Mismatch**
- **Problem:** Mixing strict and lax validation across agent messages
- **Consequence:** Inter-agent messages rejected unexpectedly
- **Fix:** Define consistent validation mode in base schema, document per-message overrides

**4. Redis Pub/Sub Reconnection**
- **Problem:** Long-running subscribers can silently disconnect
- **Consequence:** Missed consensus votes or alerts
- **Fix:** Implement heartbeat monitoring with reconnection logic

### Moderate Pitfalls

**5. JSONB Query Performance**
- **Problem:** Unindexed JSONB columns become slow at scale
- **Fix:** Use GIN indexes on frequently queried JSONB paths

**6. Migration Conflicts in Multi-Agent Schema**
- **Problem:** Concurrent alembic migrations from multiple agents
- **Fix:** Use branching with explicit migration dependency chains

**7. Connection Pool Exhaustion**
- **Problem:** Long-running agent operations hold connections
- **Fix:** Use `pool_pre_ping=True` and set `pool_recycle` to reclaim stale connections

---

## Sources

- [FastAPI Async Documentation](https://fastapi.tiangolo.com/async/) - Async/await patterns, concurrency vs parallelism
- [SQLAlchemy 2.0 Documentation](https://docs.sqlalchemy.org/en/20/) - Async ORM, connection pooling
- [Alembic Documentation](https://alembic.sqlalchemy.org/en/latest/) - Migration patterns, branching
- [Pydantic v2 Documentation](https://pydantic.dev/docs/validation/latest/get-started/) - Rust-powered validation, strict mode
- [FastAPI Python Types](https://fastapi.tiangolo.com/python-types/) - Type hint integration

---

## Recommendations

1. **Start with asyncpg + SQLAlchemy 2.0** - The async ORM is non-negotiable for 23-agent concurrency
2. **Use Pydantic v2 strict mode by default** - Aligns with zero-trust validation requirements
3. **Implement Redis pub/sub first** - Critical for inter-agent messaging before consensus building
4. **Profile before scaling workers** - uvicorn 4 workers handles this load; adding more adds complexity
5. **Document agent message schemas early** - 23 agents need consistent interfaces to communicate
