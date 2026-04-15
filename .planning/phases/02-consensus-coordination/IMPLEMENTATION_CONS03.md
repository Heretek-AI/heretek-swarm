# Implementation Plan: CONS-03 — Behavioral Baseline Updating

## Task Overview

**Owner**: Core Triad
**Depends**: Task 1 (Deliberation Engine), Task 2 (Immune Response Building)
**Verification**: Baseline changes require CONS-03 quorum approval; immutable audit trail; rollback capability

## Edge Cases

- Baseline drift during normal operation — gradual update with multi-agent approval
- Emergency baseline reset — Steward can initiate with Charlie approval

---

## 1. Analysis of Existing Code

### 1.1 Behavioral Baseline Store (created by Task 2)

**Location**: `src/heretek_swarm/security/behavioral_baseline.py`

**From CONS-02 Implementation**:
- `SecurityPattern` dataclass - learned security patterns
- `PatternStatus` enum - PROVISIONAL, PROVEN, REJECTED, HUMAN_REVIEW
- `BaselineChange` dataclass - immutable change records with hash chain
- `BehavioralBaselineStore` class - pattern storage with quorum tracking

**Gap for CONS-03**:
- No active quorum voting mechanism (just recording)
- No rollback capability
- No emergency reset handling
- No baseline drift detection

### 1.2 Existing Tribunal System (`src/heretek_swarm/consensus/tribunal.py`)

**Current Capabilities**:
- `TribunalCase` - appeal cases with evidence chains
- `TribunalEvidence` - evidence submission with cryptographic hash
- `TribunalRuling` - binding decisions with precedent tracking
- `EvidenceType` enum - DOCUMENT, TEST_RESULT, EXPERT_OPINION, etc.
- `RulingType` enum - UPHOLD, OVERRULE, MODIFY, DISMISS, REMAND

**Gap for CONS-03**:
- Not designed for real-time baseline change approval
- No quorum tracking for baseline changes
- No emergency reset workflow

### 1.3 Steward Agent (`src/heretek_swarm/actors/steward.py`)

**Current Capabilities**:
- `TribunalMixin` integrated
- `coordinate_triad()` - initiates deliberations
- `active_deliberations` - tracks deliberation state
- Governance policies management

**Gap for CONS-03**:
- No baseline change coordination
- No emergency reset with Charlie approval
- No drift detection

### 1.4 Consensus Audit Trail (`src/heretek_swarm/consensus/audit_trail.py`)

**Available Features**:
- Hash-chained immutable events
- `verify_integrity()` - tamper detection
- `record_rollback()` - rollback tracking

**Use for**: Baseline change audit trail integration

---

## 2. Implementation Architecture

### 2.1 New Files to Create

```
src/heretek_swarm/consensus/baseline_tribunal.py  # NEW - Baseline-specific tribunal
src/heretek_swarm/security/baseline_rollback.py   # NEW - Rollback capability
```

### 2.2 Files to Modify

```
src/heretek_swarm/security/behavioral_baseline.py   # ENHANCE - Add voting, rollback
src/heretek_swarm/actors/steward.py                # ENHANCE - Coordinate baseline votes
```

### 2.3 Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                      CONS-03 Architecture                            │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌─────────────┐    ┌──────────────────┐    ┌─────────────────────┐  │
│  │  Sentinel   │───►│ BehavioralBaseline│───►│ BaselineTribunal    │  │
│  │ (Immune)   │    │     Store        │    │ (CONS-03 Quorum)    │  │
│  └─────────────┘    └──────────────────┘    └─────────────────────┘  │
│         │                   │                        │              │
│         │                   │                        ▼              │
│         │                   │              ┌─────────────────┐       │
│         │                   └─────────────►│  StewardAgent   │       │
│         │                              │  (Vote Coord)    │       │
│         │                              └─────────────────┘       │
│         │                                       │                 │
│         ▼                                       ▼                 │
│  ┌─────────────┐                      ┌─────────────────┐          │
│  │ Anomaly     │                      │ ConsensusAudit  │          │
│  │ Detection   │                      │ Trail           │          │
│  └─────────────┘                      └─────────────────┘          │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 3. Detailed Implementation

### 3.1 `src/heretek_swarm/security/baseline_rollback.py` (NEW)

**Purpose**: Rollback capability for baseline changes with full audit trail.

#### Data Structures

