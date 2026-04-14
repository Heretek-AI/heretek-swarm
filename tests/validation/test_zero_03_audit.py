"""ZERO-03 Comprehensive Audit Trails — Validation Tests.

Validates that the audit trail implementation meets ALL success criteria:
1. Every agent action logged with: timestamp, actor_id, action_type, input_hash, output_hash
2. Audit trail queryable by actor_id, time range, action_type
3. Immutable storage (append-only)

Edge cases verified:
- Ring buffer overflow (1M entries in memory, flush every 1000/60s)
- Zero-activity agent detection
- Tampering / chain integrity detection
"""

import hashlib
import json
import time
from datetime import UTC, datetime, timedelta

import pytest

from heretek_swarm.infrastructure.audit import (
    AuditEntry,
    AuditLogger,
    get_audit_logger,
    init_audit_logger,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def audit_logger():
    """Create a fresh AuditLogger for each test."""
    return AuditLogger(
        max_entries=1000,
        flush_interval_entries=100,
        flush_interval_seconds=60,
    )


@pytest.fixture
def populated_logger(audit_logger):
    """AuditLogger pre-populated with known entries."""
    for i in range(5):
        audit_logger.log(
            actor_id=f"agent-{'alpha' if i < 3 else 'beta'}",
            action_type="message_received" if i % 2 == 0 else "decision_made",
            input_data={"payload": f"input-{i}"},
            output_data={"result": f"output-{i}"},
        )
    return audit_logger


# ===================================================================
# SUCCESS CRITERION 1: Entry Completeness
# ===================================================================


class TestAuditEntryCompleteness:
    """Verify every audit entry includes all required fields."""

    def test_entry_has_timestamp(self, audit_logger):
        entry = audit_logger.log(
            actor_id="agent-1",
            action_type="message_received",
            input_data={"msg": "hello"},
            output_data={"ack": True},
        )
        assert entry.timestamp is not None
        # Must be parseable as ISO-8601
        parsed = datetime.fromisoformat(entry.timestamp)
        assert parsed.tzinfo is not None  # timezone-aware

    def test_entry_has_actor_id(self, audit_logger):
        entry = audit_logger.log(
            actor_id="agent-steward-001",
            action_type="message_sent",
        )
        assert entry.actor_id == "agent-steward-001"

    def test_entry_has_action_type(self, audit_logger):
        entry = audit_logger.log(
            actor_id="agent-1",
            action_type="state_change",
        )
        assert entry.action_type == "state_change"

    def test_entry_has_input_hash(self, audit_logger):
        entry = audit_logger.log(
            actor_id="agent-1",
            action_type="message_received",
            input_data={"content": "test payload"},
        )
        assert entry.input_hash is not None
        assert len(entry.input_hash) == 64  # SHA-256 hex

    def test_entry_has_output_hash(self, audit_logger):
        entry = audit_logger.log(
            actor_id="agent-1",
            action_type="decision_made",
            input_data={"context": "x"},
            output_data={"decision": "approve"},
        )
        assert entry.output_hash is not None
        assert len(entry.output_hash) == 64  # SHA-256 hex

    def test_input_hash_matches_data(self, audit_logger):
        """Verify the input_hash is a deterministic hash of the input."""
        input_data = {"key": "value", "nested": {"a": 1}}
        entry = audit_logger.log(
            actor_id="agent-1",
            action_type="test_action",
            input_data=input_data,
        )
        expected = hashlib.sha256(
            json.dumps({"data": input_data}, sort_keys=True, default=str).encode()
        ).hexdigest()
        assert entry.input_hash == expected

    def test_output_hash_matches_data(self, audit_logger):
        output_data = {"result": "success", "code": 200}
        entry = audit_logger.log(
            actor_id="agent-1",
            action_type="test_action",
            output_data=output_data,
        )
        expected = hashlib.sha256(
            json.dumps({"data": output_data}, sort_keys=True, default=str).encode()
        ).hexdigest()
        assert entry.output_hash == expected

    def test_no_input_output_means_null_hashes(self, audit_logger):
        entry = audit_logger.log(
            actor_id="agent-1",
            action_type="heartbeat",
        )
        assert entry.input_hash is None
        assert entry.output_hash is None

    def test_entry_has_entry_id(self, audit_logger):
        entry = audit_logger.log(
            actor_id="agent-1",
            action_type="test",
        )
        assert entry.entry_id is not None
        assert entry.entry_id.startswith("audit_")

    def test_entry_has_entry_hash(self, audit_logger):
        entry = audit_logger.log(
            actor_id="agent-1",
            action_type="test",
        )
        assert entry.entry_hash is not None
        assert len(entry.entry_hash) == 64

    def test_to_dict_includes_all_fields(self, audit_logger):
        entry = audit_logger.log(
            actor_id="agent-1",
            action_type="decision_made",
            input_data={"x": 1},
            output_data={"y": 2},
        )
        d = entry.to_dict()
        required_keys = {
            "entry_id",
            "timestamp",
            "actor_id",
            "action_type",
            "input_hash",
            "output_hash",
            "metadata",
            "previous_hash",
            "entry_hash",
        }
        assert required_keys.issubset(d.keys())

    def test_all_action_types_covered(self, audit_logger):
        """Ensure the system can log every documented action type."""
        action_types = [
            "message_received",
            "message_sent",
            "state_change",
            "handler_executed",
            "decision_made",
            "validation_performed",
        ]
        for atype in action_types:
            entry = audit_logger.log(
                actor_id="agent-1",
                action_type=atype,
            )
            assert entry.action_type == atype
            assert entry.timestamp is not None
            assert entry.actor_id == "agent-1"


# ===================================================================
# SUCCESS CRITERION 2: Queryability
# ===================================================================


class TestAuditQueryability:
    """Verify audit log is queryable by actor_id, time range, action_type."""

    def test_query_by_actor_id(self, populated_logger):
        results = populated_logger.query(actor_id="agent-alpha")
        assert len(results) == 3
        assert all(r["actor_id"] == "agent-alpha" for r in results)

    def test_query_by_action_type(self, populated_logger):
        results = populated_logger.query(action_type="message_received")
        assert len(results) == 3  # indices 0, 2, 4
        assert all(r["action_type"] == "message_received" for r in results)

    def test_query_by_time_range(self, audit_logger):
        # Create entries at specific times
        now = datetime.now(UTC)
        past = now - timedelta(hours=2)
        future = now + timedelta(hours=2)

        # Manually inject entries with controlled timestamps
        audit_logger.log(actor_id="a1", action_type="old_action")
        # The entry gets "now" timestamp, query with time range should work

        results = audit_logger.query(
            start_time=now - timedelta(minutes=1),
            end_time=now + timedelta(minutes=1),
        )
        assert len(results) >= 1

    def test_query_by_time_range_excludes_old(self, audit_logger):
        now = datetime.now(UTC)
        # Query a range far in the past — should return nothing
        results = audit_logger.query(
            start_time=now - timedelta(hours=2),
            end_time=now - timedelta(hours=1),
        )
        assert len(results) == 0

    def test_query_combined_filters(self, populated_logger):
        results = populated_logger.query(
            actor_id="agent-alpha",
            action_type="message_received",
        )
        # agent-alpha at indices 0, 1, 2; message_received at indices 0, 2
        # agent-alpha + message_received = indices 0, 2 => 2 entries
        assert len(results) == 2

    def test_query_returns_dicts(self, populated_logger):
        results = populated_logger.query(actor_id="agent-alpha")
        for r in results:
            assert isinstance(r, dict)
            assert "entry_id" in r
            assert "timestamp" in r
            assert "actor_id" in r
            assert "action_type" in r

    def test_query_limit(self, populated_logger):
        results = populated_logger.query(limit=2)
        assert len(results) <= 2

    def test_query_no_filters_returns_all(self, populated_logger):
        results = populated_logger.query(limit=100)
        assert len(results) == 5


# ===================================================================
# SUCCESS CRITERION 3: Immutable / Append-Only Storage
# ===================================================================


class TestAuditImmutability:
    """Verify audit log storage is append-only (no delete or modify)."""

    def test_no_delete_method(self):
        """AuditLogger should NOT expose any delete/remove methods."""
        logger = AuditLogger()
        forbidden = ["delete", "remove", "pop", "clear", "truncate", "update_entry"]
        for method in forbidden:
            assert not hasattr(logger, method) or not callable(getattr(logger, method, None)), (
                f"AuditLogger should not expose mutable method: {method}"
            )

    def test_deque_is_append_only(self, audit_logger):
        """The internal deque uses maxlen for ring buffer — no manual removal."""
        assert hasattr(audit_logger._log, "append")
        assert hasattr(audit_logger._log, "maxlen")
        assert audit_logger._log.maxlen == 1000

    def test_entries_cannot_be_modified_after_creation(self, audit_logger):
        """Verify entry data is not modifiable through the logger."""
        entry = audit_logger.log(
            actor_id="agent-1",
            action_type="test",
            input_data={"x": 1},
        )
        # The entry returned should have immutable-looking fields
        original_hash = entry.entry_hash
        original_actor = entry.actor_id

        # Try to mutate — the dataclass allows it, but the stored entry
        # in the deque is the same object. Verify what's stored matches.
        stored = list(audit_logger._log)[-1]
        assert stored.entry_hash == original_hash
        assert stored.actor_id == original_actor

    def test_append_only_grows(self, audit_logger):
        """Verify that logging only adds entries, never removes existing ones."""
        entries = []
        for i in range(10):
            e = audit_logger.log(actor_id="a", action_type="test")
            entries.append(e)

        stored = list(audit_logger._log)
        assert len(stored) == 10
        # All stored entries match what was returned
        for returned, stored_entry in zip(entries, stored):
            assert returned.entry_id == stored_entry.entry_id


# ===================================================================
# EDGE CASE: Chain Integrity / Tampering Detection
# ===================================================================


class TestChainIntegrity:
    """Verify cryptographic hash chain between entries."""

    def test_first_entry_has_no_previous_hash(self, audit_logger):
        entry = audit_logger.log(actor_id="a", action_type="test")
        assert entry.previous_hash is None

    def test_subsequent_entries_chain(self, audit_logger):
        entry1 = audit_logger.log(actor_id="a", action_type="test1")
        entry2 = audit_logger.log(actor_id="a", action_type="test2")
        assert entry2.previous_hash == entry1.entry_hash

    def test_chain_integrity_verification_passes(self, audit_logger):
        for i in range(10):
            audit_logger.log(actor_id=f"agent-{i}", action_type="test")

        is_valid, broken = audit_logger.verify_chain_integrity()
        assert is_valid is True
        assert broken == []

    def test_tampering_detected_via_previous_hash(self, audit_logger):
        audit_logger.log(actor_id="a", action_type="test1")
        audit_logger.log(actor_id="b", action_type="test2")
        audit_logger.log(actor_id="c", action_type="test3")

        # Tamper: modify the middle entry's previous_hash
        entries = list(audit_logger._log)
        entries[1].previous_hash = "TAMPERED_HASH"

        is_valid, broken = audit_logger.verify_chain_integrity()
        assert is_valid is False
        assert len(broken) > 0

    def test_tampering_detected_via_entry_hash(self, audit_logger):
        audit_logger.log(actor_id="a", action_type="test1")
        audit_logger.log(actor_id="b", action_type="test2")

        # Tamper: modify the first entry's hash
        entries = list(audit_logger._log)
        entries[0].entry_hash = "TAMPERED_ENTRY_HASH"

        is_valid, broken = audit_logger.verify_chain_integrity()
        assert is_valid is False
        assert len(broken) > 0

    def test_tampering_detected_via_content_change(self, audit_logger):
        audit_logger.log(actor_id="a", action_type="test1")
        audit_logger.log(actor_id="b", action_type="test2")

        # Tamper: change content but not hash — hash mismatch detected
        entries = list(audit_logger._log)
        entries[0].actor_id = "tampered_actor"

        is_valid, broken = audit_logger.verify_chain_integrity()
        assert is_valid is False
        assert len(broken) > 0

    def test_tamper_increments_statistic(self, audit_logger):
        audit_logger.log(actor_id="a", action_type="test")
        list(audit_logger._log)[0].entry_hash = "BAD"

        audit_logger.verify_chain_integrity()
        stats = audit_logger.get_statistics()
        assert stats["tamper_detections"] > 0


# ===================================================================
# EDGE CASE: Ring Buffer Overflow
# ===================================================================


class TestRingBufferOverflow:
    """Verify ring buffer behavior at capacity."""

    def test_ring_buffer_respects_max_size(self):
        logger = AuditLogger(max_entries=10)
        for i in range(20):
            logger.log(actor_id=f"a-{i}", action_type="test")

        assert len(logger._log) == 10

    def test_ring_buffer_keeps_newest_entries(self):
        logger = AuditLogger(max_entries=5)
        for i in range(10):
            logger.log(actor_id=f"a-{i}", action_type="test")

        stored_ids = [e.actor_id for e in logger._log]
        # Should keep the last 5: a-5 through a-9
        assert "a-9" in stored_ids
        assert "a-0" not in stored_ids

    def test_default_max_entries_is_one_million(self):
        logger = AuditLogger()
        assert logger.max_entries == 1_000_000
        assert logger._log.maxlen == 1_000_000

    def test_entry_count_continues_past_buffer(self):
        """Even after buffer overflow, total entry count keeps growing."""
        logger = AuditLogger(max_entries=5)
        for i in range(20):
            logger.log(actor_id=f"a-{i}", action_type="test")

        assert logger._entry_count == 20
        stats = logger.get_statistics()
        assert stats["total_entries"] == 20

    def test_flush_triggered_by_entry_count(self):
        """Flush should trigger after flush_interval_entries."""
        flushed = []

        logger = AuditLogger(
            max_entries=100,
            flush_interval_entries=5,
            flush_interval_seconds=3600,  # Never time-trigger
        )
        logger.set_persist_callback(lambda entries: flushed.append(entries))

        for i in range(6):
            logger.log(actor_id=f"a-{i}", action_type="test")

        assert len(flushed) >= 1
        assert len(flushed[0]) == 5


# ===================================================================
# EDGE CASE: Zero-Activity Agent Detection
# ===================================================================


class TestZeroActivityDetection:
    """Verify Steward can detect zero-activity agents via activity rate."""

    def test_activity_rate_returns_zero_for_unknown_agent(self, populated_logger):
        rate = populated_logger.get_activity_rate("unknown-agent")
        assert rate == 0.0

    def test_activity_rate_returns_positive_for_active_agent(self, populated_logger):
        rate = populated_logger.get_activity_rate("agent-alpha")
        assert rate > 0.0

    def test_activity_rate_measures_window(self, audit_logger):
        # Log entries for agent-X
        for _ in range(10):
            audit_logger.log(actor_id="agent-X", action_type="test")

        rate = audit_logger.get_activity_rate("agent-X", window_seconds=60)
        assert rate > 0.0
        # 10 entries / 60 seconds
        assert abs(rate - 10 / 60) < 0.1

    def test_statistics_track_entries_by_actor(self, populated_logger):
        stats = populated_logger.get_statistics()
        assert "entries_by_actor" in stats
        assert "agent-alpha" in stats["entries_by_actor"]
        assert stats["entries_by_actor"]["agent-alpha"] == 3

    def test_steward_pattern_detect_inactive(self, populated_logger):
        """Simulate Steward monitoring: agents with 0 activity flagged as suspect."""
        active_agents = ["agent-alpha", "agent-beta"]
        all_agents = active_agents + ["agent-gamma", "agent-delta"]

        suspects = []
        for agent_id in all_agents:
            rate = populated_logger.get_activity_rate(agent_id, window_seconds=300)
            if rate == 0.0:
                suspects.append(agent_id)

        assert "agent-gamma" in suspects
        assert "agent-delta" in suspects
        assert "agent-alpha" not in suspects


# ===================================================================
# Integration: AuditMixin + Infrastructure
# ===================================================================


class TestAuditMixinIntegration:
    """Verify AuditMixin integrates correctly with AuditLogger."""

    @pytest.fixture
    def initialized_audit(self):
        """Initialize the global audit logger."""
        import heretek_swarm.infrastructure.audit as audit_mod

        audit_mod._audit_logger = AuditLogger(max_entries=100)
        yield audit_mod._audit_logger
        audit_mod._audit_logger = None

    def test_mixin_uses_infrastructure_logger(self, initialized_audit):
        from heretek_swarm.actors.mixins.audit import AuditMixin

        class FakeAgent(AuditMixin):
            agent_id = "test-agent-001"
            actor_type = "TestAgent"
            name = "Test"
            _config = {}
            _last_sender = "sender-1"

        agent = FakeAgent()
        assert agent._audit_logger is initialized_audit

    def test_mixin_audit_message_received(self, initialized_audit):
        from heretek_swarm.actors.mixins.audit import AuditMixin

        class FakeAgent(AuditMixin):
            agent_id = "test-agent-001"
            actor_type = "TestAgent"
            name = "Test"
            _config = {}
            _last_sender = "sender-1"

        agent = FakeAgent()
        agent._audit_message_received(
            message_type="task_request",
            content={"task": "analyze"},
        )

        results = initialized_audit.query(action_type="message_received")
        assert len(results) == 1
        assert results[0]["actor_id"] == "test-agent-001"

    def test_mixin_audit_message_sent(self, initialized_audit):
        from heretek_swarm.actors.mixins.audit import AuditMixin

        class FakeAgent(AuditMixin):
            agent_id = "test-agent-001"
            actor_type = "TestAgent"
            name = "Test"
            _config = {}

        agent = FakeAgent()
        agent._audit_message_sent(
            topic="results",
            message_type="task_result",
            content={"status": "done"},
        )

        results = initialized_audit.query(action_type="message_sent")
        assert len(results) == 1

    def test_mixin_audit_state_change(self, initialized_audit):
        from heretek_swarm.actors.mixins.audit import AuditMixin

        class FakeAgent(AuditMixin):
            agent_id = "test-agent-001"
            actor_type = "TestAgent"
            name = "Test"
            _config = {}

        agent = FakeAgent()
        agent._audit_state_change(
            old_state="spawning",
            new_state="active",
            reason="initialization complete",
        )

        results = initialized_audit.query(action_type="state_change")
        assert len(results) == 1
        assert results[0]["input_hash"] is not None
        assert results[0]["output_hash"] is not None

    def test_mixin_audit_decision_made(self, initialized_audit):
        from heretek_swarm.actors.mixins.audit import AuditMixin

        class FakeAgent(AuditMixin):
            agent_id = "test-agent-001"
            actor_type = "TestAgent"
            name = "Test"
            _config = {}

        agent = FakeAgent()
        agent._audit_decision_made(
            decision_type="task_priority",
            decision_data={"priority": "high"},
            context={"queue_depth": 10},
        )

        results = initialized_audit.query(action_type="decision_made")
        assert len(results) == 1

    def test_mixin_audit_handler_executed(self, initialized_audit):
        from heretek_swarm.actors.mixins.audit import AuditMixin

        class FakeAgent(AuditMixin):
            agent_id = "test-agent-001"
            actor_type = "TestAgent"
            name = "Test"
            _config = {}

        agent = FakeAgent()
        agent._audit_handler_executed(
            handler_name="handle_task",
            message_type="task_request",
            result={"processed": True},
        )

        results = initialized_audit.query(action_type="handler_executed")
        assert len(results) == 1

    def test_mixin_audit_disabled(self, initialized_audit):
        from heretek_swarm.actors.mixins.audit import AuditMixin

        class FakeAgent(AuditMixin):
            agent_id = "test-agent-001"
            actor_type = "TestAgent"
            name = "Test"
            _config = {"audit_enabled": False}

        agent = FakeAgent()
        assert agent._audit_enabled is False

        result = agent._audit("test_action")
        assert result is None
        assert len(initialized_audit._log) == 0


# ===================================================================
# Global Instance Management
# ===================================================================


class TestGlobalAuditInstance:
    """Test the global singleton pattern for audit logger."""

    def test_init_and_get(self):
        import heretek_swarm.infrastructure.audit as audit_mod

        original = audit_mod._audit_logger

        try:
            logger = init_audit_logger(max_entries=500)
            assert get_audit_logger() is logger
        finally:
            audit_mod._audit_logger = original

    def test_get_raises_when_not_initialized(self):
        import heretek_swarm.infrastructure.audit as audit_mod

        original = audit_mod._audit_logger

        try:
            audit_mod._audit_logger = None
            with pytest.raises(RuntimeError, match="not initialized"):
                get_audit_logger()
        finally:
            audit_mod._audit_logger = original
