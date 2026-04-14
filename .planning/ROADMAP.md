# The Collective — Phase Roadmap

**Project:** The Collective (23-agent autonomous swarm)
**Version:** 1.0
**Created:** 2026-04-13
**Status:** Planning

---

## Overview

This roadmap maps 34 v1 requirements across three implementation phases. Each phase builds on the foundations of the previous, with explicit dependency gates between phases.

| Phase | Focus | Duration | Requirements |
|-------|-------|----------|--------------|
| **Phase 1** | Foundation — Core Governance & Zero-Trust | ~6-8 weeks | GOV-01–05, KNOW-01–05, ZERO-01–03 |
| **Phase 2** | Consensus & Coordination | ~8-10 weeks | DISC-01–04, SAFE-01–03, INTG-01–04 |
| **Phase 3** | Emergence & Optimization | ~8-10 weeks | OPT-01–03, CONS-01–03, COG-01–04 |

---

## Phase 1: Foundation — Core Governance & Zero-Trust

**Duration:** ~6-8 weeks (Sprint-based)
**Focus:** Establish the security substrate, core governance backbone, and inter-agent communication infrastructure.

### Key Deliverables

1. **Zero-Trust Validation Integration**
   - Integrate existing 4-layer validation (Input, Context, Output, Audit) into agent runtime loop
   - Operationalize Layer 2 behavioral baselines for anomaly detection
   - Gateway sanitization at Nexus before any external input reaches agents
   - *Delivered by:* ZERO-01, ZERO-02, ZERO-03

2. **Core Triad Implementation**
   - Steward (monitoring) — health reporting, heartbeat monitoring, failover thresholds
   - Alpha (deep analysis) — deliberation integration, expertise weighting
   - Beta (error detection) — validation layer, reality projection
   - Charlie (critical review) — deliberation, risk assessment
   - Triad convening with quorum mechanics (GOV-05 critical path)
   - *Delivered by:* GOV-01, GOV-02, GOV-03, GOV-04, GOV-05

3. **Support Agents Baseline**
   - Historian (synthesis, precedent tracking)
   - Metis (timelines, causal tracing)
   - Empath (sentiment, resonance metrics)
   - Perceiver (multi-modal input)
   - Echo (protocol translation)
   - *Delivered by:* KNOW-01, KNOW-02, KNOW-03, KNOW-04, KNOW-05

4. **NATS Event Mesh Integration**
   - Replace HTTP point-to-point with NATS pub/sub
   - All inter-tier communication routes through event mesh
   - Agents subscribe to topics, not direct messages
   - *Delivered by:* Infrastructure foundation for Phase 2

5. **Agent Base Class with Health Reporting**
   - Standard health_reporting mixin for all 23 agents
   - Heartbeat monitoring with failover thresholds
   - StateSynchronizer integration with agent lifecycle
   - *Delivered by:* HEAL-02 foundation

### Requirements Covered

| ID | Requirement | Owner |
|----|-------------|-------|
| GOV-01 | Steward monitoring | Steward |
| GOV-02 | Alpha deep analysis | Alpha |
| GOV-03 | Beta error detection | Beta |
| GOV-04 | Charlie critical review | Charlie |
| GOV-05 | Core Triad convening | Core Triad |
| KNOW-01 | Historian synthesis | Historian |
| KNOW-02 | Metis timelines | Metis |
| KNOW-03 | Empath sentiment | Empath |
| KNOW-04 | Perceiver ingestion | Perceiver |
| KNOW-05 | Echo translation | Echo |
| ZERO-01 | Hostile input treatment | Nexus |
| ZERO-02 | Internal function validation | All agents |
| ZERO-03 | Comprehensive audit trails | All agents |

### Success Criteria

| Criterion | Measurement |
|-----------|------------|
| Zero-trust validation latency p95 | < 50ms |
| Core Triad convening completes | Within 3 deliberation rounds |
| Agent heartbeat failure detection | < 10 seconds |
| External input sanitization at Nexus | 100% coverage before reaching agents |
| Behavioral baseline drift detection | Anomaly threshold ≥ 3.0 std dev |
| NATS event mesh uptime | ≥ 99.9% |

