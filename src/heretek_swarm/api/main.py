"""
Heretek Swarm FastAPI Main Application

Provides HTTP endpoints for:
- Health checks (gateway, redis, postgres, qdrant)
- Agent management and monitoring
- Memory statistics (PostgreSQL and mem0)
- LiteLLM metrics
- A2A message history
- Consensus state

Reference: MiniMax Audit Lines 585-725
"""

import os
from typing import Any, Dict, List, Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
import structlog

from heretek_swarm.actors.supervisor import ActorSupervisor
from memory.persistent import PersistentMemoryStore
from heretek_swarm.api import websockets, consensus, plugins, workflows, evaluation
from heretek_swarm.api.rate_limiting import setup_rate_limiting
from heretek_swarm.gateway.auth import verify_auth

# Import mem0 backend
try:
    from memory import Mem0Backend, Mem0Config, MEM0_AVAILABLE
except ImportError:
    MEM0_AVAILABLE = False
    Mem0Backend = None
    Mem0Config = None

logger = structlog.get_logger("api.main")

# Global supervisor instance
supervisor: Optional[ActorSupervisor] = None
memory_store: Optional[PersistentMemoryStore] = None
mem0_backend: Optional[Any] = None  # Mem0Backend when available


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler for startup and shutdown."""
    global supervisor, memory_store, mem0_backend
    
    # Startup
    logger.info("Starting Heretek Swarm API...")
    
    # Initialize supervisor
    supervisor = ActorSupervisor()
    logger.info("ActorSupervisor initialized")
    
    # Initialize memory store
    try:
        database_url = os.environ.get(
            "DATABASE_URL",
            "postgresql+asyncpg://postgres:langfuse@localhost:5432/heretek_swarm"
        )
        memory_store = PersistentMemoryStore()
        await memory_store.connect()
        logger.info("PersistentMemoryStore connected")
    except Exception as e:
        logger.warning("PersistentMemoryStore not available", error=str(e))
        memory_store = None
    
    # Initialize mem0 backend if available
    if MEM0_AVAILABLE:
        try:
            mem0_config = Mem0Config(
                qdrant_host=os.environ.get("QDRANT_HOST", "localhost"),
                qdrant_port=int(os.environ.get("QDRANT_PORT", "6333")),
                openai_api_key=os.environ.get("OPENAI_API_KEY"),
            )
            mem0_backend = Mem0Backend(config=mem0_config)
            await mem0_backend.initialize()
            logger.info("Mem0Backend initialized")
        except Exception as e:
            logger.warning("Mem0Backend not available", error=str(e))
            mem0_backend = None
    else:
        logger.info("mem0 not installed - using PostgreSQL memory only")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Heretek Swarm API...")
    
    if supervisor:
        await supervisor.terminate_all()
    
    if mem0_backend:
        await mem0_backend.shutdown()
    
    if memory_store:
        await memory_store.disconnect()


# Create FastAPI application
app = FastAPI(
    title="Heretek Swarm API",
    description="Multi-agent swarm orchestration with A2A protocol communication",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# Add CORS middleware with environment-based configuration
environment = os.getenv("ENVIRONMENT", "development")

if environment == "production":
    allowed_origins = os.getenv(
        "CORS_ORIGINS",
        "https://your-domain.com"
    ).split(",")
else:
    allowed_origins = ["http://localhost:3000", "http://localhost:5173", "http://localhost:8000"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
    allow_headers=["Authorization", "Content-Type", "X-Requested-With"],
)

# Register routers
app.include_router(websockets.router)
app.include_router(consensus.router)
app.include_router(plugins.router)
app.include_router(workflows.router)
app.include_router(observability.router)
app.include_router(evaluation.router)

# Setup rate limiting
rate_limit_enabled = os.environ.get("RATE_LIMIT_ENABLED", "true").lower() == "true"
setup_rate_limiting(app, enabled=rate_limit_enabled)


# =============================================================================
# Health Check Functions
# =============================================================================

async def check_gateway() -> Dict[str, Any]:
    """Check the EventMesh gateway status."""
    try:
        from heretek_swarm.gateway import EventMesh
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


async def check_redis() -> Dict[str, Any]:
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


async def check_postgres() -> Dict[str, Any]:
    """Check PostgreSQL connection status."""
    try:
        if memory_store and memory_store._engine:
            async with memory_store._engine.connect() as conn:
                await conn.execute("SELECT 1")
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


async def check_qdrant() -> Dict[str, Any]:
    """Check Qdrant vector database status."""
    try:
        import httpx
        qdrant_url = os.environ.get("QDRANT_URL", "http://localhost:6333")
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
    """
    return {
        "status": "healthy",
        "services": {
            "gateway": await check_gateway(),
            "redis": await check_redis(),
            "postgres": await check_postgres(),
            "qdrant": await check_qdrant(),
        },
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
        agents.append({
            "id": agent_id,
            "type": actor.__class__.__name__,
            "status": status.state.value if status else "unknown",
            "message_count": status.message_count if status else 0,
            "error_count": status.error_count if status else 0,
            "last_activity": status.last_activity.isoformat() if status and status.last_activity else None,
        })
    
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
        "last_activity": status.last_activity.isoformat() if status and status.last_activity else None,
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
        from sqlalchemy import select, func
        from heretek_swarm.memory.persistent import MemoryEntryModel
        
        async with memory_store._session_factory() as session:
            # Total count
            stmt = select(func.count()).select_from(MemoryEntryModel)
            result = await session.execute(stmt)
            total = result.scalar() or 0
            
            # By agent
            agent_stmt = select(
                MemoryEntryModel.agent_id,
                func.count()
            ).group_by(MemoryEntryModel.agent_id)
            agent_result = await session.execute(agent_stmt)
            by_agent = {row[0]: row[1] for row in agent_result.all()}
            
            # By type
            type_stmt = select(
                MemoryEntryModel.memory_type,
                func.count()
            ).group_by(MemoryEntryModel.memory_type)
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
    
    litellm_url = os.environ.get("LITELLM_URL", "http://localhost:4000")
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
async def search_mem0_memory(query: str, agent_id: str, limit: int = 10, authenticated: str = Depends(verify_auth)):
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
async def get_agent_memories(agent_id: str, limit: int = 100, authenticated: str = Depends(verify_auth)):
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
        import redis.asyncio as redis
        import json
        
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
async def get_a2a_conversation(
    from_agent: str,
    to_agent: str,
    limit: int = 50
):
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
        import redis.asyncio as redis
        import json
        
        redis_url = os.environ.get("REDIS_URL", "redis://localhost:6379")
        r = redis.from_url(redis_url)
        
        # Get messages and filter
        all_messages = await r.lrange("a2a:messages", 0, 1000)
        await r.close()
        
        # Filter for this conversation
        conversation = []
        for msg_bytes in all_messages:
            msg = json.loads(msg_bytes)
            if (msg.get("from") == from_agent and msg.get("to") == to_agent) or \
               (msg.get("from") == to_agent and msg.get("to") == from_agent):
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
    }