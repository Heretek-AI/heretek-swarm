"""
Unit Tests for Phi Training Environment.

Tests cover:
- Training environment initialization
- Episode execution
- Reward calculation
- Scenario types
- Metrics collection
- Rate limiting
- Prometheus export
"""


import pytest

from heretek_swarm.consciousness.iit_phi import PhiCalculator
from heretek_swarm.consciousness.phi_training import (
    AgentActor,
    CommunicationTrainingScenario,
    ConsensusTrainingScenario,
    DecisionCoherenceTrainingScenario,
    PhiTrainingEnvironment,
    ScenarioType,
    TrainingEpisode,
    TrainingMode,
    TrainingResult,
    TrainingScenario,
)


class TestAgentActor:
    """Tests for AgentActor base class."""

    def test_initialization(self):
        """Test agent actor initialization."""
        actor = AgentActor(agent_id="test_agent", agent_type="default")

        assert actor.agent_id == "test_agent"
        assert actor.agent_type == "default"
        assert actor.state == {}
        assert actor.message_history == []

    @pytest.mark.asyncio
    async def test_act_not_implemented(self):
        """Test that act method raises NotImplementedError."""
        actor = AgentActor(agent_id="test_agent", agent_type="default")

        with pytest.raises(NotImplementedError):
            await actor.act({"observation": "test"})

    def test_get_state(self):
        """Test getting agent state."""
        actor = AgentActor(agent_id="test_agent", agent_type="default")
        actor.state = {"key": "value"}

        state = actor.get_state()
        assert state == {"key": "value"}
        assert state is not actor.state  # Should be a copy

    def test_reset(self):
        """Test resetting agent state."""
        actor = AgentActor(agent_id="test_agent", agent_type="default")
        actor.state = {"key": "value"}
        actor.message_history = [{"msg": "test"}]

        actor.reset()

        assert actor.state == {}
        assert actor.message_history == []


class TestTrainingEpisode:
    """Tests for TrainingEpisode dataclass."""

    def test_creation(self):
        """Test episode creation."""
        episode = TrainingEpisode(
            episode_id="ep_123",
            scenario_type=ScenarioType.COMMUNICATION,
            start_phi=0.5,
            end_phi=0.7,
            phi_delta=0.2,
            steps=10,
            duration_seconds=5.5,
        )

        assert episode.episode_id == "ep_123"
        assert episode.scenario_type == ScenarioType.COMMUNICATION
        assert episode.phi_delta == 0.2
        assert "timestamp" in episode.to_dict()

    def test_to_dict(self):
        """Test episode serialization."""
        episode = TrainingEpisode(
            episode_id="ep_123",
            scenario_type=ScenarioType.DECISION_COHERENCE,
            start_phi=0.3,
            end_phi=0.6,
            phi_delta=0.3,
            steps=5,
            duration_seconds=2.0,
            metadata={"test": "data"},
        )

        result = episode.to_dict()

        assert result["episode_id"] == "ep_123"
        assert result["scenario_type"] == "decision_coherence"
        assert result["start_phi"] == 0.3
        assert result["metadata"]["test"] == "data"


class TestTrainingScenario:
    """Tests for TrainingScenario dataclass."""

    def test_creation(self):
        """Test scenario creation."""
        scenario = TrainingScenario(
            scenario_id="scenario_123",
            scenario_type=ScenarioType.TASK_COLLABORATION,
            description="Test scenario",
            agent_count=5,
            initial_state={"key": "value"},
            objectives=["maximize_phi"],
            max_steps=50,
            phi_target=0.8,
        )

        assert scenario.scenario_id == "scenario_123"
        assert scenario.agent_count == 5
        assert scenario.phi_target == 0.8

    def test_to_dict(self):
        """Test scenario serialization."""
        scenario = TrainingScenario(
            scenario_id="scenario_123",
            scenario_type=ScenarioType.CONSENSUS_FORMATION,
            description="Test",
            agent_count=3,
            initial_state={},
            objectives=["test"],
        )

        result = scenario.to_dict()

        assert result["scenario_id"] == "scenario_123"
        assert result["scenario_type"] == "consensus_formation"
        assert result["agent_count"] == 3


