"""
Comprehensive Tests for Session 46: Emergent Intelligence Enhancement

Tests for:
- Adaptive Learning Rate Controller
- Pattern-Based Agent Adaptor
- Emergent Pattern Detector
- Collective Intelligence Metrics

All tests follow zero-trust principles and include validation checks.
"""

import asyncio

import pytest

from heretek_swarm.collective import (
    AdaptationStrategy,
    AdaptationTarget,
    AdaptiveLearningRateController,
    CollectiveIntelligenceMetrics,
    EmergenceDetectionConfig,
    EmergentPatternDetector,
    LearningRateConfig,
    LearningRateStrategy,
    PatternBasedAgentAdaptor,
)
from heretek_swarm.collective.adaptive_learning import (
    ConvergenceMetrics,
)
from heretek_swarm.collective.emergent_detection import (
    AgentBehaviorSnapshot,
    CollectiveBehavior,
)
from heretek_swarm.collective.learning import (
    ExtractedPattern,
    PatternMetadata,
    PatternSource,
    PatternType,
)
from heretek_swarm.collective.metrics import (
    CollectiveEfficiencyMetrics,
    EmergenceCoefficient,
    KnowledgeTransferMetrics,
    MetricsDashboard,
    SwarmIntelligenceQuotient,
)

# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def sample_pattern() -> ExtractedPattern:
    """Create a sample extracted pattern for testing."""
    return ExtractedPattern(
        metadata=PatternMetadata(
            pattern_id="test-pattern-001",
            pattern_type=PatternType.SUCCESS,
            source=PatternSource.MESSAGE_HISTORY,
            confidence=0.85,
            support_count=5,
            agents_involved=["agent-1", "agent-2", "agent-3"],
            topics=["coordination", "optimization"],
            tags=["success", "collaboration"],
        ),
        pattern_data={
            "behavioral_weights": {
                "cooperation": 0.8,
                "efficiency": 0.7,
            },
            "strategy": {
                "name": "collaborative_optimization",
                "priority": 0.9,
            },
        },
        context={
            "environment": "test",
            "task_complexity": "high",
        },
        outcomes=[
            {"success": True, "efficiency_gain": 0.25},
        ],
        preconditions=["agents_available", "communication_channel_open"],
        postconditions=["task_completed", "knowledge_shared"],
    )


@pytest.fixture
def failure_pattern() -> ExtractedPattern:
    """Create a sample failure pattern for testing."""
    return ExtractedPattern(
        metadata=PatternMetadata(
            pattern_id="test-pattern-failure-001",
            pattern_type=PatternType.FAILURE,
            source=PatternSource.ERROR_LOG,
            confidence=0.75,
            support_count=3,
            agents_involved=["agent-1", "agent-2"],
            topics=["error", "recovery"],
            tags=["failure", "avoid"],
        ),
        pattern_data={
            "error_type": "communication_failure",
            "recovery_strategy": "retry_with_backoff",
        },
        context={
            "environment": "test",
            "error_severity": "medium",
        },
        outcomes=[
            {"success": False, "recovery_time": 5.0},
        ],
    )


@pytest.fixture
def adaptive_controller() -> AdaptiveLearningRateController:
    """Create an adaptive learning rate controller for testing."""
    config = LearningRateConfig(
        initial_rate=0.1,
        min_rate=0.001,
        max_rate=1.0,
        strategy=LearningRateStrategy.ADAPTIVE,
        success_boost=0.1,
        failure_penalty=0.2,
        validation_required=False,  # Disable for testing
    )
    return AdaptiveLearningRateController(config=config)


@pytest.fixture
def agent_adaptor() -> PatternBasedAgentAdaptor:
    """Create a pattern-based agent adaptor for testing."""
    return PatternBasedAgentAdaptor(
        default_strategy=AdaptationStrategy.GRADUAL,
        validation_required=False,  # Disable for testing
    )


@pytest.fixture
def emergence_detector() -> EmergentPatternDetector:
    """Create an emergent pattern detector for testing."""
    config = EmergenceDetectionConfig(
        min_emergence_score=0.3,
        min_participating_agents=2,
        min_coherence=0.5,
        validation_required=False,  # Disable for testing
    )
    return EmergentPatternDetector(config=config)


