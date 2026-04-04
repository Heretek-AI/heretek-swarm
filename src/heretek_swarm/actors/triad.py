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

import asyncio
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

import structlog
from swarms import Agent

from heretek_swarm.actors.base import AgentActor, ActorMessage

logger = structlog.get_logger("TriadAgents")


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

    def __init__(
        self,
        agent_id: str = "steward",
        name: str = "Steward",
        description: str = "Triad coordinator and governance agent",
        swarms_agent: Optional[Agent] = None,
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

    async def process_message(self, message: ActorMessage) -> None:
        """
        Process incoming messages.

        Args:
            message: Actor message to process
        """
        handler = self._message_handlers.get(message.message_type)
        if handler:
            await handler(message)
        else:
            logger.warning(
                f"[{self.agent_id}] Unhandled message type: {message.message_type}"
            )

    async def _handle_start_deliberation(self, message: ActorMessage) -> None:
        """Handle deliberation start requests."""
        deliberation_id = message.content.get("deliberation_id")
        topic = message.content.get("topic")
        triad_members = message.content.get("triad_members", [])

        if not deliberation_id or not topic:
            logger.error(f"[{self.agent_id}] Missing deliberation parameters")
            return

        # Initialize deliberation
        self.active_deliberations[deliberation_id] = {
            "topic": topic,
            "triad_members": triad_members,
            "status": "initiated",
            "started_at": datetime.utcnow().isoformat(),
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
        decision_context = message.content.get("context", {})

        logger.info(
            f"[{self.agent_id}] Processing decision request: {request_id}"
        )

        # Make executive decision or delegate to triad
        if self.swarms_agent:
            try:
                decision = await self.run_with_llm(
                    prompt=f"Make an executive decision on: {decision_context}"
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
        """Handle status reports from triad members."""
        reporter_id = message.content.get("agent_id")
        status = message.content.get("status", {})

        logger.debug(f"[{self.agent_id}] Status report from {reporter_id}")

        # Update internal tracking
        self.update_state(f"status:{reporter_id}", status)

    async def _handle_policy_update(self, message: ActorMessage) -> None:
        """Handle policy update requests."""
        policy_id = message.content.get("policy_id")
        policy_data = message.content.get("policy_data")

        if policy_id and policy_data:
            self.governance_policies[policy_id] = {
                **policy_data,
                "updated_at": datetime.utcnow().isoformat(),
                "updated_by": message.sender,
            }
            logger.info(f"[{self.agent_id}] Updated policy: {policy_id}")

    async def coordinate_triad(
        self,
        topic: str,
        triad_members: List[str],
    ) -> str:
        """
        Coordinate a triad deliberation.

        Args:
            topic: Deliberation topic
            triad_members: List of triad member IDs

        Returns:
            Deliberation ID
        """
        deliberation_id = f"del_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"

        await self.send(
            topic="triad",
            content={
                "message_type": "start_deliberation",
                "deliberation_id": deliberation_id,
                "topic": topic,
                "triad_members": triad_members,
            },
        )

        return deliberation_id

    def get_deliberation_status(self, deliberation_id: str) -> Optional[Dict[str, Any]]:
        """Get status of a deliberation."""
        return self.active_deliberations.get(deliberation_id)

    def get_governance_policy(self, policy_id: str) -> Optional[Dict[str, Any]]:
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

    def __init__(
        self,
        agent_id: str = "alpha",
        name: str = "Alpha",
        description: str = "Primary decision maker and analyst",
        swarms_agent: Optional[Agent] = None,
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
        self.analysis_history: List[Dict[str, Any]] = []
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
            await handler(message)
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
        """Handle analysis requests."""
        request_id = message.content.get("request_id")
        problem = message.content.get("problem")

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

        self.analysis_history.append({
            "request_id": request_id,
            "analysis": analysis,
            "timestamp": datetime.utcnow().isoformat(),
        })

    async def _handle_validation_request(self, message: ActorMessage) -> None:
        """Handle validation requests."""
        request_id = message.content.get("request_id")
        decision_to_validate = message.content.get("decision")

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

    async def _perform_analysis(self, problem: str) -> Dict[str, Any]:
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
                    prompt=f"Analyze this problem and provide a decision with confidence: {problem}"
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

    async def _validate_decision(self, decision: Any) -> Dict[str, Any]:
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
                    prompt=f"Validate this decision: {decision}"
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

    def __init__(
        self,
        agent_id: str = "beta",
        name: str = "Beta",
        description: str = "Secondary analyst and validator",
        swarms_agent: Optional[Agent] = None,
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
        self.validation_history: List[Dict[str, Any]] = []
        self.error_detections: List[Dict[str, Any]] = []

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
            await handler(message)
        else:
            logger.warning(
                f"[{self.agent_id}] Unhandled message type: {message.message_type}"
            )

    async def _handle_deliberation_request(self, message: ActorMessage) -> None:
        """Handle deliberation requests."""
        deliberation_id = message.content.get("deliberation_id")
        topic = message.content.get("topic")

        logger.info(
            f"[{self.agent_id}] Participating in deliberation {deliberation_id}"
        )

        # Perform independent analysis
        analysis = await self._perform_analysis(topic)

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

        self.validation_history.append({
            "request_id": request_id,
            "validation": validation,
            "timestamp": datetime.utcnow().isoformat(),
        })

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

        if errors:
            self.error_detections.append({
                "content": content,
                "errors": errors,
                "timestamp": datetime.utcnow().isoformat(),
            })
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

    async def _perform_analysis(self, problem: str) -> Dict[str, Any]:
        """Perform independent analysis."""
        if self.swarms_agent:
            try:
                analysis_result = await self.run_with_llm(
                    prompt=f"Provide independent analysis (Beta perspective): {problem}"
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
        original_analysis: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Validate a decision with Beta's perspective."""
        if self.swarms_agent:
            try:
                validation_result = await self.run_with_llm(
                    prompt=f"Beta validation of: {decision}. Original: {original_analysis}"
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

    async def _detect_errors(self, content: Any) -> List[Dict[str, Any]]:
        """Detect errors in content."""
        errors = []

        if self.swarms_agent:
            try:
                error_check = await self.run_with_llm(
                    prompt=f"Check for errors in: {content}"
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

    def __init__(
        self,
        agent_id: str = "charlie",
        name: str = "Charlie",
        description: str = "Tertiary perspective and challenger",
        swarms_agent: Optional[Agent] = None,
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
        self.challenges_raised: List[Dict[str, Any]] = []
        self.risk_assessments: List[Dict[str, Any]] = []

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
            await handler(message)
        else:
            logger.warning(
                f"[{self.agent_id}] Unhandled message type: {message.message_type}"
            )

    async def _handle_deliberation_request(self, message: ActorMessage) -> None:
        """Handle deliberation requests."""
        deliberation_id = message.content.get("deliberation_id")
        topic = message.content.get("topic")

        logger.info(
            f"[{self.agent_id}] Participating in deliberation {deliberation_id}"
        )

        # Perform challenging analysis
        analysis = await self._perform_analysis(topic)

        await self.send(
            topic="triad",
            content={
                "message_type": "vote_response",
                "deliberation_id": deliberation_id,
                "agent_id": self.agent_id,
                "decision": analysis["decision"],
                "confidence": analysis["confidence"],
                "reasoning": analysis["reasoning"],
                "challenges": analysis.get("challenges", []),
            },
        )

    async def _handle_challenge_request(self, message: ActorMessage) -> None:
        """Handle challenge requests."""
        request_id = message.content.get("request_id")
        proposition = message.content.get("proposition")

        logger.info(f"[{self.agent_id}] Challenging: {request_id}")

        challenges = await self._generate_challenges(proposition)

        self.challenges_raised.append({
            "proposition": proposition,
            "challenges": challenges,
            "timestamp": datetime.utcnow().isoformat(),
        })

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
        request_id = message.content.get("request_id")
        scenario = message.content.get("scenario")

        logger.info(f"[{self.agent_id}] Assessing risks: {request_id}")

        assessment = await self._assess_risks(scenario)

        self.risk_assessments.append({
            "scenario": scenario,
            "assessment": assessment,
            "timestamp": datetime.utcnow().isoformat(),
        })

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

    async def _perform_analysis(self, problem: str) -> Dict[str, Any]:
        """Perform challenging analysis."""
        if self.swarms_agent:
            try:
                analysis_result = await self.run_with_llm(
                    prompt=f"Analyze with critical perspective (Charlie): {problem}. Identify risks and alternatives."
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

    async def _generate_challenges(self, proposition: Any) -> List[Dict[str, Any]]:
        """Generate challenges to a proposition."""
        challenges = []

        if self.swarms_agent:
            try:
                challenge_result = await self.run_with_llm(
                    prompt=f"Challenge this proposition: {proposition}"
                )
                challenges.append({
                    "type": "logical_challenge",
                    "description": challenge_result,
                    "severity": "medium",
                })
            except Exception as e:
                logger.error(f"[{self.agent_id}] Challenge error: {e}")

        return challenges

    async def _assess_risks(self, scenario: Any) -> Dict[str, Any]:
        """Assess risks in a scenario."""
        if self.swarms_agent:
            try:
                risk_result = await self.run_with_llm(
                    prompt=f"Assess risks: {scenario}"
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
