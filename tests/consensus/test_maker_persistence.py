"""
Tests for Enhanced MAKER Consensus Persistence.

Tests the persistence mechanisms for:
- Expertise profiles (export/import, save/load)
- Accuracy history (export/import)
- Decision provenance (export)
- Complete state (save/load)
"""

import json
import os
import tempfile
from datetime import UTC, datetime

import pytest

from heretek_swarm.consensus.expertise import AgentExpertiseProfiler
from heretek_swarm.consensus.maker_enhanced import EnhancedMAKERConsensus


class TestExpertiseProfilePersistence:
    """Test expertise profile export/import functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.profiler = AgentExpertiseProfiler(calibration_window=10)

    def test_export_profiles_structure(self):
        """Test export_profiles returns correct structure."""
        # Register an agent with domain expertise
        self.profiler.register_agent("agent-1", domains=["testing"], initial_expertise=0.8)
        self.profiler.record_outcome("agent-1", "testing", was_correct=True, confidence=0.85)

        exported = self.profiler.export_profiles()

        assert "profiles" in exported
        assert "domain_statistics" in exported
        assert "calibration_window" in exported
        assert "agent-1" in exported["profiles"]
        assert "testing" in exported["domain_statistics"]

    def test_export_import_roundtrip(self):
        """Test exported profiles can be imported back."""
        # Set up profiler with data
        self.profiler.register_agent("agent-1", domains=["testing", "security"])
        self.profiler.register_agent("agent-2", domains=["testing"], initial_expertise=0.9)

        # Record some outcomes
        self.profiler.record_outcome("agent-1", "testing", was_correct=True, confidence=0.8)
        self.profiler.record_outcome("agent-1", "testing", was_correct=True, confidence=0.85)
        self.profiler.record_outcome("agent-1", "security", was_correct=False, confidence=0.6)
        self.profiler.record_outcome("agent-2", "testing", was_correct=True, confidence=0.95)

        # Export
        exported = self.profiler.export_profiles()

        # Create new profiler and import
        new_profiler = AgentExpertiseProfiler()
        new_profiler.import_profiles(exported)

        # Verify data was preserved
        assert len(new_profiler.profiles) == 2
        assert "agent-1" in new_profiler.profiles
        assert "agent-2" in new_profiler.profiles

        # Verify domain expertise
        agent1_testing = new_profiler.get_expertise_score("agent-1", "testing")
        original_agent1_testing = self.profiler.get_expertise_score("agent-1", "testing")
        assert agent1_testing == original_agent1_testing

        # Verify domain statistics
        assert "testing" in new_profiler.domain_statistics
        assert "security" in new_profiler.domain_statistics

    def test_save_load_to_file(self):
        """Test save_to_file and load_from_file."""
        # Set up profiler with data
        self.profiler.register_agent("agent-1", domains=["testing"])
        self.profiler.record_outcome("agent-1", "testing", was_correct=True, confidence=0.9)

        # Create temp file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            temp_path = f.name

        try:
            # Save
            self.profiler.save_to_file(temp_path)

            # Verify file exists and is valid JSON
            with open(temp_path) as f:
                data = json.load(f)
            assert "profiles" in data

            # Load into new profiler
            new_profiler = AgentExpertiseProfiler()
            new_profiler.load_from_file(temp_path)

            # Verify data was loaded
            assert len(new_profiler.profiles) == 1
            assert new_profiler.get_expertise_score("agent-1", "testing") > 0.5

        finally:
            # Cleanup
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    def test_export_individual_profile(self):
        """Test export_profile for single agent."""
        self.profiler.register_agent("agent-1", domains=["testing"], initial_expertise=0.75)
        self.profiler.record_outcome("agent-1", "testing", was_correct=True, confidence=0.8)

        exported = self.profiler.export_profile("agent-1")

        assert exported["agent_id"] == "agent-1"
        assert "domains" in exported
        assert "testing" in exported["domains"]
        assert exported["domains"]["testing"]["expertise_score"] > 0.5
        assert "overall_reputation" in exported

    def test_export_unknown_agent(self):
        """Test export_profile for unknown agent returns empty."""
        exported = self.profiler.export_profile("unknown-agent")
        assert exported == {}


class TestAccuracyHistoryPersistence:
    """Test accuracy history export/import functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.consensus = EnhancedMAKERConsensus()
        self.consensus.start_consensus("test-consensus", domain="testing")

    def test_export_accuracy_history_structure(self):
        """Test export_accuracy_history returns correct structure."""
        # Record some outcomes
        self.consensus.record_decision_outcome("test-consensus", "agent-1", was_correct=True)
        self.consensus.record_decision_outcome("test-consensus", "agent-1", was_correct=False)
        self.consensus.record_decision_outcome("test-consensus", "agent-2", was_correct=True)

        exported = self.consensus.export_accuracy_history()

        assert "agent_accuracy_history" in exported
        assert "evidence_cache" in exported
        assert "test-consensus" in exported["agent_accuracy_history"]

    def test_export_import_accuracy_history_roundtrip(self):
        """Test accuracy history can be exported and imported."""
        # Record outcomes
        self.consensus.record_decision_outcome("test-consensus", "agent-1", was_correct=True)
        self.consensus.record_decision_outcome("test-consensus", "agent-1", was_correct=True)
        self.consensus.record_decision_outcome("test-consensus", "agent-1", was_correct=False)
        self.consensus.record_decision_outcome("test-consensus", "agent-2", was_correct=True)

        # Export
        exported = self.consensus.export_accuracy_history()

        # Create new consensus and import
        new_consensus = EnhancedMAKERConsensus()
        new_consensus.start_consensus("test-consensus")
        new_consensus.import_accuracy_history(exported)

        # Verify history was preserved
        assert "agent-1" in new_consensus.agent_accuracy_history["test-consensus"]
        assert new_consensus.agent_accuracy_history["test-consensus"]["agent-1"] == [True, True, False]
        assert new_consensus.agent_accuracy_history["test-consensus"]["agent-2"] == [True]

    def test_import_empty_accuracy_history(self):
        """Test importing empty accuracy history."""
        new_consensus = EnhancedMAKERConsensus()
        new_consensus.import_accuracy_history({})

        # Should not crash, just log
        assert isinstance(new_consensus.agent_accuracy_history, dict)


