"""
Tests for Runtime Startup Manager.

Verifies that the startup manager correctly subscribes to wizard.completed
events and starts the autonomous runtime with tier-specific configuration.
"""

import json
from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch, PropertyMock

import pytest

from heretek_swarm.infrastructure.nats.publisher import (
    EventPriority,
    SwarmEvent,
)
from heretek_swarm.runtime.startup_manager import (
    StartupManager,
    get_startup_manager,
)


@pytest.fixture
def manager():
    """Create a fresh startup manager instance."""
    return StartupManager()


@pytest.fixture
def mock_subscriber():
    """Create a mock NATS subscriber."""
    subscriber = AsyncMock()
    subscriber.initialize = AsyncMock()
    subscriber.subscribe = AsyncMock(return_value="sub_test_123")
    subscriber.unsubscribe = AsyncMock()
    subscriber.close = AsyncMock()
    return subscriber


@pytest.fixture
def mock_autonomous_runtime():
    """Create a mock autonomous runtime."""
    runtime = MagicMock()
    runtime.initialize = AsyncMock()
    runtime.start = AsyncMock()
    runtime.stop = AsyncMock()
    runtime.get_status = MagicMock(return_value={"running": True})
    runtime.config = None
    return runtime


@pytest.fixture
def sample_wizard_event():
    """Create a sample wizard.completed event."""
    return SwarmEvent(
        event_type="wizard.completed",
        source_agent="wizard",
        payload={
            "tier_id": "development",
            "agent_count": 4,
            "agents": ["coordinator", "alpha", "beta"],
            "memory_enabled": True,
            "consciousness_enabled": True,
        },
        priority=EventPriority.HIGH,
        correlation_id="test-corr-123",
        timestamp=datetime.now(UTC).isoformat(),
    )


class TestStartupManager:
    """Tests for StartupManager class."""

    @pytest.mark.asyncio
    async def test_initialize_creates_subscriber(self, manager, mock_subscriber):
        """Test that initialize creates and initializes the subscriber."""
        with patch(
            "heretek_swarm.runtime.startup_manager.get_subscriber",
            return_value=mock_subscriber,
        ):
            await manager.initialize()

            assert manager._subscriber is not None
            mock_subscriber.initialize.assert_called_once()

    @pytest.mark.asyncio
    async def test_start_creates_subscription(self, manager, mock_subscriber):
        """Test that start creates a NATS subscription."""
        manager._subscriber = mock_subscriber

        await manager.start()

        mock_subscriber.subscribe.assert_called_once()
        call_args = mock_subscriber.subscribe.call_args
        assert call_args.kwargs["subject"] == "swarm.wizard.completed"
        assert call_args.kwargs["queue"] == "startup_manager"

    @pytest.mark.asyncio
    async def test_start_is_idempotent(self, manager, mock_subscriber):
        """Test that calling start multiple times doesn't create duplicate subscriptions."""
        manager._subscriber = mock_subscriber
        manager._running = True

        await manager.start()

        # Should not have subscribed again
        mock_subscriber.subscribe.assert_not_called()

    @pytest.mark.asyncio
    async def test_stop_closes_subscription(self, manager, mock_subscriber):
        """Test that stop unsubscribes and closes the subscriber."""
        manager._subscriber = mock_subscriber
        manager._subscription_id = "sub_test_123"
        manager._running = True

        await manager.stop()

        mock_subscriber.unsubscribe.assert_called_once_with("sub_test_123")
        mock_subscriber.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_stop_stops_runtime(self, manager, mock_subscriber, mock_autonomous_runtime):
        """Test that stop also stops the runtime if it's running."""
        manager._subscriber = mock_subscriber
        manager._runtime = mock_autonomous_runtime
        manager._running = True

        await manager.stop()

        mock_autonomous_runtime.stop.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_status_returns_manager_state(self, manager, mock_subscriber, mock_autonomous_runtime):
        """Test that get_status returns correct manager state."""
        manager._subscriber = mock_subscriber
        manager._running = True
        manager._subscription_id = "sub_test_123"
        manager._runtime = mock_autonomous_runtime

        status = manager.get_status()

        assert status["running"] is True
        assert status["subscription_id"] == "sub_test_123"
        assert status["runtime_active"] is True
        assert "runtime_status" in status

    @pytest.mark.asyncio
    async def test_get_status_no_runtime(self, manager, mock_subscriber):
        """Test that get_status handles no runtime gracefully."""
        manager._subscriber = mock_subscriber
        manager._running = True
        manager._subscription_id = "sub_test_123"
        manager._runtime = None

        status = manager.get_status()

        assert status["running"] is True
        assert status["runtime_active"] is False
        assert status["runtime_status"] is None


