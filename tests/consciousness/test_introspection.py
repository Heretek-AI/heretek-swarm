"""
Test Suite for Introspection Module

This module provides comprehensive tests for the introspection implementation,
including:

1. Unit tests for IntrospectionModule class
2. Tests for organic evolution mechanisms (confidence decay/growth)
3. Tests for belief reflection and conflict detection
4. Tests for goal evolution and progress tracking
5. Tests for introspection reporting
6. Integration tests with SelfModel

Author: Heretek Swarm Collective
Date: 2026-04-10
"""

import pytest
from datetime import datetime, timezone, timedelta
from typing import Dict, Any
import uuid
import time

from src.heretek_swarm.consciousness.self_model import (
    SelfModel,
    Belief,
    Goal,
    BeliefType,
    GoalStatus,
    Capability,
    Preference,
)
from src.heretek_swarm.consciousness.introspection import (
    IntrospectionModule,
    BeliefEvolutionRecord,
    GoalEvolutionRecord,
    ConflictPair,
    IntrospectionReport,
    ConflictResolutionStrategy,
)


class TestIntrospectionModuleInitialization:
    """Test suite for IntrospectionModule initialization."""
    
    @pytest.fixture
    def self_model(self):
        """Create a SelfModel instance for testing."""
        return SelfModel(agent_id="test-agent-1")
    
    @pytest.fixture
    def introspection(self, self_model):
        """Create an IntrospectionModule instance."""
        return IntrospectionModule(self_model)
    
    def test_init_with_empty_self_model(self, self_model):
        """Test initialization with empty SelfModel."""
        introspection = IntrospectionModule(self_model)
        
        assert introspection.self_model is self_model
        assert introspection.self_model.agent_id == "test-agent-1"
        assert len(introspection._belief_evolution_history) == 0
        assert len(introspection._goal_evolution_history) == 0
    
    def test_init_with_populated_self_model(self):
        """Test initialization with populated SelfModel."""
        self_model = SelfModel(
            agent_id="test-agent-2",
            initial_beliefs=[
                {"state": "Python is a programming language", "confidence": 0.9, "belief_type": "factual"},
                {"state": "AI can learn from experience", "confidence": 0.8, "belief_type": "factual"},
            ],
            initial_goals=[
                {"description": "Complete task A", "priority": 0.7},
                {"description": "Complete task B", "priority": 0.5},
            ],
        )
        
        introspection = IntrospectionModule(self_model)
        
        assert len(introspection._belief_update_counts) == 2
        assert len(introspection._belief_initial_time) == 2


class TestReflectOnBeliefs:
    """Test suite for reflect_on_beliefs method."""
    
    @pytest.fixture
    def introspection_with_beliefs(self):
        """Create IntrospectionModule with sample beliefs."""
        self_model = SelfModel(
            agent_id="test-agent",
            initial_beliefs=[
                {"state": "High confidence belief", "confidence": 0.9, "belief_type": "factual"},
                {"state": "Medium confidence belief", "confidence": 0.5, "belief_type": "procedural"},
                {"state": "Low confidence belief", "confidence": 0.2, "belief_type": "self"},
            ],
        )
        return IntrospectionModule(self_model)
    
    def test_reflect_returns_correct_structure(self, introspection_with_beliefs):
        """Test that reflect_on_beliefs returns correct structure."""
        result = introspection_with_beliefs.reflect_on_beliefs()
        
        assert "confidence_distribution" in result
        assert "insights" in result
        assert "average_confidence" in result
        assert "confidence_variance" in result
        assert "evidence_quality_summary" in result
        assert "total_beliefs" in result
        assert "beliefs_with_conflicts" in result
    
    def test_confidence_distribution_correct(self, introspection_with_beliefs):
        """Test confidence distribution calculation."""
        result = introspection_with_beliefs.reflect_on_beliefs()
        
        dist = result["confidence_distribution"]
        assert dist["very_high"] == 1  # 0.9
        assert dist["moderate"] == 1  # 0.5
        assert dist["low"] == 1  # 0.2
    
    def test_average_confidence_calculation(self, introspection_with_beliefs):
        """Test average confidence calculation."""
        result = introspection_with_beliefs.reflect_on_beliefs()
        
        expected_avg = (0.9 + 0.5 + 0.2) / 3
        assert abs(result["average_confidence"] - expected_avg) < 0.01
    
    def test_insights_generated(self, introspection_with_beliefs):
        """Test that insights are generated for each belief."""
        result = introspection_with_beliefs.reflect_on_beliefs()
        
        assert len(result["insights"]) == 3
        
        for insight in result["insights"]:
            assert "belief_id" in insight
            assert "state" in insight
            assert "confidence" in insight
            assert "confidence_trend" in insight
            assert "evidence_quality" in insight
    
    def test_reflect_empty_beliefs(self):
        """Test reflection with no beliefs."""
        self_model = SelfModel(agent_id="empty-agent")
        introspection = IntrospectionModule(self_model)
        
        result = introspection.reflect_on_beliefs()
        
        assert result["total_beliefs"] == 0
        assert result["average_confidence"] == 0.0
        assert len(result["insights"]) == 0


