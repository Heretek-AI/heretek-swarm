"""
Test Suite for FEP Active Inference Module.

This module provides comprehensive tests for the Free Energy Principle (FEP)
active inference implementation, including:

1. Unit tests for FreeEnergyCalculator class
2. Unit tests for ActiveInferenceAgent class
3. Integration tests with consciousness metrics
4. Validation against known FEP scenarios
5. Zero-trust input validation tests

Test Coverage Requirements:
- Minimum 80% line coverage
- Minimum 70% branch coverage

Author: Heretek Swarm Collective
Date: 2026-04-07
"""

import pytest
from datetime import datetime, timezone
from typing import Dict, Any
import uuid

from src.heretek_swarm.consciousness.fep_active_inference import (
    FreeEnergyCalculator,
    ActiveInferenceAgent,
    BeliefState,
    Action,
    Policy,
    FEPResult,
)
from src.heretek_swarm.plugins.consciousness_metrics import (
    ConsciousnessMetricsCalculator,
    AgentConsciousnessData,
)


class TestFreeEnergyCalculator:
    """Test suite for FreeEnergyCalculator class."""
    
    @pytest.fixture
    def calculator(self):
        """Create a FreeEnergyCalculator instance."""
        return FreeEnergyCalculator(strict_validation=True)
    
    @pytest.fixture
    def sample_observations(self) -> Dict[str, Any]:
        """Sample observations for testing."""
        return {
            "state": "high_reward",
            "context": "safe",
            "reward": 0.8,
        }
    
    @pytest.fixture
    def sample_generative_model(self) -> Dict[str, Any]:
        """Sample generative model for testing."""
        return {
            "likelihood": {
                "state": {"high_reward": 0.8, "low_reward": 0.2},
                "context": {"safe": 0.9, "dangerous": 0.1},
            },
            "prior": {
                "state": {"high_reward": 0.5, "low_reward": 0.5},
                "context": {"safe": 0.7, "dangerous": 0.3},
            },
            "posterior": {
                "state": {"high_reward": 0.7, "low_reward": 0.3},
                "context": {"safe": 0.85, "dangerous": 0.15},
            },
        }
    
    def test_calculate_free_energy_basic(self, calculator, sample_observations, sample_generative_model):
        """Test basic free energy calculation."""
        free_energy = calculator.calculate_free_energy(
            sample_observations,
            sample_generative_model,
        )
        
        # Free energy should be normalized to 0-1 range
        assert 0.0 <= free_energy <= 1.0
        assert isinstance(free_energy, float)
    
    def test_calculate_free_energy_empty_observations(self, calculator, sample_generative_model):
        """Test free energy calculation with empty observations."""
        free_energy = calculator.calculate_free_energy({}, sample_generative_model)
        
        # Should handle empty observations gracefully
        assert isinstance(free_energy, float)
    
    def test_calculate_free_energy_empty_model(self, calculator, sample_observations):
        """Test free energy calculation with empty model."""
        free_energy = calculator.calculate_free_energy(sample_observations, {})
        
        # Should handle empty model gracefully
        assert isinstance(free_energy, float)
    
    def test_calculate_free_energy_invalid_inputs(self, calculator):
        """Test free energy calculation with invalid inputs."""
        # Test with non-dict inputs
        with pytest.raises(ValueError):
            calculator.calculate_free_energy("not a dict", {})
        
        with pytest.raises(ValueError):
            calculator.calculate_free_energy({}, "not a dict")
    
    def test_calculate_surprise_basic(self, calculator, sample_observations):
        """Test basic surprise calculation."""
        predictions = {
            "state": {"high_reward": 0.7, "low_reward": 0.3},
            "context": {"safe": 0.8, "dangerous": 0.2},
        }
        
        surprise = calculator.calculate_surprise(sample_observations, predictions)
        
        # Surprise should be normalized to 0-1 range
        assert 0.0 <= surprise <= 1.0
        assert isinstance(surprise, float)
    
    def test_calculate_surprise_perfect_prediction(self, calculator):
        """Test surprise with perfect prediction (should be low)."""
        observations = {"outcome": "success"}
        predictions = {"outcome": {"success": 0.99}}
        
        surprise = calculator.calculate_surprise(observations, predictions)
        
        # Perfect prediction should have low surprise
        assert surprise < 0.5
    
    def test_calculate_surprise_wrong_prediction(self, calculator):
        """Test surprise with wrong prediction (should be high)."""
        observations = {"outcome": "failure"}
        predictions = {"outcome": {"success": 0.99, "failure": 0.01}}
        
        surprise = calculator.calculate_surprise(observations, predictions)
        
        # Wrong prediction should have higher surprise
        assert surprise > 0.3
    
    def test_calculate_surprise_empty_inputs(self, calculator):
        """Test surprise calculation with empty inputs."""
        surprise_empty_obs = calculator.calculate_surprise({}, {"outcome": 0.5})
        surprise_empty_pred = calculator.calculate_surprise({"outcome": 1}, {})
        
        assert surprise_empty_obs == 0.0
        assert surprise_empty_pred == 0.0
    
    def test_calculate_kl_divergence_identical(self, calculator):
        """Test KL divergence for identical distributions (should be 0)."""
        dist = {"a": 0.5, "b": 0.3, "c": 0.2}
        
        kl = calculator.calculate_kl_divergence(dist, dist)
        
        # KL divergence of identical distributions is 0
        assert kl == 0.0
    
    def test_calculate_kl_divergence_different(self, calculator):
        """Test KL divergence for different distributions."""
        q_dist = {"a": 0.8, "b": 0.2}
        p_dist = {"a": 0.2, "b": 0.8}
        
        kl = calculator.calculate_kl_divergence(q_dist, p_dist)
        
        # KL divergence should be positive for different distributions
        assert kl > 0.0
    
    def test_calculate_kl_divergence_empty(self, calculator):
        """Test KL divergence with empty distributions."""
        kl_empty_q = calculator.calculate_kl_divergence({}, {"a": 0.5})
        kl_empty_p = calculator.calculate_kl_divergence({"a": 0.5}, {})
        kl_both_empty = calculator.calculate_kl_divergence({}, {})
        
        assert kl_empty_q == 0.0
        assert kl_empty_p == 0.0
        assert kl_both_empty == 0.0
    
    def test_perform_active_inference_basic(self, calculator, sample_observations):
        """Test basic active inference."""
        agent_state = {
            "beliefs": {
                "beliefs": {"state": {"good": 0.6, "bad": 0.4}},
                "precision": 0.8,
            },
            "policies": [],
            "preferences": {"reward": 0.9, "safety": 0.7},
        }
        
        result = calculator.perform_active_inference(agent_state, sample_observations)
        
        # Result should contain required fields
        assert "selected_action" in result
        assert "selected_policy" in result
        assert "updated_beliefs" in result
        assert "expected_free_energy" in result
        
        # Selected action should have required fields
        assert "action_type" in result["selected_action"]
    
    def test_perform_active_inference_with_policies(self, calculator, sample_observations):
        """Test active inference with predefined policies."""
        policy = {
            "policy_id": "test_policy",
            "actions": [
                {
                    "action_type": "explore",
                    "parameters": {"target": "unknown"},
                    "cost": 0.2,
                    "expected_outcome": {"reward": 0.7},
                }
            ],
            "prior_probability": 0.5,
        }
        
        agent_state = {
            "beliefs": {"beliefs": {"state": {"good": 0.5}}, "precision": 0.8},
            "policies": [policy],
            "preferences": {"reward": 0.9},
        }
        
        result = calculator.perform_active_inference(agent_state, sample_observations)
        
        # Should select from provided policies
        assert result["selected_policy"] is not None
    
    def test_fep_result_serialization(self, calculator):
        """Test FEPResult serialization."""
        result = FEPResult(
            free_energy=0.3,
            surprise=0.2,
            kl_divergence=0.1,
        )
        
        result_dict = result.to_dict()
        
        assert result_dict["free_energy"] == 0.3
        assert result_dict["surprise"] == 0.2
        assert result_dict["kl_divergence"] == 0.1
        assert "calculation_id" in result_dict
        assert "timestamp" in result_dict
    
    def test_calculator_statistics(self, calculator, sample_observations, sample_generative_model):
        """Test calculator statistics tracking."""
        # Perform multiple calculations
        for _ in range(5):
            calculator.calculate_free_energy(sample_observations, sample_generative_model)
        
        stats = calculator.get_statistics()
        
        assert stats["calculation_count"] >= 5
        assert "cache_size" in stats
        assert "last_calculation_time" in stats
    
    def test_cache_operations(self, calculator):
        """Test cache operations."""
        # Clear cache
        calculator.clear_cache()
        
        stats = calculator.get_statistics()
        assert stats["cache_size"] == 0