@pytest.fixture
def collective_metrics(
    adaptive_controller,
    agent_adaptor,
    emergence_detector,
) -> CollectiveIntelligenceMetrics:
    """Create collective intelligence metrics for testing."""
    return CollectiveIntelligenceMetrics(
        learning_controller=adaptive_controller,
        agent_adaptor=agent_adaptor,
        emergence_detector=emergence_detector,
    )


# =============================================================================
# Adaptive Learning Rate Controller Tests
# =============================================================================

class TestAdaptiveLearningRateController:
    """Tests for AdaptiveLearningRateController."""

    def test_initialization(self, adaptive_controller):
        """Test controller initialization."""
        assert adaptive_controller.config.initial_rate == 0.1
        assert adaptive_controller.config.min_rate == 0.001
        assert adaptive_controller.config.max_rate == 1.0
        assert adaptive_controller.config.strategy == LearningRateStrategy.ADAPTIVE

    def test_get_or_create_state(self, adaptive_controller):
        """Test state creation for new agent."""
        agent_id = "test-agent-001"
        state = adaptive_controller.get_or_create_state(agent_id)

        assert state.agent_id == agent_id
        assert state.current_rate == 0.1
        assert state.initial_rate == 0.1
        assert state.total_updates == 0
        assert state.success_rate == 0.0

    def test_record_update_success(self, adaptive_controller):
        """Test recording successful update."""
        agent_id = "test-agent-001"

        asyncio.run(adaptive_controller.record_update(agent_id, success=True))

        state = adaptive_controller.get_agent_state(agent_id)
        assert state.total_updates == 1
        assert state.successful_updates == 1
        assert state.failed_updates == 0
        assert state.success_rate == 1.0

    def test_record_update_failure(self, adaptive_controller):
        """Test recording failed update."""
        agent_id = "test-agent-001"

        asyncio.run(adaptive_controller.record_update(agent_id, success=False))

        state = adaptive_controller.get_agent_state(agent_id)
        assert state.total_updates == 1
        assert state.successful_updates == 0
        assert state.failed_updates == 1
        assert state.success_rate == 0.0

    def test_learning_rate_adjustment_on_success(self, adaptive_controller):
        """Test learning rate increases on success."""
        agent_id = "test-agent-001"
        initial_rate = adaptive_controller.get_current_rate(agent_id)

        asyncio.run(adaptive_controller.record_update(agent_id, success=True))

        new_rate = adaptive_controller.get_current_rate(agent_id)
        assert new_rate >= initial_rate  # Should increase or stay same

    def test_learning_rate_adjustment_on_failure(self, adaptive_controller):
        """Test learning rate decreases on failure."""
        agent_id = "test-agent-001"
        initial_rate = adaptive_controller.get_current_rate(agent_id)

        asyncio.run(adaptive_controller.record_update(agent_id, success=False))

        new_rate = adaptive_controller.get_current_rate(agent_id)
        assert new_rate <= initial_rate  # Should decrease or stay same

    async def test_adopt_success_pattern(self, adaptive_controller, sample_pattern):
        """Test adopting a success pattern."""
        agent_id = "test-agent-001"
        initial_rate = adaptive_controller.get_current_rate(agent_id)

        result = await adaptive_controller.adopt_pattern(agent_id, sample_pattern)

        assert result is True
        state = adaptive_controller.get_agent_state(agent_id)
        assert sample_pattern.metadata.pattern_id in state.adopted_patterns

        # Rate should increase due to success pattern
        new_rate = adaptive_controller.get_current_rate(agent_id)
        assert new_rate >= initial_rate

    async def test_adopt_failure_pattern(self, adaptive_controller, failure_pattern):
        """Test adopting (avoiding) a failure pattern."""
        agent_id = "test-agent-001"
        initial_rate = adaptive_controller.get_current_rate(agent_id)

        result = await adaptive_controller.adopt_pattern(agent_id, failure_pattern)

        assert result is True  # Still returns True as pattern was recorded
        state = adaptive_controller.get_agent_state(agent_id)
        assert failure_pattern.metadata.pattern_id in state.avoided_patterns

        # Rate should decrease due to failure pattern
        new_rate = adaptive_controller.get_current_rate(agent_id)
        assert new_rate <= initial_rate

    def test_get_swarm_statistics(self, adaptive_controller):
        """Test swarm statistics calculation."""
        # Create multiple agents with different states
        asyncio.run(adaptive_controller.record_update("agent-1", success=True))
        asyncio.run(adaptive_controller.record_update("agent-2", success=True))
        asyncio.run(adaptive_controller.record_update("agent-3", success=False))

        stats = adaptive_controller.get_swarm_statistics()

        assert stats["total_agents"] == 3
        assert stats["total_adaptations"] > 0
        assert "avg_learning_rate" in stats
        assert "avg_success_rate" in stats

    def test_convergence_metrics(self, adaptive_controller):
        """Test convergence metrics tracking."""
        agent_id = "test-agent-001"

        # Record multiple updates
        for _ in range(20):
            asyncio.run(adaptive_controller.record_update(agent_id, success=True))

        metrics = adaptive_controller.get_convergence_metrics(agent_id)
        assert isinstance(metrics, ConvergenceMetrics)
        assert metrics.agent_id == agent_id

    def test_reset_agent(self, adaptive_controller):
        """Test agent state reset."""
        agent_id = "test-agent-001"

        # Create some state
        asyncio.run(adaptive_controller.record_update(agent_id, success=True))
        asyncio.run(adaptive_controller.record_update(agent_id, success=False))

        # Reset
        asyncio.run(adaptive_controller.reset_agent(agent_id))

        state = adaptive_controller.get_agent_state(agent_id)
        assert state.current_rate == 0.1  # Back to initial
        assert state.total_updates == 0
        assert state.successful_updates == 0


