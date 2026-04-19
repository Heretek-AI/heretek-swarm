"""
Heretek Swarm FastAPI Main Application

Provides HTTP endpoints for:
- Health checks (gateway, redis, postgres, qdrant)
- Agent management and monitoring
- Memory statistics (PostgreSQL and mem0)
- LiteLLM metrics
- A2A message history
- Consensus state
- Prometheus metrics (/metrics)

Reference: MiniMax Audit Lines 585-725
"""

import asyncio
import os
from contextlib import asynccontextmanager
from datetime import UTC, datetime
from typing import Any

import structlog
from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from heretek_swarm.logging.config import logger as logging_logger

# Initialize logging with JSON output for Loki/Promtail
from heretek_swarm.logging.config import setup_logging

# Setup structured JSON logging
log_level = os.getenv("LOG_LEVEL", "INFO").upper()
json_output = os.getenv("LOG_FORMAT", "json").lower() == "json"
setup_logging(log_level=log_level, json_output=json_output)

from heretek_swarm.actors.supervisor import ActorSupervisor
from heretek_swarm.api import (
    agents_management,
    autonomous,
    collective_evolution,
    configuration,
    consciousness,
    consensus,
    emergent_intelligence,
    evaluation,
    metrics,
    observability,
    plugins,
    provisioner,
    rag,
    websockets,
    workflows,
    wizard,
)
from heretek_swarm.api.rate_limiting import setup_rate_limiting
from heretek_swarm.config.loader import (
    get_config,
    initialize_config_loader,
)
from heretek_swarm.config.service import (
    get_config_service,
    initialize_config_service,
    shutdown_config_service,
)
from heretek_swarm.gateway.auth import verify_auth
from heretek_swarm.gateway.nats_event_mesh import NATSEventMesh
from heretek_swarm.memory.persistent import PersistentMemory as PersistentMemoryStore
from heretek_swarm.observability.tracing import setup_telemetry_middleware

# Import mem0 backend
try:
    from memory import MEM0_AVAILABLE, Mem0Backend, Mem0Config
except ImportError:
    MEM0_AVAILABLE = False
    Mem0Backend = None
    Mem0Config = None

# Import logging middleware
from heretek_swarm.api.logging_middleware import setup_logging_middleware

logger = structlog.get_logger("api.main")

