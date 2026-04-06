# Heretek Swarm Deployment Guide

## Complete Setup and Deployment Instructions

**Version:** 1.11.0  
**Session:** 21 (2026-04-06)  
**Health Score:** 100/100

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Quick Start](#quick-start)
3. [Local Development Setup](#local-development-setup)
4. [Docker Deployment](#docker-deployment)
5. [Kubernetes Deployment](#kubernetes-deployment)
6. [Production Deployment](#production-deployment)
7. [Configuration Reference](#configuration-reference)
8. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### Required Software

| Software | Version | Purpose |
|----------|---------|---------|
| Python | 3.11+ | Runtime |
| Node.js | 18+ | Dashboard frontend |
| Docker | 24+ | Containerization |
| Docker Compose | 2.20+ | Multi-container orchestration |
| kubectl | 1.28+ | Kubernetes CLI (for K8s deployment) |
| Helm | 3.13+ | Kubernetes package manager (optional) |

### Infrastructure Requirements

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| CPU | 4 cores | 8+ cores |
| RAM | 8 GB | 16+ GB |
| Storage | 20 GB | 50+ GB SSD |
| Network | 100 Mbps | 1 Gbps |

### External Services

| Service | Purpose | Required |
|---------|---------|----------|
| OpenAI API | LLM integration | Yes (for AI features) |
| PostgreSQL 15+ | Persistent storage | Yes |
| Redis 7+ | Caching & pub/sub | Yes |
| Qdrant 1.7+ | Vector memory | Yes (for mem0) |

---

## Quick Start

### 1. Clone Repository

```bash
git clone https://github.com/Heretek-AI/heretek-swarm.git
cd heretek-swarm
```

### 2. Setup Environment

```bash
# Copy environment template
cp .env.example .env

# Edit with your credentials
nano .env  # or use your preferred editor
```

### 3. Start with Docker

```bash
# Build and start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Check health
curl http://localhost:8000/health
```

### 4. Access Services

| Service | URL | Description |
|---------|-----|-------------|
| API | http://localhost:8000 | FastAPI backend |
| Dashboard | http://localhost:3000 | React frontend |
| Docs | http://localhost:8000/docs | API documentation |
| Grafana | http://localhost:3001 | Metrics dashboard |

---

## Local Development Setup

### Step 1: Install Python Dependencies

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or: venv\Scripts\activate  # Windows

# Install with dev dependencies
pip install -e ".[dev]"

# Verify installation
python -c "from heretek_swarm.actors import StewardAgent; print('OK')"
```

### Step 2: Setup Database

```bash
# Start PostgreSQL (Docker)
docker run -d --name postgres \
  -e POSTGRES_USER=postgres \
  -e POSTGRES_PASSWORD=postgres \
  -e POSTGRES_DB=heretek_swarm \
  -p 5432:5432 \
  postgres:15

# Run migrations
python scripts/run_migrations.py

# Verify tables
psql postgresql://postgres:postgres@localhost:5432/heretek_swarm -c "\dt"
```

### Step 3: Setup Redis

```bash
# Start Redis (Docker)
docker run -d --name redis \
  -p 6379:6379 \
  redis:7-alpine

# Test connection
redis-cli ping  # Should return: PONG
```

### Step 4: Setup Qdrant

```bash
# Start Qdrant (Docker)
docker run -d --name qdrant \
  -p 6333:6333 \
  -p 6334:6334 \
  qdrant/qdrant:latest

# Test connection
curl http://localhost:6333/
```

### Step 5: Start API Server

```bash
# Development mode with auto-reload
uvicorn heretek_swarm.api.main:app \
  --reload \
  --host 0.0.0.0 \
  --port 8000

# Production mode
uvicorn heretek_swarm.api.main:app \
  --host 0.0.0.0 \
  --port 8000 \
  --workers 4
```

### Step 6: Run Tests

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ -v --cov=src/heretek_swarm --cov-report=html

# Run specific test category
pytest tests/actors/ -v
pytest tests/memory/ -v
pytest tests/plugins/ -v
```

### Step 7: Setup Dashboard (Optional)

```bash
cd dashboard

# Install dependencies
npm install

# Start development server
npm run dev

# Build for production
npm run build
```

---

## Docker Deployment

### Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    docker-compose.yml                    │
├─────────────────────────────────────────────────────────┤
│  Service        │ Port  │ Description                    │
├─────────────────────────────────────────────────────────┤
│  api            │ 8000  │ FastAPI backend                │
│  dashboard      │ 3000  │ React frontend                 │
│  postgres       │ 5432  │ PostgreSQL database            │
│  redis          │ 6379  │ Redis cache                    │
│  qdrant         │ 6333  │ Vector database                │
│  grafana        │ 3001  │ Metrics dashboard              │
│  prometheus     │ 9090  │ Metrics collection             │
└─────────────────────────────────────────────────────────┘
```

### Configuration

**docker-compose.yml:**

```yaml
version: '3.8'

services:
  api:
    build:
      context: .
      dockerfile: docker/Dockerfile.api
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://postgres:postgres@postgres:5432/heretek_swarm
      - REDIS_URL=redis://redis:6379
      - QDRANT_HOST=qdrant
      - OPENAI_API_KEY=${OPENAI_API_KEY}
    depends_on:
      - postgres
      - redis
      - qdrant
    volumes:
      - ./src:/app/src

  dashboard:
    build:
      context: ./dashboard
      dockerfile: ../docker/Dockerfile
    ports:
      - "3000:3000"
    depends_on:
      - api

  postgres:
    image: postgres:15
    environment:
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
      POSTGRES_DB: heretek_swarm
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./migrations:/docker-entrypoint-initdb.d

  redis:
    image: redis:7-alpine
    volumes:
      - redis_data:/data

  qdrant:
    image: qdrant/qdrant:latest
    volumes:
      - qdrant_data:/qdrant/storage

  grafana:
    image: grafana/grafana:latest
    ports:
      - "3001:3000"
    volumes:
      - grafana_data:/var/lib/grafana

  prometheus:
    image: prom/prometheus:latest
    ports:
      - "9090:9090"
    volumes:
      - ./docker/prometheus.yml:/etc/prometheus/prometheus.yml

volumes:
  postgres_data:
  redis_data:
  qdrant_data:
  grafana_data:
```

### Commands

```bash
# Build all images
docker-compose build

# Start all services
docker-compose up -d

# View logs
docker-compose logs -f
docker-compose logs api
docker-compose logs dashboard

# Stop all services
docker-compose down

# Stop and remove volumes (WARNING: deletes data)
docker-compose down -v

# Restart specific service
docker-compose restart api

# Scale service (for stateless services)
docker-compose up -d --scale api=3
```

### Health Checks

```bash
# API health
curl http://localhost:8000/health

# Database connection
docker-compose exec api python -c "from heretek_swarm.memory import Mem0Backend; print('OK')"

# Redis connection
docker-compose exec redis redis-cli ping

# Qdrant connection
curl http://localhost:6333/
```

---

## Kubernetes Deployment

### Prerequisites

- Kubernetes cluster 1.28+
- kubectl configured
- Helm 3.13+ (optional)
- Storage class configured

### Namespace Setup

```bash
# Create namespace
kubectl apply -f k8s/namespace.yaml

# Verify
kubectl get namespace heretek-swarm
```

### Configuration

```bash
# Apply ConfigMap
kubectl apply -f k8s/configmaps.yaml

# Create secrets (edit first)
kubectl apply -f k8s/secrets.yaml
```

### Deploy Infrastructure

```bash
# PostgreSQL
kubectl apply -f k8s/postgres-deployment.yaml

# Redis
kubectl apply -f k8s/redis-deployment.yaml

# Qdrant
kubectl apply -f k8s/qdrant-deployment.yaml
```

### Deploy Application

```bash
# API
kubectl apply -f k8s/api-deployment.yaml

# Dashboard
kubectl apply -f k8s/dashboard-deployment.yaml

# Autonomous Runtime (optional)
kubectl apply -f k8s/autonomous-deployment.yaml
```

### Monitoring

```bash
# Prometheus
kubectl apply -f k8s/prometheus-config.yaml
kubectl apply -f k8s/prometheus-deployment.yaml

# Grafana
kubectl apply -f k8s/grafana-deployment.yaml
```

### Networking

```bash
# Ingress
kubectl apply -f k8s/ingress.yaml

# Horizontal Pod Autoscaler
kubectl apply -f k8s/hpa.yaml
```

### Verification

```bash
# Check all pods
kubectl get pods -n heretek-swarm

# Check services
kubectl get svc -n heretek-swarm

# View logs
kubectl logs -n heretek-swarm deploy/api

# Port forward for testing
kubectl port-forward -n heretek-swarm svc/api 8000:80
kubectl port-forward -n heretek-swarm svc/dashboard 3000:80
```

### Scaling

```bash
# Manual scaling
kubectl scale deployment api -n heretek-swarm --replicas=3

# View HPA
kubectl get hpa -n heretek-swarm
```

### Cleanup

```bash
# Delete all resources
kubectl delete namespace heretek-swarm
```

---

## Production Deployment

### Security Checklist

- [ ] API keys rotated and secured
- [ ] Database credentials changed from defaults
- [ ] TLS/SSL configured for all endpoints
- [ ] Firewall rules configured
- [ ] Rate limiting enabled
- [ ] Authentication required on all endpoints
- [ ] Secrets stored in secure vault
- [ ] Audit logging enabled

### Environment Variables (Production)

```bash
# Required
OPENAI_API_KEY=sk-...
DATABASE_URL=postgresql://user:pass@host:5432/db
REDIS_URL=redis://host:6379
QDRANT_HOST=host

# Security
HERETEK_API_KEY=htsk_...
SECRET_KEY=your-secret-key-here

# Optional
LOG_LEVEL=INFO
ENABLE_TRACING=true
ENABLE_METRICS=true
```

### High Availability

```yaml
# Example: Multi-replica API deployment
apiVersion: apps/v1
kind: Deployment
metadata:
  name: api
spec:
  replicas: 3
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1
      maxUnavailable: 0
  template:
    spec:
      affinity:
        podAntiAffinity:
          requiredDuringSchedulingIgnoredDuringExecution:
          - labelSelector:
              matchExpressions:
              - key: app
                operator: In
                values:
                - api
            topologyKey: "kubernetes.io/hostname"
```

### Backup Strategy

```bash
# PostgreSQL backup
pg_dump postgresql://user:pass@host:5432/db > backup.sql

# Redis backup
redis-cli BGSAVE

# Qdrant snapshot
curl -X POST http://host:6333/collections/_local/snapshots
```

### Monitoring

| Metric | Alert Threshold | Action |
|--------|-----------------|--------|
| API Latency (p95) | > 500ms | Scale up |
| Error Rate | > 1% | Investigate |
| Memory Usage | > 80% | Scale up |
| CPU Usage | > 70% | Scale up |
| Queue Depth | > 1000 | Scale workers |

---

## Configuration Reference

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `OPENAI_API_KEY` | - | OpenAI API key for LLM |
| `DATABASE_URL` | - | PostgreSQL connection string |
| `REDIS_URL` | `redis://localhost:6379` | Redis connection string |
| `QDRANT_HOST` | `localhost` | Qdrant vector database host |
| `QDRANT_PORT` | `6333` | Qdrant port |
| `HERETEK_API_KEY` | - | API authentication key |
| `LOG_LEVEL` | `INFO` | Logging level |
| `ENABLE_TRACING` | `false` | Enable OpenTelemetry tracing |
| `ENABLE_METRICS` | `true` | Enable Prometheus metrics |

### File Locations

| Path | Description |
|------|-------------|
| `config/` | Configuration files |
| `migrations/` | Database migrations |
| `scripts/` | Utility scripts |
| `k8s/` | Kubernetes manifests |
| `docker/` | Docker configurations |
| `dashboard/` | Frontend application |
| `src/heretek_swarm/` | Main source code |
| `tests/` | Test suite |

---

## Troubleshooting

### Common Issues

#### API Won't Start

```bash
# Check logs
docker-compose logs api

# Verify database connection
docker-compose exec api python -c "from heretek_swarm.memory import Mem0Backend"

# Check environment variables
docker-compose exec api env | grep -E "DATABASE|REDIS|QDRANT"
```

#### Database Connection Failed

```bash
# Check PostgreSQL is running
docker-compose ps postgres

# Test connection
docker-compose exec postgres psql -U postgres -c "SELECT 1"

# Check connection string
echo $DATABASE_URL
```

#### Memory Issues

```bash
# Check memory usage
docker stats

# Increase container memory
# Edit docker-compose.yml:
services:
  api:
    deploy:
      resources:
        limits:
          memory: 2G
```

#### High Latency

```bash
# Check API metrics
curl http://localhost:8000/api/observability/metrics

# Check database slow queries
docker-compose exec postgres psql -U postgres -c "SELECT * FROM pg_stat_statements ORDER BY total_time DESC LIMIT 10"

# Scale API
docker-compose up -d --scale api=3
```

### Debug Mode

```bash
# Enable debug logging
export LOG_LEVEL=DEBUG

# Start with verbose output
docker-compose up -d

# View debug logs
docker-compose logs -f api | grep DEBUG
```

### Support

- GitHub Issues: https://github.com/Heretek-AI/heretek-swarm/issues
- Documentation: https://github.com/Heretek-AI/heretek-swarm/docs

---

**License:** Apache 2.0  
**Version:** 1.11.0  
**Last Updated:** 2026-04-06 (Session 21)
