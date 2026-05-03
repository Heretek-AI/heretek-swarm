"""
Consensus Coordinator — bridges agent actors with MAKER voting.

Orchestrates the full consensus flow:
1. Select domain-relevant agents via DomainSelector
2. Start a MAKER consensus process
3. Collect votes from each agent via run_with_llm()
4. Parse decisions and confidence scores
5. Compute and return the ConsensusResult

Handles agent unavailability (skip + warn) and LLM failures
(abstain with zero confidence). Each agent receives a prompt
requesting a structured response with a decision and confidence.
"""

import asyncio
import json
import re
import uuid
from datetime import UTC, datetime
from typing import Any

import structlog

from heretek_swarm.consensus.domain_selector import DomainSelector
from heretek_swarm.consensus.maker import ConsensusResult, MAKERConsensus

logger = structlog.get_logger("ConsensusCoordinator")


# Prompt template sent to each agent for voting
_VOTE_PROMPT = """You are participating in a multi-agent consensus process.

QUESTION: {question}

Respond with a JSON object containing:
- "decision": your answer (a short phrase or single word like "yes", "no", "approve", "reject", or a brief categorical answer)
- "confidence": a number between 0.0 and 1.0 indicating how confident you are
- "reasoning": one sentence explaining your decision

Respond ONLY with the JSON object, no other text.
Example: {{"decision": "yes", "confidence": 0.85, "reasoning": "The evidence supports this approach."}}"""

# Pattern for extracting JSON from potentially messy LLM output
_JSON_PATTERN = re.compile(r"\{[^}]+\}")