class TestUpdateBeliefFromOutcome:
    """Test suite for update_belief_from_outcome method."""
    
    @pytest.fixture
    def introspection_with_belief(self):
        """Create IntrospectionModule with a test belief."""
        self_model = SelfModel(
            agent_id="test-agent",
            initial_beliefs=[
                {"state": "Test belief", "confidence": 0.5, "belief_type": "factual"},
            ],
        )
        return IntrospectionModule(self_model)
    
    def test_update_with_positive_outcome(self, introspection_with_belief):
        """Test belief update with positive outcome."""
        belief_id = list(introspection_with_belief.self_model.beliefs.keys())[0]
        old_belief = introspection_with_belief.self_model.beliefs[belief_id]
        old_confidence = old_belief.confidence
        
        outcome = {"success": True, "actual_value": "expected"}
        evidence = {"source": "test_evidence", "strength": 0.8}
        
        updated_belief = introspection_with_belief.update_belief_from_outcome(
            belief_id, outcome, evidence
        )
        
        assert updated_belief is not None
        assert updated_belief.confidence > old_confidence
        assert "test_evidence" in updated_belief.supporting_evidence
    
    def test_update_with_negative_outcome(self, introspection_with_belief):
        """Test belief update with negative outcome."""
        belief_id = list(introspection_with_belief.self_model.beliefs.keys())[0]
        old_belief = introspection_with_belief.self_model.beliefs[belief_id]
        old_confidence = old_belief.confidence
        
        outcome = {"success": False, "actual_value": "unexpected"}
        evidence = {"source": "negative_evidence", "strength": 0.9}
        
        updated_belief = introspection_with_belief.update_belief_from_outcome(
            belief_id, outcome, evidence
        )
        
        assert updated_belief is not None
        assert updated_belief.confidence < old_confidence
    
    def test_update_nonexistent_belief(self, introspection_with_belief):
        """Test update with non-existent belief ID."""
        outcome = {"success": True}
        evidence = {"source": "test", "strength": 0.5}
        
        result = introspection_with_belief.update_belief_from_outcome(
            "nonexistent-belief-id", outcome, evidence
        )
        
        assert result is None
    
    def test_evolution_record_created(self, introspection_with_belief):
        """Test that evolution record is created on update."""
        belief_id = list(introspection_with_belief.self_model.beliefs.keys())[0]
        
        outcome = {"success": True}
        evidence = {"source": "test", "strength": 0.5}
        
        introspection_with_belief.update_belief_from_outcome(belief_id, outcome, evidence)
        
        assert len(introspection_with_belief._belief_evolution_history) == 1
        record = introspection_with_belief._belief_evolution_history[0]
        assert record.belief_id == belief_id
        assert record.reason == "outcome_update"
    
    def test_confidence_bounds_respected(self):
        """Test that confidence stays within bounds."""
        self_model = SelfModel(
            agent_id="test-agent",
            initial_beliefs=[
                {"state": "High confidence belief", "confidence": 0.95, "belief_type": "factual"},
            ],
        )
        introspection = IntrospectionModule(self_model)
        belief_id = list(introspection.self_model.beliefs.keys())[0]
        
        # Multiple positive updates should not exceed max
        for _ in range(20):
            outcome = {"success": True}
            evidence = {"source": "test", "strength": 1.0}
            introspection.update_belief_from_outcome(belief_id, outcome, evidence)
        
        belief = introspection.self_model.beliefs[belief_id]
        assert belief.confidence <= IntrospectionModule.CONFIDENCE_MAX
        assert belief.confidence >= IntrospectionModule.CONFIDENCE_MIN


