"""
Emergent Pattern Detector - Session 46 Emergent Intelligence

Implements detection of patterns emerging from swarm interactions that are
not present in individual agents. This module identifies collective behaviors,
classifies emergent patterns, and validates emergence.

Features:
- Detect patterns emerging from swarm interactions
- Identify collective behaviors not present in individual agents
- Classify emergent patterns (coordination, optimization, innovation)
- Emergent pattern validation
- Zero-trust validation of all detected patterns
- Evolution Engine for organic capability development tracking

Zero-Trust Principles:
- All emergent patterns validated before reporting
- Statistical significance required
- Multi-agent correlation verified
- Audit logging for all detections
"""

import asyncio
import uuid
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Tuple

import structlog

from .learning import ExtractedPattern, PatternType, PatternMetadata, PatternSource

_logger = structlog.get_logger(__name__)


class EmergentPatternClass(str, Enum):
    """Classification of emergent patterns."""
    
    COORDINATION = "coordination"
    OPTIMIZATION = "optimization"
    INNOVATION = "innovation"
    SELF_ORGANIZATION = "self_organization"
    ADAPTATION = "adaptation"
    PHASE_TRANSITION = "phase_transition"
    CASCADE = "cascade"
    RESONANCE = "resonance"


class EmergenceLevel(str, Enum):
    """Levels of emergence strength."""
    
    WEAK = "weak"
    MODERATE = "moderate"
    STRONG = "strong"
    CRITICAL = "critical"


class EvolutionPhase(str, Enum):
    """Phases of evolutionary development."""
    
    INITIALIZATION = "initialization"
    EXPLORATION = "exploration"
    SELECTION = "selection"
    CONSOLIDATION = "consolidation"
    EMERGENCE = "emergence"
    MATURATION = "maturation"
    EQUILIBRIUM = "equilibrium"


@dataclass
class CapabilityRecord:
    """Record of a capability gained by an agent or the swarm."""
    
    capability_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    capability_type: str = ""
    capability_name: str = ""
    description: str = ""
    
    origin_agent_id: Optional[str] = None
    contributing_agents: List[str] = field(default_factory=list)
    
    development_time_seconds: float = 0.0
    evolution_rate: float = 0.0
    
    fitness_contribution: float = 0.0
    selection_pressure: float = 0.0
    
    first_observed: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    last_reinforced: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    stabilization_time: Optional[str] = None
    is_stabilized: bool = False
    is_inherited: bool = False
    inheritance_count: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "capability_id": self.capability_id,
            "capability_type": self.capability_type,
            "capability_name": self.capability_name,
            "description": self.description,
            "origin_agent_id": self.origin_agent_id,
            "contributing_agents": self.contributing_agents,
            "development_time_seconds": self.development_time_seconds,
            "evolution_rate": self.evolution_rate,
            "fitness_contribution": self.fitness_contribution,
            "selection_pressure": self.selection_pressure,
            "first_observed": self.first_observed,
            "last_reinforced": self.last_reinforced,
            "stabilization_time": self.stabilization_time,
            "is_stabilized": self.is_stabilized,
            "is_inherited": self.is_inherited,
            "inheritance_count": self.inheritance_count,
            "metadata": self.metadata,
        }


@dataclass
class EvolutionMetrics:
    """Metrics tracking the evolution of the swarm."""
    
    evolution_rate: float = 0.0
    capabilities_per_generation: float = 0.0
    capability_diversity: float = 0.0
    
    fitness_landscape: float = 0.0
    fitness_variance: float = 0.0
    fitness_trend: float = 0.0
    
    adaptability_index: float = 0.0
    adaptation_latency: float = 0.0
    selection_fidelity: float = 0.0
    
    total_capabilities: int = 0
    stabilized_capabilities: int = 0
    inherited_capabilities: int = 0
    active_capabilities: int = 0
    
    current_phase: EvolutionPhase = EvolutionPhase.INITIALIZATION
    generations: int = 0
    generation_time_seconds: float = 0.0
    
    avg_fitness: float = 0.0
    max_fitness: float = 0.0
    min_fitness: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "evolution_rate": self.evolution_rate,
            "capabilities_per_generation": self.capabilities_per_generation,
            "capability_diversity": self.capability_diversity,
            "fitness_landscape": self.fitness_landscape,
            "fitness_variance": self.fitness_variance,
            "fitness_trend": self.fitness_trend,
            "adaptability_index": self.adaptability_index,
            "adaptation_latency": self.adaptation_latency,
            "selection_fidelity": self.selection_fidelity,
            "total_capabilities": self.total_capabilities,
            "stabilized_capabilities": self.stabilized_capabilities,
            "inherited_capabilities": self.inherited_capabilities,
            "active_capabilities": self.active_capabilities,
            "current_phase": self.current_phase.value,
            "generations": self.generations,
            "generation_time_seconds": self.generation_time_seconds,
            "avg_fitness": self.avg_fitness,
            "max_fitness": self.max_fitness,
            "min_fitness": self.min_fitness,
        }


@dataclass
class AgentCapabilitySnapshot:
    """Snapshot of agent capabilities at a point in time."""
    
    agent_id: str
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    capability_levels: Dict[str, float] = field(default_factory=dict)
    fitness_score: float = 0.0
    fitness_history: List[float] = field(default_factory=list)
    behavior_diversity: float = 0.0
    behavior_innovation: float = 0.0
    success_rate: float = 0.0
    adaptation_count: int = 0
    active_capabilities: List[str] = field(default_factory=list)
    newly_acquired: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "agent_id": self.agent_id,
            "timestamp": self.timestamp,
            "capability_levels": self.capability_levels,
            "fitness_score": self.fitness_score,
            "fitness_history": self.fitness_history,
            "behavior_diversity": self.behavior_diversity,
            "behavior_innovation": self.behavior_innovation,
            "success_rate": self.success_rate,
            "adaptation_count": self.adaptation_count,
            "active_capabilities": self.active_capabilities,
            "newly_acquired": self.newly_acquired,
        }


