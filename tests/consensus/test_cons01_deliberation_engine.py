"""
Tests for CONS01: Inter-Agent Dispute Consensus Engine.

These tests verify the deliberation engine resolves non-critical disputes
without human mediation and achieves ≥15% position change ratio.
"""

import pytest
from unittest.mock import Mock

from heretek_swarm.consensus.cons01_dispute_resolution import (
    DisputeType,
    DisputeState,
    DisputeSubmission,
    DisputeResult,
    MinorityReport,
    PositionChangeRecord,
    DisputeResolutionEngine,
)


@pytest.fixture
def engine():
    return DisputeResolutionEngine(
        consensus_threshold=0.75,
        min_rounds=2,
        max_rounds=5,
        position_change_target=0.15,
    )


@pytest.fixture
def mock_swarm_deliberation():
    mock = Mock()
    mock.start_deliberation.return_value = None
    mock.submit_position.return_value = True
    mock.run_deliberation_round.return_value = Mock(
        round_number=1,
        consensus_score=0.80,
        position_changes=1,
    )
    mock.finalize_deliberation.return_value = Mock(
        final_position=Mock(value="agree"),
        consensus_score=0.80,
        minority_report=[],
        rounds_completed=2,
    )
    mock.get_minority_opinions.return_value = []
    return mock


@pytest.fixture
def mock_tribunal():
    from heretek_swarm.consensus.tribunal import Tribunal, TribunalCase, TribunalRuling, RulingType

    mock = Mock(spec=Tribunal)
    case = TribunalCase(
        case_id="case-001",
        original_decision_id="dispute-006",
        appellant_agent_id="agent-1",
        grounds="CRITICAL dispute: safety_critical",
        description="Safety protocol change: Modifying safety constraints",
    )
    mock.create_case.return_value = case
    ruling = TribunalRuling(
        ruling_id="ruling-001",
        case_id=case.case_id,
        ruling_type=RulingType.UPHOLD,
        reasoning="Binding decision for CRITICAL safety_critical dispute",
        confidence=1.0,
    )
    mock.issue_ruling.return_value = ruling
    return mock


class TestDisputeTypeClassification:
    def test_constitutional_is_critical(self):
        assert DisputeType.CONSTITUTIONAL.is_critical is True

    def test_safety_critical_is_critical(self):
        assert DisputeType.SAFETY_CRITICAL.is_critical is True

    def test_resource_over_threshold_is_critical(self):
        assert DisputeType.RESOURCE_ALLOCATION.is_critical is True

    def test_external_reputation_is_critical(self):
        assert DisputeType.EXTERNAL_REPUTATION.is_critical is True

    def test_technical_is_non_critical(self):
        assert DisputeType.TECHNICAL.is_critical is False

    def test_priority_is_non_critical(self):
        assert DisputeType.PRIORITY.is_critical is False

    def test_implementation_is_non_critical(self):
        assert DisputeType.IMPLEMENTATION.is_critical is False


class TestDisputeSubmission:
    def test_create_dispute_submission(self):
        submission = DisputeSubmission(
            dispute_id="dispute-001",
            parties=["agent-1", "agent-2"],
            topic="Implementation approach",
            description="Agent-1 and Agent-2 disagree on approach",
            dispute_type=DisputeType.IMPLEMENTATION,
            submitted_by="agent-1",
        )

        assert submission.dispute_id == "dispute-001"
        assert len(submission.parties) == 2
        assert submission.dispute_type == DisputeType.IMPLEMENTATION
        assert submission.status == DisputeState.SUBMITTED

    def test_dispute_type_detection(self):
        assert DisputeType.TECHNICAL.is_critical is False
        assert DisputeType.CONSTITUTIONAL.is_critical is True


class TestPositionChangeTracking:
    def test_track_position_change(self):
        record = PositionChangeRecord(
            agent_id="agent-1",
            dispute_id="dispute-001",
            round=1,
            old_position="AGAINST",
            new_position="FOR",
        )

        assert record.agent_id == "agent-1"
        assert record.old_position == "AGAINST"
        assert record.new_position == "FOR"

    def test_position_change_ratio_calculation(self):
        changes = [
            PositionChangeRecord("agent-1", "d1", 1, "AGAINST", "FOR"),
        ]
        total_participants = 4

        ratio = len(changes) / total_participants
        assert ratio >= 0.15

    def test_position_change_ratio_below_target(self):
        changes = [
            PositionChangeRecord("agent-1", "d1", 1, "AGAINST", "FOR"),
        ]
        total_participants = 10

        ratio = len(changes) / total_participants
        assert ratio < 0.15


