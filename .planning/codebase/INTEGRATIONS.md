# External Integrations

**Analysis Date:** 2026-04-13

## APIs & External Services

**LLM Providers (via LiteLLM):**
- **MiniMax** - Primary LLM provider
  - Config: `MINIMAX_API_KEY`, `MINIMAX_BASE_URL`
  - Endpoint: `minimax/*`
- **OpenAI** - GPT models
  - Config: `OPENAI_API_KEY`
  - Endpoint: `openai/*`
- **Ollama** - Local LLM
  - Config: `OLLAMA_API_KEY`, `OLLAMA_BASE_URL`
  - Endpoint: `ollama/*`
  - Default: `http://localhost:11434`
- **Z.AI (Claude compatible)** - Anthropic-style API
  - Config: `ZAI_API_KEY`, `ZAI_BASE_URL`
  - Endpoint: `zai/*`
- **Local LM Studio** - Local llama.cpp
  - Config: `LOCAL_API_KEY`, `LOCAL_BASE_URL`
  - Endpoint: `local/*`
  - Default: `http://localhost:1234/v1`

## Data Storage

**PostgreSQL:**
- Connection: `DATABASE_URL` env var
- Client: `asyncpg`, `psycopg2-binary`
- Used for: Persistent agent state, swarm memories

**Redis:**
- Connection: `REDIS_URL` env var (k8s configMap: `redis-config.host`)
- Used for: Caching, session management

**Qdrant (Vector Database):**
- Connection: `QDRANT_URL` env var (k8s configMap: `qdrant-config.host`)
- Auth: `QDRANT_API_KEY` optional
- Collections:
  - `heretek_memory` - Agent memory embeddings
  - `heretek_memory_access` - Memory access patterns
- Setup: `migrations/scripts/setup_qdrant_collections.py`

## Authentication & Identity

**JWT Authentication:**
- Secret: `JWT_SECRET` (k8s secret: `auth-secret.jwt-secret`)
- Used in: API gateway, agent authentication

**API Key Authentication:**
- Header: `API_KEY` (k8s secret: `auth-secret.api-key`)
- Used in: External API access

## Monitoring & Observability

**Prometheus:**
- Client: `prometheus-client`
- Config: `litellm_config.yaml` success_callback/failure_callback
- Endpoint: `/metrics` exposed by API

**OpenTelemetry:**
- Tracing: `opentelemetry-api`, `opentelemetry-sdk`
- Export: `opentelemetry-exporter-otlp`
- Config: `otel-collector-config.yaml`

**Logging:**
- Framework: `structlog`
- JSON output configured for serverless Lambda

**Grafana:**
- Deployment: `k8s/grafana-deployment.yaml`
- Dashboards: Observability metrics

**Alerting:**
- Custom alerting in `src/heretek_swarm/observability/alerting.py`
- Supports webhook notifications (Slack, PagerDuty, Discord)

## CI/CD & Deployment

**Container Registry:**
- Image: `ghcr.io/heretek-ai/heretek-swarm-api:1.0.0`
- Deployment: Kubernetes with 3 replicas

**Kubernetes:**
- Namespace: `heretek-swarm`
- Components:
  - API deployment (heretek-swarm-api)
  - Autonomous agent deployment (heretek-swarm-autonomous)
  - Postgres deployment
  - Redis deployment
  - Qdrant deployment
  - Prometheus deployment
  - Grafana deployment

**Serverless:**
- Lambda handler: `serverless/handler.py`
- Uses structlog for JSON logging

## Environment Configuration

**Required env vars:**
- `DATABASE_URL` - PostgreSQL connection
- `REDIS_URL` - Redis connection
- `QDRANT_URL` - Qdrant connection
- `HERETEK_ENV` - Environment (production/development)
- `LOG_LEVEL` - Logging level

**Optional env vars:**
- `OPENAI_API_KEY` - OpenAI API key
- `ANTHROPIC_API_KEY` - Anthropic API key
- `QDRANT_API_KEY` - Qdrant API key

**Secrets (k8s secrets):**
- `postgres-credentials.database-url`
- `api-keys.openai-api-key`
- `api-keys.anthropic-api-key`
- `api-keys.qdrant-api-key`
- `auth-secret.jwt-secret`
- `auth-secret.api-key`

## Webhooks & Callbacks

**Outgoing:**
- Alerting webhooks (configurable per alert channel)
- Prometheus metrics callbacks

**Incoming:**
- `/api/health/live` - Liveness probe
- `/api/health/ready` - Readiness probe

## Event Mesh

**NATS:**
- URL: `nats://localhost:4222` (CLI default)
- Used for: Agent-to-agent communication, event mesh
- Implementation: `src/heretek_swarm/gateway/nats_event_mesh.py`

**Integration Libraries:**
- `nats-py` - Python NATS client
- `autogen` - Microsoft AutoGen integration (`src/heretek_swarm/integrations/autogen.py`)
- `crewai` - CrewAI integration (`src/heretek_swarm/integrations/crewai.py`)

## Agent Integrations

**Telegram Bot:**
- `src/heretek_swarm/integrations/telegram_bot.py`

---

*Integration audit: 2026-04-13*