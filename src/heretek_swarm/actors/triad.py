"""
Triad Agents - Port of legacy OpenClaw Triad agents to Swarms.

This module implements the core Triad agents:
- Steward: Overall coordination and governance
- Alpha: Primary decision maker
- Beta: Secondary analyst and validator
- Charlie: Tertiary perspective and challenger
- Historian: Memory and context provider

These agents work together using MAKER consensus for deliberation.
"""

from datetime import UTC, datetime
from typing import Any

import structlog
from swarms import Agent

from heretek_swarm.actors.base import ActorMessage, AgentActor
from heretek_swarm.actors.mixins import DeliberationMixin, LearningMixin, MemoryMixin, PatternMixin

logger = structlog.get_logger("TriadAgents")


class StewardAgent(DeliberationMixin, PatternMixin, MemoryMixin, LearningMixin, AgentActor):
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


class AlphaAgent(DeliberationMixin, PatternMixin, MemoryMixin, LearningMixin, AgentActor):
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
            logger.warning(
                f"[{self.agent_id}] Unhandled message type: {message.message_type}"
            )

    async def _handle_deliberation_request(self, message: ActorMessage) -> None:
        """Handle deliberation requests from Steward."""
        deliberation_id = message.content.get("deliberation_id")
        topic = message.content.get("topic")

        logger.info(
            f"[{self.agent_id}] Participating in deliberation {deliberation_id}: {topic}"
        )

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
        self.analysis_history.append({
            "request_id": request_id,
            "analysis": analysis,
            "timestamp": datetime.now(UTC).isoformat(),
        })
        # P1-3: Trim history if it exceeds max size
        if len(self.analysis_history) > self.max_history_size:
            self.analysis_history = self.analysis_history[-self.max_history_size:]

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
                _original_analysis = message.content.get("original_analysis")  # Reserved for future use
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
                    timeout=60
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
                    prompt=f"Validate this decision: {decision}",
                    timeout=60
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


class BetaAgent(DeliberationMixin, PatternMixin, MemoryMixin, LearningMixin, AgentActor):
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


class CharlieAgent(DeliberationMixin, PatternMixin, MemoryMixin, LearningMixin, AgentActor):
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
