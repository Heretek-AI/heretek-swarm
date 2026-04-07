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
- GET /api/agents/{id}/channels - Get agent channel subscriptions
- POST /api/agents/{id}/channels - Add channel subscription
- DELETE /api/agents/{id}/channels/{channelName} - Remove channel subscription

Enhanced with Behavior Profiling:
- GET /api/agents/{id}/profiling/metrics - Get agent behavior metrics
- GET /api/agents/{id}/profiling/profile - Get agent behavior profile
- GET /api/agents/{id}/profiling/anomalies - Detect anomalies
- GET /api/agents/profiling/alerts - Get all alerts
- POST /api/agents/profiling/alerts/{index}/acknowledge - Acknowledge alert
- GET /api/agents/profiling/stats - Get profiler statistics
- GET /api/agents/profiling/prometheus - Prometheus metrics export
"""

import asyncio
from dataclasses import field
from typing import Any, Dict, List, Optional
from datetime import datetime, timezone
from enum import Enum
from pydantic import BaseModel, Field

from fastapi import APIRouter, HTTPException, Depends
import structlog

from heretek_swarm.gateway.auth import verify_auth
from heretek_swarm.runtime.registry_enhanced import (
    get_enhanced_registry,
    EnhancedAgentRegistry,
    AgentLifecycleState,
)
from heretek_swarm.channels.registry import ChannelRegistry, get_channel_registry
from heretek_swarm.gateway.content_router import (
    ContentRouter,
    get_content_router,
    RoutingRule,
    ContentFilter,
    FilterOperator,
)

# Import behavior profiling
try:
    from heretek_swarm.actors.profiling import (
        BehaviorProfiler,
        ProfilingConfig,
        get_profiler,
        ActionType,
        AlertSeverity,
    )
    PROFILING_AVAILABLE = True
except ImportError:
    PROFILING_AVAILABLE = False
    BehaviorProfiler = None
    ProfilingConfig = None
    get_profiler = None
    ActionType = None
    AlertSeverity = None

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


# =============================================================================
# Channel Subscription Models
# =============================================================================

class ChannelType(str, Enum):
    """Channel type enumeration."""
    EVENT = "event"
    COMMAND = "command"
    RESPONSE = "response"
    METRIC = "metric"


class ChannelDirection(str, Enum):
    """Channel direction enumeration."""
    INPUT = "input"
    OUTPUT = "output"
    BIDIRECTIONAL = "bidirectional"


class ChannelSubscriptionCreate(BaseModel):
    """Request model for creating a channel subscription."""
    channelName: str = Field(..., description="Channel name")
    channelType: ChannelType = Field(..., description="Channel type")
    direction: ChannelDirection = Field(..., description="Channel direction")
    dataType: Optional[str] = Field(None, description="Data type handled by channel")
    description: Optional[str] = Field(None, description="Channel description")


class ChannelSubscriptionResponse(BaseModel):
    """Response model for channel subscription."""
    channelName: str
    channelType: ChannelType
    direction: ChannelDirection
    dataType: Optional[str] = None
    description: Optional[str] = None
    subscribedAt: str


class ChannelSubscriptionsListResponse(BaseModel):
    """Response model for listing channel subscriptions."""
    agentId: str
    subscriptions: List[ChannelSubscriptionResponse]
    total: int


# =============================================================================
# Channel Subscription Endpoints
# =============================================================================

def get_channel_registry_instance() -> ChannelRegistry:
    """Dependency to get the channel registry."""
    return get_channel_registry()


@router.get("/{instance_id}/channels")
async def get_agent_channels(
    instance_id: str,
    registry: EnhancedAgentRegistry = Depends(get_registry),
    channel_registry: ChannelRegistry = Depends(get_channel_registry_instance),
    authenticated: str = Depends(verify_auth),
) -> ChannelSubscriptionsListResponse:
    """
    Get all channel subscriptions for an agent.
    
    Args:
        instance_id: Agent instance ID
        
    Returns:
        List of channel subscriptions for the agent
    """
    # Verify agent exists
    instance = registry.get_instance(instance_id)
    if not instance:
        raise HTTPException(404, f"Agent instance '{instance_id}' not found")
    
    try:
        # Get subscriptions from channel registry
        subscriptions = channel_registry.get_subscriptions(instance_id)
        
        # Format response
        subscription_list = []
        for sub in subscriptions:
            # Get channel details
            channel = channel_registry.get_channel(sub)
            if channel:
                subscription_list.append(ChannelSubscriptionResponse(
                    channelName=channel.name,
                    channelType=ChannelType.EVENT,  # Default type
                    direction=ChannelDirection.BIDIRECTIONAL,  # Default direction
                    description=channel.description,
                    subscribedAt=channel_registry.get_stats(channel.name).get("created_at", "") if channel_registry.get_stats(channel.name) else "",
                ))
        
        return ChannelSubscriptionsListResponse(
            agentId=instance_id,
            subscriptions=subscription_list,
            total=len(subscription_list),
        )
    except Exception as e:
        logger.error(f"Failed to get agent channels: {e}", exc_info=True)
        raise HTTPException(500, f"Failed to get agent channels: {str(e)}")


@router.post("/{instance_id}/channels")
async def add_agent_channel_subscription(
    instance_id: str,
    subscription: ChannelSubscriptionCreate,
    registry: EnhancedAgentRegistry = Depends(get_registry),
    channel_registry: ChannelRegistry = Depends(get_channel_registry_instance),
    authenticated: str = Depends(verify_auth),
) -> ChannelSubscriptionResponse:
    """
    Add a channel subscription for an agent.
    
    Args:
        instance_id: Agent instance ID
        subscription: Channel subscription details
        
    Returns:
        Created subscription details
    """
    # Verify agent exists
    instance = registry.get_instance(instance_id)
    if not instance:
        raise HTTPException(404, f"Agent instance '{instance_id}' not found")
    
    try:
        # Subscribe agent to channel
        success = channel_registry.subscribe_agent(instance_id, subscription.channelName)
        
        if not success:
            raise HTTPException(400, f"Failed to subscribe to channel '{subscription.channelName}'")
        
        logger.info(
            "agent_channel_subscribed",
            agent_id=instance_id,
            channel=subscription.channelName,
            type=subscription.channelType.value,
        )
        
        return ChannelSubscriptionResponse(
            channelName=subscription.channelName,
            channelType=subscription.channelType,
            direction=subscription.direction,
            dataType=subscription.dataType,
            description=subscription.description,
            subscribedAt=datetime.now(timezone.utc).isoformat(),
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to add channel subscription: {e}", exc_info=True)
        raise HTTPException(500, f"Failed to add channel subscription: {str(e)}")


@router.delete("/{instance_id}/channels/{channel_name}")
async def remove_agent_channel_subscription(
    instance_id: str,
    channel_name: str,
    registry: EnhancedAgentRegistry = Depends(get_registry),
    channel_registry: ChannelRegistry = Depends(get_channel_registry_instance),
    authenticated: str = Depends(verify_auth),
) -> Dict[str, str]:
    """
    Remove a channel subscription from an agent.
    
    Args:
        instance_id: Agent instance ID
        channel_name: Channel name to unsubscribe from
        
    Returns:
        Success status
    """
    # Verify agent exists
    instance = registry.get_instance(instance_id)
    if not instance:
        raise HTTPException(404, f"Agent instance '{instance_id}' not found")
    
    try:
        # Unsubscribe agent from channel
        success = channel_registry.unsubscribe_agent(instance_id, channel_name)
        
        if not success:
            raise HTTPException(400, f"Agent not subscribed to channel '{channel_name}'")
        
        logger.info(
            "agent_channel_unsubscribed",
            agent_id=instance_id,
            channel=channel_name,
        )
        
        return {"status": "success", "message": f"Unsubscribed from channel '{channel_name}'"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to remove channel subscription: {e}", exc_info=True)
        raise HTTPException(500, f"Failed to remove channel subscription: {str(e)}")


# =============================================================================
# Routing Configuration API Endpoints
# =============================================================================

class RoutingRuleCreate(BaseModel):
    """Request model for creating a routing rule."""
    id: str = Field(..., description="Unique rule identifier")
    name: str = Field(..., description="Human-readable rule name")
    priority: int = Field(..., description="Rule priority (higher evaluated first)")
    subject_pattern: str = Field(..., description="Wildcard pattern for subject")
    content_filters: List[Dict[str, Any]] = Field(default_factory=list, description="Content filters")
    target_channel: str = Field(..., description="Target channel for routed messages")
    target_agents: List[str] = Field(default_factory=list, description="Target agent IDs")
    enabled: bool = Field(default=True, description="Whether rule is active")
    description: Optional[str] = Field(None, description="Optional rule description")


class RoutingRuleResponse(BaseModel):
    """Response model for routing rule."""
    id: str
    name: str
    priority: int
    subject_pattern: str
    content_filters: List[Dict[str, Any]]
    target_channel: str
    target_agents: List[str]
    enabled: bool
    description: Optional[str]


class RoutingRulesListResponse(BaseModel):
    """Response model for listing routing rules."""
    rules: List[RoutingRuleResponse]
    total: int
    active: int


class RoutingStatsResponse(BaseModel):
    """Response model for routing statistics."""
    messages_evaluated: int
    messages_matched: int
    messages_no_match: int
    errors: int
    active_rules: int
    total_rules: int
    uptime_seconds: float


def get_router_instance() -> ContentRouter:
    """Dependency to get the content router."""
    return get_content_router()


@router.get("/routing/rules")
async def list_routing_rules(
    enabled_only: bool = False,
    router: ContentRouter = Depends(get_router_instance),
    authenticated: str = Depends(verify_auth),
) -> RoutingRulesListResponse:
    """
    List all routing rules.
    
    Args:
        enabled_only: If True, only return enabled rules
        
    Returns:
        List of routing rules
    """
    try:
        rules_data = router.list_rules(enabled_only=enabled_only)
        active_count = len([r for r in rules_data if r.get("enabled", False)])
        
        return RoutingRulesListResponse(
            rules=[RoutingRuleResponse(**r) for r in rules_data],
            total=len(rules_data),
            active=active_count,
        )
    except Exception as e:
        logger.error(f"Failed to list routing rules: {e}", exc_info=True)
        raise HTTPException(500, f"Failed to list routing rules: {str(e)}")


@router.get("/routing/rules/{rule_id}")
async def get_routing_rule(
    rule_id: str,
    router: ContentRouter = Depends(get_router_instance),
    authenticated: str = Depends(verify_auth),
) -> RoutingRuleResponse:
    """
    Get a specific routing rule by ID.
    
    Args:
        rule_id: Rule identifier
        
    Returns:
        Routing rule details
    """
    rule = router.get_rule(rule_id)
    
    if not rule:
        raise HTTPException(404, f"Routing rule '{rule_id}' not found")
    
    return RoutingRuleResponse(
        id=rule.id,
        name=rule.name,
        priority=rule.priority,
        subject_pattern=rule.subject_pattern,
        content_filters=[
            {"field": f.field, "operator": f.operator.value, "value": f.value}
            for f in rule.content_filters
        ],
        target_channel=rule.target_channel,
        target_agents=rule.target_agents,
        enabled=rule.enabled,
        description=rule.description,
    )


@router.post("/routing/rules")
async def create_routing_rule(
    rule_data: RoutingRuleCreate,
    router: ContentRouter = Depends(get_router_instance),
    authenticated: str = Depends(verify_auth),
) -> RoutingRuleResponse:
    """
    Create a new routing rule.
    
    Args:
        rule_data: Rule configuration
        
    Returns:
        Created rule details
    """
    try:
        # Convert content filters
        content_filters = []
        for cf in rule_data.content_filters:
            content_filters.append(ContentFilter(
                field=cf["field"],
                operator=FilterOperator(cf["operator"]),
                value=cf["value"],
            ))
        
        # Create rule
        rule = RoutingRule(
            id=rule_data.id,
            name=rule_data.name,
            priority=rule_data.priority,
            subject_pattern=rule_data.subject_pattern,
            content_filters=content_filters,
            target_channel=rule_data.target_channel,
            target_agents=rule_data.target_agents,
            enabled=rule_data.enabled,
            description=rule_data.description,
        )
        
        # Add to router
        if not router.add_rule(rule):
            raise HTTPException(409, f"Routing rule '{rule_data.id}' already exists")
        
        logger.info(
            "routing_rule_created",
            rule_id=rule.id,
            name=rule.name,
            priority=rule.priority,
        )
        
        return RoutingRuleResponse(
            id=rule.id,
            name=rule.name,
            priority=rule.priority,
            subject_pattern=rule.subject_pattern,
            content_filters=[
                {"field": f.field, "operator": f.operator.value, "value": f.value}
                for f in rule.content_filters
            ],
            target_channel=rule.target_channel,
            target_agents=rule.target_agents,
            enabled=rule.enabled,
            description=rule.description,
        )
    except ValueError as e:
        raise HTTPException(400, str(e))
    except Exception as e:
        logger.error(f"Failed to create routing rule: {e}", exc_info=True)
        raise HTTPException(500, f"Failed to create routing rule: {str(e)}")


@router.put("/routing/rules/{rule_id}")
async def update_routing_rule(
    rule_id: str,
    rule_data: RoutingRuleCreate,
    router: ContentRouter = Depends(get_router_instance),
    authenticated: str = Depends(verify_auth),
) -> RoutingRuleResponse:
    """
    Update an existing routing rule.
    
    Args:
        rule_id: Rule identifier
        rule_data: Updated rule configuration
        
    Returns:
        Updated rule details
    """
    # Remove existing rule
    router.remove_rule(rule_id)
    
    # Convert content filters
    content_filters = []
    for cf in rule_data.content_filters:
        content_filters.append(ContentFilter(
            field=cf["field"],
            operator=FilterOperator(cf["operator"]),
            value=cf["value"],
        ))
    
    # Create updated rule
    rule = RoutingRule(
        id=rule_data.id,
        name=rule_data.name,
        priority=rule_data.priority,
        subject_pattern=rule_data.subject_pattern,
        content_filters=content_filters,
        target_channel=rule_data.target_channel,
        target_agents=rule_data.target_agents,
        enabled=rule_data.enabled,
        description=rule_data.description,
    )
    
    # Add to router
    if not router.add_rule(rule):
        raise HTTPException(500, "Failed to add updated rule")
    
    logger.info("routing_rule_updated", rule_id=rule_id)
    
    return RoutingRuleResponse(
        id=rule.id,
        name=rule.name,
        priority=rule.priority,
        subject_pattern=rule.subject_pattern,
        content_filters=[
            {"field": f.field, "operator": f.operator.value, "value": f.value}
            for f in rule.content_filters
        ],
        target_channel=rule.target_channel,
        target_agents=rule.target_agents,
        enabled=rule.enabled,
        description=rule.description,
    )


@router.delete("/routing/rules/{rule_id}")
async def delete_routing_rule(
    rule_id: str,
    router: ContentRouter = Depends(get_router_instance),
    authenticated: str = Depends(verify_auth),
) -> Dict[str, str]:
    """
    Delete a routing rule.
    
    Args:
        rule_id: Rule identifier
        
    Returns:
        Success status
    """
    if not router.remove_rule(rule_id):
        raise HTTPException(404, f"Routing rule '{rule_id}' not found")
    
    logger.info("routing_rule_deleted", rule_id=rule_id)
    
    return {"status": "success", "message": f"Deleted rule '{rule_id}'"}


@router.post("/routing/rules/{rule_id}/enable")
async def enable_routing_rule(
    rule_id: str,
    router: ContentRouter = Depends(get_router_instance),
    authenticated: str = Depends(verify_auth),
) -> Dict[str, str]:
    """Enable a routing rule."""
    if not router.enable_rule(rule_id):
        raise HTTPException(404, f"Routing rule '{rule_id}' not found")
    
    return {"status": "success", "message": f"Enabled rule '{rule_id}'"}


@router.post("/routing/rules/{rule_id}/disable")
async def disable_routing_rule(
    rule_id: str,
    router: ContentRouter = Depends(get_router_instance),
    authenticated: str = Depends(verify_auth),
) -> Dict[str, str]:
    """Disable a routing rule."""
    if not router.disable_rule(rule_id):
        raise HTTPException(404, f"Routing rule '{rule_id}' not found")
    
    return {"status": "success", "message": f"Disabled rule '{rule_id}'"}


@router.get("/routing/stats")
async def get_routing_stats(
    router: ContentRouter = Depends(get_router_instance),
    authenticated: str = Depends(verify_auth),
) -> RoutingStatsResponse:
    """
    Get routing statistics.
    
    Returns statistics about message routing and rule evaluation.
    """
    try:
        stats = router.get_stats()
        return RoutingStatsResponse(**stats)
    except Exception as e:
        logger.error(f"Failed to get routing stats: {e}", exc_info=True)
        raise HTTPException(500, f"Failed to get routing stats: {str(e)}")


@router.post("/routing/evaluate")
async def evaluate_routing(
    subject: str,
    payload: Dict[str, Any],
    correlation_id: Optional[str] = None,
    router: ContentRouter = Depends(get_router_instance),
    authenticated: str = Depends(verify_auth),
) -> Dict[str, Any]:
    """
    Evaluate routing for a message (test endpoint).
    
    Args:
        subject: Message subject
        payload: Message payload
        correlation_id: Optional correlation ID
        
    Returns:
        Routing decision details
    """
    try:
        decision = router.route(
            subject=subject,
            payload=payload,
            correlation_id=correlation_id,
        )
        
        return {
            "decision": decision.decision.value,
            "matched_rule": {
                "id": decision.matched_rule.id,
                "name": decision.matched_rule.name,
                "target_channel": decision.matched_rule.target_channel,
                "target_agents": decision.matched_rule.target_agents,
            } if decision.matched_rule else None,
            "correlation_id": decision.correlation_id,
            "evaluation_time_ms": decision.evaluation_time_ms,
            "filters_evaluated": decision.filters_evaluated,
            "filters_matched": decision.filters_matched,
        }
    except Exception as e:
        logger.error(f"Failed to evaluate routing: {e}", exc_info=True)
        raise HTTPException(500, f"Failed to evaluate routing: {str(e)}")


# =============================================================================
# Behavior Profiling Endpoints
# =============================================================================

def get_profiler_instance() -> Optional[BehaviorProfiler]:
    """Dependency to get the behavior profiler."""
    if PROFILING_AVAILABLE and get_profiler:
        return get_profiler()
    return None


class ProfilingMetricsResponse(BaseModel):
    """Response model for agent profiling metrics."""
    agentId: str
    totalActions: int = 0
    actionsPerMinute: float = 0.0
    messageSentCount: int = 0
    messageReceivedCount: int = 0
    tasksStarted: int = 0
    tasksCompleted: int = 0
    tasksFailed: int = 0
    taskSuccessRate: float = 0.0
    avgTaskDurationMs: float = 0.0
    errorCount: int = 0
    errorRate: float = 0.0
    avgResponseTimeMs: float = 0.0
    maxResponseTimeMs: float = 0.0
    minResponseTimeMs: float = 0.0
    responseTimeStddev: float = 0.0
    stateChanges: int = 0


class ProfilingProfileResponse(BaseModel):
    """Response model for behavior profile."""
    agentType: str
    createdAt: str
    updatedAt: str
    baselineActionsPerMinute: float = 0.0
    baselineTaskSuccessRate: float = 1.0
    baselineAvgTaskDurationMs: float = 0.0
    baselineErrorRate: float = 0.0
    baselineResponseTimeMs: float = 0.0
    sampleCount: int = 0


class AnomalyResponse(BaseModel):
    """Response model for detected anomaly."""
    timestamp: str
    agentId: str
    anomalyType: str
    severity: str
    description: str
    metrics: Dict[str, Any] = field(default_factory=dict)
    expectedValue: float = 0.0
    actualValue: float = 0.0


class AlertResponse(BaseModel):
    """Response model for alert."""
    timestamp: str
    agentId: str
    anomaly: AnomalyResponse
    message: str
    acknowledged: bool
    acknowledgedAt: Optional[str] = None
    acknowledgedBy: Optional[str] = None


class ProfilingStatsResponse(BaseModel):
    """Response model for profiler statistics."""
    totalActivitiesRecorded: int
    totalAnomaliesDetected: int
    totalAlertsGenerated: int
    profilesCreated: int
    activeAgents: int
    profilesCount: int
    unacknowledgedAlerts: int


@router.get("/{instance_id}/profiling/metrics")
async def get_agent_profiling_metrics(
    instance_id: str,
    registry: EnhancedAgentRegistry = Depends(get_registry),
    profiler: Optional[BehaviorProfiler] = Depends(get_profiler_instance),
    authenticated: str = Depends(verify_auth),
) -> ProfilingMetricsResponse:
    """
    Get behavior profiling metrics for an agent.
    
    Args:
        instance_id: Agent instance ID
        
    Returns:
        Agent behavior metrics
    """
    if not PROFILING_AVAILABLE or not profiler:
        raise HTTPException(503, "Behavior profiling not available")
    
    # Verify agent exists
    instance = registry.get_instance(instance_id)
    if not instance:
        raise HTTPException(404, f"Agent instance '{instance_id}' not found")
    
    # Compute and get metrics
    metrics = profiler.compute_metrics(instance_id)
    
    if not metrics:
        return ProfilingMetricsResponse(agentId=instance_id)
    
    return ProfilingMetricsResponse(
        agentId=instance_id,
        totalActions=metrics.total_actions,
        actionsPerMinute=metrics.actions_per_minute,
        messageSentCount=metrics.message_sent_count,
        messageReceivedCount=metrics.message_received_count,
        tasksStarted=metrics.tasks_started,
        tasksCompleted=metrics.tasks_completed,
        tasksFailed=metrics.tasks_failed,
        taskSuccessRate=metrics.task_success_rate,
        avgTaskDurationMs=metrics.avg_task_duration_ms,
        errorCount=metrics.error_count,
        errorRate=metrics.error_rate,
        avgResponseTimeMs=metrics.avg_response_time_ms,
        maxResponseTimeMs=metrics.max_response_time_ms,
        minResponseTimeMs=metrics.min_response_time_ms,
        responseTimeStddev=metrics.response_time_stddev,
        stateChanges=metrics.state_changes,
    )


@router.get("/{instance_id}/profiling/profile")
async def get_agent_profiling_profile(
    instance_id: str,
    registry: EnhancedAgentRegistry = Depends(get_registry),
    profiler: Optional[BehaviorProfiler] = Depends(get_profiler_instance),
    authenticated: str = Depends(verify_auth),
) -> ProfilingProfileResponse:
    """
    Get behavior profile for an agent's type.
    
    Args:
        instance_id: Agent instance ID
        
    Returns:
        Behavior profile for the agent type
    """
    if not PROFILING_AVAILABLE or not profiler:
        raise HTTPException(503, "Behavior profiling not available")
    
    # Verify agent exists
    instance = registry.get_instance(instance_id)
    if not instance:
        raise HTTPException(404, f"Agent instance '{instance_id}' not found")
    
    # Get agent type from instance
    agent_type = instance.agent_type
    
    # Update profile with current data
    profiler.update_profile(agent_type, instance_id)
    
    # Get profile
    profile = profiler.get_profile(agent_type)
    
    if not profile:
        raise HTTPException(404, f"No profile available for agent type '{agent_type}'")
    
    return ProfilingProfileResponse(
        agentType=profile.agent_type,
        createdAt=profile.created_at.isoformat(),
        updatedAt=profile.updated_at.isoformat(),
        baselineActionsPerMinute=profile.baseline_actions_per_minute,
        baselineTaskSuccessRate=profile.baseline_task_success_rate,
        baselineAvgTaskDurationMs=profile.baseline_avg_task_duration_ms,
        baselineErrorRate=profile.baseline_error_rate,
        baselineResponseTimeMs=profile.baseline_response_time_ms,
        sampleCount=profile.sample_count,
    )


@router.get("/{instance_id}/profiling/anomalies")
async def detect_agent_anomalies(
    instance_id: str,
    registry: EnhancedAgentRegistry = Depends(get_registry),
    profiler: Optional[BehaviorProfiler] = Depends(get_profiler_instance),
    authenticated: str = Depends(verify_auth),
) -> List[AnomalyResponse]:
    """
    Detect anomalies in agent behavior.
    
    Args:
        instance_id: Agent instance ID
        
    Returns:
        List of detected anomalies
    """
    if not PROFILING_AVAILABLE or not profiler:
        raise HTTPException(503, "Behavior profiling not available")
    
    # Verify agent exists
    instance = registry.get_instance(instance_id)
    if not instance:
        raise HTTPException(404, f"Agent instance '{instance_id}' not found")
    
    # Detect anomalies
    anomalies = profiler.detect_anomalies(instance_id)
    
    return [
        AnomalyResponse(
            timestamp=a.timestamp.isoformat(),
            agentId=a.agent_id,
            anomalyType=a.anomaly_type.value,
            severity=a.severity.value,
            description=a.description,
            metrics=a.metrics,
            expectedValue=a.expected_value,
            actualValue=a.actual_value,
        )
        for a in anomalies
    ]


@router.get("/profiling/alerts")
async def get_profiling_alerts(
    severity: Optional[str] = None,
    unacknowledged_only: bool = False,
    profiler: Optional[BehaviorProfiler] = Depends(get_profiler_instance),
    authenticated: str = Depends(verify_auth),
) -> List[AlertResponse]:
    """
    Get all profiling alerts.
    
    Args:
        severity: Filter by severity (low, medium, high, critical)
        unacknowledged_only: Only return unacknowledged alerts
        
    Returns:
        List of alerts
    """
    if not PROFILING_AVAILABLE or not profiler:
        raise HTTPException(503, "Behavior profiling not available")
    
    # Parse severity
    severity_filter = None
    if severity:
        try:
            severity_filter = AlertSeverity(severity.lower())
        except ValueError:
            raise HTTPException(400, f"Invalid severity: {severity}")
    
    # Get alerts
    alerts = profiler.get_alerts(
        severity=severity_filter,
        unacknowledged_only=unacknowledged_only,
    )
    
    return [
        AlertResponse(
            timestamp=a.timestamp.isoformat(),
            agentId=a.agent_id,
            anomaly=AnomalyResponse(
                timestamp=a.anomaly.timestamp.isoformat(),
                agentId=a.anomaly.agent_id,
                anomalyType=a.anomaly.anomaly_type.value,
                severity=a.anomaly.severity.value,
                description=a.anomaly.description,
                metrics=a.anomaly.metrics,
                expectedValue=a.anomaly.expected_value,
                actualValue=a.anomaly.actual_value,
            ),
            message=a.message,
            acknowledged=a.acknowledged,
            acknowledgedAt=a.acknowledged_at.isoformat() if a.acknowledged_at else None,
            acknowledgedBy=a.acknowledged_by,
        )
        for a in alerts
    ]


@router.post("/profiling/alerts/{index}/acknowledge")
async def acknowledge_profiling_alert(
    index: int,
    acknowledged_by: str,
    profiler: Optional[BehaviorProfiler] = Depends(get_profiler_instance),
    authenticated: str = Depends(verify_auth),
) -> Dict[str, Any]:
    """
    Acknowledge a profiling alert.
    
    Args:
        index: Alert index in list
        acknowledged_by: User/system acknowledging
        
    Returns:
        Success status
    """
    if not PROFILING_AVAILABLE or not profiler:
        raise HTTPException(503, "Behavior profiling not available")
    
    if not profiler.acknowledge_alert(index, acknowledged_by):
        raise HTTPException(404, f"Alert at index {index} not found")
    
    return {"status": "success", "message": f"Alert {index} acknowledged"}


@router.get("/profiling/stats")
async def get_profiling_stats(
    profiler: Optional[BehaviorProfiler] = Depends(get_profiler_instance),
    authenticated: str = Depends(verify_auth),
) -> ProfilingStatsResponse:
    """
    Get profiler statistics.
    
    Returns:
        Profiler statistics
    """
    if not PROFILING_AVAILABLE or not profiler:
        raise HTTPException(503, "Behavior profiling not available")
    
    stats = profiler.get_stats()
    
    return ProfilingStatsResponse(
        totalActivitiesRecorded=stats["total_activities_recorded"],
        totalAnomaliesDetected=stats["total_anomalies_detected"],
        totalAlertsGenerated=stats["total_alerts_generated"],
        profilesCreated=stats["profiles_created"],
        activeAgents=stats["active_agents"],
        profilesCount=stats["profiles_count"],
        unacknowledgedAlerts=stats["alerts_count"],
    )


@router.get("/profiling/prometheus")
async def get_profiling_prometheus_metrics(
    profiler: Optional[BehaviorProfiler] = Depends(get_profiler_instance),
) -> str:
    """
    Get profiling metrics in Prometheus format.
    
    Returns:
        Prometheus-formatted metrics string
    """
    if not PROFILING_AVAILABLE or not profiler:
        return "# Behavior profiling not available\n"
    
    return profiler.export_prometheus_metrics()


@router.post("/{instance_id}/profiling/record")
async def record_agent_activity(
    instance_id: str,
    action: str,
    duration_ms: float = 0.0,
    success: bool = True,
    metadata: Optional[Dict[str, Any]] = None,
    registry: EnhancedAgentRegistry = Depends(get_registry),
    profiler: Optional[BehaviorProfiler] = Depends(get_profiler_instance),
    authenticated: str = Depends(verify_auth),
) -> Dict[str, Any]:
    """
    Record an agent activity for profiling.
    
    Args:
        instance_id: Agent instance ID
        action: Action type (message_sent, task_completed, etc.)
        duration_ms: Action duration in milliseconds
        success: Whether action was successful
        metadata: Additional metadata
        
    Returns:
        Success status
    """
    if not PROFILING_AVAILABLE or not profiler:
        raise HTTPException(503, "Behavior profiling not available")
    
    # Verify agent exists
    instance = registry.get_instance(instance_id)
    if not instance:
        raise HTTPException(404, f"Agent instance '{instance_id}' not found")
    
    # Parse action type
    try:
        action_type = ActionType(action.lower())
    except ValueError:
        action_type = ActionType.CUSTOM
    
    # Record activity
    profiler.record_activity(
        agent_id=instance_id,
        action=action_type,
        metadata=metadata or {},
        duration_ms=duration_ms,
        success=success,
    )
    
    return {"status": "success", "message": f"Activity recorded: {action}"}


# =============================================================================
# JetStream Stream Management Endpoints
# =============================================================================

def get_jetstream_manager() -> Optional[Any]:
    """Dependency to get the JetStream manager."""
    try:
        from heretek_swarm.gateway.jetstream_manager import get_jetstream_manager as get_js
        return get_js()
    except ImportError:
        return None


class JetStreamConfigCreate(BaseModel):
    """Request model for creating a JetStream."""
    stream_name: str = Field(..., description="Stream name")
    subjects: List[str] = Field(..., description="List of subjects to capture")
    retention: str = Field(default="limits", description="Retention policy (limits, interest, workqueue)")
    max_messages: int = Field(default=1000000, description="Maximum messages to retain")
    max_age: str = Field(default="72h", description="Maximum age (e.g., 72h, 7d)")
    storage: str = Field(default="file", description="Storage type (file, memory)")
    replicas: int = Field(default=1, description="Number of replicas")
    max_bytes: int = Field(default=1073741824, description="Maximum size in bytes")
    description: Optional[str] = Field(None, description="Stream description")


class JetStreamConsumerCreate(BaseModel):
    """Request model for creating a durable consumer."""
    durable_name: str = Field(..., description="Durable consumer name")
    stream_name: str = Field(..., description="Source stream name")
    deliver_policy: str = Field(default="all", description="Delivery policy")
    ack_policy: str = Field(default="explicit", description="Acknowledgment policy")
    filter_subject: Optional[str] = Field(None, description="Subject filter")


class StreamInfoResponse(BaseModel):
    """Response model for stream information."""
    name: str
    subjects: List[str]
    retention: str
    max_messages: int
    max_age: str
    storage: str
    replicas: int
    max_bytes: int
    description: Optional[str]
    state: Dict[str, Any]
    created_at: Optional[str]


class StreamListResponse(BaseModel):
    """Response model for listing streams."""
    streams: List[StreamInfoResponse]
    total: int


@router.get("/jetstream/streams")
async def list_jetstream_streams(
    js_manager: Optional[Any] = Depends(get_jetstream_manager),
    authenticated: str = Depends(verify_auth),
) -> StreamListResponse:
    """
    List all JetStream streams.
    
    Returns:
        List of stream information
    """
    if not js_manager:
        raise HTTPException(503, "JetStream manager not available")
    
    try:
        streams = await js_manager.list_streams()
        
        return StreamListResponse(
            streams=[
                StreamInfoResponse(
                    name=s.name,
                    subjects=s.config.subjects,
                    retention=s.config.retention.value,
                    max_messages=s.config.max_messages,
                    max_age=s.config.max_age,
                    storage=s.config.storage.value,
                    replicas=s.config.replicas,
                    max_bytes=s.config.max_bytes,
                    description=s.config.description,
                    state=s.state,
                    created_at=s.created_at.isoformat() if s.created_at else None,
                )
                for s in streams
            ],
            total=len(streams),
        )
    except Exception as e:
        logger.error(f"Failed to list streams: {e}", exc_info=True)
        raise HTTPException(500, f"Failed to list streams: {str(e)}")


@router.get("/jetstream/streams/{stream_name}")
async def get_jetstream_stream(
    stream_name: str,
    js_manager: Optional[Any] = Depends(get_jetstream_manager),
    authenticated: str = Depends(verify_auth),
) -> StreamInfoResponse:
    """
    Get information about a specific stream.
    
    Args:
        stream_name: Stream name
    """
    if not js_manager:
        raise HTTPException(503, "JetStream manager not available")
    
    try:
        info = await js_manager.get_stream_info(stream_name)
        
        if not info:
            raise HTTPException(404, f"Stream '{stream_name}' not found")
        
        return StreamInfoResponse(
            name=info.name,
            subjects=info.config.subjects,
            retention=info.config.retention.value,
            max_messages=info.config.max_messages,
            max_age=info.config.max_age,
            storage=info.config.storage.value,
            replicas=info.config.replicas,
            max_bytes=info.config.max_bytes,
            description=info.config.description,
            state=info.state,
            created_at=info.created_at.isoformat() if info.created_at else None,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get stream info: {e}", exc_info=True)
        raise HTTPException(500, f"Failed to get stream info: {str(e)}")


@router.post("/jetstream/streams")
async def create_jetstream_stream(
    config_data: JetStreamConfigCreate,
    js_manager: Optional[Any] = Depends(get_jetstream_manager),
    authenticated: str = Depends(verify_auth),
) -> Dict[str, Any]:
    """
    Create a new JetStream.
    
    Args:
        config_data: Stream configuration
    """
    if not js_manager:
        raise HTTPException(503, "JetStream manager not available")
    
    try:
        from heretek_swarm.gateway.jetstream_manager import (
            JetStreamConfig,
            RetentionPolicy,
            StorageType,
        )
        
        config = JetStreamConfig(
            stream_name=config_data.stream_name,
            subjects=config_data.subjects,
            retention=RetentionPolicy(config_data.retention),
            max_messages=config_data.max_messages,
            max_age=config_data.max_age,
            storage=StorageType(config_data.storage),
            replicas=config_data.replicas,
            max_bytes=config_data.max_bytes,
            description=config_data.description,
        )
        
        success = await js_manager.create_stream(config)
        
        if not success:
            raise HTTPException(500, "Failed to create stream")
        
        logger.info(
            "jetstream_stream_created",
            stream_name=config_data.stream_name,
            subjects=config_data.subjects,
        )
        
        return {
            "status": "success",
            "stream_name": config_data.stream_name,
            "subjects": config_data.subjects,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create stream: {e}", exc_info=True)
        raise HTTPException(500, f"Failed to create stream: {str(e)}")


@router.delete("/jetstream/streams/{stream_name}")
async def delete_jetstream_stream(
    stream_name: str,
    js_manager: Optional[Any] = Depends(get_jetstream_manager),
    authenticated: str = Depends(verify_auth),
) -> Dict[str, str]:
    """
    Delete a JetStream.
    
    Args:
        stream_name: Stream name
    """
    if not js_manager:
        raise HTTPException(503, "JetStream manager not available")
    
    try:
        success = await js_manager.delete_stream(stream_name)
        
        if not success:
            raise HTTPException(404, f"Stream '{stream_name}' not found or delete failed")
        
        logger.info("jetstream_stream_deleted", stream_name=stream_name)
        
        return {"status": "success", "message": f"Deleted stream '{stream_name}'"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete stream: {e}", exc_info=True)
        raise HTTPException(500, f"Failed to delete stream: {str(e)}")


@router.post("/jetstream/streams/{stream_name}/replay")
async def replay_stream_messages(
    stream_name: str,
    start_sequence: Optional[int] = None,
    end_sequence: Optional[int] = None,
    subject_filter: Optional[str] = None,
    js_manager: Optional[Any] = Depends(get_jetstream_manager),
    authenticated: str = Depends(verify_auth),
) -> Dict[str, Any]:
    """
    Replay messages from a stream.
    
    Args:
        stream_name: Stream name
        start_sequence: Start sequence number
        end_sequence: End sequence number
        subject_filter: Subject pattern filter
    """
    if not js_manager:
        raise HTTPException(503, "JetStream manager not available")
    
    try:
        messages = await js_manager.replay_messages(
            stream_name=stream_name,
            start_sequence=start_sequence,
            end_sequence=end_sequence,
            subject_filter=subject_filter,
        )
        
        return {
            "stream_name": stream_name,
            "messages_replayed": len(messages),
            "messages": messages[:100],  # Limit response size
        }
    except Exception as e:
        logger.error(f"Failed to replay messages: {e}", exc_info=True)
        raise HTTPException(500, f"Failed to replay messages: {str(e)}")


@router.get("/jetstream/stats")
async def get_jetstream_stats(
    js_manager: Optional[Any] = Depends(get_jetstream_manager),
    authenticated: str = Depends(verify_auth),
) -> Dict[str, Any]:
    """
    Get JetStream manager statistics.
    
    Returns:
        Manager statistics
    """
    if not js_manager:
        raise HTTPException(503, "JetStream manager not available")
    
    try:
        stats = await js_manager.get_stats()
        return stats
    except Exception as e:
        logger.error(f"Failed to get JetStream stats: {e}", exc_info=True)
        raise HTTPException(500, f"Failed to get JetStream stats: {str(e)}")


@router.post("/jetstream/initialize")
async def initialize_jetstream(
    create_defaults: bool = True,
    js_manager: Optional[Any] = Depends(get_jetstream_manager),
    authenticated: str = Depends(verify_auth),
) -> Dict[str, Any]:
    """
    Initialize JetStream with default streams.
    
    Args:
        create_defaults: Create default stream configurations
        
    Returns:
        Creation results for each stream
    """
    if not js_manager:
        raise HTTPException(503, "JetStream manager not available")
    
    try:
        results = await js_manager.initialize_default_streams()
        
        logger.info("JetStream default streams initialized", results=results)
        
        return {
            "status": "success",
            "streams": results,
            "total_created": sum(1 for v in results.values() if v),
        }
    except Exception as e:
        logger.error(f"Failed to initialize JetStream: {e}", exc_info=True)
        raise HTTPException(500, f"Failed to initialize JetStream: {str(e)}")
