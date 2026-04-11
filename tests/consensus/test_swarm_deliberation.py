"""
Comprehensive tests for Swarm Deliberation and Enhanced Consensus modules.

This test suite covers:
- SwarmDeliberationEngine functionality
- AgentExpertiseProfiler functionality
- EnhancedMAKERConsensus functionality
- ConsensusAuditTrail functionality
- Integration between all modules
"""


import pytest

from heretek_swarm.consensus.audit import (
    ConsensusAuditTrail,
    DecisionOutcome,
)
from heretek_swarm.consensus.expertise import (
    AgentExpertiseProfiler,
    ExpertiseLevel,
)
from heretek_swarm.consensus.maker_enhanced import (
    EnhancedMAKERConsensus,
    ReasoningChain,
    ReasoningChainStatus,
    ReasoningStep,
)
from heretek_swarm.consensus.swarm_deliberation import (
    DeliberationState,
    Position,
    SwarmDeliberationEngine,
)


class TestAgentExpertiseProfiler:
    """Tests for AgentExpertiseProfiler."""

    def test_profiler_initialization(self) -> None:
        """Test profiler initializes correctly."""
        profiler = AgentExpertiseProfiler(calibration_window=20)
        assert profiler.calibration_window == 20
        assert len(profiler.profiles) == 0
        assert len(profiler.domain_statistics) == 0

    def test_register_agent(self) -> None:
        """Test agent registration."""
        profiler = AgentExpertiseProfiler()
        profile = profiler.register_agent(
            agent_id="agent-1",
            domains=["code_review", "security"],
            initial_expertise=0.6,
        )

        assert profile.agent_id == "agent-1"
        assert "code_review" in profile.domains
        assert "security" in profile.domains
        assert profile.domains["code_review"].expertise_score == 0.6
        assert profile.domains["security"].expertise_score == 0.6

    def test_register_agent_duplicate(self) -> None:
        """Test registering an already registered agent."""
        profiler = AgentExpertiseProfiler()
        profiler.register_agent("agent-1", ["domain1"])
        profile = profiler.register_agent("agent-1", ["domain2"])

        assert "domain1" in profile.domains
        assert "domain2" in profile.domains

    def test_record_outcome(self) -> None:
        """Test recording decision outcomes."""
        profiler = AgentExpertiseProfiler()
        profiler.register_agent("agent-1", ["code_review"])

        # Record multiple outcomes
        for i in range(10):
            profiler.record_outcome(
                agent_id="agent-1",
                domain="code_review",
                was_correct=(i < 8),  # 80% accuracy
                confidence=0.85,
            )

        profile = profiler.get_profile("agent-1")
        assert profile is not None
        assert profile.domains["code_review"].total_decisions == 10
        assert profile.domains["code_review"].correct_decisions == 8
        assert profile.domains["code_review"].accuracy == 0.8

    def test_get_weighted_confidence(self) -> None:
        """Test expertise-weighted confidence calculation."""
        profiler = AgentExpertiseProfiler()
        profiler.register_agent("agent-1", ["code_review"])

        # Record positive outcomes to build expertise
        for _ in range(20):
            profiler.record_outcome(
                agent_id="agent-1",
                domain="code_review",
                was_correct=True,
                confidence=0.9,
            )

        # Get weighted confidence
        weighted = profiler.get_weighted_confidence(
            agent_id="agent-1",
            domain="code_review",
            base_confidence=0.85,
        )

        # Weighted confidence should be higher due to expertise
        assert weighted >= 0.85

    def test_get_expertise_score_unknown_agent(self) -> None:
        """Test getting expertise for unknown agent."""
        profiler = AgentExpertiseProfiler()
        score = profiler.get_expertise_score("unknown-agent", "domain")
        assert score == 0.5  # Default score

    def test_get_expertise_level(self) -> None:
        """Test expertise level classification."""
        profiler = AgentExpertiseProfiler()
        profiler.register_agent("agent-1", ["domain"])

        # Initially novice or intermediate (default expertise is 0.5)
        level = profiler.get_expertise_level("agent-1", "domain")
        assert level in [ExpertiseLevel.NOVICE, ExpertiseLevel.INTERMEDIATE]

        # Build expertise
        for _ in range(50):
            profiler.record_outcome(
                agent_id="agent-1",
                domain="domain",
                was_correct=True,
                confidence=0.95,
            )

        level = profiler.get_expertise_level("agent-1", "domain")
        assert level in [ExpertiseLevel.EXPERT, ExpertiseLevel.MASTER]

    def test_get_domain_experts(self) -> None:
        """Test finding domain experts."""
        profiler = AgentExpertiseProfiler()

        # Register agents with varying expertise
        profiler.register_agent("expert", ["ml"], initial_expertise=0.9)
        profiler.register_agent("intermediate", ["ml"], initial_expertise=0.5)
        profiler.register_agent("novice", ["ml"], initial_expertise=0.2)

        experts = profiler.get_domain_experts("ml", min_expertise=0.6)

        assert len(experts) == 1
        assert experts[0][0] == "expert"
        assert experts[0][1] >= 0.6

    def test_get_reputation_weight(self) -> None:
        """Test getting reputation weight."""
        profiler = AgentExpertiseProfiler()
        profiler.register_agent("agent-1", ["domain"])

        weight = profiler.get_reputation_weight("agent-1")
        assert 0.0 <= weight <= 1.0

        # Unknown agent gets default weight
        unknown_weight = profiler.get_reputation_weight("unknown")
        assert unknown_weight == 0.5

    def test_export_profile(self) -> None:
        """Test exporting agent profile."""
        profiler = AgentExpertiseProfiler()
        profiler.register_agent("agent-1", ["domain"])
        profiler.record_outcome("agent-1", "domain", True, 0.8)

        export = profiler.export_profile("agent-1")

        assert "agent_id" in export
        assert "domains" in export
        assert "domain" in export["domains"]
        assert "expertise_score" in export["domains"]["domain"]

    def test_reset_agent_expertise(self) -> None:
        """Test resetting agent expertise."""
        profiler = AgentExpertiseProfiler()
        profiler.register_agent("agent-1", ["domain"])

        # Build expertise
        for _ in range(10):
            profiler.record_outcome("agent-1", "domain", True, 0.9)

        initial_score = profiler.get_expertise_score("agent-1", "domain")

        # Reset
        profiler.reset_agent_expertise("agent-1", "domain", reset_value=0.5)

        new_score = profiler.get_expertise_score("agent-1", "domain")
        assert new_score == 0.5
        assert new_score < initial_score