class TestWizardCompletedHandling:
    """Tests for wizard.completed event handling."""

    @pytest.mark.asyncio
    async def test_handle_wizard_completed_creates_runtime(
        self, manager, mock_subscriber, sample_wizard_event, mock_autonomous_runtime
    ):
        """Test that handling wizard.completed creates an autonomous runtime."""
        manager._subscriber = mock_subscriber

        with patch(
            "heretek_swarm.runtime.startup_manager.AutonomousRuntime",
            return_value=mock_autonomous_runtime,
        ):
            await manager._handle_wizard_completed(sample_wizard_event)

        # Verify runtime was created and initialized
        assert manager._runtime is mock_autonomous_runtime
        mock_autonomous_runtime.initialize.assert_called_once()
        mock_autonomous_runtime.start.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_wizard_completed_error_handling(
        self, manager, mock_subscriber, sample_wizard_event
    ):
        """Test that errors during handling don't crash the manager."""
        manager._subscriber = mock_subscriber
        manager._running = False  # Not running yet

        with patch(
            "heretek_swarm.runtime.startup_manager.AutonomousRuntime",
            side_effect=Exception("Runtime initialization failed"),
        ):
            # Should not raise - errors are caught and logged
            await manager._handle_wizard_completed(sample_wizard_event)

        # Manager should still be functional (no runtime was set)
        assert manager._runtime is None

    @pytest.mark.asyncio
    async def test_handle_wizard_completed_extracts_tier_config(
        self, manager, mock_subscriber, sample_wizard_event
    ):
        """Test that tier configuration is extracted from the event payload."""
        manager._subscriber = mock_subscriber

        captured_config = {}

        class MockRuntime:
            def __init__(self, config):
                captured_config["config"] = config
                self.config = config
                self._status = {"running": True}

            async def initialize(self):
                pass

            async def start(self):
                pass

            def get_status(self):
                return self._status

        with patch(
            "heretek_swarm.runtime.startup_manager.AutonomousRuntime",
            side_effect=lambda config: MockRuntime(config),
        ):
            await manager._handle_wizard_completed(sample_wizard_event)

            # Verify config was created with correct tier settings
            config = captured_config.get("config")
            assert config is not None
            assert config.consciousness_plugin_enabled is True
            assert config.rag_enabled is True


class TestBuildAgentConfigs:
    """Tests for agent config building."""

    def test_build_agent_configs_returns_dict(self, manager):
        """Test that build_agent_configs returns a dictionary."""
        with patch.object(Path, "__truediv__", lambda self, x: Path(f"/fake/{x}")):
            configs = manager._build_agent_configs(
                agents=["coordinator"],
                tier_id="test",
            )

            assert isinstance(configs, dict)
            assert "coordinator" in configs

    def test_build_agent_configs_empty_list_uses_coordinator(self, manager):
        """Test that empty agent list falls back to coordinator."""
        with patch.object(Path, "__truediv__", lambda self, x: Path(f"/fake/{x}")):
            configs = manager._build_agent_configs(agents=[], tier_id="test")

            assert "coordinator" in configs


class TestGetStartupManager:
    """Tests for the get_startup_manager factory function."""

    def test_get_startup_manager_returns_singleton(self):
        """Test that get_startup_manager returns the same instance."""
        # Reset global
        import heretek_swarm.runtime.startup_manager as sm
        sm._manager = None

        manager1 = get_startup_manager()
        manager2 = get_startup_manager()

        assert manager1 is manager2

    def test_get_startup_manager_new_instance_after_reset(self):
        """Test that resetting allows creating new instance."""
        import heretek_swarm.runtime.startup_manager as sm
        sm._manager = None

        manager1 = get_startup_manager()
        sm._manager = None
        manager2 = get_startup_manager()

        assert manager1 is not manager2