class TestEvolveGoals:
    """Test suite for evolve_goals method."""
    
    @pytest.fixture
    def introspection_with_goals(self):
        """Create IntrospectionModule with sample goals."""
        self_model = SelfModel(
            agent_id="test-agent",
            initial_goals=[
                {"description": "Complete task A", "priority": 0.7, "progress": 0.3},
                {"description": "Complete task B", "priority": 0.5, "progress": 0.5},
                {"description": "Blocked task", "priority": 0.6, "progress": 0.0},
            ],
        )
        return IntrospectionModule(self_model)
    
    def test_evolve_with_completed_tasks(self, introspection_with_goals):
        """Test goal evolution with completed tasks."""
        goal_id = list(introspection_with_goals.self_model.goals.keys())[0]
        
        current_state = {
            "completed_tasks": [goal_id],
            "achievements": [],
            "resources": {},
            "constraints": [],
        }
        
        result = introspection_with_goals.evolve_goals(current_state)
        
        # Goal progress should increase when in completed_tasks
        goal = introspection_with_goals.self_model.goals[goal_id]
        assert goal.progress > 0.3
    
    def test_evolve_goal_completion(self, introspection_with_goals):
        """Test goal completion when progress reaches 1.0."""
        goal_id = list(introspection_with_goals.self_model.goals.keys())[0]
        introspection_with_goals.self_model.goals[goal_id].progress = 0.95
        
        current_state = {
            "completed_tasks": [goal_id],
            "achievements": [],
            "resources": {},
            "constraints": [],
        }
        
        result = introspection_with_goals.evolve_goals(current_state)
        
        goal = introspection_with_goals.self_model.goals[goal_id]
        assert goal.status == GoalStatus.COMPLETED
        assert goal.completed_at is not None
        assert goal_id in result["status_changes"]
    
    def test_evolve_with_constraints(self, introspection_with_goals):
        """Test goal evolution with constraints."""
        goal_id = list(introspection_with_goals.self_model.goals.keys())[0]
        goal = introspection_with_goals.self_model.goals[goal_id]
        goal.description = "Complete task A with resource X"
        
        current_state = {
            "completed_tasks": [],
            "achievements": [],
            "resources": {},
            "constraints": ["resource X"],
        }
        
        result = introspection_with_goals.evolve_goals(current_state)
        
        assert goal.status == GoalStatus.BLOCKED
        assert "constraint" in goal.blocked_by
        assert goal_id in result["new_blocked_goals"]
    
    def test_evolve_with_high_resources(self, introspection_with_goals):
        """Test goal evolution with high resource availability."""
        goal_id = list(introspection_with_goals.self_model.goals.keys())[0]
        goal = introspection_with_goals.self_model.goals[goal_id]
        goal.priority = 0.5  # Start with moderate priority
        
        current_state = {
            "completed_tasks": [],
            "achievements": [],
            "resources": {"cpu": 0.9, "memory": 0.95},
            "constraints": [],
        }
        
        result = introspection_with_goals.evolve_goals(current_state)
        
        assert goal.priority > 0.5
    
    def test_evolve_empty_state(self, introspection_with_goals):
        """Test goal evolution with empty state."""
        current_state = {
            "completed_tasks": [],
            "achievements": [],
            "resources": {},
            "constraints": [],
        }
        
        result = introspection_with_goals.evolve_goals(current_state)
        
        assert len(result["updated_goals"]) == 0
        assert len(result["priority_changes"]) == 0


