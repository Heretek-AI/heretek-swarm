# Codebase Structure

**Analysis Date:** 2026-04-15

## Directory Layout

```
heretek-swarm/
├── src/heretek_swarm/          # Python backend source
├── dashboard/frontend/src/     # React frontend source
├── tests/                      # Python test suite
├── docs/                       # Architecture documentation
├── k8s/                        # Kubernetes manifests
├── docker/                     # Dockerfile and docker configs
├── scripts/                    # Utility scripts
├── migrations/                 # Database migrations
└── .planning/codebase/         # Codebase mapping docs
```

## Directory Purposes

**`src/heretek_swarm/actors/`:**
- Purpose: 23 agent implementations plus base classes
- Contains:
  - `base.py`, `base/core.py`, `base/state_management.py`, `base/message_handling.py` - Base actor class
  - Individual agents: `steward.py`, `alpha.py`, `beta.py`, `charlie.py`, `historian.py`, `metis.py`, `empath.py`, `perceiver.py`, `perceiver_plus.py`, `explorer.py`, `examiner.py`, `coder.py`, `catalyst.py`, `chronos.py`, `coordinator.py`, `nexus.py`, `sentinel.py`, `sentinel_prime.py`, `arbiter.py`, `prism.py`, `habit_forge.py`, `dreamer.py`, `echo.py`
  - `mixins/` - Reusable capability modules: `memory_access.py`, `health_reporting.py`, `validation.py`, `deliberation.py`, `audit.py`, `learning.py`, `pattern.py`, `tribunal.py`
  - `arbiter/` - Conflict resolution submodule: `core.py`, `handlers.py`, `strategies.py`, `constants.py`
  - `factory.py` - Actor instantiation registry
  - `handoff.py`, `handoff_handlers.py` - Agent handoff logic
  - `supervisor.py` - Health monitoring
  - `triad.py` - Core triad orchestration
  - `stubs.py` - Placeholder implementations
  - `profiling.py`, `validation.py` - Agent utilities

**`src/heretek_swarm/api/`:**
- Purpose: FastAPI HTTP endpoints
- Contains:
  - `main.py` - FastAPI application entry point
  - Routers: `agents/`, `agents_management.py`, `workflows.py`, `consciousness.py`, `consensus.py`, `configuration.py`, `autonomous.py`, `emergent_intelligence.py`, `collective_evolution.py`, `evaluation.py`, `observability.py`, `metrics.py`, `plugins.py`, `rag.py`, `alerts.py`, `websockets.py`, `wizard.py`, `mcp.py`, `rate_limiting.py`
  - `logging_middleware.py` - Request/response logging

**`src/heretek_swarm/consensus/`:**
- Purpose: MAKER protocol and voting mechanisms
- Contains: `maker.py`, `maker_enhanced.py`, `tribunal.py`, `deliberation.py`, `immune.py`, `mediation.py`, `cons01_dispute_resolution.py`, `swarm_deliberation.py`, `raft_election.py`, `expertise.py`, `audit*.py` (audit.py, audit_models.py, audit_query.py, audit_trail.py)

**`src/heretek_swarm/gateway/`:**
- Purpose: NATS event mesh for A2A communication
- Contains: `nats_event_mesh.py`, `event_mesh.py`, `a2a_protocol.py`, `a2a_server.py`, `jetstream_manager.py`, `auth.py`, `content_router.py`, `external_api.py`, `message_replay.py`

**`src/heretek_swarm/memory/`:**
- Purpose: Multi-tier memory system
- Contains: `tiering.py`, `base.py`, `persistent.py`, `compression.py`, `migration_strategies.py`, `access_patterns.py`, `prefetcher.py`, `eliza_memory.py`

**`src/heretek_swarm/security/`:**
- Purpose: Zero-trust security implementation
- Contains: `zero_trust.py`, `guardrails.py`, `validators.py`, `adversarial.py`, `behavioral_baseline.py`, `baseline_update.py`, `threat_detection.py`, `anomaly_detection.py`, `safe01_anomaly_response.py`, `ddos_protection.py`

**`src/heretek_swarm/consciousness/`:**
- Purpose: Consciousness frameworks for agent awareness
- Contains: `gwt.py`, `gwt_deliberation.py`, `ast.py`, `iit.py`, `iit_phi.py`, `fep.py`, `fep_active_inference.py`, `agency_metrics.py`, `self_model.py`, `introspection.py`, `phi_training.py`, `metrics/`

**`src/heretek_swarm/runtime/`:**
- Purpose: Autonomous operation orchestration
- Contains: `main_loop.py`, `autonomous_runtime.py`, `autonomous_runtime_config.py`, `agent_runtime.py`, `registry.py`, `registry_enhanced.py`, `scaling.py`, `characters.py`, `tools.py`

**`src/heretek_swarm/state/`:**
- Purpose: PostgreSQL-backed state persistence
- Contains: `repository.py`, `event_store.py`, `models.py`