```python
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any
import hashlib
import json

class RollbackReason(StrEnum):
    """Reasons for baseline rollback."""
    QUORUM_FAILED = "quorum_failed"
    EMERGENCY_RESET = "emergency_reset"
    CORRUPTION_DETECTED = "corruption_detected"
    MANUAL_OVERRIDE = "manual_override"

class RollbackStatus(StrEnum):
    """Status of a rollback operation."""
    PENDING = "pending"
    APPROVED = "approved"
    EXECUTED = "executed"
    CANCELLED = "cancelled"

@dataclass
class BaselineSnapshot:
    """Point-in-time snapshot of baseline state."""
    snapshot_id: str
    timestamp: str
    baseline_hash: str
    pattern_count: int
    patterns_summary: dict[str, int]  # status -> count
    change_history_ids: list[str]  # IDs of changes included
    previous_snapshot_hash: str | None
    hash: str | None = None

    def __post_init__(self) -> None:
        if not self.hash:
            self.hash = self._generate_hash()

    def _generate_hash(self) -> str:
        data = {
            "snapshot_id": self.snapshot_id,
            "timestamp": self.timestamp,
            "baseline_hash": self.baseline_hash,
            "pattern_count": self.pattern_count,
            "patterns_summary": self.patterns_summary,
            "change_history_ids": self.change_history_ids,
            "previous_snapshot_hash": self.previous_snapshot_hash,
        }
        return hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()

@dataclass
class RollbackOperation:
    """Record of a rollback operation."""
    rollback_id: str
    target_snapshot_id: str | None  # None for emergency reset
    reason: RollbackReason
    initiated_by: str  # agent_id
    approved_by: list[str] = field(default_factory=list)  # agent_ids
    status: RollbackStatus = RollbackStatus.PENDING
    created_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    executed_at: str | None = None
    changes_rolled_back: list[str] = field(default_factory=list)  # change_ids
    emergency: bool = False
    hash: str | None = None

    def __post_init__(self) -> None:
        if not self.hash:
            self.hash = self._generate_hash()

    def _generate_hash(self) -> str:
        data = {
            "rollback_id": self.rollback_id,
            "target_snapshot_id": self.target_snapshot_id,
            "reason": self.reason.value,
            "initiated_by": self.initiated_by,
            "approved_by": sorted(self.approved_by),
            "status": self.status.value,
            "created_at": self.created_at,
            "emergency": self.emergency,
        }
        return hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()
```

#### Core Class: `BaselineRollbackManager`