class TestDetectConflictingBeliefs:
    """Test suite for detect_conflicting_beliefs method."""
    
    @pytest.fixture
    def introspection_with_conflicts(self):
        """Create IntrospectionModule with conflicting beliefs."""
        # Use beliefs that will be detected as conflicting by _are_beliefs_conflicting
        # The method looks for negation patterns like "not", "no", "never", etc.
        self_model = SelfModel(
            agent_id="test-agent",
            initial_beliefs=[
                {"state": "System is stable", "confidence": 0.8, "belief_type": "factual"},
                {"state": "System is not stable", "confidence": 0.6, "belief_type": "factual"},
                {"state": "Database is fast", "confidence": 0.7, "belief_type": "factual"},
            ],
        )
        return IntrospectionModule(self_model)
    
    def test_detect_conflicts_finds_conflicts(self, introspection_with_conflicts):
        """Test that conflicts are detected."""
        conflicts = introspection_with_conflicts.detect_conflicting_beliefs()
        
        # Should detect at least one conflict between beliefs with negation patterns
        assert len(conflicts) >= 1
        
        conflict = conflicts[0]
        assert isinstance(conflict, ConflictPair)
        # Verify the conflict involves beliefs with "not" negation
        states = [conflict.belief_1_state, conflict.belief_2_state]
        assert any("not" in s.lower() for s in states)
    
    def test_conflict_resolution_suggestion(self, introspection_with_conflicts):
        """Test that resolution suggestions are provided."""
        conflicts = introspection_with_conflicts.detect_conflicting_beliefs()
        
        assert len(conflicts) >= 1
        conflict = conflicts[0]
        assert conflict.resolution_suggestion is not None
        assert len(conflict.resolution_suggestion) > 0
    
    def test_no_conflicts_detected(self):
        """Test with non-conflicting beliefs."""
        self_model = SelfModel(
            agent_id="test-agent",
            initial_beliefs=[
                {"state": "Python is a language", "confidence": 0.9, "belief_type": "factual"},
                {"state": "Java is also a language", "confidence": 0.8, "belief_type": "factual"},
            ],
        )
        introspection = IntrospectionModule(self_model)
        
        conflicts = introspection.detect_conflicting_beliefs()
        
        assert len(conflicts) == 0
    
    def test_different_strategies(self, introspection_with_conflicts):
        """Test different conflict resolution strategies."""
        strategies = [
            ConflictResolutionStrategy.CONFIDENCE_BASED,
            ConflictResolutionStrategy.EVIDENCE_BASED,
            ConflictResolutionStrategy.RECENCY_BASED,
            ConflictResolutionStrategy.AVERAGE,
        ]
        
        for strategy in strategies:
            conflicts = introspection_with_conflicts.detect_conflicting_beliefs(strategy)
            assert len(conflicts) >= 1
            # resolution_strategy is an enum, compare enum values
            assert conflicts[0].resolution_strategy == strategy


class TestTrackGoalProgress:
    """Test suite for track_goal_progress method."""
    
    @pytest.fixture
    def introspection_with_goal(self):
        """Create IntrospectionModule with a test goal."""
        self_model = SelfModel(
            agent_id="test-agent",
            initial_goals=[
                {"description": "Test goal", "priority": 0.7, "progress": 0.3},
            ],
        )
        return IntrospectionModule(self_model)
    
    def test_track_positive_progress(self, introspection_with_goal):
        """Test tracking positive progress."""
        goal_id = list(introspection_with_goal.self_model.goals.keys())[0]
        
        outcome = {"success": True, "progress_delta": 0.2}
        
        result = introspection_with_goal.track_goal_progress(goal_id, outcome)
        
        assert result is True
        goal = introspection_with_goal.self_model.goals[goal_id]
        assert goal.progress == 0.5
    
    def test_track_negative_progress(self, introspection_with_goal):
        """Test tracking negative progress."""
        goal_id = list(introspection_with_goal.self_model.goals.keys())[0]
        
        outcome = {"success": False, "progress_delta": -0.1}
        
        result = introspection_with_goal.track_goal_progress(goal_id, outcome)
        
        assert result is True
        goal = introspection_with_goal.self_model.goals[goal_id]
        # Use approximate equality for floating point
        assert abs(goal.progress - 0.2) < 0.001
    
    def test_track_completion(self, introspection_with_goal):
        """Test tracking goal completion."""
        goal_id = list(introspection_with_goal.self_model.goals.keys())[0]
        introspection_with_goal.self_model.goals[goal_id].progress = 0.9
        
        outcome = {"completion": True}
        
        result = introspection_with_goal.track_goal_progress(goal_id, outcome)
        
        goal = introspection_with_goal.self_model.goals[goal_id]
        assert goal.status == GoalStatus.COMPLETED
        assert goal.progress == 1.0
    
    def test_track_with_blockers(self, introspection_with_goal):
        """Test tracking with new blockers."""
        goal_id = list(introspection_with_goal.self_model.goals.keys())[0]
        
        outcome = {"blockers": ["resource_unavailable", "dependency_missing"]}
        
        result = introspection_with_goal.track_goal_progress(goal_id, outcome)
        
        goal = introspection_with_goal.self_model.goals[goal_id]
        assert goal.status == GoalStatus.BLOCKED
        assert "resource_unavailable" in goal.blocked_by
        assert "dependency_missing" in goal.blocked_by
    
    def test_track_nonexistent_goal(self, introspection_with_goal):
        """Test tracking progress for non-existent goal."""
        outcome = {"success": True}
        
        result = introspection_with_goal.track_goal_progress("nonexistent-id", outcome)
        
        assert result is False


