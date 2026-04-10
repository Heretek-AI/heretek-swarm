"""
Adaptive Learning Rate Controller - Session 46 Emergent Intelligence

Implements dynamic learning rate adjustment for individual agents based on
pattern success rates, failure avoidance, and convergence tracking.

Features:
- Dynamic learning rate adjustment per agent
- Success-weighted pattern adoption
- Failure pattern avoidance
- Learning convergence tracking
- Zero-trust validation of all adaptive changes

Zero-Trust Principles:
- All learning rate changes validated before application
- Source attribution required for pattern adoption
- Confidence thresholds enforced
- Audit logging for all adaptations
"""

import asyncio
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Tuple

import structlog

from .learning import ExtractedPattern, PatternType, LearningSignal

logger = structlog.get_logger(__name__)


class LearningRateStrategy(str, Enum):
    """Strategies for learning rate adaptation."""
    
    CONSTANT = "constant"  # Fixed learning rate
    DECAY = "decay"  # Time-based decay
    ADAPTIVE = "adaptive"  # Success-based adaptation
    CONVERGENCE = "convergence"  # Convergence-guided
    OPTIMISTIC = "optimistic"  # Increase on success
    PESSIMISTIC = "pessimistic"  # Decrease on failure


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


@dataclass
class LearningRateConfig:
    """Configuration for adaptive learning rate controller."""
    
    initial_rate: float = 0.1  # Initial learning rate
    min_rate: float = 0.001  # Minimum learning rate
    max_rate: float = 1.0  # Maximum learning rate
    strategy: LearningRateStrategy = LearningRateStrategy.ADAPTIVE
    decay_factor: float = 0.95  # Decay factor for time-based decay
    success_boost: float = 0.1  # Rate increase on success
    failure_penalty: float = 0.2  # Rate decrease on failure
    convergence_threshold: float = 0.01  # Threshold for convergence detection
    window_size: int = 100  # Window size for moving averages
    validation_required: bool = True  # Require validation for changes
    audit_logging: bool = True  # Enable audit logging


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
    convergence_score: float = 1.0  # 1.0 = not converged, 0.0 = fully converged
    performance_trend: float = 0.0  # Positive = improving, negative = declining
    adopted_patterns: List[str] = field(default_factory=list)  # Pattern IDs
    avoided_patterns: List[str] = field(default_factory=list)  # Pattern IDs
    rate_history: List[Tuple[str, float, AdaptationReason]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "agent_id": self.agent_id,
            "current_rate": self.current_rate,
            "initial_rate": self.initial_rate,
            "total_updates": self.total_updates,
            "successful_updates": self.successful_updates,
            "failed_updates": self.failed_updates,
            "success_rate": self.success_rate,
            "last_adaptation": self.last_adaptation,
            "adaptation_count": self.adaptation_count,
            "convergence_score": self.convergence_score,
            "performance_trend": self.performance_trend,
            "adopted_patterns": self.adopted_patterns,
            "avoided_patterns": self.avoided_patterns,
            "rate_history_count": len(self.rate_history),
            "metadata": self.metadata,
        }
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate of updates."""
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
    validation_passed: bool = True
    validation_details: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
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
        """Convert to dictionary for serialization."""
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


class AdaptiveLearningRateController:
    """
    Controller for adaptive learning rate adjustment.
    
    This controller dynamically adjusts learning rates for individual agents
    based on their performance, pattern success rates, and convergence status.
    
    Attributes:
        config: Configuration for adaptive learning
        agent_states: Dictionary of agent learning states
        adaptation_events: List of adaptation events for audit
    """
    
    def __init__(
        self,
        config: Optional[LearningRateConfig] = None,
    ):
        """
        Initialize adaptive learning rate controller.
        
        Args:
            config: Configuration options (default: LearningRateConfig())
        """
        self.config = config or LearningRateConfig()
        
        self._agent_states: Dict[str, AgentLearningState] = {}
        self._adaptation_events: List[AdaptationEvent] = []
        self._convergence_metrics: Dict[str, ConvergenceMetrics] = {}
        
        # Performance tracking windows
        self._performance_windows: Dict[str, List[float]] = {}
        self._rate_windows: Dict[str, List[float]] = {}
        
        # Callbacks
        self._on_adaptation: List[Callable] = []
        self._on_convergence: List[Callable] = []
        
        # Validation hooks
        self._validation_hooks: List[Callable] = []
        
        logger.info(
            "adaptive_learning_controller_initialized",
            strategy=self.config.strategy.value,
            initial_rate=self.config.initial_rate,
        )
    
    def register_adaptation_callback(self, callback: Callable) -> None:
        """
        Register callback for adaptation events.
        
        Args:
            callback: Async callable receiving AdaptationEvent
        """
        self._on_adaptation.append(callback)
        logger.debug("adaptation_callback_registered", callback=callback.__name__)
    
    def register_convergence_callback(self, callback: Callable) -> None:
        """
        Register callback for convergence detection.
        
        Args:
            callback: Async callable receiving ConvergenceMetrics
        """
        self._on_convergence.append(callback)
        logger.debug("convergence_callback_registered", callback=callback.__name__)
    
    def register_validation_hook(self, callback: Callable) -> None:
        """
        Register validation hook for rate changes.
        
        Args:
            callback: Async callable receiving proposed rate change
        """
        self._validation_hooks.append(callback)
        logger.debug("validation_hook_registered", callback=callback.__name__)
    
    def get_or_create_state(self, agent_id: str) -> AgentLearningState:
        """
        Get or create learning state for an agent.
        
        Args:
            agent_id: Agent identifier
            
        Returns:
            AgentLearningState for the agent
        """
        if agent_id not in self._agent_states:
            self._agent_states[agent_id] = AgentLearningState(
                agent_id=agent_id,
                current_rate=self.config.initial_rate,
                initial_rate=self.config.initial_rate,
            )
            self._performance_windows[agent_id] = []
            self._rate_windows[agent_id] = []
            self._convergence_metrics[agent_id] = ConvergenceMetrics(agent_id=agent_id)
            
            logger.debug("agent_learning_state_created", agent_id=agent_id)
        
        return self._agent_states[agent_id]
    
    async def record_update(
        self,
        agent_id: str,
        success: bool,
        pattern_id: Optional[str] = None,
    ) -> None:
        """
        Record an update result for an agent.
        
        Args:
            agent_id: Agent identifier
            success: Whether the update was successful
            pattern_id: Optional pattern ID that was being applied
        """
        state = self.get_or_create_state(agent_id)
        
        state.total_updates += 1
        if success:
            state.successful_updates += 1
        else:
            state.failed_updates += 1
        
        # Update performance window
        performance_value = 1.0 if success else 0.0
        self._update_performance_window(agent_id, performance_value)
        
        # Update convergence metrics
        await self._update_convergence_metrics(agent_id)
        
        # Apply strategy-based adaptation
        if self.config.strategy == LearningRateStrategy.ADAPTIVE:
            await self._apply_adaptive_adjustment(agent_id, success, pattern_id)
        
        elif self.config.strategy == LearningRateStrategy.DECAY:
            await self._apply_time_decay(agent_id)
        
        elif self.config.strategy == LearningRateStrategy.CONVERGENCE:
            await self._apply_convergence_guided_adjustment(agent_id)
        
        logger.debug(
            "update_recorded",
            agent_id=agent_id,
            success=success,
            total_updates=state.total_updates,
            success_rate=state.success_rate,
        )
    
    async def adopt_pattern(
        self,
        agent_id: str,
        pattern: ExtractedPattern,
    ) -> bool:
        """
        Adopt a successful pattern for an agent.
        
        Args:
            agent_id: Agent identifier
            pattern: Pattern to adopt
            
        Returns:
            True if pattern was adopted successfully
        """
        state = self.get_or_create_state(agent_id)
        
        # Zero-trust validation
        if self.config.validation_required:
            is_valid = await self._validate_pattern_adoption(agent_id, pattern)
            if not is_valid:
                logger.warning(
                    "pattern_adoption_rejected",
                    agent_id=agent_id,
                    pattern_id=pattern.metadata.pattern_id,
                    reason="validation_failed",
                )
                return False
        
        # Check if pattern should be avoided
        if pattern.metadata.pattern_type == PatternType.FAILURE:
            state.avoided_patterns.append(pattern.metadata.pattern_id)
            # Decrease learning rate to avoid learning from failures
            await self._apply_rate_change(
                agent_id,
                -self.config.failure_penalty,
                AdaptationReason.FAILURE_PATTERN,
                pattern_id=pattern.metadata.pattern_id,
            )
            logger.info(
                "failure_pattern_avoided",
                agent_id=agent_id,
                pattern_id=pattern.metadata.pattern_id,
            )
            return True
        
        # Adopt successful pattern
        state.adopted_patterns.append(pattern.metadata.pattern_id)
        
        # Increase learning rate based on pattern confidence
        confidence_boost = self.config.success_boost * pattern.metadata.confidence
        await self._apply_rate_change(
            agent_id,
            confidence_boost,
            AdaptationReason.SUCCESS_PATTERN,
            pattern_id=pattern.metadata.pattern_id,
        )
        
        logger.info(
            "pattern_adopted",
            agent_id=agent_id,
            pattern_id=pattern.metadata.pattern_id,
            confidence_boost=confidence_boost,
        )
        
        return True
    
    async def process_learning_signal(self, signal: LearningSignal) -> None:
        """
        Process a learning signal and adjust rates accordingly.
        
        Args:
            signal: Learning signal to process
        """
        for target_agent in signal.target_agents:
            state = self.get_or_create_state(target_agent)
            
            # Adjust based on signal magnitude
            if signal.signal_type == "reward":
                adjustment = self.config.success_boost * signal.magnitude
                reason = AdaptationReason.EXTERNAL_SIGNAL
            elif signal.signal_type == "penalty":
                adjustment = -self.config.failure_penalty * signal.magnitude
                reason = AdaptationReason.EXTERNAL_SIGNAL
            else:
                # Neutral signal - no adjustment
                continue
            
            await self._apply_rate_change(
                target_agent,
                adjustment,
                reason,
                trigger_signal_id=signal.signal_id,
            )
        
        logger.debug(
            "learning_signal_processed",
            signal_id=signal.signal_id,
            target_count=len(signal.target_agents),
        )
    
    def get_current_rate(self, agent_id: str) -> float:
        """
        Get current learning rate for an agent.
        
        Args:
            agent_id: Agent identifier
            
        Returns:
            Current learning rate
        """
        state = self.get_or_create_state(agent_id)
        return state.current_rate
    
    def get_agent_state(self, agent_id: str) -> AgentLearningState:
        """
        Get learning state for an agent.
        
        Args:
            agent_id: Agent identifier
            
        Returns:
            AgentLearningState for the agent
        """
        return self.get_or_create_state(agent_id)
    
    def get_convergence_metrics(self, agent_id: str) -> ConvergenceMetrics:
        """
        Get convergence metrics for an agent.
        
        Args:
            agent_id: Agent identifier
            
        Returns:
            ConvergenceMetrics for the agent
        """
        if agent_id not in self._convergence_metrics:
            self._convergence_metrics[agent_id] = ConvergenceMetrics(agent_id=agent_id)
        
        return self._convergence_metrics[agent_id]
    
    def get_all_agent_states(self) -> Dict[str, AgentLearningState]:
        """
        Get all agent learning states.
        
        Returns:
            Dictionary of agent states
        """
        return self._agent_states.copy()
    
    def get_adaptation_history(
        self,
        agent_id: Optional[str] = None,
        limit: int = 100,
    ) -> List[AdaptationEvent]:
        """
        Get adaptation event history.
        
        Args:
            agent_id: Optional agent filter
            limit: Maximum events to return
            
        Returns:
            List of adaptation events
        """
        events = self._adaptation_events
        
        if agent_id:
            events = [e for e in events if e.agent_id == agent_id]
        
        return events[-limit:]
    
    def get_swarm_statistics(self) -> Dict[str, Any]:
        """
        Get swarm-wide learning statistics.
        
        Returns:
            Dictionary of swarm statistics
        """
        if not self._agent_states:
            return {
                "total_agents": 0,
                "avg_learning_rate": 0.0,
                "avg_success_rate": 0.0,
                "converged_agents": 0,
                "total_adaptations": 0,
            }
        
        states = list(self._agent_states.values())
        converged_count = sum(
            1 for m in self._convergence_metrics.values() if m.is_converged
        )
        
        return {
            "total_agents": len(states),
            "avg_learning_rate": sum(s.current_rate for s in states) / len(states),
            "avg_success_rate": sum(s.success_rate for s in states) / len(states),
            "converged_agents": converged_count,
            "total_adaptations": len(self._adaptation_events),
            "adopted_patterns_total": sum(len(s.adopted_patterns) for s in states),
            "avoided_patterns_total": sum(len(s.avoided_patterns) for s in states),
        }
    
    async def reset_agent(self, agent_id: str) -> None:
        """
        Reset learning state for an agent.
        
        Args:
            agent_id: Agent identifier
        """
        if agent_id in self._agent_states:
            state = self._agent_states[agent_id]
            state.current_rate = self.config.initial_rate
            state.total_updates = 0
            state.successful_updates = 0
            state.failed_updates = 0
            state.adopted_patterns = []
            state.avoided_patterns = []
            state.convergence_score = 1.0
            state.performance_trend = 0.0
            state.rate_history = []
            
            # Clear windows
            self._performance_windows[agent_id] = []
            self._rate_windows[agent_id] = []
            
            logger.info("agent_learning_reset", agent_id=agent_id)
    
    def _update_performance_window(self, agent_id: str, value: float) -> None:
        """Update performance tracking window for an agent."""
        window = self._performance_windows.setdefault(agent_id, [])
        window.append(value)
        
        # Trim window
        if len(window) > self.config.window_size:
            window.pop(0)
        
        # Update performance trend
        if len(window) >= 10:
            recent_avg = sum(window[-10:]) / 10
            older_avg = sum(window[:-10]) / max(len(window) - 10, 1)
            state = self._agent_states.get(agent_id)
            if state:
                state.performance_trend = recent_avg - older_avg
    
    def _update_rate_window(self, agent_id: str, rate: float) -> None:
        """Update rate tracking window for an agent."""
        window = self._rate_windows.setdefault(agent_id, [])
        window.append(rate)
        
        # Trim window
        if len(window) > self.config.window_size:
            window.pop(0)
    
    async def _update_convergence_metrics(self, agent_id: str) -> None:
        """Update convergence metrics for an agent."""
        rate_window = self._rate_windows.get(agent_id, [])
        perf_window = self._performance_windows.get(agent_id, [])
        
        metrics = self._convergence_metrics[agent_id]
        state = self._agent_states.get(agent_id)
        
        if not state:
            return
        
        # Calculate rate variance
        if len(rate_window) >= 10:
            mean_rate = sum(rate_window) / len(rate_window)
            variance = sum((r - mean_rate) ** 2 for r in rate_window) / len(rate_window)
            metrics.rate_variance = variance
        else:
            metrics.rate_variance = 1.0  # High variance with insufficient data
        
        # Calculate performance stability
        if len(perf_window) >= 10:
            mean_perf = sum(perf_window) / len(perf_window)
            perf_variance = sum((p - mean_perf) ** 2 for p in perf_window) / len(perf_window)
            metrics.performance_stability = 1.0 - min(perf_variance * 4, 1.0)
        else:
            metrics.performance_stability = 1.0
        
        # Calculate convergence score
        # Lower is more converged
        rate_component = min(metrics.rate_variance * 100, 1.0)
        stability_component = 1.0 - metrics.performance_stability
        metrics.convergence_score = (rate_component + stability_component) / 2
        
        # Check for convergence
        if metrics.convergence_score < self.config.convergence_threshold and not metrics.is_converged:
            metrics.is_converged = True
            metrics.convergence_detected_at = datetime.now(timezone.utc).isoformat()
            metrics.final_rate = state.current_rate
            
            logger.info(
                "convergence_detected",
                agent_id=agent_id,
                convergence_score=metrics.convergence_score,
                final_rate=metrics.final_rate,
            )
            
            # Call convergence callbacks
            await self._call_convergence_callbacks(metrics)
    
    async def _apply_adaptive_adjustment(
        self,
        agent_id: str,
        success: bool,
        pattern_id: Optional[str],
    ) -> None:
        """Apply adaptive adjustment based on success/failure."""
        if success:
            adjustment = self.config.success_boost
            reason = AdaptationReason.SUCCESS_PATTERN
        else:
            adjustment = -self.config.failure_penalty
            reason = AdaptationReason.FAILURE_PATTERN
        
        await self._apply_rate_change(agent_id, adjustment, reason, pattern_id=pattern_id)
    
    async def _apply_time_decay(self, agent_id: str) -> None:
        """Apply time-based decay to learning rate."""
        state = self._agent_states.get(agent_id)
        if not state:
            return
        
        # Calculate time since last adaptation
        last_adaptation = datetime.fromisoformat(state.last_adaptation)
        time_diff = datetime.now(timezone.utc) - last_adaptation
        hours_elapsed = time_diff.total_seconds() / 3600
        
        # Apply decay
        decay_multiplier = self.config.decay_factor ** max(hours_elapsed, 0)
        new_rate = state.current_rate * decay_multiplier
        
        # Ensure minimum rate
        new_rate = max(new_rate, self.config.min_rate)
        
        if abs(new_rate - state.current_rate) > 0.001:
            await self._apply_rate_change(
                agent_id,
                new_rate - state.current_rate,
                AdaptationReason.TIME_DECAY,
            )
    
    async def _apply_convergence_guided_adjustment(self, agent_id: str) -> None:
        """Apply convergence-guided adjustment."""
        metrics = self._convergence_metrics.get(agent_id)
        state = self._agent_states.get(agent_id)
        
        if not metrics or not state:
            return
        
        # Reduce learning rate as convergence approaches
        if metrics.is_converged:
            # Already converged - minimal adjustments
            return
        
        # Scale adjustment by convergence score
        convergence_factor = metrics.convergence_score
        state.current_rate = self.config.initial_rate * convergence_factor
        
        # Clamp to valid range
        state.current_rate = max(self.config.min_rate, min(state.current_rate, self.config.max_rate))
    
    async def _apply_rate_change(
        self,
        agent_id: str,
        delta: float,
        reason: AdaptationReason,
        pattern_id: Optional[str] = None,
        trigger_signal_id: Optional[str] = None,
    ) -> bool:
        """
        Apply a learning rate change with validation.
        
        Args:
            agent_id: Agent identifier
            delta: Rate change amount
            reason: Reason for change
            pattern_id: Optional triggering pattern ID
            trigger_signal_id: Optional triggering signal ID
            
        Returns:
            True if change was applied
        """
        state = self.get_or_create_state(agent_id)
        
        # Calculate proposed new rate
        proposed_rate = state.current_rate + delta
        
        # Clamp to valid range
        proposed_rate = max(self.config.min_rate, min(proposed_rate, self.config.max_rate))
        
        # Skip if no meaningful change
        if abs(proposed_rate - state.current_rate) < 0.0001:
            return False
        
        # Zero-trust validation
        if self.config.validation_required:
            is_valid = await self._validate_rate_change(
                agent_id,
                state.current_rate,
                proposed_rate,
                reason,
            )
            if not is_valid:
                logger.warning(
                    "rate_change_rejected",
                    agent_id=agent_id,
                    old_rate=state.current_rate,
                    proposed_rate=proposed_rate,
                    reason=reason.value,
                )
                return False
        
        # Create adaptation event
        event = AdaptationEvent(
            agent_id=agent_id,
            reason=reason,
            old_rate=state.current_rate,
            new_rate=proposed_rate,
            delta=delta,
            trigger_pattern_id=pattern_id,
            trigger_signal_id=trigger_signal_id,
        )
        
        # Apply change
        state.current_rate = proposed_rate
        state.last_adaptation = datetime.now(timezone.utc).isoformat()
        state.adaptation_count += 1
        state.rate_history.append((event.timestamp, proposed_rate, reason))
        
        # Update rate window
        self._update_rate_window(agent_id, proposed_rate)
        
        # Store event
        self._adaptation_events.append(event)
        
        # Call adaptation callbacks
        await self._call_adaptation_callbacks(event)
        
        logger.info(
            "rate_changed",
            agent_id=agent_id,
            old_rate=event.old_rate,
            new_rate=event.new_rate,
            reason=reason.value,
        )
        
        return True
    
    async def _validate_pattern_adoption(
        self,
        agent_id: str,
        pattern: ExtractedPattern,
    ) -> bool:
        """
        Validate pattern adoption with zero-trust principles.
        
        Args:
            agent_id: Agent identifier
            pattern: Pattern to validate
            
        Returns:
            True if pattern adoption is valid
        """
        # Check pattern confidence
        if pattern.metadata.confidence < self.config.min_rate:
            return False
        
        # Check pattern type
        if pattern.metadata.pattern_type not in [
            PatternType.SUCCESS,
            PatternType.OPTIMIZATION,
            PatternType.FAILURE,
        ]:
            return False
        
        # Call validation hooks
        for hook in self._validation_hooks:
            try:
                result = hook(agent_id, pattern)
                if asyncio.iscoroutine(result):
                    result = await result
                if not result:
                    return False
            except Exception as e:
                logger.error(
                    "validation_hook_error",
                    agent_id=agent_id,
                    hook=hook.__name__,
                    error=str(e),
                )
        
        return True
    
    async def _validate_rate_change(
        self,
        agent_id: str,
        old_rate: float,
        new_rate: float,
        reason: AdaptationReason,
    ) -> bool:
        """
        Validate rate change with zero-trust principles.
        
        Args:
            agent_id: Agent identifier
            old_rate: Current rate
            new_rate: Proposed new rate
            reason: Reason for change
            
        Returns:
            True if rate change is valid
        """
        # Check rate bounds
        if new_rate < self.config.min_rate or new_rate > self.config.max_rate:
            return False
        
        # Check for extreme changes
        if abs(new_rate - old_rate) > 0.5:
            return False
        
        # Call validation hooks
        for hook in self._validation_hooks:
            try:
                result = hook(agent_id, old_rate, new_rate, reason)
                if asyncio.iscoroutine(result):
                    result = await result
                if not result:
                    return False
            except Exception as e:
                logger.error(
                    "validation_hook_error",
                    agent_id=agent_id,
                    hook=hook.__name__,
                    error=str(e),
                )
        
        return True
    
    async def _call_adaptation_callbacks(self, event: AdaptationEvent) -> None:
        """Call registered adaptation callbacks."""
        for callback in self._on_adaptation:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(event)
                else:
                    callback(event)
            except Exception as e:
                logger.error(
                    "adaptation_callback_error",
                    callback=callback.__name__,
                    error=str(e),
                )
    
    async def _call_convergence_callbacks(self, metrics: ConvergenceMetrics) -> None:
        """Call registered convergence callbacks."""
        for callback in self._on_convergence:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(metrics)
                else:
                    callback(metrics)
            except Exception as e:
                logger.error(
                    "convergence_callback_error",
                    callback=callback.__name__,
                    error=str(e),
                )
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get controller status summary.
        
        Returns:
            Status dictionary
        """
        return {
            "config": {
                "strategy": self.config.strategy.value,
                "initial_rate": self.config.initial_rate,
                "min_rate": self.config.min_rate,
                "max_rate": self.config.max_rate,
                "validation_required": self.config.validation_required,
            },
            "total_agents": len(self._agent_states),
            "total_adaptations": len(self._adaptation_events),
            "converged_agents": sum(
                1 for m in self._convergence_metrics.values() if m.is_converged
            ),
        }


