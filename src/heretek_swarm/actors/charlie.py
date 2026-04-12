"""
Charlie Agent - Tertiary perspective and challenger.

The Charlie provides critical challenge to the Triad:
- Devil's advocate perspective
- Edge case identification
- Risk assessment
- Creative alternative solutions

This module was refactored from triad.py to use mixins.
"""

from datetime import UTC, datetime
from typing import Any

import structlog
from swarms import Agent

from heretek_swarm.actors.base import ActorMessage, AgentActor
from heretek_swarm.actors.mixins import LearningMixin

logger = structlog.get_logger("CharlieAgent")


class CharlieAgent(LearningMixin, AgentActor):
    """
    Charlie Agent - Tertiary perspective and challenger.

    The Charlie provides critical challenge to the Triad:
    - Devil's advocate perspective
    - Edge case identification
    - Risk assessment
    - Creative alternative solutions
    """

    def __init__(
        self,
        agent_id: str = "charlie",
        name: str = "Charlie",
        description: str = "Tertiary perspective and challenger",
        swarms_agent: Agent | None = None,
        challenge_intensity: str = "moderate",
        **kwargs,
    ) -> None:
        """
        Initialize the Charlie agent.

        Args:
            agent_id: Unique identifier
            name: Human-readable name
            description: Agent description
            swarms_agent: Optional Swarms Agent for LLM capabilities
            challenge_intensity: Challenge intensity (low, moderate, high)
            **kwargs: Additional arguments
        """
        super().__init__(
            agent_id=agent_id,
            name=name,
            description=description,
            topics=["triad", "challenge", "risk", "charlie"],
            capabilities=[
                "devil-advocate",
                "risk-assessment",
                "edge-case-analysis",
                "creative-solutions",
            ],
            swarms_agent=swarms_agent,
            **kwargs,
        )

        self.challenge_intensity = challenge_intensity
        self.max_history_size = 1000  # P1-3: Limit history size to prevent memory leaks
        self.challenges_raised: list[dict[str, Any]] = []
        self.risk_assessments: list[dict[str, Any]] = []
        # Dict-based tracking keyed by session/request id for test assertions
        self._challenges: dict[str, Any] = {}
        self._risk_assessments: dict[str, Any] = {}

        logger.info(f"[{self.agent_id}] Charlie agent initialized")

    async def initialize(self) -> None:
        """Initialize the Charlie agent."""
        self.register_handler("deliberation_request", self._handle_deliberation_request)
        self.register_handler("challenge_request", self._handle_challenge_request)
        self.register_handler("risk_assessment", self._handle_risk_assessment)

        logger.info(f"[{self.agent_id}] Charlie initialization complete")

    async def process_message(self, message: ActorMessage) -> None:
        """Process incoming messages."""
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

    async def _handle_deliberation_request(self, message: ActorMessage) -> None:
        """Handle deliberation requests."""
        deliberation_id = message.content.get("deliberation_id")
        session_id = message.content.get("session_id", deliberation_id)
        topic = message.content.get("topic") or message.content.get("problem")

        logger.info(
            f"[{self.agent_id}] Participating in deliberation {session_id}"
        )

        # Perform challenging analysis
        analysis = await self._perform_analysis(topic or "")

        # Store result keyed by session_id
        if session_id:
            self._challenges[session_id] = {
                "session_id": session_id,
                "analysis": analysis,
                "challenges": analysis.get("challenges", []),
            }

        await self.send(
            topic="triad",
            content={
                "message_type": "vote_response",
                "deliberation_id": session_id,
                "agent_id": self.agent_id,
                "decision": analysis["decision"],
                "confidence": analysis["confidence"],
                "reasoning": analysis["reasoning"],
                "challenges": analysis.get("challenges", []),
            },
        )

    async def _handle_challenge_request(self, message: ActorMessage) -> None:
        """Handle challenge requests."""
        request_id = message.content.get("request_id") or str(len(self._challenges))
        proposition = message.content.get("proposition")

        logger.info(f"[{self.agent_id}] Challenging: {request_id}")

        challenges = await self._generate_challenges(proposition)

        # P2-1 fix: Use timezone-aware datetime
        challenge_entry = {
            "proposition": proposition,
            "challenges": challenges,
            "timestamp": datetime.now(UTC).isoformat(),
        }
        self.challenges_raised.append(challenge_entry)
        self._challenges[request_id] = challenge_entry
        # P1-3: Trim history if it exceeds max size
        if len(self.challenges_raised) > self.max_history_size:
            self.challenges_raised = self.challenges_raised[-self.max_history_size:]

        reply_topic = message.content.get("reply_to", "challenges")
        await self.send(
            topic=reply_topic,
            content={
                "message_type": "challenge_response",
                "request_id": request_id,
                "challenges": challenges,
                "challenge_count": len(challenges),
            },
            correlation_id=message.correlation_id,
        )

    async def _handle_risk_assessment(self, message: ActorMessage) -> None:
        """Handle risk assessment requests."""
        request_id = message.content.get("request_id") or str(len(self._risk_assessments))
        scenario = message.content.get("scenario")

        logger.info(f"[{self.agent_id}] Assessing risks: {request_id}")

        assessment = await self._assess_risks(scenario)

        # P2-1 fix: Use timezone-aware datetime
        assessment_entry = {
            "scenario": scenario,
            "assessment": assessment,
            "timestamp": datetime.now(UTC).isoformat(),
        }
        self.risk_assessments.append(assessment_entry)
        self._risk_assessments[request_id] = assessment_entry
        # P1-3: Trim history if it exceeds max size
        if len(self.risk_assessments) > self.max_history_size:
            self.risk_assessments = self.risk_assessments[-self.max_history_size:]

        reply_topic = message.content.get("reply_to", "risks")
        await self.send(
            topic=reply_topic,
            content={
                "message_type": "risk_assessment_response",
                "request_id": request_id,
                **assessment,
            },
            correlation_id=message.correlation_id,
        )

    async def _perform_analysis(self, problem: str) -> dict[str, Any]:
        """Perform challenging analysis."""
        if self.swarms_agent:
            try:
                analysis_result = await self.run_with_llm(
                    prompt=f"Analyze with critical perspective (Charlie): {problem}. Identify risks and alternatives.",
                    timeout=60
                )
                return {
                    "decision": analysis_result,
                    "confidence": 0.75,
                    "reasoning": "Critical Charlie analysis",
                    "perspective": "challenger",
                    "challenges": ["Identified potential risks", "Proposed alternatives"],
                }
            except Exception as e:
                logger.error(f"[{self.agent_id}] Analysis error: {e}")

        return {
            "decision": "charlie_analysis_complete",
            "confidence": 0.7,
            "reasoning": "Fallback Charlie analysis",
            "perspective": "challenger",
            "challenges": [],
        }

    async def _generate_challenges(
        self,
        proposition: Any,
        alpha_findings: dict[str, Any] | None = None,
        beta_findings: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        """Generate challenges to a proposition."""
        challenges = []

        if self.swarms_agent:
            try:
                challenge_result = await self.run_with_llm(
                    prompt=f"Challenge this proposition: {proposition}",
                    timeout=60
                )
                challenges.append({
                    "type": "logical_challenge",
                    "description": challenge_result,
                    "severity": "medium",
                })
            except Exception as e:
                logger.error(f"[{self.agent_id}] Challenge error: {e}")

        return challenges

    async def _assess_risks(self, scenario: Any) -> dict[str, Any]:
        """Assess risks in a scenario."""
        if self.swarms_agent:
            try:
                risk_result = await self.run_with_llm(
                    prompt=f"Assess risks: {scenario}",
                    timeout=60
                )
                return {
                    "risks_identified": [risk_result],
                    "risk_level": "medium",
                    "mitigations": ["Standard mitigations"],
                }
            except Exception as e:
                logger.error(f"[{self.agent_id}] Risk assessment error: {e}")

        return {
            "risks_identified": [],
            "risks": [],
            "risk_level": "unknown",
            "mitigations": [],
        }

    def get_challenge_statistics(self) -> dict[str, Any]:
        """Get challenge statistics."""
        return {
            "total_challenges": len(self.challenges_raised) + len(self._challenges),
            "total_risk_assessments": len(self.risk_assessments) + len(self._risk_assessments),
            "challenge_intensity": self.challenge_intensity,
            "recent_challenges": self.challenges_raised[-5:],
        }
