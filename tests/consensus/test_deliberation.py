"""
Tests for the enhanced Deliberation module.

Tests cover:
- Argument and CounterArgument creation
- Evidence quality weighting
- DeliberationEngine functionality
- Consensus confidence calculation
- Dissent tracking
"""

import pytest
from datetime import datetime, timezone, timedelta

from heretek_swarm.consensus.deliberation import (
    DeliberationEngine,
    DeliberationConfig,
    Argument,
    CounterArgument,
    Evidence,
    DeliberationRound,
    ConsensusConfidence,
    DissentRecord,
    Position,
    ArgumentType,
    EvidenceType,
    DeliberationOutcome,
)


class TestArgument:
    """Tests for Argument dataclass."""

    def test_argument_creation(self):
        """Test basic argument creation."""
        arg = Argument(
            agent_id="agent-1",
            position=Position.FOR,
            reasoning="This is a strong argument",
            confidence=0.8,
        )

        assert arg.agent_id == "agent-1"
        assert arg.position == Position.FOR
        assert arg.reasoning == "This is a strong argument"
        assert arg.confidence == 0.8
        assert arg.argument_type == ArgumentType.PRIMARY
        assert arg.expertise_weight == 1.0

    def test_argument_with_evidence(self):
        """Test argument with evidence references."""
        arg = Argument(
            agent_id="agent-1",
            position=Position.FOR,
            reasoning="Evidence supports this",
            evidence_refs=["evidence-1", "evidence-2"],
            confidence=0.9,
        )

        assert len(arg.evidence_refs) == 2
        assert "evidence-1" in arg.evidence_refs

    def test_calculate_strength_no_evidence(self):
        """Test argument strength calculation without evidence."""
        arg = Argument(
            agent_id="agent-1",
            position=Position.FOR,
            reasoning="No evidence argument",
            confidence=0.7,
            evidence_refs=[],
        )

        strength = arg.calculate_strength({})
        # With no evidence: 0.6 * confidence + 0.4 * 0 = 0.6 * 0.7 = 0.42
        assert abs(strength - 0.42) < 0.01

    def test_calculate_strength_with_evidence(self):
        """Test argument strength calculation with evidence."""
        arg = Argument(
            agent_id="agent-1",
            position=Position.FOR,
            reasoning="With evidence",
            confidence=0.7,
            evidence_refs=["evidence-1"],
            expertise_weight=1.0,
        )

        evidence = Evidence(
            evidence_type=EvidenceType.DATA,
            content="Strong evidence",
            reliability_score=0.9,
        )
        evidence_dict = {"evidence-1": evidence}

        strength = arg.calculate_strength(evidence_dict)
        # Should factor in both confidence and evidence quality
        assert 0.5 <= strength <= 1.0

    def test_calculate_strength_with_expertise_weight(self):
        """Test argument strength calculation with expertise weighting."""
        arg = Argument(
            agent_id="expert-agent",
            position=Position.FOR,
            reasoning="Expert opinion",
            confidence=0.8,
            expertise_weight=1.5,  # Higher expertise
        )

        strength = arg.calculate_strength({})
        # Base: 0.6 * 0.8 = 0.48, then * 1.5 = 0.72
        assert abs(strength - 0.72) < 0.01


class TestEvidence:
    """Tests for Evidence dataclass."""

    def test_evidence_creation(self):
        """Test basic evidence creation."""
        evidence = Evidence(
            evidence_type=EvidenceType.DATA,
            content="This is evidence content",
            source="Research paper",
            reliability_score=0.85,
        )

        assert evidence.evidence_type == EvidenceType.DATA
        assert evidence.content == "This is evidence content"
        assert evidence.source == "Research paper"
        assert evidence.reliability_score == 0.85

    def test_calculate_quality_default(self):
        """Test quality calculation with default values."""
        evidence = Evidence(
            evidence_type=EvidenceType.DATA,
            content="Basic evidence",
            reliability_score=0.5,
        )

        quality = evidence.calculate_quality()
        # DATA type has 1.0 modifier, no source bonus: 0.5 * 1.0 = 0.5
        assert abs(quality - 0.5) < 0.01

    def test_calculate_quality_with_source(self):
        """Test quality calculation with verified source."""
        evidence = Evidence(
            evidence_type=EvidenceType.DATA,
            content="Verified evidence",
            source="Peer-reviewed journal",
            reliability_score=0.9,
        )

        quality = evidence.calculate_quality()
        # DATA type: 0.9 * 1.0 + 0.1 (source bonus) = 1.0 (capped)
        assert quality == 1.0