```python
class BaselineRollbackManager:
    """
    Manages baseline snapshots and rollback operations.

    Features:
    - Periodic baseline snapshots
    - Rollback to any previous snapshot
    - Emergency reset with Charlie approval
    - Full audit trail
    """

    def __init__(
        self,
        snapshot_interval: int = 100,  # snapshots per X changes
        max_snapshots: int = 50,
        emergency_approval_required: list[str] | None = None,  # Charlie agent_id
    ):
        # Snapshots storage
        self._snapshots: dict[str, BaselineSnapshot] = {}
        self._latest_snapshot_id: str | None = None
        self._snapshot_interval = snapshot_interval
        self._max_snapshots = max_snapshots

        # Rollback operations
        self._rollback_operations: dict[str, RollbackOperation] = {}
        self._change_counter: int = 0

        # Emergency approval
        self._emergency_approval_required = emergency_approval_required or ["charlie"]

        logger.info(
            "BaselineRollbackManager initialized",
            snapshot_interval=snapshot_interval,
            max_snapshots=max_snapshots,
        )

    def create_snapshot(
        self,
        baseline_store: "BehavioralBaselineStore",
        patterns: dict[str, "SecurityPattern"],
    ) -> BaselineSnapshot:
        """Create a point-in-time snapshot of baseline."""
        self._change_counter += 1

        # Calculate patterns summary
        summary: dict[str, int] = {}
        for pattern in patterns.values():
            status = pattern.status.value
            summary[status] = summary.get(status, 0) + 1

        # Generate baseline hash
        baseline_hash = baseline_store.get_baseline_hash()

        snapshot = BaselineSnapshot(
            snapshot_id=f"snap-{datetime.now(UTC).timestamp()}",
            timestamp=datetime.now(UTC).isoformat(),
            baseline_hash=baseline_hash,
            pattern_count=len(patterns),
            patterns_summary=summary,
            change_history_ids=baseline_store.get_change_history_ids(),
            previous_snapshot_hash=self._snapshots.get(self._latest_snapshot_id).hash if self._latest_snapshot_id else None,
        )

        self._snapshots[snapshot.snapshot_id] = snapshot
        self._latest_snapshot_id = snapshot.snapshot_id

        # Prune old snapshots
        self._prune_snapshots()

        logger.info(
            "Baseline snapshot created",
            snapshot_id=snapshot.snapshot_id,
            pattern_count=len(patterns),
        )

        return snapshot

    def request_rollback(
        self,
        target_snapshot_id: str | None,
        reason: RollbackReason,
        initiated_by: str,
        emergency: bool = False,
    ) -> RollbackOperation:
        """Request a rollback operation."""
        rollback_id = f"rb-{datetime.now(UTC).timestamp()}"

        rollback_op = RollbackOperation(
            rollback_id=rollback_id,
            target_snapshot_id=target_snapshot_id,
            reason=reason,
            initiated_by=initiated_by,
            emergency=emergency,
        )

        self._rollback_operations[rollback_id] = rollback_op

        logger.info(
            "Rollback requested",
            rollback_id=rollback_id,
            reason=reason.value,
            initiated_by=initiated_by,
            emergency=emergency,
        )

        return rollback_op

    def approve_rollback(
        self,
        rollback_id: str,
        approved_by: str,
    ) -> bool:
        """
        Approve a rollback operation.

        Returns True if rollback can proceed.
        """
        rollback_op = self._rollback_operations.get(rollback_id)
        if not rollback_op:
            return False

        if approved_by not in rollback_op.approved_by:
            rollback_op.approved_by.append(approved_by)

        # Check if we have enough approvals
        if rollback_op.emergency:
            # Emergency requires Charlie approval
            return "charlie" in rollback_op.approved_by
        else:
            # Normal requires 2 approvals
            return len(rollback_op.approved_by) >= 2

    def execute_rollback(
        self,
        rollback_id: str,
        baseline_store: "BehavioralBaselineStore",
    ) -> bool:
        """
        Execute an approved rollback.

        Returns True if successful.
        """
        rollback_op = self._rollback_operations.get(rollback_id)
        if not rollback_op:
            return False

        if rollback_op.status != RollbackStatus.PENDING:
            return False

        # Execute the rollback
        try:
            if rollback_op.emergency:
                # Emergency reset - restore to empty baseline or specific snapshot
                if rollback_op.target_snapshot_id:
                    snapshot = self._snapshots.get(rollback_op.target_snapshot_id)
                    if snapshot:
                        baseline_store.restore_from_snapshot(snapshot)
                else:
                    baseline_store.emergency_reset()
            else:
                # Normal rollback to snapshot
                snapshot = self._snapshots.get(rollback_op.target_snapshot_id)
                if snapshot:
                    baseline_store.restore_from_snapshot(snapshot)

            rollback_op.status = RollbackStatus.EXECUTED
            rollback_op.executed_at = datetime.now(UTC).isoformat()

            logger.info(
                "Rollback executed",
                rollback_id=rollback_id,
                target=rollback_op.target_snapshot_id,
            )

            return True

        except Exception as e:
            logger.error(f"Rollback failed: {e}")
            rollback_op.status = RollbackStatus.CANCELLED
            return False

    def _prune_snapshots(self) -> None:
        """Remove old snapshots beyond max limit."""
        if len(self._snapshots) <= self._max_snapshots:
            return

        # Keep most recent snapshots
        sorted_snapshots = sorted(
            self._snapshots.values(),
            key=lambda s: s.timestamp,
            reverse=True,
        )

        for snapshot in sorted_snapshots[self._max_snapshots:]:
            del self._snapshots[snapshot.snapshot_id]

    def get_snapshot_history(self, limit: int = 10) -> list[BaselineSnapshot]:
        """Get recent snapshots."""
        return sorted(
            self._snapshots.values(),
            key=lambda s: s.timestamp,
            reverse=True,
        )[:limit]

    def get_rollback_status(self, rollback_id: str) -> RollbackOperation | None:
        """Get status of a rollback operation."""
        return self._rollback_operations.get(rollback_id)
```

### 3.2 `src/heretek_swarm/consensus/baseline_tribunal.py` (NEW)

**Purpose**: Specialized tribunal for baseline change approval with quorum tracking.

#### Data Structures

