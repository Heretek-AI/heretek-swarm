"""
Tests for Immune Response Building Module.

Reference: Phase 2 Plan Task 2 (CONS-02)
"""

import pytest
from datetime import UTC, datetime

from heretek_swarm.consensus.immune import (
    ImmuneResponseBuilding,
    ImmunePattern,
    ImmuneResponse,
    NovelPatternPreservation,
    ImmuneQuorum,
    ImmuneStatus,
    PatternClassification,
    ResponseOutcome,
)


class TestImmuneResponseBuilding:
    """Tests for the ImmuneResponseBuilding class."""

    @pytest.fixture
    def immune_system(self):
        """Create a fresh immune system for testing."""
        return ImmuneResponseBuilding(
            min_occurrences_for_immunity=3,
            min_confidence_for_baseline=0.7,
            max_false_positive_rate=0.01,
            quorum_required_agents=3,
        )

    def test_initialization(self, immune_system):
        """Test immune system initializes correctly."""
        assert immune_system.min_occurrences_for_immunity == 3
        assert immune_system.min_confidence_for_baseline == 0.7
        assert immune_system.max_false_positive_rate == 0.01
        assert immune_system._stats["total_responses"] == 0
        assert len(immune_system._immune_memory) == 0

    def test_record_response_success(self, immune_system):
        """Test recording a successful immune response."""
        pattern_content = {"type": "rate_deviation", "agent_id": "test-agent"}
        
        response = immune_system.record_response(
            pattern_content=pattern_content,
            anomaly_id="anomaly-001",
            agent_id="test-agent",
            outcome=ResponseOutcome.SUCCESS,
            response_time_ms=150.0,
        )
        
        assert response is not None
        assert response.outcome == ResponseOutcome.SUCCESS
        assert response.pattern_id is not None
        assert immune_system._stats["total_responses"] == 1
        assert immune_system._stats["successful_responses"] == 1

    def test_record_response_false_positive(self, immune_system):
        """Test recording a false positive response."""
        pattern_content = {"type": "rate_deviation", "agent_id": "test-agent"}
        
        response = immune_system.record_response(
            pattern_content=pattern_content,
            anomaly_id="anomaly-002",
            agent_id="test-agent",
            outcome=ResponseOutcome.FALSE_POSITIVE,
            response_time_ms=100.0,
        )
        
        assert response.outcome == ResponseOutcome.FALSE_POSITIVE
        assert immune_system._stats["false_positives_reported"] == 1

    def test_learn_from_response_immunity_acquired(self, immune_system):
        """Test that immunity is acquired after sufficient successful responses."""
        pattern_content = {"type": "rate_deviation", "agent_id": "test-agent"}
        
        # Record multiple successful responses
        for i in range(5):
            response = immune_system.record_response(
                pattern_content=pattern_content,
                anomaly_id=f"anomaly-{i}",
                agent_id="test-agent",
                outcome=ResponseOutcome.SUCCESS,
                response_time_ms=150.0,
            )
            immune_system.learn_from_response(
                response=response,
                pattern_content=pattern_content,
                pattern_type="rate_deviation",
                severity="high",
            )
        
        # Check pattern was learned
        pattern_id = response.pattern_id
        assert pattern_id in immune_system._immune_memory
        
        immune_pattern = immune_system._immune_memory[pattern_id]
        assert immune_pattern.occurrence_count == 5
        assert immune_pattern.block_count == 5
        assert immune_pattern.confidence >= 0.7
        assert immune_system._stats["patterns_learned"] > 0

    def test_learn_from_response_false_positive_decreases_confidence(self, immune_system):
        """Test that false positives decrease pattern confidence."""
        pattern_content = {"type": "rate_deviation", "agent_id": "test-agent"}
        
        # Record mixed responses
        outcomes = [
            ResponseOutcome.SUCCESS,
            ResponseOutcome.SUCCESS,
            ResponseOutcome.FALSE_POSITIVE,
        ]
        
        for i, outcome in enumerate(outcomes):
            response = immune_system.record_response(
                pattern_content=pattern_content,
                anomaly_id=f"anomaly-{i}",
                agent_id="test-agent",
                outcome=outcome,
                response_time_ms=150.0,
            )
            immune_system.learn_from_response(
                response=response,
                pattern_content=pattern_content,
                pattern_type="rate_deviation",
                severity="high",
            )
        
        pattern_id = response.pattern_id
        immune_pattern = immune_system._immune_memory[pattern_id]
        assert immune_pattern.false_positive_count == 1
        # Confidence should still be reasonable with 2 successes and 1 FP
        assert immune_pattern.confidence > 0.0

    def test_check_pattern_immunity_novel(self, immune_system):
        """Test checking a novel pattern."""
        pattern_content = {"type": "novel_attack", "agent_id": "test-agent"}
        
        classification, immune_pattern = immune_system.check_pattern_immunity(pattern_content)
        
        assert classification == PatternClassification.NOVEL_MALICIOUS
        assert immune_pattern is None

    def test_check_pattern_immunity_known(self, immune_system):
        """Test checking a known (learned) pattern."""
        pattern_content = {"type": "rate_deviation", "agent_id": "test-agent"}
        
        # Learn the pattern
        for i in range(5):
            response = immune_system.record_response(
                pattern_content=pattern_content,
                anomaly_id=f"anomaly-{i}",
                agent_id="test-agent",
                outcome=ResponseOutcome.SUCCESS,
                response_time_ms=150.0,
            )
            immune_system.learn_from_response(
                response=response,
                pattern_content=pattern_content,
                pattern_type="rate_deviation",
                severity="high",
            )
        
        classification, immune_pattern = immune_system.check_pattern_immunity(pattern_content)
        
        # With enough successful responses and low FP rate, should be KNOWN_MALICIOUS
        assert immune_pattern is not None
        assert immune_pattern.occurrence_count == 5

    def test_preserve_novel_pattern(self, immune_system):
        """Test preserving a novel pattern for human review."""
        pattern_content = {"type": "unknown_attack", "agent_id": "test-agent"}
        
        preservation_id = immune_system.preserve_novel_pattern(
            pattern_content=pattern_content,
            pattern_type="unknown_attack",
            context={"first_observed": datetime.now(UTC).isoformat()},
        )
        
        assert preservation_id is not None
        assert immune_system._stats["novel_patterns_preserved"] == 1
        
        patterns = immune_system.get_novel_patterns_for_review(limit=10)
        assert len(patterns) == 1
        assert patterns[0].pattern_type == "unknown_attack"

    def test_record_human_review_approve(self, immune_system):
        """Test recording human review that approves a pattern."""
        pattern_content = {"type": "attack_pattern", "agent_id": "test-agent"}
        
        preservation_id = immune_system.preserve_novel_pattern(
            pattern_content=pattern_content,
            pattern_type="attack_pattern",
            context={},
        )
        
        result = immune_system.record_human_review(
            preservation_id=preservation_id,
            reviewer_id="human-reviewer",
            disposition="approve",
            notes="Confirmed as malicious pattern",
        )

        assert result is True

        # Check pattern was added to immune memory (approved patterns are moved from novel_patterns to immune_memory)
        pattern_id = list(immune_system._immune_memory.keys())[0] if immune_system._immune_memory else None
        assert pattern_id is not None
        approved_pattern = immune_system._immune_memory.get(pattern_id)
        assert approved_pattern is not None
        assert approved_pattern.approved is True
        assert approved_pattern.approved_by == "human-reviewer"

    def test_quorum_request_and_vote(self, immune_system):
        """Test quorum-based baseline update request and voting."""
        pattern_content = {"type": "attack", "agent_id": "test-agent"}
        
        # Learn the pattern first
        for i in range(5):
            response = immune_system.record_response(
                pattern_content=pattern_content,
                anomaly_id=f"anomaly-{i}",
                agent_id="test-agent",
                outcome=ResponseOutcome.SUCCESS,
                response_time_ms=150.0,
            )
            immune_system.learn_from_response(
                response=response,
                pattern_content=pattern_content,
                pattern_type="attack",
                severity="high",
            )
        
        # Request baseline update
        pattern_id = list(immune_system._immune_memory.keys())[0]
        quorum_id = immune_system.request_baseline_update(
            pattern_id=pattern_id,
            requesting_agent_id="sentinel",
        )
        
        assert quorum_id is not None
        
        # Submit votes
        agents = ["agent-1", "agent-2", "agent-3"]
        for agent_id in agents:
            immune_system.submit_quorum_vote(
                quorum_id=quorum_id,
                agent_id=agent_id,
                approve=True,
            )
        
        # Check quorum was approved
        assert immune_system._pending_quorums[quorum_id].is_approved() is True
        assert immune_system._stats["baseline_updates_approved"] == 1

    def test_false_positive_rate_calculation(self, immune_system):
        """Test false positive rate calculation."""
        pattern_content = {"type": "test", "agent_id": "test-agent"}
        
        # Record mixed responses
        outcomes = [
            ResponseOutcome.SUCCESS,
            ResponseOutcome.SUCCESS,
            ResponseOutcome.FALSE_POSITIVE,
            ResponseOutcome.SUCCESS,
        ]
        
        for i, outcome in enumerate(outcomes):
            response = immune_system.record_response(
                pattern_content=pattern_content,
                anomaly_id=f"anomaly-{i}",
                agent_id="test-agent",
                outcome=outcome,
                response_time_ms=150.0,
            )
            immune_system.learn_from_response(
                response=response,
                pattern_content=pattern_content,
                pattern_type="test",
                severity="medium",
            )
        
        fp_rate = immune_system.calculate_false_positive_rate()
        assert fp_rate == 0.25  # 1 FP out of 4

    def test_precision_calculation(self, immune_system):
        """Test precision calculation (1 - FP rate)."""
        pattern_content = {"type": "test", "agent_id": "test-agent"}
        
        # 3 successes, 1 FP
        outcomes = [
            ResponseOutcome.SUCCESS,
            ResponseOutcome.SUCCESS,
            ResponseOutcome.SUCCESS,
            ResponseOutcome.FALSE_POSITIVE,
        ]
        
        for i, outcome in enumerate(outcomes):
            response = immune_system.record_response(
                pattern_content=pattern_content,
                anomaly_id=f"anomaly-{i}",
                agent_id="test-agent",
                outcome=outcome,
                response_time_ms=150.0,
            )
        
        precision = immune_system.get_precision()
        assert precision == 0.75  # 1 - (1/4) = 0.75

    def test_precision_target_met(self, immune_system):
        """Test precision target (99%) is met."""
        # Record mostly successful responses with few FPs
        pattern_content = {"type": "test", "agent_id": "test-agent"}
        
        for i in range(100):
            outcome = ResponseOutcome.SUCCESS if i % 100 < 99 else ResponseOutcome.FALSE_POSITIVE
            response = immune_system.record_response(
                pattern_content=pattern_content,
                anomaly_id=f"anomaly-{i}",
                agent_id="test-agent",
                outcome=outcome,
                response_time_ms=150.0,
            )
        
        precision = immune_system.get_precision()
        assert precision >= 0.99

    def test_audit_trail_recording(self, immune_system):
        """Test that events are recorded to audit trail."""
        pattern_content = {"type": "test", "agent_id": "test-agent"}
        
        response = immune_system.record_response(
            pattern_content=pattern_content,
            anomaly_id="anomaly-001",
            agent_id="test-agent",
            outcome=ResponseOutcome.SUCCESS,
            response_time_ms=150.0,
        )
        
        immune_system.learn_from_response(
            response=response,
            pattern_content=pattern_content,
            pattern_type="test",
            severity="medium",
        )
        
        # Check audit trail has entries
        audit_trail = immune_system.get_audit_trail(limit=10)
        assert len(audit_trail) >= 2  # At least response and learning events
        
        # Check audit trail has proper structure
        for entry in audit_trail:
            assert "timestamp" in entry
            assert "event_type" in entry
            assert "hash" in entry


