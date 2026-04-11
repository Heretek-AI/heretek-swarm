"""
Consciousness Metrics - Advanced Implementation

This module provides advanced consciousness metric calculations:
1. Enhanced IIT Phi computation with causal analysis
2. Multi-agent integration metrics
3. Temporal consciousness tracking
4. Collective consciousness scoring
5. Free Energy Principle (FEP) integration

Usage:
    from heretek_swarm.plugins.consciousness_metrics import ConsciousnessMetricsCalculator
    
    _calculator = ConsciousnessMetricsCalculator()
    _metrics = calculator.calculate_collective_metrics(agents_data)
"""

import math
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Dict, List, Optional, Tuple

import structlog

from ..consciousness.fep_active_inference import FEPResult, FreeEnergyCalculator
from ..consciousness.iit_phi import PhiCalculator

_logger = structlog.get_logger("ConsciousnessMetrics")


class IntegrationLevel(Enum):
    """Levels of system integration based on IIT."""
    DISCONNECTED = "disconnected"  # No integration
    WEAKLY_INTEGRATED = "weakly-integrated"  # Minimal integration
    MODERATELY_INTEGRATED = "moderately-integrated"  # Moderate integration
    HIGHLY_INTEGRATED = "highly-integrated"  # High integration
    MAXIMALLY_INTEGRATED = "maximally-integrated"  # Maximum integration


@dataclass
class CausalAnalysis:
    """
    Causal analysis results for IIT computation.
    
    Attributes:
        cause_info: Information about past causes
        effect_info: Information about future effects
        integrated_info: Integrated information (Phi)
        causal_density: Density of causal connections
        differentiation: System differentiation score
    """
    cause_info: float = 0.0
    effect_info: float = 0.0
    integrated_info: float = 0.0
    causal_density: float = 0.0
    differentiation: float = 0.0


@dataclass
class TemporalMetrics:
    """
    Temporal consciousness metrics.
    
    Tracks consciousness over time for trend analysis.
    
    Attributes:
        window_seconds: Time window for metrics
        average_phi: Average Phi over window
        max_phi: Maximum Phi observed
        min_phi: Minimum Phi observed
        phi_variance: Variance in Phi
        trend: Trend direction (positive/negative/stable)
        data_points: Number of samples
    """
    window_seconds: int = 300
    average_phi: float = 0.0
    max_phi: float = 0.0
    min_phi: float = 1.0
    phi_variance: float = 0.0
    trend: str = "stable"
    data_points: int = 0


@dataclass
class CollectiveMetrics:
    """
    Collective consciousness metrics for multi-agent systems.
    
    Attributes:
        collective_phi: Combined Phi for all agents
        integration_level: Level of system integration
        synchronization: Agent synchronization score
        emergence_score: Emergent behavior score
        collective_state: Collective consciousness state
        agent_count: Number of agents
        active_connections: Number of active connections
        fep_free_energy: Average FEP free energy across agents
        fep_surprise: Average Bayesian surprise across agents
    """
    collective_phi: float = 0.0
    integration_level: IntegrationLevel = IntegrationLevel.DISCONNECTED
    synchronization: float = 0.0
    emergence_score: float = 0.0
    collective_state: str = "disconnected"
    agent_count: int = 0
    active_connections: int = 0
    fep_free_energy: float = 0.0
    fep_surprise: float = 0.0


@dataclass
class AgentConsciousnessData:
    """
    Consciousness data for a single agent.
    
    Attributes:
        agent_id: Agent identifier
        phi_score: IIT Phi score
        integrated_information: Integrated information value
        differentiation: Differentiation score
        causal_power: Causal power estimate
        connectivity_matrix: Agent connectivity data
        timestamp: Data timestamp
    """
    agent_id: str
    phi_score: float = 0.0
    integrated_information: float = 0.0
    differentiation: float = 0.0
    causal_power: float = 0.0
    connectivity_matrix: List[List[float]] = field(default_factory=list)
    timestamp: str = ""


