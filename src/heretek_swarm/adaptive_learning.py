"""
Adaptive Learning Rate Controller - Session 46 Emergent Intelligence

Implements dynamic learning rate adjustment for individual agents based on
pattern success rates, failure avoidance, and convergence tracking.

Features:
- Dynamic learning rate adjustment per agent
- Success-weighted pattern adoption
- Failure pattern avoidance
- Learning convergence tracking
- Environment-adaptive learning rate
- Fitness-based behavior selection
- Capability mutation for evolution
- Zero-trust validation of all adaptive changes
"""

import asyncio
import random
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Tuple

import structlog

from .learning import ExtractedPattern, PatternType, LearningSignal

_logger = structlog.get_logger(__name__)


class LearningRateStrategy(str, Enum):
    """Strategies for learning rate adaptation."""
    
    CONSTANT = "constant"
    DECAY = "decay"
    ADAPTIVE = "adaptive"
    CONVERGENCE = "convergence"
    OPTIMISTIC = "optimistic"
    PESSIMISTIC = "pessimistic"
    EVOLUTIONARY = "evolutionary"


class AdaptationReason(str, Enum):
    """Reasons for learning rate adaptation."""
    
    SUCCESS_PATTERN = "success_pattern"
    FAILURE_PATTERN = "failure_pattern"
    CONVERGENCE_DETECTED = "convergence_detected"
    DIVERGENCE_DETECTED = "divergence_detected"
    PERFORMANCE_CHANGE = "performance_change"
    EXTERNAL_SIGNAL = "external_signal"
    TIME_DECAY = "time_decay"
    MANUAL_OVERRIDE = "manual_override"
    ENVIRONMENT_CHANGE = "environment_change"
    FITNESS_PRESSURE = "fitness_pressure"


class MutationType(str, Enum):
    """Types of capability mutations."""
    
    EXPLORATION = "exploration"
    EXPLOITATION = "exploitation"
    CROSSOVER = "crossover"
    ADAPTATION = "adaptation"


class BehaviorFitness:
    """Tracks fitness of a specific behavior."""
    
    def __init__(self, behavior_id: str, behavior_type: str, initial_fitness: float):
        self.behavior_id = behavior_id
        self.behavior_type = behavior_type
        self.fitness = initial_fitness
        self.fitness_history: List[float] = [initial_fitness]
        self.selection_count = 0
        self.success_count = 0
        self.failure_count = 0
        self.adaptation_events: List[Dict[str, Any]] = []
    
    @property
    def success_rate(self) -> float:
        total = self.success_count + self.failure_count
        if total == 0:
            return 0.5
        return self.success_count / total
    
    def update_fitness(self, success: bool, reward: float) -> float:
        if success:
            self.success_count += 1
            delta = reward
        else:
            self.failure_count += 1
            delta = -reward * 0.5
        
        self.fitness = max(0.0, min(1.0, self.fitness + delta))
        self.fitness_history.append(self.fitness)
        
        return self.fitness
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "behavior_id": self.behavior_id,
            "behavior_type": self.behavior_type,
            "fitness": self.fitness,
            "success_rate": self.success_rate,
            "selection_count": self.selection_count,
            "success_count": self.success_count,
            "failure_count": self.failure_count,
        }


class EnvironmentProfile:
    """Profile of the current environment for adaptive learning."""
    
    def __init__(self):
        self.stability: float = 0.5
        self.complexity: float = 0.5
        self.demand_profile: Dict[str, float] = {}
        self.change_frequency: float = 0.0
        self.last_change: str = datetime.now(timezone.utc).isoformat()
        self.optimal_learning_rate: float = 0.1
        self.selection_pressure: float = 0.5
    
    def update_from_observations(self, performance_variance: float, task_diversity: float, success_rate: float) -> None:
        self.stability = max(0.0, min(1.0, 1.0 - performance_variance))
        self.complexity = max(0.0, min(1.0, task_diversity * (1.0 - success_rate)))
        
        if self.stability > 0.7:
            self.optimal_learning_rate = 0.05 + (1.0 - self.stability) * 0.1
        else:
            self.optimal_learning_rate = 0.1 + (1.0 - self.stability) * 0.2
        
        self.selection_pressure = (self.complexity + (1.0 - self.stability)) / 2
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "stability": self.stability,
            "complexity": self.complexity,
            "demand_profile": self.demand_profile,
            "change_frequency": self.change_frequency,
            "last_change": self.last_change,
            "optimal_learning_rate": self.optimal_learning_rate,
            "selection_pressure": self.selection_pressure,
        }