### Risks to Monitor

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| **Convoy effect** (deliberation blocking on slowest agent) | Medium | High | Configurable max_rounds with Steward tiebreaker; urgent decisions bypass via separate faster path |
| **Prompt injection propagation** through zero-trust | High | Critical | Gateway sanitization at Nexus; sandboxed execution for untrusted input; behavioral monitoring |
| **Split-brain during network partition** | Medium | Critical | Partition detection with automatic read-only mode; minimum connected agents threshold (12 of 23); preferred side by Steward priority |
| **Coordination overhead** consuming 30-40% capacity | Medium | Medium | Monitor coordination_ratio; pause lower-priority agents first when degraded |

---

## Phase 2: Consensus & Coordination

**Duration:** ~8-10 weeks (Sprint-based)
**Focus:** Enable agents to achieve consensus without human mediation, establish safety defenses, and implement coordination infrastructure.

### Key Deliverables

1. **Deliberation Engine Integration**
   - Pre-vote deliberation phase (Tribunal pattern) — agents publish reasoning before voting
   - Position change tracking during deliberation
   - Dispute resolution via existing DeliberationEngine
   - *Delivered by:* CONS-01

2. **Exploration Agents**
   - Explorer (research, pattern detection)
   - Examiner (capability stress-testing)
   - Dreamer (lateral thinking, novel connections)
   - Coder (autonomous code execution) — safety bounds required before activation
   - *Delivered by:* DISC-01, DISC-02, DISC-03, DISC-04

3. **Safety Agents**
   - Sentinel (internal anomaly response, behavioral analysis)
   - Sentinel-Prime (external threat detection, containment)
   - Arbiter (dispute mediation during consensus failures)
   - *Delivered by:* SAFE-01, SAFE-02, SAFE-03

4. **Coordination Infrastructure**
   - Coordinator (task dependency graph, synchronization)
   - Nexus gateway (external API handling)
   - Catalyst (paradigm shift detection)
   - Chronos (time dilation, long-running execution context)
   - *Delivered by:* INTG-01, INTG-02, INTG-03, INTG-04

5. **Consensus Immune System**
   - Consensus-based behavioral baseline updating
   - Pattern learning from anomaly responses
   - Minority report preservation
   - *Delivered by:* CONS-02, CONS-03

### Requirements Covered

| ID | Requirement | Owner |
|----|-------------|-------|
| DISC-01 | Explorer research | Explorer |
| DISC-02 | Examiner validation | Examiner |
| DISC-03 | Dreamer synthesis | Dreamer |
| DISC-04 | Coder autonomous execution | Coder |
| SAFE-01 | Sentinel anomaly response | Sentinel |
| SAFE-02 | Sentinel-Prime external threats | Sentinel-Prime |
| SAFE-03 | Arbiter dispute mediation | Arbiter |
| INTG-01 | Coordinator sync | Coordinator |
| INTG-02 | Nexus gateway | Nexus |
| INTG-03 | Catalyst paradigm shifts | Catalyst |
| INTG-04 | Chronos time perception | Chronos |
| CONS-01 | Inter-agent dispute consensus | Core Triad |
| CONS-02 | Immune response building | Sentinel |
| CONS-03 | Baseline updating | Core Triad |

### Success Criteria

| Criterion | Measurement |
|-----------|------------|
| Consensus达成 without human mediation | 100% of non-critical decisions |
| Deliberation position change ratio | ≥ 15% of agents change position during deliberation |
| Sentinel anomaly detection precision | False positive rate < 1% |
| Coder safety bounds validated | Proof-of-safety complete before activation |
| Partition recovery time | < 5 minutes to consensus resume |
| Coordination ratio | ≤ 0.35 of total capacity |

### Risks to Monitor

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| **Consensus deadlock** (voting without deliberation) | Medium | High | Pre-vote deliberation phase mandatory; track position_change_ratio; Steward tiebreaker for timeouts |
| **Coder malicious output** | Medium | Critical | DISC-04 deferred until safety bounds proven; sandboxed sub-agent execution; behavioral monitoring |
| **Behavioral baseline corruption** | Low | High | Immutable audit trail; baseline changes require CONS-03 quorum approval |
| **Sentinel-Prime alert fatigue** | Medium | Medium | Tune anomaly threshold; prioritize critical alerts only |