# =============================================================================
# Pattern-Based Agent Adaptor Tests
# =============================================================================

class TestPatternBasedAgentAdaptor:
    """Tests for PatternBasedAgentAdaptor."""

    def test_initialization(self, agent_adaptor):
        """Test adaptor initialization."""
        assert agent_adaptor.default_strategy == AdaptationStrategy.GRADUAL
        assert agent_adaptor.validation_required is False

    def test_get_or_create_state(self, agent_adaptor):
        """Test state creation for new agent."""
        agent_id = "test-agent-001"
        state = agent_adaptor.get_or_create_state(agent_id)

        assert state.agent_id == agent_id
        assert len(state.behavioral_weights) == 0
        assert len(state.strategy_profiles) == 0
        assert state.adaptation_count == 0

    async def test_apply_pattern_behavioral_weights(
        self,
        agent_adaptor,
        sample_pattern,
    ):
        """Test applying pattern with behavioral weights."""
        agent_id = "test-agent-001"

        result = await agent_adaptor.apply_pattern(
            agent_id,
            sample_pattern,
            target=AdaptationTarget.BEHAVIORAL_WEIGHTS,
        )

        assert result is True
        state = agent_adaptor.get_adaptation_state(agent_id)
        assert len(state.adopted_patterns) > 0
        assert state.adaptation_count > 0

    async def test_apply_pattern_strategy_selection(
        self,
        agent_adaptor,
        sample_pattern,
    ):
        """Test applying pattern for strategy selection."""
        agent_id = "test-agent-001"

        result = await agent_adaptor.apply_pattern(
            agent_id,
            sample_pattern,
            target=AdaptationTarget.STRATEGY_SELECTION,
        )

        assert result is True
        state = agent_adaptor.get_adaptation_state(agent_id)
        assert len(state.active_strategies) > 0

    async def test_adjust_behavioral_weight(self, agent_adaptor):
        """Test direct behavioral weight adjustment."""
        agent_id = "test-agent-001"
        aspect = "cooperation"

        result = await agent_adaptor.adjust_behavioral_weight(
            agent_id,
            aspect,
            adjustment=0.1,
        )

        assert result is True
        state = agent_adaptor.get_adaptation_state(agent_id)
        assert aspect in state.behavioral_weights
        assert state.behavioral_weights[aspect].current_value > 0.5

    async def test_register_strategy(self, agent_adaptor):
        """Test registering a new strategy."""
        agent_id = "test-agent-001"

        strategy_id = await agent_adaptor.register_strategy(
            agent_id,
            "test_strategy",
            description="A test strategy",
            initial_priority=0.7,
        )

        state = agent_adaptor.get_adaptation_state(agent_id)
        assert strategy_id in state.strategy_profiles
        assert strategy_id in state.active_strategies

        profile = state.strategy_profiles[strategy_id]
        assert profile.name == "test_strategy"
        assert profile.priority == 0.7

    async def test_select_optimal_strategy(self, agent_adaptor):
        """Test selecting optimal strategy for context."""
        agent_id = "test-agent-001"

        # Register multiple strategies
        await agent_adaptor.register_strategy(
            agent_id,
            "high_priority_strategy",
            initial_priority=0.9,
        )
        await agent_adaptor.register_strategy(
            agent_id,
            "low_priority_strategy",
            initial_priority=0.3,
        )

        selected = await agent_adaptor.select_optimal_strategy(
            agent_id,
            context={"task_type": "test"},
        )

        assert selected is not None
        assert selected.name == "high_priority_strategy"

    def test_get_adaptation_history(self, agent_adaptor):
        """Test getting adaptation history."""
        agent_id = "test-agent-001"
        history = agent_adaptor.get_adaptation_history(agent_id)
        assert isinstance(history, list)

    def test_get_swarm_adaptation_stats(self, agent_adaptor):
        """Test swarm adaptation statistics."""
        stats = agent_adaptor.get_swarm_adaptation_stats()

        assert "total_agents" in stats
        assert "total_adaptations" in stats
        assert "avg_adaptations_per_agent" in stats


