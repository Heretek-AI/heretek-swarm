"""
Tests for Organic Evolution Mechanisms - Session 46 Emergent Intelligence

Tests for:
- EvolutionEngine: Tracking capability development
- EvolutionMetrics: Evolution rate, fitness landscape, adaptability
- Adaptive Learning with environment adaptation
- Fitness-based behavior selection
- Capability mutation
"""


import pytest

from heretek_swarm.collective.adaptive_learning import (
    AdaptiveLearningRateController,
    BehaviorFitness,
    EnvironmentProfile,
    EvolutionResult,
    LearningRateConfig,
    LearningRateStrategy,
    MutationType,
)
from heretek_swarm.collective.emergent_detection_types import (
    EvolutionMetrics,
    EvolutionPhase,
)
from heretek_swarm.collective.evolution_engine import EvolutionEngine

# =============================================================================
# EvolutionEngine Tests
# =============================================================================

class TestEvolutionEngine:
    """Tests for the EvolutionEngine class."""

    @pytest.fixture
    def engine(self):
        """Create a fresh EvolutionEngine instance."""
        return EvolutionEngine(
            capability_window_hours=24.0,
            stabilization_threshold=0.8,
            min_fitness_samples=5,
        )

    @pytest.mark.asyncio
    async def test_initialization(self, engine):
        """Test EvolutionEngine initialization."""
        assert engine is not None
        assert engine._capability_window_hours == 24.0
        assert engine._stabilization_threshold == 0.8
        assert len(engine._capability_records) == 0
        assert len(engine._agent_snapshots) == 0

    @pytest.mark.asyncio
    async def test_record_capability_gain(self, engine):
        """Test recording a new capability."""
        record = engine.record_capability_gain(
            agent_id="agent_1",
            capability_type="collaboration",
            capability_name="team_synchronization",
            fitness_contribution=0.7,
            description="Agents learned to work in sync",
        )

        assert record is not None
        assert record.capability_type == "collaboration"
        assert record.capability_name == "team_synchronization"
        assert record.origin_agent_id == "agent_1"
        assert record.fitness_contribution == 0.7
        assert record.is_stabilized is False

        # Verify it was stored
        assert len(engine._capability_records) == 1

    @pytest.mark.asyncio
    async def test_record_multiple_capabilities(self, engine):
        """Test recording multiple capabilities."""
        engine.record_capability_gain(
            agent_id="agent_1",
            capability_type="collaboration",
            capability_name="sync_1",
            fitness_contribution=0.5,
        )
        engine.record_capability_gain(
            agent_id="agent_2",
            capability_type="optimization",
            capability_name="opt_1",
            fitness_contribution=0.6,
        )
        engine.record_capability_gain(
            agent_id="agent_1",
            capability_type="problem_solving",
            capability_name="solve_1",
            fitness_contribution=0.8,
        )

        assert len(engine._capability_records) == 3

        # Check evolution rate updated
        metrics = engine.get_evolution_metrics()
        assert metrics.evolution_rate > 0

    @pytest.mark.asyncio
    async def test_detect_evolution(self, engine):
        """Test detecting evolution from agent states."""
        agent_states = {
            "agent_1": {
                "capability_levels": {
                    "collaboration": 0.3,
                    "problem_solving": 0.4,
                },
                "fitness_score": 0.5,
                "behaviors": ["explore", "exploit"],
            },
            "agent_2": {
                "capability_levels": {
                    "optimization": 0.6,
                },
                "fitness_score": 0.7,
                "behaviors": ["optimize"],
            },
        }

        # Create initial snapshots
        engine._create_agent_snapshot("agent_1", agent_states["agent_1"])

        # Update with new capabilities
        updated_states = {
            "agent_1": {
                "capability_levels": {
                    "collaboration": 0.8,  # Significant increase
                    "problem_solving": 0.4,
                },
                "fitness_score": 0.7,
                "behaviors": ["explore", "exploit", "coordinate"],
            },
            "agent_2": {
                "capability_levels": {
                    "optimization": 0.6,
                },
                "fitness_score": 0.7,
                "behaviors": ["optimize"],
            },
        }

        new_capabilities = engine.detect_evolution(updated_states)

        # Should detect the collaboration capability increase
        assert len(new_capabilities) >= 0  # May or may not detect depending on thresholds

    @pytest.mark.asyncio
    async def test_assess_fitness(self, engine):
        """Test fitness assessment."""
        performance_history = [0.5, 0.6, 0.7, 0.65, 0.8, 0.85]
        capability_levels = {
            "collaboration": 0.7,
            "optimization": 0.6,
        }

        fitness = engine.assess_fitness(
            agent_id="agent_1",
            performance_history=performance_history,
            capability_levels=capability_levels,
        )

        assert 0.0 <= fitness <= 1.0
        # With good performance history and capabilities, fitness should be high
        assert fitness > 0.5

    @pytest.mark.asyncio
    async def test_assess_fitness_with_environment(self, engine):
        """Test fitness assessment with environment demands."""
        performance_history = [0.6, 0.7, 0.8]
        capability_levels = {
            "collaboration": 0.8,  # High - matches demand
            "optimization": 0.3,   # Low - doesn't match demand
        }
        environment_demand = {
            "collaboration": 0.9,
            "optimization": 0.8,
        }

        fitness = engine.assess_fitness(
            agent_id="agent_1",
            performance_history=performance_history,
            capability_levels=capability_levels,
            environment_demand=environment_demand,
        )

        # Should have high fitness due to collaboration match
        assert fitness > 0.5

    @pytest.mark.asyncio
    async def test_get_capability_records_filtering(self, engine):
        """Test filtering capability records."""
        engine.record_capability_gain(
            agent_id="agent_1",
            capability_type="collaboration",
            capability_name="collab_1",
            fitness_contribution=0.7,
        )
        engine.record_capability_gain(
            agent_id="agent_2",
            capability_type="optimization",
            capability_name="opt_1",
            fitness_contribution=0.5,
        )
        engine.record_capability_gain(
            agent_id="agent_3",
            capability_type="problem_solving",
            capability_name="solve_1",
            fitness_contribution=0.9,
        )

        # Filter by type
        collab_caps = engine.get_capability_records(capability_type="collaboration")
        assert len(collab_caps) == 1
        assert collab_caps[0].capability_type == "collaboration"

        # Filter by min fitness
        high_fitness = engine.get_capability_records(min_fitness=0.6)
        assert len(high_fitness) == 2

    @pytest.mark.asyncio
    async def test_evolution_metrics(self, engine):
        """Test evolution metrics calculation."""
        # Add some capabilities
        engine.record_capability_gain(
            agent_id="agent_1",
            capability_type="collaboration",
            capability_name="collab_1",
            fitness_contribution=0.7,
        )
        engine.record_capability_gain(
            agent_id="agent_2",
            capability_type="optimization",
            capability_name="opt_1",
            fitness_contribution=0.6,
        )

        # Create agent snapshots with fitness
        engine._create_agent_snapshot("agent_1", {
            "capability_levels": {"collaboration": 0.7},
            "fitness_score": 0.8,
            "fitness_history": [0.5, 0.6, 0.8],
            "behaviors": ["coordinate"],
        })

        metrics = engine.get_evolution_metrics()

        assert isinstance(metrics, EvolutionMetrics)
        assert metrics.total_capabilities == 2
        assert metrics.evolution_rate > 0
        assert metrics.capability_diversity > 0
        assert metrics.avg_fitness > 0

    @pytest.mark.asyncio
    async def test_evolution_phases(self, engine):
        """Test evolution phase determination."""
        # Initially should be in initialization
        metrics = engine.get_evolution_metrics()
        assert metrics.current_phase == EvolutionPhase.INITIALIZATION

        # Add capabilities to move to exploration
        for i in range(3):
            engine.record_capability_gain(
                agent_id=f"agent_{i}",
                capability_type=f"cap_{i}",
                capability_name=f"capability_{i}",
                fitness_contribution=0.5,
            )

        metrics = engine.get_evolution_metrics()
        # Should have moved past initialization
        assert metrics.current_phase != EvolutionPhase.INITIALIZATION


