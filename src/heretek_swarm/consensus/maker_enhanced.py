"""
Enhanced MAKER Protocol - Multi-Agent Knowledge Extraction & Reasoning with advanced features.

This module extends the base MAKER consensus with:
- Extended knowledge extraction with pattern library integration
- Cross-validation of reasoning chains
- Decision provenance tracking
- Rollback capability for failed decisions

The enhanced protocol builds upon the base MAKER algorithm to provide
more robust decision-making with full audit trails and recovery mechanisms.

Example:
    ```python
    from heretek_swarm.consensus.maker_enhanced import EnhancedMAKERConsensus

    # Initialize enhanced consensus
    consensus = EnhancedMAKERConsensus(
        ahead_by_k=2,
        min_votes=3,
        enable_pattern_library=True,
        enable_rollback=True
    )

    # Start consensus with pattern integration
    consensus.start_consensus("deploy-decision", domain="deployment")

    # Add votes with reasoning chains
    consensus.add_vote_with_reasoning(
        consensus_id="deploy-decision",
        agent_id="agent-1",
        decision="deploy",
        confidence=0.9,
        reasoning_chain=[
            {"step": 1, "observation": "All tests passed"},
            {"step": 2, "conclusion": "Safe to deploy"}
        ]
    )

    # Compute consensus with cross-validation
    result = consensus.compute_consensus_with_validation("deploy-decision")

    # Access decision provenance
    provenance = consensus.get_decision_provenance("deploy-decision")
    ```
"""

import hashlib
import json
import logging
import statistics
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple

import structlog

from .expertise import AgentExpertiseProfiler
from .maker import MAKERConsensus, ConsensusResult, ConsensusState, Vote

logger = structlog.get_logger("EnhancedMAKERConsensus")


class ReasoningChainStatus(Enum):
    """Status of reasoning chain validation."""

    VALID = "valid"
    INVALID = "invalid"
    INCOMPLETE = "incomplete"
    CIRCULAR = "circular"
    UNVERIFIED = "unverified"


@dataclass
class ReasoningStep:
    """
    Single step in a reasoning chain.

    Attributes:
        step_number: Step sequence number
        step_type: Type of step (observation, inference, conclusion)
        content: Step content
        confidence: Confidence in this step
        sources: Optional source references
        validates: IDs of steps this validates
    """

    step_number: int
    step_type: str  # "observation", "inference", "conclusion"
    content: str
    confidence: float
    sources: List[str] = field(default_factory=list)
    validates: List[str] = field(default_factory=list)


@dataclass
class ReasoningChain:
    """
    Complete reasoning chain for a decision.

    Attributes:
        chain_id: Unique chain identifier
        agent_id: Agent who created the chain
        steps: Ordered list of reasoning steps
        status: Validation status
        validation_errors: List of validation errors
        created_at: Creation timestamp
    """

    chain_id: str
    agent_id: str
    steps: List[ReasoningStep]
    status: ReasoningChainStatus = ReasoningChainStatus.UNVERIFIED
    validation_errors: List[str] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def add_step(
        self,
        step_type: str,
        content: str,
        confidence: float,
        sources: Optional[List[str]] = None,
    ) -> ReasoningStep:
        """Add a step to the reasoning chain."""
        step = ReasoningStep(
            step_number=len(self.steps) + 1,
            step_type=step_type,
            content=content,
            confidence=confidence,
            sources=sources or [],
        )
        self.steps.append(step)
        return step

    def validate_chain(self) -> bool:
        """
        Validate the reasoning chain for logical consistency.

        Returns:
            True if chain is valid
        """
        errors = []

        if not self.steps:
            errors.append("Empty reasoning chain")
            self.status = ReasoningChainStatus.INVALID
            return False

        # Check for required conclusion step
        has_conclusion = any(s.step_type == "conclusion" for s in self.steps)
        if not has_conclusion:
            errors.append("Missing conclusion step")

        # Check chain flow: observation -> inference -> conclusion
        step_types = [s.step_type for s in self.steps]
        if "observation" not in step_types:
            errors.append("Missing observation step")

        # Check for circular reasoning (simplified check)
        conclusion_steps = [s for s in self.steps if s.step_type == "conclusion"]
        for step in self.steps:
            if step.step_type == "observation":
                # Observations should not reference conclusions
                for validates_id in step.validates:
                    validating_step = next(
                        (s for s in self.steps if id(s) == id(step)), None
                    )
                    if validating_step and validating_step.step_type == "conclusion":
                        errors.append("Circular reasoning detected")
                        self.status = ReasoningChainStatus.CIRCULAR
                        break

        # Check confidence consistency
        confidences = [s.confidence for s in self.steps]
        if confidences:
            avg_confidence = statistics.mean(confidences)
            low_confidence_steps = [s for s in self.steps if s.confidence < 0.5]
            if len(low_confidence_steps) > len(self.steps) / 2:
                errors.append("Majority of steps have low confidence")

        if errors:
            self.validation_errors = errors
            self.status = ReasoningChainStatus.INVALID
            return False

        self.status = ReasoningChainStatus.VALID
        return True


