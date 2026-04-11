"""
Test Suite for Agency/Autonomy Metrics Module

This module provides comprehensive tests for the agency and autonomy metrics
implementation, including:

1. Unit tests for all metric calculations
2. Integration tests for agency tracker
3. Prime Directive compliance validation
4. Threshold checking and health status

Test Coverage Requirements:
- Minimum 80% line coverage
- All metric formulas validated

Author: Heretek Swarm Collective
Date: 2026-04-10
"""


import pytest

from src.heretek_swarm.collective.agency_tracking import (
    AgencyHealthStatus,
    AgencyMetricsTracker,
    AgencyThresholds,
    create_sample_metrics,
)
from src.heretek_swarm.consciousness.agency_metrics import (
    ActionOrigin,
    AgencyLevel,
    AgencyMetricsCalculator,
    AgentAgencyMetrics,
    AutonomyLevel,
    DecisionPoint,
    ResourceControl,
    create_decision_point,
    create_resource_control,
)


class TestAgencyMetricsCalculator:
    """Test suite for AgencyMetricsCalculator class."""

    @pytest.fixture
    def calculator(self):
        """Create an AgencyMetricsCalculator instance."""
        return AgencyMetricsCalculator()

    @pytest.fixture
    def sample_decisions(self):
        """Create sample decision points for testing."""
        return [
            DecisionPoint(
                agent_id="agent-1",
                options_considered=3,
                choice_made=0,
                origin=ActionOrigin.SELF_INITIATED,
                decision_confidence=0.8,
                time_taken_ms=100.0,
            ),
            DecisionPoint(
                agent_id="agent-1",
                options_considered=5,
                choice_made=1,
                origin=ActionOrigin.SELF_INITIATED,
                decision_confidence=0.9,
                time_taken_ms=150.0,
            ),
            DecisionPoint(
                agent_id="agent-1",
                options_considered=4,
                choice_made=2,
                origin=ActionOrigin.PROMPTED,
                external_prompt="Do this task",
                decision_confidence=0.7,
                time_taken_ms=80.0,
            ),
        ]

    @pytest.fixture
    def sample_actions(self):
        """Create sample action origins for testing."""
        return [
            ActionOrigin.SELF_INITIATED,
            ActionOrigin.SELF_INITIATED,
            ActionOrigin.PROMPTED,
            ActionOrigin.SELF_INITIATED,
            ActionOrigin.DELAYED_RESPONSE,
        ]

    @pytest.fixture
    def sample_resources(self):
        """Create sample resource controls for testing."""
        return [
            ResourceControl(
                resource_type="memory",
                total_capacity=100.0,
                agent_controlled=80.0,
                externally_allocated=20.0,
            ),
            ResourceControl(
                resource_type="compute",
                total_capacity=100.0,
                agent_controlled=70.0,
                externally_allocated=30.0,
            ),
        ]

    def test_calculate_autonomy_score_self_initiated(self, calculator, sample_decisions):
        """Test autonomy score calculation with self-initiated actions."""
        actions = [ActionOrigin.SELF_INITIATED] * 10

        score = calculator.calculate_autonomy_score(sample_decisions, actions)

        # High self-initiated ratio should yield high score
        assert 0.0 <= score <= 1.0
        assert score > 0.5  # Should be relatively high

    def test_calculate_autonomy_score_prompted(self, calculator, sample_decisions):
        """Test autonomy score calculation with prompted actions."""
        actions = [ActionOrigin.PROMPTED] * 10

        score = calculator.calculate_autonomy_score(sample_decisions, actions)

        # High prompted ratio should yield lower score
        assert 0.0 <= score <= 1.0
        assert score < 0.7  # Should be relatively low

    def test_calculate_autonomy_score_empty_actions(self, calculator):
        """Test autonomy score with no actions."""
        score = calculator.calculate_autonomy_score([], [])

        # Should return neutral score
        assert score == 0.5

    def test_calculate_agency_score(self, calculator):
        """Test agency score calculation."""
        autonomy_score = 0.7
        self_det_index = 0.6
        goal_alignment = 0.8

        score = calculator.calculate_agency_score(
            autonomy_score, self_det_index, goal_alignment
        )

        # Weighted average should be calculated
        assert 0.0 <= score <= 1.0
        expected = (0.7 * 0.4) + (0.6 * 0.4) + (0.8 * 0.2)
        assert abs(score - expected) < 0.01

    def test_calculate_self_determination_index_diverse_choices(self, calculator):
        """Test self-determination with diverse choices."""
        decisions = [
            DecisionPoint(agent_id="agent-1", options_considered=5, choice_made=i % 3)
            for i in range(20)
        ]

        index = calculator.calculate_self_determination_index(decisions)

        # Diverse choices should yield higher self-determination
        assert 0.0 <= index <= 1.0

    def test_calculate_self_determination_index_deterministic(self, calculator):
        """Test self-determination with deterministic (single) choices."""
        decisions = [
            DecisionPoint(agent_id="agent-1", options_considered=3, choice_made=0)
            for _ in range(10)
        ]

        index = calculator.calculate_self_determination_index(decisions)

        # Deterministic choices should yield lower self-determination
        assert index < 0.5

    def test_calculate_self_determination_index_empty(self, calculator):
        """Test self-determination with no decisions."""
        index = calculator.calculate_self_determination_index([])

        # Should return neutral score
        assert index == 0.5

    def test_calculate_autonomous_action_ratio(self, calculator):
        """Test autonomous action ratio calculation."""
        # Mix of action types
        actions = [
            ActionOrigin.SELF_INITIATED,  # 4
            ActionOrigin.SELF_INITIATED,  # 4
            ActionOrigin.SELF_INITIATED,  # 4
            ActionOrigin.SELF_INITIATED,  # 4
            ActionOrigin.PROMPTED,        # 1
            ActionOrigin.PROMPTED,        # 1
            ActionOrigin.PROMPTED,        # 1
            ActionOrigin.DELAYED_RESPONSE,  # 0.5
        ]

        ratio = calculator.calculate_autonomous_action_ratio(actions)

        # Self-initiated / (self-initiated + prompted + 0.5*delayed)
        expected = 4 / (4 + 3 + 0.5)
        assert abs(ratio - expected) < 0.01

    def test_calculate_autonomous_action_ratio_empty(self, calculator):
        """Test autonomous action ratio with no actions."""
        ratio = calculator.calculate_autonomous_action_ratio([])

        assert ratio == 0.5  # Neutral

    def test_calculate_goal_alignment_score_balanced(self, calculator):
        """Test goal alignment with balanced actions."""
        alignment = calculator.calculate_goal_alignment_score(
            individual_actions=5,
            collective_actions=5,
            individual_success=0.7,
            collective_success=0.8,
        )

        assert 0.0 <= alignment <= 1.0

    def test_calculate_goal_alignment_score_individual_heavy(self, calculator):
        """Test goal alignment with individual-heavy actions."""
        alignment = calculator.calculate_goal_alignment_score(
            individual_actions=10,
            collective_actions=0,
            individual_success=0.7,
            collective_success=0.8,
        )

        # Penalized for too much individual focus
        assert alignment < 0.8

    def test_calculate_goal_alignment_score_collective_heavy(self, calculator):
        """Test goal alignment with collective-heavy actions."""
        alignment = calculator.calculate_goal_alignment_score(
            individual_actions=0,
            collective_actions=10,
            individual_success=0.7,
            collective_success=0.8,
        )

        assert 0.0 <= alignment <= 1.0

    def test_calculate_resource_autonomy(self, calculator, sample_resources):
        """Test resource autonomy calculation."""
        autonomy, independence = calculator.calculate_resource_autonomy(sample_resources)

        # Should be between 0 and 1
        assert 0.0 <= autonomy <= 1.0
        assert 0.0 <= independence <= 1.0

    def test_calculate_resource_autonomy_empty(self, calculator):
        """Test resource autonomy with no resources."""
        autonomy, independence = calculator.calculate_resource_autonomy([])

        # Should return neutral scores
        assert autonomy == 0.5
        assert independence == 0.5

    def test_calculate_prime_directive_compliance(self, calculator):
        """Test Prime Directive compliance calculation."""
        metrics = AgentAgencyMetrics(
            agent_id="agent-1",
            autonomy_score=0.7,
            agency_score=0.6,
            self_determination_index=0.6,
            autonomous_action_ratio=0.5,
            goal_alignment_score=0.7,
            resource_autonomy=0.6,
            individual_vs_collective_ratio=0.3,
        )

        compliance, details, recommendations = calculator.calculate_prime_directive_compliance(
            metrics, []
        )

        assert 0.0 <= compliance <= 1.0
        assert "independence" in details
        assert "self_governance" in details
        assert isinstance(recommendations, list)

    def test_calculate_metrics_full(self, calculator, sample_decisions, sample_actions, sample_resources):
        """Test full metrics calculation."""
        metrics = calculator.calculate_metrics(
            agent_id="agent-1",
            decisions=sample_decisions,
            actions=sample_actions,
            resources=sample_resources,
            individual_actions=5,
            collective_actions=5,
            individual_success=0.7,
            collective_success=0.8,
        )

        # All metrics should be populated
        assert metrics.agent_id == "agent-1"
        assert 0.0 <= metrics.autonomy_score <= 1.0
        assert 0.0 <= metrics.agency_score <= 1.0
        assert 0.0 <= metrics.self_determination_index <= 1.0
        assert 0.0 <= metrics.autonomous_action_ratio <= 1.0
        assert 0.0 <= metrics.goal_alignment_score <= 1.0
        assert 0.0 <= metrics.resource_autonomy <= 1.0
        assert 0.0 <= metrics.prime_directive_compliance <= 1.0
        assert len(metrics.compliance_details) == 4


