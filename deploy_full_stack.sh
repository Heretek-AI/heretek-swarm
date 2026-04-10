#!/bin/bash
# Full Stack Deployment Script for Heretek Swarm
# Uses Lemonade Server for embeddings and MiniMax for LLM

set -e

echo "=============================================="
echo "Heretek Swarm - Full Stack Deployment"
echo "=============================================="

# Load environment variables
if [ -f .env ]; then
    echo "Loading environment from .env..."
    export $(cat .env | grep -v '^#' | xargs)
fi

# Build images
echo ""
echo "[1/4] Building docker compose --env-file .env build --no-cache"
docker compose build --no-cache

# Start infrastructure services first
echo ""
echo "[2/4] Starting infrastructure services..."
docker compose up -d postgres redis qdrant

# Wait for health checks
echo "Waiting for postgres..."
until docker compose exec -T postgres pg_isready -U heretek -d heretek_swarm 2>/dev/null; do
    echo -n "."
    sleep 2
done
echo "✓ postgres ready"

echo "Waiting for redis..."
until docker compose exec -T redis redis-cli ping 2>/dev/null | grep -q PONG; do
    sleep 2
done
echo "✓ redis ready"

echo "Waiting for qdrant..."
until curl -s http://localhost:6333/ >/dev/null 2>&1; do
    sleep 2
done
echo "✓ qdrant ready"

# Start API and frontend
echo ""
echo "[3/4] Starting application services..."
docker compose up -d api

# Wait for API to be healthy
echo "Waiting for API..."
until curl -s http://localhost:8000/api/health >/dev/null 2>&1; do
    sleep 2
done
echo "✓ API ready"

# Start frontend
echo ""
echo "[4/4] Starting frontend..."
docker compose up -d frontend

echo ""
echo "=============================================="
echo "Deployment Complete!"
echo "=============================================="
echo "Services:"
echo "  API:       http://localhost:8000"
echo "  Frontend:  http://localhost:3000"
echo "  Qdrant:    http://localhost:6333"
echo "  Postgres: localhost:5432"
echo "  Redis:     localhost:6379"
echo ""
echo "Embedding Provider: Lemonade Server"
echo "  URL:       http://192.168.31.18:13305/api/v1"
echo "  Model:     nomic-embed-text-v2-moe-GGUF"
echo ""
echo "LLM Provider: MiniMax"
echo "  URL:       https://api.minimax.io/v1"
echo "  Model:     MiniMax-M2.7"
echo "=============================================="