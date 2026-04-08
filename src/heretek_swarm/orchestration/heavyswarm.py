"""
HeavySwarm Workflow - 5-Phase Deliberation Pattern.

This module implements the HeavySwarm 5-phase workflow for complex analytical tasks:
1. Research Phase - Gather information and context
2. Analysis Phase - Analyze the problem from multiple perspectives
3. Alternatives Phase - Generate alternative solutions
4. Verification Phase - Verify and validate solutions
5. Decision Phase - Final decision with consensus

Based on the Swarms framework HeavySwarm pattern.
"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Tuple

from .phase_handlers import (
    PhaseHandler,
    PhaseHandlerRegistry,
    ResearchPhaseHandler,
    AnalysisPhaseHandler,
    AlternativesPhaseHandler,
    VerificationPhaseHandler,
    DecisionPhaseHandler,
)

import structlog

from heretek_swarm.actors.base import AgentActor
from heretek_swarm.consensus.maker import MAKERConsensus, ConsensusResult

from .phase_handlers import (
    PhaseHandlerRegistry,
    ResearchPhaseHandler,
    AnalysisPhaseHandler,
    AlternativesPhaseHandler,
    VerificationPhaseHandler,
    DecisionPhaseHandler,
)

logger = structlog.get_logger("HeavySwarmWorkflow")


class WorkflowPhase(Enum):
    """HeavySwarm workflow phases."""

    RESEARCH = "research"
    ANALYSIS = "analysis"
    ALTERNATIVES = "alternatives"
    VERIFICATION = "verification"
    DECISION = "decision"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class PhaseResult:
    """
    Result from a workflow phase.

    Attributes:
        phase: Phase identifier
        success: Whether phase succeeded
        output: Phase output data
        metadata: Additional metadata
        duration_ms: Phase duration in milliseconds
        errors: List of error messages
    """

    phase: WorkflowPhase
    success: bool
    output: Dict[str, Any]
    metadata: Dict[str, Any] = field(default_factory=dict)
    duration_ms: float = 0.0
    errors: List[str] = field(default_factory=list)


@dataclass
class WorkflowResult:
    """
    Complete workflow result.

    Attributes:
        workflow_id: Unique workflow identifier
        topic: Workflow topic/problem
        state: Final workflow state
        phase_results: Results from each phase
        final_decision: Final decision from consensus
        started_at: Workflow start timestamp
        completed_at: Workflow completion timestamp
        total_duration_ms: Total workflow duration
    """

    workflow_id: str
    topic: str
    state: WorkflowPhase
    phase_results: Dict[str, PhaseResult]
    final_decision: Optional[ConsensusResult] = None
    started_at: str = ""
    completed_at: str = ""
    total_duration_ms: float = 0.0


class HeavySwarmWorkflow:
    """
    HeavySwarm 5-Phase Deliberation Workflow.

    The HeavySwarm pattern provides comprehensive analysis through five
    distinct phases, ensuring thorough examination of complex problems
    before reaching a decision.

    Phases:
    1. **Research**: Gather information, context, and relevant history
    2. **Analysis**: Analyze the problem from multiple perspectives (Triad)
    3. **Alternatives**: Generate and evaluate alternative solutions
    4. **Verification**: Verify and validate proposed solutions
    5. **Decision**: Reach final decision through MAKER consensus

    Example:
        ```python
        workflow = HeavySwarmWorkflow(
            triad_agents=["alpha", "beta", "charlie"],
            historian="historian",
        )

        result = await workflow.execute(
            topic="Should we deploy to production?",
            context={"current_state": "staging", "tests_passed": True}
        )

        print(f"Decision: {result.final_decision.decision}")
        print(f"Confidence: {result.final_decision.confidence:.2f}")
        ```
    """

    def __init__(
        self,
        name: Optional[str] = None,
        triad_agents: Optional[List[str]] = None,
        historian: Optional[str] = None,
        steward: Optional[str] = None,
        consensus_engine: Optional[MAKERConsensus] = None,
        phase_timeout: float = 60.0,
        enable_parallel_phases: bool = True,
    ) -> None:
        """
        Initialize the HeavySwarm workflow.

        Args:
            name: Workflow name
            triad_agents: List of triad agent IDs (alpha, beta, charlie)
            historian: Historian agent ID
            steward: Steward agent ID
            consensus_engine: MAKER consensus engine instance
            phase_timeout: Timeout per phase in seconds
            enable_parallel_phases: Enable parallel phase execution where possible
        """
        self.name = name or "HeavySwarm"
        self.triad_agents = triad_agents or ["alpha", "beta", "charlie"]
        self.historian = historian or "historian"
        self.steward = steward or "steward"
        self.consensus_engine = consensus_engine or MAKERConsensus()
        self.phase_timeout = phase_timeout
        self.enable_parallel_phases = enable_parallel_phases

        # Agent references (set during execution)
        self.agents: Dict[str, AgentActor] = {}

        # Workflow state
        self.active_workflows: Dict[str, WorkflowResult] = {}
        self.workflow_history: List[WorkflowResult] = []

        # Phase handler registry
        self._phase_handlers = self._create_phase_handlers()

        logger.info(
            f"[{self.name}] HeavySwarm workflow initialized",
            extra={
                "triad_agents": self.triad_agents,
                "historian": self.historian,
                "steward": self.steward,
            },
        )

    def _create_phase_handlers(self) -> PhaseHandlerRegistry:
        """Create and register phase handlers"""
        registry = PhaseHandlerRegistry()
        # Note: Handlers are created lazily with agent references
        return registry

    def _get_phase_handler(self, phase: WorkflowPhase) -> Optional[PhaseHandler]:
        """Get or create a phase handler for the given phase"""
        if not self.agents:
            return None
        
        if phase == WorkflowPhase.RESEARCH:
            return ResearchPhaseHandler(self.historian, self.agents)
        elif phase == WorkflowPhase.ANALYSIS:
            return AnalysisPhaseHandler(self.triad_agents, self.agents)
        elif phase == WorkflowPhase.ALTERNATIVES:
            return AlternativesPhaseHandler(self.agents)
        elif phase == WorkflowPhase.VERIFICATION:
            return VerificationPhaseHandler(self.agents)
        elif phase == WorkflowPhase.DECISION:
            return DecisionPhaseHandler(self.triad_agents, self.agents, self.consensus_engine)
        return None

    def register_agent(self, agent_id: str, agent: AgentActor) -> None:
        """
        Register an agent for use in workflows.

        Args:
            agent_id: Agent identifier
            agent: Agent instance
        """
        self.agents[agent_id] = agent
        logger.debug(f"[{self.name}] Registered agent: {agent_id}")

    async def execute(
        self,
        topic: str,
        context: Optional[Dict[str, Any]] = None,
        workflow_id: Optional[str] = None,
    ) -> WorkflowResult:
        """
        Execute the complete 5-phase HeavySwarm workflow.

        Args:
            topic: Problem/topic to deliberate
            context: Additional context information
            workflow_id: Optional workflow identifier (auto-generated if None)

        Returns:
            Complete workflow result
        """
        workflow_id = workflow_id or self._generate_workflow_id()
        started_at = datetime.now(timezone.utc)

        logger.info(
            f"[{self.name}] Starting workflow {workflow_id}",
            extra={"topic": topic},
        )

        # Initialize workflow result
        result = WorkflowResult(
            workflow_id=workflow_id,
            topic=topic,
            state=WorkflowPhase.RESEARCH,
            phase_results={},
            started_at=started_at.isoformat(),
        )

        self.active_workflows[workflow_id] = result

        try:
            # Phase 1: Research
            research_result = await self._execute_phase(
                workflow_id,
                WorkflowPhase.RESEARCH,
                self._research_phase,
                topic,
                context,
            )
            result.phase_results["research"] = research_result

            if not research_result.success:
                raise WorkflowPhaseError(
                    f"Research phase failed: {research_result.errors}"
                )

            # Phase 2: Analysis
            result.state = WorkflowPhase.ANALYSIS
            analysis_result = await self._execute_phase(
                workflow_id,
                WorkflowPhase.ANALYSIS,
                self._analysis_phase,
                topic,
                context,
                research_result.output,
            )
            result.phase_results["analysis"] = analysis_result

            if not analysis_result.success:
                raise WorkflowPhaseError(
                    f"Analysis phase failed: {analysis_result.errors}"
                )

            # Phase 3: Alternatives
            result.state = WorkflowPhase.ALTERNATIVES
            alternatives_result = await self._execute_phase(
                workflow_id,
                WorkflowPhase.ALTERNATIVES,
                self._alternatives_phase,
                topic,
                context,
                analysis_result.output,
            )
            result.phase_results["alternatives"] = alternatives_result

            if not alternatives_result.success:
                raise WorkflowPhaseError(
                    f"Alternatives phase failed: {alternatives_result.errors}"
                )

            # Phase 4: Verification
            result.state = WorkflowPhase.VERIFICATION
            verification_result = await self._execute_phase(
                workflow_id,
                WorkflowPhase.VERIFICATION,
                self._verification_phase,
                topic,
                context,
                alternatives_result.output,
            )
            result.phase_results["verification"] = verification_result

            if not verification_result.success:
                raise WorkflowPhaseError(
                    f"Verification phase failed: {verification_result.errors}"
                )

            # Phase 5: Decision
            result.state = WorkflowPhase.DECISION
            decision_result = await self._execute_phase(
                workflow_id,
                WorkflowPhase.DECISION,
                self._decision_phase,
                topic,
                context,
                verification_result.output,
            )
            result.phase_results["decision"] = decision_result

            if not decision_result.success:
                raise WorkflowPhaseError(
                    f"Decision phase failed: {decision_result.errors}"
                )

            # Set final decision
            result.final_decision = decision_result.output.get("consensus_result")
            result.state = WorkflowPhase.COMPLETED

        except WorkflowPhaseError as e:
            logger.error(f"[{self.name}] Workflow failed: {e}")
            result.state = WorkflowPhase.FAILED
            result.errors = [str(e)]

        except Exception as e:
            logger.error(f"[{self.name}] Workflow error: {e}", exc_info=True)
            result.state = WorkflowPhase.FAILED
            result.errors = [str(e)]

        finally:
            # Finalize
            completed_at = datetime.now(timezone.utc)
            result.completed_at = completed_at.isoformat()
            result.total_duration_ms = (
                completed_at - started_at
            ).total_seconds() * 1000

            # Move to history
            if workflow_id in self.active_workflows:
                del self.active_workflows[workflow_id]
            self.workflow_history.append(result)

            logger.info(
                f"[{self.name}] Workflow {workflow_id} completed",
                extra={
                    "state": result.state.value,
                    "duration_ms": result.total_duration_ms,
                },
            )

        return result

    async def _execute_phase(
        self,
        workflow_id: str,
        phase: WorkflowPhase,
        phase_func: Callable,
        *args: Any,
        **kwargs: Any,
    ) -> PhaseResult:
        """
        Execute a single workflow phase with timeout.

        Args:
            workflow_id: Workflow identifier
            phase: Phase identifier
            phase_func: Phase function to execute
            *args: Arguments for phase function
            **kwargs: Keyword arguments for phase function

        Returns:
            Phase result
        """
        started_at = datetime.now(timezone.utc)
        logger.info(f"[{self.name}] Executing phase: {phase.value}")

        try:
            # Execute with timeout
            output = await asyncio.wait_for(
                phase_func(workflow_id, *args, **kwargs),
                timeout=self.phase_timeout,
            )

            duration_ms = (datetime.now(timezone.utc) - started_at).total_seconds() * 1000

            return PhaseResult(
                phase=phase,
                success=True,
                output=output,
                duration_ms=duration_ms,
            )

        except asyncio.TimeoutError:
            duration_ms = (datetime.now(timezone.utc) - started_at).total_seconds() * 1000
            error_msg = f"Phase {phase.value} timed out after {self.phase_timeout}s"

            return PhaseResult(
                phase=phase,
                success=False,
                output={},
                duration_ms=duration_ms,
                errors=[error_msg],
            )

        except Exception as e:
            duration_ms = (datetime.now(timezone.utc) - started_at).total_seconds() * 1000

            return PhaseResult(
                phase=phase,
                success=False,
                output={},
                duration_ms=duration_ms,
                errors=[str(e)],
            )

    # =========================================================================
    # Phase 1: Research
    # =========================================================================

    async def _research_phase(
        self,
        workflow_id: str,
        topic: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Phase 1: Research - Gather information and context.

        This phase:
        - Queries historian for relevant historical context
        - Gathers available information about the topic
        - Identifies key facts and constraints
        - Prepares research summary for analysis phase

        Args:
            workflow_id: Workflow identifier
            topic: Problem/topic to research
            context: Additional context

        Returns:
            Research summary with gathered information
        """
        logger.info(f"[{self.name}] Research phase: Gathering information")

        research_data = {
            "topic": topic,
            "context": context or {},
            "historical_context": [],
            "relevant_facts": [],
            "constraints": [],
            "assumptions": [],
        }

        # Query historian for context
        if self.historian in self.agents:
            historian_agent = self.agents[self.historian]
            try:
                deliberation_context = await historian_agent.provide_deliberation_context(
                    deliberation_id=workflow_id,
                    topic=topic,
                )
                research_data["historical_context"] = deliberation_context.get(
                    "relevant_memories", []
                )
                research_data["matched_patterns"] = deliberation_context.get(
                    "matched_patterns", []
                )
            except Exception as e:
                logger.warning(f"[{self.name}] Historian query failed: {e}")

        # Synthesize knowledge if historian available
        if self.historian in self.agents:
            historian_agent = self.agents[self.historian]
            try:
                knowledge = await historian_agent.synthesize_knowledge(
                    topic=topic,
                    limit=10,
                )
                research_data["knowledge_summary"] = knowledge.get("summary", "")
            except Exception as e:
                logger.warning(f"[{self.name}] Knowledge synthesis failed: {e}")

        # Identify constraints and assumptions from context
        if context:
            research_data["constraints"] = context.get("constraints", [])
            research_data["assumptions"] = context.get("assumptions", [])

        logger.info(
            f"[{self.name}] Research phase complete",
            extra={
                "historical_context_count": len(research_data["historical_context"]),
                "constraints_count": len(research_data["constraints"]),
            },
        )

        return research_data

    # =========================================================================
    # Phase 2: Analysis
    # =========================================================================

    async def _analysis_phase(
        self,
        workflow_id: str,
        topic: str,
        context: Optional[Dict[str, Any]] = None,
        research_data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Phase 2: Analysis - Analyze from multiple perspectives.

        This phase:
        - Distributes analysis to triad members (Alpha, Beta, Charlie)
        - Alpha provides primary analysis
        - Beta provides secondary/validation perspective
        - Charlie provides critical challenge perspective
        - Aggregates all perspectives

        Args:
            workflow_id: Workflow identifier
            topic: Problem/topic to analyze
            context: Additional context
            research_data: Output from research phase

        Returns:
            Analysis results from all triad perspectives
        """
        logger.info(f"[{self.name}] Analysis phase: Multi-perspective analysis")

        analysis_data = {
            "topic": topic,
            "research_summary": research_data,
            "alpha_analysis": None,
            "beta_analysis": None,
            "charlie_analysis": None,
            "perspectives": [],
            "key_insights": [],
            "disagreements": [],
        }

        # Collect analysis from each triad member
        triad_analyses = await self._collect_triad_analyses(
            workflow_id=workflow_id,
            topic=topic,
            research_data=research_data,
            analysis_type="deep_analysis",
        )

        analysis_data["alpha_analysis"] = triad_analyses.get("alpha")
        analysis_data["beta_analysis"] = triad_analyses.get("beta")
        analysis_data["charlie_analysis"] = triad_analyses.get("charlie")
        analysis_data["perspectives"] = list(triad_analyses.values())

        # Identify key insights
        for agent_id, analysis in triad_analyses.items():
            if analysis:
                insights = analysis.get("insights", [])
                analysis_data["key_insights"].extend(insights)

        # Identify disagreements
        decisions = [
            a.get("decision")
            for a in triad_analyses.values()
            if a and a.get("decision")
        ]
        if len(set(decisions)) > 1:
            analysis_data["disagreements"].append(
                f"Triad disagreement on initial analysis: {decisions}"
            )

        logger.info(
            f"[{self.name}] Analysis phase complete",
            extra={
                "perspectives_count": len(analysis_data["perspectives"]),
                "insights_count": len(analysis_data["key_insights"]),
                "disagreements_count": len(analysis_data["disagreements"]),
            },
        )

        return analysis_data

    async def _collect_triad_analyses(
        self,
        workflow_id: str,
        topic: str,
        research_data: Dict[str, Any],
        analysis_type: str = "deep_analysis",
    ) -> Dict[str, Dict[str, Any]]:
        """
        Collect analyses from all triad members.

        Args:
            workflow_id: Workflow identifier
            topic: Problem/topic
            research_data: Research phase output
            analysis_type: Type of analysis requested

        Returns:
            Dictionary of agent_id -> analysis results
        """
        analyses = {}

        for agent_id in self.triad_agents:
            if agent_id not in self.agents:
                logger.warning(f"[{self.name}] Triad agent not found: {agent_id}")
                continue

            agent = self.agents[agent_id]

            try:
                # Send analysis request
                await agent.send_to_actor(
                    target_actor_id=agent_id,
                    message_type="analysis_request",
                    content={
                        "workflow_id": workflow_id,
                        "topic": topic,
                        "research_data": research_data,
                        "analysis_type": analysis_type,
                    },
                )

                # For now, use placeholder analysis
                # In full implementation, would wait for agent response
                analyses[agent_id] = {
                    "agent_id": agent_id,
                    "decision": f"{agent_id}_analysis_complete",
                    "confidence": 0.8,
                    "insights": [
                        f"Key insight from {agent_id}",
                        "Analysis based on research data",
                    ],
                    "reasoning": f"Analysis by {agent_id}",
                }

            except Exception as e:
                logger.error(
                    f"[{self.name}] Error collecting analysis from {agent_id}: {e}"
                )
                analyses[agent_id] = {
                    "agent_id": agent_id,
                    "decision": "analysis_failed",
                    "confidence": 0.0,
                    "insights": [],
                    "reasoning": f"Error: {e}",
                }

        return analyses

    # =========================================================================
    # Phase 3: Alternatives
    # =========================================================================

    async def _alternatives_phase(
        self,
        workflow_id: str,
        topic: str,
        context: Optional[Dict[str, Any]] = None,
        analysis_data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Phase 3: Alternatives - Generate and evaluate solutions.

        This phase:
        - Generates multiple alternative solutions
        - Evaluates each alternative against criteria
        - Ranks alternatives by feasibility and impact
        - Identifies trade-offs

        Args:
            workflow_id: Workflow identifier
            topic: Problem/topic
            context: Additional context
            analysis_data: Output from analysis phase

        Returns:
            Alternatives evaluation with rankings
        """
        logger.info(f"[{self.name}] Alternatives phase: Generating solutions")

        alternatives_data = {
            "topic": topic,
            "analysis_summary": analysis_data,
            "alternatives": [],
            "evaluation_criteria": [
                "feasibility",
                "impact",
                "risk",
                "cost",
                "time_to_implement",
            ],
            "recommended_alternative": None,
            "trade_offs": [],
        }

        # Generate alternatives (would use LLM in full implementation)
        alternatives = await self._generate_alternatives(
            topic=topic,
            analysis_data=analysis_data,
        )
        alternatives_data["alternatives"] = alternatives

        # Evaluate each alternative
        for alt in alternatives:
            evaluation = await self._evaluate_alternative(alt, analysis_data)
            alt["evaluation"] = evaluation

        # Rank alternatives
        ranked = sorted(
            alternatives,
            key=lambda x: x.get("evaluation", {}).get("total_score", 0),
            reverse=True,
        )

        if ranked:
            alternatives_data["recommended_alternative"] = ranked[0]
            alternatives_data["alternatives"] = ranked

        # Identify trade-offs
        alternatives_data["trade_offs"] = await self._identify_trade_offs(ranked)

        logger.info(
            f"[{self.name}] Alternatives phase complete",
            extra={
                "alternatives_count": len(alternatives),
                "recommended": alternatives_data["recommended_alternative"].get(
                    "id" if alternatives_data["recommended_alternative"] else "name",
                    "none",
                ),
            },
        )

        return alternatives_data

    async def _generate_alternatives(
        self,
        topic: str,
        analysis_data: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """Generate alternative solutions."""
        # Placeholder - would use LLM in full implementation
        alternatives = [
            {
                "id": "alt_1",
                "name": "Conservative Approach",
                "description": "Minimal change, low risk",
                "type": "conservative",
            },
            {
                "id": "alt_2",
                "name": "Balanced Approach",
                "description": "Moderate change, balanced risk/reward",
                "type": "balanced",
            },
            {
                "id": "alt_3",
                "name": "Aggressive Approach",
                "description": "Significant change, high risk/reward",
                "type": "aggressive",
            },
        ]
        return alternatives

    async def _evaluate_alternative(
        self,
        alternative: Dict[str, Any],
        analysis_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Evaluate a single alternative."""
        # Placeholder scoring
        return {
            "feasibility": 0.8,
            "impact": 0.7,
            "risk": 0.3,
            "cost": 0.5,
            "time_to_implement": 0.6,
            "total_score": 0.58,
        }

    async def _identify_trade_offs(
        self,
        alternatives: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """Identify trade-offs between alternatives."""
        if len(alternatives) < 2:
            return []

        trade_offs = []
        for i, alt1 in enumerate(alternatives[:-1]):
            for alt2 in alternatives[i + 1 :]:
                trade_offs.append({
                    "alternative_1": alt1.get("name", "unknown"),
                    "alternative_2": alt2.get("name", "unknown"),
                    "trade_off": "Different risk/reward profiles",
                })

        return trade_offs

    # =========================================================================
    # Phase 4: Verification
    # =========================================================================

    async def _verification_phase(
        self,
        workflow_id: str,
        topic: str,
        context: Optional[Dict[str, Any]] = None,
        alternatives_data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Phase 4: Verification - Verify and validate solutions.

        This phase:
        - Validates the recommended alternative
        - Checks for edge cases and failure modes
        - Verifies assumptions
        - Beta performs error detection
        - Charlie performs risk assessment

        Args:
            workflow_id: Workflow identifier
            topic: Problem/topic
            context: Additional context
            alternatives_data: Output from alternatives phase

        Returns:
            Verification results with validation status
        """
        logger.info(f"[{self.name}] Verification phase: Validating solutions")

        verification_data = {
            "topic": topic,
            "recommended_alternative": alternatives_data.get(
                "recommended_alternative", {}
            ),
            "validation_results": [],
            "error_checks": [],
            "risk_assessments": [],
            "edge_cases": [],
            "overall_valid": True,
            "confidence": 0.0,
        }

        recommended = alternatives_data.get("recommended_alternative")

        if not recommended:
            verification_data["overall_valid"] = False
            verification_data["errors"] = ["No recommended alternative to verify"]
            return verification_data

        # Beta: Error detection
        if "beta" in self.agents:
            beta_agent = self.agents["beta"]
            try:
                errors = await beta_agent._detect_errors(recommended)
                verification_data["error_checks"] = errors
                if errors:
                    verification_data["overall_valid"] = False
            except Exception as e:
                logger.warning(f"[{self.name}] Beta error check failed: {e}")

        # Charlie: Risk assessment
        if "charlie" in self.agents:
            charlie_agent = self.agents["charlie"]
            try:
                risk_assessment = await charlie_agent._assess_risks(recommended)
                verification_data["risk_assessments"] = risk_assessment.get(
                    "risks_identified", []
                )
                verification_data["risk_level"] = risk_assessment.get(
                    "risk_level", "unknown"
                )
            except Exception as e:
                logger.warning(f"[{self.name}] Charlie risk assessment failed: {e}")

        # Calculate overall confidence
        error_count = len(verification_data["error_checks"])
        risk_count = len(verification_data["risk_assessments"])

        base_confidence = recommended.get("evaluation", {}).get("total_score", 0.5)
        penalty = (error_count * 0.1) + (risk_count * 0.05)
        verification_data["confidence"] = max(0.0, base_confidence - penalty)

        logger.info(
            f"[{self.name}] Verification phase complete",
            extra={
                "overall_valid": verification_data["overall_valid"],
                "confidence": verification_data["confidence"],
                "errors_found": error_count,
                "risks_identified": risk_count,
            },
        )

        return verification_data

    # =========================================================================
    # Phase 5: Decision
    # =========================================================================

    async def _decision_phase(
        self,
        workflow_id: str,
        topic: str,
        context: Optional[Dict[str, Any]] = None,
        verification_data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Phase 5: Decision - Reach final decision through consensus.

        This phase:
        - Initiates MAKER consensus process
        - Triad members cast weighted votes
        - First-to-ahead-by-k voting determines winner
        - Red-flagging for anomalous outputs
        - Returns final consensus result

        Args:
            workflow_id: Workflow identifier
            topic: Problem/topic
            context: Additional context
            verification_data: Output from verification phase

        Returns:
            Decision results with consensus outcome
        """
        logger.info(f"[{self.name}] Decision phase: Running consensus")

        consensus_id = f"consensus_{workflow_id}"

        # Start consensus process
        self.consensus_engine.start_consensus(consensus_id)

        # Collect votes from triad
        votes = await self._collect_triad_votes(
            consensus_id=consensus_id,
            topic=topic,
            verification_data=verification_data,
        )

        # Compute consensus
        consensus_result = self.consensus_engine.compute_consensus(consensus_id)

        # Cleanup
        self.consensus_engine.cleanup_process(consensus_id)

        decision_data = {
            "topic": topic,
            "consensus_id": consensus_id,
            "consensus_result": consensus_result,
            "votes": votes,
            "recommended_action": None,
            "confidence": 0.0,
        }

        if consensus_result:
            decision_data["recommended_action"] = consensus_result.decision
            decision_data["confidence"] = consensus_result.confidence
            decision_data["red_flags"] = consensus_result.red_flags

        logger.info(
            f"[{self.name}] Decision phase complete",
            extra={
                "decision": decision_data.get("recommended_action"),
                "confidence": decision_data.get("confidence"),
                "red_flags": len(decision_data.get("red_flags", [])),
            },
        )

        return decision_data

    async def _collect_triad_votes(
        self,
        consensus_id: str,
        topic: str,
        verification_data: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """
        Collect votes from triad members.

        Args:
            consensus_id: Consensus process identifier
            topic: Problem/topic
            verification_data: Verification phase output

        Returns:
            List of votes
        """
        votes = []

        for agent_id in self.triad_agents:
            if agent_id not in self.agents:
                continue

            agent = self.agents[agent_id]

            # Simulate vote (would be real agent vote in full implementation)
            vote = {
                "agent_id": agent_id,
                "decision": verification_data.get("recommended_alternative", {}).get(
                    "name", "unknown"
                ),
                "confidence": 0.8,
            }

            # Add to consensus engine
            self.consensus_engine.add_vote(
                consensus_id=consensus_id,
                agent_id=agent_id,
                decision=vote["decision"],
                confidence=vote["confidence"],
            )

            votes.append(vote)

        return votes

    def _generate_workflow_id(self) -> str:
        """Generate a unique workflow identifier."""
        import uuid

        return f"workflow_{uuid.uuid4().hex[:12]}"

    def get_workflow_status(self, workflow_id: str) -> Optional[WorkflowResult]:
        """
        Get status of a workflow.

        Args:
            workflow_id: Workflow identifier

        Returns:
            Workflow result or None
        """
        # Check active workflows
        if workflow_id in self.active_workflows:
            return self.active_workflows[workflow_id]

        # Check history
        for workflow in self.workflow_history:
            if workflow.workflow_id == workflow_id:
                return workflow

        return None

    def get_statistics(self) -> Dict[str, Any]:
        """Get workflow statistics."""
        total_workflows = len(self.workflow_history)
        completed = sum(
            1 for w in self.workflow_history if w.state == WorkflowPhase.COMPLETED
        )
        failed = sum(
            1 for w in self.workflow_history if w.state == WorkflowPhase.FAILED
        )

        avg_duration = (
            sum(w.total_duration_ms for w in self.workflow_history) / total_workflows
            if total_workflows > 0
            else 0.0
        )

        return {
            "total_workflows": total_workflows,
            "completed": completed,
            "failed": failed,
            "success_rate": completed / total_workflows if total_workflows > 0 else 0.0,
            "average_duration_ms": avg_duration,
            "active_workflows": len(self.active_workflows),
        }


class WorkflowPhaseError(Exception):
    """Exception raised when a workflow phase fails."""

    pass