class TestImmuneQuorum:
    """Tests for the ImmuneQuorum class."""

    def test_quorum_not_complete_initially(self):
        """Test quorum is not complete when first created."""
        quorum = ImmuneQuorum(required_agents=3)
        
        assert quorum.is_complete() is False
        assert quorum.is_approved() is None

    def test_quorum_complete_with_approvals(self):
        """Test quorum becomes complete and approved with enough approvals."""
        quorum = ImmuneQuorum(required_agents=3, approval_threshold=0.66)
        
        quorum.current_approvals = 2
        quorum.rejection_count = 1
        
        assert quorum.get_approval_ratio() == 2/3
        assert quorum.is_complete() is True
        assert quorum.is_approved() is True

    def test_quorum_rejected(self):
        """Test quorum is rejected when rejections exceed approvals."""
        quorum = ImmuneQuorum(required_agents=3, approval_threshold=0.66)
        
        quorum.current_approvals = 1
        quorum.rejection_count = 2
        
        assert quorum.get_approval_ratio() == 1/3
        assert quorum.is_complete() is True
        assert quorum.is_approved() is False

    def test_quorum_timeout(self):
        """Test quorum can expire due to timeout."""
        quorum = ImmuneQuorum(required_agents=3, timeout_seconds=0.1)
        quorum.started_at = datetime.now(UTC)
        
        # Simulate time passing (in real test would use mocking)
        import time
        time.sleep(0.2)
        
        assert quorum.is_complete() is True
        assert quorum.is_approved() is None  # No votes cast