```python
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

class BaselineChangeType(StrEnum):
    """Types of baseline changes requiring approval."""
    PATTERN_ADD = "pattern_add"
    PATTERN_REMOVE = "pattern_remove"
    PATTERN_MODIFY = "pattern_modify"
    PATTERN_PROMOTE = "pattern_promote"  # PROVISIONAL -> PROVEN
    PATTERN_DEMOTE = "pattern_demote"  # PROVEN -> REJECTED
    BASELINE_RESET = "baseline_reset"
    EMERGENCY_RESET = "emergency_reset"

class VoteDecision(StrEnum):
    """Voting decisions."""
    APPROVE = "approve"
    REJECT = "reject"
    ABSTAIN = "abstain"

class BaselineChangeStatus(StrEnum):
    """Status of a baseline change proposal."""
    PROPOSED = "proposed"
    VOTING = "voting"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXECUTED = "executed"
    EXPIRED = "expired"
    ROLLED_BACK = "rolled_back"

@dataclass
class BaselineChangeProposal:
    """Proposal for a baseline change requiring tribunal approval."""
    proposal_id: str
    change_type: BaselineChangeType
    pattern_id: str | None  # None for reset
    proposed_by: str  # agent_id
    rationale: str
    evidence_refs: list[str] = field(default_factory=list)
    status: BaselineChangeStatus = BaselineChangeStatus.PROPOSED
    votes: dict[str, VoteDecision] = field(default_factory=dict)  # agent_id -> vote
    approvers: list[str] = field(default_factory=list)
    rejectors: list[str] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    voting_deadline: str | None = None
    executed_at: str | None = None
    previous_change_hash: str | None = None
    proposal_hash: str | None = None

    def __post_init__(self) -> None:
        if not self.proposal_hash:
            self.proposal_hash = self._generate_hash()

    def _generate_hash(self) -> str:
        data = {
            "proposal_id": self.proposal_id,
            "change_type": self.change_type.value,
            "pattern_id": self.pattern_id,
            "proposed_by": self.proposed_by,
            "rationale": self.rationale,
            "created_at": self.created_at,
        }
        return hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()

@dataclass
class BaselineTribunalRuling:
    """Tribunal ruling on a baseline change."""
    ruling_id: str
    proposal_id: str
    ruling_type: RulingType  # UPHOLD, OVERRULE, MODIFY, DISMISS
    reasoning: str
    confidence: float
    quorum_achieved: bool
    vote_summary: dict[str, int]  # APPROVE/REJECT/ABSTAIN counts
    issued_by: str = "baseline_tribunal"
    timestamp: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    hash: str | None = None

    def __post_init__(self) -> None:
        if not self.hash:
            self.hash = self._generate_hash()

    def _generate_hash(self) -> str:
        data = {
            "ruling_id": self.ruling_id,
            "proposal_id": self.proposal_id,
            "ruling_type": self.ruling_type.value,
            "reasoning": self.reasoning,
            "confidence": self.confidence,
            "quorum_achieved": self.quorum_achieved,
            "vote_summary": self.vote_summary,
            "timestamp": self.timestamp,
        }
        return hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()
```

#### Core Class: `BaselineTribunal`

