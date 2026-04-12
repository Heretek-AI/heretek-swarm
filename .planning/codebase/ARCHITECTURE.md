# Architecture

**Analysis Date:** 2026-04-12

## Pattern Overview

**Overall:** Actor-based multi-agent system with layered API and event-driven communication

**Key Characteristics:**
- Actor model pattern for agent isolation and message passing
- FastAPI for HTTP/WebSocket gateway
- Event mesh (NATS) for inter-agent communication
- Swarms framework integration for LLM capabilities
- Layered architecture separating API, agents, collective intelligence, and infrastructure

## Layers

**API Gateway Layer:**
- Purpose: HTTP/WebSocket API exposing agent management and swarm operations
- Location: `src/heretek_swarm/api/`
- Contains: REST endpoints, WebSocket handlers, authentication, middleware
- Depends on: Actor layer, memory layer, security layer
- Used by: External clients, dashboard frontend

**Actor Layer:**
- Purpose: Agent lifecycle management, message processing, state persistence
- Location: `src/heretek_swarm/actors/`
- Contains: `AgentActor` base class, specialized agents, `ActorSupervisor`
- Depends on: State repository, LLM providers, event mesh
- Used by: API layer, collective layer

**Collective Intelligence Layer:**
- Purpose: Swarm intelligence patterns for emergent group behavior
- Location: `src/heretek_swarm/collective/`
- Contains: `SwarmIntelligenceEngine`, emergence detection, adaptation, learning
- Depends on: Actor layer
- Used by: API layer for consensus and collective decisions

**Memory Layer:**
- Purpose: Persistent storage for agent state and memories
- Location: `src/heretek_swarm/memory/`
- Contains: PostgreSQL persistent memory, mem0 integration, vector storage
- Depends on: Database infrastructure
- Used by: Actor layer, API layer

**Consciousness Layer:**
- Purpose: Agent self-modeling, introspection, and phi computation
- Location: `src/heretek_swarm/consciousness/`
- Contains: `IIT_phi`, introspection, agency metrics, FEP active inference
- Depends on: Actor layer
- Used by: Internal agent operations

**Security Layer:**
- Purpose: Authentication, authorization, guardrails, adversarial protection
- Location: `src/heretek_swarm/security/`
- Contains: Zero-trust implementation, rate limiting, DDOS protection
- Depends on: Gateway auth
- Used by: API layer

**Infrastructure Layer:**
- Purpose: Cross-cutting concerns (logging, observability, tracing, config)
- Location: `src/heretek_swarm/infrastructure/`, `src/heretek_swarm/logging/`, `src/heretek_swarm/observability/`
- Contains: OpenTelemetry tracing, Prometheus metrics, structured logging
- Depends on: External services (Loki, Prometheus, Jaeger)
- Used by: All layers

## Data Flow

**Agent Message Flow:**
```
External Client → FastAPI Gateway → ActorSupervisor → AgentActor → Event Mesh (NATS)
                                                      ↓
                                              State Repository (PostgreSQL)
```

**Collective Decision Flow:**
```
API Request → SwarmIntelligenceEngine → ActorSupervisor → Multiple AgentActors
                                    ↓
                            Emergence Detection → Decision Result
```

**Memory Query Flow:**
```
API Request → Memory Layer → Qdrant (vector) / PostgreSQL (persistent) / mem0
```

## Key Abstractions

**AgentActor:**
- Purpose: Base class for all agents implementing actor model with mailbox
- Examples: `src/heretek_swarm/actors/base.py`
- Pattern: Actor model with async message processing

**ActorSupervisor:**
- Purpose: Centralized actor lifecycle management and coordination
- Examples: `src/heretek_swarm/actors/supervisor.py`
- Pattern: Supervisor pattern for actor restarts and health monitoring

**SwarmIntelligenceEngine:**
- Purpose: Bio-inspired algorithms for collective decision making
- Examples: `src/heretek_swarm/collective/swarm_intelligence.py`
- Pattern: Particle Swarm Optimization, Ant Colony, Bee Algorithm, Flocking, Stigmergy

**StateRepository:**
- Purpose: Abstract state persistence interface
- Examples: `src/heretek_swarm/state/repository.py`
- Pattern: Repository pattern for state storage

## Entry Points

**API Entry:**
- Location: `src/heretek_swarm/api/main.py`
- Triggers: HTTP requests to FastAPI routes
- Responsibilities: Request routing, authentication, middleware setup

**WebSocket Entry:**
- Location: `src/heretek_swarm/api/websockets.py`
- Triggers: WebSocket connections for real-time agent communication
- Responsibilities: Connection management, message forwarding

**CLI Entry:**
- Location: `src/cli.py`
- Triggers: Command-line invocation
- Responsibilities: Local agent spawning and management

## Error Handling

**Strategy:** Layered error handling with structured logging

**Patterns:**
- Pydantic validation errors caught at message boundary
- Circuit breaker pattern via `circuitbreaker` library
- Retry logic via `tenacity`
- Structured JSON logging via `structlog`

## Cross-Cutting Concerns

**Logging:** structlog with JSON output for Loki/Promtail integration
**Validation:** Pydantic models for message validation at API and actor boundaries
**Authentication:** Bearer token auth via `gateway/auth.py` with environment-based API keys
**Observability:** OpenTelemetry distributed tracing, Prometheus metrics

---

*Architecture analysis: 2026-04-12*