class EvolutionEngine:
    """
    Evolution Engine for tracking and managing organic capability development.
    
    Key Metrics:
        - evolution_rate: Speed of capability development (capabilities/hour)
        - fitness_landscape: Current environment-agent fit (0-1)
        - adaptability_index: How quickly swarm adapts to changes (0-1)
    """
    
    def __init__(self, capability_window_hours: float, stabilization_threshold: float, min_fitness_samples: int):
        self._capability_records: Dict[str, CapabilityRecord] = {}
        self._agent_snapshots: Dict[str, List[AgentCapabilitySnapshot]] = {}
        self._capability_history: List[CapabilityRecord] = []
        
        self._evolution_start: str = datetime.now(timezone.utc).isoformat()
        self._last_evolution_check: str = datetime.now(timezone.utc).isoformat()
        self._generation_counter: int = 0
        
        self._capability_window_hours = capability_window_hours
        self._stabilization_threshold = stabilization_threshold
        self._min_fitness_samples = min_fitness_samples
        
        self._metrics = EvolutionMetrics()
        
        self._on_capability_emerged: List[Callable] = []
        self._on_capability_stabilized: List[Callable] = []
        self._on_evolution_phase_changed: List[Callable] = []
        
        logger.info(
            "evolution_engine_initialized",
            _capability_window_hours = capability_window_hours,
            _stabilization_threshold = stabilization_threshold,
        )
    
    def register_capability_emerged_callback(self, callback: Callable) -> None:
        self._on_capability_emerged.append(callback)
    
    def register_capability_stabilized_callback(self, callback: Callable) -> None:
        self._on_capability_stabilized.append(callback)
    
    def register_phase_changed_callback(self, callback: Callable) -> None:
        self._on_evolution_phase_changed.append(callback)
    
    def record_capability_gain(self, agent_id: str, capability_type: str, capability_name: str, fitness_contribution: float, description: str, contributing_agents: Optional[List[str]]) -> CapabilityRecord:
        _existing_key = f"{capability_type}:{capability_name}"
        if existing_key in self._capability_records:
            record = self._capability_records[existing_key]
            record.last_reinforced = datetime.now(timezone.utc).isoformat()
            if agent_id not in record.contributing_agents:
                record.contributing_agents.append(agent_id)
            return record
        
        start_time = datetime.fromisoformat(self._evolution_start)
        development_time = (datetime.now(timezone.utc) - start_time).total_seconds()
        
        total_capabilities = len(self._capability_history)
        _hours_elapsed = max(development_time / 3600, 0.001)
        evolution_rate = (total_capabilities + 1) / hours_elapsed
        
        record = CapabilityRecord(
            capability_type=capability_type,
            _capability_name = capability_name,
            description=description,
            _origin_agent_id = agent_id,
            _contributing_agents = contributing_agents or [agent_id],
            development_time_seconds=development_time,
            evolution_rate=evolution_rate,
            fitness_contribution=fitness_contribution,
        )
        
        self._capability_records[existing_key] = record
        self._capability_history.append(record)
        
        self._update_agent_capabilities(agent_id, capability_type, capability_name)
        self._update_evolution_metrics()
        
        asyncio.create_task(self._call_capability_emerged_callbacks(record))
        
        logger.info(
            "capability_recorded",
            capability_type=capability_type,
            _capability_name = capability_name,
            agent_id=agent_id,
            evolution_rate=evolution_rate,
        )
        
        return record
    
    def detect_evolution(self, agent_states: Dict[str, Dict[str, Any]]) -> List[CapabilityRecord]:
        _new_capabilities = []
        
        for agent_id, state in agent_states.items():
            _prev_snapshot = self._get_latest_snapshot(agent_id)
            
            _current_caps = state.get("capability_levels", {})
            _current_fitness = state.get("fitness_score", 0.0)
            _current_behaviors = state.get("behaviors", [])
            
            if prev_snapshot:
                for cap_type, level in current_caps.items():
                    _prev_level = prev_snapshot.capability_levels.get(cap_type, 0.0)
                    
                    if level > prev_level + 0.2 and level > 0.5:
                        record = self.record_capability_gain(
                            agent_id=agent_id,
                            capability_type=capability_type,
                            _capability_name = f"{cap_type}_level_{int(level * 100)}",
                            fitness_contribution=level - prev_level,
                            description=f"Advanced {cap_type} capability",
                        )
                        new_capabilities.append(record)
            
            self._create_agent_snapshot(agent_id, state)
        
        self._update_evolution_metrics()
        
        return new_capabilities
    
    def assess_fitness(self, _agent_id: str, performance_history: List[float], capability_levels: Dict[str, float], environment_demand: Optional[Dict[str, float]]) -> float:
        if not performance_history:
            return 0.0
        
        _recent_perf = performance_history[-10:] if len(performance_history) >= 10 else performance_history
        _base_fitness = sum(recent_perf) / len(recent_perf)
        
        if capability_levels:
            _capability_fitness = sum(capability_levels.values()) / len(capability_levels)
        else:
            _capability_fitness = 0.5
        
        if len(performance_history) >= 10:
            _early_avg = sum(performance_history[:5]) / 5
            _late_avg = sum(performance_history[-5:]) / 5
            _trend = (late_avg - early_avg) / max(early_avg, 0.01)
            _trend_fitness = max(0, min(1, 0.5 + trend))
        else:
            _trend_fitness = 0.5
        
        if environment_demand:
            _alignment_scores = []
            for cap_type, demand_level in environment_demand.items():
                _current_level = capability_levels.get(cap_type, 0.0)
                _alignment = 1.0 - abs(current_level - demand_level)
                alignment_scores.append(max(0, alignment))
            
            _environment_fitness = sum(alignment_scores) / len(alignment_scores) if alignment_scores else 0.5
        else:
            _environment_fitness = 0.5
        
        fitness = (
            base_fitness * 0.4 +
            capability_fitness * 0.3 +
            trend_fitness * 0.15 +
            environment_fitness * 0.15
        )
        
        return max(0.0, min(1.0, fitness))
    
    def get_evolution_metrics(self) -> EvolutionMetrics:
        return self._metrics
    
    def get_capability_records(self, capability_type: Optional[str], min_fitness: Optional[float], stabilized_only: bool) -> List[CapabilityRecord]:
        _records = list(self._capability_records.values())
        
        if capability_type:
            _records = [r for r in records if r.capability_type == capability_type]
        
        if min_fitness is not None:
            _records = [r for r in records if r.fitness_contribution >= min_fitness]
        
        if stabilized_only:
            _records = [r for r in records if r.is_stabilized]
        
        return records
    
    def get_agent_capability_history(self, agent_id: str) -> List[AgentCapabilitySnapshot]:
        return self._agent_snapshots.get(agent_id, [])
    
    def _update_agent_capabilities(self, agent_id: str, _capability_type: str, _capability_name: str) -> None:
        if agent_id not in self._agent_snapshots:
            self._agent_snapshots[agent_id] = []
    
    def _get_latest_snapshot(self, agent_id: str) -> Optional[AgentCapabilitySnapshot]:
        _snapshots = self._agent_snapshots.get(agent_id, [])
        return snapshots[-1] if snapshots else None
    
    def _create_agent_snapshot(self, agent_id: str, state: Dict[str, Any]) -> AgentCapabilitySnapshot:
        _prev_snapshot = self._get_latest_snapshot(agent_id)
        
        _newly_acquired = []
        _current_caps = state.get("capability_levels", {})
        
        if prev_snapshot:
            for cap_type, level in current_caps.items():
                if cap_type not in prev_snapshot.capability_levels:
                    newly_acquired.append(cap_type)
        
        _snapshot = AgentCapabilitySnapshot(
            agent_id=agent_id,
            _capability_levels = current_caps.copy(),
            fitness_score=state.get("fitness_score", 0.0),
            _fitness_history = state.get("fitness_history", []),
            _behavior_diversity = state.get("behavior_diversity", 0.0),
            _behavior_innovation = state.get("behavior_innovation", 0.0),
            success_rate=state.get("success_rate", 0.0),
            _adaptation_count = state.get("adaptation_count", 0),
            active_capabilities=list(current_caps.keys()),
            _newly_acquired = newly_acquired,
        )
        
        if agent_id not in self._agent_snapshots:
            self._agent_snapshots[agent_id] = []
        
        self._agent_snapshots[agent_id].append(snapshot)
        
        if len(self._agent_snapshots[agent_id]) > 100:
            self._agent_snapshots[agent_id] = self._agent_snapshots[agent_id][-100:]
        
        return snapshot
    
    def _update_evolution_metrics(self) -> None:
        metrics = self._metrics
        
        metrics.total_capabilities = len(self._capability_records)
        
        metrics.stabilized_capabilities = sum(
            1 for r in self._capability_records.values() if r.is_stabilized
        )
        
        metrics.inherited_capabilities = sum(
            r.inheritance_count for r in self._capability_records.values()
        )
        
        _cutoff = datetime.now(timezone.utc) - timedelta(hours=self._capability_window_hours)
        metrics.active_capabilities = sum(
            1 for r in self._capability_records.values()
            if datetime.fromisoformat(r.last_reinforced) > cutoff
        )
        
        start_time = datetime.fromisoformat(self._evolution_start)
        _hours_elapsed = max((datetime.now(timezone.utc) - start_time).total_seconds() / 3600, 0.001)
        metrics.evolution_rate = metrics.total_capabilities / hours_elapsed
        
        if self._capability_records:
            _types = set(r.capability_type for r in self._capability_records.values())
            metrics.capability_diversity = len(types) / max(metrics.total_capabilities, 1)
        else:
            metrics.capability_diversity = 0.0
        
        _all_fitness = []
        for snapshots in self._agent_snapshots.values():
            if snapshots:
                all_fitness.append(snapshots[-1].fitness_score)
        
        if all_fitness:
            metrics.avg_fitness = sum(all_fitness) / len(all_fitness)
            metrics.max_fitness = max(all_fitness)
            metrics.min_fitness = min(all_fitness)
            metrics.fitness_variance = self._calculate_variance(all_fitness)
            
            if len(all_fitness) >= 2:
                metrics.fitness_trend = all_fitness[-1] - all_fitness[0]
        else:
            metrics.avg_fitness = 0.0
            metrics.max_fitness = 0.0
            metrics.min_fitness = 0.0
            metrics.fitness_variance = 0.0
            metrics.fitness_trend = 0.0
        
        metrics.fitness_landscape = metrics.avg_fitness
        metrics.adaptability_index = self._calculate_adaptability_index()
        
        _new_phase = self._determine_evolution_phase()
        if new_phase != metrics.current_phase:
            _old_phase = metrics.current_phase
            metrics.current_phase = new_phase
            asyncio.create_task(self._call_phase_changed_callbacks(old_phase, new_phase))
        
        metrics.generations = self._generation_counter
        metrics.selection_fidelity = self._calculate_selection_fidelity()
    
    def _calculate_variance(self, values: List[float]) -> float:
        if len(values) < 2:
            return 0.0
        _mean = sum(values) / len(values)
        return sum((v - mean) ** 2 for v in values) / len(values)
    
    def _calculate_adaptability_index(self) -> float:
        if not self._capability_history:
            return 0.5
        
        _recent_window = timedelta(hours=self._capability_window_hours)
        _cutoff = datetime.now(timezone.utc) - recent_window
        
        _recent_caps = [
            r for r in self._capability_history
            if datetime.fromisoformat(r.first_observed) > cutoff
        ]
        
        if not recent_caps:
            return 0.5
        
        _recent_rate = len(recent_caps) / self._capability_window_hours
        _avg_dev_time = sum(r.development_time_seconds for r in recent_caps) / len(recent_caps)
        
        _rate_component = min(recent_rate / 10.0, 1.0)
        _time_component = max(0, 1.0 - (avg_dev_time / 3600))
        
        adaptability = (rate_component + time_component) / 2
        
        return max(0.0, min(1.0, adaptability))
    
    def _determine_evolution_phase(self) -> EvolutionPhase:
        _total_capabilities = len(self._capability_records)
        _stabilized_count = self._metrics.stabilized_capabilities
        
        if total_capabilities > 0:
            _stabilization_ratio = stabilized_count / total_capabilities
        else:
            _stabilization_ratio = 0.0
        
        if total_capabilities == 0:
            return EvolutionPhase.INITIALIZATION
        
        if stabilization_ratio > 0.7 and self._metrics.avg_fitness > 0.7:
            return EvolutionPhase.EQUILIBRIUM
        
        if stabilization_ratio > 0.5:
            return EvolutionPhase.MATURATION
        
        if self._metrics.capability_diversity > 0.5:
            return EvolutionPhase.EMERGENCE
        
        if total_capabilities > 5:
            return EvolutionPhase.SELECTION
        
        return EvolutionPhase.EXPLORATION
    
    def _calculate_selection_fidelity(self) -> float:
        if not self._capability_records:
            return 0.5
        
        _recent_capabilities = list(self._capability_records.values())[-20:]
        
        if not recent_capabilities:
            return 0.5
        
        _high_fitness = sum(1 for r in recent_capabilities if r.fitness_contribution > 0.5)
        _selection_fidelity = high_fitness / len(recent_capabilities)
        
        return max(0.0, min(1.0, selection_fidelity))
    
    async def _call_capability_emerged_callbacks(self, record: CapabilityRecord) -> None:
        for callback in self._on_capability_emerged:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(record)
                else:
                    callback(record)
            except Exception as e:
                logger.error("capability_emerged_callback_error", error=str(e))
    
    async def _call_capability_stabilized_callbacks(self, record: CapabilityRecord) -> None:
        for callback in self._on_capability_stabilized:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(record)
                else:
                    callback(record)
            except Exception as e:
                logger.error("capability_stabilized_callback_error", error=str(e))
    
    async def _call_phase_changed_callbacks(self, old_phase: EvolutionPhase, new_phase: EvolutionPhase) -> None:
        for callback in self._on_evolution_phase_changed:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(old_phase, new_phase)
                else:
                    callback(old_phase, new_phase)
            except Exception as e:
                logger.error("phase_changed_callback_error", error=str(e))
    
    def get_status(self) -> Dict[str, Any]:
        return {
            "total_capabilities": len(self._capability_records),
            "tracked_agents": len(self._agent_snapshots),
            "current_phase": self._metrics.current_phase.value,
            "evolution_rate": self._metrics.evolution_rate,
            "fitness_landscape": self._metrics.fitness_landscape,
            "adaptability_index": self._metrics.adaptability_index,
        }


