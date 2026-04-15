# IMPLEMENTATION_CONS01: Inter-Agent Dispute Consensus Engine

## Phase 2 - Gate 2 Implementation

**Created:** 2026-04-15  
**Status:** IMPLEMENTED  
**Success Criteria:** 100% consensus without human mediation for non-critical decisions, ≥15% position change ratio

---

## 1. Overview

### Purpose
CONS01 implements the Inter-Agent Dispute Consensus engine - the foundational deliberation mechanism that resolves disputes between agents without human mediation.

### Critical Path Context
- **Gate 1:** PASSED (7/7 criteria met 2026-04-14)
- **Gate 2 Target:** 100% consensus without human mediation for non-critical decisions
- **Blocking:** CONS02, CONS03, SAFE03

### Critical vs Non-Critical Decisions

| Decision Type | Classification | Mediation Required |
|---------------|----------------|-------------------|
| Constitutional rules | CRITICAL | YES - Human escalation |
| Safety-critical actions | CRITICAL | YES - Human escalation |
| Resource allocation >20% capacity | CRITICAL | YES - Human escalation |
| External-facing with reputational impact | CRITICAL | YES - Human escalation |
| All other decisions | NON-CRITICAL | NO - 100% autonomous |

---

## 2. Architecture

### 2.1 Core Components

```
cons01_dispute_resolution.py
├── DisputeType enum - Classifies disputes as CRITICAL/NON-CRITICAL
├── Dispute dataclass - Dispute submission with parties, topic, evidence
├── DisputeState enum - States: SUBMITTED → DELIBERATING → CONSENSUS/ESCALATED
├── PositionChangeTracker - Tracks position changes for ≥15% ratio
├── ConsensusResult - Final outcome with minority reports preserved
└── DisputeResolutionEngine - Main orchestration engine
```

### 2.2 Integration with Existing Infrastructure

| Component | Relationship | Purpose |
|-----------|--------------|---------|
| `SwarmDeliberationEngine` | Composes | Multi-round deliberation with argument exchange |
| `MAKERConsensus` | Composes | First-to-ahead-by-k voting mechanism |
| `Tribunal` | Escalates to | Binding decisions for CRITICAL disputes |
| `AgentExpertiseProfiler` | Uses | Expertise-weighted voting |
| `DeliberationMixin` | Uses | Agent deliberation interface |

### 2.3 Data Flow

```
1. Dispute Submitted (agent dispute)
         ↓
2. Classify Dispute (CRITICAL vs NON-CRITICAL)
         ↓
   ┌─────┴─────┐
   ↓           ↓
CRITICAL    NON-CRITICAL
   ↓           ↓
Tribunal    SwarmDeliberationEngine
(_binding)   (autonomous)
   ↓           ↓
   └─────┬─────┘
         ↓
3. Track Position Changes (≥15% target)
         ↓
4. Reach Consensus or Binding Decision
         ↓
5. Preserve Minority Reports
         ↓
6. Return DisputeResult
```

---

## 3. Implementation Details

### 3.1 Dispute Classification

```python
class DisputeType(Enum):
    """Classification of disputes by criticality."""
    CONSTITUTIONAL = "constitutional"      # CRITICAL - human escalation
    SAFETY_CRITICAL = "safety_critical"   # CRITICAL - human escalation
    RESOURCE_ALLOCATION = "resource"      # CRITICAL - human escalation if >20%
    EXTERNAL_REPUTATION = "reputation"     # CRITICAL - human escalation
    TECHNICAL = "technical"                # NON-CRITICAL - autonomous
    PRIORITY = "priority"                  # NON-CRITICAL - autonomous
    IMPLEMENTATION = "implementation"       # NON-CRITICAL - autonomous
```

### 3.2 Position Change Tracking

The deliberation engine tracks all position changes to ensure ≥15% of agents modify their positions during deliberation:

```python
@dataclass
class PositionChangeRecord:
    agent_id: str
    dispute_id: str
    round: int
    old_position: str
    new_position: str
    timestamp: str

# Calculation
position_change_ratio = agents_who_changed_position / total_participants
# Target: ≥ 0.15 (15%)
```

### 3.3 Consensus Achievement

For **NON-CRITICAL** disputes, consensus is achieved when:
1. ≥ 75% weighted agreement (configurable threshold)
2. All participants have submitted positions
3. Minimum deliberation rounds completed (2 rounds minimum)

For **CRITICAL** disputes, consensus is escalated to Tribunal with:
1. Full evidence package
2. All minority reports
3. Binding decision requirement

---

## 4. API Design

### 4.1 DisputeSubmission

```python
@dataclass
class DisputeSubmission:
    dispute_id: str
    parties: list[str]  # Agent IDs involved in dispute
    topic: str
    description: str
    dispute_type: DisputeType
    evidence: list[Evidence]  # Supporting evidence
    submitted_by: str
    timestamp: str
```

