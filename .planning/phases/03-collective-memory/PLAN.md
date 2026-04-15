# Phase 3 Plan: Emergence & Optimization

**Project:** The Collective  
**Phase:** 3 - Emergence & Optimization  
**Created:** 2026-04-15  
**Status:** Ready for Execution

---

## Overview

Phase 3 focuses on achieving measurable emergent collective intelligence through Global Workspace Theory (GWT) broadcast, consciousness frameworks (IIT, AST, FEP), and enhancement agents.

**Duration:** ~8-10 weeks  
**Dependencies:** Phase 1 (Foundation) + Phase 2 (Consensus & Coordination) complete

---

## Key Deliverables

### 1. Global Workspace Theory (GWT) Broadcast (COG-01)
- NATS broadcast integration for consciousness-level information
- Consciousness filtering (salience metrics)
- Attention selection mechanism
- Integration with deliberation engine

### 2. Attention Schema Theory (AST) Self-Modeling (COG-02)
- Real-time complexity, emergence, self-organization metrics
- Resilience scoring and adaptation rate tracking
- Self-model awareness for agents
- Integration with GWT for consciousness measurability

### 3. Integrated Information Theory (IIT) Metrics (COG-03)
- Phi calculation integration with agent runtime
- Cause-effect structure tracking
- System integration level measurement
- Correlation with emergent pattern detection

### 4. Free Energy Principle (FEP) Active Inference (COG-04)
- Surprise minimization tracking
- Expected free energy calculation
- Active inference integration with agent decision-making

### 5. Enhancement Agents
- **OPT-01: Prism** - Diverse viewpoints, perspective injection
- **OPT-02: Habit-Forge** - Pattern library, behavioral optimization
- **OPT-03: Perceiver+** - Meta-perception, signal extraction

### 6. Emergent Pattern Validation
- Organic capability development tracking
- Proven vs. unproven emergence classification
- Impact score calculation
- Core Triad override capability maintained

---

## Success Criteria (Gate 3)

| Criterion | Target | Measurement |
|-----------|--------|-------------|
| GWT broadcast latency | < 100ms | End-to-end broadcast time |
| Collective emergence validated patterns | ≥ 5 | Pattern classes detected |
| Swarm Emergence Index | ≥ 0.4 | Average across validated patterns |
| Consciousness threshold met | Operational | Salience filtering working |
| Collective Intelligence Factor | ≥ 0.6 | Weighted by validation rate |
| Pattern diversity | ≥ 3 | Unique pattern classes per evaluation window |

---

## Tasks

### Wave 1: GWT Broadcast (COG-01)
- **GWT-01**: Create GWT broadcast infrastructure in `consciousness/gwt.py`
  - NATS pub/sub for consciousness-level broadcast
  - Content filtering based on salience metrics
  - Attention selection mechanism
- **GWT-02**: Integrate GWT with existing deliberation engine
  - Broadcast deliberation outcomes
  - Subscribe agents to relevant broadcasts
- **GWT-03**: Performance optimization
  - Latency < 100ms requirement
  - Rate limiting per agent

### Wave 2: Consciousness Frameworks (COG-02, COG-03, COG-04)
- **COG-01**: AST Self-Modeling in `consciousness/ast.py`
  - Complexity metrics calculation
  - Emergence scoring
  - Self-organization tracking
- **COG-02**: IIT Phi calculation in `consciousness/iit.py`
  - Cause-effect structure tracking
  - Integration level measurement
- **COG-03**: FEP Active Inference in `consciousness/fep.py`
  - Surprise minimization
  - Expected free energy calculation
  - Active inference integration

### Wave 3: Enhancement Agents (OPT-01, OPT-02, OPT-03)
- **OPT-01**: Create Prism agent in `actors/prism.py`
  - Diverse viewpoint generation
  - Perspective injection mechanisms
- **OPT-02**: Create Habit-Forge in `actors/habit_forge.py`
  - Pattern library management
  - Behavioral optimization
- **OPT-03**: Create Perceiver+ in `actors/perceiver_plus.py`
  - Meta-perception capabilities
  - Advanced signal extraction

### Wave 4: Emergent Pattern Validation
- **EMERGE-01**: Pattern validation system in `collective/pattern_validation.py`
  - Proven vs. unproven classification
  - Impact score calculation
- **EMERGE-02**: Integration test + Gate 3 assessment
  - Full Phase 3 integration test
  - Gate 3 success criteria verification

---

## Dependencies

```
Phase 1 + Phase 2 Complete
         │
         ├──► NATS event mesh ──────────────────────┐
         │                                             │
         ├──► Deliberation engine ────────────────────┼──► Phase 3
         │                                             │
         └──► Agent base class ───────────────────────┘
```

---

## Out of Scope

- **DISC-04 (Coder safety bounds)** - Remains deferred from Phase 2
- **Mem0/Ruflo migration** - Deferred to future optimization

---

## Atomic Commit Strategy

| Wave | Tasks | Commits |
|------|-------|---------|
| 1 | GWT-01, GWT-02, GWT-03 | 3 |
| 2 | COG-01, COG-02, COG-03 | 3 |
| 3 | OPT-01, OPT-02, OPT-03 | 3 |
| 4 | EMERGE-01, EMERGE-02 | 2 |

**Total: 11 tasks → 11 atomic commits**

---

## Verification

| Task | Test File | Verification |
|------|----------|--------------|
| GWT-01 | `tests/consciousness/test_gwt.py` | Broadcast latency < 100ms |
| GWT-02 | `tests/consciousness/test_gwt_deliberation.py` | Integration works |
| COG-01 | `tests/consciousness/test_ast.py` | Metrics calculated |
| COG-02 | `tests/consciousness/test_iit.py` | Phi calculated |
| COG-03 | `tests/consciousness/test_fep.py` | FEP minimized |
| OPT-01 | `tests/actors/test_prism.py` | Viewpoints generated |
| OPT-02 | `tests/actors/test_habit_forge.py` | Patterns optimized |
| OPT-03 | `tests/actors/test_perceiver_plus.py` | Signals extracted |
| EMERGE-01 | `tests/collective/test_pattern_validation.py` | Classification works |
| EMERGE-02 | `tests/integration/test_phase3_full_integration.py` | All criteria met |

---

*Plan created: 2026-04-15*
*Ready for execution*