```python
class BaselineTribunal:
    """
    Specialized tribunal for baseline change approval.

    Extends the general Tribunal system with baseline-specific
    quorum voting and approval workflows.

    Features:
    - CONS-03 quorum approval (3+ agents required)
    - Gradual drift handling via deliberation
    - Emergency reset with Charlie approval
    - Integration with ConsensusAuditTrail
    """

    def __init__(
        self,
        quorum_size: int = 3,
        voting_timeout_seconds: float = 300.0,
        approval_threshold: float = 0.66,
        drift_threshold: float = 0.15,  # 15% change triggers drift review
    ):
        # Storage
        self._proposals: dict[str, BaselineChangeProposal] = {}
        self._rulings: dict[str, BaselineTribunalRuling] = {}
        self._pattern_change_votes: dict[str, dict[str, str]] = {}  # pattern_id -> {agent_id -> vote}

        # Configuration
        self._quorum_size = quorum_size
        self._voting_timeout = voting_timeout_seconds
        self._approval_threshold = approval_threshold
        self._drift_threshold = drift_threshold

        # Eligible voters (Core Triad + Safety agents)
        self._eligible_voters: set[str] = {
            "steward", "alpha", "beta", "charlie",
            "sentinel", "sentinel_prime",
        }

        # Drift tracking
        self._drift_history: list[dict[str, Any]] = []

        logger.info(
            "BaselineTribunal initialized",
            quorum_size=quorum_size,
            voting_timeout=voting_timeout_seconds,
            drift_threshold=drift_threshold,
        )

    def propose_baseline_change(
        self,
        change_type: BaselineChangeType,
        proposed_by: str,
        rationale: str,
        pattern_id: str | None = None,
        evidence_refs: list[str] | None = None,
    ) -> BaselineChangeProposal:
        """Propose a baseline change for tribunal approval."""
        proposal_id = f"bl_proposal-{datetime.now(UTC).timestamp()}"

        # Calculate voting deadline
        voting_deadline = datetime.now(UTC).timestamp() + self._voting_timeout

        proposal = BaselineChangeProposal(
            proposal_id=proposal_id,
            change_type=change_type,
            pattern_id=pattern_id,
            proposed_by=proposed_by,
            rationale=rationale,
            evidence_refs=evidence_refs or [],
            voting_deadline=datetime.fromtimestamp(voting_deadline, UTC).isoformat(),
        )

        self._proposals[proposal_id] = proposal

        logger.info(
            "Baseline change proposed",
            proposal_id=proposal_id,
            change_type=change_type.value,
            proposed_by=proposed_by,
        )

        return proposal

    def cast_vote(
        self,
        proposal_id: str,
        agent_id: str,
        decision: VoteDecision,
        reasoning: str | None = None,
    ) -> dict[str, Any]:
        """
        Cast a vote on a baseline change proposal.

        Returns result with quorum status.
        """
        proposal = self._proposals.get(proposal_id)
        if not proposal:
            return {"success": False, "error": "Proposal not found"}

        if proposal.status not in (BaselineChangeStatus.PROPOSED, BaselineChangeStatus.VOTING):
            return {"success": False, "error": "Proposal not accepting votes"}

        if agent_id not in self._eligible_voters:
            return {"success": False, "error": "Agent not eligible to vote"}

        # Record vote
        proposal.votes[agent_id] = decision

        if decision == VoteDecision.APPROVE:
            if agent_id not in proposal.approvers:
                proposal.approvers.append(agent_id)
        elif decision == VoteDecision.REJECT:
            if agent_id not in proposal.rejectors:
                proposal.rejectors.append(agent_id)

        # Update status
        proposal.status = BaselineChangeStatus.VOTING

        # Check quorum
        quorum_result = self._check_quorum(proposal)

        logger.info(
            "Vote cast",
            proposal_id=proposal_id,
            agent_id=agent_id,
            decision=decision.value,
            current_approvers=len(proposal.approvers),
            current_rejectors=len(proposal.rejectors),
        )

        return {
            "success": True,
            "proposal_id": proposal_id,
            "vote_recorded": True,
            "quorum_achieved": quorum_result["achieved"],
            "votes_summary": {
                "approve": len(proposal.approvers),
                "reject": len(proposal.rejectors),
                "total": len(proposal.votes),
            },
        }

    def _check_quorum(self, proposal: BaselineChangeProposal) -> dict[str, Any]:
        """Check if quorum has been achieved."""
        total_votes = len(proposal.votes)
        approve_count = len(proposal.approvers)
        reject_count = len(proposal.rejectors)

        if total_votes < self._quorum_size:
            return {
                "achieved": False,
                "reason": f"Insufficient votes: {total_votes}/{self._quorum_size}",
                "approve_count": approve_count,
                "reject_count": reject_count,
            }

        approve_ratio = approve_count / total_votes

        if approve_ratio >= self._approval_threshold:
            proposal.status = BaselineChangeStatus.APPROVED
            return {
                "achieved": True,
                "reason": "Approval threshold reached",
                "approve_count": approve_count,
                "reject_count": reject_count,
            }

        if reject_count >= total_votes - approve_count + 1:  # Majority reject
            proposal.status = BaselineChangeStatus.REJECTED
            return {
                "achieved": False,
                "reason": "Majority rejection",
                "approve_count": approve_count,
                "reject_count": reject_count,
            }

        return {
            "achieved": False,
            "reason": "Voting ongoing",
            "approve_count": approve_count,
            "reject_count": reject_count,
        }

    def issue_ruling(
        self,
        proposal_id: str,
        reasoning: str,
        confidence: float = 1.0,
    ) -> BaselineTribunalRuling:
        """Issue a ruling on an approved baseline change."""
        proposal = self._proposals.get(proposal_id)
        if not proposal:
            raise ValueError(f"Proposal not found: {proposal_id}")

        ruling_id = f"bl_ruling-{datetime.now(UTC).timestamp()}"

        ruling = BaselineTribunalRuling(
            ruling_id=ruling_id,
            proposal_id=proposal_id,
            ruling_type=RulingType.UPHOLD,
            reasoning=reasoning,
            confidence=confidence,
            quorum_achieved=proposal.status == BaselineChangeStatus.APPROVED,
            vote_summary={
                "approve": len(proposal.approvers),
                "reject": len(proposal.rejectors),
                "abstain": len(proposal.votes) - len(proposal.approvers) - len(proposal.rejectors),
            },
        )

        self._rulings[ruling_id] = ruling
        proposal.status = BaselineChangeStatus.EXECUTED
        proposal.executed_at = datetime.now(UTC).isoformat()

        logger.info(
            "Baseline tribunal ruling issued",
            ruling_id=ruling_id,
            proposal_id=proposal_id,
            ruling_type=RulingType.UPHOLD.value,
        )

        return ruling

    def request_emergency_reset(
        self,
        initiated_by: str,
        reason: str,
        target_snapshot_id: str | None = None,
    ) -> BaselineChangeProposal:
        """Request emergency baseline reset - requires Charlie approval."""
        if initiated_by != "steward":
            raise ValueError("Only Steward can initiate emergency reset")

        proposal = self.propose_baseline_change(
            change_type=BaselineChangeType.EMERGENCY_RESET,
            proposed_by=initiated_by,
            rationale=reason,
            pattern_id=target_snapshot_id,
        )
        proposal.emergency = True

        logger.warning(
            "Emergency reset requested",
            proposal_id=proposal.proposal_id,
            initiated_by=initiated_by,
            reason=reason,
        )

        return proposal

    def approve_emergency_reset(
        self,
        proposal_id: str,
        approved_by: str,
    ) -> dict[str, Any]:
        """Approve emergency reset - requires Charlie."""
        if approved_by != "charlie":
            return {"success": False, "error": "Charlie approval required for emergency reset"}

        proposal = self._proposals.get(proposal_id)
        if not proposal:
            return {"success": False, "error": "Proposal not found"}

        if proposal.change_type != BaselineChangeType.EMERGENCY_RESET:
            return {"success": False, "error": "Not an emergency reset proposal"}

        # Charlie approved - auto-approve
        result = self.cast_vote(proposal_id, approved_by, VoteDecision.APPROVE)

        if result.get("quorum_achieved"):
            # Issue immediate ruling
            self.issue_ruling(
                proposal_id,
                reasoning="Emergency reset approved by Charlie",
                confidence=1.0,
            )

        return result

    def check_baseline_drift(
        self,
        baseline_store: "BehavioralBaselineStore",
    ) -> dict[str, Any]:
        """
        Check for baseline drift (gradual unauthorized changes).

        Returns drift analysis.
        """
        patterns = baseline_store.get_all_patterns()

        # Calculate status distribution
        status_counts: dict[str, int] = {}
        for pattern in patterns.values():
            status_counts[pattern.status.value] = status_counts.get(pattern.status.value, 0) + 1

        total = len(patterns)
        provisional_ratio = status_counts.get("provisional", 0) / max(total, 1)
        proven_ratio = status_counts.get("proven", 0) / max(total, 1)

        drift_detected = provisional_ratio > self._drift_threshold

        drift_report = {
            "drift_detected": drift_detected,
            "total_patterns": total,
            "status_distribution": status_counts,
            "provisional_ratio": provisional_ratio,
            "proven_ratio": proven_ratio,
            "threshold": self._drift_threshold,
        }

        if drift_detected:
            self._drift_history.append({
                "timestamp": datetime.now(UTC).isoformat(),
                "report": drift_report,
            })
            logger.warning("Baseline drift detected", **drift_report)

        return drift_report

    def get_proposal_status(self, proposal_id: str) -> BaselineChangeProposal | None:
        """Get current status of a proposal."""
        return self._proposals.get(proposal_id)

    def list_pending_proposals(self) -> list[BaselineChangeProposal]:
        """List all proposals awaiting approval."""
        return [
            p for p in self._proposals.values()
            if p.status in (BaselineChangeStatus.PROPOSED, BaselineChangeStatus.VOTING)
        ]

    def get_tribunal_statistics(self) -> dict[str, Any]:
        """Get tribunal statistics."""
        total = len(self._proposals)
        approved = sum(1 for p in self._proposals.values() if p.status == BaselineChangeStatus.APPROVED)
        rejected = sum(1 for p in self._proposals.values() if p.status == BaselineChangeStatus.REJECTED)

        return {
            "total_proposals": total,
            "approved": approved,
            "rejected": rejected,
            "pending": total - approved - rejected,
            "approval_rate": approved / max(total, 1),
            "quorum_size": self._quorum_size,
            "eligible_voters": list(self._eligible_voters),
            "drift_events": len(self._drift_history),
        }
```

