"""
Swarm Intelligence Patterns for Collective Decision Making.

This module implements bio-inspired swarm intelligence patterns:
- Particle Swarm Optimization (PSO) for decision convergence
- Ant Colony Optimization for pathfinding/routing
- Bee Algorithm for task allocation
- Flocking behavior for agent coordination
- Stigmergy for indirect coordination

These patterns enable emergent collective intelligence through simple
local interactions between agents.

Example:
    ```python
    from heretek_swarm.collective.swarm_intelligence import (
        SwarmIntelligenceEngine,
        SwarmPattern,
        SwarmConfig,
    )

    # Initialize engine
    config = SwarmConfig()
    _engine = SwarmIntelligenceEngine(config)

    # Run PSO for decision convergence
    _result = await engine.run_pso(
        _participants = ["agent-1", "agent-2", "agent-3"],
        _decision_space = {"option_a": 0.3, "option_b": 0.7},
        _iterations = 10
    )

    # Run bee algorithm for task allocation
    _allocation = await engine.run_bee_algorithm(
        _tasks = ["task-1", "task-2", "task-3"],
        _foragers = ["agent-1", "agent-2"]
    )
    ```
"""

import math
import random
import uuid
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Tuple

import structlog

_logger = structlog.get_logger("SwarmIntelligenceEngine")


class SwarmPattern(Enum):
    """Swarm intelligence pattern types."""
    PSO = "particle_swarm_optimization"
    ANT_COLONY = "ant_colony_optimization"
    BEE_ALGORITHM = "bee_algorithm"
    FLOCKING = "flocking_behavior"
    STIGMERGY = "stigmergy_indirect_coordination"


class FlockingRule(Enum):
    """Flocking behavior rules."""
    SEPARATION = "separation"  # Avoid crowding neighbors
    ALIGNMENT = "alignment"  # Steer towards average heading
    COHESION = "cohesion"  # Move toward average position


@dataclass
class Particle:
    """
    Particle in PSO algorithm.

    Attributes:
        particle_id: Unique identifier
        position: Current position in search space
        velocity: Current velocity vector
        best_position: Best position found by this particle
        best_value: Best fitness value found
        agent_id: Associated agent ID
    """
    particle_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    position: Dict[str, float] = field(default_factory=dict)
    velocity: Dict[str, float] = field(default_factory=dict)
    best_position: Dict[str, float] = field(default_factory=dict)
    best_value: float = float('-inf')
    agent_id: str = ""


@dataclass
class PheromoneTrail:
    """
    Pheromone trail for Ant Colony Optimization.

    Attributes:
        trail_id: Unique identifier
        from_node: Starting node
        to_node: Ending node
        pheromone_level: Current pheromone level
        evaporation_rate: Rate of pheromone decay
        quality: Quality of the path
    """
    trail_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    from_node: str = ""
    to_node: str = ""
    pheromone_level: float = 1.0
    evaporation_rate: float = 0.1
    quality: float = 1.0
    last_updated: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


@dataclass
class BeeAgent:
    """
    Bee agent in the Bee Algorithm.

    Attributes:
        bee_id: Unique identifier
        role: Bee role (scout, forager, unemployed)
        current_task: Current task being worked on
        task_quality: Quality assessment of current task
        dance_strength: Strength of waggle dance
        agent_id: Associated agent ID
    """
    bee_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    role: str = "unemployed"  # scout, forager, unemployed
    current_task: Optional[str] = None
    task_quality: float = 0.0
    dance_strength: float = 0.0
    agent_id: str = ""


@dataclass
class FlockingAgent:
    """
    Agent exhibiting flocking behavior.

    Attributes:
        agent_id: Unique identifier
        position: Current position in 3D space
        velocity: Current velocity vector
        heading: Current heading direction
        neighbors: Nearby flocking agents
    """
    agent_id: str = ""
    position: Tuple[float, float, float] = (0.0, 0.0, 0.0)
    velocity: Tuple[float, float, float] = (0.0, 0.0, 0.0)
    heading: Tuple[float, float, float] = (0.0, 0.0, 1.0)
    neighbors: List[str] = field(default_factory=list)


@dataclass
class StigmergicTrace:
    """
    Trace left by an agent for stigmergic coordination.

    Attributes:
        trace_id: Unique identifier
        agent_id: Agent that left the trace
        trace_type: Type of trace
        content: Trace content/data
        strength: Current trace strength
        decay_rate: Rate of trace decay
        timestamp: When trace was left
    """
    trace_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    agent_id: str = ""
    trace_type: str = "marker"
    content: Dict[str, Any] = field(default_factory=dict)
    strength: float = 1.0
    decay_rate: float = 0.05
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


@dataclass
class SwarmDecision:
    """
    Result of a swarm intelligence decision process.

    Attributes:
        pattern: Swarm pattern used
        participants: Participating agents
        convergence_iterations: Iterations to converge
        final_position: Final decision position
        confidence: Decision confidence
        emergence_indicators: Indicators of emergent behavior
        quality_metrics: Quality metrics for the decision
    """
    pattern: SwarmPattern = SwarmPattern.PSO
    participants: List[str] = field(default_factory=list)
    convergence_iterations: int = 0
    final_position: Dict[str, Any] = field(default_factory=dict)
    confidence: float = 0.0
    emergence_indicators: List[str] = field(default_factory=list)
    quality_metrics: Dict[str, float] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


