# Architecture

**Analysis Date:** 2026-04-15

## Pattern Overview

**Overall:** 23-Agent Collective System with Event-Driven Architecture

**Key Characteristics:**
- Agent-based architecture with 23 specialized agent types organized in 6 tiers
- Event mesh communication via NATS A2A (Agent-to-Agent) protocol
- Multi-tier memory system (episodic, semantic, working, procedural)
- Consensus-driven decision making via MAKER protocol
- Zero-trust security with 4-layer validation architecture
- Consciousness frameworks for agent awareness (GWT, AST, IIT, FEP)

## Layers

**Core Runtime:**
- Purpose: Main entry point for autonomous 24/7 swarm operation
- Location: `src/heretek_swarm/runtime/main_loop.py`
- Contains: `AutonomousSwarm` class - wires all components together
- Depends on: NATS event mesh, memory, RAG, consensus engine
- Used by: Startup scripts, container orchestration

**Actors (Agents):**
- Purpose: 23 specialized AI agents that perceive, decide, and act
- Location: `src/heretek_swarm/actors/`
- Contains: Agent implementations (steward, alpha, beta, charlie, etc.)
- Tier 1 (Core Triad): Steward, Alpha, Beta, Charlie
- Tier 2 (Support): Historian, Metis, Empath, Perceiver, Echo
- Tier 3 (Exploration): Explorer, Examiner, Dreamer, Coder
- Tier 4 (Safety): Sentinel, Sentinel-Prime, Arbiter
- Tier 5 (Coordination): Coordinator, Nexus, Catalyst, Chronos
- Tier 6 (Enhancement): Prism, Habit-Forge, Perceiver+
- Depends on: Base actor class, mixins, memory access, security
- Used by: Runtime, gateway, consensus

**Gateway (Event Mesh):**
- Purpose: NATS-based A2A communication between agents
- Location: `src/heretek_swarm/gateway/`
- Contains: `NATSEventMesh`, `A2AProtocol`, `JetStreamManager`
- Depends on: NATS server, actor registry
- Used by: All agents for inter-agent communication

**Consensus (MAKER Protocol):**
- Purpose: Multi-agent decision aggregation and voting
- Location: `src/heretek_swarm/consensus/`
- Contains: `MAKERConsensus`, `Tribunal`, `Deliberation`
- Depends on: Agent votes, reputation tracking
- Used by: Steward, Coordinator for critical decisions

**Security (Zero-Trust):**
- Purpose: 4-layer validation architecture
- Location: `src/heretek_swarm/security/`
- Contains: `ZeroTrustValidator`, `InputValidator`, `ContextValidator`, `OutputValidator`, `AuditLogger`
- Layer 1: Input Validation (Pydantic v2, UUID v4, size limits)
- Layer 2: Context Validation (injection detection, behavioral analysis)
- Layer 3: Output Validation (PII detection, sensitive data filtering)
- Layer 4: Audit Logging (structured logging, severity levels)
- Used by: Gateway, API, all agents

**Memory System:**
- Purpose: Multi-tier storage management
- Location: `src/heretek_swarm/memory/`
- Contains: `TieredMemory`, `TierConfig`, migration logic
- Tiers: L1_HOT (Redis), L2_WARM (PostgreSQL), L3_COLD (compressed archive)
- Used by: All agents for persistence

**State Management:**
- Purpose: PostgreSQL-backed event sourcing
- Location: `src/heretek_swarm/state/`
- Contains: `EventStore`, `Repository`, `models`
- Used by: API, runtime, consensus

**Consciousness Frameworks:**
- Purpose: Agent self-awareness and agency metrics
- Location: `src/heretek_swarm/consciousness/`
- Contains: `GWT` (Global Workspace Theory), `IIT` (Integrated Information Theory), `AST` (Adaptive Suspension Theory), `FEP` (Free Energy Principle)
- Used by: Enhancement tier agents (Prism, Habit-Forge, Perceiver+)

**API Layer:**
- Purpose: HTTP endpoints for external clients
- Location: `src/heretek_swarm/api/`
- Contains: FastAPI application with routers for agents, workflows, consciousness, config
- Used by: Frontend dashboard, external consumers

**Collective Intelligence:**
- Purpose: Emergent behavior detection and learning
- Location: `src/heretek_swarm/collective/`
- Contains: `SwarmIntelligence`, `EmergenceAnalyzer`, `PatternLibrary`
- Used by: Steward, Coordinator for swarm-level decisions

