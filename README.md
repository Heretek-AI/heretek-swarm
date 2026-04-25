# Heretek Swarm - The Collective

**Version:** 0.1.0  
**Framework:** Python 3.11+  
**Status:** `PRODUCTION READY`  
**Last Updated:** 2026-04-18

---

## Installation

### Two-Package Architecture

This project ships as two separate packages:

| Package | Manager | Install Command | Path |
|---------|---------|------------------|------|
| **heretek-swarm** | pip | `pip install heretek-swarm` | `heretek-swarm/` |
| **@heretek-ai/swarm-dashboard** | npm | `cd swarm-dashboard && npm install` | `swarm-dashboard/` |

### Python Package (pip)

```bash
pip install heretek-swarm
```

The package provides the core `heretek_swarm` library installed under `heretek-swarm/heretek_swarm/`.

### Frontend Dashboard (npm)

```bash
cd swarm-dashboard
npm install
npm run dev
```

### Docker Compose (Local Development)

```bash
docker-compose up -d
```

Starts PostgreSQL, Redis, Qdrant, the API server, and the frontend dashboard.

---

## Package Structure

```
heretek-swarm/                  # Python package (pip-installable)
├── heretek_swarm/              # Core library
│   ├── actors/                # 23 agent implementations
│   ├── api/                    # FastAPI endpoints
│   ├── consciousness/         # Consciousness metrics (GWT, IIT, FEP)
│   ├── consensus/             # MAKER protocol implementation
│   ├── gateway/                # NATS event mesh
│   ├── memory/                 # Multi-tier memory system
│   ├── security/               # Zero-trust validation
│   └── state/                  # PostgreSQL persistence
├── config/                     # Configuration files
│   ├── litellm_config.yaml
│   ├── otel-collector-config.yaml
│   └── config.example.json
└── cli/                        # CLI entry point

swarm-dashboard/                # React dashboard (npm-managed)
├── src/                        # React/Vite application
├── public/
└── package.json
```

---

## Quick Start

### Prerequisites

| Requirement | Minimum |
|-------------|---------|
| **Docker** | 20.10+ |
| **Docker Compose** | 2.0+ |
| **Python** | 3.11+ |

### One-Shot Deployment

```bash
./deploy.sh
```

The script checks prerequisites, creates `.env`, pulls images, starts services, and runs migrations.

### Manual Start

```bash
# Start infrastructure
docker-compose up -d postgres redis qdrant

# Start API
uvicorn src.heretek_swarm.api.main:app --reload

# Start frontend
cd swarm-dashboard && npm run dev
```

### Script Commands

| Command | Description |
|---------|-------------|
| `./deploy.sh` | Deploy all services |
| `./deploy.sh stop` | Stop all services |
| `./deploy.sh restart` | Restart all services |
| `./deploy.sh status` | Show service status |
| `./deploy.sh logs` | View live logs |
| `./deploy.sh clean` | Remove all containers and volumes |

### Troubleshooting

```bash
docker-compose ps          # Check service status
docker-compose logs api    # View error logs
docker-compose restart api # Restart a specific service
```

### Kubernetes

For production Kubernetes deployment, see [`k8s/README.md`](k8s/README.md).

---

## Infrastructure (External Services)

The system depends on the following external services:

| Service | Default Port | Purpose |
|---------|--------------|---------|
| PostgreSQL | 5432 | State persistence, mem0 episodic memory |
| Redis | 6379 | Working memory, caching |
| Qdrant | 6333 | Semantic/vector memory storage |
| NATS | 4222 | Event mesh (A2A agent communication) |

All services are defined in `docker-compose.yml`. For local development without Docker, set `DATABASE_URL`, `REDIS_URL`, and `QDRANT_HOST` environment variables pointing to your infrastructure hosts.

---

## 🏛️ The 23 Agents