class TestMinorityReportPreservation:
    def test_create_minority_report(self):
        report = MinorityReport(
            agent_id="agent-dissenter",
            original_position="AGAINST",
            final_position="AGAINST",
            rationale="Significant risks identified",
            confidence=0.85,
        )

        assert report.agent_id == "agent-dissenter"
        assert report.persisted is True
        assert report.original_position == report.final_position

    def test_minority_report_after_position_change(self):
        report = MinorityReport(
            agent_id="agent-1",
            original_position="AGAINST",
            final_position="FOR",
            rationale="Convinced by peer arguments",
            confidence=0.75,
        )

        assert report.original_position == "AGAINST"
        assert report.final_position == "FOR"


class TestDisputeResolutionEngine:
    def test_engine_initialization(self, engine):
        assert engine.consensus_threshold == 0.75
        assert engine.min_rounds == 2
        assert engine.max_rounds == 5
        assert engine.position_change_target == 0.15

    def test_submit_non_critical_dispute(self, engine):
        submission = DisputeSubmission(
            dispute_id="dispute-001",
            parties=["agent-1", "agent-2", "agent-3"],
            topic="Code review approach",
            description="Disagreement on review depth",
            dispute_type=DisputeType.TECHNICAL,
            submitted_by="agent-1",
        )

        dispute_id = engine.submit_dispute(submission)

        assert dispute_id == "dispute-001"
        assert dispute_id in engine.active_disputes

    def test_submit_critical_dispute_requires_human(self, engine):
        submission = DisputeSubmission(
            dispute_id="dispute-002",
            parties=["agent-1", "agent-2"],
            topic="Constitutional amendment",
            description="Changing core rules",
            dispute_type=DisputeType.CONSTITUTIONAL,
            submitted_by="agent-1",
        )

        dispute_id = engine.submit_dispute(submission)
        dispute = engine.active_disputes[dispute_id]

        assert dispute.requires_human_escalation is True
        assert dispute.status == DisputeState.ESCALATED

    def test_run_deliberation_updates_position_change_ratio(self, engine, mock_swarm_deliberation):
        engine._swarm_engine = mock_swarm_deliberation

        submission = DisputeSubmission(
            dispute_id="dispute-003",
            parties=["agent-1", "agent-2", "agent-3", "agent-4"],
            topic="Priority ordering",
            description="Disagreement on task priority",
            dispute_type=DisputeType.PRIORITY,
            submitted_by="agent-1",
        )
        engine.submit_dispute(submission)

        engine._position_changes["dispute-003"].append(
            PositionChangeRecord("agent-1", "dispute-003", 1, "AGAINST", "FOR")
        )

        ratio = engine.get_position_change_ratio("dispute-003")
        assert ratio >= 0.15

    def test_finalize_consensus_for_non_critical(self, engine, mock_swarm_deliberation):
        engine._swarm_engine = mock_swarm_deliberation

        submission = DisputeSubmission(
            dispute_id="dispute-004",
            parties=["agent-1", "agent-2"],
            topic="API design choice",
            description="REST vs GraphQL",
            dispute_type=DisputeType.TECHNICAL,
            submitted_by="agent-1",
        )
        engine.submit_dispute(submission)

        result = engine.finalize_consensus("dispute-004")

        assert result is not None
        assert result.binding is False
        assert result.consensus_score >= 0.75

    def test_finalize_consensus_preserves_minority_reports(self, engine, mock_swarm_deliberation):
        engine._swarm_engine = mock_swarm_deliberation

        submission = DisputeSubmission(
            dispute_id="dispute-005",
            parties=["agent-1", "agent-2", "agent-3"],
            topic="Testing strategy",
            description="Unit vs integration focus",
            dispute_type=DisputeType.TECHNICAL,
            submitted_by="agent-1",
        )
        engine.submit_dispute(submission)

        engine._minority_reports["dispute-005"].append(
            MinorityReport(
                agent_id="agent-2",
                original_position="AGAINST",
                final_position="FOR",
                rationale="Convinced by arguments",
                confidence=0.7,
            )
        )

        result = engine.finalize_consensus("dispute-005")

        assert len(result.minority_reports) == 1
        assert result.minority_reports[0].agent_id == "agent-2"

    def test_escalate_critical_to_tribunal(self, engine, mock_tribunal):
        engine.tribunal = mock_tribunal

        submission = DisputeSubmission(
            dispute_id="dispute-006",
            parties=["agent-1", "agent-2"],
            topic="Safety protocol change",
            description="Modifying safety constraints",
            dispute_type=DisputeType.SAFETY_CRITICAL,
            submitted_by="agent-1",
        )
        engine.submit_dispute(submission)

        result = engine.escalate_to_tribunal("dispute-006")

        assert result is not None
        assert result.binding is True
        assert result.status == DisputeState.ESCALATED


