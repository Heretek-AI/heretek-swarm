"""
Decision Audit Trail - Complete decision history with reasoning and outcome tracking.

This module provides comprehensive audit capabilities for consensus decisions:
- Complete decision history with reasoning
- Vote breakdowns and argument logs
- Outcome tracking for learning
- Export capabilities for analysis

The audit system maintains an immutable record of all consensus decisions,
enabling post-hoc analysis, compliance reporting, and continuous improvement.

Example:
    ```python
    from heretek_swarm.consensus.audit import ConsensusAuditTrail

    # Initialize audit trail
    audit = ConsensusAuditTrail(
        storage_backend="postgresql",
        retention_days=90
    )

    # Record a decision
    audit.record_decision(
        decision_id="deploy-001",
        consensus_type="MAKER",
        decision="deploy",
        confidence=0.85,
        participants=["agent-1", "agent-2", "agent-3"],
        reasoning="All tests passed, deployment approved"
    )

    # Record vote breakdown
    audit.record_vote_breakdown("deploy-001", [
        {"agent_id": "agent-1", "vote": "deploy", "confidence": 0.9},
        {"agent_id": "agent-2", "vote": "deploy", "confidence": 0.85},
        {"agent_id": "agent-3", "vote": "wait", "confidence": 0.7}
    ])

    # Query audit trail
    decisions = audit.query_decisions(
        start_date="2026-04-01",
        consensus_type="MAKER",
        min_confidence=0.8
    )

    # Export for analysis
    export_data = audit.export_audit_data(format="json")
    ```
"""

import hashlib
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

import structlog

logger = structlog.get_logger("ConsensusAuditTrail")


class AuditEventType(Enum):
    """Types of audit events."""

    CONSENSUS_INITIATED = "consensus_initiated"
    VOTE_SUBMITTED = "vote_submitted"
    ARGUMENT_SUBMITTED = "argument_submitted"
    POSITION_CHANGED = "position_changed"
    CONSENSUS_REACHED = "consensus_reached"
    CONSENSUS_FAILED = "consensus_failed"
    DECISION_ROLLED_BACK = "decision_rolled_back"
    DECISION_EXPORTED = "decision_exported"
    AUDIT_QUERY = "audit_query"


class DecisionOutcome(Enum):
    """Possible decision outcomes."""

    SUCCESS = "success"  # Decision led to successful outcome
    FAILURE = "failure"  # Decision led to failure
    PARTIAL_SUCCESS = "partial_success"  # Mixed outcome
    PENDING = "pending"  # Outcome not yet determined
    UNKNOWN = "unknown"  # Outcome cannot be determined


@dataclass
class AuditEvent:
    """
    Single audit event in the trail.

    Attributes:
        event_id: Unique event identifier
        event_type: Type of event
        timestamp: Event timestamp
        consensus_id: Related consensus process
        agent_id: Related agent (if any)
        data: Event-specific data
        hash: Cryptographic hash for integrity
        previous_hash: Hash of previous event (chain linkage)
    """

    event_id: str
    event_type: AuditEventType
    timestamp: str
    consensus_id: str
    agent_id: Optional[str] = None
    data: Dict[str, Any] = field(default_factory=dict)
    hash: Optional[str] = None
    previous_hash: Optional[str] = None

    def __post_init__(self) -> None:
        """Generate hash after initialization."""
        if not self.hash:
            self.hash = self._generate_hash()

    def _generate_hash(self) -> str:
        """Generate cryptographic hash of event."""
        data = {
            "event_id": self.event_id,
            "event_type": self.event_type.value,
            "timestamp": self.timestamp,
            "consensus_id": self.consensus_id,
            "agent_id": self.agent_id,
            "data": self.data,
            "previous_hash": self.previous_hash,
        }
        data_json = json.dumps(data, sort_keys=True)
        return hashlib.sha256(data_json.encode()).hexdigest()