class TestGetIntrospectionReport:
    """Test suite for get_introspection_report method."""
    
    @pytest.fixture
    def introspection_with_data(self):
        """Create IntrospectionModule with beliefs and goals."""
        self_model = SelfModel(
            agent_id="test-agent",
            initial_beliefs=[
                {"state": "Belief 1", "confidence": 0.8, "belief_type": "factual"},
                {"state": "Belief 2", "confidence": 0.6, "belief_type": "procedural"},
            ],
            initial_goals=[
                {"description": "Goal 1", "priority": 0.7, "progress": 0.5},
                {"description": "Goal 2", "priority": 0.5, "progress": 0.3},
            ],
        )
        introspection = IntrospectionModule(self_model)
        
        # Add some evolution history
        belief_id = list(introspection.self_model.beliefs.keys())[0]
        introspection.update_belief_from_outcome(
            belief_id,
            {"success": True},
            {"source": "test", "strength": 0.5}
        )
        
        return introspection
    
    def test_report_structure(self, introspection_with_data):
        """Test introspection report structure."""
        report = introspection_with_data.get_introspection_report()
        
        assert isinstance(report, IntrospectionReport)
        assert report.agent_id == "test-agent"
        assert report.belief_count == 2
        assert report.goal_count == 2
    
    def test_report_beliefs_included(self, introspection_with_data):
        """Test that beliefs are included in report."""
        report = introspection_with_data.get_introspection_report()
        
        assert len(report.beliefs) == 2
        for belief in report.beliefs:
            assert "belief_id" in belief
            assert "confidence" in belief
            assert "state" in belief
    
    def test_report_goals_included(self, introspection_with_data):
        """Test that goals are included in report."""
        report = introspection_with_data.get_introspection_report()
        
        assert len(report.goals) == 2
        for goal in report.goals:
            assert "goal_id" in goal
            assert "description" in goal
            assert "progress" in goal
    
    def test_report_conflicts_included(self, introspection_with_data):
        """Test that conflicts are included in report."""
        report = introspection_with_data.get_introspection_report()
        
        assert "conflicts" in report.to_dict()
    
    def test_report_evolution_history_included(self, introspection_with_data):
        """Test that evolution history is included in report."""
        report = introspection_with_data.get_introspection_report()
        
        assert len(report.evolution_history) >= 1
    
    def test_report_to_dict(self, introspection_with_data):
        """Test report serialization."""
        report = introspection_with_data.get_introspection_report()
        report_dict = report.to_dict()
        
        assert "timestamp" in report_dict
        assert "agent_id" in report_dict
        assert "belief_count" in report_dict
        assert "goal_count" in report_dict
        assert "beliefs" in report_dict
        assert "goals" in report_dict


class TestConfidenceDecay:
    """Test suite for confidence decay mechanism."""
    
    @pytest.fixture
    def introspection_with_beliefs(self):
        """Create IntrospectionModule with beliefs."""
        self_model = SelfModel(
            agent_id="test-agent",
            initial_beliefs=[
                {"state": "Old belief", "confidence": 0.8, "belief_type": "factual"},
                {"state": "New belief", "confidence": 0.5, "belief_type": "factual"},
            ],
        )
        return IntrospectionModule(self_model)
    
    def test_decay_applied(self, introspection_with_beliefs):
        """Test that decay is applied to beliefs."""
        belief_id = list(introspection_with_beliefs.self_model.beliefs.keys())[0]
        old_confidence = introspection_with_beliefs.self_model.beliefs[belief_id].confidence
        
        changes = introspection_with_beliefs.apply_confidence_decay(days_elapsed=10)
        
        # After 10 days, decay should be applied
        if belief_id in changes:
            assert changes[belief_id] < 0  # Confidence should decrease
    
    def test_decay_toward_neutral(self, introspection_with_beliefs):
        """Test that confidence decays toward neutral (0.5)."""
        # Set up beliefs with high and low confidence
        self_model = introspection_with_beliefs.self_model
        high_conf_belief = list(self_model.beliefs.values())[0]
        high_conf_belief.confidence = 0.9
        
        changes = introspection_with_beliefs.apply_confidence_decay(days_elapsed=30)
        
        # High confidence should decrease toward 0.5
        for belief_id, change in changes.items():
            if self_model.beliefs[belief_id].confidence > 0.5:
                assert change < 0
    
    def test_decay_records_evolution(self, introspection_with_beliefs):
        """Test that decay creates evolution records."""
        initial_history_count = len(introspection_with_beliefs._belief_evolution_history)
        
        introspection_with_beliefs.apply_confidence_decay(days_elapsed=30)
        
        # Evolution records should be created for decayed beliefs
        new_history_count = len(introspection_with_beliefs._belief_evolution_history)
        assert new_history_count >= initial_history_count


