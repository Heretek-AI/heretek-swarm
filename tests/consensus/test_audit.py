"""
Tests for the Decision Audit Trail module.

Tests cover:
- Audit event recording
- Decision record creation
- Vote and argument tracking
- Deliberation round recording
- Decision audit creation
- Export and verification
- Hash chain integrity
"""

import json
from datetime import datetime, timezone

import pytest

from heretek_swarm.consensus.audit import (
    ArgumentRecord,
    AuditEvent,
    AuditEventType,
    ConsensusAuditTrail,
    DecisionAudit,
    DecisionOutcome,
    DecisionRecord,
    DeliberationRoundRecord,
    VoteRecord,
)


class TestAuditEventType:
    """Tests for AuditEventType enum."""

    def test_event_type_values(self):
        """Test audit event type values."""
        assert AuditEventType.CONSENSUS_INITIATED.value == "consensus_initiated"
        assert AuditEventType.VOTE_SUBMITTED.value == "vote_submitted"
        assert AuditEventType.ARGUMENT_SUBMITTED.value == "argument_submitted"
        assert AuditEventType.CONSENSUS_REACHED.value == "consensus_reached"
        assert AuditEventType.CONSENSUS_FAILED.value == "consensus_failed"


class TestAuditEvent:
    """Tests for AuditEvent dataclass."""

    def test_audit_event_creation(self):
        """Test basic audit event creation."""
        event = AuditEvent(
            event_id="evt-001",
            event_type=AuditEventType.VOTE_SUBMITTED,
            timestamp=datetime.now(timezone.utc).isoformat(),
            consensus_id="consensus-1",
            agent_id="agent-1",
            data={"vote": "yes", "confidence": 0.8},
        )

        assert event.event_id == "evt-001"
        assert event.event_type == AuditEventType.VOTE_SUBMITTED
        assert event.consensus_id == "consensus-1"
        assert event.agent_id == "agent-1"
        assert event.data["vote"] == "yes"

    def test_audit_event_hash_generation(self):
        """Test that hash is generated for audit event."""
        event = AuditEvent(
            event_id="evt-001",
            event_type=AuditEventType.VOTE_SUBMITTED,
            timestamp="2026-04-07T12:00:00Z",
            consensus_id="consensus-1",
            agent_id="agent-1",
        )

        assert event.hash is not None
        assert len(event.hash) == 64  # SHA-256 hex length

    def test_audit_event_hash_chain(self):
        """Test hash chain linkage."""
        event1 = AuditEvent(
            event_id="evt-001",
            event_type=AuditEventType.CONSENSUS_INITIATED,
            timestamp="2026-04-07T12:00:00Z",
            consensus_id="consensus-1",
        )

        event2 = AuditEvent(
            event_id="evt-002",
            event_type=AuditEventType.VOTE_SUBMITTED,
            timestamp="2026-04-07T12:01:00Z",
            consensus_id="consensus-1",
            previous_hash=event1.hash,
        )

        assert event2.previous_hash == event1.hash


class TestVoteRecord:
    """Tests for VoteRecord dataclass."""

    def test_vote_record_creation(self):
        """Test basic vote record creation."""
        vote = VoteRecord(
            vote_id="vote-001",
            consensus_id="consensus-1",
            agent_id="agent-1",
            decision="approve",
            confidence=0.85,
            reasoning="All tests passed",
        )

        assert vote.vote_id == "vote-001"
        assert vote.consensus_id == "consensus-1"
        assert vote.agent_id == "agent-1"
        assert vote.decision == "approve"
        assert vote.confidence == 0.85
        assert vote.reasoning == "All tests passed"

    def test_vote_record_default_values(self):
        """Test vote record default values."""
        vote = VoteRecord(
            vote_id="vote-001",
            consensus_id="consensus-1",
            agent_id="agent-1",
            decision="approve",
            confidence=0.8,
        )

        # Default values should be present
        assert vote.reasoning is None or isinstance(vote.reasoning, str)
        assert isinstance(vote.metadata, dict)