@dataclass
class EnhancedVote:
    """
    Enhanced vote with reasoning chain and pattern integration.

    Attributes:
        vote: Base vote object
        reasoning_chain: Optional reasoning chain
        pattern_references: References to patterns from pattern library
        cross_validated: Whether vote has been cross-validated
        validation_score: Score from cross-validation
    """

    vote: Vote
    reasoning_chain: Optional[ReasoningChain] = None
    pattern_references: List[str] = field(default_factory=list)
    cross_validated: bool = False
    validation_score: float = 0.0

    @property
    def agent_id(self) -> str:
        return self.vote.agent_id

    @property
    def decision(self) -> str:
        return self.vote.decision

    @property
    def confidence(self) -> float:
        return self.vote.confidence


@dataclass
class DecisionProvenance:
    """
    Complete provenance tracking for a decision.

    Attributes:
        decision_id: Decision identifier
        proposal: Original proposal
        start_time: Consensus start time
        end_time: Consensus end time
        participating_agents: List of participating agents
        votes_cast: Total votes cast
        reasoning_chains: All reasoning chains submitted
        patterns_used: Patterns referenced during deliberation
        validation_results: Cross-validation results
        rollback_available: Whether rollback is possible
        rollback_checkpoint: Checkpoint data for rollback
    """

    decision_id: str
    proposal: str
    start_time: str
    end_time: Optional[str] = None
    participating_agents: List[str] = field(default_factory=list)
    votes_cast: int = 0
    reasoning_chains: List[ReasoningChain] = field(default_factory=list)
    patterns_used: List[str] = field(default_factory=list)
    validation_results: Dict[str, Any] = field(default_factory=dict)
    rollback_available: bool = False
    rollback_checkpoint: Optional[Dict[str, Any]] = None


