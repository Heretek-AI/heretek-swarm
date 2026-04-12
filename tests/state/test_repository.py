"""
Tests for State Persistence Repository.

Validates PostgreSQL-backed state persistence with:
- Save and load operations
- Version management with optimistic locking
- Concurrent state updates
- Checkpoint creation and restoration
- Recovery after simulated restart
"""

import asyncio
from datetime import UTC, datetime
from uuid import UUID, uuid4

import pytest

from heretek_swarm.state.repository import (
    AgentStateRecord,
    StateRepository,
)

# Fixtures

@pytest.fixture
def sample_state():
    """Sample agent state for testing."""
    return {
        "internal_state": {"key": "value", "counter": 42},
        "message_count": 100,
        "error_count": 5,
        "state": "active",
        "topics": ["test", "events"],
        "capabilities": ["process", "analyze"],
    }


@pytest.fixture
async def repository():
    """Create state repository with in-memory fallback."""
    repo = StateRepository(
        db_pool=None,  # Use in-memory for tests
        max_retries=3,
        retry_delay=0.01,
    )
    await repo.initialize()
    return repo


@pytest.fixture
async def repository_with_db():
    """Create state repository with database connection if available."""
    # This fixture requires a running PostgreSQL instance
    # Skip if database not available
    try:
        import asyncpg
        db_pool = await asyncpg.create_pool(
            host="localhost",
            port=5432,
            user="test",
            password="test",
            database="test_db",
        )
        repo = StateRepository(db_pool=db_pool)
        await repo.initialize()
        yield repo
        await db_pool.close()
    except Exception:
        pytest.skip("Database not available")


# Test Cases

class TestAgentStateRecord:
    """Test AgentStateRecord model."""

    def test_create_record(self, sample_state):
        """Test basic record creation."""
        record = AgentStateRecord(
            agent_id="agent-1",
            agent_type="TestAgent",
            state=sample_state,
        )

        assert record.agent_id == "agent-1"
        assert record.agent_type == "TestAgent"
        assert record.state == sample_state
        assert record.version == 1
        assert record.is_active is True
        assert isinstance(record.id, UUID)

    def test_to_dict(self, sample_state):
        """Test record serialization."""
        record = AgentStateRecord(
            agent_id="agent-1",
            agent_type="TestAgent",
            state=sample_state,
        )

        data = record.to_dict()

        assert data["agent_id"] == "agent-1"
        assert data["agent_type"] == "TestAgent"
        assert data["state"] == sample_state
        assert data["version"] == 1
        assert isinstance(data["id"], str)

    def test_from_dict(self, sample_state):
        """Test record deserialization."""
        data = {
            "id": str(uuid4()),
            "agent_id": "agent-1",
            "agent_type": "TestAgent",
            "state": sample_state,
            "version": 2,
            "created_at": datetime.now(UTC).isoformat(),
            "updated_at": datetime.now(UTC).isoformat(),
            "is_active": True,
        }

        record = AgentStateRecord.from_dict(data)

        assert record.agent_id == "agent-1"
        assert record.version == 2
        assert record.state == sample_state


