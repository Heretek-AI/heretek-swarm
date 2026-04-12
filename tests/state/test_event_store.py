"""
Tests for Event Sourcing Implementation.

Tests cover:
- Domain event creation and serialization
- Event store append and retrieval
- State reconstruction from events
- Snapshot management
- Event querying by various criteria
- Event handlers
"""

import asyncio
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

import pytest

from heretek_swarm.state.event_store import (
    DomainEvent,
    EventStore,
    EventType,
    Snapshot,
    create_event_applier,
    get_event_store,
    setup_event_store,
)


class TestDomainEvent:
    """Test DomainEvent model."""

    def test_create_event(self):
        """Test creating a domain event."""
        event = DomainEvent.create(
            event_type="agent.state.changed",
            aggregate_id="agent-1",
            aggregate_type="Agent",
            payload={"old_state": "stopped", "new_state": "running"},
            version=1,
            metadata={"user_id": "user-123", "correlation_id": "corr-456"},
        )

        assert event.event_type == "agent.state.changed"
        assert event.aggregate_id == "agent-1"
        assert event.aggregate_type == "Agent"
        assert event.version == 1
        assert event.payload == {"old_state": "stopped", "new_state": "running"}
        assert event.metadata == {"user_id": "user-123", "correlation_id": "corr-456"}
        assert event.event_id is not None
        assert event.timestamp is not None

    def test_event_to_dict(self):
        """Test event serialization."""
        event = DomainEvent.create(
            event_type="agent.state.changed",
            aggregate_id="agent-1",
            aggregate_type="Agent",
            payload={"state": "running"},
        )

        data = event.to_dict()

        assert data["event_type"] == "agent.state.changed"
        assert data["aggregate_id"] == "agent-1"
        assert data["payload"] == {"state": "running"}
        assert "timestamp" in data
        assert "event_id" in data

    def test_event_from_dict(self):
        """Test event deserialization."""
        data = {
            "event_id": "test-123",
            "event_type": "agent.config.updated",
            "aggregate_id": "agent-1",
            "aggregate_type": "Agent",
            "timestamp": "2024-01-01T12:00:00+00:00",
            "version": 5,
            "payload": {"config_key": "config_value"},
            "metadata": {"source": "api"},
        }

        event = DomainEvent.from_dict(data)

        assert event.event_id == "test-123"
        assert event.event_type == "agent.config.updated"
        assert event.aggregate_id == "agent-1"
        assert event.version == 5
        assert event.payload == {"config_key": "config_value"}
        assert event.metadata == {"source": "api"}


class TestEventType:
    """Test EventType enumeration."""

    def test_agent_events(self):
        """Test agent event types."""
        assert EventType.AGENT_CREATED.value == "agent.created"
        assert EventType.AGENT_STARTED.value == "agent.started"
        assert EventType.AGENT_STOPPED.value == "agent.stopped"
        assert EventType.AGENT_STATE_CHANGED.value == "agent.state.changed"
        assert EventType.AGENT_CONFIG_UPDATED.value == "agent.config.updated"

    def test_workflow_events(self):
        """Test workflow event types."""
        assert EventType.WORKFLOW_CREATED.value == "workflow.created"
        assert EventType.WORKFLOW_STARTED.value == "workflow.started"
        assert EventType.WORKFLOW_COMPLETED.value == "workflow.completed"
        assert EventType.WORKFLOW_FAILED.value == "workflow.failed"

    def test_consciousness_events(self):
        """Test consciousness event types."""
        assert EventType.PHI_CALCULATED.value == "consciousness.phi.calculated"
        assert EventType.COHERENCE_UPDATED.value == "consciousness.coherence.updated"
        assert EventType.EMERGENCE_DETECTED.value == "consciousness.emergence.detected"

    def test_system_events(self):
        """Test system event types."""
        assert EventType.SYSTEM_HEALTH_CHECK.value == "system.health.check"
        assert EventType.SYSTEM_RESOURCE_UPDATED.value == "system.resource.updated"


