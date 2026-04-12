"""
DeliberationMixin - Swarm deliberation consensus methods.

Provides methods for initiating, participating in, and finalizing
swarm deliberations for collective decision-making.
"""

from typing import Any

import structlog

from heretek_swarm.actors.base import AgentActor
from heretek_swarm.consensus.swarm_deliberation import (
    Position,
    SwarmDeliberationEngine,
)

logger = structlog.get_logger("DeliberationMixin")


class DeliberationMixin:
    """
    Mixin providing swarm deliberation consensus methods.

    Requires the host actor to have:
        - deliberation_engine: SwarmDeliberationEngine | None
        - access_analyzer: AccessPatternAnalyzer | None
        - _active_deliberations: dict[str, str]

    Methods:
        _initiate_deliberation: Start a new deliberation session
        _submit_deliberation_position: Submit an agent's position
        _finalize_deliberation: Complete and apply deliberation results
    """

    deliberation_engine: SwarmDeliberationEngine | None = None
    access_analyzer: Any = None
    _active_deliberations: dict[str, str] = None
    _deliberation_active: bool = False
    _deliberation_id: str | None = None
    _deliberation_position: Any | None = None

    @property
    def is_deliberating(self) -> bool:
        """Check if actor is currently in an active deliberation."""
        return self._deliberation_active

    def _get_deliberation_status(self) -> dict[str, Any]:
        """Get current deliberation status."""
        return {
            "active": self._deliberation_active,
            "deliberation_id": self._deliberation_id,
            "position": self._deliberation_position,
        }

    async def _initiate_deliberation(
        self,
        topic: str,
        options: list[str],
        participating_agents: list[str] | None = None,
        domain: str = "general",
    ) -> str | None:
        """
        Initiate swarm deliberation.

        Args:
            topic: Unique identifier for the deliberation subject
            options: List of options being deliberated
            participating_agents: List of agent IDs participating
            domain: Domain context for the deliberation

        Returns:
            deliberation_id if successful, None otherwise
        """
        deliberation_id = f"delib_{topic}"
        self._deliberation_active = True
        self._deliberation_id = deliberation_id
        self._deliberation_position = {"topic": topic, "options": options}

        if self.deliberation_engine:
            try:
                self.deliberation_engine.start_deliberation(
                    deliberation_id=deliberation_id,
                    proposal=str(options)[:200],
                    participants=participating_agents or [],
                    domain=domain,
                )
                self._active_deliberations[topic] = deliberation_id
            except Exception as e:
                logger.warning(
                    "deliberation_initiated_without_engine",
                    deliberation_id=deliberation_id,
                    topic=topic,
                    error=str(e),
                )
        else:
            # Standalone mode - just track locally
            if self._active_deliberations is None:
                self._active_deliberations = {}
            self._active_deliberations[topic] = deliberation_id

        return deliberation_id

    async def _submit_deliberation_position(
        self,
        deliberation_id: str,
        position: Any,
        rationale: str = "",
        agent_id: str | None = None,
    ) -> bool:
        """
        Submit agent position in an active deliberation.

        Args:
            deliberation_id: The deliberation identifier
            position: The position being submitted
            rationale: Supporting argument for the position
            agent_id: ID of the agent submitting position

        Returns:
            True if submission succeeded
        """
        # Check if this deliberation is active
        if not self._deliberation_active or self._deliberation_id != deliberation_id:
            return False

        self._deliberation_position = {
            "position": position,
            "rationale": rationale,
        }

        if self.deliberation_engine and agent_id:
            try:
                self.deliberation_engine.submit_position(
                    deliberation_id=deliberation_id,
                    agent_id=agent_id,
                    position=position,
                    confidence=0.9,
                    argument=rationale,
                )
            except Exception as e:
                logger.warning(
                    "deliberation_submit_without_engine",
                    deliberation_id=deliberation_id,
                    error=str(e),
                )

        return True

    async def _finalize_deliberation(self, deliberation_id: str) -> dict[str, Any]:
        """
        Finalize deliberation and apply results.

        Args:
            deliberation_id: The deliberation identifier

        Returns:
            Deliberation result dict
        """
        self._deliberation_active = False
        result = {
            "success": True,
            "deliberation_id": deliberation_id,
            "position": self._deliberation_position,
        }
        self._deliberation_id = None
        self._deliberation_position = None

        if self.deliberation_engine:
            try:
                engine_result = self.deliberation_engine.finalize_deliberation(deliberation_id)
                if engine_result:
                    self.deliberation_engine.cleanup_deliberation(deliberation_id)
                    result["engine_result"] = engine_result
            except Exception as e:
                logger.warning(
                    "deliberation_finalize_without_engine",
                    deliberation_id=deliberation_id,
                    error=str(e),
                )

        return result