### 4.2 DisputeResolutionEngine Methods

| Method | Purpose |
|--------|---------|
| `submit_dispute()` | Accept dispute submission, classify, initiate deliberation |
| `add_participant()` | Add agent to active deliberation |
| `submit_position()` | Agent submits position with rationale |
| `run_deliberation_round()` | Execute one round of deliberation |
| `get_position_change_ratio()` | Calculate current position change ratio |
| `finalize_consensus()` | Complete deliberation, return result |
| `escalate_to_tribunal()` | Escalate CRITICAL dispute to Tribunal |
| `get_minority_report()` | Retrieve preserved minority opinions |

### 4.3 Return Types

```python
@dataclass
class DisputeResult:
    dispute_id: str
    status: DisputeState
    final_position: str | None
    consensus_score: float
    position_change_ratio: float
    minority_reports: list[MinorityReport]
    deliberation_rounds: int
    binding: bool  # True if Tribunal decision
    timestamp: str
```

---

## 5. TDD Approach

### 5.1 RED Phase - Test First

```python
def test_deliberation_engine_resolves_noncritical_disputes_without_human():
    """CONS01: Non-critical disputes achieve consensus without human mediation."""
    # 1. Create dispute between two agents
    # 2. Classify as NON-CRITICAL
    # 3. Run deliberation
    # 4. Verify consensus reached without human involvement
    # 5. Verify position change ratio ≥ 15%
```

### 5.2 GREEN Phase - Minimum Viable

- Basic dispute submission and classification
- Single-round deliberation
- Simple majority voting
- Position change tracking

### 5.3 REFACTOR Phase

- Add expertise weighting (via AgentExpertiseProfiler)
- Multi-round deliberation (via SwarmDeliberationEngine)
- Dissent tracking and minority report preservation
- Consensus threshold adaptation

---

## 6. Configuration

### 6.1 Default Values

```python
CONS01_CONFIG = {
    "consensus_threshold": 0.75,        # 75% weighted agreement
    "min_deliberation_rounds": 2,        # Minimum rounds before consensus
    "max_deliberation_rounds": 5,        # Maximum rounds
    "position_change_target": 0.15,      # 15% position change target
    "critical_resource_threshold": 0.20, # 20% capacity threshold
    "minority_report_preservation": True,
}
```

### 6.2 Expertise Weighting

Agents with higher expertise in the dispute domain receive higher vote weights:
- NOVICE (0.0-0.3): 0.5x weight
- INTERMEDIATE (0.3-0.6): 0.75x weight
- EXPERT (0.6-0.85): 1.0x weight
- MASTER (0.85-1.0): 1.5x weight

---

## 7. Minority Report Preservation

All dissenting opinions are preserved regardless of consensus outcome:

```python
@dataclass
class MinorityReport:
    agent_id: str
    original_position: str
    final_position: str  # May have changed during deliberation
    rationale: str
    confidence: float
    persisted: bool = True  # Always True for CONS01
```

---

## 8. Files Created

| File | Purpose |
|------|---------|
| `src/heretek_swarm/consensus/cons01_dispute_resolution.py` | Main implementation |
| `tests/test_consensus/test_cons01_deliberation_engine.py` | TDD tests |

---

## 9. Integration Points

### 9.1 With SwarmDeliberationEngine
- Uses `SwarmDeliberationEngine` for multi-round deliberation
- Inherits argument exchange, confidence-weighted voting
- Position change tracking integrated

### 9.2 With Tribunal
- CRITICAL disputes escalate to `Tribunal.issue_ruling()`
- Evidence package includes all deliberation records
- Tribunal ruling is binding

### 9.3 With AgentExpertiseProfiler
- Queries expertise scores for vote weighting
- Records decision outcomes for expertise updates
- Peer trust scores influence final权重

---

## 10. Verification

### 10.1 Success Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| Non-critical consensus rate | 100% | Disputes resolved without human |
| Position change ratio | ≥15% | Agents modifying positions |
| Deliberation rounds | ≤5 | Efficiency of resolution |
| Minority report preservation | 100% | All dissent recorded |

### 10.2 Test Coverage

- Non-critical dispute resolution
- CRITICAL dispute escalation
- Position change tracking
- Minority report preservation
- Expertise weighting
- Multi-round deliberation
- Edge cases (equal split, all agree, all disagree)

---

## 11. Dependencies

- `swarm_deliberation.py` - Multi-round deliberation
- `maker.py` - MAKER voting
- `tribunal.py` - CRITICAL dispute escalation
- `expertise.py` - AgentExpertiseProfiler
- `deliberation.py` - DeliberationMixin

---

## 12. Follow-on Work

- **CONS02:** Consensus state persistence
- **CONS03:** Cross-domain dispute resolution
- **SAFE03:** Safety-critical dispute handling