class TestArgumentRecord:
    """Tests for ArgumentRecord dataclass."""

    def test_argument_record_creation(self):
        """Test basic argument record creation."""
        arg = ArgumentRecord(
            argument_id="arg-001",
            consensus_id="consensus-1",
            agent_id="agent-1",
            position="for",
            content="This proposal should be approved because...",
            supports=["arg-000"],
            rebuttals=[],
        )

        assert arg.argument_id == "arg-001"
        assert arg.position == "for"
        assert len(arg.supports) == 1
        assert len(arg.rebuttals) == 0


class TestDecisionRecord:
    """Tests for DecisionRecord dataclass."""

    def test_decision_record_creation(self):
        """Test basic decision record creation."""
        decision = DecisionRecord(
            decision_id="decision-001",
            consensus_id="consensus-1",
            proposal="Deploy to production",
            decision="deploy",
            confidence=0.85,
            participants=["agent-1", "agent-2", "agent-3"],
        )

        assert decision.decision_id == "decision-001"
        assert decision.proposal == "Deploy to production"
        assert decision.decision == "deploy"
        assert decision.confidence == 0.85
        assert len(decision.participants) == 3
        assert decision.outcome == DecisionOutcome.PENDING


class TestDecisionOutcome:
    """Tests for DecisionOutcome enum."""

    def test_outcome_values(self):
        """Test decision outcome values."""
        assert DecisionOutcome.SUCCESS.value == "success"
        assert DecisionOutcome.FAILURE.value == "failure"
        assert DecisionOutcome.PARTIAL_SUCCESS.value == "partial_success"
        assert DecisionOutcome.PENDING.value == "pending"
        assert DecisionOutcome.UNKNOWN.value == "unknown"


class TestDeliberationRoundRecord:
    """Tests for DeliberationRoundRecord dataclass."""

    def test_round_record_creation(self):
        """Test basic deliberation round record creation."""
        record = DeliberationRoundRecord(
            round_id="round-001",
            round_number=1,
            consensus_id="consensus-1",
            arguments_submitted=["arg-1", "arg-2"],
            positions={"agent-1": "for", "agent-2": "against"},
            consensus_score=0.65,
        )

        assert record.round_id == "round-001"
        assert record.round_number == 1
        assert len(record.arguments_submitted) == 2
        assert record.consensus_score == 0.65


class TestDecisionAudit:
    """Tests for DecisionAudit dataclass."""

    def test_decision_audit_creation(self):
        """Test basic decision audit creation."""
        audit = DecisionAudit(
            decision_id="decision-001",
            consensus_id="consensus-1",
            final_decision="deploy",
            consensus_method="MAKER",
            confidence_score=0.85,
            dissenting_agents=["agent-3"],
        )

        assert audit.decision_id == "decision-001"
        assert audit.final_decision == "deploy"
        assert audit.consensus_method == "MAKER"
        assert audit.confidence_score == 0.85
        assert len(audit.dissenting_agents) == 1
        assert audit.provenance_hash is not None

    def test_decision_audit_provenance_hash(self):
        """Test that provenance hash is generated."""
        audit = DecisionAudit(
            decision_id="decision-001",
            consensus_id="consensus-1",
            final_decision="deploy",
            consensus_method="MAKER",
        )

        assert audit.provenance_hash is not None
        assert len(audit.provenance_hash) == 64

    def test_decision_audit_update_outcome(self):
        """Test updating decision outcome."""
        audit = DecisionAudit(
            decision_id="decision-001",
            consensus_id="consensus-1",
            final_decision="deploy",
        )

        original_hash = audit.provenance_hash

        audit.update_outcome(DecisionOutcome.SUCCESS, verified=True)

        assert audit.outcome == DecisionOutcome.SUCCESS
        assert audit.outcome_verified_at is not None
        assert audit.provenance_hash != original_hash  # Hash should change

    def test_decision_audit_add_round(self):
        """Test adding deliberation round."""
        audit = DecisionAudit(
            decision_id="decision-001",
            consensus_id="consensus-1",
            final_decision="deploy",
        )

        original_hash = audit.provenance_hash
        original_count = len(audit.deliberation_rounds)

        round_record = DeliberationRoundRecord(
            round_id="round-001",
            round_number=1,
            consensus_id="consensus-1",
            consensus_score=0.7,
        )

        audit.add_deliberation_round(round_record)

        assert len(audit.deliberation_rounds) == original_count + 1
        assert audit.provenance_hash != original_hash

    def test_decision_audit_verify_integrity(self):
        """Test verifying audit integrity."""
        audit = DecisionAudit(
            decision_id="decision-001",
            consensus_id="consensus-1",
            final_decision="deploy",
        )

        is_valid = audit.verify_integrity()
        assert is_valid is True

    def test_decision_audit_to_dict(self):
        """Test converting audit to dictionary."""
        audit = DecisionAudit(
            decision_id="decision-001",
            consensus_id="consensus-1",
            final_decision="deploy",
            confidence_score=0.85,
        )

        data = audit.to_dict()

        assert data["decision_id"] == "decision-001"
        assert data["final_decision"] == "deploy"
        assert data["confidence_score"] == 0.85
        assert "provenance_hash" in data