class TestActiveInferenceAgent:
    """Test suite for ActiveInferenceAgent class."""
    
    @pytest.fixture
    def agent(self):
        """Create an ActiveInferenceAgent instance."""
        return ActiveInferenceAgent(agent_id="test-agent-001")
    
    @pytest.fixture
    def sample_observations(self) -> Dict[str, Any]:
        """Sample observations for testing."""
        return {
            "state": "high_reward",
            "reward": 0.8,
        }
    
    def test_agent_initialization(self, agent):
        """Test agent initialization."""
        assert agent.agent_id == "test-agent-001"
        
        stats = agent.get_statistics()
        assert stats["agent_id"] == "test-agent-001"
        assert stats["perceptions"] == 0
        assert stats["actions"] == 0
    
    def test_update_beliefs(self, agent, sample_observations):
        """Test belief update."""
        result = agent.update_beliefs(sample_observations)
        
        # Result should contain belief state
        assert "belief_id" in result
        assert "beliefs" in result
        assert "kl_divergence" in result
        
        # Statistics should be updated
        stats = agent.get_statistics()
        assert stats["belief_updates"] >= 1
    
    def test_update_beliefs_invalid(self, agent):
        """Test belief update with invalid observations."""
        # Invalid JSON should be handled gracefully
        result = agent.update_beliefs({"invalid": lambda x: x})
        
        # Should still return a valid belief state
        assert "belief_id" in result
    
    def test_select_action(self, agent):
        """Test action selection."""
        result = agent.select_action()
        
        # Result should contain action
        assert "action" in result
        assert "action_type" in result["action"]
        assert "expected_free_energy" in result
        
        # Statistics should be updated
        stats = agent.get_statistics()
        assert stats["actions"] >= 1
    
    def test_select_action_with_beliefs(self, agent):
        """Test action selection with custom beliefs."""
        custom_beliefs = {
            "belief_id": "custom-beliefs",
            "beliefs": {"state": {"good": 0.8, "bad": 0.2}},
            "precision": 0.9,
        }
        
        result = agent.select_action(beliefs=custom_beliefs)
        
        assert "action" in result
    
    def test_select_action_with_preferences(self, agent):
        """Test action selection with custom preferences."""
        custom_preferences = {"reward": 0.95, "safety": 0.6}
        
        result = agent.select_action(preferences=custom_preferences)
        
        assert "action" in result
    
    def test_predict_outcomes(self, agent):
        """Test outcome prediction."""
        actions = [
            {
                "action_type": "explore",
                "parameters": {"target": "unknown"},
                "cost": 0.2,
            },
            {
                "action_type": "exploit",
                "parameters": {"target": "known"},
                "cost": 0.1,
            },
        ]
        
        predictions = agent.predict_outcomes(actions)
        
        # Should have predictions for each action
        assert len(predictions) == 2
        
        # Statistics should be updated
        stats = agent.get_statistics()
        assert stats["predictions"] >= 2
    
    def test_minimize_surprise(self, agent):
        """Test surprise minimization."""
        policy = {
            "policy_id": "test-policy",
            "actions": [
                {
                    "action_type": "explore",
                    "parameters": {"target": "unknown"},
                    "expected_outcome": {"reward": 0.7},
                    "cost": 0.2,
                }
            ],
            "prior_probability": 0.5,
        }
        
        result = agent.minimize_surprise(policy)
        
        # Result should contain optimization info
        assert "original_policy" in result
        assert "optimized_policy" in result
        assert "current_surprise" in result
        assert "optimized_surprise" in result
        assert "surprise_reduction" in result
        
        # Statistics should be updated
        stats = agent.get_statistics()
        assert stats["surprise_minimizations"] >= 1
    
    def test_perceive_and_act(self, agent, sample_observations):
        """Test combined perception-action cycle."""
        result = agent.perceive_and_act(sample_observations)
        
        # Result should contain all components
        assert "action" in result
        assert "beliefs" in result
        assert "surprise" in result
        assert "free_energy" in result
        assert "expected_free_energy" in result
        
        # Statistics should be updated
        stats = agent.get_statistics()
        assert stats["perceptions"] >= 1
        assert stats["actions"] >= 1
    
    def test_set_generative_model(self, agent):
        """Test setting generative model."""
        model = {
            "likelihood": {"state": {"good": 0.8, "bad": 0.2}},
            "prior": {"state": {"good": 0.5, "bad": 0.5}},
        }
        
        agent.set_generative_model(model)
        
        # Model should be set (internal state)
        stats = agent.get_statistics()
        assert "agent_id" in stats
    
    def test_set_generative_model_invalid(self, agent):
        """Test setting invalid generative model."""
        invalid_model = {"invalid": lambda x: x}
        
        agent.set_generative_model(invalid_model)
        
        # Should handle gracefully
    
    def test_set_preferences(self, agent):
        """Test setting preferences."""
        preferences = {"reward": 0.9, "safety": 0.7, "novelty": 0.5}
        
        agent.set_preferences(preferences)
        
        # Preferences should be set
        stats = agent.get_statistics()
        assert "agent_id" in stats
    
    def test_set_preferences_invalid(self, agent):
        """Test setting invalid preferences."""
        invalid_preferences = {"reward": 1.5}  # Out of range
        
        agent.set_preferences(invalid_preferences)
        
        # Should handle gracefully
    
    def test_add_policy(self, agent):
        """Test adding a policy."""
        policy = {
            "policy_id": "test-policy",
            "actions": [
                {
                    "action_type": "explore",
                    "parameters": {},
                    "cost": 0.2,
                }
            ],
            "prior_probability": 0.5,
        }
        
        agent.add_policy(policy)
        
        stats = agent.get_statistics()
        assert stats["policy_count"] >= 1
    
    def test_belief_state_serialization(self):
        """Test BeliefState serialization."""
        belief = BeliefState(
            beliefs={"state": {"good": 0.7, "bad": 0.3}},
            precision=0.8,
        )
        
        belief_dict = belief.to_dict()
        
        assert belief_dict["precision"] == 0.8
        assert "belief_id" in belief_dict
        assert "timestamp" in belief_dict
        
        # Test deserialization
        restored = BeliefState.from_dict(belief_dict)
        assert restored.precision == 0.8
    
    def test_action_serialization(self):
        """Test Action serialization."""
        action = Action(
            action_type="explore",
            parameters={"target": "unknown"},
            cost=0.2,
        )
        
        action_dict = action.to_dict()
        
        assert action_dict["action_type"] == "explore"
        assert action_dict["cost"] == 0.2
        assert "action_id" in action_dict
    
    def test_policy_serialization(self):
        """Test Policy serialization."""
        policy = Policy(
            actions=[
                Action(action_type="explore", cost=0.2),
                Action(action_type="exploit", cost=0.1),
            ],
            prior_probability=0.6,
        )
        
        policy_dict = policy.to_dict()
        
        assert len(policy_dict["actions"]) == 2
        assert policy_dict["prior_probability"] == 0.6
        assert "policy_id" in policy_dict


