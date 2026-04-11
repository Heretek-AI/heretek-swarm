"""
Tests for State Management System.

Validates functionality, performance, and reliability of
message lineage, snapshots, and state management.
"""

from datetime import datetime
from uuid import uuid4

import pytest

from heretek_swarm.state import (
    AgentState,
    ConversationState,
    LineageConfig,
    LineageTracker,
    MessageLineage,
    SnapshotConfig,
    SnapshotManager,
    StateConfig,
    StateManager,
    StateStatus,
    SystemState,
)

# Fixtures

@pytest.fixture
def lineage_config():
    """Test configuration for lineage tracker"""
    return LineageConfig(
        max_lineage_depth=50,
        cache_size=100
    )


@pytest.fixture
def snapshot_config(tmp_path):
    """Test configuration for snapshot manager"""
    return SnapshotConfig(
        storage_path=str(tmp_path / "snapshots"),
        max_snapshots=20,
        auto_snapshot_enabled=False,
        auto_cleanup_enabled=False
    )


@pytest.fixture
def state_config(snapshot_config):
    """Test configuration for state manager"""
    return StateConfig(
        lineage=LineageConfig(),
        snapshots=snapshot_config,
        max_agents=100,
        auto_recovery_enabled=False
    )


@pytest.fixture
async def lineage_tracker(lineage_config):
    """Create lineage tracker"""
    tracker = LineageTracker(lineage_config)
    yield tracker


@pytest.fixture
async def snapshot_manager(snapshot_config):
    """Create snapshot manager"""
    manager = SnapshotManager(snapshot_config)
    await manager.initialize()
    yield manager
    await manager.shutdown()


@pytest.fixture
async def state_manager(state_config):
    """Create state manager"""
    manager = StateManager(state_config)
    await manager.initialize()
    yield manager
    await manager.shutdown()


# Test Cases

class TestMessageLineage:
    """Test message lineage model"""

    def test_create_lineage(self):
        """Test basic lineage creation"""
        lineage = MessageLineage(
            conversation_id=uuid4(),
            root_message_id=uuid4(),
            sender_agent_id="agent-1",
            content_hash="abc123",
            content_size_bytes=100
        )

        assert lineage.message_id is not None
        assert lineage.depth == 0
        assert lineage.child_count == 0

    def test_lineage_with_parent(self):
        """Test lineage with parent relationship"""
        parent_id = uuid4()
        root_id = uuid4()

        lineage = MessageLineage(
            conversation_id=uuid4(),
            parent_message_id=parent_id,
            root_message_id=root_id,
            ancestor_ids=[parent_id],
            depth=1,
            sender_agent_id="agent-2",
            content_hash="def456",
            content_size_bytes=200
        )

        assert lineage.parent_message_id == parent_id
        assert lineage.root_message_id == root_id
        assert lineage.depth == 1
        assert parent_id in lineage.ancestor_ids


class TestAgentState:
    """Test agent state model"""

    def test_create_agent_state(self):
        """Test basic agent state creation"""
        state = AgentState(
            agent_id="agent-1",
            agent_type="worker"
        )

        assert state.agent_id == "agent-1"
        assert state.status == StateStatus.ACTIVE
        assert state.version == 1

    def test_agent_state_touch(self):
        """Test state update tracking"""
        state = AgentState(
            agent_id="agent-1",
            agent_type="worker"
        )

        original_time = state.updated_at
        original_version = state.version

        state.touch()
        state.version += 1

        assert state.updated_at > original_time
        assert state.version == original_version + 1

    def test_compute_hash(self):
        """Test state hash computation"""
        state1 = AgentState(
            agent_id="agent-1",
            agent_type="worker",
            working_memory={"key": "value1"}
        )

        state2 = AgentState(
            agent_id="agent-1",
            agent_type="worker",
            working_memory={"key": "value2"}
        )

        hash1 = state1.compute_hash()
        hash2 = state2.compute_hash()

        assert hash1 != hash2


class TestConversationState:
    """Test conversation state model"""

    def test_create_conversation(self):
        """Test basic conversation creation"""
        conv = ConversationState(
            initiator_agent_id="agent-1",
            participant_ids={"agent-1", "agent-2"}
        )

        assert conv.initiator_agent_id == "agent-1"
        assert len(conv.participant_ids) == 2
        assert conv.status == StateStatus.ACTIVE

    def test_add_decision(self):
        """Test adding decisions to conversation"""
        conv = ConversationState(
            initiator_agent_id="agent-1"
        )

        conv.decisions.append({
            "decision": "proceed",
            "by": "agent-1",
            "at": datetime.utcnow().isoformat()
        })

        assert len(conv.decisions) == 1