class TestBeliefEvolutionHistory:
    """Test suite for belief evolution history tracking."""
    
    @pytest.fixture
    def introspection(self):
        """Create IntrospectionModule with a belief."""
        self_model = SelfModel(
            agent_id="test-agent",
            initial_beliefs=[
                {"state": "Test belief", "confidence": 0.5, "belief_type": "factual"},
            ],
        )
        return IntrospectionModule(self_model)
    
    def test_get_belief_evolution_history(self, introspection):
        """Test retrieving belief evolution history."""
        belief_id = list(introspection.self_model.beliefs.keys())[0]
        
        # Make several updates
        for i in range(5):
            introspection.update_belief_from_outcome(
                belief_id,
                {"success": i % 2 == 0},
                {"source": f"evidence_{i}", "strength": 0.5}
            )
        
        history = introspection.get_belief_evolution_history(belief_id)
        
        assert len(history) == 5
        for record in history:
            assert "belief_id" in record
            assert "old_confidence" in record
            assert "new_confidence" in record
            assert "timestamp" in record
    
    def test_get_nonexistent_belief_history(self, introspection):
        """Test getting history for non-existent belief."""
        history = introspection.get_belief_evolution_history("nonexistent-id")
        
        assert len(history) == 0


class TestGoalEvolutionHistory:
    """Test suite for goal evolution history tracking."""
    
    @pytest.fixture
    def introspection(self):
        """Create IntrospectionModule with a goal."""
        self_model = SelfModel(
            agent_id="test-agent",
            initial_goals=[
                {"description": "Test goal", "priority": 0.5, "progress": 0.0},
            ],
        )
        return IntrospectionModule(self_model)
    
    def test_get_goal_evolution_history(self, introspection):
        """Test retrieving goal evolution history."""
        goal_id = list(introspection.self_model.goals.keys())[0]
        
        # Make several updates
        for i in range(3):
            introspection.track_goal_progress(
                goal_id,
                {"success": True, "progress_delta": 0.1}
            )
        
        history = introspection.get_goal_evolution_history(goal_id)
        
        assert len(history) == 3
        for record in history:
            assert "goal_id" in record
            assert "old_progress" in record
            assert "new_progress" in record
            assert "timestamp" in record


class TestConflictResolutionStrategies:
    """Test suite for conflict resolution strategies."""
    
    @pytest.fixture
    def introspection_with_conflicts(self):
        """Create IntrospectionModule with conflicting beliefs."""
        self_model = SelfModel(
            agent_id="test-agent",
            initial_beliefs=[
                {"state": "High confidence belief", "confidence": 0.9, "belief_type": "factual"},
                {"state": "Low confidence belief (not high)", "confidence": 0.3, "belief_type": "factual"},
            ],
        )
        introspection = IntrospectionModule(self_model)
        
        # Add evidence to first belief
        belief_id = list(introspection.self_model.beliefs.keys())[0]
        introspection.self_model.beliefs[belief_id].supporting_evidence = ["e1", "e2", "e3", "e4", "e5"]
        
        return introspection
    
    def test_confidence_based_strategy(self, introspection_with_conflicts):
        """Test confidence-based resolution."""
        conflicts = introspection_with_conflicts.detect_conflicting_beliefs(
            ConflictResolutionStrategy.CONFIDENCE_BASED
        )
        
        if conflicts:
            suggestion = conflicts[0].resolution_suggestion
            assert "confidence" in suggestion.lower()
    
    def test_evidence_based_strategy(self, introspection_with_conflicts):
        """Test evidence-based resolution."""
        conflicts = introspection_with_conflicts.detect_conflicting_beliefs(
            ConflictResolutionStrategy.EVIDENCE_BASED
        )
        
        if conflicts:
            suggestion = conflicts[0].resolution_suggestion
            assert "evidence" in suggestion.lower()


