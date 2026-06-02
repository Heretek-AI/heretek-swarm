"""
Phase Handlers for HeavySwarm Workflow

.. deprecated::
    These placeholder PhaseHandler classes are being replaced by
    LangGraph nodes as part of M-arch PR #6 (see PLAN.md §M-arch).
    The abstract :class:`PhaseHandler` interface and the five concrete
    handler classes are preserved as documentation of the intended
    extension point. The active code path lives in
    :mod:`heretek_swarm.orchestration.heavyswarm` which calls phase
    logic via instance methods directly.

Provides handler classes for each phase of the workflow.

**Important:** These handlers are currently unused extension points.
HeavySwarmWorkflow calls phase logic via instance methods directly
(_research_phase, _analysis_phase, _alternatives_phase, etc.) rather
than through these PhaseHandler classes. The handlers below exist as
placeholders for future phase handler injection (ADR-008). All hardcoded
scores are set to 0.0 with structured ``phase_handler_*_hardcoded`` log
warnings so future developers understand these are not the active code
path. See heavyswarm.py for the real phase implementations.
"""

from abc import ABC, abstractmethod
from typing import Any

import structlog

logger = structlog.get_logger(__name__)


class PhaseHandler(ABC):
    """Abstract base class for workflow phase handlers"""

    @abstractmethod
    async def execute(
        self,
        workflow_id: str,
        topic: str,
        context: dict[str, Any] | None = None,
        previous_output: dict[str, Any] | None = None,
    ) -> tuple[bool, dict[str, Any], list[str]]:
        """
        Execute the phase handler.

        Returns:
            Tuple of (success, output, errors)
        """


class ResearchPhaseHandler(PhaseHandler):
    """Handler for Research phase"""

    def __init__(self, historian_id: str, agents: dict[str, Any]):
        self.historian_id = historian_id
        self.agents = agents

    async def execute(
        self,
        workflow_id: str,
        topic: str,
        context: dict[str, Any] | None = None,
        previous_output: dict[str, Any] | None = None,  # noqa: ARG002
    ) -> tuple[bool, dict[str, Any], list[str]]:
        """Execute research phase"""
        logger.info("Research phase: Gathering information")

        research_data = {
            "topic": topic,
            "context": context or {},
            "historical_context": [],
            "relevant_facts": [],
            "constraints": [],
            "assumptions": [],
        }

        errors = []

        # Query historian for context
        if self.historian_id in self.agents:
            historian_agent = self.agents[self.historian_id]
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
                errors.append(f"Historian query failed: {e}")
                logger.warning("Historian query failed: {e}")

        # Synthesize knowledge if historian available
        if self.historian_id in self.agents:
            historian_agent = self.agents[self.historian_id]
            try:
                knowledge = await historian_agent.synthesize_knowledge(
                    topic=topic,
                    limit=10,
                )
                research_data["knowledge_summary"] = knowledge.get("summary", "")
            except Exception as e:
                errors.append(f"Knowledge synthesis failed: {e}")
                logger.warning("Knowledge synthesis failed: {e}")

        # Identify constraints and assumptions from context
        if context:
            research_data["constraints"] = context.get("constraints", [])
            research_data["assumptions"] = context.get("assumptions", [])

        logger.info(
            "Research phase complete",
            extra={
                "historical_context_count": len(research_data["historical_context"]),
                "constraints_count": len(research_data["constraints"]),
            },
        )

        return len(errors) == 0, research_data, errors


