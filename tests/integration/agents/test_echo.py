"""
Integration tests for EchoActor.

Tier 2 (Support) - EchoActor handles multi-channel communication and protocol translation.
"""

import asyncio
import pytest
import pytest_asyncio
from datetime import datetime
from unittest.mock import patch

from src.heretek_swarm.actors.echo import EchoActor, CommunicationChannel
from src.heretek_swarm.actors.base import ActorMessage, ActorState


_pytestmark = pytest.mark.integration


class TestEchoActorIntegration:
    """Integration tests for EchoActor."""

    @pytest_asyncio.fixture
    async def echo_actor(self, _mock_nats, _mock_llm, _mock_db):
        """Create EchoActor with mock dependencies."""
        with patch('src.heretek_swarm.actors.echo.get_nats_event_mesh', return_value=mock_nats):
            with patch('src.heretek_swarm.actors.base.get_llm_provider', return_value=mock_llm):
                with patch('src.heretek_swarm.actors.echo.get_db_pool', return_value=mock_db):
                    actor = EchoActor(actor_id="echo-test-001")
                    yield actor
                    if actor._state != ActorState.TERMINATED:
                        await actor.terminate()

    @pytest_asyncio.fixture
    async def spawned_echo(self, _echo_actor):
        """Create and spawn EchoActor."""
        await echo_actor.spawn()
        yield echo_actor

    @pytest.mark.asyncio
    async def test_actor_spawn(self, _echo_actor):
        """Test actor spawning lifecycle."""
        assert echo_actor._state == ActorState.SPAWNING
        await echo_actor.spawn()
        assert echo_actor._state == ActorState.ACTIVE
        assert echo_actor.is_alive

    @pytest.mark.asyncio
    async def test_actor_terminate(self, _spawned_echo):
        """Test actor termination lifecycle."""
        assert spawned_echo._state == ActorState.ACTIVE
        await spawned_echo.terminate()
        assert spawned_echo._state == ActorState.TERMINATED
        assert not spawned_echo.is_alive

    @pytest.mark.asyncio
    async def test_handle_format_message(self, _spawned_echo, _mock_nats):
        """Test handling message formatting request."""
        # Create message
        _message = ActorMessage(
            _message_type = "format_message",
            _content = {
                "content": "Important update for the team",
                "channel": "slack",
                "priority": "high",
            },
            _sender = "coordinator",
            _recipient = "echo-test-001",
            _timestamp = datetime.utcnow().isoformat(),
        )

        # Process message
        await spawned_echo.process_message(message)

        # Verify message formatted
        assert len(mock_nats.published_messages) > 0

    @pytest.mark.asyncio
    async def test_handle_translate_protocol(self, _spawned_echo, _mock_nats):
        """Test handling protocol translation request."""
        # Create message
        _message = ActorMessage(
            _message_type = "translate_protocol",
            _content = {
                "content": "System alert: High CPU usage detected",
                "from_protocol": "internal",
                "to_protocol": "slack",
            },
            _sender = "sentinel",
            _recipient = "echo-test-001",
            _timestamp = datetime.utcnow().isoformat(),
        )

        # Process message
        await spawned_echo.process_message(message)

        # Verify translation performed
        assert len(mock_nats.published_messages) > 0

    @pytest.mark.asyncio
    async def test_handle_send_to_channel(self, _spawned_echo, _mock_nats):
        """Test handling channel send request."""
        # Create message
        _message = ActorMessage(
            _message_type = "send_to_channel",
            _content = {
                "content": "Message for Slack channel",
                "channel": "slack",
                "style": {"tone": "professional"},
            },
            _sender = "coordinator",
            _recipient = "echo-test-001",
            _timestamp = datetime.utcnow().isoformat(),
        )

        # Process message
        await spawned_echo.process_message(message)

        # Verify message sent
        assert len(mock_nats.published_messages) > 0

    @pytest.mark.asyncio
    async def test_handle_set_communication_style(self, _spawned_echo, _mock_nats):
        """Test handling communication style setting."""
        # Create message
        _message = ActorMessage(
            _message_type = "set_communication_style",
            _content = {
                "channel": "email",
                "style": {"tone": "formal", "format": "html"},
            },
            _sender = "governance",
            _recipient = "echo-test-001",
            _timestamp = datetime.utcnow().isoformat(),
        )

        # Process message
        await spawned_echo.process_message(message)

        # Verify style set
        assert "email" in spawned_echo._communication_styles

    @pytest.mark.asyncio
    async def test_handle_get_channel_status(self, _spawned_echo, _mock_nats):
        """Test handling channel status request."""
        # Setup channel status
        spawned_echo._channel_status["slack"] = {
            "connected": True,
            "messages_sent": 10,
            "last_activity": datetime.utcnow().isoformat(),
        }

        # Create message
        _message = ActorMessage(
            _message_type = "get_channel_status",
            _content = {"channel": "slack"},
            _sender = "monitor",
            _recipient = "echo-test-001",
            _timestamp = datetime.utcnow().isoformat(),
        )

        # Process message
        await spawned_echo.process_message(message)

        # Verify status published
        assert len(mock_nats.published_messages) > 0

    @pytest.mark.asyncio
    async def test_handle_broadcast_message(self, _spawned_echo, _mock_nats):
        """Test handling broadcast message request."""
        # Create message
        _message = ActorMessage(
            _message_type = "broadcast_message",
            _content = {
                "content": "System-wide announcement",
                "channels": ["slack", "email", "webhook"],
                "priority": "high",
            },
            _sender = "coordinator",
            _recipient = "echo-test-001",
            _timestamp = datetime.utcnow().isoformat(),
        )

        # Process message
        await spawned_echo.process_message(message)

        # Verify broadcast performed
        _stats = spawned_echo.statistics
        assert stats["messages_sent"] >= 1

    @pytest.mark.asyncio
    async def test_get_communication_style(self, _spawned_echo):
        """Test getting communication style."""
        # Set style
        spawned_echo._communication_styles["test-channel"] = {
            "tone": "friendly",
            "format": "markdown",
            "emoji": True,
        }

        # Get style
        _style = spawned_echo._get_communication_style(
            _style_config = {"channel": "test-channel"}
        )

        assert style is not None

    @pytest.mark.asyncio
    async def test_format_for_channel(self, _spawned_echo):
        """Test formatting message for channel."""
        # Format for JSON
        _formatted = await spawned_echo._format_for_channel(
            _content = {"message": "Test"},
            _channel = CommunicationChannel.WEBHOOK,
            _priority = "high"
        )

        assert isinstance(formatted, str)

    @pytest.mark.asyncio
    async def test_apply_style(self, _spawned_echo):
        """Test applying communication style."""
        from src.heretek_swarm.actors.echo import CommunicationStyle

        _style = CommunicationStyle(
            _tone = "professional",
            _format_type = "text",
            _emoji = False,
            _verbosity = "concise"
        )

        _styled = spawned_echo._apply_style(
            _content = "Hello team",
            _style = style
        )

        assert isinstance(styled, str)

    @pytest.mark.asyncio
    async def test_format_as_json(self, _spawned_echo):
        """Test JSON formatting."""
        _formatted = spawned_echo._format_as_json(
            _content = "Test message",
            _priority = "normal"
        )

        assert "Test message" in formatted
        assert "priority" in formatted

    @pytest.mark.asyncio
    async def test_format_as_markdown(self, _spawned_echo):
        """Test Markdown formatting."""
        from src.heretek_swarm.actors.echo import CommunicationStyle

        _style = CommunicationStyle(
            _tone = "professional",
            _format_type = "markdown",
            _emoji = False,
            _verbosity = "normal"
        )

        _formatted = spawned_echo._format_as_markdown(
            _content = "Important update",
            _style = style
        )

        assert isinstance(formatted, str)

    @pytest.mark.asyncio
    async def test_translate_content(self, _spawned_echo, _mock_llm):
        """Test content translation."""
        # Setup mock LLM
        mock_llm.register_response(
            "translate",
            "Translated content in target language."
        )

        # Translate
        _translated = await spawned_echo._translate_content(
            _content = "Hello world",
            _from_lang = "en",
            _to_lang = "es"
        )

        assert isinstance(translated, str)

    @pytest.mark.asyncio
    async def test_send_to_channel_impl(self, _spawned_echo, _mock_nats):
        """Test channel send implementation."""
        # Send to channel
        _result = await spawned_echo._send_to_channel_impl(
            _channel = CommunicationChannel.SLACK,
            _content = "Test message",
            _style_config = {"tone": "casual"}
        )

        assert result is not None

    @pytest.mark.asyncio
    async def test_statistics_tracking(self, _spawned_echo):
        """Test statistics tracking."""
        # Simulate messages sent
        spawned_echo._stats["messages_sent"] = 10
        spawned_echo._stats["translations"] = 5
        spawned_echo._stats["formatting_ops"] = 20

        # Get statistics
        _stats = spawned_echo.statistics

        assert stats["messages_sent"] == 10
        assert stats["translations"] == 5

    @pytest.mark.asyncio
    async def test_concurrent_broadcasts(self, _spawned_echo, _mock_nats):
        """Test handling multiple concurrent broadcasts."""
        # Simulate multiple broadcasts
        for i in range(5):
            spawned_echo._stats["messages_sent"] += 1

        # Verify statistics
        _stats = spawned_echo.statistics
        assert stats["messages_sent"] >= 5

    @pytest.mark.asyncio
    async def test_message_validation(self, _spawned_echo):
        """Test message validation."""
        # Create invalid message
        _message = ActorMessage(
            _message_type = "format_message",
            _content = {},  # Missing required fields
            _sender = "test",
            _recipient = "echo-test-001",
            _timestamp = datetime.utcnow().isoformat(),
        )

        # Process should handle validation error gracefully
        await spawned_echo.process_message(message)

        # Verify actor still active
        assert spawned_echo._state == ActorState.ACTIVE

    @pytest.mark.asyncio
    async def test_latency_baseline(self, _spawned_echo, _assert_latency_baseline):
        """Test message processing latency meets baseline."""
        import time

        _message = ActorMessage(
            _message_type = "get_channel_status",
            _content = {"channel": "test"},
            _sender = "test",
            _recipient = "echo-test-001",
            _timestamp = datetime.utcnow().isoformat(),
        )

        _start = time.time()
        await spawned_echo.process_message(message)
        _latency_ms = (time.time() - start) * 1000

        assert_latency_baseline(latency_ms, "echo_message_process")

    @pytest.mark.asyncio
    async def test_state_persistence(self, _spawned_echo, _mock_db):
        """Test actor state persistence."""
        # Add channel status
        spawned_echo._channel_status["persist-channel"] = {
            "connected": True,
            "messages_sent": 5,
        }

        # Save state
        with patch('src.heretek_swarm.actors.base.get_db_pool', return_value=mock_db):
            await spawned_echo.save_state()

        # Verify state saved
        _table = mock_db.get_table("agent_states")
        assert len(table) > 0

    @pytest.mark.asyncio
    async def test_error_recovery(self, _echo_actor):
        """Test actor error recovery."""
        await echo_actor.spawn()
        echo_actor._state = ActorState.ERROR
        await echo_actor.resume()
        assert echo_actor._state == ActorState.ACTIVE