class TestSnapshot:
    """Test Snapshot model."""

    def test_create_snapshot(self):
        """Test creating a snapshot."""
        snapshot = Snapshot(
            snapshot_id="snap-123",
            aggregate_id="agent-1",
            aggregate_type="Agent",
            state={"state": "running", "config": {"key": "value"}},
            version=10,
            created_at=datetime.now(timezone.utc),
            metadata={"reason": "periodic"},
        )

        assert snapshot.snapshot_id == "snap-123"
        assert snapshot.aggregate_id == "agent-1"
        assert snapshot.version == 10
        assert snapshot.state == {"state": "running", "config": {"key": "value"}}

    def test_snapshot_to_dict(self):
        """Test snapshot serialization."""
        snapshot = Snapshot(
            snapshot_id="snap-123",
            aggregate_id="agent-1",
            aggregate_type="Agent",
            state={"state": "running"},
            version=10,
            created_at=datetime.now(timezone.utc),
        )

        data = snapshot.to_dict()

        assert data["snapshot_id"] == "snap-123"
        assert data["aggregate_id"] == "agent-1"
        assert data["version"] == 10
        assert data["state"] == {"state": "running"}
        assert "created_at" in data

    def test_snapshot_from_dict(self):
        """Test snapshot deserialization."""
        data = {
            "snapshot_id": "snap-456",
            "aggregate_id": "agent-2",
            "aggregate_type": "Agent",
            "state": {"state": "stopped"},
            "version": 20,
            "created_at": "2024-01-01T12:00:00+00:00",
            "metadata": {"reason": "manual"},
        }

        snapshot = Snapshot.from_dict(data)

        assert snapshot.snapshot_id == "snap-456"
        assert snapshot.aggregate_id == "agent-2"
        assert snapshot.version == 20
        assert snapshot.state == {"state": "stopped"}
        assert snapshot.metadata == {"reason": "manual"}


