"""
FEP Active Inference Module - Free Energy Principle Implementation.

This module implements the Free Energy Principle (FEP) for active inference
and surprise minimization in agent swarms. FEP provides a mathematical
framework for understanding how agents minimize surprise (variational free energy)
through perception and action.

Key Concepts:
- Variational Free Energy: Upper bound on surprise
- Bayesian Surprise: Information gain from belief updates
- KL Divergence: Distance between probability distributions
- Active Inference: Action selection minimizing expected free energy
- Generative Model: Agent's internal model of the world

References:
- Friston, K. (2010). The free-energy principle: a unified brain theory.
- Friston, K., et al. (2017). Active inference: a process theory.
- Parr, T., et al. (2022). Active inference: the free energy principle in mind, brain, and behavior.

Author: Heretek Swarm Collective
Date: 2026-04-07
Version: 1.0.0
"""

import math
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

import structlog

from ..security.zero_trust import ZeroTrustValidator
from ..validation.llm_output import LLMOutputValidator, ValidationResult, ValidationSeverity

_logger = structlog.get_logger("FEPActiveInference")


@dataclass
class BeliefState:
    """
    Represents an agent's belief state about the world.
    
    Attributes:
        belief_id: Unique identifier for this belief state
        beliefs: Dictionary mapping state variables to probability distributions
        precision: Confidence in beliefs (0.0-1.0)
        timestamp: Creation/update timestamp
        prior: Prior belief distribution
        posterior: Updated belief distribution after observation
    """
    belief_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    beliefs: Dict[str, Dict[str, float]] = field(default_factory=dict)
    precision: float = 1.0
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    prior: Dict[str, float] = field(default_factory=dict)
    posterior: Dict[str, float] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "belief_id": self.belief_id,
            "beliefs": self.beliefs,
            "precision": self.precision,
            "timestamp": self.timestamp,
            "prior": self.prior,
            "posterior": self.posterior,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "BeliefState":
        """Create from dictionary."""
        return cls(
            _belief_id = data.get("belief_id", str(uuid.uuid4())),
            beliefs=data.get("beliefs", {}),
            precision=data.get("precision", 1.0),
            timestamp=data.get("timestamp", datetime.now(timezone.utc).isoformat()),
            prior=data.get("prior", {}),
            posterior=data.get("posterior", {}),
        )


@dataclass
class Action:
    """
    Represents an action that an agent can take.
    
    Attributes:
        action_id: Unique identifier
        action_type: Type/category of action
        parameters: Action-specific parameters
        expected_outcome: Predicted outcome distribution
        cost: Action cost (energy, resources, etc.)
        policy_id: Associated policy identifier
    """
    action_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    action_type: str = "default"
    parameters: Dict[str, Any] = field(default_factory=dict)
    expected_outcome: Dict[str, float] = field(default_factory=dict)
    cost: float = 0.0
    policy_id: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "action_id": self.action_id,
            "action_type": self.action_type,
            "parameters": self.parameters,
            "expected_outcome": self.expected_outcome,
            "cost": self.cost,
            "policy_id": self.policy_id,
        }


@dataclass
class Policy:
    """
    Represents a sequence of actions (policy) for achieving a goal.
    
    Attributes:
        policy_id: Unique policy identifier
        actions: Sequence of actions in the policy
        expected_free_energy: Expected free energy of following this policy
        prior_probability: Prior probability of this policy being optimal
        value: Expected value/utility of this policy
    """
    policy_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    actions: List[Action] = field(default_factory=list)
    expected_free_energy: float = 0.0
    prior_probability: float = 0.5
    value: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "policy_id": self.policy_id,
            "actions": [a.to_dict() for a in self.actions],
            "expected_free_energy": self.expected_free_energy,
            "prior_probability": self.prior_probability,
            "value": self.value,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Policy":
        """Create from dictionary."""
        actions = []
        for action_data in data.get("actions", []):
            if isinstance(action_data, Action):
                actions.append(action_data)
            elif isinstance(action_data, dict):
                actions.append(Action(**action_data))
        
        return cls(
            policy_id=data.get("policy_id", str(uuid.uuid4())),
            actions=actions,
            expected_free_energy=data.get("expected_free_energy", 0.0),
            prior_probability=data.get("prior_probability", 0.5),
            value=data.get("value", 0.0),
        )


@dataclass
class FEPResult:
    """
    Result of Free Energy Principle calculation.
    
    Attributes:
        calculation_id: Unique identifier for this calculation
        free_energy: Calculated variational free energy value
        surprise: Bayesian surprise value
        kl_divergence: KL divergence between distributions
        belief_update: Updated belief state
        selected_action: Action selected via active inference
        policy: Policy used for action selection
        timestamp: Calculation timestamp
        metadata: Additional metadata about the calculation
    """
    calculation_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    free_energy: float = 0.0
    surprise: float = 0.0
    kl_divergence: float = 0.0
    belief_update: Optional[BeliefState] = None
    selected_action: Optional[Action] = None
    policy: Optional[Policy] = None
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "calculation_id": self.calculation_id,
            "free_energy": self.free_energy,
            "surprise": self.surprise,
            "kl_divergence": self.kl_divergence,
            "belief_update": self.belief_update.to_dict() if self.belief_update else None,
            "selected_action": self.selected_action.to_dict() if self.selected_action else None,
            "policy": self.policy.to_dict() if self.policy else None,
            "timestamp": self.timestamp,
            "metadata": self.metadata,
        }