class TestEvidenceCachePersistence:
    """Test evidence cache export/import functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.consensus = EnhancedMAKERConsensus()

    def test_evidence_cache_in_export(self):
        """Test evidence cache is included in export."""
        # Create evidence quality manually
        from heretek_swarm.consensus.maker_enhanced import EvidenceQuality

        self.consensus.evidence_cache["test-key"] = EvidenceQuality(
            source_count=5,
            source_reliability=0.9,
            completeness=0.8,
            consistency=0.85,
            recency_score=0.7,
        )

        exported = self.consensus.export_accuracy_history()

        assert "evidence_cache" in exported
        assert "test-key" in exported["evidence_cache"]
        assert exported["evidence_cache"]["test-key"]["source_count"] == 5

    def test_evidence_cache_import_roundtrip(self):
        """Test evidence cache can be imported."""
        from heretek_swarm.consensus.maker_enhanced import EvidenceQuality

        # Set up evidence cache
        original_evidence = EvidenceQuality(
            source_count=5,
            source_reliability=0.9,
            completeness=0.8,
            consistency=0.85,
            recency_score=0.7,
        )
        self.consensus.evidence_cache["test-key"] = original_evidence

        # Export and import
        exported = self.consensus.export_accuracy_history()
        new_consensus = EnhancedMAKERConsensus()
        new_consensus.import_accuracy_history(exported)

        # Verify evidence was restored
        assert "test-key" in new_consensus.evidence_cache
        imported_evidence = new_consensus.evidence_cache["test-key"]
        assert imported_evidence.source_count == 5
        assert imported_evidence.source_reliability == 0.9


class TestCompleteStatePersistence:
    """Test complete state save/load functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.consensus = EnhancedMAKERConsensus(
            enable_pattern_library=True,
            enable_rollback=True,
            enable_cross_validation=True,
        )

    def test_save_state_structure(self):
        """Test save_state creates valid JSON file."""
        # Set up some state
        self.consensus.start_consensus("test-consensus", domain="testing")
        self.consensus.expertise_profiler.register_agent("agent-1", domains=["testing"])
        self.consensus.record_decision_outcome("test-consensus", "agent-1", was_correct=True)

        # Create temp file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            temp_path = f.name

        try:
            # Save state
            self.consensus.save_state(temp_path)

            # Verify file is valid JSON with expected structure
            with open(temp_path) as f:
                state = json.load(f)

            assert "expertise_profiler" in state
            assert "accuracy_history" in state
            assert "decision_provenance" in state

        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    def test_save_load_complete_state_roundtrip(self):
        """Test complete state can be saved and loaded."""
        # Set up comprehensive state
        self.consensus.start_consensus("test-consensus", domain="testing")

        # Register agents
        self.consensus.expertise_profiler.register_agent("agent-1", domains=["testing", "security"])
        self.consensus.expertise_profiler.register_agent("agent-2", domains=["testing"], initial_expertise=0.9)

        # Record outcomes
        self.consensus.record_decision_outcome("test-consensus", "agent-1", was_correct=True)
        self.consensus.record_decision_outcome("test-consensus", "agent-1", was_correct=True)
        self.consensus.record_decision_outcome("test-consensus", "agent-2", was_correct=True)

        # Add vote with reasoning
        self.consensus.add_vote_with_reasoning(
            consensus_id="test-consensus",
            agent_id="agent-1",
            decision="approve",
            confidence=0.85,
            reasoning_chain=[
                {"type": "observation", "content": "Tests passed", "confidence": 0.9},
                {"type": "conclusion", "content": "Safe to approve", "confidence": 0.85},
            ],
        )

        # Compute consensus to create provenance
        self.consensus.compute_consensus("test-consensus")

        # Create temp file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            temp_path = f.name

        try:
            # Save state
            self.consensus.save_state(temp_path)

            # Load into new consensus
            new_consensus = EnhancedMAKERConsensus()
            new_consensus.load_state(temp_path)

            # Verify expertise was restored
            assert len(new_consensus.expertise_profiler.profiles) == 2
            assert "agent-1" in new_consensus.expertise_profiler.profiles
            assert "agent-2" in new_consensus.expertise_profiler.profiles

            # Verify accuracy history was restored
            assert "test-consensus" in new_consensus.agent_accuracy_history
            assert new_consensus.agent_accuracy_history["test-consensus"]["agent-1"] == [True, True]

        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    def test_load_nonexistent_file(self):
        """Test load_state handles nonexistent file gracefully."""
        new_consensus = EnhancedMAKERConsensus()

        with pytest.raises(FileNotFoundError):
            new_consensus.load_state("/nonexistent/path/state.json")

    def test_load_invalid_json(self):
        """Test load_state handles invalid JSON gracefully."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            f.write("not valid json {")
            temp_path = f.name

        try:
            new_consensus = EnhancedMAKERConsensus()

            with pytest.raises(json.JSONDecodeError):
                new_consensus.load_state(temp_path)

        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)


class TestDecisionProvenanceExport:
    """Test decision provenance export functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.consensus = EnhancedMAKERConsensus(
            enable_pattern_library=True,
            enable_rollback=True,
        )

    def test_export_provenance_structure(self):
        """Test export_provenance returns correct structure."""
        self.consensus.start_consensus("test-consensus", proposal="Test proposal", domain="testing")

        # Add a vote
        self.consensus.add_vote_with_reasoning(
            consensus_id="test-consensus",
            agent_id="agent-1",
            decision="approve",
            confidence=0.85,
            reasoning_chain=[
                {"type": "observation", "content": "All good", "confidence": 0.9},
                {"type": "conclusion", "content": "Approve", "confidence": 0.85},
            ],
        )

        # Compute to finalize
        self.consensus.compute_consensus("test-consensus")

        exported = self.consensus.export_provenance("test-consensus")

        assert exported is not None
        assert exported["decision_id"] == "test-consensus"
        assert exported["proposal"] == "Test proposal"
        assert "start_time" in exported
        assert "end_time" in exported
        assert "participating_agents" in exported
        assert "reasoning_chains" in exported

    def test_export_provenance_with_patterns(self):
        """Test provenance includes pattern references."""
        self.consensus.start_consensus("test-consensus", domain="testing")

        # Add vote with pattern references
        self.consensus.add_vote_with_reasoning(
            consensus_id="test-consensus",
            agent_id="agent-1",
            decision="approve",
            confidence=0.85,
            reasoning_chain=[
                {"type": "observation", "content": "Pattern matched", "confidence": 0.9},
                {"type": "conclusion", "content": "Approve", "confidence": 0.85},
            ],
            pattern_references=["pattern-1", "pattern-2"],
        )

        self.consensus.compute_consensus("test-consensus")

        exported = self.consensus.export_provenance("test-consensus")

        assert "patterns_used" in exported
        assert "pattern-1" in exported["patterns_used"]
        assert "pattern-2" in exported["patterns_used"]

    def test_export_provenance_with_validation_results(self):
        """Test provenance includes validation results."""
        self.consensus.start_consensus("test-consensus", domain="testing")

        self.consensus.add_vote_with_reasoning(
            consensus_id="test-consensus",
            agent_id="agent-1",
            decision="approve",
            confidence=0.85,
            reasoning_chain=[
                {"type": "observation", "content": "Validated", "confidence": 0.9},
                {"type": "conclusion", "content": "Approve", "confidence": 0.85},
            ],
        )

        self.consensus.compute_consensus("test-consensus")

        exported = self.consensus.export_provenance("test-consensus")

        assert "validation_results" in exported

    def test_export_provenance_unknown_consensus(self):
        """Test export_provenance returns None for unknown consensus."""
        result = self.consensus.export_provenance("unknown-consensus")
        assert result is None

    def test_get_decision_provenance(self):
        """Test get_decision_provenance method."""
        self.consensus.start_consensus("test-consensus", domain="testing")
        self.consensus.add_vote("test-consensus", "agent-1", "approve", 0.8)

        provenance = self.consensus.get_decision_provenance("test-consensus")

        assert provenance is not None
        assert provenance.decision_id == "test-consensus"
        assert "agent-1" in provenance.participating_agents
        assert provenance.votes_cast == 1