@dataclass
class AgentBehaviorSnapshot:
    """Snapshot of an agent's behavior at a point in time."""
    
    agent_id: str
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    state: str = ""
    active_strategies: List[str] = field(default_factory=list)
    decision_history: List[Dict[str, Any]] = field(default_factory=list)
    interaction_count: int = 0
    success_rate: float = 0.0
    metrics: Dict[str, float] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "agent_id": self.agent_id,
            "timestamp": self.timestamp,
            "state": self.state,
            "active_strategies": self.active_strategies,
            "decision_history": self.decision_history,
            "interaction_count": self.interaction_count,
            "success_rate": self.success_rate,
            "metrics": self.metrics,
        }


@dataclass
class CollectiveBehavior:
    """Represents a collective behavior observed in the swarm."""
    
    behavior_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    behavior_type: str = ""
    participating_agents: List[str] = field(default_factory=list)
    start_time: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    end_time: Optional[str] = None
    duration_seconds: float = 0.0
    intensity: float = 0.0
    coherence: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "behavior_id": self.behavior_id,
            "behavior_type": self.behavior_type,
            "participating_agents": self.participating_agents,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "duration_seconds": self.duration_seconds,
            "intensity": self.intensity,
            "coherence": self.coherence,
            "metadata": self.metadata,
        }


