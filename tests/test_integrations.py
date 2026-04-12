"""
Comprehensive test suite for Platform Integrations

Tests for:
- Discord bot integration
- Telegram bot integration
- Slack bot integration
- Agent routing and handoffs
"""

from unittest.mock import AsyncMock, Mock, patch

import pytest

try:
    from heretek_swarm.integrations.discord_bot import DISCORD_AVAILABLE, DiscordBot
except ImportError:
    DISCORD_AVAILABLE = False
    DiscordBot = None

try:
    from heretek_swarm.integrations.telegram_bot import TELEGRAM_AVAILABLE, TelegramBot
except ImportError:
    TELEGRAM_AVAILABLE = False
    TelegramBot = None

try:
    from heretek_swarm.integrations.slack_bot import SLACK_AVAILABLE, SlackBot
except ImportError:
    SLACK_AVAILABLE = False
    SlackBot = None


# =============================================================================
# Discord Bot Tests
# =============================================================================

class TestDiscordBot:
    """Test suite for Discord bot integration."""

    @pytest.fixture(autouse=True)
    def check_discord_available(self):
        """Skip tests if discord.py is not available."""
        if not DISCORD_AVAILABLE:
            pytest.skip("discord.py not installed")

    @pytest.fixture
    def discord_config(self):
        """Create Discord bot configuration."""
        return {
            "token": "test_token",
            "agent_runtime": None,
            "handoff_manager": None,
        }

    @pytest.fixture
    def mock_supervisor(self):
        """Create mock supervisor."""
        supervisor = AsyncMock()
        supervisor.send_message.return_value = "Test response"
        return supervisor

    @pytest.fixture
    def discord_bot(self, discord_config, mock_supervisor):
        """Create Discord bot instance."""
        return DiscordBot(
            token=discord_config["token"],
            agent_runtime=discord_config["agent_runtime"],
            handoff_manager=discord_config["handoff_manager"],
        )

    def test_initialization(self, discord_bot):
        """Test Discord bot initialization."""
        assert discord_bot.token == "test_token"
        assert discord_bot.agent_runtime is None
        assert discord_bot.handoff_manager is None

    def test_register_commands(self, discord_bot):
        """Test command registration."""
        assert hasattr(discord_bot, '_bot')
        discord_bot._register_commands()

        # Check that commands are registered
        assert "start" in discord_bot._bot.all_commands
        assert "help" in discord_bot._bot.all_commands
        assert "status" in discord_bot._bot.all_commands
        assert "agents" in discord_bot._bot.all_commands
        assert "chat" in discord_bot._bot.all_commands

    @pytest.mark.asyncio
    async def test_route_message_to_agent(self, discord_bot):
        """Test routing message to agent."""
        response = await discord_bot._route_message(
            "hello",
            "test_user"
        )

        assert response is not None
        assert isinstance(response, str)

    @pytest.mark.asyncio
    async def test_send_notification(self, discord_bot):
        """Test sending notification."""
        mock_channel = AsyncMock()
        mock_channel.send = AsyncMock()

        await discord_bot.send_notification(
            channel=mock_channel,
            message="Test notification"
        )

        mock_channel.send.assert_called_once_with("Test notification")

    @pytest.mark.asyncio
    async def test_notify_handoff(self, discord_bot):
        """Test handoff notification."""
        mock_channel = AsyncMock()
        mock_channel.send = AsyncMock()

        await discord_bot.notify_handoff(
            channel=mock_channel,
            from_agent="agent-1",
            to_agent="agent-2",
            reason="test reason"
        )

        mock_channel.send.assert_called_once()
        call_args = mock_channel.send.call_args[0][0]
        assert "agent-1" in call_args
        assert "agent-2" in call_args


# =============================================================================
# Telegram Bot Tests
# =============================================================================

