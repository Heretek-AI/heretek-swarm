"""
Discord Bot Integration - PraisonAI Pattern

Discord bot for agent interaction and notifications.
Reference: PraisonAI Discord integration
"""

import os
from typing import Optional, Dict, TYPE_CHECKING
import structlog

try:
    import discord
    from discord.ext import commands
    DISCORD_AVAILABLE = True
except ImportError:
    DISCORD_AVAILABLE = False
    _discord = None
    _commands = None

# TYPE_CHECKING ensures type hints are not evaluated at runtime when discord is None
if TYPE_CHECKING:
    from discord import Intents, Message, Embed

_logger = structlog.get_logger(__name__)


class DiscordBot:
    """
    Discord bot for Heretek Swarm interaction.
    
    Features:
    - Chat with agents via DM or channels
    - Task submission commands
    - Status notifications
    - Handoff updates
    - Embed-based rich responses
    """
    
    def __init__(self, _token: Optional[str], _agent_runtime = None, _handoff_manager = None, _intents: "Optional[Intents]"):
        self.token = token or os.getenv("DISCORD_BOT_TOKEN")
        self.agent_runtime = agent_runtime
        self.handoff_manager = handoff_manager
        self._bot = None
        self._running = False
        
        if not DISCORD_AVAILABLE:
            logger.warning("discord_bot_unavailable", message="discord.py not installed")
            return
        
        # Set up intents - lazy import to avoid AttributeError at class definition
        if intents is None:
            _intents = discord.Intents.default()
            intents.message_content = True
            intents.members = True
        
        # Initialize bot
        self._bot = commands.Bot(
            _command_prefix = "!",
            _intents = intents,
            _help_command = None,  # Custom help
        )
        
        # Register events
        self._bot.event(self.on_ready)
        self._bot.event(self.on_message)
        
        # Register commands
        self._register_commands()
    
    def _register_commands(self) -> None:
        """Register Discord commands."""
        
        @self._bot.command(name="start")
        async def start(_ctx):
            """Welcome message."""
            _embed = discord.Embed(
                title="🤖 Welcome to Heretek Swarm!",
                _description = "I'm your Discord assistant for interacting with the AI agent collective.",
                _color = discord.Color.blue(),
            )
            embed.add_field(
                name="Commands",
                _value = (
                    "`!help` - Show this help\n"
                    "`!status` - Check swarm status\n"
                    "`!agents` - List available agents\n"
                    "`!chat <agent> <message>` - Chat with specific agent"
                ),
                _inline = False,
            )
            embed.add_field(
                name="Example",
                _value = "`!chat steward Analyze this codebase`",
                _inline = False,
            )
            await ctx.send(embed=embed)
        
        @self._bot.command(name="help")
        async def help_cmd(_ctx):
            """Show help."""
            _embed = discord.Embed(
                title="📖 Heretek Swarm Help",
                _color = discord.Color.green(),
            )
            embed.add_field(
                name="Chat with Agents",
                value="Just type your message in #agent-chat or DM me, and I'll route it to the appropriate agent.",
                _inline = False,
            )
            embed.add_field(
                name="Available Agents",
                _value = (
                    "🎯 Steward (Orchestrator)\n"
                    "🔬 Alpha (Analysis)\n"
                    "✅ Beta (Validation)\n"
                    "💻 Coder (Development)\n"
                    "🛡️ Sentinel (Safety)\n"
                    "📚 Historian (Memory)"
                ),
                _inline = False,
            )
            await ctx.send(embed=embed)
        
        @self._bot.command(name="status")
        async def status(_ctx):
            """Show swarm status."""
            _embed = discord.Embed(
                title="📊 Swarm Status",
                _color = discord.Color.purple(),
            )
            
            if self.agent_runtime:
                _status_text = ""
                for agent_id, runtime in self.agent_runtime.items():
                    _status = runtime.get_status()
                    _emoji = "🟢" if status.get("state") == "idle" else "🟡"
                    status_text += f"{emoji} **{agent_id}**: {status.get('state')}\n"
                embed.add_field(name="Active Agents", value=status_text, inline=False)
            else:
                embed.add_field(name="Status", value="Swarm status unavailable", inline=False)
            
            await ctx.send(embed=embed)
        
        @self._bot.command(name="agents")
        async def agents(_ctx):
            """List available agents."""
            _embed = discord.Embed(
                title="🤖 Available Agents",
                _color = discord.Color.gold(),
            )
            embed.add_field(
                name="🎯 Steward",
                _value = "Orchestrator - Routes tasks and manages consensus",
                _inline = False,
            )
            embed.add_field(
                name="🔬 Alpha",
                _value = "Analyst - Deep analysis and research",
                _inline = False,
            )
            embed.add_field(
                name="✅ Beta",
                _value = "Validator - Quality assurance and testing",
                _inline = False,
            )
            embed.add_field(
                name="💻 Coder",
                _value = "Developer - Code generation and refactoring",
                _inline = False,
            )
            embed.add_field(
                name="🛡️ Sentinel",
                _value = "Safety - Ethics and constraint enforcement",
                _inline = False,
            )
            embed.add_field(
                name="📚 Historian",
                _value = "Memory - RAG and context management",
                _inline = False,
            )
            await ctx.send(embed=embed)
        
        @self._bot.command(name="chat")
        async def chat(_ctx, _agent: str, _*, _message: str):
            """Chat with specific agent."""
            await ctx.typing()
            
            _response = await self._route_message(f"{agent}: {message}", str(ctx.author.id))
            
            _embed = discord.Embed(
                title=f"🤖 {agent.title()}'s Response",
                _description = response,
                _color = discord.Color.blue(),
            )
            embed.set_footer(text=f"Requested by {ctx.author.name}")
            await ctx.send(embed=embed)
    
    async def on_ready(self) -> None:
        """Bot ready event."""
        logger.info(
            "discord_bot_ready",
            user=self._bot.user.name,
            id=self._bot.user.id,
            _guilds = len(self._bot.guilds),
        )
        self._running = True
    
    async def on_message(self, _message: "Message") -> None:
        """Message received event."""
        # Ignore bot messages
        if message.author.bot:
            return
        
        # Ignore commands (handled separately)
        if message.content.startswith("!"):
            await self._bot.process_commands(message)
            return
        
        # Route message in DMs or agent-chat channel
        if isinstance(message.channel, discord.DMChannel) or \
           (hasattr(message.channel, 'name') and message.channel.name == "agent-chat"):
            
            await message.channel.typing()
            
            _user_id = str(message.author.id)
            _response = await self._route_message(message.content, user_id)
            
            _embed = discord.Embed(
                _description = response,
                _color = discord.Color.blue(),
            )
            await message.channel.send(embed=embed)
    
    async def initialize(self) -> bool:
        """Initialize bot."""
        if not DISCORD_AVAILABLE:
            return False
        
        if not self.token:
            logger.warning("discord_token_missing")
            return False
        
        logger.info("discord_bot_initialized")
        return True
    
    async def start(self) -> None:
        """Start bot."""
        if not self._bot:
            await self.initialize()
        
        await self._bot.start(self.token)
    
    async def stop(self) -> None:
        """Stop bot."""
        self._running = False
        
        if self._bot:
            await self._bot.close()
        
        logger.info("discord_bot_stopped")
    
    async def _route_message(self, _message: str, _user_id: str) -> str:
        """
        Route message to appropriate agent.
        
        Args:
            message: User message
            user_id: Discord user ID
            
        Returns:
            Agent response
        """
        _message_lower = message.lower()
        
        # Determine agent from message
        if any(word in message_lower for word in ["code", "program", "script", "debug"]):
            _agent_id = "coder"
        elif any(word in message_lower for word in ["analyze", "research", "investigate"]):
            _agent_id = "alpha"
        elif any(word in message_lower for word in ["validate", "test", "check", "verify"]):
            _agent_id = "beta"
        elif any(word in message_lower for word in ["memory", "remember", "history", "context"]):
            _agent_id = "historian"
        elif any(word in message_lower for word in ["safe", "ethic", "constraint"]):
            _agent_id = "sentinel"
        else:
            _agent_id = "steward"
        
        logger.info(
            "discord_message_routed",
            agent=agent_id,
            _user = user_id,
        )
        
        # Get agent response
        if self.agent_runtime and agent_id in self.agent_runtime:
            try:
                _runtime = self.agent_runtime[agent_id]
                _response = await runtime.think(message)
                return f"**{agent_id.title()}**: {response}"
            except Exception as e:
                logger.error("agent_response_error", error=str(e))
                return f"⚠️ Error: {str(e)}"
        
        return f"🤖 Agent {agent_id} is unavailable."
    
    async def send_notification(self, _channel_id: int, _message: str, _embed: "Optional[Embed]") -> bool:
        """
        Send notification to channel.
        
        Args:
            channel_id: Discord channel ID
            message: Message text
            embed: Optional embed
            
        Returns:
            True if sent
        """
        if not self._bot:
            return False
        
        try:
            _channel = self._bot.get_channel(channel_id)
            if channel:
                if embed:
                    await channel.send(content=message, embed=embed)
                else:
                    await channel.send(message)
                return True
        except Exception as e:
            logger.error(
                "discord_notification_failed",
                _channel_id = channel_id,
                _error = str(e),
            )
        return False
    
    async def notify_handoff(self, _channel_id: int, _handoff_context: Dict) -> None:
        """
        Send handoff notification.
        
        Args:
            channel_id: Channel to notify
            handoff_context: Handoff details
        """
        _embed = discord.Embed(
            _title = "🔄 Task Handoff",
            _color = discord.Color.orange(),
        )
        embed.add_field(name="From", value=handoff_context.get("source_agent"), inline=True)
        embed.add_field(name="To", value=handoff_context.get("target_agent"), inline=True)
        embed.add_field(
            _name = "Priority",
            _value = handoff_context.get("priority", "normal"),
            _inline = True,
        )
        embed.add_field(
            _name = "Task",
            _value = handoff_context.get("task_description"),
            _inline = False,
        )
        
        await self.send_notification(channel_id, "", embed=embed)


# Global bot instance
discord_bot: Optional["DiscordBot"] = None


def get_discord_bot() -> Optional["DiscordBot"]:
    """Get global bot instance."""
    return discord_bot


async def start_discord_bot(_agent_runtime = None, _handoff_manager = None) -> None:
    """Start Discord bot."""
    global discord_bot
    
    if not DISCORD_AVAILABLE:
        logger.warning("discord_not_available")
        return
    
    _discord_bot = DiscordBot(
        _agent_runtime = agent_runtime,
        _handoff_manager = handoff_manager,
    )
    
    await discord_bot.initialize()
    await discord_bot.start()


async def stop_discord_bot() -> None:
    """Stop Discord bot."""
    global discord_bot
    
    if discord_bot:
        await discord_bot.stop()
        _discord_bot = None