@dataclass
class RollbackResult:
    """
    Result of a rollback operation.

    Attributes:
        success: Whether rollback succeeded
        message: Result message
        previous_state: State rolled back to
        timestamp: Rollback timestamp
    """

    success: bool
    message: str
    previous_state: Optional[Dict[str, Any]] = None
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class EnhancedMAKERConsensus(MAKERConsensus):
    """
    Enhanced MAKER Consensus with advanced features.

    Extends the base MAKER consensus with:
    - Extended knowledge extraction with pattern library integration
    - Cross-validation of reasoning chains
    - Decision provenance tracking
    - Rollback capability for failed decisions

    The enhanced protocol maintains full audit trails and enables
    recovery from failed decisions through checkpoint-based rollback.

    Attributes:
        enable_pattern_library: Enable pattern library integration
        enable_rollback: Enable rollback capability
        enable_cross_validation: Enable cross-validation of reasoning
        expertise_profiler: Optional expertise profiler
    """

    def __init__(
        self,
        ahead_by_k: int = 2,
        min_votes: int = 3,
        confidence_threshold: float = 0.6,
        reputation_weights: Optional[Dict[str, float]] = None,
        enable_pattern_library: bool = True,
        enable_rollback: bool = True,
        enable_cross_validation: bool = True,
        expertise_profiler: Optional[AgentExpertiseProfiler] = None,
        max_reasoning_depth: int = 10,
    ) -> None:
        """
        Initialize the enhanced consensus engine.

        Args:
            ahead_by_k: Number of votes needed to be ahead to win
            min_votes: Minimum number of votes required
            confidence_threshold: Minimum confidence threshold
            reputation_weights: Optional reputation weights per agent
            enable_pattern_library: Enable pattern library integration
            enable_rollback: Enable rollback capability
            enable_cross_validation: Enable cross-validation
            expertise_profiler: Optional expertise profiler
            max_reasoning_depth: Maximum reasoning chain depth
        """
        super().__init__(
            ahead_by_k=ahead_by_k,
            min_votes=min_votes,
            confidence_threshold=confidence_threshold,
            reputation_weights=reputation_weights,
        )

        self.enable_pattern_library = enable_pattern_library
        self.enable_rollback = enable_rollback
        self.enable_cross_validation = enable_cross_validation
        self.expertise_profiler = expertise_profiler
        self.max_reasoning_depth = max_reasoning_depth

        # Enhanced vote storage
        self.enhanced_votes: Dict[str, List[EnhancedVote]] = {}

        # Reasoning chains
        self.reasoning_chains: Dict[str, List[ReasoningChain]] = {}

        # Decision provenance tracking
        self.decision_provenance: Dict[str, DecisionProvenance] = {}

        # Rollback checkpoints
        self.rollback_checkpoints: Dict[str, Dict[str, Any]] = {}

        # Pattern library integration (simplified - would integrate with actual pattern library)
        self.pattern_library: Dict[str, Any] = {}

        logger.info(
            f"EnhancedMAKERConsensus initialized with "
            f"pattern_library={enable_pattern_library}, "
            f"rollback={enable_rollback}, "
            f"cross_validation={enable_cross_validation}"
        )

    def start_consensus(
        self,
        consensus_id: str,
        proposal: Optional[str] = None,
        domain: Optional[str] = None,
    ) -> None:
        """
        Start a new enhanced consensus process.

        Args:
            consensus_id: Unique identifier for the consensus process
            proposal: Optional proposal description
            domain: Optional domain for expertise weighting
        """
        # Call base implementation
        super().start_consensus(consensus_id)

        # Initialize enhanced structures
        self.enhanced_votes[consensus_id] = []
        self.reasoning_chains[consensus_id] = []

        # Create decision provenance
        self.decision_provenance[consensus_id] = DecisionProvenance(
            decision_id=consensus_id,
            proposal=proposal or consensus_id,
            start_time=datetime.now(timezone.utc).isoformat(),
        )

        # Create rollback checkpoint if enabled
        if self.enable_rollback:
            self.rollback_checkpoints[consensus_id] = {
                "state": "initiated",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "votes": [],
                "reasoning_chains": [],
            }

        logger.info(
            f"Enhanced consensus started: {consensus_id} "
            f"(proposal: {proposal or 'none'})"
        )

    def add_vote(
        self,
        consensus_id: str,
        agent_id: str,
        decision: str,
        confidence: float,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Add a vote to a consensus process (base implementation).

        Args:
            consensus_id: Consensus process identifier
            agent_id: Agent submitting the vote
            decision: Agent's decision
            confidence: Confidence level (0.0 to 1.0)
            metadata: Optional metadata
        """
        # Call base implementation
        super().add_vote(consensus_id, agent_id, decision, confidence, metadata)

        # Update provenance
        if consensus_id in self.decision_provenance:
            self.decision_provenance[consensus_id].participating_agents = list(
                set(
                    self.decision_provenance[consensus_id].participating_agents
                    + [agent_id]
                )
            )
            self.decision_provenance[consensus_id].votes_cast += 1

    def add_vote_with_reasoning(
        self,
        consensus_id: str,
        agent_id: str,
        decision: str,
        confidence: float,
        reasoning_chain: List[Dict[str, Any]],
        pattern_references: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Optional[str]:
        """
        Add a vote with full reasoning chain.

        Args:
            consensus_id: Consensus process identifier
            agent_id: Agent submitting the vote
            decision: Agent's decision
            confidence: Confidence level (0.0 to 1.0)
            reasoning_chain: List of reasoning steps
            pattern_references: Optional pattern library references
            metadata: Optional metadata

        Returns:
            Chain ID if successful, None otherwise
        """
        # Create base vote
        vote = Vote(
            agent_id=agent_id,
            decision=decision,
            confidence=confidence,
            timestamp=datetime.now(timezone.utc).isoformat(),
            metadata=metadata or {},
        )

        # Build reasoning chain
        chain = ReasoningChain(chain_id=f"chain-{consensus_id}-{agent_id}", agent_id=agent_id, steps=[])

        for step_data in reasoning_chain:
            step = chain.add_step(
                step_type=step_data.get("type", "inference"),
                content=step_data.get("content", ""),
                confidence=step_data.get("confidence", 0.5),
                sources=step_data.get("sources", []),
            )

        # Validate the chain
        chain.validate_chain()

        # Create enhanced vote
        enhanced_vote = EnhancedVote(
            vote=vote,
            reasoning_chain=chain,
            pattern_references=pattern_references or [],
        )

        # Store enhanced vote
        if consensus_id in self.enhanced_votes:
            self.enhanced_votes[consensus_id].append(enhanced_vote)
            self.reasoning_chains[consensus_id].append(chain)

            # Update provenance
            if pattern_references:
                self.decision_provenance[consensus_id].patterns_used.extend(
                    pattern_references
                )
            self.decision_provenance[consensus_id].reasoning_chains.append(chain)

            # Update rollback checkpoint
            if self.enable_rollback and consensus_id in self.rollback_checkpoints:
                self.rollback_checkpoints[consensus_id]["votes"].append({
                    "agent_id": agent_id,
                    "decision": decision,
                    "confidence": confidence,
                    "chain_id": chain.chain_id,
                })

            logger.info(
                f"Vote with reasoning added: {agent_id} -> {decision} "
                f"(chain: {chain.chain_id}, status: {chain.status.value})"
            )

            return chain.chain_id

        return None

    def compute_consensus(
        self,
        consensus_id: str,
    ) -> Optional[ConsensusResult]:
        """
        Compute consensus with enhanced validation.

        Args:
            consensus_id: Consensus process identifier

        Returns:
            Consensus result or None
        """
        # Perform cross-validation if enabled
        if self.enable_cross_validation:
            self._cross_validate_reasoning(consensus_id)

        # Call base implementation
        result = super().compute_consensus(consensus_id)

        if result:
            # Update provenance
            if consensus_id in self.decision_provenance:
                self.decision_provenance[consensus_id].end_time = datetime.now(
                    timezone.utc
                ).isoformat()
                self.decision_provenance[consensus_id].validation_results = (
                    self._get_validation_results(consensus_id)
                )
                self.decision_provenance[consensus_id].rollback_available = (
                    self.enable_rollback
                )
                if self.enable_rollback:
                    self.decision_provenance[consensus_id].rollback_checkpoint = (
                        self.rollback_checkpoints.get(consensus_id)
                    )

            # Update rollback checkpoint state
            if self.enable_rollback and consensus_id in self.rollback_checkpoints:
                self.rollback_checkpoints[consensus_id]["state"] = "completed"
                self.rollback_checkpoints[consensus_id]["result"] = {
                    "decision": result.decision,
                    "confidence": result.confidence,
                }

        return result

    def compute_consensus_with_validation(
        self,
        consensus_id: str,
        min_validation_score: float = 0.6,
    ) -> Optional[ConsensusResult]:
        """
        Compute consensus with validation score threshold.

        Args:
            consensus_id: Consensus process identifier
            min_validation_score: Minimum validation score required

        Returns:
            Consensus result or None if validation fails
        """
        # Perform cross-validation
        validation_results = self._cross_validate_reasoning(consensus_id)

        # Check if validation passes threshold
        avg_validation_score = statistics.mean(
            v.validation_score for v in self.enhanced_votes.get(consensus_id, [])
            if v.cross_validated
        ) if self.enhanced_votes.get(consensus_id) else 0.0

        if avg_validation_score < min_validation_score:
            logger.warning(
                f"Validation score {avg_validation_score:.2f} below threshold "
                f"{min_validation_score:.2f} for {consensus_id}"
            )
            self.process_states[consensus_id] = ConsensusState.FAILED
            return None

        # Compute consensus
        return self.compute_consensus(consensus_id)

    def _cross_validate_reasoning(
        self,
        consensus_id: str,
    ) -> Dict[str, Any]:
        """
        Cross-validate reasoning chains across all votes.

        Args:
            consensus_id: Consensus process identifier

        Returns:
            Validation results dictionary
        """
        if not self.enable_cross_validation:
            return {"status": "disabled"}

        enhanced_votes = self.enhanced_votes.get(consensus_id, [])
        chains = self.reasoning_chains.get(consensus_id, [])

        validation_results = {
            "total_chains": len(chains),
            "valid_chains": 0,
            "invalid_chains": 0,
            "cross_validations": [],
        }

        # Validate individual chains
        for chain in chains:
            if chain.status == ReasoningChainStatus.VALID:
                validation_results["valid_chains"] += 1
            else:
                validation_results["invalid_chains"] += 1

        # Cross-validate between chains (check for consistency)
        decisions_by_chain: Dict[str, str] = {}
        for ev in enhanced_votes:
            if ev.reasoning_chain:
                decisions_by_chain[ev.reasoning_chain.chain_id] = ev.decision

        # Check for contradictory reasoning supporting same decision
        for i, chain1 in enumerate(chains):
            for chain2 in chains[i + 1 :]:
                if chain1.status == ReasoningChainStatus.VALID and chain2.status == ReasoningChainStatus.VALID:
                    # Check if chains reference contradictory patterns
                    if self.enable_pattern_library:
                        common_patterns = set(chain1.pattern_references) & set(
                            chain2.pattern_references
                        )
                        if common_patterns:
                            # Chains share pattern references - check consistency
                            decision1 = decisions_by_chain.get(chain1.chain_id)
                            decision2 = decisions_by_chain.get(chain2.chain_id)
                            if decision1 != decision2:
                                validation_results["cross_validations"].append({
                                    "chain1": chain1.chain_id,
                                    "chain2": chain2.chain_id,
                                    "issue": "contradictory_conclusions",
                                    "shared_patterns": list(common_patterns),
                                })

        # Calculate validation scores for each enhanced vote
        for ev in enhanced_votes:
            if ev.reasoning_chain:
                if ev.reasoning_chain.status == ReasoningChainStatus.VALID:
                    ev.validation_score = 0.8 + (0.2 * ev.confidence)
                else:
                    ev.validation_score = 0.3
                ev.cross_validated = True

        validation_results["average_validation_score"] = (
            statistics.mean(
                ev.validation_score
                for ev in enhanced_votes
                if ev.cross_validated
            )
            if enhanced_votes
            else 0.0
        )

        # Store validation results in provenance
        if consensus_id in self.decision_provenance:
            self.decision_provenance[consensus_id].validation_results = (
                validation_results
            )

        logger.info(
            f"Cross-validation complete for {consensus_id}: "
            f"{validation_results['valid_chains']}/{validation_results['total_chains']} "
            f"valid chains"
        )

        return validation_results

    def _get_validation_results(
        self,
        consensus_id: str,
    ) -> Dict[str, Any]:
        """
        Get validation results for a consensus.

        Args:
            consensus_id: Consensus identifier

        Returns:
            Validation results dictionary
        """
        if consensus_id in self.decision_provenance:
            return self.decision_provenance[consensus_id].validation_results
        return {}

    def get_decision_provenance(
        self,
        consensus_id: str,
    ) -> Optional[DecisionProvenance]:
        """
        Get complete provenance for a decision.

        Args:
            consensus_id: Consensus identifier

        Returns:
            Decision provenance or None
        """
        return self.decision_provenance.get(consensus_id)

    def get_reasoning_chains(
        self,
        consensus_id: str,
    ) -> List[ReasoningChain]:
        """
        Get all reasoning chains for a consensus.

        Args:
            consensus_id: Consensus identifier

        Returns:
            List of reasoning chains
        """
        return self.reasoning_chains.get(consensus_id, [])

    def rollback_decision(
        self,
        consensus_id: str,
        reason: Optional[str] = None,
    ) -> RollbackResult:
        """
        Rollback a decision to its pre-consensus state.

        Args:
            consensus_id: Consensus identifier
            reason: Optional reason for rollback

        Returns:
            Rollback result
        """
        if not self.enable_rollback:
            return RollbackResult(
                success=False,
                message="Rollback is not enabled",
            )

        if consensus_id not in self.rollback_checkpoints:
            return RollbackResult(
                success=False,
                message=f"No rollback checkpoint found for {consensus_id}",
            )

        checkpoint = self.rollback_checkpoints[consensus_id]

        if checkpoint.get("state") != "completed":
            return RollbackResult(
                success=False,
                message=f"Decision not in completed state: {checkpoint.get('state')}",
            )

        # Perform rollback
        try:
            # Clear votes and reset state
            if consensus_id in self.active_processes:
                self.active_processes[consensus_id] = []
            if consensus_id in self.process_states:
                self.process_states[consensus_id] = ConsensusState.GATHERING

            # Update provenance
            if consensus_id in self.decision_provenance:
                self.decision_provenance[consensus_id].rollback_available = False

            # Clear checkpoint
            del self.rollback_checkpoints[consensus_id]

            logger.info(
                f"Rollback completed for {consensus_id}: {reason or 'no reason provided'}"
            )

            return RollbackResult(
                success=True,
                message=f"Decision rolled back: {reason or 'no reason provided'}",
                previous_state=checkpoint,
            )

        except Exception as e:
            logger.error(f"Rollback failed: {e}")
            return RollbackResult(
                success=False,
                message=f"Rollback failed: {str(e)}",
            )

    def export_provenance(
        self,
        consensus_id: str,
    ) -> Optional[Dict[str, Any]]:
        """
        Export decision provenance for external audit.

        Args:
            consensus_id: Consensus identifier

        Returns:
            Serializable provenance dictionary or None
        """
        provenance = self.decision_provenance.get(consensus_id)
        if not provenance:
            return None

        return {
            "decision_id": provenance.decision_id,
            "proposal": provenance.proposal,
            "start_time": provenance.start_time,
            "end_time": provenance.end_time,
            "participating_agents": provenance.participating_agents,
            "votes_cast": provenance.votes_cast,
            "reasoning_chains": [
                {
                    "chain_id": chain.chain_id,
                    "agent_id": chain.agent_id,
                    "status": chain.status.value,
                    "steps": [
                        {
                            "step_number": step.step_number,
                            "step_type": step.step_type,
                            "content": step.content,
                            "confidence": step.confidence,
                        }
                        for step in chain.steps
                    ],
                    "validation_errors": chain.validation_errors,
                }
                for chain in provenance.reasoning_chains
            ],
            "patterns_used": provenance.patterns_used,
            "validation_results": provenance.validation_results,
            "rollback_available": provenance.rollback_available,
        }

    def get_enhanced_statistics(self) -> Dict[str, Any]:
        """
        Get enhanced consensus statistics.

        Returns:
            Statistics dictionary
        """
        base_stats = self.get_statistics()

        total_chains = sum(
            len(chains) for chains in self.reasoning_chains.values()
        )
        valid_chains = sum(
            sum(1 for c in chains if c.status == ReasoningChainStatus.VALID)
            for chains in self.reasoning_chains.values()
        )

        return {
            **base_stats,
            "total_reasoning_chains": total_chains,
            "valid_reasoning_chains": valid_chains,
            "chain_validity_rate": (
                valid_chains / total_chains if total_chains > 0 else 0.0
            ),
            "provenance_tracked": len(self.decision_provenance),
            "rollbacks_available": sum(
                1 for p in self.decision_provenance.values()
                if p.rollback_available
            ),
        }

    def register_pattern(
        self,
        pattern_id: str,
        pattern_data: Dict[str, Any],
    ) -> None:
        """
        Register a pattern in the pattern library.

        Args:
            pattern_id: Pattern identifier
            pattern_data: Pattern data
        """
        self.pattern_library[pattern_id] = pattern_data
        logger.debug(f"Registered pattern: {pattern_id}")

    def get_pattern(
        self,
        pattern_id: str,
    ) -> Optional[Dict[str, Any]]:
        """
        Get pattern from the pattern library.

        Args:
            pattern_id: Pattern identifier

        Returns:
            Pattern data or None
        """
        return self.pattern_library.get(pattern_id)

    def generate_decision_hash(
        self,
        consensus_id: str,
    ) -> Optional[str]:
        """
        Generate cryptographic hash of decision for integrity verification.

        Args:
            consensus_id: Consensus identifier

        Returns:
            SHA-256 hash or None
        """
        provenance = self.decision_provenance.get(consensus_id)
        if not provenance or not provenance.end_time:
            return None

        # Create hashable data
        data = {
            "decision_id": provenance.decision_id,
            "proposal": provenance.proposal,
            "start_time": provenance.start_time,
            "end_time": provenance.end_time,
            "participating_agents": sorted(provenance.participating_agents),
            "votes_cast": provenance.votes_cast,
        }

        # Generate hash
        data_json = json.dumps(data, sort_keys=True)
        return hashlib.sha256(data_json.encode()).hexdigest()
