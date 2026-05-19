"""
Agent Management API Endpoints.

This module provides REST API endpoints for agent lifecycle management,
delegating to submodules for each functional area.

Submodules:
- chat: Chat messaging via triad deliberation
- core: Agent type discovery and deployment
- lifecycle: Agent start/stop/suspend/resume
- instances: Agent instance management
- jetstream: JetStream stream management
- profiling: Behavior profiling endpoints
- routing_rules: Content routing rules
- routing_control: Routing rule control (enable/disable)
- supervisor: Supervisor-based agent management (wins GET /{param} path collision)
"""

import structlog
from fastapi import APIRouter

from heretek_swarm.api.agents import (
    chat,
    core,
    instances,
    jetstream,
    lifecycle,
    profiling,
    routing_control,
    routing_rules,
    supervisor,
)

logger = structlog.get_logger()

router = APIRouter(prefix="/api/agents")

# Include routers from submodules
# Supervisor must be first to win the GET /{param} path collision
router.include_router(supervisor.router, tags=["supervisor"])
router.include_router(chat.router, tags=["chat"])
router.include_router(core.router, tags=["core"])
router.include_router(lifecycle.router, tags=["lifecycle"])
router.include_router(instances.router, tags=["instances"])
router.include_router(jetstream.router, tags=["jetstream"])
router.include_router(profiling.router, tags=["profiling"])
router.include_router(routing_rules.router, tags=["routing_rules"])
router.include_router(routing_control.router, tags=["routing_control"])
