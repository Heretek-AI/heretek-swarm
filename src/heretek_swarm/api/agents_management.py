"""
Agent Management API Endpoints.

This module provides REST API endpoints for agent lifecycle management:
- GET /api/agents/available - List all available agent types
- POST /api/agents/deploy - Deploy a new agent instance
- DELETE /api/agents/{id} - Remove an agent instance
- POST /api/agents/{id}/start - Start an agent
- POST /api/agents/{id}/stop - Stop an agent
- POST /api/agents/{id}/suspend - Suspend an agent
- POST /api/agents/{id}/resume - Resume an agent
- PUT /api/agents/{id}/config - Update agent configuration
- GET /api/agents/{id}/logs - Get agent-specific logs
"""

import asyncio
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Depends
import structlog

from heretek_swarm.gateway.auth import verify_auth
from heretek_swarm.runtime.registry_enhanced import (
    get_enhanced_registry,
    EnhancedAgentRegistry,
    AgentLifecycleState,
)

logger = structlog.get_logger("api.agents_management")

router = APIRouter(prefix="/api/agents", tags=["agents-management"])


def get_registry() -> EnhancedAgentRegistry:
    """Dependency to get the enhanced registry."""
    return get_enhanced_registry()


# =============================================================================
# Agent Type Discovery Endpoints
# =============================================================================


@router.get("/available")
async def list_available_agents(
    registry: EnhancedAgentRegistry = Depends(get_registry),
    authenticated: str = Depends(verify_auth),
):
    """
    List all available agent types that can be deployed.
    
    Returns metadata about each agent type including:
    - Type name and description
    - Capabilities
    - Default topics
    - Configuration schema
    """
    try:
        agent_types = registry.get_available_agents()
        
        return {
            "available_agents": [
                {
                    "type_name": agent.type_name,
                    "module_path": agent.module_path,
                    "description": agent.description,
                    "capabilities": agent.capabilities,
                    "topics": agent.topics,
                    "config_schema": agent.config_schema,
                    "actor_type": agent.actor_type,
                }
                for agent in agent_types
            ],
            "total": len(agent_types),
        }
    except Exception as e:
        logger.error(f"Failed to list available agents: {e}", exc_info=True)
        raise HTTPException(500, f"Failed to list available agents: {str(e)}")


@router.get("/types/{agent_type}")
async def get_agent_type_metadata(
    agent_type: str,
    registry: EnhancedAgentRegistry = Depends(get_registry),
    authenticated: str = Depends(verify_auth),
):
    """
    Get metadata for a specific agent type.
    
    Args:
        agent_type: Agent type name
    """
    metadata = registry.get_agent_metadata(agent_type)
    
    if not metadata:
        raise HTTPException(404, f"Agent type '{agent_type}' not found")
    
    return {
        "type_name": metadata.type_name,
        "module_path": metadata.module_path,
        "description": metadata.description,
        "capabilities": metadata.capabilities,
        "topics": metadata.topics,
        "config_schema": metadata.config_schema,
        "actor_type": metadata.actor_type,
    }


# =============================================================================
# Agent Deployment Endpoints
# =============================================================================