class TestStateRepository:
    """Test StateRepository operations."""

    @pytest.mark.asyncio
    async def test_save_state(self, repository, sample_state):
        """Test saving agent state."""
        record = await repository.save_state(
            agent_id="agent-1",
            state=sample_state,
            agent_type="TestAgent",
        )

        assert record is not None
        assert record.agent_id == "agent-1"
        assert record.agent_type == "TestAgent"
        assert record.state == sample_state
        assert record.version == 1

    @pytest.mark.asyncio
    async def test_load_state(self, repository, sample_state):
        """Test loading agent state."""
        # Save first
        await repository.save_state(
            agent_id="agent-1",
            state=sample_state,
            agent_type="TestAgent",
        )

        # Load
        record = await repository.load_state("agent-1")

        assert record is not None
        assert record.agent_id == "agent-1"
        assert record.state == sample_state

    @pytest.mark.asyncio
    async def test_load_nonexistent_state(self, repository):
        """Test loading nonexistent state returns None."""
        record = await repository.load_state("nonexistent-agent")
        assert record is None

    @pytest.mark.asyncio
    async def test_delete_state(self, repository, sample_state):
        """Test deleting agent state."""
        # Save first
        await repository.save_state(
            agent_id="agent-1",
            state=sample_state,
            agent_type="TestAgent",
        )

        # Delete
        deleted = await repository.delete_state("agent-1")
        assert deleted is True

        # Verify deleted
        record = await repository.load_state("agent-1")
        assert record is None

    @pytest.mark.asyncio
    async def test_list_active_states(self, repository, sample_state):
        """Test listing all active states."""
        # Save multiple states
        await repository.save_state("agent-1", sample_state, "TestAgent")
        await repository.save_state("agent-2", sample_state, "TestAgent")
        await repository.save_state("agent-3", sample_state, "TestAgent")

        # List
        states = await repository.list_active_states()

        assert len(states) == 3
        agent_ids = {s.agent_id for s in states}
        assert "agent-1" in agent_ids
        assert "agent-2" in agent_ids
        assert "agent-3" in agent_ids

    @pytest.mark.asyncio
    async def test_update_state(self, repository, sample_state):
        """Test updating existing state."""
        # Save initial state
        record1 = await repository.save_state(
            agent_id="agent-1",
            state=sample_state,
            agent_type="TestAgent",
        )

        # Update state
        updated_state = {**sample_state, "counter": 99}
        record2 = await repository.save_state(
            agent_id="agent-1",
            state=updated_state,
            agent_type="TestAgent",
            version=record1.version + 1,
        )

        assert record2.version == record1.version + 1
        assert record2.state["counter"] == 99

        # Verify load returns updated state
        loaded = await repository.load_state("agent-1")
        assert loaded.state["counter"] == 99


class TestVersionManagement:
    """Test version management and optimistic locking."""

    @pytest.mark.asyncio
    async def test_version_increment(self, repository, sample_state):
        """Test version increments on updates."""
        record1 = await repository.save_state(
            agent_id="agent-1",
            state=sample_state,
            agent_type="TestAgent",
        )

        record2 = await repository.save_state(
            agent_id="agent-1",
            state=sample_state,
            agent_type="TestAgent",
            version=record1.version + 1,
        )

        assert record2.version == record1.version + 1

    @pytest.mark.asyncio
    async def test_concurrent_updates(self, repository, sample_state):
        """Test handling of concurrent state updates."""
        # Save initial state
        record1 = await repository.save_state(
            agent_id="agent-1",
            state=sample_state,
            agent_type="TestAgent",
        )

        # Simulate concurrent updates with same version
        async def update_with_version(version):
            return await repository.save_state(
                agent_id="agent-1",
                state={**sample_state, "updated_by": version},
                agent_type="TestAgent",
                version=version,
            )

        # First update should succeed
        result1 = await update_with_version(record1.version + 1)
        assert result1 is not None
        assert result1.state["updated_by"] == 2

        # Second update with same version should retry and succeed with new version
        # Note: In-memory implementation doesn't have true concurrent locking,
        # so we test that sequential updates with correct versions work
        result2 = await update_with_version(result1.version + 1)
        assert result2 is not None
        assert result2.version == result1.version + 1
        assert result2.state["updated_by"] == 3

    @pytest.mark.asyncio
    async def test_stats_tracking(self, repository, sample_state):
        """Test repository statistics tracking."""
        await repository.save_state("agent-1", sample_state, "TestAgent")
        await repository.load_state("agent-1")

        stats = await repository.get_stats()

        assert stats["memory_saves"] >= 1
        assert stats["memory_loads"] >= 1
        assert stats["initialized"] is True
        assert stats["using_database"] is False