class TestIntegrationPersistenceWithWeighting:
    """Test persistence works correctly with vote weighting."""

    def test_weighting_uses_persisted_expertise(self):
        """Test vote weighting uses expertise from loaded profiles."""
        # Create and save profiler state
        profiler = AgentExpertiseProfiler()
        profiler.register_agent("expert", domains=["testing"], initial_expertise=0.95)

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            temp_path = f.name

        try:
            profiler.save_to_file(temp_path)

            # Create new consensus with loaded profiler
            consensus = EnhancedMAKERConsensus()
            consensus.expertise_profiler.load_from_file(temp_path)
            consensus.start_consensus("test-consensus", domain="testing")

            # Create vote
            from heretek_swarm.consensus.maker_enhanced import EnhancedVote, Vote
            vote = Vote(
                agent_id="expert",
                decision="approve",
                confidence=0.8,
                timestamp=datetime.now(UTC).isoformat(),
            )
            enhanced_vote = EnhancedVote(vote=vote)

            # Calculate weight - should use loaded expertise
            weight = consensus.calculate_vote_weight(
                consensus_id="test-consensus",
                enhanced_vote=enhanced_vote,
                domain="testing",
            )

            # Expert should have high weight
            assert weight > 1.0

        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    def test_weighting_uses_persisted_accuracy_history(self):
        """Test vote weighting uses accuracy from loaded history."""
        # Create consensus and record history
        consensus1 = EnhancedMAKERConsensus()
        consensus1.start_consensus("test-consensus")
        consensus1.record_decision_outcome("test-consensus", "agent-1", was_correct=True)
        consensus1.record_decision_outcome("test-consensus", "agent-1", was_correct=True)
        consensus1.record_decision_outcome("test-consensus", "agent-1", was_correct=True)

        # Export and import
        exported = consensus1.export_accuracy_history()

        consensus2 = EnhancedMAKERConsensus()
        consensus2.start_consensus("test-consensus")
        consensus2.import_accuracy_history(exported)

        # Create vote
        from heretek_swarm.consensus.maker_enhanced import EnhancedVote, Vote
        vote = Vote(
            agent_id="agent-1",
            decision="approve",
            confidence=0.7,
            timestamp=datetime.now(UTC).isoformat(),
        )
        enhanced_vote = EnhancedVote(vote=vote)

        # Calculate weight - should use imported history
        weight = consensus2.calculate_vote_weight(
            consensus_id="test-consensus",
            enhanced_vote=enhanced_vote,
        )

        # Good history should boost weight
        assert weight > 0.7  # Higher than confidence alone
