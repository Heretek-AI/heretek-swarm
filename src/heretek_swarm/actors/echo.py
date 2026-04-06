"""
Echo Agent - Communication & Protocol Translation

The Echo agent is responsible for:
- Protocol translation between external systems
- Message formatting and normalization
- External API integration gateway
- Communication style adaptation
- Multi-channel message delivery

This agent ensures clear, contextual communication across all swarm interfaces.
"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Set
import uuid

from ..actors.base import AgentActor, ActorMessage
from ..actors.validation import (
    MessageContent,
    validate_message_content,
)

logger = logging.getLogger(__name__)


class CommunicationChannel(Enum):
    """Supported communication channels."""
    INTERNAL = "internal"
    API = "api"
    WEBSOCKET = "websocket"
    SLACK = "slack"
    DISCORD = "discord"
    TELEGRAM = "telegram"
    EMAIL = "email"
    CONSOLE = "console"


class MessagePriority(Enum):
    """Message priority levels."""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


@dataclass
class CommunicationStyle:
    """Communication style configuration."""
    tone: str = "professional"
    formality: float = 0.7
    verbosity: float = 0.5
    emoji_usage: bool = False
    audience: str = "technical"


@dataclass
class TranslationRule:
    """Rule for protocol translation."""
    source_format: str
    target_format: str
    transformation: str
    priority: int = 0


class EchoActor(AgentActor):
    """
    Echo Agent - Communication & Protocol Translation Specialist
    
    Responsibilities:
    - Format messages for different audiences and channels
    - Translate between communication protocols
    - Manage communication styles and tone
    - Handle multi-channel message delivery
    - Ensure message consistency across channels
    """
    
    def __init__(
        self,
        agent_id: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            agent_id=agent_id or f"echo-{uuid.uuid4().hex[:8]}",
            actor_type="echo",
            config=config
        )
        
        # Communication state
        self._active_channels: Set[str] = set()
        self._message_queue: List[Dict[str, Any]] = []
        self._translation_rules: Dict[str, TranslationRule] = {}
        self._communication_styles: Dict[str, CommunicationStyle] = {}
        
        # Channel-specific configurations
        self._channel_configs: Dict[str, Dict[str, Any]] = {
            CommunicationChannel.INTERNAL.value: {
                "max_length": None,
                "format": "markdown",
                "include_metadata": True
            },
            CommunicationChannel.API.value: {
                "max_length": 4096,
                "format": "json",
                "include_metadata": False
            },
            CommunicationChannel.SLACK.value: {
                "max_length": 4000,
                "format": "slack_mrkdwn",
                "include_metadata": False
            },
            CommunicationChannel.DISCORD.value: {
                "max_length": 2000,
                "format": "markdown",
                "include_metadata": False
            },
            CommunicationChannel.TELEGRAM.value: {
                "max_length": 4096,
                "format": "html",
                "include_metadata": False
            },
            CommunicationChannel.EMAIL.value: {
                "max_length": None,
                "format": "html",
                "include_metadata": True
            },
            CommunicationChannel.CONSOLE.value: {
                "max_length": None,
                "format": "text",
                "include_metadata": True
            }
        }
        
        # Default communication style
        self._default_style = CommunicationStyle(
            tone="professional",
            formality=0.7,
            verbosity=0.5,
            emoji_usage=False,
            audience="technical"
        )
        
        # Statistics
        self._stats = {
            "messages_formatted": 0,
            "messages_translated": 0,
            "channels_used": set(),
            "errors": 0
        }
        
        self.logger.info("Echo agent initialized", 
                        agent_id=self.agent_id,
                        channels=list(self._channel_configs.keys()))
    
    @property
    def active_channels(self) -> Set[str]:
        """Get currently active communication channels."""
        return self._active_channels.copy()
    
    @property
    def statistics(self) -> Dict[str, Any]:
        """Get communication statistics."""
        return {
            **self._stats,
            "channels_used": list(self._stats["channels_used"]),
            "queue_size": len(self._message_queue)
        }
    
    async def initialize(self) -> None:
        """Initialize the Echo agent."""
        await super().initialize()
        
        # Register default message handlers
        await self.register_handler("format_message", self._handle_format_message)
        await self.register_handler("translate_protocol", self._handle_translate_protocol)
        await self.register_handler("send_to_channel", self._handle_send_to_channel)
        await self.register_handler("set_communication_style", self._handle_set_communication_style)
        await self.register_handler("get_channel_status", self._handle_get_channel_status)
        await self.register_handler("broadcast_message", self._handle_broadcast_message)
        
        self.logger.info("Echo agent handlers registered", agent_id=self.agent_id)
    
    async def _validate_input(self, content: Dict[str, Any]) -> MessageContent:
        """Validate input using shared validation."""
        return validate_message_content(content)
    
    # =========================================================================
    # Message Handlers
    # =========================================================================
    
    async def _handle_format_message(self, message: ActorMessage) -> Optional[Dict[str, Any]]:
        """
        Format a message for a specific channel and audience.
        
        Content schema:
        {
            "content": str,
            "channel": str,
            "style": Optional[Dict],
            "priority": Optional[str]
        }
        """
        try:
            validated = await self._validate_input(message.content)
            content = validated.content
            channel = content.get("channel", "internal")
            style_config = content.get("style")
            priority = content.get("priority", "normal")
            
            # Get or create communication style
            style = self._get_communication_style(style_config)
            
            # Format the message
            formatted = await self._format_for_channel(
                content=content.get("content", ""),
                channel=channel,
                style=style,
                priority=priority
            )
            
            self._stats["messages_formatted"] += 1
            
            return {
                "status": "success",
                "formatted_message": formatted,
                "channel": channel,
                "style_applied": style.tone
            }
            
        except Exception as e:
            self._stats["errors"] += 1
            self.logger.error("Failed to format message", 
                            error=str(e),
                            channel=message.content.get("channel", "unknown"))
            return {"status": "error", "error": str(e)}
    
    async def _handle_translate_protocol(self, message: ActorMessage) -> Optional[Dict[str, Any]]:
        """
        Translate content between communication protocols.
        
        Content schema:
        {
            "content": Any,
            "source_format": str,
            "target_format": str
        }
        """
        try:
            content = message.content
            source_format = content.get("source_format", "internal")
            target_format = content.get("target_format", "json")
            payload = content.get("content")
            
            # Perform translation
            translated = await self._translate_content(
                content=payload,
                source_format=source_format,
                target_format=target_format
            )
            
            self._stats["messages_translated"] += 1
            
            return {
                "status": "success",
                "translated_content": translated,
                "source_format": source_format,
                "target_format": target_format
            }
            
        except Exception as e:
            self._stats["errors"] += 1
            self.logger.error("Failed to translate protocol",
                            error=str(e),
                            source=message.content.get("source_format"),
                            target=message.content.get("target_format"))
            return {"status": "error", "error": str(e)}
    
    async def _handle_send_to_channel(self, message: ActorMessage) -> Optional[Dict[str, Any]]:
        """
        Send a formatted message to a specific channel.
        
        Content schema:
        {
            "channel": str,
            "message": str,
            "metadata": Optional[Dict]
        }
        """
        try:
            content = message.content
            channel = content.get("channel", "internal")
            message_text = content.get("message", "")
            metadata = content.get("metadata", {})
            
            # Validate channel exists
            if channel not in self._channel_configs:
                return {
                    "status": "error",
                    "error": f"Unknown channel: {channel}"
                }
            
            # Simulate sending (in production, integrate with actual channel APIs)
            send_result = await self._send_to_channel_impl(
                channel=channel,
                message=message_text,
                metadata=metadata
            )
            
            self._stats["channels_used"].add(channel)
            
            return {
                "status": "success" if send_result else "partial",
                "channel": channel,
                "delivered": send_result
            }
            
        except Exception as e:
            self._stats["errors"] += 1
            self.logger.error("Failed to send to channel",
                            error=str(e),
                            channel=message.content.get("channel"))
            return {"status": "error", "error": str(e)}
    
    async def _handle_set_communication_style(self, message: ActorMessage) -> Optional[Dict[str, Any]]:
        """
        Set or update communication style for a context.
        
        Content schema:
        {
            "context": str,
            "style": {
                "tone": str,
                "formality": float,
                "verbosity": float,
                "emoji_usage": bool,
                "audience": str
            }
        }
        """
        try:
            content = message.content
            context = content.get("context", "default")
            style_config = content.get("style", {})
            
            # Create and store communication style
            style = CommunicationStyle(
                tone=style_config.get("tone", "professional"),
                formality=style_config.get("formality", 0.7),
                verbosity=style_config.get("verbosity", 0.5),
                emoji_usage=style_config.get("emoji_usage", False),
                audience=style_config.get("audience", "technical")
            )
            
            self._communication_styles[context] = style
            
            return {
                "status": "success",
                "context": context,
                "style": {
                    "tone": style.tone,
                    "formality": style.formality,
                    "verbosity": style.verbosity,
                    "emoji_usage": style.emoji_usage,
                    "audience": style.audience
                }
            }
            
        except Exception as e:
            self._stats["errors"] += 1
            self.logger.error("Failed to set communication style",
                            error=str(e),
                            context=message.content.get("context"))
            return {"status": "error", "error": str(e)}
    
    async def _handle_get_channel_status(self, message: ActorMessage) -> Optional[Dict[str, Any]]:
        """
        Get status of communication channels.
        
        Content schema:
        {
            "channel": Optional[str] - Specific channel or all if None
        }
        """
        try:
            channel = message.content.get("channel")
            
            if channel:
                # Return specific channel status
                config = self._channel_configs.get(channel, {})
                return {
                    "status": "success",
                    "channel": channel,
                    "active": channel in self._active_channels,
                    "config": config
                }
            else:
                # Return all channel statuses
                channel_statuses = {}
                for ch, config in self._channel_configs.items():
                    channel_statuses[ch] = {
                        "active": ch in self._active_channels,
                        "config": config
                    }
                
                return {
                    "status": "success",
                    "channels": channel_statuses,
                    "statistics": self.statistics
                }
                
        except Exception as e:
            self._stats["errors"] += 1
            self.logger.error("Failed to get channel status",
                            error=str(e))
            return {"status": "error", "error": str(e)}
    
    async def _handle_broadcast_message(self, message: ActorMessage) -> Optional[Dict[str, Any]]:
        """
        Broadcast a message to multiple channels.
        
        Content schema:
        {
            "content": str,
            "channels": List[str],
            "style": Optional[Dict],
            "priority": Optional[str]
        }
        """
        try:
            content = message.content
            message_content = content.get("content", "")
            channels = content.get("channels", ["internal"])
            style_config = content.get("style")
            priority = content.get("priority", "normal")
            
            # Get communication style
            style = self._get_communication_style(style_config)
            
            # Broadcast to each channel
            results = {}
            for channel in channels:
                try:
                    formatted = await self._format_for_channel(
                        content=message_content,
                        channel=channel,
                        style=style,
                        priority=priority
                    )
                    
                    send_result = await self._send_to_channel_impl(
                        channel=channel,
                        message=formatted,
                        metadata={"priority": priority}
                    )
                    
                    results[channel] = {
                        "status": "success" if send_result else "failed",
                        "delivered": send_result
                    }
                    
                    if send_result:
                        self._stats["channels_used"].add(channel)
                        
                except Exception as e:
                    results[channel] = {
                        "status": "error",
                        "error": str(e)
                    }
                    self._stats["errors"] += 1
            
            self._stats["messages_formatted"] += len(channels)
            
            return {
                "status": "success",
                "results": results,
                "total_channels": len(channels),
                "successful": sum(1 for r in results.values() if r.get("status") == "success")
            }
            
        except Exception as e:
            self._stats["errors"] += 1
            self.logger.error("Failed to broadcast message",
                            error=str(e))
            return {"status": "error", "error": str(e)}
    
    # =========================================================================
    # Communication Formatting
    # =========================================================================
    
    def _get_communication_style(self, style_config: Optional[Dict]) -> CommunicationStyle:
        """Get or create communication style."""
        if style_config:
            return CommunicationStyle(
                tone=style_config.get("tone", "professional"),
                formality=style_config.get("formality", 0.7),
                verbosity=style_config.get("verbosity", 0.5),
                emoji_usage=style_config.get("emoji_usage", False),
                audience=style_config.get("audience", "technical")
            )
        return self._default_style
    
    async def _format_for_channel(
        self,
        content: str,
        channel: str,
        style: CommunicationStyle,
        priority: str = "normal"
    ) -> str:
        """Format content for a specific channel and style."""
        config = self._channel_configs.get(channel, self._channel_configs["internal"])
        max_length = config.get("max_length")
        format_type = config.get("format", "text")
        
        # Apply style transformations
        formatted = self._apply_style(content, style)
        
        # Apply channel-specific formatting
        if format_type == "json":
            formatted = self._format_as_json(formatted, priority)
        elif format_type == "slack_mrkdwn":
            formatted = self._format_for_slack(formatted)
        elif format_type == "html":
            formatted = self._format_as_html(formatted, style)
        elif format_type == "markdown":
            formatted = self._format_as_markdown(formatted, style)
        
        # Truncate if necessary
        if max_length and len(formatted) > max_length:
            formatted = formatted[:max_length - 3] + "..."
        
        return formatted
    
    def _apply_style(self, content: str, style: CommunicationStyle) -> str:
        """Apply communication style to content."""
        # Adjust tone
        if style.tone == "friendly":
            content = f"Hello! {content}"
        elif style.tone == "formal":
            content = f"Please be advised: {content}"
        elif style.tone == "urgent":
            content = f"⚠️ URGENT: {content}" if style.emoji_usage else f"URGENT: {content}"
        
        # Adjust verbosity
        if style.verbosity < 0.3:
            # Make more concise
            content = content[:200] + "..." if len(content) > 200 else content
        
        # Add emoji if enabled
        if style.emoji_usage and style.tone == "friendly":
            content = content + " ✨"
        
        return content
    
    def _format_as_json(self, content: str, priority: str) -> str:
        """Format content as JSON."""
        import json
        return json.dumps({
            "message": content,
            "priority": priority,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
    
    def _format_for_slack(self, content: str) -> str:
        """Format content for Slack."""
        # Convert basic markdown to Slack mrkdwn
        content = content.replace("**", "*")  # Bold
        content = content.replace("__", "_")  # Italic
        return content
    
    def _format_as_html(self, content: str, style: CommunicationStyle) -> str:
        """Format content as HTML."""
        # Basic HTML formatting
        content = content.replace("\n", "<br>")
        content = content.replace("**", "<strong>").replace("**", "</strong>")
        
        if style.tone == "friendly":
            return f"<p style='color: #28a745;'>{content}</p>"
        elif style.tone == "urgent":
            return f"<p style='color: #dc3545; font-weight: bold;'>{content}</p>"
        
        return f"<p>{content}</p>"
    
    def _format_as_markdown(self, content: str, style: CommunicationStyle) -> str:
        """Format content as markdown."""
        if style.tone == "formal":
            return f"## Message\n\n{content}"
        return content
    
    # =========================================================================
    # Protocol Translation
    # =========================================================================
    
    async def _translate_content(
        self,
        content: Any,
        source_format: str,
        target_format: str
    ) -> Any:
        """Translate content between formats."""
        import json
        
        # Handle common translations
        if source_format == "json" and target_format == "text":
            if isinstance(content, dict):
                return json.dumps(content, indent=2)
            return str(content)
        
        elif source_format == "text" and target_format == "json":
            return {"content": str(content)}
        
        elif source_format == "internal" and target_format == "api":
            # Convert internal format to API response
            return {
                "success": True,
                "data": content,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        
        elif source_format == "api" and target_format == "internal":
            # Extract data from API response
            if isinstance(content, dict):
                return content.get("data", content)
            return content
        
        # Default: return as-is
        return content
    
    # =========================================================================
    # Channel Delivery
    # =========================================================================
    
    async def _send_to_channel_impl(
        self,
        channel: str,
        message: str,
        metadata: Dict[str, Any]
    ) -> bool:
        """
        Send message to channel (implementation stub).
        
        In production, this would integrate with:
        - Slack API
        - Discord API
        - Telegram Bot API
        - Email SMTP/SendGrid
        - WebSocket connections
        """
        # Log the send attempt
        self.logger.info("Sending to channel",
                        channel=channel,
                        message_length=len(message),
                        metadata=metadata)
        
        # Add to message queue for processing
        self._message_queue.append({
            "channel": channel,
            "message": message,
            "metadata": metadata,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
        
        # Keep queue bounded
        if len(self._message_queue) > 1000:
            self._message_queue = self._message_queue[-1000:]
        
        # Simulate successful send
        return True
    
    # =========================================================================
    # Lifecycle
    # =========================================================================
    
    async def terminate(self) -> None:
        """Terminate the Echo agent."""
        # Process remaining messages
        if self._message_queue:
            self.logger.info("Processing remaining messages",
                            count=len(self._message_queue))
        
        await super().terminate()
        self.logger.info("Echo agent terminated", agent_id=self.agent_id)