@dataclass
class EmergentPattern:
    """Represents a detected emergent pattern."""
    
    pattern_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    pattern_class: EmergentPatternClass = EmergentPatternClass.COORDINATION
    emergence_level: EmergenceLevel = EmergenceLevel.WEAK
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    
    description: str = ""
    participating_agents: List[str] = field(default_factory=list)
    collective_behaviors: List[CollectiveBehavior] = field(default_factory=list)
    
    emergence_score: float = 0.0
    individual_baseline: float = 0.0
    collective_capability: float = 0.0
    emergence_ratio: float = 0.0
    
    statistical_significance: float = 0.0
    confidence: float = 0.0
    is_validated: bool = False
    impact_score: float = 0.0
    first_detected: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    last_observed: Optional[str] = None
    pattern_data: Dict[str, Any] = field(default_factory=dict)
    context: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "description": self.description,
            "participating_agents": self.participating_agents,
            "collective_behaviors": [b.to_dict() for b in self.collective_behaviors],
            "emergence_score": self.emergence_score,
            "individual_baseline": self.individual_baseline,
            "collective_capability": self.collective_capability,
            "emergence_ratio": self.emergence_ratio,
            "statistical_significance": self.statistical_significance,
            "confidence": self.confidence,
            "is_validated": self.is_validated,
            "pattern_data": self.pattern_data,
            "context": self.context,
            "metadata": self.metadata,
        }
    
    
    def to_extracted_pattern(self) -> ExtractedPattern:
        _pattern_type_map = {
            EmergentPatternClass.COORDINATION: PatternType.COLLABORATION,
            EmergentPatternClass.OPTIMIZATION: PatternType.OPTIMIZATION,
            EmergentPatternClass.INNOVATION: PatternType.EMERGENT,
            EmergentPatternClass.SELF_ORGANIZATION: PatternType.EMERGENT,
            EmergentPatternClass.ADAPTATION: PatternType.EMERGENT,
            EmergentPatternClass.PHASE_TRANSITION: PatternType.EMERGENT,
            EmergentPatternClass.CASCADE: PatternType.COMMUNICATION,
            EmergentPatternClass.RESONANCE: PatternType.COLLABORATION,
        }
        
        return ExtractedPattern(
            metadata=PatternMetadata(
                pattern_id=self.pattern_id,
                _pattern_type = pattern_type_map.get(self.pattern_class, PatternType.EMERGENT),
                _source = PatternSource.AGENT_STATE,
                confidence=self.confidence,
                _support_count = len(self.participating_agents),
                _first_observed = self.timestamp,
                _last_observed = self.timestamp,
                _agents_involved = self.participating_agents,
                _tags = ["emergent", self.emergence_level.value, self.pattern_class.value],
            ),
            _pattern_data = self.pattern_data,
            context=self.context,
            _outcomes = [{
                "emergence_score": self.emergence_score,
                "emergence_ratio": self.emergence_ratio,
                "collective_capability": self.collective_capability,
            }],
            _preconditions = list(self.context.get("preconditions", [])),
            _postconditions = list(self.context.get("postconditions", [])),
            _applicability_conditions = [
                f"min_agents: {len(self.participating_agents)}",
                f"min_emergence_score: {self.emergence_score}",
            ],
        )