@dataclass
class SwarmConfig:
    """
    Configuration for swarm intelligence algorithms.

    Attributes:
        pso_inertia: PSO inertia weight
        pso_cognitive: PSO cognitive coefficient
        pso_social: PSO social coefficient
        ant_evaporation: Pheromone evaporation rate
        ant_alpha: Pheromone importance factor
        ant_beta: Heuristic importance factor
        bee_scout_ratio: Ratio of scout bees
        bee_dance_threshold: Threshold for waggle dance
        flock_separation_weight: Separation rule weight
        flock_alignment_weight: Alignment rule weight
        flock_cohesion_weight: Cohesion rule weight
        stigmergy_decay: Trace decay rate
        max_iterations: Maximum iterations for convergence
        convergence_threshold: Threshold for convergence detection
    """
    # PSO parameters
    pso_inertia: float = 0.7
    pso_cognitive: float = 1.5
    pso_social: float = 1.5

    # Ant Colony parameters
    ant_evaporation: float = 0.1
    ant_alpha: float = 1.0
    ant_beta: float = 2.0

    # Bee Algorithm parameters
    bee_scout_ratio: float = 0.2
    bee_dance_threshold: float = 0.7

    # Flocking parameters
    flock_separation_weight: float = 1.5
    flock_alignment_weight: float = 1.0
    flock_cohesion_weight: float = 1.0
    flock_perception_radius: float = 10.0

    # Stigmergy parameters
    stigmergy_decay: float = 0.05

    # General parameters
    max_iterations: int = 100
    convergence_threshold: float = 0.95