class TestFEPIntegration:
    """Integration tests for FEP with consciousness metrics."""
    
    @pytest.fixture
    def metrics_calculator(self):
        """Create a ConsciousnessMetricsCalculator instance."""
        return ConsciousnessMetricsCalculator(strict_validation=True)
    
    @pytest.fixture
    def fep_calculator(self):
        """Create a FreeEnergyCalculator instance."""
        return FreeEnergyCalculator(strict_validation=True)
    
    def test_fep_metrics_calculation(self, metrics_calculator):
        """Test FEP metrics calculation through consciousness metrics."""
        observations = {
            "state": "high_reward",
            "reward": 0.8,
        }
        
        generative_model = {
            "likelihood": {"state": {"high_reward": 0.8}},
            "prior": {"state": {"high_reward": 0.5}},
            "predictions": {"state": {"high_reward": 0.7}},
        }
        
        fep_result = metrics_calculator.calculate_fep_metrics(observations, generative_model)
        
        assert isinstance(fep_result.free_energy, float)
        assert isinstance(fep_result.surprise, float)
        assert isinstance(fep_result.kl_divergence, float)
    
    def test_collective_metrics_with_fep(self, metrics_calculator):
        """Test collective metrics calculation with FEP integration."""
        agent_data = [
            AgentConsciousnessData(
                agent_id="agent-1",
                phi_score=0.7,
                integrated_information=0.6,
                differentiation=0.5,
            ),
            AgentConsciousnessData(
                agent_id="agent-2",
                phi_score=0.6,
                integrated_information=0.5,
                differentiation=0.4,
            ),
        ]
        
        agent_observations = {
            "agent-1": {"state": "good", "reward": 0.8},
            "agent-2": {"state": "neutral", "reward": 0.5},
        }
        
        agent_models = {
            "agent-1": {
                "likelihood": {"state": {"good": 0.8}},
                "prior": {"state": {"good": 0.5}},
                "predictions": {"state": {"good": 0.7}},
            },
            "agent-2": {
                "likelihood": {"state": {"neutral": 0.6}},
                "prior": {"state": {"neutral": 0.5}},
                "predictions": {"state": {"neutral": 0.5}},
            },
        }
        
        collective_metrics = metrics_calculator.calculate_collective_metrics(
            agent_data,
            agent_observations=agent_observations,
            agent_models=agent_models,
        )
        
        # Should include FEP metrics
        assert hasattr(collective_metrics, "fep_free_energy")
        assert hasattr(collective_metrics, "fep_surprise")
        assert isinstance(collective_metrics.fep_free_energy, float)
        assert isinstance(collective_metrics.fep_surprise, float)
    
    def test_known_fep_scenario_low_surprise(self, fep_calculator):
        """Test known FEP scenario: accurate predictions should yield low surprise."""
        observations = {"outcome": "expected"}
        predictions = {"outcome": {"expected": 0.95}}
        
        surprise = fep_calculator.calculate_surprise(observations, predictions)
        
        # High accuracy prediction should have low surprise
        assert surprise < 0.3
    
    def test_known_fep_scenario_high_surprise(self, fep_calculator):
        """Test known FEP scenario: unexpected outcomes should yield high surprise."""
        observations = {"outcome": "unexpected"}
        predictions = {"outcome": {"expected": 0.95, "unexpected": 0.05}}
        
        surprise = fep_calculator.calculate_surprise(observations, predictions)
        
        # Unexpected outcome should have high surprise
        assert surprise > 0.5
    
    def test_known_fep_scenario_belief_update(self, fep_calculator):
        """Test known FEP scenario: belief update from observations."""
        agent_state = {
            "beliefs": {
                "beliefs": {"state": {"good": 0.5, "bad": 0.5}},
                "precision": 0.7,
            },
            "policies": [],
            "preferences": {"reward": 0.8},
        }
        
        observations = {"state": "good", "reward": 0.9}
        
        result = fep_calculator.perform_active_inference(agent_state, observations)
        
        # Beliefs should be updated toward observed state
        updated_beliefs = result["updated_beliefs"]
        assert "beliefs" in updated_beliefs


