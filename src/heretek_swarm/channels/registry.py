"""
Channel Registry for Heretek Swarm

Provides formal communication channel architecture for agent-to-agent
communication using NATS subjects and A2A protocol patterns.

Implements channel subscription management, message routing, and
tier-based agent organization.
"""

from typing import Dict, Any, List, Optional, Set
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
import structlog

logger = structlog.get_logger(__name__)


class ChannelType(str, Enum):
    """Channel types for different communication patterns."""
    INTERNAL = "internal"       # Agent-to-agent within swarm
    EXTERNAL = "external"       # External system integration
    SYSTEM = "system"           # System-wide broadcasts
    CONSENSUS = "consensus"     # MAKER consensus voting
    HEALTH = "health"           # Health monitoring


class QoSLevel(str, Enum):
    """Quality of Service levels for message delivery."""
    AT_MOST_ONCE = "at-most-once"    # Fire and forget
    AT_LEAST_ONCE = "at-least-once"  # Guaranteed delivery with possible duplicates
    EXACTLY_ONCE = "exactly-once"    # Guaranteed single delivery


@dataclass
class ChannelDefinition:
    """
    Channel definition with routing and QoS configuration.
    
    Attributes:
        name: Channel identifier (e.g., "swarm.internal.triad")
        description: Human-readable description
        channel_type: Type of channel (internal, external, system)
        subscribers: List of agent IDs subscribed to this channel
        message_types: Allowed message types for this channel
        qos: Quality of Service level
        retention: Message retention period (e.g., "24h", "7d")
        priority: Channel priority (low, normal, high, critical)
    """
    name: str
    description: str
    channel_type: ChannelType
    subscribers: List[str] = field(default_factory=list)
    message_types: List[str] = field(default_factory=list)
    qos: QoSLevel = QoSLevel.AT_LEAST_ONCE
    retention: str = "24h"
    priority: str = "normal"
    enabled: bool = True


@dataclass
class ChannelMessage:
    """
    Standardized message structure for all channel communication.
    
    Follows the SwarmMessage pattern from the proposal documents.
    """
    # Routing
    subject: str                    # NATS subject / channel
    correlation_id: str             # Unique message ID
    reply_to: Optional[str]         # Response subject (for request-reply)
    
    # Sender/Receiver
    sender_agent: str               # Sending agent ID
    target_agents: List[str]        # Target agent IDs (or ["*"] for broadcast)
    
    # Content
    message_type: str               # Type identifier
    content: Dict[str, Any]         # Message payload
    metadata: Dict[str, Any]        # Additional context
    
    # Timing
    timestamp: str                  # ISO8601 timestamp
    ttl_seconds: Optional[int]      # Time-to-live (optional)
    
    # Priority
    priority: str = "normal"        # low, normal, high, critical
    requires_ack: bool = False      # Require acknowledgment
    
    # Context
    workflow_id: Optional[str] = None      # Associated workflow
    task_id: Optional[str] = None          # Associated task
    session_id: Optional[str] = None       # User/session context
    
    @classmethod
    def create(
        cls,
        subject: str,
        message_type: str,
        content: Dict[str, Any],
        sender_agent: str,
        target_agents: Optional[List[str]] = None,
        reply_to: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        priority: str = "normal",
        requires_ack: bool = False,
        workflow_id: Optional[str] = None,
        task_id: Optional[str] = None,
        session_id: Optional[str] = None,
        ttl_seconds: Optional[int] = None,
    ) -> "ChannelMessage":
        """Factory method for creating messages with defaults."""
        import uuid
        
        return cls(
            subject=subject,
            correlation_id=str(uuid.uuid4()),
            reply_to=reply_to,
            sender_agent=sender_agent,
            target_agents=target_agents or ["*"],
            message_type=message_type,
            content=content,
            metadata=metadata or {},
            timestamp=datetime.now(timezone.utc).isoformat(),
            ttl_seconds=ttl_seconds,
            priority=priority,
            requires_ack=requires_ack,
            workflow_id=workflow_id,
            task_id=task_id,
            session_id=session_id,
        )