class TestEventStore:
    """Test EventStore functionality."""

    @pytest.fixture
    def event_store(self):
        """Create an event store instance."""
        return EventStore(
            snapshot_interval=10,
            zero_trust_enabled=False,
        )

    @pytest.mark.asyncio
    async def test_initialize(self, event_store):
        """Test event store initialization."""
        await event_store.initialize()

        assert event_store._initialized is True

    @pytest.mark.asyncio
    async def test_append_event(self, event_store):
        """Test appending an event."""
        await event_store.initialize()

        event = DomainEvent.create(
            event_type="agent.state.changed",
            aggregate_id="agent-1",
            aggregate_type="Agent",
            payload={"state": "running"},
            version=1,
        )

        result = await event_store.append(event)

        assert result is True
        assert event_store._stats["events_appended"] == 1

    @pytest.mark.asyncio
    async def test_get_events(self, event_store):
        """Test retrieving events for an aggregate."""
        await event_store.initialize()

        # Append multiple events
        for i in range(5):
            event = DomainEvent.create(
                event_type="agent.state.changed",
                aggregate_id="agent-1",
                aggregate_type="Agent",
                payload={"state": f"state_{i}"},
                version=i + 1,
            )
            await event_store.append(event)

        # Get events
        events = await event_store.get_events("agent-1")

        assert len(events) == 5
        assert events[0].version == 1
        assert events[4].version == 5

    @pytest.mark.asyncio
    async def test_get_events_with_version_range(self, event_store):
        """Test retrieving events with version range."""
        await event_store.initialize()

        # Append events
        for i in range(10):
            event = DomainEvent.create(
                event_type="agent.state.changed",
                aggregate_id="agent-1",
                aggregate_type="Agent",
                payload={"state": f"state_{i}"},
                version=i + 1,
            )
            await event_store.append(event)

        # Get events with version range
        events = await event_store.get_events(
            "agent-1",
            from_version=3,
            to_version=7,
        )

        # Note: from_version is exclusive, to_version is inclusive
        # So we get versions 4, 5, 6, 7
        assert len(events) >= 4
        assert events[0].version == 4

    @pytest.mark.asyncio
    async def test_get_events_by_type(self, event_store):
        """Test retrieving events by type."""
        await event_store.initialize()

        # Append events of different types
        for i in range(5):
            event = DomainEvent.create(
                event_type="agent.state.changed",
                aggregate_id=f"agent-{i}",
                aggregate_type="Agent",
                payload={"state": "running"},
                version=1,
            )
            await event_store.append(event)

        for i in range(3):
            event = DomainEvent.create(
                event_type="agent.config.updated",
                aggregate_id=f"agent-{i}",
                aggregate_type="Agent",
                payload={"config": "updated"},
                version=1,
            )
            await event_store.append(event)

        # Get events by type
        events = await event_store.get_events_by_type(
            "agent.state.changed",
            limit=10,
        )

        assert len(events) == 5

    @pytest.mark.asyncio
    async def test_get_events_by_time_range(self, event_store):
        """Test retrieving events by time range."""
        await event_store.initialize()

        now = datetime.now(timezone.utc)

        # Append events with different timestamps
        for i in range(5):
            event = DomainEvent(
                event_id=f"event-{i}",
                event_type="agent.state.changed",
                aggregate_id="agent-1",
                aggregate_type="Agent",
                timestamp=now - timedelta(hours=i),
                version=i + 1,
                payload={"state": f"state_{i}"},
            )
            await event_store.append(event)

        # Get events in time range
        start_time = now - timedelta(hours=3)
        end_time = now - timedelta(hours=1)

        events = await event_store.get_events_by_time_range(
            start_time, end_time, limit=10
        )

        assert len(events) >= 2

    @pytest.mark.asyncio
    async def test_get_last_version(self, event_store):
        """Test getting the last version for an aggregate."""
        await event_store.initialize()

        # Append events
        for i in range(5):
            event = DomainEvent.create(
                event_type="agent.state.changed",
                aggregate_id="agent-1",
                aggregate_type="Agent",
                payload={"state": f"state_{i}"},
                version=i + 1,
            )
            await event_store.append(event)

        version = await event_store.get_last_version("agent-1")

        assert version == 5

    @pytest.mark.asyncio
    async def test_reconstruct_state(self, event_store):
        """Test reconstructing state from events."""
        await event_store.initialize()

        # Define state applier
        def applier(state, event):
            state["state"] = event.payload.get("state")
            state["version"] = event.version
            return state

        # Append events
        for i in range(5):
            event = DomainEvent.create(
                event_type="agent.state.changed",
                aggregate_id="agent-1",
                aggregate_type="Agent",
                payload={"state": f"state_{i}"},
                version=i + 1,
            )
            await event_store.append(event)

        # Reconstruct state
        state = await event_store.reconstruct_state(
            "agent-1",
            applier,
            initial_state={},
        )

        assert state["state"] == "state_4"
        assert state["version"] == 5

    @pytest.mark.asyncio
    async def test_create_snapshot(self, event_store):
        """Test creating a snapshot."""
        await event_store.initialize()

        state = {"state": "running", "config": {"key": "value"}}

        result = await event_store.create_snapshot(
            aggregate_id="agent-1",
            aggregate_type="Agent",
            state=state,
            version=10,
        )

        assert result is True
        assert event_store._stats["snapshots_created"] == 1

    @pytest.mark.asyncio
    async def test_get_snapshot(self, event_store):
        """Test retrieving a snapshot."""
        await event_store.initialize()

        state = {"state": "running"}
        await event_store.create_snapshot(
            aggregate_id="agent-1",
            aggregate_type="Agent",
            state=state,
            version=10,
        )

        snapshot = await event_store.get_snapshot("agent-1")

        assert snapshot is not None
        assert snapshot.aggregate_id == "agent-1"
        assert snapshot.version == 10
        assert snapshot.state == {"state": "running"}

    @pytest.mark.asyncio
    async def test_reconstruct_state_with_snapshot(self, event_store):
        """Test reconstructing state using a snapshot."""
        await event_store.initialize()

        def applier(state, event):
            state["state"] = event.payload.get("state")
            return state

        # Create snapshot at version 5
        await event_store.create_snapshot(
            aggregate_id="agent-1",
            aggregate_type="Agent",
            state={"state": "state_4"},
            version=5,
        )

        # Append more events after snapshot
        for i in range(5, 10):
            event = DomainEvent.create(
                event_type="agent.state.changed",
                aggregate_id="agent-1",
                aggregate_type="Agent",
                payload={"state": f"state_{i}"},
                version=i + 1,
            )
            await event_store.append(event)

        # Reconstruct state (should use snapshot)
        state = await event_store.reconstruct_state("agent-1", applier)

        assert state["state"] == "state_9"
        assert event_store._stats["snapshots_restored"] >= 1

    @pytest.mark.asyncio
    async def test_register_handler(self, event_store):
        """Test registering event handlers."""
        await event_store.initialize()

        received_events = []

        def handler(event):
            received_events.append(event)

        event_store.register_handler("agent.state.changed", handler)

        # Append event
        event = DomainEvent.create(
            event_type="agent.state.changed",
            aggregate_id="agent-1",
            aggregate_type="Agent",
            payload={"state": "running"},
        )
        await event_store.append(event)

        # Wait for async handler
        await asyncio.sleep(0.1)

        assert len(received_events) == 1
        assert received_events[0].event_type == "agent.state.changed"

    @pytest.mark.asyncio
    async def test_get_stats(self, event_store):
        """Test getting event store statistics."""
        await event_store.initialize()

        # Append some events
        for i in range(5):
            event = DomainEvent.create(
                event_type="agent.state.changed",
                aggregate_id="agent-1",
                aggregate_type="Agent",
                payload={"state": f"state_{i}"},
            )
            await event_store.append(event)

        stats = await event_store.get_stats()

        assert "events_appended" in stats
        assert "events_replayed" in stats
        assert "snapshots_created" in stats
        assert stats["events_appended"] == 5