class TestLineageTracker:
    """Test lineage tracker functionality"""

    @pytest.mark.asyncio
    async def test_record_root_message(self, lineage_tracker):
        """Test recording a root message"""
        conversation_id = uuid4()

        lineage = await lineage_tracker.record_message(
            content="Root message",
            conversation_id=conversation_id,
            sender_agent_id="agent-1"
        )

        assert lineage.message_id is not None
        assert lineage.parent_message_id is None
        assert lineage.root_message_id == lineage.message_id
        assert lineage.depth == 0

    @pytest.mark.asyncio
    async def test_record_child_message(self, lineage_tracker):
        """Test recording a child message"""
        conversation_id = uuid4()

        # Record root
        root = await lineage_tracker.record_message(
            content="Root",
            conversation_id=conversation_id,
            sender_agent_id="agent-1"
        )

        # Record child
        child = await lineage_tracker.record_message(
            content="Child",
            conversation_id=conversation_id,
            sender_agent_id="agent-2",
            receiver_agent_id="agent-1",
            parent_message_id=root.message_id
        )

        assert child.parent_message_id == root.message_id
        assert child.root_message_id == root.message_id
        assert child.depth == 1
        assert root.message_id in child.ancestor_ids

    @pytest.mark.asyncio
    async def test_get_ancestry(self, lineage_tracker):
        """Test getting message ancestry"""
        conversation_id = uuid4()

        # Create chain: root -> child1 -> child2
        root = await lineage_tracker.record_message(
            content="Root",
            conversation_id=conversation_id,
            sender_agent_id="agent-1"
        )

        child1 = await lineage_tracker.record_message(
            content="Child1",
            conversation_id=conversation_id,
            sender_agent_id="agent-2",
            parent_message_id=root.message_id
        )

        child2 = await lineage_tracker.record_message(
            content="Child2",
            conversation_id=conversation_id,
            sender_agent_id="agent-1",
            parent_message_id=child1.message_id
        )

        # Get ancestry
        ancestry = await lineage_tracker.get_ancestry(child2.message_id)

        assert len(ancestry) == 3
        assert ancestry[0].message_id == root.message_id
        assert ancestry[1].message_id == child1.message_id
        assert ancestry[2].message_id == child2.message_id

    @pytest.mark.asyncio
    async def test_get_descendants(self, lineage_tracker):
        """Test getting message descendants"""
        conversation_id = uuid4()

        # Create tree: root -> [child1, child2]
        root = await lineage_tracker.record_message(
            content="Root",
            conversation_id=conversation_id,
            sender_agent_id="agent-1"
        )

        child1 = await lineage_tracker.record_message(
            content="Child1",
            conversation_id=conversation_id,
            sender_agent_id="agent-2",
            parent_message_id=root.message_id
        )

        child2 = await lineage_tracker.record_message(
            content="Child2",
            conversation_id=conversation_id,
            sender_agent_id="agent-3",
            parent_message_id=root.message_id
        )

        # Get descendants
        descendants = await lineage_tracker.get_descendants(root.message_id)

        assert len(descendants) == 2
        descendant_ids = {d.message_id for d in descendants}
        assert child1.message_id in descendant_ids
        assert child2.message_id in descendant_ids

    @pytest.mark.asyncio
    async def test_find_branch_points(self, lineage_tracker):
        """Test finding branch points"""
        conversation_id = uuid4()

        # Create branch point
        root = await lineage_tracker.record_message(
            content="Root",
            conversation_id=conversation_id,
            sender_agent_id="agent-1"
        )

        await lineage_tracker.record_message(
            content="Child1",
            conversation_id=conversation_id,
            sender_agent_id="agent-2",
            parent_message_id=root.message_id
        )

        await lineage_tracker.record_message(
            content="Child2",
            conversation_id=conversation_id,
            sender_agent_id="agent-3",
            parent_message_id=root.message_id
        )

        # Find branch points
        branches = await lineage_tracker.find_branch_points(conversation_id)

        assert len(branches) == 1
        assert branches[0].message_id == root.message_id

    @pytest.mark.asyncio
    async def test_integrity_verification(self, lineage_tracker):
        """Test message integrity verification"""
        conversation_id = uuid4()

        root = await lineage_tracker.record_message(
            content="Root",
            conversation_id=conversation_id,
            sender_agent_id="agent-1"
        )

        child = await lineage_tracker.record_message(
            content="Child",
            conversation_id=conversation_id,
            sender_agent_id="agent-2",
            parent_message_id=root.message_id
        )

        # Verify integrity
        assert await lineage_tracker.verify_integrity(child.message_id)

    @pytest.mark.asyncio
    async def test_stats(self, lineage_tracker):
        """Test lineage statistics"""
        conversation_id = uuid4()

        for i in range(10):
            await lineage_tracker.record_message(
                content=f"Message {i}",
                conversation_id=conversation_id,
                sender_agent_id=f"agent-{i % 3}"
            )

        stats = lineage_tracker.get_stats()

        assert stats["total_messages"] == 10
        assert stats["active_messages"] == 10