class ChannelRegistry:
    """
    Registry for communication channels.
    
    Manages channel subscriptions, message routing, and provides
    NATS subject mapping for the event mesh.
    """
    
    def __init__(self):
        self._channels: Dict[str, ChannelDefinition] = {}
        self._agent_subscriptions: Dict[str, Set[str]] = {}  # agent_id -> set of channels
        self._message_handlers: Dict[str, callable] = {}
        self._stats: Dict[str, Dict] = {}
        self._setup_default_channels()
    
    def _setup_default_channels(self):
        """Set up default channel architecture from proposal documents."""
        
        # === INTERNAL AGENT CHANNELS ===
        
        # Triad Channel - Core governance deliberation
        self.register(ChannelDefinition(
            name="swarm.internal.triad",
            description="Core governance deliberation channel",
            channel_type=ChannelType.INTERNAL,
            subscribers=["steward", "alpha", "beta", "charlie"],
            message_types=[
                "proposal", "analysis", "validation", "challenge", 
                "decision", "deliberation_start", "deliberation_complete"
            ],
            qos=QoSLevel.AT_LEAST_ONCE,
            retention="24h",
            priority="high",
        ))
        
        # Coordination Channel - Multi-agent task coordination
        self.register(ChannelDefinition(
            name="swarm.internal.coordination",
            description="Multi-agent task coordination channel",
            channel_type=ChannelType.INTERNAL,
            subscribers=["coordinator", "catalyst", "chronos", "metis"],
            message_types=[
                "task_start", "task_complete", "dependency_ready", 
                "blocker", "resource_request", "status_update"
            ],
            qos=QoSLevel.AT_LEAST_ONCE,
            retention="12h",
        ))
        
        # Safety Channel - Security and safety alerts
        self.register(ChannelDefinition(
            name="swarm.internal.safety",
            description="Security and safety alerts channel",
            channel_type=ChannelType.INTERNAL,
            subscribers=["sentinel", "sentinel-prime", "arbiter", "steward"],
            message_types=[
                "threat_detected", "quarantine", "all_clear", 
                "incident_report", "validation_request", "security_alert"
            ],
            qos=QoSLevel.EXACTLY_ONCE,
            retention="7d",
            priority="critical",
        ))
        
        # Memory Channel - Memory and knowledge operations
        self.register(ChannelDefinition(
            name="swarm.internal.memory",
            description="Memory and knowledge operations channel",
            channel_type=ChannelType.INTERNAL,
            subscribers=["historian", "prism", "habit-forge"],
            message_types=[
                "store_request", "retrieve_request", "learn_pattern", 
                "forget", "context_request", "lineage_query"
            ],
            qos=QoSLevel.AT_MOST_ONCE,
            retention="1h",
        ))
        
        # Exploration Channel - Research and implementation
        self.register(ChannelDefinition(
            name="swarm.internal.exploration",
            description="Research and implementation channel",
            channel_type=ChannelType.INTERNAL,
            subscribers=["explorer", "examiner", "dreamer", "coder"],
            message_types=[
                "research_task", "analysis_result", "creative_request", 
                "code_review", "discovery", "implementation_complete"
            ],
            qos=QoSLevel.AT_LEAST_ONCE,
            retention="6h",
        ))
        
        # Perception Channel - Input processing and translation
        self.register(ChannelDefinition(
            name="swarm.internal.perception",
            description="Input processing and translation channel",
            channel_type=ChannelType.INTERNAL,
            subscribers=["perceiver", "perceiver-plus", "empath", "echo"],
            message_types=[
                "input_received", "sentiment_analysis", "translation_request", 
                "feature_extracted", "format_request", "broadcast_request"
            ],
            qos=QoSLevel.AT_MOST_ONCE,
            retention="1h",
        ))
        
        # === SYSTEM CHANNELS ===
        
        # Health Channel - Health monitoring (all agents)
        self.register(ChannelDefinition(
            name="swarm.system.health",
            description="Health monitoring channel (all agents)",
            channel_type=ChannelType.SYSTEM,
            subscribers=["*"],  # Wildcard - all agents
            message_types=[
                "heartbeat", "health_status", "error_report", 
                "restart_request", "scaling_request"
            ],
            qos=QoSLevel.AT_MOST_ONCE,
            retention="1h",
        ))
        
        # Consciousness Channel - Consciousness metrics broadcast
        self.register(ChannelDefinition(
            name="swarm.system.consciousness",
            description="Consciousness metrics broadcast channel",
            channel_type=ChannelType.SYSTEM,
            subscribers=["*"],
            message_types=[
                "phi_update", "attention_state", "workspace_broadcast", 
                "integration_metric", "global_state"
            ],
            qos=QoSLevel.AT_MOST_ONCE,
            retention="30m",
        ))
        
        # Consensus Channel - MAKER consensus voting
        self.register(ChannelDefinition(
            name="swarm.system.consensus",
            description="MAKER consensus voting channel",
            channel_type=ChannelType.CONSENSUS,
            subscribers=["steward", "alpha", "beta", "charlie"],
            message_types=[
                "vote_cast", "consensus_reached", "red_flag", 
                "reputation_update", "proposal_start", "proposal_complete"
            ],
            qos=QoSLevel.EXACTLY_ONCE,
            retention="24h",
            priority="high",
        ))
        
        # === EXTERNAL CHANNELS ===
        
        # Discord Channel
        self.register(ChannelDefinition(
            name="swarm.external.discord",
            description="Discord integration channel",
            channel_type=ChannelType.EXTERNAL,
            subscribers=["nexus", "echo"],
            message_types=[
                "discord_message", "discord_command", "discord_response"
            ],
            qos=QoSLevel.AT_LEAST_ONCE,
            retention="1h",
        ))
        
        # Slack Channel
        self.register(ChannelDefinition(
            name="swarm.external.slack",
            description="Slack integration channel",
            channel_type=ChannelType.EXTERNAL,
            subscribers=["nexus", "echo"],
            message_types=[
                "slack_message", "slack_command", "slack_response"
            ],
            qos=QoSLevel.AT_LEAST_ONCE,
            retention="1h",
        ))
        
        # Telegram Channel
        self.register(ChannelDefinition(
            name="swarm.external.telegram",
            description="Telegram integration channel",
            channel_type=ChannelType.EXTERNAL,
            subscribers=["nexus", "echo"],
            message_types=[
                "telegram_message", "telegram_command", "telegram_response"
            ],
            qos=QoSLevel.AT_LEAST_ONCE,
            retention="1h",
        ))
        
        # API Channel - External API requests
        self.register(ChannelDefinition(
            name="swarm.external.api",
            description="External API requests channel",
            channel_type=ChannelType.EXTERNAL,
            subscribers=["nexus"],
            message_types=[
                "api_request", "api_response", "webhook_event"
            ],
            qos=QoSLevel.AT_LEAST_ONCE,
            retention="1h",
        ))
        
        # Workflow Channel - Workflow events
        self.register(ChannelDefinition(
            name="swarm.workflow.events",
            description="Workflow lifecycle events channel",
            channel_type=ChannelType.SYSTEM,
            subscribers=["*"],
            message_types=[
                "workflow_start", "workflow_phase", "workflow_complete", 
                "workflow_error", "workflow_checkpoint"
            ],
            qos=QoSLevel.AT_LEAST_ONCE,
            retention="24h",
        ))
    
    def register(self, channel: ChannelDefinition) -> None:
        """
        Register a channel.
        
        Args:
            channel: Channel definition to register
        """
        if channel.name in self._channels:
            logger.warning("channel_registration_conflict", channel_name=channel.name)
            raise ValueError(f"Channel {channel.name} already registered")
        
        self._channels[channel.name] = channel
        self._stats[channel.name] = {
            "messages_published": 0,
            "messages_delivered": 0,
            "errors": 0,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        
        # Update agent subscriptions
        for subscriber in channel.subscribers:
            if subscriber not in self._agent_subscriptions:
                self._agent_subscriptions[subscriber] = set()
            self._agent_subscriptions[subscriber].add(channel.name)
        
        logger.info("channel_registered", name=channel.name, type=channel.channel_type.value)
    
    def unregister(self, name: str) -> bool:
        """Unregister a channel by name."""
        if name not in self._channels:
            return False
        
        channel = self._channels.pop(name)
        self._stats.pop(name)
        
        # Remove from agent subscriptions
        for agent_id, channels in self._agent_subscriptions.items():
            channels.discard(name)
        
        logger.info("channel_unregistered", name=name)
        return True
    
    def get_channel(self, name: str) -> Optional[ChannelDefinition]:
        """Get a channel by name."""
        return self._channels.get(name)
    
    def list_channels(
        self, 
        channel_type: Optional[ChannelType] = None,
        subscriber: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        List channels with optional filtering.
        
        Args:
            channel_type: Filter by channel type
            subscriber: Filter by agent subscriber
            
        Returns:
            List of channel definitions
        """
        channels = self._channels.values()
        
        if channel_type:
            channels = [c for c in channels if c.channel_type == channel_type]
        
        if subscriber:
            channels = [c for c in channels if subscriber in c.subscribers or "*" in c.subscribers]
        
        return [
            {
                "name": c.name,
                "description": c.description,
                "type": c.channel_type.value,
                "subscribers": c.subscribers,
                "message_types": c.message_types,
                "qos": c.qos.value,
                "retention": c.retention,
                "priority": c.priority,
                "enabled": c.enabled,
            }
            for c in channels if c.enabled
        ]
    
    def get_subscriptions(self, agent_id: str) -> List[str]:
        """Get all channels an agent is subscribed to."""
        subscriptions = self._agent_subscriptions.get(agent_id, set()).copy()
        
        # Add wildcard subscriptions
        for channel in self._channels.values():
            if "*" in channel.subscribers and channel.enabled:
                subscriptions.add(channel.name)
        
        return list(subscriptions)
    
    def get_subscribers(self, channel_name: str) -> List[str]:
        """Get all agents subscribed to a channel."""
        channel = self._channels.get(channel_name)
        if not channel:
            return []
        
        subscribers = channel.subscribers.copy()
        
        # Expand wildcard
        if "*" in subscribers:
            subscribers.remove("*")
            subscribers.extend(list(self._agent_subscriptions.keys()))
        
        return list(set(subscribers))
    
    def get_stats(self, channel_name: str) -> Optional[Dict[str, Any]]:
        """Get statistics for a channel."""
        return self._stats.get(channel_name)
    
    def record_message(self, channel_name: str, delivered: bool = True) -> None:
        """Record a message published to a channel."""
        if channel_name in self._stats:
            self._stats[channel_name]["messages_published"] += 1
            if delivered:
                self._stats[channel_name]["messages_delivered"] += 1
    
    def record_error(self, channel_name: str) -> None:
        """Record an error on a channel."""
        if channel_name in self._stats:
            self._stats[channel_name]["errors"] += 1
    
    def subscribe_agent(self, agent_id: str, channel_name: str) -> bool:
        """Subscribe an agent to a channel."""
        if channel_name not in self._channels:
            return False
        
        if agent_id not in self._agent_subscriptions:
            self._agent_subscriptions[agent_id] = set()
        
        self._agent_subscriptions[agent_id].add(channel_name)
        
        # Add agent to channel subscribers
        if agent_id not in self._channels[channel_name].subscribers:
            self._channels[channel_name].subscribers.append(agent_id)
        
        logger.debug("agent_subscribed", agent_id=agent_id, channel=channel_name)
        return True
    
    def unsubscribe_agent(self, agent_id: str, channel_name: str) -> bool:
        """Unsubscribe an agent from a channel."""
        if agent_id not in self._agent_subscriptions:
            return False
        
        self._agent_subscriptions[agent_id].discard(channel_name)
        
        # Remove from channel subscribers
        if channel_name in self._channels:
            if agent_id in self._channels[channel_name].subscribers:
                self._channels[channel_name].subscribers.remove(agent_id)
        
        logger.debug("agent_unsubscribed", agent_id=agent_id, channel=channel_name)
        return True
    
    def get_nats_subject(self, channel_name: str) -> str:
        """Convert channel name to NATS subject format."""
        return channel_name.replace(".", ".")
    
    def get_routing_rules(self) -> Dict[str, Any]:
        """
        Get task routing rules for the Steward agent.
        
        Returns routing configuration based on task type keywords.
        """
        return {
            "deliberation": {
                "keywords": ["decide", "evaluate", "assess", "recommend", "approve"],
                "channel": "swarm.internal.triad",
                "agents": ["alpha", "beta", "charlie", "historian"],
                "consensus_required": True,
            },
            "research": {
                "keywords": ["research", "investigate", "gather", "discover", "find"],
                "channel": "swarm.internal.exploration",
                "agents": ["explorer", "examiner", "historian"],
                "consensus_required": False,
            },
            "implementation": {
                "keywords": ["build", "create", "implement", "code", "develop"],
                "channel": "swarm.internal.exploration",
                "agents": ["dreamer", "coder", "examiner"],
                "consensus_required": False,
            },
            "security": {
                "keywords": ["threat", "vulnerability", "attack", "breach", "unsafe"],
                "channel": "swarm.internal.safety",
                "agents": ["sentinel", "sentinel-prime", "arbiter"],
                "consensus_required": True,
                "priority": "critical",
            },
            "query": {
                "keywords": ["what", "when", "where", "who", "find information"],
                "channel": "swarm.internal.memory",
                "agents": ["historian", "perceiver-plus"],
                "consensus_required": False,
            },
            "external": {
                "keywords": ["api", "webhook", "external", "integration"],
                "channel": "swarm.external.api",
                "agents": ["nexus", "echo"],
                "consensus_required": False,
            },
        }
    
    def get_all_stats(self) -> Dict[str, Dict[str, Any]]:
        """Get statistics for all channels."""
        return self._stats.copy()


# ============================================================================
# Agent Communication Groups
# ============================================================================

class CommunicationGroup:
    """
    Communication group for organizing agent collaboration patterns.
    
    Groups provide higher-level abstractions over individual channels
    for common collaboration patterns.
    """
    
    def __init__(
        self,
        name: str,
        members: List[str],
        primary_channel: str,
        topics: List[str],
        description: str = "",
        consensus_enabled: bool = False,
        rag_enabled: bool = False,
    ):
        self.name = name
        self.members = members
        self.primary_channel = primary_channel
        self.topics = topics
        self.description = description
        self.consensus_enabled = consensus_enabled
        self.rag_enabled = rag_enabled
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "name": self.name,
            "members": self.members,
            "primary_channel": self.primary_channel,
            "topics": self.topics,
            "description": self.description,
            "consensus_enabled": self.consensus_enabled,
            "rag_enabled": self.rag_enabled,
        }


class GroupRegistry:
    """Registry for communication groups."""
    
    def __init__(self, channel_registry: ChannelRegistry):
        self._groups: Dict[str, CommunicationGroup] = {}
        self._channel_registry = channel_registry
        self._setup_default_groups()
    
    def _setup_default_groups(self):
        """Set up default communication groups from proposal documents."""
        
        # Governance Group
        self.register(CommunicationGroup(
            name="governance",
            members=["steward", "alpha", "beta", "charlie", "historian"],
            primary_channel="swarm.internal.triad",
            topics=["decisions", "deliberations", "governance"],
            description="Core governance and decision making",
            consensus_enabled=True,
        ))
        
        # Execution Group
        self.register(CommunicationGroup(
            name="execution",
            members=["coordinator", "coder", "explorer", "examiner"],
            primary_channel="swarm.internal.coordination",
            topics=["tasks", "execution", "results"],
            description="Task planning and execution",
        ))
        
        # Safety Group
        self.register(CommunicationGroup(
            name="safety",
            members=["sentinel", "sentinel-prime", "arbiter", "beta"],
            primary_channel="swarm.internal.safety",
            topics=["security", "validation", "alerts"],
            description="Security and validation",
            consensus_enabled=True,
        ))
        
        # Memory Group
        self.register(CommunicationGroup(
            name="memory",
            members=["historian", "metis", "perceiver", "perceiver-plus"],
            primary_channel="swarm.internal.memory",
            topics=["memory", "context", "retrieval"],
            description="Knowledge management and RAG",
            rag_enabled=True,
        ))
        
        # External Integration Group
        self.register(CommunicationGroup(
            name="external",
            members=["nexus", "echo", "catalyst"],
            primary_channel="swarm.external.api",
            topics=["external", "webhooks", "events"],
            description="External system integration",
        ))
    
    def register(self, group: CommunicationGroup) -> None:
        """Register a communication group."""
        if group.name in self._groups:
            raise ValueError(f"Group {group.name} already registered")
        
        self._groups[group.name] = group
        
        # Subscribe all members to the primary channel
        for member in group.members:
            self._channel_registry.subscribe_agent(member, group.primary_channel)
        
        logger.info("group_registered", name=group.name, members=group.members)
    
    def get_group(self, name: str) -> Optional[CommunicationGroup]:
        """Get a group by name."""
        return self._groups.get(name)
    
    def list_groups(self) -> List[Dict[str, Any]]:
        """List all registered groups."""
        return [g.to_dict() for g in self._groups.values()]
    
    def get_group_members(self, name: str) -> List[str]:
        """Get members of a group."""
        group = self._groups.get(name)
        return group.members if group else []


# Global instance
_channel_registry_instance: Optional[ChannelRegistry] = None


def get_channel_registry() -> ChannelRegistry:
    """Get or create the channel registry singleton."""
    global _channel_registry_instance
    if _channel_registry_instance is None:
        _channel_registry_instance = ChannelRegistry()
    return _channel_registry_instance
