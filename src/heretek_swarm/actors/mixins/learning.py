"""
LearningMixin - Learning status and adaptation methods.

This mixin provides methods for tracking learning status,
adaptation progress, and performance metrics.

Methods:
    get_learning_status: Get current learning status
    record_learning_signal: Record a learning signal
    update_adaptation: Update adaptation metrics
    get_performance_metrics: Get performance metrics

Version: 1.44.0
"""

import asyncio
from datetime import datetime, timezone
from enum import Enum
from typing import Any

import structlog

logger = structlog.get_logger("LearningMixin")


class LearningState(str, Enum):
    """Learning state for an actor."""

    IDLE = "idle"
    LEARNING = "learning"
    ADAPTING = "adapting"
    CONVERGED = "converged"
    DIVERGENT = "divergent"


class LearningMixin:
    """
    Mixin providing learning status and adaptation methods.

    Actors with this mixin can track their learning progress,
    record learning signals, and report performance metrics.
    """

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Initialize learning state."""
        super().__init__(*args, **kwargs)
        self._learning_state: LearningState = LearningState.IDLE
        self._learning_signals: list[dict[str, Any]] = []
        self._adaptation_score: float = 0.5
        self._performance_history: list[float] = []
        self._convergence_threshold: float = 0.9
        self._divergence_threshold: float = 0.3
        self._learning_rate: float = 0.1
        self._total_updates: int = 0

    async def get_learning_status(self) -> dict[str, Any]:
        """
        Get current learning status.

        Returns:
            Current learning state and metrics
        """
        return {
            "state": self._learning_state.value,
            "adaptation_score": self._adaptation_score,
            "total_updates": self._total_updates,
            "signal_count": len(self._learning_signals),
            "performance_trend": self._get_performance_trend(),
            "convergence_status": self._get_convergence_status(),
            "agent_id": self.agent_id,
        }

    async def record_learning_signal(
        self,
        signal_type: str,
        magnitude: float,
        context: dict[str, Any] | None = None,
    ) -> str:
        """
        Record a learning signal.

        Args:
            signal_type: Type of signal (reward, penalty, etc.)
            magnitude: Signal magnitude (-1.0 to 1.0)
            context: Optional context for the signal

        Returns:
            signal_id: Unique identifier for the signal
        """
        signal_id = f"signal_{self.agent_id}_{len(self._learning_signals)}"

        signal = {
            "signal_id": signal_id,
            "signal_type": signal_type,
            "magnitude": magnitude,
            "context": context or {},
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        self._learning_signals.append(signal)
        self._total_updates += 1

        # Update adaptation score
        await self._update_adaptation_score(magnitude)

        logger.info(
            "learning_signal_recorded",
            signal_id=signal_id,
            signal_type=signal_type,
            magnitude=magnitude,
            agent_id=self.agent_id,
        )

        return signal_id

    async def _update_adaptation_score(self, signal_magnitude: float) -> None:
        """
        Update adaptation score based on signal.

        Args:
            signal_magnitude: Magnitude of the learning signal
        """
        # Update state based on adaptation score
        if self._adaptation_score >= self._convergence_threshold:
            self._learning_state = LearningState.CONVERGED
        elif self._adaptation_score <= self._divergence_threshold:
            self._learning_state = LearningState.DIVERGENT
        elif self._learning_state == LearningState.IDLE:
            self._learning_state = LearningState.LEARNING

        logger.debug(
            "adaptation_score_updated",
            old_score=self._adaptation_score,
            signal_magnitude=signal_magnitude,
            new_state=self._learning_state.value,
            agent_id=self.agent_id,
        )

    async def update_adaptation(
        self,
        performance_delta: float,
        learning_rate: float | None = None,
    ) -> dict[str, Any]:
        """
        Update adaptation metrics based on performance.

        Args:
            performance_delta: Change in performance (-1.0 to 1.0)
            learning_rate: Optional custom learning rate

        Returns:
            Updated adaptation metrics
        """
        rate = learning_rate or self._learning_rate

        # Update adaptation score with exponential moving average
        old_score = self._adaptation_score
        self._adaptation_score = (
            (1 - rate) * self._adaptation_score +
            rate * (0.5 + performance_delta * 0.5)
        )
        self._adaptation_score = max(0.0, min(1.0, self._adaptation_score))

        # Update performance history
        self._performance_history.append(self._adaptation_score)
        if len(self._performance_history) > 100:
            self._performance_history = self._performance_history[-100:]

        # Update state
        if self._learning_state not in (LearningState.CONVERGED, LearningState.DIVERGENT):
            self._learning_state = LearningState.ADAPTING

        result = {
            "old_score": old_score,
            "new_score": self._adaptation_score,
            "delta": self._adaptation_score - old_score,
            "state": self._learning_state.value,
            "agent_id": self.agent_id,
        }

        logger.debug(
            "adaptation_updated",
            **result,
        )

        return result

    def _get_performance_trend(self) -> str:
        """
        Calculate performance trend.

        Returns:
            Trend direction: "improving", "stable", "declining"
        """
        if len(self._performance_history) < 5:
            return "insufficient_data"

        recent = self._performance_history[-5:]
        first = sum(recent[:2]) / 2
        last = sum(recent[-2:]) / 2

        if last > first + 0.05:
            return "improving"
        elif last < first - 0.05:
            return "declining"
        else:
            return "stable"

    def _get_convergence_status(self) -> str:
        """
        Get convergence status.

        Returns:
            Convergence status: "converged", "converging", "diverging", "unknown"
        """
        if self._learning_state == LearningState.CONVERGED:
            return "converged"
        elif self._learning_state == LearningState.DIVERGENT:
            return "diverging"
        elif len(self._performance_history) >= 10:
            # Check if recent performance is stable
            recent = self._performance_history[-10:]
            variance = sum((x - sum(recent)/len(recent))**2 for x in recent) / len(recent)
            if variance < 0.01:
                return "converging"
        return "unknown"

    async def get_performance_metrics(self) -> dict[str, Any]:
        """
        Get comprehensive performance metrics.

        Returns:
            Performance metrics and statistics
        """
        return {
            "adaptation_score": self._adaptation_score,
            "total_updates": self._total_updates,
            "learning_rate": self._learning_rate,
            "signal_count": len(self._learning_signals),
            "performance_trend": self._get_performance_trend(),
            "convergence_status": self._get_convergence_status(),
            "history_length": len(self._performance_history),
            "avg_recent_performance": (
                sum(self._performance_history[-10:]) / min(10, len(self._performance_history))
                if self._performance_history else 0.0
            ),
            "state": self._learning_state.value,
            "agent_id": self.agent_id,
        }

    def reset_learning(self) -> None:
        """Reset learning state to initial values."""
        self._learning_state = LearningState.IDLE
        self._adaptation_score = 0.5
        self._performance_history.clear()
        self._total_updates = 0
        logger.info("learning_reset", agent_id=self.agent_id)

    @property
    def is_converged(self) -> bool:
        """Check if learning has converged."""
        return self._learning_state == LearningState.CONVERGED

    @property
    def is_learning(self) -> bool:
        """Check if currently learning."""
        return self._learning_state in (LearningState.LEARNING, LearningState.ADAPTING)