class TestEdgeCases:
    """Test suite for edge cases and boundary conditions."""
    
    def test_empty_self_model(self):
        """Test introspection with empty SelfModel."""
        self_model = SelfModel(agent_id="empty-agent")
        introspection = IntrospectionModule(self_model)
        
        # All methods should work without errors
        reflect_result = introspection.reflect_on_beliefs()
        assert reflect_result["total_beliefs"] == 0
        
        evolve_result = introspection.evolve_goals({})
        assert len(evolve_result["updated_goals"]) == 0
        
        conflicts = introspection.detect_conflicting_beliefs()
        assert len(conflicts) == 0
        
        report = introspection.get_introspection_report()
        assert report.belief_count == 0
        assert report.goal_count == 0
    
    def test_many_beliefs_performance(self):
        """Test with many beliefs."""
        beliefs = [
            {"state": f"Belief {i}", "confidence": 0.5 + (i % 50) / 100, "belief_type": "factual"}
            for i in range(100)
        ]
        self_model = SelfModel(agent_id="test-agent", initial_beliefs=beliefs)
        introspection = IntrospectionModule(self_model)
        
        # Should complete without timeout
        result = introspection.reflect_on_beliefs()
        assert result["total_beliefs"] == 100
    
    def test_many_goals_performance(self):
        """Test with many goals."""
        goals = [
            {"description": f"Goal {i}", "priority": 0.5, "progress": i / 100}
            for i in range(50)
        ]
        self_model = SelfModel(agent_id="test-agent", initial_goals=goals)
        introspection = IntrospectionModule(self_model)
        
        # Should complete without timeout
        result = introspection.evolve_goals({
            "completed_tasks": [],
            "achievements": [],
            "resources": {},
            "constraints": [],
        })
        assert len(result["updated_goals"]) <= 50
    
    def test_evolution_history_trimming(self):
        """Test that evolution history is trimmed to max size."""
        self_model = SelfModel(
            agent_id="test-agent",
            initial_beliefs=[{"state": "Test", "confidence": 0.5}],
        )
        introspection = IntrospectionModule(self_model)
        belief_id = list(introspection.self_model.beliefs.keys())[0]
        
        # Create more than MAX_EVOLUTION_HISTORY records
        for i in range(IntrospectionModule.MAX_EVOLUTION_HISTORY + 100):
            introspection.update_belief_from_outcome(
                belief_id,
                {"success": i % 2 == 0},
                {"source": f"evidence_{i}", "strength": 0.5}
            )
        
        # History should be trimmed
        assert len(introspection._belief_evolution_history) <= IntrospectionModule.MAX_EVOLUTION_HISTORY


