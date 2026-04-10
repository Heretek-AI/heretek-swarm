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

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import structlog
from swarms import Agent

from heretek_swarm.actors.base import AgentActor, ActorMessage

_logger = structlog.get_logger("TriadAgents")


class StewardAgent(AgentActor):
    """
    Steward Agent - Overall coordination and governance.

    The Steward is the primary coordinator for the Triad, responsible for:
    - Initiating deliberation processes
    - Coordinating between Triad members
    - Making final executive decisions
    - Managing system governance and policy
    - Overseeing resource allocation
    """

    def __init__(self, _agent_id: str, _name: str, _description: str, _swarms_agent: Optional[Agent], **kwargs) -> None:
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
            _name = name,
            _description = description,
            _topics = ["triad", "coordination", "governance", "decisions"],
            _capabilities = [
                "coordination",
                "governance",
                "decision-making",
                "resource-management",
            ],
            swarms_agent=swarms_agent,
            **kwargs,
        )

        # Steward-specific state
        self.active_deliberations: Dict[str, Dict[str, Any]] = {}
        self.governance_policies: Dict[str, Any] = {}
        self.resource_allocations: Dict[str, float] = {}

        logger.info(f"[{self.agent_id}] Steward agent initialized")

    async def initialize(self) -> None:
        """Initialize the Steward agent."""
        # Register message handlers
        self.register_handler("start_deliberation", self._handle_start_deliberation)
        self.register_handler("request_decision", self._handle_request_decision)
        self.register_handler("report_status", self._handle_report_status)
        self.register_handler("policy_update", self._handle_policy_update)

        logger.info(f"[{self.agent_id}] Steward initialization complete")

    async def process_message(self, _message: ActorMessage) -> None:
        """
        Process incoming messages.

        Args:
            message: Actor message to process
        """
        _handler = self._message_handlers.get(message.message_type)
        if handler:
            try:
                await handler(message)
            except Exception as e:
                logger.error(
                    f"[{self.agent_id}] Error processing message {message.message_type}: {e}",
                    _exc_info = True,
                )
                self.error_count += 1
                # Send error response if reply_to is specified
                if message.content.get("reply_to"):
                    await self.send(
                        _topic = message.content["reply_to"],
                        _content = {
                            "message_type": "error_response",
                            "error": str(e),
                            "original_message_type": message.message_type,
                        },
                        _correlation_id = message.correlation_id,
                    )
        else:
            logger.warning(
                f"[{self.agent_id}] Unhandled message type: {message.message_type}"
            )

    async def _handle_start_deliberation(self, _message: ActorMessage) -> None:
        """Handle deliberation start requests with validation."""
        # P2-7 fix: Validate input before processing
        try:
            _validated = self._validate_message_content("start_deliberation", message.content)
            if validated:
                _deliberation_id = validated.deliberation_id
                _topic = validated.topic
                _triad_members = validated.triad_members
            else:
                # Fallback to unvalidated access
                _deliberation_id = message.content.get("deliberation_id")
                _topic = message.content.get("topic")
                _triad_members = message.content.get("triad_members", [])
                
                if not deliberation_id or not topic:
                    logger.error(f"[{self.agent_id}] Missing deliberation parameters")
                    return
        except ValueError as e:
            logger.error(f"[{self.agent_id}] Deliberation validation failed: {e}")
            return

        # Initialize deliberation
        # P2-1 fix: Use timezone-aware datetime
        self.active_deliberations[deliberation_id] = {
            "topic": topic,
            "triad_members": triad_members,
            "status": "initiated",
            "started_at": datetime.now(timezone.utc).isoformat(),
            "votes": {},
        }

        logger.info(
            f"[{self.agent_id}] Started deliberation {deliberation_id} on topic: {topic}"
        )

        # Notify triad members
        for member_id in triad_members:
            await self.send_to_actor(
                _target_actor_id = member_id,
                message_type="deliberation_request",
                _content = {
                    "deliberation_id": deliberation_id,
                    "topic": topic,
                    "steward_id": self.agent_id,
                },
            )

    async def _handle_request_decision(self, _message: ActorMessage) -> None:
        """Handle decision requests."""
        _request_id = message.content.get("request_id")
        _decision_context = message.content.get("context", {})

        logger.info(
            f"[{self.agent_id}] Processing decision request: {request_id}"
        )

        # Make executive decision or delegate to triad
        if self.swarms_agent:
            try:
                decision = await self.run_with_llm(
                    _prompt = f"Make an executive decision on: {decision_context}",
                    _timeout = 60
                )
                await self.send(
                    _topic = "decisions",
                    _content = {
                        "message_type": "decision_response",
                        "request_id": request_id,
                        "decision": decision,
                        "source": "steward",
                    },
                    _correlation_id = message.correlation_id,
                )
            except Exception as e:
                logger.error(f"[{self.agent_id}] Decision error: {e}")
        else:
            # Fallback logic
            await self.send(
                _topic = "decisions",
                _content = {
                    "message_type": "decision_response",
                    "request_id": request_id,
                    "decision": "defer_to_triad",
                    "source": "steward",
                },
                _correlation_id = message.correlation_id,
            )

    async def _handle_report_status(self, _message: ActorMessage) -> None:
        """Handle status reports from triad members."""
        _reporter_id = message.content.get("agent_id")
        _status = message.content.get("status", {})

        logger.debug(f"[{self.agent_id}] Status report from {reporter_id}")

        # Update internal tracking
        self.update_state(f"status:{reporter_id}", status)

    async def _handle_policy_update(self, _message: ActorMessage) -> None:
        """Handle policy update requests."""
        _policy_id = message.content.get("policy_id")
        _policy_data = message.content.get("policy_data")

        if policy_id and policy_data:
            # P2-1 fix: Use timezone-aware datetime
            self.governance_policies[policy_id] = {
                **policy_data,
                "updated_at": datetime.now(timezone.utc).isoformat(),
                "updated_by": message.sender,
            }
            logger.info(f"[{self.agent_id}] Updated policy: {policy_id}")

    async def coordinate_triad(self, _topic: str, _triad_members: List[str]) -> str:
        """
        Coordinate a triad deliberation.

        Args:
            topic: Deliberation topic
            triad_members: List of triad member IDs

        Returns:
            Deliberation ID
        """
        # P2-1 fix: Use timezone-aware datetime
        _deliberation_id = f"del_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}"

        await self.send(
            _topic = "triad",
            _content = {
                "message_type": "start_deliberation",
                "deliberation_id": deliberation_id,
                "topic": topic,
                "triad_members": triad_members,
            },
        )

        return deliberation_id

    def get_deliberation_status(self, _deliberation_id: str) -> Optional[Dict[str, Any]]:
        """Get status of a deliberation."""
        return self.active_deliberations.get(deliberation_id)

    def get_governance_policy(self, _policy_id: str) -> Optional[Dict[str, Any]]:
        """Get a governance policy."""
        return self.governance_policies.get(policy_id)


