# Codebase Structure

**Analysis Date:** 2026-04-12

## Directory Layout

```
/home/john/Projects/heretek-swarm/
├── src/                          # Python source code
│   ├── heretek_swarm/            # Main package
│   └── cli.py                    # CLI entry point
├── tests/                        # Test suite
├── dashboard/                    # React frontend
├── docker/                       # Docker configurations
├── k8s/                         # Kubernetes manifests
├── migrations/                   # Database migrations
├── scripts/                      # Utility scripts
├── docs/                         # Documentation
└── [config files]                # pyproject.toml, package.json, etc.
```

## Directory Purposes

**Source (`src/heretek_swarm/`):**
- Purpose: Main Python package containing all application code
- Contains: actors, api, collective, config, consciousness, consensus, memory, security, etc.
- Key files: `__init__.py`, api/main.py, actors/base.py

**Actors (`src/heretek_swarm/actors/`):**
- Purpose: Agent implementations and base classes
- Contains: AgentActor base, specialized agents (Alpha, Beta, Coordinator, etc.), mixins, supervisor, factory
- Key files: `base.py`, `supervisor.py`, `factory.py`

**API (`src/heretek_swarm/api/`):**
- Purpose: HTTP/WebSocket gateway and REST endpoints
- Contains: main.py, websockets.py, agents/, workflows.py, consensus.py, consciousness.py
- Key files: `main.py` (FastAPI app), `websockets.py`

**Collective (`src/heretek_swarm/collective/`):**
- Purpose: Swarm intelligence and emergent behavior
- Contains: swarm_intelligence.py, emergence_detection.py, adaptive_learning.py, agency_tracking.py
- Key files: `swarm_intelligence.py`

**Memory (`src/heretek_swarm/memory/`):**
- Purpose: Persistent memory storage
- Contains: persistent.py, mem0 integration
- Key files: `persistent.py`

**Security (`src/heretek_swarm/security/`):**
- Purpose: Authentication, authorization, guardrails
- Contains: zero_trust.py, guardrails.py, adversarial.py, ddos_protection.py
- Key files: `zero_trust.py`

**Consciousness (`src/heretek_swarm/consciousness/`):**
- Purpose: Agent self-modeling and introspection
- Contains: iit_phi.py, introspection.py, fep_active_inference.py, self_model.py

**Consensus (`src/heretek_swarm/consensus/`):**
- Purpose: Multi-agent deliberation and consensus
- Contains: deliberation.py, tribunal.py, maker_enhanced.py

**Infrastructure (`src/heretek_swarm/infrastructure/`):**
- Purpose: Cross-cutting infrastructure services
- Contains: NATS event mesh, database connections

**Logging (`src/heretek_swarm/logging/`):**
- Purpose: Structured logging configuration
- Contains: config.py for structlog setup

**Observability (`src/heretek_swarm/observability/`):**
- Purpose: Metrics and distributed tracing
- Contains: prometheus_metrics.py, tracing.py

**Gateway (`src/heretek_swarm/gateway/`):**
- Purpose: Authentication and request gateway
- Contains: auth.py (Bearer token auth)

**Tests (`tests/`):**
- Purpose: Test suite organized by type
- Contains: unit/, integration/, load/, fixtures/, various domain folders
- Pattern: Tests mirror source structure under `tests/`

**Dashboard (`dashboard/`):**
- Purpose: React frontend application
- Contains: frontend/ (Vite + React application)

## Key File Locations

**Entry Points:**
- `src/cli.py`: CLI application entry point
- `src/heretek_swarm/api/main.py`: FastAPI application factory
- `dashboard/frontend/src/main.tsx`: React application entry point

**Configuration:**
- `pyproject.toml`: Python package configuration and dependencies
- `package.json`: Node.js dependencies and scripts
- `config.example.json`: Configuration template
- `.env.example`: Environment variables template
- `vite.config.ts`: Vite bundler configuration

**Actor Base:**
- `src/heretek_swarm/actors/base.py`: AgentActor base class (1528 lines)
- `src/heretek_swarm/actors/supervisor.py`: ActorSupervisor for actor management

**API Routes:**
- `src/heretek_swarm/api/main.py`: Main FastAPI app with all routers included
- `src/heretek_swarm/api/websockets.py`: WebSocket handling (44514 bytes)
- `src/heretek_swarm/api/consensus.py`: Consensus endpoints
- `src/heretek_swarm/api/consciousness.py`: Consciousness endpoints
- `src/heretek_swarm/api/wizard.py`: Configuration wizard endpoints

## Naming Conventions

**Files:**
- Python: `snake_case.py`
- TypeScript/React: `PascalCase.tsx` for components, `camelCase.ts` for utilities
- Config: `kebab-case.extension`

**Directories:**
- Python modules: `snake_case/`
- TypeScript: `camelCase/` or `kebab-case/`

**Classes:**
- PascalCase: `AgentActor`, `ActorSupervisor`, `SwarmIntelligenceEngine`

## Where to Add New Code

**New Agent:**
- Implementation: `src/heretek_swarm/actors/[agent_name].py`
- Tests: `tests/actors/test_[agent_name].py`
- Register in: `src/heretek_swarm/actors/factory.py`

**New API Endpoint:**
- Implementation: `src/heretek_swarm/api/[feature].py`
- Router registration: `src/heretek_swarm/api/main.py`
- Tests: `tests/integration/test_[feature].py`

**New Collective Algorithm:**
- Implementation: `src/heretek_swarm/collective/[algorithm].py`
- Tests: `tests/collective/test_[algorithm].py`

**New Security Component:**
- Implementation: `src/heretek_swarm/security/[component].py`
- Tests: `tests/security/test_[component].py`

**New Frontend Component:**
- Implementation: `dashboard/frontend/src/components/[Feature]/`
- Tests: `dashboard/frontend/src/components/[Feature]/*.test.tsx`

## Special Directories

**Node Modules (`node_modules/`):**
- Purpose: NPM dependencies
- Generated: Yes
- Committed: No

**Python Cache (`__pycache__/`):**
- Purpose: Python bytecode cache
- Generated: Yes
- Committed: No

**Test Fixtures (`tests/fixtures/`):**
- Purpose: Shared test data and fixtures
- Contains: `conftest.py`, factory fixtures

**Docker (`docker/`):**
- Purpose: Docker-related configurations
- Contains: Dockerfiles, docker-compose files

**Kubernetes (`k8s/`):**
- Purpose: K8s deployment manifests
- Contains: Service, deployment, ingress YAMLs

---

*Structure analysis: 2026-04-12*