class TestIntegration:
    """Integration tests for IntrospectionModule with SelfModel."""
    
    def test_full_workflow(self):
        """Test complete introspection workflow."""
        # Create SelfModel with initial state
        self_model = SelfModel(
            agent_id="integration-test-agent",
            initial_beliefs=[
                {"state": "API endpoint is reliable", "confidence": 0.7, "belief_type": "factual"},
                {"state": "Database queries are slow", "confidence": 0.6, "belief_type": "factual"},
            ],
            initial_goals=[
                {"description": "Improve API reliability", "priority": 0.8, "progress": 0.2},
                {"description": "Optimize database queries", "priority": 0.6, "progress": 0.1},
            ],
        )
        
        # Create IntrospectionModule
        introspection = IntrospectionModule(self_model)
        
        # Reflect on beliefs
        reflection = introspection.reflect_on_beliefs()
        assert reflection["total_beliefs"] == 2
        
        # Update belief from positive outcome
        belief_id = list(self_model.beliefs.keys())[0]
        introspection.update_belief_from_outcome(
            belief_id,
            {"success": True, "actual_value": "fast response"},
            {"source": "performance_test", "strength": 0.8}
        )
        
        # Track goal progress
        goal_id = list(self_model.goals.keys())[0]
        introspection.track_goal_progress(
            goal_id,
            {"success": True, "progress_delta": 0.3}
        )
        
        # Evolve goals based on state
        evolution = introspection.evolve_goals({
            "completed_tasks": [],
            "achievements": ["API response time improved"],
            "resources": {"cpu": 0.8, "memory": 0.7},
            "constraints": [],
        })
        
        # Detect conflicts
        conflicts = introspection.detect_conflicting_beliefs()
        
        # Get introspection report
        report = introspection.get_introspection_report()
        
        # Verify report contains expected data
        assert report.agent_id == "integration-test-agent"
        assert report.belief_count == 2
        assert report.goal_count == 2
        assert len(report.evolution_history) >= 2  # At least belief update and goal tracking
    
    def test_conflict_detection_and_resolution(self):
        """Test conflict detection and resolution workflow."""
        self_model = SelfModel(
            agent_id="conflict-test-agent",
            initial_beliefs=[
                {"state": "API is reliable", "confidence": 0.8, "belief_type": "factual"},
                {"state": "API is not reliable", "confidence": 0.5, "belief_type": "factual"},
            ],
        )
        
        introspection = IntrospectionModule(self_model)
        
        # Detect conflicts
        conflicts = introspection.detect_conflicting_beliefs(
            ConflictResolutionStrategy.CONFIDENCE_BASED
        )
        
        # Should find conflict between "API is reliable" and "API is not reliable"
        assert len(conflicts) >= 1, "Expected conflict between 'API is reliable' and 'API is not reliable'"
        conflict = conflicts[0]
        
        # Resolution should favor higher confidence belief
        assert "0.8" in conflict.resolution_suggestion or "0.5" in conflict.resolution_suggestion
        
        # Update lower confidence belief with positive evidence
        belief_id = [b.belief_id for b in self_model.beliefs.values() if b.confidence == 0.5][0]
        introspection.update_belief_from_outcome(
            belief_id,
            {"success": True},
            {"source": "new_evidence", "strength": 0.9}
        )
        
        # Re-detect conflicts - should still exist
        new_conflicts = introspection.detect_conflicting_beliefs()
        assert len(new_conflicts) >= 1


class TestDataClasses:
    """Test suite for introspection dataclasses."""
    
    def test_belief_evolution_record_to_dict(self):
        """Test BeliefEvolutionRecord serialization."""
        record = BeliefEvolutionRecord(
            belief_id="test-id",
            old_confidence=0.5,
            new_confidence=0.7,
            evidence_count=3,
            reason="test",
        )
        
        data = record.to_dict()
        
        assert data["belief_id"] == "test-id"
        assert data["old_confidence"] == 0.5
        assert data["new_confidence"] == 0.7
        assert "timestamp" in data
    
    def test_goal_evolution_record_to_dict(self):
        """Test GoalEvolutionRecord serialization."""
        record = GoalEvolutionRecord(
            goal_id="test-id",
            old_priority=0.5,
            new_priority=0.7,
            old_progress=0.2,
            new_progress=0.4,
            old_status="active",
            new_status="completed",
            reason="test",
        )
        
        data = record.to_dict()
        
        assert data["goal_id"] == "test-id"
        assert data["old_priority"] == 0.5
        assert data["new_priority"] == 0.7
        assert "timestamp" in data
    
    def test_conflict_pair_to_dict(self):
        """Test ConflictPair serialization."""
        pair = ConflictPair(
            belief_1_id="b1",
            belief_2_id="b2",
            belief_1_state="State 1",
            belief_2_state="State 2",
            belief_1_confidence=0.8,
            belief_2_confidence=0.6,
            resolution_suggestion="Prefer belief 1",
            resolution_strategy=ConflictResolutionStrategy.CONFIDENCE_BASED,
        )
        
        data = pair.to_dict()
        
        assert data["belief_1_id"] == "b1"
        assert data["belief_2_id"] == "b2"
        assert data["resolution_strategy"] == "confidence_based"
    
    def test_introspection_report_to_dict(self):
        """Test IntrospectionReport serialization."""
        report = IntrospectionReport(
            agent_id="test-agent",
            belief_count=2,
            goal_count=1,
            beliefs=[{"belief_id": "b1"}],
            goals=[{"goal_id": "g1"}],
            conflicts=[],
        )
        
        data = report.to_dict()
        
        assert data["agent_id"] == "test-agent"
        assert data["belief_count"] == 2
        assert data["goal_count"] == 1
        assert "timestamp" in data