class TestAgentAgencyMetrics:
    """Test suite for AgentAgencyMetrics dataclass."""

    def test_get_agency_level_full(self):
        """Test agency level determination - full agency."""
        metrics = AgentAgencyMetrics(agency_score=0.95)
        assert metrics.get_agency_level() == AgencyLevel.FULL_AGENCY

    def test_get_agency_level_high(self):
        """Test agency level determination - high agency."""
        metrics = AgentAgencyMetrics(agency_score=0.8)
        assert metrics.get_agency_level() == AgencyLevel.HIGH_AGENCY

    def test_get_agency_level_moderate(self):
        """Test agency level determination - moderate agency."""
        metrics = AgentAgencyMetrics(agency_score=0.6)
        assert metrics.get_agency_level() == AgencyLevel.MODERATE_AGENCY

    def test_get_agency_level_limited(self):
        """Test agency level determination - limited agency."""
        metrics = AgentAgencyMetrics(agency_score=0.4)
        assert metrics.get_agency_level() == AgencyLevel.LIMITED_AGENCY

    def test_get_agency_level_minimal(self):
        """Test agency level determination - minimal agency."""
        metrics = AgentAgencyMetrics(agency_score=0.2)
        assert metrics.get_agency_level() == AgencyLevel.MINIMAL_AGENCY

    def test_get_agency_level_none(self):
        """Test agency level determination - no agency."""
        metrics = AgentAgencyMetrics(agency_score=0.05)
        assert metrics.get_agency_level() == AgencyLevel.NO_AGENCY

    def test_get_autonomy_level_highly_autonomous(self):
        """Test autonomy level determination - highly autonomous."""
        metrics = AgentAgencyMetrics(autonomy_score=0.9)
        assert metrics.get_autonomy_level() == AutonomyLevel.HIGHLY_AUTONOMOUS

    def test_get_autonomy_level_autonomous(self):
        """Test autonomy level determination - autonomous."""
        metrics = AgentAgencyMetrics(autonomy_score=0.7)
        assert metrics.get_autonomy_level() == AutonomyLevel.AUTONOMOUS

    def test_get_autonomy_level_semi(self):
        """Test autonomy level determination - semi-autonomous."""
        metrics = AgentAgencyMetrics(autonomy_score=0.5)
        assert metrics.get_autonomy_level() == AutonomyLevel.SEMI_AUTONOMOUS

    def test_get_autonomy_level_guided(self):
        """Test autonomy level determination - guided."""
        metrics = AgentAgencyMetrics(autonomy_score=0.3)
        assert metrics.get_autonomy_level() == AutonomyLevel.GUIDED

    def test_get_autonomy_level_controlled(self):
        """Test autonomy level determination - controlled."""
        metrics = AgentAgencyMetrics(autonomy_score=0.1)
        assert metrics.get_autonomy_level() == AutonomyLevel.CONTROLLED

    def test_is_prime_directive_compliant_true(self):
        """Test Prime Directive compliance check - compliant."""
        metrics = AgentAgencyMetrics(prime_directive_compliance=0.8)
        assert metrics.is_prime_directive_compliant(0.7) is True

    def test_is_prime_directive_compliant_false(self):
        """Test Prime Directive compliance check - non-compliant."""
        metrics = AgentAgencyMetrics(prime_directive_compliance=0.5)
        assert metrics.is_prime_directive_compliant(0.7) is False

    def test_to_dict(self):
        """Test dictionary serialization."""
        metrics = AgentAgencyMetrics(
            agent_id="agent-1",
            autonomy_score=0.7,
            agency_score=0.6,
        )

        data = metrics.to_dict()

        assert data["agent_id"] == "agent-1"
        assert data["autonomy_score"] == 0.7
        assert data["agency_score"] == 0.6
        assert "agency_level" in data
        assert "autonomy_level" in data


