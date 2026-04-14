# Technology Stack

**Analysis Date:** 2026-04-13

## Languages

**Primary:**
- Python 3.12+ - Core backend, agents, API services
- TypeScript 5.3+ - Frontend (React), Electron desktop app

**Secondary:**
- JavaScript - Electron main process

## Runtime

**Python:**
- Version: 3.12+ (from pyproject.toml requires-python)
- Package Manager: pip/uv

**Node.js:**
- Version: 20.x (from @types/node ^20.10.0)
- Package Manager: npm

## Frameworks

**Backend:**
- FastAPI 0.109+ - HTTP API framework (`src/heretek_swarm/api/`, `mem0_server/main.py`)
- Starlette 0.27+ - ASGI framework (underlying FastAPI)
- Uvicorn 0.25+ - ASGI server

**Agent Framework:**
- Swarms 5.0+ - Agent orchestration (from requirements.txt)
- Pydantic 2.0+ - Data validation (base models, agents)

**Frontend:**
- React 18.2+ - UI framework
- Vite 5.0+ - Build tool
- React Router 6.21+ - Routing

**Desktop:**
- Electron 28+ - Desktop app shell

**Testing:**
- pytest - Python testing framework
- Vitest - JS/TS testing (implied by Vite ecosystem)

**Styling:**
- Tailwind CSS 3.4+ - Utility-first CSS

## Key Dependencies

**Agent & AI:**
- `swarms>=5.0.0` - Agent orchestration
- `mem0ai>=1.0.0` - Memory system
- `opentelemetry-api>=1.22.0` - Observability tracing
- `opentelemetry-sdk>=1.22.0` - Observability SDK

**Web & HTTP:**
- `httpx>=0.25.0` - Async HTTP client
- `websockets>=12.0` - WebSocket support

**Database & Cache:**
- `redis>=5.0.0` - Caching, session
- `qdrant-client>=1.7.0` - Vector database (RAG, memory)
- `asyncpg>=0.29.0` - PostgreSQL async driver
- `psycopg2-binary>=2.9.0` - PostgreSQL sync driver

**Validation & Serialization:**
- `pydantic>=2.0.0` - Data validation

**Logging & Observability:**
- `structlog>=24.1.0` - Structured logging
- `prometheus-client>=0.19.0` - Metrics
- `opentelemetry-exporter-otlp>=1.22.0` - Trace export

**Resilience:**
- `tenacity>=8.2.0` - Retry logic
- `circuitbreaker>=2.0.0` - Circuit breaker pattern

**Web Servers:**
- `gunicorn>=21.0.0` - WSGI server

**Frontend Libraries:**
- `lucide-react` - Icons
- `zustand>=4.4.7` - State management
- `electron-log>=5.0.3` - Electron logging
- `electron-store>=8.1.0` - Electron config storage

**CLI:**
- `click` - CLI framework

**NATS:**
- `nats-py` - NATS client for event mesh

## Configuration

**Environment:**
- Python: `.env` via `python-dotenv`
- Node: `package.json` scripts

**Build Tools:**
- Vite (frontend build)
- electron-builder (desktop packaging)
- TypeScript compiler

**Deployment:**
- Kubernetes (k8s/ directory)
- Docker (docker-compose implied)

**LLM Routing:**
- LiteLLM (`litellm_config.yaml`) - Multi-provider LLM proxy

## Platform Requirements

**Development:**
- Python 3.12+
- Node.js 20+
- NATS server (for event mesh)

**Production:**
- Container orchestration (Kubernetes)
- PostgreSQL database
- Redis cache
- Qdrant vector database

---

*Stack analysis: 2026-04-13*