"""DeliberationMixin for consensus-based decision making."""
import asyncio
from typing import Any, Dict, Optional


class DeliberationMixin:
    """Mixin for consensus deliberation methods.

    Extracted from 21 actor files to remove ~735 lines of duplication.
    """

    _deliberation_active: bool = False
    _deliberation_id: Optional[str] = None
    _deliberation_position: Optional[Dict[str, Any]] = None

    @property
    def is_deliberating(self) -> bool:
        """Check if currently in deliberation."""
        return self._deliberation_active

    async def _initiate_deliberation(
        self,
        topic: str,
        options: list[str],
    ) -> str:
        """Initiate a new deliberation.
        
        Args:
            topic: The topic to deliberate
            options: List of options to choose from
            
        Returns:
            deliberation_id: Unique ID for this deliberation
        """
        self._deliberation_active = True
        self._deliberation_id = f"delib_{hash(topic) % 1000000}"
        self._deliberation_position = None
        return self._deliberation_id

    async def _submit_deliberation_position(
        self,
        position: Dict[str, Any],
        consensus_round: str,
        timeout: float = 30.0
    ) -> Optional[Dict[str, Any]]:
        """Submit position to consensus deliberation.

        Args:
            position: The position/proposal to submit
            consensus_round: Current consensus round identifier
            timeout: Timeout in seconds for deliberation

        Returns:
            Consensus result if reached, None if timeout
        """
        try:
            await self._publish_position(position, consensus_round)
            result = await asyncio.wait_for(
                self._wait_for_consensus(consensus_round),
                timeout=timeout
            )
            self._deliberation_position = position
            return result
        except asyncio.TimeoutError:
            self.logger.warning(
                f"Consensus timeout for round {consensus_round}",
                extra={"consensus_round": consensus_round}
            )
            return None
        except Exception as e:
            self.logger.error(
                f"Error submitting deliberation position: {e}",
                extra={"consensus_round": consensus_round}
            )
            return None

    async def _finalize_deliberation(
        self,
        consensus_result: Dict[str, Any],
        binding: bool = True
    ) -> Dict[str, Any]:
        """Finalize deliberation and apply consensus.

        Args:
            consensus_result: The consensus result from deliberation
            binding: Whether consensus is binding on this agent

        Returns:
            Finalized decision with metadata
        """
        finalized = {
            "decision": consensus_result.get("decision"),
            "confidence": consensus_result.get("confidence", 0.0),
            "participation_rate": consensus_result.get("participation_rate", 0.0),
            "binding": binding,
            "timestamp": asyncio.get_event_loop().time(),
            "success": True,
        }

        if binding:
            await self._apply_consensus_decision(finalized)

        await self._emit_pattern(
            pattern_type="consensus_decision",
            data=finalized
        )

        self._deliberation_active = False
        return finalized

    def _get_deliberation_status(self) -> Dict[str, Any]:
        """Get current deliberation status."""
        return {
            "active": self._deliberation_active,
            "deliberation_id": self._deliberation_id,
            "position": self._deliberation_position,
        }

    async def _publish_position(
        self,
        position: Dict[str, Any],
        consensus_round: str
    ) -> None:
        """Publish position to consensus channel."""
        if hasattr(self, '_consensus_publisher'):
            await self._consensus_publisher.publish(
                channel=f"consensus:{consensus_round}",
                message=position
            )

    async def _wait_for_consensus(
        self,
        consensus_round: str
    ) -> Dict[str, Any]:
        """Wait for consensus result."""
        if hasattr(self, '_consensus_subscriber'):
            return await self._consensus_subscriber.subscribe(
                channel=f"consensus:{consensus_round}"
            )
        return {"decision": None, "confidence": 0.0}

    async def _apply_consensus_decision(
        self,
        decision: Dict[str, Any]
    ) -> None:
        """Apply consensus decision to agent state."""
        if hasattr(self, 'state'):
            self.state["last_consensus_decision"] = decision