### 3.3 Enhanced `src/heretek_swarm/security/behavioral_baseline.py`

#### Additions Required

```python
# Add to existing BehavioralBaselineStore class:

class BehavioralBaselineStore:
    # ... existing code from CONS-02 ...

    def get_baseline_hash(self) -> str:
        """Get cryptographic hash of current baseline state."""
        # Generate hash from all patterns

    def get_change_history_ids(self) -> list[str]:
        """Get list of change history IDs."""
        # Return change IDs from audit trail

    def restore_from_snapshot(self, snapshot: BaselineSnapshot) -> bool:
        """Restore baseline from a snapshot."""
        # Implement restoration logic
```

### 3.4 Enhanced `src/heretek_swarm/actors/steward.py`

#### Additions for CONS-03

```python
# Add imports
from heretek_swarm.consensus.baseline_tribunal import (
    BaselineTribunal,
    BaselineChangeProposal,
    BaselineChangeType,
    VoteDecision,
    BaselineChangeStatus,
)
from heretek_swarm.security.baseline_rollback import (
    BaselineRollbackManager,
    RollbackReason,
)
from heretek_swarm.security.behavioral_baseline import BehavioralBaselineStore

# Add new attributes
self.baseline_tribunal: BaselineTribunal | None = None
self.baseline_rollback_manager: BaselineRollbackManager | None = None
self.baseline_store: BehavioralBaselineStore | None = None
self._baseline_deliberations: dict[str, dict[str, Any]] = {}

# Add new message handlers
self.register_handler("propose_baseline_change", self._handle_propose_baseline_change)
self.register_handler("vote_baseline_change", self._handle_vote_baseline_change)
self.register_handler("request_emergency_reset", self._handle_emergency_reset)
self.register_handler("approve_emergency_reset", self._handle_approve_emergency_reset)
self.register_handler("check_baseline_drift", self._handle_check_baseline_drift)
self.register_handler("get_baseline_status", self._handle_get_baseline_status)

# New handler methods

async def _handle_propose_baseline_change(self, message: ActorMessage) -> None:
    """
    Handle baseline change proposal.

    Content: {
        "change_type": str,
        "pattern_id": str | None,
        "rationale": str,
        "evidence_refs": list[str] | None,
    }
    """
    content = message.content
    change_type = BaselineChangeType(content["change_type"])
    pattern_id = content.get("pattern_id")
    rationale = content["rationale"]
    evidence_refs = content.get("evidence_refs", [])

    if not self.baseline_tribunal:
        await self._send_error(message, "Tribunal not initialized")
        return

    proposal = self.baseline_tribunal.propose_baseline_change(
        change_type=change_type,
        proposed_by=self.agent_id,
        rationale=rationale,
        pattern_id=pattern_id,
        evidence_refs=evidence_refs,
    )

    await self._send_response(message, {
        "proposal_id": proposal.proposal_id,
        "status": proposal.status.value,
        "voting_deadline": proposal.voting_deadline,
    })

async def _handle_vote_baseline_change(self, message: ActorMessage) -> None:
    """
    Handle vote on baseline change.

    Content: {
        "proposal_id": str,
        "decision": str (approve/reject/abstain),
        "reasoning": str | None,
    }
    """
    content = message.content
    proposal_id = content["proposal_id"]
    decision = VoteDecision(content["decision"])

    if not self.baseline_tribunal:
        await self._send_error(message, "Tribunal not initialized")
        return

    result = self.baseline_tribunal.cast_vote(
        proposal_id=proposal_id,
        agent_id=self.agent_id,
        decision=decision,
        reasoning=content.get("reasoning"),
    )

    await self._send_response(message, result)

async def _handle_emergency_reset(self, message: ActorMessage) -> None:
    """
    Handle emergency reset request (Steward only).

    Content: {
        "reason": str,
        "target_snapshot_id": str | None,
    }
    """
    if self.agent_id != "steward":
        await self._send_error(message, "Only Steward can request emergency reset")
        return

    content = message.content
    reason = content["reason"]
    target_snapshot_id = content.get("target_snapshot_id")

    if not self.baseline_tribunal:
        await self._send_error(message, "Tribunal not initialized")
        return

    proposal = self.baseline_tribunal.request_emergency_reset(
        initiated_by=self.agent_id,
        reason=reason,
        target_snapshot_id=target_snapshot_id,
    )

    await self._send_response(message, {
        "proposal_id": proposal.proposal_id,
        "status": "awaiting_charlie_approval",
        "requires_charlie": True,
    })

async def _handle_approve_emergency_reset(self, message: ActorMessage) -> None:
    """
    Handle Charlie's approval of emergency reset.

    Content: {
        "proposal_id": str,
    }
    """
    content = message.content

    if self.agent_id != "charlie":
        await self._send_error(message, "Only Charlie can approve emergency reset")
        return

    if not self.baseline_tribunal:
        await self._send_error(message, "Tribunal not initialized")
        return

    result = self.baseline_tribunal.approve_emergency_reset(
        proposal_id=content["proposal_id"],
        approved_by=self.agent_id,
    )

    if result.get("success") and result.get("quorum_achieved"):
        # Execute the rollback
        if self.baseline_rollback_manager:
            self.baseline_rollback_manager.execute_rollback(
                content["proposal_id"],
                self.baseline_store,
            )

    await self._send_response(message, result)

async def _handle_check_baseline_drift(self, message: ActorMessage) -> None:
    """
    Check for baseline drift.

    Returns drift analysis report.
    """
    if not self.baseline_tribunal or not self.baseline_store:
        await self._send_error(message, "Tribunal or baseline store not initialized")
        return

    drift_report = self.baseline_tribunal.check_baseline_drift(self.baseline_store)

    await self._send_response(message, drift_report)

async def _handle_get_baseline_status(self, message: ActorMessage) -> None:
    """
    Get current baseline status.

    Returns current patterns and tribunal status.
    """
    if not self.baseline_store:
        await self._send_error(message, "Baseline store not initialized")
        return

    patterns = self.baseline_store.get_all_patterns()
    tribunal_stats = self.baseline_tribunal.get_tribunal_statistics() if self.baseline_tribunal else {}

    await self._send_response(message, {
        "total_patterns": len(patterns),
        "patterns_by_status": {
            status.value: sum(1 for p in patterns.values() if p.status == status)
            for status in PatternStatus
        },
        "tribunal_statistics": tribunal_stats,
    })
```

