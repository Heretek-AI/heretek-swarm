"""
Comprehensive test suite for Platform Integrations

Tests for:
- Discord bot integration
- Telegram bot integration
- Slack bot integration
- Agent routing and handoffs
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch

try:
    from heretek_swarm.integrations.discord_bot import DiscordBot, DISCORD_AVAILABLE
except ImportError:
    DISCORD_AVAILABLE = False
    _DiscordBot = None

try:
    from heretek_swarm.integrations.telegram_bot import TelegramBot, TELEGRAM_AVAILABLE
except ImportError:
    TELEGRAM_AVAILABLE = False
    _TelegramBot = None

try:
    from heretek_swarm.integrations.slack_bot import SlackBot, SLACK_AVAILABLE
except ImportError:
    SLACK_AVAILABLE = False
    _SlackBot = None


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
        _supervisor = AsyncMock()
        supervisor.send_message.return_value = "Test response"
        return supervisor

    @pytest.fixture
    def discord_bot(self, _discord_config, _mock_supervisor):
        """Create Discord bot instance."""
        return DiscordBot(
            token=discord_config["token"],
            agent_runtime=discord_config["agent_runtime"],
            handoff_manager=discord_config["handoff_manager"],
        )

    def test_initialization(self, _discord_bot):
        """Test Discord bot initialization."""
        assert discord_bot.token == "test_token"
        assert discord_bot.agent_runtime is None
        assert discord_bot.handoff_manager is None

    def test_register_commands(self, _discord_bot):
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
    async def test_route_message_to_agent(self, _discord_bot):
        """Test routing message to agent."""
        _response = await discord_bot._route_message(
            "hello",
            "test_user"
        )

        assert response is not None
        assert isinstance(response, str)

    @pytest.mark.asyncio
    async def test_send_notification(self, _discord_bot):
        """Test sending notification."""
        _mock_channel = AsyncMock()
        mock_channel.send = AsyncMock()

        await discord_bot.send_notification(
            _channel = mock_channel,
            _message = "Test notification"
        )

        mock_channel.send.assert_called_once_with("Test notification")

    @pytest.mark.asyncio
    async def test_notify_handoff(self, _discord_bot):
        """Test handoff notification."""
        _mock_channel = AsyncMock()
        mock_channel.send = AsyncMock()

        await discord_bot.notify_handoff(
            _channel = mock_channel,
            _from_agent = "agent-1",
            _to_agent = "agent-2",
            _reason = "test reason"
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
        _supervisor = AsyncMock()
        supervisor.send_message.return_value = "Test response"
        return supervisor

    @pytest.fixture
    def telegram_bot(self, _telegram_config, _mock_supervisor):
        """Create Telegram bot instance."""
        return TelegramBot(
            _token = telegram_config["token"],
            _agent_id = telegram_config["agent_id"],
            _supervisor = mock_supervisor,
        )

    def test_initialization(self, _telegram_bot):
        """Test Telegram bot initialization."""
        assert telegram_bot._token == "test_token"
        assert telegram_bot._agent_id == "test-agent"

    @pytest.mark.asyncio
    async def test_initialize(self, _telegram_bot):
        """Test bot initialization."""
        with patch("telegram.ext.Application.builder") as mock_builder:
            _mock_app = AsyncMock()
            mock_builder.return_value.build.return_value = mock_app

            _result = await telegram_bot.initialize()

            assert result is True

    @pytest.mark.asyncio
    async def test_handle_start(self, _telegram_bot):
        """Test /start command handler."""
        _mock_update = Mock()
        mock_update.effective_chat.id = 12345
        mock_update.message.reply_text = AsyncMock()

        await telegram_bot._handle_start(mock_update, None)

        mock_update.message.reply_text.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_help(self, _telegram_bot):
        """Test /help command handler."""
        _mock_update = Mock()
        mock_update.message.reply_text = AsyncMock()

        await telegram_bot._handle_help(mock_update, None)

        mock_update.message.reply_text.assert_called_once()
        _call_args = mock_update.message.reply_text.call_args[0][0]
        assert "Available commands" in call_args

    @pytest.mark.asyncio
    async def test_route_message(self, _telegram_bot):
        """Test routing message to agent."""
        _response = await telegram_bot._route_message(
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
        _supervisor = AsyncMock()
        supervisor.send_message.return_value = "Test response"
        return supervisor

    @pytest.fixture
    def slack_bot(self, _slack_config, _mock_supervisor):
        """Create Slack bot instance."""
        return SlackBot(
            _token = slack_config["token"],
            _signing_secret = slack_config["signing_secret"],
            _agent_id = slack_config["agent_id"],
            _supervisor = mock_supervisor,
        )

    def test_initialization(self, _slack_bot):
        """Test Slack bot initialization."""
        assert slack_bot._token == "test_token"
        assert slack_bot._signing_secret == "test_secret"
        assert slack_bot._agent_id == "test-agent"

    @pytest.mark.asyncio
    async def test_route_message(self, _slack_bot):
        """Test routing message to agent."""
        _response = await slack_bot._route_message(
            "hello",
            "test_user"
        )

        assert response is not None
        assert isinstance(response, str)

    @pytest.mark.asyncio
    async def test_send_notification(self, _slack_bot):
        """Test sending notification."""
        _mock_client = AsyncMock()
        mock_client.chat_postMessage = AsyncMock()

        slack_bot._client = mock_client

        await slack_bot.send_notification(
            _channel = "C12345",
            _message = "Test notification"
        )

        mock_client.chat_postMessage.assert_called_once_with(
            _channel = "C12345",
            _text = "Test notification"
        )
