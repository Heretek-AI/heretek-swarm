"""
Alpha Agent - Primary decision maker and analyst.

The Alpha is the primary analytical agent in the Triad:
- Provides first-pass analysis on problems
- Makes initial recommendations
- Leads consensus building
- Validates final decisions

This module was refactored from triad.py to use mixins.
"""

from datetime import UTC, datetime
from typing import Any

import structlog
from swarms import Agent

from heretek_swarm.actors.base import ActorMessage, AgentActor
from heretek_swarm.actors.mixins import HealthReportingMixin, LearningMixin, ValidationMixin

logger = structlog.get_logger("AlphaAgent")


class AlphaAgent(HealthReportingMixin, ValidationMixin, LearningMixin, AgentActor):
    """
    Alpha Agent - Primary decision maker and analyst.

    The Alpha is the primary analytical agent in the Triad:
    - Provides first-pass analysis on problems
    - Makes initial recommendations
    - Leads consensus building
    - Validates final decisions
    """

    def __init__(
        self,
        agent_id: str = "alpha",
        name: str = "Alpha",
        description: str = "Primary decision maker and analyst",
        swarms_agent: Agent | None = None,
        analysis_depth: str = "deep",
        **kwargs,
    ) -> None:
        """
        Initialize the Alpha agent.

        Args:
            agent_id: Unique identifier
            name: Human-readable name
            description: Agent description
            swarms_agent: Optional Swarms Agent for LLM capabilities
            analysis_depth: Analysis depth level (shallow, medium, deep)
            **kwargs: Additional arguments
        """
        super().__init__(
            agent_id=agent_id,
            name=name,
            description=description,
            topics=["triad", "analysis", "decisions", "alpha"],
            capabilities=[
                "primary-analysis",
                "decision-making",
                "consensus-building",
                "validation",
            ],
            swarms_agent=swarms_agent,
            **kwargs,
        )

        self.analysis_depth = analysis_depth
        self.max_history_size = 1000  # P1-3: Limit history size to prevent memory leaks
        self.analysis_history: list[dict[str, Any]] = []
        self.decision_count = 0

        logger.info(f"[{self.agent_id}] Alpha agent initialized")

    async def initialize(self) -> None:
        """Initialize the Alpha agent."""
        self.register_handler("deliberation_request", self._handle_deliberation_request)
        self.register_handler("analysis_request", self._handle_analysis_request)
        self.register_handler("validation_request", self._handle_validation_request)

        logger.info(f"[{self.agent_id}] Alpha initialization complete")

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
            logger.warning(f"[{self.agent_id}] Unhandled message type: {message.message_type}")

    async def _handle_deliberation_request(self, message: ActorMessage) -> None:
        """Handle deliberation requests from Steward."""
        deliberation_id = message.content.get("deliberation_id")
        topic = message.content.get("topic")

        logger.info(f"[{self.agent_id}] Participating in deliberation {deliberation_id}: {topic}")

        # Perform analysis
        analysis = await self._perform_analysis(topic)

        # Submit vote/analysis
        await self.send(
            topic="triad",
            content={
                "message_type": "vote_response",
                "deliberation_id": deliberation_id,
                "agent_id": self.agent_id,
                "decision": analysis["decision"],
                "confidence": analysis["confidence"],
                "reasoning": analysis["reasoning"],
            },
        )

        self.decision_count += 1

    async def _handle_analysis_request(self, message: ActorMessage) -> None:
        """Handle analysis requests with validation."""
        # P2-7 fix: Validate input before processing
        try:
            validated = self._validate_message_content("analysis_request", message.content)
            if validated:
                request_id = validated.request_id
                problem = validated.problem
            else:
                # Fallback to unvalidated access
                request_id = message.content.get("request_id")
                problem = message.content.get("problem")
        except ValueError as e:
            logger.error(f"[{self.agent_id}] Analysis validation failed: {e}")
            return

        logger.info(f"[{self.agent_id}] Analyzing: {request_id}")

        analysis = await self._perform_analysis(problem)

        reply_topic = message.content.get("reply_to", "analysis")
        await self.send(
            topic=reply_topic,
            content={
                "message_type": "analysis_response",
                "request_id": request_id,
                **analysis,
            },
            correlation_id=message.correlation_id,
        )

        # P2-1 fix: Use timezone-aware datetime
        self.analysis_history.append(
            {
                "request_id": request_id,
                "analysis": analysis,
                "timestamp": datetime.now(UTC).isoformat(),
            }
        )
        # P1-3: Trim history if it exceeds max size
        if len(self.analysis_history) > self.max_history_size:
            self.analysis_history = self.analysis_history[-self.max_history_size :]

    async def _handle_validation_request(self, message: ActorMessage) -> None:
        """Handle validation requests with validation."""
        # P2-7 fix: Validate input before processing
        try:
            validated = self._validate_message_content("validation_request", message.content)
            if validated:
                request_id = validated.request_id
                decision_to_validate = validated.decision
            else:
                # Fallback to unvalidated access
                request_id = message.content.get("request_id")
                decision_to_validate = message.content.get("decision")
                _original_analysis = message.content.get(
                    "original_analysis"
                )  # Reserved for future use
        except ValueError as e:
            logger.error(f"[{self.agent_id}] Validation request validation failed: {e}")
            return

        logger.info(f"[{self.agent_id}] Validating: {request_id}")

        validation = await self._validate_decision(decision_to_validate)

        reply_topic = message.content.get("reply_to", "validation")
        await self.send(
            topic=reply_topic,
            content={
                "message_type": "validation_response",
                "request_id": request_id,
                **validation,
            },
            correlation_id=message.correlation_id,
        )

    async def _perform_analysis(self, problem: str) -> dict[str, Any]:
        """
        Perform analysis on a problem.

        Args:
            problem: Problem description

        Returns:
            Analysis results with decision, confidence, and reasoning
        """
        if self.swarms_agent:
            try:
                analysis_result = await self.run_with_llm(
                    prompt=f"Analyze this problem and provide a decision with confidence: {problem}",
                    timeout=60,
                )
                return {
                    "decision": analysis_result,
                    "confidence": 0.85,
                    "reasoning": "LLM-based analysis",
                    "depth": self.analysis_depth,
                }
            except Exception as e:
                logger.error(f"[{self.agent_id}] Analysis error: {e}")

        # Fallback analysis
        return {
            "decision": "analysis_complete",
            "confidence": 0.7,
            "reasoning": "Fallback analysis",
            "depth": self.analysis_depth,
        }

    async def _validate_decision(self, decision: Any) -> dict[str, Any]:
        """
        Validate a decision.

        Args:
            decision: Decision to validate

        Returns:
            Validation results
        """
        if self.swarms_agent:
            try:
                validation_result = await self.run_with_llm(
                    prompt=f"Validate this decision: {decision}", timeout=60
                )
                return {
                    "valid": True,
                    "confidence": 0.8,
                    "feedback": validation_result,
                }
            except Exception as e:
                logger.error(f"[{self.agent_id}] Validation error: {e}")

        return {
            "valid": True,
            "confidence": 0.7,
            "feedback": "Fallback validation",
        }

    def get_analysis_statistics(self) -> dict[str, Any]:
        """Get analysis statistics."""
        return {
            "total_analyses": len(self.analysis_history),
            "total_decisions": self.decision_count,
            "analysis_depth": self.analysis_depth,
            "recent_analyses": self.analysis_history[-5:],
        }
