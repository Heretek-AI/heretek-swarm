"""
Enhanced MAKER Consensus Deliberation Module.

This module implements multi-round deliberation with:
- Argument/counter-argument structure
- Evidence quality weighting
- Consensus confidence scoring
- Dissent tracking and resolution

The deliberation system facilitates structured group decision-making
by allowing agents to exchange arguments, evaluate evidence quality,
and converge toward consensus through iterative rounds.

Example:
    ```python
    from heretek_swarm.consensus.deliberation import (
        DeliberationEngine,
        DeliberationConfig,
        Argument,
        CounterArgument,
        Evidence,
    )

    # Initialize engine
    config = DeliberationConfig(max_rounds=5, consensus_threshold=0.75)
    _engine = DeliberationEngine(config)

    # Start deliberation
    engine.start_deliberation(
        _topic = "Deploy to production",
        _participants = ["agent-1", "agent-2", "agent-3"]
    )

    # Submit argument with evidence
    engine.submit_argument(
        agent_id="agent-1",
        position="for",
        _reasoning = "All tests passed",
        evidence_refs=["test-report-001"],
        confidence=0.9
    )

    # Run deliberation
    _result = await engine.run_deliberation()
    ```
"""

import hashlib
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

import structlog

_logger = structlog.get_logger("DeliberationEngine")


class Position(Enum):
    """Position options in deliberation."""
    FOR = "for"
    AGAINST = "against"
    NEUTRAL = "neutral"


class DeliberationOutcome(Enum):
    """Possible deliberation outcomes."""
    CONSENSUS = "consensus"
    MAJORITY = "majority"
    DEADLOCK = "deadlock"
    TIMEOUT = "timeout"
    WITHDRAWN = "withdrawn"


class ArgumentType(Enum):
    """Types of arguments."""
    PRIMARY = "primary"
    SUPPORTING = "supporting"
    COUNTER = "counter"
    REBUTTAL = "rebuttal"


class EvidenceType(Enum):
    """Types of evidence."""
    DATA = "data"
    TEST_RESULT = "test_result"
    EXPERT_OPINION = "expert_opinion"
    HISTORICAL = "historical"
    LOGICAL = "logical"
    SIMULATION = "simulation"


@dataclass
class Evidence:
    """
    Evidence submitted to support an argument.

    Attributes:
        evidence_id: Unique identifier
        evidence_type: Type of evidence
        content: Evidence content or reference
        source: Source of the evidence
        reliability_score: Reliability rating (0.0-1.0)
        timestamp: Submission timestamp
        submitted_by: Agent who submitted evidence
    """
    evidence_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    evidence_type: EvidenceType = EvidenceType.DATA
    content: str = ""
    source: Optional[str] = None
    reliability_score: float = 0.5
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    submitted_by: str = ""

    def calculate_quality(self) -> float:
        """
        Calculate evidence quality score.

        Returns:
            Quality score (0.0-1.0)
        """
        # Base quality from reliability
        _base_quality = self.reliability_score

        # Type-based modifiers
        _type_modifiers = {
            EvidenceType.DATA: 1.0,
            EvidenceType.TEST_RESULT: 0.95,
            EvidenceType.EXPERT_OPINION: 0.8,
            EvidenceType.HISTORICAL: 0.85,
            EvidenceType.LOGICAL: 0.9,
            EvidenceType.SIMULATION: 0.75,
        }

        _type_modifier = type_modifiers.get(self.evidence_type, 0.8)

        # Source verification bonus
        _source_bonus = 0.1 if self.source else 0.0

        return min(1.0, base_quality * type_modifier + source_bonus)