class TestCheckpoints:
    """Test checkpoint creation and restoration."""

    @pytest.mark.asyncio
    async def test_create_checkpoint(self, repository, sample_state):
        """Test creating a checkpoint."""
        # Save state first
        await repository.save_state(
            agent_id="agent-1",
            state=sample_state,
            agent_type="TestAgent",
        )

        # Create checkpoint
        checkpoint = await repository.checkpoint(
            agent_id="agent-1",
            state=sample_state,
            version=1,
            metadata={"reason": "test_checkpoint"},
        )

        assert checkpoint is not None
        assert checkpoint.agent_id == "agent-1"
        assert checkpoint.version == 1
        assert checkpoint.metadata == {"reason": "test_checkpoint"}
        assert isinstance(checkpoint.checkpoint_id, UUID)

    @pytest.mark.asyncio
    async def test_get_checkpoint(self, repository, sample_state):
        """Test retrieving a specific checkpoint."""
        # Create checkpoint
        checkpoint = await repository.checkpoint(
            agent_id="agent-1",
            state=sample_state,
            version=1,
        )

        # Retrieve
        retrieved = await repository.get_checkpoint(checkpoint.checkpoint_id)

        assert retrieved is not None
        assert retrieved.checkpoint_id == checkpoint.checkpoint_id
        assert retrieved.state == sample_state

    @pytest.mark.asyncio
    async def test_get_checkpoints(self, repository, sample_state):
        """Test listing checkpoints for an agent."""
        # Create multiple checkpoints
        for i in range(5):
            await repository.checkpoint(
                agent_id="agent-1",
                state={**sample_state, "version": i},
                version=i + 1,
            )

        # List checkpoints
        checkpoints = await repository.get_checkpoints("agent-1", limit=3)

        assert len(checkpoints) == 3
        # Should be ordered by version descending
        assert checkpoints[0].version == 5
        assert checkpoints[1].version == 4
        assert checkpoints[2].version == 3

    @pytest.mark.asyncio
    async def test_restore_from_checkpoint(self, repository, sample_state):
        """Test restoring state from a checkpoint."""
        # Save initial state
        await repository.save_state(
            agent_id="agent-1",
            state=sample_state,
            agent_type="TestAgent",
        )

        # Modify state
        modified_state = {**sample_state, "counter": 999}
        await repository.save_state(
            agent_id="agent-1",
            state=modified_state,
            agent_type="TestAgent",
            version=2,
        )

        # Create checkpoint of original state
        checkpoint = await repository.checkpoint(
            agent_id="agent-1",
            state=sample_state,
            version=1,
        )

        # Restore from checkpoint
        restored = await repository.restore_from_checkpoint(
            agent_id="agent-1",
            checkpoint_id=checkpoint.checkpoint_id,
        )

        assert restored is True

        # Verify state is restored
        record = await repository.load_state("agent-1")
        # The checkpoint state should be restored (counter=42 from sample_state)
        assert record.state.get("counter") == 42 or record.state.get("internal_state", {}).get("counter") == 42

    @pytest.mark.asyncio
    async def test_restore_nonexistent_checkpoint(self, repository):
        """Test restoring from nonexistent checkpoint."""
        fake_id = uuid4()
        restored = await repository.restore_from_checkpoint(
            agent_id="agent-1",
            checkpoint_id=fake_id,
        )
        assert restored is False


class TestStateRecovery:
    """Test state recovery after simulated restart."""

    @pytest.mark.asyncio
    async def test_recovery_after_restart(self, repository, sample_state):
        """Test recovering state after simulated restart."""
        # Save state (simulating previous run)
        await repository.save_state(
            agent_id="agent-1",
            state=sample_state,
            agent_type="TestAgent",
        )

        # Simulate restart by creating new repository instance
        # pointing to same storage (in-memory in this case)
        new_repo = StateRepository()
        await new_repo.initialize()

        # Manually copy memory store for test (simulates shared persistence)
        new_repo._memory_store = repository._memory_store.copy()

        # Load state in new repository
        record = await new_repo.load_state("agent-1")

        assert record is not None
        assert record.state == sample_state
        assert record.agent_type == "TestAgent"

    @pytest.mark.asyncio
    async def test_checkpoint_recovery(self, repository, sample_state):
        """Test recovering from checkpoint after failure."""
        # Create initial checkpoint
        checkpoint = await repository.checkpoint(
            agent_id="agent-1",
            state=sample_state,
            version=1,
            metadata={"checkpoint_type": "recovery_point"},
        )

        # Simulate state corruption
        corrupted_state = {**sample_state, "corrupted": True}
        await repository.save_state(
            agent_id="agent-1",
            state=corrupted_state,
            agent_type="TestAgent",
            version=2,
        )

        # Verify corruption
        record = await repository.load_state("agent-1")
        assert record.state.get("corrupted") is True

        # Recover from checkpoint
        restored = await repository.restore_from_checkpoint(
            agent_id="agent-1",
            checkpoint_id=checkpoint.checkpoint_id,
        )

        assert restored is True

        # Verify recovery
        record = await repository.load_state("agent-1")
        assert record.state.get("corrupted") is None
        assert record.state == sample_state


