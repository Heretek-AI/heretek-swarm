"""
Integration tests for ActorBase with StateRepository.

Tests state persistence and recovery for actors:
- Actor spawn with state loading
- State checkpointing during operation
- State recovery after simulated restart
- Checkpoint-based rollback
"""

import asyncio
from datetime import datetime, timezone

import pytest

from heretek_swarm.actors.base import ActorMessage, ActorState, AgentActor
from heretek_swarm.state.repository import StateRepository

# Test Actor Implementation

class TestActor(AgentActor):
    """Test actor for integration testing."""

    actor_type = "TestActor"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.processed_messages = []

    async def process_message(self, message: ActorMessage) -> None:
        """Process incoming messages."""
        self.processed_messages.append(message)
        # Update state on message processing
        self.update_state("last_message", message.content)
        self.update_state("message_count", len(self.processed_messages))

        # Save state periodically
        if len(self.processed_messages) % 5 == 0:
            await self.save_checkpoint(metadata={
                "reason": "periodic_checkpoint",
                "message_count": len(self.processed_messages),
            })

    async def initialize(self) -> None:
        """Initialize actor with custom state."""
        self.update_state("initialized_at", datetime.now(timezone.utc).isoformat())
        self.update_state("custom_data", {"counter": 0})

    async def cleanup(self) -> None:
        """Cleanup before termination."""
        await self.save_checkpoint(metadata={"reason": "termination"})


# Fixtures

@pytest.fixture
async def state_repository():
    """Create state repository for tests."""
    repo = StateRepository(db_pool=None)  # In-memory for tests
    await repo.initialize()
    yield repo


@pytest.fixture
async def test_actor(state_repository):
    """Create test actor with state repository."""
    actor = TestActor(
        agent_id="test-actor-1",
        name="Test Actor",
        state_repository=state_repository,
        load_state_on_init=True,
    )
    yield actor


# Test Cases

class TestActorStatePersistence:
    """Test actor state persistence."""

    @pytest.mark.asyncio
    async def test_actor_spawn_with_repository(self, test_actor):
        """Test actor spawns correctly with state repository."""
        await test_actor.spawn()

        assert test_actor.state == ActorState.ACTIVE
        assert test_actor._state_repository is not None
        assert test_actor._running is True

        await test_actor.terminate()

    @pytest.mark.asyncio
    async def test_actor_state_save(self, test_actor, state_repository):
        """Test actor saves state to repository."""
        await test_actor.spawn()

        # Update some state
        test_actor.update_state("test_key", "test_value")
        test_actor.update_state("counter", 42)

        # Save state
        await test_actor.save_state()

        # Verify state was saved
        record = await state_repository.load_state(test_actor.agent_id)
        assert record is not None
        # State is stored with internal_state nested structure
        assert record.state.get("internal_state", {}).get("test_key") == "test_value"
        assert record.state.get("internal_state", {}).get("counter") == 42

        await test_actor.terminate()

    @pytest.mark.asyncio
    async def test_actor_state_load_on_spawn(self, state_repository):
        """Test actor loads state on spawn."""
        # First, save state directly
        initial_state = {
            "internal_state": {"persistent_key": "persistent_value"},
            "message_count": 100,
            "error_count": 5,
            "state": "active",
        }
        await state_repository.save_state(
            agent_id="test-actor-2",
            state=initial_state,
            agent_type="TestActor",
        )

        # Create new actor with same ID
        actor = TestActor(
            agent_id="test-actor-2",
            name="Test Actor 2",
            state_repository=state_repository,
            load_state_on_init=True,
        )

        # Spawn should load state
        await actor.spawn()

        # Verify state was loaded
        assert actor.get_state("persistent_key") == "persistent_value"
        assert actor.message_count == 100
        assert actor.error_count == 5

        await actor.terminate()

    @pytest.mark.asyncio
    async def test_actor_checkpoint_save(self, test_actor):
        """Test actor can save checkpoints."""
        await test_actor.spawn()

        # Update state
        test_actor.update_state("checkpoint_data", "important_value")

        # Save checkpoint
        checkpoint = await test_actor.save_checkpoint(metadata={
            "reason": "test_checkpoint",
        })

        assert checkpoint is not None
        assert checkpoint.metadata["reason"] == "test_checkpoint"

        await test_actor.terminate()

    @pytest.mark.asyncio
    async def test_actor_checkpoint_restore(self, test_actor, state_repository):
        """Test actor can restore from checkpoint."""
        await test_actor.spawn()

        # Set initial state and checkpoint
        test_actor.update_state("original_value", "original")
        await test_actor.save_checkpoint(metadata={"reason": "before_change"})

        # Change state
        test_actor.update_state("original_value", "modified")
        test_actor.update_state("new_value", "new")
        await test_actor.save_state()

        # Get checkpoint
        checkpoints = await test_actor.get_checkpoints(limit=1)
        assert len(checkpoints) >= 1

        # Restore from checkpoint
        checkpoint = checkpoints[0]
        restored = await test_actor.restore_from_checkpoint(checkpoint.checkpoint_id)

        assert restored is True

        await test_actor.terminate()


