"""
Steward Agent - Overall coordination and governance.

This module implements the Steward agent extracted from triad.py.
The Steward is the primary coordinator for the Triad, responsible for:
- Initiating deliberation processes
- Coordinating between Triad members
- Making final executive decisions
- Managing system governance and policy
- Overseeing resource allocation
"""

from datetime import UTC, datetime
from typing import Any

import structlog
from swarms import Agent

from heretek_swarm.actors.base import ActorMessage, AgentActor
from heretek_swarm.actors.mixins import (
    DeliberationMixin,
    LearningMixin,
    MemoryMixin,
    PatternMixin,
)

logger = structlog.get_logger("StewardAgent")


class StewardAgent(
    DeliberationMixin,
    PatternMixin,
    MemoryMixin,
    LearningMixin,
    AgentActor,
):
    """
    Steward Agent - Overall coordination and governance.

    The Steward is the primary coordinator for the Triad, responsible for:
    - Initiating deliberation processes
    - Coordinating between Triad members
    - Making final executive decisions
    - Managing system governance and policy
    - Overseeing resource allocation
    """

    def __init__(
        self,
        agent_id: str = "steward",
        name: str = "Steward",
        description: str = "Triad coordinator and governance agent",
        swarms_agent: Agent | None = None,
        **kwargs,
    ) -> None:
        """
        Initialize the Steward agent.

        Args:
            agent_id: Unique identifier
            name: Human-readable name
            description: Agent description
            swarms_agent: Optional Swarms Agent for LLM capabilities
            **kwargs: Additional arguments
        """
        super().__init__(
            agent_id=agent_id,
            name=name,
            description=description,
            topics=["triad", "coordination", "governance", "decisions"],
            capabilities=[
                "coordination",
                "governance",
                "decision-making",
                "resource-management",
            ],
            swarms_agent=swarms_agent,
            **kwargs,
        )

        # Steward-specific state
        self.active_deliberations: dict[str, dict[str, Any]] = {}
        self._deliberations = self.active_deliberations  # alias for test compatibility
        self.governance_policies: dict[str, Any] = {}
        self._policies = self.governance_policies  # alias for test compatibility
        self.resource_allocations: dict[str, float] = {}

        # Initialize mixin-required state
        self._pattern_emitted: set[str] = set()
        self._active_deliberations: dict[str, str] = {}

        logger.info(f"[{self.agent_id}] Steward agent initialized")

    async def initialize(self) -> None:
        """Initialize the Steward agent."""
        # Register message handlers
        self.register_handler("start_deliberation", self._handle_start_deliberation)
        self.register_handler("request_decision", self._handle_request_decision)
        self.register_handler("report_status", self._handle_report_status)
        self.register_handler("policy_update", self._handle_policy_update)

        logger.info(f"[{self.agent_id}] Steward initialization complete")

    async def process_message(self, message: ActorMessage) -> None:
        """
        Process incoming messages.

        Args:
            message: Actor message to process
        """
        handler = self._message_handlers.get(message.message_type)
        if handler:
            try:
                await handler(message)
            except Exception as e:
                logger.error(
                    f"[{self.agent_id}] Error processing message {message.message_type}: {e}",
                    exc_info=True,
                )
                self.error_count += 1
                # Send error response if reply_to is specified
                if message.content.get("reply_to"):
                    await self.send(
                        topic=message.content["reply_to"],
                        content={
                            "message_type": "error_response",
                            "error": str(e),
                            "original_message_type": message.message_type,
                        },
                        correlation_id=message.correlation_id,
                    )
        else:
            logger.warning(
                f"[{self.agent_id}] Unhandled message type: {message.message_type}"
            )

    async def _handle_start_deliberation(self, message: ActorMessage) -> None:
        """Handle deliberation start requests with validation."""
        # P2-7 fix: Validate input before processing
        try:
            validated = self._validate_message_content("start_deliberation", message.content)
            if validated:
                deliberation_id = validated.deliberation_id
                topic = validated.topic
                triad_members = validated.triad_members
            else:
                # Fallback to unvalidated access
                # Support both deliberation_id/topic and session_id/problem field names
                deliberation_id = message.content.get("deliberation_id") or message.content.get("session_id")
                topic = message.content.get("topic") or message.content.get("problem")
                triad_members = message.content.get("triad_members", [])

                if not deliberation_id or not topic:
                    # Auto-generate if missing
                    deliberation_id = deliberation_id or f"del_{datetime.now(UTC).strftime('%Y%m%d_%H%M%S')}"
                    topic = topic or "unspecified"
        except (ValueError, Exception) as e:
            logger.warning(f"[{self.agent_id}] Deliberation validation issue, using fallback: {e}")
            # Fallback: support both deliberation_id/topic and session_id/problem field names
            deliberation_id = message.content.get("deliberation_id") or message.content.get("session_id") or f"del_{datetime.now(UTC).strftime('%Y%m%d_%H%M%S')}"
            topic = message.content.get("topic") or message.content.get("problem") or "unspecified"
            triad_members = message.content.get("triad_members", [])

        # Initialize deliberation
        # P2-1 fix: Use timezone-aware datetime
        self.active_deliberations[deliberation_id] = {
            "topic": topic,
            "triad_members": triad_members,
            "status": "initiated",
            "started_at": datetime.now(UTC).isoformat(),
            "votes": {},
        }

        logger.info(
            f"[{self.agent_id}] Started deliberation {deliberation_id} on topic: {topic}"
        )

        # Notify triad members
        for member_id in triad_members:
            await self.send_to_actor(
                target_actor_id=member_id,
                message_type="deliberation_request",
                content={
                    "deliberation_id": deliberation_id,
                    "topic": topic,
                    "steward_id": self.agent_id,
                },
            )

    async def _handle_request_decision(self, message: ActorMessage) -> None:
        """Handle decision requests."""
        request_id = message.content.get("request_id")
        session_id = message.content.get("session_id")
        decision_context = message.content.get("context", {})

        # Advance deliberation phase when a triad member requests decision
        if session_id and session_id in self._deliberations:
            current_phase = self._deliberations[session_id].get("phase", "alpha")
            phase_progression = {"alpha": "beta", "beta": "charlie", "charlie": "complete"}
            next_phase = phase_progression.get(current_phase, current_phase)
            self._deliberations[session_id]["phase"] = next_phase
            logger.info(f"[{self.agent_id}] Deliberation {session_id} phase: {current_phase} -> {next_phase}")

        logger.info(
            f"[{self.agent_id}] Processing decision request: {request_id}"
        )

        # Make executive decision or delegate to triad
        if self.swarms_agent:
            try:
                decision = await self.run_with_llm(
                    prompt=f"Make an executive decision on: {decision_context}",
                    timeout=60
                )
                await self.send(
                    topic="decisions",
                    content={
                        "message_type": "decision_response",
                        "request_id": request_id,
                        "decision": decision,
                        "source": "steward",
                    },
                    correlation_id=message.correlation_id,
                )
            except Exception as e:
                logger.error(f"[{self.agent_id}] Decision error: {e}")
        else:
            # Fallback logic
            await self.send(
                topic="decisions",
                content={
                    "message_type": "decision_response",
                    "request_id": request_id,
                    "decision": "defer_to_triad",
                    "source": "steward",
                },
                correlation_id=message.correlation_id,
            )

    async def _handle_report_status(self, message: ActorMessage) -> None:
        """Handle status report requests - publish current status."""
        reporter_id = message.content.get("agent_id")
        requester = message.content.get("requester", message.sender)
        status = message.content.get("status", {})

        logger.debug(f"[{self.agent_id}] Status report from {reporter_id or requester}")

        # Update internal tracking
        if reporter_id:
            self.update_state(f"status:{reporter_id}", status)

        # Publish status back to requester
        await self.send(
            topic="status",
            content={
                "message_type": "status_response",
                "agent_id": self.agent_id,
                "state": self.state.value,
                "active_deliberations": len(self._deliberations),
                "policies_count": len(self._policies),
                "requester": requester,
            },
            correlation_id=message.correlation_id,
        )

    async def _handle_policy_update(self, message: ActorMessage) -> None:
        """Handle policy update requests."""
        policy_id = message.content.get("policy_id")
        policy_data = message.content.get("policy_data") or {
            k: v for k, v in message.content.items()
            if k not in ("policy_id", "reply_to")
        }

        if policy_id:
            # P2-1 fix: Use timezone-aware datetime
            self.governance_policies[policy_id] = {
                **policy_data,
                "updated_at": datetime.now(UTC).isoformat(),
                "updated_by": message.sender,
            }
            logger.info(f"[{self.agent_id}] Updated policy: {policy_id}")

    async def coordinate_triad(
        self,
        topic: str | None = None,
        triad_members: list[str] | None = None,
        problem: str | None = None,
        context: dict[str, Any] | None = None,
    ) -> str:
        """
        Coordinate a triad deliberation.

        Args:
            topic: Deliberation topic
            triad_members: List of triad member IDs
            problem: Alternative name for topic
            context: Additional context for deliberation

        Returns:
            Deliberation ID
        """
        # P2-1 fix: Use timezone-aware datetime
        deliberation_id = f"del_{datetime.now(UTC).strftime('%Y%m%d_%H%M%S')}"
        effective_topic = topic or problem

        await self.send(
            topic="triad",
            content={
                "message_type": "start_deliberation",
                "deliberation_id": deliberation_id,
                "topic": effective_topic,
                "triad_members": triad_members or [],
                "context": context or {},
            },
        )

        # Store deliberation for observability
        deliberation_record = {
            "session_id": deliberation_id,
            "topic": effective_topic,
            "phase": "initiated",
            "status": "pending",
            "timestamp": datetime.now(UTC).isoformat(),
        }
        self.active_deliberations[deliberation_id] = deliberation_record

        return deliberation_record

    def get_deliberation_status(self, deliberation_id: str) -> dict[str, Any] | None:
        """Get status of a deliberation."""
        return self.active_deliberations.get(deliberation_id)

    def get_all_deliberation_statuses(self) -> dict[str, dict[str, Any]]:
        """Get status of all active deliberations."""
        return dict(self.active_deliberations)

    def get_governance_policy(self, policy_id: str) -> dict[str, Any] | None:
        """Get a governance policy."""
        return self.governance_policies.get(policy_id)
