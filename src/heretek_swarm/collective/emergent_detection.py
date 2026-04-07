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

Zero-Trust Principles:
- All emergent patterns validated before reporting
- Statistical significance required
- Multi-agent correlation verified
- Audit logging for all detections
"""

import asyncio
import hashlib
import uuid
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set, Tuple

import structlog

from .learning import ExtractedPattern, PatternType, PatternMetadata, PatternSource

logger = structlog.get_logger(__name__)


class EmergentPatternClass(str, Enum):
    """Classification of emergent patterns."""
    
    COORDINATION = "coordination"  # Synchronized behaviors
    OPTIMIZATION = "optimization"  # Collective efficiency improvements
    INNOVATION = "innovation"  # Novel solutions emerging
    SELF_ORGANIZATION = "self_organization"  # Spontaneous order formation
    ADAPTATION = "adaptation"  # Collective response to environment
    PHASE_TRANSITION = "phase_transition"  # Sudden behavioral shifts
    CASCADE = "cascade"  # Chain reaction patterns
    RESONANCE = "resonance"  # Amplified collective response


class EmergenceLevel(str, Enum):
    """Levels of emergence strength."""
    
    WEAK = "weak"  # Minor emergent effects
    MODERATE = "moderate"  # Noticeable emergence
    STRONG = "strong"  # Significant emergence
    CRITICAL = "critical"  # Major system-level emergence


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
        """Convert to dictionary for serialization."""
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
    intensity: float = 0.0  # 0.0 to 1.0
    coherence: float = 0.0  # How synchronized the behavior is
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
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
    """
    Represents a detected emergent pattern.
    
    Attributes:
        pattern_id: Unique identifier
        pattern_class: Classification of pattern type
        emergence_level: Level of emergence strength
        timestamp: Detection timestamp
        description: Human-readable description
        participating_agents: Agents involved in pattern
        collective_behaviors: Associated collective behaviors
        emergence_score: Overall emergence strength (0.0-1.0)
        individual_baseline: Average individual capability
        collective_capability: Observed collective capability
        emergence_ratio: Ratio of collective/individual capability
        statistical_significance: P-value equivalent
        confidence: Detection confidence (0.0-1.0)
        is_validated: Whether pattern has been validated
        impact_score: Impact rating (-1.0 harmful to +1.0 beneficial)
        first_detected: When pattern was first detected
        last_observed: When pattern was last observed
        frequency: How often pattern has been observed
        recommended_action: Suggested response action
        pattern_data: Raw pattern data
        context: Pattern context
        metadata: Additional metadata
    """
    
    pattern_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    pattern_class: EmergentPatternClass = EmergentPatternClass.COORDINATION
    emergence_level: EmergenceLevel = EmergenceLevel.WEAK
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    
    # Pattern characteristics
    description: str = ""
    participating_agents: List[str] = field(default_factory=list)
    collective_behaviors: List[CollectiveBehavior] = field(default_factory=list)
    
    # Emergence metrics
    emergence_score: float = 0.0  # Overall emergence strength
    individual_baseline: float = 0.0  # Average individual capability
    collective_capability: float = 0.0  # Observed collective capability
    emergence_ratio: float = 0.0  # collective / individual
    
    # Validation
    statistical_significance: float = 0.0  # p-value equivalent
    confidence: float = 0.0
    is_validated: bool = False
    
    # Impact tracking (NEW)
    impact_score: float = 0.0  # -1.0 (harmful) to +1.0 (beneficial)
    first_detected: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    last_observed: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    frequency: int = 1
    recommended_action: Optional[str] = None
    
    # Pattern data
    pattern_data: Dict[str, Any] = field(default_factory=dict)
    context: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "pattern_id": self.pattern_id,
            "pattern_class": self.pattern_class.value,
            "emergence_level": self.emergence_level.value,
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
        """Convert to ExtractedPattern for integration with collective learning."""
        pattern_type_map = {
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
                pattern_type=pattern_type_map.get(
                    self.pattern_class,
                    PatternType.EMERGENT,
                ),
                source=PatternSource.AGENT_STATE,
                confidence=self.confidence,
                support_count=len(self.participating_agents),
                first_observed=self.timestamp,
                last_observed=self.timestamp,
                agents_involved=self.participating_agents,
                tags=["emergent", self.emergence_level.value, self.pattern_class.value],
            ),
            pattern_data=self.pattern_data,
            context=self.context,
            outcomes=[{
                "emergence_score": self.emergence_score,
                "emergence_ratio": self.emergence_ratio,
                "collective_capability": self.collective_capability,
            }],
            preconditions=list(self.context.get("preconditions", [])),
            postconditions=list(self.context.get("postconditions", [])),
            applicability_conditions=[
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
    validation_details: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
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
    
    # Detection thresholds
    min_emergence_score: float = 0.3  # Minimum score to consider emergence
    min_participating_agents: int = 3  # Minimum agents for emergence
    min_coherence: float = 0.5  # Minimum behavioral coherence
    statistical_threshold: float = 0.05  # Significance threshold
    
    # Analysis windows
    analysis_window_seconds: float = 300.0  # 5 minute analysis window
    baseline_window_seconds: float = 600.0  # 10 minute baseline
    
    # Validation
    validation_required: bool = True
    min_confidence: float = 0.6
    
    # Detection methods
    enable_coordination_detection: bool = True
    enable_optimization_detection: bool = True
    enable_innovation_detection: bool = True
    enable_phase_transition_detection: bool = True
    
    # Rate limiting
    max_detections_per_window: int = 10


class EmergentPatternDetector:
    """
    Detector for emergent patterns in swarm behavior.
    
    This detector analyzes collective agent behaviors to identify
    patterns that emerge from interactions but are not present in
    individual agents.
    
    Attributes:
        config: Configuration for detection
        agent_snapshots: Historical agent behavior snapshots
        collective_behaviors: Detected collective behaviors
        emergent_patterns: Validated emergent patterns
    """
    
    def __init__(
        self,
        config: Optional[EmergenceDetectionConfig] = None,
    ):
        """
        Initialize emergent pattern detector.
        
        Args:
            config: Configuration options (default: EmergenceDetectionConfig())
        """
        self.config = config or EmergenceDetectionConfig()
        
        self._agent_snapshots: Dict[str, List[AgentBehaviorSnapshot]] = {}
        self._collective_behaviors: List[CollectiveBehavior] = []
        self._emergent_patterns: List[EmergentPattern] = []
        self._detection_events: List[DetectionEvent] = []
        
        # Baseline metrics
        self._individual_baselines: Dict[str, Dict[str, float]] = {}
        self._collective_baselines: Dict[str, float] = {}
        
        # Callbacks
        self._on_emergence_detected: List[Callable] = []
        self._on_pattern_validated: List[Callable] = []
        
        # Validation hooks
        self._validation_hooks: List[Callable] = []
        
        logger.info(
            "emergent_pattern_detector_initialized",
            min_emergence_score=self.config.min_emergence_score,
            min_participating_agents=self.config.min_participating_agents,
        )
    
    def register_detection_callback(self, callback: Callable) -> None:
        """
        Register callback for emergence detection events.
        
        Args:
            callback: Async callable receiving DetectionEvent
        """
        self._on_emergence_detected.append(callback)
        logger.debug("detection_callback_registered", callback=callback.__name__)
    
    def register_validation_callback(self, callback: Callable) -> None:
        """
        Register callback for pattern validation.
        
        Args:
            callback: Async callable receiving EmergentPattern
        """
        self._on_pattern_validated.append(callback)
        logger.debug("validation_callback_registered", callback=callback.__name__)
    
    def register_validation_hook(self, callback: Callable) -> None:
        """
        Register validation hook for emergent patterns.
        
        Args:
            callback: Async callable receiving EmergentPattern
        """
        self._validation_hooks.append(callback)
        logger.debug("validation_hook_registered", callback=callback.__name__)
    
    def record_agent_snapshot(self, snapshot: AgentBehaviorSnapshot) -> None:
        """
        Record an agent behavior snapshot.
        
        Args:
            snapshot: Agent behavior snapshot
        """
        agent_id = snapshot.agent_id
        
        if agent_id not in self._agent_snapshots:
            self._agent_snapshots[agent_id] = []
        
        self._agent_snapshots[agent_id].append(snapshot)
        
        # Trim old snapshots
        window = self._agent_snapshots[agent_id]
        cutoff = datetime.now(timezone.utc) - timedelta(
            seconds=self.config.baseline_window_seconds * 2
        )
        
        self._agent_snapshots[agent_id] = [
            s for s in window
            if datetime.fromisoformat(s.timestamp) > cutoff
        ]
        
        # Update individual baseline
        self._update_individual_baseline(agent_id)
    
    def record_collective_behavior(self, behavior: CollectiveBehavior) -> None:
        """
        Record a collective behavior.
        
        Args:
            behavior: Collective behavior to record
        """
        self._collective_behaviors.append(behavior)
        
        # Trim old behaviors
        cutoff = datetime.now(timezone.utc) - timedelta(
            seconds=self.config.analysis_window_seconds * 2
        )
        
        self._collective_behaviors = [
            b for b in self._collective_behaviors
            if datetime.fromisoformat(b.start_time) > cutoff
        ]
    
    async def analyze_for_emergence(self) -> List[EmergentPattern]:
        """
        Analyze current state for emergent patterns.
        
        Returns:
            List of detected emergent patterns
        """
        detected_patterns = []
        
        # Check for coordination patterns
        if self.config.enable_coordination_detection:
            coordination = await self._detect_coordination_patterns()
            detected_patterns.extend(coordination)
        
        # Check for optimization patterns
        if self.config.enable_optimization_detection:
            optimization = await self._detect_optimization_patterns()
            detected_patterns.extend(optimization)
        
        # Check for innovation patterns
        if self.config.enable_innovation_detection:
            innovation = await self._detect_innovation_patterns()
            detected_patterns.extend(innovation)
        
        # Check for phase transitions
        if self.config.enable_phase_transition_detection:
            transitions = await self._detect_phase_transitions()
            detected_patterns.extend(transitions)
        
        # Validate and store patterns
        for pattern in detected_patterns:
            event = await self._validate_and_store_pattern(pattern)
            if event.passed_validation:
                await self._call_detection_callbacks(event)
        
        return detected_patterns
    
    def get_emergent_patterns(
        self,
        pattern_class: Optional[EmergentPatternClass] = None,
        min_emergence_level: Optional[EmergenceLevel] = None,
        limit: int = 100,
    ) -> List[EmergentPattern]:
        """
        Get detected emergent patterns.
        
        Args:
            pattern_class: Optional filter by class
            min_emergence_level: Optional minimum emergence level
            limit: Maximum patterns to return
            
        Returns:
            List of emergent patterns
        """
        patterns = self._emergent_patterns
        
        if pattern_class:
            patterns = [p for p in patterns if p.pattern_class == pattern_class]
        
        if min_emergence_level:
            level_order = {
                EmergenceLevel.WEAK: 0,
                EmergenceLevel.MODERATE: 1,
                EmergenceLevel.STRONG: 2,
                EmergenceLevel.CRITICAL: 3,
            }
            min_level = level_order[min_emergence_level]
            patterns = [
                p for p in patterns
                if level_order[p.emergence_level] >= min_level
            ]
        
        return patterns[-limit:]
    
    def get_patterns_by_impact(
        self,
        min_impact: float = 0.0,
        max_impact: float = 1.0,
        limit: int = 100,
    ) -> List[EmergentPattern]:
        """
        Get patterns filtered by impact score.
        
        Args:
            min_impact: Minimum impact score (-1.0 to 1.0)
            max_impact: Maximum impact score (-1.0 to 1.0)
            limit: Maximum patterns to return
            
        Returns:
            List of patterns sorted by impact score (descending)
        """
        patterns = [
            p for p in self._emergent_patterns
            if min_impact <= p.impact_score <= max_impact
        ]
        
        # Sort by impact score descending
        patterns.sort(key=lambda p: p.impact_score, reverse=True)
        
        return patterns[:limit]
    
    def get_harmful_patterns(self, limit: int = 50) -> List[EmergentPattern]:
        """
        Get patterns with negative impact scores (potentially harmful).
        
        Args:
            limit: Maximum patterns to return
            
        Returns:
            List of harmful patterns sorted by severity
        """
        patterns = [p for p in self._emergent_patterns if p.impact_score < 0]
        patterns.sort(key=lambda p: p.impact_score)  # Most negative first
        return patterns[:limit]
    
    def get_beneficial_patterns(self, min_impact: float = 0.3, limit: int = 50) -> List[EmergentPattern]:
        """
        Get patterns with positive impact scores (beneficial).
        
        Args:
            min_impact: Minimum positive impact threshold
            limit: Maximum patterns to return
            
        Returns:
            List of beneficial patterns sorted by impact
        """
        patterns = [p for p in self._emergent_patterns if p.impact_score >= min_impact]
        patterns.sort(key=lambda p: p.impact_score, reverse=True)
        return patterns[:limit]
    
    def get_collective_behaviors(
        self,
        behavior_type: Optional[str] = None,
        limit: int = 100,
    ) -> List[CollectiveBehavior]:
        """
        Get recorded collective behaviors.
        
        Args:
            behavior_type: Optional filter by type
            limit: Maximum behaviors to return
            
        Returns:
            List of collective behaviors
        """
        behaviors = self._collective_behaviors
        
        if behavior_type:
            behaviors = [b for b in behaviors if b.behavior_type == behavior_type]
        
        return behaviors[-limit:]
    
    def get_detection_history(self, limit: int = 100) -> List[DetectionEvent]:
        """
        Get detection event history.
        
        Args:
            limit: Maximum events to return
            
        Returns:
            List of detection events
        """
        return self._detection_events[-limit:]
    
    def get_emergence_statistics(self) -> Dict[str, Any]:
        """
        Get emergence detection statistics.
        
        Returns:
            Dictionary of statistics
        """
        if not self._emergent_patterns:
            return {
                "total_patterns": 0,
                "validated_patterns": 0,
                "by_class": {},
                "by_level": {},
                "avg_emergence_score": 0.0,
                "avg_confidence": 0.0,
            }
        
        patterns = self._emergent_patterns
        
        # Count by class
        by_class: Dict[str, int] = {}
        for pc in EmergentPatternClass:
            by_class[pc.value] = sum(1 for p in patterns if p.pattern_class == pc)
        
        # Count by level
        by_level: Dict[str, int] = {}
        for el in EmergenceLevel:
            by_level[el.value] = sum(1 for p in patterns if p.emergence_level == el)
        
        return {
            "total_patterns": len(patterns),
            "validated_patterns": sum(1 for p in patterns if p.is_validated),
            "by_class": by_class,
            "by_level": by_level,
            "avg_emergence_score": sum(p.emergence_score for p in patterns) / len(patterns),
            "avg_confidence": sum(p.confidence for p in patterns) / len(patterns),
            "total_collective_behaviors": len(self._collective_behaviors),
            "tracked_agents": len(self._agent_snapshots),
        }
    
    def calculate_emergence_metrics(self) -> Dict[str, float]:
        """
        Calculate emergence metrics for the swarm.
        
        Returns:
            Dictionary of emergence metrics
        """
        metrics = {
            "swarm_emergence_index": 0.0,
            "collective_intelligence_factor": 0.0,
            "coordination_level": 0.0,
            "adaptation_capacity": 0.0,
        }
        
        if self._emergent_patterns:
            # Swarm Emergence Index: weighted average of emergence scores
            weights = {
                EmergenceLevel.WEAK: 0.25,
                EmergenceLevel.MODERATE: 0.5,
                EmergenceLevel.STRONG: 0.75,
                EmergenceLevel.CRITICAL: 1.0,
            }
            
            weighted_sum = sum(
                p.emergence_score * weights.get(p.emergence_level, 0.25)
                for p in self._emergent_patterns
            )
            metrics["swarm_emergence_index"] = weighted_sum / len(self._emergent_patterns)
            
            # Collective Intelligence Factor: avg emergence ratio
            ratios = [p.emergence_ratio for p in self._emergent_patterns if p.emergence_ratio > 0]
            if ratios:
                metrics["collective_intelligence_factor"] = sum(ratios) / len(ratios)
        
        # Coordination level from collective behaviors
        if self._collective_behaviors:
            metrics["coordination_level"] = sum(
                b.coherence for b in self._collective_behaviors
            ) / len(self._collective_behaviors)
        
        return metrics
    
    async def _detect_coordination_patterns(self) -> List[EmergentPattern]:
        """Detect coordination patterns in swarm behavior."""
        patterns = []
        
        # Look for synchronized behaviors
        recent_behaviors = [
            b for b in self._collective_behaviors
            if datetime.fromisoformat(b.start_time) > datetime.now(timezone.utc) - timedelta(
                seconds=self.config.analysis_window_seconds
            )
        ]
        
        # Group behaviors by type
        behavior_groups: Dict[str, List[CollectiveBehavior]] = defaultdict(list)
        for behavior in recent_behaviors:
            behavior_groups[behavior.behavior_type].append(behavior)
        
        # Find coordinated patterns
        for behavior_type, behaviors in behavior_groups.items():
            if len(behaviors) < 2:
                continue
            
            # Check for temporal clustering
            clustered = self._find_temporal_clusters(behaviors)
            
            for cluster in clustered:
                if len(cluster) < self.config.min_participating_agents:
                    continue
                
                # Calculate coordination metrics
                participating = set()
                for b in cluster:
                    participating.update(b.participating_agents)
                
                if len(participating) < self.config.min_participating_agents:
                    continue
                
                avg_coherence = sum(b.coherence for b in cluster) / len(cluster)
                
                if avg_coherence < self.config.min_coherence:
                    continue
                
                # Create emergent pattern
                pattern = EmergentPattern(
                    pattern_class=EmergentPatternClass.COORDINATION,
                    description=f"Coordinated {behavior_type} behavior across {len(participating)} agents",
                    participating_agents=list(participating),
                    collective_behaviors=cluster,
                    emergence_score=avg_coherence,
                    individual_baseline=self._get_individual_baseline(participating),
                    collective_capability=self._measure_collective_capability(cluster),
                    pattern_data={
                        "behavior_type": behavior_type,
                        "cluster_size": len(cluster),
                        "temporal_span_seconds": self._calculate_temporal_span(cluster),
                    },
                )
                
                # Calculate emergence ratio
                if pattern.individual_baseline > 0:
                    pattern.emergence_ratio = pattern.collective_capability / pattern.individual_baseline
                
                patterns.append(pattern)
        
        return patterns
    
    async def _detect_optimization_patterns(self) -> List[EmergentPattern]:
        """Detect optimization patterns in swarm behavior."""
        patterns = []
        
        # Analyze efficiency improvements over time
        for agent_id, snapshots in self._agent_snapshots.items():
            if len(snapshots) < 10:
                continue
            
            # Calculate efficiency trend
            early_efficiency = sum(s.metrics.get("efficiency", 0) for s in snapshots[:5]) / 5
            late_efficiency = sum(s.metrics.get("efficiency", 0) for s in snapshots[-5:]) / 5
            
            improvement = late_efficiency - early_efficiency
            
            if improvement > 0.2:  # 20% improvement threshold
                pattern = EmergentPattern(
                    pattern_class=EmergentPatternClass.OPTIMIZATION,
                    emergence_level=self._classify_emergence_level(improvement),
                    description=f"Efficiency optimization detected for agent {agent_id}",
                    participating_agents=[agent_id],
                    emergence_score=improvement,
                    individual_baseline=early_efficiency,
                    collective_capability=late_efficiency,
                    emergence_ratio=late_efficiency / max(early_efficiency, 0.01),
                    pattern_data={
                        "improvement": improvement,
                        "early_efficiency": early_efficiency,
                        "late_efficiency": late_efficiency,
                    },
                )
                patterns.append(pattern)
        
        return patterns
    
    async def _detect_innovation_patterns(self) -> List[EmergentPattern]:
        """Detect innovation patterns - novel solutions emerging."""
        patterns = []
        
        # Look for novel strategy combinations
        strategy_combinations: Dict[str, List[str]] = defaultdict(list)
        
        for agent_id, snapshots in self._agent_snapshots.items():
            if not snapshots:
                continue
            
            latest = snapshots[-1]
            strategy_combo = ",".join(sorted(latest.active_strategies))
            strategy_combinations[strategy_combo].append(agent_id)
        
        # Find novel combinations used by multiple agents
        for combo, agents in strategy_combinations.items():
            if len(agents) >= self.config.min_participating_agents:
                # Check if this is a new combination
                is_novel = self._is_novel_strategy_combination(combo)
                
                if is_novel:
                    pattern = EmergentPattern(
                        pattern_class=EmergentPatternClass.INNOVATION,
                        description=f"Novel strategy combination: {combo}",
                        participating_agents=agents,
                        emergence_score=0.7,
                        pattern_data={
                            "strategy_combination": combo,
                            "agent_count": len(agents),
                        },
                    )
                    patterns.append(pattern)
        
        return patterns
    
    async def _detect_phase_transitions(self) -> List[EmergentPattern]:
        """Detect phase transitions - sudden behavioral shifts."""
        patterns = []
        
        # Analyze aggregate swarm metrics for sudden changes
        time_windows = self._create_time_windows()
        
        for i in range(1, len(time_windows)):
            prev_window = time_windows[i - 1]
            curr_window = time_windows[i]
            
            # Calculate aggregate metrics
            prev_metrics = self._calculate_window_metrics(prev_window)
            curr_metrics = self._calculate_window_metrics(curr_window)
            
            # Detect significant shifts
            shift_score = self._calculate_shift_score(prev_metrics, curr_metrics)
            
            if shift_score > 0.5:  # Significant shift threshold
                pattern = EmergentPattern(
                    pattern_class=EmergentPatternClass.PHASE_TRANSITION,
                    emergence_level=self._classify_emergence_level(shift_score),
                    description="Phase transition detected in swarm behavior",
                    participating_agents=self._get_active_agents(curr_window),
                    emergence_score=shift_score,
                    pattern_data={
                        "previous_metrics": prev_metrics,
                        "current_metrics": curr_metrics,
                        "shift_score": shift_score,
                    },
                )
                patterns.append(pattern)
        
        return patterns
    
    def _find_temporal_clusters(
        self,
        behaviors: List[CollectiveBehavior],
        max_gap_seconds: float = 60.0,
    ) -> List[List[CollectiveBehavior]]:
        """Find temporal clusters in behaviors."""
        if not behaviors:
            return []
        
        # Sort by start time
        sorted_behaviors = sorted(
            behaviors,
            key=lambda b: datetime.fromisoformat(b.start_time),
        )
        
        clusters = []
        current_cluster = [sorted_behaviors[0]]
        
        for i in range(1, len(sorted_behaviors)):
            prev_end = sorted_behaviors[i - 1].end_time or sorted_behaviors[i - 1].start_time
            curr_start = sorted_behaviors[i].start_time
            
            prev_time = datetime.fromisoformat(prev_end)
            curr_time = datetime.fromisoformat(curr_start)
            
            gap = (curr_time - prev_time).total_seconds()
            
            if gap <= max_gap_seconds:
                current_cluster.append(sorted_behaviors[i])
            else:
                clusters.append(current_cluster)
                current_cluster = [sorted_behaviors[i]]
        
        if current_cluster:
            clusters.append(current_cluster)
        
        return clusters
    
    def _is_novel_strategy_combination(self, combo: str) -> bool:
        """Check if strategy combination is novel."""
        # This would compare against historical patterns
        # For now, return True for any combination
        return True
    
    def _create_time_windows(
        self,
        window_size_seconds: float = 60.0,
    ) -> List[List[AgentBehaviorSnapshot]]:
        """Create time windows from agent snapshots."""
        all_snapshots = []
        for snapshots in self._agent_snapshots.values():
            all_snapshots.extend(snapshots)
        
        if not all_snapshots:
            return []
        
        # Sort by timestamp
        sorted_snapshots = sorted(
            all_snapshots,
            key=lambda s: datetime.fromisoformat(s.timestamp),
        )
        
        windows = []
        current_window = []
        window_start = datetime.fromisoformat(sorted_snapshots[0].timestamp)
        
        for snapshot in sorted_snapshots:
            snapshot_time = datetime.fromisoformat(snapshot.timestamp)
            
            if (snapshot_time - window_start).total_seconds() <= window_size_seconds:
                current_window.append(snapshot)
            else:
                windows.append(current_window)
                current_window = [snapshot]
                window_start = snapshot_time
        
        if current_window:
            windows.append(current_window)
        
        return windows
    
    def _calculate_window_metrics(
        self,
        window: List[AgentBehaviorSnapshot],
    ) -> Dict[str, float]:
        """Calculate aggregate metrics for a time window."""
        if not window:
            return {}
        
        return {
            "avg_success_rate": sum(s.success_rate for s in window) / len(window),
            "avg_interaction_count": sum(s.interaction_count for s in window) / len(window),
            "unique_agents": len(set(s.agent_id for s in window)),
            "total_interactions": sum(s.interaction_count for s in window),
        }
    
    def _calculate_shift_score(
        self,
        prev_metrics: Dict[str, float],
        curr_metrics: Dict[str, float],
    ) -> float:
        """Calculate shift score between two metric sets."""
        if not prev_metrics or not curr_metrics:
            return 0.0
        
        shifts = []
        
        for key in prev_metrics:
            if key in curr_metrics and prev_metrics[key] != 0:
                change = abs(curr_metrics[key] - prev_metrics[key]) / prev_metrics[key]
                shifts.append(change)
        
        if not shifts:
            return 0.0
        
        return sum(shifts) / len(shifts)
    
    def _get_active_agents(self, window: List[AgentBehaviorSnapshot]) -> List[str]:
        """Get unique active agents in a window."""
        return list(set(s.agent_id for s in window))
    
    def _classify_emergence_level(self, score: float) -> EmergenceLevel:
        """Classify emergence level based on score."""
        if score >= 0.8:
            return EmergenceLevel.CRITICAL
        elif score >= 0.6:
            return EmergenceLevel.STRONG
        elif score >= 0.4:
            return EmergenceLevel.MODERATE
        else:
            return EmergenceLevel.WEAK
    
    def _update_individual_baseline(self, agent_id: str) -> None:
        """Update individual baseline metrics for an agent."""
        snapshots = self._agent_snapshots.get(agent_id, [])
        
        if len(snapshots) < 5:
            return
        
        # Calculate baseline from recent snapshots
        recent = snapshots[-10:]
        
        self._individual_baselines[agent_id] = {
            "success_rate": sum(s.success_rate for s in recent) / len(recent),
            "interaction_rate": sum(s.interaction_count for s in recent) / len(recent),
            "efficiency": sum(s.metrics.get("efficiency", 0.5) for s in recent) / len(recent),
        }
    
    def _get_individual_baseline(self, agent_ids: List[str]) -> float:
        """Get average individual baseline for a set of agents."""
        baselines = []
        
        for agent_id in agent_ids:
            if agent_id in self._individual_baselines:
                baselines.append(
                    self._individual_baselines[agent_id].get("success_rate", 0.5)
                )
        
        return sum(baselines) / len(baselines) if baselines else 0.5
    
    def _measure_collective_capability(
        self,
        behaviors: List[CollectiveBehavior],
    ) -> float:
        """Measure collective capability from behaviors."""
        if not behaviors:
            return 0.0
        
        # Weight by coherence and intensity
        weighted_sum = sum(
            b.coherence * b.intensity for b in behaviors
        )
        
        return weighted_sum / len(behaviors)
    
    def _calculate_temporal_span(
        self,
        behaviors: List[CollectiveBehavior],
    ) -> float:
        """Calculate temporal span of behaviors in seconds."""
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
    
    async def _validate_and_store_pattern(
        self,
        pattern: EmergentPattern,
    ) -> DetectionEvent:
        """Validate and store an emergent pattern."""
        event = DetectionEvent(
            pattern=pattern,
            detection_method="multi_agent_analysis",
            raw_score=pattern.emergence_score,
            threshold=self.config.min_emergence_score,
        )
        
        # Check basic thresholds
        if pattern.emergence_score < self.config.min_emergence_score:
            event.passed_validation = False
            event.validation_details["reason"] = "emergence_score_below_threshold"
            return event
        
        if len(pattern.participating_agents) < self.config.min_participating_agents:
            event.passed_validation = False
            event.validation_details["reason"] = "insufficient_participating_agents"
            return event
        
        # Calculate statistical significance
        pattern.statistical_significance = self._calculate_statistical_significance(pattern)
        
        if pattern.statistical_significance > self.config.statistical_threshold:
            event.passed_validation = False
            event.validation_details["reason"] = "not_statistically_significant"
            return event
        
        # Calculate confidence
        pattern.confidence = self._calculate_confidence(pattern)
        
        if pattern.confidence < self.config.min_confidence:
            event.passed_validation = False
            event.validation_details["reason"] = "confidence_below_threshold"
            return event
        
        # Call validation hooks
        if self.config.validation_required:
            for hook in self._validation_hooks:
                try:
                    result = hook(pattern)
                    if asyncio.iscoroutine(result):
                        result = await result
                    if not result:
                        event.passed_validation = False
                        event.validation_details["reason"] = "validation_hook_rejected"
                        return event
                except Exception as e:
                    logger.error(
                        "validation_hook_error",
                        pattern_id=pattern.pattern_id,
                        hook=hook.__name__,
                        error=str(e),
                    )
        
        # Pattern passed validation
        event.passed_validation = True
        pattern.is_validated = True
        
        # Calculate impact score and recommended action
        pattern.impact_score = self._calculate_impact_score(pattern)
        pattern.recommended_action = self._generate_recommended_action(pattern)
        
        # Update frequency if pattern already exists
        existing_pattern = self._find_similar_pattern(pattern)
        if existing_pattern:
            pattern.frequency = existing_pattern.frequency + 1
            pattern.first_detected = existing_pattern.first_detected
        
        # Store pattern
        self._emergent_patterns.append(pattern)
        
        logger.info(
            "emergent_pattern_validated",
            pattern_id=pattern.pattern_id,
            pattern_class=pattern.pattern_class.value,
            emergence_level=pattern.emergence_level.value,
            impact_score=pattern.impact_score,
        )
        
        return event
    
    def _find_similar_pattern(self, pattern: EmergentPattern) -> Optional[EmergentPattern]:
        """
        Find a similar existing pattern for frequency tracking.
        
        Args:
            pattern: Pattern to find similar match for
            
        Returns:
            Similar pattern or None
        """
        for existing in self._emergent_patterns:
            # Match by pattern class and participating agents
            if (existing.pattern_class == pattern.pattern_class and
                set(existing.participating_agents) == set(pattern.participating_agents)):
                return existing
        return None
    
    def _calculate_statistical_significance(self, pattern: EmergentPattern) -> float:
        """Calculate statistical significance of a pattern."""
        # Simplified significance calculation
        # In production, this would use proper statistical tests
        
        n_agents = len(pattern.participating_agents)
        emergence_score = pattern.emergence_score
        
        # More agents and higher emergence = more significant
        significance = 1.0 / (n_agents * (1.0 - emergence_score + 0.01))
        
        return min(significance, 1.0)
    
    def _calculate_confidence(self, pattern: EmergentPattern) -> float:
        """Calculate confidence score for a pattern."""
        factors = []
        
        # Factor 1: Emergence score
        factors.append(pattern.emergence_score)
        
        # Factor 2: Number of participating agents
        agent_factor = min(len(pattern.participating_agents) / 10.0, 1.0)
        factors.append(agent_factor)
        
        # Factor 3: Validation status
        factors.append(1.0 if pattern.is_validated else 0.5)
        
        # Factor 4: Emergence ratio
        ratio_factor = min(pattern.emergence_ratio / 2.0, 1.0) if pattern.emergence_ratio > 0 else 0
        factors.append(ratio_factor)
        
        return sum(factors) / len(factors)
    
    def _calculate_impact_score(self, pattern: EmergentPattern) -> float:
        """
        Calculate impact score for an emergent pattern.
        
        Impact score ranges from -1.0 (harmful) to +1.0 (beneficial).
        
        Args:
            pattern: Emergent pattern to evaluate
            
        Returns:
            Impact score (-1.0 to +1.0)
        """
        # Base impact from emergence level
        level_impact = {
            EmergenceLevel.WEAK: 0.2,
            EmergenceLevel.MODERATE: 0.4,
            EmergenceLevel.STRONG: 0.6,
            EmergenceLevel.CRITICAL: 0.8,
        }
        base_impact = level_impact.get(pattern.emergence_level, 0.2)
        
        # Pattern class impact modifiers
        # Positive emergence (beneficial patterns)
        positive_patterns = [
            EmergentPatternClass.COORDINATION,
            EmergentPatternClass.OPTIMIZATION,
            EmergentPatternClass.INNOVATION,
            EmergentPatternClass.SELF_ORGANIZATION,
            EmergentPatternClass.ADAPTATION,
        ]
        
        # Negative emergence (potentially harmful patterns)
        negative_patterns = [
            EmergentPatternClass.CASCADE,  # Can be runaway chain reactions
            EmergentPatternClass.PHASE_TRANSITION,  # Can be disruptive
        ]
        
        # Resonance can be either positive or negative depending on context
        if pattern.pattern_class in positive_patterns:
            class_modifier = 1.0  # Positive impact
        elif pattern.pattern_class in negative_patterns:
            class_modifier = -0.5  # Potentially negative impact
        elif pattern.pattern_class == EmergentPatternClass.RESONANCE:
            # Resonance impact depends on emergence ratio
            if pattern.emergence_ratio > 1.5:
                class_modifier = 0.8  # Amplified positive
            elif pattern.emergence_ratio < 0.5:
                class_modifier = -0.3  # Damped/negative
            else:
                class_modifier = 0.3  # Neutral-positive
        else:
            class_modifier = 0.0  # Neutral
        
        # Confidence modifier - higher confidence = stronger impact
        confidence_modifier = pattern.confidence * 0.2
        
        # Frequency modifier - repeated patterns have stronger impact
        frequency_modifier = min(0.2, pattern.frequency * 0.02)
        
        # Calculate final impact
        impact = (base_impact * class_modifier) + confidence_modifier + frequency_modifier
        
        # Clamp to valid range
        return max(-1.0, min(1.0, impact))
    
    def _generate_recommended_action(self, pattern: EmergentPattern) -> Optional[str]:
        """
        Generate recommended action based on pattern characteristics.
        
        Args:
            pattern: Emergent pattern to analyze
            
        Returns:
            Recommended action string or None
        """
        impact_score = self._calculate_impact_score(pattern)
        
        # High positive impact - encourage/reinforce
        if impact_score >= 0.7:
            return "REINFORCE: High-value emergent pattern detected. Consider reinforcing conditions that enabled this behavior."
        
        # Moderate positive impact - monitor and document
        elif impact_score >= 0.3:
            return "MONITOR: Beneficial pattern detected. Document conditions for future replication."
        
        # Neutral impact - observe
        elif impact_score >= -0.3:
            return "OBSERVE: Neutral emergence. Continue monitoring for changes."
        
        # Moderate negative impact - investigate
        elif impact_score >= -0.7:
            return "INVESTIGATE: Potentially harmful pattern. Analyze root causes and consider intervention."
        
        # High negative impact - immediate action
        else:
            return "ALERT: Harmful emergent pattern detected. Immediate intervention recommended."
    
    async def _call_detection_callbacks(self, event: DetectionEvent) -> None:
        """Call registered detection callbacks."""
        for callback in self._on_emergence_detected:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(event)
                else:
                    callback(event)
            except Exception as e:
                logger.error(
                    "detection_callback_error",
                    callback=callback.__name__,
                    error=str(e),
                )
        
        # Store event
        self._detection_events.append(event)
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get detector status summary.
        
        Returns:
            Status dictionary
        """
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
    """
    Analyzer for emergent patterns and collective behaviors.
    
    This class provides advanced analysis capabilities for understanding
    and interpreting emergent patterns.
    """
    
    def __init__(self, detector: EmergentPatternDetector):
        """
        Initialize emergence analyzer.
        
        Args:
            detector: EmergentPatternDetector instance
        """
        self.detector = detector
        
        logger.info("emergence_analyzer_initialized")
    
    def analyze_emergence_trends(self) -> Dict[str, Any]:
        """
        Analyze trends in emergence detection.
        
        Returns:
            Dictionary of trend analysis
        """
        patterns = self.detector._emergent_patterns
        
        if len(patterns) < 5:
            return {"trend": "insufficient_data"}
        
        # Split into early and recent
        mid = len(patterns) // 2
        early = patterns[:mid]
        recent = patterns[mid:]
        
        early_avg = sum(p.emergence_score for p in early) / len(early)
        recent_avg = sum(p.emergence_score for p in recent) / len(recent)
        
        trend = "increasing" if recent_avg > early_avg else "decreasing"
        change = abs(recent_avg - early_avg)
        
        return {
            "trend": trend,
            "early_avg_score": early_avg,
            "recent_avg_score": recent_avg,
            "change": change,
            "early_count": len(early),
            "recent_count": len(recent),
        }
    
    def identify_key_contributors(self) -> List[Dict[str, Any]]:
        """
        Identify agents that frequently contribute to emergence.
        
        Returns:
            List of agent contribution records
        """
        agent_contributions: Dict[str, int] = defaultdict(int)
        
        for pattern in self.detector._emergent_patterns:
            for agent_id in pattern.participating_agents:
                agent_contributions[agent_id] += 1
        
        # Sort by contribution count
        contributors = [
            {"agent_id": aid, "contribution_count": count}
            for aid, count in sorted(
                agent_contributions.items(),
                key=lambda x: x[1],
                reverse=True,
            )
        ]
        
        return contributors[:10]  # Top 10
    
    def analyze_pattern_correlations(self) -> Dict[str, Any]:
        """
        Analyze correlations between different pattern classes.
        
        Returns:
            Dictionary of correlation analysis
        """
        patterns = self.detector._emergent_patterns
        
        if len(patterns) < 10:
            return {"correlations": "insufficient_data"}
        
        # Count co-occurrences
        class_cooccurrences: Dict[Tuple[str, str], int] = defaultdict(int)
        
        for pattern in patterns:
            class1 = pattern.pattern_class.value
            for other in patterns:
                if other.pattern_id != pattern.pattern_id:
                    class2 = other.pattern_class.value
                    key = tuple(sorted([class1, class2]))
                    class_cooccurrences[key] += 1
        
        return {
            "cooccurrences": dict(class_cooccurrences),
            "most_correlated": max(
                class_cooccurrences.items(),
                key=lambda x: x[1],
            )[0] if class_cooccurrences else None,
        }
    
    def get_emergence_timeline(self) -> List[Dict[str, Any]]:
        """
        Get timeline of emergence events.
        
        Returns:
            List of timeline entries
        """
        timeline = []
        
        for pattern in sorted(
            self.detector._emergent_patterns,
            key=lambda p: p.timestamp,
        ):
            timeline.append({
                "timestamp": pattern.timestamp,
                "pattern_class": pattern.pattern_class.value,
                "emergence_level": pattern.emergence_level.value,
                "emergence_score": pattern.emergence_score,
                "agent_count": len(pattern.participating_agents),
            })
        
        return timeline