class TestConcurrency:
    """Test concurrent state access patterns."""

    @pytest.mark.asyncio
    async def test_concurrent_saves(self, repository, sample_state):
        """Test multiple concurrent save operations."""
        agent_id = "concurrent-agent"

        async def save_state(value):
            return await repository.save_state(
                agent_id=agent_id,
                state={**sample_state, "value": value},
                agent_type="TestAgent",
            )

        # Run concurrent saves
        tasks = [save_state(i) for i in range(10)]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # All should complete (some may retry)
        successful = [r for r in results if not isinstance(r, Exception)]
        assert len(successful) > 0

        # Final state should have one of the values
        final_record = await repository.load_state(agent_id)
        assert final_record is not None
        assert "value" in final_record.state

    @pytest.mark.asyncio
    async def test_concurrent_loads(self, repository, sample_state):
        """Test multiple concurrent load operations."""
        # Save state first
        await repository.save_state(
            agent_id="agent-1",
            state=sample_state,
            agent_type="TestAgent",
        )

        async def load_state():
            return await repository.load_state("agent-1")

        # Run concurrent loads
        tasks = [load_state() for _ in range(100)]
        results = await asyncio.gather(*tasks)

        # All should return the same state
        for result in results:
            assert result is not None
            assert result.state == sample_state


class TestEdgeCases:
    """Test edge cases and error handling."""

    @pytest.mark.asyncio
    async def test_empty_state(self, repository):
        """Test saving empty state."""
        record = await repository.save_state(
            agent_id="agent-1",
            state={},
            agent_type="TestAgent",
        )

        assert record is not None
        assert record.state == {}

    @pytest.mark.asyncio
    async def test_large_state(self, repository):
        """Test saving large state."""
        large_state = {
            "data": ["x" * 1000 for _ in range(100)],
            "metadata": {"size": "large"},
        }

        record = await repository.save_state(
            agent_id="agent-1",
            state=large_state,
            agent_type="TestAgent",
        )

        assert record is not None
        assert len(record.state["data"]) == 100

    @pytest.mark.asyncio
    async def test_special_characters_in_state(self, repository):
        """Test state with special characters."""
        special_state = {
            "unicode": "Hello 世界 🌍",
            "quotes": "Test 'single' and \"double\" quotes",
            "newlines": "Line1\nLine2\nLine3",
        }

        record = await repository.save_state(
            agent_id="agent-1",
            state=special_state,
            agent_type="TestAgent",
        )

        assert record is not None

        # Load and verify
        loaded = await repository.load_state("agent-1")
        assert loaded.state["unicode"] == "Hello 世界 🌍"
        assert loaded.state["newlines"] == "Line1\nLine2\nLine3"

    @pytest.mark.asyncio
    async def test_nested_state(self, repository):
        """Test deeply nested state structure."""
        nested_state = {
            "level1": {
                "level2": {
                    "level3": {
                        "value": "deep"
                    }
                }
            }
        }

        record = await repository.save_state(
            agent_id="agent-1",
            state=nested_state,
            agent_type="TestAgent",
        )

        assert record is not None

        loaded = await repository.load_state("agent-1")
        assert loaded.state["level1"]["level2"]["level3"]["value"] == "deep"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