class TestCounterArgument:
    """Tests for CounterArgument dataclass."""

    def test_counter_argument_creation(self):
        """Test counter argument creation."""
        counter = CounterArgument(
            agent_id="agent-2",
            original_argument_id="arg-1",
            counter_reasoning="This argument is flawed because...",
            confidence=0.75,
        )

        assert counter.original_argument_id == "arg-1"
        assert counter.counter_reasoning == "This argument is flawed because..."
        assert counter.confidence == 0.75

    def test_counter_argument_fields(self):
        """Test counter argument has required fields."""
        counter = CounterArgument(
            agent_id="agent-2",
            original_argument_id="arg-1",
            counter_reasoning="Direct rebuttal",
            confidence=0.8,
        )

        assert counter.counter_id is not None
        assert counter.timestamp is not None


class TestDeliberationEngine:
    """Tests for DeliberationEngine."""

    @pytest.fixture
    def engine(self):
        """Create a deliberation engine for testing."""
        config = DeliberationConfig(max_rounds=3, consensus_threshold=0.7, min_participants=2)
        return DeliberationEngine(config)

    def test_start_deliberation(self, engine):
        """Test starting a deliberation."""
        deliberation_id = engine.start_deliberation(
            topic="Feature Discussion",
            participants=["agent-1", "agent-2", "agent-3"],
        )

        assert deliberation_id is not None
        assert deliberation_id in engine.active_deliberations

        state = engine.active_deliberations[deliberation_id]
        assert state["topic"] == "Feature Discussion"
        assert len(state["participants"]) == 3

    def test_submit_argument_for(self, engine):
        """Test submitting a FOR argument."""
        deliberation_id = engine.start_deliberation(
            topic="Test topic",
            participants=["agent-1", "agent-2"],
        )

        argument_id = engine.submit_argument(
            deliberation_id=deliberation_id,
            agent_id="agent-1",
            position=Position.FOR,
            reasoning="I support this",
            confidence=0.8,
        )

        assert argument_id is not None

    def test_submit_argument_against(self, engine):
        """Test submitting an AGAINST argument."""
        deliberation_id = engine.start_deliberation(
            topic="Test topic",
            participants=["agent-1", "agent-2"],
        )

        argument_id = engine.submit_argument(
            deliberation_id=deliberation_id,
            agent_id="agent-1",
            position=Position.AGAINST,
            reasoning="I oppose this",
            confidence=0.7,
        )

        assert argument_id is not None

    def test_submit_argument_invalid_deliberation(self, engine):
        """Test submitting argument to non-existent deliberation."""
        argument_id = engine.submit_argument(
            deliberation_id="non-existent",
            agent_id="agent-1",
            position=Position.FOR,
            reasoning="Test",
        )

        assert argument_id is None

    def test_submit_evidence(self, engine):
        """Test submitting evidence."""
        deliberation_id = engine.start_deliberation(
            topic="Test topic",
            participants=["agent-1", "agent-2"],
        )

        argument_id = engine.submit_argument(
            deliberation_id=deliberation_id,
            agent_id="agent-1",
            position=Position.FOR,
            reasoning="Argument with evidence",
            confidence=0.8,
        )

        # Submit evidence using the engine's API (not Evidence object)
        evidence_id = engine.submit_evidence(
            deliberation_id=deliberation_id,
            evidence_type=EvidenceType.DATA,
            content="Supporting evidence",
            source="Test source",
            reliability_score=0.9,
            submitted_by="agent-1",
        )

        assert evidence_id is not None

    def test_run_deliberation_round(self, engine):
        """Test running a deliberation round."""
        deliberation_id = engine.start_deliberation(
            topic="Test topic",
            participants=["agent-1", "agent-2"],
        )

        # Submit arguments from both agents
        engine.submit_argument(
            deliberation_id=deliberation_id,
            agent_id="agent-1",
            position=Position.FOR,
            reasoning="Reason 1",
            confidence=0.8,
        )

        engine.submit_argument(
            deliberation_id=deliberation_id,
            agent_id="agent-2",
            position=Position.FOR,
            reasoning="Reason 2",
            confidence=0.7,
        )

        round_result = engine.run_deliberation_round(deliberation_id=deliberation_id)

        assert round_result is not None
        assert round_result.consensus_score > 0.5  # Both agents support

    def test_get_position_distribution(self, engine):
        """Test getting position distribution."""
        deliberation_id = engine.start_deliberation(
            topic="Test topic",
            participants=["agent-1", "agent-2", "agent-3"],
        )

        engine.submit_argument(
            deliberation_id=deliberation_id,
            agent_id="agent-1",
            position=Position.FOR,
            reasoning="For argument",
        )

        engine.submit_argument(
            deliberation_id=deliberation_id,
            agent_id="agent-2",
            position=Position.AGAINST,
            reasoning="Against argument",
        )

        engine.submit_argument(
            deliberation_id=deliberation_id,
            agent_id="agent-3",
            position=Position.NEUTRAL,
            reasoning="Neutral argument",
        )

        distribution = engine.get_position_distribution(deliberation_id=deliberation_id)

        # Distribution should contain position counts
        assert isinstance(distribution, dict)
        assert len(distribution) > 0

    def test_finalize_deliberation_consensus(self, engine):
        """Test finalizing deliberation with consensus."""
        deliberation_id = engine.start_deliberation(
            topic="Test topic",
            participants=["agent-1", "agent-2"],
        )

        # Both agents strongly support
        engine.submit_argument(
            deliberation_id=deliberation_id,
            agent_id="agent-1",
            position=Position.FOR,
            reasoning="Strong support",
            confidence=0.9,
        )

        engine.submit_argument(
            deliberation_id=deliberation_id,
            agent_id="agent-2",
            position=Position.FOR,
            reasoning="Also support",
            confidence=0.85,
        )

        result = engine.finalize_deliberation(deliberation_id=deliberation_id)

        assert result is not None
        assert result.final_position == Position.FOR
        assert result.consensus_score > 0.7

    def test_finalize_deliberation_dissent(self, engine):
        """Test finalizing deliberation with dissent."""
        deliberation_id = engine.start_deliberation(
            topic="Controversial topic",
            participants=["agent-1", "agent-2"],
        )

        # Agents disagree
        engine.submit_argument(
            deliberation_id=deliberation_id,
            agent_id="agent-1",
            position=Position.FOR,
            reasoning="For argument",
            confidence=0.9,
        )

        engine.submit_argument(
            deliberation_id=deliberation_id,
            agent_id="agent-2",
            position=Position.AGAINST,
            reasoning="Against argument",
            confidence=0.8,
        )

        result = engine.finalize_deliberation(deliberation_id=deliberation_id)

        assert result is not None


