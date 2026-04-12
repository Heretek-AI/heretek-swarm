"""
Tests for JetStream Manager.

Tests cover:
- Stream configuration and lifecycle management
- Consumer management with durable subscriptions
- Message retention policies
- Stream monitoring and statistics
- Fallback to in-memory storage
"""

from datetime import UTC, datetime
from unittest.mock import patch

import pytest

from heretek_swarm.gateway.jetstream_manager import (
    AckPolicy,
    ConsumerConfig,
    DeliverPolicy,
    JetStreamConfig,
    JetStreamManager,
    RetentionPolicy,
    StorageType,
    get_jetstream_manager,
    setup_jetstream,
)


class TestJetStreamConfig:
    """Test JetStream configuration model."""

    def test_create_config(self):
        """Test creating a JetStream configuration."""
        config = JetStreamConfig(
            stream_name="TEST_STREAM",
            subjects=["test.*", "events.>"],
            retention=RetentionPolicy.LIMITS,
            max_messages=10000,
            max_age="24h",
            storage=StorageType.MEMORY,
            replicas=1,
            max_bytes=1048576,
        )

        assert config.stream_name == "TEST_STREAM"
        assert config.subjects == ["test.*", "events.>"]
        assert config.retention == RetentionPolicy.LIMITS
        assert config.max_messages == 10000
        assert config.max_age == "24h"
        assert config.storage == StorageType.MEMORY
        assert config.replicas == 1
        assert config.max_bytes == 1048576

    def test_config_to_dict(self):
        """Test configuration serialization."""
        config = JetStreamConfig(
            stream_name="TEST_STREAM",
            subjects=["test.*"],
            retention=RetentionPolicy.LIMITS,
        )

        data = config.to_dict()

        assert data["stream_name"] == "TEST_STREAM"
        assert data["subjects"] == ["test.*"]
        assert data["retention"] == "limits"
        assert data["storage"] == "file"
        assert data["max_messages"] == 1000000

    def test_config_from_dict(self):
        """Test configuration deserialization."""
        data = {
            "stream_name": "TEST_STREAM",
            "subjects": ["test.*"],
            "retention": "limits",
            "max_messages": 5000,
            "max_age": "48h",
            "storage": "memory",
            "replicas": 3,
            "max_bytes": 2097152,
        }

        config = JetStreamConfig.from_dict(data)

        assert config.stream_name == "TEST_STREAM"
        assert config.max_messages == 5000
        assert config.max_age == "48h"
        assert config.storage == StorageType.MEMORY
        assert config.replicas == 3


class TestConsumerConfig:
    """Test consumer configuration model."""

    def test_create_consumer_config(self):
        """Test creating a consumer configuration."""
        config = ConsumerConfig(
            durable_name="test-consumer",
            stream_name="TEST_STREAM",
            deliver_policy=DeliverPolicy.NEW,
            ack_policy=AckPolicy.EXPLICIT,
            max_deliver=50,
            ack_wait=60.0,
            filter_subject="test.*",
        )

        assert config.durable_name == "test-consumer"
        assert config.stream_name == "TEST_STREAM"
        assert config.deliver_policy == DeliverPolicy.NEW
        assert config.ack_policy == AckPolicy.EXPLICIT
        assert config.max_deliver == 50
        assert config.ack_wait == 60.0
        assert config.filter_subject == "test.*"

    def test_consumer_config_to_dict(self):
        """Test consumer configuration serialization."""
        config = ConsumerConfig(
            durable_name="test-consumer",
            stream_name="TEST_STREAM",
        )

        data = config.to_dict()

        assert data["durable_name"] == "test-consumer"
        assert data["stream_name"] == "TEST_STREAM"
        assert data["deliver_policy"] == "all"
        assert data["ack_policy"] == "explicit"