class TestTelegramBot:
    """Test suite for Telegram bot integration."""

    @pytest.fixture(autouse=True)
    def check_telegram_available(self):
        """Skip tests if python-telegram-bot is not available."""
        if not TELEGRAM_AVAILABLE:
            pytest.skip("python-telegram-bot not installed")

    @pytest.fixture
    def telegram_config(self):
        """Create Telegram bot configuration."""
        return {
            "token": "test_token",
            "agent_id": "test-agent",
        }

    @pytest.fixture
    def mock_supervisor(self):
        """Create mock supervisor."""
        supervisor = AsyncMock()
        supervisor.send_message.return_value = "Test response"
        return supervisor

    @pytest.fixture
    def telegram_bot(self, telegram_config, mock_supervisor):
        """Create Telegram bot instance."""
        return TelegramBot(
            token=telegram_config["token"],
            agent_id=telegram_config["agent_id"],
            supervisor=mock_supervisor,
        )

    def test_initialization(self, telegram_bot):
        """Test Telegram bot initialization."""
        assert telegram_bot._token == "test_token"
        assert telegram_bot._agent_id == "test-agent"

    @pytest.mark.asyncio
    async def test_initialize(self, telegram_bot):
        """Test bot initialization."""
        with patch("telegram.ext.Application.builder") as mock_builder:
            mock_app = AsyncMock()
            mock_builder.return_value.build.return_value = mock_app

            result = await telegram_bot.initialize()

            assert result is True

    @pytest.mark.asyncio
    async def test_handle_start(self, telegram_bot):
        """Test /start command handler."""
        mock_update = Mock()
        mock_update.effective_chat.id = 12345
        mock_update.message.reply_text = AsyncMock()

        await telegram_bot._handle_start(mock_update, None)

        mock_update.message.reply_text.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_help(self, telegram_bot):
        """Test /help command handler."""
        mock_update = Mock()
        mock_update.message.reply_text = AsyncMock()

        await telegram_bot._handle_help(mock_update, None)

        mock_update.message.reply_text.assert_called_once()
        call_args = mock_update.message.reply_text.call_args[0][0]
        assert "Available commands" in call_args

    @pytest.mark.asyncio
    async def test_route_message(self, telegram_bot):
        """Test routing message to agent."""
        response = await telegram_bot._route_message(
            "hello",
            "test_user"
        )

        assert response is not None
        assert isinstance(response, str)


# =============================================================================
# Slack Bot Tests
# =============================================================================

class TestSlackBot:
    """Test suite for Slack bot integration."""

    @pytest.fixture(autouse=True)
    def check_slack_available(self):
        """Skip tests if slack_sdk is not available."""
        if not SLACK_AVAILABLE:
            pytest.skip("slack_sdk not installed")

    @pytest.fixture
    def slack_config(self):
        """Create Slack bot configuration."""
        return {
            "token": "test_token",
            "signing_secret": "test_secret",
            "agent_id": "test-agent",
        }

    @pytest.fixture
    def mock_supervisor(self):
        """Create mock supervisor."""
        supervisor = AsyncMock()
        supervisor.send_message.return_value = "Test response"
        return supervisor

    @pytest.fixture
    def slack_bot(self, slack_config, mock_supervisor):
        """Create Slack bot instance."""
        return SlackBot(
            token=slack_config["token"],
            signing_secret=slack_config["signing_secret"],
            agent_id=slack_config["agent_id"],
            supervisor=mock_supervisor,
        )

    def test_initialization(self, slack_bot):
        """Test Slack bot initialization."""
        assert slack_bot._token == "test_token"
        assert slack_bot._signing_secret == "test_secret"
        assert slack_bot._agent_id == "test-agent"

    @pytest.mark.asyncio
    async def test_route_message(self, slack_bot):
        """Test routing message to agent."""
        response = await slack_bot._route_message(
            "hello",
            "test_user"
        )

        assert response is not None
        assert isinstance(response, str)

    @pytest.mark.asyncio
    async def test_send_notification(self, slack_bot):
        """Test sending notification."""
        mock_client = AsyncMock()
        mock_client.chat_postMessage = AsyncMock()

        slack_bot._client = mock_client

        await slack_bot.send_notification(
            channel="C12345",
            message="Test notification"
        )

        mock_client.chat_postMessage.assert_called_once_with(
            channel="C12345",
            text="Test notification"
        )
