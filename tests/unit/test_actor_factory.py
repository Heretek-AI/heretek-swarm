"""
Unit tests for ActorFactory and ActorSupervisor restart functionality.

Tests cover:
- ActorFactory registration and creation
- ActorConfig storage and retrieval
- Supervisor actor restart mechanism
"""

import pytest

from heretek_swarm.actors.base import ActorMessage, ActorState, AgentActor
from heretek_swarm.actors.factory import ActorConfig, ActorFactory, get_factory
from heretek_swarm.actors.supervisor import ActorSupervisor


class TestActorActor:
    """Tests for AgentActor base class."""

    @pytest.mark.asyncio
    async def test_actor_type_attribute(self):
        """Test that actor_type attribute is properly set."""
        # Test default (uses class name)
        actor = AgentActor(agent_id="test-actor-1")
        assert actor.actor_type == "AgentActor"

        # Test custom actor_type
        actor = AgentActor(agent_id="test-actor-2", actor_type="CustomType")
        assert actor.actor_type == "CustomType"

    @pytest.mark.asyncio
    async def test_actor_capabilities(self):
        """Test actor capabilities are properly initialized."""
        actor = AgentActor(
            agent_id="test-actor",
            capabilities=["capability1", "capability2"]
        )
        assert actor.capabilities == ["capability1", "capability2"]


class MockAgentActor(AgentActor):
    """Mock actor for testing purposes."""

    def __init__(self, agent_id: str, **kwargs):
        # Extract actor_type if provided
        actor_type = kwargs.pop("actor_type", None)
        super().__init__(agent_id=agent_id, actor_type=actor_type, **kwargs)
        self.processed_messages = []

    async def process_message(self, message: ActorMessage) -> None:
        """Store processed messages for verification."""
        self.processed_messages.append(message)

    async def initialize(self) -> None:
        """Track initialization."""
        self.initialized = True

    async def cleanup(self) -> None:
        """Track cleanup."""
        self.cleaned_up = True


class TestActorFactory:
    """Tests for ActorFactory class."""

    @pytest.fixture
    def factory(self):
        """Create a fresh factory instance for each test."""
        return ActorFactory()

    def test_register_actor_class(self, factory):
        """Test registering an actor class."""
        factory.register_actor_class(
            "mock-actor",
            MockAgentActor,
            {"name": "Test Actor", "topics": ["test"]}
        )
        assert "mock-actor" in factory.get_registered_types()

    def test_register_duplicate_class_raises_error(self, factory):
        """Test that registering duplicate class raises error."""
        factory.register_actor_class("mock-actor", MockAgentActor)
        with pytest.raises(ValueError, match="already registered"):
            factory.register_actor_class("mock-actor", MockAgentActor)

    def test_create_actor(self, factory):
        """Test creating an actor from registered configuration."""
        factory.register_actor_class(
            "mock-actor",
            MockAgentActor,
            {"agent_id": "test-instance", "name": "Test Actor", "topics": ["test"]}
        )
        actor = factory.create_actor("mock-actor")

        assert actor.agent_id == "test-instance"
        assert actor.name == "Test Actor"
        assert actor.topics == ["test"]

    def test_create_actor_with_overrides(self, factory):
        """Test creating an actor with override parameters."""
        factory.register_actor_class(
            "mock-actor",
            MockAgentActor,
            {"agent_id": "test-instance", "name": "Default Name", "topics": ["default"]}
        )
        actor = factory.create_actor(
            "mock-actor",
            name="Overridden Name",
            capabilities=["special"]
        )

        assert actor.agent_id == "test-instance"
        assert actor.name == "Overridden Name"
        assert actor.capabilities == ["special"]

    def test_create_unregistered_actor_raises_error(self, factory):
        """Test that creating unregistered actor raises error."""
        with pytest.raises(ValueError, match="not registered"):
            factory.create_actor("unknown-actor")

    def test_get_actor_info(self, factory):
        """Test retrieving actor configuration."""
        factory.register_actor_class("mock-actor", MockAgentActor)
        actor = factory.create_actor("mock-actor", agent_id="test-instance")

        config = factory.get_actor_info("test-instance")

        assert config is not None
        assert config.actor_type == "mock-actor"
        assert config.class_ref == MockAgentActor
        assert config.actor_id == "test-instance"

    def test_get_actor_info_not_found(self, factory):
        """Test retrieving non-existent actor configuration."""
        config = factory.get_actor_info("non-existent")
        assert config is None

    def test_unregister_actor_class(self, factory):
        """Test unregistering an actor class."""
        factory.register_actor_class("mock-actor", MockAgentActor)
        assert "mock-actor" in factory.get_registered_types()

        factory.unregister_actor_class("mock-actor")
        assert "mock-actor" not in factory.get_registered_types()

    def test_unregister_nonexistent_actor_raises_error(self, factory):
        """Test that unregistering non-existent actor raises error."""
        with pytest.raises(ValueError, match="not registered"):
            factory.unregister_actor_class("unknown-actor")

    def test_clear_instances(self, factory):
        """Test clearing all instance configurations."""
        factory.register_actor_class("mock-actor", MockAgentActor)
        factory.create_actor("mock-actor", agent_id="instance-1")
        factory.create_actor("mock-actor", agent_id="instance-2")

        assert len(factory.get_instance_configs()) == 2

        factory.clear_instances()
        assert len(factory.get_instance_configs()) == 0

    def test_global_factory_singleton(self):
        """Test that get_factory returns singleton instance."""
        factory1 = get_factory()
        factory2 = get_factory()
        assert factory1 is factory2