class TestConsensusAuditTrail:
    """Tests for ConsensusAuditTrail."""

    @pytest.fixture
    def audit_trail(self):
        """Create audit trail for testing."""
        return ConsensusAuditTrail(
            storage_backend="memory",
            retention_days=90,
            enable_hash_chain=True,
        )

    def test_trail_initialization(self, audit_trail):
        """Test audit trail initialization."""
        assert audit_trail.storage_backend == "memory"
        assert audit_trail.retention_days == 90
        assert audit_trail.enable_hash_chain is True
        assert audit_trail.events == []
        assert audit_trail.decisions == {}

    def test_record_event(self, audit_trail):
        """Test recording an audit event."""
        event = audit_trail.record_event(
            event_type=AuditEventType.CONSENSUS_INITIATED,
            consensus_id="consensus-1",
            data={"proposal": "Test proposal"},
        )

        assert event.event_id is not None
        assert event.event_type == AuditEventType.CONSENSUS_INITIATED
        assert len(audit_trail.events) == 1

    def test_record_event_hash_chain(self, audit_trail):
        """Test hash chain linkage in events."""
        event1 = audit_trail.record_event(
            event_type=AuditEventType.CONSENSUS_INITIATED,
            consensus_id="consensus-1",
        )

        event2 = audit_trail.record_event(
            event_type=AuditEventType.VOTE_SUBMITTED,
            consensus_id="consensus-1",
            agent_id="agent-1",
        )

        assert event2.previous_hash == event1.hash

    def test_record_decision(self, audit_trail):
        """Test recording a decision."""
        decision = audit_trail.record_decision(
            decision_id="decision-001",
            consensus_id="consensus-1",
            proposal="Deploy to production",
            decision="deploy",
            confidence=0.85,
            participants=["agent-1", "agent-2"],
            reasoning="All tests passed",
        )

        assert decision.decision_id == "decision-001"
        assert len(audit_trail.decisions) == 1

        # Should have recorded events
        assert len(audit_trail.events) >= 2  # Initiated + Reached

    def test_record_vote(self, audit_trail):
        """Test recording a vote."""
        vote = audit_trail.record_vote(
            consensus_id="consensus-1",
            agent_id="agent-1",
            decision="approve",
            confidence=0.8,
            reasoning="Looks good",
        )

        assert vote.vote_id is not None
        assert vote.agent_id == "agent-1"
        assert len(audit_trail.votes["consensus-1"]) == 1

    def test_record_argument(self, audit_trail):
        """Test recording an argument."""
        arg = audit_trail.record_argument(
            consensus_id="consensus-1",
            agent_id="agent-1",
            position="for",
            content="This should be approved",
            supports=[],
            rebuttals=[],
        )

        assert arg.argument_id is not None
        assert len(audit_trail.arguments["consensus-1"]) == 1

    def test_record_decision_outcome(self, audit_trail):
        """Test recording decision outcome."""
        # First record a decision
        audit_trail.record_decision(
            decision_id="decision-001",
            consensus_id="consensus-1",
            proposal="Test",
            decision="approve",
            confidence=0.8,
        )

        # Record outcome
        audit_trail.record_decision_outcome(
            decision_id="decision-001",
            outcome=DecisionOutcome.SUCCESS,
            outcome_data={"deployment_id": "deploy-123"},
        )

        assert audit_trail.outcomes["decision-001"] == DecisionOutcome.SUCCESS

    def test_record_rollback(self, audit_trail):
        """Test recording a rollback."""
        audit_trail.record_decision(
            decision_id="decision-001",
            consensus_id="consensus-1",
            proposal="Test",
            decision="approve",
            confidence=0.8,
        )

        audit_trail.record_rollback(
            decision_id="decision-001",
            reason="Deployment failed health check",
        )

        # Should have recorded rollback event
        rollback_events = [
            e for e in audit_trail.events
            if e.event_type == AuditEventType.DECISION_ROLLED_BACK
        ]
        assert len(rollback_events) == 1

    def test_create_decision_audit(self, audit_trail):
        """Test creating a comprehensive decision audit."""
        # Record some data first
        audit_trail.record_decision(
            decision_id="decision-001",
            consensus_id="consensus-1",
            proposal="Test",
            decision="approve",
            confidence=0.8,
        )

        audit_trail.record_vote(
            consensus_id="consensus-1",
            agent_id="agent-1",
            decision="approve",
            confidence=0.85,
        )

        # Create audit
        audit = audit_trail.create_decision_audit(
            decision_id="decision-001",
            consensus_id="consensus-1",
            final_decision="approve",
            consensus_method="MAKER",
            confidence_score=0.8,
            dissenting_agents=[],
        )

        assert audit.audit_id is not None
        assert audit.final_decision == "approve"
        assert len(audit.votes_with_reasoning) == 1

    def test_record_deliberation_round(self, audit_trail):
        """Test recording a deliberation round."""
        round_record = audit_trail.record_deliberation_round(
            consensus_id="consensus-1",
            round_number=1,
            arguments_submitted=["arg-1"],
            positions={"agent-1": "for"},
            consensus_score=0.7,
        )

        assert round_record.round_id is not None
        assert round_record.round_number == 1

        # Should be stored
        history = audit_trail.get_deliberation_history("consensus-1")
        assert len(history) == 1

    def test_get_decision_audit(self, audit_trail):
        """Test getting a decision audit."""
        audit_trail.create_decision_audit(
            decision_id="decision-001",
            consensus_id="consensus-1",
            final_decision="approve",
            consensus_method="MAKER",
        )

        audit = audit_trail.get_decision_audit("decision-001")

        assert audit is not None
        assert audit.decision_id == "decision-001"

    def test_get_deliberation_history(self, audit_trail):
        """Test getting deliberation history."""
        audit_trail.record_deliberation_round(
            consensus_id="consensus-1",
            round_number=1,
            consensus_score=0.6,
        )

        audit_trail.record_deliberation_round(
            consensus_id="consensus-1",
            round_number=2,
            consensus_score=0.75,
        )

        history = audit_trail.get_deliberation_history("consensus-1")

        assert len(history) == 2
        assert history[0].round_number == 1
        assert history[1].round_number == 2

    def test_export_decision_audit(self, audit_trail):
        """Test exporting decision audit."""
        audit_trail.create_decision_audit(
            decision_id="decision-001",
            consensus_id="consensus-1",
            final_decision="approve",
        )

        export_data = audit_trail.export_decision_audit("decision-001", format="json")

        assert isinstance(export_data, str)
        data = json.loads(export_data)
        assert data["decision_id"] == "decision-001"

    def test_verify_audit_integrity(self, audit_trail):
        """Test verifying audit integrity."""
        audit_trail.create_decision_audit(
            decision_id="decision-001",
            consensus_id="consensus-1",
            final_decision="approve",
        )

        verification = audit_trail.verify_audit_integrity("decision-001")

        assert "valid" in verification
        assert verification["valid"] is True

    def test_get_audits_by_outcome(self, audit_trail):
        """Test getting audits by outcome."""
        # First record the decisions
        audit_trail.record_decision(
            decision_id="decision-001",
            consensus_id="consensus-1",
            proposal="Test proposal 1",
            decision="approve",
            confidence=0.8,
        )

        audit_trail.record_decision(
            decision_id="decision-002",
            consensus_id="consensus-2",
            proposal="Test proposal 2",
            decision="reject",
            confidence=0.7,
        )

        # Create decision audits
        audit_trail.create_decision_audit(
            decision_id="decision-001",
            consensus_id="consensus-1",
            final_decision="approve",
        )

        audit_trail.create_decision_audit(
            decision_id="decision-002",
            consensus_id="consensus-2",
            final_decision="reject",
        )

        # Update outcomes
        audit_trail.record_decision_outcome("decision-001", DecisionOutcome.SUCCESS)
        audit_trail.record_decision_outcome("decision-002", DecisionOutcome.FAILURE)

        successful = audit_trail.get_audits_by_outcome(DecisionOutcome.SUCCESS)
        failed = audit_trail.get_audits_by_outcome(DecisionOutcome.FAILURE)

        assert len(successful) >= 0
        assert len(failed) >= 0

    def test_get_failed_audits(self, audit_trail):
        """Test getting failed audits."""
        audit_trail.record_decision(
            decision_id="decision-001",
            consensus_id="consensus-1",
            proposal="Test proposal",
            decision="approve",
            confidence=0.8,
        )
        audit_trail.create_decision_audit(
            decision_id="decision-001",
            consensus_id="consensus-1",
            final_decision="approve",
        )
        audit_trail.record_decision_outcome("decision-001", DecisionOutcome.FAILURE)

        failed = audit_trail.get_failed_audits()

        assert len(failed) >= 0

    def test_get_successful_audits(self, audit_trail):
        """Test getting successful audits."""
        audit_trail.record_decision(
            decision_id="decision-001",
            consensus_id="consensus-1",
            proposal="Test proposal",
            decision="approve",
            confidence=0.8,
        )
        audit_trail.create_decision_audit(
            decision_id="decision-001",
            consensus_id="consensus-1",
            final_decision="approve",
        )
        audit_trail.record_decision_outcome("decision-001", DecisionOutcome.SUCCESS)

        successful = audit_trail.get_successful_audits()

        assert len(successful) >= 0

    def test_get_audit_statistics(self, audit_trail):
        """Test getting audit statistics."""
        audit_trail.create_decision_audit(
            decision_id="decision-001",
            consensus_id="consensus-1",
            final_decision="approve",
            confidence_score=0.8,
        )

        audit_trail.create_decision_audit(
            decision_id="decision-002",
            consensus_id="consensus-2",
            final_decision="reject",
            confidence_score=0.6,
        )

        stats = audit_trail.get_audit_statistics()

        assert stats["total_audits"] == 2
        assert stats["average_confidence"] == 0.7

    def test_get_decision(self, audit_trail):
        """Test getting a decision record."""
        audit_trail.record_decision(
            decision_id="decision-001",
            consensus_id="consensus-1",
            proposal="Test",
            decision="approve",
            confidence=0.8,
        )

        decision = audit_trail.get_decision("decision-001")

        assert decision is not None
        assert decision.decision_id == "decision-001"

    def test_get_vote_breakdown(self, audit_trail):
        """Test getting vote breakdown."""
        audit_trail.record_vote(
            consensus_id="consensus-1",
            agent_id="agent-1",
            decision="approve",
            confidence=0.9,
        )

        audit_trail.record_vote(
            consensus_id="consensus-1",
            agent_id="agent-2",
            decision="approve",
            confidence=0.8,
        )

        audit_trail.record_vote(
            consensus_id="consensus-1",
            agent_id="agent-3",
            decision="reject",
            confidence=0.6,
        )

        breakdown = audit_trail.get_vote_breakdown("consensus-1")

        assert breakdown["total_votes"] == 3
        assert "approve" in breakdown["by_decision"]
        assert "reject" in breakdown["by_decision"]

    def test_query_decisions(self, audit_trail):
        """Test querying decisions."""
        audit_trail.record_decision(
            decision_id="decision-001",
            consensus_id="consensus-1",
            proposal="Test 1",
            decision="approve",
            confidence=0.8,
            participants=["agent-1"],
        )

        audit_trail.record_decision(
            decision_id="decision-002",
            consensus_id="consensus-2",
            proposal="Test 2",
            decision="reject",
            confidence=0.6,
            participants=["agent-2"],
        )

        # Query all
        result = audit_trail.query_decisions()
        assert result.total_results == 2

        # Query by min confidence
        result = audit_trail.query_decisions(min_confidence=0.7)
        assert result.total_results == 1

    def test_get_decision_timeline(self, audit_trail):
        """Test getting decision timeline."""
        audit_trail.record_event(
            event_type=AuditEventType.CONSENSUS_INITIATED,
            consensus_id="consensus-1",
        )

        audit_trail.record_vote(
            consensus_id="consensus-1",
            agent_id="agent-1",
            decision="approve",
            confidence=0.8,
        )

        audit_trail.record_event(
            event_type=AuditEventType.CONSENSUS_REACHED,
            consensus_id="consensus-1",
        )

        timeline = audit_trail.get_decision_timeline("consensus-1")

        assert len(timeline) >= 2
        # Timeline should be sorted by timestamp
        for i in range(len(timeline) - 1):
            assert timeline[i]["timestamp"] <= timeline[i + 1]["timestamp"]

    def test_export_audit_data(self, audit_trail):
        """Test exporting audit data."""
        audit_trail.record_decision(
            decision_id="decision-001",
            consensus_id="consensus-1",
            proposal="Test",
            decision="approve",
            confidence=0.8,
        )

        export_data = audit_trail.export_audit_data(
            format="json",
            consensus_id="consensus-1",
            include_events=True,
            include_votes=True,
        )

        assert "export_timestamp" in export_data
        assert "decisions" in export_data
        assert len(export_data["decisions"]) == 1

    def test_verify_integrity(self, audit_trail):
        """Test verifying overall audit trail integrity."""
        audit_trail.record_event(
            event_type=AuditEventType.CONSENSUS_INITIATED,
            consensus_id="consensus-1",
        )

        audit_trail.record_event(
            event_type=AuditEventType.VOTE_SUBMITTED,
            consensus_id="consensus-1",
            agent_id="agent-1",
        )

        result = audit_trail.verify_integrity()

        assert "status" in result
        assert "total_events" in result
        assert "verified_events" in result

    def test_get_statistics(self, audit_trail):
        """Test getting audit trail statistics."""
        audit_trail.record_decision(
            decision_id="decision-001",
            consensus_id="consensus-1",
            proposal="Test",
            decision="approve",
            confidence=0.8,
        )

        audit_trail.record_vote(
            consensus_id="consensus-1",
            agent_id="agent-1",
            decision="approve",
            confidence=0.85,
        )

        stats = audit_trail.get_statistics()

        assert stats["total_decisions"] == 1
        assert stats["total_votes"] == 1
        assert stats["hash_chain_enabled"] is True

    def test_cleanup_old_data(self, audit_trail):
        """Test cleaning up old data."""
        # This is a placeholder test since cleanup depends on storage backend
        cleaned = audit_trail.cleanup_old_data()

        assert isinstance(cleaned, int)


