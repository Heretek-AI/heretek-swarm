# Heretek Swarm - Production Dockerfile
# Multi-stage build for optimized production deployment

# Stage 1: Base image with system dependencies
FROM python:3.13-slim as base

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Stage 2: Builder stage
FROM base as builder

# Set working directory
WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY src/ ./src

# Build the application
RUN python -m py_compile src/ -o /tmp/build

# Stage 3: Production image
FROM python:3.13-slim as production

# Create non-root user
RUN useradd -m -s /bin/bash -u heretek

# Install runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy built artifacts from builder
COPY --from=builder /tmp/build /app/build
COPY --from=builder /usr/local/lib/python3.13/site-packages /usr/local/lib/python3.13/site-packages

# Copy source code (for development mode) — owned by root so runtime user cannot modify
COPY --chown=root:root src/ ./src

# Create necessary directories
RUN mkdir -p /app/logs /app/data /app/workflows /app/documents

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    HERETEK_ENV=production \
    LOG_LEVEL=INFO \
    LOG_FORMAT=json

# Switch to non-root user before running (S6471 fix)
USER heretek

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/api/health/live || exit 1

# Expose ports
EXPOSE 8000 8765

# Run with gunicorn for production
CMD ["gunicorn", "heretek_swarm.api.main:app", \
    "--bind", "0.0.0.0:8000", \
    "--workers", "4", \
    "--worker-class", "sync", \
    "--worker-connections", "1000", \
    "--max-requests", "1000", \
    "--max-requests-jitter", "50", \
    "--timeout", "120", \
    "--access-logfile", "/app/logs/access.log", \
    "--error-logfile", "/app/logs/error.log", \
    "--log-level", "info"]

# Labels for orchestration
LABEL maintainer="Heretek AI <dev@heretek.ai>" \
      version="1.0.0" \
      description="Heretek Swarm - Multi-Agent Autonomous AI System" \
      org.opencontainers.image="Heretek Swarm API"
