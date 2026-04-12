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


class DeliberationMixin(AgentActor):
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

    async def _initiate_deliberation(
        self,
        item_id: str,
        proposal: str,
        participating_agents: list[str],
        domain: str = "general",
    ) -> str | None:
        """
        Initiate swarm deliberation.

        Args:
            item_id: Unique identifier for the deliberation subject
            proposal: The proposal being deliberated
            participating_agents: List of agent IDs participating
            domain: Domain context for the deliberation

        Returns:
            deliberation_id if successful, None otherwise
        """
        if not self.deliberation_engine:
            return None

        try:
            deliberation_id = f"delib_{item_id}"
            self.deliberation_engine.start_deliberation(
                deliberation_id=deliberation_id,
                proposal=proposal[:200],
                participants=participating_agents,
                domain=domain,
            )
            self._active_deliberations[item_id] = deliberation_id

            logger.info(
                "deliberation_initiated",
                deliberation_id=deliberation_id,
                item_id=item_id,
            )
            return deliberation_id
        except Exception as e:
            logger.error(
                "failed_to_initiate_deliberation",
                item_id=item_id,
                error=str(e),
            )
            return None

    async def _submit_deliberation_position(
        self,
        item_id: str,
        agent_id: str,
        position: Position,
        confidence: float,
        argument: str,
    ) -> bool:
        """
        Submit agent position in an active deliberation.

        Args:
            item_id: The deliberation item identifier
            agent_id: ID of the agent submitting position
            position: The position being submitted
            confidence: Confidence level (0-1)
            argument: Supporting argument for the position

        Returns:
            True if submission succeeded
        """
        if not self.deliberation_engine:
            return False

        deliberation_id = self._active_deliberations.get(item_id)
        if not deliberation_id:
            return False

        try:
            success = self.deliberation_engine.submit_position(
                deliberation_id=deliberation_id,
                agent_id=agent_id,
                position=position,
                confidence=confidence,
                argument=argument,
            )

            if success and self.access_analyzer:
                self.access_analyzer.record_access(
                    memory_id=f"delib_{deliberation_id}_{agent_id}",
                    access_type="write",
                    agent_id=agent_id,
                )

            return success
        except Exception as e:
            logger.error(
                "failed_to_submit_deliberation_position",
                error=str(e),
            )
            return False

    async def _finalize_deliberation(self, item_id: str) -> Any | None:
        """
        Finalize deliberation and apply results.

        Args:
            item_id: The deliberation item identifier

        Returns:
            Deliberation result if successful
        """
        if not self.deliberation_engine:
            return None

        deliberation_id = self._active_deliberations.get(item_id)
        if not deliberation_id:
            return None

        try:
            result = self.deliberation_engine.finalize_deliberation(deliberation_id)

            if result:
                self.deliberation_engine.cleanup_deliberation(deliberation_id)
                del self._active_deliberations[item_id]
                logger.info("deliberation_finalized", deliberation_id=deliberation_id)

            return result
        except Exception as e:
            logger.error(
                "failed_to_finalize_deliberation",
                error=str(e),
            )
            return None