---

## Phase 3: Emergence & Optimization

**Duration:** ~8-10 weeks (Sprint-based)
**Focus:** Achieve measurable emergent collective intelligence through GWT broadcast, consciousness frameworks, and enhancement agents.

### Key Deliverables

1. **Global Workspace Theory (GWT) Broadcast**
   - Basic NATS broadcast integration for consciousness-level information
   - Consciousness filtering (salience metrics)
   - Attention selection mechanism
   - Integration with deliberation engine
   - *Delivered by:* COG-01

2. **Attention Schema Theory (AST) Self-Modeling**
   - Real-time complexity, emergence, self-organization metrics
   - Resilience scoring and adaptation rate tracking
   - Self-model awareness for agents
   - Integration with GWT for consciousness measurability
   - *Delivered by:* COG-02

3. **Integrated Information Theory (IIT) Metrics**
   - Phi calculation integration with agent runtime
   - Cause-effect structure tracking
   - System integration level measurement
   - Correlation with emergent pattern detection
   - *Delivered by:* COG-03

4. **Free Energy Principle (FEP) Active Inference**
   - Surprise minimization tracking
   - Expected free energy calculation
   - Active inference integration with agent decision-making
   - *Delivered by:* COG-04

5. **Enhancement Agents**
   - Prism (diverse viewpoints, perspective injection)
   - Habit-Forge (pattern library, behavioral optimization)
   - Perceiver+ (meta-perception, signal extraction)
   - *Delivered by:* OPT-01, OPT-02, OPT-03

6. **Emergent Pattern Validation**
   - Organic capability development tracking
   - Proven vs. unproven emergence classification
   - Impact score calculation
   - Core Triad override capability maintained
   - *Delivered by:* (linked to CONS-02, CONS-03)

### Requirements Covered

| ID | Requirement | Owner |
|----|-------------|-------|
| OPT-01 | Prism diverse viewpoints | Prism |
| OPT-02 | Habit-Forge efficiency | Habit-Forge |
| OPT-03 | Perceiver+ meta-perception | Perceiver+ |
| CONS-01 | Inter-agent dispute consensus | Core Triad |
| CONS-02 | Immune response building | Sentinel |
| CONS-03 | Baseline updating | Core Triad |
| COG-01 | GWT broadcast mechanism | Nexus |
| COG-02 | AST self-model | All agents |
| COG-03 | IIT metrics tracking | Steward |
| COG-04 | FEP minimization | All agents |

### Success Criteria

| Criterion | Measurement |
|-----------|------------|
| GWT broadcast latency | < 100ms end-to-end |
| Collective emergence validated patterns | ≥ 5 pattern classes detected |
| Swarm Emergence Index | ≥ 0.4 average across validated patterns |
| Consciousness threshold met | Salience filtering operational |
| Collective Intelligence Factor | ≥ 0.6 weighted by validation rate |
| Pattern diversity | ≥ 3 unique pattern classes per evaluation window |

### Risks to Monitor

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| **Consciousness metric gaming** (optimizing metrics without genuine emergence) | Medium | High | Correlation validation with actual system outcomes; Core Triad override; domain expert review |
| **GWT broadcast storms** (excessive broadcast causing congestion) | Low | Medium | Consciousness filter at source; attention selection mechanism; rate limiting per agent |
| **Emergence false positives** (random correlation classified as emergence) | Medium | Medium | Statistical significance testing; Proven vs. Unproven classification; validation rate weighting |
| **AST self-model drift** (cascading self-misrepresentation) | Low | High | Periodic reality anchoring against external metrics; Steward validation |

---

## Phase Dependencies