class TestConsensusConfidence:
    """Tests for ConsensusConfidence calculation."""

    def test_confidence_initialization(self):
        """Test ConsensusConfidence initialization."""
        cc = ConsensusConfidence()

        assert cc.overall_confidence == 0.0
        assert cc.evidence_quality_avg == 0.0
        assert cc.agreement_level == 0.0
        assert cc.dissent_count == 0
        assert cc.dissent_severity == 0.0
        assert cc.stability_score == 0.0

    def test_confidence_calculation_high_agreement(self):
        """Test confidence calculation with high agreement."""
        cc = ConsensusConfidence()
        
        dissent_records = []
        cc.calculate(
            for_weight=0.9,
            against_weight=0.1,
            total_weight=1.0,
            evidence_scores=[0.85, 0.9],
            dissent_records=dissent_records,
        )

        # High agreement, good evidence, no dissent = high confidence
        assert cc.overall_confidence > 0.7
        assert cc.agreement_level > 0.8

    def test_confidence_calculation_low_agreement(self):
        """Test confidence calculation with low agreement."""
        cc = ConsensusConfidence()
        
        dissent_records = [
            DissentRecord(agent_id="agent-1", position=Position.AGAINST, confidence=0.8, reasoning="Disagree")
        ]
        cc.calculate(
            for_weight=0.3,
            against_weight=0.7,
            total_weight=1.0,
            evidence_scores=[0.5],
            dissent_records=dissent_records,
        )

        # Low agreement, high dissent = lower confidence
        assert cc.dissent_count == 1
        assert cc.dissent_severity > 0


