"""
Slack Bot Integration - PraisonAI Pattern

Slack bot for agent interaction and notifications.
Reference: PraisonAI Slack integration
"""

import os
from typing import Optional, Dict, Any
import structlog

try:
    from slack_sdk import WebClient
    from slack_sdk.errors import SlackApiError
    SLACK_AVAILABLE = True
except ImportError:
    SLACK_AVAILABLE = False
    _WebClient = None
    _SlackApiError = None
    _logger = structlog.get_logger(__name__)

class SlackBot:
    """
    Slack bot for Heretek Swarm interaction.
    
    Features:
    - Chat with agents via DM or channels
    - Task submission commands
    - Status notifications
    - Handoff updates
    - Rich message formatting with blocks
    """
    
    def __init__(self, token: Optional[str], agent_runtime, handoff_manager, intents: Optional[Any]):
        self.token = token or os.getenv("SLACK_BOT_TOKEN")
        self.agent_runtime = agent_runtime
        self.handoff_manager = handoff_manager
        self._bot = None
        self._running = False
        
        if not SLACK_AVAILABLE:
            logger.warning("slack_bot_unavailable", message="slack_sdk not installed")
            return
        
        # Set up intents
        if intents is None:
            _intents = {
                "message_content": True,
                "blocks": True,
                "members": True,
                "chat": True,
            }
        else:
            _intents = intents
        
        # Initialize bot
        self._bot = WebClient(token=self.token)
        
        # Register events
        self._bot.event(self.on_message)
    
    async def initialize(self) -> bool:
        """Initialize bot."""
        if not SLACK_AVAILABLE:
            return False
        
        if not self.token:
            logger.warning("slack_token_missing")
            return False
        
        try:
            # Test connection
            _auth_result = await self._bot.auth_test()
            logger.info("slack_auth_test", success=auth_result)
        except Exception as e:
            logger.error("slack_init_failed", error=str(e))
            return False
        
        logger.info("slack_bot_initialized")
        return True
    
    async def start(self) -> None:
        """Start bot."""
        if not self._bot:
            logger.warning("slack_bot_not_initialized")
            return
        
        self._running = True
        await self._bot.start()
        logger.info("slack_bot_started")
    
    async def stop(self) -> None:
        """Stop bot."""
        if not self._bot:
            return
        
        self._running = False
        await self._bot.stop()
        logger.info("slack_bot_stopped")
    
    async def send_notification(self, channel: str, message: str, blocks: Optional[list]) -> bool:
        """
        Send notification to Slack channel.
        
        Args:
            channel: Channel ID or name
            message: Message text
            blocks: Optional Slack blocks for rich formatting
            authenticated: Authentication token
        
        Returns:
            Success status
        """
        try:
            if blocks:
                _result = await self._bot.chat_postMessage(
                    _channel = channel,
                    _blocks = blocks,
                    _text = ""
                )
            else:
                _result = await self._bot.chat_postMessage(
                    _channel = channel,
                    _text = message
                )
            
            if not result["ok"]:
                logger.error("slack_notification_failed", channel=channel)
                return False
            
            logger.info("slack_notification_sent", channel=channel)
            return True
        
        except Exception as e:
            logger.error("slack_notification_error", error=str(e))
            return False
    
    async def send_agent_status(self, agent_id: str, status: str, details: Optional[Dict[str, Any]]) -> bool:
        """
        Send agent status update to Slack.
        
        Args:
            agent_id: Agent ID
            status: Agent status
            details: Optional additional details
            authenticated: Authentication token
        
        Returns:
            Success status
        """
        try:
            _blocks = [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"Agent Status: {status}"
                    }
                },
                {
                    "type": "context",
                    "elements": [
                        {
                            "type": "mrkdwn",
                            "text": f"Agent ID: {agent_id}"
                        }
                    ]
                }
            ]
            
            if details:
                blocks[1]["fields"] = [
                    {
                        "type": "mrkdwn",
                        "text": "Details:",
                        "fields": [
                            {
                                "type": "plain_text",
                                "text": f"Type: {details.get('type', 'N/A')}"
                            },
                            {
                                "type": "plain_text",
                                "text": f"Runtime: {details.get('runtime', 'N/A')}"
                            },
                            {
                                "type": "plain_text",
                                "text": f"Last Activity: {details.get('last_activity', 'N/A')}"
                            },
                        ]
                    }
                ]
            
            _result = await self._bot.chat_postMessage(
                _channel = self._get_status_channel(),
                _blocks = blocks
            )
            
            return result["ok"]
        
        except Exception as e:
            logger.error("slack_agent_status_failed", agent_id=agent_id, error=str(e))
            return False
    
    async def send_handoff_notification(self, from_agent: str, to_agent: str, reason: str, context: Optional[str]) -> bool:
        """
        Send handoff notification between agents.
        
        Args:
            from_agent: Source agent ID
            to_agent: Target agent ID
            reason: Handoff reason
            context: Optional context information
            authenticated: Authentication token
        
        Returns:
            Success status
        """
        try:
            _blocks = [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": "Agent Handoff"
                    }
                },
                {
                    "type": "context",
                    "elements": [
                        {
                            "type": "mrkdwn",
                            "text": f"From: {from_agent}"
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"To: {to_agent}"
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"Reason: {reason}"
                        },
                        {
                            "type": "plain_text",
                            "text": context if context else ""
                        }
                    ]
                }
            ]
            
            _result = await self._bot.chat_postMessage(
                _channel = self._get_status_channel(),
                _blocks = blocks
            )
            
            return result["ok"]
        
        except Exception as e:
            logger.error("slack_handoff_failed", from_agent=from_agent, to_agent=to_agent, error=str(e))
            return False
    
    async def _get_status_channel(self) -> str:
        """Get the status notification channel."""
        # In production, this would be configured via environment variable
        return os.environ.get("SLACK_STATUS_CHANNEL", "#general")
    
    async def _handle_message(self, event) -> None:
        """Handle incoming Slack messages."""
        if "text" in event and "user" in event["user"]:
            _message = event["text"].strip()
            
            if message.startswith("!help"):
                await self._handle_help(event)
            elif message.startswith("!status"):
                await self._handle_status_request(event)
            elif message.startswith("!agents"):
                await self._handle_agents_list(event)
            elif message.startswith("!chat"):
                await self._handle_chat_command(event)
            else:
                # Log unhandled message
                logger.info(f"slack_message_received", user=event["user"], message=message)
    
    async def _handle_help(self, event) -> None:
        """Handle !help command."""
        _help_text = """
*Available Commands:*
• `!help` - Show this help
• `!status` - Check swarm status
• `!agents` - List available agents
• `!chat <agent> <message>` - Chat with specific agent
• `!handoff <from> <to> <reason>` - Trigger agent handoff
        """
        
        _blocks = [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "🤖 Heretek Swarm Commands"
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "Chat Commands"
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "Status Commands"
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrdwn",
                    "text": "Handoff Commands"
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "Example: `!chat steward Analyze this codebase`"
                }
            },
        ]
        
        await self._bot.chat_postMessage(
            _channel = event["channel"],
            _blocks = blocks
        )
    
    async def _handle_status_request(self, event) -> None:
        """Handle !status command."""
        try:
            # Get swarm status from agent runtime
            _status = await self.agent_runtime.get_swarm_status()
            
            _blocks = [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": "📊 Swarm Status"
                    }
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"Active Agents: {status.get('active_agents', 0)}"
                    }
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"Total Tasks: {status.get('total_tasks', 0)}"
                    }
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"Error Rate: {status.get('error_rate', '0/min')}"
                    }
                },
            ]
            
            _result = await self._bot.chat_postMessage(
                _channel = event["channel"],
                _blocks = blocks
            )
            
            return result["ok"]
        
        except Exception as e:
            logger.error("slack_status_failed", error=str(e))
            await self._bot.chat_postMessage(
                _channel = event["channel"],
                _text = f"Failed to get status: {str(e)}"
            )
    
    async def _handle_agents_list(self, event) -> None:
        """Handle !agents command."""
        try:
            # Get agents from runtime
            _agents = await self.agent_runtime.list_agents()
            
            if not agents:
                _blocks = [
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": "📋 No Active Agents"
                        }
                    }
                ]
                
                for agent in agents:
                    _status_emoji = "🟢" if agent.get("status") == "active" else "⚪"
                    
                    blocks.append({
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": f"{status_emoji} {agent.get('id', 'Unknown')}"
                        }
                    })
            
            await self._bot.chat_postMessage(
                _channel = event["channel"],
                _blocks = blocks
            )
        
        except Exception as e:
            logger.error("slack_agents_list_failed", error=str(e))
            await self._bot.chat_postMessage(
                _channel = event["channel"],
                _text = f"Failed to list agents: {str(e)}"
            )
    
    async def _handle_chat_command(self, event) -> None:
        """Handle !chat command."""
        # Parse command: !chat <agent> <message>
        _parts = event["text"].split(maxsplit=2)
        
        if len(parts) < 2:
            _blocks = [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": "❌ Invalid format. Use: `!chat <agent> <message>`"
                    }
                }
            ]
            await self._bot.chat_postMessage(
                _channel = event["channel"],
                _blocks = blocks
            )
            return
        
        _agent_id = parts[0].strip()
        _message = " ".join(parts[1:])
        
        try:
            # Send message to agent
            _response = await self.agent_runtime.send_message_to_agent(
                _agent_id = agent_id,
                _message = message
            )
            
            _blocks = [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": "💬 Message Sent"
                    }
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"To: {agent_id}"
                    }
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"Message: {message[:100]}..."
                    }
                }
            ]
            
            await self._bot.chat_postMessage(
                _channel = event["channel"],
                _blocks = blocks
            )
        
        except Exception as e:
            logger.error("slack_chat_failed", agent_id=agent_id, message=str(e))
            await self._bot.chat_postMessage(
                _channel = event["channel"],
                _text = f"Failed to send message: {str(e)}"
            )
    
    async def _handle_handoff_command(self, event) -> None:
        """Handle !handoff command."""
        # Parse: !handoff <from> <to> <reason>
        _parts = event["text"].split(maxsplit=4)
        
        if len(parts) < 3:
            _blocks = [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": "❌ Invalid format. Use: `!handoff <from> <to> <reason>`"
                    }
                }
            ]
            await self._bot.chat_postMessage(
                _channel = event["channel"],
                _blocks = blocks
            )
            return
        
        _from_agent = parts[1].strip()
        _to_agent = parts[2].strip()
        _reason = " ".join(parts[3:])
        
        try:
            # Trigger handoff through runtime
            _result = await self.agent_runtime.handoff(
                _from_agent = from_agent,
                _to_agent = to_agent,
                _reason = reason,
                _context = event
            )
            
            if result:
                _blocks = [
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": "🔄 Handoff Triggered"
                        }
                    },
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": f"From: {from_agent}"
                        }
                    },
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": f"To: {to_agent}"
                        }
                    },
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": f"Reason: {reason}"
                        }
                    },
                ]
            
            await self._bot.chat_postMessage(
                _channel = event["channel"],
                _blocks = blocks
            )
        
        except Exception as e:
            logger.error("slack_handoff_failed", from_agent=from_agent, to_agent=to_agent, error=str(e))
            await self._bot.chat_postMessage(
                _channel = event["channel"],
                _text = f"Failed to trigger handoff: {str(e)}"
            )
    
    async def _handle_message(self, event) -> None:
        """Handle incoming Slack messages."""
        if "text" in event and "user" in event["user"]:
            _message = event["text"].strip()
            
            if message.startswith("!help"):
                await self._handle_help(event)
            elif message.startswith("!status"):
                await self._handle_status_request(event)
            elif message.startswith("!agents"):
                await self._handle_agents_list(event)
            elif message.startswith("!chat"):
                await self._handle_chat_command(event)
            elif message.startswith("!handoff"):
                await self._handle_handoff_command(event)
            else:
                # Log unhandled message
                logger.info(f"slack_message_received", user=event["user"], message=message)
    
    async def start(self) -> None:
        """Start bot polling."""
        if not self._bot:
            logger.warning("slack_bot_not_initialized")
            return
        
        self._running = True
        await self._bot.start()
        logger.info("slack_bot_started")
    
    async def stop(self) -> None:
        """Stop bot."""
        if not self._bot:
            return
        
        self._running = False
        await self._bot.stop()
        logger.info("slack_bot_stopped")