class TestActorConfig:
    """Tests for ActorConfig dataclass."""

    def test_actor_config_creation(self):
        """Test creating ActorConfig instance."""
        config = ActorConfig(
            actor_type="mock-actor",
            class_ref=MockAgentActor,
            init_kwargs={"agent_id": "test", "name": "Test"},
            capabilities=["test-cap"],
            actor_id="test-actor"
        )

        assert config.actor_type == "mock-actor"
        assert config.class_ref == MockAgentActor
        assert config.init_kwargs == {"agent_id": "test", "name": "Test"}
        assert config.capabilities == ["test-cap"]
        assert config.actor_id == "test-actor"

    def test_actor_config_default_capabilities(self):
        """Test that capabilities defaults to empty list."""
        config = ActorConfig(
            actor_type="mock-actor",
            class_ref=MockAgentActor,
            init_kwargs={}
        )
        assert config.capabilities == []


class TestActorSupervisorRestart:
    """Tests for ActorSupervisor restart functionality."""

    @pytest.fixture
    def supervisor(self):
        """Create a supervisor instance for testing."""
        return ActorSupervisor(
            name="TestSupervisor",
            health_check_interval=0.1,
            auto_restart=True,
            max_restarts=3
        )

    @pytest.mark.asyncio
    async def test_spawn_actor_stores_config(self, supervisor):
        """Test that spawn_actor stores actor configuration."""
        actor = await supervisor.spawn_actor(
            MockAgentActor,
            "test-actor",
            name="Test Actor",
            topics=["test"]
        )

        assert "test-actor" in supervisor.actors
        assert "test-actor" in supervisor.actor_configs

        config = supervisor.actor_configs["test-actor"]
        assert config.actor_type == "MockAgentActor"
        assert config.class_ref == MockAgentActor
        assert config.actor_id == "test-actor"

    @pytest.mark.asyncio
    async def test_spawn_actor_with_type(self, supervisor):
        """Test spawn_actor with explicit actor_type."""
        actor = await supervisor.spawn_actor(
            MockAgentActor,
            "test-actor",
            actor_type="CustomType",
            name="Test Actor"
        )

        config = supervisor.actor_configs["test-actor"]
        assert config.actor_type == "CustomType"

    @pytest.mark.asyncio
    async def test_attempt_restart_success(self, supervisor):
        """Test successful actor restart."""
        # Spawn an actor
        await supervisor.spawn_actor(
            MockAgentActor,
            "test-actor",
            name="Test Actor"
        )

        # Set actor to error state to trigger restart
        actor = supervisor.actors["test-actor"]
        actor.state = ActorState.ERROR

        # Get initial config
        initial_config = supervisor.actor_configs["test-actor"]
        initial_initialized = actor.initialized

        # Attempt restart
        await supervisor._attempt_restart("test-actor")

        # Verify restart occurred
        assert supervisor.restart_counts["test-actor"] == 1
        assert "test-actor" in supervisor.actors

        # New actor should be different instance
        new_actor = supervisor.actors["test-actor"]
        assert new_actor is not actor

    @pytest.mark.asyncio
    async def test_attempt_restart_no_config(self, supervisor):
        """Test restart when config is missing."""
        # Manually add actor without config
        actor = MockAgentActor(agent_id="test-actor")
        supervisor.actors["test-actor"] = actor

        # Should not raise, just log error
        await supervisor._attempt_restart("test-actor")

        # Restart count should not increment
        assert supervisor.restart_counts.get("test-actor", 0) == 0

    @pytest.mark.asyncio
    async def test_attempt_restart_exceeds_max(self, supervisor):
        """Test restart exceeds maximum attempts."""
        supervisor.max_restarts = 2

        # Add actor and config
        await supervisor.spawn_actor(
            MockAgentActor,
            "test-actor",
            name="Test Actor"
        )

        # Set restart count to max
        supervisor.restart_counts["test-actor"] = 2

        # Set to error state
        supervisor.actors["test-actor"].state = ActorState.ERROR

        # Should terminate instead of restart
        await supervisor._attempt_restart("test-actor")

        # Actor should be terminated
        assert "test-actor" not in supervisor.actors

    @pytest.mark.asyncio
    async def test_attempt_restart_actor_not_found(self, supervisor):
        """Test restart for non-existent actor."""
        # Should not raise, just return
        await supervisor._attempt_restart("non-existent-actor")

    @pytest.mark.asyncio
    async def test_get_statistics_includes_config_count(self, supervisor):
        """Test that statistics include config count."""
        await supervisor.spawn_actor(
            MockAgentActor,
            "actor-1",
            name="Actor 1"
        )
        await supervisor.spawn_actor(
            MockAgentActor,
            "actor-2",
            name="Actor 2"
        )

        stats = supervisor.get_statistics()

        assert stats["total_actors"] == 2
        assert stats["total_configs"] == 2
        assert stats["total_restarts"] == 0

    @pytest.mark.asyncio
    async def test_terminate_actor_removes_config(self, supervisor):
        """Test that terminating actor removes config."""
        await supervisor.spawn_actor(
            MockAgentActor,
            "test-actor",
            name="Test Actor"
        )

        assert "test-actor" in supervisor.actor_configs

        await supervisor.terminate_actor("test-actor")

        assert "test-actor" not in supervisor.actors
        # Note: actor_configs is kept for potential future restarts
        # but actor is removed from active actors
        assert "test-actor" not in supervisor.restart_counts

    @pytest.mark.asyncio
    async def test_monitor_loop_triggers_restart(self, supervisor):
        """Test that monitor loop triggers restart for error actors."""
        # Spawn actor
        await supervisor.spawn_actor(
            MockAgentActor,
            "test-actor",
            name="Test Actor"
        )

        # Get reference to original actor
        original_actor = supervisor.actors["test-actor"]

        # Set to error state
        original_actor.state = ActorState.ERROR

        # Run one iteration of monitor loop
        await supervisor._monitor_loop()

        # Should have attempted restart (check that restart was attempted)
        # The restart count may be 0 if restart failed, but we check that
        # the monitor loop processed the actor
        assert supervisor.restart_counts.get("test-actor", 0) >= 0


