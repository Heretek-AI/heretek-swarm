# Implementation Plan: CONS-02 — Immune Response Building

## Task Overview

**Owner**: Sentinel
**Depends**: Task 1 (deliberation engine), Phase 1 (ValidationMixin)
**Verification**: Sentinel learns from anomaly responses; patterns added to baseline; false positive rate < 1%

## Edge Cases

- Baseline corruption attempt — immutable audit trail; baseline changes require quorum
- Novel attack patterns — preserved for human review; not auto-added to baseline

---

## 1. Analysis of Existing Code

### 1.1 Sentinel Agent (`src/heretek_swarm/actors/sentinel.py`)

**Current Capabilities**:
- Input/output validation with `_scan_content()`
- Pattern-based injection detection (`_check_injection_patterns()`)
- PII detection (`_check_pii_patterns()`)
- Violation tracking with LRU history
- Safety reporting

**Missing for Immune Response**:
- No learning from past detections
- No pattern memory across sessions
- No feedback loop from confirmed attacks
- No integration with deliberation for baseline changes

### 1.2 Behavioral Baseline (referenced in existing code)

**Where it exists**:
- `zero_trust.py`: `BehavioralBaseline` dataclass (lines 344-354) - simple in-memory baseline per agent
- `validation.py`: `_behavioral_baseline` dict in ValidationMixin - tracks operation metrics

**Gap**: No persistent, auditable baseline store for security patterns

### 1.3 Deliberation Engine (`src/heretek_swarm/consensus/deliberation.py`)

**Key Classes**:
- `DeliberationEngine` - multi-round deliberation
- `Evidence` - evidence quality tracking
- `ConsensusConfidence` - confidence scoring

**Integration Point**: Use deliberation for baseline change approvals (quorum voting)

### 1.4 Audit Trail (`src/heretek_swarm/consensus/audit_trail.py`)

**Available Features**:
- `ConsensusAuditTrail` - hash-chained immutable events
- `record_event()` - audit with cryptographic integrity
- `verify_integrity()` - detect tampering

**Use for**: Immutable audit trail on baseline changes

### 1.5 Adversarial Detector (`src/heretek_swarm/security/adversarial.py`)

**Available**:
- `AdversarialDetector` with 50+ prompt injection signatures
- `ThreatLevel` enum (BENIGN, LOW, MEDIUM, HIGH, CRITICAL)
- `AttackCategory` enum

**Gap**: No mechanism to add new patterns from observed attacks

---

## 2. Implementation Architecture

### 2.1 New Files to Create

```
src/heretek_swarm/consensus/immune.py       # NEW - Immune Response Engine
src/heretek_swarm/security/behavioral_baseline.py  # NEW - Baseline Store
```

### 2.2 Files to Modify

```
src/heretek_swarm/actors/sentinel.py        # MODIFY - Integrate immune response
```

---

## 3. Detailed Implementation

### 3.1 `src/heretek_swarm/security/behavioral_baseline.py` (NEW)

**Purpose**: Persistent, auditable storage for security patterns that Sentinel learns.

#### Data Structures

```python
@dataclass
class SecurityPattern:
    """A security pattern learned from anomaly responses."""
    pattern_id: str
    pattern_type: str  # "injection", "pii", "adversarial"
    signature: str     # regex or hash
    description: str
    confidence: float
    first_seen: datetime
    last_confirmed: datetime
    confirmation_count: int
    false_positive_count: int
    source: str  # "immune_response", "manual", "deliberation"
    status: PatternStatus  # PROVISIONAL, PROVEN, REJECTED, HUMAN_REVIEW

class PatternStatus(StrEnum):
    PROVISIONAL = "provisional"    # Auto-added, needs confirmation
    PROVEN = "proven"              # Confirmed, safe to auto-block
    REJECTED = "rejected"          # False positive, never block
    HUMAN_REVIEW = "human_review"  # Novel attack, needs human decision

@dataclass
class BaselineChange:
    """Immutable record of a baseline modification."""
    change_id: str
    pattern_id: str
    action: ChangeAction  # ADDED, REMOVED, MODIFIED
    previous_state: dict | None
    new_state: dict | None
    quorum_votes: dict[str, str]  # agent_id -> vote (approve/reject)
    quorum_achieved: bool
    timestamp: datetime
    previous_change_hash: str | None
    change_hash: str

class ChangeAction(StrEnum):
    ADDED = "added"
    REMOVED = "removed"
    MODIFIED = "modified"
```