**`src/heretek_swarm/collective/`:**
- Purpose: Swarm-level emergent intelligence
- Contains: `swarm_intelligence.py`, `emergence_analyzer.py`, `evolution_engine.py`, `adaptive_learning.py`, `agent_adaptation.py`, `distributed_learning.py`, `knowledge_transform.py`, `agency_tracking.py`, `pattern_library.py`, `pattern_validation.py`, `society.py`, `algorithms/`, `metrics.py`

**`src/heretek_swarm/coordination/`:**
- Purpose: Multi-agent coordination
- Contains: `time_dilation.py`, `paradigm_detection.py`, `sync.py`, `task_graph.py`

**`src/heretek_swarm/mcp/`:**
- Purpose: MCP (Model Context Protocol) tools
- Contains: MCP tool definitions and handlers

**`src/heretek_swarm/orchestration/`:**
- Purpose: Phase-based workflow orchestration
- Contains: `heavyswarm.py`, `phase_handlers.py`

**`src/heretek_swarm/creativity/`:**
- Purpose: Creative AI capabilities
- Contains: `novel_connections.py`

**`src/heretek_swarm/embeddings/`:**
- Purpose: Vector embedding providers
- Contains: `providers/base.py`, `providers/factory.py`, `providers/openai_provider.py`, `providers/ollama_provider.py`

**`src/heretek_swarm/channels/`:**
- Purpose: Communication channel registry
- Contains: `registry.py`, `defaults.py`

**`src/heretek_swarm/observability/`:**
- Purpose: Metrics and monitoring
- Contains: `metrics.py`, `prometheus_metrics.py`, `tracing.py`, `alerting.py`

**`src/heretek_swarm/logging/`:**
- Purpose: Structured logging configuration
- Contains: `config.py`

**`src/heretek_swarm/routing/`:**
- Purpose: LLM model routing
- Contains: `model_router.py`

**`src/heretek_swarm/config/`:**
- Purpose: Configuration management
- Contains: Config loaders and service

**`dashboard/frontend/src/`:**
- Purpose: React dashboard for swarm visualization
- Structure: See Frontend Directory Structure below

## Key File Locations

**Entry Points:**
- `src/heretek_swarm/api/main.py` - FastAPI server (port 8000)
- `src/heretek_swarm/runtime/main_loop.py` - Autonomous runtime
- `dashboard/frontend/src/main.tsx` - React entry point

**Configuration:**
- `src/heretek_swarm/config/` - Config loaders
- `dashboard/frontend/src/App.tsx` - Frontend routing

**Core Logic:**
- `src/heretek_swarm/actors/base/core.py` - AgentActor base class
- `src/heretek_swarm/actors/factory.py` - Agent factory
- `src/heretek_swarm/consensus/maker.py` - MAKER consensus

**Security:**
- `src/heretek_swarm/security/zero_trust.py` - Zero-trust validator

**Memory:**
- `src/heretek_swarm/memory/tiering.py` - Memory tier system

**Testing:**
- `tests/` - Python test files
- `dashboard/frontend/src/hooks/__tests__/` - React component tests

## Frontend Directory Structure

