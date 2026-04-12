# =============================================================================
"""Agent instances endpoints."""

from enum import StrEnum
from typing import Any

import structlog
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from heretek_swarm.channels.registry import ChannelRegistry, get_channel_registry
from heretek_swarm.gateway.auth import verify_auth
from heretek_swarm.runtime.registry_enhanced import EnhancedAgentRegistry, get_enhanced_registry

logger = structlog.get_logger()
router = APIRouter()


def get_registry() -> EnhancedAgentRegistry:
    """Dependency to get the enhanced agent registry."""
    return get_enhanced_registry()


@router.get("/instances")
async def list_agent_instances(
    agent_type: str | None = None,
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
        raise HTTPException(500, f"Failed to list instances: {e!s}")


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
        except Exception as e:
            logger.debug("agent_status_log_read_failed", error=str(e))

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
        return registry.get_registry_stats()
    except Exception as e:
        logger.error(f"Failed to get registry stats: {e}", exc_info=True)
        raise HTTPException(500, f"Failed to get registry stats: {e!s}")


# =============================================================================
# Channel Subscription Models
# =============================================================================

class ChannelType(StrEnum):
    """Channel type enumeration."""
    EVENT = "event"
    COMMAND = "command"
    RESPONSE = "response"
    METRIC = "metric"


class ChannelDirection(StrEnum):
    """Channel direction enumeration."""
    INPUT = "input"
    OUTPUT = "output"
    BIDIRECTIONAL = "bidirectional"


class ChannelSubscriptionCreate(BaseModel):
    """Request model for creating a channel subscription."""
    channelName: str = Field(..., description="Channel name")
    channelType: ChannelType = Field(..., description="Channel type")
    direction: ChannelDirection = Field(..., description="Channel direction")
    dataType: str | None = Field(None, description="Data type handled by channel")
    description: str | None = Field(None, description="Channel description")


class ChannelSubscriptionResponse(BaseModel):
    """Response model for channel subscription."""
    channelName: str
    channelType: ChannelType
    direction: ChannelDirection
    dataType: str | None = None
    description: str | None = None
    subscribedAt: str


class ChannelSubscriptionsListResponse(BaseModel):
    """Response model for listing channel subscriptions."""
    agentId: str
    subscriptions: list[ChannelSubscriptionResponse]
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
        raise HTTPException(500, f"Failed to get agent channels: {e!s}")


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
            subscribedAt=datetime.now(UTC).isoformat(),
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to add channel subscription: {e}", exc_info=True)
        raise HTTPException(500, f"Failed to add channel subscription: {e!s}")


@router.delete("/{instance_id}/channels/{channel_name}")
async def remove_agent_channel_subscription(
    instance_id: str,
    channel_name: str,
    registry: EnhancedAgentRegistry = Depends(get_registry),
    channel_registry: ChannelRegistry = Depends(get_channel_registry_instance),
    authenticated: str = Depends(verify_auth),
) -> dict[str, str]:
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
        raise HTTPException(500, f"Failed to remove channel subscription: {e!s}")


# =============================================================================