#### Core Class: `BehavioralBaselineStore`

```python
class BehavioralBaselineStore:
    """
    Persistent, auditable store for security patterns.

    Features:
    - Immutable audit trail for all changes (hash chain)
    - Quorum-based change approval
    - Pattern classification (proven/novel/false positive)
    - False positive tracking for rate < 1%
    """

    def __init__(
        self,
        storage_backend: str = "memory",
        quorum_size: int = 3,
        approval_threshold: float = 0.66,
    ):
        # Pattern storage
        self._patterns: dict[str, SecurityPattern] = {}

        # Change audit trail
        self._change_history: list[BaselineChange] = []
        self._last_change_hash: str | None = None

        # Quorum configuration
        self._quorum_size = quorum_size
        self._approval_threshold = approval_threshold

        # Statistics
        self._stats = {
            "total_patterns": 0,
            "proven_patterns": 0,
            "false_positives": 0,
            "novel_attacks": 0,
        }

    def add_provisional_pattern(self, pattern: SecurityPattern) -> str:
        """Add a new pattern in provisional status."""
        # Creates hash chain entry
        # Does NOT auto-promote to proven

    def record_false_positive(self, pattern_id: str) -> None:
        """Record that a pattern caused a false positive."""
        # Increments false_positive_count
        # If FP rate > 5%, demotes to REJECTED

    def confirm_pattern(self, pattern_id: str) -> None:
        """Confirm a provisional pattern as valid attack."""
        # Increments confirmation_count
        # If confirmation_rate > 80%, promotes to PROVEN

    def request_human_review(self, pattern_id: str) -> None:
        """Flag pattern for human review (novel attack)."""
        # Sets status to HUMAN_REVIEW
        # Does NOT auto-add to blocking patterns

    def propose_baseline_change(
        self,
        pattern_id: str,
        action: ChangeAction,
    ) -> BaselineChange:
        """Propose a baseline change requiring quorum."""
        # Creates BaselineChange record
        # Requires quorum approval to apply

    def cast_vote(
        self,
        change_id: str,
        agent_id: str,
        vote: str,  # "approve" or "reject"
    ) -> bool:
        """Cast a vote on a proposed baseline change."""
        # Records vote in quorum_votes
        # Returns True if quorum achieved

    def apply_change(self, change_id: str) -> bool:
        """Apply an approved baseline change."""
        # Verifies quorum achieved
        # Updates pattern store
        # Creates new hash chain entry

    def verify_integrity(self) -> dict[str, Any]:
        """Verify hash chain integrity."""
        # Checks all change hashes
        # Returns integrity status
```

### 3.2 `src/heretek_swarm/consensus/immune.py` (NEW)

**Purpose**: Core immune response engine - learns from anomaly responses.

#### Data Structures

```python
@dataclass
class AnomalyResponse:
    """Record of how Sentinel responded to an anomaly."""
    response_id: str
    anomaly_type: str
    detection_signature: str
    action_taken: ResponseAction  # BLOCKED, FLAGGED, ALLOWED
    was_correct: bool | None  # None = unconfirmed
    timestamp: datetime
    agent_id: str | None
    false_positive: bool = False

class ResponseAction(StrEnum):
    BLOCKED = "blocked"
    FLAGGED = "flagged"
    ALLOWED = "allowed"

@dataclass
class ImmuneLearningResult:
    """Result of immune learning analysis."""
    new_patterns_proposed: int
    patterns_confirmed: int
    false_positives_identified: int
    novel_attacks_flagged: int
    false_positive_rate: float
```

#### Core Class: `ImmuneResponseEngine`

