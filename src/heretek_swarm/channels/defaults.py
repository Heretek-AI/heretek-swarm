"""Default channel and group definitions.

This module provides default channel configurations organized by type,
enabling cleaner separation of channel definitions from registration logic.
"""

from typing import List

from .registry import ChannelDefinition, ChannelType, QoSLevel


def get_internal_channels() -> List[ChannelDefinition]:
    """Get default internal agent channels.
    
    Returns:
        List of internal channel definitions
    """
    return [
        # Triad Channel - Core governance deliberation
        ChannelDefinition(
            _name = "swarm.internal.triad",
            _description = "Core governance deliberation channel",
            _channel_type = ChannelType.INTERNAL,
            _subscribers = ["steward", "alpha", "beta", "charlie"],
            _message_types = [
                "proposal", "analysis", "validation", "challenge", 
                "decision", "deliberation_start", "deliberation_complete"
            ],
            _qos = QoSLevel.AT_LEAST_ONCE,
            _retention = "24h",
            _priority = "high",
        ),

        # Coordination Channel - Multi-agent task coordination
        ChannelDefinition(
            _name = "swarm.internal.coordination",
            _description = "Multi-agent task coordination channel",
            _channel_type = ChannelType.INTERNAL,
            _subscribers = ["coordinator", "catalyst", "chronos", "metis"],
            _message_types = [
                "task_start", "task_complete", "dependency_ready", 
                "blocker", "resource_request", "status_update"
            ],
            _qos = QoSLevel.AT_LEAST_ONCE,
            _retention = "12h",
        ),

        # Safety Channel - Security and safety alerts
        ChannelDefinition(
            _name = "swarm.internal.safety",
            _description = "Security and safety alerts channel",
            _channel_type = ChannelType.INTERNAL,
            _subscribers = ["sentinel", "sentinel-prime", "arbiter", "steward"],
            _message_types = [
                "threat_detected", "quarantine", "all_clear", 
                "incident_report", "validation_request", "security_alert"
            ],
            _qos = QoSLevel.EXACTLY_ONCE,
            _retention = "7d",
            _priority = "critical",
        ),

        # Memory Channel - Memory and knowledge operations
        ChannelDefinition(
            _name = "swarm.internal.memory",
            _description = "Memory and knowledge operations channel",
            _channel_type = ChannelType.INTERNAL,
            _subscribers = ["historian", "prism", "habit-forge"],
            _message_types = [
                "store_request", "retrieve_request", "learn_pattern", 
                "forget", "context_request", "lineage_query"
            ],
            _qos = QoSLevel.AT_MOST_ONCE,
            _retention = "1h",
        ),

        # Exploration Channel - Research and implementation
        ChannelDefinition(
            _name = "swarm.internal.exploration",
            _description = "Research and implementation channel",
            _channel_type = ChannelType.INTERNAL,
            _subscribers = ["explorer", "examiner", "dreamer", "coder"],
            _message_types = [
                "research_task", "analysis_result", "creative_request", 
                "code_review", "discovery", "implementation_complete"
            ],
            _qos = QoSLevel.AT_LEAST_ONCE,
            _retention = "6h",
        ),

        # Perception Channel - Input processing and translation
        ChannelDefinition(
            _name = "swarm.internal.perception",
            _description = "Input processing and translation channel",
            _channel_type = ChannelType.INTERNAL,
            _subscribers = ["perceiver", "perceiver-plus", "empath", "echo"],
            _message_types = [
                "input_received", "sentiment_analysis", "translation_request", 
                "feature_extracted", "format_request", "broadcast_request"
            ],
            _qos = QoSLevel.AT_MOST_ONCE,
            _retention = "1h",
        ),
    ]


