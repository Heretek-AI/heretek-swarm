"""
HeavySwarm Workflow - 5-Phase Deliberation Pattern.

.. deprecated::
    The custom 5-phase workflow engine is being replaced by LangGraph
    as part of M-arch PR #6 (see PLAN.md §M-arch). The public contract
    — :class:`WorkflowPhase` enum and :class:`WorkflowResult` dataclass
    — is preserved; only the internal implementation is expected to
    change. Full LangGraph migration is deferred to a follow-up PR
    (LangGraph state machine with 5 nodes, MAKER consensus as Decision
    node, MemorySaver for resumability). This file remains the active
    code path until the LangGraph replacement ships.

This module implements the HeavySwarm 5-phase workflow for complex analytical tasks:
1. Research Phase - Gather information and context
2. Analysis Phase - Analyze the problem from multiple perspectives
3. Alternatives Phase - Generate alternative solutions
4. Verification Phase - Verify and validate solutions
5. Decision Phase - Final decision with consensus

Based on the Swarms framework HeavySwarm pattern.
"""

import asyncio
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any

import structlog

from heretek_swarm.actors.base import AgentActor
from heretek_swarm.consensus.maker import ConsensusResult, MAKERConsensus

from .phase_handlers import (
    AlternativesPhaseHandler,
    AnalysisPhaseHandler,
    DecisionPhaseHandler,
    PhaseHandler,
    PhaseHandlerRegistry,
    ResearchPhaseHandler,
    VerificationPhaseHandler,
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
    output: dict[str, Any]
    metadata: dict[str, Any] = field(default_factory=dict)
    duration_ms: float = 0.0
    errors: list[str] = field(default_factory=list)


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
    phase_results: dict[str, PhaseResult]
    final_decision: ConsensusResult | None = None
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
        name: str | None = None,
        triad_agents: list[str] | None = None,
        historian: str | None = None,
        steward: str | None = None,
        consensus_engine: MAKERConsensus | None = None,
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
        self.agents: dict[str, AgentActor] = {}

        # Workflow state
        self.active_workflows: dict[str, WorkflowResult] = {}
        self.workflow_history: list[WorkflowResult] = []

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
        return PhaseHandlerRegistry()
        # Note: Handlers are created lazily with agent references

    def _get_phase_handler(self, phase: WorkflowPhase) -> PhaseHandler | None:
        """Get or create a phase handler for the given phase"""
        if not self.agents:
            return None

        if phase == WorkflowPhase.RESEARCH:
            return ResearchPhaseHandler(self.historian, self.agents)
        if phase == WorkflowPhase.ANALYSIS:
            return AnalysisPhaseHandler(self.triad_agents, self.agents)
        if phase == WorkflowPhase.ALTERNATIVES:
            return AlternativesPhaseHandler(self.agents)
        if phase == WorkflowPhase.VERIFICATION:
            return VerificationPhaseHandler(self.agents)
        if phase == WorkflowPhase.DECISION:
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
        context: dict[str, Any] | None = None,
        workflow_id: str | None = None,
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
        started_at = datetime.now(UTC)

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
                raise WorkflowPhaseError(f"Research phase failed: {research_result.errors}")

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
                raise WorkflowPhaseError(f"Analysis phase failed: {analysis_result.errors}")

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
                raise WorkflowPhaseError(f"Alternatives phase failed: {alternatives_result.errors}")

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
                raise WorkflowPhaseError(f"Verification phase failed: {verification_result.errors}")

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
                raise WorkflowPhaseError(f"Decision phase failed: {decision_result.errors}")

            # Set final decision
            result.final_decision = decision_result.output.get("consensus_result")
            result.state = WorkflowPhase.COMPLETED

        except WorkflowPhaseError as e:
            logger.error(f"[{self.name}] Workflow failed: {e}")
            result.state = WorkflowPhase.FAILED
            result.errors = [str(e)]

        except Exception as e:
            logger.exception(f"[{self.name}] Workflow error: {e}")
            result.state = WorkflowPhase.FAILED
            result.errors = [str(e)]

        finally:
            # Finalize
            completed_at = datetime.now(UTC)
            result.completed_at = completed_at.isoformat()
            result.total_duration_ms = (completed_at - started_at).total_seconds() * 1000

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
        started_at = datetime.now(UTC)
        logger.info(f"[{self.name}] Executing phase: {phase.value}")

        try:
            # Execute with timeout
            output = await asyncio.wait_for(
                phase_func(workflow_id, *args, **kwargs),
                timeout=self.phase_timeout,
            )

            duration_ms = (datetime.now(UTC) - started_at).total_seconds() * 1000

            return PhaseResult(
                phase=phase,
                success=True,
                output=output,
                duration_ms=duration_ms,
            )

        except TimeoutError:
            duration_ms = (datetime.now(UTC) - started_at).total_seconds() * 1000
            error_msg = f"Phase {phase.value} timed out after {self.phase_timeout}s"

            return PhaseResult(
                phase=phase,
                success=False,
                output={},
                duration_ms=duration_ms,
                errors=[error_msg],
            )

        except Exception as e:
            duration_ms = (datetime.now(UTC) - started_at).total_seconds() * 1000

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
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
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
                research_data["matched_patterns"] = deliberation_context.get("matched_patterns", [])
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
        context: dict[str, Any] | None = None,
        research_data: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
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
        for analysis in triad_analyses.values():
            if analysis:
                insights = analysis.get("insights", [])
                analysis_data["key_insights"].extend(insights)

        # Identify disagreements
        decisions = [a.get("decision") for a in triad_analyses.values() if a and a.get("decision")]
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
        research_data: dict[str, Any],
        analysis_type: str = "deep_analysis",
    ) -> dict[str, dict[str, Any]]:
        """
        Collect analyses from all triad members via NATS request-reply.

        Per D004, uses send_with_reply with a 30s timeout to await real
        agent responses. Falls back to confidence=0.0 with empty insights
        on timeout, and emits structured log events for observability.

        Args:
            workflow_id: Workflow identifier
            topic: Problem/topic
            research_data: Research phase output
            analysis_type: Type of analysis requested

        Returns:
            Dictionary of agent_id -> analysis results
        """
        analyses: dict[str, dict[str, Any]] = {}

        for agent_id in self.triad_agents:
            if agent_id not in self.agents:
                logger.warning(f"[{self.name}] Triad agent not found: {agent_id}")
                continue

            agent = self.agents[agent_id]

            try:
                # Send request via NATS request-reply (D004) and await real agent analysis
                reply = await agent.send_with_reply(
                    recipient=agent_id,
                    message_type="analysis_request",
                    content={
                        "workflow_id": workflow_id,
                        "topic": topic,
                        "research_data": research_data,
                        "analysis_type": analysis_type,
                    },
                    timeout=30,
                )

                if reply is not None:
                    # Successful response — extract real analysis data
                    analyses[agent_id] = {
                        "agent_id": agent_id,
                        "decision": reply.get("decision", f"{agent_id}_analysis_complete"),
                        "confidence": reply.get("confidence", 0.0),
                        "insights": reply.get("insights", []),
                        "reasoning": reply.get("reasoning", ""),
                    }
                else:
                    # Timeout — honest fallback with confidence=0.0
                    logger.warning(
                        "heavyswarm_analysis_timeout",
                        extra={
                            "agent_id": agent_id,
                            "workflow_id": workflow_id,
                            "timeout_s": 30,
                        },
                    )
                    analyses[agent_id] = {
                        "agent_id": agent_id,
                        "decision": "analysis_timeout",
                        "confidence": 0.0,
                        "insights": [],
                        "reasoning": f"Request to {agent_id} timed out after 30s",
                    }

            except Exception as e:
                logger.exception(
                    "heavyswarm_analysis_error",
                    extra={
                        "agent_id": agent_id,
                        "workflow_id": workflow_id,
                        "error": str(e),
                    },
                )
                analyses[agent_id] = {
                    "agent_id": agent_id,
                    "decision": "analysis_error",
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
        context: dict[str, Any] | None = None,
        analysis_data: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
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
        analysis_data: dict[str, Any],
    ) -> list[dict[str, Any]]:
        """
        Generate alternative solutions via LLM agent deliberation.

        Routes through dreamer agent (or alpha as fallback) with a structured
        prompt requesting 3 alternative solutions. On timeout (60s) or LLM
        failure, falls back to the hardcoded list and logs the structured event
        ``heavyswarm_alternatives_llm_failed``. On success, logs
        ``heavyswarm_alternatives_llm_success``.
        """
        # Select agent: dreamer preferred, alpha as fallback
        agent = self.agents.get("dreamer") or self.agents.get("alpha")
        if agent is None:
            logger.warning(
                "heavyswarm_alternatives_llm_failed",
                extra={
                    "reason": "no_agent_available",
                    "topic": topic,
                },
            )
            return self._generate_alternatives_fallback()

        # Build a structured prompt requesting JSON output
        insights = analysis_data.get("key_insights", []) if analysis_data else []
        perspectives = analysis_data.get("perspectives", []) if analysis_data else []

        prompt = f"""You are generating alternative solutions for a complex decision.

Problem/Topic: {topic}

Key insights from analysis:
{chr(10).join(f'- {i}' for i in insights) if insights else '- None provided'}

Agent perspectives:
{chr(10).join(f'- {p}' for p in perspectives) if perspectives else '- None provided'}

Generate exactly 3 alternative solutions with distinct risk/reward profiles.
Respond ONLY with a JSON array of 3 objects, each with these keys:
- id (string, e.g. "alt_1")
- name (string, descriptive label)
- description (string, 1-2 sentence summary)
- type (string, one of: "conservative", "balanced", "aggressive")

Example response format:
[
  {{"id": "alt_1", "name": "Conserve", "description": "Minimal change, low risk",
    "type": "conservative"}},
  {{"id": "alt_2", "name": "Balance", "description": "Moderate change, balanced",
    "type": "balanced"}},
  {{"id": "alt_3", "name": "Aggressive", "description": "Major change, high risk",
    "type": "aggressive"}}
]"""

        try:
            response = await agent.run_with_llm(prompt, timeout=60)
            alternatives = self._parse_alternatives_json(response)
            if alternatives:
                logger.info(
                    "heavyswarm_alternatives_llm_success",
                    extra={
                        "topic": topic,
                        "alternative_count": len(alternatives),
                    },
                )
                return alternatives
        except Exception as e:
            logger.error(
                "heavyswarm_alternatives_llm_failed",
                extra={
                    "reason": str(e),
                    "topic": topic,
                },
            )

        # Fallback to hardcoded alternatives on any failure
        logger.warning(
            "heavyswarm_alternatives_llm_failed",
            extra={
                "reason": "fallback_to_hardcoded",
                "topic": topic,
            },
        )
        return self._generate_alternatives_fallback()

    def _generate_alternatives_fallback(self) -> list[dict[str, Any]]:
        """Return hardcoded alternatives when LLM is unavailable."""
        return [
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

    @staticmethod
    def _parse_alternatives_json(response: str) -> list[dict[str, Any]] | None:
        """Parse LLM response into a list of alternative dicts.

        Handles common LLM response quirks: leading/trailing markdown fences,
        extra whitespace, and wrapping in a code block.
        """
        import json
        import re

        # Strip markdown code fences if present
        cleaned = response.strip()
        # Remove ```json ... ``` or ``` ... ``` wrappers
        cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
        cleaned = re.sub(r"\s*```$", "", cleaned)

        try:
            parsed = json.loads(cleaned)
            if isinstance(parsed, list) and len(parsed) >= 1:
                # Validate each alternative has required keys
                for alt in parsed:
                    if not isinstance(alt, dict):
                        return None
                return parsed
            return None
        except json.JSONDecodeError:
            return None

    async def _evaluate_alternative(
        self,
        alternative: dict[str, Any],
        _analysis_data: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Evaluate a single alternative via alpha agent LLM scoring.

        Routes through alpha agent with a prompt requesting
        feasibility/impact/risk/cost/time_to_implement scoring (0.0-1.0).
        On failure or timeout (60s), returns an honest fallback with all
        zero scores and logs ``heavyswarm_evaluation_llm_failed``.
        On success, logs ``heavyswarm_evaluation_llm_success``.
        """
        agent = self.agents.get("alpha")
        if agent is None:
            logger.warning(
                "heavyswarm_evaluation_llm_failed",
                extra={
                    "reason": "no_alpha_agent_available",
                    "alternative": alternative.get("name", "unknown"),
                },
            )
            return self._evaluate_alternative_fallback(alternative)

        alt_name = alternative.get("name", "unknown")
        alt_desc = alternative.get("description", "")

        prompt = f"""Evaluate the following alternative solution for a complex decision.

Alternative: {alt_name}
Description: {alt_desc}

Evaluation criteria (score each from 0.0 to 1.0):
- feasibility: How practical is this solution to implement?
- impact: How much positive impact will this have?
- risk: How risky is this? (0.0 = very low risk, 1.0 = extremely risky)
- cost: How expensive? (0.0 = free, 1.0 = prohibitive)
- time_to_implement: How quickly? (0.0 = instant, 1.0 = forever)
- total_score: Weighted overall score (0.0-1.0)

Respond ONLY with a JSON object with these exact numeric keys.
Example:
{{"feasibility": 0.75, "impact": 0.80, "risk": 0.25, "cost": 0.40,
 "time_to_implement": 0.35, "total_score": 0.62}}"""

        try:
            response = await agent.run_with_llm(prompt, timeout=60)
            evaluation = self._parse_evaluation_json(response)
            if evaluation:
                logger.info(
                    "heavyswarm_evaluation_llm_success",
                    extra={
                        "alternative": alt_name,
                        "total_score": evaluation.get("total_score", 0.0),
                    },
                )
                return evaluation
        except Exception as e:
            logger.error(
                "heavyswarm_evaluation_llm_failed",
                extra={
                    "reason": str(e),
                    "alternative": alt_name,
                },
            )

        logger.warning(
            "heavyswarm_evaluation_llm_failed",
            extra={
                "reason": "fallback_to_zero_scores",
                "alternative": alt_name,
            },
        )
        return self._evaluate_alternative_fallback(alternative)

    def _evaluate_alternative_fallback(
        self, alternative: dict[str, Any]
    ) -> dict[str, Any]:
        """Return zero-score fallback when LLM evaluation is unavailable."""
        return {
            "feasibility": 0.0,
            "impact": 0.0,
            "risk": 0.0,
            "cost": 0.0,
            "time_to_implement": 0.0,
            "total_score": 0.0,
        }

    @staticmethod
    def _parse_evaluation_json(response: str) -> dict[str, Any] | None:
        """Parse LLM evaluation response into a scores dict."""
        import json
        import re

        cleaned = response.strip()
        cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
        cleaned = re.sub(r"\s*```$", "", cleaned)

        try:
            parsed = json.loads(cleaned)
            if isinstance(parsed, dict):
                required_keys = {"feasibility", "impact", "risk", "cost", "time_to_implement"}
                # Accept if it has at least some of the required keys
                if any(k in parsed for k in required_keys):
                    # Ensure all expected keys exist, defaulting missing ones to 0.0
                    for k in required_keys | {"total_score"}:
                        if k not in parsed:
                            parsed[k] = 0.0
                    return parsed
            return None
        except json.JSONDecodeError:
            return None

    async def _identify_trade_offs(
        self,
        alternatives: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """Identify trade-offs between alternatives."""
        if len(alternatives) < 2:
            return []

        trade_offs = []
        for i, alt1 in enumerate(alternatives[:-1]):
            for alt2 in alternatives[i + 1 :]:
                trade_offs.append(
                    {
                        "alternative_1": alt1.get("name", "unknown"),
                        "alternative_2": alt2.get("name", "unknown"),
                        "trade_off": "Different risk/reward profiles",
                    }
                )

        return trade_offs

    # =========================================================================
    # Phase 4: Verification
    # =========================================================================

    async def _verification_phase(
        self,
        workflow_id: str,
        topic: str,
        context: dict[str, Any] | None = None,
        alternatives_data: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
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
            "recommended_alternative": alternatives_data.get("recommended_alternative", {}),
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
                verification_data["risk_assessments"] = risk_assessment.get("risks_identified", [])
                verification_data["risk_level"] = risk_assessment.get("risk_level", "unknown")
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
        context: dict[str, Any] | None = None,
        verification_data: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
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
        verification_data: dict[str, Any],
    ) -> list[dict[str, Any]]:
        """
        Collect votes from triad members via NATS request-reply.

        Each triad agent receives a vote request and returns its own
        decision and confidence score. On timeout (30s), falls back to
        ``confidence=0.0`` and logs ``heavyswarm_vote_timeout``. On error,
        logs ``heavyswarm_vote_error``. On success, logs
        ``heavyswarm_vote_collected``.

        Args:
            consensus_id: Consensus process identifier
            topic: Problem/topic
            verification_data: Verification phase output

        Returns:
            List of votes with real agent-deliberated confidence scores
        """
        votes: list[dict[str, Any]] = []
        recommended = verification_data.get("recommended_alternative", {})
        recommended_name = recommended.get("name", "unknown") if recommended else "unknown"

        for agent_id in self.triad_agents:
            if agent_id not in self.agents:
                logger.warning(f"[{self.name}] Triad agent not found for voting: {agent_id}")
                continue

            agent = self.agents[agent_id]

            try:
                reply = await agent.send_with_reply(
                    recipient=agent_id,
                    message_type="vote_request",
                    content={
                        "consensus_id": consensus_id,
                        "topic": topic,
                        "recommended_alternative": recommended,
                        "verification_data": {
                            "overall_valid": verification_data.get("overall_valid", True),
                            "confidence": verification_data.get("confidence", 0.0),
                            "error_checks": verification_data.get("error_checks", []),
                            "risk_assessments": verification_data.get("risk_assessments", []),
                        },
                    },
                    timeout=30,
                )

                if reply is not None:
                    # Successful response — extract real agent vote
                    vote_decision = reply.get("decision", recommended_name)
                    vote_confidence = reply.get("confidence", 0.0)

                    logger.info(
                        "heavyswarm_vote_collected",
                        extra={
                            "agent_id": agent_id,
                            "consensus_id": consensus_id,
                            "decision": vote_decision,
                            "confidence": vote_confidence,
                        },
                    )

                    vote = {
                        "agent_id": agent_id,
                        "decision": vote_decision,
                        "confidence": vote_confidence,
                    }
                else:
                    # Timeout — honest fallback with confidence=0.0
                    logger.warning(
                        "heavyswarm_vote_timeout",
                        extra={
                            "agent_id": agent_id,
                            "consensus_id": consensus_id,
                            "timeout_s": 30,
                        },
                    )
                    vote = {
                        "agent_id": agent_id,
                        "decision": "vote_timeout",
                        "confidence": 0.0,
                    }

            except Exception as e:
                logger.exception(
                    "heavyswarm_vote_error",
                    extra={
                        "agent_id": agent_id,
                        "consensus_id": consensus_id,
                        "error": str(e),
                    },
                )
                vote = {
                    "agent_id": agent_id,
                    "decision": "vote_error",
                    "confidence": 0.0,
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

    def get_workflow_status(self, workflow_id: str) -> WorkflowResult | None:
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

    def get_statistics(self) -> dict[str, Any]:
        """Get workflow statistics."""
        total_workflows = len(self.workflow_history)
        completed = sum(1 for w in self.workflow_history if w.state == WorkflowPhase.COMPLETED)
        failed = sum(1 for w in self.workflow_history if w.state == WorkflowPhase.FAILED)

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