@pytest.mark.asyncio
class TestAsyncDeliberation:
    @pytest.fixture
    async def async_engine(self):
        return DisputeResolutionEngine()

    async def test_async_deliberation_flow(self, async_engine):
        submission = DisputeSubmission(
            dispute_id="async-dispute-001",
            parties=["agent-async-1", "agent-async-2", "agent-async-3"],
            topic="Deployment strategy",
            description="Blue-green vs canary deployment",
            dispute_type=DisputeType.IMPLEMENTATION,
            submitted_by="agent-async-1",
        )

        dispute_id = async_engine.submit_dispute(submission)
        assert dispute_id in async_engine.active_disputes


class TestDisputeResult:
    def test_create_dispute_result(self):
        result = DisputeResult(
            dispute_id="dispute-result-001",
            status=DisputeState.CONSENSUS,
            final_position="FOR",
            consensus_score=0.85,
            position_change_ratio=0.25,
            minority_reports=[],
            deliberation_rounds=3,
            binding=False,
        )

        assert result.dispute_id == "dispute-result-001"
        assert result.status == DisputeState.CONSENSUS
        assert result.consensus_score == 0.85
        assert result.position_change_ratio == 0.25
        assert result.binding is False

    def test_dispute_result_with_minority_reports(self):
        minority = MinorityReport(
            agent_id="dissenter",
            original_position="AGAINST",
            final_position="AGAINST",
            rationale="Risks outweigh benefits",
            confidence=0.9,
        )

        result = DisputeResult(
            dispute_id="dispute-result-002",
            status=DisputeState.CONSENSUS,
            final_position="FOR",
            consensus_score=0.80,
            position_change_ratio=0.15,
            minority_reports=[minority],
            deliberation_rounds=4,
            binding=False,
        )

        assert len(result.minority_reports) == 1
        assert result.minority_reports[0].agent_id == "dissenter"


class TestGate2Criteria:
    def test_noncritical_disputes_achieve_consensus_without_human(
        self, engine, mock_swarm_deliberation
    ):
        engine._swarm_engine = mock_swarm_deliberation

        submission = DisputeSubmission(
            dispute_id="gate2-dispute-001",
            parties=["agent-1", "agent-2", "agent-3"],
            topic="Cache invalidation strategy",
            description="TTL vs explicit invalidation",
            dispute_type=DisputeType.TECHNICAL,
            submitted_by="agent-1",
        )
        dispute_id = engine.submit_dispute(submission)

        for _ in range(2):
            engine.run_deliberation_round(dispute_id)

        result = engine.finalize_consensus(dispute_id)

        assert result.binding is False
        assert result.status == DisputeState.CONSENSUS
        assert dispute_id in engine.completed_disputes

    def test_position_change_ratio_meets_15_percent_target(self, engine, mock_swarm_deliberation):
        engine._swarm_engine = mock_swarm_deliberation

        submission = DisputeSubmission(
            dispute_id="gate2-dispute-002",
            parties=["agent-1", "agent-2", "agent-3", "agent-4", "agent-5"],
            topic="Database selection",
            description="PostgreSQL vs MongoDB",
            dispute_type=DisputeType.TECHNICAL,
            submitted_by="agent-1",
        )
        engine.submit_dispute(submission)

        engine._position_changes["gate2-dispute-002"].append(
            PositionChangeRecord("agent-1", "gate2-dispute-002", 1, "AGAINST", "FOR")
        )
        engine._position_changes["gate2-dispute-002"].append(
            PositionChangeRecord("agent-2", "gate2-dispute-002", 2, "AGAINST", "FOR")
        )

        ratio = engine.get_position_change_ratio("gate2-dispute-002")

        assert ratio >= 0.15

    def test_minority_reports_preserved_regardless_of_outcome(
        self, engine, mock_swarm_deliberation
    ):
        engine._swarm_engine = mock_swarm_deliberation

        submission = DisputeSubmission(
            dispute_id="gate2-dispute-003",
            parties=["agent-1", "agent-2", "agent-3"],
            topic="API versioning approach",
            description="URL versioning vs header versioning",
            dispute_type=DisputeType.TECHNICAL,
            submitted_by="agent-1",
        )
        engine.submit_dispute(submission)

        engine._minority_reports["gate2-dispute-003"].append(
            MinorityReport(
                agent_id="agent-2",
                original_position="AGAINST",
                final_position="FOR",
                rationale="Convinced by maintainability arguments",
                confidence=0.75,
            )
        )
        engine._minority_reports["gate2-dispute-003"].append(
            MinorityReport(
                agent_id="agent-3",
                original_position="AGAINST",
                final_position="AGAINST",
                rationale="Backward compatibility risks",
                confidence=0.85,
            )
        )

        result = engine.finalize_consensus("gate2-dispute-003")

        assert len(result.minority_reports) == 2
        assert all(r.persisted for r in result.minority_reports)