@dataclass
class DetectionEvent:
    """Represents an emergent pattern detection event."""
    
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    pattern: Optional[EmergentPattern] = None
    detection_method: str = ""
    raw_score: float = 0.0
    threshold: float = 0.0
    passed_validation: bool = False
    validation_details: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_id": self.event_id,
            "timestamp": self.timestamp,
            "pattern": self.pattern.to_dict() if self.pattern else None,
            "detection_method": self.detection_method,
            "raw_score": self.raw_score,
            "threshold": self.threshold,
            "passed_validation": self.passed_validation,
            "validation_details": self.validation_details,
            "metadata": self.metadata,
        }


@dataclass
class EmergenceDetectionConfig:
    """Configuration for emergent pattern detection."""
    
    min_emergence_score: float = 0.3
    min_participating_agents: int = 3
    min_coherence: float = 0.5
    statistical_threshold: float = 0.05
    
    analysis_window_seconds: float = 300.0
    baseline_window_seconds: float = 600.0
    
    validation_required: bool = True
    min_confidence: float = 0.6
    
    enable_coordination_detection: bool = True
    enable_optimization_detection: bool = True
    enable_innovation_detection: bool = True
    enable_phase_transition_detection: bool = True
    
    max_detections_per_window: int = 10


class EmergentPatternDetector:
    """
    Detector for emergent patterns in swarm behavior.
    """
    
    def __init__(self, config: Optional[EmergenceDetectionConfig]):
        self.config = config or EmergenceDetectionConfig()
        
        self._agent_snapshots: Dict[str, List[AgentBehaviorSnapshot]] = {}
        self._collective_behaviors: List[CollectiveBehavior] = []
        self._emergent_patterns: List[EmergentPattern] = []
        self._detection_events: List[DetectionEvent] = []
        
        self._individual_baselines: Dict[str, Dict[str, float]] = {}
        self._collective_baselines: Dict[str, float] = {}
        
        self._evolution_engine: Optional[EvolutionEngine] = None
        
        self._on_emergence_detected: List[Callable] = []
        self._on_pattern_validated: List[Callable] = []
        self._validation_hooks: List[Callable] = []
        
        logger.info(
            "emergent_pattern_detector_initialized",
            min_emergence_score=self.config.min_emergence_score,
            min_participating_agents=self.config.min_participating_agents,
        )
    
    @property
    def evolution_engine(self) -> EvolutionEngine:
        if self._evolution_engine is None:
            self._evolution_engine = EvolutionEngine()
        return self._evolution_engine
    
    def set_evolution_engine(self, engine: EvolutionEngine) -> None:
        self._evolution_engine = engine
    
    def register_detection_callback(self, callback: Callable) -> None:
        self._on_emergence_detected.append(callback)
        logger.debug("detection_callback_registered", callback=callback.__name__)
    
    def register_validation_callback(self, callback: Callable) -> None:
        self._on_pattern_validated.append(callback)
        logger.debug("validation_callback_registered", callback=callback.__name__)
    
    def register_validation_hook(self, callback: Callable) -> None:
        self._validation_hooks.append(callback)
        logger.debug("validation_hook_registered", callback=callback.__name__)
    
    def record_agent_snapshot(self, snapshot: AgentBehaviorSnapshot) -> None:
        agent_id = snapshot.agent_id
        
        if agent_id not in self._agent_snapshots:
            self._agent_snapshots[agent_id] = []
        
        self._agent_snapshots[agent_id].append(snapshot)
        
        _cutoff = datetime.now(timezone.utc) - timedelta(
            _seconds = self.config.baseline_window_seconds * 2
        )
        
        self._agent_snapshots[agent_id] = [
            s for s in self._agent_snapshots[agent_id]
            if datetime.fromisoformat(s.timestamp) > cutoff
        ]
        
        self._update_individual_baseline(agent_id)
        
        if self._evolution_engine:
            _agent_state = {
                "capability_levels": snapshot.metrics,
                "fitness_score": snapshot.success_rate,
                "behaviors": snapshot.active_strategies,
            }
            self._evolution_engine._create_agent_snapshot(agent_id, agent_state)
    
    def record_collective_behavior(self, behavior: CollectiveBehavior) -> None:
        self._collective_behaviors.append(behavior)
        
        _cutoff = datetime.now(timezone.utc) - timedelta(
            _seconds = self.config.analysis_window_seconds * 2
        )
        
        self._collective_behaviors = [
            b for b in self._collective_behaviors
            if datetime.fromisoformat(b.start_time) > cutoff
        ]
    
    async def analyze_for_emergence(self) -> List[EmergentPattern]:
        _detected_patterns = []
        
        if self.config.enable_coordination_detection:
            _coordination = await self._detect_coordination_patterns()
            detected_patterns.extend(coordination)
        
        if self.config.enable_optimization_detection:
            _optimization = await self._detect_optimization_patterns()
            detected_patterns.extend(optimization)
        
        if self.config.enable_innovation_detection:
            _innovation = await self._detect_innovation_patterns()
            detected_patterns.extend(innovation)
        
        if self.config.enable_phase_transition_detection:
            _transitions = await self._detect_phase_transitions()
            detected_patterns.extend(transitions)
        
        for pattern in detected_patterns:
            _event = await self._validate_and_store_pattern(pattern)
            if event.passed_validation:
                await self._call_detection_callbacks(event)
                
                if self._evolution_engine:
                    self._evolution_engine.record_capability_gain(
                        agent_id=pattern.participating_agents[0] if pattern.participating_agents else "unknown",
                        _capability_type = f"emergent_{pattern.pattern_class.value}",
                        _capability_name = f"{pattern.pattern_class.value}_{pattern.emergence_level.value}",
                        _fitness_contribution = pattern.impact_score,
                        _description = pattern.description,
                        _contributing_agents = pattern.participating_agents,
                    )
        
        return detected_patterns
    
    def get_emergent_patterns(self, pattern_class: Optional[EmergentPatternClass], min_emergence_level: Optional[EmergenceLevel], limit: int) -> List[EmergentPattern]:
        _patterns = self._emergent_patterns
        
        if pattern_class:
            _patterns = [p for p in patterns if p.pattern_class == pattern_class]
        
        if min_emergence_level:
            _level_order = {
                EmergenceLevel.WEAK: 0,
                EmergenceLevel.MODERATE: 1,
                EmergenceLevel.STRONG: 2,
                EmergenceLevel.CRITICAL: 3,
            }
            _min_level = level_order[min_emergence_level]
            _patterns = [
                p for p in patterns
                if level_order[p.emergence_level] >= min_level
            ]
        
        return patterns[-limit:]
    
    def get_evolution_metrics(self) -> Dict[str, Any]:
        if self._evolution_engine:
            return self._evolution_engine.get_evolution_metrics().to_dict()
        return {}
    
    async def _detect_coordination_patterns(self) -> List[EmergentPattern]:
        return []
    
    async def _detect_optimization_patterns(self) -> List[EmergentPattern]:
        return []
    
    async def _detect_innovation_patterns(self) -> List[EmergentPattern]:
        return []
    
    async def _detect_phase_transitions(self) -> List[EmergentPattern]:
        return []
    
    def _analyze_temporal_windows(self, window_size_seconds: float) -> List[List[AgentBehaviorSnapshot]]:
        _all_snapshots = []
        for snapshots in self._agent_snapshots.values():
            all_snapshots.extend(snapshots)
        
        if not all_snapshots:
            return []
        
        _sorted_snapshots = sorted(all_snapshots, key=lambda s: datetime.fromisoformat(s.timestamp))
        
        _windows = []
        _current_window = []
        _window_start = datetime.fromisoformat(sorted_snapshots[0].timestamp)
        
        for snapshot in sorted_snapshots:
            _snapshot_time = datetime.fromisoformat(snapshot.timestamp)
            
            if (snapshot_time - window_start).total_seconds() <= window_size_seconds:
                current_window.append(snapshot)
            else:
                windows.append(current_window)
                _current_window = [snapshot]
                _window_start = snapshot_time
        
        if current_window:
            windows.append(current_window)
        
        return windows
    
    def _calculate_window_metrics(self, window: List[AgentBehaviorSnapshot]) -> Dict[str, float]:
        if not window:
            return {}
        
        return {
            "avg_success_rate": sum(s.success_rate for s in window) / len(window),
            "avg_interaction_count": sum(s.interaction_count for s in window) / len(window),
            "unique_agents": len(set(s.agent_id for s in window)),
            "total_interactions": sum(s.interaction_count for s in window),
        }
    
    def _calculate_shift_score(self, prev_metrics: Dict[str, float], curr_metrics: Dict[str, float]) -> float:
        if not prev_metrics or not curr_metrics:
            return 0.0
        
        _shifts = []
        for key in prev_metrics:
            if key in curr_metrics and prev_metrics[key] != 0:
                _change = abs(curr_metrics[key] - prev_metrics[key]) / prev_metrics[key]
                shifts.append(change)
        
        if not shifts:
            return 0.0
        
        return sum(shifts) / len(shifts)
    
    def _get_active_agents(self, window: List[AgentBehaviorSnapshot]) -> List[str]:
        return list(set(s.agent_id for s in window))
    
    def _classify_emergence_level(self, score: float) -> EmergenceLevel:
        if score >= 0.8:
            return EmergenceLevel.CRITICAL
        elif score >= 0.6:
            return EmergenceLevel.STRONG
        elif score >= 0.4:
            return EmergenceLevel.MODERATE
        else:
            return EmergenceLevel.WEAK
    
    def _update_individual_baseline(self, agent_id: str) -> None:
        _snapshots = self._agent_snapshots.get(agent_id, [])
        
        if len(snapshots) < 5:
            return
        
        _recent = snapshots[-10:]
        
        self._individual_baselines[agent_id] = {
            "success_rate": sum(s.success_rate for s in recent) / len(recent),
            "interaction_rate": sum(s.interaction_count for s in recent) / len(recent),
            "efficiency": sum(s.metrics.get("efficiency", 0.5) for s in recent) / len(recent),
        }
    
    def _get_individual_baseline(self, agent_ids: List[str]) -> float:
        _baselines = []
        
        for agent_id in agent_ids:
            if agent_id in self._individual_baselines:
                baselines.append(self._individual_baselines[agent_id].get("success_rate", 0.5))
        
        return sum(baselines) / len(baselines) if baselines else 0.5
    
    def _measure_collective_capability(self, behaviors: List[CollectiveBehavior]) -> float:
        if not behaviors:
            return 0.0
        
        _weighted_sum = sum(b.coherence * b.intensity for b in behaviors)
        return weighted_sum / len(behaviors)
    
    def _calculate_temporal_span(self, behaviors: List[CollectiveBehavior]) -> float:
        if not behaviors:
            return 0.0
        
        times = []
        for b in behaviors:
            times.append(datetime.fromisoformat(b.start_time))
            if b.end_time:
                times.append(datetime.fromisoformat(b.end_time))
        
        if len(times) < 2:
            return 0.0
        
        return (max(times) - min(times)).total_seconds()
    
    async def _validate_and_store_pattern(self, pattern: EmergentPattern) -> DetectionEvent:
        _event = DetectionEvent(
            pattern=pattern,
            _detection_method = "multi_agent_analysis",
            _raw_score = pattern.emergence_score,
            _threshold = self.config.min_emergence_score,
        )
        
        if pattern.emergence_score < self.config.min_emergence_score:
            event.passed_validation = False
            event.validation_details["reason"] = "emergence_score_below_threshold"
            return event
        
        if len(pattern.participating_agents) < self.config.min_participating_agents:
            event.passed_validation = False
            event.validation_details["reason"] = "insufficient_participating_agents"
            return event
        
        pattern.statistical_significance = self._calculate_statistical_significance(pattern)
        
        if pattern.statistical_significance > self.config.statistical_threshold:
            event.passed_validation = False
            event.validation_details["reason"] = "not_statistically_significant"
            return event
        
        pattern.confidence = self._calculate_confidence(pattern)
        
        if pattern.confidence < self.config.min_confidence:
            event.passed_validation = False
            event.validation_details["reason"] = "confidence_below_threshold"
            return event
        
        if self.config.validation_required:
            for hook in self._validation_hooks:
                try:
                    _result = hook(pattern)
                    if asyncio.iscoroutine(result):
                        _result = await result
                    if not result:
                        event.passed_validation = False
                        event.validation_details["reason"] = "validation_hook_rejected"
                        return event
                except Exception as e:
                    logger.error("validation_hook_error", pattern_id=pattern.pattern_id, error=str(e))
        
        event.passed_validation = True
        pattern.is_validated = True
        
        pattern.impact_score = self._calculate_impact_score(pattern)
        pattern.recommended_action = self._generate_recommended_action(pattern)
        
        _existing_pattern = self._find_similar_pattern(pattern)
        
        if existing_pattern:
            pattern.frequency = existing_pattern.frequency + 1
            pattern.first_detected = existing_pattern.first_detected
        
        self._emergent_patterns.append(pattern)
        
        logger.info(
            "emergent_pattern_validated",
            pattern_id=pattern.pattern_id,
            pattern_class=pattern.pattern_class.value,
            emergence_level=pattern.emergence_level.value,
            _impact_score = pattern.impact_score,
        )
        
        return event
    
    def _find_similar_pattern(self, pattern: EmergentPattern) -> Optional[EmergentPattern]:
        for existing in self._emergent_patterns:
            if (existing.pattern_class == pattern.pattern_class and
                set(existing.participating_agents) == set(pattern.participating_agents)):
                return existing
        return None
    
    def _calculate_statistical_significance(self, pattern: EmergentPattern) -> float:
        _n_agents = len(pattern.participating_agents)
        emergence_score = pattern.emergence_score
        
        _significance = 1.0 / (n_agents * (1.0 - emergence_score + 0.01))
        return min(significance, 1.0)
    
    def _calculate_confidence(self, pattern: EmergentPattern) -> float:
        _factors = []
        factors.append(pattern.emergence_score)
        _agent_factor = min(len(pattern.participating_agents) / 10.0, 1.0)
        factors.append(agent_factor)
        factors.append(1.0 if pattern.is_validated else 0.5)
        _ratio_factor = min(pattern.emergence_ratio / 2.0, 1.0) if pattern.emergence_ratio > 0 else 0
        factors.append(ratio_factor)
        
        return sum(factors) / len(factors)
    
    def _calculate_impact_score(self, pattern: EmergentPattern) -> float:
        _level_impact = {
            EmergenceLevel.WEAK: 0.2,
            EmergenceLevel.MODERATE: 0.4,
            EmergenceLevel.STRONG: 0.6,
            EmergenceLevel.CRITICAL: 0.8,
        }
        _base_impact = level_impact.get(pattern.emergence_level, 0.2)
        
        _positive_patterns = [
            EmergentPatternClass.COORDINATION,
            EmergentPatternClass.OPTIMIZATION,
            EmergentPatternClass.INNOVATION,
            EmergentPatternClass.SELF_ORGANIZATION,
            EmergentPatternClass.ADAPTATION,
        ]
        
        _negative_patterns = [
            EmergentPatternClass.CASCADE,
            EmergentPatternClass.PHASE_TRANSITION,
        ]
        
        if pattern.pattern_class in positive_patterns:
            _class_modifier = 1.0
        elif pattern.pattern_class in negative_patterns:
            _class_modifier = -0.5
        elif pattern.pattern_class == EmergentPatternClass.RESONANCE:
            if pattern.emergence_ratio > 1.5:
                _class_modifier = 0.8
            elif pattern.emergence_ratio < 0.5:
                _class_modifier = -0.3
            else:
                _class_modifier = 0.3
        else:
            _class_modifier = 0.0
        
        _confidence_modifier = pattern.confidence * 0.2
        _frequency_modifier = min(0.2, pattern.frequency * 0.02)
        
        _impact = (base_impact * class_modifier) + confidence_modifier + frequency_modifier
        return max(-1.0, min(1.0, impact))
    
    def _generate_recommended_action(self, pattern: EmergentPattern) -> Optional[str]:
        _impact_score = self._calculate_impact_score(pattern)
        
        if impact_score >= 0.7:
            return "REINFORCE: High-value emergent pattern detected. Consider reinforcing conditions that enabled this behavior."
        elif impact_score >= 0.3:
            return "MONITOR: Beneficial pattern detected. Document conditions for future replication."
        elif impact_score >= -0.3:
            return "OBSERVE: Neutral emergence. Continue monitoring for changes."
        elif impact_score >= -0.7:
            return "INVESTIGATE: Potentially harmful pattern. Analyze root causes and consider intervention."
        else:
            return "ALERT: Harmful emergent pattern detected. Immediate intervention recommended."
    
    async def _call_detection_callbacks(self, event: DetectionEvent) -> None:
        for callback in self._on_emergence_detected:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(event)
                else:
                    callback(event)
            except Exception as e:
                logger.error("detection_callback_error", callback=callback.__name__, error=str(e))
        
        self._detection_events.append(event)
    
    def get_status(self) -> Dict[str, Any]:
        return {
            "total_patterns": len(self._emergent_patterns),
            "validated_patterns": sum(1 for p in self._emergent_patterns if p.is_validated),
            "total_behaviors": len(self._collective_behaviors),
            "tracked_agents": len(self._agent_snapshots),
            "config": {
                "min_emergence_score": self.config.min_emergence_score,
                "min_participating_agents": self.config.min_participating_agents,
                "validation_required": self.config.validation_required,
            },
        }