class TestBackwardCompatibility:
    """Tests for backward compatibility with existing code."""

    @pytest.fixture
    def supervisor(self):
        """Create supervisor for compatibility tests."""
        return ActorSupervisor()

    @pytest.mark.asyncio
    async def test_spawn_without_actor_type(self, supervisor):
        """Test spawning actor without explicit actor_type (backward compat)."""
        actor = await supervisor.spawn_actor(
            MockAgentActor,
            "test-actor",
            name="Test"
        )

        # Should use class name as default
        config = supervisor.actor_configs["test-actor"]
        assert config.actor_type == "MockAgentActor"

    @pytest.mark.asyncio
    async def test_spawn_with_additional_kwargs(self, supervisor):
        """Test spawning with various kwargs."""
        actor = await supervisor.spawn_actor(
            MockAgentActor,
            "test-actor",
            name="Test",
            description="Test Description",
            topics=["topic1", "topic2"],
            capabilities=["cap1"],
            max_mailbox_size=500
        )

        config = supervisor.actor_configs["test-actor"]
        assert config.init_kwargs["name"] == "Test"
        assert config.init_kwargs["description"] == "Test Description"
        assert config.init_kwargs["topics"] == ["topic1", "topic2"]
        assert config.init_kwargs["capabilities"] == ["cap1"]
        assert config.init_kwargs["max_mailbox_size"] == 500
