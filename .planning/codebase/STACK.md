# Technology Stack

**Analysis Date:** 2026-04-15

## Languages

**Primary:**
- Python 3.11+ - Core backend, agents, API server, orchestration
- TypeScript/TSX - Frontend dashboard (React 18.2+)

**Secondary:**
- JavaScript (ES2022) - Frontend build tooling

## Runtime

**Environment:**
- Python 3.11+ (requires >=3.11 per pyproject.toml)
- Node.js 18+ (for frontend build)

**Package Managers:**
- Python: `pip` with `setuptools` build backend
- Node.js: `npm` (v8+ for workspaces)
- Lockfiles: `package-lock.json` (npm), `pip` constraints optional

## Frameworks

**Backend:**
- FastAPI 0.109+ - API framework (`src/heretek_swarm/api/`)
- Starlette 0.27+ - Web toolkit (ASGI)
- Uvicorn 0.25+ - ASGI server
- Pydantic v2.0+ - Data validation and settings
- websockets 12.0+ - WebSocket support for real-time communication

**Frontend:**
- React 18.2+ - UI framework (`dashboard/frontend/`)
- Vite 5.0+ - Build tool and dev server
- @xyflow/react 12.10+ - React Flow for workflow canvas
- Zustand 4.5+ - State management
- Tailwind CSS 3.4+ - Utility-first CSS framework

**Agent Framework:**
- Swarms 5.0+ - Multi-agent orchestration framework

**Testing:**
- pytest 8.0+ - Python testing framework
- pytest-asyncio 0.23+ - Async test support
- pytest-cov 4.1+ - Coverage reporting
- pytest-xdist 3.5+ - Parallel test execution
- pytest-mock 3.12+ - Mocking utilities
- pytest-timeout 2.3+ - Test timeout control

**Load Testing:**
- Locust 2.23+ - Distributed load testing

## Key Dependencies

**Core Agents & Orchestration:**
- `swarms>=5.0.0` - Multi-agent framework
- `pydantic>=2.0.0` - Data validation
- `mem0ai>=1.0.0` - Long-term memory system

**HTTP & Networking:**
- `httpx>=0.25.0` - HTTP client (async)
- `websockets>=12.0` - WebSocket support
- `nats>=2.5.0` - NATS client library

**Database & Storage:**
- `redis>=5.0.0` - Redis client for caching/pub-sub
- `qdrant-client>=1.7.0` - Vector database client
- `asyncpg>=0.29.0` - Async PostgreSQL driver
- `psycopg2-binary>=2.9.0` - PostgreSQL adapter

**Observability:**
- `opentelemetry-api>=1.22.0` - OpenTelemetry API
- `opentelemetry-sdk>=1.22.0` - OpenTelemetry SDK
- `opentelemetry-exporter-otlp>=1.22.0` - OTLP exporter
- `structlog>=24.1.0` - Structured logging
- `prometheus-client>=0.19.0` - Prometheus metrics

**Resilience:**
- `tenacity>=8.2.0` - Retry logic
- `circuitbreaker>=2.0.0` - Circuit breaker pattern

**CLI & Configuration:**
- `click>=8.1.0` - CLI framework
- `gunicorn>=21.0.0` - WSGI server

**Frontend Dependencies:**
- `axios>=1.6.0` - HTTP client
- `pino>=8.21.0` - Logging (frontend)
- `reactflow>=11.10.0` - React Flow nodes
- `eslint>=8.55.0` - Linting
- `typescript>=5.2.2` - TypeScript compiler
- `autoprefixer>=10.4.16` - CSS autoprefixing
- `postcss>=8.4.32` - CSS processing

**Dev Tools:**
- `ruff>=0.2.0` - Python linting
- `mypy>=1.8.0` - Type checking
- `coverage[toml]>=7.4.0` - Coverage measurement
- `pre-commit>=3.6.0` - Git hooks
- `testcontainers>=3.7.0` - Docker test containers

## Infrastructure Services

**Container Platform:**
- Docker 20.10+ - Container runtime
- Docker Compose 2.0+ - Multi-container orchestration

**Service Images:**
- `pgvector/pgvector:pg16` - PostgreSQL with vector support
- `redis:7-alpine` - Redis 7
- `qdrant/qdrant:latest` - Vector database
- `nats:2.10-alpine` - NATS messaging with JetStream

**Optional Services:**
- `ghcr.io/berriai/litellm:latest` - LiteLLM proxy for multi-provider LLM
- `ollama/ollama:latest` - Local LLM inference
- `mem0ai/mem0` - Self-hosted memory service

## Configuration

**Environment Variables:**
| Variable | Purpose |
|----------|---------|
| `DATABASE_URL` | PostgreSQL async connection string |
| `REDIS_URL` | Redis connection string |
| `QDRANT_HOST` | Qdrant server host |
| `NATS_URL` | NATS server URL |
| `OPENAI_API_KEY` | OpenAI API key |
| `MINIMAX_API_KEY` | MiniMax API key |
| `HERETEK_API_KEY` | Internal API authentication |
| `LLM_MODEL` | Default LLM model |
| `EMBEDDING_PROVIDER` | Embedding provider type |
| `EMBEDDER_MODEL` | Embedding model |

**Config Files:**
- `pyproject.toml` - Python project configuration
- `package.json` - Node.js dependencies
- `docker-compose.yml` - Service orchestration
- `tailwind.config.js` - Tailwind CSS configuration
- `vite.config.ts` - Vite build configuration
- `tsconfig.json` - TypeScript configuration
- `.env.example` - Environment template

## Platform Requirements

**Development:**
- Python 3.11+
- Node.js 18+
- Docker Desktop / Docker Engine
- 4GB RAM minimum
- 10GB disk space

**Production:**
- Docker Compose OR Kubernetes
- PostgreSQL 15+ with pgvector
- Redis 7+
- Qdrant 1.8+
- NATS 2.10+ with JetStream
- 8GB RAM recommended
- 20GB+ disk space

## Directory Structure

```
heretek-swarm/
├── src/heretek_swarm/     # Python source
│   ├── actors/            # 23 agent implementations
│   ├── api/               # FastAPI endpoints
│   ├── llm/               # LLM providers
│   ├── memory/            # Memory systems
│   ├── gateway/           # NATS event mesh
│   ├── consensus/         # Consensus engine
│   ├── security/           # Zero-trust validation
│   └── state/             # State persistence
├── dashboard/frontend/     # React frontend
├── docker/                 # Docker configurations
├── k8s/                    # Kubernetes manifests
├── tests/                  # Test suite
└── migrations/            # Database migrations
```

---

*Stack analysis: 2026-04-15*
