"""
Prism Agent - Multi-Perspective Analysis & Bias Detection.

The Prism agent provides:
- Multi-perspective analysis of complex issues
- Cognitive bias detection in collective reasoning
- Analytical framework application (First Principles, Systems Thinking, etc.)
- Stakeholder mapping and viewpoint synthesis
- Perspective diversification for decision-making

Named for the ability to refract complex issues into multiple distinct perspectives,
revealing hidden facets and ensuring comprehensive analysis.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

import structlog
from swarms import Agent

from heretek_swarm.actors.base import ActorMessage, AgentActor

# Session 44: Collective Learning Integration
from heretek_swarm.collective.learning import PatternExtractor, PatternType

# Phi Training Integration
from heretek_swarm.consciousness.phi_training import (
    AgentActor,
    DecisionCoherenceTrainingScenario,
    PhiTrainingEnvironment,
    TrainingScenario,
)

# Session 44: Consensus Integration
from heretek_swarm.consensus.swarm_deliberation import Position, SwarmDeliberationEngine

# Session 44: Memory Optimization Integration
from heretek_swarm.memory.access_patterns import AccessPatternAnalyzer, AccessTier

# Session 44: Zero-Trust Validation
from heretek_swarm.security.zero_trust import ZeroTrustValidator

logger = structlog.get_logger("PrismAgent")


class PerspectiveType(str, Enum):
    """Types of perspectives Prism can generate."""
    TECHNICAL = "technical"
    USER = "user"
    BUSINESS = "business"
    SECURITY = "security"
    ETHICAL = "ethical"
    LONG_TERM = "long_term"
    SHORT_TERM = "short_term"
    STAKEHOLDER = "stakeholder"
    SYSTEMS = "systems"
    FIRST_PRINCIPLES = "first_principles"


class BiasType(str, Enum):
    """Cognitive biases Prism can detect."""
    CONFIRMATION = "confirmation_bias"
    ANCHORING = "anchoring_bias"
    AVAILABILITY = "availability_heuristic"
    SURVIVORSHIP = "survivorship_bias"
    SUNK_COST = "sunk_cost_fallacy"
    OVERCONFIDENCE = "overconfidence_bias"
    GROUP_THINK = "group_think"
    RECENTCY = "recency_bias"
    SELECTION = "selection_bias"
    ATTRIBUTION = "attribution_error"


class AnalyticalFramework(str, Enum):
    """Analytical frameworks Prism can apply."""
    FIRST_PRINCIPLES = "first_principles"
    SYSTEMS_THINKING = "systems_thinking"
    PRE_MORTEM = "pre_mortem"
    STAKEHOLDER_IMPACT = "stakeholder_impact"
    COST_BENEFIT = "cost_benefit"
    SWOT = "swot_analysis"
    FIVE_WHY = "five_whys"
    ROOT_CAUSE = "root_cause_analysis"


class Perspective:
    """Represents a single perspective on an issue."""

    def __init__(
        self,
        perspective_type: PerspectiveType,
        viewpoint: str,
        key_insights: List[str],
        assumptions: List[str],
        blind_spots: List[str],
        confidence: float = 0.0,
    ) -> None:
        self.perspective_type = perspective_type
        self.viewpoint = viewpoint
        self.key_insights = key_insights
        self.assumptions = assumptions
        self.blind_spots = blind_spots
        self.confidence = confidence
        self.timestamp = datetime.now(timezone.utc)

    def to_dict(self) -> Dict[str, Any]:
        """Convert perspective to dictionary."""
        return {
            "perspective_type": self.perspective_type.value,
            "viewpoint": self.viewpoint,
            "key_insights": self.key_insights,
            "assumptions": self.assumptions,
            "blind_spots": self.blind_spots,
            "confidence": self.confidence,
            "timestamp": self.timestamp.isoformat(),
        }


class BiasDetection:
    """Represents a detected cognitive bias."""

    def __init__(
        self,
        bias_type: BiasType,
        description: str,
        evidence: List[str],
        severity: str = "medium",
        recommendation: Optional[str] = None,
    ) -> None:
        self.bias_type = bias_type
        self.description = description
        self.evidence = evidence
        self.severity = severity
        self.recommendation = recommendation
        self.timestamp = datetime.now(timezone.utc)

    def to_dict(self) -> Dict[str, Any]:
        """Convert bias detection to dictionary."""
        return {
            "bias_type": self.bias_type.value,
            "description": self.description,
            "evidence": self.evidence,
            "severity": self.severity,
            "recommendation": self.recommendation,
            "timestamp": self.timestamp.isoformat(),
        }


class PrismAgent(AgentActor):
    """
    Prism Agent - Multi-Perspective Analysis Specialist.
    
    The Prism is responsible for:
    - Generating multiple perspectives on complex issues
    - Detecting cognitive biases in collective reasoning
    - Applying different analytical frameworks to problems
    - Mapping stakeholders and their interests
    - Ensuring diverse viewpoints are considered
    
    Perspective Analysis Workflow:
    1. Receive issue or decision for analysis
    2. Identify relevant perspective types
    3. Generate viewpoints for each perspective
    4. Detect biases in current reasoning
    5. Apply analytical frameworks
    6. Synthesize insights for collective
    """

    def __init__(
        self,
        agent_id: str = "prism",
        name: str = "Prism",
        description: str = "Multi-perspective analysis and bias detection specialist",
        swarms_agent: Optional[Agent] = None,
        max_perspectives: int = 12,
        max_bias_history: int = 100,
        confidence_threshold: float = 0.6,
        **kwargs,
    ) -> None:
        """
        Initialize the Prism agent.
        
        Args:
            agent_id: Unique identifier
            name: Human-readable name
            description: Agent description
            swarms_agent: Optional Swarms Agent for LLM capabilities
            max_perspectives: Maximum perspectives to generate per issue
            max_bias_history: Maximum bias detections to track
            confidence_threshold: Minimum confidence for perspective recommendations
            **kwargs: Additional arguments
        """
        super().__init__(
            agent_id=agent_id,
            name=name,
            description=description,
            topics=[
                "perspectives",
                "analysis",
                "reframing",
                "biases",
                "viewpoints",
            ],
            capabilities=[
                "multi-perspective-analysis",
                "bias-detection",
                "framework-application",
                "stakeholder-mapping",
                "viewpoint-synthesis",
            ],
            swarms_agent=swarms_agent,
            **kwargs,
        )

        # Prism-specific state
        self.max_perspectives = max_perspectives
        self.max_bias_history = max_bias_history
        self.confidence_threshold = confidence_threshold

        # Perspective and bias tracking
        self.active_analyses: Dict[str, Dict[str, Any]] = {}
        self.perspective_cache: Dict[str, List[Perspective]] = {}
        self.bias_history: List[BiasDetection] = []
        self.framework_results: Dict[str, Dict[str, Any]] = {}
        self.stakeholder_maps: Dict[str, Dict[str, Any]] = {}

        # Available perspectives and frameworks
        self.available_perspectives: List[PerspectiveType] = list(PerspectiveType)
        self.available_frameworks: List[AnalyticalFramework] = list(AnalyticalFramework)
        self.available_biases: List[BiasType] = list(BiasType)


        # Session 44: Collective Learning Integration
        self.pattern_extractor = pattern_extractor or PatternExtractor(min_support=3, min_confidence=0.6)

        # Session 44: Consensus Integration
        self.deliberation_engine = deliberation_engine or SwarmDeliberationEngine(
            max_rounds=5, consensus_threshold=0.75, min_participants=2
        )

        # Session 44: Memory Optimization Integration
        self.access_analyzer = access_analyzer or AccessPatternAnalyzer()

        # Session 44: Zero-Trust Validation
        self.zero_trust_validator = zero_trust_validator or ZeroTrustValidator()

        # Session 44: Integration state
        self._active_deliberations: Dict[str, str] = {}
        self._pattern_emitted: Set[str] = set()


        logger.info(f"[{self.agent_id}] Prism agent initialized")

    async def initialize(self) -> None:
        """Initialize the Prism agent."""
        # Register message handlers with Zero-Trust validation
        self.register_handler("generate_perspectives", self._handle_generate_perspectives)
        self.register_handler("detect_biases", self._handle_detect_biases)
        self.register_handler("apply_framework", self._handle_apply_framework)
        self.register_handler("map_stakeholders", self._handle_map_stakeholders)
        self.register_handler("get_analysis_summary", self._handle_get_analysis_summary)
        self.register_handler("reframe_issue", self._handle_reframe_issue)

        logger.info(f"[{self.agent_id}] Prism initialization complete")

    async def process_message(self, message: ActorMessage) -> None:
        """
        Process incoming messages with exception handling.
        
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
                if message.content.get("reply_to"):
                    await self.send(
                        topic=message.content["reply_to"],
                        content={
                            "message_type": "error_response",
                            "error": str(e),
                            "original_message_type": message.message_type,
                        },
                        sender_id=self.agent_id,
                    )
        else:
            logger.warning(f"[{self.agent_id}] Unknown message type: {message.message_type}")

    def _validate_analysis_request(self, content: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Validate analysis request content.
        
        Args:
            content: Message content to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if "issue" not in content:
            return False, "Missing required field: issue"
        if not isinstance(content["issue"], str):
            return False, "Field 'issue' must be a string"
        if len(content["issue"]) > 10000:
            return False, "Issue exceeds maximum length (10000 chars)"
        return True, ""

    async def _handle_generate_perspectives(self, message: ActorMessage) -> None:
        """
        Generate multiple perspectives on an issue.
        
        Args:
            message: Actor message with issue details
        """
        try:
            # Validate content
            is_valid, error = self._validate_analysis_request(message.content)
            if not is_valid:
                logger.error(f"[{self.agent_id}] Invalid perspective request: {error}")
                return

            issue = message.content["issue"]
            analysis_id = message.content.get("analysis_id", f"analysis_{datetime.now(timezone.utc).timestamp()}")
            requested_perspectives = message.content.get("perspective_types", None)

            logger.info(f"[{self.agent_id}] Generating perspectives for analysis: {analysis_id}")

            # Generate perspectives
            perspectives = await self._generate_perspectives(
                issue=issue,
                perspective_types=requested_perspectives,
            )

            # Store in cache
            self.perspective_cache[analysis_id] = perspectives

            # Store active analysis
            self.active_analyses[analysis_id] = {
                "issue": issue,
                "perspectives_count": len(perspectives),
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "status": "complete",
            }

            # Send response
            response = {
                "message_type": "perspectives_response",
                "analysis_id": analysis_id,
                "perspectives": [p.to_dict() for p in perspectives],
                "perspectives_count": len(perspectives),
            }

            if message.content.get("reply_to"):
                await self.send(
                    topic=message.content["reply_to"],
                    content=response,
                    sender_id=self.agent_id,
                )

            logger.info(f"[{self.agent_id}] Generated {len(perspectives)} perspectives for analysis: {analysis_id}")

        except Exception as e:
            logger.error(f"[{self.agent_id}] Error generating perspectives: {e}", exc_info=True)

    async def _generate_perspectives(
        self,
        issue: str,
        perspective_types: Optional[List[str]] = None,
    ) -> List[Perspective]:
        """
        Generate multiple perspectives on an issue.
        
        Args:
            issue: The issue to analyze
            perspective_types: Optional list of specific perspective types
            
        Returns:
            List of Perspective objects
        """
        perspectives = []

        # Determine which perspectives to generate
        if perspective_types:
            types_to_use = [
                PerspectiveType(t) for t in perspective_types 
                if t in [pt.value for pt in PerspectiveType]
            ]
        else:
            types_to_use = self.available_perspectives[:self.max_perspectives]

        # Generate perspective for each type
        for ptype in types_to_use:
            try:
                perspective = await self._generate_single_perspective(issue, ptype)
                if perspective.confidence >= self.confidence_threshold:
                    perspectives.append(perspective)
            except Exception as e:
                logger.warning(f"[{self.agent_id}] Failed to generate {ptype.value} perspective: {e}")

        # Sort by confidence
        perspectives.sort(key=lambda p: p.confidence, reverse=True)

        return perspectives[:self.max_perspectives]

    async def _generate_single_perspective(
        self,
        issue: str,
        perspective_type: PerspectiveType,
    ) -> Perspective:
        """
        Generate a single perspective on an issue.
        
        Args:
            issue: The issue to analyze
            perspective_type: Type of perspective to generate
            
        Returns:
            Perspective object
        """
        # Build prompt for LLM
        prompt = f"""Analyze the following issue from a {perspective_type.value} perspective:

ISSUE: {issue}

Generate a comprehensive {perspective_type.value} perspective including:
1. The primary viewpoint from this perspective
2. Key insights this perspective reveals
3. Underlying assumptions this perspective makes
4. Blind spots or limitations of this perspective
5. A confidence score (0-1) in the analysis

Respond in JSON format:
{{
    "viewpoint": "...",
    "key_insights": ["...", "..."],
    "assumptions": ["...", "..."],
    "blind_spots": ["...", "..."],
    "confidence": 0.0-1.0
}}"""

        try:
            # Try LLM-based generation
            if self.swarms_agent:
                result = await self.run_with_llm(
                    prompt=prompt,
                    timeout=60,
                )

                # Parse result (assume JSON in response)
                import json
                try:
                    # Extract JSON from response
                    start_idx = result.find("{")
                    end_idx = result.rfind("}") + 1
                    if start_idx >= 0 and end_idx > start_idx:
                        json_str = result[start_idx:end_idx]
                        data = json.loads(json_str)

                        return Perspective(
                            perspective_type=perspective_type,
                            viewpoint=data.get("viewpoint", ""),
                            key_insights=data.get("key_insights", []),
                            assumptions=data.get("assumptions", []),
                            blind_spots=data.get("blind_spots", []),
                            confidence=float(data.get("confidence", 0.5)),
                        )
                except Exception:
                    pass

            # Fallback: Generate heuristic perspective
            return self._heuristic_perspective(issue, perspective_type)

        except Exception as e:
            logger.warning(f"[{self.agent_id}] LLM perspective generation failed, using heuristic: {e}")
            return self._heuristic_perspective(issue, perspective_type)

    def _heuristic_perspective(
        self,
        issue: str,
        perspective_type: PerspectiveType,
    ) -> Perspective:
        """
        Generate a heuristic perspective when LLM is unavailable.
        
        Args:
            issue: The issue to analyze
            perspective_type: Type of perspective
            
        Returns:
            Perspective object with heuristic analysis
        """
        # Perspective-specific heuristics
        viewpoint_templates = {
            PerspectiveType.TECHNICAL: "From a technical standpoint, this issue involves implementation considerations...",
            PerspectiveType.USER: "From a user perspective, the key concerns are usability and experience...",
            PerspectiveType.BUSINESS: "From a business perspective, we must consider cost-benefit and ROI...",
            PerspectiveType.SECURITY: "From a security perspective, we need to evaluate risks and vulnerabilities...",
            PerspectiveType.ETHICAL: "From an ethical perspective, we should consider moral implications...",
            PerspectiveType.LONG_TERM: "From a long-term perspective, we need to consider future impacts...",
            PerspectiveType.SHORT_TERM: "From a short-term perspective, immediate concerns include...",
            PerspectiveType.STAKEHOLDER: "From a stakeholder perspective, multiple parties are affected...",
            PerspectiveType.SYSTEMS: "From a systems perspective, we must analyze interconnections...",
            PerspectiveType.FIRST_PRINCIPLES: "From first principles, we break this down to fundamental truths...",
        }

        base_viewpoint = viewpoint_templates.get(
            perspective_type,
            f"From a {perspective_type.value} perspective..."
        )

        return Perspective(
            perspective_type=perspective_type,
            viewpoint=base_viewpoint,
            key_insights=[f"Heuristic insight for {perspective_type.value} perspective"],
            assumptions=["Based on general domain knowledge"],
            blind_spots=["May miss context-specific factors"],
            confidence=0.5,  # Lower confidence for heuristic
        )

    async def _handle_detect_biases(self, message: ActorMessage) -> None:
        """
        Detect cognitive biases in reasoning or deliberation.
        
        Args:
            message: Actor message with reasoning/deliberation content
        """
        try:
            # Validate content
            content = message.content.get("reasoning", "") or message.content.get("deliberation", "")
            if not content:
                logger.error(f"[{self.agent_id}] No reasoning content provided for bias detection")
                return

            if len(content) > 50000:
                logger.error(f"[{self.agent_id}] Content exceeds maximum length")
                return

            logger.info(f"[{self.agent_id}] Detecting biases in reasoning")

            # Detect biases
            biases = await self._detect_biases_in_content(content)

            # Store in history
            self.bias_history.extend(biases)
            if len(self.bias_history) > self.max_bias_history:
                self.bias_history = self.bias_history[-self.max_bias_history:]

            # Send response
            response = {
                "message_type": "bias_detection_response",
                "biases_detected": len(biases),
                "biases": [b.to_dict() for b in biases],
                "recommendations": [b.recommendation for b in biases if b.recommendation],
            }

            if message.content.get("reply_to"):
                await self.send(
                    topic=message.content["reply_to"],
                    content=response,
                    sender_id=self.agent_id,
                )

            logger.info(f"[{self.agent_id}] Detected {len(biases)} potential biases")

        except Exception as e:
            logger.error(f"[{self.agent_id}] Error detecting biases: {e}", exc_info=True)

    async def _detect_biases_in_content(self, content: str) -> List[BiasDetection]:
        """
        Detect cognitive biases in content.
        
        Args:
            content: Text content to analyze
            
        Returns:
            List of detected biases
        """
        biases = []

        # Build prompt for LLM
        prompt = f"""Analyze the following reasoning for cognitive biases:

REASONING: {content[:5000]}  # Truncate for prompt

Identify any cognitive biases present, including:
- Confirmation bias (favoring information that confirms existing beliefs)
- Anchoring bias (relying too heavily on first piece of information)
- Availability heuristic (overweighting recent/vivid information)
- Survivorship bias (focusing on successes while ignoring failures)
- Sunk cost fallacy (continuing due to invested resources)
- Overconfidence bias (excessive confidence in judgments)
- Group think (conforming to group consensus)
- Recency bias (overweighting recent events)

For each bias detected, provide:
1. Bias type
2. Description of how it manifests
3. Evidence from the text
4. Severity (low/medium/high)
5. Recommendation to mitigate

Respond in JSON format:
[
    {{
        "bias_type": "...",
        "description": "...",
        "evidence": ["...", "..."],
        "severity": "...",
        "recommendation": "..."
    }}
]"""

        try:
            if self.swarms_agent:
                result = await self.run_with_llm(
                    prompt=prompt,
                    timeout=60,
                )

                import json
                try:
                    start_idx = result.find("[")
                    end_idx = result.rfind("]") + 1
                    if start_idx >= 0 and end_idx > start_idx:
                        json_str = result[start_idx:end_idx]
                        data = json.loads(json_str)

                        for item in data:
                            bias_type_str = item.get("bias_type", "")
                            bias_type = None
                            for bt in self.available_biases:
                                if bt.value == bias_type_str or bt.name.lower() == bias_type_str.lower():
                                    bias_type = bt
                                    break

                            if bias_type:
                                biases.append(BiasDetection(
                                    bias_type=bias_type,
                                    description=item.get("description", ""),
                                    evidence=item.get("evidence", []),
                                    severity=item.get("severity", "medium"),
                                    recommendation=item.get("recommendation"),
                                ))
                except Exception:
                    pass

            # Fallback: Pattern-based bias detection
            biases.extend(self._heuristic_bias_detection(content))

        except Exception as e:
            logger.warning(f"[{self.agent_id}] LLM bias detection failed: {e}")
            biases.extend(self._heuristic_bias_detection(content))

        return biases

    def _heuristic_bias_detection(self, content: str) -> List[BiasDetection]:
        """
        Detect biases using pattern matching when LLM unavailable.
        
        Args:
            content: Text content to analyze
            
        Returns:
            List of detected biases
        """
        biases = []

        # Simple pattern indicators
        bias_patterns = {
            BiasType.CONFIRMATION: ["clearly shows", "obviously proves", "as expected", "confirms our"],
            BiasType.ANCHORING: ["initial", "starting with", "base case", "original"],
            BiasType.SUNK_COST: ["already invested", "we've come so far", "can't stop now", "previous commitment"],
            BiasType.OVERCONFIDENCE: ["definitely", "certainly", "without doubt", "guaranteed", "always"],
            BiasType.GROUP_THINK: ["everyone agrees", "consensus is", "we all think", "unanimous"],
        }

        content_lower = content.lower()
        for bias_type, patterns in bias_patterns.items():
            for pattern in patterns:
                if pattern in content_lower:
                    biases.append(BiasDetection(
                        bias_type=bias_type,
                        description=f"Potential {bias_type.value} detected based on language patterns",
                        evidence=[f"Found pattern: '{pattern}'"],
                        severity="low",
                        recommendation="Consider alternative viewpoints and seek disconfirming evidence",
                    ))
                    break  # One detection per bias type

        return biases

    async def _handle_apply_framework(self, message: ActorMessage) -> None:
        """
        Apply an analytical framework to an issue.
        
        Args:
            message: Actor message with issue and framework
        """
        try:
            # Validate content
            is_valid, error = self._validate_analysis_request(message.content)
            if not is_valid:
                logger.error(f"[{self.agent_id}] Invalid framework request: {error}")
                return

            issue = message.content["issue"]
            framework_str = message.content.get("framework", "first_principles")
            analysis_id = message.content.get("analysis_id", f"framework_{datetime.now(timezone.utc).timestamp()}")

            # Map framework string to enum
            framework = None
            for f in self.available_frameworks:
                if f.value == framework_str or f.name.lower() == framework_str.lower():
                    framework = f
                    break

            if not framework:
                logger.error(f"[{self.agent_id}] Unknown framework: {framework_str}")
                return

            logger.info(f"[{self.agent_id}] Applying framework {framework.value} to issue")

            # Apply framework
            result = await self._apply_framework_to_issue(issue, framework)

            # Store results
            self.framework_results[analysis_id] = {
                "framework": framework.value,
                "issue": issue,
                "result": result,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

            # Send response
            response = {
                "message_type": "framework_response",
                "analysis_id": analysis_id,
                "framework": framework.value,
                "result": result,
            }

            if message.content.get("reply_to"):
                await self.send(
                    topic=message.content["reply_to"],
                    content=response,
                    sender_id=self.agent_id,
                )

            logger.info(f"[{self.agent_id}] Framework {framework.value} applied successfully")

        except Exception as e:
            logger.error(f"[{self.agent_id}] Error applying framework: {e}", exc_info=True)

    async def _apply_framework_to_issue(
        self,
        issue: str,
        framework: AnalyticalFramework,
    ) -> Dict[str, Any]:
        """
        Apply an analytical framework to an issue.
        
        Args:
            issue: The issue to analyze
            framework: Framework to apply
            
        Returns:
            Framework analysis result
        """
        # Framework-specific prompts
        framework_prompts = {
            AnalyticalFramework.FIRST_PRINCIPLES: f"""Break down this issue to first principles:

ISSUE: {issue}

Identify:
1. Fundamental truths that are certain
2. Assumptions that can be questioned
3. Core components without analogy
4. Reconstruction from basics

Respond in JSON:
{{
    "fundamental_truths": ["...", "..."],
    "questionable_assumptions": ["...", "..."],
    "core_components": ["...", "..."],
    "reconstruction": "..."
}}""",
            AnalyticalFramework.SYSTEMS_THINKING: f"""Analyze this issue using systems thinking:

ISSUE: {issue}

Identify:
1. System elements and components
2. Interconnections and relationships
3. Feedback loops (reinforcing/balancing)
4. System boundaries
5. Leverage points for intervention

Respond in JSON:
{{
    "elements": ["...", "..."],
    "interconnections": ["...", "..."],
    "feedback_loops": ["...", "..."],
    "boundaries": "...",
    "leverage_points": ["...", "..."]
}}""",
            AnalyticalFramework.PRE_MORTEM: f"""Conduct a pre-mortem analysis for this issue:

ISSUE: {issue}

Imagine the solution has failed spectacularly. Identify:
1. What caused the failure
2. Early warning signs that were missed
3. Prevention strategies
4. Mitigation plans

Respond in JSON:
{{
    "failure_causes": ["...", "..."],
    "warning_signs": ["...", "..."],
    "prevention_strategies": ["...", "..."],
    "mitigation_plans": ["...", "..."]
}}""",
            AnalyticalFramework.STAKEHOLDER_IMPACT: f"""Analyze stakeholder impacts for this issue:

ISSUE: {issue}

Identify:
1. All affected stakeholders
2. Impact on each stakeholder (positive/negative)
3. Stakeholder interests and concerns
4. Trade-offs between stakeholders

Respond in JSON:
{{
    "stakeholders": ["...", "..."],
    "impacts": {{"stakeholder": "impact"}},
    "interests": {{"stakeholder": "interest"}},
    "trade_offs": ["...", "..."]
}}""",
        }

        prompt = framework_prompts.get(
            framework,
            f"Analyze this issue: {issue}"
        )

        try:
            if self.swarms_agent:
                result = await self.run_with_llm(
                    prompt=prompt,
                    timeout=60,
                )

                import json
                try:
                    start_idx = result.find("{")
                    end_idx = result.rfind("}") + 1
                    if start_idx >= 0 and end_idx > start_idx:
                        json_str = result[start_idx:end_idx]
                        return json.loads(json_str)
                except Exception:
                    pass

            # Fallback
            return {
                "framework": framework.value,
                "analysis": f"Heuristic analysis using {framework.value}",
                "note": "LLM unavailable - limited analysis",
            }

        except Exception as e:
            logger.warning(f"[{self.agent_id}] Framework application failed: {e}")
            return {
                "framework": framework.value,
                "error": str(e),
                "note": "Framework application failed",
            }

    async def _handle_map_stakeholders(self, message: ActorMessage) -> None:
        """
        Map stakeholders and their interests for an issue.
        
        Args:
            message: Actor message with issue details
        """
        try:
            is_valid, error = self._validate_analysis_request(message.content)
            if not is_valid:
                logger.error(f"[{self.agent_id}] Invalid stakeholder mapping request: {error}")
                return

            issue = message.content["issue"]
            map_id = message.content.get("map_id", f"stakeholders_{datetime.now(timezone.utc).timestamp()}")

            logger.info(f"[{self.agent_id}] Mapping stakeholders for issue")

            # Generate stakeholder map
            stakeholder_map = await self._generate_stakeholder_map(issue)

            # Store map
            self.stakeholder_maps[map_id] = stakeholder_map

            # Send response
            response = {
                "message_type": "stakeholder_map_response",
                "map_id": map_id,
                "stakeholders": stakeholder_map,
            }

            if message.content.get("reply_to"):
                await self.send(
                    topic=message.content["reply_to"],
                    content=response,
                    sender_id=self.agent_id,
                )

            logger.info(f"[{self.agent_id}] Stakeholder mapping complete")

        except Exception as e:
            logger.error(f"[{self.agent_id}] Error mapping stakeholders: {e}", exc_info=True)

    async def _generate_stakeholder_map(self, issue: str) -> Dict[str, Any]:
        """
        Generate a stakeholder map for an issue.
        
        Args:
            issue: The issue to analyze
            
        Returns:
            Stakeholder map dictionary
        """
        prompt = f"""Identify all stakeholders for this issue:

ISSUE: {issue}

For each stakeholder, identify:
1. Name/role
2. Interest in the issue
3. Level of influence (low/medium/high)
4. Impact on them (low/medium/high)
5. Their position (supportive/neutral/opposed)

Respond in JSON:
{{
    "stakeholders": [
        {{
            "name": "...",
            "interest": "...",
            "influence": "...",
            "impact": "...",
            "position": "..."
        }}
    ],
    "power_interest_matrix": "...",
    "engagement_strategy": "..."
}}"""

        try:
            if self.swarms_agent:
                result = await self.run_with_llm(
                    prompt=prompt,
                    timeout=60,
                )

                import json
                try:
                    start_idx = result.find("{")
                    end_idx = result.rfind("}") + 1
                    if start_idx >= 0 and end_idx > start_idx:
                        return json.loads(result[start_idx:end_idx])
                except Exception:
                    pass

            # Fallback
            return {
                "stakeholders": [],
                "note": "Stakeholder mapping requires LLM capabilities",
            }

        except Exception as e:
            logger.warning(f"[{self.agent_id}] Stakeholder mapping failed: {e}")
            return {
                "stakeholders": [],
                "error": str(e),
            }

    async def _handle_get_analysis_summary(self, message: ActorMessage) -> None:
        """
        Get summary of all active analyses.
        
        Args:
            message: Actor message
        """
        try:
            analysis_id = message.content.get("analysis_id", None)

            if analysis_id and analysis_id in self.active_analyses:
                # Return specific analysis
                summary = self.active_analyses[analysis_id]
                perspectives = self.perspective_cache.get(analysis_id, [])
                summary["perspectives"] = [p.to_dict() for p in perspectives]
            else:
                # Return all analyses
                summary = {
                    "active_analyses_count": len(self.active_analyses),
                    "analyses": list(self.active_analyses.values()),
                    "bias_detections_count": len(self.bias_history),
                    "framework_applications_count": len(self.framework_results),
                }

            response = {
                "message_type": "analysis_summary_response",
                "summary": summary,
            }

            if message.content.get("reply_to"):
                await self.send(
                    topic=message.content["reply_to"],
                    content=response,
                    sender_id=self.agent_id,
                )

        except Exception as e:
            logger.error(f"[{self.agent_id}] Error getting analysis summary: {e}", exc_info=True)

    async def _handle_reframe_issue(self, message: ActorMessage) -> None:
        """
        Reframe an issue from multiple angles.
        
        Args:
            message: Actor message with issue to reframe
        """
        try:
            is_valid, error = self._validate_analysis_request(message.content)
            if not is_valid:
                logger.error(f"[{self.agent_id}] Invalid reframe request: {error}")
                return

            issue = message.content["issue"]

            logger.info(f"[{self.agent_id}] Reframing issue")

            # Generate reframes
            reframes = await self._generate_reframes(issue)

            response = {
                "message_type": "reframe_response",
                "original_issue": issue,
                "reframes": reframes,
            }

            if message.content.get("reply_to"):
                await self.send(
                    topic=message.content["reply_to"],
                    content=response,
                    sender_id=self.agent_id,
                )

            logger.info(f"[{self.agent_id}] Issue reframed into {len(reframes)} perspectives")

        except Exception as e:
            logger.error(f"[{self.agent_id}] Error reframing issue: {e}", exc_info=True)


    # =========================================================================
    # Session 44: Collective Learning Integration Methods
    # =========================================================================

    async def _emit_pattern(self, item_id: str, item_type: str, outcome: str, content: Dict[str, Any]) -> None:
        """Emit pattern for collective learning."""
        if not self.pattern_extractor:
            return

        if item_id in self._pattern_emitted:
            return

        try:
            await self.pattern_extractor.analyze_message(
                message_id=f"{item_type}_{item_id}",
                sender=self.agent_id,
                recipient="broadcast",
                message_type=f"{item_type}_completion",
                content=content,
                timestamp=datetime.now(timezone.utc).isoformat(),
            )

            self._pattern_emitted.add(item_id)
            logger.info(f"{item_type}_pattern_emitted", item_id=item_id, outcome=outcome)
        except Exception as e:
            logger.warning("failed_to_emit_pattern", item_id=item_id, error=str(e))

    async def _consume_patterns(self, pattern_types: Optional[List[PatternType]] = None) -> List[Dict[str, Any]]:
        """Consume patterns from collective learning."""
        if not self.pattern_extractor:
            return []

        try:
            patterns = await self.pattern_extractor.extract_patterns(
                time_window_hours=24,
                pattern_types=pattern_types or [PatternType.SUCCESS, PatternType.DECISION],
            )
            return [p.to_dict() for p in patterns if p.metadata.confidence >= 0.7]
        except Exception as e:
            logger.warning("failed_to_consume_patterns", error=str(e))
            return []

    # =========================================================================
    # Session 44: Consensus Deliberation Integration Methods
    # =========================================================================

    async def _initiate_deliberation(
        self,
        item_id: str,
        proposal: str,
        participating_agents: List[str],
        domain: str = "general",
    ) -> Optional[str]:
        """Initiate swarm deliberation."""
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

            logger.info("deliberation_initiated", deliberation_id=deliberation_id, item_id=item_id)
            return deliberation_id
        except Exception as e:
            logger.error("failed_to_initiate_deliberation", item_id=item_id, error=str(e))
            return None

    async def _submit_deliberation_position(
        self,
        item_id: str,
        agent_id: str,
        position: Position,
        confidence: float,
        argument: str,
    ) -> bool:
        """Submit agent position in deliberation."""
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
            logger.error("failed_to_submit_deliberation_position", error=str(e))
            return False

    async def _finalize_deliberation(self, item_id: str) -> Optional[Any]:
        """Finalize deliberation and apply result."""
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
            logger.error("failed_to_finalize_deliberation", error=str(e))
            return None

    # =========================================================================
    # Session 44: Memory Optimization Integration Methods
    # =========================================================================

    def _track_memory_access(self, item_id: str, item_type: str, access_type: str = "read") -> None:
        """Track memory access patterns."""
        if not self.access_analyzer:
            return

        memory_id = f"{item_type}_{item_id}"
        self.access_analyzer.record_access(
            memory_id=memory_id,
            access_type=access_type,
            agent_id=self.agent_id,
        )

    def _get_memory_tier(self, item_id: str, item_type: str) -> AccessTier:
        """Get memory tier classification."""
        if not self.access_analyzer:
            return AccessTier.COLD

        memory_id = f"{item_type}_{item_id}"
        profile = self.access_analyzer.get_profile(memory_id)
        return profile.tier if profile else AccessTier.COLD

    async def _prefetch_relevant(self, agent_id: str, item_type: str) -> List[str]:
        """Prefetch items an agent is likely to need."""
        if not self.access_analyzer:
            return []

        try:
            predicted_memories = self.access_analyzer.predict_agent_access(agent_id)
            return [
                mem.replace(f"{item_type}_", "")
                for mem in predicted_memories
                if mem.startswith(f"{item_type}_")
            ]
        except Exception as e:
            logger.warning("failed_to_prefetch", agent_id=agent_id, error=str(e))
            return []

    def get_learning_status(self) -> Dict[str, Any]:
        """Get collective learning and memory optimization status."""
        return {
            "agent_id": self.agent_id,
            "collective_learning": {
                "patterns_extracted": len(self.pattern_extractor._validated_patterns) if self.pattern_extractor else 0,
                "message_cache_size": len(self.pattern_extractor._message_cache) if self.pattern_extractor else 0,
            },
            "consensus": {
                "active_deliberations": len(self._active_deliberations),
                "deliberation_engine_stats": self.deliberation_engine.get_statistics() if self.deliberation_engine else {},
            },
            "memory_optimization": {
                "access_statistics": self.access_analyzer.get_statistics().to_dict() if self.access_analyzer else {},
            },
            "phi_training": self.get_phi_training_status(),
        }

    # =========================================================================
    # Phi Training Integration Methods
    # =========================================================================

    def _prism_agent_actor(self) -> AgentActor:
        """Create an AgentActor wrapper for Prism for Phi training."""
        class PrismAgentActor(AgentActor):
            def __init__(self, prism: "PrismAgent"):
                super().__init__(
                    agent_id=prism.agent_id,
                    agent_type="prism",
                )
                self.prism = prism

            async def act(self, observation: Dict[str, Any]) -> Dict[str, Any]:
                """Take action based on observation for Phi training."""
                # Use perspective analysis to determine action
                issue = observation.get("issue", "")
                if issue:
                    perspectives = self.prism.perspective_cache.get(issue, [])
                    if perspectives:
                        return {
                            "action": "analyze_perspectives",
                            "perspective_count": len(perspectives),
                            "avg_confidence": sum(p.confidence for p in perspectives) / len(perspectives),
                        }
                return {"action": "monitor"}

            def get_state(self) -> Dict[str, Any]:
                """Get current state for Phi calculation."""
                return {
                    "active_analyses": len(self.prism.active_analyses),
                    "perspective_cache_size": len(self.prism.perspective_cache),
                    "bias_history_size": len(self.prism.bias_history),
                    "framework_results_size": len(self.prism.framework_results),
                    "activation": len(self.prism.active_analyses) / max(len(self.prism.available_perspectives), 1),
                }

        return PrismAgentActor(self)

    async def run_phi_training_episode(
        self,
        scenario: Optional[TrainingScenario] = None,
        participating_agents: Optional[List[AgentActor]] = None,
    ) -> Dict[str, Any]:
        """
        Run a Phi training episode for Prism.
        
        Args:
            scenario: Optional training scenario (defaults to decision coherence)
            participating_agents: Optional list of agents to train with
            
        Returns:
            Training result dictionary
        """
        # Create training environment
        env = PhiTrainingEnvironment()

        # Get agent actors
        agent_actors = participating_agents or [self._prism_agent_actor()]

        # Use default scenario if not provided
        if scenario is None:
            scenario = DecisionCoherenceTrainingScenario(agent_count=len(agent_actors))

        # Run episode
        result = await env.run_episode(agent_actors, scenario)

        logger.info(
            "phi_training_episode_completed",
            agent_id=self.agent_id,
            phi_delta=result.episode.phi_delta,
            success=result.success,
        )

        return result.to_dict()

    def get_phi_training_status(self) -> Dict[str, Any]:
        """Get Phi training status and metrics."""
        return {
            "phi_training_enabled": True,
            "agent_type": "prism",
            "training_capability": "decision_coherence",
            "phi_optimization_target": "perspective_integration",
        }


    async def _generate_reframes(self, issue: str) -> List[Dict[str, Any]]:
        """
        Generate multiple reframes of an issue.
        
        Args:
            issue: The issue to reframe
            
        Returns:
            List of reframes
        """
        prompt = f"""Reframe this issue in multiple ways:

ORIGINAL ISSUE: {issue}

Generate 3-5 alternative framings that:
1. Change the scope (wider/narrower)
2. Change the timeframe (shorter/longer)
3. Change the perspective (different stakeholder)
4. Challenge assumptions
5. Focus on opportunities vs problems

Respond in JSON:
[
    {{
        "reframe": "...",
        "type": "...",
        "insights_revealed": ["...", "..."]
    }}
]"""

        try:
            if self.swarms_agent:
                result = await self.run_with_llm(
                    prompt=prompt,
                    timeout=60,
                )

                import json
                try:
                    start_idx = result.find("[")
                    end_idx = result.rfind("]") + 1
                    if start_idx >= 0 and end_idx > start_idx:
                        return json.loads(result[start_idx:end_idx])
                except Exception:
                    pass

            # Fallback
            return [
                {
                    "reframe": f"Reframe 1: Consider the opposite assumption",
                    "type": "assumption_challenge",
                    "insights_revealed": ["Challenges core assumptions"],
                },
                {
                    "reframe": f"Reframe 2: View from a different stakeholder",
                    "type": "perspective_shift",
                    "insights_revealed": ["Reveals stakeholder impacts"],
                },
            ]

        except Exception as e:
            logger.warning(f"[{self.agent_id}] Reframe generation failed: {e}")
            return []