class SwarmIntelligenceEngine:
    """
    Engine for swarm intelligence patterns.

    This engine implements multiple bio-inspired algorithms:
    - Particle Swarm Optimization for decision convergence
    - Ant Colony Optimization for pathfinding
    - Bee Algorithm for task allocation
    - Flocking behavior for coordination
    - Stigmergy for indirect coordination

    Attributes:
        config: Swarm configuration
    """

    def __init__(self, config: Optional[SwarmConfig]) -> None:
        """
        Initialize swarm intelligence engine.

        Args:
            config: Swarm configuration
        """
        self.config = config or SwarmConfig()

        # PSO state
        self.particles: Dict[str, Particle] = {}
        self.global_best_position: Dict[str, float] = {}
        self.global_best_value: float = float('-inf')

        # Ant Colony state
        self.pheromone_trails: Dict[str, Dict[str, PheromoneTrail]] = {}

        # Bee Algorithm state
        self.bee_colony: List[BeeAgent] = []
        self.task_pool: Dict[str, Dict[str, Any]] = {}

        # Flocking state
        self.flocking_agents: Dict[str, FlockingAgent] = {}

        # Stigmergy state
        self.traces: Dict[str, List[StigmergicTrace]] = {}

        # Decision history
        self.decision_history: List[SwarmDecision] = []

        logger.info(
            f"SwarmIntelligenceEngine initialized with "
            f"max_iterations={self.config.max_iterations}"
        )

    # =========================================================================
    # Particle Swarm Optimization
    # =========================================================================

    async def run_pso(self, participants: List[str], decision_space: Dict[str, float], fitness_function: Optional[Callable[[Dict[str, float]], float]], iterations: Optional[int]) -> SwarmDecision:
        """
        Run Particle Swarm Optimization for decision convergence.

        Args:
            participants: List of participating agent IDs
            decision_space: Initial decision space with options and weights
            fitness_function: Function to evaluate solution quality
            iterations: Number of iterations (uses config default if None)

        Returns:
            Swarm decision with converged result
        """
        _iterations = iterations or self.config.max_iterations

        # Initialize particles from participants
        self._initialize_pso_particles(participants, decision_space)

        # Run PSO iterations
        _converged = False
        for iteration in range(iterations):
            # Update particle velocities and positions
            for particle in self.particles.values():
                self._update_particle_velocity(particle)
                self._update_particle_position(particle)

                # Evaluate fitness
                _fitness = self._evaluate_fitness(particle.position, fitness_function)

                # Update personal best
                if fitness > particle.best_value:
                    particle.best_value = fitness
                    particle.best_position = particle.position.copy()

                # Update global best
                if fitness > self.global_best_value:
                    self.global_best_value = fitness
                    self.global_best_position = particle.position.copy()

            # Check convergence
            if self._check_convergence(iteration):
                _converged = True
                logger.info(f"PSO converged at iteration {iteration}")
                break

        # Build decision result
        decision = SwarmDecision(
            pattern=SwarmPattern.PSO,
            _participants = participants,
            _convergence_iterations = iteration + 1,
            final_position=self.global_best_position.copy(),
            confidence=self.global_best_value,
            _emergence_indicators = self._detect_emergence_pso(),
            _quality_metrics = {
                "convergence_rate": (iteration + 1) / iterations,
                "final_fitness": self.global_best_value,
                "particle_diversity": self._calculate_particle_diversity(),
            }
        )

        self.decision_history.append(decision)

        logger.info(
            f"PSO completed: {iteration + 1} iterations, "
            f"confidence={self.global_best_value:.2f}"
        )

        return decision

    def _initialize_pso_particles(self, participants: List[str], decision_space: Dict[str, float]) -> None:
        """Initialize PSO particles from participants."""
        self.particles.clear()
        self.global_best_position = {}
        self.global_best_value = float('-inf')

        for i, agent_id in enumerate(participants):
            # Initialize position based on decision space
            position = {}
            for key, weight in decision_space.items():
                # Add some randomness to initial position
                position[key] = weight + random.uniform(-0.1, 0.1)

            # Normalize positions
            _total = sum(position.values())
            if total > 0:
                position = {k: v / total for k, v in position.items()}

            # Initialize velocity
            velocity = {k: random.uniform(-0.01, 0.01) for k in position.keys()}

            particle = Particle(
                particle_id=f"particle-{i}",
                position=position,
                velocity=velocity,
                best_position=position.copy(),
                _agent_id = agent_id,
            )

            self.particles[particle.particle_id] = particle

    def _update_particle_velocity(self, particle: Particle) -> None:
        """Update particle velocity using PSO equations."""
        for key in particle.position.keys():
            # Cognitive component (attraction to personal best)
            _cognitive = (
                self.config.pso_cognitive *
                random.random() *
                (particle.best_position.get(key, 0) - particle.position[key])
            )

            # Social component (attraction to global best)
            _social = (
                self.config.pso_social *
                random.random() *
                (self.global_best_position.get(key, 0) - particle.position[key])
            )

            # Update velocity with inertia
            particle.velocity[key] = (
                self.config.pso_inertia * particle.velocity.get(key, 0) +
                cognitive + social
            )

            # Clamp velocity
            particle.velocity[key] = max(-0.5, min(0.5, particle.velocity[key]))

    def _update_particle_position(self, particle: Particle) -> None:
        """Update particle position based on velocity."""
        for key in particle.position.keys():
            particle.position[key] += particle.velocity.get(key, 0)

        # Normalize to ensure valid probability distribution
        _total = sum(particle.position.values())
        if total > 0:
            particle.position = {k: v / total for k, v in particle.position.items()}

    def _evaluate_fitness(self, position: Dict[str, float], fitness_function: Optional[Callable[[Dict[str, float]], float]]) -> float:
        """Evaluate fitness of a position."""
        if fitness_function:
            return fitness_function(position)

        # Default fitness: sum of weighted positions
        return sum(position.values())

    def _check_convergence(self, iteration: int) -> bool:
        """Check if PSO has converged."""
        if iteration < 5:
            return False

        # Check if global best hasn't changed significantly
        _recent_best = [d.final_position for d in self.decision_history[-5:]]
        if len(recent_best) < 5:
            return False

        # Simple convergence check
        if self.global_best_value >= self.config.convergence_threshold:
            return True

        return False

    def _detect_emergence_pso(self) -> List[str]:
        """Detect emergence indicators in PSO."""
        _indicators = []

        # Check for consensus formation
        if self.global_best_value >= 0.8:
            indicators.append("strong_consensus")

        # Check for particle clustering
        _diversity = self._calculate_particle_diversity()
        if diversity < 0.2:
            indicators.append("high_clustering")
        elif diversity > 0.8:
            indicators.append("exploratory_behavior")

        return indicators

    def _calculate_particle_diversity(self) -> float:
        """Calculate diversity of particle positions."""
        if not self.particles:
            return 0.0

        _positions = [p.position for p in self.particles.values()]
        if not positions:
            return 0.0

        # Calculate variance across positions
        _all_keys = set()
        for pos in positions:
            all_keys.update(pos.keys())

        _variance_sum = 0.0
        for key in all_keys:
            values = [pos.get(key, 0) for pos in positions]
            _mean = sum(values) / len(values)
            _variance = sum((v - mean) ** 2 for v in values) / len(values)
            variance_sum += variance

        return variance_sum / len(all_keys) if all_keys else 0.0

    # =========================================================================
    # Ant Colony Optimization
    # =========================================================================

    async def run_ant_colony(self, nodes: List[str], edges: List[Tuple[str, str]], start_node: str, end_node: str, num_ants: int, iterations: Optional[int]) -> SwarmDecision:
        """
        Run Ant Colony Optimization for pathfinding.

        Args:
            nodes: List of node identifiers
            edges: List of edges (from, to)
            start_node: Starting node
            end_node: Destination node
            num_ants: Number of ants to simulate
            iterations: Number of iterations

        Returns:
            Swarm decision with optimal path
        """
        _iterations = iterations or self.config.max_iterations

        # Initialize pheromone trails
        self._initialize_pheromone_trails(edges)

        _best_path = []
        _best_path_quality = 0.0

        for iteration in range(iterations):
            # Each ant constructs a solution
            _paths = []
            for _ in range(num_ants):
                _path = self._construct_ant_path(nodes, edges, start_node, end_node)
                if path:
                    paths.append(path)

            # Update pheromones based on path quality
            for path in paths:
                quality = self._evaluate_path_quality(path, edges)
                self._update_pheromones(path, quality)

                if quality > best_path_quality:
                    _best_path = path
                    _best_path_quality = quality

            # Evaporate pheromones
            self._evaporate_pheromones()

            # Check convergence
            if best_path_quality >= self.config.convergence_threshold:
                break

        # Build decision result
        decision = SwarmDecision(
            pattern=SwarmPattern.ANT_COLONY,
            _participants = [f"ant-{i}" for i in range(num_ants)],
            _convergence_iterations = iteration + 1,
            _final_position = {"path": best_path, "quality": best_path_quality},
            confidence=best_path_quality,
            _emergence_indicators = self._detect_emergence_aco(best_path),
            _quality_metrics = {
                "path_length": len(best_path),
                "pheromone_strength": self._get_path_pheromone_strength(best_path),
            }
        )

        self.decision_history.append(decision)

        logger.info(
            f"ACO completed: found path with quality {best_path_quality:.2f}"
        )

        return decision

    def _initialize_pheromone_trails(self, edges: List[Tuple[str, str]]) -> None:
        """Initialize pheromone trails for edges."""
        self.pheromone_trails.clear()

        for from_node, to_node in edges:
            if from_node not in self.pheromone_trails:
                self.pheromone_trails[from_node] = {}

            _trail = PheromoneTrail(
                _from_node = from_node,
                _to_node = to_node,
                pheromone_level=1.0,
                evaporation_rate=self.config.ant_evaporation,
            )

            self.pheromone_trails[from_node][to_node] = trail

    def _construct_ant_path(self, _nodes: List[str], edges: List[Tuple[str, str]], start_node: str, end_node: str) -> List[str]:
        """Construct a path for an ant using pheromone probabilities."""
        _path = [start_node]
        current = start_node
        _visited = {start_node}

        # Build adjacency list
        _adjacency = defaultdict(list)
        for from_node, to_node in edges:
            adjacency[from_node].append(to_node)

        while current != end_node:
            neighbors = [n for n in adjacency[current] if n not in visited]

            if not neighbors:
                # Dead end, backtrack
                if len(path) > 1:
                    path.pop()
                    current = path[-1]
                    continue
                else:
                    return []  # No valid path

            # Calculate probabilities based on pheromone and heuristic
            _probabilities = []
            for neighbor in neighbors:
                pheromone = self.pheromone_trails.get(current, {}).get(neighbor, PheromoneTrail())
                _tau = pheromone.pheromone_level ** self.config.ant_alpha

                # Heuristic: prefer shorter paths (inverse distance)
                eta = 1.0 / (1 + len(path))  # Simple distance heuristic
                _eta = eta ** self.config.ant_beta

                probabilities.append(tau * eta)

            # Normalize probabilities
            _total = sum(probabilities)
            if total > 0:
                _probabilities = [p / total for p in probabilities]

            # Select next node
            _selected = random.choices(neighbors, weights=probabilities, k=1)[0]
            path.append(selected)
            visited.add(selected)
            current = selected

        return path

    def _evaluate_path_quality(self, path: List[str], edges: List[Tuple[str, str]]) -> float:
        """Evaluate quality of a path."""
        if not path:
            return 0.0

        # Shorter paths are better
        _length_factor = 1.0 / len(path)

        # Check if path uses valid edges
        _edge_set = set(edges)
        _valid_edges = 0
        for i in range(len(path) - 1):
            if (path[i], path[i + 1]) in edge_set:
                valid_edges += 1

        _validity_factor = valid_edges / (len(path) - 1) if len(path) > 1 else 0

        return 0.7 * length_factor + 0.3 * validity_factor

    def _update_pheromones(self, path: List[str], quality: float) -> None:
        """Update pheromones along a path."""
        for i in range(len(path) - 1):
            from_node, to_node = path[i], path[i + 1]
            if from_node in self.pheromone_trails and to_node in self.pheromone_trails[from_node]:
                _trail = self.pheromone_trails[from_node][to_node]
                trail.pheromone_level += quality * 0.1
                trail.quality = quality
                trail.last_updated = datetime.now(timezone.utc).isoformat()

    def _evaporate_pheromones(self) -> None:
        """Evaporate pheromones on all trails."""
        for from_node in self.pheromone_trails.values():
            for trail in from_node.values():
                trail.pheromone_level *= (1 - trail.evaporation_rate)
                trail.pheromone_level = max(0.1, trail.pheromone_level)  # Minimum pheromone

    def _get_path_pheromone_strength(self, path: List[str]) -> float:
        """Get total pheromone strength along a path."""
        _total = 0.0
        for i in range(len(path) - 1):
            from_node, to_node = path[i], path[i + 1]
            if from_node in self.pheromone_trails and to_node in self.pheromone_trails[from_node]:
                total += self.pheromone_trails[from_node][to_node].pheromone_level
        return total

    def _detect_emergence_aco(self, best_path: List[str]) -> List[str]:
        """Detect emergence indicators in ACO."""
        _indicators = []

        if len(best_path) > 0:
            indicators.append("path_emergence")

        # Check for pheromone concentration
        _avg_pheromone = sum(
            trail.pheromone_level
            for from_node in self.pheromone_trails.values()
            for trail in from_node.values()
        ) / max(1, sum(len(v) for v in self.pheromone_trails.values()))

        if avg_pheromone > 2.0:
            indicators.append("strong_pheromone_trail")

        return indicators

    # =========================================================================
    # Bee Algorithm
    # =========================================================================

    async def run_bee_algorithm(self, tasks: List[str], foragers: List[str], task_qualities: Optional[Dict[str, float]], iterations: Optional[int]) -> SwarmDecision:
        """
        Run Bee Algorithm for task allocation.

        Args:
            tasks: List of task identifiers
            foragers: List of forager agent IDs
            task_qualities: Optional initial task quality assessments
            iterations: Number of iterations

        Returns:
            Swarm decision with task allocation
        """
        _iterations = iterations or self.config.max_iterations

        # Initialize bee colony
        self._initialize_bee_colony(tasks, foragers, task_qualities or {})

        # Store task qualities
        for task_id, quality in (task_qualities or {}).items():
            if task_id in self.task_pool:
                self.task_pool[task_id]["quality"] = quality

        _best_allocation = {}
        _best_allocation_score = 0.0

        for iteration in range(iterations):
            # Scout phase: discover new tasks
            self._bee_scout_phase()

            # Forager phase: exploit known tasks
            self._bee_forager_phase()

            # Dance phase: share information
            self._bee_dance_phase()

            # Evaluate allocation
            _allocation = self._get_current_allocation()
            _score = self._evaluate_allocation(allocation)

            if score > best_allocation_score:
                _best_allocation = allocation
                _best_allocation_score = score

            # Check convergence
            if score >= self.config.convergence_threshold:
                break

        # Build decision result
        decision = SwarmDecision(
            pattern=SwarmPattern.BEE_ALGORITHM,
            _participants = foragers,
            _convergence_iterations = iteration + 1,
            _final_position = {"allocation": best_allocation},
            confidence=best_allocation_score,
            _emergence_indicators = self._detect_emergence_bee(best_allocation),
            _quality_metrics = {
                "tasks_allocated": len(best_allocation),
                "allocation_efficiency": best_allocation_score,
            }
        )

        self.decision_history.append(decision)

        logger.info(
            f"Bee Algorithm completed: {len(best_allocation)} tasks allocated"
        )

        return decision

    def _initialize_bee_colony(self, tasks: List[str], foragers: List[str], task_qualities: Dict[str, float]) -> None:
        """Initialize bee colony with scouts and foragers."""
        self.bee_colony.clear()
        self.task_pool.clear()

        # Create tasks
        for task_id in tasks:
            self.task_pool[task_id] = {
                "quality": task_qualities.get(task_id, 0.5),
                "assigned_foragers": [],
                "last_updated": datetime.now(timezone.utc).isoformat(),
            }

        # Create bees
        _num_scouts = max(1, int(len(foragers) * self.config.bee_scout_ratio))
        _num_foragers = len(foragers) - num_scouts

        for i, agent_id in enumerate(foragers[:num_scouts]):
            bee = BeeAgent(
                role="scout",
                _agent_id = agent_id,
            )
            self.bee_colony.append(bee)

        for i, agent_id in enumerate(foragers[num_scouts:]):
            bee = BeeAgent(
                role="forager",
                _agent_id = agent_id,
            )
            self.bee_colony.append(bee)

    def _bee_scout_phase(self) -> None:
        """Scout bees search for new tasks."""
        _scouts = [b for b in self.bee_colony if b.role == "scout"]

        for scout in scouts:
            # Randomly discover tasks
            _available_tasks = [
                t for t, data in self.task_pool.items()
                if not data["assigned_foragers"]
            ]

            if available_tasks:
                _discovered = random.choice(available_tasks)
                # Update task quality based on scout assessment
                self.task_pool[discovered]["quality"] = random.uniform(0.3, 1.0)

    def _bee_forager_phase(self) -> None:
        """Forager bees exploit known tasks."""
        _foragers = [b for b in self.bee_colony if b.role == "forager"]

        for forager in foragers:
            # Choose task based on dance strength
            if forager.current_task:
                # Continue with current task
                _quality = self.task_pool.get(forager.current_task, {}).get("quality", 0)
                forager.task_quality = quality
            else:
                # Select new task based on dance strength
                _task_dances = []
                for task_id, data in self.task_pool.items():
                    dance_strength = sum(
                        b.dance_strength for b in self.bee_colony
                        if b.current_task == task_id
                    )
                    if dance_strength > 0:
                        task_dances.append((task_id, dance_strength))

                if task_dances:
                    # Probabilistic selection based on dance strength
                    _total = sum(d[1] for d in task_dances)
                    _weights = [d[1] / total for d in task_dances]
                    _selected = random.choices([d[0] for d in task_dances], weights=weights, k=1)[0]
                    forager.current_task = selected
                    forager.task_quality = self.task_pool[selected]["quality"]

                    # Add to task's assigned foragers
                    self.task_pool[selected]["assigned_foragers"].append(forager.agent_id)

    def _bee_dance_phase(self) -> None:
        """Bees perform waggle dance to share task information."""
        for bee in self.bee_colony:
            if bee.current_task:
                # Calculate dance strength based on task quality
                if bee.task_quality >= self.config.bee_dance_threshold:
                    bee.dance_strength = bee.task_quality
                else:
                    # Abandon task if quality is low
                    if bee.current_task in self.task_pool:
                        if bee.agent_id in self.task_pool[bee.current_task]["assigned_foragers"]:
                            self.task_pool[bee.current_task]["assigned_foragers"].remove(bee.agent_id)
                    bee.current_task = None
                    bee.dance_strength = 0.0
                    bee.role = "scout"

    def _get_current_allocation(self) -> Dict[str, List[str]]:
        """Get current task allocation."""
        _allocation = {}
        for task_id, data in self.task_pool.items():
            allocation[task_id] = data["assigned_foragers"].copy()
        return allocation

    def _evaluate_allocation(self, allocation: Dict[str, List[str]]) -> float:
        """Evaluate quality of task allocation."""
        if not allocation:
            return 0.0

        # Calculate coverage (tasks with at least one forager)
        _covered = sum(1 for agents in allocation.values() if agents)
        _coverage_score = covered / len(allocation) if allocation else 0

        # Calculate balance (even distribution of foragers)
        _forager_counts = [len(agents) for agents in allocation.values() if agents]
        if forager_counts:
            _avg_count = sum(forager_counts) / len(forager_counts)
            _variance = sum((c - avg_count) ** 2 for c in forager_counts) / len(forager_counts)
            _balance_score = 1.0 / (1.0 + variance)
        else:
            _balance_score = 0

        return 0.6 * coverage_score + 0.4 * balance_score

    def _detect_emergence_bee(self, allocation: Dict[str, List[str]]) -> List[str]:
        """Detect emergence indicators in bee algorithm."""
        _indicators = []

        # Check for self-organization
        if allocation:
            _covered_tasks = sum(1 for agents in allocation.values() if agents)
            if covered_tasks == len(allocation):
                indicators.append("complete_coverage")

        # Check for specialization
        _specialist_count = sum(
            1 for bee in self.bee_colony
            if bee.current_task is not None and bee.dance_strength > 0.7
        )
        if specialist_count > len(self.bee_colony) * 0.5:
            indicators.append("task_specialization")

        return indicators

    # =========================================================================
    # Flocking Behavior
    # =========================================================================

    async def run_flocking(self, agents: List[str], initial_positions: Optional[Dict[str, Tuple[float, float, float]]], iterations: int) -> SwarmDecision:
        """
        Run flocking behavior simulation for agent coordination.

        Args:
            agents: List of agent IDs
            initial_positions: Optional initial positions
            iterations: Number of simulation iterations

        Returns:
            Swarm decision with coordination metrics
        """
        # Initialize flocking agents
        self._initialize_flocking_agents(agents, initial_positions or {})

        _flock_center = (0.0, 0.0, 0.0)
        _avg_heading = (0.0, 0.0, 1.0)

        for iteration in range(iterations):
            # Update neighbors for each agent
            self._update_neighbors()

            # Apply flocking rules
            for agent in self.flocking_agents.values():
                self._apply_flocking_rules(agent)

            # Update positions
            for agent in self.flocking_agents.values():
                self._update_flocking_position(agent)

            # Calculate flock metrics
            _flock_center = self._calculate_flock_center()
            _avg_heading = self._calculate_average_heading()

        # Build decision result
        decision = SwarmDecision(
            pattern=SwarmPattern.FLOCKING,
            _participants = agents,
            _convergence_iterations = iterations,
            _final_position = {
                "center": flock_center,
                "heading": avg_heading,
            },
            confidence=self._calculate_flocking_cohesion(),
            _emergence_indicators = self._detect_emergence_flocking(),
            _quality_metrics = {
                "cohesion": self._calculate_flocking_cohesion(),
                "alignment": self._calculate_flocking_alignment(),
                "separation": self._calculate_flocking_separation(),
            }
        )

        self.decision_history.append(decision)

        logger.info(f"Flocking simulation completed: {iterations} iterations")

        return decision

    def _initialize_flocking_agents(self, agents: List[str], initial_positions: Dict[str, Tuple[float, float, float]]) -> None:
        """Initialize flocking agents."""
        self.flocking_agents.clear()

        for agent_id in agents:
            position = initial_positions.get(agent_id, (
                random.uniform(-10, 10),
                random.uniform(-10, 10),
                random.uniform(-10, 10),
            ))

            velocity = (
                random.uniform(-1, 1),
                random.uniform(-1, 1),
                random.uniform(-1, 1),
            )

            _agent = FlockingAgent(
                _agent_id = agent_id,
                position=position,
                velocity=velocity,
                heading=(0.0, 0.0, 1.0),
            )

            self.flocking_agents[agent_id] = agent

    def _update_neighbors(self) -> None:
        """Update neighbor lists for all agents."""
        for agent_id, agent in self.flocking_agents.items():
            neighbors = []
            for other_id, other in self.flocking_agents.items():
                if other_id != agent_id:
                    _distance = self._calculate_distance(agent.position, other.position)
                    if distance < self.config.flock_perception_radius:
                        neighbors.append(other_id)
            agent.neighbors = neighbors

    def _apply_flocking_rules(self, agent: FlockingAgent) -> None:
        """Apply flocking rules to update agent velocity."""
        _separation = self._calculate_separation(agent)
        _alignment = self._calculate_alignment(agent)
        _cohesion = self._calculate_cohesion(agent)

        # Apply weights
        _new_velocity = (
            agent.velocity[0] +
            separation[0] * self.config.flock_separation_weight +
            alignment[0] * self.config.flock_alignment_weight +
            cohesion[0] * self.config.flock_cohesion_weight,
            agent.velocity[1] +
            separation[1] * self.config.flock_separation_weight +
            alignment[1] * self.config.flock_alignment_weight +
            cohesion[1] * self.config.flock_cohesion_weight,
            agent.velocity[2] +
            separation[2] * self.config.flock_separation_weight +
            alignment[2] * self.config.flock_alignment_weight +
            cohesion[2] * self.config.flock_cohesion_weight,
        )

        # Normalize velocity
        _magnitude = math.sqrt(sum(v ** 2 for v in new_velocity))
        if magnitude > 0:
            _max_speed = 2.0
            _scale = min(magnitude, max_speed) / magnitude
            agent.velocity = tuple(v * scale for v in new_velocity)

        # Update heading
        agent.heading = agent.velocity

    def _calculate_separation(self, agent: FlockingAgent) -> Tuple[float, float, float]:
        """Calculate separation steering force."""
        _separation = [0.0, 0.0, 0.0]
        _count = 0

        for neighbor_id in agent.neighbors:
            neighbor = self.flocking_agents[neighbor_id]
            _distance = self._calculate_distance(agent.position, neighbor.position)

            if distance > 0 and distance < 5.0:  # Separation threshold
                _diff = tuple(a - b for a, b in zip(agent.position, neighbor.position))
                diff = tuple(d / distance for d in diff)  # Normalize
                _separation = tuple(s + d for s, d in zip(separation, diff))
                count += 1

        if count > 0:
            _separation = tuple(s / count for s in separation)

        return separation

    def _calculate_alignment(self, agent: FlockingAgent) -> Tuple[float, float, float]:
        """Calculate alignment steering force."""
        if not agent.neighbors:
            return (0.0, 0.0, 0.0)

        _avg_velocity = [0.0, 0.0, 0.0]
        for neighbor_id in agent.neighbors:
            neighbor = self.flocking_agents[neighbor_id]
            _avg_velocity = tuple(a + b for a, b in zip(avg_velocity, neighbor.velocity))

        _avg_velocity = tuple(v / len(agent.neighbors) for v in avg_velocity)

        # Steering force is difference from current velocity
        return tuple(a - c for a, c in zip(avg_velocity, agent.velocity))

    def _calculate_cohesion(self, agent: FlockingAgent) -> Tuple[float, float, float]:
        """Calculate cohesion steering force."""
        if not agent.neighbors:
            return (0.0, 0.0, 0.0)

        _center = [0.0, 0.0, 0.0]
        for neighbor_id in agent.neighbors:
            neighbor = self.flocking_agents[neighbor_id]
            _center = tuple(c + n for c, n in zip(center, neighbor.position))

        _center = tuple(c / len(agent.neighbors) for c in center)

        # Steering force toward center
        return tuple(c - p for c, p in zip(center, agent.position))

    def _update_flocking_position(self, agent: FlockingAgent) -> None:
        """Update agent position based on velocity."""
        agent.position = tuple(p + v for p, v in zip(agent.position, agent.velocity))

    def _calculate_distance(self, pos1: Tuple[float, float, float], pos2: Tuple[float, float, float]) -> float:
        """Calculate Euclidean distance between two positions."""
        return math.sqrt(sum((a - b) ** 2 for a, b in zip(pos1, pos2)))

    def _calculate_flock_center(self) -> Tuple[float, float, float]:
        """Calculate center of the flock."""
        if not self.flocking_agents:
            return (0.0, 0.0, 0.0)

        _center = [0.0, 0.0, 0.0]
        for agent in self.flocking_agents.values():
            _center = tuple(c + a for c, a in zip(center, agent.position))

        return tuple(c / len(self.flocking_agents) for c in center)

    def _calculate_average_heading(self) -> Tuple[float, float, float]:
        """Calculate average heading of the flock."""
        if not self.flocking_agents:
            return (0.0, 0.0, 1.0)

        _avg = [0.0, 0.0, 0.0]
        for agent in self.flocking_agents.values():
            _avg = tuple(a + h for a, h in zip(avg, agent.heading))

        _result = tuple(a / len(self.flocking_agents) for a in avg)

        # Normalize
        _magnitude = math.sqrt(sum(v ** 2 for v in result))
        if magnitude > 0:
            _result = tuple(v / magnitude for v in result)

        return result

    def _calculate_flocking_cohesion(self) -> float:
        """Calculate overall flock cohesion."""
        if len(self.flocking_agents) < 2:
            return 1.0

        _center = self._calculate_flock_center()
        _distances = [
            self._calculate_distance(agent.position, center)
            for agent in self.flocking_agents.values()
        ]

        _avg_distance = sum(distances) / len(distances)

        # Convert to cohesion score (closer = higher cohesion)
        return 1.0 / (1.0 + avg_distance / 10.0)

    def _calculate_flocking_alignment(self) -> float:
        """Calculate overall flock alignment."""
        if not self.flocking_agents:
            return 0.0

        _avg_heading = self._calculate_average_heading()

        _alignment_sum = 0.0
        for agent in self.flocking_agents.values():
            _dot_product = sum(a * h for a, h in zip(agent.heading, avg_heading))
            alignment_sum += dot_product

        return alignment_sum / len(self.flocking_agents)

    def _calculate_flocking_separation(self) -> float:
        """Calculate overall flock separation."""
        if len(self.flocking_agents) < 2:
            return 1.0

        _min_distances = []
        for agent_id, agent in self.flocking_agents.items():
            _min_dist = float('inf')
            for other_id, other in self.flocking_agents.items():
                if other_id != agent_id:
                    _dist = self._calculate_distance(agent.position, other.position)
                    _min_dist = min(min_dist, dist)
            if min_dist < float('inf'):
                min_distances.append(min_dist)

        if not min_distances:
            return 0.0

        _avg_min_dist = sum(min_distances) / len(min_distances)

        # Higher separation is better (up to a point)
        return min(1.0, avg_min_dist / 5.0)

    def _detect_emergence_flocking(self) -> List[str]:
        """Detect emergence indicators in flocking."""
        _indicators = []

        _cohesion = self._calculate_flocking_cohesion()
        _alignment = self._calculate_flocking_alignment()

        if cohesion > 0.8:
            indicators.append("tight_flock")

        if alignment > 0.9:
            indicators.append("synchronized_movement")

        if cohesion > 0.7 and alignment > 0.8:
            indicators.append("collective_behavior")

        return indicators

    # =========================================================================
    # Stigmergy (Indirect Coordination)
    # =========================================================================

    async def run_stigmergy(
        self,
        agents: List[str],
        environment_size: Tuple[int, int] = (100, 100),
        iterations: int = 100,
    ) -> SwarmDecision:
        """
        Run stigmergic coordination simulation.

        Args:
            agents: List of agent IDs
            environment_size: Size of the environment grid
            iterations: Number of simulation iterations

        Returns:
            Swarm decision with coordination metrics
        """
        # Initialize traces
        self.traces.clear()
        for x in range(environment_size[0]):
            self.traces[x] = []

        _agent_positions = {
            agent_id: (random.randint(0, environment_size[0] - 1),
                      random.randint(0, environment_size[1] - 1))
            for agent_id in agents
        }

        _trace_density = 0.0
        _coordination_score = 0.0

        for iteration in range(iterations):
            # Each agent leaves a trace and responds to traces
            for agent_id in agents:
                x, y = agent_positions[agent_id]

                # Leave trace
                trace = StigmergicTrace(
                    _agent_id = agent_id,
                    _trace_type = "marker",
                    content={"position": (x, y)},
                    strength=1.0,
                    decay_rate=self.config.stigmergy_decay,
                )

                if x in self.traces:
                    self.traces[x].append(trace)

                # Sense traces and move
                _new_position = self._stigmergic_movement(agent_id, (x, y), environment_size)
                agent_positions[agent_id] = new_position

            # Decay traces
            self._decay_traces()

            # Calculate metrics
            _trace_density = self._calculate_trace_density(environment_size)
            _coordination_score = self._calculate_stigmergy_coordination(agent_positions)

        # Build decision result
        decision = SwarmDecision(
            pattern=SwarmPattern.STIGMERGY,
            _participants = agents,
            _convergence_iterations = iterations,
            _final_position = {
                "trace_density": trace_density,
                "coordination_score": coordination_score,
            },
            confidence=coordination_score,
            _emergence_indicators = self._detect_emergence_stigmergy(trace_density),
            _quality_metrics = {
                "trace_density": trace_density,
                "coordination_score": coordination_score,
            }
        )

        self.decision_history.append(decision)

        logger.info(f"Stigmergy simulation completed: density={trace_density:.2f}")

        return decision

    def _stigmergic_movement(self, _agent_id: str, current_pos: Tuple[int, int], environment_size: Tuple[int, int]) -> Tuple[int, int]:
        """Move agent based on stigmergic traces."""
        x, y = current_pos

        # Find nearby traces
        _nearby_traces = []
        _search_radius = 5

        for dx in range(-search_radius, search_radius + 1):
            for dy in range(-search_radius, search_radius + 1):
                nx, ny = x + dx, y + dy
                if 0 <= nx < environment_size[0] and 0 <= ny < environment_size[1]:
                    if nx in self.traces:
                        for trace in self.traces[nx]:
                            if abs(trace.content.get("position", (0, 0))[1] - ny) <= search_radius:
                                nearby_traces.append(trace)

        if nearby_traces:
            # Move toward strongest trace
            _strongest = max(nearby_traces, key=lambda t: t.strength)
            target_x, target_y = strongest.content.get("position", (x, y))

            # Move one step toward target
            _new_x = x + (1 if target_x > x else (-1 if target_x < x else 0))
            _new_y = y + (1 if target_y > y else (-1 if target_y < y else 0))

            return (new_x, new_y)

        # Random walk if no traces
        _new_x = max(0, min(environment_size[0] - 1, x + random.randint(-1, 1)))
        _new_y = max(0, min(environment_size[1] - 1, y + random.randint(-1, 1)))

        return (new_x, new_y)

    def _decay_traces(self) -> None:
        """Decay trace strengths over time."""
        for x in self.traces:
            for trace in self.traces[x]:
                trace.strength *= (1 - trace.decay_rate)

        # Remove weak traces
        for x in self.traces:
            self.traces[x] = [t for t in self.traces[x] if t.strength > 0.1]

    def _calculate_trace_density(self, environment_size: Tuple[int, int]) -> float:
        """Calculate trace density in environment."""
        _total_traces = sum(len(traces) for traces in self.traces.values())
        _total_cells = environment_size[0] * environment_size[1]

        return total_traces / total_cells if total_cells > 0 else 0.0

    def _calculate_stigmergy_coordination(self, agent_positions: Dict[str, Tuple[int, int]]) -> float:
        """Calculate coordination score from agent positions."""
        if len(agent_positions) < 2:
            return 1.0

        # Calculate clustering
        _positions = list(agent_positions.values())
        _center_x = sum(p[0] for p in positions) / len(positions)
        _center_y = sum(p[1] for p in positions) / len(positions)

        _avg_distance = sum(
            math.sqrt((p[0] - center_x) ** 2 + (p[1] - center_y) ** 2)
            for p in positions
        ) / len(positions)

        # Higher coordination when agents cluster
        _max_distance = math.sqrt(
            (positions[0][0] - positions[-1][0]) ** 2 +
            (positions[0][1] - positions[-1][1]) ** 2
        ) if len(positions) > 1 else 1.0

        return 1.0 - (avg_distance / max_distance) if max_distance > 0 else 1.0

    def _detect_emergence_stigmergy(self, trace_density: float) -> List[str]:
        """Detect emergence indicators in stigmergy."""
        _indicators = []

        if trace_density > 0.1:
            indicators.append("trace_accumulation")

        if trace_density > 0.3:
            indicators.append("collective_marking")

        return indicators

    # =========================================================================
    # General Methods
    # =========================================================================

    def get_decision_history(self, limit: int) -> List[SwarmDecision]:
        """Get decision history."""
        return self.decision_history[-limit:]

    def get_statistics(self) -> Dict[str, Any]:
        """Get swarm intelligence statistics."""
        return {
            "total_decisions": len(self.decision_history),
            "patterns_used": list(set(d.pattern.value for d in self.decision_history)),
            "avg_confidence": (
                sum(d.confidence for d in self.decision_history) / len(self.decision_history)
                if self.decision_history else 0.0
            ),
        }

    def clear_state(self) -> None:
        """Clear all swarm state."""
        self.particles.clear()
        self.pheromone_trails.clear()
        self.bee_colony.clear()
        self.task_pool.clear()
        self.flocking_agents.clear()
        self.traces.clear()
        self.decision_history.clear()

        logger.info("Swarm intelligence state cleared")
