"""
Autonomous Runtime Integration Endpoints.

Provides endpoints for the autonomous runtime to register its agents
and for the frontend to query autonomous agent status.

The autonomous runtime periodically POSTs agent status to this endpoint,
and the frontend queries it via GET.
"""

import asyncio
import math
from datetime import UTC, datetime
from typing import Any

import structlog
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from heretek_swarm.gateway.auth import verify_auth

logger = structlog.get_logger("api.autonomous")

router = APIRouter(
    prefix="/api/autonomous",
    tags=["autonomous"],
    dependencies=[Depends(verify_auth)],
)

# In-memory cache of autonomous agent statuses
# Key: agent_id, Value: status dict with timestamp
_autonomous_agents: dict[str, dict[str, Any]] = {}
_last_update: datetime | None = None
_cache_lock = asyncio.Lock()

# In-memory buffer for analysis records (capped at 1000)
_analysis_records: list[dict[str, Any]] = []
_recents_lock = asyncio.Lock()
MAX_ANALYSIS_RECORDS = 1000


def get_autonomous_agent_count_sync() -> int:
    """Synchronous access to agent count (for use in sync endpoints)."""
    return len(_autonomous_agents)


async def push_analysis_record(record: dict[str, Any]) -> None:
    """
    Push an analysis record into the in-memory buffer.

    Appends the record and trims to MAX_ANALYSIS_RECORDS if the buffer
    exceeds the cap. Records are stored in insertion order so they can
    be served to the frontend via GET /api/autonomous/analyses.

    Args:
        record: Structured analysis record dict with keys:
            id, collected_at, trigger_type, metis_analyses,
            empath_responses, chronos_actions, mediation_dispatched
    """
    global _analysis_records
    async with _recents_lock:
        _analysis_records.append(record)
        if len(_analysis_records) > MAX_ANALYSIS_RECORDS:
            _analysis_records[:] = _analysis_records[-MAX_ANALYSIS_RECORDS:]
    logger.debug("analysis_record_stored", id=record.get("id"))


class AutonomousAgentStatus(BaseModel):
    """Agent status from the autonomous runtime."""

    agent_id: str
    agent_type: str
    state: str
    message_count: int = 0
    error_count: int = 0
    mailbox_size: int = 0
    last_activity: str | None = None
    uptime_seconds: float = 0.0


class AutonomousStatusUpdate(BaseModel):
    """Request model for autonomous runtime status updates."""

    runtime_id: str
    agents: list[AutonomousAgentStatus]
    total_agents: int
    uptime_seconds: float = 0.0


class AnalysisRecordResponse(BaseModel):
    """Response model for a single analysis record."""

    id: str
    collected_at: str
    trigger_type: str | None = None
    metis_analyses: list[dict] = []
    empath_responses: list[dict] = []
    chronos_actions: list[dict] = []
    mediation_dispatched: bool = False


class AnalysisListResponse(BaseModel):
    """Response model for paginated analysis list."""

    items: list[AnalysisRecordResponse]
    total: int
    page: int
    limit: int
    pages: int


class AutonomousAgentsResponse(BaseModel):
    """Response model for autonomous agents query."""

    agents: list[AutonomousAgentStatus]
    total: int
    last_update: str | None
    healthy: bool


@router.post("/agents", status_code=200)
async def register_autonomous_agents(
    update: AutonomousStatusUpdate,
) -> dict[str, str]:
    """
    Receive agent status update from autonomous runtime.

    The autonomous runtime calls this endpoint periodically to register
    its running agents. This data is cached and served to the frontend.

    Args:
        update: Status update from autonomous runtime
    """
    global _autonomous_agents, _last_update

    async with _cache_lock:
        _autonomous_agents = {agent.agent_id: agent.model_dump() for agent in update.agents}
        _last_update = datetime.now(UTC)

    logger.debug(
        "autonomous_agents_registered",
        runtime_id=update.runtime_id,
        agent_count=update.total_agents,
    )

    return {"status": "ok", "agents": str(update.total_agents)}


@router.get("/agents")
async def get_autonomous_agents() -> AutonomousAgentsResponse:
    """
    Get current autonomous agent statuses.

    Returns the cached list of agents running in the autonomous runtime.
    This is queried by the frontend to display agent health.

    Returns:
        List of autonomous agents with their statuses
    """
    async with _cache_lock:
        agents = list(_autonomous_agents.values())
        total = len(agents)

    # Determine health: agents are healthy if we have data less than 2 minutes old
    healthy = True
    if _last_update:
        age = (datetime.now(UTC) - _last_update).total_seconds()
        healthy = age < 120

    return AutonomousAgentsResponse(
        agents=[AutonomousAgentStatus(**a) for a in agents],
        total=total,
        last_update=_last_update.isoformat() if _last_update else None,
        healthy=healthy,
    )


@router.get("/analyses")
async def get_analyses(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
) -> AnalysisListResponse:
    """
    Get paginated analysis history.

    Returns analysis records sorted by recency (most recent first).
    This is the main frontend entry point for viewing analysis history.

    Args:
        page: Page number (1-indexed)
        limit: Records per page (max 100)
    """
    async with _recents_lock:
        snapshot = list(reversed(_analysis_records))

    total = len(snapshot)
    pages = math.ceil(total / limit) if total > 0 else 1
    start = (page - 1) * limit
    items = snapshot[start : start + limit]

    return AnalysisListResponse(
        items=[AnalysisRecordResponse(**r) for r in items],
        total=total,
        page=page,
        limit=limit,
        pages=pages,
    )


@router.get("/analyses/{analysis_id}")
async def get_analysis_by_id(analysis_id: str) -> AnalysisRecordResponse:
    """
    Get a single analysis record by its ID.

    Args:
        analysis_id: UUID of the analysis record

    Raises:
        HTTPException 404 if not found
    """
    async with _recents_lock:
        for record in _analysis_records:
            if record.get("id") == analysis_id:
                return AnalysisRecordResponse(**record)
    raise HTTPException(status_code=404, detail="Analysis not found")


@router.get("/status")
async def get_autonomous_status() -> dict[str, Any]:
    """
    Get autonomous runtime status.

    Returns basic status about the autonomous runtime connection
    and analysis record count.
    """
    async with _cache_lock:
        agent_count = len(_autonomous_agents)
    async with _recents_lock:
        total_analyses = len(_analysis_records)

    return {
        "connected": _last_update is not None,
        "agent_count": agent_count,
        "last_update": _last_update.isoformat() if _last_update else None,
        "total_analyses": total_analyses,
    }