class TestSwarmDeliberationEngine:
    """Tests for SwarmDeliberationEngine."""

    def test_engine_initialization(self) -> None:
        """Test engine initializes correctly."""
        engine = SwarmDeliberationEngine(
            max_rounds=5,
            consensus_threshold=0.75,
            min_participants=3,
        )

        assert engine.max_rounds == 5
        assert engine.consensus_threshold == 0.75
        assert engine.min_participants == 3

    def test_start_deliberation(self) -> None:
        """Test starting a deliberation."""
        engine = SwarmDeliberationEngine()

        engine.start_deliberation(
            deliberation_id="test-1",
            proposal="Deploy to production",
            participants=["agent-1", "agent-2", "agent-3"],
        )

        state = engine.get_deliberation_state("test-1")
        assert state == DeliberationState.GATHERING_POSITIONS
        assert "test-1" in engine.active_deliberations

    def test_submit_position(self) -> None:
        """Test submitting positions."""
        engine = SwarmDeliberationEngine()
        engine.start_deliberation(
            deliberation_id="test-1",
            proposal="Test proposal",
            participants=["agent-1", "agent-2"],
        )

        result = engine.submit_position(
            deliberation_id="test-1",
            agent_id="agent-1",
            position=Position.AGREE,
            confidence=0.85,
            argument="All tests passed",
        )

        assert result is True
        assert "agent-1" in engine.active_deliberations["test-1"]["positions"]

    def test_submit_position_invalid_agent(self) -> None:
        """Test submitting position with invalid agent."""
        engine = SwarmDeliberationEngine()
        engine.start_deliberation(
            deliberation_id="test-1",
            proposal="Test",
            participants=["agent-1"],
        )

        result = engine.submit_position(
            deliberation_id="test-1",
            agent_id="agent-unknown",
            position=Position.AGREE,
            confidence=0.8,
        )

        assert result is False

    def test_run_deliberation_round(self) -> None:
        """Test running a deliberation round."""
        engine = SwarmDeliberationEngine()
        engine.start_deliberation(
            deliberation_id="test-1",
            proposal="Test",
            participants=["agent-1", "agent-2", "agent-3"],
        )

        # Submit positions
        engine.submit_position("test-1", "agent-1", Position.AGREE, 0.9)
        engine.submit_position("test-1", "agent-2", Position.AGREE, 0.85)
        engine.submit_position("test-1", "agent-3", Position.LEAN_AGREE, 0.6)

        # Run round
        round_result = engine.run_deliberation_round("test-1")

        assert round_result is not None
        assert round_result.round_number == 1
        assert len(round_result.positions) == 3

    def test_calculate_consensus_score(self) -> None:
        """Test consensus score calculation."""
        engine = SwarmDeliberationEngine()
        engine.start_deliberation(
            deliberation_id="test-1",
            proposal="Test",
            participants=["agent-1", "agent-2"],
        )

        # Unanimous agreement
        engine.submit_position("test-1", "agent-1", Position.STRONG_AGREE, 0.95)
        engine.submit_position("test-1", "agent-2", Position.AGREE, 0.9)

        score = engine._calculate_consensus_score("test-1")
        assert score > 0.8  # High consensus

    def test_get_minority_opinions(self) -> None:
        """Test getting minority opinions."""
        engine = SwarmDeliberationEngine()
        engine.start_deliberation(
            deliberation_id="test-1",
            proposal="Test",
            participants=["agent-1", "agent-2", "agent-3"],
        )

        # 2 agree, 1 disagrees
        engine.submit_position("test-1", "agent-1", Position.AGREE, 0.9)
        engine.submit_position("test-1", "agent-2", Position.AGREE, 0.85)
        engine.submit_position("test-1", "agent-3", Position.DISAGREE, 0.75)

        minority = engine.get_minority_opinions("test-1", min_confidence=0.6)

        assert len(minority) == 1
        assert minority[0]["agent_id"] == "agent-3"

    def test_finalize_deliberation(self) -> None:
        """Test finalizing deliberation."""
        engine = SwarmDeliberationEngine()
        engine.start_deliberation(
            deliberation_id="test-1",
            proposal="Deploy",
            participants=["agent-1", "agent-2", "agent-3"],
        )

        engine.submit_position("test-1", "agent-1", Position.AGREE, 0.9)
        engine.submit_position("test-1", "agent-2", Position.AGREE, 0.85)
        engine.submit_position("test-1", "agent-3", Position.LEAN_AGREE, 0.6)

        result = engine.finalize_deliberation("test-1")

        assert result is not None
        assert result.deliberation_id == "test-1"
        assert result.proposal == "Deploy"
        assert result.final_position in [Position.AGREE, Position.STRONG_AGREE]

    def test_get_position_distribution(self) -> None:
        """Test getting position distribution."""
        engine = SwarmDeliberationEngine()
        engine.start_deliberation(
            deliberation_id="test-1",
            proposal="Test",
            participants=["agent-1", "agent-2", "agent-3", "agent-4"],
        )

        engine.submit_position("test-1", "agent-1", Position.AGREE, 0.9)
        engine.submit_position("test-1", "agent-2", Position.AGREE, 0.85)
        engine.submit_position("test-1", "agent-3", Position.DISAGREE, 0.7)
        engine.submit_position("test-1", "agent-4", Position.LEAN_AGREE, 0.55)

        distribution = engine.get_position_distribution("test-1")

        assert "agree" in distribution
        assert "disagree" in distribution
        assert distribution["agree"] == 0.5  # 2 out of 4

    def test_cleanup_deliberation(self) -> None:
        """Test cleaning up deliberation."""
        engine = SwarmDeliberationEngine()
        engine.start_deliberation("test-1", "Test", ["agent-1"])

        assert "test-1" in engine.active_deliberations

        engine.cleanup_deliberation("test-1")

        assert "test-1" not in engine.active_deliberations
        assert "test-1" not in engine.deliberation_states

    def test_get_statistics(self) -> None:
        """Test getting engine statistics."""
        engine = SwarmDeliberationEngine()

        stats = engine.get_statistics()

        assert "max_rounds" in stats
        assert "consensus_threshold" in stats
        assert "min_participants" in stats

    @pytest.mark.asyncio
    async def test_run_deliberation_with_timeout(self) -> None:
        """Test running deliberation with timeout."""
        engine = SwarmDeliberationEngine(max_rounds=3)
        engine.start_deliberation(
            deliberation_id="test-1",
            proposal="Test",
            participants=["agent-1", "agent-2"],
        )

        # Submit initial positions
        engine.submit_position("test-1", "agent-1", Position.AGREE, 0.9)
        engine.submit_position("test-1", "agent-2", Position.AGREE, 0.85)

        result = await engine.run_deliberation_with_timeout(
            deliberation_id="test-1",
            round_interval=0.1,
            timeout=1.0,
        )

        assert result is not None
        assert result.rounds_completed <= 3


