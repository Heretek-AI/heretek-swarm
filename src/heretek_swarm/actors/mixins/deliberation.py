"""
DeliberationMixin - Shared deliberation methods for actors.

This mixin provides methods for participating in deliberation and consensus
processes, extracting common functionality from actor classes.

Methods:
    _submit_deliberation_position: Submit a position to the deliberation
    _finalize_deliberation: Finalize deliberation participation
    _initiate_deliberation: Initiate a new deliberation
    _get_deliberation_status: Get current deliberation status

Version: 1.44.0
"""

import asyncio
from typing import TYPE_CHECKING, Any

import structlog

if TYPE_CHECKING:
    from heretek_swarm.consensus.maker import MakerConsensus

logger = structlog.get_logger("DeliberationMixin")


class DeliberationMixin:
    """
    Mixin providing deliberation and consensus participation methods.

    Actors with this mixin can participate in deliberation processes,
    submit positions, and finalize their participation in consensus.
    """

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Initialize deliberation state."""
        super().__init__(*args, **kwargs)
        self._deliberation_active: bool = False
        self._deliberation_id: str | None = None
        self._deliberation_position: dict[str, Any] | None = None
        self._consensus: "MakerConsensus | None" = None

    async def _initiate_deliberation(
        self,
        topic: str,
        options: list[str] | None = None,
        timeout: float = 60.0,
    ) -> str:
        """
        Initiate a new deliberation.

        Args:
            topic: The deliberation topic
            options: Optional list of decision options
            timeout: Maximum deliberation duration in seconds

        Returns:
            deliberation_id: Unique identifier for the deliberation
        """
        deliberation_id = f"delib_{self.agent_id}_{asyncio.get_event_loop().time():.0f}"
        self._deliberation_id = deliberation_id
        self._deliberation_active = True

        logger.info(
            "deliberation_initiated",
            deliberation_id=deliberation_id,
            topic=topic,
            agent_id=self.agent_id,
        )

        return deliberation_id

    async def _submit_deliberation_position(
        self,
        deliberation_id: str,
        position: dict[str, Any],
        rationale: str | None = None,
    ) -> bool:
        """
        Submit a position to a deliberation.

        Args:
            deliberation_id: The deliberation to submit to
            position: The position/stance being submitted
            rationale: Optional explanation for the position

        Returns:
            True if submission was successful
        """
        if deliberation_id != self._deliberation_id:
            logger.warning(
                "deliberation_mismatch",
                expected=self._deliberation_id,
                received=deliberation_id,
            )
            return False

        self._deliberation_position = {
            "position": position,
            "rationale": rationale,
            "submitted_at": asyncio.get_event_loop().time(),
        }

        logger.info(
            "deliberation_position_submitted",
            deliberation_id=deliberation_id,
            agent_id=self.agent_id,
            rationale=rationale,
        )

        return True

    async def _finalize_deliberation(
        self,
        deliberation_id: str,
        outcome: str | None = None,
    ) -> dict[str, Any]:
        """
        Finalize participation in a deliberation.

        Args:
            deliberation_id: The deliberation to finalize
            outcome: Optional outcome if known

        Returns:
            Finalization result with summary
        """
        if deliberation_id != self._deliberation_id:
            logger.warning(
                "deliberation_finalize_mismatch",
                expected=self._deliberation_id,
                received=deliberation_id,
            )
            return {"success": False, "error": "deliberation_id mismatch"}

        result = {
            "success": True,
            "deliberation_id": deliberation_id,
            "agent_id": self.agent_id,
            "position": self._deliberation_position,
            "outcome": outcome,
        }

        self._deliberation_active = False
        self._deliberation_id = None
        self._deliberation_position = None

        logger.info(
            "deliberation_finalized",
            deliberation_id=deliberation_id,
            agent_id=self.agent_id,
            outcome=outcome,
        )

        return result

    def _get_deliberation_status(self) -> dict[str, Any]:
        """
        Get current deliberation status.

        Returns:
            Status information about active deliberation
        """
        return {
            "active": self._deliberation_active,
            "deliberation_id": self._deliberation_id,
            "position_submitted": self._deliberation_position is not None,
            "agent_id": self.agent_id,
        }

    @property
    def is_deliberating(self) -> bool:
        """Check if agent is currently in a deliberation."""
        return self._deliberation_active
