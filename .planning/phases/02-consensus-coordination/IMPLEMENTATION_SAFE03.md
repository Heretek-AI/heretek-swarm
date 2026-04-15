# SAFE-03 Implementation Plan: Arbiter Dispute Mediation

## Context

**Task**: SAFE-03 — Arbiter Dispute Mediation  
**Owner**: Arbiter  
**Depends**: Task 1 (deliberation engine - CONS-01)  
**Status**: Planning

## Current State Analysis

### Existing Components

| Component | Status | Notes |
|-----------|--------|-------|
| `actors/arbiter.py` | ✅ Stub exists | Re-exports from `actors.arbiter.core` |
| `actors/arbiter/core.py` | ✅ Implemented | Full `ArbiterAgent` with conflict detection, resolution strategies, relationship management |
| `actors/arbiter/strategies.py` | ✅ Implemented | All resolution strategy methods |
| `consensus/deliberation.py` | ✅ Implemented | `DeliberationEngine` with multi-round deliberation |
| `consensus/tribunal.py` | ✅ Implemented | `Tribunal` for appeals and retroactive binding decisions |

### What mediation.py Must Provide

The current architecture handles:
- **Deliberation**: Multi-round argument exchange via `DeliberationEngine`
- **Tribunal**: Appeals and retroactive decisions via `Tribunal`

Missing is **mediation.py** - the bridge between failed deliberation and binding decisions. This module provides:

1. **Consensus failure mediation** - When deliberation deadlocks or fails
2. **Binding decision arbitration** - Arbiter provides binding resolution
3. **Core Triad override handling** - When Arbiter decisions conflict with Core Triad governance
4. **Human review escalation** - Last resort for unresolvable disputes

## Architecture Design

```
consensus/mediation.py
├── MediationSession (dataclass) - Ongoing mediation session state
├── MediationOutcome (enum) - How mediation concluded
├── MediationRequest (dataclass) - Request for mediation
├── MediationResult (dataclass) - Result of mediation
├── MediationEngine (class) - Main mediation logic
│   ├── start_mediation() - Initiate mediation from failed deliberation
│   ├── submit_position() - Agent submits position during mediation
│   ├── run_mediation_round() - Execute one mediation round
│   ├── finalize_mediation() - Conclude and emit binding decision
│   └── escalate_to_human() - Trigger human review
├── CoreTriadOverride (dataclass) - Core Triad governance override record
└── HumanReviewEscalation (dataclass) - Human review request
```

## Implementation Details

### 1. MediationSession Dataclass

```python
@dataclass
class MediationSession:
    session_id: str
    conflict_id: str
    deliberation_id: str  # Link to failed deliberation
    participants: list[str]
    started_at: datetime
    rounds: int = 0
    max_rounds: int = 3
    state: str = "active"  # active, stalled, resolved, escalated
    positions: dict[str, Position]
    binding_decision: dict | None = None
```

### 2. MediationOutcome Enum

```python
class MediationOutcome(Enum):
    RESOLVED_BINDING = "resolved_binding"      # Arbiter issued binding decision
    RESOLVED_CONSENSUS = "resolved_consensus"  # Parties reached agreement
    ESCALATED_CORE_TRIAD = "escalated_core_triad"  # Core Triad override invoked
    ESCALATED_HUMAN = "escalated_human"        # Human review requested
    FAILED = "failed"                          # Mediation failed
```

### 3. MediationEngine Core Logic

```python
class MediationEngine:
    def __init__(self, deliberation_engine, tribunal, arbiter_agent):
        self.deliberation_engine = deliberation_engine
        self.tribunal = tribunal
        self.arbiter_agent = arbiter_agent
        
    async def start_mediation(
        self,
        deliberation_id: str,
        reason: str
    ) -> MediationSession:
        """Start mediation after deliberation failure."""
        
    async def check_core_triad_override(
        self,
        session: MediationSession
    ) -> bool:
        """Check if Core Triad governance overrides Arbiter decision."""
        
    async def issue_binding_decision(
        self,
        session: MediationSession
    ) -> dict[str, Any]:
        """Issue binding decision when mediation reaches conclusion."""
        
    async def escalate_to_human_review(
        self,
        session: MediationSession
    ) -> HumanReviewEscalation:
        """Escalate to human review as last resort."""
```

### 4. Edge Case Handling

| Edge Case | Handling |
|-----------|----------|
| Arbiter-Core Triad conflict | `check_core_triad_override()` - Core Triad governance takes precedence |
| Unresolvable disputes | After max_rounds, escalate to human review |
| Deliberation deadlock | Detect via `DeliberationOutcome.DEADLOCK`, auto-initiate mediation |
| Agent refuses mediation | Document as dissent, proceed with binding decision |

## Files to Create/Modify

### Create: `src/heretek_swarm/consensus/mediation.py`

New module with:
- `MediationSession` dataclass
- `MediationOutcome` enum  
- `MediationRequest` dataclass
- `MediationResult` dataclass
- `MediationEngine` class
- `CoreTriadOverride` dataclass
- `HumanReviewEscalation` dataclass

### Modify: `src/heretek_swarm/actors/arbiter/core.py`

Add integration with `MediationEngine`:
- Import `MediationEngine`
- Add `_mediation_engine` attribute
- Add `_start_mediation_from_deliberation()` method
- Add `_submit_to_mediation()` method

## Verification Criteria

1. **Mediation initiates on deliberation failure** - When `DeliberationOutcome.DEADLOCK` occurs, Arbiter auto-starts mediation
2. **Binding decisions work** - Arbiter can issue binding decisions that all agents must follow
3. **Core Triad override maintained** - If Core Triad governance conflicts with Arbiter decision, Core Triad wins
4. **Human escalation works** - Unresolvable disputes escalate to human review after max rounds
5. **Integration with existing components** - Uses `DeliberationEngine` and `Tribunal` properly

## Edge Cases Implementation

### 1. Arbiter-Core Triad Conflict

```python
# In MediationEngine.check_core_triad_override()
# Core Triad agents are: Steward, Alpha, Beta, Charlie
CORE_TRIAD_AGENTS = {"steward", "alpha", "beta", "charlie"}

# If any Core Triad agent rejects Arbiter's binding decision,
# the decision is escalated to full Core Triad review
```

### 2. Unresolvable Disputes → Human Review

```python
# After max_rounds (default: 3) of mediation without resolution:
# 1. Mark session as "escalated"
# 2. Create HumanReviewEscalation record
# 3. Log for human operator attention
# 4. Proceed with Arbiter's best-effort binding decision as interim
```

## Dependencies

- `consensus/deliberation.py` - Uses `DeliberationEngine` to get failed deliberation context
- `consensus/tribunal.py` - Uses `Tribunal` to file appeals
- `actors/arbiter/core.py` - Integrates as `ArbiterAgent._mediation_engine`

## Implementation Order

1. Create `mediation.py` with all dataclasses and `MediationEngine` class
2. Update `arbiter/core.py` to integrate `MediationEngine`
3. Add tests for mediation flow
4. Verify integration with deliberation and tribunal

## Out of Scope

- Direct implementation of `arbiter.py` stub (already exists)
- Modifications to `DeliberationEngine` 
- Modifications to `Tribunal`

## Open Questions (from Plan.md)

1. **Escalation threshold**: How many rounds before human escalation triggers? (Default: 3)
2. **Binding decision authority**: Should Arbiter's binding decisions require any Core Triad confirmation for non-critical disputes?
3. **Human review channel**: How should human review requests be delivered? (Notification system, database flag, etc.)

These questions should be resolved during implementation review.