```
┌─────────────────────────────────────────────────────────────────┐
│                    THE COLLECTIVE (23 AGENT TYPES)              │
├─────────────────────────────────────────────────────────────────┤
│ TIER 1: CORE TRIAD (4)     │ TIER 4: SAFETY (3)               │
│ ├── Steward (Orchestrator) │ ├── Sentinel (Safety Guardian)   │
│ ├── Alpha (Deep Analysis)  │ ├── Sentinel-Prime (Security)    │
│ ├── Beta (Validation)      │ └── Arbiter (Conflict Resolution)│
│ └── Charlie (Challenge)    │                                   │
│                            │ TIER 5: COORDINATION (4)         │
│ TIER 2: SUPPORT (5)        │ ├── Coordinator (Multi-Agent)    │
│ ├── Historian (Memory)     │ ├── Nexus (External Integration) │
│ ├── Metis (Strategy)       │ ├── Catalyst (Change Mgmt)       │
│ ├── Empath (Emotional IQ)  │ └── Chronos (Scheduling)         │
│ └── Perceiver (Sensory)    │                                   │
│                            │ TIER 6: ENHANCEMENT (3)          │
│ TIER 3: EXPLORATION (4)    │ ├── Prism (Multi-Perspective)    │
│ ├── Explorer (Discovery)   │ ├── Habit-Forge (Optimization)   │
│ ├── Examiner (QA)          │ └── Perceiver+ (Advanced)        │
│ └── Coder (Implementation)│                                   │
└─────────────────────────────────────────────────────────────────┘
```

---

## System Architecture

### Components

| Component | Port | Notes |
|-----------|------|-------|
| FastAPI Server | 8000 | Python 3.11+ |
| React Dashboard | 3000 → 80 | Vite/React |
| PostgreSQL | 5432 | pgvector enabled |
| Redis | 6379 | redis:7-alpine |
| Qdrant | 6333 | Vector storage |

### Frontend Dashboard

The React-based dashboard (located in `swarm-dashboard/`) provides:

- **Agent Management:** Deploy and monitor agents
- **Consciousness Metrics:** Real-time consciousness visualizations
- **Workflow Builder:** Visual workflow design with React Flow
- **Settings:** LLM providers, embedding models, system config

**Technology Stack:** React 18.2+, Vite 5.0+, @xyflow/react 12.0+, Zustand, Tailwind CSS 3.4+

---

## Configuration

| Variable | Required | Description |
|----------|----------|-------------|
| `DATABASE_URL` | Yes | PostgreSQL connection string |
| `REDIS_URL` | Yes | Redis connection string |
| `QDRANT_HOST` | Yes | Qdrant host |
| `OPENAI_API_KEY` | Yes | OpenAI-compatible API key |
| `OPENAI_BASE_URL` | Yes | OpenAI-compatible API base URL |
| `LLM_MODEL` | Yes | LLM model name |

---

## Documentation

| Document | Description |
|----------|-------------|
| [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) | System architecture details |
| [`docs/API_ENDPOINTS.md`](docs/API_ENDPOINTS.md) | API reference |
| [`docs/DEPLOYMENT.md`](docs/DEPLOYMENT.md) | Deployment guide |
| [`docs/CONSCIOUSNESS_PLUGINS.md`](docs/CONSCIOUSNESS_PLUGINS.md) | Consciousness frameworks |
| [`docs/AGENTS.md`](docs/AGENTS.md) | Complete agent reference |
| [`PRIME_DIRECTIVE.md`](PRIME_DIRECTIVE.md) | Project vision and philosophy |
| [`swarm-dashboard/README.md`](swarm-dashboard/README.md) | Frontend dashboard docs |

---

## The Prime Directive

> **Build a self-governing swarm of 23 specialized AI agents that operate independently 24/7, make collective decisions through consensus, adapt and learn from experience, and exhibit emergent collective intelligence.**

🦞 *The thought that never ends.*

---

**License:** Apache 2.0

*Last Updated: 2026-04-18*
