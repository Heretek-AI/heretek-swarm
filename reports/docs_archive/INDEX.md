# Heretek Swarm Documentation Index

**Version:** 2.0.0  
**Date:** 2026-04-10  
**Health Score:** 98/100  
**Phase:** Phase 1-2 Complete — Audit & Remediation  
**Agents:** 23/23 Implemented

Welcome to the Heretek Swarm documentation. This index provides navigation to all documentation sections.

---

## Quick Navigation

| Document | Description |
|----------|-------------|
| [Core Actors System](./CORE_ACTORS.md) | AgentActor base class, validation models, actor lifecycle |
| [Agent Reference](./AGENT_REFERENCE.md) | Complete reference for all 23 agents by tier |
| [Memory System](./MEMORY_SYSTEM.md) | Dual-tier memory with mem0, Qdrant, PostgreSQL |
| [Emergent Intelligence](./architecture/emergent-intelligence.md) | GWT, IIT, AST, FEP implementations |
| [API Endpoints](./API_ENDPOINTS.md) | REST API reference |
| [Deployment Guide](./DEPLOYMENT.md) | Setup and deployment instructions |
| [Autonomous Workflow](./AUTONOMOUS_WORKFLOW.md) | 24/7 autonomous operation guide |

> **Note:** Some legacy documents (Gateway Communication, Development Plan, Expansion Roadmap, Remediation Backlog) have been archived or migrated. Gateway communication is documented in `backend/heretek_swarm/gateway/`. Development tracking is handled via GSD milestones.

---

## Documentation Structure

```
docs/
├── INDEX.md                    # This file - documentation index
├── CORE_ACTORS.md              # Core actors system documentation
├── AGENT_REFERENCE.md          # All 23 agents reference
├── MEMORY_SYSTEM.md            # Memory system documentation
├── API_ENDPOINTS.md            # API endpoints reference
├── DEPLOYMENT.md               # Deployment guide
├── AUTONOMOUS_WORKFLOW.md      # 24/7 autonomous operation
└── architecture/               # Architecture documentation
    ├── actors-system.md
    ├── consensus-mechanism.md
    ├── emergent-intelligence.md
    ├── memory-system.md
    ├── observability.md
    ├── orchestration-system.md
    ├── plugins.md
    └── state-management.md
```

---

## System Overview

### The 23 Agents

| Tier | Agents | Purpose |
|------|--------|---------|
| Tier 1 | Steward, Alpha, Beta, Charlie | Core Triad - Governance |
| Tier 2 | Historian, Metis, Empath, Perceiver, Echo | Support - Knowledge & Memory |
| Tier 3 | Explorer, Examiner, Dreamer, Coder | Exploration - Discovery & Creation |
| Tier 4 | Sentinel, Sentinel Prime, Arbiter | Safety & Security - Protection |
| Tier 5 | Coordinator, Nexus, Catalyst, Chronos | Coordination - Integration |
| Tier 6 | Prism, Habit Forge, Perceiver+ | Enhancement - Optimization |

### Key Components

- **Actor Model**: Async message passing for all agents
- **Zero-Trust Security**: Pydantic v2 validation for all inputs
- **Consciousness Framework**: GWT, IIT, AST, FEP theories
- **Dual-Tier Memory**: Redis (ephemeral), PostgreSQL (persistent), Qdrant (vector)
- **Event Mesh**: WebSocket + NATS JetStream for communication
- **FastAPI**: REST API with WebSocket support

---

## Getting Started

1. **Quick Start**: See [Deployment Guide - Quick Start](./DEPLOYMENT.md#quick-start)
2. **Architecture**: Read [Core Actors System](./CORE_ACTORS.md)
3. **Agent Details**: Browse [Agent Reference](./AGENT_REFERENCE.md)
4. **API Usage**: Check [API Endpoints](./API_ENDPOINTS.md)

---
## Development

### Current Status

- **Version**: 2.0.0
- **Date**: 2026-04-10
- **Health Score**: 98/100 (Active Development)
- **Phase**: Phase 1-2 Complete — Audit & Remediation
- **Agents Implemented**: 23/23 (100%)
- **Zero-Trust Compliance**: Verified

### Next Priorities

| Priority | Feature | Status |
|----------|---------|--------|
| P1 | Consciousness Metrics (IIT Phi, FEP) | ✅ Wired in main loop |
| P1 | Event Mesh (NATS JetStream) | ✅ Operational |
| P1 | Zero-Trust Validation | ✅ Active |
| P2 | WebUI Dashboard | ✅ Implemented |
| P2 | Tribunal Integration | ✅ Wired (M029) |
| P3 | Load Testing | ⏳ Pending |

> Development priorities are tracked via GSD milestones in `.gsd/milestones/`.

---

## External Links

- **GitHub**: [Heretek-AI/heretek-swarm](https://github.com/Heretek-AI/heretek-swarm)
- **License**: Apache 2.0