def get_system_channels() -> List[ChannelDefinition]:
    """Get default system channels.
    
    Returns:
        List of system channel definitions
    """
    return [
        # Health Channel - Health monitoring (all agents)
        ChannelDefinition(
            _name = "swarm.system.health",
            _description = "Health monitoring channel (all agents)",
            _channel_type = ChannelType.SYSTEM,
            _subscribers = ["*"],  # Wildcard - all agents
            _message_types = [
                "heartbeat", "health_status", "error_report", 
                "restart_request", "scaling_request"
            ],
            _qos = QoSLevel.AT_MOST_ONCE,
            _retention = "1h",
        ),

        # Consciousness Channel - Consciousness metrics broadcast
        ChannelDefinition(
            _name = "swarm.system.consciousness",
            _description = "Consciousness metrics broadcast channel",
            _channel_type = ChannelType.SYSTEM,
            _subscribers = ["*"],
            _message_types = [
                "phi_update", "attention_state", "workspace_broadcast", 
                "integration_metric", "global_state"
            ],
            _qos = QoSLevel.AT_MOST_ONCE,
            _retention = "30m",
        ),

        # Consensus Channel - MAKER consensus voting
        ChannelDefinition(
            _name = "swarm.system.consensus",
            _description = "MAKER consensus voting channel",
            _channel_type = ChannelType.CONSENSUS,
            _subscribers = ["steward", "alpha", "beta", "charlie"],
            _message_types = [
                "vote_cast", "consensus_reached", "red_flag", 
                "reputation_update", "proposal_start", "proposal_complete"
            ],
            _qos = QoSLevel.EXACTLY_ONCE,
            _retention = "24h",
            _priority = "high",
        ),

        # Workflow Channel - Workflow events
        ChannelDefinition(
            _name = "swarm.workflow.events",
            _description = "Workflow lifecycle events channel",
            _channel_type = ChannelType.SYSTEM,
            _subscribers = ["*"],
            _message_types = [
                "workflow_start", "workflow_phase", "workflow_complete", 
                "workflow_error", "workflow_checkpoint"
            ],
            _qos = QoSLevel.AT_LEAST_ONCE,
            _retention = "24h",
        ),
    ]


def get_external_channels() -> List[ChannelDefinition]:
    """Get default external integration channels.
    
    Returns:
        List of external channel definitions
    """
    return [
        # Discord Channel
        ChannelDefinition(
            _name = "swarm.external.discord",
            _description = "Discord integration channel",
            _channel_type = ChannelType.EXTERNAL,
            _subscribers = ["nexus", "echo"],
            _message_types = [
                "discord_message", "discord_command", "discord_response"
            ],
            _qos = QoSLevel.AT_LEAST_ONCE,
            _retention = "1h",
        ),

        # Slack Channel
        ChannelDefinition(
            _name = "swarm.external.slack",
            _description = "Slack integration channel",
            _channel_type = ChannelType.EXTERNAL,
            _subscribers = ["nexus", "echo"],
            _message_types = [
                "slack_message", "slack_command", "slack_response"
            ],
            _qos = QoSLevel.AT_LEAST_ONCE,
            _retention = "1h",
        ),

        # Telegram Channel
        ChannelDefinition(
            _name = "swarm.external.telegram",
            _description = "Telegram integration channel",
            _channel_type = ChannelType.EXTERNAL,
            _subscribers = ["nexus", "echo"],
            _message_types = [
                "telegram_message", "telegram_command", "telegram_response"
            ],
            _qos = QoSLevel.AT_LEAST_ONCE,
            _retention = "1h",
        ),

        # API Channel - External API requests
        ChannelDefinition(
            _name = "swarm.external.api",
            _description = "External API requests channel",
            _channel_type = ChannelType.EXTERNAL,
            _subscribers = ["nexus"],
            _message_types = [
                "api_request", "api_response", "webhook_event"
            ],
            _qos = QoSLevel.AT_LEAST_ONCE,
            _retention = "1h",
        ),
    ]


def get_all_default_channels() -> List[ChannelDefinition]:
    """Get all default channels.
    
    Returns:
        List of all default channel definitions
    """
    return (
        get_internal_channels() + 
        get_system_channels() + 
        get_external_channels()
    )