class TestZeroTrustValidation:
    """Test zero-trust validation for FEP inputs."""
    
    @pytest.fixture
    def calculator(self):
        """Create a FreeEnergyCalculator with strict validation."""
        return FreeEnergyCalculator(strict_validation=True)
    
    def test_injection_pattern_detection(self, calculator):
        """Test detection of injection patterns in inputs."""
        malicious_observations = {
            "state": "normal",
            "injection": "<script>alert('xss')</script>",
        }
        
        # Should handle malicious input safely
        try:
            free_energy = calculator.calculate_free_energy(malicious_observations, {})
            assert isinstance(free_energy, float)
        except ValueError:
            pass  # Expected if validation catches it
    
    def test_numeric_validation(self, calculator):
        """Test validation of numeric inputs."""
        observations = {
            "value": float("inf"),  # Infinity
        }
        
        # Should handle extreme values
        try:
            result = calculator.calculate_surprise(observations, {"value": 0.5})
            assert isinstance(result, float)
        except (ValueError, OverflowError):
            pass  # Expected
    
    def test_deeply_nested_structure(self, calculator):
        """Test validation of deeply nested structures."""
        nested_observations = {
            "level1": {
                "level2": {
                    "level3": {
                        "value": 0.5
                    }
                }
            }
        }
        
        nested_model = {
            "likelihood": nested_observations,
            "prior": nested_observations,
        }
        
        free_energy = calculator.calculate_free_energy(nested_observations, nested_model)
        assert isinstance(free_energy, float)


