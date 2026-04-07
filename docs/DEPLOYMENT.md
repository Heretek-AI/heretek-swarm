# Heretek Swarm Deployment Guide

**Version:** 2.0.0  
**Date:** 2026-04-07  
**Status:** Production-Ready

---

## Table of Contents

1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [Quick Start](#quick-start)
4. [Docker Compose Deployment](#docker-compose-deployment)
5. [Autonomous Mode Deployment](#autonomous-mode-deployment)
6. [Kubernetes Deployment](#kubernetes-deployment)
7. [Environment Variables Reference](#environment-variables-reference)
8. [Configuration Migration](#configuration-migration)
9. [Troubleshooting](#troubleshooting)

---

## Overview

The Heretek Swarm can be deployed in several configurations:

| Deployment | Use Case | Complexity |
|------------|----------|------------|
| Docker Compose | Development, testing, small production | Low |
| Docker Compose (Autonomous) | 24/7 autonomous operation | Low |
| Kubernetes | Production, scaling, high availability | Medium |
| Systemd | Bare-metal Linux deployment | Medium |

---

## Prerequisites

### Required Software

| Software | Minimum Version | Purpose |
|----------|-----------------|---------|
| Python | 3.11+ | Runtime |
| Node.js | 18+ | Dashboard frontend |
| Docker | 24+ | Containerization |
| Docker Compose | 2.20+ | Multi-container orchestration |
| kubectl | 1.28+ | Kubernetes CLI (for K8s) |
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
| PostgreSQL 15+ | State persistence | Yes |
| Redis 7+ | Caching & pub/sub | Yes |
| Qdrant 1.8+ | Vector memory | Yes |
| NATS 2.10+ | Event mesh | Yes |

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
nano .env
```

### 3. Start with Docker Compose

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

## Docker Compose Deployment

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

## Autonomous Mode Deployment

For 24/7 autonomous operation, use the autonomous Docker Compose configuration.

### docker-compose.autonomous.yml

```yaml
version: '3.8'

services:
  heretek-swarm-autonomous:
    build:
      context: .
      dockerfile: docker/Dockerfile.autonomous
    ports:
      - "8000:8000"   # API Gateway
      - "18789:18789" # A2A Protocol
      - "18790:18790" # MCP Server
    environment:
      - DATABASE_URL=postgresql://postgres:postgres@postgres:5432/heretek_swarm
      - REDIS_URL=redis://redis:6379
      - QDRANT_HOST=qdrant
      - NATS_SERVERS=nats://nats:4222
      - OPENAI_API_KEY=${OPENAI_API_KEY}
    depends_on:
      - postgres
      - redis
      - qdrant
      - nats
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  nats:
    image: nats:latest
    ports:
      - "4222:4222"
      - "8222:8222"
    command: ["-js"]  # Enable JetStream
    restart: unless-stopped

  # ... (postgres, redis, qdrant same as above)
```

### Commands

```bash
# Start autonomous mode
docker-compose -f docker-compose.autonomous.yml up -d

# View autonomous swarm logs
docker-compose -f docker-compose.autonomous.yml logs -f heretek-swarm-autonomous

# Check service health
curl http://localhost:8000/health
curl http://localhost:18789/health  # A2A Protocol
curl http://localhost:18790/health  # MCP Server

# Access services
# API Gateway:    http://localhost:8000
# A2A Protocol:   http://localhost:18789
# MCP Server:     http://localhost:18790
# Qdrant UI:      http://localhost:6333/dashboard
# NATS Monitor:   http://localhost:8222
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

## Environment Variables Reference

### Required Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `OPENAI_API_KEY` | - | OpenAI API key for LLM |
| `DATABASE_URL` | - | PostgreSQL connection string |
| `REDIS_URL` | `redis://localhost:6379` | Redis connection string |
| `QDRANT_HOST` | `localhost` | Qdrant vector database host |
| `QDRANT_PORT` | `6333` | Qdrant port |
| `NATS_SERVERS` | `nats://localhost:4222` | NATS server URLs |

### Security Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `HERETEK_API_KEY` | - | API authentication key |
| `SECRET_KEY` | - | Secret key for JWT tokens |

### Optional Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `LOG_LEVEL` | `INFO` | Logging level |
| `ENABLE_TRACING` | `true` | Enable OpenTelemetry tracing |
| `ENABLE_METRICS` | `true` | Enable Prometheus metrics |
| `CONSCIOUSNESS_ENABLED` | `true` | Enable consciousness metrics |
| `RAG_ENABLED` | `true` | Enable RAG pipeline |
| `DEBUG_MODE` | `false` | Enable debug logging |

---

## Configuration Migration

### From Environment to Database

The Heretek Swarm supports database-backed configuration for all user-facing settings.

#### Step 1: Run Database Migration

```bash
psql -U postgres -d heretek_swarm -f migrations/009_create_configuration_tables.sql
```

#### Step 2: Migrate from Environment

```bash
curl -X POST http://localhost:8000/api/config/migrate-from-env \
  -H "Authorization: Bearer YOUR_API_KEY"
```

#### Step 3: Update .env File

After migration, your `.env` file should only contain deployment secrets:

```bash
# Keep these in .env (deployment secrets)
DATABASE_URL=postgresql+asyncpg://postgres:password@localhost:5432/heretek_swarm
REDIS_URL=redis://localhost:6379
QDRANT_HOST=localhost
QDRANT_PORT=6333

# Remove these (now in database)
# OPENAI_API_KEY - moved to database
# RATE_LIMIT_ENABLED - moved to database
# MEMORY_MAX_SIZE - moved to database
```

### LLM Provider Configuration

Configure LLM providers through the API or UI:

```bash
# Add OpenAI provider
curl -X POST http://localhost:8000/api/config/llm/providers \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "provider_name": "my-openai",
    "provider_type": "openai",
    "base_url": "https://api.openai.com/v1",
    "api_key": "sk-...",
    "default_model": "gpt-4o",
    "is_enabled": true,
    "is_default": true
  }'
```

### Import/Export Configuration

```bash
# Export all configurations
curl -X GET http://localhost:8000/api/config/export \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -o config-backup.json

# Import configurations
curl -X POST http://localhost:8000/api/config/import \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d @config-backup.json
```

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

#### NATS Connection Failed

```bash
# Check NATS is running
docker-compose ps nats

# Test connection
docker-compose exec nats nats sub '>' --server nats://localhost:4222

# Check NATS logs
docker-compose logs nats
```

#### Qdrant Connection Failed

```bash
# Check Qdrant container
docker ps | grep qdrant
docker logs qdrant

# Test connection
curl http://localhost:6333/

# Check collections
curl http://localhost:6333/collections
```

### Debug Mode

```bash
# Enable debug logging
export LOG_LEVEL=DEBUG
export DEBUG_MODE=true

# Restart service
docker-compose restart api

# View debug logs
docker-compose logs -f api | grep DEBUG
```

### Kubernetes Troubleshooting

```bash
# Check pod status
kubectl get pods -n heretek-swarm

# Describe problematic pod
kubectl describe pod <pod-name> -n heretek-swarm

# View pod logs
kubectl logs <pod-name> -n heretek-swarm

# Check events
kubectl get events -n heretek-swarm --sort-by='.lastTimestamp'
```

---

## Support

- GitHub Issues: https://github.com/Heretek-AI/heretek-swarm/issues
- Documentation: https://github.com/Heretek-AI/heretek-swarm/docs

---

**License:** Apache 2.0  
**Version:** 2.0.0  
**Last Updated:** 2026-04-07