# =============================================================================
# Emergent Pattern Detector Tests
# =============================================================================

class TestEmergentPatternDetector:
    """Tests for EmergentPatternDetector."""

    def test_initialization(self, emergence_detector):
        """Test detector initialization."""
        assert emergence_detector.config.min_emergence_score == 0.3
        assert emergence_detector.config.min_participating_agents == 2

    def test_record_agent_snapshot(self, emergence_detector):
        """Test recording agent behavior snapshot."""
        snapshot = AgentBehaviorSnapshot(
            agent_id="test-agent-001",
            state="active",
            active_strategies=["strategy-1"],
            success_rate=0.8,
            metrics={"efficiency": 0.75},
        )

        emergence_detector.record_agent_snapshot(snapshot)

        assert "test-agent-001" in emergence_detector._agent_snapshots
        snapshots = emergence_detector._agent_snapshots["test-agent-001"]
        assert len(snapshots) == 1

    def test_record_collective_behavior(self, emergence_detector):
        """Test recording collective behavior."""
        behavior = CollectiveBehavior(
            behavior_type="synchronized_action",
            participating_agents=["agent-1", "agent-2", "agent-3"],
            intensity=0.8,
            coherence=0.7,
        )

        emergence_detector.record_collective_behavior(behavior)

        assert len(emergence_detector._collective_behaviors) == 1

    async def test_analyze_for_emergence(self, emergence_detector):
        """Test emergence analysis."""
        # Record some data
        for i in range(5):
            snapshot = AgentBehaviorSnapshot(
                agent_id=f"agent-{i}",
                state="active",
                success_rate=0.8,
                metrics={"efficiency": 0.7 + i * 0.05},
            )
            emergence_detector.record_agent_snapshot(snapshot)

        # Record coordinated behaviors
        behavior = CollectiveBehavior(
            behavior_type="coordination",
            participating_agents=["agent-0", "agent-1", "agent-2"],
            intensity=0.8,
            coherence=0.7,
        )
        emergence_detector.record_collective_behavior(behavior)

        # Analyze
        patterns = await emergence_detector.analyze_for_emergence()

        assert isinstance(patterns, list)

    def test_get_emergent_patterns(self, emergence_detector):
        """Test getting detected emergent patterns."""
        patterns = emergence_detector.get_emergent_patterns()
        assert isinstance(patterns, list)

    def test_get_emergence_statistics(self, emergence_detector):
        """Test emergence statistics."""
        stats = emergence_detector.get_emergence_statistics()

        assert "total_patterns" in stats
        assert "validated_patterns" in stats
        assert "by_class" in stats
        assert "by_level" in stats

    def test_calculate_emergence_metrics(self, emergence_detector):
        """Test emergence metrics calculation."""
        metrics = emergence_detector.calculate_emergence_metrics()

        assert "swarm_emergence_index" in metrics
        assert "collective_intelligence_factor" in metrics
        assert "coordination_level" in metrics