@dataclass
class VoteRecord:
    """
    Complete record of a single vote.

    Attributes:
        vote_id: Unique vote identifier
        consensus_id: Consensus process identifier
        agent_id: Voting agent
        decision: Vote decision
        confidence: Confidence level
        reasoning: Optional reasoning text
        timestamp: Vote timestamp
        metadata: Additional metadata
    """

    vote_id: str
    consensus_id: str
    agent_id: str
    decision: str
    confidence: float
    reasoning: Optional[str] = None
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ArgumentRecord:
    """
    Record of an argument submitted during deliberation.

    Attributes:
        argument_id: Unique argument identifier
        consensus_id: Consensus process identifier
        agent_id: Submitting agent
        position: Position being supported
        content: Argument content
        supports: IDs of supported arguments
        rebuttals: IDs of rebutted arguments
        timestamp: Submission timestamp
    """

    argument_id: str
    consensus_id: str
    agent_id: str
    position: str
    content: str
    supports: List[str] = field(default_factory=list)
    rebuttals: List[str] = field(default_factory=list)
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


@dataclass
class DecisionRecord:
    """
    Complete record of a consensus decision.

    Attributes:
        decision_id: Decision identifier
        consensus_id: Related consensus process
        proposal: Original proposal
        decision: Final decision
        confidence: Overall confidence
        outcome: Decision outcome
        participants: List of participating agents
        votes: All votes cast
        arguments: All arguments submitted
        reasoning_summary: Summary of reasoning
        start_time: Consensus start time
        end_time: Consensus end time
        metadata: Additional metadata
    """

    decision_id: str
    consensus_id: str
    proposal: str
    decision: str
    confidence: float
    outcome: DecisionOutcome = DecisionOutcome.PENDING
    participants: List[str] = field(default_factory=list)
    votes: List[VoteRecord] = field(default_factory=list)
    arguments: List[ArgumentRecord] = field(default_factory=list)
    reasoning_summary: Optional[str] = None
    start_time: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    end_time: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class QueryResult:
    """
    Result of an audit query.

    Attributes:
        query: Original query parameters
        total_results: Number of results
        results: Query results
        execution_time_ms: Query execution time
        timestamp: Query timestamp
    """

    query: Dict[str, Any]
    total_results: int
    results: List[Dict[str, Any]]
    execution_time_ms: float
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class ConsensusAuditTrail:
    """
    Comprehensive audit trail for consensus decisions.

    Provides complete decision history with:
    - Vote breakdowns and argument logs
    - Outcome tracking for learning
    - Export capabilities for analysis
    - Cryptographic integrity verification

    The audit trail maintains an immutable chain of events,
    enabling full追溯 ability of all consensus decisions.

    Attributes:
        storage_backend: Storage backend type
        retention_days: Data retention period
        enable_hash_chain: Enable cryptographic chaining
    """

    def __init__(
        self,
        storage_backend: str = "memory",
        retention_days: int = 90,
        enable_hash_chain: bool = True,
    ) -> None:
        """
        Initialize the audit trail.

        Args:
            storage_backend: Storage backend (memory, postgresql, sqlite)
            retention_days: Number of days to retain audit data
            enable_hash_chain: Enable cryptographic event chaining
        """
        self.storage_backend = storage_backend
        self.retention_days = retention_days
        self.enable_hash_chain = enable_hash_chain

        # In-memory storage (would be replaced by actual backend)
        self.events: List[AuditEvent] = []
        self.decisions: Dict[str, DecisionRecord] = {}
        self.votes: Dict[str, List[VoteRecord]] = {}
        self.arguments: Dict[str, List[ArgumentRecord]] = {}
        self.outcomes: Dict[str, DecisionOutcome] = {}

        # Event chain tracking
        self.last_event_hash: Optional[str] = None

        # Query statistics
        self.query_count = 0
        self.total_query_time_ms = 0.0

        logger.info(
            f"ConsensusAuditTrail initialized with "
            f"backend={storage_backend}, retention={retention_days} days"
        )

    def record_event(
        self,
        event_type: AuditEventType,
        consensus_id: str,
        agent_id: Optional[str] = None,
        data: Optional[Dict[str, Any]] = None,
    ) -> AuditEvent:
        """
        Record an audit event.

        Args:
            event_type: Type of event
            consensus_id: Related consensus process
            agent_id: Related agent (if any)
            data: Event-specific data

        Returns:
            Created audit event
        """
        # Generate event ID
        event_id = f"evt-{consensus_id}-{len(self.events) + 1}"

        # Create event with hash chain
        previous_hash = self.last_event_hash if self.enable_hash_chain else None

        event = AuditEvent(
            event_id=event_id,
            event_type=event_type,
            timestamp=datetime.now(timezone.utc).isoformat(),
            consensus_id=consensus_id,
            agent_id=agent_id,
            data=data or {},
            previous_hash=previous_hash,
        )

        # Store event
        self.events.append(event)
        self.last_event_hash = event.hash

        logger.debug(
            f"Audit event recorded: {event_id} ({event_type.value})"
        )

        return event

    def record_decision(
        self,
        decision_id: str,
        consensus_id: str,
        proposal: str,
        decision: str,
        confidence: float,
        participants: Optional[List[str]] = None,
        reasoning: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> DecisionRecord:
        """
        Record a consensus decision.

        Args:
            decision_id: Decision identifier
            consensus_id: Related consensus process
            proposal: Original proposal
            decision: Final decision
            confidence: Overall confidence
            participants: List of participating agents
            reasoning: Optional reasoning summary
            metadata: Additional metadata

        Returns:
            Created decision record
        """
        # Record consensus initiated event
        self.record_event(
            event_type=AuditEventType.CONSENSUS_INITIATED,
            consensus_id=consensus_id,
            data={
                "decision_id": decision_id,
                "proposal": proposal,
                "participants": participants or [],
            },
        )

        # Create decision record
        record = DecisionRecord(
            decision_id=decision_id,
            consensus_id=consensus_id,
            proposal=proposal,
            decision=decision,
            confidence=confidence,
            participants=participants or [],
            reasoning_summary=reasoning,
            metadata=metadata or {},
        )

        # Store decision
        self.decisions[decision_id] = record

        # Record consensus reached event
        self.record_event(
            event_type=AuditEventType.CONSENSUS_REACHED,
            consensus_id=consensus_id,
            data={
                "decision_id": decision_id,
                "decision": decision,
                "confidence": confidence,
            },
        )

        logger.info(
            f"Decision recorded: {decision_id} -> {decision} "
            f"(confidence: {confidence:.2f})"
        )

        return record

    def record_vote(
        self,
        consensus_id: str,
        agent_id: str,
        decision: str,
        confidence: float,
        reasoning: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> VoteRecord:
        """
        Record a single vote.

        Args:
            consensus_id: Consensus process identifier
            agent_id: Voting agent
            decision: Vote decision
            confidence: Confidence level
            reasoning: Optional reasoning text
            metadata: Additional metadata

        Returns:
            Created vote record
        """
        vote_id = f"vote-{consensus_id}-{agent_id}"

        vote = VoteRecord(
            vote_id=vote_id,
            consensus_id=consensus_id,
            agent_id=agent_id,
            decision=decision,
            confidence=confidence,
            reasoning=reasoning,
            metadata=metadata or {},
        )

        # Store vote
        if consensus_id not in self.votes:
            self.votes[consensus_id] = []
        self.votes[consensus_id].append(vote)

        # Update decision record if exists
        for decision_record in self.decisions.values():
            if decision_record.consensus_id == consensus_id:
                decision_record.votes.append(vote)
                if agent_id not in decision_record.participants:
                    decision_record.participants.append(agent_id)

        # Record vote event
        self.record_event(
            event_type=AuditEventType.VOTE_SUBMITTED,
            consensus_id=consensus_id,
            agent_id=agent_id,
            data={
                "vote_id": vote_id,
                "decision": decision,
                "confidence": confidence,
            },
        )

        logger.debug(
            f"Vote recorded: {agent_id} -> {decision} "
            f"(confidence: {confidence:.2f})"
        )

        return vote

    def record_argument(
        self,
        consensus_id: str,
        agent_id: str,
        position: str,
        content: str,
        supports: Optional[List[str]] = None,
        rebuttals: Optional[List[str]] = None,
    ) -> ArgumentRecord:
        """
        Record an argument submitted during deliberation.

        Args:
            consensus_id: Consensus process identifier
            agent_id: Submitting agent
            position: Position being supported
            content: Argument content
            supports: IDs of supported arguments
            rebuttals: IDs of rebutted arguments

        Returns:
            Created argument record
        """
        argument_id = f"arg-{consensus_id}-{len(self.arguments.get(consensus_id, [])) + 1}"

        argument = ArgumentRecord(
            argument_id=argument_id,
            consensus_id=consensus_id,
            agent_id=agent_id,
            position=position,
            content=content,
            supports=supports or [],
            rebuttals=rebuttals or [],
        )

        # Store argument
        if consensus_id not in self.arguments:
            self.arguments[consensus_id] = []
        self.arguments[consensus_id].append(argument)

        # Update decision record if exists
        for decision_record in self.decisions.values():
            if decision_record.consensus_id == consensus_id:
                decision_record.arguments.append(argument)

        # Record argument event
        self.record_event(
            event_type=AuditEventType.ARGUMENT_SUBMITTED,
            consensus_id=consensus_id,
            agent_id=agent_id,
            data={
                "argument_id": argument_id,
                "position": position,
                "content_length": len(content),
            },
        )

        logger.debug(
            f"Argument recorded: {argument_id} by {agent_id} ({position})"
        )

        return argument

    def record_decision_outcome(
        self,
        decision_id: str,
        outcome: DecisionOutcome,
        outcome_data: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Record the outcome of a decision.

        Args:
            decision_id: Decision identifier
            outcome: Decision outcome
            outcome_data: Additional outcome data
        """
        if decision_id not in self.decisions:
            logger.warning(f"Decision not found: {decision_id}")
            return

        # Update decision record
        self.decisions[decision_id].outcome = outcome
        if outcome_data:
            self.decisions[decision_id].metadata["outcome_data"] = outcome_data

        # Store outcome tracking
        self.outcomes[decision_id] = outcome

        # Record rollback event if applicable
        if outcome == DecisionOutcome.FAILURE:
            self.record_event(
                event_type=AuditEventType.CONSENSUS_FAILED,
                consensus_id=self.decisions[decision_id].consensus_id,
                data={
                    "decision_id": decision_id,
                    "outcome": outcome.value,
                    "outcome_data": outcome_data,
                },
            )

        logger.info(
            f"Decision outcome recorded: {decision_id} -> {outcome.value}"
        )

    def record_rollback(
        self,
        decision_id: str,
        reason: str,
    ) -> None:
        """
        Record a decision rollback.

        Args:
            decision_id: Decision identifier
            reason: Reason for rollback
        """
        if decision_id not in self.decisions:
            logger.warning(f"Decision not found: {decision_id}")
            return

        # Update decision metadata
        self.decisions[decision_id].metadata["rollback_reason"] = reason
        self.decisions[decision_id].metadata["rollback_time"] = datetime.now(
            timezone.utc
        ).isoformat()

        # Record rollback event
        self.record_event(
            event_type=AuditEventType.DECISION_ROLLED_BACK,
            consensus_id=self.decisions[decision_id].consensus_id,
            data={
                "decision_id": decision_id,
                "reason": reason,
            },
        )

        logger.info(f"Rollback recorded for {decision_id}: {reason}")

    def get_decision(
        self,
        decision_id: str,
    ) -> Optional[DecisionRecord]:
        """
        Get complete decision record.

        Args:
            decision_id: Decision identifier

        Returns:
            Decision record or None
        """
        return self.decisions.get(decision_id)

    def get_votes_for_consensus(
        self,
        consensus_id: str,
    ) -> List[VoteRecord]:
        """
        Get all votes for a consensus process.

        Args:
            consensus_id: Consensus identifier

        Returns:
            List of vote records
        """
        return self.votes.get(consensus_id, [])

    def get_arguments_for_consensus(
        self,
        consensus_id: str,
    ) -> List[ArgumentRecord]:
        """
        Get all arguments for a consensus process.

        Args:
            consensus_id: Consensus identifier

        Returns:
            List of argument records
        """
        return self.arguments.get(consensus_id, [])

    def get_vote_breakdown(
        self,
        consensus_id: str,
    ) -> Dict[str, Any]:
        """
        Get vote breakdown for a consensus process.

        Args:
            consensus_id: Consensus identifier

        Returns:
            Vote breakdown dictionary
        """
        votes = self.get_votes_for_consensus(consensus_id)

        if not votes:
            return {"total_votes": 0, "by_decision": {}, "by_agent": {}}

        # Group by decision
        by_decision: Dict[str, List[VoteRecord]] = {}
        by_agent: Dict[str, VoteRecord] = {}

        for vote in votes:
            if vote.decision not in by_decision:
                by_decision[vote.decision] = []
            by_decision[vote.decision].append(vote)
            by_agent[vote.agent_id] = vote

        return {
            "total_votes": len(votes),
            "by_decision": {
                decision: {
                    "count": len(v),
                    "avg_confidence": sum(vote.confidence for vote in v) / len(v),
                    "votes": [
                        {
                            "agent_id": vote.agent_id,
                            "confidence": vote.confidence,
                            "reasoning": vote.reasoning,
                        }
                        for vote in v
                    ],
                }
                for decision, v in by_decision.items()
            },
            "by_agent": {
                agent_id: {
                    "decision": vote.decision,
                    "confidence": vote.confidence,
                }
                for agent_id, vote in by_agent.items()
            },
        }

    def query_decisions(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        consensus_type: Optional[str] = None,
        min_confidence: Optional[float] = None,
        outcome: Optional[DecisionOutcome] = None,
        participants: Optional[List[str]] = None,
    ) -> QueryResult:
        """
        Query decisions with filters.

        Args:
            start_date: Filter by start date (ISO format)
            end_date: Filter by end date (ISO format)
            consensus_type: Filter by consensus type
            min_confidence: Filter by minimum confidence
            outcome: Filter by outcome
            participants: Filter by participants

        Returns:
            Query result
        """
        start_time = datetime.now(timezone.utc)

        # Record query event
        self.record_event(
            event_type=AuditEventType.AUDIT_QUERY,
            consensus_id="audit_system",
            data={
                "query_type": "decisions",
                "filters": {
                    "start_date": start_date,
                    "end_date": end_date,
                    "consensus_type": consensus_type,
                    "min_confidence": min_confidence,
                    "outcome": outcome.value if outcome else None,
                    "participants": participants,
                },
            },
        )

        # Filter decisions
        results = []
        for decision_id, record in self.decisions.items():
            # Apply filters
            if start_date and record.start_time < start_date:
                continue
            if end_date and record.end_time and record.end_time > end_date:
                continue
            if min_confidence and record.confidence < min_confidence:
                continue
            if outcome and record.outcome != outcome:
                continue
            if participants and not any(
                p in record.participants for p in participants
            ):
                continue

            # Add to results
            results.append({
                "decision_id": decision_id,
                "consensus_id": record.consensus_id,
                "proposal": record.proposal,
                "decision": record.decision,
                "confidence": record.confidence,
                "outcome": record.outcome.value,
                "participants": record.participants,
                "start_time": record.start_time,
                "end_time": record.end_time,
                "vote_count": len(record.votes),
                "argument_count": len(record.arguments),
            })

        # Calculate execution time
        end_time = datetime.now(timezone.utc)
        execution_time_ms = (end_time - start_time).total_seconds() * 1000

        # Update query statistics
        self.query_count += 1
        self.total_query_time_ms += execution_time_ms

        query_result = QueryResult(
            query={
                "start_date": start_date,
                "end_date": end_date,
                "consensus_type": consensus_type,
                "min_confidence": min_confidence,
                "outcome": outcome,
                "participants": participants,
            },
            total_results=len(results),
            results=results,
            execution_time_ms=execution_time_ms,
        )

        logger.info(
            f"Audit query completed: {len(results)} results in {execution_time_ms:.2f}ms"
        )

        return query_result

    def get_decision_timeline(
        self,
        consensus_id: str,
    ) -> List[Dict[str, Any]]:
        """
        Get complete timeline of events for a consensus process.

        Args:
            consensus_id: Consensus identifier

        Returns:
            Timeline of events
        """
        timeline = []

        # Get all events for this consensus
        consensus_events = [
            e for e in self.events if e.consensus_id == consensus_id
        ]

        for event in consensus_events:
            timeline.append({
                "event_id": event.event_id,
                "event_type": event.event_type.value,
                "timestamp": event.timestamp,
                "agent_id": event.agent_id,
                "data": event.data,
            })

        # Sort by timestamp
        timeline.sort(key=lambda x: x["timestamp"])

        return timeline

    def export_audit_data(
        self,
        format: str = "json",
        consensus_id: Optional[str] = None,
        include_events: bool = True,
        include_votes: bool = True,
        include_arguments: bool = True,
    ) -> Dict[str, Any]:
        """
        Export audit data for external analysis.

        Args:
            format: Export format (json, csv)
            consensus_id: Optional specific consensus to export
            include_events: Include event log
            include_votes: Include vote records
            include_arguments: Include argument records

        Returns:
            Exported data dictionary
        """
        export_data: Dict[str, Any] = {
            "export_timestamp": datetime.now(timezone.utc).isoformat(),
            "format": format,
            "audit_trail_version": "1.0",
        }

        if consensus_id:
            # Export specific consensus
            decision = self.get_decision(consensus_id)
            if decision:
                export_data["decisions"] = [
                    {
                        "decision_id": decision.decision_id,
                        "consensus_id": decision.consensus_id,
                        "proposal": decision.proposal,
                        "decision": decision.decision,
                        "confidence": decision.confidence,
                        "outcome": decision.outcome.value,
                        "participants": decision.participants,
                        "reasoning_summary": decision.reasoning_summary,
                        "start_time": decision.start_time,
                        "end_time": decision.end_time,
                        "metadata": decision.metadata,
                    }
                ]

            if include_votes:
                export_data["votes"] = [
                    {
                        "vote_id": v.vote_id,
                        "agent_id": v.agent_id,
                        "decision": v.decision,
                        "confidence": v.confidence,
                        "reasoning": v.reasoning,
                        "timestamp": v.timestamp,
                    }
                    for v in self.get_votes_for_consensus(consensus_id)
                ]

            if include_arguments:
                export_data["arguments"] = [
                    {
                        "argument_id": a.argument_id,
                        "agent_id": a.agent_id,
                        "position": a.position,
                        "content": a.content,
                        "timestamp": a.timestamp,
                    }
                    for a in self.get_arguments_for_consensus(consensus_id)
                ]

            if include_events:
                export_data["events"] = [
                    {
                        "event_id": e.event_id,
                        "event_type": e.event_type.value,
                        "timestamp": e.timestamp,
                        "agent_id": e.agent_id,
                        "data": e.data,
                    }
                    for e in self.events
                    if e.consensus_id == consensus_id
                ]
        else:
            # Export all data
            export_data["decisions"] = [
                {
                    "decision_id": d.decision_id,
                    "consensus_id": d.consensus_id,
                    "proposal": d.proposal,
                    "decision": d.decision,
                    "confidence": d.confidence,
                    "outcome": d.outcome.value,
                    "participants": d.participants,
                    "start_time": d.start_time,
                    "end_time": d.end_time,
                }
                for d in self.decisions.values()
            ]

            if include_events:
                export_data["events"] = [
                    {
                        "event_id": e.event_id,
                        "event_type": e.event_type.value,
                        "timestamp": e.timestamp,
                        "consensus_id": e.consensus_id,
                        "agent_id": e.agent_id,
                        "data": e.data,
                    }
                    for e in self.events
                ]

        # Record export event
        self.record_event(
            event_type=AuditEventType.DECISION_EXPORTED,
            consensus_id=consensus_id or "all",
            data={
                "format": format,
                "record_count": len(export_data.get("decisions", [])),
            },
        )

        logger.info(
            f"Audit data exported: {len(export_data.get('decisions', []))} decisions"
        )

        return export_data

    def verify_integrity(self) -> Dict[str, Any]:
        """
        Verify cryptographic integrity of audit trail.

        Returns:
            Integrity verification results
        """
        results = {
            "total_events": len(self.events),
            "verified_events": 0,
            "failed_events": 0,
            "chain_broken": False,
            "errors": [],
        }

        if not self.enable_hash_chain:
            results["status"] = "hash_chain_disabled"
            return results

        previous_hash = None
        for i, event in enumerate(self.events):
            # Verify event hash
            expected_hash = event._generate_hash()
            if event.hash != expected_hash:
                results["failed_events"] += 1
                results["errors"].append(f"Event {event.event_id}: hash mismatch")
            else:
                results["verified_events"] += 1

            # Verify chain linkage
            if event.previous_hash != previous_hash:
                results["chain_broken"] = True
                results["errors"].append(
                    f"Event {event.event_id}: chain broken at position {i}"
                )

            previous_hash = event.hash

        results["status"] = "valid" if results["failed_events"] == 0 and not results["chain_broken"] else "invalid"

        logger.info(
            f"Integrity verification: {results['status']} "
            f"({results['verified_events']}/{results['total_events']} verified)"
        )

        return results

    def get_statistics(self) -> Dict[str, Any]:
        """
        Get audit trail statistics.

        Returns:
            Statistics dictionary
        """
        # Calculate outcome distribution
        outcome_counts: Dict[str, int] = {}
        for outcome in self.outcomes.values():
            outcome_key = outcome.value
            outcome_counts[outcome_key] = outcome_counts.get(outcome_key, 0) + 1

        return {
            "total_events": len(self.events),
            "total_decisions": len(self.decisions),
            "total_votes": sum(len(v) for v in self.votes.values()),
            "total_arguments": sum(len(a) for a in self.arguments.values()),
            "outcome_distribution": outcome_counts,
            "query_count": self.query_count,
            "avg_query_time_ms": (
                self.total_query_time_ms / self.query_count
                if self.query_count > 0
                else 0.0
            ),
            "storage_backend": self.storage_backend,
            "retention_days": self.retention_days,
            "hash_chain_enabled": self.enable_hash_chain,
        }

    def cleanup_old_data(
        self,
        current_date: Optional[datetime] = None,
    ) -> int:
        """
        Clean up data older than retention period.

        Args:
            current_date: Current date for calculation

        Returns:
            Number of records cleaned up
        """
        if current_date is None:
            current_date = datetime.now(timezone.utc)

        cutoff_date = datetime(
            current_date.year,
            current_date.month,
            current_date.day,
            tzinfo=timezone.utc,
        )

        # Simple implementation - would be more sophisticated with actual storage backend
        cleaned = 0

        # This is a placeholder for actual cleanup logic
        # which would depend on the storage backend

        logger.info(f"Cleanup completed: {cleaned} records removed")

        return cleaned