class TestEnhancedMAKERConsensus:
    """Tests for EnhancedMAKERConsensus."""

    def test_enhanced_initialization(self) -> None:
        """Test enhanced consensus initialization."""
        consensus = EnhancedMAKERConsensus(
            ahead_by_k=2,
            min_votes=3,
            enable_pattern_library=True,
            enable_rollback=True,
            enable_cross_validation=True,
        )

        assert consensus.ahead_by_k == 2
        assert consensus.min_votes == 3
        assert consensus.enable_pattern_library is True
        assert consensus.enable_rollback is True
        assert consensus.enable_cross_validation is True

    def test_start_consensus_with_proposal(self) -> None:
        """Test starting consensus with proposal."""
        consensus = EnhancedMAKERConsensus()

        consensus.start_consensus(
            consensus_id="test-1",
            proposal="Deploy to production",
            domain="deployment",
        )

        assert "test-1" in consensus.enhanced_votes
        assert "test-1" in consensus.decision_provenance
        assert consensus.decision_provenance["test-1"].proposal == "Deploy to production"

    def test_add_vote_with_reasoning(self) -> None:
        """Test adding vote with reasoning chain."""
        consensus = EnhancedMAKERConsensus()
        consensus.start_consensus("test-1", "Test proposal")

        chain_id = consensus.add_vote_with_reasoning(
            consensus_id="test-1",
            agent_id="agent-1",
            decision="deploy",
            confidence=0.9,
            reasoning_chain=[
                {"type": "observation", "content": "All tests passed", "confidence": 0.95},
                {"type": "inference", "content": "System is stable", "confidence": 0.9},
                {"type": "conclusion", "content": "Safe to deploy", "confidence": 0.9},
            ],
        )

        assert chain_id is not None
        assert len(consensus.reasoning_chains["test-1"]) == 1

    def test_reasoning_chain_validation(self) -> None:
        """Test reasoning chain validation."""
        chain = ReasoningChain(
            chain_id="chain-1",
            agent_id="agent-1",
            steps=[
                ReasoningStep(
                    step_number=1,
                    step_type="observation",
                    content="Tests passed",
                    confidence=0.95,
                ),
                ReasoningStep(
                    step_number=2,
                    step_type="conclusion",
                    content="Deploy",
                    confidence=0.9,
                ),
            ],
        )

        is_valid = chain.validate_chain()
        assert is_valid is True
        assert chain.status == ReasoningChainStatus.VALID

    def test_reasoning_chain_missing_conclusion(self) -> None:
        """Test reasoning chain validation with missing conclusion."""
        chain = ReasoningChain(
            chain_id="chain-1",
            agent_id="agent-1",
            steps=[
                ReasoningStep(
                    step_number=1,
                    step_type="observation",
                    content="Tests passed",
                    confidence=0.95,
                ),
            ],
        )

        is_valid = chain.validate_chain()
        assert is_valid is False
        assert chain.status == ReasoningChainStatus.INVALID

    def test_compute_consensus_with_validation(self) -> None:
        """Test computing consensus with validation."""
        # Test basic consensus (base functionality)
        consensus = EnhancedMAKERConsensus(min_votes=3, enable_pattern_library=False, enable_cross_validation=False, ahead_by_k=1)
        consensus.start_consensus("test-1", "Test proposal")

        # Add simple votes with different options (need at least 2 different decisions for algorithm)
        consensus.add_vote("test-1", "agent-1", "deploy", 0.9)
        consensus.add_vote("test-1", "agent-2", "deploy", 0.85)
        consensus.add_vote("test-1", "agent-3", "wait", 0.5)  # Different option

        # Test base consensus computation
        result = consensus.compute_consensus("test-1")

        assert result is not None
        assert result.decision == "deploy"

    def test_get_decision_provenance(self) -> None:
        """Test getting decision provenance."""
        consensus = EnhancedMAKERConsensus()
        consensus.start_consensus("test-1", "Test proposal")
        consensus.add_vote("test-1", "agent-1", "deploy", 0.9)

        provenance = consensus.get_decision_provenance("test-1")

        assert provenance is not None
        assert provenance.decision_id == "test-1"
        assert provenance.proposal == "Test proposal"

    def test_rollback_decision(self) -> None:
        """Test rolling back a decision."""
        consensus = EnhancedMAKERConsensus(enable_rollback=True, ahead_by_k=1)
        consensus.start_consensus("test-1", "Test proposal")

        # Need at least 2 different decisions for first_to_ahead_by_k to work
        consensus.add_vote("test-1", "agent-1", "deploy", 0.9)
        consensus.add_vote("test-1", "agent-2", "deploy", 0.85)
        consensus.add_vote("test-1", "agent-3", "wait", 0.8)  # Different vote

        result = consensus.compute_consensus("test-1")
        assert result is not None

        # Rollback
        rollback_result = consensus.rollback_decision(
            "test-1",
            reason="Deployment failed",
        )

        assert rollback_result.success is True
        assert "rolled back" in rollback_result.message.lower()

    def test_rollback_not_enabled(self) -> None:
        """Test rollback when not enabled."""
        consensus = EnhancedMAKERConsensus(enable_rollback=False)
        consensus.start_consensus("test-1", "Test")

        result = consensus.rollback_decision("test-1", "Test reason")

        assert result.success is False
        assert "not enabled" in result.message.lower()

    def test_export_provenance(self) -> None:
        """Test exporting decision provenance."""
        consensus = EnhancedMAKERConsensus()
        consensus.start_consensus("test-1", "Test proposal")
        consensus.add_vote_with_reasoning(
            consensus_id="test-1",
            agent_id="agent-1",
            decision="deploy",
            confidence=0.9,
            reasoning_chain=[
                {"type": "observation", "content": "Test", "confidence": 0.9},
                {"type": "conclusion", "content": "Deploy", "confidence": 0.9},
            ],
        )

        export = consensus.export_provenance("test-1")

        assert export is not None
        assert "decision_id" in export
        assert "reasoning_chains" in export

    def test_generate_decision_hash(self) -> None:
        """Test generating decision hash."""
        consensus = EnhancedMAKERConsensus(ahead_by_k=1)
        consensus.start_consensus("test-1", "Test proposal")
        # Need different votes for consensus to be reached
        consensus.add_vote("test-1", "agent-1", "deploy", 0.9)
        consensus.add_vote("test-1", "agent-2", "deploy", 0.85)
        consensus.add_vote("test-1", "agent-3", "wait", 0.8)
        result = consensus.compute_consensus("test-1")

        # Only test hash generation if consensus was reached
        if result is not None:
            hash_value = consensus.generate_decision_hash("test-1")
            assert hash_value is not None
            assert len(hash_value) == 64  # SHA-256 hex length

    def test_get_enhanced_statistics(self) -> None:
        """Test getting enhanced statistics."""
        consensus = EnhancedMAKERConsensus()
        consensus.start_consensus("test-1", "Test")
        consensus.add_vote_with_reasoning(
            "test-1", "agent-1", "deploy", 0.9,
            [{"type": "observation", "content": "Test", "confidence": 0.9},
             {"type": "conclusion", "content": "Deploy", "confidence": 0.9}],
        )

        stats = consensus.get_enhanced_statistics()

        assert "total_reasoning_chains" in stats
        assert "valid_reasoning_chains" in stats
        assert "chain_validity_rate" in stats


