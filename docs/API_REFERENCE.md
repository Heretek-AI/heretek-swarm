# Heretek Swarm API Reference

**Version:** 2.0.0  
**Session:** 21 (2026-04-06)

> **Note:** This API reference has been split into separate, focused documents for better organization. Please use the links below to navigate to specific sections.

---

## Documentation Index

For the main documentation index with quick navigation, see [INDEX.md](./INDEX.md).

---

## API Reference Sections

| Document | Description |
|----------|-------------|
| [Core Actors System](./CORE_ACTORS.md) | AgentActor base class, ActorMessage, ActorFactory, ActorSupervisor, validation models |
| [Agent Reference](./AGENT_REFERENCE.md) | Complete reference for all 23 agents organized by tier |
| [Gateway & Communication](./GATEWAY_COMMUNICATION.md) | EventMesh, A2A protocol server, authentication, NATS event mesh |
| [Memory System](./MEMORY_SYSTEM.md) | Mem0Backend, memory models, dual-tier architecture, usage examples |
| [Consciousness Plugins](./CONSCIOUSNESS_PLUGINS.md) | GWT, IIT, AST, FEP implementations and metrics |
| [API Endpoints](./API_ENDPOINTS.md) | REST API endpoints, WebSocket, rate limiting, error responses |

---

## Quick Reference

### Main API Entry Point

**File:** [`src/heretek_swarm/api/main.py`](../src/heretek_swarm/api/main.py)

```python
app = FastAPI(title="Heretek Swarm API", version="2.0.0")

# Include routers
app.include_router(workflows.router, prefix="/api/workflows")
app.include_router(observability.router, prefix="/api/observability")
app.include_router(plugins.router, prefix="/api/plugins")
app.include_router(autonomous.router, prefix="/api/autonomous")
app.include_router(agents_management.router, prefix="/api/agents")
app.include_router(consensus.router, prefix="/api/consensus")
```

### Health Endpoints

```bash
# API health
curl http://localhost:8000/health

# Readiness probe
curl http://localhost:8000/ready

# Liveness probe
curl http://localhost:8000/live
```

### Key API Routes

| Route | Method | Description | Full Docs |
|-------|--------|-------------|-----------|
| `/api/workflows/execute` | POST | Execute workflow | [API Endpoints](./API_ENDPOINTS.md#workflow-endpoints) |
| `/api/consciousness/metrics` | GET | Global consciousness metrics | [Consciousness Plugins](./CONSCIOUSNESS_PLUGINS.md) |
| `/api/observability/traces` | GET | Execution traces | [API Endpoints](./API_ENDPOINTS.md#observability-endpoints) |
| `/api/agents/status` | GET | All agents status | [API Endpoints](./API_ENDPOINTS.md) |

---

## See Also

- [Documentation Index](./INDEX.md) - Main documentation navigation
- [Deployment Guide](./DEPLOYMENT.md) - Setup and deployment instructions
- [Expansion Roadmap](./EXPANSION_ROADMAP.md) - Development priorities

---

**License:** Apache 2.0  
**GitHub:** [Heretek-AI/heretek-swarm](https://github.com/Heretek-AI/heretek-swarm)