@dataclass
class LearningRateConfig:
    """Configuration for adaptive learning rate controller."""
    
    initial_rate: float = 0.1
    min_rate: float = 0.001
    max_rate: float = 1.0
    strategy: LearningRateStrategy = LearningRateStrategy.ADAPTIVE
    decay_factor: float = 0.95
    success_boost: float = 0.1
    failure_penalty: float = 0.2
    convergence_threshold: float = 0.01
    window_size: int = 100
    validation_required: bool = True
    audit_logging: bool = True
    
    mutation_rate: float = 0.1
    crossover_rate: float = 0.2
    selection_pressure: float = 0.5
    environment_adaptation: bool = True
    fitness_threshold: float = 0.3


@dataclass
class AgentLearningState:
    """Learning state for a single agent."""
    
    agent_id: str
    current_rate: float = 0.1
    initial_rate: float = 0.1
    total_updates: int = 0
    successful_updates: int = 0
    failed_updates: int = 0
    last_adaptation: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    adaptation_count: int = 0
    convergence_score: float = 1.0
    performance_trend: float = 0.0
    adopted_patterns: List[str] = field(default_factory=list)
    avoided_patterns: List[str] = field(default_factory=list)
    rate_history: List[Tuple[str, float, AdaptationReason]] = field(default_factory=list)
    
    fitness_score: float = 0.5
    behavior_pool: Dict[str, BehaviorFitness] = field(default_factory=dict)
    
    @property
    def success_rate(self) -> float:
        if self.total_updates == 0:
            return 0.0
        return self.successful_updates / self.total_updates


@dataclass
class AdaptationEvent:
    """Represents a learning rate adaptation event."""
    
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    agent_id: str = ""
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    reason: AdaptationReason = AdaptationReason.EXTERNAL_SIGNAL
    old_rate: float = 0.0
    new_rate: float = 0.0
    delta: float = 0.0
    trigger_pattern_id: Optional[str] = None
    trigger_signal_id: Optional[str] = None
    validation_passed: bool = False
    validation_details: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_id": self.event_id,
            "agent_id": self.agent_id,
            "timestamp": self.timestamp,
            "reason": self.reason.value,
            "old_rate": self.old_rate,
            "new_rate": self.new_rate,
            "delta": self.delta,
            "trigger_pattern_id": self.trigger_pattern_id,
            "trigger_signal_id": self.trigger_signal_id,
            "validation_passed": self.validation_passed,
            "validation_details": self.validation_details,
            "metadata": self.metadata,
        }


@dataclass
class ConvergenceMetrics:
    """Metrics for tracking learning convergence."""
    
    agent_id: str
    is_converged: bool = False
    convergence_score: float = 1.0
    iterations_to_convergence: int = 0
    final_rate: float = 0.0
    rate_variance: float = 0.0
    performance_stability: float = 0.0
    last_change_iteration: int = 0
    convergence_detected_at: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "agent_id": self.agent_id,
            "is_converged": self.is_converged,
            "convergence_score": self.convergence_score,
            "iterations_to_convergence": self.iterations_to_convergence,
            "final_rate": self.final_rate,
            "rate_variance": self.rate_variance,
            "performance_stability": self.performance_stability,
            "last_change_iteration": self.last_change_iteration,
            "convergence_detected_at": self.convergence_detected_at,
        }


@dataclass
class EvolutionResult:
    """Result of an evolution cycle."""
    
    mutated_behaviors: List[str] = field(default_factory=list)
    selected_behaviors: List[str] = field(default_factory=list)
    crossovers: List[Dict[str, str]] = field(default_factory=list)
    eliminated_behaviors: List[str] = field(default_factory=list)
    new_capabilities: List[str] = field(default_factory=list)
    fitness_improvement: float = 0.0