class ConsensusCoordinator:
    """
    Bridges agent actors with MAKER consensus voting.

    Coordinates the end-to-end consensus flow by:
    - Using DomainSelector to find relevant agents for a question
    - Sending each agent the question via run_with_llm()
    - Parsing structured decision+confidence responses
    - Feedings votes into MAKERConsensus for aggregation

    Args:
        maker: MAKERConsensus instance for vote aggregation
        domain_selector: DomainSelector for agent selection
        actors: Dict mapping agent_id -> AgentActor instances
    """

    def __init__(
        self,
        maker: MAKERConsensus,
        domain_selector: DomainSelector,
        actors: dict[str, Any],
    ) -> None:
        self.maker = maker
        self.domain_selector = domain_selector
        self.actors = actors

    async def run_consensus(
        self,
        question: str,
        timeout: float = 120,
        max_rounds: int = 3,
    ) -> ConsensusResult | None:
        """
        Run a full consensus process on *question*.

        Steps:
        1. Select domain-relevant agents via DomainSelector
        2. Start a MAKER consensus process
        3. Collect votes from each agent concurrently (with timeout)
        4. Parse each agent's response for decision + confidence
        5. Compute consensus via MAKER ahead-by-k voting

        Args:
            question: The question to reach consensus on
            timeout: Overall timeout in seconds (default 120)
            max_rounds: Reserved for future multi-round deliberation

        Returns:
            ConsensusResult on success, None on failure/timeout
        """
        consensus_id = str(uuid.uuid4())[:8]

        logger.info(
            "consensus_started",
            consensus_id=consensus_id,
            question=question[:200],
            timeout=timeout,
        )

        # 1. Select agents
        selected_ids = self.domain_selector.score_agents(question)
        logger.info(
            "domain_selection_complete",
            consensus_id=consensus_id,
            selected_agents=selected_ids,
            agent_count=len(selected_ids),
        )

        # 2. Start MAKER process
        self.maker.start_consensus(consensus_id)

        # 3. Collect votes concurrently with timeout
        try:
            await asyncio.wait_for(
                self._collect_all_votes(consensus_id, question, selected_ids),
                timeout=timeout,
            )
        except TimeoutError:
            logger.warning(
                "consensus_failed",
                consensus_id=consensus_id,
                reason="timeout",
                timeout=timeout,
            )
            self.maker.process_states[consensus_id] = (
                self.maker.process_states.get(consensus_id)
            )
            # Still try to compute with whatever votes we have
        except Exception as exc:
            logger.error(
                "consensus_failed",
                consensus_id=consensus_id,
                reason=str(exc),
            )

        # 4. Compute consensus
        result = self.maker.compute_consensus(consensus_id)

        if result:
            logger.info(
                "consensus_completed",
                consensus_id=consensus_id,
                decision=result.decision,
                confidence=result.confidence,
                vote_count=len(result.votes),
                red_flag_count=len(result.red_flags),
            )
        else:
            logger.warning(
                "consensus_failed",
                consensus_id=consensus_id,
                reason="insufficient_votes_or_no_agreement",
            )

        # Cleanup MAKER state
        self.maker.cleanup_process(consensus_id)

        return result

    async def _collect_all_votes(
        self,
        consensus_id: str,
        question: str,
        agent_ids: list[str],
    ) -> None:
        """Collect votes from all selected agents concurrently."""
        prompt = _VOTE_PROMPT.format(question=question)

        tasks = [
            self._collect_single_vote(consensus_id, agent_id, prompt)
            for agent_id in agent_ids
        ]
        await asyncio.gather(*tasks, return_exceptions=True)

    async def _collect_single_vote(
        self,
        consensus_id: str,
        agent_id: str,
        prompt: str,
    ) -> None:
        """
        Collect a vote from a single agent.

        Handles:
        - Agent not found in registry (skip + warn)
        - LLM failure (record as abstain with zero confidence)
        - Response parsing failure (record as abstain with zero confidence)
        """
        actor = self.actors.get(agent_id)

        if actor is None:
            logger.warning(
                "agent_vote_collected",
                consensus_id=consensus_id,
                agent_id=agent_id,
                status="unavailable",
                decision="abstain",
                confidence=0.0,
            )
            self.maker.add_vote(
                consensus_id=consensus_id,
                agent_id=agent_id,
                decision="abstain",
                confidence=0.0,
                metadata={"status": "agent_unavailable"},
            )
            return

        try:
            # Call the agent's LLM via run_with_llm
            raw_response = await actor.run_with_llm(prompt, timeout=30)
            decision, confidence = self._parse_response(raw_response)

            logger.info(
                "agent_vote_collected",
                consensus_id=consensus_id,
                agent_id=agent_id,
                status="success",
                decision=decision,
                confidence=confidence,
            )
            self.maker.add_vote(
                consensus_id=consensus_id,
                agent_id=agent_id,
                decision=decision,
                confidence=confidence,
            )

        except Exception as exc:
            logger.warning(
                "agent_vote_collected",
                consensus_id=consensus_id,
                agent_id=agent_id,
                status="llm_failure",
                decision="abstain",
                confidence=0.0,
                error=str(exc)[:200],
            )
            self.maker.add_vote(
                consensus_id=consensus_id,
                agent_id=agent_id,
                decision="abstain",
                confidence=0.0,
                metadata={"status": "llm_failure", "error": str(exc)[:200]},
            )

    @staticmethod
    def _parse_response(raw: str) -> tuple[str, float]:
        """
        Parse an agent's LLM response into (decision, confidence).

        Attempts:
        1. JSON parse of the full response
        2. Regex extraction of a JSON object substring
        3. Fallback: first meaningful word as decision, 0.5 confidence

        Args:
            raw: Raw LLM response string

        Returns:
            Tuple of (decision, confidence)
        """
        if not raw or not raw.strip():
            return "abstain", 0.0

        text = raw.strip()

        # Try 1: Direct JSON parse
        try:
            data = json.loads(text)
            return _extract_decision_confidence(data)
        except (json.JSONDecodeError, ValueError):
            pass

        # Try 2: Regex extract JSON substring
        match = _JSON_PATTERN.search(text)
        if match:
            try:
                data = json.loads(match.group())
                return _extract_decision_confidence(data)
            except (json.JSONDecodeError, ValueError):
                pass

        # Try 3: Look for common decision patterns in free text
        lower = text.lower()
        words = [re.sub(r"[^a-z]", "", w) for w in lower.split()]
        for keyword in ("yes", "no", "approve", "reject", "support", "oppose"):
            if keyword in words:
                return keyword, 0.5

        # Fallback: first meaningful word
        for word in words:
            if word and len(word) <= 20:
                return word, 0.3

        return "abstain", 0.0


def _extract_decision_confidence(data: dict) -> tuple[str, float]:
    """Extract decision and confidence from a parsed JSON dict."""
    decision = str(data.get("decision", "abstain")).strip().lower()
    try:
        confidence = float(data.get("confidence", 0.5))
        confidence = max(0.0, min(1.0, confidence))
    except (TypeError, ValueError):
        confidence = 0.5

    if not decision:
        decision = "abstain"

    return decision, confidence