# =============================================================================
# Collective Intelligence Metrics Tests
# =============================================================================

class TestCollectiveIntelligenceMetrics:
    """Tests for CollectiveIntelligenceMetrics."""

    def test_initialization(self, collective_metrics):
        """Test metrics initialization."""
        assert collective_metrics.learning_controller is not None
        assert collective_metrics.agent_adaptor is not None
        assert collective_metrics.emergence_detector is not None

    async def test_calculate_siq(self, collective_metrics):
        """Test SIQ calculation."""
        # Create some agent states
        controller = collective_metrics.learning_controller
        await controller.record_update("agent-1", success=True)
        await controller.record_update("agent-2", success=True)
        await controller.record_update("agent-3", success=False)

        siq = await collective_metrics.calculate_siq()

        assert isinstance(siq, SwarmIntelligenceQuotient)
        assert 50.0 <= siq.overall_siq <= 150.0
        assert 0.0 <= siq.siq_percentile <= 100.0
        assert siq.agent_count > 0

    async def test_calculate_collective_efficiency(self, collective_metrics):
        """Test collective efficiency calculation."""
        controller = collective_metrics.learning_controller
        for i in range(5):
            await controller.record_update(f"agent-{i}", success=i % 2 == 0)

        efficiency = await collective_metrics.calculate_collective_efficiency()

        assert isinstance(efficiency, CollectiveEfficiencyMetrics)
        assert 0.0 <= efficiency.task_completion_rate <= 1.0
        assert 0.0 <= efficiency.efficiency_ratio <= 1.0

    async def test_calculate_knowledge_transfer(self, collective_metrics):
        """Test knowledge transfer metrics calculation."""
        adaptor = collective_metrics.agent_adaptor

        # Create some adaptations
        sample_pattern = ExtractedPattern(
            metadata=PatternMetadata(
                pattern_type=PatternType.SUCCESS,
                confidence=0.8,
            ),
            pattern_data={},
        )
        await adaptor.apply_pattern("agent-1", sample_pattern)

        transfer = await collective_metrics.calculate_knowledge_transfer()

        assert isinstance(transfer, KnowledgeTransferMetrics)
        assert transfer.adoption_rate >= 0.0

    async def test_calculate_emergence_coefficient(self, collective_metrics):
        """Test emergence coefficient calculation."""
        detector = collective_metrics.emergence_detector

        # Record some collective behavior
        behavior = CollectiveBehavior(
            behavior_type="test",
            participating_agents=["agent-1", "agent-2"],
            coherence=0.7,
            intensity=0.6,
        )
        detector.record_collective_behavior(behavior)

        coefficient = await collective_metrics.calculate_emergence_coefficient()

        assert isinstance(coefficient, EmergenceCoefficient)
        assert 0.0 <= coefficient.emergence_coefficient <= 1.0

    def test_get_dashboard_data(self, collective_metrics):
        """Test dashboard data generation."""
        dashboard = collective_metrics.get_dashboard_data()

        assert isinstance(dashboard, MetricsDashboard)
        assert 0.0 <= dashboard.swarm_health_score <= 100.0
        assert dashboard.total_agents >= 0
        assert isinstance(dashboard.alerts, list)

    def test_metric_definitions(self, collective_metrics):
        """Test metric definitions."""
        definitions = collective_metrics.get_all_metric_definitions()

        assert len(definitions) > 0
        for definition in definitions:
            assert definition.name
            assert definition.category
            assert definition.aggregation


# =============================================================================
# Zero-Trust Verification Tests
# =============================================================================