@dataclass
class Argument:
    """
    An argument submitted during deliberation.

    Attributes:
        argument_id: Unique identifier
        agent_id: Submitting agent
        position: Position (for/against/neutral)
        reasoning: Argument reasoning text
        evidence_refs: References to supporting evidence
        confidence: Confidence in argument (0.0-1.0)
        argument_type: Type of argument
        supports: IDs of arguments this supports
        rebuttals: IDs of arguments this rebuts
        timestamp: Submission timestamp
    """
    argument_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    agent_id: str = ""
    position: Position = Position.NEUTRAL
    reasoning: str = ""
    evidence_refs: List[str] = field(default_factory=list)
    confidence: float = 0.5
    argument_type: ArgumentType = ArgumentType.PRIMARY
    supports: List[str] = field(default_factory=list)
    rebuttals: List[str] = field(default_factory=list)
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    expertise_weight: float = 1.0

    def calculate_strength(self, _evidence_dict: Dict[str, _Evidence]) -> float:
        """
        Calculate argument strength based on evidence and confidence.

        Args:
            evidence_dict: Dictionary of evidence by ID

        Returns:
            Strength score (0.0-1.0)
        """
        # Base strength from confidence
        _base_strength = self.confidence

        # Evidence quality contribution
        _evidence_scores = []
        for ref in self.evidence_refs:
            if ref in evidence_dict:
                evidence_scores.append(evidence_dict[ref].calculate_quality())

        _evidence_contribution = sum(evidence_scores) / len(evidence_scores) if evidence_scores else 0.0

        # Weight evidence at 40%, confidence at 60%
        _strength = 0.6 * base_strength + 0.4 * evidence_contribution

        # Apply expertise weight
        strength *= self.expertise_weight

        return min(1.0, strength)


@dataclass
class CounterArgument:
    """
    A counter-argument responding to another argument.

    Attributes:
        counter_id: Unique identifier
        original_argument_id: ID of argument being countered
        agent_id: Submitting agent
        counter_reasoning: Counter-argument reasoning
        evidence_refs: References to supporting evidence
        confidence: Confidence in counter-argument
        timestamp: Submission timestamp
    """
    counter_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    original_argument_id: str = ""
    agent_id: str = ""
    counter_reasoning: str = ""
    evidence_refs: List[str] = field(default_factory=list)
    confidence: float = 0.5
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    expertise_weight: float = 1.0

    def calculate_effectiveness(self, _evidence_dict: Dict[str, _Evidence]) -> float:
        """
        Calculate counter-argument effectiveness.

        Args:
            evidence_dict: Dictionary of evidence by ID

        Returns:
            Effectiveness score (0.0-1.0)
        """
        # Base effectiveness from confidence
        _base_effectiveness = self.confidence

        # Evidence contribution
        _evidence_scores = []
        for ref in self.evidence_refs:
            if ref in evidence_dict:
                evidence_scores.append(evidence_dict[ref].calculate_quality())

        _evidence_contribution = sum(evidence_scores) / len(evidence_scores) if evidence_scores else 0.0

        # Weight evidence at 40%, confidence at 60%
        _effectiveness = 0.6 * base_effectiveness + 0.4 * evidence_contribution

        # Apply expertise weight
        effectiveness *= self.expertise_weight

        return min(1.0, effectiveness)


@dataclass
class DeliberationRound:
    """
    Results from a single deliberation round.

    Attributes:
        round_id: Unique round identifier
        topic: Deliberation topic
        arguments: Arguments submitted in this round
        counter_arguments: Counter-arguments submitted
        evidence_submitted: New evidence submitted
        participant_agents: Participating agents
        round_duration: Duration of the round
        outcome: Round outcome
        consensus_score: Current consensus score
        position_changes: Number of position changes
    """
    round_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    topic: str = ""
    arguments: List[Argument] = field(default_factory=list)
    counter_arguments: List[CounterArgument] = field(default_factory=list)
    evidence_submitted: List[Evidence] = field(default_factory=list)
    participant_agents: List[str] = field(default_factory=list)
    round_duration: timedelta = timedelta(0)
    outcome: DeliberationOutcome = DeliberationOutcome.DEADLOCK
    consensus_score: float = 0.0
    position_changes: int = 0
    start_time: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    end_time: Optional[str] = None


