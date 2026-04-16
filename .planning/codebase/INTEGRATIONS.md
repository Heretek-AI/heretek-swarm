# External Integrations

**Analysis Date:** 2026-04-15

## APIs & External Services

### NATS Event Mesh (JetStream)

**Purpose:** Agent-to-agent (A2A) communication, event broadcasting, pub-sub messaging

**Implementation:**
- Library: `nats>=2.5.0` (Python client)
- Server: `nats:2.10-alpine` Docker image
- Ports: 4222 (client), 8222 (monitoring), 6222 (cluster)
- Features: JetStream persistence, durable consumers, message replay

**Key Files:**
- `src/heretek_swarm/gateway/nats_event_mesh.py` - Main NATS integration
- `src/heretek_swarm/gateway/jetstream_manager.py` - JetStream management
- `src/heretek_swarm/infrastructure/nats/client.py` - NATS client wrapper

**Environment Variables:**
- `NATS_URL=nats://nats:4222`

**Pattern:** Publish/subscribe + request-reply with timeout

---

### PostgreSQL / pgvector

**Purpose:** Relational data storage, state persistence, vector embeddings (via pgvector extension)

**Implementation:**
- Image: `pgvector/pgvector:pg16`
- Port: 5432
- Driver: `asyncpg>=0.29.0` (async), `psycopg2-binary>=2.9.0` (sync)

**Key Files:**
- `src/heretek_swarm/state/repository.py` - State persistence
- `src/heretek_swarm/config/db_models.py` - Database models
- `src/heretek_swarm/memory/persistent.py` - Memory persistence

**Environment Variables:**
- `DATABASE_URL=postgresql+asyncpg://heretek:${POSTGRES_PASSWORD}@postgres:5432/heretek_swarm`

**Tables/Collections:**
- Agent state storage
- Workflow execution history
- Configuration storage
- Memory tier (episodic)

---

### Redis

**Purpose:** Caching, pub/sub for consciousness metrics, working memory, rate limiting

**Implementation:**
- Image: `redis:7-alpine`
- Port: 6379
- Client: `redis>=5.0.0`

**Key Files:**
- `src/heretek_swarm/api/rate_limiting.py` - Rate limiting implementation
- `src/heretek_swarm/state/` - State caching

**Environment Variables:**
- `REDIS_URL=redis://redis:6379`

**Usage Patterns:**
- Consciousness metric broadcasting (GWT pub/sub)
- Agent working memory cache
- Rate limiting counters
- Session state caching

---

### Qdrant

**Purpose:** Semantic search, vector storage for RAG, memory semantic tier

**Implementation:**
- Image: `qdrant/qdrant:latest`
- Ports: 6333 (API), 6334 (gRPC)
- Client: `qdrant-client>=1.7.0`

**Key Files:**
- `src/heretek_swarm/rag/rag_pipeline.py` - RAG pipeline
- `src/heretek_swarm/embeddings/providers/` - Embedding providers
- `src/heretek_swarm/memory/` - Memory system

**Environment Variables:**
- `QDRANT_HOST=qdrant`
- `QDRANT_PORT=6333`
- `QDRANT_URL=http://qdrant:6333`

**Usage:**
- Semantic memory storage
- RAG document embeddings
- Agent knowledge retrieval

---

### LLM Providers

The system supports multiple LLM providers via a provider factory pattern.

**Provider Registry** (`src/heretek_swarm/llm/providers/factory.py`):
- `openai` - OpenAI models (GPT-4, etc.)
- `openai_compatible` - OpenAI-compatible APIs
- `minimax` - MiniMax abab models
- `ollama` - Local Ollama inference
- `llamacpp` - llama.cpp server
- `zai` - ZAI provider
- `lemonade` - Lemonade embeddings

**MiniMax Provider** (`src/heretek_swarm/llm/providers/minimax_provider.py`):
- Base URL: `https://api.minimax.chat/v1`
- Models: abab6.5, abab6.5s, abab5.5
- Features: Streaming, function calling, Chinese/English

**OpenAI Compatible** (`src/heretek_swarm/llm/providers/openai_compatible.py`):
- Any OpenAI API-compatible endpoint
- Configurable base URL and API key

**LiteLLM Integration** (`docker-compose.yml` service):
- Image: `ghcr.io/berriai/litellm:latest`
- Port: 4000
- Purpose: Unified LLM proxy for multiple providers
- Config: `litellm_config.yaml` mounted as `/app/config.yaml`

**Environment Variables:**
- `OPENAI_API_KEY` - OpenAI API key
- `OPENAI_BASE_URL` - OpenAI base URL (optional)
- `LLM_MODEL` - Default model
- `EMBEDDING_PROVIDER` - Embedding provider type
- `EMBEDDING_BASE_URL` - Embedding API URL
- `EMBEDDING_API_KEY` - Embedding API key
- `EMBEDER_MODEL` - Embedding model name
- `MINIMAX_API_KEY` - MiniMax API key

---

## Memory System (Mem0)

**Purpose:** Long-term memory for agents, episodic/semantic/procedural memory tiers