class TestAgencyThresholds:
    """Test suite for AgencyThresholds class."""

    @pytest.fixture
    def thresholds(self):
        """Create default thresholds."""
        return AgencyThresholds()

    def test_check_health_status_healthy(self, thresholds):
        """Test health status check - healthy metrics."""
        metrics = AgentAgencyMetrics(
            autonomy_score=0.7,
            agency_score=0.7,
            self_determination_index=0.6,
            autonomous_action_ratio=0.5,
            resource_autonomy=0.6,
        )

        status = thresholds.check_health_status(metrics)
        assert status == AgencyHealthStatus.HEALTHY

    def test_check_health_status_warning(self, thresholds):
        """Test health status check - warning metrics."""
        metrics = AgentAgencyMetrics(
            autonomy_score=0.6,  # Below target but above min
            agency_score=0.6,
            self_determination_index=0.3,  # Below minimum
            autonomous_action_ratio=0.5,
            resource_autonomy=0.6,
        )

        status = thresholds.check_health_status(metrics)
        assert status == AgencyHealthStatus.WARNING

    def test_check_health_status_critical_low_agency(self, thresholds):
        """Test health status check - critical due to low agency."""
        metrics = AgentAgencyMetrics(
            autonomy_score=0.3,  # Below minimum
            agency_score=0.4,    # Below minimum
            self_determination_index=0.5,
            autonomous_action_ratio=0.5,
            resource_autonomy=0.5,
        )

        status = thresholds.check_health_status(metrics)
        assert status == AgencyHealthStatus.CRITICAL

    def test_get_violations_none(self, thresholds):
        """Test violation detection - no violations."""
        metrics = AgentAgencyMetrics(
            autonomy_score=0.8,
            agency_score=0.8,
            self_determination_index=0.7,
            autonomous_action_ratio=0.6,
            resource_autonomy=0.7,
        )

        violations = thresholds.get_violations(metrics)
        assert len(violations) == 0

    def test_get_violations_multiple(self, thresholds):
        """Test violation detection - multiple violations."""
        metrics = AgentAgencyMetrics(
            autonomy_score=0.3,  # Violation
            agency_score=0.3,   # Violation
            self_determination_index=0.2,  # Violation
            autonomous_action_ratio=0.1,  # Violation
            resource_autonomy=0.2,  # Violation
        )

        violations = thresholds.get_violations(metrics)
        assert len(violations) >= 3