class FreeEnergyCalculator:
    """
    Free Energy Principle Calculator for Active Inference.
    
    This class implements the core FEP calculations for measuring and minimizing
    variational free energy in agent systems. The calculator provides:
    
    1. Variational free energy calculation from observations and generative models
    2. Bayesian surprise computation for belief updates
    3. KL divergence between probability distributions
    4. Active inference for action selection
    
    The Free Energy Principle states that agents minimize variational free energy,
    which is an upper bound on surprise (negative log model evidence).
    
    Example:
        ```python
        _calculator = FreeEnergyCalculator()
        
        # Define observations and generative model
        _observations = {"state": "high_reward", "context": "safe"}
        _generative_model = {
            "likelihood": {"state": {"high_reward": 0.8, "low_reward": 0.2}},
            "prior": {"state": {"high_reward": 0.5, "low_reward": 0.5}},
        }
        
        # Calculate free energy
        _free_energy = calculator.calculate_free_energy(observations, generative_model)
        
        # Calculate surprise
        _predictions = {"state": {"high_reward": 0.6, "low_reward": 0.4}}
        _surprise = calculator.calculate_surprise(observations, predictions)
        ```
    """
    
    # Free energy thresholds for classification
    FREE_ENERGY_THRESHOLDS = {
        "very_low": 0.1,
        "low": 0.3,
        "moderate": 0.5,
        "high": 0.7,
        "very_high": 0.9,
    }
    
    # Surprise thresholds
    SURPRISE_THRESHOLDS = {
        "minimal": 0.1,
        "low": 0.3,
        "moderate": 0.5,
        "high": 0.7,
        "extreme": 0.9,
    }
    
    def __init__(self, strict_validation: bool):
        """
        Initialize the Free Energy calculator.
        
        Args:
            strict_validation: If True, strictly validate all inputs
        """
        self._validator = LLMOutputValidator(strict_mode=strict_validation)
        self._zero_trust = ZeroTrustValidator()
        self._cache: Dict[str, FEPResult] = {}
        self._calculation_count = 0
        self._last_calculation_time: Optional[datetime] = None
        
        logger.info("FreeEnergyCalculator initialized", extra={"strict_validation": strict_validation})
    
    def calculate_free_energy(self, observations: Dict[str, Any], generative_model: Dict[str, Any]) -> float:
        """
        Calculate variational free energy from observations and generative model.
        
        Variational free energy F is defined as:
        F = E_q[log q(s) - log p(o,s)]
          = D_KL[q(s) || p(s|o)] - log p(o)
          = D_KL[q(s) || p(s)] - E_q[log p(o|s)]
        
        Where:
        - q(s) is the approximate posterior (recognition density)
        - p(o,s) is the joint distribution (generative model)
        - p(o|s) is the likelihood
        - p(s) is the prior
        
        Args:
            observations: Observed data o
            generative_model: Model containing 'likelihood' and 'prior' distributions
            
        Returns:
            Variational free energy value (lower is better)
            
        Raises:
            ValueError: If inputs are invalid
        """
        _start_time = datetime.now(timezone.utc)
        
        # Zero-trust validation
        _validation_result = self._validate_inputs(observations, generative_model)
        if not validation_result.valid:
            raise ValueError(f"Invalid inputs: {validation_result.errors}")
        
        # Extract model components
        _likelihood = generative_model.get("likelihood", {})
        prior = generative_model.get("prior", {})
        posterior = generative_model.get("posterior", prior)  # Use prior if posterior not provided
        
        # Calculate expected energy (negative log likelihood)
        _expected_energy = self._calculate_expected_energy(observations, likelihood)
        
        # Calculate entropy of posterior
        _entropy = self._calculate_entropy(posterior)
        
        # Calculate KL divergence from prior to posterior
        _kl_divergence = self.calculate_kl_divergence(posterior, prior)
        
        # Free energy = expected energy - entropy + KL divergence
        _free_energy = expected_energy - entropy + kl_divergence
        
        # Normalize to 0-1 range for consistency
        _normalized_free_energy = self._normalize_free_energy(free_energy)
        
        # Cache result
        self._calculation_count += 1
        self._last_calculation_time = datetime.now(timezone.utc)
        
        logger.debug(
            "Free energy calculated",
            _extra = {
                "free_energy": normalized_free_energy,
                "expected_energy": expected_energy,
                "entropy": entropy,
                "kl_divergence": kl_divergence,
            },
        )
        
        return normalized_free_energy
    
    def calculate_surprise(self, observations: Dict[str, Any], predictions: Dict[str, Any]) -> float:
        """
        Calculate Bayesian surprise from observations and predictions.
        
        Bayesian surprise measures the information gain from updating beliefs
        based on new observations. It is defined as the KL divergence between
        posterior and prior beliefs:
        
        _Surprise = D_KL[p(s|o) || p(s)]
        
        High surprise indicates significant belief update is needed.
        
        Args:
            observations: Observed data
            predictions: Predicted probability distribution over outcomes
            
        Returns:
            Bayesian surprise value (0.0-1.0, higher = more surprising)
        """
        # Validate inputs
        if not observations or not predictions:
            logger.warning("Empty observations or predictions")
            return 0.0
        
        # Calculate negative log probability of observations under predictions
        _surprise = 0.0
        
        for key, obs_value in observations.items():
            if key in predictions:
                _pred_dist = predictions[key]
                if isinstance(pred_dist, dict):
                    # Get probability of observed value
                    _prob = pred_dist.get(str(obs_value), pred_dist.get(obs_value, 0.0))
                    if prob > 0:
                        surprise -= math.log(prob + 1e-10)
                    else:
                        surprise += 10.0  # High surprise for zero probability
                elif isinstance(pred_dist, (int, float)):
                    # Single probability value
                    _prob = pred_dist
                    if prob > 0:
                        surprise -= math.log(prob + 1e-10)
                    else:
                        surprise += 10.0
        
        # Normalize surprise to 0-1 range
        _normalized_surprise = self._normalize_surprise(surprise)
        
        logger.debug("Surprise calculated", extra={"surprise": normalized_surprise})
        
        return normalized_surprise
    
    def calculate_kl_divergence(self, q_distribution: Dict[str, Any], p_distribution: Dict[str, Any]) -> float:
        """
        Calculate Kullback-Leibler divergence between two distributions.
        
        KL divergence D_KL[q || p] measures how much q diverges from p:
        
        D_KL[q || p] = Σ q(x) * log(q(x) / p(x))
        
        Properties:
        - Non-negative: D_KL >= 0
        - Zero iff q = p everywhere
        - Not symmetric: D_KL[q || p] != D_KL[p || q]
        
        Args:
            q_distribution: Approximate/reference distribution q
            p_distribution: True/target distribution p
            
        Returns:
            KL divergence value (>= 0, 0 means distributions are identical)
        """
        if not q_distribution or not p_distribution:
            return 0.0
        
        _kl_div = 0.0
        
        # Flatten distributions if nested
        _q_flat = self._flatten_distribution(q_distribution)
        _p_flat = self._flatten_distribution(p_distribution)
        
        # Calculate KL divergence
        for key, q_prob in q_flat.items():
            if q_prob > 0:
                _p_prob = p_flat.get(key, 0.0)
                if p_prob > 0:
                    kl_div += q_prob * math.log(q_prob / (p_prob + 1e-10))
                else:
                    kl_div += q_prob * 10.0  # High penalty for zero probability
        
        return max(0.0, kl_div)
    
    def perform_active_inference(self, agent_state: Dict[str, Any], observations: Dict[str, Any]) -> Dict[str, Any]:
        """
        Perform active inference for action selection.
        
        Active inference selects actions that minimize expected free energy:
        
        π* = argmin_π E[G(π)]
        
        Where G(π) is the expected free energy of policy π:
        G(π) = E[F(o,s) | π]
        
        This involves:
        1. Updating beliefs based on observations
        2. Generating candidate policies
        3. Evaluating expected free energy for each policy
        4. Selecting the policy with minimum expected free energy
        
        Args:
            agent_state: Current agent state including beliefs, policies, preferences
            observations: Current observations
            
        Returns:
            Dictionary with selected action, updated beliefs, and policy info
        """
        # Extract agent components
        _beliefs_data = agent_state.get("beliefs", {})
        _policies_data = agent_state.get("policies", [])
        _preferences = agent_state.get("preferences", {})
        
        # Create belief state
        _current_beliefs = BeliefState.from_dict(beliefs_data) if beliefs_data else BeliefState()
        
        # Update beliefs based on observations
        _updated_beliefs = self._update_beliefs_from_observations(current_beliefs, observations)
        
        # Generate candidate policies if not provided
        if not policies_data:
            _policies = self._generate_default_policies(observations, preferences)
        else:
            _policies = [Policy.from_dict(p) if isinstance(p, dict) else p for p in policies_data]
        
        # Evaluate expected free energy for each policy
        policy_evaluations: List[Tuple[Policy, float]] = []
        for policy in policies:
            _efe = self._calculate_expected_free_energy(policy, updated_beliefs, preferences)
            policy.expected_free_energy = efe
            policy_evaluations.append((policy, efe))
        
        # Select policy with minimum expected free energy
        if policy_evaluations:
            selected_policy, min_efe = min(policy_evaluations, key=lambda x: x[1])
            _selected_action = selected_policy.actions[0] if selected_policy.actions else Action()
        else:
            _selected_policy = Policy()
            _selected_action = Action()
            _min_efe = 0.0
        
        _result = {
            "selected_action": selected_action.to_dict(),
            "selected_policy": selected_policy.to_dict(),
            "updated_beliefs": updated_beliefs.to_dict(),
            "expected_free_energy": min_efe,
            "policy_evaluations": [(p.to_dict(), efe) for p, efe in policy_evaluations],
        }
        
        logger.info(
            "Active inference performed",
            _extra = {
                "selected_action": selected_action.action_type,
                "expected_free_energy": min_efe,
            },
        )
        
        return result
    
    def _validate_inputs(self, observations: Dict[str, Any], generative_model: Dict[str, Any]) -> ValidationResult:
        """
        Validate inputs using zero-trust validation.
        
        Args:
            observations: Observations to validate
            generative_model: Generative model to validate
            
        Returns:
            ValidationResult with validation status
        """
        errors: List[str] = []
        warnings: List[str] = []
        
        # Validate observations
        if not isinstance(observations, dict):
            errors.append("Observations must be a dictionary")
        
        # Validate generative model structure
        if not isinstance(generative_model, dict):
            errors.append("Generative model must be a dictionary")
        else:
            # Check for required components
            if "likelihood" not in generative_model:
                warnings.append("Generative model missing 'likelihood' component")
            if "prior" not in generative_model:
                warnings.append("Generative model missing 'prior' component")
        
        # Check for dangerous patterns
        _obs_str = str(observations)
        _model_str = str(generative_model)
        
        _safety_result = self._validator.validate_text(obs_str, content_type="json")
        if not safety_result.valid:
            errors.extend(safety_result.errors)
        
        _safety_result = self._validator.validate_text(model_str, content_type="json")
        if not safety_result.valid:
            errors.extend(safety_result.errors)
        
        _severity = ValidationSeverity.CRITICAL if errors else (
            ValidationSeverity.WARNING if warnings else ValidationSeverity.INFO
        )
        
        return ValidationResult(
            valid=len(errors) == 0,
            _content = {"observations": observations, "generative_model": generative_model},
            errors=errors,
            _warnings = warnings,
            _severity = severity,
        )
    
    def _calculate_expected_energy(self, observations: Dict[str, Any], likelihood: Dict[str, Any]) -> float:
        """
        Calculate expected energy (negative log likelihood).
        
        Args:
            observations: Observed data
            likelihood: Likelihood distribution p(o|s)
            
        Returns:
            Expected energy value
        """
        _energy = 0.0
        
        for key, obs_value in observations.items():
            if key in likelihood:
                _like_dist = likelihood[key]
                if isinstance(like_dist, dict):
                    # Handle case where obs_value might be a dict (nested structure)
                    if isinstance(obs_value, dict):
                        # For nested observations, use a default probability
                        _prob = 0.5
                    else:
                        _prob = like_dist.get(str(obs_value), like_dist.get(obs_value, 0.0))
                    
                    if prob > 0:
                        energy -= math.log(prob + 1e-10)
                    else:
                        energy += 10.0  # High energy for impossible observation
                elif isinstance(like_dist, (int, float)):
                    if like_dist > 0:
                        energy -= math.log(like_dist + 1e-10)
                    else:
                        energy += 10.0
        
        return energy
    
    def _calculate_entropy(self, distribution: Dict[str, Any]) -> float:
        """
        Calculate Shannon entropy of a probability distribution.
        
        H = -Σ p(x) * log(p(x))
        
        Args:
            distribution: Probability distribution
            
        Returns:
            Entropy value (higher = more uncertain)
        """
        if not distribution:
            return 0.0
        
        _entropy = 0.0
        _flat_dist = self._flatten_distribution(distribution)
        
        for prob in flat_dist.values():
            if prob > 0:
                entropy -= prob * math.log2(prob + 1e-10)
        
        return entropy
    
    def _flatten_distribution(self, distribution: Dict[str, Any]) -> Dict[str, float]:
        """
        Flatten nested distribution to single-level dictionary.
        
        Args:
            distribution: Potentially nested distribution
            
        Returns:
            Flattened distribution
        """
        flat: Dict[str, float] = {}
        
        def flatten(d: Dict[str, Any], prefix: str):
            for key, value in d.items():
                _new_key = f"{prefix}.{key}" if prefix else key
                if isinstance(value, dict):
                    flatten(value, new_key)
                elif isinstance(value, (int, float)):
                    flat[new_key] = float(value)
        
        flatten(distribution)
        return flat
    
    def _normalize_free_energy(self, free_energy: float) -> float:
        """
        Normalize free energy to 0.0-1.0 range using sigmoid.
        
        Args:
            free_energy: Raw free energy value
            
        Returns:
            Normalized free energy
        """
        # Sigmoid normalization
        _normalized = 1.0 / (1.0 + math.exp(-free_energy + 2.5))
        return min(1.0, max(0.0, normalized))
    
    def _normalize_surprise(self, surprise: float) -> float:
        """
        Normalize surprise to 0.0-1.0 range.
        
        Args:
            surprise: Raw surprise value
            
        Returns:
            Normalized surprise
        """
        # Log-based normalization
        _normalized = math.tanh(surprise / 5.0)
        return min(1.0, max(0.0, normalized))
    
    def _update_beliefs_from_observations(self, current_beliefs: BeliefState, observations: Dict[str, Any]) -> BeliefState:
        """
        Update beliefs based on new observations (Bayesian update).
        
        Args:
            current_beliefs: Current belief state
            observations: New observations
            
        Returns:
            Updated belief state
        """
        _updated = BeliefState(
            _belief_id = str(uuid.uuid4()),
            beliefs=current_beliefs.beliefs.copy(),
            precision=current_beliefs.precision,
            prior=current_beliefs.posterior or current_beliefs.beliefs,
        )
        
        # Simple Bayesian update: weighted average of prior and observation
        for key, obs_value in observations.items():
            if key in updated.beliefs:
                _prior_dist = updated.beliefs[key]
                # Update based on observation (simplified)
                if isinstance(prior_dist, dict):
                    _obs_key = str(obs_value)
                    if obs_key in prior_dist:
                        # Increase probability of observed state
                        for k in prior_dist:
                            if k == obs_key:
                                prior_dist[k] = min(1.0, prior_dist[k] * 1.5)
                            else:
                                prior_dist[k] = max(0.0, prior_dist[k] * 0.8)
                        
                        # Normalize
                        _total = sum(prior_dist.values())
                        if total > 0:
                            updated.beliefs[key] = {k: v / total for k, v in prior_dist.items()}
                    updated.posterior = updated.beliefs[key]
        
        return updated
    
    def _generate_default_policies(self, _observations: Dict[str, Any], _preferences: Dict[str, Any]) -> List[Policy]:
        """
        Generate default policies based on observations and preferences.
        
        Args:
            observations: Current observations
            preferences: Agent preferences
            
        Returns:
            List of candidate policies
        """
        policies: List[Policy] = []
        
        # Generate explore policy
        _explore_action = Action(
            action_type="explore",
            parameters={"target": "unknown"},
            cost=0.2,
        )
        _explore_policy = Policy(
            actions=[explore_action],
            prior_probability=0.3,
        )
        policies.append(explore_policy)
        
        # Generate exploit policy
        _exploit_action = Action(
            action_type="exploit",
            parameters={"target": "known_reward"},
            cost=0.1,
        )
        _exploit_policy = Policy(
            actions=[exploit_action],
            prior_probability=0.5,
        )
        policies.append(exploit_policy)
        
        # Generate minimize surprise policy
        _surprise_action = Action(
            action_type="minimize_surprise",
            parameters={"target": "predicted_state"},
            cost=0.15,
        )
        _surprise_policy = Policy(
            actions=[surprise_action],
            prior_probability=0.4,
        )
        policies.append(surprise_policy)
        
        return policies
    
    def _calculate_expected_free_energy(self, policy: Policy, _beliefs: BeliefState, preferences: Dict[str, Any]) -> float:
        """
        Calculate expected free energy for a policy.
        
        Expected free energy G combines:
        - Risk: Divergence from preferred outcomes
        - Ambiguity: Uncertainty about outcomes
        
        G(π) = Risk(π) + Ambiguity(π)
        
        Args:
            policy: Policy to evaluate
            beliefs: Current beliefs
            preferences: Preferred outcomes
            
        Returns:
            Expected free energy value
        """
        # Calculate risk (divergence from preferences)
        _risk = 0.0
        for action in policy.actions:
            _outcome = action.expected_outcome
            for key, pref_value in preferences.items():
                if key in outcome:
                    risk += abs(outcome[key] - pref_value)
        
        # Calculate ambiguity (uncertainty)
        _ambiguity = 0.0
        for action in policy.actions:
            _outcome = action.expected_outcome
            _outcome_dist = {k: v for k, v in outcome.items() if isinstance(v, (int, float))}
            if outcome_dist:
                _total = sum(outcome_dist.values())
                if total > 0:
                    _normalized = {k: v / total for k, v in outcome_dist.items()}
                    ambiguity += self._calculate_entropy(normalized)
        
        # Combine with policy cost
        _total_cost = sum(a.cost for a in policy.actions)
        
        # Expected free energy
        _efe = risk + ambiguity + total_cost * 0.1
        
        return efe
    
    def get_cached_result(self, calculation_id: str) -> Optional[FEPResult]:
        """
        Get cached FEP calculation result.
        
        Args:
            calculation_id: Calculation identifier
            
        Returns:
            Cached result or None
        """
        return self._cache.get(calculation_id)
    
    def clear_cache(self) -> None:
        """Clear all cached results."""
        self._cache.clear()
        logger.info("FreeEnergyCalculator cache cleared")
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get calculator statistics.
        
        Returns:
            Dictionary with calculation statistics
        """
        return {
            "calculation_count": self._calculation_count,
            "cache_size": len(self._cache),
            "last_calculation_time": (
                self._last_calculation_time.isoformat()
                if self._last_calculation_time
                else None
            ),
        }


class ActiveInferenceAgent:
    """
    Active Inference Agent implementing FEP-based decision making.
    
    This agent class implements active inference for perception and action:
    
    1. Perceive observations from the environment
    2. Update beliefs using variational inference
    3. Select actions that minimize expected free energy
    4. Predict outcomes from generative model
    5. Minimize surprise through policy optimization
    
    The agent maintains a generative model of the world and uses it to:
    - Predict future observations
    - Evaluate potential actions
    - Update beliefs based on prediction errors
    
    Example:
        ```python
        agent = ActiveInferenceAgent(agent_id="agent-001")
        
        # Set up generative model
        agent.set_generative_model({
            "likelihood": {"state": {"good": 0.8, "bad": 0.2}},
            "prior": {"state": {"good": 0.5, "bad": 0.5}},
        })
        
        # Set preferences
        agent.set_preferences({"reward": 0.9, "safety": 0.8})
        
        # Perceive and act
        _observations = {"state": "good", "reward": 0.7}
        action = agent.perceive_and_act(observations)
        ```
    """
    
    def __init__(self, agent_id: str, calculator: Optional[FreeEnergyCalculator], strict_validation: bool):
        """
        Initialize the active inference agent.
        
        Args:
            agent_id: Unique agent identifier
            calculator: Optional FreeEnergyCalculator (created if not provided)
            strict_validation: If True, strictly validate all inputs
        """
        self.agent_id = agent_id
        self._calculator = calculator or FreeEnergyCalculator(strict_validation=strict_validation)
        self._validator = LLMOutputValidator(strict_mode=strict_validation)
        
        # Agent state
        self._beliefs = BeliefState()
        self._generative_model: Dict[str, Any] = {}
        self._preferences: Dict[str, float] = {}
        self._policies: List[Policy] = []
        
        # History for learning
        self._observation_history: List[Dict[str, Any]] = []
        self._action_history: List[Action] = []
        self._prediction_history: List[Dict[str, Any]] = []
        
        # Statistics
        self._stats = {
            "perceptions": 0,
            "actions": 0,
            "belief_updates": 0,
            "predictions": 0,
            "surprise_minimizations": 0,
        }
        
        logger.info("ActiveInferenceAgent initialized", extra={"agent_id": agent_id})
    
    def update_beliefs(self, observations: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update beliefs based on new observations using variational inference.
        
        This implements approximate Bayesian inference:
        q(s) = argmin_q D_KL[q(s) || p(s|o)]
        
        Where q(s) is the approximate posterior that minimizes KL divergence
        from the true posterior p(s|o).
        
        Args:
            observations: New observations from the environment
            
        Returns:
            Updated belief state as dictionary
        """
        # Validate observations
        _validation = self._validator.validate_text(str(observations), content_type="json")
        if not validation.valid:
            logger.warning("Invalid observations", extra={"errors": validation.errors})
            return self._beliefs.to_dict()
        
        # Store prior
        self._beliefs.prior = self._beliefs.posterior or self._beliefs.beliefs
        
        # Update beliefs using the calculator
        self._beliefs = self._calculator._update_beliefs_from_observations(
            self._beliefs, observations
        )
        
        # Calculate KL divergence (measure of belief update)
        _kl_div = self._calculator.calculate_kl_divergence(
            self._beliefs.posterior,
            self._beliefs.prior,
        )
        
        # Update statistics
        self._stats["belief_updates"] += 1
        
        # Store observation in history
        self._observation_history.append(observations)
        
        logger.debug(
            "Beliefs updated",
            _extra = {
                "agent_id": self.agent_id,
                "kl_divergence": kl_div,
                "precision": self._beliefs.precision,
            },
        )
        
        return {
            **self._beliefs.to_dict(),
            "kl_divergence": kl_div,
        }
    
    def select_action(self, beliefs: Optional[Dict[str, Any]], preferences: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Select action that minimizes expected free energy.
        
        Action selection follows the active inference principle:
        π* = argmin_π E[G(π)]
        
        Where G(π) is the expected free energy of policy π.
        
        Args:
            beliefs: Optional belief state (uses current if not provided)
            preferences: Optional preferences (uses current if not provided)
            
        Returns:
            Selected action as dictionary with metadata
        """
        # Use current beliefs/preferences if not provided
        _belief_state = BeliefState.from_dict(beliefs) if beliefs else self._beliefs
        _agent_prefs = preferences or self._preferences
        
        # Build agent state for active inference
        _agent_state = {
            "beliefs": belief_state.to_dict(),
            "policies": [p.to_dict() for p in self._policies],
            "preferences": agent_prefs,
        }
        
        # Perform active inference
        _observations = self._observation_history[-1] if self._observation_history else {}
        _result = self._calculator.perform_active_inference(agent_state, observations)
        
        # Extract selected action
        _selected_action_data = result.get("selected_action", {})
        _selected_action = Action(**selected_action_data) if selected_action_data else Action()
        
        # Update statistics
        self._stats["actions"] += 1
        self._action_history.append(selected_action)
        
        logger.info(
            "Action selected",
            _extra = {
                "agent_id": self.agent_id,
                "action_type": selected_action.action_type,
                "expected_free_energy": result.get("expected_free_energy", 0.0),
            },
        )
        
        return {
            "action": selected_action.to_dict(),
            "policy": result.get("selected_policy", {}),
            "expected_free_energy": result.get("expected_free_energy", 0.0),
        }
    
    def predict_outcomes(self, actions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Predict outcomes from actions using the generative model.
        
        Uses the agent's internal generative model to predict:
        p(o|a) = Σ_s p(o|s) * p(s|a)
        
        Args:
            actions: List of actions to predict outcomes for
            
        Returns:
            Dictionary mapping action IDs to predicted outcomes
        """
        predictions: Dict[str, Any] = {}
        
        for action_data in actions:
            action = Action(**action_data) if isinstance(action_data, dict) else action_data
            
            # Use generative model to predict outcome
            if self._generative_model:
                _likelihood = self._generative_model.get("likelihood", {})
                _predicted_outcome = self._predict_from_model(action, likelihood)
            else:
                # Default prediction based on action type
                _predicted_outcome = self._default_prediction(action)
            
            # Store prediction
            action.expected_outcome = predicted_outcome
            predictions[action.action_id] = predicted_outcome
            
            # Update statistics
            self._stats["predictions"] += 1
            self._prediction_history.append({"action": action_data, "outcome": predicted_outcome})
        
        logger.debug(
            "Outcomes predicted",
            _extra = {
                "agent_id": self.agent_id,
                "prediction_count": len(predictions),
            },
        )
        
        return predictions
    
    def minimize_surprise(self, policy: Dict[str, Any]) -> Dict[str, Any]:
        """
        Optimize policy to minimize surprise.
        
        Surprise minimization adjusts the policy to reduce the difference
        between predicted and actual outcomes:
        
        min_π Surprise(π) = min_π D_KL[p(o|π) || q(o)]
        
        Args:
            policy: Policy to optimize
            
        Returns:
            Optimization result with updated policy and surprise metrics
        """
        # Convert policy dict to Policy object
        _policy_obj = Policy.from_dict(policy) if isinstance(policy, dict) else policy
        
        # Calculate current surprise
        _current_surprise = self._calculate_policy_surprise(policy_obj)
        
        # Optimize policy (adjust action parameters to reduce surprise)
        _optimized_policy = self._optimize_policy(policy_obj, current_surprise)
        
        # Calculate new surprise
        _optimized_surprise = self._calculate_policy_surprise(optimized_policy)
        
        # Calculate improvement
        _surprise_reduction = current_surprise - optimized_surprise
        
        # Update statistics
        self._stats["surprise_minimizations"] += 1
        
        logger.info(
            "Surprise minimized",
            _extra = {
                "agent_id": self.agent_id,
                "current_surprise": current_surprise,
                "optimized_surprise": optimized_surprise,
                "reduction": surprise_reduction,
            },
        )
        
        return {
            "original_policy": policy_obj.to_dict(),
            "optimized_policy": optimized_policy.to_dict(),
            "current_surprise": current_surprise,
            "optimized_surprise": optimized_surprise,
            "surprise_reduction": surprise_reduction,
        }
    
    def perceive_and_act(self, observations: Dict[str, Any]) -> Dict[str, Any]:
        """
        Combined perception and action cycle.
        
        This is the main active inference loop:
        1. Update beliefs from observations
        2. Calculate prediction errors
        3. Select action minimizing expected free energy
        4. Execute action (return action for execution)
        
        Args:
            observations: Current observations from environment
            
        Returns:
            Dictionary with action, updated beliefs, and metrics
        """
        # Update beliefs
        _updated_beliefs = self.update_beliefs(observations)
        
        # Calculate surprise
        _predictions = self._prediction_history[-1] if self._prediction_history else {}
        _surprise = self._calculator.calculate_surprise(observations, predictions)
        
        # Select action
        _action_result = self.select_action()
        
        # Calculate free energy
        _free_energy = self._calculator.calculate_free_energy(
            observations,
            self._generative_model,
        )
        
        # Update statistics
        self._stats["perceptions"] += 1
        
        return {
            "action": action_result["action"],
            "beliefs": updated_beliefs,
            "surprise": surprise,
            "free_energy": free_energy,
            "expected_free_energy": action_result["expected_free_energy"],
        }
    
    def set_generative_model(self, model: Dict[str, Any]) -> None:
        """
        Set the agent's generative model.
        
        Args:
            model: Generative model with likelihood and prior
        """
        # Validate model
        _validation = self._validator.validate_text(str(model), content_type="json")
        if not validation.valid:
            logger.warning("Invalid generative model", extra={"errors": validation.errors})
            return
        
        self._generative_model = model
        logger.debug("Generative model set", extra={"agent_id": self.agent_id})
    
    def set_preferences(self, preferences: Dict[str, float]) -> None:
        """
        Set agent preferences (desired outcomes).
        
        Args:
            preferences: Dictionary mapping outcome variables to preferred values
        """
        # Validate preferences
        for key, value in preferences.items():
            if not isinstance(value, (int, float)) or value < 0 or value > 1:
                logger.warning(f"Invalid preference value for {key}: {value}")
                continue
            self._preferences[key] = float(value)
        
        logger.debug(
            "Preferences set",
            _extra = {"agent_id": self.agent_id, "preference_count": len(self._preferences)},
        )
    
    def add_policy(self, policy: Dict[str, Any]) -> None:
        """
        Add a policy to the agent's policy repertoire.
        
        Args:
            policy: Policy dictionary or Policy object
        """
        if isinstance(policy, dict):
            _policy_obj = Policy.from_dict(policy)
        else:
            _policy_obj = policy
        
        self._policies.append(policy_obj)
        logger.debug(
            "Policy added",
            _extra = {"agent_id": self.agent_id, "policy_id": policy_obj.policy_id},
        )
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get agent statistics.
        
        Returns:
            Dictionary with agent statistics
        """
        return {
            "agent_id": self.agent_id,
            **self._stats,
            "belief_precision": self._beliefs.precision,
            "policy_count": len(self._policies),
            "observation_history_length": len(self._observation_history),
            "calculator_stats": self._calculator.get_statistics(),
        }
    
    # Internal methods
    
    def _predict_from_model(self, action: Action, likelihood: Dict[str, Any]) -> Dict[str, float]:
        """
        Predict outcome from generative model.
        
        Args:
            action: Action to predict outcome for
            likelihood: Likelihood distribution from model
            
        Returns:
            Predicted outcome distribution
        """
        predicted: Dict[str, float] = {}
        
        # Use action type to select relevant likelihood
        action_type = action.action_type
        if action_type in likelihood:
            _predicted = likelihood[action_type]
        else:
            # Default prediction based on action parameters
            for key, param in action.parameters.items():
                if isinstance(param, (int, float)):
                    predicted[key] = min(1.0, max(0.0, float(param)))
                else:
                    predicted[key] = 0.5
        
        return predicted
    
    def _default_prediction(self, action: Action) -> Dict[str, float]:
        """
        Generate default prediction when no model is available.
        
        Args:
            action: Action to predict
            
        Returns:
            Default prediction based on action characteristics
        """
        return {
            "success": 0.5,
            "reward": 0.5,
            "cost": action.cost,
        }
    
    def _calculate_policy_surprise(self, policy: Policy) -> float:
        """
        Calculate surprise for a policy.
        
        Args:
            policy: Policy to evaluate
            
        Returns:
            Surprise value
        """
        _total_surprise = 0.0
        
        for action in policy.actions:
            # Compare predicted vs actual outcomes
            _predicted = action.expected_outcome
            _actual = self._observation_history[-1] if self._observation_history else {}
            
            _surprise = self._calculator.calculate_surprise(actual, predicted)
            total_surprise += surprise
        
        return total_surprise / max(1, len(policy.actions))
    
    def _optimize_policy(self, policy: Policy, current_surprise: float) -> Policy:
        """
        Optimize policy to reduce surprise.
        
        Args:
            policy: Current policy
            current_surprise: Current surprise level
            
        Returns:
            Optimized policy
        """
        # Create optimized copy
        _optimized = Policy(
            policy_id=str(uuid.uuid4()),
            actions=[],
            _prior_probability = policy.prior_probability,
        )
        
        # Adjust action parameters based on surprise
        _surprise_factor = 1.0 - current_surprise
        
        for action in policy.actions:
            _optimized_action = Action(
                _action_id = str(uuid.uuid4()),
                _action_type = action.action_type,
                parameters=action.parameters.copy(),
                expected_outcome=action.expected_outcome.copy(),
                _cost = action.cost * (1.0 - surprise_factor * 0.1),  # Slight cost reduction
                _policy_id = optimized.policy_id,
            )
            
            # Adjust parameters toward expected outcomes
            for key in optimized_action.parameters:
                if key in optimized_action.expected_outcome:
                    _expected = optimized_action.expected_outcome[key]
                    _current = optimized_action.parameters[key]
                    # Move toward expected value
                    optimized_action.parameters[key] = current + surprise_factor * (expected - current)
            
            optimized.actions.append(optimized_action)
        
        return optimized
