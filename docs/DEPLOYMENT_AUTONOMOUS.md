# Heretek Swarm - Autonomous Deployment Guide

## Executive Summary

This guide provides comprehensive instructions for deploying Heretek Swarm in autonomous mode for 24/7 operation. Two deployment methods are supported:

1. **Docker Compose** - Recommended for most deployments (containerized)
2. **Systemd** - For bare-metal Linux deployments

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Docker Compose Deployment](#docker-compose-deployment)
3. [Systemd Deployment](#systemd-deployment)
4. [Configuration Reference](#configuration-reference)
5. [Security Hardening](#security-hardening)
6. [Monitoring & Observability](#monitoring--observability)
7. [Troubleshooting](#troubleshooting)

## Prerequisites

### Hardware Requirements

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| CPU | 4 cores | 8+ cores |
| RAM | 8 GB | 16+ GB |
| Storage | 50 GB SSD | 100+ GB NVMe |
| Network | 1 Gbps | 10 Gbps |

### Software Requirements

#### Docker Compose Deployment

- Docker 24.0+
- Docker Compose 2.20+
- Linux kernel 5.10+ or macOS 12+ or Windows 11 with WSL2

#### Systemd Deployment

- Linux distribution with systemd (Ubuntu 22.04+, Debian 11+, RHEL 9+)
- Python 3.11+
- PostgreSQL 15+
- Redis 7+
- NATS Server 2.10+
- Qdrant 1.7+

### Environment Variables

Create `/etc/heretek-swarm/.env` for systemd or `.env` for Docker Compose:

```bash
# Required API Keys
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...

# Database Configuration
DATABASE_URL=postgresql://heretek:password@localhost:5432/heretek_swarm
REDIS_URL=redis://localhost:6379

# Event Mesh Configuration
NATS_SERVERS=nats://localhost:4222

# Vector Store Configuration
QDRANT_URL=http://localhost:6333

# Feature Flags
CONSCIOUSNESS_ENABLED=true
RAG_ENABLED=true
MEMORY_ENABLED=true

# Security
AUTH_TOKEN=your-secure-token-here
DEBUG_MODE=false
```

## Docker Compose Deployment

### Step 1: Clone and Prepare

```bash
git clone https://github.com/heretek/heretek-swarm.git
cd heretek-swarm
```

### Step 2: Configure Environment

```bash
cp .env.example .env
# Edit .env with your configuration
nano .env
```

### Step 3: Start Services

```bash
# Start the full stack
docker-compose -f docker-compose.autonomous.yml up -d

# View logs
docker-compose -f docker-compose.autonomous.yml logs -f heretek-swarm

# Check service health
docker-compose -f docker-compose.autonomous.yml ps
```

### Step 4: Verify Deployment

```bash
# Check API health
curl http://localhost:8000/api/health

# Check A2A Protocol
curl http://localhost:18789/health

# Check MCP Server
curl http://localhost:18790/health
```

### Step 5: Access Services

| Service | URL | Description |
|---------|-----|-------------|
| API Gateway | http://localhost:8000 | REST API |
| A2A Protocol | http://localhost:18789 | Agent-to-Agent |
| MCP Server | http://localhost:18790 | Model Context Protocol |
| Qdrant UI | http://localhost:6333/dashboard | Vector Store UI |
| NATS Monitor | http://localhost:8222 | Event Mesh Monitor |

### Docker Commands Reference

```bash
# Stop all services
docker-compose -f docker-compose.autonomous.yml down

# Stop and remove volumes (data loss!)
docker-compose -f docker-compose.autonomous.yml down -v

# Rebuild containers
docker-compose -f docker-compose.autonomous.yml up -d --build

# Scale services (if stateless)
docker-compose -f docker-compose.autonomous.yml up -d --scale heretek-swarm=3

# View resource usage
docker stats

# Execute command in container
docker exec -it heretek-swarm-autonomous bash
```

## Systemd Deployment

### Step 1: Install Dependencies

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python and dependencies
sudo apt install -y python3.11 python3.11-venv python3-pip git curl

# Install PostgreSQL
sudo apt install -y postgresql-15 postgresql-contrib

# Install Redis
sudo apt install -y redis-server

# Install NATS (from official repo)
curl -fsSL https://raw.githubusercontent.com/nats-io/nats-server/main/install.sh | sh

# Install Qdrant (Docker or binary)
docker pull qdrant/qdrant:latest
```

### Step 2: Create Application User

```bash
sudo useradd --system --create-home --shell /bin/bash heretek
```

### Step 3: Install Application

```bash
# Create directories
sudo mkdir -p /opt/heretek-swarm/{src,logs,data}
sudo chown -R heretek:heretek /opt/heretek-swarm

# Clone repository
sudo -u heretek git clone https://github.com/heretek/heretek-swarm.git /opt/heretek-swarm/src

# Create virtual environment
sudo -u heretek python3 -m venv /opt/heretek-swarm/venv

# Install dependencies
sudo -u heretek /opt/heretek-swarm/venv/bin/pip install -e /opt/heretek-swarm/src[all]
```

### Step 4: Configure Database

```bash
# Create PostgreSQL user and database
sudo -u postgres psql << EOF
CREATE USER heretek WITH PASSWORD 'password';
CREATE DATABASE heretek_swarm OWNER heretek;
GRANT ALL PRIVILEGES ON DATABASE heretek_swarm TO heretek;
\\c heretek_swarm
CREATE EXTENSION IF NOT EXISTS vector;
EOF

# Start and enable PostgreSQL
sudo systemctl enable postgresql
sudo systemctl start postgresql
```

### Step 5: Configure Redis

```bash
# Configure Redis
sudo sed -i 's/# maxmemory <bytes>/maxmemory 512mb/' /etc/redis/redis.conf
sudo sed -i 's/# maxmemory-policy noeviction/maxmemory-policy allkeys-lru/' /etc/redis/redis.conf

# Start and enable Redis
sudo systemctl enable redis-server
sudo systemctl start redis-server
```

### Step 6: Configure NATS

```bash
# Create NATS configuration
sudo mkdir -p /etc/nats
sudo tee /etc/nats/nats.conf > /dev/null << EOF
jetstream {
    store_dir: /var/lib/nats/jetstream
    max_mem_store: 256MB
    max_file_store: 1GB
}

listen: 0.0.0.0:4222
monitor_port: 8222
EOF

# Create NATS service
sudo tee /etc/systemd/system/nats.service > /dev/null << EOF
[Unit]
Description=NATS Server
Documentation=https://nats.io
After=network.target

[Service]
Type=exec
User=nats
Group=nats
ExecStart=/usr/local/bin/nats-server --config /etc/nats/nats.conf
Restart=always
LimitNOFILE=65536

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable nats
sudo systemctl start nats
```

### Step 7: Configure Qdrant

```bash
# Run Qdrant with Docker
docker run -d \
    --name qdrant \
    -p 6333:6333 \
    -p 6334:6334 \
    -v qdrant_storage:/qdrant/storage \
    --restart unless-stopped \
    qdrant/qdrant:latest
```

### Step 8: Install Systemd Service

```bash
# Copy service file
sudo cp systemd/heretek-swarm.service /etc/systemd/system/

# Create environment file
sudo mkdir -p /etc/heretek-swarm
sudo cp .env.example /etc/heretek-swarm/.env
sudo nano /etc/heretek-swarm/.env

# Set permissions
sudo chown -R heretek:heretek /etc/heretek-swarm
sudo chmod 600 /etc/heretek-swarm/.env
```

### Step 9: Start Service

```bash
# Reload systemd
sudo systemctl daemon-reload

# Enable service
sudo systemctl enable heretek-swarm

# Start service
sudo systemctl start heretek-swarm

# Check status
sudo systemctl status heretek-swarm

# View logs
sudo journalctl -u heretek-swarm -f
```

### Step 10: Verify Deployment

```bash
# Check API health
curl http://localhost:8000/api/health

# Check service status
sudo systemctl is-active heretek-swarm

# Check listening ports
sudo ss -tlnp | grep -E '8000|18789|18790'
```

## Configuration Reference

### Environment Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `OPENAI_API_KEY` | OpenAI API key | - | Yes (for OpenAI) |
| `ANTHROPIC_API_KEY` | Anthropic API key | - | Yes (for Claude) |
| `DATABASE_URL` | PostgreSQL connection string | - | Yes |
| `REDIS_URL` | Redis connection string | redis://localhost:6379 | Yes |
| `NATS_SERVERS` | NATS server URLs | nats://localhost:4222 | Yes |
| `QDRANT_URL` | Qdrant vector store URL | http://localhost:6333 | Yes |
| `CONSCIOUSNESS_ENABLED` | Enable consciousness metrics | true | No |
| `RAG_ENABLED` | Enable RAG pipeline | true | No |
| `MEMORY_ENABLED` | Enable memory system | true | No |
| `AUTH_TOKEN` | API authentication token | - | Yes |
| `DEBUG_MODE` | Enable debug logging | false | No |
| `LOG_LEVEL` | Logging level | INFO | No |

### Docker Compose Services

| Service | Image | Port | Volume |
|---------|-------|------|--------|
| heretek-swarm | Custom | 8000, 18789, 18790 | swarm_logs |
| postgres | postgres:15-alpine | 5432 | postgres_data |
| redis | redis:7-alpine | 6379 | redis_data |
| qdrant | qdrant/qdrant:latest | 6333, 6334 | qdrant_data |
| nats | nats:latest | 4222, 8222 | nats_data |

## Security Hardening

### Zero-Trust Principles

The deployment follows zero-trust security principles:

1. **Least Privilege** - Non-root user, minimal capabilities
2. **Defense in Depth** - Multiple security layers
3. **Network Segmentation** - Isolated Docker network
4. **Input Validation** - All inputs sanitized
5. **Audit Logging** - All actions logged

### Systemd Security Features

The systemd service includes:

- `NoNewPrivileges=yes` - Prevent privilege escalation
- `ProtectSystem=strict` - Read-only system directories
- `ProtectHome=yes` - Isolate from user home directories
- `PrivateTmp=yes` - Private /tmp namespace
- `RestrictAddressFamilies` - Limited network access
- `CapabilityBoundingSet` - Minimal Linux capabilities
- `MemoryDenyWriteExecute=yes` - Prevent code injection

### Docker Security Features

The Docker deployment includes:

- Non-root `heretek` user
- Read-only root filesystem
- Health checks for all services
- Network isolation
- Resource limits

### Firewall Configuration

```bash
# UFW (Ubuntu)
sudo ufw allow 22/tcp      # SSH
sudo ufw allow 8000/tcp    # API Gateway
sudo ufw allow 18789/tcp   # A2A Protocol
sudo ufw allow 18790/tcp   # MCP Server
sudo ufw enable

# firewalld (RHEL/CentOS)
sudo firewall-cmd --permanent --add-port=22/tcp
sudo firewall-cmd --permanent --add-port=8000/tcp
sudo firewall-cmd --permanent --add-port=18789/tcp
sudo firewall-cmd --permanent --add-port=18790/tcp
sudo firewall-cmd --reload
```

## Monitoring & Observability

### Health Checks

```bash
# API Gateway health
curl http://localhost:8000/api/health

# Agent health
curl http://localhost:8000/api/agents/health

# System metrics
curl http://localhost:8000/api/metrics

# NATS health
curl http://localhost:8222/healthz

# Qdrant health
curl http://localhost:6333/
```

### Log Locations

| Deployment | Log Location |
|------------|--------------|
| Docker Compose | `docker-compose logs -f` |
| Systemd | `journalctl -u heretek-swarm -f` |
| Application | `/opt/heretek-swarm/logs/` |

### Metrics Endpoints

| Endpoint | Description |
|----------|-------------|
| `/api/metrics` | Prometheus metrics |
| `/api/health` | Health status |
| `/api/agents/health` | Agent health |
| `/api/channels/stats` | Channel statistics |

### Grafana Dashboard

Import the Grafana dashboard from `dashboard/` for visualization:

1. Install Grafana
2. Add Prometheus data source
3. Import dashboard from `dashboard/grafana-dashboard.json`

## Troubleshooting

### Common Issues

#### Service Won't Start

```bash
# Check systemd status
sudo systemctl status heretek-swarm

# Check logs
sudo journalctl -u heretek-swarm -n 100

# Verify environment file
sudo cat /etc/heretek-swarm/.env

# Test configuration
sudo -u heretek /opt/heretek-swarm/venv/bin/python -m heretek_swarm.runtime.main_loop --check-config
```

#### Database Connection Failed

```bash
# Check PostgreSQL status
sudo systemctl status postgresql

# Test connection
psql -h localhost -U heretek -d heretek_swarm

# Check pgvector extension
psql -h localhost -U heretek -d heretek_swarm -c "SELECT * FROM pg_extension WHERE extname='vector';"
```

#### NATS Connection Failed

```bash
# Check NATS status
sudo systemctl status nats

# Test connection
nats sub '>' --server nats://localhost:4222

# Check NATS logs
sudo journalctl -u nats -f
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

#### High Memory Usage

```bash
# Check memory usage
docker stats
# or
ps aux | grep heretek-swarm

# Restart service
sudo systemctl restart heretek-swarm
# or
docker-compose -f docker-compose.autonomous.yml restart

# Adjust Redis maxmemory
sudo redis-cli CONFIG SET maxmemory 512mb
```

### Debug Mode

Enable debug logging for troubleshooting:

```bash
# In .env or /etc/heretek-swarm/.env
DEBUG_MODE=true
LOG_LEVEL=DEBUG
```

Then restart the service.

### Performance Tuning

#### PostgreSQL

```sql
-- In /var/lib/postgresql/15/main/postgresql.conf
shared_buffers = 256MB
effective_cache_size = 1GB
work_mem = 16MB
maintenance_work_mem = 128MB
max_connections = 100
```

#### Redis

```bash
# In /etc/redis/redis.conf
maxmemory 512mb
maxmemory-policy allkeys-lru
appendonly yes
appendfsync everysec
```

#### NATS

```bash
# In /etc/nats/nats.conf
max_payload: 8MB
max_pending: 64MB
write_deadline: 10s
```

## Support

For issues and feature requests, please open an issue at:
https://github.com/heretek/heretek-swarm/issues

For security issues, please email security@heretek.io