class TestPhiTrainingEnvironment:
    """Tests for PhiTrainingEnvironment class."""

    def test_initialization(self):
        """Test environment initialization."""
        env = PhiTrainingEnvironment(
            training_mode=TrainingMode.SIMULATION,
        )

        assert env.training_mode == TrainingMode.SIMULATION
        assert isinstance(env.phi_calculator, PhiCalculator)
        assert env.episode_history == []

    def test_initialization_with_custom_calculator(self):
        """Test initialization with custom Phi calculator."""
        custom_calculator = PhiCalculator()
        env = PhiTrainingEnvironment(phi_calculator=custom_calculator)

        assert env.phi_calculator is custom_calculator

    @pytest.mark.asyncio
    async def test_run_episode_basic(self):
        """Test basic episode execution."""
        env = PhiTrainingEnvironment()

        # Create mock agents
        class MockAgent(AgentActor):
            async def act(self, observation):
                return {"action": "test"}

        agents = [MockAgent(f"agent_{i}", "default") for i in range(3)]

        scenario = TrainingScenario(
            scenario_id="test_scenario",
            scenario_type=ScenarioType.COMMUNICATION,
            description="Test",
            agent_count=3,
            initial_state={},
            objectives=["test"],
            max_steps=5,
        )

        result = await env.run_episode(agents, scenario)

        assert isinstance(result, TrainingResult)
        assert result.episode.scenario_type == ScenarioType.COMMUNICATION
        assert len(env.episode_history) == 1

    @pytest.mark.asyncio
    async def test_run_episode_with_target(self):
        """Test episode execution with Phi target."""
        env = PhiTrainingEnvironment()

        class MockAgent(AgentActor):
            async def act(self, observation):
                return {"action": "test"}

        agents = [MockAgent(f"agent_{i}", "default") for i in range(3)]

        scenario = TrainingScenario(
            scenario_id="test_scenario",
            scenario_type=ScenarioType.COMMUNICATION,
            description="Test",
            agent_count=3,
            initial_state={},
            objectives=["test"],
            max_steps=100,
            phi_target=0.01,  # Low target for quick completion
        )

        result = await env.run_episode(agents, scenario)

        assert result.episode.phi_delta >= 0 or result.episode.steps <= 100

    def test_calculate_phi_reward_positive(self):
        """Test reward calculation for positive Phi change."""
        env = PhiTrainingEnvironment()

        reward = env.calculate_phi_reward(before=0.5, after=0.7)

        delta = 0.2
        expected = delta + delta * 0.5  # Base + 50% bonus
        assert reward == pytest.approx(expected, rel=1e-9)

    def test_calculate_phi_reward_negative(self):
        """Test reward calculation for negative Phi change."""
        env = PhiTrainingEnvironment()

        reward = env.calculate_phi_reward(before=0.7, after=0.5)

        delta = -0.2
        # Base reward with penalty for large negative
        assert reward < delta

    def test_calculate_phi_reward_small_negative(self):
        """Test reward calculation for small negative Phi change."""
        env = PhiTrainingEnvironment()

        reward = env.calculate_phi_reward(before=0.5, after=0.45)

        # Small negative should just be the delta
        assert reward == pytest.approx(-0.05, rel=1e-9)

    def test_export_metrics(self):
        """Test metrics export."""
        env = PhiTrainingEnvironment()

        metrics = env.export_metrics()

        assert "total_episodes" in metrics
        assert "successful_episodes" in metrics
        assert "total_phi_improvement" in metrics
        assert "avg_phi_improvement" in metrics
        assert "best_phi_achieved" in metrics

    def test_export_prometheus_metrics(self):
        """Test Prometheus metrics export."""
        env = PhiTrainingEnvironment()

        metrics_str = env.export_prometheus_metrics()

        assert "heretek_phi_training_episodes_total" in metrics_str
        assert "heretek_phi_training_success_total" in metrics_str
        assert "heretek_phi_training_avg_improvement" in metrics_str

    def test_get_episode_history(self):
        """Test getting episode history."""
        env = PhiTrainingEnvironment()

        # History should be empty initially
        history = env.get_episode_history()
        assert history == []

        # Limit should work
        history = env.get_episode_history(limit=50)
        assert len(history) == 0

    def test_get_training_statistics_empty(self):
        """Test statistics with no episodes."""
        env = PhiTrainingEnvironment()

        stats = env.get_training_statistics()

        assert stats["episodes"] == 0

    def test_rate_limiting(self):
        """Test rate limiting."""
        env = PhiTrainingEnvironment()
        env._max_episodes_per_minute = 2

        # First two should succeed
        env._check_rate_limit()
        env._check_rate_limit()

        # Third should fail
        with pytest.raises(RuntimeError, match="Rate limit exceeded"):
            env._check_rate_limit()

    def test_update_metrics(self):
        """Test metrics update after episode."""
        env = PhiTrainingEnvironment()

        # Create mock result
        episode = TrainingEpisode(
            episode_id="test",
            scenario_type=ScenarioType.COMMUNICATION,
            start_phi=0.5,
            end_phi=0.7,
            phi_delta=0.2,
            steps=10,
            duration_seconds=5.0,
        )

        result = TrainingResult(
            episode=episode,
            total_reward=1.0,
            avg_phi=0.6,
            max_phi=0.7,
            convergence_step=None,
            success=True,
        )

        env._update_metrics(result)

        assert env.metrics["total_episodes"] == 1
        assert env.metrics["successful_episodes"] == 1
        assert env.metrics["total_phi_improvement"] == 0.2
        assert env.metrics["best_phi_achieved"] == 0.7