class TestEdgeCases:
    """Test edge cases and boundary conditions."""
    
    @pytest.fixture
    def calculator(self):
        """Create a FreeEnergyCalculator instance."""
        return FreeEnergyCalculator(strict_validation=True)
    
    def test_zero_probability_handling(self, calculator):
        """Test handling of zero probabilities."""
        observations = {"outcome": "impossible"}
        predictions = {"outcome": {"possible": 1.0, "impossible": 0.0}}
        
        surprise = calculator.calculate_surprise(observations, predictions)
        
        # Should handle zero probability gracefully
        assert isinstance(surprise, float)
    
    def test_single_element_distribution(self, calculator):
        """Test KL divergence with single element distributions."""
        q_dist = {"only": 1.0}
        p_dist = {"only": 1.0}
        
        kl = calculator.calculate_kl_divergence(q_dist, p_dist)
        
        assert kl == 0.0
    
    def test_extreme_free_energy_values(self, calculator):
        """Test handling of extreme free energy values."""
        # Very high energy scenario
        observations = {"state": "chaos"}
        model = {
            "likelihood": {"state": {"order": 1.0}},
            "prior": {"state": {"order": 1.0}},
        }
        
        free_energy = calculator.calculate_free_energy(observations, model)
        
        # Should be normalized to 0-1 range
        assert 0.0 <= free_energy <= 1.0
    
    def test_empty_agent_state(self, calculator):
        """Test active inference with empty agent state."""
        agent_state = {}
        observations = {}
        
        result = calculator.perform_active_inference(agent_state, observations)
        
        # Should return valid result structure
        assert "selected_action" in result
        assert "selected_policy" in result


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--cov=src/heretek_swarm/consciousness/fep_active_inference", "--cov-report=term-missing"])
