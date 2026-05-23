"""
Tests for ConsensusAuditTrail JSONL fallback (--no-infra mode).

Verifies that audit events are written to a JSONL file when
storage_backend="jsonl", using a background writer thread with
queue.Queue for non-blocking writes.
"""

import json
from pathlib import Path

import pytest


pytestmark = [pytest.mark.integration]

from heretek_swarm.consensus.audit_trail import (
    ConsensusAuditTrail,
)


@pytest.fixture
def tmp_jsonl_path(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Redirect the JSONL file constant to a temp directory."""
    test_path = tmp_path / "consensus_audit.jsonl"
    monkeypatch.setattr(
        "heretek_swarm.consensus.audit_trail._CONSENSUS_AUDIT_FILE",
        test_path,
    )
    return test_path


@pytest.fixture
def jsonl_trail(tmp_jsonl_path: Path) -> ConsensusAuditTrail:
    """Create a ConsensusAuditTrail in jsonl mode with writer started."""
    trail = ConsensusAuditTrail(storage_backend="jsonl")
    trail.initialize()
    yield trail
    trail.cleanup()


# ---------------------------------------------------------------------------
# JSONL file creation
# ---------------------------------------------------------------------------


class TestJSONLFileCreation:
    """Test that the JSONL file is created on first write."""

    def test_file_created_on_first_decision(
        self, jsonl_trail: ConsensusAuditTrail, tmp_jsonl_path: Path
    ) -> None:
        """JSONL file should exist after recording the first decision."""
        jsonl_trail.record_decision(
            decision_id="d1",
            consensus_id="c1",
            proposal="Deploy v2?",
            decision="Yes",
            confidence=0.9,
        )
        # Give the writer thread time to flush
        jsonl_trail._jsonl_queue.join()
        assert tmp_jsonl_path.exists()

    def test_file_created_on_first_vote(
        self, jsonl_trail: ConsensusAuditTrail, tmp_jsonl_path: Path
    ) -> None:
        """JSONL file should exist after recording the first vote."""
        jsonl_trail.record_vote(
            consensus_id="c1",
            agent_id="agent-1",
            decision="Yes",
            confidence=0.85,
        )
        jsonl_trail._jsonl_queue.join()
        assert tmp_jsonl_path.exists()


# ---------------------------------------------------------------------------
# Valid JSON per line
# ---------------------------------------------------------------------------


class TestJSONLLineValidity:
    """Test that each line in the JSONL file is valid JSON."""

    def test_each_line_is_valid_json(
        self, jsonl_trail: ConsensusAuditTrail, tmp_jsonl_path: Path
    ) -> None:
        """Every line in the JSONL file must be independently parseable."""
        for i in range(5):
            jsonl_trail.record_decision(
                decision_id=f"d{i}",
                consensus_id=f"c{i}",
                proposal=f"Proposal {i}",
                decision=f"Decision {i}",
                confidence=0.7 + i * 0.05,
            )
        jsonl_trail._jsonl_queue.join()

        lines = tmp_jsonl_path.read_text(encoding="utf-8").strip().splitlines()
        assert len(lines) == 5
        for i, line in enumerate(lines):
            record = json.loads(line)  # Should not raise
            assert record["decision_id"] == f"d{i}"

    def test_newline_separated_not_pretty_printed(
        self, jsonl_trail: ConsensusAuditTrail, tmp_jsonl_path: Path
    ) -> None:
        """Each record must be on a single line (no embedded newlines in JSON)."""
        jsonl_trail.record_decision(
            decision_id="d1",
            consensus_id="c1",
            proposal="Test",
            decision="Yes",
            confidence=0.9,
            reasoning="Line1\nLine2\nLine3",
        )
        jsonl_trail._jsonl_queue.join()

        lines = tmp_jsonl_path.read_text(encoding="utf-8").strip().splitlines()
        assert len(lines) == 1
        record = json.loads(lines[0])
        # The reasoning field should preserve newlines within the JSON string
        assert "\n" in record["reasoning_summary"]


# ---------------------------------------------------------------------------
# Decision record content
# ---------------------------------------------------------------------------


class TestDecisionRecordJSONL:
    """Test that record_decision produces correct JSONL entries."""

    def test_decision_record_fields(
        self, jsonl_trail: ConsensusAuditTrail, tmp_jsonl_path: Path
    ) -> None:
        """Decision JSONL entry should contain all expected fields."""
        jsonl_trail.record_decision(
            decision_id="deploy-001",
            consensus_id="consensus-abc",
            proposal="Deploy service v2 to production",
            decision="Approved",
            confidence=0.92,
            participants=["agent-1", "agent-2"],
            reasoning="All tests pass, low risk",
            metadata={"priority": "high"},
        )
        jsonl_trail._jsonl_queue.join()

        lines = tmp_jsonl_path.read_text(encoding="utf-8").strip().splitlines()
        assert len(lines) == 1
        record = json.loads(lines[0])

        assert record["record_type"] == "decision"
        assert record["decision_id"] == "deploy-001"
        assert record["consensus_id"] == "consensus-abc"
        assert record["proposal"] == "Deploy service v2 to production"
        assert record["decision"] == "Approved"
        assert record["confidence"] == 0.92
        assert record["participants"] == ["agent-1", "agent-2"]
        assert record["reasoning_summary"] == "All tests pass, low risk"
        assert record["metadata"] == {"priority": "high"}
        assert "timestamp" in record

    def test_decision_with_none_optional_fields(
        self, jsonl_trail: ConsensusAuditTrail, tmp_jsonl_path: Path
    ) -> None:
        """Decision with None optional fields should serialize cleanly."""
        jsonl_trail.record_decision(
            decision_id="d-minimal",
            consensus_id="c-minimal",
            proposal="Minimal",
            decision="Yes",
            confidence=0.5,
        )
        jsonl_trail._jsonl_queue.join()

        lines = tmp_jsonl_path.read_text(encoding="utf-8").strip().splitlines()
        record = json.loads(lines[0])
        assert record["participants"] == []
        assert record["reasoning_summary"] is None
        assert record["metadata"] == {}


# ---------------------------------------------------------------------------
# Vote record content
# ---------------------------------------------------------------------------


class TestVoteRecordJSONL:
    """Test that record_vote produces correct JSONL entries."""

    def test_vote_record_fields(
        self, jsonl_trail: ConsensusAuditTrail, tmp_jsonl_path: Path
    ) -> None:
        """Vote JSONL entry should contain all expected fields."""
        jsonl_trail.record_vote(
            consensus_id="consensus-xyz",
            agent_id="agent-7",
            decision="Approve",
            confidence=0.88,
            reasoning="Solid implementation",
            metadata={"round": 2},
        )
        jsonl_trail._jsonl_queue.join()

        lines = tmp_jsonl_path.read_text(encoding="utf-8").strip().splitlines()
        assert len(lines) == 1
        record = json.loads(lines[0])

        assert record["record_type"] == "vote"
        assert record["vote_id"] == "vote-consensus-xyz-agent-7"
        assert record["consensus_id"] == "consensus-xyz"
        assert record["agent_id"] == "agent-7"
        assert record["decision"] == "Approve"
        assert record["confidence"] == 0.88
        assert record["reasoning"] == "Solid implementation"
        assert record["metadata"] == {"round": 2}
        assert "timestamp" in record

    def test_vote_with_none_reasoning(
        self, jsonl_trail: ConsensusAuditTrail, tmp_jsonl_path: Path
    ) -> None:
        """Vote with None reasoning should serialize as null."""
        jsonl_trail.record_vote(
            consensus_id="c1",
            agent_id="agent-1",
            decision="Yes",
            confidence=0.7,
        )
        jsonl_trail._jsonl_queue.join()

        lines = tmp_jsonl_path.read_text(encoding="utf-8").strip().splitlines()
        record = json.loads(lines[0])
        assert record["reasoning"] is None


# ---------------------------------------------------------------------------
# In-memory storage preserved
# ---------------------------------------------------------------------------


class TestInMemoryPreservation:
    """Test that in-memory storage works alongside JSONL."""

    def test_decisions_still_in_memory(self, jsonl_trail: ConsensusAuditTrail) -> None:
        """In-memory decisions dict should be populated in JSONL mode."""
        jsonl_trail.record_decision(
            decision_id="d1",
            consensus_id="c1",
            proposal="Test",
            decision="Yes",
            confidence=0.9,
        )
        assert "d1" in jsonl_trail.decisions
        assert jsonl_trail.decisions["d1"].decision == "Yes"

    def test_votes_still_in_memory(self, jsonl_trail: ConsensusAuditTrail) -> None:
        """In-memory votes dict should be populated in JSONL mode."""
        jsonl_trail.record_vote(
            consensus_id="c1",
            agent_id="agent-1",
            decision="Yes",
            confidence=0.85,
        )
        assert "c1" in jsonl_trail.votes
        assert len(jsonl_trail.votes["c1"]) == 1

    def test_events_still_in_memory(self, jsonl_trail: ConsensusAuditTrail) -> None:
        """In-memory events list should be populated in JSONL mode."""
        jsonl_trail.record_decision(
            decision_id="d1",
            consensus_id="c1",
            proposal="Test",
            decision="Yes",
            confidence=0.9,
        )
        # record_decision calls record_event twice
        assert len(jsonl_trail.events) == 2


# ---------------------------------------------------------------------------
# Cleanup flushes pending writes
# ---------------------------------------------------------------------------


class TestCleanup:
    """Test that cleanup() flushes pending writes."""

    def test_cleanup_flushes_pending(self, tmp_jsonl_path: Path) -> None:
        """Cleanup should drain the queue before stopping the writer."""
        trail = ConsensusAuditTrail(storage_backend="jsonl")
        trail.initialize()

        # Queue several records
        for i in range(10):
            trail.record_decision(
                decision_id=f"d{i}",
                consensus_id=f"c{i}",
                proposal=f"P{i}",
                decision=f"D{i}",
                confidence=0.5,
            )

        trail.cleanup()

        lines = tmp_jsonl_path.read_text(encoding="utf-8").strip().splitlines()
        assert len(lines) == 10

    def test_cleanup_idempotent(self, jsonl_trail: ConsensusAuditTrail) -> None:
        """Calling cleanup() multiple times should not raise."""
        jsonl_trail.record_decision(
            decision_id="d1",
            consensus_id="c1",
            proposal="Test",
            decision="Yes",
            confidence=0.9,
        )
        jsonl_trail.cleanup()
        jsonl_trail.cleanup()  # Second call should be a no-op


# ---------------------------------------------------------------------------
# Writer handles errors gracefully
# ---------------------------------------------------------------------------


class TestWriterErrorHandling:
    """Test that the writer handles errors without crashing."""

    def test_non_serializable_record_logged(
        self, jsonl_trail: ConsensusAuditTrail, tmp_jsonl_path: Path
    ) -> None:
        """A record with non-serializable fields should be logged, not crash."""
        # Inject a non-serializable object into metadata by calling
        # _record_to_jsonl directly with a bad record
        jsonl_trail._record_to_jsonl(
            {
                "record_type": "test",
                "bad_field": object(),  # Not JSON serializable
            }
        )
        # Wait for the queue to drain
        jsonl_trail._jsonl_queue.join()
        # The writer should log the error but not crash
        assert jsonl_trail._writer_thread is not None
        assert jsonl_trail._writer_thread.is_alive()

    def test_in_memory_mode_no_writer_thread(self) -> None:
        """In-memory mode should not start a writer thread."""
        trail = ConsensusAuditTrail(storage_backend="memory")
        trail.initialize()
        assert trail._writer_thread is None
        trail.record_decision(
            decision_id="d1",
            consensus_id="c1",
            proposal="Test",
            decision="Yes",
            confidence=0.9,
        )
        # Should work fine without JSONL
        assert "d1" in trail.decisions


# ---------------------------------------------------------------------------
# Empty audit trail boundary
# ---------------------------------------------------------------------------


class TestEmptyAuditTrail:
    """Test behavior with no records written."""

    def test_empty_file_after_init_only(self, tmp_jsonl_path: Path) -> None:
        """No file should exist if initialize() is called but nothing recorded."""
        trail = ConsensusAuditTrail(storage_backend="jsonl")
        trail.initialize()
        trail.cleanup()
        # File should not have been created since nothing was queued
        assert not tmp_jsonl_path.exists()

    def test_cleanup_without_initialize(self, tmp_jsonl_path: Path) -> None:
        """cleanup() without initialize() should be a no-op."""
        trail = ConsensusAuditTrail(storage_backend="jsonl")
        trail.cleanup()  # Should not raise


# ---------------------------------------------------------------------------
# Rapid fire writes
# ---------------------------------------------------------------------------


class TestRapidFireWrites:
    """Test that rapid writes are all captured."""

    def test_many_rapid_decisions(
        self, jsonl_trail: ConsensusAuditTrail, tmp_jsonl_path: Path
    ) -> None:
        """Rapid-fire decision writes should all be persisted."""
        count = 100
        for i in range(count):
            jsonl_trail.record_decision(
                decision_id=f"d{i}",
                consensus_id=f"c{i}",
                proposal=f"Proposal {i}",
                decision=f"Decision {i}",
                confidence=0.5 + (i % 50) * 0.01,
            )

        jsonl_trail._jsonl_queue.join()
        lines = tmp_jsonl_path.read_text(encoding="utf-8").strip().splitlines()
        assert len(lines) == count


# ---------------------------------------------------------------------------
# Non-JSONL mode does not write files
# ---------------------------------------------------------------------------


class TestMemoryModeNoFile:
    """Test that memory mode does not create JSONL files."""

    def test_memory_mode_no_jsonl_file(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Memory mode should not create any JSONL file."""
        test_path = tmp_path / "should_not_exist.jsonl"
        monkeypatch.setattr(
            "heretek_swarm.consensus.audit_trail._CONSENSUS_AUDIT_FILE",
            test_path,
        )
        trail = ConsensusAuditTrail(storage_backend="memory")
        trail.record_decision(
            decision_id="d1",
            consensus_id="c1",
            proposal="Test",
            decision="Yes",
            confidence=0.9,
        )
        assert not test_path.exists()