class AnalysisPhaseHandler(PhaseHandler):
    """Handler for Analysis phase"""

    def __init__(self, triad_agents: list[str], agents: dict[str, Any]):
        self.triad_agents = triad_agents
        self.agents = agents

    async def execute(
        self,
        workflow_id: str,
        topic: str,
        context: dict[str, Any] | None = None,  # noqa: ARG002
        previous_output: dict[str, Any] | None = None,
    ) -> tuple[bool, dict[str, Any], list[str]]:
        """Execute analysis phase"""
        logger.info("Analysis phase: Multi-perspective analysis")

        analysis_data = {
            "topic": topic,
            "research_summary": previous_output,
            "alpha_analysis": None,
            "beta_analysis": None,
            "charlie_analysis": None,
            "perspectives": [],
            "key_insights": [],
            "disagreements": [],
        }

        errors = []

        # Collect analysis from each triad member
        triad_analyses = {}

        for agent_id in self.triad_agents:
            if agent_id not in self.agents:
                errors.append(f"Triad agent not found: {agent_id}")
                continue

            agent = self.agents[agent_id]

            try:
                await agent.send_to_actor(
                    target_actor_id=agent_id,
                    message_type="analysis_request",
                    content={
                        "workflow_id": workflow_id,
                        "topic": topic,
                        "research_data": previous_output,
                    },
                )

                # Phase handler is unused — honest zero confidence with structured log
                logger.warning(
                    "phase_handler_analysis_hardcoded",
                    extra={
                        "agent_id": agent_id,
                        "workflow_id": workflow_id,
                        "reason": "PhaseHandler analysis path is not the active code path; "
                        "HeavySwarmWorkflow._analysis_phase() bypasses this handler",
                    },
                )

                triad_analyses[agent_id] = {
                    "agent_id": agent_id,
                    "decision": f"{agent_id}_analysis_complete",
                    "confidence": 0.0,
                    "insights": [],
                    "reasoning": (
                        "Phase handler analysis path unused —"
                        " see heavyswarm._analysis_phase"
                    ),
                }
            except Exception as e:
                errors.append(f"Error collecting analysis from {agent_id}: {e}")
                triad_analyses[agent_id] = {
                    "agent_id": agent_id,
                    "decision": "analysis_failed",
                    "confidence": 0.0,
                    "insights": [],
                    "reasoning": f"Error: {e}",
                }

        analysis_data["alpha_analysis"] = triad_analyses.get("alpha")
        analysis_data["beta_analysis"] = triad_analyses.get("beta")
        analysis_data["charlie_analysis"] = triad_analyses.get("charlie")
        analysis_data["perspectives"] = list(triad_analyses.values())

        # Identify key insights
        for agent_id, analysis in triad_analyses.items():  # noqa: B007
            if analysis:
                insights = analysis.get("insights", [])
                analysis_data["key_insights"].extend(insights)

        # Identify disagreements
        decisions = [a.get("decision") for a in triad_analyses.values() if a and a.get("decision")]
        if len(set(decisions)) > 1:
            analysis_data["disagreements"].append(f"Triad disagreement: {decisions}")

        return len(errors) == 0, analysis_data, errors


class AlternativesPhaseHandler(PhaseHandler):
    """Handler for Alternatives phase"""

    def __init__(self, agents: dict[str, Any]):
        self.agents = agents

    async def execute(
        self,
        workflow_id: str,
        topic: str,
        _context: dict[str, Any] | None = None,
        previous_output: dict[str, Any] | None = None,
    ) -> tuple[bool, dict[str, Any], list[str]]:
        """Execute alternatives phase"""
        logger.info("Alternatives phase: Generating solutions")

        alternatives_data = {
            "topic": topic,
            "analysis_summary": previous_output,
            "alternatives": [],
            "evaluation_criteria": ["feasibility", "impact", "risk", "cost", "time_to_implement"],
            "recommended_alternative": None,
            "trade_offs": [],
        }

        errors = []

        # Phase handler is unused — honest zero values with structured log
        # HeavySwarmWorkflow._alternatives_phase() is the active code path
        logger.warning(
            "phase_handler_alternatives_hardcoded",
            extra={
                "workflow_id": workflow_id,
                "topic": topic,
                "reason": "PhaseHandler alternatives path is not the active code path; "
                "HeavySwarmWorkflow._alternatives_phase() bypasses this handler",
            },
        )

        # Empty alternatives — no hardcoded synthetic data
        alternatives_data["alternatives"] = []

        logger.warning(
            "phase_handler_evaluation_hardcoded",
            extra={
                "workflow_id": workflow_id,
                "topic": topic,
                "reason": "All evaluation scores set to 0.0 — "
                "HeavySwarmWorkflow._alternatives_phase() is the active code path",
            },
        )

        alternatives_data["recommended_alternative"] = None
        alternatives_data["alternatives"] = []

        alternatives_data["evaluation_criteria"] = [
            "feasibility",
            "impact",
            "risk",
            "cost",
            "time_to_implement",
        ]

        return True, alternatives_data, errors


