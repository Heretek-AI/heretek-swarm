"""
Supervisor-based agent endpoints.

Provides 4 routes mirroring the current main.py agent management endpoints:
- GET  /              → list all supervisor-managed actors
- GET  /{agent_id}    → get agent detail from supervisor.actors
- GET  /{agent_id}/metrics    → get agent performance metrics
- POST /{agent_id}/terminate  → terminate an agent

All routes use lazy import of get_supervisor() to avoid circular imports
(main.py → agents_management → supervisor → get_supervisor from actors.supervisor).

F-009 (2026-06-01 cold-start validation): the {agent_id} path is constrained
by a positive allow-list regex (the 23 valid agent IDs). A negative-lookahead
exclusion list was tried first but pydantic_core's regex engine (Rust regex
crate) does not support look-around. The allow-list has the same effect: it
restricts /{agent_id} to the 23 known agent IDs so that reserved literal
segments (instances, available, types, deploy, chat, jetstream, profiling,
routing_rules, routing_control, metrics, terminate) fall through to the
sub-routers that own them. If a new agent type is added to
heretek_swarm.actors, this allow-list must be updated to match.
"""

from datetime import UTC, datetime
from typing import Annotated

import structlog
from fastapi import APIRouter, Depends, HTTPException, Path

from heretek_swarm.gateway.auth import verify_auth

logger = structlog.get_logger(__name__)

# Positive allow-list of the 23 valid agent IDs that supervisor.actors can
# contain. This drives the path-constraint regex below; reserved literal
# segments owned by sibling sub-routers (instances, available, types, etc.)
# are intentionally absent so requests to those segments fall through.
VALID_AGENT_IDS = frozenset(
    {
        "alpha",
        "arbiter",
        "beta",
        "catalyst",
        "charlie",
        "chronos",
        "coder",
        "coordinator",
        "dreamer",
        "echo",
        "empath",
        "examiner",
        "explorer",
        "habit-forge",
        "historian",
        "metis",
        "nexus",
        "perceiver",
        "perceiver-plus",
        "prism",
        "sentinel",
        "sentinel-prime",
        "steward",
    }
)

# Alternation regex matching ONLY the 23 valid agent IDs. No look-around
# (pydantic_core's Rust regex engine does not support it). The end-anchor
# ($) is what actually prevents partial matches: ^sentinel$ will not match
# "sentinel-prime" because the input has trailing characters after "sentinel".
AGENT_ID_PATTERN = r"^(" + "|".join(sorted(VALID_AGENT_IDS)) + r")$"

router = APIRouter()


def _uptime_seconds(created_at: str) -> float:
    """Compute uptime in seconds from an ISO-8601 created_at timestamp."""
    try:
        created = datetime.fromisoformat(created_at)
        now = datetime.now(UTC)
        return (now - created).total_seconds()
    except (ValueError, TypeError):
        return 0.0


@router.get("/")
async def list_supervisor_agents(authenticated: str = Depends(verify_auth)):
    """
    List all agents managed by the supervisor.

    Returns:
        {agents: [...], total: N}
    """
    from heretek_swarm.actors.supervisor import get_supervisor

    supervisor = get_supervisor()
    if not supervisor or not supervisor.actors:
        return {"agents": [], "total": 0}

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
                "last_activity": (
                    status.last_activity if status and status.last_activity else None
                ),
            }
        )

    return {"agents": agents, "total": len(agents)}


@router.get("/{agent_id}")
async def get_supervisor_agent(
    agent_id: Annotated[
        str,
        Path(
            pattern=AGENT_ID_PATTERN,
            description="Agent identifier; must not collide with reserved sub-router literals",
        ),
    ],
    authenticated: str = Depends(verify_auth),
):
    """
    Get details of a specific agent from the supervisor.

    Returns:
        {id, type, status, topics, capabilities, ...}
    """
    from heretek_swarm.actors.supervisor import get_supervisor

    supervisor = get_supervisor()
    if not supervisor or agent_id not in supervisor.actors:
        raise HTTPException(404, f"Agent {agent_id} not found")

    actor = supervisor.actors[agent_id]
    status = actor.get_status()

    return {
        "id": agent_id,
        "type": actor.__class__.__name__,
        "status": status.state.value if status else "unknown",
        "message_count": status.message_count if status else 0,
        "error_count": status.error_count if status else 0,
        "last_activity": (
            status.last_activity if status and status.last_activity else None
        ),
        "topics": list(actor.topics),
        "capabilities": list(actor.capabilities),
    }


@router.get("/{agent_id}/metrics")
async def get_supervisor_agent_metrics(
    agent_id: Annotated[
        str,
        Path(
            pattern=AGENT_ID_PATTERN,
            description="Agent identifier; must not collide with reserved sub-router literals",
        ),
    ],
    authenticated: str = Depends(verify_auth),
):
    """
    Get performance metrics for a specific agent.

    Returns:
        {agent_id, messages_processed, errors, uptime_seconds}
    """
    from heretek_swarm.actors.supervisor import get_supervisor

    supervisor = get_supervisor()
    if not supervisor or agent_id not in supervisor.actors:
        raise HTTPException(404, f"Agent {agent_id} not found")

    actor = supervisor.actors[agent_id]
    status = actor.get_status()

    return {
        "agent_id": agent_id,
        "messages_processed": status.message_count if status else 0,
        "errors": status.error_count if status else 0,
        "uptime_seconds": (
            _uptime_seconds(status.created_at)
            if status and status.created_at
            else 0.0
        ),
    }


@router.post("/{agent_id}/terminate")
async def terminate_supervisor_agent(
    agent_id: Annotated[
        str,
        Path(
            pattern=AGENT_ID_PATTERN,
            description="Agent identifier; must not collide with reserved sub-router literals",
        ),
    ],
    authenticated: str = Depends(verify_auth),
):
    """
    Terminate a specific agent via the supervisor.

    Returns:
        {status: "terminated", agent_id}
    """
    from heretek_swarm.actors.supervisor import get_supervisor

    supervisor = get_supervisor()
    if not supervisor or agent_id not in supervisor.actors:
        raise HTTPException(404, f"Agent {agent_id} not found")

    await supervisor.terminate_actor(agent_id)

    return {
        "status": "terminated",
        "agent_id": agent_id,
    }