class TestJetStreamManager:
    """Test JetStream manager functionality."""

    @pytest.fixture
    def manager(self):
        """Create a JetStream manager instance."""
        return JetStreamManager(
            servers=["nats://localhost:4222"],
            fallback_enabled=True,
            zero_trust_enabled=False,
        )

    @pytest.mark.asyncio
    async def test_initialize(self, manager):
        """Test manager initialization."""
        result = await manager.connect()

        assert result is True
        # In fallback mode, _connected is True but is_connected checks for _js
        assert manager._connected is True
        assert manager.is_fallback_mode is True  # Fallback enabled

    @pytest.mark.asyncio
    async def test_create_stream(self, manager):
        """Test creating a stream."""
        await manager.connect()

        config = JetStreamConfig(
            stream_name="TEST_STREAM",
            subjects=["test.*"],
            retention=RetentionPolicy.LIMITS,
            max_messages=1000,
            max_age="24h",
        )

        result = await manager.create_stream(config)

        assert result is True
        assert "TEST_STREAM" in manager.stream_names

    @pytest.mark.asyncio
    async def test_delete_stream(self, manager):
        """Test deleting a stream."""
        await manager.connect()

        config = JetStreamConfig(
            stream_name="TEST_STREAM_DELETE",
            subjects=["test.delete.*"],
        )

        # Create stream
        await manager.create_stream(config)
        assert "TEST_STREAM_DELETE" in manager.stream_names

        # Delete stream
        result = await manager.delete_stream("TEST_STREAM_DELETE")

        assert result is True
        assert "TEST_STREAM_DELETE" not in manager.stream_names

    @pytest.mark.asyncio
    async def test_get_stream_info(self, manager):
        """Test getting stream information."""
        await manager.connect()

        config = JetStreamConfig(
            stream_name="TEST_STREAM_INFO",
            subjects=["test.info.*"],
        )

        await manager.create_stream(config)
        info = await manager.get_stream_info("TEST_STREAM_INFO")

        assert info is not None
        assert info.name == "TEST_STREAM_INFO"
        assert info.config.subjects == ["test.info.*"]

    @pytest.mark.asyncio
    async def test_list_streams(self, manager):
        """Test listing all streams."""
        await manager.connect()

        # Create multiple streams
        configs = [
            JetStreamConfig(stream_name="STREAM_1", subjects=["s1.*"]),
            JetStreamConfig(stream_name="STREAM_2", subjects=["s2.*"]),
            JetStreamConfig(stream_name="STREAM_3", subjects=["s3.*"]),
        ]

        for config in configs:
            await manager.create_stream(config)

        streams = await manager.list_streams()

        assert len(streams) >= 3
        names = [s.name for s in streams]
        assert "STREAM_1" in names
        assert "STREAM_2" in names
        assert "STREAM_3" in names

    @pytest.mark.asyncio
    async def test_publish_message(self, manager):
        """Test publishing a message to a stream."""
        await manager.connect()

        config = JetStreamConfig(
            stream_name="TEST_PUBLISH",
            subjects=["test.publish.*"],
        )

        await manager.create_stream(config)

        result = await manager.publish(
            stream_name="TEST_PUBLISH",
            subject="test.publish.event",
            data={"message": "test"},
        )

        assert result is True

    @pytest.mark.asyncio
    async def test_publish_to_nonexistent_stream(self, manager):
        """Test publishing to a stream that doesn't exist."""
        await manager.connect()

        result = await manager.publish(
            stream_name="NONEXISTENT_STREAM",
            subject="test.event",
            data={"message": "test"},
        )

        assert result is False

    @pytest.mark.asyncio
    async def test_replay_messages(self, manager):
        """Test replaying messages from a stream."""
        await manager.connect()

        config = JetStreamConfig(
            stream_name="TEST_REPLAY",
            subjects=["test.replay.*"],
        )

        await manager.create_stream(config)

        # Publish messages
        for i in range(5):
            await manager.publish(
                stream_name="TEST_REPLAY",
                subject="test.replay.event",
                data={"index": i},
            )

        # Replay messages
        received = []

        def callback(subject, data):
            received.append((subject, data))

        messages = await manager.replay_messages(
            stream_name="TEST_REPLAY",
            callback=callback,
        )

        assert len(messages) == 5

    @pytest.mark.asyncio
    async def test_replay_with_sequence_filter(self, manager):
        """Test replaying messages with sequence filter."""
        await manager.connect()

        config = JetStreamConfig(
            stream_name="TEST_REPLAY_SEQ",
            subjects=["test.replay.seq.*"],
        )

        await manager.create_stream(config)

        # Publish messages
        for i in range(10):
            await manager.publish(
                stream_name="TEST_REPLAY_SEQ",
                subject="test.replay.seq.event",
                data={"index": i},
            )

        # Replay with sequence range
        messages = await manager.replay_messages(
            stream_name="TEST_REPLAY_SEQ",
            start_sequence=3,
            end_sequence=7,
        )

        assert len(messages) == 5  # Messages 3, 4, 5, 6, 7

    @pytest.mark.asyncio
    async def test_replay_with_subject_filter(self, manager):
        """Test replaying messages with subject filter."""
        await manager.connect()

        config = JetStreamConfig(
            stream_name="TEST_REPLAY_SUBJ",
            subjects=["test.replay.subj.*"],
        )

        await manager.create_stream(config)

        # Publish messages with different subjects
        for i in range(5):
            subject = "test.replay.subj.typeA" if i % 2 == 0 else "test.replay.subj.typeB"
            await manager.publish(
                stream_name="TEST_REPLAY_SUBJ",
                subject=subject,
                data={"index": i, "type": "A" if i % 2 == 0 else "B"},
            )

        # Replay with subject filter
        messages = await manager.replay_messages(
            stream_name="TEST_REPLAY_SUBJ",
            subject_filter="*.typeA",
        )

        assert len(messages) == 3  # Only typeA messages

    @pytest.mark.asyncio
    async def test_create_consumer(self, manager):
        """Test creating a durable consumer."""
        await manager.connect()

        config = JetStreamConfig(
            stream_name="TEST_CONSUMER",
            subjects=["test.consumer.*"],
        )

        await manager.create_stream(config)

        received = []

        async def callback(subject, data):
            received.append((subject, data))

        consumer_config = ConsumerConfig(
            durable_name="test-durable-consumer",
            stream_name="TEST_CONSUMER",
            deliver_policy=DeliverPolicy.NEW,
        )

        consumer_id = await manager.create_consumer(consumer_config, callback)

        assert consumer_id is not None
        assert "TEST_CONSUMER_test-durable-consumer" in consumer_id

    @pytest.mark.asyncio
    async def test_get_stats(self, manager):
        """Test getting manager statistics."""
        await manager.connect()

        config = JetStreamConfig(
            stream_name="TEST_STATS",
            subjects=["test.stats.*"],
        )

        await manager.create_stream(config)
        await manager.publish(
            stream_name="TEST_STATS",
            subject="test.stats.event",
            data={"test": "data"},
        )

        stats = await manager.get_stats()

        assert "streams_created" in stats
        assert "messages_published" in stats
        assert stats["streams_created"] >= 1
        assert stats["messages_published"] >= 1
        assert stats["connected"] is True
        assert stats["fallback_mode"] is True

    @pytest.mark.asyncio
    async def test_initialize_default_streams(self, manager):
        """Test initializing default streams."""
        await manager.connect()

        results = await manager.initialize_default_streams()

        assert "AGENT_EVENTS" in results
        assert "WORKFLOW_EVENTS" in results
        assert "CONSCIOUSNESS_METRICS" in results
        assert "SYSTEM_HEALTH" in results

        # Check streams were created
        streams = await manager.list_streams()
        names = [s.name for s in streams]

        assert "AGENT_EVENTS" in names
        assert "WORKFLOW_EVENTS" in names
        assert "CONSCIOUSNESS_METRICS" in names
        assert "SYSTEM_HEALTH" in names


