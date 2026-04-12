    # Heretek Swarm API Server
# Multi-stage build for production deployment

# =============================================================================
# Stage 1: Dependencies
# =============================================================================
FROM python:3.11-slim as dependencies

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY pyproject.toml .
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Install the package in development mode
COPY src/ ./src/
RUN pip install -e .

# =============================================================================
# Stage 2: Runtime
# =============================================================================
FROM python:3.11-slim as runtime

WORKDIR /app

# Create non-root user
RUN useradd -m -u 1000 appuser

# Copy installed dependencies
COPY --from=dependencies /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=dependencies /usr/local/bin /usr/local/bin

# Copy application code
COPY migrations/ ./migrations/
# Copy data directory if it exists (optional)
COPY data/ ./data/

# Create mem0 history database directory and initialize SQLite db
RUN mkdir -p /data && \
    touch /data/mem0_history.db && \
    chown -R appuser:appuser /data

# Set ownership
RUN chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONPATH=/app:$PYTHONPATH
ENV PATH="/home/appuser/.local/bin:$PATH"

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import httpx; httpx.get('http://localhost:8000/api/health')" || exit 1

# Expose port
EXPOSE 8000

# Run application
CMD ["python", "-m", "uvicorn", "src.heretek_swarm.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