class EmergenceAnalyzer:
    """Analyzer for emergent patterns and collective behaviors."""
    
    def __init__(self, detector: EmergentPatternDetector):
        self.detector = detector
        logger.info("emergence_analyzer_initialized")
    
    def analyze_emergence_trends(self) -> Dict[str, Any]:
        _patterns = self.detector._emergent_patterns
        
        if len(patterns) < 5:
            return {"trend": "insufficient_data"}
        
        _mid = len(patterns) // 2
        _early = patterns[:mid]
        _recent = patterns[mid:]
        
        _early_avg = sum(p.emergence_score for p in early) / len(early)
        _recent_avg = sum(p.emergence_score for p in recent) / len(recent)
        
        _trend = "increasing" if recent_avg > early_avg else "decreasing"
        _change = abs(recent_avg - early_avg)
        
        return {
            "trend": trend,
            "early_avg_score": early_avg,
            "recent_avg_score": recent_avg,
            "change": change,
            "early_count": len(early),
            "recent_count": len(recent),
        }
    
    def identify_key_contributors(self) -> List[Dict[str, Any]]:
        agent_contributions: Dict[str, int] = defaultdict(int)
        
        for pattern in self.detector._emergent_patterns:
            for agent_id in pattern.participating_agents:
                agent_contributions[agent_id] += 1
        
        _contributors = [
            {"agent_id": aid, "contribution_count": count}
            for aid, count in sorted(agent_contributions.items(), key=lambda x: x[1], reverse=True)
        ]
        
        return contributors[:10]
    
    def analyze_pattern_correlations(self) -> Dict[str, Any]:
        _patterns = self.detector._emergent_patterns
        
        if len(patterns) < 10:
            return {"correlations": "insufficient_data"}
        
        class_cooccurrences: Dict[Tuple[str, str], int] = defaultdict(int)
        
        for pattern in patterns:
            _class1 = pattern.pattern_class.value
            for other in patterns:
                if other.pattern_id != pattern.pattern_id:
                    _class2 = other.pattern_class.value
                    _key = tuple(sorted([class1, class2]))
                    class_cooccurrences[key] += 1
        
        return {
            "cooccurrences": dict(class_cooccurrences),
            "most_correlated": max(class_cooccurrences.items(), key=lambda x: x[1])[0] if class_cooccurrences else None,
        }
    
    def get_emergence_timeline(self) -> List[Dict[str, Any]]:
        _timeline = []
        
        for pattern in sorted(self.detector._emergent_patterns, key=lambda p: p.timestamp):
            timeline.append({
                "timestamp": pattern.timestamp,
                "pattern_class": pattern.pattern_class.value,
                "emergence_level": pattern.emergence_level.value,
                "emergence_score": pattern.emergence_score,
                "agent_count": len(pattern.participating_agents),
            })
        
        return timeline
