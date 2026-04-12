# External Integrations

**Analysis Date:** 2026-04-12

## APIs & External Services

**LLM Providers:**
- **OpenAI** - GPT models via official openai package
  - SDK: `openai` package
  - Auth: `OPENAI_API_KEY` environment variable
- **Anthropic** - Claude models via anthropic package
  - SDK: `anthropic` package
  - Auth: `ANTHROPIC_API_KEY` environment variable
- **MiniMax** - MiniMax M2 model
  - Provider: `minimax_provider.py`
  - Auth: `MINIMAX_API_KEY` environment variable
  - Base URL: `https://api.minimax.io/v1`
- **Ollama** - Local LLM inference
  - Provider: `ollama_provider.py`
  - Base URL: Configurable (default `http://localhost:11434`)
- **Llama.cpp** - Local GGUF model inference
  - Provider: `llamacpp_provider.py`
  - Base URL: Configurable endpoint
- **Lemonade** - OpenAI-compatible embedding server
  - Provider: `lemonade_provider.py`
  - Auth: `EMBEDDING_API_KEY` environment variable
  - Base URL: `http://192.168.31.18:13305/api/v1`
- **ZAI** - ZAI provider
  - Provider: `zai_provider.py`
- **OpenAI Compatible** - Generic OpenAI-compatible endpoints
  - Provider: `openai_compatible.py`

**Agent Frameworks:**
- **AutoGen** - Multi-agent conversation framework
  - Integration: `src/heretek_swarm/integrations/autogen.py`
- **CrewAI** - AI agent crew framework
  - Integration: `src/heretek_swarm/integrations/crewai.py`
- **LangGraph** - LLM workflow/graph framework
  - Integration: `src/heretek_swarm/integrations/langgraph.py`
- **OpenAI Assistants** - OpenAI Assistant API integration
  - Integration: `src/heretek_swarm/integrations/openai_assistants.py`
- **PraisonAI** - Handoffs pattern
  - Integration: `src/heretek_swarm/integrations/praison_handoffs.py`

**Messaging Platforms:**
- **Slack** - Bot integration for agent interaction
  - SDK: `slack_sdk`
  - Auth: `SLACK_BOT_TOKEN` environment variable
  - File: `src/heretek_swarm/integrations/slack_bot.py`
- **Telegram** - Bot integration
  - Auth: `TELEGRAM_BOT_TOKEN` environment variable
  - File: `src/heretek_swarm/integrations/telegram_bot.py`
- **Discord** - Bot integration
  - Auth: `DISCORD_BOT_TOKEN` environment variable
  - File: `src/heretek_swarm/integrations/discord_bot.py`

## Data Storage

**Relational Database:**
- **PostgreSQL** - Primary persistent storage
  - Connection: `DATABASE_URL` environment variable
  - Driver: `postgresql+asyncpg://`
  - Used by: Configuration storage, agent state, audit logs

**Vector Database:**
- **Qdrant** - Vector storage for RAG and embeddings
  - Connection: `QDRANT_URL`, `QDRANT_API_KEY` environment variables
  - Default host: `localhost:6333`
  - Client: `qdrant-client>=1.7.0`
  - Used by: RAG pipeline, embedding retrieval

**Cache & Pub/Sub:**
- **Redis** - Caching, pub/sub, session management
  - Connection: `REDIS_URL` environment variable
  - Default: `redis://localhost:6379`
  - Client: `redis>=5.0.0` (async)
  - Used by: Pattern library, distributed learning, scaling, WebSocket state

**File Storage:**
- Local filesystem for agent workspace
- Directory: `src/heretek_swarm/agent_workspace/`

## Authentication & Identity

**Auth Provider:**
- Custom JWT/API key authentication
  - Implementation: `src/heretek_swarm/gateway/auth.py`
  - Header: `Authorization: Bearer <token>`
  - Config: `HERETEK_API_KEY` environment variable

**Rate Limiting:**
- Custom rate limiting middleware
  - Implementation: `src/heretek_swarm/api/rate_limiting.py`
  - Config: `RATE_LIMIT_ENABLED` environment variable

## Monitoring & Observability

**Tracing:**
- **OpenTelemetry** - Distributed tracing
  - SDK: `opentelemetry-sdk>=1.22.0`
  - Export: OTLP protocol via `opentelemetry-exporter-otlp`
  - Auto-instrumentation: FastAPI, httpx
  - File: `src/heretek_swarm/observability/tracing.py`

**Metrics:**
- **Prometheus** - Metrics collection
  - Client: `prometheus_client`
  - Endpoint: `/metrics`
  - File: `src/heretek_swarm/observability/prometheus_metrics.py`

**Logging:**
- **structlog** - Structured JSON logging
  - Output: JSON format for Loki/Promtail
  - Config: `LOG_LEVEL`, `LOG_FORMAT` environment variables
  - File: `src/heretek_swarm/logging/config.py`

## Message Broker & Event Mesh

**NATS:**
- **NATS JetStream** - Event mesh and message broker
  - Server: NATS server 3.0+
  - Connection: `nats_url` parameter (default `nats://localhost:4222`)
  - Used by: `src/heretek_swarm/gateway/jetstream_manager.py`
  - Used by: `src/heretek_swarm/gateway/nats_event_mesh.py`
  - Features: Durable streams, consumer groups, message replay

## Infrastructure

**Message Queue:**
- NATS JetStream (primary)
- Redis Pub/Sub (fallback/local)

**Proxy/Load Balancing:**
- Vite dev server proxy for API requests
- Configured in `dashboard/frontend/vite.config.ts`

## Environment Configuration

**Required env vars:**
| Variable | Purpose | Example |
|----------|---------|---------|
| `HERETEK_API_KEY` | API authentication | `htsk_...` |
| `DATABASE_URL` | PostgreSQL connection | `postgresql+asyncpg://...` |
| `REDIS_URL` | Redis connection | `redis://localhost:6379` |
| `QDRANT_URL` | Qdrant server | `http://localhost:6333` |
| `QDRANT_API_KEY` | Qdrant auth | `...` |
| `MINIMAX_API_KEY` | MiniMax LLM | `sk-...` |
| `MINIMAX_BASE_URL` | MiniMax endpoint | `https://api.minimax.io/v1` |
| `EMBEDDING_BASE_URL` | Embedding server | `http://192.168.31.18:13305` |
| `EMBEDDING_API_KEY` | Embedding auth | `lemonade` |
| `LOG_LEVEL` | Logging level | `INFO` |
| `ENVIRONMENT` | deployment environment | `development` |

**Optional env vars:**
| Variable | Purpose |
|----------|---------|
| `SLACK_BOT_TOKEN` | Slack integration |
| `TELEGRAM_BOT_TOKEN` | Telegram integration |
| `DISCORD_BOT_TOKEN` | Discord integration |
| `CORS_ORIGINS` | Allowed CORS origins |
| `NATS_URL` | NATS server URL |

**Secrets location:**
- Environment variables (`.env` file, not committed)
- Environment variable hints stored in `api_key_hint` fields
- `heretek_swarm/config/models.py` defines sensitive field handling

---

*Integration audit: 2026-04-12*
