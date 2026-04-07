# Heretek Swarm API Endpoints

**Version:** 2.0.0  
**Date:** 2026-04-07  
**Status:** Production-Ready

---

## Table of Contents

1. [Main API](#main-api)
2. [Health Endpoints](#health-endpoints)
3. [Agent Management Endpoints](#agent-management-endpoints)
4. [Workflow Endpoints](#workflow-endpoints)
5. [Consciousness Endpoints](#consciousness-endpoints)
6. [Observability Endpoints](#observability-endpoints)
7. [Plugin Endpoints](#plugin-endpoints)
8. [Evaluation Endpoints](#evaluation-endpoints)
9. [RAG Endpoints](#rag-endpoints)
10. [Configuration Endpoints](#configuration-endpoints)
11. [Integration Endpoints](#integration-endpoints)
12. [Rate Limiting](#rate-limiting)

---

## Main API

**File:** [`src/heretek_swarm/api/main.py`](src/heretek_swarm/api/main.py)

FastAPI application with all endpoint routers.

```python
app = FastAPI(
    title="Heretek Swarm API",
    description="Multi-agent swarm orchestration with A2A protocol communication",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)
```

### Registered Routers

| Router | Prefix | File |
|--------|--------|------|
| websockets | - | [`websockets.py`](src/heretek_swarm/api/websockets.py) |
| consensus | /api/consensus | [`consensus.py`](src/heretek_swarm/api/consensus.py) |
| plugins | /api/plugins | [`plugins.py`](src/heretek_swarm/api/plugins.py) |
| workflows | /api/workflows | [`workflows.py`](src/heretek_swarm/api/workflows.py) |
| observability | /api/observability | [`observability.py`](src/heretek_swarm/api/observability.py) |
| evaluation | /api/evaluation | [`evaluation.py`](src/heretek_swarm/api/evaluation.py) |
| rag | /api/rag | [`rag.py`](src/heretek_swarm/api/rag.py) |
| consciousness | /api/consciousness | [`consciousness.py`](src/heretek_swarm/api/consciousness.py) |
| emergent_intelligence | /api/v1/emergent-intelligence | [`emergent_intelligence.py`](src/heretek_swarm/api/emergent_intelligence.py) |
| agents_management | /api/agents | [`agents_management.py`](src/heretek_swarm/api/agents_management.py) |
| configuration | /api/config | [`configuration.py`](src/heretek_swarm/api/configuration.py) |

---

## Health Endpoints

### API Health Check

```http
GET /api/health
```

**Response:**
```json
{
  "status": "healthy",
  "services": {
    "gateway": {"status": "healthy", "active_connections": 0},
    "redis": {"status": "healthy", "version": "7.0.0"},
    "postgres": {"status": "healthy", "database": "heretek_swarm"},
    "qdrant": {"status": "healthy", "collections": []}
  }
}
```

### Kubernetes Liveness Probe

```http
GET /api/health/live
```

**Response:**
```json
{"status": "alive"}
```

### Kubernetes Readiness Probe

```http
GET /api/health/ready
```

**Response:**
```json
{"status": "ready"}
```

---

## Agent Management Endpoints

**File:** [`src/heretek_swarm/api/main.py`](src/heretek_swarm/api/main.py:327)

### List All Agents

```http
GET /api/agents
Authorization: Bearer {api_key}
```

**Response:**
```json
{
  "agents": [
    {
      "id": "steward-001",
      "type": "StewardAgent",
      "status": "running",
      "message_count": 1523,
      "error_count": 0,
      "last_activity": "2026-04-07T15:00:00Z"
    }
  ],
  "total": 23
}
```

### Get Agent Details

```http
GET /api/agents/{agent_id}
Authorization: Bearer {api_key}
```

**Response:**
```json
{
  "id": "steward-001",
  "type": "StewardAgent",
  "status": "running",
  "message_count": 1523,
  "error_count": 0,
  "last_activity": "2026-04-07T15:00:00Z",
  "topics": ["deliberation", "orchestration"],
  "capabilities": ["process_message", "send_message", "broadcast"]
}
```

### Get Agent Metrics

```http
GET /api/agents/{agent_id}/metrics
Authorization: Bearer {api_key}
```

**Response:**
```json
{
  "agent_id": "steward-001",
  "messages_processed": 1523,
  "errors": 0,
  "uptime_seconds": 3600
}
```

### Terminate Agent

```http
POST /api/agents/{agent_id}/terminate
Authorization: Bearer {api_key}
```

**Response:**
```json
{
  "status": "terminated",
  "agent_id": "steward-001"
}
```

### Supervisor Status

```http
GET /api/supervisor/status
Authorization: Bearer {api_key}
```

**Response:**
```json
{
  "total_actors": 23,
  "active_actors": 23,
  "suspended_actors": 0,
  "terminating_actors": 0
}
```

---

## Workflow Endpoints

**File:** [`src/heretek_swarm/api/workflows.py`](src/heretek_swarm/api/workflows.py)

### Execute Workflow

```http
POST /api/workflows/execute
Authorization: Bearer {api_key}
Content-Type: application/json
```

**Request:**
```json
{
  "workflow_id": "deliberation-001",
  "agents": ["steward-001", "alpha-001", "beta-001", "charlie-001"],
  "input": {
    "topic": "System architecture decision",
    "context": {}
  },
  "timeout": 300
}
```

**Response:**
```json
{
  "workflow_id": "deliberation-001",
  "status": "running",
  "started_at": "2026-04-07T15:00:00Z",
  "estimated_completion": "2026-04-07T15:05:00Z"
}
```

### Get Workflow Status

```http
GET /api/workflows/status/{workflow_id}
Authorization: Bearer {api_key}
```

**Response:**
```json
{
  "workflow_id": "deliberation-001",
  "status": "completed",
  "result": {
    "decision": "approved",
    "confidence": 0.95,
    "reasoning": "..."
  },
  "completed_at": "2026-04-07T15:04:32Z"
}
```

### List Workflows

```http
GET /api/workflows/list?state=running&limit=100
Authorization: Bearer {api_key}
```

---

## Consciousness Endpoints

**File:** [`src/heretek_swarm/api/consciousness.py`](src/heretek_swarm/api/consciousness.py)

### Get Global Metrics

```http
GET /api/consciousness/metrics
Authorization: Bearer {api_key}
```

**Response:**
```json
{
  "average_gwt_score": 0.75,
  "average_phi": 0.68,
  "average_ast_competence": 0.82,
  "average_free_energy": 0.15,
  "consciousness_state": "conscious",
  "agent_count": 23,
  "timestamp": "2026-04-07T15:00:00Z"
}
```

### Get Agent Metrics

```http
GET /api/consciousness/agent/{agent_id}/metrics
Authorization: Bearer {api_key}
```

**Response:**
```json
{
  "agent_id": "steward-001",
  "gwt_score": 0.85,
  "phi_value": 0.72,
  "ast_competence": 0.90,
  "free_energy": 0.12,
  "consciousness_state": "highly_conscious",
  "attention_focus": "deliberation_orchestration",
  "timestamp": "2026-04-07T15:00:00Z"
}
```

### Submit to Workspace

```http
POST /api/consciousness/workspace/submit
Authorization: Bearer {api_key}
Content-Type: application/json
```

**Request:**
```json
{
  "source": "steward-001",
  "content": {"decision": "approved", "reasoning": "..."},
  "priority": 0.8
}
```

**Response:**
```json
{
  "workspace_id": "ws-123456",
  "submitted_at": "2026-04-07T15:00:00Z"
}
```

### Get Workspace Contents

```http
GET /api/consciousness/workspace?limit=10&attended_only=false
Authorization: Bearer {api_key}
```

---

## Observability Endpoints

**File:** [`src/heretek_swarm/api/observability.py`](src/heretek_swarm/api/observability.py)

### Get Traces

```http
GET /api/observability/traces?agent_id=steward-001&limit=100
Authorization: Bearer {api_key}
```

**Response:**
```json
[
  {
    "trace_id": "trace-123",
    "agent_id": "steward-001",
    "operation": "deliberation",
    "duration_ms": 1523,
    "status": "success",
    "timestamp": "2026-04-07T15:00:00Z"
  }
]
```

### Get Latency Metrics

```http
GET /api/observability/metrics/latency
Authorization: Bearer {api_key}
```

**Response:**
```json
{
  "p50_ms": 45,
  "p95_ms": 120,
  "p99_ms": 250,
  "avg_ms": 67,
  "request_count": 10000
}
```

### Get Agent Status

```http
GET /api/observability/agents/status
Authorization: Bearer {api_key}
```

---

## Plugin Endpoints

**File:** [`src/heretek_swarm/api/plugins.py`](src/heretek_swarm/api/plugins.py)

### List Plugins

```http
GET /api/plugins/list
Authorization: Bearer {api_key}
```

**Response:**
```json
[
  {
    "name": "consciousness",
    "version": "1.0.0",
    "enabled": true,
    "description": "GWT/AST consciousness framework"
  },
  {
    "name": "consciousness_enhanced",
    "version": "1.0.0",
    "enabled": true,
    "description": "IIT/FEP enhanced consciousness"
  }
]
```

### Enable Plugin

```http
POST /api/plugins/{plugin_name}/enable
Authorization: Bearer {api_key}
```

### Disable Plugin

```http
POST /api/plugins/{plugin_name}/disable
Authorization: Bearer {api_key}
```

### Get Plugin Status

```http
GET /api/plugins/{plugin_name}/status
Authorization: Bearer {api_key}
```

---

## Evaluation Endpoints

**File:** [`src/heretek_swarm/api/evaluation.py`](src/heretek_swarm/api/evaluation.py)

### Run Evaluation

```http
POST /api/evaluation/run
Authorization: Bearer {api_key}
Content-Type: application/json
```

**Request:**
```json
{
  "target": "agent",
  "target_id": "steward-001",
  "eval_type": "performance",
  "metrics": ["latency", "accuracy", "throughput"]
}
```

**Response:**
```json
{
  "eval_id": "eval-123",
  "status": "completed",
  "results": {
    "latency_p95_ms": 120,
    "accuracy": 0.95,
    "throughput_rps": 50
  }
}
```

### Get Evaluation Results

```http
GET /api/evaluation/results/{eval_id}
Authorization: Bearer {api_key}
```

### List Evaluations

```http
GET /api/evaluation/list?target_type=agent&limit=100
Authorization: Bearer {api_key}
```

---

## RAG Endpoints

**File:** [`src/heretek_swarm/api/rag.py`](src/heretek_swarm/api/rag.py)

### Ingest Document

```http
POST /api/rag/ingest
Authorization: Bearer {api_key}
Content-Type: application/json
```

**Request:**
```json
{
  "document": "Document content...",
  "metadata": {"source": "manual", "category": "knowledge"},
  "chunk_size": 500,
  "chunk_overlap": 50
}
```

**Response:**
```json
{
  "document_id": "doc-123",
  "chunks_created": 15,
  "ingested_at": "2026-04-07T15:00:00Z"
}
```

### Query Documents

```http
POST /api/rag/query
Authorization: Bearer {api_key}
Content-Type: application/json
```

**Request:**
```json
{
  "query": "What is the deliberation process?",
  "top_k": 5,
  "filters": {"category": "knowledge"}
}
```

**Response:**
```json
{
  "query": "What is the deliberation process?",
  "results": [
    {
      "chunk_id": "chunk-123",
      "content": "The deliberation process involves...",
      "score": 0.92,
      "metadata": {}
    }
  ]
}
```

### Delete Document

```http
DELETE /api/rag/documents/{document_id}
Authorization: Bearer {api_key}
```

---

## Configuration Endpoints

**File:** [`src/heretek_swarm/api/configuration.py`](src/heretek_swarm/api/configuration.py)

### List Configurations

```http
GET /api/config
Authorization: Bearer {api_key}
```

### Get Configuration

```http
GET /api/config/{key}
Authorization: Bearer {api_key}
```

### Update Configuration

```http
PUT /api/config/{key}
Authorization: Bearer {api_key}
Content-Type: application/json
```

### Create Configuration

```http
POST /api/config
Authorization: Bearer {api_key}
Content-Type: application/json
```

### Delete Configuration

```http
DELETE /api/config/{key}
Authorization: Bearer {api_key}
```

### LLM Providers

```http
GET /api/config/llm/providers
POST /api/config/llm/providers
PUT /api/config/llm/providers/{id}
DELETE /api/config/llm/providers/{id}
POST /api/config/llm/providers/{id}/test
GET /api/config/llm/types
```

### Embedding Providers

```http
GET /api/config/embedding/providers
POST /api/config/embedding/providers
PUT /api/config/embedding/providers/{id}
DELETE /api/config/embedding/providers/{id}
POST /api/config/embedding/providers/{id}/test
GET /api/config/embedding/types
```

### Import/Export

```http
GET /api/config/export
POST /api/config/import
POST /api/config/migrate-from-env
```

---

## Integration Endpoints

**File:** [`src/heretek_swarm/integrations/manager.py`](src/heretek_swarm/integrations/manager.py)

### List Integrations

```http
GET /api/v1/integrations
Authorization: Bearer {api_key}
```

**Response:**
```json
{
  "integrations": [
    {
      "integration_id": "langgraph-001",
      "type": "langgraph",
      "status": "running",
      "health": "healthy"
    }
  ],
  "total": 1
}
```

### Get Integration Details

```http
GET /api/v1/integrations/{integration_id}
Authorization: Bearer {api_key}
```

### Start Integration

```http
POST /api/v1/integrations/{integration_id}/start
Authorization: Bearer {api_key}
```

### Stop Integration

```http
POST /api/v1/integrations/{integration_id}/stop
Authorization: Bearer {api_key}
```

### Health Check

```http
GET /api/v1/integrations/{integration_id}/health
Authorization: Bearer {api_key}
```

### Get Statistics

```http
GET /api/v1/integrations/{integration_id}/statistics
Authorization: Bearer {api_key}
```

### LangGraph Endpoints

```http
GET /api/v1/integrations/langgraph/graphs
```

### AutoGen Endpoints

```http
GET /api/v1/integrations/autogen/agents
```

### CrewAI Endpoints

```http
GET /api/v1/integrations/crewai/crews
```

### OpenAI Assistants Endpoints

```http
GET /api/v1/integrations/openai/assistants
```

### Anthropic Endpoints

```http
GET /api/v1/integrations/anthropic/conversations
```

---

## Memory Endpoints

**File:** [`src/heretek_swarm/api/main.py`](src/heretek_swarm/api/main.py:459)

### Get Memory Stats

```http
GET /api/memory
Authorization: Bearer {api_key}
```

**Response:**
```json
{
  "total_memories": 1523,
  "by_agent": {"steward-001": 500, "alpha-001": 300},
  "by_type": {"episodic": 1000, "semantic": 523},
  "status": "available"
}
```

### Get mem0 Stats

```http
GET /api/memory/mem0
Authorization: Bearer {api_key}
```

### Search mem0

```http
POST /api/memory/mem0/search?query={query}&agent_id={agent_id}&limit=10
Authorization: Bearer {api_key}
```

### Get Agent Memories

```http
GET /api/memory/mem0/agents/{agent_id}?limit=100
Authorization: Bearer {api_key}
```

---

## A2A Message Endpoints

**File:** [`src/heretek_swarm/api/main.py`](src/heretek_swarm/api/main.py:670)

### Get Recent Messages

```http
GET /api/a2a/messages?limit=100
Authorization: Bearer {api_key}
```

### Get Conversation

```http
GET /api/a2a/messages/{from_agent}/{to_agent}?limit=50
```

---

## Rate Limiting

**File:** [`src/heretek_swarm/api/rate_limiting.py`](src/heretek_swarm/api/rate_limiting.py)

### Rate Limit Tiers

| Tier | Requests/Minute | Requests/Hour | Use Case |
|------|-----------------|---------------|----------|
| Free | 60 | 1000 | Development |
| Basic | 300 | 10000 | Standard usage |
| Pro | 1000 | 50000 | Production |
| Enterprise | 5000 | 200000 | High volume |

### Rate Limit Headers

```http
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 999
X-RateLimit-Reset: 1649260800
```

### Rate Limit Response

```json
{
  "error": "rate_limit_exceeded",
  "message": "Too many requests. Please retry after 60 seconds.",
  "retry_after": 60
}
```

---

## Error Responses

### Standard Error Format

```json
{
  "error": {
    "code": "AGENT_NOT_FOUND",
    "message": "Agent 'steward-001' not found",
    "details": {}
  }
}
```

### HTTP Status Codes

| Code | Meaning |
|------|---------|
| 200 | Success |
| 201 | Created |
| 400 | Bad Request |
| 401 | Unauthorized |
| 403 | Forbidden |
| 404 | Not Found |
| 408 | Request Timeout |
| 429 | Too Many Requests |
| 500 | Internal Server Error |
| 503 | Service Unavailable |

---

## Authentication

All endpoints except health checks require Bearer token authentication:

```http
Authorization: Bearer {api_key}
```

API keys are managed through the ConfigurationService and can be created via the UI or API.

---

**License:** Apache 2.0  
**GitHub:** [Heretek-AI/heretek-swarm](https://github.com/Heretek-AI/heretek-swarm)