@router.post("/deploy")
async def deploy_agent(
    agent_type: str,
    config: Optional[Dict[str, Any]] = None,
    instance_id: Optional[str] = None,
    registry: EnhancedAgentRegistry = Depends(get_registry),
    authenticated: str = Depends(verify_auth),
):
    """
    Deploy a new agent instance.
    
    Args:
        agent_type: Type of agent to deploy
        config: Optional configuration dictionary
        instance_id: Optional custom instance ID
        
    Returns:
        Deployed agent instance information
    """
    # Validate agent type exists
    metadata = registry.get_agent_metadata(agent_type)
    if not metadata:
        raise HTTPException(400, f"Unknown agent type: {agent_type}")
    
    try:
        # Deploy the agent
        instance = await registry.deploy_agent(
            agent_type=agent_type,
            config=config,
            instance_id=instance_id,
        )
        
        if not instance:
            raise HTTPException(500, "Failed to deploy agent")
        
        return {
            "instance_id": instance.instance_id,
            "agent_type": instance.agent_type,
            "config": instance.config,
            "state": instance.state.value,
            "status": "deployed",
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to deploy agent: {e}", exc_info=True)
        raise HTTPException(500, f"Failed to deploy agent: {str(e)}")


@router.delete("/{instance_id}")
async def remove_agent(
    instance_id: str,
    registry: EnhancedAgentRegistry = Depends(get_registry),
    authenticated: str = Depends(verify_auth),
):
    """
    Remove an agent instance.
    
    Args:
        instance_id: Instance ID to remove
    """
    instance = registry.get_instance(instance_id)
    if not instance:
        raise HTTPException(404, f"Agent instance '{instance_id}' not found")
    
    try:
        success = await registry.remove_agent(instance_id)
        
        if not success:
            raise HTTPException(500, "Failed to remove agent")
        
        return {
            "instance_id": instance_id,
            "status": "removed",
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to remove agent: {e}", exc_info=True)
        raise HTTPException(500, f"Failed to remove agent: {str(e)}")


# =============================================================================
# Agent Lifecycle Control Endpoints
# =============================================================================


@router.post("/{instance_id}/start")
async def start_agent(
    instance_id: str,
    registry: EnhancedAgentRegistry = Depends(get_registry),
    authenticated: str = Depends(verify_auth),
):
    """
    Start a deployed agent instance.
    
    Args:
        instance_id: Instance ID to start
    """
    instance = registry.get_instance(instance_id)
    if not instance:
        raise HTTPException(404, f"Agent instance '{instance_id}' not found")
    
    try:
        success = await registry.start_agent(instance_id)
        
        if not success:
            raise HTTPException(500, "Failed to start agent")
        
        return {
            "instance_id": instance_id,
            "status": "running",
            "state": AgentLifecycleState.RUNNING.value,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to start agent: {e}", exc_info=True)
        raise HTTPException(500, f"Failed to start agent: {str(e)}")


@router.post("/{instance_id}/stop")
async def stop_agent(
    instance_id: str,
    registry: EnhancedAgentRegistry = Depends(get_registry),
    authenticated: str = Depends(verify_auth),
):
    """
    Stop a running agent instance.
    
    Args:
        instance_id: Instance ID to stop
    """
    instance = registry.get_instance(instance_id)
    if not instance:
        raise HTTPException(404, f"Agent instance '{instance_id}' not found")
    
    try:
        success = await registry.stop_agent(instance_id)
        
        if not success:
            raise HTTPException(500, "Failed to stop agent")
        
        return {
            "instance_id": instance_id,
            "status": "stopped",
            "state": AgentLifecycleState.STOPPED.value,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to stop agent: {e}", exc_info=True)
        raise HTTPException(500, f"Failed to stop agent: {str(e)}")


@router.post("/{instance_id}/suspend")
async def suspend_agent(
    instance_id: str,
    registry: EnhancedAgentRegistry = Depends(get_registry),
    authenticated: str = Depends(verify_auth),
):
    """
    Suspend a running agent instance.
    
    Args:
        instance_id: Instance ID to suspend
    """
    instance = registry.get_instance(instance_id)
    if not instance:
        raise HTTPException(404, f"Agent instance '{instance_id}' not found")
    
    try:
        success = await registry.suspend_agent(instance_id)
        
        if not success:
            raise HTTPException(500, "Failed to suspend agent")
        
        return {
            "instance_id": instance_id,
            "status": "suspended",
            "state": AgentLifecycleState.SUSPENDED.value,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to suspend agent: {e}", exc_info=True)
        raise HTTPException(500, f"Failed to suspend agent: {str(e)}")


@router.post("/{instance_id}/resume")
async def resume_agent(
    instance_id: str,
    registry: EnhancedAgentRegistry = Depends(get_registry),
    authenticated: str = Depends(verify_auth),
):
    """
    Resume a suspended agent instance.
    
    Args:
        instance_id: Instance ID to resume
    """
    instance = registry.get_instance(instance_id)
    if not instance:
        raise HTTPException(404, f"Agent instance '{instance_id}' not found")
    
    try:
        success = await registry.resume_agent(instance_id)
        
        if not success:
            raise HTTPException(500, "Failed to resume agent")
        
        return {
            "instance_id": instance_id,
            "status": "running",
            "state": AgentLifecycleState.RUNNING.value,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to resume agent: {e}", exc_info=True)
        raise HTTPException(500, f"Failed to resume agent: {str(e)}")


# =============================================================================
# Agent Configuration Endpoints
# =============================================================================


@router.put("/{instance_id}/config")
async def update_agent_config(
    instance_id: str,
    config: Dict[str, Any],
    registry: EnhancedAgentRegistry = Depends(get_registry),
    authenticated: str = Depends(verify_auth),
):
    """
    Update agent configuration.
    
    Args:
        instance_id: Instance ID
        config: New configuration dictionary
    """
    instance = registry.get_instance(instance_id)
    if not instance:
        raise HTTPException(404, f"Agent instance '{instance_id}' not found")
    
    try:
        success = registry.update_agent_config(instance_id, config)
        
        if not success:
            raise HTTPException(500, "Failed to update configuration")
        
        return {
            "instance_id": instance_id,
            "config": instance.config,
            "status": "updated",
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update config: {e}", exc_info=True)
        raise HTTPException(500, f"Failed to update configuration: {str(e)}")


# =============================================================================
# Agent Information Endpoints
# =============================================================================


@router.get("/instances")
async def list_agent_instances(
    agent_type: Optional[str] = None,
    registry: EnhancedAgentRegistry = Depends(get_registry),
    authenticated: str = Depends(verify_auth),
):
    """
    List all deployed agent instances.
    
    Args:
        agent_type: Optional filter by agent type
    """
    try:
        if agent_type:
            instances = registry.get_instances_by_type(agent_type)
        else:
            instances = registry.get_all_instances()
        
        return {
            "instances": [
                {
                    "instance_id": inst.instance_id,
                    "agent_type": inst.agent_type,
                    "state": inst.state.value,
                    "config": inst.config,
                    "has_actor": inst.actor is not None,
                }
                for inst in instances
            ],
            "total": len(instances),
        }
    except Exception as e:
        logger.error(f"Failed to list instances: {e}", exc_info=True)
        raise HTTPException(500, f"Failed to list instances: {str(e)}")


@router.get("/{instance_id}")
async def get_agent_instance(
    instance_id: str,
    registry: EnhancedAgentRegistry = Depends(get_registry),
    authenticated: str = Depends(verify_auth),
):
    """
    Get details of a specific agent instance.
    
    Args:
        instance_id: Instance ID
    """
    instance = registry.get_instance(instance_id)
    if not instance:
        raise HTTPException(404, f"Agent instance '{instance_id}' not found")
    
    # Get actor status if running
    actor_status = None
    if instance.actor:
        try:
            status = instance.actor.get_status()
            actor_status = {
                "agent_id": status.agent_id,
                "state": status.state.value,
                "message_count": status.message_count,
                "error_count": status.error_count,
                "mailbox_size": status.mailbox_size,
                "last_activity": status.last_activity,
            }
        except Exception as e:
            logger.warning(f"Failed to get actor status: {e}")
    
    return {
        "instance_id": instance.instance_id,
        "agent_type": instance.agent_type,
        "state": instance.state.value,
        "config": instance.config,
        "metadata": {
            "type_name": instance.metadata.type_name if instance.metadata else None,
            "description": instance.metadata.description if instance.metadata else None,
            "capabilities": instance.metadata.capabilities if instance.metadata else None,
        } if instance.metadata else None,
        "actor_status": actor_status,
    }


@router.get("/{instance_id}/logs")
async def get_agent_logs(
    instance_id: str,
    limit: int = 100,
    registry: EnhancedAgentRegistry = Depends(get_registry),
    authenticated: str = Depends(verify_auth),
):
    """
    Get agent-specific logs.
    
    Note: This is a placeholder implementation. In production, this would
    integrate with a logging system like ELK stack or similar.
    
    Args:
        instance_id: Instance ID
        limit: Maximum log entries to return
    """
    instance = registry.get_instance(instance_id)
    if not instance:
        raise HTTPException(404, f"Agent instance '{instance_id}' not found")
    
    # Placeholder: Return agent state information as "logs"
    # In production, this would query a logging system
    logs = []
    
    # Add lifecycle events
    logs.append({
        "timestamp": instance.config.get("created_at", "unknown"),
        "level": "info",
        "message": f"Agent instance {instance_id} deployed",
        "agent_type": instance.agent_type,
    })
    
    if instance.actor:
        try:
            status = instance.actor.get_status()
            logs.append({
                "timestamp": status.last_activity or "unknown",
                "level": "info",
                "message": f"Agent processed {status.message_count} messages",
                "message_count": status.message_count,
                "error_count": status.error_count,
            })
        except Exception:
            pass
    
    # Sort by timestamp (newest first) and limit
    logs = sorted(logs, key=lambda x: x.get("timestamp", ""), reverse=True)[:limit]
    
    return {
        "instance_id": instance_id,
        "logs": logs,
        "total": len(logs),
    }


# =============================================================================
# Registry Statistics Endpoint
# =============================================================================


@router.get("/stats")
async def get_registry_stats(
    registry: EnhancedAgentRegistry = Depends(get_registry),
    authenticated: str = Depends(verify_auth),
):
    """
    Get registry statistics.
    
    Returns statistics about agent types and instances.
    """
    try:
        stats = registry.get_registry_stats()
        return stats
    except Exception as e:
        logger.error(f"Failed to get registry stats: {e}", exc_info=True)
        raise HTTPException(500, f"Failed to get registry stats: {str(e)}")