@dataclass
class DissentRecord:
    """
    Record of dissenting opinion for minority report.

    Attributes:
        agent_id: Dissenting agent
        position: Agent's position
        confidence: Confidence in dissenting position
        reasoning: Reasoning for dissent
        key_arguments: Key arguments supporting dissent
        resolved: Whether dissent was resolved
        resolution_notes: Notes on resolution attempt
    """
    agent_id: str = ""
    position: Position = Position.NEUTRAL
    confidence: float = 0.0
    reasoning: str = ""
    key_arguments: List[str] = field(default_factory=list)
    resolved: bool = False
    resolution_notes: Optional[str] = None


@dataclass
class ConsensusConfidence:
    """
    Consensus confidence scoring.

    Attributes:
        overall_confidence: Overall confidence in consensus
        evidence_quality_avg: Average evidence quality
        agreement_level: Level of agreement
        dissent_count: Number of dissenting agents
        dissent_severity: Severity of dissent
        stability_score: How stable the consensus is
    """
    overall_confidence: float = 0.0
    evidence_quality_avg: float = 0.0
    agreement_level: float = 0.0
    dissent_count: int = 0
    dissent_severity: float = 0.0
    stability_score: float = 0.0

    def calculate(self, _for_weight: float, _against_weight: float, _total_weight: float, _evidence_scores: List[float], _dissent_records: List[DissentRecord]) -> None:
        """
        Calculate consensus confidence.

        Args:
            for_weight: Total weight of 'for' positions
            against_weight: Total weight of 'against' positions
            total_weight: Total weight of all positions
            evidence_scores: List of evidence quality scores
            dissent_records: List of dissent records
        """
        # Agreement level (0.5-1.0)
        if total_weight > 0:
            _majority_weight = max(for_weight, against_weight)
            self.agreement_level = majority_weight / total_weight
        else:
            self.agreement_level = 0.5

        # Evidence quality
        self.evidence_quality_avg = sum(evidence_scores) / len(evidence_scores) if evidence_scores else 0.0

        # Dissent metrics
        self.dissent_count = len(dissent_records)
        if dissent_records:
            self.dissent_severity = sum(d.confidence for d in dissent_records) / len(dissent_records)
        else:
            self.dissent_severity = 0.0

        # Stability based on position changes in recent rounds
        self.stability_score = 1.0 - (self.dissent_severity * 0.3) - ((1 - self.agreement_level) * 0.3)

        # Overall confidence
        self.overall_confidence = (
            0.35 * self.agreement_level +
            0.25 * self.evidence_quality_avg +
            0.20 * self.stability_score +
            0.20 * (1.0 - self.dissent_severity)
        )


@dataclass
class DeliberationResult:
    """
    Final result of a deliberation.

    Attributes:
        deliberation_id: Deliberation identifier
        topic: Deliberation topic
        outcome: Final outcome
        final_position: Final agreed position
        consensus_score: Final consensus score
        confidence: Consensus confidence
        dissenting_agents: Agents who dissented
        minority_report: Summary of minority opinions
        rounds_completed: Number of rounds run
        total_arguments: Total arguments submitted
        total_evidence: Total evidence pieces
        decision_hash: Immutable hash of decision
        timestamp: Result timestamp
    """
    deliberation_id: str = ""
    topic: str = ""
    outcome: DeliberationOutcome = DeliberationOutcome.DEADLOCK
    final_position: Position = Position.NEUTRAL
    consensus_score: float = 0.0
    confidence: ConsensusConfidence = field(default_factory=ConsensusConfidence)
    dissenting_agents: List[str] = field(default_factory=list)
    minority_report: List[DissentRecord] = field(default_factory=list)
    rounds_completed: int = 0
    total_arguments: int = 0
    total_evidence: int = 0
    decision_hash: Optional[str] = None
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