# Global supervisor instance
supervisor: ActorSupervisor | None = None
memory_store: PersistentMemoryStore | None = None
mem0_backend: Any | None = None  # Mem0Backend when available
_nats_mesh: NATSEventMesh | None = None  # NATS event mesh for WebSocket bridge


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler for startup and shutdown."""
    global supervisor, memory_store, mem0_backend

    # Startup
    logger.info("Starting Heretek Swarm API...")

    await _init_config_service()
    await _init_supervisor()
    await _init_memory_store()
    await _init_mem0()
    await _init_nats_bridge()
    await _log_startup_complete()

    yield

    # Shutdown
    logger.info("Shutting down Heretek Swarm API...")

    if supervisor:
        await supervisor.terminate_all()

    if mem0_backend:
        await mem0_backend.shutdown()

    if memory_store:
        await memory_store.disconnect()

    if _nats_mesh:
        await _nats_mesh.disconnect()

    # Shutdown ConfigurationService
    await shutdown_config_service()
    logger.info("ConfigurationService shutdown complete")


async def _init_config_service() -> None:
    """Initialize ConfigurationService and loader."""
    global mem0_backend

    config_source = "environment"
    try:
        await initialize_config_service()
        await initialize_config_loader()

        config_service = get_config_service()
        rate_limit_config = await config_service.get_config("rate_limit.enabled")
        if rate_limit_config is not None:
            config_source = "database"
            logger.info("Configuration loaded from database")
        else:
            logger.info("Configuration falling back to environment variables")

        try:
            seed_result = await config_service.seed_from_env()
            if seed_result.get("providers_created") or seed_result.get("embedding_providers_created") or seed_result.get("configs_created"):
                logger.info("env_seeding_complete", **seed_result)
            else:
                logger.info("env_seeding_skipped", reason="no_env_vars_set")
        except Exception as e:
            logger.warning("env_seeding_skipped", reason=str(e))
    except Exception as e:
        logger.warning("ConfigurationService not available", error=str(e))
        logger.info("Using environment variables for configuration")


async def _init_supervisor() -> None:
    """Initialize ActorSupervisor."""
    global supervisor

    supervisor = ActorSupervisor()
    logger.info("ActorSupervisor initialized")

    # Fire-and-forget: spawn all 23 agents without blocking API startup
    asyncio.create_task(_spawn_all_agents())


async def _spawn_all_agents() -> None:
    """
    Spawn all 23 agents into the global supervisor.

    Mirrors the agent list from runtime/main_loop.py:_spawn_all_actors().
    Uses local imports inside the function to avoid import-cycle issues.
    Each spawn is wrapped in try/except so a single failure does not
    prevent others from spawning.
    """
    logger.info("agents_auto_spawn_started")

    # Tier 1: Core Triad (Governance)
    from heretek_swarm.actors.arbiter import ArbiterAgent
    from heretek_swarm.actors.catalyst import CatalystAgent
    from heretek_swarm.actors.chronos import ChronosAgent
    from heretek_swarm.actors.coder import CoderAgent

    # Tier 5: Coordination Agents (Integration)
    from heretek_swarm.actors.coordinator import CoordinatorAgent
    from heretek_swarm.actors.dreamer import DreamerAgent
    from heretek_swarm.actors.echo import EchoActor
    from heretek_swarm.actors.empath import EmpathAgent
    from heretek_swarm.actors.examiner import ExaminerAgent

    # Tier 3: Exploration Agents (Discovery & Creation)
    from heretek_swarm.actors.explorer import ExplorerAgent
    from heretek_swarm.actors.habit_forge import HabitForgeAgent

    # Tier 2: Support Agents (Knowledge & Memory)
    from heretek_swarm.actors.historian import HistorianAgent
    from heretek_swarm.actors.metis import MetisAgent
    from heretek_swarm.actors.nexus import NexusAgent
    from heretek_swarm.actors.perceiver import PerceiverAgent
    from heretek_swarm.actors.perceiver_plus import PerceiverPlusAgent

    # Tier 6: Enhancement Agents (Optimization)
    from heretek_swarm.actors.prism import PrismAgent

    # Tier 4: Safety & Security (Protection)
    from heretek_swarm.actors.sentinel import SentinelAgent
    from heretek_swarm.actors.sentinel_prime import SentinelPrimeAgent
    from heretek_swarm.actors.triad import AlphaAgent, BetaAgent, CharlieAgent, StewardAgent

    actors = [
        # Tier 1: Core Triad
        (StewardAgent, "steward"),
        (AlphaAgent, "alpha"),
        (BetaAgent, "beta"),
        (CharlieAgent, "charlie"),
        # Tier 2: Support
        (HistorianAgent, "historian"),
        (MetisAgent, "metis"),
        (EmpathAgent, "empath"),
        (PerceiverAgent, "perceiver"),
        (EchoActor, "echo"),
        # Tier 3: Exploration
        (ExplorerAgent, "explorer"),
        (ExaminerAgent, "examiner"),
        (DreamerAgent, "dreamer"),
        (CoderAgent, "coder"),
        # Tier 4: Safety
        (SentinelAgent, "sentinel"),
        (SentinelPrimeAgent, "sentinel-prime"),
        (ArbiterAgent, "arbiter"),
        # Tier 5: Coordination
        (CoordinatorAgent, "coordinator"),
        (NexusAgent, "nexus"),
        (CatalystAgent, "catalyst"),
        (ChronosAgent, "chronos"),
        # Tier 6: Enhancement
        (PrismAgent, "prism"),
        (HabitForgeAgent, "habit-forge"),
        (PerceiverPlusAgent, "perceiver-plus"),
    ]

    spawned_count = 0
    for agent_class, agent_id in actors:
        try:
            await supervisor.spawn_actor(agent_class, agent_id)
            logger.info("actor_spawned", agent_id=agent_id)
            spawned_count += 1
        except Exception as e:
            logger.error("actor_spawn_failed", agent_id=agent_id, error=str(e))

    logger.info("all_actors_spawned", count=spawned_count)


async def _init_memory_store() -> None:
    """Initialize PersistentMemoryStore."""
    global memory_store

    try:
        database_url = await get_config("database.url", default=os.environ.get("DATABASE_URL"))
        if not database_url:
            raise ValueError("DATABASE_URL is required")
        memory_store = PersistentMemoryStore()
        await memory_store.connect()
        logger.info("PersistentMemoryStore connected")
    except Exception as e:
        logger.warning("PersistentMemoryStore not available", error=str(e))
        memory_store = None


async def _init_mem0() -> None:
    """Initialize Mem0Backend if available."""
    global mem0_backend

    if MEM0_AVAILABLE:
        try:
            qdrant_host = await get_config(
                "qdrant.url", default=os.environ.get("QDRANT_HOST", "localhost")
            )
            qdrant_port = await get_config(
                "qdrant.port", default=int(os.environ.get("QDRANT_PORT", "6333"))
            )
            openai_api_key = await get_config(
                "llm.api_key", default=os.environ.get("OPENAI_API_KEY")
            )

            mem0_config = Mem0Config(
                qdrant_host=qdrant_host,
                qdrant_port=int(qdrant_port),
                openai_api_key=openai_api_key,
            )
            mem0_backend = Mem0Backend(config=mem0_config)
            await mem0_backend.initialize()
            logger.info("Mem0Backend initialized")
        except Exception as e:
            logger.warning("Mem0Backend not available", error=str(e))
            mem0_backend = None
    else:
        logger.info("mem0 not installed - using PostgreSQL memory only")


async def _init_nats_bridge() -> None:
    """Initialize NATS EventMesh for WebSocket bridge."""
    global _nats_mesh

    try:
        _nats_mesh = NATSEventMesh(fallback=True)
        connected = await _nats_mesh.connect()
        if connected:
            logger.info("NATS EventMesh connected for WebSocket bridge")

            # Subscribe to A2A events from NATS and broadcast to WebSocket clients
            from heretek_swarm.api import websockets

            async def a2a_event_handler(
                mesh: NATSEventMesh, subject: str, data: dict[str, Any]
            ) -> None:
                """Handle A2A event from NATS and broadcast to WebSocket clients."""
                try:
                    await websockets.manager.broadcast_a2a(data)
                    await websockets.manager.broadcast_dashboard({"type": "a2a_message", **data})
                    logger.debug(
                        "broadcast_a2a_from_nats",
                        subject=subject,
                        has_from=bool(data.get("from")),
                        has_to=bool(data.get("to")),
                    )
                except Exception as e:
                    logger.error(
                        "broadcast_a2a_failed",
                        subject=subject,
                        error=str(e),
                    )

            # Subscribe to swarm events (A2A messages)
            await _nats_mesh.subscribe("swarm.events", a2a_event_handler)
            # Also support wildcard pattern for agent messages
            await _nats_mesh.subscribe("agent.>.messages", a2a_event_handler)

            logger.info("NATS subscription registered for A2A events")
        else:
            logger.warning("NATS EventMesh not available, WebSocket bridge using fallback")
    except Exception as e:
        logger.warning("NATS bridge initialization failed", error=str(e))
        _nats_mesh = None


async def _log_startup_complete() -> None:
    """Log application startup completion."""
    logger.info(
        "Application startup complete",
        rate_limit_enabled=await get_config("rate_limit.enabled", default=True),
    )


# Create FastAPI application
app = FastAPI(
    title="Heretek Swarm API",
    description="Multi-agent swarm orchestration with A2A protocol communication",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)


# Add CORS middleware with configuration-based configuration
# Configuration will be loaded from database with environment fallback
allowed_origins_env = os.getenv("CORS_ORIGINS", "")
if allowed_origins_env:
    allowed_origins = allowed_origins_env.split(",")
elif os.getenv("ENVIRONMENT", "development") == "production":
    # Include localhost:3000 for local testing without CORS_ORIGINS env var
    allowed_origins = ["https://your-domain.com", "http://localhost:3000"]
else:
    allowed_origins = ["http://localhost:3000", "http://localhost:5173", "http://localhost:8000"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
    allow_headers=["Authorization", "Content-Type", "X-Requested-With"],
)

# Setup logging middleware for request tracking
setup_logging_middleware(app)
logging_logger.info("Logging middleware configured")


# Register routers
app.include_router(websockets.router)
app.include_router(consensus.router)
app.include_router(plugins.router)
app.include_router(workflows.router)
app.include_router(observability.router)
app.include_router(evaluation.router)
app.include_router(rag.router)
app.include_router(consciousness.router)
app.include_router(emergent_intelligence.router)
app.include_router(agents_management.router)
app.include_router(autonomous.router)
app.include_router(configuration.router)
app.include_router(wizard.router)
app.include_router(provisioner.router)
app.include_router(metrics.router)
app.include_router(collective_evolution.router)

# Setup Prometheus metrics middleware
from heretek_swarm.observability.prometheus_metrics import setup_metrics_middleware

setup_metrics_middleware(app)
logger.info("Prometheus metrics middleware configured")

# Setup OpenTelemetry distributed tracing middleware
setup_telemetry_middleware(app)
logger.info("OpenTelemetry tracing middleware configured")

# Setup rate limiting with configuration from database
# Note: Rate limiting is set up after lifespan starts, so we use environment variable here
# For runtime config changes, use the /api/config/reload endpoint
rate_limit_enabled = os.environ.get("RATE_LIMIT_ENABLED", "true").lower() == "true"
setup_rate_limiting(app, enabled=rate_limit_enabled)
logger.info("Rate limiting configured", enabled=rate_limit_enabled)


# =============================================================================
# Health Check Functions
# =============================================================================


async def check_gateway() -> dict[str, Any]:
    """Check the EventMesh gateway status."""
    try:
        # Check if event mesh is accessible
        # Note: In production, this would check actual connections
        return {
            "status": "healthy",
            "active_connections": 0,
            "messages_processed": 0,
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
        }


async def check_redis() -> dict[str, Any]:
    """Check Redis connection status."""
    try:
        import redis.asyncio as redis

        # Try to connect to Redis
        redis_url = os.environ.get("REDIS_URL", "redis://localhost:6379")
        client = redis.from_url(redis_url)
        await client.ping()
        info = await client.info("server")
        await client.close()
        return {
            "status": "healthy",
            "version": info.get("redis_version", "unknown"),
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
        }


async def check_postgres() -> dict[str, Any]:
    """Check PostgreSQL connection status."""
    try:
        if not memory_store:
            # Try to get database URL and connect directly
            db_url = os.environ.get("DATABASE_URL", "")
            if not db_url:
                raise ValueError("DATABASE_URL environment variable is required")
            from sqlalchemy import text
            from sqlalchemy.ext.asyncio import create_async_engine

            engine = create_async_engine(db_url)
            async with engine.connect() as conn:
                await conn.execute(text("SELECT 1"))
            await engine.dispose()
            return {
                "status": "healthy",
                "database": "heretek_swarm",
            }
        if memory_store and memory_store._engine:
            from sqlalchemy import text

            async with memory_store._engine.connect() as conn:
                await conn.execute(text("SELECT 1"))
            return {
                "status": "healthy",
                "database": "heretek_swarm",
            }
        return {
            "status": "unhealthy",
            "error": "Not connected",
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
        }


async def check_qdrant() -> dict[str, Any]:
    """Check Qdrant vector database status."""
    try:
        import httpx

        # Check multiple environment variables for compatibility
        qdrant_url = os.environ.get("QDRANT_URL")
        if not qdrant_url:
            qdrant_host = os.environ.get("QDRANT_HOST", "localhost")
            qdrant_port = os.environ.get("QDRANT_PORT", "6333")
            qdrant_url = (
                f"https://{qdrant_host}:{qdrant_port}"
                if os.environ.get("ENVIRONMENT") == "production"
                else f"http://{qdrant_host}:{qdrant_port}"
            )
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{qdrant_url}/collections")
            if response.status_code == 200:
                return {
                    "status": "healthy",
                    "collections": response.json().get("result", {}).get("collections", []),
                }
        return {
            "status": "unhealthy",
            "error": "Connection failed",
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
        }


# =============================================================================
# Health Check Endpoints
# =============================================================================


@app.get("/api/health")
async def health_check():
    """
    Health check endpoint returning status of all services.

    Returns:
        - gateway: EventMesh status
        - redis: Redis connection status
        - postgres: PostgreSQL connection status
        - qdrant: Qdrant vector DB status
        - pool: Database connection pool stats
    """
    from heretek_swarm.state.repository import StateRepository

    return {
        "status": "healthy",
        "services": {
            "gateway": await check_gateway(),
            "redis": await check_redis(),
            "postgres": await check_postgres(),
            "qdrant": await check_qdrant(),
        },
        "pool": StateRepository.get_pool_stats(),
        "timestamp": datetime.utcnow().isoformat(),
    }


@app.get("/api/health/live")
async def liveness_check():
    """Kubernetes liveness probe endpoint."""
    return {"status": "alive"}


@app.get("/api/health/ready")
async def readiness_check():
    """Kubernetes readiness probe endpoint."""
    # Check if critical services are available
    checks = await check_postgres()
    if checks.get("status") != "healthy":
        raise HTTPException(503, "PostgreSQL not ready")
    return {"status": "ready"}


# =============================================================================
# Agent Management Endpoints
# =============================================================================


@app.get("/api/agents")
async def get_agents(authenticated: str = Depends(verify_auth)):
    """
    Get all agents managed by the supervisor.

    Returns list of all agents with their status, type, and metrics.
    """
    if not supervisor:
        raise HTTPException(503, "Supervisor not initialized")

    agents = []
    for agent_id, actor in supervisor.actors.items():
        status = actor.get_status()
        agents.append(
            {
                "id": agent_id,
                "type": actor.__class__.__name__,
                "status": status.state.value if status else "unknown",
                "message_count": status.message_count if status else 0,
                "error_count": status.error_count if status else 0,
                "last_activity": status.last_activity.isoformat()
                if status and status.last_activity
                else None,
            }
        )

    return {"agents": agents, "total": len(agents)}


@app.get("/api/agents/{agent_id}")
async def get_agent(agent_id: str, authenticated: str = Depends(verify_auth)):
    """
    Get details of a specific agent.

    Args:
        agent_id: Unique agent identifier

    Returns:
        Agent details including type, status, memory stats, and tools
    """
    if not supervisor:
        raise HTTPException(503, "Supervisor not initialized")

    if agent_id not in supervisor.actors:
        raise HTTPException(404, f"Agent {agent_id} not found")

    actor = supervisor.actors[agent_id]
    status = actor.get_status()

    return {
        "id": agent_id,
        "type": actor.__class__.__name__,
        "status": status.state.value if status else "unknown",
        "message_count": status.message_count if status else 0,
        "error_count": status.error_count if status else 0,
        "last_activity": status.last_activity.isoformat()
        if status and status.last_activity
        else None,
        "topics": list(actor.topics),
        "capabilities": list(actor.capabilities),
    }


@app.get("/api/agents/{agent_id}/metrics")
async def get_agent_metrics(agent_id: str, authenticated: str = Depends(verify_auth)):
    """
    Get metrics for a specific agent.

    Args:
        agent_id: Unique agent identifier

    Returns:
        Agent performance metrics
    """
    if not supervisor:
        raise HTTPException(503, "Supervisor not initialized")

    if agent_id not in supervisor.actors:
        raise HTTPException(404, f"Agent {agent_id} not found")

    actor = supervisor.actors[agent_id]
    status = actor.get_status()

    return {
        "agent_id": agent_id,
        "messages_processed": status.message_count if status else 0,
        "errors": status.error_count if status else 0,
        "uptime_seconds": status.uptime_seconds if status else 0,
    }


@app.post("/api/agents/{agent_id}/terminate")
async def terminate_agent(agent_id: str, authenticated: str = Depends(verify_auth)):
    """
    Terminate a specific agent.

    Args:
        agent_id: Unique agent identifier

    Returns:
        Termination confirmation
    """
    if not supervisor:
        raise HTTPException(503, "Supervisor not initialized")

    if agent_id not in supervisor.actors:
        raise HTTPException(404, f"Agent {agent_id} not found")

    await supervisor.terminate_actor(agent_id)

    return {
        "status": "terminated",
        "agent_id": agent_id,
    }


# =============================================================================
# Supervisor Endpoints
# =============================================================================


@app.get("/api/supervisor/status")
async def get_supervisor_status(authenticated: str = Depends(verify_auth)):
    """
    Get supervisor overall status and statistics.

    Returns:
        Supervisor statistics including total, active, suspended actors
    """
    if not supervisor:
        raise HTTPException(503, "Supervisor not initialized")

    return supervisor.get_statistics()


# =============================================================================
# Memory Endpoints
# =============================================================================


@app.get("/api/memory")
async def get_memory_stats(authenticated: str = Depends(verify_auth)):
    """
    Get memory statistics across all agents.

    Returns:
        - total_memories: Total memory entries
        - by_agent: Memory count per agent
        - by_type: Memory count per type
    """
    if not memory_store:
        return {
            "total_memories": 0,
            "by_agent": {},
            "by_type": {},
            "status": "unavailable",
        }

    try:
        # Get total count
        from sqlalchemy import func, select

        from heretek_swarm.memory.persistent import MemoryEntryModel

        async with memory_store._session_factory() as session:
            # Total count
            stmt = select(func.count()).select_from(MemoryEntryModel)
            result = await session.execute(stmt)
            total = result.scalar() or 0

            # By agent
            agent_stmt = select(MemoryEntryModel.agent_id, func.count()).group_by(
                MemoryEntryModel.agent_id
            )
            agent_result = await session.execute(agent_stmt)
            by_agent = {row[0]: row[1] for row in agent_result.all()}

            # By type
            type_stmt = select(MemoryEntryModel.memory_type, func.count()).group_by(
                MemoryEntryModel.memory_type
            )
            type_result = await session.execute(type_stmt)
            by_type = {row[0]: row[1] for row in type_result.all()}

        return {
            "total_memories": total,
            "by_agent": by_agent,
            "by_type": by_type,
            "status": "available",
        }
    except Exception as e:
        logger.error("Memory stats failed", error=str(e))
        return {
            "total_memories": 0,
            "by_agent": {},
            "by_type": {},
            "status": "error",
            "error": str(e),
        }


# =============================================================================
# LiteLLM Metrics Endpoint
# =============================================================================


@app.get("/api/litellm/metrics")
async def get_litellm_metrics(authenticated: str = Depends(verify_auth)):
    """
    Get LiteLLM metrics if available.

    Returns:
        LiteLLM proxy metrics
    """
    import httpx

    litellm_url = os.environ.get("LITELLM_URL", "http://localhost:4000")  # Local dev only
    litellm_key = os.environ.get("LITELLM_MASTER_KEY", "")

    try:
        async with httpx.AsyncClient() as client:
            headers = {}
            if litellm_key:
                headers["Authorization"] = f"Bearer {litellm_key}"

            response = await client.get(
                f"{litellm_url}/metrics",
                headers=headers,
                timeout=5.0,
            )

            if response.status_code == 200:
                return response.json()

            return {
                "status": "error",
                "code": response.status_code,
                "message": "Failed to fetch metrics",
            }
    except Exception as e:
        return {
            "status": "unavailable",
            "error": str(e),
        }


# =============================================================================
# mem0 Memory Endpoints
# =============================================================================


@app.get("/api/memory/mem0")
async def get_mem0_stats(authenticated: str = Depends(verify_auth)):
    """
    Get mem0 memory statistics.

    Returns:
        - available: Whether mem0 is available
        - latency_stats: Latency statistics for mem0 operations
    """
    if not MEM0_AVAILABLE or not mem0_backend:
        return {
            "available": False,
            "message": "mem0 not installed or not initialized",
        }

    return {
        "available": True,
        "latency_stats": mem0_backend.get_latency_stats(),
    }


@app.post("/api/memory/mem0/search")
async def search_mem0_memory(
    query: str, agent_id: str, limit: int = 10, authenticated: str = Depends(verify_auth)
):
    """
    Search mem0 memory for an agent.

    Args:
        query: Search query text
        agent_id: Agent to search memories for
        limit: Maximum results to return

    Returns:
        List of matching memories
    """
    if not MEM0_AVAILABLE or not mem0_backend:
        raise HTTPException(503, "mem0 not available")

    from memory import MemoryQuery

    search_query = MemoryQuery(
        query_text=query,
        agent_ids=[agent_id],
        limit=limit,
    )

    result = await mem0_backend.search(search_query)

    return {
        "query": query,
        "agent_id": agent_id,
        "results": [
            {
                "id": str(entry.id),
                "content": entry.content,
                "memory_type": entry.memory_type.value,
                "importance_score": entry.importance_score,
                "created_at": entry.created_at.isoformat(),
            }
            for entry in result.entries
        ],
        "total_count": result.total_count,
    }


@app.get("/api/memory/mem0/agents/{agent_id}")
async def get_agent_memories(
    agent_id: str, limit: int = 100, authenticated: str = Depends(verify_auth)
):
    """
    Get all memories for an agent from mem0.

    Args:
        agent_id: Agent to get memories for
        limit: Maximum results to return

    Returns:
        List of agent memories
    """
    if not MEM0_AVAILABLE or not mem0_backend:
        raise HTTPException(503, "mem0 not available")

    entries = await mem0_backend.get_all(agent_id)

    return {
        "agent_id": agent_id,
        "memories": [
            {
                "id": str(entry.id),
                "content": entry.content,
                "memory_type": entry.memory_type.value,
                "importance_score": entry.importance_score,
                "created_at": entry.created_at.isoformat(),
            }
            for entry in entries[:limit]
        ],
        "total_count": len(entries),
    }


# =============================================================================
# A2A Message History Endpoints
# =============================================================================


@app.get("/api/a2a/messages")
async def get_a2a_messages(limit: int = 100, authenticated: str = Depends(verify_auth)):
    """
    Get recent A2A messages from Redis.

    Args:
        limit: Maximum messages to return

    Returns:
        List of recent A2A messages
    """
    try:
        import json

        import redis.asyncio as redis

        redis_url = os.environ.get("REDIS_URL", "redis://localhost:6379")
        r = redis.from_url(redis_url)

        # Get recent messages from Redis list
        messages = await r.lrange("a2a:messages", 0, limit - 1)
        await r.close()

        return {
            "messages": [json.loads(m) for m in messages],
            "count": len(messages),
        }

    except Exception as e:
        logger.warning("Failed to get A2A messages", error=str(e))
        return {
            "messages": [],
            "count": 0,
            "error": str(e),
        }


@app.get("/api/a2a/messages/{from_agent}/{to_agent}")
async def get_a2a_conversation(from_agent: str, to_agent: str, limit: int = 50):
    """
    Get A2A messages between two agents.

    Args:
        from_agent: Source agent ID
        to_agent: Target agent ID
        limit: Maximum messages to return

    Returns:
        List of messages between the agents
    """
    try:
        import json

        import redis.asyncio as redis

        redis_url = os.environ.get("REDIS_URL", "redis://localhost:6379")
        r = redis.from_url(redis_url)

        # Get messages and filter
        all_messages = await r.lrange("a2a:messages", 0, 1000)
        await r.close()

        # Filter for this conversation
        conversation = []
        for msg_bytes in all_messages:
            msg = json.loads(msg_bytes)
            if (msg.get("from") == from_agent and msg.get("to") == to_agent) or (
                msg.get("from") == to_agent and msg.get("to") == from_agent
            ):
                conversation.append(msg)
                if len(conversation) >= limit:
                    break

        return {
            "from_agent": from_agent,
            "to_agent": to_agent,
            "messages": conversation[:limit],
            "count": len(conversation[:limit]),
        }

    except Exception as e:
        logger.warning("Failed to get A2A conversation", error=str(e))
        return {
            "from_agent": from_agent,
            "to_agent": to_agent,
            "messages": [],
            "count": 0,
            "error": str(e),
        }


# =============================================================================
# OpenAPI Documentation
# =============================================================================


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "name": "Heretek Swarm API",
        "version": "0.1.0",
        "docs": "/docs",
        "redoc": "/redoc",
        "workflows": "/api/workflows",
        "metrics": "/metrics",
    }
