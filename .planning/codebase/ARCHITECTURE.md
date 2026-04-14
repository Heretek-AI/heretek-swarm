# Architecture

**Analysis Date:** 2026-04-13

## Pattern Overview

**Overall:** Multi-agent swarm orchestration with actor model, event-driven communication, and collective intelligence

**Key Characteristics:**
- Actor model for agents (`AgentActor` base class) with supervised lifecycle
- Agent-to-Agent (A2A) protocol over JSON-RPC 2.0 for inter-agent communication
- NATS messaging infrastructure for distributed communication
- MAKER consensus protocol for collective decision-making
- HeavySwarm deliberation workflows for complex reasoning
- Tiered agent hierarchy (6 tiers, 23 agents total)

## Layers

**Actors (Tiered Agent System):**
- Purpose: Autonomous agents that process tasks and collaborate
- Location: `src/heretek_swarm/actors/`
- Contains: 23 specialized agents organized in tiers
  - Tier 1 (Core Triad): Steward, Alpha, Beta, Charlie
  - Tier 2 (Support): Historian, Metis, Empath, Perceiver, Echo
  - Tier 3 (Exploration): Explorer, Examiner, Dreamer, Coder
  - Tier 4 (Safety): Sentinel, Sentinel-Prime, Arbiter
  - Tier 5 (Coordination): Coordinator, Nexus, Catalyst, Chronos
  - Tier 6 (Enhancement): Prism, Habit-Forge, Perceiver+
- Depends on: Base agent classes, mixins, memory system
- Used by: API layer, gateway, collective intelligence

**API Layer:**
- Purpose: FastAPI-based REST/WebSocket interface for agent management
- Location: `src/heretek_swarm/api/`
- Contains: Agent management, rate limiting, consensus, emergent intelligence, alerts, metrics, evaluation, RAG, consciousness, workflows, autonomous endpoints
- Depends on: Actors, gateway, consensus, collective
- Used by: External clients, frontend

**Gateway (A2A Protocol):**
- Purpose: Agent-to-agent communication and message routing
- Location: `src/heretek_swarm/gateway/`
- Contains: A2A server, protocol handler, auth, event mesh, content router, JetStream manager
- Depends on: NATS infrastructure, A2A protocol
- Used by: Actors (for inter-agent communication)

**Consensus (MAKER Protocol):**
- Purpose: Multi-agent decision-making and agreement
- Location: `src/heretek_swarm/consensus/`
- Contains: MAKER consensus, deliberation, expertise weighting, tribunal, audit trail, Raft election
- Depends on: Actors, collective
- Used by: Gateway, collective intelligence

**Collective Intelligence:**
- Purpose: Emergent behavior detection, pattern learning, distributed optimization
- Location: `src/heretek_swarm/collective/`
- Contains: Emergence analyzer, pattern library, agent adaptation, distributed learning, metrics, agency tracking
- Depends on: Consensus, actors, memory
- Used by: API layer, agents

**Infrastructure:**
- Purpose: NATS messaging, OpenTelemetry observability
- Location: `src/heretek_swarm/infrastructure/`
- Contains: NATS client, consensus, memory sync; OpenTelemetry logging
- Used by: Gateway, API

**Memory System:**
- Purpose: Persistent storage and retrieval for agents
- Location: `src/heretek_swarm/memory/`
- Contains: Memory system base classes
- Used by: Actors, collective

**Runtime:**
- Purpose: Agent execution context, character system, tool registry
- Location: `src/heretek_swarm/runtime/`
- Contains: AgentRuntime, AgentContext, Character system, ToolRegistry
- Used by: Actors

## Data Flow

**Agent Communication Flow:**

1. Client sends request to FastAPI (`src/heretek_swarm/api/main.py`)
2. API routes to appropriate agent management endpoint
3. Agent processes request, may delegate via A2A protocol
4. A2A message created at `src/heretek_swarm/gateway/a2a_server.py`
5. Message routed through NATS infrastructure
6. Target agent receives and processes via `AgentActor.handle_message()`
7. Response flows back through gateway to API to client

**Consensus Flow:**

1. Agent identifies need for consensus
2. MAKER consensus invoked (`src/heretek_swarm/consensus/maker.py`)
3. Deliberation through tribunal process
4. Expertise weighting calculated
5. Audit trail maintained
6. Result propagated to involved agents

**State Management:**

- Actor state managed through `AgentActorStateManagement` mixin (`src/heretek_swarm/actors/base/state_management.py`)
- Message handling via `AgentActorMessageHandling` mixin (`src/heretek_swarm/actors/base/message_handling.py`)
- Persistent state in memory system

## Key Abstractions

**AgentActor (Base Class):**
- Purpose: Base class for all agents
- Location: `src/heretek_swarm/actors/base/core.py`
- Pattern: Mixin-based composition (state management + message handling + core)

**ActorFactory:**
- Purpose: Registry and factory for actor creation
- Location: `src/heretek_swarm/actors/factory.py`
- Pattern: Factory pattern with registration

**ActorSupervisor:**
- Purpose: Lifecycle management and monitoring of actors
- Location: `src/heretek_swarm/actors/supervisor.py`
- Pattern: Supervisor/observer pattern

**A2AProtocol:**
- Purpose: JSON-RPC 2.0 based agent communication
- Location: `src/heretek_swarm/infrastructure/a2a/protocol.py`
- Pattern: Protocol handler with capability discovery

**MAKERConsensus:**
- Purpose: Multi-agent consensus with confidence thresholds
- Location: `src/heretek_swarm/consensus/maker.py`
- Pattern: Consensus protocol with audit trail

## Entry Points

**CLI:**
- Location: `src/cli.py`
- Triggers: `heretek-swarm deploy`, `update`, `status`
- Responsibilities: Deployment commands, version management

**API Server:**
- Location: `src/heretek_swarm/api/main.py`
- Triggers: HTTP/WebSocket connections
- Responsibilities: Agent management, metrics, autonomous operations

**Actor Supervisor:**
- Location: `src/heretek_swarm/actors/supervisor.py`
- Triggers: Agent spawn, termination, health monitoring
- Responsibilities: Actor lifecycle, status aggregation

## Error Handling

**Strategy:** Structured logging via structlog, error propagation through actor hierarchy

**Patterns:**
- Actor-level error catching with recovery attempts
- Supervisor escalation on unrecoverable failures
- Consensus-based error resolution via tribunal
- Audit trail logging for all error conditions

## Cross-Cutting Concerns

**Logging:** structlog throughout all modules
**Validation:** Input validation in API layer, agent validation mixin
**Authentication:** Gateway auth in `src/heretek_swarm/gateway/auth.py`
**Observability:** OpenTelemetry in `src/heretek_swarm/infrastructure/otel/`
**Rate Limiting:** `src/heretek_swarm/api/rate_limiting.py`

---

*Architecture analysis: 2026-04-13*
