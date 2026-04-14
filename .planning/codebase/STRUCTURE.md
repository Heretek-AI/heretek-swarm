# Codebase Structure

**Analysis Date:** 2026-04-13

## Directory Layout

```
heretek-swarm/
├── src/
│   └── heretek_swarm/
│       ├── actors/           # Tiered agent system (23 agents)
│       ├── api/              # FastAPI endpoints
│       ├── collective/      # Collective intelligence
│       ├── consensus/       # MAKER consensus protocol
│       ├── gateway/          # A2A protocol server
│       ├── infrastructure/  # NATS, OpenTelemetry
│       ├── memory/           # Memory system
│       ├── runtime/         # Agent runtime, characters, tools
│       ├── channels/         # Message channels
│       ├── config/           # Configuration management
│       ├── consciousness/   # Consciousness metrics
│       ├── embeddings/       # Embedding providers
│       ├── evaluation/      # Evaluation metrics
│       ├── integrations/    # Third-party integrations
│       ├── interfaces/      # Interface definitions
│       ├── knowledge/       # Knowledge management
│       ├── llm/              # LLM integrations
│       ├── logging/          # Logging setup
│       ├── mcp/              # MCP protocol
│       ├── observability/    # Observability tools
│       ├── orchestration/    # Workflow orchestration
│       ├── plugins/          # Plugin system
│       ├── rag/              # RAG functionality
│       ├── routing/          # Message routing
│       ├── security/         # Security utilities
│       ├── state/            # State management
│       ├── tools/            # Tool definitions
│       ├── utils/            # Utilities
│       ├── validation/       # Validation utilities
│       └── workflow/         # Workflow definitions
├── tests/                    # Test suite
├── docker-compose.yml         # Container orchestration
├── pyproject.toml           # Project configuration
└── src/cli.py               # CLI entry point
```

## Directory Purposes