class TestDissentRecord:
    """Tests for DissentRecord."""

    def test_dissent_record_creation(self):
        """Test creating a dissent record."""
        record = DissentRecord(
            agent_id="agent-dissenter",
            position=Position.AGAINST,
            reasoning="I disagree because...",
            confidence=0.85,
        )

        assert record.agent_id == "agent-dissenter"
        assert record.position == Position.AGAINST
        assert record.reasoning == "I disagree because..."
        assert record.confidence == 0.85
        assert record.resolved is False

    def test_dissent_record_resolved(self):
        """Test dissent record with resolution."""
        record = DissentRecord(
            agent_id="agent-1",
            position=Position.NEUTRAL,
            reasoning="Initially disagreed",
            confidence=0.6,
            resolved=True,
            resolution_notes="Reached compromise",
        )

        assert record.resolved is True
        assert record.resolution_notes == "Reached compromise"


class TestDeliberationRound:
    """Tests for DeliberationRound."""

    def test_round_creation(self):
        """Test creating a deliberation round."""
        round_result = DeliberationRound(
            topic="Test Topic",
            consensus_score=0.75,
            outcome=DeliberationOutcome.DEADLOCK,
        )

        assert round_result.topic == "Test Topic"
        assert round_result.consensus_score == 0.75
        assert round_result.outcome == DeliberationOutcome.DEADLOCK

    def test_round_attributes(self):
        """Test DeliberationRound attributes."""
        round_result = DeliberationRound(
            topic="Test Topic",
            consensus_score=0.8,
            outcome=DeliberationOutcome.CONSENSUS,
        )

        assert round_result.topic == "Test Topic"
        assert round_result.consensus_score == 0.8
        assert round_result.outcome == DeliberationOutcome.CONSENSUS
        assert round_result.round_id is not None
        assert isinstance(round_result.arguments, list)
        assert isinstance(round_result.participant_agents, list)


@pytest.mark.asyncio
class TestAsyncDeliberation:
    """Async tests for deliberation engine."""

    @pytest.fixture
    async def engine(self):
        """Create async deliberation engine."""
        config = DeliberationConfig(max_rounds=3, min_participants=2)
        return DeliberationEngine(config)

    async def test_deliberation_basic(self, engine):
        """Test basic deliberation flow."""
        deliberation_id = engine.start_deliberation(
            topic="Time-sensitive topic",
            participants=["agent-1", "agent-2"],
        )

        # Submit initial argument
        engine.submit_argument(
            deliberation_id=deliberation_id,
            agent_id="agent-1",
            position=Position.FOR,
            reasoning="Initial position",
            confidence=0.8,
        )

        # Run a round
        round_result = engine.run_deliberation_round(deliberation_id=deliberation_id)

        assert round_result is not None