class VerificationPhaseHandler(PhaseHandler):
    """Handler for Verification phase"""

    def __init__(self, agents: dict[str, Any]):
        self.agents = agents

    async def execute(
        self,
        workflow_id: str,  # noqa: ARG002
        topic: str,
        context: dict[str, Any] | None = None,  # noqa: ARG002
        previous_output: dict[str, Any] | None = None,
    ) -> tuple[bool, dict[str, Any], list[str]]:
        """Execute verification phase"""
        logger.info("Verification phase: Validating solutions")

        verification_data = {
            "topic": topic,
            "recommended_alternative": previous_output.get("recommended_alternative", {}),
            "validation_results": [],
            "error_checks": [],
            "risk_assessments": [],
            "edge_cases": [],
            "overall_valid": True,
            "confidence": 0.0,
        }

        errors = []
        recommended = previous_output.get("recommended_alternative")

        if not recommended:
            verification_data["overall_valid"] = False
            errors.append("No recommended alternative to verify")
            return False, verification_data, errors

        # Beta: Error detection
        if "beta" in self.agents:
            beta_agent = self.agents["beta"]
            try:
                errors_found = await beta_agent._detect_errors(recommended)  # noqa: SLF001
                verification_data["error_checks"] = errors_found
                if errors_found:
                    verification_data["overall_valid"] = False
            except Exception as e:
                errors.append(f"Beta error check failed: {e}")

        # Charlie: Risk assessment
        if "charlie" in self.agents:
            charlie_agent = self.agents["charlie"]
            try:
                risk_assessment = await charlie_agent._assess_risks(recommended)  # noqa: SLF001
                verification_data["risk_assessments"] = risk_assessment.get("risks_identified", [])
                verification_data["risk_level"] = risk_assessment.get("risk_level", "unknown")
            except Exception as e:
                errors.append(f"Charlie risk assessment failed: {e}")

        # Calculate confidence
        error_count = len(verification_data["error_checks"])
        risk_count = len(verification_data["risk_assessments"])
        base_confidence = recommended.get("evaluation", {}).get("total_score", 0.5)
        penalty = (error_count * 0.1) + (risk_count * 0.05)
        verification_data["confidence"] = max(0.0, base_confidence - penalty)

        return verification_data["overall_valid"], verification_data, errors


class DecisionPhaseHandler(PhaseHandler):
    """Handler for Decision phase"""

    def __init__(self, triad_agents: list[str], agents: dict[str, Any], consensus_engine: Any):
        self.triad_agents = triad_agents
        self.agents = agents
        self.consensus_engine = consensus_engine

    async def execute(
        self,
        workflow_id: str,
        topic: str,
        context: dict[str, Any] | None = None,  # noqa: ARG002
        previous_output: dict[str, Any] | None = None,
    ) -> tuple[bool, dict[str, Any], list[str]]:
        """Execute decision phase"""
        logger.info("Decision phase: Running consensus")

        consensus_id = f"consensus_{workflow_id}"

        # Start consensus process
        self.consensus_engine.start_consensus(consensus_id)

        errors = []
        votes = []

        # Collect votes from triad
        for agent_id in self.triad_agents:
            if agent_id not in self.agents:
                continue

            # Phase handler is unused — honest zero confidence with structured log
            logger.warning(
                "phase_handler_vote_hardcoded",
                extra={
                    "agent_id": agent_id,
                    "consensus_id": consensus_id,
                    "workflow_id": workflow_id,
                    "reason": "PhaseHandler vote path is not the active code path; "
                    "HeavySwarmWorkflow._decision_phase() bypasses this handler",
                },
            )

            vote = {
                "agent_id": agent_id,
                "decision": previous_output.get("recommended_alternative", {}).get(
                    "name", "unknown"
                ),
                "confidence": 0.0,
            }

            self.consensus_engine.add_vote(
                consensus_id=consensus_id,
                agent_id=agent_id,
                decision=vote["decision"],
                confidence=vote["confidence"],
            )

            votes.append(vote)

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

        return True, decision_data, errors


class PhaseHandlerRegistry:
    """Registry for phase handlers"""

    def __init__(self):
        self._handlers: dict[str, PhaseHandler] = {}

    def register(self, phase_name: str, handler: PhaseHandler) -> None:
        """Register a phase handler"""
        self._handlers[phase_name] = handler

    def get(self, phase_name: str) -> PhaseHandler | None:
        """Get a phase handler"""
        return self._handlers.get(phase_name)

    def get_all(self) -> dict[str, PhaseHandler]:
        """Get all registered handlers"""
        return self._handlers.copy()
