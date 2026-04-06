# Heretek Swarm Documentation Index

**Version:** 1.11.0  
**Session:** 21 (2026-04-06)  
**Health Score:** 100/100  
**Agents:** 23/23 Implemented

Welcome to the Heretek Swarm documentation. This index provides navigation to all documentation sections.

---

## Quick Navigation

| Document | Description |
|----------|-------------|
| [Core Actors System](./CORE_ACTORS.md) | AgentActor base class, validation models, actor lifecycle |
| [Agent Reference](./AGENT_REFERENCE.md) | Complete reference for all 23 agents by tier |
| [Gateway & Communication](./GATEWAY_COMMUNICATION.md) | A2A protocol, event mesh, authentication |
| [Memory System](./MEMORY_SYSTEM.md) | Dual-tier memory with mem0, Qdrant, PostgreSQL |
| [Consciousness Plugins](./CONSCIOUSNESS_PLUGINS.md) | GWT, IIT, AST, FEP implementations |
| [API Endpoints](./API_ENDPOINTS.md) | REST API reference |
| [Deployment Guide](./DEPLOYMENT.md) | Setup and deployment instructions |
| [Expansion Roadmap](./EXPANSION_ROADMAP.md) | Development priorities and roadmap |
| [Development Plan](./DEVELOPMENT_PLAN.md) | Phase-based execution roadmap |
| [Remediation Backlog](./REMEDIATION_BACKLOG.md) | Technical debt and remediation tracking |

---

## Documentation Structure

```
docs/
├── INDEX.md                    # This file - documentation index
├── CORE_ACTORS.md              # Core actors system documentation
├── AGENT_REFERENCE.md          # All 23 agents reference
├── GATEWAY_COMMUNICATION.md    # Gateway and communication
├── MEMORY_SYSTEM.md            # Memory system documentation
├── CONSCIOUSNESS_PLUGINS.md    # Consciousness plugins
├── API_ENDPOINTS.md            # API endpoints reference
├── DEPLOYMENT.md               # Deployment guide
├── EXPANSION_ROADMAP.md        # Development roadmap
├── DEVELOPMENT_PLAN.md         # Phase-based plan
├── REMEDIATION_BACKLOG.md      # Technical debt backlog
└── architecture/               # Architecture documentation
    ├── actors-system.md
    ├── consensus-mechanism.md
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

- **Version**: 1.11.0
- **Session**: 21 Complete
- **Health Score**: 100/100
- **Agents Implemented**: 23/23 (100%)
- **Zero-Trust Compliance**: Verified

### Next Priorities

| Priority | Feature | Status |
|----------|---------|--------|
| P1 | Consciousness Metrics (IIT Phi, FEP) | ⏳ Pending |
| P1 | Event Mesh (NATS JetStream) | ⏳ Pending |
| P2 | WebUI (ReactFlow) | ⏳ Pending |
| P2 | Integration Testing | ⏳ Pending |
| P3 | Load Testing | ⏳ Pending |

See [EXPANSION_ROADMAP.md](./EXPANSION_ROADMAP.md) for details.

---

## External Links

- **GitHub**: [Heretek-AI/heretek-swarm](https://github.com/Heretek-AI/heretek-swarm)
- **License**: Apache 2.0