---

## 4. Integration Points

### 4.1 With Immune Response Engine (Task 2)

- Immune system proposes baseline changes via `BaselineTribunal`
- Immune learning triggers drift detection
- False positive patterns require tribunal approval to reject

### 4.2 With Consensus Audit Trail

- All baseline changes recorded via `ConsensusAuditTrail`
- Hash chain ensures immutability
- Rollback operations audited

### 4.3 With Deliberation Engine (Task 1)

- Use `DeliberationEngine` for multi-round baseline discussions
- Integrate with tribunal voting

---

## 5. Verification Criteria

| Criterion | Measurement | Pass Threshold |
|-----------|-------------|----------------|
| CONS-03 quorum approval | Baseline changes require votes | 3+ agents approve |
| Immutable audit trail | Hash chain integrity | Passes verify_integrity() |
| Rollback capability | Can restore to snapshot | Successfully restores patterns |
| Emergency reset | Charlie approval required | Only Charlie can approve |
| Baseline drift detection | 15% change threshold | Detects gradual drift |
| Gradual update approval | Multi-agent deliberation | 3+ round deliberation |

---

## 6. Edge Case Handling

### 6.1 Baseline Drift During Normal Operation

**Detection**:
- `check_baseline_drift()` monitors provisional ratio
- If >15% patterns are provisional, drift flagged