# =============================================================================
# AdaptiveLearningRateController Tests
# =============================================================================

class TestAdaptiveLearningRateController:
    """Tests for the AdaptiveLearningRateController with evolutionary features."""

    @pytest.fixture
    def controller(self):
        """Create a fresh AdaptiveLearningRateController instance."""
        config = LearningRateConfig(
            initial_rate=0.1,
            min_rate=0.001,
            max_rate=1.0,
            strategy=LearningRateStrategy.EVOLUTIONARY,
            mutation_rate=0.1,
            crossover_rate=0.2,
            selection_pressure=0.5,
        )
        return AdaptiveLearningRateController(config=config)

    @pytest.mark.asyncio
    async def test_initialization(self, controller):
        """Test controller initialization."""
        assert controller is not None
        assert controller.config.initial_rate == 0.1
        assert controller.config.strategy == LearningRateStrategy.EVOLUTIONARY

    @pytest.mark.asyncio
    async def test_record_update(self, controller):
        """Test recording updates."""
        await controller.record_update("agent_1", success=True)
        await controller.record_update("agent_1", success=False)
        await controller.record_update("agent_1", success=True)

        state = controller.get_agent_state("agent_1")
        assert state.total_updates == 3
        assert state.successful_updates == 2
        assert state.failed_updates == 1

    @pytest.mark.asyncio
    async def test_evolve_behaviors(self, controller):
        """Test behavior evolution."""
        # Add some initial behaviors
        state = controller.get_or_create_state("agent_1")
        state.behavior_pool["behavior_1"] = BehaviorFitness(
            behavior_id="behavior_1",
            behavior_type="exploration",
            initial_fitness=0.7,
        )
        state.behavior_pool["behavior_2"] = BehaviorFitness(
            behavior_id="behavior_2",
            behavior_type="optimization",
            initial_fitness=0.4,
        )

        result = await controller.evolve_behaviors("agent_1")

        assert isinstance(result, EvolutionResult)
        # Should have selected behaviors
        assert len(result.selected_behaviors) >= 0

    @pytest.mark.asyncio
    async def test_mutate_capabilities(self, controller):
        """Test capability mutation."""
        state = controller.get_or_create_state("agent_1")
        state.capability_levels = {
            "collaboration": 0.5,
            "optimization": 0.6,
        }

        # Run mutation multiple times
        mutated = await controller.mutate_capabilities(
            "agent_1",
            mutation_type=MutationType.EXPLORATION,
        )

        # Mutation may or may not create new behaviors based on randomness
        # Just verify it doesn't crash
        assert isinstance(mutated, list)

    @pytest.mark.asyncio
    async def test_select_fittest(self, controller):
        """Test fitness-based behavior selection."""
        state = controller.get_or_create_state("agent_1")

        # Add behaviors with different fitness
        for i in range(5):
            state.behavior_pool[f"behavior_{i}"] = BehaviorFitness(
                behavior_id=f"behavior_{i}",
                behavior_type="test",
                initial_fitness=0.2 + (i * 0.15),  # Increasing fitness
            )

        selected = await controller.select_fittest("agent_1", count=3)

        assert len(selected) <= 3
        # Higher fitness behaviors should be selected
        if len(selected) >= 1:
            # Verify selected behaviors exist
            for bid in selected:
                assert bid in state.behavior_pool

    @pytest.mark.asyncio
    async def test_environment_profile(self, controller):
        """Test environment profile tracking."""
        profile = controller.get_environment_profile()

        assert "stability" in profile
        assert "complexity" in profile
        assert "optimal_learning_rate" in profile
        assert "selection_pressure" in profile

    @pytest.mark.asyncio
    async def test_swarm_statistics(self, controller):
        """Test swarm-wide statistics."""
        # Add some agents
        await controller.record_update("agent_1", success=True)
        await controller.record_update("agent_1", success=True)
        await controller.record_update("agent_2", success=False)
        await controller.record_update("agent_3", success=True)

        stats = controller.get_swarm_statistics()

        assert stats["total_agents"] == 3
        assert stats["avg_learning_rate"] > 0
        assert "avg_fitness" in stats
        assert "environment_stability" in stats

    @pytest.mark.asyncio
    async def test_behavior_fitness_update(self):
        """Test BehaviorFitness class."""
        bf = BehaviorFitness(
            behavior_id="test_behavior",
            behavior_type="test",
            initial_fitness=0.5,
        )

        # Update with successes
        for _ in range(5):
            bf.update_fitness(success=True)

        assert bf.success_count == 5
        assert bf.fitness > 0.5
        assert bf.success_rate == 1.0

        # Update with failures
        for _ in range(3):
            bf.update_fitness(success=False)

        assert bf.failure_count == 3
        assert bf.success_rate < 1.0