```python
class ImmuneResponseEngine:
    """
    Sentinel's immune response system - learns from past anomalies.

    Responsibilities:
    1. Track anomaly responses over time
    2. Identify patterns that worked (blocking) vs didn't (false positives)
    3. Calculate false positive rate
    4. Propose new patterns to baseline store
    5. Integrate with deliberation for quorum votes

    Key Metrics:
    - False positive rate < 1%
    - Pattern confirmation threshold: 3+ confirmations
    - Novel attack flagging for human review
    """

    def __init__(
        self,
        baseline_store: BehavioralBaselineStore,
        deliberation_engine: DeliberationEngine | None = None,
    ):
        self._baseline_store = baseline_store
        self._deliberation_engine = deliberation_engine

        # Response tracking
        self._responses: list[AnomalyResponse] = []
        self._max_response_history = 10000

        # Learning configuration
        self._confirmation_threshold = 3
        self._false_positive_rate_window = 1000  # Check last 1000 responses
        self._novel_attack_threshold = 0.85  # Confidence to flag as novel

    async def record_response(
        self,
        anomaly_type: str,
        detection_signature: str,
        action: ResponseAction,
        agent_id: str | None = None,
    ) -> str:
        """Record how Sentinel responded to an anomaly."""

    async def confirm_detection(
        self,
        response_id: str,
        was_correct: bool,
    ) -> None:
        """Confirm whether a detection was correct."""
        # If was_correct=False: likely false positive
        # If was_correct=True and action=BLOCKED: confirms attack pattern

    async def analyze_and_learn(self) -> ImmuneLearningResult:
        """
        Analyze response history and update baseline.

        Returns:
            ImmuneLearningResult with learning metrics
        """
        # 1. Count recent false positives
        # 2. Identify patterns needing confirmation
        # 3. Flag novel attacks for human review
        # 4. Return learning results

    def calculate_false_positive_rate(self) -> float:
        """Calculate current false positive rate."""
        # FP / (FP + TP) over recent window
        # Must be < 0.01 (1%)

    def get_pattern_recommendations(self) -> list[dict[str, Any]]:
        """Get patterns recommended for baseline addition."""
        # Patterns with confirmation_count >= threshold
        # Excludes false positives

    async def request_baseline_change(
        self,
        pattern_id: str,
        change_type: ChangeAction,
    ) -> str:
        """Request a baseline change through deliberation."""
        # Creates BaselineChange proposal
        # Initiates quorum voting
```

### 3.3 Sentinel Enhancements (`src/heretek_swarm/actors/sentinel.py`)

#### New Imports

```python
from heretek_swarm.consensus.immune import (
    ImmuneResponseEngine,
    AnomalyResponse,
    ResponseAction,
)
from heretek_swarm.security.behavioral_baseline import (
    BehavioralBaselineStore,
    SecurityPattern,
    PatternStatus,
)
```

#### New Attributes

```python
# Immune response system
self._immune_engine: ImmuneResponseEngine | None = None
self._baseline_store: BehavioralBaselineStore | None = None

# Pattern cache for current session
self._active_patterns: dict[str, SecurityPattern] = {}
```

#### New Message Handlers

```python
# In _register_handlers()
"immune_record_response": self._handle_immune_record_response,
"immune_get_learning_result": self._handle_immune_get_learning_result,
"immune_request_baseline_change": self._handle_immune_request_baseline_change,
"baseline_get_patterns": self._handle_baseline_get_patterns,
```

#### New Methods

```python
async def _handle_immune_record_response(self, message: ActorMessage) -> None:
    """
    Record an immune response from Sentinel's detection.

    Content: {
        "anomaly_type": str,
        "detection_signature": str,
        "action": str (blocked/flagged/allowed),
        "was_correct": bool | None,
    }
    """

async def _handle_immune_get_learning_result(self, message: ActorMessage) -> None:
    """
    Get immune learning analysis results.

    Returns: {
        "new_patterns_proposed": int,
        "patterns_confirmed": int,
        "false_positives_identified": int,
        "novel_attacks_flagged": int,
        "false_positive_rate": float,
    }
    """

async def _handle_baseline_get_patterns(self, message: ActorMessage) -> None:
    """
    Get current baseline patterns.

    Content: {
        "status": str | None (filter by status),
    }
    """
```

#### Pattern Integration in `_scan_content()`

Modify `_scan_content()` to:
1. Check detected patterns against `BehavioralBaselineStore`
2. Use PROVEN patterns in addition to built-in patterns
3. Record responses via `_immune_engine.record_response()`

---

## 4. Integration Points

### 4.1 With Deliberation Engine (Task 1 dependency)

- Use `DeliberationEngine` for quorum voting on baseline changes
- Baseline changes require `quorum_size` agents to approve
- Integrate via `TribunalMixin` if available

### 4.2 With Audit Trail

- All baseline changes recorded via `ConsensusAuditTrail`
- Hash chain ensures immutability
- `verify_integrity()` available for corruption detection

### 4.3 With ValidationMixin (Phase 1)

