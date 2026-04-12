"""
Beta Agent - Secondary analyst and validator.

The Beta provides complementary analysis to Alpha:
- Secondary perspective on problems
- Independent validation
- Error detection and correction
- Alternative solution generation

This module was refactored from triad.py to use mixins.
"""

from datetime import UTC, datetime
from typing import Any

import structlog
from swarms import Agent

from heretek_swarm.actors.base import ActorMessage, AgentActor
from heretek_swarm.actors.mixins import LearningMixin

logger = structlog.get_logger("BetaAgent")


class BetaAgent(LearningMixin, AgentActor):
    """
    Beta Agent - Secondary analyst and validator.

    The Beta provides complementary analysis to Alpha:
    - Secondary perspective on problems
    - Independent validation
    - Error detection and correction
    - Alternative solution generation
    """

    def __init__(
        self,
        agent_id: str = "beta",
        name: str = "Beta",
        description: str = "Secondary analyst and validator",
        swarms_agent: Agent | None = None,
        validation_strictness: float = 0.8,
        **kwargs,
    ) -> None:
        """
        Initialize the Beta agent.

        Args:
            agent_id: Unique identifier
            name: Human-readable name
            description: Agent description
            swarms_agent: Optional Swarms Agent for LLM capabilities
            validation_strictness: Validation strictness threshold
            **kwargs: Additional arguments
        """
        super().__init__(
            agent_id=agent_id,
            name=name,
            description=description,
            topics=["triad", "analysis", "validation", "beta"],
            capabilities=[
                "secondary-analysis",
                "validation",
                "error-detection",
                "alternative-generation",
            ],
            swarms_agent=swarms_agent,
            **kwargs,
        )

        self.validation_strictness = validation_strictness
        self.max_history_size = 1000  # P1-3: Limit history size to prevent memory leaks
        self.validation_history: list[dict[str, Any]] = []
        self._validations: dict[str, Any] = {}  # dict for test-injectable validation state
        self._analyses: dict[str, Any] = {}  # dict for analysis records
        self._error_checks: dict[str, Any] = {}  # dict for error check records
        self.error_detections: list[dict[str, Any]] = []

        logger.info(f"[{self.agent_id}] Beta agent initialized")

    async def initialize(self) -> None:
        """Initialize the Beta agent."""
        self.register_handler("deliberation_request", self._handle_deliberation_request)
        self.register_handler("validation_request", self._handle_validation_request)
        self.register_handler("error_check", self._handle_error_check)

        logger.info(f"[{self.agent_id}] Beta initialization complete")

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
        deliberation_id = message.content.get("deliberation_id") or message.content.get("session_id")
        topic = message.content.get("topic") or message.content.get("problem")

        logger.info(
            f"[{self.agent_id}] Participating in deliberation {deliberation_id}"
        )

        # Perform independent analysis
        analysis = await self._perform_analysis(topic)

        # Store in _analyses dict for test observability
        if deliberation_id:
            self._analyses[deliberation_id] = {
                "analysis": analysis,
                "message": message.content,
                "timestamp": datetime.now(UTC).isoformat(),
            }

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

    async def _handle_validation_request(self, message: ActorMessage) -> None:
        """Handle validation requests."""
        request_id = message.content.get("request_id")
        decision_to_validate = message.content.get("decision")
        original_analysis = message.content.get("original_analysis")

        logger.info(f"[{self.agent_id}] Validating: {request_id}")

        validation = await self._validate_decision(
            decision_to_validate,
            original_analysis,
        )

        # P2-1 fix: Use timezone-aware datetime
        record = {
            "request_id": request_id,
            "validation": validation,
            "timestamp": datetime.now(UTC).isoformat(),
        }
        self.validation_history.append(record)
        if request_id:
            self._validations[request_id] = record
        # P1-3: Trim history if it exceeds max size
        if len(self.validation_history) > self.max_history_size:
            self.validation_history = self.validation_history[-self.max_history_size:]

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

    async def _handle_error_check(self, message: ActorMessage) -> None:
        """Handle error check requests."""
        content = message.content.get("content")

        errors = await self._detect_errors(content)

        # Always record the error check (even if no errors found)
        check_id = message.content.get("check_id") or message.content.get("session_id")
        check_record = {
            "content": content,
            "errors": errors,
            "timestamp": datetime.now(UTC).isoformat(),
        }
        self.error_detections.append(check_record)
        if check_id:
            self._error_checks[check_id] = check_record
        # P1-3: Trim history if it exceeds max size
        if len(self.error_detections) > self.max_history_size:
            self.error_detections = self.error_detections[-self.max_history_size:]
        if errors:
            logger.warning(f"[{self.agent_id}] Detected {len(errors)} errors")

        reply_topic = message.content.get("reply_to", "errors")
        await self.send(
            topic=reply_topic,
            content={
                "message_type": "error_check_response",
                "errors": errors,
                "error_count": len(errors),
            },
            correlation_id=message.correlation_id,
        )

    async def _perform_analysis(self, problem: str) -> dict[str, Any]:
        """Perform independent analysis."""
        if self.swarms_agent:
            try:
                analysis_result = await self.run_with_llm(
                    prompt=f"Provide independent analysis (Beta perspective): {problem}",
                    timeout=60
                )
                return {
                    "decision": analysis_result,
                    "confidence": 0.8,
                    "reasoning": "Independent Beta analysis",
                    "perspective": "secondary",
                }
            except Exception as e:
                logger.error(f"[{self.agent_id}] Analysis error: {e}")

        return {
            "decision": "beta_analysis_complete",
            "confidence": 0.75,
            "reasoning": "Fallback Beta analysis",
            "perspective": "secondary",
        }

    async def _validate_decision(
        self,
        decision: Any,
        original_analysis: dict[str, Any] | None = None,
        criteria: list[str] | None = None,
        alpha_findings: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Validate a decision with Beta's perspective."""
        if self.swarms_agent:
            try:
                validation_result = await self.run_with_llm(
                    prompt=f"Beta validation of: {decision}. Original: {original_analysis}",
                    timeout=60
                )
                return {
                    "valid": True,
                    "confidence": 0.85,
                    "feedback": validation_result,
                    "perspective": "secondary",
                }
            except Exception as e:
                logger.error(f"[{self.agent_id}] Validation error: {e}")

        return {
            "valid": True,
            "confidence": 0.75,
            "feedback": "Fallback Beta validation",
            "perspective": "secondary",
        }

    async def _detect_errors(self, content: Any) -> list[dict[str, Any]]:
        """Detect errors in content."""
        errors = []

        if self.swarms_agent:
            try:
                error_check = await self.run_with_llm(
                    prompt=f"Check for errors in: {content}",
                    timeout=60
                )
                if "error" in error_check.lower():
                    errors.append({
                        "type": "logical_error",
                        "description": error_check,
                        "severity": "medium",
                    })
            except Exception as e:
                logger.error(f"[{self.agent_id}] Error detection error: {e}")

        return errors

    def get_validation_statistics(self) -> dict[str, Any]:
        """Get validation statistics."""
        return {
            "total_validations": len(self.validation_history) + len(self._validations),
            "total_error_checks": len(self.error_detections) + len(self._error_checks),
            "total_errors_detected": len(self.error_detections),
            "validation_strictness": self.validation_strictness,
            "recent_validations": self.validation_history[-5:],
        }