class TestZeroTrustCompliance:
    """Tests for zero-trust compliance."""

    def test_no_datetime_utcnow(self):
        """Verify no datetime.utcnow() usage."""
        import inspect

        from heretek_swarm.collective import (
            adaptive_learning,
            agent_adaptation,
            emergent_detection,
            metrics,
        )

        modules = [
            adaptive_learning,
            agent_adaptation,
            emergent_detection,
            metrics,
        ]

        for module in modules:
            source = inspect.getsource(module)
            assert "datetime.utcnow" not in source, \
                f"datetime.utcnow found in {module.__name__}"

    def test_no_hardcoded_secrets(self):
        """Verify no hardcoded secrets."""
        import inspect

        from heretek_swarm.collective import (
            adaptive_learning,
            agent_adaptation,
            emergent_detection,
            metrics,
        )

        modules = [
            adaptive_learning,
            agent_adaptation,
            emergent_detection,
            metrics,
        ]

        for module in modules:
            source = inspect.getsource(module)
            assert "password = " not in source, \
                f"Hardcoded password found in {module.__name__}"
            assert "password='" not in source, \
                f"Hardcoded password found in {module.__name__}"
            assert 'password="' not in source, \
                f"Hardcoded password found in {module.__name__}"

    def test_no_todo_fixme_comments(self):
        """Verify no TODO/FIXME/XXX/HACK comments."""
        import inspect

        from heretek_swarm.collective import (
            adaptive_learning,
            agent_adaptation,
            emergent_detection,
            metrics,
        )

        modules = [
            adaptive_learning,
            agent_adaptation,
            emergent_detection,
            metrics,
        ]

        for module in modules:
            source = inspect.getsource(module)
            assert "TODO" not in source, f"TODO comment found in {module.__name__}"
            assert "FIXME" not in source, f"FIXME comment found in {module.__name__}"
            assert "XXX" not in source, f"XXX comment found in {module.__name__}"
            assert "HACK" not in source, f"HACK comment found in {module.__name__}"


# =============================================================================
# Integration Tests
# =============================================================================

class TestSession46Integration:
    """Integration tests for Session 46 components."""

    async def test_full_emergent_intelligence_workflow(self, collective_metrics):
        """Test complete emergent intelligence workflow."""
        # 1. Create agents and record updates
        controller = collective_metrics.learning_controller
        adaptor = collective_metrics.agent_adaptor
        detector = collective_metrics.emergence_detector

        for i in range(5):
            agent_id = f"agent-{i}"
            # Record learning updates
            await controller.record_update(agent_id, success=i % 2 == 0)

            # Record behavior snapshots
            snapshot = AgentBehaviorSnapshot(
                agent_id=agent_id,
                state="active",
                success_rate=0.5 + (i * 0.1),
                metrics={"efficiency": 0.6 + (i * 0.05)},
            )
            detector.record_agent_snapshot(snapshot)

        # 2. Apply patterns
        sample_pattern = ExtractedPattern(
            metadata=PatternMetadata(
                pattern_type=PatternType.SUCCESS,
                confidence=0.85,
            ),
            pattern_data={
                "behavioral_weights": {"cooperation": 0.8},
            },
        )

        for i in range(3):
            await adaptor.apply_pattern(f"agent-{i}", sample_pattern)

        # 3. Record collective behavior
        behavior = CollectiveBehavior(
            behavior_type="synchronized_optimization",
            participating_agents=["agent-0", "agent-1", "agent-2"],
            intensity=0.8,
            coherence=0.7,
        )
        detector.record_collective_behavior(behavior)

        # 4. Analyze emergence
        await detector.analyze_for_emergence()

        # 5. Calculate all metrics
        siq = await collective_metrics.calculate_siq()
        efficiency = await collective_metrics.calculate_collective_efficiency()
        transfer = await collective_metrics.calculate_knowledge_transfer()
        emergence = await collective_metrics.calculate_emergence_coefficient()

        # 6. Get dashboard data
        dashboard = collective_metrics.get_dashboard_data()

        # Verify results
        assert siq.overall_siq > 0
        assert efficiency.efficiency_ratio >= 0
        assert transfer.adoption_rate >= 0
        assert emergence.emergence_coefficient >= 0
        assert dashboard.swarm_health_score >= 0

    def test_metrics_export(self, collective_metrics):
        """Test metrics export functionality."""
        from heretek_swarm.collective.metrics import MetricsExporter

        exporter = MetricsExporter(collective_metrics)
        summary = exporter.export_summary()

        assert isinstance(summary, dict)
        assert "swarm_health" in summary
        assert "siq" in summary
        assert "efficiency" in summary
        assert "emergence" in summary


# =============================================================================
# Run Tests
# =============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