class TestSnapshotManager:
    """Test snapshot manager functionality"""

    @pytest.mark.asyncio
    async def test_create_snapshot(self, snapshot_manager):
        """Test creating a snapshot"""
        system_state = SystemState(system_id="test-system")
        agent_state = AgentState(agent_id="agent-1", agent_type="worker")

        snapshot = await snapshot_manager.create_snapshot(
            system_state=system_state,
            agent_states={"agent-1": agent_state},
            trigger="test",
            description="Test snapshot"
        )

        assert snapshot.snapshot_id is not None
        assert snapshot.trigger == "test"
        assert snapshot.system_state is not None
        assert len(snapshot.agent_states) == 1

    @pytest.mark.asyncio
    async def test_get_snapshot(self, snapshot_manager):
        """Test retrieving a snapshot"""
        snapshot = await snapshot_manager.create_snapshot(
            system_state=SystemState(),
            trigger="test"
        )

        retrieved = await snapshot_manager.get_snapshot(snapshot.snapshot_id)

        assert retrieved is not None
        assert retrieved.snapshot_id == snapshot.snapshot_id

    @pytest.mark.asyncio
    async def test_list_snapshots(self, snapshot_manager):
        """Test listing snapshots"""
        # Create multiple snapshots
        for i in range(3):
            await snapshot_manager.create_snapshot(
                system_state=SystemState(),
                trigger=f"test-{i}"
            )

        snapshots = await snapshot_manager.list_snapshots()

        assert len(snapshots) == 3

    @pytest.mark.asyncio
    async def test_delete_snapshot(self, snapshot_manager):
        """Test deleting a snapshot"""
        snapshot = await snapshot_manager.create_snapshot(
            system_state=SystemState(),
            trigger="test"
        )

        deleted = await snapshot_manager.delete_snapshot(snapshot.snapshot_id)
        assert deleted is True

        retrieved = await snapshot_manager.get_snapshot(snapshot.snapshot_id)
        assert retrieved is None

    @pytest.mark.asyncio
    async def test_compute_diff(self, snapshot_manager):
        """Test computing diff between snapshots"""
        # Create first snapshot
        agent1_v1 = AgentState(
            agent_id="agent-1",
            agent_type="worker",
            working_memory={"value": 1}
        )

        snapshot1 = await snapshot_manager.create_snapshot(
            agent_states={"agent-1": agent1_v1},
            trigger="test-1"
        )

        # Create second snapshot
        agent1_v2 = AgentState(
            agent_id="agent-1",
            agent_type="worker",
            working_memory={"value": 2}
        )
        agent2 = AgentState(
            agent_id="agent-2",
            agent_type="coordinator"
        )

        snapshot2 = await snapshot_manager.create_snapshot(
            agent_states={
                "agent-1": agent1_v2,
                "agent-2": agent2
            },
            trigger="test-2"
        )

        # Compute diff
        diff = await snapshot_manager.compute_diff(
            snapshot1.snapshot_id,
            snapshot2.snapshot_id
        )

        assert diff is not None
        assert "agent-2" in diff.added_agents
        assert "agent-1" in diff.modified_agents