**actors/**
- Purpose: Multi-agent system implementation
- Contains: 23 agent implementations organized in tiers, base classes, mixins, factory, supervisor
- Key files:
  - `base/core.py` - AgentActor base class
  - `base/state_management.py` - State mixin
  - `base/message_handling.py` - Message handling mixin
  - `factory.py` - ActorFactory for actor registration/creation
  - `supervisor.py` - ActorSupervisor for lifecycle
  - `triad.py` - Tier 1 core agents (Steward, Alpha, Beta, Charlie)
  - `arbiter/` - Safety and validation agents

**api/**
- Purpose: FastAPI REST/WebSocket API
- Contains: Agent management, metrics, consensus endpoints, workflows, autonomous operations
- Key files:
  - `main.py` - FastAPI application entry
  - `agents/core.py` - Core agent API types
  - `agents/instances.py` - Agent instance management
  - `agents/lifecycle.py` - Agent lifecycle endpoints
  - `agents/routing_control.py` - Routing management
  - `agents/routing_rules.py` - Routing rules
  - `agents/jetstream.py` - JetStream integration
  - `agents/profiling.py` - Agent profiling
  - `websocket.py` - WebSocket handling
  - `autonomous.py` - Autonomous mode endpoints
  - `rate_limiting.py` - Rate limiting middleware

**collective/**
- Purpose: Collective intelligence and emergent behavior
- Contains: Emergence detection, pattern library, distributed learning, agency tracking, metrics
- Key files:
  - `emergence_analyzer.py` - Emergence analysis
  - `emergent_detection.py` - Pattern detection
  - `pattern_library.py` - Pattern storage and retrieval
  - `agent_adaptation.py` - Agent adaptation
  - `distributed_learning.py` - Cross-agent learning
  - `agency_tracking.py` - Agency metrics
  - `metrics.py` - Collective metrics
  - `society.py` - AgentSociety implementation

**consensus/**
- Purpose: MAKER consensus protocol implementation
- Contains: Deliberation, expertise weighting, tribunal, audit trail, Raft election
- Key files:
  - `maker.py` - MAKERConsensus main implementation
  - `deliberation.py` - Deliberation process
  - `tribunal.py` - Tribunal for disputes
  - `audit.py`, `audit_trail.py` - Audit logging
  - `expertise.py` - Expertise weighting

**gateway/**
- Purpose: A2A protocol server and routing
- Contains: A2A server, protocol handler, auth, event mesh, content router
- Key files:
  - `a2a_server.py` - Main A2A server
  - `a2a_protocol.py` - A2A protocol definitions
  - `auth.py` - Authentication
  - `event_mesh.py` - Event distribution
  - `content_router.py` - Message routing

**infrastructure/**
- Purpose: Low-level infrastructure components
- Contains: NATS client/consensus/memory_sync, OpenTelemetry
- Key files:
  - `nats/client.py` - NATS connection
  - `nats/consensus.py` - NATS consensus
  - `nats/memory_sync.py` - Memory synchronization
  - `a2a/protocol.py` - A2A protocol
  - `otel/logging.py` - OpenTelemetry setup

**memory/**
- Purpose: Persistent memory for agents
- Contains: Memory system base classes

**runtime/**
- Purpose: Agent execution context
- Contains: AgentRuntime, AgentContext, Character system, ToolRegistry
- Key files:
  - `agent_runtime.py` - Runtime context
  - `characters.py` - Character definitions
  - `tools.py` - Tool registry

**plugins/**
- Purpose: Extensibility system
- Contains: Consciousness and liberation plugins

## Key File Locations

**Entry Points:**
- `src/cli.py` - CLI commands (deploy, update, status)
- `src/heretek_swarm/api/main.py` - FastAPI app initialization

**Configuration:**
- `pyproject.toml` - Python project configuration
- `src/heretek_swarm/config/` - Configuration loaders

**Core Logic:**
- `src/heretek_swarm/actors/base/core.py` - AgentActor base
- `src/heretek_swarm/actors/factory.py` - Actor factory
- `src/heretek_swarm/consensus/maker.py` - MAKER consensus
- `src/heretek_swarm/gateway/a2a_server.py` - A2A server

**Testing:**
- `tests/` - Test suite (pytest based)

## Naming Conventions

**Files:**
- Python modules: `snake_case.py`
- Test files: `test_*.py` or `*_test.py`
- Mixin modules: `*_mixin.py` (in `mixins/` subdirectory)

**Directories:**
- Package directories: `snake_case/`

**Classes:**
- PascalCase: `AgentActor`, `ActorFactory`, `MAKERConsensus`
- Mixins: `*Mixin` suffix: `AgentActorStateManagement`

**Functions:**
- snake_case: `create_actor()`, `get_factory()`

## Where to Add New Code

**New Agent:**
- Primary code: `src/heretek_swarm/actors/<agent_name>.py`
- Tests: `tests/test_<agent_name>.py`
- Register in `src/heretek_swarm/actors/__init__.py`

**New API Endpoint:**
- Implementation: `src/heretek_swarm/api/<feature>.py`
- Register routes in `src/heretek_swarm/api/main.py`

**New Consensus/Collective Feature:**
- Consensus: `src/heretek_swarm/consensus/<feature>.py`
- Collective: `src/heretek_swarm/collective/<feature>.py`

**New Infrastructure (NATS/OpenTelemetry):**
- Location: `src/heretek_swarm/infrastructure/<component>/`

**New Mixin for AgentActor:**
- Location: `src/heretek_swarm/actors/base/<feature>.py`
- Import in `src/heretek_swarm/actors/base/core.py` or `__init__.py`

## Special Directories

**actors/mixins/**
- Purpose: Reusable behavior compositions for agents
- Contains: `pattern.py`, `tribunal.py`, `memory.py`, `learning.py`, `memory_access.py`, `health_reporting.py`, `deliberation.py`
- Pattern: Mixin classes that add capabilities to AgentActor

**collective/**
- Purpose: Emergent intelligence and collective behavior
- Generated: No
- Committed: Yes

**infrastructure/a2a/**
- Purpose: A2A protocol definitions separate from server implementation
- Contains: `protocol.py` with A2AMessage, A2AMessageType, A2AProtocol

**runtime/characters/**
- Purpose: JSON character definitions for agents
- Format: JSON files with personality, goals, constraints

---

*Structure analysis: 2026-04-13*