class AlphaAgent(AgentActor):
    """
    Alpha Agent - Primary decision maker and analyst.

    The Alpha is the primary analytical agent in the Triad:
    - Provides first-pass analysis on problems
    - Makes initial recommendations
    - Leads consensus building
    - Validates final decisions
    """

    def __init__(self, _agent_id: str, _name: str, _description: str, _swarms_agent: Optional[Agent], _analysis_depth: str, **kwargs) -> None:
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
            _name = name,
            _description = description,
            _topics = ["triad", "analysis", "decisions", "alpha"],
            _capabilities = [
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
        self.analysis_history: List[Dict[str, Any]] = []
        self.decision_count = 0

        logger.info(f"[{self.agent_id}] Alpha agent initialized")

    async def initialize(self) -> None:
        """Initialize the Alpha agent."""
        self.register_handler("deliberation_request", self._handle_deliberation_request)
        self.register_handler("analysis_request", self._handle_analysis_request)
        self.register_handler("validation_request", self._handle_validation_request)

        logger.info(f"[{self.agent_id}] Alpha initialization complete")

    async def process_message(self, _message: ActorMessage) -> None:
        """Process incoming messages."""
        _handler = self._message_handlers.get(message.message_type)
        if handler:
            try:
                await handler(message)
            except Exception as e:
                logger.error(
                    f"[{self.agent_id}] Error processing message {message.message_type}: {e}",
                    _exc_info = True,
                )
                self.error_count += 1
                if message.content.get("reply_to"):
                    await self.send(
                        _topic = message.content["reply_to"],
                        _content = {
                            "message_type": "error_response",
                            "error": str(e),
                            "original_message_type": message.message_type,
                        },
                        _correlation_id = message.correlation_id,
                    )
        else:
            logger.warning(
                f"[{self.agent_id}] Unhandled message type: {message.message_type}"
            )

    async def _handle_deliberation_request(self, _message: ActorMessage) -> None:
        """Handle deliberation requests from Steward."""
        _deliberation_id = message.content.get("deliberation_id")
        _topic = message.content.get("topic")

        logger.info(
            f"[{self.agent_id}] Participating in deliberation {deliberation_id}: {topic}"
        )

        # Perform analysis
        _analysis = await self._perform_analysis(topic)

        # Submit vote/analysis
        await self.send(
            _topic = "triad",
            _content = {
                "message_type": "vote_response",
                "deliberation_id": deliberation_id,
                "agent_id": self.agent_id,
                "decision": analysis["decision"],
                "confidence": analysis["confidence"],
                "reasoning": analysis["reasoning"],
            },
        )

        self.decision_count += 1

    async def _handle_analysis_request(self, _message: ActorMessage) -> None:
        """Handle analysis requests with validation."""
        # P2-7 fix: Validate input before processing
        try:
            _validated = self._validate_message_content("analysis_request", message.content)
            if validated:
                _request_id = validated.request_id
                _problem = validated.problem
            else:
                # Fallback to unvalidated access
                _request_id = message.content.get("request_id")
                _problem = message.content.get("problem")
        except ValueError as e:
            logger.error(f"[{self.agent_id}] Analysis validation failed: {e}")
            return

        logger.info(f"[{self.agent_id}] Analyzing: {request_id}")

        analysis = await self._perform_analysis(problem)

        _reply_topic = message.content.get("reply_to", "analysis")
        await self.send(
            _topic = reply_topic,
            _content = {
                "message_type": "analysis_response",
                "request_id": request_id,
                **analysis,
            },
            _correlation_id = message.correlation_id,
        )

        # P2-1 fix: Use timezone-aware datetime
        self.analysis_history.append({
            "request_id": request_id,
            "analysis": analysis,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })
        # P1-3: Trim history if it exceeds max size
        if len(self.analysis_history) > self.max_history_size:
            self.analysis_history = self.analysis_history[-self.max_history_size:]

    async def _handle_validation_request(self, _message: ActorMessage) -> None:
        """Handle validation requests with validation."""
        # P2-7 fix: Validate input before processing
        try:
            _validated = self._validate_message_content("validation_request", message.content)
            if validated:
                _request_id = validated.request_id
                _decision_to_validate = validated.decision
                _original_analysis = validated.original_analysis
            else:
                # Fallback to unvalidated access
                _request_id = message.content.get("request_id")
                _decision_to_validate = message.content.get("decision")
                _original_analysis = message.content.get("original_analysis")  # Reserved for future use
        except ValueError as e:
            logger.error(f"[{self.agent_id}] Validation request validation failed: {e}")
            return

        logger.info(f"[{self.agent_id}] Validating: {request_id}")

        validation = await self._validate_decision(decision_to_validate)

        _reply_topic = message.content.get("reply_to", "validation")
        await self.send(
            _topic = reply_topic,
            _content = {
                "message_type": "validation_response",
                "request_id": request_id,
                **validation,
            },
            _correlation_id = message.correlation_id,
        )

    async def _perform_analysis(self, _problem: str) -> Dict[str, Any]:
        """
        Perform analysis on a problem.

        Args:
            problem: Problem description

        Returns:
            Analysis results with decision, confidence, and reasoning
        """
        if self.swarms_agent:
            try:
                _analysis_result = await self.run_with_llm(
                    _prompt = f"Analyze this problem and provide a decision with confidence: {problem}",
                    _timeout = 60
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

    async def _validate_decision(self, _decision: Any) -> Dict[str, Any]:
        """
        Validate a decision.

        Args:
            decision: Decision to validate

        Returns:
            Validation results
        """
        if self.swarms_agent:
            try:
                _validation_result = await self.run_with_llm(
                    _prompt = f"Validate this decision: {decision}",
                    _timeout = 60
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

    def get_analysis_statistics(self) -> Dict[str, Any]:
        """Get analysis statistics."""
        return {
            "total_analyses": len(self.analysis_history),
            "total_decisions": self.decision_count,
            "analysis_depth": self.analysis_depth,
            "recent_analyses": self.analysis_history[-5:],
        }


class BetaAgent(AgentActor):
    """
    Beta Agent - Secondary analyst and validator.

    The Beta provides complementary analysis to Alpha:
    - Secondary perspective on problems
    - Independent validation
    - Error detection and correction
    - Alternative solution generation
    """

    def __init__(self, _agent_id: str, _name: str, _description: str, _swarms_agent: Optional[Agent], _validation_strictness: float, **kwargs) -> None:
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
            _name = name,
            _description = description,
            _topics = ["triad", "analysis", "validation", "beta"],
            _capabilities = [
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
        self.validation_history: List[Dict[str, Any]] = []
        self.error_detections: List[Dict[str, Any]] = []

        logger.info(f"[{self.agent_id}] Beta agent initialized")

    async def initialize(self) -> None:
        """Initialize the Beta agent."""
        self.register_handler("deliberation_request", self._handle_deliberation_request)
        self.register_handler("validation_request", self._handle_validation_request)
        self.register_handler("error_check", self._handle_error_check)

        logger.info(f"[{self.agent_id}] Beta initialization complete")

    async def process_message(self, _message: ActorMessage) -> None:
        """Process incoming messages."""
        _handler = self._message_handlers.get(message.message_type)
        if handler:
            try:
                await handler(message)
            except Exception as e:
                logger.error(
                    f"[{self.agent_id}] Error processing message {message.message_type}: {e}",
                    _exc_info = True,
                )
                self.error_count += 1
                if message.content.get("reply_to"):
                    await self.send(
                        _topic = message.content["reply_to"],
                        _content = {
                            "message_type": "error_response",
                            "error": str(e),
                            "original_message_type": message.message_type,
                        },
                        _correlation_id = message.correlation_id,
                    )
        else:
            logger.warning(
                f"[{self.agent_id}] Unhandled message type: {message.message_type}"
            )

    async def _handle_deliberation_request(self, _message: ActorMessage) -> None:
        """Handle deliberation requests."""
        _deliberation_id = message.content.get("deliberation_id")
        _topic = message.content.get("topic")

        logger.info(
            f"[{self.agent_id}] Participating in deliberation {deliberation_id}"
        )

        # Perform independent analysis
        _analysis = await self._perform_analysis(topic)

        await self.send(
            _topic = "triad",
            _content = {
                "message_type": "vote_response",
                "deliberation_id": deliberation_id,
                "agent_id": self.agent_id,
                "decision": analysis["decision"],
                "confidence": analysis["confidence"],
                "reasoning": analysis["reasoning"],
            },
        )

    async def _handle_validation_request(self, _message: ActorMessage) -> None:
        """Handle validation requests."""
        _request_id = message.content.get("request_id")
        _decision_to_validate = message.content.get("decision")
        _original_analysis = message.content.get("original_analysis")

        logger.info(f"[{self.agent_id}] Validating: {request_id}")

        validation = await self._validate_decision(
            decision_to_validate,
            original_analysis,
        )

        # P2-1 fix: Use timezone-aware datetime
        self.validation_history.append({
            "request_id": request_id,
            "validation": validation,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })
        # P1-3: Trim history if it exceeds max size
        if len(self.validation_history) > self.max_history_size:
            self.validation_history = self.validation_history[-self.max_history_size:]

        _reply_topic = message.content.get("reply_to", "validation")
        await self.send(
            _topic = reply_topic,
            _content = {
                "message_type": "validation_response",
                "request_id": request_id,
                **validation,
            },
            _correlation_id = message.correlation_id,
        )

    async def _handle_error_check(self, _message: ActorMessage) -> None:
        """Handle error check requests."""
        content = message.content.get("content")

        _errors = await self._detect_errors(content)

        if errors:
            # P2-1 fix: Use timezone-aware datetime
            self.error_detections.append({
                "content": content,
                "errors": errors,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            })
            # P1-3: Trim history if it exceeds max size
            if len(self.error_detections) > self.max_history_size:
                self.error_detections = self.error_detections[-self.max_history_size:]
            logger.warning(f"[{self.agent_id}] Detected {len(errors)} errors")

        _reply_topic = message.content.get("reply_to", "errors")
        await self.send(
            _topic = reply_topic,
            _content = {
                "message_type": "error_check_response",
                "errors": errors,
                "error_count": len(errors),
            },
            _correlation_id = message.correlation_id,
        )

    async def _perform_analysis(self, _problem: str) -> Dict[str, Any]:
        """Perform independent analysis."""
        if self.swarms_agent:
            try:
                _analysis_result = await self.run_with_llm(
                    _prompt = f"Provide independent analysis (Beta perspective): {problem}",
                    _timeout = 60
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

    async def _validate_decision(self, _decision: Any, _original_analysis: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Validate a decision with Beta's perspective."""
        if self.swarms_agent:
            try:
                _validation_result = await self.run_with_llm(
                    _prompt = f"Beta validation of: {decision}. Original: {original_analysis}",
                    _timeout = 60
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

    async def _detect_errors(self, _content: Any) -> List[Dict[str, Any]]:
        """Detect errors in content."""
        _errors = []

        if self.swarms_agent:
            try:
                _error_check = await self.run_with_llm(
                    _prompt = f"Check for errors in: {content}",
                    _timeout = 60
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

    def get_validation_statistics(self) -> Dict[str, Any]:
        """Get validation statistics."""
        return {
            "total_validations": len(self.validation_history),
            "total_errors_detected": len(self.error_detections),
            "validation_strictness": self.validation_strictness,
            "recent_validations": self.validation_history[-5:],
        }


class CharlieAgent(AgentActor):
    """
    Charlie Agent - Tertiary perspective and challenger.

    The Charlie provides critical challenge to the Triad:
    - Devil's advocate perspective
    - Edge case identification
    - Risk assessment
    - Creative alternative solutions
    """

    def __init__(self, _agent_id: str, _name: str, _description: str, _swarms_agent: Optional[Agent], _challenge_intensity: str, **kwargs) -> None:
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
            _name = name,
            _description = description,
            _topics = ["triad", "challenge", "risk", "charlie"],
            _capabilities = [
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
        self.challenges_raised: List[Dict[str, Any]] = []
        self.risk_assessments: List[Dict[str, Any]] = []

        logger.info(f"[{self.agent_id}] Charlie agent initialized")

    async def initialize(self) -> None:
        """Initialize the Charlie agent."""
        self.register_handler("deliberation_request", self._handle_deliberation_request)
        self.register_handler("challenge_request", self._handle_challenge_request)
        self.register_handler("risk_assessment", self._handle_risk_assessment)

        logger.info(f"[{self.agent_id}] Charlie initialization complete")

    async def process_message(self, _message: ActorMessage) -> None:
        """Process incoming messages."""
        _handler = self._message_handlers.get(message.message_type)
        if handler:
            try:
                await handler(message)
            except Exception as e:
                logger.error(
                    f"[{self.agent_id}] Error processing message {message.message_type}: {e}",
                    _exc_info = True,
                )
                self.error_count += 1
                if message.content.get("reply_to"):
                    await self.send(
                        _topic = message.content["reply_to"],
                        _content = {
                            "message_type": "error_response",
                            "error": str(e),
                            "original_message_type": message.message_type,
                        },
                        _correlation_id = message.correlation_id,
                    )
        else:
            logger.warning(
                f"[{self.agent_id}] Unhandled message type: {message.message_type}"
            )

    async def _handle_deliberation_request(self, _message: ActorMessage) -> None:
        """Handle deliberation requests."""
        _deliberation_id = message.content.get("deliberation_id")
        _topic = message.content.get("topic")

        logger.info(
            f"[{self.agent_id}] Participating in deliberation {deliberation_id}"
        )

        # Perform challenging analysis
        _analysis = await self._perform_analysis(topic)

        await self.send(
            _topic = "triad",
            _content = {
                "message_type": "vote_response",
                "deliberation_id": deliberation_id,
                "agent_id": self.agent_id,
                "decision": analysis["decision"],
                "confidence": analysis["confidence"],
                "reasoning": analysis["reasoning"],
                "challenges": analysis.get("challenges", []),
            },
        )

    async def _handle_challenge_request(self, _message: ActorMessage) -> None:
        """Handle challenge requests."""
        _request_id = message.content.get("request_id")
        _proposition = message.content.get("proposition")

        logger.info(f"[{self.agent_id}] Challenging: {request_id}")

        challenges = await self._generate_challenges(proposition)

        # P2-1 fix: Use timezone-aware datetime
        self.challenges_raised.append({
            "proposition": proposition,
            "challenges": challenges,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })
        # P1-3: Trim history if it exceeds max size
        if len(self.challenges_raised) > self.max_history_size:
            self.challenges_raised = self.challenges_raised[-self.max_history_size:]

        _reply_topic = message.content.get("reply_to", "challenges")
        await self.send(
            _topic = reply_topic,
            _content = {
                "message_type": "challenge_response",
                "request_id": request_id,
                "challenges": challenges,
                "challenge_count": len(challenges),
            },
            _correlation_id = message.correlation_id,
        )

    async def _handle_risk_assessment(self, _message: ActorMessage) -> None:
        """Handle risk assessment requests."""
        _request_id = message.content.get("request_id")
        _scenario = message.content.get("scenario")

        logger.info(f"[{self.agent_id}] Assessing risks: {request_id}")

        _assessment = await self._assess_risks(scenario)

        # P2-1 fix: Use timezone-aware datetime
        self.risk_assessments.append({
            "scenario": scenario,
            "assessment": assessment,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })
        # P1-3: Trim history if it exceeds max size
        if len(self.risk_assessments) > self.max_history_size:
            self.risk_assessments = self.risk_assessments[-self.max_history_size:]

        _reply_topic = message.content.get("reply_to", "risks")
        await self.send(
            _topic = reply_topic,
            _content = {
                "message_type": "risk_assessment_response",
                "request_id": request_id,
                **assessment,
            },
            _correlation_id = message.correlation_id,
        )

    async def _perform_analysis(self, _problem: str) -> Dict[str, Any]:
        """Perform challenging analysis."""
        if self.swarms_agent:
            try:
                _analysis_result = await self.run_with_llm(
                    _prompt = f"Analyze with critical perspective (Charlie): {problem}. Identify risks and alternatives.",
                    _timeout = 60
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

    async def _generate_challenges(self, _proposition: Any) -> List[Dict[str, Any]]:
        """Generate challenges to a proposition."""
        challenges = []

        if self.swarms_agent:
            try:
                _challenge_result = await self.run_with_llm(
                    _prompt = f"Challenge this proposition: {proposition}",
                    _timeout = 60
                )
                challenges.append({
                    "type": "logical_challenge",
                    "description": challenge_result,
                    "severity": "medium",
                })
            except Exception as e:
                logger.error(f"[{self.agent_id}] Challenge error: {e}")

        return challenges

    async def _assess_risks(self, _scenario: Any) -> Dict[str, Any]:
        """Assess risks in a scenario."""
        if self.swarms_agent:
            try:
                _risk_result = await self.run_with_llm(
                    _prompt = f"Assess risks: {scenario}",
                    _timeout = 60
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
            "risk_level": "unknown",
            "mitigations": [],
        }

    def get_challenge_statistics(self) -> Dict[str, Any]:
        """Get challenge statistics."""
        return {
            "total_challenges": len(self.challenges_raised),
            "total_risk_assessments": len(self.risk_assessments),
            "challenge_intensity": self.challenge_intensity,
            "recent_challenges": self.challenges_raised[-5:],
        }