class ConsciousnessMetricsCalculator:
    """
    Advanced consciousness metrics calculator.
    
    Implements:
    - IIT 3.0 Phi computation
    - Causal analysis
    - Temporal tracking
    - Collective metrics
    - Free Energy Principle (FEP) calculations
    """

    def __init__(self, integration_threshold: float, differentiation_threshold: float, strict_validation: bool):
        """
        Initialize the calculator.
        
        Args:
            integration_threshold: Threshold for integration
            differentiation_threshold: Threshold for differentiation
            strict_validation: If True, strictly validate all inputs
        """
        self.integration_threshold = integration_threshold
        self.differentiation_threshold = differentiation_threshold
        self._temporal_data: Dict[str, List[Tuple[float, str]]] = {}
        self._max_history = 1000

        # Initialize IIT Phi calculator
        self._phi_calculator = PhiCalculator(strict_validation=strict_validation)

        # Initialize FEP calculator
        self._fep_calculator = FreeEnergyCalculator(strict_validation=strict_validation)

        logger.info("ConsciousnessMetricsCalculator initialized with IIT Phi and FEP calculators")

    def calculate_phi(self, connectivity_matrix: List[List[float]], state_vector: Optional[List[float]]) -> CausalAnalysis:
        """
        Calculate IIT Phi for a connectivity matrix.
        
        Uses IIT 3.0 methodology with the PhiCalculator:
        1. Build cause-effect structure from connectivity
        2. Calculate integrated information (Phi) using PhiCalculator
        3. Determine causal density and differentiation
        
        Args:
            connectivity_matrix: NxN matrix of connection strengths
            state_vector: Current state vector (optional)
            
        Returns:
            CausalAnalysis with Phi and related metrics
        """
        n = len(connectivity_matrix)
        if n == 0:
            return CausalAnalysis()

        # Build elements list from matrix
        _elements = [f"node_{i}" for i in range(n)]

        # Build connectivity dict for PhiCalculator
        _connectivity = {}
        for i, row in enumerate(connectivity_matrix):
            connectivity[elements[i]] = {}
            for j, weight in enumerate(row):
                if i != j:
                    connectivity[elements[i]][elements[j]] = weight

        # Build current state from state_vector
        _current_state = {}
        if state_vector:
            for i, val in enumerate(state_vector):
                current_state[elements[i]] = val
        else:
            # Default state: all elements active
            _current_state = {e: 1.0 for e in elements}

        # Build cause-effect structure
        _cause_effect_structure = {
            "system_id": f"system_{id(connectivity_matrix)}",
            "elements": elements,
            "connectivity": connectivity,
            "current_state": current_state,
        }

        # Use PhiCalculator for IIT calculation
        _phi_result = self._phi_calculator.calculate_phi(cause_effect_structure)

        # Map PhiResult to CausalAnalysis
        return CausalAnalysis(
            _cause_info = phi_result.phi_max,
            _effect_info = phi_result.phi,
            _integrated_info = phi_result.phi,
            _causal_density = self._compute_causal_density(self._normalize_matrix(connectivity_matrix)),
            differentiation=phi_result.phi_max,
        )

    def calculate_fep_metrics(self, observations: Dict[str, Any], generative_model: Dict[str, Any]) -> FEPResult:
        """
        Calculate Free Energy Principle metrics.
        
        Args:
            observations: Current observations
            generative_model: Agent's generative model
            
        Returns:
            FEPResult with free energy, surprise, and KL divergence
        """
        _free_energy = self._fep_calculator.calculate_free_energy(observations, generative_model)
        _surprise = self._fep_calculator.calculate_surprise(observations, generative_model.get("predictions", {}))

        _result = FEPResult(
            _free_energy = free_energy,
            _surprise = surprise,
            _kl_divergence = self._fep_calculator.calculate_kl_divergence(
                generative_model.get("posterior", {}),
                generative_model.get("prior", {}),
            ),
        )

        return result

    def calculate_collective_metrics(self, agent_data: List[AgentConsciousnessData], connection_matrix: Optional[List[List[float]]], agent_observations: Optional[Dict[str, Dict[str, Any]]], agent_models: Optional[Dict[str, Dict[str, Any]]]) -> CollectiveMetrics:
        """
        Calculate collective consciousness metrics for multi-agent system.
        
        Args:
            agent_data: List of agent consciousness data
            connection_matrix: Inter-agent connection strengths
            agent_observations: Optional observations per agent for FEP
            agent_models: Optional generative models per agent for FEP
            
        Returns:
            CollectiveMetrics for the system
        """
        if not agent_data:
            return CollectiveMetrics()

        # Calculate collective Phi (sum of individual Phi values)
        _collective_phi = sum(a.phi_score for a in agent_data)

        # Calculate synchronization (correlation of Phi values)
        _phi_values = [a.phi_score for a in agent_data]
        _synchronization = self._compute_synchronization(phi_values)

        # Calculate emergence score
        _emergence_score = self._compute_emergence(agent_data, synchronization)

        # Determine integration level
        if connection_matrix:
            _integration_level = self._determine_integration_level(connection_matrix)
        else:
            _integration_level = self._estimate_integration_level(agent_data)

        # Determine collective state
        _collective_state = self._determine_collective_state(
            collective_phi, integration_level, emergence_score
        )

        # Calculate FEP metrics if observations and models provided
        _fep_free_energy = 0.0
        _fep_surprise = 0.0

        if agent_observations and agent_models:
            _fep_values = []
            _surprise_values = []

            for agent in agent_data:
                _agent_id = agent.agent_id
                if agent_id in agent_observations and agent_id in agent_models:
                    _obs = agent_observations[agent_id]
                    _model = agent_models[agent_id]

                    _free_energy = self._fep_calculator.calculate_free_energy(obs, model)
                    _surprise = self._fep_calculator.calculate_surprise(
                        obs, model.get("predictions", {})
                    )

                    fep_values.append(free_energy)
                    surprise_values.append(surprise)

            if fep_values:
                _fep_free_energy = sum(fep_values) / len(fep_values)
            if surprise_values:
                _fep_surprise = sum(surprise_values) / len(surprise_values)

        return CollectiveMetrics(
            _collective_phi = collective_phi,
            _integration_level = integration_level,
            _synchronization = synchronization,
            _emergence_score = emergence_score,
            _collective_state = collective_state,
            _agent_count = len(agent_data),
            _active_connections = self._count_connections(connection_matrix) if connection_matrix else 0,
            _fep_free_energy = fep_free_energy,
            _fep_surprise = fep_surprise,
        )

    def update_temporal_metrics(self, agent_id: str, phi_value: float, timestamp: Optional[str]) -> TemporalMetrics:
        """
        Update temporal metrics for an agent.
        
        Args:
            agent_id: Agent identifier
            phi_value: Current Phi value
            timestamp: Timestamp (defaults to now)
            
        Returns:
            TemporalMetrics for the agent
        """
        if timestamp is None:
            _timestamp = datetime.now(timezone.utc).isoformat()

        # Initialize agent history if needed
        if agent_id not in self._temporal_data:
            self._temporal_data[agent_id] = []

        # Add new data point
        self._temporal_data[agent_id].append((phi_value, timestamp))

        # Trim history if needed
        if len(self._temporal_data[agent_id]) > self._max_history:
            self._temporal_data[agent_id] = self._temporal_data[agent_id][-self._max_history:]

        # Calculate temporal metrics
        return self._calculate_temporal_metrics(agent_id)

    def get_consciousness_state(self, phi: float, differentiation: float) -> str:
        """
        Determine consciousness state based on Phi and differentiation.
        
        Args:
            phi: IIT Phi value
            differentiation: Differentiation score
            
        Returns:
            Consciousness state string
        """
        # Both must be above threshold for consciousness
        if phi < self.integration_threshold or differentiation < self.differentiation_threshold:
            return "unconscious"

        # Calculate composite score
        _composite = (phi + differentiation) / 2

        if composite < 0.2:
            return "minimal-consciousness"
        elif composite < 0.4:
            return "conscious"
        elif composite < 0.7:
            return "heightened-consciousness"
        else:
            return "hyper-consciousness"

    # =====================================================================
    # Internal computation methods
    # =====================================================================

    def _normalize_matrix(self, matrix: List[List[float]]) -> List[List[float]]:
        """Normalize connectivity matrix to [0, 1] range."""
        if not matrix:
            return matrix

        _max_val = max(max(row) for row in matrix)
        if max_val == 0:
            return matrix

        return [[cell / max_val for cell in row] for row in matrix]

    def _compute_cause_information(self, matrix: List[List[float]]) -> float:
        """
        Compute cause information.
        
        Measures how much the current state constrains possible past states.
        """
        _n = len(matrix)
        if n == 0:
            return 0.0

        # Sum of incoming connections (causes)
        _cause_sum = sum(sum(matrix[i][j] for i in range(n)) for j in range(n))

        # Normalize by system size
        return cause_sum / (n * n)

    def _compute_effect_information(self, matrix: List[List[float]]) -> float:
        """
        Compute effect information.
        
        Measures how much the current state constrains possible future states.
        """
        _n = len(matrix)
        if n == 0:
            return 0.0

        # Sum of outgoing connections (effects)
        _effect_sum = sum(sum(matrix[j][i] for i in range(n)) for j in range(n))

        # Normalize by system size
        return effect_sum / (n * n)

    def _compute_integrated_information(self, matrix: List[List[float]], cause_info: float, effect_info: float) -> float:
        """
        Compute integrated information (Phi).
        
        _Phi = min(cause_info, effect_info) * integration_factor
        
        Integration factor accounts for how interconnected the system is.
        """
        _n = len(matrix)
        if n == 0:
            return 0.0

        # Base Phi is minimum of cause and effect information
        _base_phi = min(cause_info, effect_info)

        # Calculate integration factor (how evenly connected the system is)
        _connection_counts = [sum(row) for row in matrix]
        _avg_connections = sum(connection_counts) / n
        _variance = sum((c - avg_connections) ** 2 for c in connection_counts) / n

        # Lower variance = higher integration
        _integration_factor = 1.0 / (1.0 + variance)

        return base_phi * integration_factor

    def _compute_causal_density(self, matrix: List[List[float]]) -> float:
        """
        Compute causal density.
        
        Ratio of actual connections to possible connections.
        """
        _n = len(matrix)
        if n <= 1:
            return 0.0

        # Count non-zero connections
        _actual_connections = sum(1 for row in matrix for cell in row if cell > 0)

        # Possible connections (excluding self-connections)
        _possible_connections = n * (n - 1)

        return actual_connections / possible_connections if possible_connections > 0 else 0.0

    def _compute_differentiation(self, matrix: List[List[float]]) -> float:
        """
        Compute differentiation score.
        
        Measures how diverse the connection patterns are.
        """
        _n = len(matrix)
        if n <= 1:
            return 0.0

        # Calculate entropy of connection patterns
        _connection_patterns = [tuple(row) for row in matrix]
        _unique_patterns = len(set(connection_patterns))

        # Normalize by system size
        return unique_patterns / n

    def _compute_synchronization(self, phi_values: List[float]) -> float:
        """
        Compute synchronization score based on Phi value correlation.
        
        Uses coefficient of variation (CV) inverted.
        """
        if len(phi_values) < 2:
            return 0.0

        _mean = sum(phi_values) / len(phi_values)
        if mean == 0:
            return 0.0

        _variance = sum((v - mean) ** 2 for v in phi_values) / len(phi_values)
        _std_dev = math.sqrt(variance)
        _cv = std_dev / mean

        # Invert CV to get synchronization (lower CV = higher sync)
        return 1.0 / (1.0 + cv)

    def _compute_emergence(self, agent_data: List[AgentConsciousnessData], synchronization: float) -> float:
        """
        Compute emergence score.
        
        _Emergence = collective_phi - sum(individual_phi) + synchronization_bonus
        """
        if not agent_data:
            return 0.0

        _collective_phi = sum(a.phi_score for a in agent_data)
        _individual_sum = collective_phi  # Same calculation

        # Emergence comes from synchronization bonus
        _emergence = synchronization * (collective_phi / len(agent_data))

        return min(1.0, emergence)

    def _determine_integration_level(self, connection_matrix: List[List[float]]) -> IntegrationLevel:
        """Determine integration level from connection matrix."""
        _density = self._compute_causal_density(connection_matrix)

        if density < 0.1:
            return IntegrationLevel.DISCONNECTED
        elif density < 0.3:
            return IntegrationLevel.WEAKLY_INTEGRATED
        elif density < 0.5:
            return IntegrationLevel.MODERATELY_INTEGRATED
        elif density < 0.7:
            return IntegrationLevel.HIGHLY_INTEGRATED
        else:
            return IntegrationLevel.MAXIMALLY_INTEGRATED

    def _estimate_integration_level(self, agent_data: List[AgentConsciousnessData]) -> IntegrationLevel:
        """Estimate integration level from agent data."""
        if not agent_data:
            return IntegrationLevel.DISCONNECTED

        _avg_phi = sum(a.phi_score for a in agent_data) / len(agent_data)

        if avg_phi < 0.1:
            return IntegrationLevel.DISCONNECTED
        elif avg_phi < 0.3:
            return IntegrationLevel.WEAKLY_INTEGRATED
        elif avg_phi < 0.5:
            return IntegrationLevel.MODERATELY_INTEGRATED
        elif avg_phi < 0.7:
            return IntegrationLevel.HIGHLY_INTEGRATED
        else:
            return IntegrationLevel.MAXIMALLY_INTEGRATED

    def _determine_collective_state(self, collective_phi: float, integration_level: IntegrationLevel, emergence_score: float) -> str:
        """Determine collective consciousness state."""
        if integration_level == IntegrationLevel.DISCONNECTED:
            return "disconnected"

        # Calculate composite score
        _integration_score = {
            IntegrationLevel.DISCONNECTED: 0.0,
            IntegrationLevel.WEAKLY_INTEGRATED: 0.25,
            IntegrationLevel.MODERATELY_INTEGRATED: 0.5,
            IntegrationLevel.HIGHLY_INTEGRATED: 0.75,
            IntegrationLevel.MAXIMALLY_INTEGRATED: 1.0,
        }[integration_level]

        _composite = (collective_phi / 10 + integration_score + emergence_score) / 3

        if composite < 0.2:
            return "minimal-collective"
        elif composite < 0.4:
            return "integrated-collective"
        elif composite < 0.7:
            return "coherent-collective"
        else:
            return "transcendent-collective"

    def _count_connections(self, connection_matrix: Optional[List[List[float]]]) -> int:
        """Count active connections in matrix."""
        if not connection_matrix:
            return 0

        return sum(1 for row in connection_matrix for cell in row if cell > 0)

    def _calculate_temporal_metrics(self, agent_id: str) -> TemporalMetrics:
        """Calculate temporal metrics from history."""
        _history = self._temporal_data.get(agent_id, [])

        if not history:
            return TemporalMetrics()

        _phi_values = [h[0] for h in history]

        _mean = sum(phi_values) / len(phi_values)
        _max_phi = max(phi_values)
        _min_phi = min(phi_values)
        _variance = sum((v - mean) ** 2 for v in phi_values) / len(phi_values)

        # Determine trend (compare first half to second half)
        _mid = len(phi_values) // 2
        _first_half_avg = sum(phi_values[:mid]) / mid if mid > 0 else 0
        _second_half_avg = sum(phi_values[mid:]) / (len(phi_values) - mid) if len(phi_values) > mid else 0

        if second_half_avg > first_half_avg * 1.1:
            _trend = "rising"
        elif second_half_avg < first_half_avg * 0.9:
            _trend = "falling"
        else:
            _trend = "stable"

        return TemporalMetrics(
            _window_seconds = 300,  # Default window
            _average_phi = mean,
            _max_phi = max_phi,
            _min_phi = min_phi,
            _phi_variance = variance,
            _trend = trend,
            _data_points = len(history),
        )