**Response**:
1. Trigger tribunal review
2. Require deliberation on drift causes
3. Gradual approval of legitimate changes
4. Reject unauthorized modifications

**Flow**:
```
Drift Detected (15%+ provisional)
    ↓
Tribunal Review Initiated
    ↓
Multi-Agent Deliberation
    ↓
Gradual Change Approval
    ↓
If Unauthorized → Rollback
If Legitimate → Promote to Proven
```

### 6.2 Emergency Baseline Reset

**Trigger**: Steward initiates with reason

**Approval**: Charlie must approve

**Execution**:
1. Steward calls `request_emergency_reset()`
2. Charlie calls `approve_emergency_reset()`
3. `BaselineRollbackManager` executes rollback
4. Full audit trail recorded

**Flow**:
```
Steward Requests Reset
    ↓
Charlie Reviews Reason
    ↓
Charlie Approves
    ↓
BaselineRollbackManager.Executing
    ↓
Immutable Audit Recorded
```

---

## 7. Implementation Order

### Phase 1: Core Infrastructure (Day 1-2)

1. Create `src/heretek_swarm/security/baseline_rollback.py`
   - `BaselineSnapshot` dataclass
   - `RollbackOperation` dataclass
   - `BaselineRollbackManager` class
   - Snapshot creation and pruning

2. Create `src/heretek_swarm/consensus/baseline_tribunal.py`
   - `BaselineChangeProposal` dataclass
   - `BaselineTribunalRuling` dataclass
   - `BaselineTribunal` class
   - Quorum voting logic

### Phase 2: Integration (Day 3-4)

3. Enhance `src/heretek_swarm/security/behavioral_baseline.py`
   - Add `get_baseline_hash()` method
   - Add `restore_from_snapshot()` method
   - Add `get_change_history_ids()` method

4. Enhance `src/heretek_swarm/actors/steward.py`
   - Add BaselineTribunal integration
   - Add message handlers
   - Add emergency reset handling

### Phase 3: Testing & Verification (Day 5)

5. Create tests:
   - `tests/consensus/test_baseline_tribunal.py`
   - `tests/security/test_baseline_rollback.py`

6. Verify:
   - Quorum voting works
   - Rollback restores state
   - Emergency reset requires Charlie
   - Drift detection triggers

---

## 8. File Summary

| File | Action | Lines Added |
|------|--------|-------------|
| `src/heretek_swarm/security/baseline_rollback.py` | CREATE | ~350 |
| `src/heretek_swarm/consensus/baseline_tribunal.py` | CREATE | ~450 |
| `src/heretek_swarm/security/behavioral_baseline.py` | ENHANCE | ~50 |
| `src/heretek_swarm/actors/steward.py` | ENHANCE | ~200 |
| `tests/consensus/test_baseline_tribunal.py` | CREATE | ~150 |
| `tests/security/test_baseline_rollback.py` | CREATE | ~150 |

**Total New Code**: ~1,050 lines
**Total Test Code**: ~300 lines

---

## 9. Dependencies

```
Task 1 (DeliberationEngine) ────────────────────┐
                                                 │
Task 2 (BehavioralBaselineStore) ────────────────┼──► THIS TASK (CONS-03)
                                                 │
Phase 1 (ConsensusAuditTrail) ─────────────────┘
```

---

## 10. Open Questions (for resolution during implementation)

1. **Quorum size**: Default is 3 - appropriate for Core Triad + Safety agents?
2. **Voting timeout**: 300 seconds (5 min) - sufficient for deliberation?
3. **Drift threshold**: 15% - too sensitive or too lenient?
4. **Emergency reset scope**: Full reset or targeted rollback?
5. **Rollback granularity**: Per-pattern or full baseline?
6. **Charlie identity**: How is Charlie agent identified in the system?