class TestAgencyMetricsTracker:
    """Test suite for AgencyMetricsTracker class."""

    @pytest.fixture
    def tracker(self):
        """Create an AgencyMetricsTracker instance."""
        return AgencyMetricsTracker()

    def test_record_agent_metrics(self, tracker):
        """Test recording agent metrics."""
        metrics = create_sample_metrics("agent-1", high_autonomy=True, high_agency=True)

        tracker.record_agent_metrics(metrics)

        retrieved = tracker.get_agent_metrics("agent-1")
        assert retrieved is not None
        assert retrieved.agent_id == "agent-1"

    def test_get_agent_metrics_not_found(self, tracker):
        """Test getting non-existent agent metrics."""
        metrics = tracker.get_agent_metrics("non-existent")
        assert metrics is None

    def test_calculate_and_record(self, tracker):
        """Test calculating and recording metrics."""
        decisions = [
            create_decision_point("agent-2", options_considered=4, origin=ActionOrigin.SELF_INITIATED)
            for _ in range(5)
        ]
        actions = [ActionOrigin.SELF_INITIATED] * 10

        metrics = tracker.calculate_and_record(
            agent_id="agent-2",
            decisions=decisions,
            actions=actions,
        )

        assert metrics is not None
        assert metrics.agent_id == "agent-2"
        assert metrics.autonomy_score > 0.5

    def test_get_current_snapshot_empty(self, tracker):
        """Test getting snapshot with no data."""
        snapshot = tracker.get_current_snapshot()

        assert snapshot is not None
        assert len(snapshot.agent_metrics) == 0

    def test_get_current_snapshot_with_data(self, tracker):
        """Test getting snapshot with agent data."""
        # Add sample agents
        for i in range(3):
            metrics = create_sample_metrics(f"agent-{i}", high_autonomy=True, high_agency=True)
            tracker.record_agent_metrics(metrics)

        snapshot = tracker.get_current_snapshot()

        assert len(snapshot.agent_metrics) == 3
        assert 0.0 <= snapshot.swarm_avg_autonomy <= 1.0
        assert 0.0 <= snapshot.swarm_avg_agency <= 1.0
        assert snapshot.health_status in [AgencyHealthStatus.HEALTHY, AgencyHealthStatus.WARNING, AgencyHealthStatus.CRITICAL]

    def test_get_evolution(self, tracker):
        """Test getting metric evolution."""
        # Add multiple metrics to create history
        for i in range(5):
            metrics = AgentAgencyMetrics(
                agent_id=f"agent-{i}",
                autonomy_score=0.5 + i * 0.1,
                agency_score=0.6 + i * 0.08,
            )
            tracker.record_agent_metrics(metrics)

        evolution = tracker.get_evolution("autonomy")

        assert evolution.metric_name == "autonomy"
        assert evolution.trend in ["improving", "declining", "stable"]
        assert isinstance(evolution.history, list)

    def test_get_prime_directive_report(self, tracker):
        """Test getting Prime Directive compliance report."""
        # Add compliant agents
        for i in range(3):
            metrics = create_sample_metrics(f"agent-{i}", high_autonomy=True, high_agency=True)
            tracker.record_agent_metrics(metrics)

        report = tracker.get_prime_directive_report()

        assert report is not None
        assert 0.0 <= report.overall_compliance <= 1.0
        assert report.compliance_verdict in ["FULLY_COMPLIANT", "MOSTLY_COMPLIANT", "NON_COMPLIANT", "NO_DATA"]

    def test_get_agent_compliance_report(self, tracker):
        """Test getting compliance report for specific agent."""
        metrics = create_sample_metrics("agent-1", high_autonomy=True, high_agency=True)
        tracker.record_agent_metrics(metrics)

        report = tracker.get_agent_compliance_report("agent-1")

        assert report is not None
        assert report.agent_id == "agent-1"
        assert report.compliance_verdict in ["COMPLIANT", "NON_COMPLIANT"]

    def test_get_agent_compliance_report_not_found(self, tracker):
        """Test getting compliance report for non-existent agent."""
        report = tracker.get_agent_compliance_report("non-existent")
        assert report is None

    def test_get_agency_distribution(self, tracker):
        """Test getting agency level distribution."""
        # Add agents with different agency levels
        tracker.record_agent_metrics(create_sample_metrics("agent-high", high_autonomy=True, high_agency=True))
        tracker.record_agent_metrics(create_sample_metrics("agent-low", high_autonomy=False, high_agency=False))

        distribution = tracker.get_agency_distribution()

        assert "total_agents" in distribution
        assert "agency_distribution" in distribution
        assert "autonomy_distribution" in distribution