class AdaptiveLearningRateController:
    """
    Controller for adaptive learning rate adjustment with evolutionary features.
    """
    
    def __init__(self, config: Optional[LearningRateConfig]):
        self.config = config or LearningRateConfig()
        
        self._agent_states: Dict[str, AgentLearningState] = {}
        self._adaptation_events: List[AdaptationEvent] = []
        self._convergence_metrics: Dict[str, ConvergenceMetrics] = {}
        
        self._performance_windows: Dict[str, List[float]] = {}
        self._rate_windows: Dict[str, List[float]] = {}
        
        self._environment_profile = EnvironmentProfile()
        
        self._on_adaptation: List[Callable] = []
        self._on_convergence: List[Callable] = []
        self._on_evolution: List[Callable] = []
        
        self._validation_hooks: List[Callable] = []
        
        logger.info(
            "adaptive_learning_controller_initialized",
            strategy=self.config.strategy.value,
            initial_rate=self.config.initial_rate,
            mutation_rate=self.config.mutation_rate,
        )
    
    def register_adaptation_callback(self, callback: Callable) -> None:
        self._on_adaptation.append(callback)
    
    def register_convergence_callback(self, callback: Callable) -> None:
        self._on_convergence.append(callback)
    
    def register_evolution_callback(self, callback: Callable) -> None:
        self._on_evolution.append(callback)
    
    def register_validation_hook(self, callback: Callable) -> None:
        self._validation_hooks.append(callback)
    
    def get_or_create_state(self, agent_id: str) -> AgentLearningState:
        if agent_id not in self._agent_states:
            self._agent_states[agent_id] = AgentLearningState(
                agent_id=agent_id,
                current_rate=self.config.initial_rate,
                initial_rate=self.config.initial_rate,
            )
            self._performance_windows[agent_id] = []
            self._rate_windows[agent_id] = []
            self._convergence_metrics[agent_id] = ConvergenceMetrics(agent_id=agent_id)
        
        return self._agent_states[agent_id]
    
    async def record_update(self, agent_id: str, success: bool, pattern_id: Optional[str]) -> None:
        _state = self.get_or_create_state(agent_id)
        
        state.total_updates += 1
        if success:
            state.successful_updates += 1
        else:
            state.failed_updates += 1
        
        _performance_value = 1.0 if success else 0.0
        self._update_performance_window(agent_id, performance_value)
        
        await self._update_convergence_metrics(agent_id)
        
        if self.config.strategy == LearningRateStrategy.ADAPTIVE:
            await self._apply_adaptive_adjustment(agent_id, success, pattern_id)
        elif self.config.strategy == LearningRateStrategy.DECAY:
            await self._apply_time_decay(agent_id)
        elif self.config.strategy == LearningRateStrategy.CONVERGENCE:
            await self._apply_convergence_guided_adjustment(agent_id)
        elif self.config.strategy == LearningRateStrategy.EVOLUTIONARY:
            await self._apply_evolutionary_adjustment(agent_id, success, pattern_id)
        
        self._update_environment_profile()
    
    async def evolve_behaviors(self, agent_id: str, environment_demands: Optional[Dict[str, float]]) -> EvolutionResult:
        _state = self.get_or_create_state(agent_id)
        _result = EvolutionResult()
        
        if environment_demands:
            self._environment_profile.demand_profile = environment_demands
        
        _selection_pressure = self._environment_profile.selection_pressure
        
        _mutated_ids = await self._mutate_capabilities(agent_id, selection_pressure)
        result.mutated_behaviors = mutated_ids
        
        _selected_ids = await self._select_fittest(agent_id, environment_demands)
        result.selected_behaviors = selected_ids
        
        _crossover_results = await self._crossover_behaviors(agent_id)
        result.crossovers = crossover_results
        
        _eliminated_ids = await self._eliminate_weak_behaviors(agent_id, selection_pressure)
        result.eliminated_behaviors = eliminated_ids
        
        _old_fitness = state.fitness_score
        state.fitness_score = self._calculate_agent_fitness(agent_id)
        result.fitness_improvement = state.fitness_score - old_fitness
        
        await self._call_evolution_callbacks(result)
        
        logger.info(
            "behaviors_evolved",
            agent_id=agent_id,
            _mutated_count = len(mutated_ids),
            _selected_count = len(selected_ids),
            _crossovers = len(crossover_results),
            _eliminated_count = len(eliminated_ids),
            _fitness_change = result.fitness_improvement,
        )
        
        return result
    
    async def mutate_capabilities(self, agent_id: str, mutation_type: MutationType) -> List[str]:
        _state = self.get_or_create_state(agent_id)
        _mutated_ids = []
        
        if mutation_type == MutationType.EXPLORATION:
            if random.random() < self.config.mutation_rate:
                _new_behavior = BehaviorFitness(
                    behavior_id=str(uuid.uuid4()),
                    behavior_type="exploration",
                    _initial_fitness = 0.3,
                )
                state.behavior_pool[new_behavior.behavior_id] = new_behavior
                state.active_behaviors.append(new_behavior.behavior_id)
                mutated_ids.append(new_behavior.behavior_id)
        
        elif mutation_type == MutationType.EXPLOITATION:
            for behavior in state.behavior_pool.values():
                if behavior.fitness > 0.6 and random.random() < self.config.mutation_rate:
                    _variant = BehaviorFitness(
                        behavior_id=str(uuid.uuid4()),
                        behavior_type=f"{behavior.behavior_type}_variant",
                        _initial_fitness = behavior.fitness * 0.9,
                    )
                    state.behavior_pool[variant.behavior_id] = variant
                    mutated_ids.append(variant.behavior_id)
        
        elif mutation_type == MutationType.ADAPTATION:
            _demands = self._environment_profile.demand_profile
            for cap_type, demand_level in demands.items():
                _current_level = state.capability_levels.get(cap_type, 0.0)
                mutation = (demand_level - current_level) * self.config.mutation_rate
                state.capability_levels[cap_type] = max(0.0, min(1.0, current_level + mutation))
        
        return mutated_ids
    
    async def select_fittest(self, agent_id: str, count: int, environment_demands: Optional[Dict[str, float]]) -> List[str]:
        return await self._select_fittest(agent_id, environment_demands, count)
    
    async def adopt_pattern(self, agent_id: str, pattern: ExtractedPattern) -> bool:
        _state = self.get_or_create_state(agent_id)
        
        if self.config.validation_required:
            _is_valid = await self._validate_pattern_adoption(agent_id, pattern)
            if not is_valid:
                logger.warning(
                    "pattern_adoption_rejected",
                    agent_id=agent_id,
                    _pattern_id = pattern.metadata.pattern_id,
                    _reason = "validation_failed",
                )
                return False
        
        if pattern.metadata.pattern_type == PatternType.FAILURE:
            state.avoided_patterns.append(pattern.metadata.pattern_id)
            await self._apply_rate_change(
                agent_id, -self.config.failure_penalty, AdaptationReason.FAILURE_PATTERN,
                _pattern_id = pattern.metadata.pattern_id,
            )
            return True
        
        state.adopted_patterns.append(pattern.metadata.pattern_id)
        
        behavior = BehaviorFitness(
            behavior_id=pattern.metadata.pattern_id,
            behavior_type=pattern.metadata.pattern_type.value,
            _initial_fitness = pattern.metadata.confidence,
        )
        state.behavior_pool[behavior.behavior_id] = behavior
        
        _confidence_boost = self.config.success_boost * pattern.metadata.confidence
        await self._apply_rate_change(
            agent_id, confidence_boost, AdaptationReason.SUCCESS_PATTERN,
            _pattern_id = pattern.metadata.pattern_id,
        )
        
        return True
    
    async def process_learning_signal(self, signal: LearningSignal) -> None:
        for target_agent in signal.target_agents:
            _state = self.get_or_create_state(target_agent)
            
            if signal.signal_type == "reward":
                _adjustment = self.config.success_boost * signal.magnitude
                _reason = AdaptationReason.EXTERNAL_SIGNAL
            elif signal.signal_type == "penalty":
                _adjustment = -self.config.failure_penalty * signal.magnitude
                _reason = AdaptationReason.EXTERNAL_SIGNAL
            else:
                continue
            
            await self._apply_rate_change(
                target_agent, adjustment, reason, trigger_signal_id=signal.signal_id,
            )
    
    def get_current_rate(self, agent_id: str) -> float:
        _state = self.get_or_create_state(agent_id)
        return state.current_rate
    
    def get_agent_state(self, agent_id: str) -> AgentLearningState:
        return self.get_or_create_state(agent_id)
    
    def get_convergence_metrics(self, agent_id: str) -> ConvergenceMetrics:
        if agent_id not in self._convergence_metrics:
            self._convergence_metrics[agent_id] = ConvergenceMetrics(agent_id=agent_id)
        return self._convergence_metrics[agent_id]
    
    def get_all_agent_states(self) -> Dict[str, AgentLearningState]:
        return self._agent_states.copy()
    
    def get_adaptation_history(self, agent_id: Optional[str], limit: int) -> List[AdaptationEvent]:
        _events = self._adaptation_events
        if agent_id:
            _events = [e for e in events if e.agent_id == agent_id]
        return events[-limit:]
    
    def get_environment_profile(self) -> Dict[str, Any]:
        return self._environment_profile.to_dict()
    
    def get_swarm_statistics(self) -> Dict[str, Any]:
        if not self._agent_states:
            return {
                "total_agents": 0, "avg_learning_rate": 0.0, "avg_success_rate": 0.0,
                "converged_agents": 0, "total_adaptations": 0, "avg_fitness": 0.0,
                "environment_stability": 0.0,
            }
        
        _states = list(self._agent_states.values())
        _converged_count = sum(1 for m in self._convergence_metrics.values() if m.is_converged)
        
        return {
            "total_agents": len(states),
            "avg_learning_rate": sum(s.current_rate for s in states) / len(states),
            "avg_success_rate": sum(s.success_rate for s in states) / len(states),
            "converged_agents": converged_count,
            "total_adaptations": len(self._adaptation_events),
            "adopted_patterns_total": sum(len(s.adopted_patterns) for s in states),
            "avoided_patterns_total": sum(len(s.avoided_patterns) for s in states),
            "avg_fitness": sum(s.fitness_score for s in states) / len(states),
            "behavior_pool_size": sum(len(s.behavior_pool) for s in states),
            "environment_stability": self._environment_profile.stability,
            "optimal_learning_rate": self._environment_profile.optimal_learning_rate,
        }
    
    async def reset_agent(self, agent_id: str) -> None:
        if agent_id in self._agent_states:
            _state = self._agent_states[agent_id]
            state.current_rate = self.config.initial_rate
            state.total_updates = 0
            state.successful_updates = 0
            state.failed_updates = 0
            state.adopted_patterns = []
            state.avoided_patterns = []
            state.convergence_score = 1.0
            state.performance_trend = 0.0
            state.rate_history = []
            state.fitness_score = 0.5
            state.behavior_pool = {}
            state.active_behaviors = []
            self._performance_windows[agent_id] = []
            self._rate_windows[agent_id] = []
    
    def _update_performance_window(self, agent_id: str, value: float) -> None:
        window = self._performance_windows.setdefault(agent_id, [])
        window.append(value)
        if len(window) > self.config.window_size:
            window.pop(0)
        
        if len(window) >= 10:
            _recent_avg = sum(window[-10:]) / 10
            _older_avg = sum(window[:-10]) / max(len(window) - 10, 1)
            _state = self._agent_states.get(agent_id)
            if state:
                state.performance_trend = recent_avg - older_avg
    
    def _update_rate_window(self, agent_id: str, rate: float) -> None:
        window = self._rate_windows.setdefault(agent_id, [])
        window.append(rate)
        if len(window) > self.config.window_size:
            window.pop(0)
    
    def _update_environment_profile(self) -> None:
        _all_performances = []
        for window in self._performance_windows.values():
            all_performances.extend(window)
        
        if len(all_performances) >= 10:
            _mean = sum(all_performances) / len(all_performances)
            _variance = sum((p - mean) ** 2 for p in all_performances) / len(all_performances)
            _unique_values = len(set(all_performances))
            _diversity = unique_values / len(all_performances)
            
            self._environment_profile.update_from_observations(variance, diversity, mean)
    
    async def _update_convergence_metrics(self, agent_id: str) -> None:
        _rate_window = self._rate_windows.get(agent_id, [])
        _perf_window = self._performance_windows.get(agent_id, [])
        
        _metrics = self._convergence_metrics[agent_id]
        _state = self._agent_states.get(agent_id)
        
        if not state:
            return
        
        if len(rate_window) >= 10:
            _mean_rate = sum(rate_window) / len(rate_window)
            _variance = sum((r - mean_rate) ** 2 for r in rate_window) / len(rate_window)
            metrics.rate_variance = variance
        else:
            metrics.rate_variance = 1.0
        
        if len(perf_window) >= 10:
            _mean_perf = sum(perf_window) / len(perf_window)
            _perf_variance = sum((p - mean_perf) ** 2 for p in perf_window) / len(perf_window)
            metrics.performance_stability = 1.0 - min(perf_variance * 4, 1.0)
        else:
            metrics.performance_stability = 1.0
        
        _rate_component = min(metrics.rate_variance * 100, 1.0)
        _stability_component = 1.0 - metrics.performance_stability
        metrics.convergence_score = (rate_component + stability_component) / 2
        
        if metrics.convergence_score < self.config.convergence_threshold and not metrics.is_converged:
            metrics.is_converged = True
            metrics.convergence_detected_at = datetime.now(timezone.utc).isoformat()
            metrics.final_rate = state.current_rate
            await self._call_convergence_callbacks(metrics)
    
    async def _apply_adaptive_adjustment(self, agent_id: str, success: bool, pattern_id: Optional[str]) -> None:
        if success:
            _adjustment = self.config.success_boost
            _reason = AdaptationReason.SUCCESS_PATTERN
        else:
            _adjustment = -self.config.failure_penalty
            _reason = AdaptationReason.FAILURE_PATTERN
        
        await self._apply_rate_change(agent_id, adjustment, reason, pattern_id=pattern_id)
    
    async def _apply_evolutionary_adjustment(self, agent_id: str, success: bool, pattern_id: Optional[str]) -> None:
        _state = self.get_or_create_state(agent_id)
        
        if success:
            _adjustment = self.config.success_boost
            _reason = AdaptationReason.SUCCESS_PATTERN
        else:
            _adjustment = -self.config.failure_penalty
            _reason = AdaptationReason.FAILURE_PATTERN
        
        _env_modifier = self._environment_profile.optimal_learning_rate / self.config.initial_rate
        adjustment *= env_modifier
        
        await self._apply_rate_change(agent_id, adjustment, reason, pattern_id=pattern_id)
        
        if pattern_id and pattern_id in state.behavior_pool:
            state.behavior_pool[pattern_id].update_fitness(success)
    
    async def _apply_time_decay(self, agent_id: str) -> None:
        _state = self._agent_states.get(agent_id)
        if not state:
            return
        
        last_adaptation = datetime.fromisoformat(state.last_adaptation)
        _time_diff = datetime.now(timezone.utc) - last_adaptation
        _hours_elapsed = time_diff.total_seconds() / 3600
        
        _decay_multiplier = self.config.decay_factor ** max(hours_elapsed, 0)
        _new_rate = state.current_rate * decay_multiplier
        _new_rate = max(new_rate, self.config.min_rate)
        
        if abs(new_rate - state.current_rate) > 0.001:
            await self._apply_rate_change(agent_id, new_rate - state.current_rate, AdaptationReason.TIME_DECAY)
    
    async def _apply_convergence_guided_adjustment(self, agent_id: str) -> None:
        _metrics = self._convergence_metrics.get(agent_id)
        _state = self._agent_states.get(agent_id)
        
        if not metrics or not state or metrics.is_converged:
            return
        
        _convergence_factor = metrics.convergence_score
        state.current_rate = self.config.initial_rate * convergence_factor
        state.current_rate = max(self.config.min_rate, min(state.current_rate, self.config.max_rate))
    
    async def _mutate_capabilities(self, agent_id: str, _selection_pressure: float) -> List[str]:
        _state = self.get_or_create_state(agent_id)
        _mutated_ids = []
        
        if random.random() < self.config.mutation_rate:
            _new_behavior = BehaviorFitness(
                behavior_id=str(uuid.uuid4()), behavior_type="exploration", initial_fitness=0.3,
            )
            state.behavior_pool[new_behavior.behavior_id] = new_behavior
            mutated_ids.append(new_behavior.behavior_id)
        
        for cap_type in list(state.capability_levels.keys()):
            if random.random() < self.config.mutation_rate * 0.5:
                current = state.capability_levels[cap_type]
                mutation = random.uniform(-0.1, 0.1)
                state.capability_levels[cap_type] = max(0.0, min(1.0, current + mutation))
        
        return mutated_ids
    
    async def _select_fittest(self, agent_id: str, environment_demands: Optional[Dict[str, float]], count: int) -> List[str]:
        _state = self.get_or_create_state(agent_id)
        
        if not state.behavior_pool:
            return []
        
        _behaviors_with_fitness = []
        for bid, behavior in state.behavior_pool.items():
            fitness = behavior.fitness
            
            if environment_demands and behavior.behavior_type in environment_demands:
                _demand = environment_demands[behavior.behavior_type]
                fitness *= (1.0 + demand) / 2
            
            behaviors_with_fitness.append((bid, fitness))
        
        behaviors_with_fitness.sort(key=lambda x: x[1], reverse=True)
        _selected = [bid for bid, _ in behaviors_with_fitness[:count]]
        
        state.active_behaviors = selected
        
        for bid in selected:
            if bid in state.behavior_pool:
                state.behavior_pool[bid].selection_count += 1
        
        return selected
    
    async def _crossover_behaviors(self, agent_id: str) -> List[Dict[str, str]]:
        _state = self.get_or_create_state(agent_id)
        _crossovers = []
        
        if len(state.behavior_pool) < 2:
            return crossovers
        
        _behaviors = list(state.behavior_pool.values())
        
        for _ in range(int(len(behaviors) * self.config.crossover_rate)):
            parent1, parent2 = random.sample(behaviors, 2)
            
            _offspring = BehaviorFitness(
                behavior_id=str(uuid.uuid4()),
                _behavior_type = f"{parent1.behavior_type}_x_{parent2.behavior_type}",
                _initial_fitness = (parent1.fitness + parent2.fitness) / 2,
            )
            
            state.behavior_pool[offspring.behavior_id] = offspring
            crossovers.append({
                "parent1": parent1.behavior_id,
                "parent2": parent2.behavior_id,
                "offspring": offspring.behavior_id,
            })
        
        return crossovers
    
    async def _eliminate_weak_behaviors(self, agent_id: str, selection_pressure: float) -> List[str]:
        _state = self.get_or_create_state(agent_id)
        _eliminated = []
        
        _threshold = self.config.fitness_threshold * (1.0 - selection_pressure * 0.3)
        
        _to_remove = [bid for bid, behavior in state.behavior_pool.items()
                     if behavior.fitness < threshold and behavior.selection_count > 5]
        
        for bid in to_remove:
            del state.behavior_pool[bid]
            eliminated.append(bid)
            if bid in state.active_behaviors:
                state.active_behaviors.remove(bid)
        
        return eliminated
    
    def _calculate_agent_fitness(self, agent_id: str) -> float:
        _state = self._agent_states.get(agent_id)
        if not state:
            return 0.0
        
        _factors = [state.success_rate]
        
        if state.behavior_pool:
            _avg_behavior_fitness = sum(b.fitness for b in state.behavior_pool.values()) / len(state.behavior_pool)
            factors.append(avg_behavior_fitness)
        
        if state.capability_levels:
            _avg_capability = sum(state.capability_levels.values()) / len(state.capability_levels)
            factors.append(avg_capability)
        
        if self._convergence_metrics.get(agent_id, ConvergenceMetrics(agent_id=agent_id)).is_converged:
            factors.append(1.0)
        else:
            factors.append(0.5)
        
        return sum(factors) / len(factors) if factors else 0.5
    
    async def _apply_rate_change(self, agent_id: str, delta: float, reason: AdaptationReason, pattern_id: Optional[str], trigger_signal_id: Optional[str]) -> bool:
        _state = self.get_or_create_state(agent_id)
        
        _proposed_rate = state.current_rate + delta
        _proposed_rate = max(self.config.min_rate, min(proposed_rate, self.config.max_rate))
        
        if abs(proposed_rate - state.current_rate) < 0.0001:
            return False
        
        if self.config.validation_required:
            _is_valid = await self._validate_rate_change(agent_id, state.current_rate, proposed_rate, reason)
            if not is_valid:
                logger.warning("rate_change_rejected", agent_id=agent_id, reason=reason.value)
                return False
        
        _event = AdaptationEvent(
            _agent_id = agent_id, reason=reason, old_rate=state.current_rate, new_rate=proposed_rate,
            _delta = delta, trigger_pattern_id=pattern_id, trigger_signal_id=trigger_signal_id,
        )
        
        state.current_rate = proposed_rate
        state.last_adaptation = datetime.now(timezone.utc).isoformat()
        state.adaptation_count += 1
        state.rate_history.append((event.timestamp, proposed_rate, reason))
        
        self._update_rate_window(agent_id, proposed_rate)
        self._adaptation_events.append(event)
        
        await self._call_adaptation_callbacks(event)
        
        return True
    
    async def _validate_pattern_adoption(self, _agent_id: str, pattern: ExtractedPattern) -> bool:
        if pattern.metadata.confidence < 0.3:
            return False
        if pattern.metadata.source == PatternSource.UNKNOWN:
            return False
        return True
    
    async def _validate_rate_change(self, agent_id: str, old_rate: float, new_rate: float, reason: AdaptationReason) -> bool:
        if abs(new_rate - old_rate) > 0.5:
            return False
        
        for hook in self._validation_hooks:
            try:
                _result = hook(agent_id, old_rate, new_rate, reason)
                if asyncio.iscoroutine(result):
                    _result = await result
                if not result:
                    return False
            except Exception as e:
                logger.error("validation_hook_error", error=str(e))
                return False
        
        return True
    
    async def _call_adaptation_callbacks(self, event: AdaptationEvent) -> None:
        for callback in self._on_adaptation:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(event)
                else:
                    callback(event)
            except Exception as e:
                logger.error("adaptation_callback_error", error=str(e))
    
    async def _call_convergence_callbacks(self, metrics: ConvergenceMetrics) -> None:
        for callback in self._on_convergence:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(metrics)
                else:
                    callback(metrics)
            except Exception as e:
                logger.error("convergence_callback_error", error=str(e))
    
    async def _call_evolution_callbacks(self, result: EvolutionResult) -> None:
        for callback in self._on_evolution:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(result)
                else:
                    callback(result)
            except Exception as e:
                logger.error("evolution_callback_error", error=str(e))