class LearningRateOptimizer:
    """
    Optimizer for finding optimal learning rates across the swarm.
    
    This class provides optimization capabilities for finding the best
    learning rates based on swarm-wide performance metrics.
    """
    
    def __init__(self, controller: AdaptiveLearningRateController):
        """
        Initialize learning rate optimizer.
        
        Args:
            controller: AdaptiveLearningRateController instance
        """
        self.controller = controller
        
        logger.info("learning_rate_optimizer_initialized")
    
    async def find_optimal_rate(
        self,
        agent_id: str,
        iterations: int = 100,
    ) -> float:
        """
        Find optimal learning rate for an agent through search.
        
        Args:
            agent_id: Agent identifier
            iterations: Number of iterations to search
            
        Returns:
            Optimal learning rate
        """
        state = self.controller.get_or_create_state(agent_id)
        
        # Binary search for optimal rate
        low = self.controller.config.min_rate
        high = self.controller.config.max_rate
        best_rate = state.current_rate
        best_performance = state.success_rate
        
        for _ in range(iterations):
            mid = (low + high) / 2
            
            # Simulate performance at this rate
            simulated_performance = await self._simulate_performance(
                agent_id,
                mid,
            )
            
            if simulated_performance > best_performance:
                best_performance = simulated_performance
                best_rate = mid
                low = mid
            else:
                high = mid
        
        return best_rate
    
    def recommend_swarm_rates(self) -> Dict[str, float]:
        """
        Recommend learning rates for all agents.
        
        Returns:
            Dictionary of agent IDs to recommended rates
        """
        recommendations = {}
        
        for agent_id, state in self.controller._agent_states.items():
            # Base recommendation on success rate and convergence
            metrics = self.controller.get_convergence_metrics(agent_id)
            
            if metrics.is_converged:
                # Converged agents get minimal rate
                recommendations[agent_id] = self.controller.config.min_rate
            elif state.success_rate > 0.8:
                # High performers get moderate rate
                recommendations[agent_id] = state.current_rate * 0.8
            elif state.success_rate < 0.3:
                # Low performers get reduced rate
                recommendations[agent_id] = state.current_rate * 0.5
            else:
                # Average performers get current rate
                recommendations[agent_id] = state.current_rate
        
        return recommendations
    
    async def _simulate_performance(
        self,
        agent_id: str,
        rate: float,
    ) -> float:
        """
        Simulate expected performance at a given learning rate.
        
        Args:
            agent_id: Agent identifier
            rate: Learning rate to simulate
            
        Returns:
            Expected performance score
        """
        state = self.controller.get_or_create_state(agent_id)
        
        # Simple simulation based on historical data
        base_performance = state.success_rate
        
        # Adjust based on rate
        if rate > 0.5:
            # High rates may cause instability
            return base_performance * 0.8
        elif rate < 0.01:
            # Very low rates may cause slow learning
            return base_performance * 0.9
        
        # Optimal range
        return base_performance * 1.1