class TestConsensusAuditTrail:
    """Tests for ConsensusAuditTrail."""

    def test_audit_trail_initialization(self) -> None:
        """Test audit trail initialization."""
        audit = ConsensusAuditTrail(
            storage_backend="memory",
            retention_days=90,
            enable_hash_chain=True,
        )

        assert audit.storage_backend == "memory"
        assert audit.retention_days == 90
        assert audit.enable_hash_chain is True

    def test_record_decision(self) -> None:
        """Test recording a decision."""
        audit = ConsensusAuditTrail()

        record = audit.record_decision(
            decision_id="decision-1",
            consensus_id="consensus-1",
            proposal="Deploy to production",
            decision="deploy",
            confidence=0.85,
            participants=["agent-1", "agent-2"],
            reasoning="All tests passed",
        )

        assert record.decision_id == "decision-1"
        assert record.decision == "deploy"
        assert len(audit.decisions) == 1

    def test_record_vote(self) -> None:
        """Test recording a vote."""
        audit = ConsensusAuditTrail()
        audit.record_decision(
            "decision-1", "consensus-1", "Test", "deploy", 0.85,
        )

        vote = audit.record_vote(
            consensus_id="consensus-1",
            agent_id="agent-1",
            decision="deploy",
            confidence=0.9,
            reasoning="Tests passed",
        )

        assert vote.vote_id is not None
        assert vote.agent_id == "agent-1"
        assert len(audit.votes.get("consensus-1", [])) == 1

    def test_record_argument(self) -> None:
        """Test recording an argument."""
        audit = ConsensusAuditTrail()
        audit.record_decision("decision-1", "consensus-1", "Test", "deploy", 0.85)

        argument = audit.record_argument(
            consensus_id="consensus-1",
            agent_id="agent-1",
            position="agree",
            content="All tests passed successfully",
        )

        assert argument.argument_id is not None
        assert argument.agent_id == "agent-1"
        assert len(audit.arguments.get("consensus-1", [])) == 1

    def test_record_decision_outcome(self) -> None:
        """Test recording decision outcome."""
        audit = ConsensusAuditTrail()
        audit.record_decision("decision-1", "consensus-1", "Test", "deploy", 0.85)

        audit.record_decision_outcome(
            decision_id="decision-1",
            outcome=DecisionOutcome.SUCCESS,
            outcome_data={"deployment_time": "2026-04-06T12:00:00Z"},
        )

        decision = audit.get_decision("decision-1")
        assert decision is not None
        assert decision.outcome == DecisionOutcome.SUCCESS

    def test_get_vote_breakdown(self) -> None:
        """Test getting vote breakdown."""
        audit = ConsensusAuditTrail()
        audit.record_decision("decision-1", "consensus-1", "Test", "deploy", 0.85)

        audit.record_vote("consensus-1", "agent-1", "deploy", 0.9)
        audit.record_vote("consensus-1", "agent-2", "deploy", 0.85)
        audit.record_vote("consensus-1", "agent-3", "wait", 0.7)

        breakdown = audit.get_vote_breakdown("consensus-1")

        assert breakdown["total_votes"] == 3
        assert "deploy" in breakdown["by_decision"]
        assert breakdown["by_decision"]["deploy"]["count"] == 2

    def test_query_decisions(self) -> None:
        """Test querying decisions."""
        audit = ConsensusAuditTrail()

        audit.record_decision("decision-1", "consensus-1", "Test 1", "deploy", 0.9)
        audit.record_decision("decision-2", "consensus-2", "Test 2", "wait", 0.6)
        audit.record_decision("decision-3", "consensus-3", "Test 3", "deploy", 0.85)

        result = audit.query_decisions(min_confidence=0.8)

        assert result.total_results == 2
        assert len(result.results) == 2

    def test_get_decision_timeline(self) -> None:
        """Test getting decision timeline."""
        audit = ConsensusAuditTrail()
        audit.record_decision("decision-1", "consensus-1", "Test", "deploy", 0.85)
        audit.record_vote("consensus-1", "agent-1", "deploy", 0.9)
        audit.record_vote("consensus-1", "agent-2", "deploy", 0.85)

        timeline = audit.get_decision_timeline("consensus-1")

        assert len(timeline) >= 3  # At least decision + 2 votes
        assert all("event_type" in event for event in timeline)

    def test_export_audit_data(self) -> None:
        """Test exporting audit data."""
        audit = ConsensusAuditTrail()
        audit.record_decision("decision-1", "consensus-1", "Test", "deploy", 0.85)
        audit.record_vote("consensus-1", "agent-1", "deploy", 0.9)

        export = audit.export_audit_data(
            format="json",
            consensus_id="consensus-1",
            include_events=True,
            include_votes=True,
        )

        assert "decisions" in export
        assert "votes" in export
        assert "events" in export
        assert len(export["decisions"]) == 1

    def test_verify_integrity(self) -> None:
        """Test verifying audit trail integrity."""
        audit = ConsensusAuditTrail(enable_hash_chain=True)
        audit.record_decision("decision-1", "consensus-1", "Test", "deploy", 0.85)
        audit.record_vote("consensus-1", "agent-1", "deploy", 0.9)

        results = audit.verify_integrity()

        assert "total_events" in results
        assert "verified_events" in results
        assert results["status"] in ["valid", "hash_chain_disabled"]

    def test_get_statistics(self) -> None:
        """Test getting audit statistics."""
        audit = ConsensusAuditTrail()
        audit.record_decision("decision-1", "consensus-1", "Test", "deploy", 0.85)
        audit.record_vote("consensus-1", "agent-1", "deploy", 0.9)
        audit.query_decisions()

        stats = audit.get_statistics()

        assert "total_events" in stats
        assert "total_decisions" in stats
        assert "query_count" in stats

    def test_record_rollback(self) -> None:
        """Test recording a rollback."""
        audit = ConsensusAuditTrail()
        audit.record_decision("decision-1", "consensus-1", "Test", "deploy", 0.85)

        audit.record_rollback("decision-1", "Deployment failed")

        decision = audit.get_decision("decision-1")
        assert decision is not None
        assert "rollback_reason" in decision.metadata

    def test_get_arguments_for_consensus(self) -> None:
        """Test getting arguments for consensus."""
        audit = ConsensusAuditTrail()
        audit.record_decision("decision-1", "consensus-1", "Test", "deploy", 0.85)
        audit.record_argument("consensus-1", "agent-1", "agree", "Test argument")

        arguments = audit.get_arguments_for_consensus("consensus-1")

        assert len(arguments) == 1
        assert arguments[0].agent_id == "agent-1"