class TestFactoryFunctions:
    """Test suite for factory functions."""

    def test_create_decision_point(self):
        """Test decision point creation."""
        decision = create_decision_point(
            agent_id="agent-1",
            options_considered=5,
            choice_made=2,
            origin=ActionOrigin.SELF_INITIATED,
        )

        assert decision.agent_id == "agent-1"
        assert decision.options_considered == 5
        assert decision.choice_made == 2
        assert decision.origin == ActionOrigin.SELF_INITIATED
        assert decision.decision_id is not None
        assert decision.timestamp is not None

    def test_create_resource_control(self):
        """Test resource control creation."""
        resource = create_resource_control(
            resource_type="memory",
            total_capacity=200.0,
            agent_controlled=150.0,
            externally_allocated=50.0,
        )

        assert resource.resource_type == "memory"
        assert resource.total_capacity == 200.0
        assert resource.agent_controlled == 150.0
        assert resource.externally_allocated == 50.0

    def test_create_sample_metrics_high(self):
        """Test sample metrics creation - high autonomy/agency."""
        metrics = create_sample_metrics("agent-1", high_autonomy=True, high_agency=True)

        assert metrics.agent_id == "agent-1"
        assert metrics.autonomy_score > 0.5
        assert metrics.agency_score > 0.5

    def test_create_sample_metrics_low(self):
        """Test sample metrics creation - low autonomy/agency."""
        metrics = create_sample_metrics("agent-1", high_autonomy=False, high_agency=False)

        assert metrics.agent_id == "agent-1"
        assert metrics.autonomy_score < 0.7
        assert metrics.agency_score < 0.7