**Self-Hosted Deployment:**
- `mem0_server/` directory with FastAPI app
- PostgreSQL 15+ (separate from main DB)
- Qdrant for vector storage
- Optional Ollama for local LLM

**Configuration:**
- `MEM0_LLM_PROVIDER` - LLM for memory processing
- `MEM0_LLM_BASE_URL` - LLM endpoint
- `MEM0_LLM_MODEL` - LLM model
- `MEM0_POSTGRES_PASSWORD` - Memory DB password

**Key Files:**
- `mem0_server/main.py` - Mem0 server
- `mem0_server/requirements.txt` - Mem0 dependencies
- `mem0_server/Dockerfile` - Mem0 container

---

## Authentication & Security

**Internal API Authentication:**
- `HERETEK_API_KEY` - Internal API key for service-to-service auth

**External Auth (if configured):**
- `JWT_SECRET` - JWT signing secret for autonomous runtime
- `API_KEY` - External API key

---

## Monitoring & Observability

**Prometheus Metrics:**
- Library: `prometheus-client>=0.19.0`
- Exposed via FastAPI `/metrics` endpoint

**OpenTelemetry:**
- API: `opentelemetry-api>=1.22.0`
- SDK: `opentelemetry-sdk>=1.22.0`
- OTLP Exporter: `opentelemetry-exporter-otlp>=1.22.0`

**Structured Logging:**
- Library: `structlog>=24.1.0`
- Output: JSON structured logs

**Key Files:**
- `src/heretek_swarm/observability/` - Observability components
- `src/heretek_swarm/logging/` - Logging configuration

---

## CI/CD & Deployment

**Docker Deployment:**
- `Dockerfile` - Main API image
- `docker/Dockerfile.autonomous` - Autonomous runtime
- `mem0_server/Dockerfile` - Mem0 service
- `dashboard/frontend/Dockerfile` - Frontend

**Orchestration:**
- `docker-compose.yml` - Core services
- `docker-compose.autonomous.yml` - With autonomous runtime
- `k8s/` - Kubernetes manifests

**Environment Configuration:**
- `.env` file via `env_file` in docker-compose
- `.env.example` template provided

---

## Environment Configuration

### Required Environment Variables

**Core Services:**
```bash
DATABASE_URL=postgresql+asyncpg://heretek:${POSTGRES_PASSWORD}@postgres:5432/heretek_swarm
REDIS_URL=redis://redis:6379
QDRANT_HOST=qdrant
QDRANT_PORT=6333
NATS_URL=nats://nats:4222
```

**API Keys:**
```bash
OPENAI_API_KEY=sk-...          # OpenAI (if using OpenAI)
MINIMAX_API_KEY=...            # MiniMax (if using MiniMax)
HERETEK_API_KEY=...           # Internal auth
LITELLM_MASTER_KEY=sk-1234    # LiteLLM (if using)
```

**LLM Configuration:**
```bash
LLM_MODEL=gpt-4o
EMBEDDING_PROVIDER=openai_compatible
EMBEDDING_BASE_URL=https://api.openai.com/v1
EMBEDDING_API_KEY=sk-...
EMBEDDER_MODEL=text-embedding-3-small
```

### Optional Variables

```bash
ENVIRONMENT=production
POSTGRES_PASSWORD=...
MEM0_POSTGRES_PASSWORD=...
JWT_SECRET=...
```

---

## Webhooks & Callbacks

**A2A Protocol Server:**
- Port: 18789
- Purpose: Agent-to-agent direct communication

**MCP Server:**
- Port: 18790
- Purpose: Model Context Protocol for external tool integration

---

## Service Connectivity Map

```
┌─────────────────────────────────────────────────────────┐
│                    External Clients                       │
└─────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────┐
│              Frontend (:3000 → :80)                      │
│  React + Zustand + React Flow + Tailwind CSS           │
└─────────────────────────────────────────────────────────┘
                            │
                            │ HTTP/WebSocket
                            ▼
┌─────────────────────────────────────────────────────────┐
│              FastAPI Backend (:8000)                     │
│  • REST API                                             │
│  • WebSocket endpoints                                   │
│  • Prometheus metrics                                    │
└─────────────────────────────────────────────────────────┘
         │            │           │           │
         ▼            ▼           ▼           ▼
┌───────────┐  ┌───────────┐  ┌──────────┐  ┌─────────┐
│   NATS    │  │ PostgreSQL│  │  Redis   │  │ Qdrant  │
│ :4222     │  │  :5432    │  │  :6379   │  │ :6333   │
│ (JetStream│  │ (pgvector)│  │ (cache)  │  │(vectors)│
└───────────┘  └───────────┘  └──────────┘  └─────────┘
         │            │           │
         ▼            ▼           ▼
┌──────────────────────────────────────────────┐
│        Mem0 Memory Service (:8888)           │
│  (Optional - self-hosted memory)             │
└──────────────────────────────────────────────┘
         │
         ▼
┌───────────────┐  ┌──────────────┐
│     Ollama    │  │ LiteLLM      │
│   (:11434)    │  │  (:4000)     │
│ (Optional)    │  │ (Optional)   │
└───────────────┘  └──────────────┘
```

---

*Integration audit: 2026-04-15*
