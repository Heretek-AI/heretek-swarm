# Heretek Swarm API — Docker build
#
# Multi-stage build:
#   1. Builder: install deps and compile the Python package
#   2. Production: slim runtime image with the installed package
#
# Build context: repo root (where pyproject.toml lives)
# Usage: docker build -f backend/Dockerfile -t heretek-swarm-api .

# =============================================================================
# Stage 1: Builder
# =============================================================================
FROM python:3.11-slim AS builder

WORKDIR /app

# Install system deps for building
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency manifests first for layer caching
COPY pyproject.toml uv.lock ./
COPY backend ./backend

# Install uv and project dependencies into a venv
RUN pip install --no-cache-dir uv && \
    uv sync --frozen --no-dev --no-editable && \
    uv pip install prometheus-client>=0.19.0 psycopg2-binary>=2.9.0 asyncpg>=0.29.0

# =============================================================================
# Stage 2: Production runtime
# =============================================================================
FROM python:3.11-slim AS production

# Install curl for HEALTHCHECK
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Security: run as non-root user
RUN groupadd -g 1001 appgroup && useradd -u 1001 -g appgroup -s /bin/bash -m appuser

WORKDIR /app

# Copy installed venv from builder
COPY --from=builder --chown=appuser:appgroup /app/.venv /app/.venv

# Copy the installed package
COPY --from=builder --chown=appuser:appgroup /app/backend /app/backend

# Copy migrations from build context root
COPY --chown=appuser:appgroup migrations /app/migrations

# Create agent_workspace and heretek_data directories owned by appuser
RUN mkdir -p /app/agent_workspace /app/heretek_data && chown appuser:appgroup /app/agent_workspace /app/heretek_data

# Set up environment
ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Switch to non-root user
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=10s --retries=3 --start-period=15s \
    CMD curl -sf http://localhost:8000/api/health || exit 1

# Default: run the API server via heretek-swarm serve
CMD ["heretek-swarm", "serve", "--host", "0.0.0.0", "--port", "8000"]
