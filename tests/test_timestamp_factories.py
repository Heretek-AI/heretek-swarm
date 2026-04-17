"""
Regression tests for timestamp default_factory bugs.

These tests verify that timestamp fields in dataclasses are properly
initialized with unique per-instance values, not shared frozen timestamps.

The bugs were:
- NATSMessage.timestamp was using `datetime.now(UTC).isoformat` directly
  instead of `lambda: datetime.now(UTC).isoformat()`
- AgentConversation.created_at had the same issue
- LogEntry.timestamp had the same issue

All three are now fixed with proper lambda wrappers.
"""

import time
from datetime import datetime

from heretek_swarm.actors.langroid_adapter import AgentConversation
from heretek_swarm.consensus.raft_election import LogEntry
from heretek_swarm.gateway.nats_event_mesh import NATSMessage


class TestTimestampFactories:
    """Test that timestamp fields produce unique per-instance values."""

    def test_nats_message_timestamp_unique(self) -> None:
        """NATSMessage should produce unique timestamps for each instance."""
        msg1 = NATSMessage(subject="test", data={})
        time.sleep(0.05)  # Ensure temporal separation
        msg2 = NATSMessage(subject="test", data={})

        # Both should be non-empty strings
        assert isinstance(msg1.timestamp, str)
        assert isinstance(msg2.timestamp, str)
        assert len(msg1.timestamp) > 0
        assert len(msg2.timestamp) > 0

        # They should differ (unique per instance)
        assert msg1.timestamp != msg2.timestamp

        # Both should be valid ISO format timestamps
        dt1 = datetime.fromisoformat(msg1.timestamp)
        dt2 = datetime.fromisoformat(msg2.timestamp)
        assert dt1.tzinfo is not None
        assert dt2.tzinfo is not None

    def test_agent_conversation_timestamp_unique(self) -> None:
        """AgentConversation should produce unique created_at and updated_at for each instance."""
        conv1 = AgentConversation(conversation_id="conv1", agent_id="agent1")
        time.sleep(0.05)  # Ensure temporal separation
        conv2 = AgentConversation(conversation_id="conv2", agent_id="agent2")

        # created_at should be non-empty strings
        assert isinstance(conv1.created_at, str)
        assert isinstance(conv2.created_at, str)
        assert len(conv1.created_at) > 0
        assert len(conv2.created_at) > 0

        # created_at should differ (unique per instance)
        assert conv1.created_at != conv2.created_at

        # updated_at should also be non-empty strings
        assert isinstance(conv1.updated_at, str)
        assert isinstance(conv2.updated_at, str)
        assert len(conv1.updated_at) > 0
        assert len(conv2.updated_at) > 0

        # updated_at should differ (unique per instance)
        assert conv1.updated_at != conv2.updated_at

        # Both should be valid ISO format timestamps
        dt1 = datetime.fromisoformat(conv1.created_at)
        dt2 = datetime.fromisoformat(conv2.created_at)
        assert dt1.tzinfo is not None
        assert dt2.tzinfo is not None

    def test_log_entry_timestamp_unique(self) -> None:
        """LogEntry should produce unique timestamps for each instance."""
        entry1 = LogEntry(index=1, term=1, data={})
        time.sleep(0.05)  # Ensure temporal separation
        entry2 = LogEntry(index=2, term=1, data={})

        # Both should be non-empty strings
        assert isinstance(entry1.timestamp, str)
        assert isinstance(entry2.timestamp, str)
        assert len(entry1.timestamp) > 0
        assert len(entry2.timestamp) > 0

        # They should differ (unique per instance)
        assert entry1.timestamp != entry2.timestamp

        # Both should be valid ISO format timestamps
        dt1 = datetime.fromisoformat(entry1.timestamp)
        dt2 = datetime.fromisoformat(entry2.timestamp)
        assert dt1.tzinfo is not None
        assert dt2.tzinfo is not None