class TestCreateEventApplier:
    """Test create_event_applier helper function."""

    def test_create_simple_applier(self):
        """Test creating a simple event applier."""
        applier = create_event_applier("state", "new_state")

        state = {"initial": "value"}
        event = DomainEvent.create(
            event_type="test.event",
            aggregate_id="test-1",
            aggregate_type="Test",
            payload={"new_state": "updated"},
        )

        result = applier(state, event)

        assert result["state"] == "updated"
        assert result["initial"] == "value"


class TestEventStoreIntegration:
    """Integration tests for event store."""

    @pytest.mark.asyncio
    async def test_full_event_sourcing_flow(self):
        """Test complete event sourcing flow."""
        store = EventStore(snapshot_interval=5, zero_trust_enabled=False)
        await store.initialize()

        # Define state applier
        def applier(state, event):
            if event.event_type == "agent.created":
                state["created"] = True
                state["config"] = event.payload.get("config", {})
            elif event.event_type == "agent.state.changed":
                state["state"] = event.payload.get("new_state")
            elif event.event_type == "agent.config.updated":
                state["config"].update(event.payload.get("updates", {}))
            return state

        # Event 1: Agent created
        event1 = DomainEvent.create(
            event_type="agent.created",
            aggregate_id="agent-1",
            aggregate_type="Agent",
            payload={"config": {"key": "value"}},
            version=1,
        )
        await store.append(event1)

        # Event 2: State changed
        event2 = DomainEvent.create(
            event_type="agent.state.changed",
            aggregate_id="agent-1",
            aggregate_type="Agent",
            payload={"new_state": "running"},
            version=2,
        )
        await store.append(event2)

        # Event 3: Config updated
        event3 = DomainEvent.create(
            event_type="agent.config.updated",
            aggregate_id="agent-1",
            aggregate_type="Agent",
            payload={"updates": {"key2": "value2"}},
            version=3,
        )
        await store.append(event3)

        # Reconstruct state
        state = await store.reconstruct_state("agent-1", applier, initial_state={})

        assert state["created"] is True
        assert state["state"] == "running"
        assert state["config"] == {"key": "value", "key2": "value2"}

        # Get event history
        events = await store.get_events("agent-1")

        assert len(events) == 3
        assert events[0].event_type == "agent.created"
        assert events[1].event_type == "agent.state.changed"
        assert events[2].event_type == "agent.config.updated"


class TestSingletonFunctions:
    """Test module singleton functions."""

    def test_get_event_store(self):
        """Test getting the event store singleton."""
        store1 = get_event_store()
        store2 = get_event_store()

        # Should return same instance
        assert store1 is store2

    @pytest.mark.asyncio
    async def test_setup_event_store(self):
        """Test setup_event_store function."""
        with patch('heretek_swarm.state.event_store._store', None):
            store = await setup_event_store(
                db_pool=None,
                snapshot_interval=50,
            )

            assert store is not None
            assert store._snapshot_interval == 50
            assert store._initialized is True