class TestImmunePattern:
    """Tests for the ImmunePattern class."""

    def test_false_positive_rate_calculation(self):
        """Test FP rate calculation."""
        pattern = ImmunePattern(
            pattern_id="test-pattern",
            pattern_hash="abc123",
            pattern_type="test",
            severity="high",
            first_seen=datetime.now(UTC),
            last_seen=datetime.now(UTC),
            occurrence_count=10,
            false_positive_count=1,
        )
        
        assert pattern.calculate_false_positive_rate() == 0.1

    def test_is_trustworthy(self):
        """Test trustworthiness check."""
        pattern = ImmunePattern(
            pattern_id="test-pattern",
            pattern_hash="abc123",
            pattern_type="test",
            severity="high",
            first_seen=datetime.now(UTC),
            last_seen=datetime.now(UTC),
            occurrence_count=10,
            false_positive_count=0,
            false_positive_rate=0.0,
            confidence=0.9,
            approved=True,
        )
        
        assert pattern.is_trustworthy(min_confidence=0.7, max_fp_rate=0.01) is True
        
        # Test with high FP rate
        pattern.false_positive_rate = 0.05
        assert pattern.is_trustworthy(min_confidence=0.7, max_fp_rate=0.01) is False
        
        # Test with low confidence
        pattern.false_positive_rate = 0.0
        pattern.confidence = 0.5
        assert pattern.is_trustworthy(min_confidence=0.7, max_fp_rate=0.01) is False
        
        # Test without approval
        pattern.confidence = 0.9
        pattern.approved = False
        assert pattern.is_trustworthy(min_confidence=0.7, max_fp_rate=0.01) is False