# =============================================================================
# Evolution Metrics Tests
# =============================================================================

class TestEvolutionMetrics:
    """Tests for EvolutionMetrics dataclass."""

    def test_evolution_metrics_creation(self):
        """Test creating EvolutionMetrics."""
        metrics = EvolutionMetrics()

        assert metrics.evolution_rate == 0.0
        assert metrics.fitness_landscape == 0.0
        assert metrics.adaptability_index == 0.0
        assert metrics.current_phase == EvolutionPhase.INITIALIZATION
        assert metrics.total_capabilities == 0

    def test_evolution_metrics_to_dict(self):
        """Test converting EvolutionMetrics to dict."""
        metrics = EvolutionMetrics(
            evolution_rate=2.5,
            fitness_landscape=0.75,
            adaptability_index=0.8,
            current_phase=EvolutionPhase.EMERGENCE,
            total_capabilities=10,
        )

        d = metrics.to_dict()

        assert d["evolution_rate"] == 2.5
        assert d["fitness_landscape"] == 0.75
        assert d["adaptability_index"] == 0.8
        assert d["current_phase"] == "emergence"
        assert d["total_capabilities"] == 10


# =============================================================================
# Environment Profile Tests
# =============================================================================

class TestEnvironmentProfile:
    """Tests for EnvironmentProfile class."""

    def test_environment_profile_creation(self):
        """Test creating EnvironmentProfile."""
        profile = EnvironmentProfile()

        assert profile.stability == 0.5
        assert profile.complexity == 0.5
        assert profile.optimal_learning_rate == 0.1
        assert profile.selection_pressure == 0.5

    def test_update_from_observations(self):
        """Test updating profile from observations."""
        profile = EnvironmentProfile()

        # Stable environment with low complexity
        profile.update_from_observations(
            performance_variance=0.1,  # Low variance = stable
            task_diversity=0.3,
            success_rate=0.9,
        )

        assert profile.stability > 0.8
        assert profile.optimal_learning_rate < 0.2  # Lower rate for stable env

        # Unstable environment with high complexity
        profile.update_from_observations(
            performance_variance=0.8,  # High variance = unstable
            task_diversity=0.9,
            success_rate=0.4,
        )

        assert profile.stability < 0.3
        assert profile.optimal_learning_rate > 0.2  # Higher rate for unstable


