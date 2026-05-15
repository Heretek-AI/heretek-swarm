"""
Deliberation Orchestrator — extracts triad deliberation, MAKER consensus,
and routed-task dispatch logic from AutonomousSwarm.

These methods coordinate multi-agent interactions but do not manage
actor lifecycle or the main processing loop.
"""

import asyncio
from typing import Any

import structlog

from heretek_swarm.consensus.consensus_coordinator import ConsensusCoordinator
from heretek_swarm.consensus.domain_selector import DomainSelector
from heretek_swarm.consensus.maker import MAKERConsensus

logger = structlog.get_logger(__name__)


class DeliberationOrchestrator:
    """Orchestrates triad deliberation, MAKER consensus, and routed-task dispatch.

    Takes supervisor and consensus engine references — these are shared
    with AutonomousSwarm and mutated during ``initialize()``, so the
    orchestrator always sees the latest state.
    """

    def __init__(
        self,
        supervisor: Any,
        consensus: MAKERConsensus | None,
        config: dict[str, Any] | None = None,
    ) -> None:
        self._supervisor = supervisor
        self._consensus = consensus
        self._config = config or {}

    async def run_deliberation(
        self,
        prompt: str,
        timeout: int = 120,  # noqa: ASYNC109
    ) -> dict[str, Any]:
        """
        Run a triad deliberation: route a prompt through Steward → Alpha → Beta → Charlie.

        NOTE: For complex questions requiring multi-agent consensus with domain-based
        agent selection, prefer ``run_consensus()`` which uses the MAKER consensus
        engine with DomainSelector for more rigorous decision-making.

        Args:
            prompt: The deliberation topic/prompt.
            timeout: Maximum total wall-clock seconds to wait for all three
                     agents to produce output (default 120). Each agent's LLM
                     call has a 60s internal timeout in run_with_llm.

        Returns:
            Dict mapping each agent_id to its output. Partial results are
            returned on timeout or agent failure.

        Raises:
            RuntimeError: If Steward agent is not in the actor registry.
        """
        logger.info(
            "run_deliberation_started",
            prompt=prompt,
            timeout=timeout,
        )

        supervisor_actors = self._supervisor.actors if self._supervisor else {}
        steward = supervisor_actors.get("steward")
        if steward is None:
            raise RuntimeError(
                "Steward agent not found in supervisor.actors — "
                "cannot coordinate triad. Ensure spawn_all_actors() "
                "completed successfully."
            )

        try:
            # Initiate triad deliberation via Steward's coordinate_triad.
            # This sends a "start_deliberation" message through steward.send()
            # which goes into the topic routing system. The message chain:
            #   coordinate_triad → send("triad", start_deliberation) →
            #   _deliver_to_registry_actors → Steward owns "triad" topic
            deliberation_id = await steward.coordinate_triad(
                topic=prompt,
                triad_members=["alpha", "beta", "charlie"],
            )
            logger.info(
                "deliberation_initiated",
                deliberation_id=deliberation_id,
            )

            # Wait for async mailbox processing to complete across all agents.
            # The message chain is: Steward mailbox → _handle_start_deliberation
            # → send_to_actor(member, deliberation_request) → each member mailbox
            # → _handle_deliberation_request → _perform_analysis() →
            # run_with_llm() (60s timeout per agent). We sleep generously since
            # the method-level timeout param caps total wall time.
            sleep_time = min(timeout, 120)
            await asyncio.sleep(sleep_time)

        except TimeoutError:
            logger.warning("deliberation_timeout", prompt=prompt)
        except Exception as exc:
            logger.error(
                "deliberation_failed",
                prompt=prompt,
                error=str(exc),
            )

        # Read results from per-agent state attributes.
        results: dict[str, Any] = {}
        for agent_id in ["alpha", "beta", "charlie"]:
            agent = supervisor_actors.get(agent_id)
            if agent is None:
                results[agent_id] = {"error": f"Agent {agent_id} not found"}
                continue

            if agent_id == "alpha":
                history = getattr(agent, "analysis_history", [])
                results[agent_id] = {"analyses": history[-3:] if history else []}
            elif agent_id == "beta":
                analyses = getattr(agent, "_analyses", {})
                results[agent_id] = {"analyses": list(analyses.values())[-3:] if analyses else []}
            elif agent_id == "charlie":
                challenges = getattr(agent, "_challenges", {})
                results[agent_id] = {
                    "challenges": list(challenges.values())[-3:] if challenges else []
                }

        logger.info(
            "run_deliberation_complete",
            alpha_count=len(results.get("alpha", {}).get("analyses", [])),
            beta_count=len(results.get("beta", {}).get("analyses", [])),
            charlie_count=len(results.get("charlie", {}).get("challenges", [])),
        )
        return results

    async def run_consensus(
        self,
        question: str,
        timeout: float = 120,  # noqa: ASYNC109
        max_rounds: int = 3,
    ) -> dict[str, Any]:
        """
        Run a MAKER consensus process with domain-based agent selection.

        Uses DomainSelector to find question-relevant agents, then orchestrates
        MAKER ahead-by-k voting via ConsensusCoordinator. Each selected agent
        produces a structured vote (decision + confidence) through its LLM.

        Args:
            question: The question to reach consensus on.
            timeout: Overall timeout in seconds (default 120).
            max_rounds: Reserved for future multi-round deliberation.

        Returns:
            Structured dict with keys:
            - decision: Winning decision string
            - confidence: Overall confidence score (0.0-1.0)
            - votes: List of per-agent vote dicts
            - red_flags: List of red flag messages
            - reasoning: Aggregated reasoning from votes
            - consensus_id: Unique process identifier

            Returns an error dict if consensus cannot be initiated
            (e.g. no supervisor, no consensus engine).
        """
        logger.info(
            "run_consensus_started",
            question=question[:200],
            timeout=timeout,
            max_rounds=max_rounds,
        )

        # Guard: supervisor must be available
        if self._supervisor is None:
            logger.error("run_consensus_no_supervisor")
            return {
                "decision": "error",
                "confidence": 0.0,
                "votes": [],
                "red_flags": ["Supervisor not initialized"],
                "reasoning": "Cannot run consensus without actor supervisor",
            }

        # Guard: consensus engine must be available
        if self._consensus is None:
            logger.error("run_consensus_no_consensus_engine")
            return {
                "decision": "error",
                "confidence": 0.0,
                "votes": [],
                "red_flags": ["Consensus engine not initialized"],
                "reasoning": "Cannot run consensus without MAKER consensus engine",
            }

        # Build domain selector from character files
        domain_selector = DomainSelector()

        # Build coordinator with real actors
        coordinator = ConsensusCoordinator(
            maker=self._consensus,
            domain_selector=domain_selector,
            actors=self._supervisor.actors,
        )

        # Run consensus
        result = await coordinator.run_consensus(
            question=question,
            timeout=timeout,
            max_rounds=max_rounds,
        )

        if result is None:
            logger.warning("run_consensus_no_result", question=question[:200])
            return {
                "decision": "no_consensus",
                "confidence": 0.0,
                "votes": [],
                "red_flags": ["No consensus reached"],
                "reasoning": "MAKER could not reach a decisive consensus",
            }

        # Build structured response
        vote_dicts = [
            {
                "agent_id": v.agent_id,
                "decision": v.decision,
                "confidence": v.confidence,
                "metadata": v.metadata,
            }
            for v in result.votes
        ]

        # Aggregate reasoning from non-abstain votes
        reasoning_parts = []
        for v in result.votes:
            if v.decision != "abstain" and v.metadata.get("reasoning"):
                reasoning_parts.append(f"{v.agent_id}: {v.metadata['reasoning']}")  # noqa: PERF401

        response = {
            "decision": result.decision,
            "confidence": result.confidence,
            "votes": vote_dicts,
            "red_flags": result.red_flags,
            "reasoning": "; ".join(reasoning_parts) if reasoning_parts else "No reasoning captured",
            "consensus_id": result.metadata.get("consensus_id", "unknown"),
            "round_history": result.metadata.get("round_history", []),
            "total_rounds": result.metadata.get("total_rounds", 1),
        }

        logger.info(
            "run_consensus_complete",
            decision=response["decision"],
            confidence=response["confidence"],
            vote_count=len(vote_dicts),
            red_flag_count=len(response["red_flags"]),
        )

        return response

    async def run_routed_task(
        self,
        agent_name: str,
        task_type: str,
        task_data: dict[str, Any],
        timeout: int = 30,  # noqa: ASYNC109
    ) -> dict[str, Any]:
        """
        Route a task to a specific agent using Steward's ``route_to_agent()``
        and log the event to Historian.

        This is a one-shot dispatch path for the CLI ``--target-agent``
        flag — it sends a structured task to a single agent (cast-style
        delivery) rather than orchestrating a triad deliberation.

        Args:
            agent_name: Target agent ID (e.g. ``"coder"``).
            task_type: Machine-readable task label (e.g. ``"code_analysis"``).
            task_data: Arbitrary payload dict for the receiving agent.
            timeout: Maximum wall-clock seconds to sleep for async mailbox
                     processing (capped at 30). The agent's internal handler
                     deadline should be shorter; this sleep is a best-effort
                     wait for the mailbox to be consumed.

        Returns:
            A dict with dispatch status, target agent, task type, and the
            message ID from Steward's send_to_actor on success::

                {"status": "dispatched", "target_agent": "coder",
                 "task_type": "code_analysis", "message_id": "abc123"}

            On dispatch failure: ``{"status": "failed",
            "error": "route_to_agent returned empty"}``

        Raises:
            RuntimeError: If Steward agent is not in the actor registry.
        """
        logger.info(
            "run_routed_task_started",
            agent_name=agent_name,
            task_type=task_type,
            timeout=timeout,
        )

        supervisor_actors = self._supervisor.actors if self._supervisor else {}
        steward = supervisor_actors.get("steward")
        if steward is None:
            raise RuntimeError(
                "Steward agent not found in supervisor.actors — "
                "cannot route task. Ensure spawn_all_actors() "
                "completed successfully."
            )

        message_id = await steward.route_to_agent(
            agent_name=agent_name,
            task_type=task_type,
            task_data=task_data,
        )

        if not message_id:
            logger.warning(
                "run_routed_task_dispatch_failed",
                agent_name=agent_name,
                task_type=task_type,
            )
            return {
                "status": "failed",
                "error": "route_to_agent returned empty",
            }

        logger.info(
            "run_routed_task_dispatched",
            agent_name=agent_name,
            task_type=task_type,
            message_id=message_id,
        )

        # Best-effort wait for async mailbox processing (same sleep pattern
        # as run_deliberation()).
        sleep_time = min(timeout, 30)
        await asyncio.sleep(sleep_time)

        # Log the routed event to Historian. Gracefully handle missing
        # historian (log warning, still return dispatch status). This
        # follows the same None-guard pattern as _process_scheduled_tasks().
        historian = supervisor_actors.get("historian")
        if historian is not None:
            await historian.log_event(
                "routed_task",
                "main_loop",
                {
                    "target_agent": agent_name,
                    "task_type": task_type,
                    "message_id": message_id,
                },
            )
        else:
            logger.warning(
                "run_routed_task_historian_skipped",
                agent_name=agent_name,
                task_type=task_type,
            )

        return {
            "status": "dispatched",
            "target_agent": agent_name,
            "task_type": task_type,
            "message_id": message_id,
        }