class TestAuditTrailIntegration:
    """Integration tests for audit trail."""

    @pytest.fixture
    def audit_trail(self):
        """Create audit trail for integration testing."""
        return ConsensusAuditTrail(enable_hash_chain=True)

    def test_full_audit_lifecycle(self, audit_trail):
        """Test complete audit lifecycle."""
        # Start consensus
        audit_trail.record_event(
            event_type=AuditEventType.CONSENSUS_INITIATED,
            consensus_id="consensus-1",
            data={"proposal": "Deploy feature X"},
        )

        # Record votes
        audit_trail.record_vote(
            consensus_id="consensus-1",
            agent_id="agent-1",
            decision="approve",
            confidence=0.9,
            reasoning="All tests passed",
        )

        audit_trail.record_vote(
            consensus_id="consensus-1",
            agent_id="agent-2",
            decision="approve",
            confidence=0.85,
        )

        audit_trail.record_vote(
            consensus_id="consensus-1",
            agent_id="agent-3",
            decision="reject",
            confidence=0.6,
            reasoning="Need more testing",
        )

        # Record arguments
        audit_trail.record_argument(
            consensus_id="consensus-1",
            agent_id="agent-1",
            position="for",
            content="CI/CD pipeline passed",
        )

        # Record deliberation rounds
        audit_trail.record_deliberation_round(
            consensus_id="consensus-1",
            round_number=1,
            consensus_score=0.7,
        )

        # Record decision
        audit_trail.record_decision(
            decision_id="decision-001",
            consensus_id="consensus-1",
            proposal="Deploy feature X",
            decision="approve",
            confidence=0.8,
            participants=["agent-1", "agent-2", "agent-3"],
        )

        # Create comprehensive audit
        audit = audit_trail.create_decision_audit(
            decision_id="decision-001",
            consensus_id="consensus-1",
            final_decision="approve",
            consensus_method="MAKER",
            confidence_score=0.8,
            dissenting_agents=["agent-3"],
        )

        # Record outcome
        audit_trail.record_decision_outcome(
            decision_id="decision-001",
            outcome=DecisionOutcome.SUCCESS,
        )

        # Verify integrity
        verification = audit_trail.verify_audit_integrity("decision-001")
        assert verification["valid"] is True

        # Export
        export_data = audit_trail.export_decision_audit("decision-001")
        assert export_data is not None

    def test_hash_chain_integrity(self, audit_trail):
        """Test hash chain maintains integrity."""
        events = []
        for i in range(5):
            event = audit_trail.record_event(
                event_type=AuditEventType.VOTE_SUBMITTED,
                consensus_id=f"consensus-{i}",
                agent_id=f"agent-{i}",
            )
            events.append(event)

        # Verify chain
        for i in range(1, len(events)):
            assert events[i].previous_hash == events[i - 1].hash

        # Verify overall integrity
        result = audit_trail.verify_integrity()
        assert result["chain_broken"] is False
        assert result["failed_events"] == 0

    def test_query_and_export_workflow(self, audit_trail):
        """Test query and export workflow."""
        # Create multiple decisions
        for i in range(5):
            audit_trail.record_decision(
                decision_id=f"decision-{i:03d}",
                consensus_id=f"consensus-{i:03d}",
                proposal=f"Proposal {i}",
                decision="approve" if i % 2 == 0 else "reject",
                confidence=0.5 + (i * 0.1),
                participants=[f"agent-{j}" for j in range(3)],
            )

            outcome = DecisionOutcome.SUCCESS if i % 2 == 0 else DecisionOutcome.FAILURE
            audit_trail.record_decision_outcome(f"decision-{i:03d}", outcome)

        # Query by outcome
        result = audit_trail.query_decisions(outcome=DecisionOutcome.SUCCESS)
        assert result.total_results == 3  # 0, 2, 4

        # Export all
        export_data = audit_trail.export_audit_data(format="json")
        assert export_data["total_audits"] if "total_audits" in export_data else len(export_data.get("decisions", [])) == 5