class LearningRateOptimizer:
    """Optimizer for learning rate hyperparameters using population-based optimization."""
    
    def __init__(self, population_size: int, mutation_rate: float):
        self.population_size = population_size
        self.mutation_rate = mutation_rate
        self.population: List[LearningRateConfig] = []
        self._initialize_population()
    
    def _initialize_population(self) -> None:
        _strategies = [LearningRateStrategy.ADAPTIVE, LearningRateStrategy.EVOLUTIONARY, LearningRateStrategy.CONVERGENCE]
        
        for i in range(self.population_size):
            _config = LearningRateConfig(
                initial_rate=0.05 + random.random() * 0.15,
                strategy=strategies[i % len(strategies)],
                mutation_rate=self.mutation_rate,
            )
            self.population.append(config)
    
    def get_config(self) -> LearningRateConfig:
        return random.choice(self.population)
    
    def update_population(self, fitness_scores: Dict[int, float]) -> None:
        _sorted_indices = sorted(fitness_scores.keys(), key=lambda x: fitness_scores[x], reverse=True)
        _survivors = [self.population[i] for i in sorted_indices[:self.population_size // 2]]
        
        _new_population = survivors.copy()
        
        while len(new_population) < self.population_size:
            _parent = random.choice(survivors)
            _child = self._mutate_config(parent)
            new_population.append(child)
        
        self.population = new_population
    
    def _mutate_config(self, config: LearningRateConfig) -> LearningRateConfig:
        return LearningRateConfig(
            _initial_rate = config.initial_rate + random.uniform(-0.02, 0.02),
            _min_rate = config.min_rate,
            _max_rate = config.max_rate,
            _strategy = config.strategy,
            _decay_factor = config.decay_factor + random.uniform(-0.05, 0.05),
            _success_boost = config.success_boost + random.uniform(-0.02, 0.02),
            _failure_penalty = config.failure_penalty + random.uniform(-0.05, 0.05),
            _mutation_rate = config.mutation_rate + random.uniform(-0.02, 0.02),
        )
