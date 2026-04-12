"""
Agent Management API Endpoints.

This module provides REST API endpoints for agent lifecycle management.
Delegated to submodules:
- agents/core.py: Agent type discovery and deployment
- agents/lifecycle.py: Agent lifecycle control (start, stop, suspend, resume)
- agents/instances.py: Agent instances, logs, stats, and channels
- agents/routing.py: Routing rules and behavior profiling
- agents/jetstream.py: JetStream stream management
"""

from fastapi import APIRouter

from heretek_swarm.api.agents.core import router as core_router
from heretek_swarm.api.agents.lifecycle import router as lifecycle_router
from heretek_swarm.api.agents.instances import router as instances_router
from heretek_swarm.api.agents.routing import router as routing_router
from heretek_swarm.api.agents.jetstream import router as jetstream_router

router = APIRouter(prefix="/api/agents", tags=["agents-management"])

# Include all sub-routers
router.include_router(core_router)
router.include_router(lifecycle_router)
router.include_router(instances_router)
router.include_router(routing_router)
router.include_router(jetstream_router)