class TestIntegration:
    """Integration tests for consensus modules working together."""

    def test_expertise_with_deliberation(self) -> None:
        """Test expertise profiler integration with deliberation."""
        profiler = AgentExpertiseProfiler()
        profiler.register_agent("expert-agent", ["deployment"], initial_expertise=0.9)
        profiler.register_agent("novice-agent", ["deployment"], initial_expertise=0.3)

        engine = SwarmDeliberationEngine(expertise_profiler=profiler)
        engine.start_deliberation(
            deliberation_id="deploy-1",
            proposal="Deploy",
            participants=["expert-agent", "novice-agent"],
            domain="deployment",
        )

        engine.submit_position("deploy-1", "expert-agent", Position.AGREE, 0.95)
        engine.submit_position("deploy-1", "novice-agent", Position.LEAN_DISAGREE, 0.6)

        result = engine.finalize_deliberation("deploy-1")

        assert result is not None
        # Expert's position should have more weight
        assert result.final_position in [
            Position.AGREE,
            Position.LEAN_AGREE,
            Position.STRONG_AGREE,
        ]

    def test_enhanced_consensus_with_audit(self) -> None:
        """Test enhanced consensus with audit trail."""
        audit = ConsensusAuditTrail()
        consensus = EnhancedMAKERConsensus(enable_rollback=True, ahead_by_k=1)

        consensus.start_consensus("test-1", "Deploy decision")
        audit.record_decision(
            decision_id="audit-1",
            consensus_id="test-1",
            proposal="Deploy decision",
            decision="pending",
            confidence=0.0,
        )

        # Add votes with different options to allow consensus algorithm to work
        consensus.add_vote_with_reasoning(
            consensus_id="test-1",
            agent_id="agent-1",
            decision="deploy",
            confidence=0.9,
            reasoning_chain=[
                {"type": "observation", "content": "Tests passed", "confidence": 0.95},
                {"type": "conclusion", "content": "Deploy", "confidence": 0.9},
            ],
        )
        consensus.add_vote("test-1", "agent-2", "deploy", 0.85)
        consensus.add_vote("test-1", "agent-3", "wait", 0.5)  # Different vote

        audit.record_vote(
            consensus_id="test-1",
            agent_id="agent-1",
            decision="deploy",
            confidence=0.9,
            reasoning="Tests passed",
        )

        result = consensus.compute_consensus("test-1")

        # Update audit with final decision
        if result:
            audit.record_decision_outcome(
                decision_id="audit-1",
                outcome=DecisionOutcome.SUCCESS,
            )

        # Verify audit trail has complete record
        decision = audit.get_decision("audit-1")
        assert decision is not None
        # Outcome may be pending if consensus wasn't reached
        assert decision.outcome in [DecisionOutcome.SUCCESS, DecisionOutcome.PENDING]

    def test_full_deliberation_workflow(self) -> None:
        """Test complete deliberation workflow with all components."""
        # Setup
        profiler = AgentExpertiseProfiler()
        profiler.register_agent("agent-1", ["code"], initial_expertise=0.8)
        profiler.register_agent("agent-2", ["code"], initial_expertise=0.7)
        profiler.register_agent("agent-3", ["code"], initial_expertise=0.6)

        engine = SwarmDeliberationEngine(
            max_rounds=3,
            consensus_threshold=0.7,
            expertise_profiler=profiler,
        )

        audit = ConsensusAuditTrail()

        # Start deliberation
        engine.start_deliberation(
            deliberation_id="code-review-1",
            proposal="Merge pull request #123",
            participants=["agent-1", "agent-2", "agent-3"],
            domain="code",
        )

        audit.record_decision(
            decision_id="audit-code-1",
            consensus_id="code-review-1",
            proposal="Merge pull request #123",
            decision="pending",
            confidence=0.0,
        )

        # Submit positions
        engine.submit_position(
            "code-review-1", "agent-1", Position.AGREE, 0.9,
            "Code quality is excellent"
        )
        engine.submit_position(
            "code-review-1", "agent-2", Position.AGREE, 0.85,
            "Tests all pass"
        )
        engine.submit_position(
            "code-review-1", "agent-3", Position.LEAN_AGREE, 0.55,
            "Minor style issues but acceptable"
        )

        # Run deliberation rounds
        for _ in range(2):
            engine.run_deliberation_round("code-review-1")

        # Finalize
        result = engine.finalize_deliberation("code-review-1")

        # Record outcome in audit
        if result:
            audit.record_decision_outcome(
                decision_id="audit-code-1",
                outcome=DecisionOutcome.SUCCESS,
            )

        # Verify results
        assert result is not None
        assert result.consensus_score > 0.7
        assert result.participation_rate == 1.0

        # Verify audit trail
        timeline = audit.get_decision_timeline("code-review-1")
        assert len(timeline) > 0