```
dashboard/frontend/src/
├── components/
│   ├── Agents/              # Agent management UI
│   │   ├── AgentCard.tsx, AgentConfigPanel.tsx, AgentsPage.tsx
│   │   ├── DeployAgentModal.tsx, AgentControls.tsx, index.ts
│   ├── Canvas/              # React Flow visual workflow builder
│   │   ├── Canvas.tsx, EnhancedCanvas.tsx, FlowCanvas.tsx
│   │   ├── AgentNode.tsx, NodePalette.tsx, CanvasToolbar.tsx
│   │   ├── ConnectionEdge.tsx, NodeConfigPanel.tsx
│   │   ├── MetricsOverlay.tsx, useMetrics.ts, index.ts
│   ├── Chat/                # Chat interface
│   │   ├── ChatInterface.tsx, MessageList.tsx, MessageInput.tsx, index.ts
│   ├── Consciousness/       # Consciousness metrics visualization
│   │   ├── ConsciousnessDashboard.tsx, ConsciousnessGauge.tsx
│   │   ├── AgentStatusGrid.tsx, RealTimeAgentPanel.tsx
│   │   ├── ConsciousnessPage.tsx, types.ts, index.ts
│   ├── Dashboard/          # Main dashboard
│   │   ├── Dashboard.tsx, UnifiedDashboard.tsx, Layout.tsx, index.ts
│   ├── Home/               # Home page
│   │   ├── HomePage.tsx, index.ts
│   ├── Logs/               # Log viewer
│   │   ├── LogsPage.tsx, index.ts
│   ├── Observability/      # Metrics and tracing
│   │   ├── Observability.tsx, A2ATracker.tsx, A2AMessageFlow.tsx
│   │   ├── LLMTrace.tsx, index.ts
│   ├── Settings/          # Configuration UI
│   │   ├── SettingsPage.tsx, AgentDefaultsSection.tsx
│   │   ├── EmbeddingProvidersSection.tsx, LLMProvidersSection.tsx
│   │   ├── ModelGarage.tsx, DeveloperModeToggle.tsx
│   │   ├── SystemConfigSection.tsx, ImportExportSection.tsx, index.ts
│   ├── Setup/             # Setup wizard
│   │   ├── SetupWizard.tsx, ConfigWizard.tsx, index.ts
│   ├── UI/               # Reusable UI components
│   │   ├── DataTable.tsx, LoadingSpinner.tsx, DebugPanel.tsx
│   │   ├── Toast.tsx, StatusBadge.tsx, EmptyState.tsx
│   │   ├── PerformanceOverlay.tsx, MetricCard.tsx
│   │   ├── ComponentErrorBoundary.tsx, ErrorBoundary.tsx, index.ts
│   ├── Workflow/         # Workflow configuration
│   │   ├── NodeConfigPanel.tsx
│   ├── WorkflowBuilder/  # Visual workflow builder
│   │   ├── WorkflowBuilder.tsx, AgentNode.tsx, MemoryNode.tsx
│   │   ├── ToolNode.tsx, LLMNode.tsx, DecisionNode.tsx
│   │   ├── ConnectorNode.tsx, NodeGroup.tsx, DynamicHandles.tsx
│   │   ├── ValidationPanel.tsx, types.ts, index.ts
│   ├── SwarmControlCenter.tsx
│   ├── SwarmHealthDashboard.tsx
│   └── ConsciousnessMetricsPanel.tsx
├── api/                  # API clients
│   ├── client.ts         # Base API client with fetch wrapper
│   ├── agents.ts        # Agent CRUD operations
│   ├── consciousness.ts # Consciousness metrics API
│   ├── configuration.ts  # Config management
│   └── wizard.ts        # Setup wizard API
├── hooks/               # Custom React hooks
│   ├── useWebSocket.ts  # WebSocket connection management
│   ├── useAgentStatus.ts # Agent status polling
│   ├── useAgentHandles.ts # React Flow node handles
│   └── __tests__/       # Hook tests
├── store/              # Zustand stores
│   └── middleware/     # Store middleware
├── stores/             # Additional stores
├── types/              # TypeScript definitions
│   └── reactflow.d.ts  # React Flow types
└── utils/              # Utilities
    ├── logger.ts       # Frontend logging
    └── setupValidation.ts # Setup validation
```

## Naming Conventions

**Files:**
- Python: `snake_case.py` (e.g., `zero_trust.py`, `maker_consensus.py`)
- TypeScript: `PascalCase.tsx` for components, `camelCase.ts` for utilities

**Directories:**
- Python: `snake_case/` (e.g., `actors/`, `consensus/`)
- TypeScript: `PascalCase/` for feature folders (e.g., `Components/`, `Hooks/`)

**Classes:**
- Python: `PascalCase` (e.g., `MAKERConsensus`, `ZeroTrustValidator`)
- TypeScript: `PascalCase` (e.g., `ConsciousnessDashboard`)

**Functions/Variables:**
- Python: `snake_case` (e.g., `start_consensus`, `agent_reputation`)
- TypeScript: `camelCase` (e.g., `useWebSocket`, `agentStatus`)

## Where to Add New Code

**New Agent:**
1. Create agent file: `src/heretek_swarm/actors/{agent_name}.py`
2. Inherit from `AgentActor` base class
3. Register in `src/heretek_swarm/actors/factory.py`
4. Add tests in `tests/`

**New API Endpoint:**
1. Create router file: `src/heretek_swarm/api/{feature}.py`
2. Import and add to `src/heretek_swarm/api/main.py`
3. Add WebSocket support if needed in `src/heretek_swarm/api/websockets.py`

**New Consensus Mechanism:**
1. Create in `src/heretek_swarm/consensus/{mechanism}.py`
2. Integrate with `Tribunal` or `MAKERConsensus`

**New Security Validator:**
1. Create in `src/heretek_swarm/security/{validator}.py`
2. Integrate with `ZeroTrustValidator` orchestrator

**New Memory Tier:**
1. Add tier definition to `src/heretek_swarm/memory/tiering.py`
2. Implement storage backend in appropriate module

**New Frontend Component:**
1. Create file in `dashboard/frontend/src/components/{Feature}/`
2. Export from `index.ts` in same directory
3. Add to routing in `App.tsx`

## Special Directories

**`.planning/codebase/`:**
- Purpose: Codebase mapping documents (ARCHITECTURE.md, STRUCTURE.md, etc.)
- Generated: Yes
- Committed: Yes

**`tests/`:**
- Purpose: Python pytest test suite
- Structure: Mirrors `src/` structure

**`docs/`:**
- Purpose: Architecture and API documentation
- Contains: ARCHITECTURE.md, API_ENDPOINTS.md, DEPLOYMENT.md, etc.

---

*Structure analysis: 2026-04-15*