class TestSimulatedRestart:
    """Test state recovery after simulated restart."""

    @pytest.mark.asyncio
    async def test_restart_recovery(self, state_repository):
        """Test actor recovers state after restart."""
        # Phase 1: Create and run actor
        actor1 = TestActor(
            agent_id="restart-test-actor",
            name="Restart Test Actor",
            state_repository=state_repository,
            load_state_on_init=True,
        )

        await actor1.spawn()

        # Do some work
        actor1.update_state("work_done", True)
        actor1.update_state("counter", 10)
        await actor1.save_checkpoint(metadata={"phase": 1})
        await actor1.save_state()

        # Simulate termination (crash)
        await actor1.terminate()

        # Phase 2: Create new actor with same ID (simulates restart)
        actor2 = TestActor(
            agent_id="restart-test-actor",
            name="Restart Test Actor",
            state_repository=state_repository,
            load_state_on_init=True,
        )

        await actor2.spawn()

        # Verify state was recovered
        assert actor2.get_state("work_done") is True
        assert actor2.get_state("counter") == 10

        # Verify checkpoints are available
        checkpoints = await actor2.get_checkpoints()
        assert len(checkpoints) >= 1

        await actor2.terminate()

    @pytest.mark.asyncio
    async def test_rollback_after_error(self, state_repository):
        """Test actor can rollback to checkpoint after error."""
        # Create actor
        actor = TestActor(
            agent_id="rollback-test",
            name="Rollback Test Actor",
            state_repository=state_repository,
            load_state_on_init=True,
        )

        await actor.spawn()

        # Set good state
        actor.update_state("status", "healthy")
        actor.update_state("data", {"value": 100})

        # Create checkpoint with explicit state (not current actor state)
        healthy_state = {
            "internal_state": dict(actor.internal_state),  # Copy current internal state
            "message_count": actor.message_count,
            "error_count": actor.error_count,
            "state": actor.state.value,
            "created_at": actor.created_at,
            "last_activity": actor.last_activity,
            "topics": actor.topics,
            "capabilities": actor.capabilities,
        }

        checkpoint = await state_repository.checkpoint(
            agent_id=actor.agent_id,
            state=healthy_state,
            version=1,
            metadata={"status": "healthy"},
        )

        # Verify checkpoint was created with correct state
        assert checkpoint is not None
        assert checkpoint.state.get("internal_state", {}).get("status") == "healthy"

        # Simulate error that corrupts state
        actor.update_state("status", "corrupted")
        actor.update_state("data", {"value": -1, "error": True})
        await actor.save_state()

        # Verify corruption
        assert actor.get_state("status") == "corrupted"

        # Rollback to healthy checkpoint
        restored = await actor.restore_from_checkpoint(checkpoint.checkpoint_id)
        assert restored is True

        # Verify the repository state was restored
        record = await state_repository.load_state(actor.agent_id)
        assert record is not None

        # The restored state should have the checkpoint's state
        restored_internal = record.state.get("internal_state", {})
        restored_status = restored_internal.get("status")
        assert restored_status == "healthy", f"Expected 'healthy' but got '{restored_status}'"

        await actor.terminate()


class TestConcurrentActors:
    """Test multiple actors with shared state repository."""

    @pytest.mark.asyncio
    async def test_multiple_actors_concurrent(self, state_repository):
        """Test multiple actors can persist state concurrently."""
        actors = []

        # Create multiple actors
        for i in range(5):
            actor = TestActor(
                agent_id=f"concurrent-actor-{i}",
                name=f"Concurrent Actor {i}",
                state_repository=state_repository,
                load_state_on_init=True,
            )
            actors.append(actor)

        # Spawn all actors
        await asyncio.gather(*[a.spawn() for a in actors])

        # Update state concurrently
        async def update_actor_state(actor, value):
            actor.update_state("concurrent_value", value)
            await actor.save_state()

        tasks = [update_actor_state(a, i * 10) for i, a in enumerate(actors)]
        await asyncio.gather(*tasks)

        # Verify all states persisted
        for i, actor in enumerate(actors):
            record = await state_repository.load_state(actor.agent_id)
            assert record is not None
            # State is nested in internal_state
            assert record.state.get("internal_state", {}).get("concurrent_value") == i * 10

        # Terminate all
        await asyncio.gather(*[a.terminate() for a in actors])

    @pytest.mark.asyncio
    async def test_list_active_states(self, state_repository):
        """Test listing all active actor states."""
        # Create and save states for multiple actors
        for i in range(3):
            actor = TestActor(
                agent_id=f"list-test-actor-{i}",
                name=f"List Test Actor {i}",
                state_repository=state_repository,
            )
            await actor.spawn()
            actor.update_state("index", i)
            await actor.save_state()
            await actor.terminate()

        # List all active states
        states = await state_repository.list_active_states()

        assert len(states) >= 3
        agent_ids = {s.agent_id for s in states}
        for i in range(3):
            assert f"list-test-actor-{i}" in agent_ids


class TestActorMessageProcessing:
    """Test state persistence during message processing."""

    @pytest.mark.asyncio
    async def test_state_persisted_on_message(self, state_repository):
        """Test state is updated when processing messages."""
        actor = TestActor(
            agent_id="message-test-actor",
            name="Message Test Actor",
            state_repository=state_repository,
            load_state_on_init=True,
        )

        await actor.spawn()

        # Send messages
        for i in range(3):
            message = ActorMessage(
                sender="test-sender",
                message_type="test",
                content={"message_id": i, "data": f"message-{i}"},
                timestamp=datetime.now(timezone.utc).isoformat(),
            )
            await actor.put_message(message)

        # Wait for processing
        await asyncio.sleep(0.5)

        # Verify state was updated
        assert len(actor.processed_messages) == 3
        assert actor.get_state("message_count") == 3

        # Save and verify persistence
        await actor.save_state()
        record = await state_repository.load_state(actor.agent_id)
        assert record is not None
        assert record.state.get("message_count") == 3

        await actor.terminate()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