- Leverage existing `_behavioral_baseline` tracking
- Extend to include security pattern learning
- Share false positive tracking metrics

---

## 5. Verification Criteria

| Criterion | Measurement | Pass Threshold |
|-----------|-------------|----------------|
| Sentinel learns from anomalies | New patterns proposed after confirmed attacks | >= 1 pattern per 10 confirmed attacks |
| Patterns added to baseline | PROVEN patterns in baseline store | Only after quorum approval |
| False positive rate | FP / (FP + TP) over window | < 1% |
| Baseline corruption detection | Hash chain integrity check | Passes verify_integrity() |
| Novel attack preservation | Patterns flagged for human review | Not auto-added to baseline |
| Quorum voting operational | Baseline changes require votes | 3+ agents approve |

---

## 6. Edge Case Handling

### 6.1 Baseline Corruption Attempt

**Detection**:
- Hash chain verification via `verify_integrity()`
- Any hash mismatch = corruption detected

**Response**:
- Reject proposed change
- Log CRITICAL security event
- Notify Core Triad (Steward)

**Prevention**:
- Immutable hash chain on all changes
- Quorum required for any modification

### 6.2 Novel Attack Patterns

**Detection**:
- High confidence detection (>85%) but not in known patterns
- First-time detection with unique signature

**Response**:
- Flag as `HUMAN_REVIEW` status
- Block content but log separately
- Do NOT auto-add to baseline
- Notify human for review

**Flow**:
```
Novel Attack Detected
    ↓
Flag as HUMAN_REVIEW
    ↓
Block content (protective)
    ↓
Notify human reviewer
    ↓
Human approves/rejects
    ↓
If approved → PROVISIONAL → quorum → PROVEN
If rejected → REJECTED
```

### 6.3 False Positive Cascade

**Detection**:
- FP rate exceeds 1% threshold
- Same pattern triggered multiple times incorrectly

**Response**:
- Auto-decrement pattern confidence
- If FP rate > 5%: demote to REJECTED
- Rate limit automated responses
- Notify human of cascade

---

## 7. Implementation Order

### Phase 1: Core Infrastructure (Day 1-2)

1. Create `src/heretek_swarm/security/behavioral_baseline.py`
   - `SecurityPattern` dataclass
   - `BaselineChange` dataclass
   - `BehavioralBaselineStore` class
   - Hash chain integrity

### Phase 2: Immune Engine (Day 3-4)

2. Create `src/heretek_swarm/consensus/immune.py`
   - `AnomalyResponse` dataclass
   - `ImmuneResponseEngine` class
   - Learning algorithms
   - Pattern recommendations

### Phase 3: Sentinel Integration (Day 5-6)

3. Enhance `src/heretek_swarm/actors/sentinel.py`
   - Add imports
   - Add new attributes
   - Add message handlers
   - Integrate with `_scan_content()`

### Phase 4: Testing & Verification (Day 7)

4. Create tests:
   - `tests/consensus/test_immune_response.py`
   - `tests/security/test_behavioral_baseline.py`

5. Verify:
   - False positive rate < 1%
   - Hash chain integrity
   - Quorum voting works

---

## 8. File Summary

| File | Action | Lines Added |
|------|--------|-------------|
| `src/heretek_swarm/security/behavioral_baseline.py` | CREATE | ~400 |
| `src/heretek_swarm/consensus/immune.py` | CREATE | ~350 |
| `src/heretek_swarm/actors/sentinel.py` | ENHANCE | ~200 |
| `tests/consensus/test_immune_response.py` | CREATE | ~150 |
| `tests/security/test_behavioral_baseline.py` | CREATE | ~150 |

**Total New Code**: ~1,100 lines
**Total Test Code**: ~300 lines

---

## 9. Dependencies

```
Phase 1 (ValidationMixin) ──────┐
                                │
Task 1 (DeliberationEngine) ───┼──► THIS TASK (CONS-02)
                                │
Phase 1 (ConsensusAuditTrail) ─┘
```

---

## 10. Open Questions (for resolution during implementation)

1. **Quorum size**: Default is 3 - appropriate for 23-agent collective?
2. **Confirmation threshold**: 3 confirmations to promote to PROVEN - sensitive enough?
3. **Novel attack confidence**: 85% threshold - too aggressive or too conservative?
4. **False positive window**: 1000 responses - statistically significant?
5. **Integration with TribunalMixin**: Should use existing tribunal or create new quorum mechanism?
