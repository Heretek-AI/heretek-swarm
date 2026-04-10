# Heretek Swarm - Full Stack Deployment & Performance Testing Plan

## Overview

This plan covers deploying Heretek Swarm with MiniMax LLM and Lemonade Server embeddings, then performing comprehensive functional and performance testing.

**Expected Duration**: 2-3 hours  
**Cluster**: Docker Compose (local)

---

## Phase 1: Pre-Deployment Verification

### 1.1 Infrastructure Health Check
- [ ] Verify Docker is running: `docker compose version`
- [ ] Check ports availability (5432, 6379, 6333, 8000)
- [ ] Confirm no conflicting containers

### 1.2 Configuration Validation
- [ ] `.env` file exists with required keys:
  - `MINIMAX_API_KEY`
  - `MINIMAX_BASE_URL`  
  - `MINIMAX_MODEL`
  - `EMBEDDING_BASE_URL`
  - `EMBEDDING_API_KEY`
  - `EMBEDDER_MODEL`
- [ ] Validate .env syntax: `set -a && source .env && set +a`

### 1.3 External Service Connectivity
- [ ] Test MiniMax API:
  ```bash
  curl -s https://api.minimax.io/v1/models \
    -H "Authorization: Bearer $MINIMAX_API_KEY" | jq
  ```
- [ ] Test Lemonade Server:
  ```bash
  curl -s http://192.168.31.18:13305/api/v1/embeddings \
    -H "Authorization: Bearer lemonade" \
    -H "Content-Type: application/json" \
    -d '{"input": "test"}' | jq
  ```

---

## Phase 2: Stack Deployment

### 2.1 Clean Start (Optional)
```bash
# Only if starting fresh
docker compose down -v
docker volume prune -f
```

### 2.2 Build Images
```bash
docker compose build --no-cache
```

### 2.3 Start Infrastructure
```bash
docker compose up -d postgres redis qdrant

# Wait for healthy
until docker compose exec -T postgres pg_isready -U heretek -d heretek_swarm; do sleep 2; done
until docker compose exec -T redis redis-cli ping | grep -q PONG; do sleep 2; done
curl -s http://localhost:6333/ | jq -e '.version' && echo "Qdrant ready"
```

### 2.4 Deploy API
```bash
docker compose up -d api

# Wait for API
for i in {1..30}; do
  status=$(curl -s http://localhost:8000/api/health 2>/dev/null | jq -r '.status')
  if [ "$status" = "healthy" ]; then
    echo "API ready"
    break
  fi
  sleep 2
done
```

### 2.5 Verify Deployment
```bash
curl -s http://localhost:8000/api/health | jq
```

**Success Criteria**: All services show "healthy" status

---

## Phase 3: Functional Testing

### 3.1 Health Endpoints
```bash
# Basic health
curl -s http://localhost:8000/api/health | jq

# Liveness
curl -s http://localhost:8000/api/health/live | jq

# Readiness  
curl -s http://localhost:8000/api/health/ready | jq
```

### 3.2 LLM Provider Tests
```bash
# Test MiniMax connectivity
curl -s http://localhost:8000/api/llm/providers | jq

# Test completion
curl -s -X POST http://localhost:8000/api/llm/complete \
  -H "Content-Type: application/json" \
  -d '{
    "model": "MiniMax-M2.7",
    "messages": [{"role": "user", "content": "Say hello in 3 words"}],
    "max_tokens": 20
  }' | jq '.choices[0].message.content'
```

### 3.3 Embedding Provider Tests
```bash
# Test embedding generation
curl -s -X POST http://localhost:8000/api/rag/embed \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Testing embedding generation",
    "model": "nomic-embed-text-v2-moe-GGUF"
  }' | jq 'length(.|keys)'
```

### 3.4 RAG Pipeline Tests
```bash
# Ingest a test document
curl -s -X POST http://localhost:8000/api/rag/ingest \
  -H "Content-Type: application/json" \
  -d '{
    "content": "Heretek Swarm is a multi-agent orchestration system.",
    "metadata": {"source": "test"}
  }' | jq '.id'

# Query the document
curl -s -X POST http://localhost:8000/api/rag/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What is Heretek Swarm?",
    "limit": 3
  }' | jq '.[0].content'
```

### 3.5 Memory Tests
```bash
# Store memory
curl -s -X POST http://localhost:8000/api/memory/store \
  -H "Content-Type: application/json" \
  -d '{
    "agent_id": "test-agent",
    "content": "Test memory entry",
    "memory_type": "ephemeral"
  }' | jq '.id'

# Retrieve memories
curl -s "http://localhost:8000/api/memory?agent_id=test-agent" | jq 'length'
```

### 3.6 Agent Tests
```bash
# List agents
curl -s http://localhost:8000/api/agents | jq

# Get supervisor status
curl -s http://localhost:8000/api/supervisor/status | jq
```

### 3.7 A2A Protocol Tests
```bash
# Get recent messages
curl -s http://localhost:8000/api/a2a/messages?limit=10 | jq 'length'
```

---

## Phase 4: Performance Testing

### 4.1 Baseline Metrics

| Metric | Target | Actual |
|--------|--------|--------|
| API startup time |