class TestStateManager:
    """Test unified state manager"""

    @pytest.mark.asyncio
    async def test_register_agent(self, state_manager):
        """Test agent registration"""
        agent = await state_manager.register_agent(
            agent_id="agent-1",
            agent_type="worker"
        )

        assert agent.agent_id == "agent-1"
        assert agent.agent_type == "worker"
        assert agent.status == StateStatus.ACTIVE

    @pytest.mark.asyncio
    async def test_update_agent_state(self, state_manager):
        """Test updating agent state"""
        await state_manager.register_agent("agent-1", "worker")

        updated = await state_manager.update_agent_state(
            agent_id="agent-1",
            updates={"state": "active"},
            working_memory_updates={"task": "analysis"},
            context_updates={"priority": "high"}
        )

        assert updated is not None
        assert updated.working_memory["task"] == "analysis"
        assert updated.context["priority"] == "high"

    @pytest.mark.asyncio
    async def test_start_conversation(self, state_manager):
        """Test starting a conversation"""
        await state_manager.register_agent("agent-1", "initiator")
        await state_manager.register_agent("agent-2", "participant")

        conv = await state_manager.start_conversation(
            initiator_agent_id="agent-1",
            participant_ids={"agent-1", "agent-2"},
            topic="Test conversation"
        )

        assert conv.initiator_agent_id == "agent-1"
        assert len(conv.participant_ids) == 2
        assert conv.topic == "Test conversation"

    @pytest.mark.asyncio
    async def test_record_message(self, state_manager):
        """Test recording a message"""
        await state_manager.register_agent("agent-1", "sender")
        await state_manager.register_agent("agent-2", "receiver")

        conv = await state_manager.start_conversation(
            initiator_agent_id="agent-1"
        )

        lineage = await state_manager.record_message(
            conversation_id=conv.conversation_id,
            sender_agent_id="agent-1",
            content="Test message",
            receiver_agent_id="agent-2"
        )

        assert lineage is not None
        assert lineage.sender_agent_id == "agent-1"
        assert lineage.receiver_agent_id == "agent-2"

    @pytest.mark.asyncio
    async def test_create_snapshot(self, state_manager):
        """Test creating state snapshot"""
        await state_manager.register_agent("agent-1", "worker")

        snapshot = await state_manager.create_snapshot(
            trigger="test"
        )

        assert snapshot.snapshot_id is not None
        assert snapshot.system_state is not None
        assert len(snapshot.agent_states) == 1

    @pytest.mark.asyncio
    async def test_rollback_to_snapshot(self, state_manager):
        """Test rolling back to a snapshot"""
        # Create initial state
        await state_manager.register_agent("agent-1", "worker")

        snapshot = await state_manager.create_snapshot(trigger="before")

        # Make changes
        await state_manager.register_agent("agent-2", "coordinator")

        # Verify state changed
        agents = await state_manager.get_active_agents()
        assert len(agents) == 2

        # Rollback
        success = await state_manager.rollback_to_snapshot(snapshot.snapshot_id)
        assert success is True

        # Verify rollback
        agents = await state_manager.get_active_agents()
        assert len(agents) == 1
        assert agents[0].agent_id == "agent-1"

    @pytest.mark.asyncio
    async def test_get_stats(self, state_manager):
        """Test getting state statistics"""
        await state_manager.register_agent("agent-1", "worker")
        await state_manager.register_agent("agent-2", "coordinator")

        conv = await state_manager.start_conversation(
            initiator_agent_id="agent-1"
        )

        await state_manager.record_message(
            conversation_id=conv.conversation_id,
            sender_agent_id="agent-1",
            content="Test"
        )

        stats = state_manager.get_stats()

        assert stats["agents"]["total"] == 2
        assert stats["agents"]["active"] == 2
        assert stats["conversations"]["total"] == 1


class TestIntegration:
    """Integration tests"""

    @pytest.mark.asyncio
    async def test_full_workflow(self, state_manager):
        """Test complete workflow"""
        # 1. Register agents
        agent1 = await state_manager.register_agent(
            "agent-1", "coordinator"
        )
        agent2 = await state_manager.register_agent(
            "agent-2", "worker"
        )

        # 2. Start conversation
        conv = await state_manager.start_conversation(
            initiator_agent_id="agent-1",
            participant_ids={"agent-1", "agent-2"},
            topic="Collaborative task"
        )

        # 3. Exchange messages
        msg1 = await state_manager.record_message(
            conversation_id=conv.conversation_id,
            sender_agent_id="agent-1",
            content="Please analyze the data",
            receiver_agent_id="agent-2"
        )

        msg2 = await state_manager.record_message(
            conversation_id=conv.conversation_id,
            sender_agent_id="agent-2",
            content="Analysis complete",
            receiver_agent_id="agent-1",
            parent_message_id=msg1.message_id
        )

        # 4. Create snapshot
        snapshot = await state_manager.create_snapshot(
            trigger="checkpoint",
            description="After analysis"
        )

        # 5. Verify lineage
        ancestry = await state_manager.lineage.get_ancestry(msg2.message_id)
        assert len(ancestry) == 2

        # 6. Complete conversation
        completed = await state_manager.complete_conversation(conv.conversation_id)
        assert completed.status == StateStatus.COMPLETED

        # 7. Get final stats
        stats = state_manager.get_stats()
        assert stats["agents"]["total"] == 2
        assert stats["conversations"]["total"] >= 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
