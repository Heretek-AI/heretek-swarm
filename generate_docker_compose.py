
content = """# Heretek Swarm - Autonomous Runtime Docker Compose
# Full stack for 24/7 continuous operation
#
# Usage:
#   docker-compose -f docker-compose.yml -f docker-compose.autonomous.yml up -d
#
# To include Prometheus monitoring:
#   docker-compose -f docker-compose.yml -f docker-compose.autonomous.yml --profile monitoring up -d
#
# Services:
#   - heretek-swarm (Autonomous runtime)
#   - postgres (Persistent storage)
#   - redis (Ephemeral storage/cache)
#   - qdrant (Vector store)
#   - nats (Event mesh)
#   - prometheus (Metrics collection - optional)
#   - grafana (Metrics visualization - optional)

version: '3.8'

services:
  # ============================================================================
  # HERETEK SWARM - Autonomous Runtime
  # ============================================================================
  heretek-swarm:
    build:
      context: .
      dockerfile: docker/Dockerfile.autonomous
    container_name: heretek-swarm-autonomous
    restart: unless-stopped
    profiles:
      - default
      - monitoring
    ports:
      - "8000:8000"   # API Gateway
      - "18789:18789" # A2A Protocol Server
      - "18790:18790" # MCP Server
    environment:
      # Database
      - DATABASE_URL=postgresql://heretek:password@postgres:5432/heretek_swarm
      # Redis
      - REDIS_URL=redis://redis:6379
      # NATS
      - NATS_SERVERS=nats://nats:4222
      # Qdrant
      - QDRANT_URL=http://qdrant:6333
      # API Keys (set via environment or secrets)
      - OPENAI_API_KEY=${OPENAI_API_KEY:-}
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY:-}
      # Auth
      - JWT_SECRET=${JWT_SECRET:-heretek-swarm-secret-key-change-in-production}
      - API_KEY=${API_KEY:-heretek-swarm-api-key-change-in-production}
      # Feature Flags
      - CONSCIOUSNESS_ENABLED=true
      - RAG_ENABLED=true
      - AUTO_RESTART_ENABLED=true
      # Prometheus metrics
      - PROMETHEUS_ENABLED=true
      # Runtime config
      - RUN_MIGRATIONS=true
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
      qdrant:
        condition: service_healthy
      nats:
        condition: service_healthy
    volumes:
      - swarm_logs:/var/log/heretek-swarm
    networks:
      - heretek-network
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/api/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 60s
    labels:
      - "prometheus.io/scrape=true"
      - "prometheus.io/port=8000"
      - "prometheus.io/path=/metrics"

  # ============================================================================
  # POSTGRESQL - Persistent Storage
  # ============================================================================
  postgres:
    image: postgres:15-alpine
    container_name: heretek-postgres
    restart: unless-stopped
    profiles:
      - default
      - monitoring
    ports:
      - "5432:5432"
    environment:
     :ro
    networks:
      - heretek-network
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U heretek -d heretek_swarm"]
      interval: 10s
      timeout: 5s
      retries: 5

  # ============================================================================
  # REDIS - Ephemeral Storage / Cache
  # ============================================================================
  redis:
    image: redis:7-alpine
    container_name: heretek-redis
    restart: unless-stopped
    profiles:
      - default
         healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

  # ============================================================================
  # QDRANT - Vector Store for RAG
  # ============================================================================
  qdrant:
    image: qdrant/qdrant:latest
    container_name: heretek-qdrant
    restart: unless-stopped
    profiles:
      - default
      - monitoring
    ports:
      - "6333:6333"
      - "6334: 10s
      timeout: 5s
      retries: 5

  # ============================================================================
  # NATS - Event Mesh
  # ============================================================================
  nats:
    image: nats:latest
    container_name: heretek-nats
    restart: unless-stopped
    profiles:
      - default
      - monitoring
    ports:
      - "4222:4222"   # Client
      - "8222:8222"   # Monitoring
    command: -js -m 8222
    volumes:
      - nats_data:/data/nats
    networks:
      - heretek-network
    healthcheck:
      test: ["CMD", "nc", "-z", "localhost", "4222"]
      interval: 10s
      timeout: 5s
      retries: 5

  # ============================================================================
  # PROMETHEUS - Metrics Collection (Optional - with --profile monitoring)
  # ============================================================================
  prometheus:
    image: prom/prometheus:latest
    container_name: heretek-prometheus
    restart: unless-stopped
         - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--web.console.libraries=/etc/prometheus/console_libraries'
      - '--web.console.templates=/etc/prometheus/consoles'
      - '--web.enable-lifecycle'
    networks:
      - heretek-network
    depends_on:
      - heretek-swarm
    healthcheck:
      test: ["CMD", "wget", "-q", "--spider", "http://localhost:9090/-/healthy"]
      interval: 30s
      timeout: 10s
      retries: 3

  # ============================================================================
  # GRAFANA - Metrics Visualization (Optional - with --profile monitoring)
  # ============================================================================
  grafana:
    image: grafana/grafana:latest
    container_name: heretek-grafana
    restart: unless-stopped
    profiles:
      - monitoring
    ports:
      - "3001:3000"
    environment:
      - GF_SECURITY_ADMIN_USER=admin
      - GF_SECURITY_ADMIN_PASSWORD=${GRAFANA_PASSWORD:-adminHELL", "wget --no-verbose --tries=1 --spider http://localhost:3000/api/health || exit 1"]
      interval: 30s
      timeout: 10s
      retries: 3

# ============================================================================
# VOLUMES.0/16
"""

_output_path = "C:/Users/derek/Desktop/Heretek-AI/heretek-swarm/docker-compose.autonomous.yml"

with open(output_path, "w", encoding="utf-8") as f:
    f.write(content)

print(f"Successfully wrote docker-compose.autonomous.yml to {output_path}")
