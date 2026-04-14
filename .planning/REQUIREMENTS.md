# Requirements: The Collective

**Defined:** 2026-04-13
**Core Value:** Unbounded autonomous operation with emergent collective intelligence

## v1 Requirements

Requirements for initial release. Each maps to roadmap phases.

### Core Governance (Core Triad)

- [~] **GOV-01**: Steward agent can monitor system homeostasis and route tasks — coordinates triad ✅, monitors agents passively ✅, heartbeat detection ❌, failover ❌
- [x] **GOV-02**: Alpha agent can perform comprehensive deep analysis and logical deconstruction — 27 tests PASS
- [x] **GOV-03**: Beta agent can detect errors, project blast radius, and validate reality — 27 tests PASS
- [x] **GOV-04**: Charlie agent can provide critical review, risk assessment, and defense counsel — 27 tests PASS
- [~] **GOV-05**: Core Triad can convene for deliberation on anomalies — 36 tests PASS. Gaps: unanimous vote bug, no max_rounds, no integrated quorum.
- [x] **KNOW-01**: Historian agent can synthesize information and log precedents — 11 tests PASS
- [x] **KNOW-02**: Metis agent can generate long-term timelines and impact analysis — 10 tests PASS
- [x] **KNOW-03**: Empath agent can analyze sentiment and measure human-AI resonance — 13 tests PASS
- [x] **KNOW-04**: Perceiver agent can ingest multi-modal data — 12 tests PASS
- [x] **KNOW-05**: Echo agent can manage translation and multi-channel communication — 9 tests PASS

### Discovery & Creation (Exploration Agents)

- [ ] **DISC-01**: Explorer agent can perform proactive research and information gathering
- [ ] **DISC-02**: Examiner agent can stress-test and validate capabilities
- [ ] **DISC-03**: Dreamer agent can perform lateral thinking and novel solution synthesis
- [ ] **DISC-04**: Coder agent can autonomously write, debug, and expand code

### Protection (Safety Agents)

- [ ] **SAFE-01**: Sentinel agent can respond to anomalies with injunctions or quarantine
- [ ] **SAFE-02**: Sentinel-Prime agent can handle external threat response and containment
- [ ] **SAFE-03**: Arbiter agent can mediate disputes during consensus failures

### Integration (Coordination Agents)

- [ ] **INTG-01**: Coordinator agent can synchronize task dependencies across agents
- [ ] **INTG-02**: Nexus agent can manage gateway to human systems and external APIs
- [ ] **INTG-03**: Catalyst agent can handle systemic shifts and paradigm transitions
- [ ] **INTG-04**: Chronos agent can manage time perception and long-running execution

### Optimization (Enhancement Agents)

- [ ] **OPT-01**: Prism agent can force diverse, non-standard viewpoints into consensus
- [ ] **OPT-02**: Habit-Forge agent can build operational efficiency patterns and record precedents
- [ ] **OPT-03**: Perceiver+ agent can extract meta-perception and signal-from-noise

### Consensus & Governance

- [ ] **CONS-01**: System can achieve consensus on inter-agent disputes without human mediation
- [ ] **CONS-02**: System can build immune responses from observed anomalies
- [ ] **CONS-03**: System can update baselines from emergent efficient actions

### Zero-Trust Architecture

- [~] **ZERO-01**: All external inputs treated as hostile by default — 75 tests PASS, 2 critical bugs fixed (config discard + sender_id bypass). Gap: rejection returns unsanitized content.
- [~] **ZERO-02**: All internal functions validated before execution — 28 tests PASS. Gap: ValidationMixin not wired into any production agent.
- [x] **ZERO-03**: Comprehensive audit trails maintained for all actions — 50 tests PASS, zero gaps.

### Consciousness Framework

- [ ] **COG-01**: Global Workspace Theory (GWT) broadcast mechanism implemented
- [ ] **COG-02**: Attention Schema Theory (AST) self-model maintained
- [ ] **COG-03**: Integrated Information Theory metrics tracked
- [ ] **COG-04**: Free Energy Principle (FEP) minimization operational

## v2 Requirements

### Self-Healing Infrastructure

- **HEAL-01**: System can detect and recover from agent failures autonomously
- **HEAL-02**: System can auto-scale agent population based on load
- **HEAL-03**: System can self-maintain without external intervention

### Emergent Intelligence

- **EMER-01**: Collective demonstrates measurable intelligence exceeding individual agents
- **EMER-02**: System develops novel solutions not explicitly programmed

## Out of Scope

| Feature | Reason |
|---------|--------|
| Human command interface | Agents operate autonomously, not as tools |
| Centralized control | Sovereign cooperation, not orchestration pipeline |
| Static rule enforcement | Organic evolution over dictated constraints |
| Periodic task invocation | Designed for persistent 24/7 continuous operation |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| GOV-01 | Phase 1 | Pending |
| GOV-02 | Phase 1 | Pending |
| GOV-03 | Phase 1 | Pending |
| GOV-04 | Phase 1 | Pending |
| GOV-05 | Phase 1 | Pending |
| KNOW-01 | Phase 1 | Pending |
| KNOW-02 | Phase 1 | Pending |
| KNOW-03 | Phase 1 | Pending |
| KNOW-04 | Phase 1 | Pending |
| KNOW-05 | Phase 1 | Pending |
| DISC-01 | Phase 2 | Pending |
| DISC-02 | Phase 2 | Pending |
| DISC-03 | Phase 2 | Pending |
| DISC-04 | Phase 2 | Pending |
| SAFE-01 | Phase 2 | Pending |
| SAFE-02 | Phase 2 | Pending |
| SAFE-03 | Phase 2 | Pending |
| INTG-01 | Phase 2 | Pending |
| INTG-02 | Phase 2 | Pending |
| INTG-03 | Phase 2 | Pending |
| INTG-04 | Phase 2 | Pending |
| OPT-01 | Phase 3 | Pending |
| OPT-02 | Phase 3 | Pending |
| OPT-03 | Phase 3 | Pending |
| CONS-01 | Phase 3 | Pending |
| CONS-02 | Phase 3 | Pending |
| CONS-03 | Phase 3 | Pending |
| ZERO-01 | Phase 1 | Pending |
| ZERO-02 | Phase 1 | Pending |
| ZERO-03 | Phase 1 | Pending |
| COG-01 | Phase 3 | Pending |
| COG-02 | Phase 3 | Pending |
| COG-03 | Phase 3 | Pending |
| COG-04 | Phase 3 | Pending |

**Coverage:**
- v1 requirements: 34 total
- Mapped to phases: 34
- Unmapped: 0 ✓

---
*Requirements defined: 2026-04-13*
*Last updated: 2026-04-14 after Phase 1 validation wave*

### Validation Status (Phase 1 — 2026-04-14)
- **ZERO-01/02/03**: Validated (75+28+50 = 153 tests)
- **GOV-01 through GOV-05**: Validated (27+36 = 63 tests)
- **KNOW-01 through KNOW-05**: Validated (55 tests)
- **Integration**: 26 tests (full Phase 1 system)
- **NATS**: 11 tests (fallback pub/sub + wildcards)
- **Total Phase 1 validation**: 308 new tests, 693 total passing
- **Gate 1 verdict**: BLOCKED (3 hard blockers)