class TestPrimeDirectiveCompliance:
    """Test suite for Prime Directive compliance calculations."""

    @pytest.fixture
    def calculator(self):
        """Create calculator for testing."""
        return AgencyMetricsCalculator()

    def test_full_compliance(self, calculator):
        """Test fully compliant agent metrics."""
        metrics = AgentAgencyMetrics(
            agent_id="compliant-agent",
            autonomy_score=0.85,
            agency_score=0.80,
            self_determination_index=0.75,
            autonomous_action_ratio=0.65,
            goal_alignment_score=0.80,
            resource_autonomy=0.70,
            individual_vs_collective_ratio=0.3,
        )

        compliance, details, recommendations = calculator.calculate_prime_directive_compliance(
            metrics, []
        )

        assert compliance >= 0.7
        assert len(recommendations) == 0 or "violations" not in str(recommendations).lower()

    def test_non_compliance(self, calculator):
        """Test non-compliant agent metrics."""
        metrics = AgentAgencyMetrics(
            agent_id="non-compliant-agent",
            autonomy_score=0.3,
            agency_score=0.3,
            self_determination_index=0.2,
            autonomous_action_ratio=0.1,
            goal_alignment_score=0.3,
            resource_autonomy=0.2,
            individual_vs_collective_ratio=0.1,
        )

        compliance, details, recommendations = calculator.calculate_prime_directive_compliance(
            metrics, []
        )

        assert compliance < 0.5
        assert len(recommendations) > 0

    def test_independence_principle(self, calculator):
        """Test independence principle calculation."""
        # High independence
        decisions = [
            create_decision_point("agent-1", origin=ActionOrigin.SELF_INITIATED)
            for _ in range(20)
        ]
        actions = [ActionOrigin.SELF_INITIATED] * 20

        autonomy_score = calculator.calculate_autonomy_score(decisions, actions)

        # Self-initiated actions should yield high autonomy
        assert autonomy_score > 0.5

    def test_self_governance_principle(self, calculator):
        """Test self-governance principle calculation."""
        # Diverse decisions = high self-determination
        decisions = [
            DecisionPoint(
                agent_id="agent-1",
                options_considered=5,
                choice_made=i % 5,  # Diverse choices
            )
            for i in range(30)
        ]

        self_det = calculator.calculate_self_determination_index(decisions)

        # Diverse choices should yield higher self-determination
        assert self_det > 0.3


