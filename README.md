# Heretek Swarm — The Collective

**Version:** 0.2.0  
**Framework:** Python 3.11+  
**Last Updated:** 2026-05-02

---

## Installation

### Python Package (pip)

```bash
# Editable install (development)
pip install -e backend/

# Or install from PyPI (when published)
pip install heretek-swarm
```

This provides the `heretek-swarm` CLI command (see [Command Reference](#command-reference) below).

### Docker Compose

```bash
cp .env.example .env
# Edit .env and set your OPENAI_API_KEY (and other values as needed)
cd backend && docker compose up
```

Starts all 6 services with health checks: PostgreSQL, Redis, Qdrant, NATS, API server, and React dashboard. No profile flags needed — everything starts by default.

---

## Quick Start

### Local (no infrastructure)

Run the swarm with in-memory state — no Docker, Postgres, Redis, Qdrant, or NATS required:

```bash
pip install -e .
heretek-swarm run --no-infra --prompt "Hello"
```

The swarm starts all 23 agents in-memory and deliberates your prompt through the Alpha/Beta/Charlie triad, then exits.

### Full Stack

```bash
cp .env.example .env
# Edit .env: set OPENAI_API_KEY, OPENAI_BASE_URL, LLM_MODEL
docker compose up
```

The API server starts on `http://localhost:8000` and the dashboard on `http://localhost:3000`. Use `heretek-swarm status` to verify all services are healthy.

---

## Command Reference

All commands are accessed via the `heretek-swarm` CLI. Run `heretek-swarm --help` for grouped help output.

### Core Operations

| Command | Description |
|---------|-------------|
| `heretek-swarm run` | Start the autonomous runtime (all 23 agents) as a standalone process |
| `heretek-swarm serve` | Start the FastAPI API server with auto-reload |
| `heretek-swarm deploy` | Print infrastructure setup instructions for Docker Compose |
| `heretek-swarm wizard` | Open the browser to the React dashboard setup wizard |

### Configuration

| Command | Description |
|---------|-------------|
| `heretek-swarm config` | Manage LLM provider configuration (wizard, list, remove, set-default, validate) |
| `heretek-swarm init` | Bootstrap `~/.heretek-swarm/.env` from `.env.example` |

### Monitoring

| Command | Description |
|---------|-------------|
| `heretek-swarm status` | Check infrastructure health; use `--json` for machine-readable output |
| `heretek-swarm stop` | Stop a running background daemon |

### Common Options

```bash
# Run in background (daemon mode)
heretek-swarm run --detach

# Skip all external infrastructure
heretek-swarm run --no-infra

# Route prompt to a specific agent
heretek-swarm run --no-infra --prompt "Analyze X" --target-agent alpha

# Serve on a custom host/port
heretek-swarm serve --host 127.0.0.1 --port 9000

# Get JSON status output
heretek-swarm status --json
```

---

## Package Structure

```
backend/                        # Python project root
├── pyproject.toml              # Package metadata & CLI entry point
├── docker-compose.yml          # All 6 services with health checks
├── .env.example                # Environment template with all vars
├── docs/                       # Architecture & API documentation
│   ├── ARCHITECTURE.md
│   ├── API_ENDPOINTS.md
│   ├── DEPLOYMENT.md
│   └── AGENTS.md
├── README.md
└── heretek_swarm/              # Core library
    ├── actors/                 # 23 agent implementations
    ├── api/                    # FastAPI endpoints
    ├── cli/                    # CLI commands & config loader
    ├── config/                 # Pydantic config models
    ├── consciousness/          # Consciousness metrics (GWT, IIT, FEP)
    ├── consensus/              # MAKER protocol implementation
    ├── gateway/                # NATS event mesh
    ├── memory/                 # Multi-tier memory system
    ├── runtime/                # AutonomousSwarm main loop & daemon
    ├── security/               # Zero-trust validation
    └── state/                  # PostgreSQL persistence
```

`swarm-dashboard/` at repo root contains the React frontend (fully decoupled).

---

## Infrastructure

All services are defined in `docker-compose.yml` and start automatically with `docker compose up`.

| Service | Default Port | Purpose |
|---------|--------------|---------|
| PostgreSQL | 5432 | State persistence, mem0 episodic memory |
| Redis | 6379 | Working memory, caching |
| Qdrant | 6333 | Semantic/vector memory storage |
| NATS | 4222 | Event mesh (A2A agent communication) |
| API Server | 8000 | FastAPI backend with 23 spawned agents |
| Dashboard | 3000 | React frontend (Vite + Tailwind CSS) |

All services include health checks and restart policies. Docker Compose coordinates startup order via `depends_on` with `condition: service_healthy`.

---

## The 23 Agents

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
│ └── Coder (Implementation) │                                   │
└─────────────────────────────────────────────────────────────────┘
```

---

## Configuration

Copy `.env.example` to `.env` and fill in your values. The key variables:

| Variable | Required | Description |
|----------|----------|-------------|
| `DATABASE_URL` | Yes | PostgreSQL connection string |
| `REDIS_URL` | Yes | Redis connection string |
| `QDRANT_HOST` | Yes | Qdrant host |
| `OPENAI_API_KEY` | Yes | OpenAI-compatible API key |
| `OPENAI_BASE_URL` | Yes | OpenAI-compatible API base URL |
| `LLM_MODEL` | Yes | LLM model name |

Docker Compose defaults are pre-configured in `.env.example` — for local development outside Docker, update the hostnames from service names (`postgres`, `redis`, `qdrant`, `nats`) to `localhost`.

---

## Documentation

| Document | Description |
|----------|-------------|
| [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) | System architecture details |
| [`docs/API_ENDPOINTS.md`](docs/API_ENDPOINTS.md) | API reference |
| [`docs/DEPLOYMENT.md`](docs/DEPLOYMENT.md) | Deployment guide |
| [`docs/AGENTS.md`](docs/AGENTS.md) | Complete agent reference |
| [`PRIME_DIRECTIVE.md`](PRIME_DIRECTIVE.md) | Project vision and philosophy |

---

## The Prime Directive

> **Build a self-governing swarm of 23 specialized AI agents that operate independently 24/7, make collective decisions through consensus, adapt and learn from experience, and exhibit emergent collective intelligence.**

🦞 *The thought that never ends.*

---

**License:** Apache 2.0

*Last Updated: 2026-05-02*