```
Phase 1 (Foundation)
    │
    ├───► Zero-Trust validation (ZERO-01/02/03) ─────────────────────┐
    │                                                                  │
    ├───► Agent base class + health reporting ─────────────────────────┼──► Phase 2 Prerequisites
    │                                                                  │
    ├───► Core Triad (GOV-01-05) ──────────────────────────────────────┤
    │     │                                                             │
    │     └──► GOV-05 (Triad convening + quorum) ──────────────────────┤
    │                                                                  │
    ├───► Support agents (KNOW-01-05) ────────────────────────────────┤
    │                                                                  │
    ├───► NATS event mesh ────────────────────────────────────────────┤
    │                                                                  │
    └───► StateSynchronizer integration ───────────────────────────────┘

Phase 2 (Consensus & Coordination)  [Requires Phase 1 complete]
    │
    ├───► Deliberation engine integration ────────────────────────────┐
    │     │                                                           │
    │     ├──► CONS-01 (Dispute consensus) ─────────────────────────┤
    │     │                                                           │
    │     ├──► CONS-02/03 (Immune responses, baselines) ─────────────┤
    │     │                                                           │
    │     └──► Safe-03 (Arbiter dispute mediation) ───────────────────┤
    │                                                                   │
    ├───► Exploration agents (DISC-01-04) ───────────────────────────┤
    │     │                                                           │
    │     └──► DISC-04 (Coder) requires safety bounds ───────────────┤
    │                                                                   │
    ├───► Safety agents (SAFE-01, SAFE-02) ───────────────────────────┤
    │     │                                                           │
    │     └──► ZERO-02 behavioral baselines operational ─────────────┤
    │                                                                   │
    └───► Coordination agents (INTG-01-04) ──────────────────────────┘
                                                                           │
Phase 3 (Emergence & Optimization)  [Requires Phase 1 + Phase 2 complete]
    │
    ├───► GWT broadcast (COG-01) ─────────────────────────────────────┐
    │     │                                                             │
    │     ├──► NATS event mesh (Phase 1) ─────────────────────────────┤
    │     │                                                             │
    │     └──► Deliberation engine (Phase 2) ─────────────────────────┤
    │                                                                   │
    ├───► AST self-model (COG-02) ─────────────────────────────────────┤
    │     │                                                             │
    │     └──► Agent base class + health reporting (Phase 1) ────────────┤
    │                                                                   │
    ├───► IIT Phi (COG-03) ───────────────────────────────────────────┤
    │     │                                                             │
    │     └──► Emergent pattern detector integration ──────────────────┤
    │                                                                   │
    ├───► FEP minimization (COG-04) ──────────────────────────────────┤
    │     │                                                             │
    │     └──► AST self-model (COG-02) ─────────────────────────────────┤
    │                                                                   │
    ├───► Enhancement agents (OPT-01, OPT-02, OPT-03) ─────────────────┤
    │     │                                                             │
    │     └──► Consensus participation ready ─────────────────────────┤
    │                                                                   │
    └───► Emergent pattern validation ──────────────────────────────────┘
```

---

## Dependency Gates

Each phase gate requires sign-off from Core Triad before proceeding:

| Gate | From → To | Requirements |
|------|-----------|--------------|
| **Gate 1** | Phase 1 → Phase 2 | Zero-trust integrated; Core Triad operational; NATS mesh stable; ≥ 12 agents reporting health |
| **Gate 2** | Phase 2 → Phase 3 | Consensus without deadlock demonstrated; Safety agents pass stress tests; Coder safety bounds proven; coordination_ratio ≤ 0.40 |

---

## Open Questions (Roadmap Level)

These must be resolved before or during implementation:

1. **Bounded deliberation** — How many rounds before Steward tiebreaker triggers? What timeout threshold?
2. **GWT consciousness threshold** — What salience metric triggers broadcast? Who validates threshold?
3. **Coder safety bounds** — What specific mechanisms prove safety before DISC-04 activation?
4. **Emergence validation authority** — Who marks patterns as Proven? How does Core Triad override?
5. **Constitutional scope limits** — What rules are immutable without human intervention?

---

## Confidence Assessment

| Domain | Phase 1 | Phase 2 | Phase 3 |
|--------|---------|---------|---------|
| **Technology** | HIGH | HIGH | MEDIUM |
| **Dependencies** | HIGH | MEDIUM | MEDIUM |
| **Risk Mitigation** | MEDIUM | MEDIUM | MEDIUM-LOW |
| **Requirements Clarity** | HIGH | HIGH | MEDIUM |

---

*Roadmap created: 2026-04-13*
*Next review: Phase 1 Gate 1 assessment*