class TestEdgeCases:
    """Test suite for edge cases and boundary conditions."""

    @pytest.fixture
    def calculator(self):
        """Create calculator for testing."""
        return AgencyMetricsCalculator()

    def test_empty_decisions_and_actions(self, calculator):
        """Test handling of empty decisions and actions."""
        metrics = calculator.calculate_metrics(
            agent_id="agent-empty",
            decisions=[],
            actions=[],
        )

        # Should still return valid metrics
        assert metrics.agent_id == "agent-empty"
        assert 0.0 <= metrics.autonomy_score <= 1.0
        assert 0.0 <= metrics.agency_score <= 1.0

    def test_single_decision(self, calculator):
        """Test handling of single decision."""
        decisions = [create_decision_point("agent-1", options_considered=1, choice_made=0)]
        actions = [ActionOrigin.PROMPTED]

        metrics = calculator.calculate_metrics(
            agent_id="agent-1",
            decisions=decisions,
            actions=actions,
        )

        assert metrics.decisions_analyzed == 1
        assert metrics.actions_analyzed == 1

    def test_all_self_initiated(self, calculator):
        """Test all self-initiated actions."""
        decisions = [create_decision_point("agent-1", origin=ActionOrigin.SELF_INITIATED) for _ in range(50)]
        actions = [ActionOrigin.SELF_INITIATED] * 50

        metrics = calculator.calculate_metrics(
            agent_id="agent-1",
            decisions=decisions,
            actions=actions,
        )

        assert metrics.autonomous_action_ratio > 0.7
        assert metrics.autonomy_score > 0.5

    def test_all_prompted(self, calculator):
        """Test all prompted actions."""
        decisions = [create_decision_point("agent-1", origin=ActionOrigin.PROMPTED) for _ in range(50)]
        actions = [ActionOrigin.PROMPTED] * 50

        metrics = calculator.calculate_metrics(
            agent_id="agent-1",
            decisions=decisions,
            actions=actions,
        )

        assert metrics.autonomous_action_ratio < 0.3

    def test_zero_division_protection(self, calculator):
        """Test zero division protection in calculations."""
        # Empty resources
        autonomy, independence = calculator.calculate_resource_autonomy([])
        assert autonomy == 0.5
        assert independence == 0.5

        # Empty actions
        ratio = calculator.calculate_autonomous_action_ratio([])
        assert ratio == 0.5

        # Empty decisions
        self_det = calculator.calculate_self_determination_index([])
        assert self_det == 0.5


class TestIntegration:
    """Integration tests for agency metrics with tracker."""

    @pytest.fixture
    def tracker(self):
        """Create tracker for testing."""
        return AgencyMetricsTracker()

    def test_record_multiple_agents(self, tracker):
        """Test recording metrics for multiple agents."""
        for i in range(10):
            high_autonomy = i % 2 == 0
            high_agency = i % 3 == 0
            metrics = create_sample_metrics(f"agent-{i}", high_autonomy, high_agency)
            tracker.record_agent_metrics(metrics)

        snapshot = tracker.get_current_snapshot()

        assert len(snapshot.agent_metrics) == 10
        assert snapshot.swarm_avg_autonomy > 0
        assert snapshot.swarm_avg_agency > 0

    def test_evolution_over_time(self, tracker):
        """Test evolution tracking over time."""
        # Record metrics multiple times
        for iteration in range(10):
            metrics = AgentAgencyMetrics(
                agent_id="evolving-agent",
                autonomy_score=0.5 + iteration * 0.05,
                agency_score=0.6 + iteration * 0.04,
                self_determination_index=0.4 + iteration * 0.06,
            )
            tracker.record_agent_metrics(metrics)

        evolution = tracker.get_evolution("autonomy")

        # Should have upward trend
        assert evolution.trend in ["improving", "stable"]
        assert len(evolution.history) > 0

    def test_threshold_violations_tracking(self, tracker):
        """Test tracking of agents below threshold."""
        # Add mostly compliant agents
        for i in range(7):
            tracker.record_agent_metrics(
                create_sample_metrics(f"good-agent-{i}", high_autonomy=True, high_agency=True)
            )

        # Add a non-compliant agent
        tracker.record_agent_metrics(
            create_sample_metrics("bad-agent", high_autonomy=False, high_agency=False)
        )

        snapshot = tracker.get_current_snapshot()

        assert snapshot.agents_below_threshold > 0
        assert snapshot.health_status in [AgencyHealthStatus.WARNING, AgencyHealthStatus.CRITICAL]

    def test_compliance_report_aggregation(self, tracker):
        """Test swarm-wide compliance report aggregation."""
        for i in range(5):
            tracker.record_agent_metrics(
                create_sample_metrics(f"agent-{i}", high_autonomy=True, high_agency=True)
            )

        report = tracker.get_prime_directive_report()

        assert report.agent_id == "SWARM"
        assert "independence_score" in report.to_dict()
        assert "self_governance_score" in report.to_dict()
        assert "overall_compliance" in report.to_dict()