class TestJetStreamManagerIntegration:
    """Integration tests for JetStream manager."""

    @pytest.mark.asyncio
    async def test_full_event_flow(self):
        """Test complete event flow: create stream, publish, replay."""
        manager = JetStreamManager(fallback_enabled=True, zero_trust_enabled=False)
        await manager.connect()

        # Create stream
        config = JetStreamConfig(
            stream_name="INTEGRATION_TEST",
            subjects=["integration.*"],
            max_messages=1000,
        )
        created = await manager.create_stream(config)
        assert created is True

        # Publish events
        for i in range(10):
            await manager.publish(
                stream_name="INTEGRATION_TEST",
                subject=f"integration.event.{i}",
                data={"event_id": i, "timestamp": datetime.now(UTC).isoformat()},
            )

        # Get stream info (in fallback mode, state is tracked differently)
        info = await manager.get_stream_info("INTEGRATION_TEST")
        assert info is not None
        # Fallback mode doesn't track message count the same way
        assert info.name == "INTEGRATION_TEST"

        # Replay events
        messages = await manager.replay_messages(
            stream_name="INTEGRATION_TEST",
            subject_filter="integration.*",
        )

        # In fallback mode, messages are stored
        assert len(messages) == 10

        # Cleanup
        await manager.delete_stream("INTEGRATION_TEST")
        await manager.disconnect()


class TestSingletonFunctions:
    """Test module singleton functions."""

    def test_get_jetstream_manager(self):
        """Test getting the JetStream manager singleton."""
        manager1 = get_jetstream_manager()
        manager2 = get_jetstream_manager()

        # Should return same instance
        assert manager1 is manager2

    @pytest.mark.asyncio
    async def test_setup_jetstream(self):
        """Test setup_jetstream function."""
        with patch("heretek_swarm.gateway.jetstream_manager._manager", None):
            manager = await setup_jetstream(
                servers=["nats://localhost:4222"],
                create_default_streams=False,
            )

            assert manager is not None
            # In fallback mode, _connected is True
            assert manager._connected is True