class TestSpecializedScenarios:
    """Tests for specialized training scenarios."""

    def test_communication_scenario(self):
        """Test CommunicationTrainingScenario creation."""
        scenario = CommunicationTrainingScenario(agent_count=5)

        assert scenario.scenario_type == ScenarioType.COMMUNICATION
        assert scenario.agent_count == 5
        assert "message_budget" in scenario.initial_state
        assert scenario.phi_target == 0.7

    def test_decision_coherence_scenario(self):
        """Test DecisionCoherenceTrainingScenario creation."""
        scenario = DecisionCoherenceTrainingScenario(agent_count=4)

        assert scenario.scenario_type == ScenarioType.DECISION_COHERENCE
        assert scenario.agent_count == 4
        assert "decision_rounds" in scenario.initial_state
        assert scenario.phi_target == 0.8

    def test_consensus_scenario(self):
        """Test ConsensusTrainingScenario creation."""
        scenario = ConsensusTrainingScenario(agent_count=6)

        assert scenario.scenario_type == ScenarioType.CONSENSUS_FORMATION
        assert scenario.agent_count == 6
        assert "proposal" in scenario.initial_state
        assert scenario.phi_target == 0.75


class TestStepExecution:
    """Tests for scenario step execution."""

    @pytest.mark.asyncio
    async def test_communication_step(self):
        """Test communication step execution."""
        env = PhiTrainingEnvironment()

        class MockAgent(AgentActor):
            async def act(self, observation):
                return {"message": "test message"}

        agents = [MockAgent(f"agent_{i}", "default") for i in range(3)]

        scenario = TrainingScenario(
            scenario_id="test",
            scenario_type=ScenarioType.COMMUNICATION,
            description="Test",
            agent_count=3,
            initial_state={},
            objectives=[],
            max_steps=10,
        )

        await env._execute_step(agents, scenario, step=0)

        # Agents should have message history
        for agent in agents:
            assert len(agent.message_history) > 0

    @pytest.mark.asyncio
    async def test_decision_coherence_step(self):
        """Test decision coherence step execution."""
        env = PhiTrainingEnvironment()

        class MockAgent(AgentActor):
            async def act(self, observation):
                return {"decision": "option_a"}

        agents = [MockAgent(f"agent_{i}", "default") for i in range(3)]

        scenario = TrainingScenario(
            scenario_id="test",
            scenario_type=ScenarioType.DECISION_COHERENCE,
            description="Test",
            agent_count=3,
            initial_state={},
            objectives=[],
            max_steps=10,
        )

        result = await env._execute_step(agents, scenario, step=0)

        assert "coherence" in result["state"]

    @pytest.mark.asyncio
    async def test_consensus_step(self):
        """Test consensus formation step execution."""
        env = PhiTrainingEnvironment()

        class MockAgent(AgentActor):
            async def act(self, observation):
                return {"position": 0.5}

        agents = [MockAgent(f"agent_{i}", "default") for i in range(3)]

        scenario = TrainingScenario(
            scenario_id="test",
            scenario_type=ScenarioType.CONSENSUS_FORMATION,
            description="Test",
            agent_count=3,
            initial_state={},
            objectives=[],
            max_steps=10,
        )

        result = await env._execute_step(agents, scenario, step=0)

        assert "consensus" in result["state"]


class TestIntegration:
    """Integration tests for Phi training environment."""

    @pytest.mark.asyncio
    async def test_full_training_session(self):
        """Test complete training session with multiple episodes."""
        env = PhiTrainingEnvironment()

        class MockAgent(AgentActor):
            async def act(self, observation):
                return {"action": "test", "message": "hello"}

        agents = [MockAgent(f"agent_{i}", "default") for i in range(3)]

        scenario = CommunicationTrainingScenario(agent_count=3)

        # Run multiple episodes
        results = []
        for _ in range(3):
            result = await env.run_episode(agents, scenario)
            results.append(result)

        # Verify results
        assert len(results) == 3
        assert len(env.episode_history) == 3

        # Check statistics
        stats = env.get_training_statistics()
        assert stats["total_episodes"] == 3

    @pytest.mark.asyncio
    async def test_training_with_different_scenarios(self):
        """Test training with different scenario types."""
        env = PhiTrainingEnvironment()

        class MockAgent(AgentActor):
            async def act(self, observation):
                return {"decision": "a", "position": 0.5}

        agents = [MockAgent(f"agent_{i}", "default") for i in range(3)]

        scenarios = [
            CommunicationTrainingScenario(agent_count=3),
            DecisionCoherenceTrainingScenario(agent_count=3),
            ConsensusTrainingScenario(agent_count=3),
        ]

        for scenario in scenarios:
            result = await env.run_episode(agents, scenario)
            assert isinstance(result, TrainingResult)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