@dataclass
class DeliberationConfig:
    """
    Configuration for deliberation engine.

    Attributes:
        max_rounds: Maximum deliberation rounds
        consensus_threshold: Threshold for consensus
        min_participants: Minimum required participants
        round_timeout_seconds: Timeout per round
        evidence_weight: Weight for evidence in scoring
        expertise_weight: Weight for expertise in scoring
        dissent_tracking: Enable dissent tracking
    """
    max_rounds: int = 5
    consensus_threshold: float = 0.75
    min_participants: int = 3
    round_timeout_seconds: float = 300.0
    evidence_weight: float = 0.35
    expertise_weight: float = 0.30
    dissent_tracking: bool = True


class DeliberationEngine:
    """
    Enhanced Deliberation Engine for multi-round consensus.

    This engine implements:
    - Multi-round deliberation with argument exchange
    - Evidence quality weighting
    - Consensus confidence scoring
    - Dissent tracking and minority reports

    Attributes:
        config: Deliberation configuration
        expertise_profiler: Optional expertise profiler
    """

    def __init__(self, _config: Optional[DeliberationConfig], _expertise_profiler):  # AgentExpertiseProfiler type
        """
        Initialize deliberation engine.

        Args:
            config: Deliberation configuration
            expertise_profiler: Optional expertise profiler for weighting
        """
        self.config = config or DeliberationConfig()
        self.expertise_profiler = expertise_profiler

        # Active deliberations
        self.active_deliberations: Dict[str, Dict[str, Any]] = {}
        self.deliberation_states: Dict[str, str] = {}

        # Evidence storage
        self.evidence_store: Dict[str, Dict[str, Evidence]] = {}

        # Round tracking
        self.current_rounds: Dict[str, int] = {}
        self.round_results: Dict[str, List[DeliberationRound]] = {}

        # Dissent tracking
        self.dissent_records: Dict[str, List[DissentRecord]] = {}

        logger.info(
            f"DeliberationEngine initialized with max_rounds={self.config.max_rounds}, "
            f"consensus_threshold={self.config.consensus_threshold:.2f}"
        )

    def start_deliberation(self, _topic: str, _participants: List[str], _deliberation_id: Optional[str], _domain: Optional[str]) -> str:
        """
        Start a new deliberation process.

        Args:
            topic: Topic to deliberate
            participants: List of participating agent IDs
            deliberation_id: Optional custom ID
            domain: Optional domain for expertise weighting

        Returns:
            Deliberation ID
        """
        if deliberation_id is None:
            _deliberation_id = str(uuid.uuid4())

        if len(participants) < self.config.min_participants:
            logger.warning(
                f"Insufficient participants: {len(participants)} < {self.config.min_participants}"
            )

        self.active_deliberations[deliberation_id] = {
            "topic": topic,
            "participants": set(participants),
            "domain": domain,
            "arguments": [],
            "counter_arguments": [],
            "evidence": {},
            "positions": {},
            "start_time": datetime.now(timezone.utc).isoformat(),
        }

        self.deliberation_states[deliberation_id] = "gathering_positions"
        self.current_rounds[deliberation_id] = 0
        self.round_results[deliberation_id] = []
        self.evidence_store[deliberation_id] = {}
        self.dissent_records[deliberation_id] = []

        logger.info(
            f"Started deliberation {deliberation_id}: '{topic}' "
            f"with {len(participants)} participants"
        )

        return deliberation_id

    def submit_argument(self, _deliberation_id: str, _agent_id: str, _position: Position, _reasoning: str, _evidence_refs: Optional[List[str]], _confidence: float, _argument_type: ArgumentType, _supports: Optional[List[str]], _rebuttals: Optional[List[str]]) -> Optional[str]:
        """
        Submit an argument to the deliberation.

        Args:
            deliberation_id: Deliberation identifier
            agent_id: Agent submitting argument
            position: Position (for/against/neutral)
            reasoning: Argument reasoning
            evidence_refs: References to supporting evidence
            confidence: Confidence in argument
            argument_type: Type of argument
            supports: IDs of arguments this supports
            rebuttals: IDs of arguments this rebuts

        Returns:
            Argument ID if accepted, None otherwise
        """
        if deliberation_id not in self.active_deliberations:
            logger.warning(f"Unknown deliberation: {deliberation_id}")
            return None

        if agent_id not in self.active_deliberations[deliberation_id]["participants"]:
            logger.warning(f"Agent {agent_id} not a participant")
            return None

        # Calculate expertise weight
        _expertise_weight = 1.0
        _domain = self.active_deliberations[deliberation_id].get("domain")
        if self.expertise_profiler and domain:
            _expertise_weight = self.expertise_profiler.get_expertise_score(agent_id, domain)

        argument = Argument(
            argument_id=f"arg-{deliberation_id}-{len(self.active_deliberations[deliberation_id]['arguments']) + 1}",
            agent_id=agent_id,
            position=position,
            _reasoning = reasoning,
            _evidence_refs = evidence_refs or [],
            _confidence = confidence,
            _argument_type = argument_type,
            _supports = supports or [],
            _rebuttals = rebuttals or [],
            _expertise_weight = expertise_weight,
        )

        self.active_deliberations[deliberation_id]["arguments"].append(argument)

        # Update agent position
        self.active_deliberations[deliberation_id]["positions"][agent_id] = {
            "position": position,
            "confidence": confidence,
            "last_argument": argument.argument_id,
        }

        logger.debug(
            f"Argument submitted in {deliberation_id}: {argument.argument_id} "
            f"by {agent_id} ({position.value})"
        )

        return argument.argument_id

    def submit_counter_argument(self, _deliberation_id: str, _agent_id: str, _original_argument_id: str, _counter_reasoning: str, _evidence_refs: Optional[List[str]], _confidence: float) -> Optional[str]:
        """
        Submit a counter-argument.

        Args:
            deliberation_id: Deliberation identifier
            agent_id: Agent submitting counter-argument
            original_argument_id: ID of argument being countered
            counter_reasoning: Counter-argument reasoning
            evidence_refs: References to supporting evidence
            confidence: Confidence in counter-argument

        Returns:
            Counter-argument ID if accepted, None otherwise
        """
        if deliberation_id not in self.active_deliberations:
            return None

        # Calculate expertise weight
        _expertise_weight = 1.0
        _domain = self.active_deliberations[deliberation_id].get("domain")
        if self.expertise_profiler and domain:
            _expertise_weight = self.expertise_profiler.get_expertise_score(agent_id, domain)

        counter = CounterArgument(
            counter_id=f"counter-{deliberation_id}-{len(self.active_deliberations[deliberation_id]['counter_arguments']) + 1}",
            _original_argument_id = original_argument_id,
            agent_id=agent_id,
            _counter_reasoning = counter_reasoning,
            _evidence_refs = evidence_refs or [],
            _confidence = confidence,
            _expertise_weight = expertise_weight,
        )

        self.active_deliberations[deliberation_id]["counter_arguments"].append(counter)

        logger.debug(
            f"Counter-argument submitted in {deliberation_id}: {counter.counter_id} "
            f"by {agent_id}"
        )

        return counter.counter_id

    def submit_evidence(self, _deliberation_id: str, _evidence_type: EvidenceType, _content: str, _source: Optional[str], _reliability_score: float, _submitted_by: str) -> Optional[str]:
        """
        Submit evidence to support arguments.

        Args:
            deliberation_id: Deliberation identifier
            evidence_type: Type of evidence
            content: Evidence content
            source: Evidence source
            reliability_score: Reliability rating
            submitted_by: Agent submitting evidence

        Returns:
            Evidence ID if accepted, None otherwise
        """
        if deliberation_id not in self.active_deliberations:
            return None

        evidence = Evidence(
            _evidence_type = evidence_type,
            _content = content,
            _source = source,
            _reliability_score = reliability_score,
            _submitted_by = submitted_by,
        )

        self.active_deliberations[deliberation_id]["evidence"][evidence.evidence_id] = evidence
        self.evidence_store[deliberation_id][evidence.evidence_id] = evidence

        logger.debug(
            f"Evidence submitted in {deliberation_id}: {evidence.evidence_id} "
            f"(type: {evidence_type.value}, reliability: {reliability_score:.2f})"
        )

        return evidence.evidence_id

    def run_deliberation_round(self, _deliberation_id: str) -> Optional[DeliberationRound]:
        """
        Run a single round of deliberation.

        Args:
            deliberation_id: Deliberation identifier

        Returns:
            Round results or None if deliberation not active
        """
        if deliberation_id not in self.active_deliberations:
            return None

        _start_time = datetime.now(timezone.utc)
        self.current_rounds[deliberation_id] += 1
        current_round = self.current_rounds[deliberation_id]

        # Get current state
        _data = self.active_deliberations[deliberation_id]
        arguments = data["arguments"].copy()
        _counter_arguments = data["counter_arguments"].copy()
        evidence = list(data["evidence"].values())

        # Calculate consensus score
        _consensus_score = self._calculate_consensus_score(deliberation_id)

        # Count position changes
        _position_changes = self._count_position_changes(deliberation_id)

        # Determine round outcome
        if consensus_score >= self.config.consensus_threshold:
            _outcome = DeliberationOutcome.CONSENSUS
        elif current_round >= self.config.max_rounds:
            _outcome = DeliberationOutcome.MAJORITY if consensus_score > 0.5 else DeliberationOutcome.DEADLOCK
        else:
            _outcome = DeliberationOutcome.DEADLOCK

        _end_time = datetime.now(timezone.utc)
        round_result = DeliberationRound(
            _topic = data["topic"],
            arguments=arguments,
            _counter_arguments = counter_arguments,
            _evidence_submitted = evidence,
            _participant_agents = list(data["participants"]),
            _round_duration = end_time - start_time,
            _outcome = outcome,
            _consensus_score = consensus_score,
            _position_changes = position_changes,
            _end_time = end_time.isoformat(),
        )

        self.round_results[deliberation_id].append(round_result)

        # Update state
        if outcome == DeliberationOutcome.CONSENSUS:
            self.deliberation_states[deliberation_id] = "completed"
        elif current_round >= self.config.max_rounds:
            self.deliberation_states[deliberation_id] = "completed"

        logger.info(
            f"Round {current_round} complete for {deliberation_id}: "
            f"consensus={consensus_score:.2f}, outcome={outcome.value}"
        )

        return round_result

    def _calculate_consensus_score(self, _deliberation_id: str) -> float:
        """
        Calculate current consensus score.

        Args:
            deliberation_id: Deliberation identifier

        Returns:
            Consensus score (0.0-1.0)
        """
        _data = self.active_deliberations[deliberation_id]
        _positions = data.get("positions", {})
        _arguments = data.get("arguments", [])
        evidence = data.get("evidence", {})

        if not positions:
            return 0.0

        # Calculate weighted positions
        _for_weight = 0.0
        _against_weight = 0.0
        _neutral_weight = 0.0

        for agent_id, pos_data in positions.items():
            _weight = 1.0
            if self.expertise_profiler and data.get("domain"):
                _weight = self.expertise_profiler.get_expertise_score(agent_id, data["domain"])

            # Apply argument strength
            _agent_args = [a for a in arguments if a.agent_id == agent_id]
            if agent_args:
                _arg_strength = max(a.calculate_strength(evidence) for a in agent_args)
                weight *= arg_strength

            if pos_data["position"] == Position.FOR:
                for_weight += weight * pos_data["confidence"]
            elif pos_data["position"] == Position.AGAINST:
                against_weight += weight * pos_data["confidence"]
            else:
                neutral_weight += weight * pos_data["confidence"]

        _total_weight = for_weight + against_weight + neutral_weight

        if total_weight == 0:
            return 0.0

        # Consensus is higher when one side dominates
        _majority_weight = max(for_weight, against_weight)
        consensus = majority_weight / total_weight

        return consensus

    def _count_position_changes(self, _deliberation_id: str) -> int:
        """Count position changes across rounds."""
        _rounds = self.round_results.get(deliberation_id, [])
        if len(rounds) < 2:
            return 0

        _changes = 0
        _prev_positions = {}

        for round_result in rounds:
            for arg in round_result.arguments:
                agent_id = arg.agent_id
                if agent_id in prev_positions:
                    if prev_positions[agent_id] != arg.position:
                        changes += 1
                prev_positions[agent_id] = arg.position

        return changes

    def track_dissent(self, _deliberation_id: str, _agent_id: str, _reasoning: str) -> None:
        """
        Track dissenting opinion for minority report.

        Args:
            deliberation_id: Deliberation identifier
            agent_id: Dissenting agent
            reasoning: Reasoning for dissent
        """
        if deliberation_id not in self.active_deliberations:
            return

        _positions = self.active_deliberations[deliberation_id].get("positions", {})
        if agent_id not in positions:
            return

        _pos_data = positions[agent_id]

        # Get agent's key arguments
        _arguments = self.active_deliberations[deliberation_id].get("arguments", [])
        _agent_args = [a.argument_id for a in arguments if a.agent_id == agent_id]

        dissent = DissentRecord(
            agent_id=agent_id,
            _position = pos_data["position"],
            _confidence = pos_data["confidence"],
            _reasoning = reasoning,
            _key_arguments = agent_args,
        )

        self.dissent_records[deliberation_id].append(dissent)

        logger.info(f"Dissent tracked for agent {agent_id} in {deliberation_id}")

    def calculate_consensus_confidence(self, _deliberation_id: str) -> ConsensusConfidence:
        """
        Calculate consensus confidence for a deliberation.

        Args:
            deliberation_id: Deliberation identifier

        Returns:
            Consensus confidence
        """
        _data = self.active_deliberations[deliberation_id]
        evidence = data.get("evidence", {})

        # Calculate weights
        for_weight, against_weight, total_weight = self._calculate_position_weights(deliberation_id)

        # Get evidence scores
        _evidence_scores = [e.calculate_quality() for e in evidence.values()]

        # Get dissent records
        dissent_records = self.dissent_records.get(deliberation_id, [])

        _confidence = ConsensusConfidence()
        confidence.calculate(for_weight, against_weight, total_weight, evidence_scores, dissent_records)

        return confidence

    def _calculate_position_weights(self, _deliberation_id: str) -> Tuple[float, float, float]:
        """Calculate position weights for consensus scoring."""
        _data = self.active_deliberations[deliberation_id]
        _positions = data.get("positions", {})
        _arguments = data.get("arguments", [])
        evidence = data.get("evidence", {})

        _for_weight = 0.0
        _against_weight = 0.0
        _total_weight = 0.0

        for agent_id, pos_data in positions.items():
            _weight = 1.0
            if self.expertise_profiler and data.get("domain"):
                _weight = self.expertise_profiler.get_expertise_score(agent_id, data["domain"])

            _agent_args = [a for a in arguments if a.agent_id == agent_id]
            if agent_args:
                _arg_strength = max(a.calculate_strength(evidence) for a in agent_args)
                weight *= arg_strength

            _weighted_confidence = weight * pos_data["confidence"]
            total_weight += weighted_confidence

            if pos_data["position"] == Position.FOR:
                for_weight += weighted_confidence
            elif pos_data["position"] == Position.AGAINST:
                against_weight += weighted_confidence

        return for_weight, against_weight, total_weight

    def finalize_deliberation(self, _deliberation_id: str) -> Optional[DeliberationResult]:
        """
        Finalize deliberation and return result.

        Args:
            deliberation_id: Deliberation identifier

        Returns:
            Deliberation result or None
        """
        if deliberation_id not in self.active_deliberations:
            return None

        self.deliberation_states[deliberation_id] = "completed"

        _data = self.active_deliberations[deliberation_id]
        _arguments = data.get("arguments", [])
        evidence = data.get("evidence", {})

        # Calculate final consensus
        _consensus_score = self._calculate_consensus_score(deliberation_id)

        # Determine final position
        for_weight, against_weight, _ = self._calculate_position_weights(deliberation_id)
        if for_weight > against_weight:
            _final_position = Position.FOR
        elif against_weight > for_weight:
            _final_position = Position.AGAINST
        else:
            _final_position = Position.NEUTRAL

        # Determine outcome
        if consensus_score >= self.config.consensus_threshold:
            _outcome = DeliberationOutcome.CONSENSUS
        elif consensus_score > 0.5:
            _outcome = DeliberationOutcome.MAJORITY
        else:
            _outcome = DeliberationOutcome.DEADLOCK

        # Calculate confidence
        _confidence = self.calculate_consensus_confidence(deliberation_id)

        # Get dissenting agents
        _dissenting_agents = [d.agent_id for d in self.dissent_records.get(deliberation_id, [])]
        _minority_report = self.dissent_records.get(deliberation_id, [])

        # Generate decision hash
        _decision_data = {
            "deliberation_id": deliberation_id,
            "topic": data["topic"],
            "final_position": final_position.value,
            "consensus_score": consensus_score,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        _decision_hash = hashlib.sha256(
            str(sorted(decision_data.items())).encode()
        ).hexdigest()

        _result = DeliberationResult(
            _deliberation_id = deliberation_id,
            _topic = data["topic"],
            _outcome = outcome,
            _final_position = final_position,
            _consensus_score = consensus_score,
            _confidence = confidence,
            _dissenting_agents = dissenting_agents,
            _minority_report = minority_report,
            _rounds_completed = self.current_rounds[deliberation_id],
            _total_arguments = len(arguments),
            _total_evidence = len(evidence),
            _decision_hash = decision_hash,
        )

        logger.info(
            f"Deliberation {deliberation_id} finalized: "
            f"{final_position.value} (consensus: {consensus_score:.2f})"
        )

        return result

    def get_deliberation_state(self, _deliberation_id: str) -> Optional[str]:
        """Get current state of a deliberation."""
        return self.deliberation_states.get(deliberation_id)

    def get_position_distribution(self, _deliberation_id: str) -> Dict[str, float]:
        """Get distribution of positions as percentages."""
        if deliberation_id not in self.active_deliberations:
            return {}

        _positions = self.active_deliberations[deliberation_id].get("positions", {})
        _total = len(positions)

        if total == 0:
            return {}

        distribution: Dict[str, int] = {}
        for pos_data in positions.values():
            _key = pos_data["position"].value
            distribution[key] = distribution.get(key, 0) + 1

        return {k: v / total for k, v in distribution.items()}

    def get_round_history(self, _deliberation_id: str) -> List[DeliberationRound]:
        """Get complete round history for a deliberation."""
        return self.round_results.get(deliberation_id, [])

    def get_statistics(self) -> Dict[str, Any]:
        """Get deliberation engine statistics."""
        _active_count = len(self.active_deliberations)
        _completed_count = sum(1 for s in self.deliberation_states.values() if s == "completed")

        return {
            "active_deliberations": active_count,
            "completed_deliberations": completed_count,
            "max_rounds": self.config.max_rounds,
            "consensus_threshold": self.config.consensus_threshold,
            "min_participants": self.config.min_participants,
            "dissent_tracking_enabled": self.config.dissent_tracking,
        }

    def cleanup_deliberation(self, _deliberation_id: str) -> None:
        """Clean up a completed deliberation."""
        for store in [self.active_deliberations, self.deliberation_states,
                      self.current_rounds, self.round_results,
                      self.evidence_store, self.dissent_records]:
            if deliberation_id in store:
                del store[deliberation_id]

        logger.debug(f"Cleaned up deliberation {deliberation_id}")