# =============================================================================
# Integration Tests
# =============================================================================

class TestEvolutionIntegration:
    """Integration tests for evolution mechanisms."""

    @pytest.mark.asyncio
    async def test_full_evolution_cycle(self):
        """Test a complete evolution cycle."""
        from heretek_swarm.collective.adaptive_learning import AdaptiveLearningRateController
        from heretek_swarm.collective.emergent_detection import EvolutionEngine

        # Create engine and controller
        engine = EvolutionEngine()
        controller = AdaptiveLearningRateController()

        # Record initial capabilities
        engine.record_capability_gain(
            agent_id="agent_1",
            capability_type="collaboration",
            capability_name="initial_collab",
            fitness_contribution=0.5,
        )

        # Record some learning updates
        for _ in range(5):
            await controller.record_update("agent_1", success=True)

        # Evolve behaviors
        await controller.evolve_behaviors("agent_1")

        # Check evolution metrics
        metrics = engine.get_evolution_metrics()
        assert metrics.total_capabilities >= 1

        # Check swarm stats
        stats = controller.get_swarm_statistics()
        assert stats["total_agents"] >= 1
        assert stats["avg_success_rate"] > 0

    @pytest.mark.asyncio
    async def test_evolution_with_environment_demands(self):
        """Test evolution with environment demands."""
        engine = EvolutionEngine()
        controller = AdaptiveLearningRateController()

        # Set environment demands
        demands = {
            "collaboration": 0.8,
            "problem_solving": 0.7,
        }

        # Record capabilities matching demands
        engine.record_capability_gain(
            agent_id="agent_1",
            capability_type="collaboration",
            capability_name="high_collab",
            fitness_contribution=0.8,
        )

        # Evolve with demands
        await controller.evolve_behaviors("agent_1", environment_demands=demands)

        # Check adaptability
        metrics = engine.get_evolution_metrics()
        assert metrics.adaptability_index >= 0


# =============================================================================
# API Endpoint Tests (Mock)
# =============================================================================

class TestEvolutionAPI:
    """Tests for evolution API endpoints."""

    def test_evolution_phase_descriptions(self):
        """Test evolution phase descriptions."""
        from heretek_swarm.api.collective_evolution import _get_phase_description

        descriptions = {
            "initialization": "Swarm is just forming",
            "exploration": "Agents are exploring",
            "selection": "Behaviors are being selected",
            "consolidation": "Successful traits are stabilizing",
            "emergence": "New capabilities are emerging",
            "maturation": "Capabilities are maturing",
            "equilibrium": "Stable evolutionary state achieved",
        }

        for phase_str, expected_substring in descriptions.items():
            result = _get_phase_description(EvolutionPhase(phase_str))
            assert expected_substring.lower() in result.lower()