## Data Flow

**Agent Communication Flow:**

1. External client sends HTTP request to API
2. API validates request via zero-trust security
3. Request published to NATS subject
4. Target agent subscribes and receives message
5. Agent processes, potentially consulting memory
6. Agent may invoke consensus for critical decisions
7. Response published back via NATS
8. API receives response and forwards to client

**State Persistence Flow:**

1. Agent completes action with state change
2. Event written to `EventStore`
3. `Repository` persists to PostgreSQL
4. Memory system indexes for retrieval
5. Audit logged via structlog

**Consensus Flow (MAKER Protocol):**

1. Steward identifies decision requiring consensus
2. `start_consensus(consensus_id)` initiated
3. Agents submit votes with confidence scores
4. `_apply_enhanced_vote_weights()` calculates weighted votes
5. `_first_to_ahead_by_k()` determines winner
6. Red flags checked for anomalies
7. `ConsensusResult` returned with decision

**Memory Tier Migration Flow:**

1. `TierManager` monitors access patterns
2. `should_migrate()` evaluates triggers (access_pattern, policy, scheduled)
3. Data moved between tiers based on `MigrationStrategy`
4. Audit logged for compliance
5. Rollback available on failure

## Key Abstractions

**AgentActor (Base Class):**
- Purpose: Foundation for all 23 agent types
- Location: `src/heretek_swarm/actors/base/core.py`
- Pattern: Mixin-based composition (state management + message handling + core)
- Exports: `ActorMessage`, `ActorState`, `ActorStatus`, `AgentActor`

**Actor Mixins:**
- Purpose: Composable capabilities (memory access, health reporting, validation)
- Location: `src/heretek_swarm/actors/mixins/`
- Examples: `memory_access.py`, `health_reporting.py`, `validation.py`, `deliberation.py`, `audit.py`, `learning.py`, `pattern.py`, `tribunal.py`

**ZeroTrustValidator:**
- Purpose: Orchestrates 4-layer security validation
- Location: `src/heretek_swarm/security/zero_trust.py`
- Pattern: Layered validation with early termination
- Target: <50ms p95 latency, <0.1% false negative rate

**MAKERConsensus:**
- Purpose: Voting-based decision aggregation
- Location: `src/heretek_swarm/consensus/maker.py`
- Pattern: First-to-ahead-by-k with reputation weighting
- Features: Red-flagging, confidence thresholds, async execution

**DualTierMemory:**
- Purpose: Hot/warm tier memory access
- Location: `src/heretek_swarm/memory/base.py`
- Pattern: Tier abstraction with automatic migration

**AutonomousSwarm:**
- Purpose: Main entry point for 24/7 operation
- Location: `src/heretek_swarm/runtime/main_loop.py`
- Wires: All components into unified autonomous loop

## Entry Points

**API Server:**
- Location: `src/heretek_swarm/api/main.py`
- Triggers: `uvicorn src.heretek_swarm.api.main:app`
- Responsibilities: HTTP endpoint routing, WebSocket support, CORS

**Autonomous Runtime:**
- Location: `src/heretek_swarm/runtime/main_loop.py`
- Triggers: `python -m heretek_swarm.runtime.main_loop`
- Responsibilities: 24/7 agent orchestration, health monitoring, task processing

**Actor Factory:**
- Location: `src/heretek_swarm/actors/factory.py`
- Triggers: Runtime initialization
- Responsibilities: Agent registration and instantiation

## Error Handling

**Strategy:** Structured logging with structlog + circuit breakers

**Patterns:**
- `try/except` blocks with `structlog` error logging
- Circuit breaker pattern in `runtime/scaling.py`
- Graceful degradation in NATS communication
- Rollback mechanisms in memory tiering

## Cross-Cutting Concerns

**Logging:** structlog with JSON output for Loki/Promtail (`src/heretek_swarm/logging/config.py`)
**Validation:** Pydantic v2 with `extra='forbid'` for injection protection
**Authentication:** JWT/API key via `gateway/auth.py`
**Observability:** Prometheus metrics, OpenTelemetry tracing (`src/heretek_swarm/observability/`)
**Rate Limiting:** Token bucket via `api/rate_limiting.py`

---

*Architecture analysis: 2026-04-15*
