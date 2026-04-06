# API Endpoints

**Version:** 1.11.0  
**Session:** 21 (2026-04-06)

FastAPI REST API reference for the Heretek Swarm system.

---

## Table of Contents

1. [Main API](#main-api)
2. [Workflow Endpoints](#workflow-endpoints)
3. [Consciousness Endpoints](#consciousness-endpoints)
4. [Observability Endpoints](#observability-endpoints)
5. [Plugin Endpoints](#plugin-endpoints)
6. [Evaluation Endpoints](#evaluation-endpoints)
7. [RAG Endpoints](#rag-endpoints)
8. [Rate Limiting](#rate-limiting)

---

## Main API

**File:** [`src/heretek_swarm/api/main.py`](../src/heretek_swarm/api/main.py)

FastAPI application with all endpoint routers.

```python
app = FastAPI(title="Heretek Swarm API", version="1.11.0")

# Include routers
app.include_router(workflows.router, prefix="/api/workflows")
app.include_router(consciousness.router, prefix="/api/consciousness")
app.include_router(observability.router, prefix="/api/observability")
app.include_router(plugins.router, prefix="/api/plugins")
app.include_router(evaluation.router, prefix="/api/evaluation")
app.include_router(rag.router, prefix="/api/rag")
```

### Health Endpoints

```python
@app.get("/health")
async def health_check() -> Dict[str, Any]:
    """API health check."""
    
@app.get("/ready")
async def readiness_check() -> Dict[str, Any]:
    """Readiness probe for Kubernetes."""
    
@app.get("/live")
async def liveness_check() -> Dict[str, Any]:
    """Liveness probe for Kubernetes."""
```

### Response Format

```json
{
  "status": "healthy",
  "version": "1.11.0",
  "agents": 23,
  "health_score": 100,
  "timestamp": "2026-04-06T10:00:00Z"
}
```

---

## Workflow Endpoints

**File:** [`src/heretek_swarm/api/workflows.py`](../src/heretek_swarm/api/workflows.py)

Workflow execution and management.

### Execute Workflow

```python
@router.post("/execute")
async def execute_workflow(request: WorkflowRequest) -> WorkflowResponse:
    """Execute workflow with specified agents."""
```

**Request:**
```json
{
  "workflow_id": "deliberation-001",
  "agents": ["steward-001", "alpha-001", "beta-001", "charlie-001"],
  "input": {
    "topic": "System architecture decision",
    "context": {...}
  },
  "timeout": 300
}
```

**Response:**
```json
{
  "workflow_id": "deliberation-001",
  "status": "running",
  "started_at": "2026-04-06T10:00:00Z",
  "estimated_completion": "2026-04-06T10:05:00Z"
}
```

### Get Workflow Status

```python
@router.get("/status/{workflow_id}")
async def get_workflow_status(workflow_id: str) -> WorkflowStatus:
    """Get workflow execution status."""
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
  "completed_at": "2026-04-06T10:04:32Z"
}
```

### List Workflows

```python
@router.get("/list")
async def list_workflows(
    state: Optional[str] = None,
    limit: int = 100
) -> List[WorkflowInfo]:
    """List workflows with optional state filter."""
```

---

## Consciousness Endpoints

**File:** [`src/heretek_swarm/api/consciousness.py`](../src/heretek_swarm/api/consciousness.py)

Consciousness metrics and global workspace operations.

### Get Global Metrics

```python
@router.get("/metrics")
async def get_consciousness_metrics() -> ConsciousnessMetricsResponse:
    """Get global consciousness metrics."""
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
  "timestamp": "2026-04-06T10:00:00Z"
}
```

### Get Agent Metrics

```python
@router.get("/agent/{agent_id}/metrics")
async def get_agent_metrics(agent_id: str) -> AgentMetricsResponse:
    """Get metrics for specific agent."""
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
  "timestamp": "2026-04-06T10:00:00Z"
}
```

### Submit to Workspace

```python
@router.post("/workspace/submit")
async def submit_to_workspace(request: WorkspaceSubmitRequest) -> str:
    """Submit content to global workspace."""
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
  "submitted_at": "2026-04-06T10:00:00Z"
}
```

### Get Workspace Contents

```python
@router.get("/workspace")
async def get_workspace_contents(
    limit: int = 10,
    attended_only: bool = False
) -> List[GlobalWorkspaceItem]:
    """Get current workspace contents."""
```

---

## Observability Endpoints

**File:** [`src/heretek_swarm/api/observability.py`](../src/heretek_swarm/api/observability.py)

Tracing, metrics, and monitoring.

### Get Traces

```python
@router.get("/traces")
async def get_traces(
    agent_id: Optional[str] = None,
    limit: int = 100
) -> List[Trace]:
    """Get execution traces."""
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
    "timestamp": "2026-04-06T10:00:00Z"
  }
]
```

### Get Latency Metrics

```python
@router.get("/metrics/latency")
async def get_latency_metrics() -> LatencyMetrics:
    """Get latency statistics."""
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

```python
@router.get("/agents/status")
async def get_all_agents_status() -> Dict[str, AgentStatus]:
    """Get status of all agents."""
```

**Response:**
```json
{
  "steward-001": {
    "state": "running",
    "health_score": 100,
    "message_count": 1523,
    "last_activity": "2026-04-06T10:00:00Z"
  },
  "alpha-001": {...}
}
```

### Get Single Agent Status

```python
@router.get("/agents/{agent_id}/status")
async def get_agent_status(agent_id: str) -> AgentStatus:
    """Get status of specific agent."""
```

---

## Plugin Endpoints

**File:** [`src/heretek_swarm/api/plugins.py`](../src/heretek_swarm/api/plugins.py)

Plugin management and operations.

### List Plugins

```python
@router.get("/list")
async def list_plugins() -> List[PluginInfo]:
    """List all loaded plugins."""
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

```python
@router.post("/{plugin_name}/enable")
async def enable_plugin(plugin_name: str) -> Dict[str, Any]:
    """Enable a plugin."""
```

### Disable Plugin

```python
@router.post("/{plugin_name}/disable")
async def disable_plugin(plugin_name: str) -> Dict[str, Any]:
    """Disable a plugin."""
```

### Get Plugin Status

```python
@router.get("/{plugin_name}/status")
async def get_plugin_status(plugin_name: str) -> PluginStatus:
    """Get plugin status and metrics."""
```

---

## Evaluation Endpoints

**File:** [`src/heretek_swarm/api/evaluation.py`](../src/heretek_swarm/api/evaluation.py)

Agent and workflow evaluation.

### Run Evaluation

```python
@router.post("/run")
async def run_evaluation(request: EvalRequest) -> EvalResponse:
    """Run evaluation on agent or workflow."""
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

```python
@router.get("/results/{eval_id}")
async def get_eval_results(eval_id: str) -> EvalResults:
    """Get evaluation results."""
```

### List Evaluations

```python
@router.get("/list")
async def list_evaluations(
    target_type: Optional[str] = None,
    limit: int = 100
) -> List[EvalSummary]:
    """List past evaluations."""
```

---

## RAG Endpoints

**File:** [`src/heretek_swarm/api/rag.py`](../src/heretek_swarm/api/rag.py)

Retrieval-Augmented Generation operations.

### Ingest Document

```python
@router.post("/ingest")
async def ingest_document(request: IngestRequest) -> IngestResponse:
    """Ingest document into RAG system."""
```

**Request:**
```json
{
  "document": "Document content...",
  "metadata": {
    "source": "manual",
    "category": "knowledge"
  },
  "chunk_size": 500,
  "chunk_overlap": 50
}
```

**Response:**
```json
{
  "document_id": "doc-123",
  "chunks_created": 15,
  "ingested_at": "2026-04-06T10:00:00Z"
}
```

### Query Documents

```python
@router.post("/query")
async def query_documents(request: QueryRequest) -> QueryResponse:
    """Query documents with RAG."""
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
      "metadata": {...}
    }
  ]
}
```

### Delete Document

```python
@router.delete("/documents/{document_id}")
async def delete_document(document_id: str) -> Dict[str, Any]:
    """Delete document from RAG system."""
```

---

## Rate Limiting

**File:** [`src/heretek_swarm/api/rate_limiting.py`](../src/heretek_swarm/api/rate_limiting.py)

API rate limiting configuration.

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
    "details": {...}
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

## WebSocket Endpoints

**File:** [`src/heretek_swarm/api/websockets.py`](../src/heretek_swarm/api/websockets.py)

Real-time WebSocket communication.

### Connect

```
ws://localhost:8000/ws?client_id=client-001
```

### Messages

**Client to Server:**
```json
{
  "type": "subscribe",
  "channel": "agent_events"
}
```

**Server to Client:**
```json
{
  "type": "agent_event",
  "data": {
    "agent_id": "steward-001",
    "event": "message_processed",
    "timestamp": "2026-04-06T10:00:00Z"
  }
}
```

---

## See Also

- [Core Actors System](./CORE_ACTORS.md) - Agent base classes
- [Agent Reference](./AGENT_REFERENCE.md) - All 23 agents
- [Gateway & Communication](./GATEWAY_COMMUNICATION.md) - A2A protocol
- [Deployment Guide](./DEPLOYMENT.md) - Setup instructions
