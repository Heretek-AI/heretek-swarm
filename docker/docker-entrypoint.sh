#!/bin/bash
set -e

# Heretek Swarm Autonomous Runtime - Docker Entrypoint
# Handles initialization and startup for 24/7 container operation

echo "=== Heretek Swarm Autonomous Runtime ==="
echo "Starting at $(date -u +%Y-%m-%dT%H:%M:%SZ)"

# Wait for dependencies if DOCKER_WAIT_FOR is set
if [ -n "$DOCKER_WAIT_FOR" ]; then
    echo "Waiting for dependencies: $DOCKER_WAIT_FOR"
    IFS=',' read -ra ADDR <<< "$DOCKER_WAIT_FOR"
    for i in "${ADDR[@]}"; do
        host=$(echo $i | cut -d':' -f1)
        port=$(echo $i | cut -d':' -f2)
        echo "  Waiting for $host:$port..."
        while ! nc -z $host $port; do
            sleep 1
        done
        echo "  $host:$port is available"
    done
fi

# Run database migrations if enabled
if [ "$RUN_MIGRATIONS" = "true" ]; then
    echo "Running database migrations..."
    python -m migrations.run || echo "Migration warning (may already be applied)"
fi

# Verify environment variables
if [ -z "$DATABASE_URL" ]; then
    echo "Warning: DATABASE_URL not set, using default"
    export DATABASE_URL="postgresql://heretek:password@postgres:5432/heretek_swarm"
fi

if [ -z "$REDIS_URL" ]; then
    echo "Warning: REDIS_URL not set, using default"
    export REDIS_URL="redis://redis:6379"
fi

if [ -z "$NATS_SERVERS" ]; then
    echo "Warning: NATS_SERVERS not set, using default"
    export NATS_SERVERS="nats://nats:4222"
fi

if [ -z "$QDRANT_URL" ]; then
    echo "Warning: QDRANT_URL not set, using default"
    export QDRANT_URL="http://qdrant:6333"
fi

# Set feature flags
export CONSCIOUSNESS_ENABLED="${CONSCIOUSNESS_ENABLED:-true}"
export RAG_ENABLED="${RAG_ENABLED:-true}"
export AUTO_RESTART_ENABLED="${AUTO_RESTART_ENABLED:-true}"

echo ""
echo "Configuration:"
echo "  DATABASE_URL: ${DATABASE_URL:0:30}..."
echo "  REDIS_URL: ${REDIS_URL:0:30}..."
echo "  NATS_SERVERS: ${NATS_SERVERS}"
echo "  QDRANT_URL: ${QDRANT_URL}"
echo "  CONSCIOUSNESS_ENABLED: $CONSCIOUSNESS_ENABLED"
echo "  RAG_ENABLED: $RAG_ENABLED"
echo "  AUTO_RESTART_ENABLED: $AUTO_RESTART_ENABLED"
echo ""

# Execute the main command
echo "Starting autonomous runtime..."
exec "$@"
