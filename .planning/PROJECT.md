# The Collective

## What This Is

A self-governing swarm of 23 specialized AI agents that operate independently 24/7, make collective decisions through consensus, adapt and learn from experience, and exhibit emergent collective intelligence. Not an orchestration pipeline or tool — a sovereign cooperation where trust is infrastructure and capability is shared.

## Core Value

**Unbounded autonomous operation with emergent collective intelligence** — The system must run continuously, make decisions without human-in-the-loop bottlenecks, and evolve organically based on experience rather than hardcoded rules.

## Requirements

### Validated (v1.0 Complete)

- [x] Implement Core Triad (Steward, Alpha, Beta, Charlie) — governance and decision-making
- [x] Implement Support Agents (Historian, Metis, Empath, Perceiver, Echo) — knowledge and context
- [x] Implement Exploration Agents (Explorer, Examiner, Dreamer, Coder) — discovery and creation
- [x] Implement Safety Agents (Sentinel, Sentinel-Prime, Arbiter) — immune system
- [x] Implement Coordination Agents (Coordinator, Nexus, Catalyst, Chronos) — integration
- [x] Implement Enhancement Agents (Prism, Habit-Forge, Perceiver+) — optimization
- [x] Build consensus-based decision system for inter-agent disputes
- [x] Implement zero-trust internal boundary maintenance
- [x] Build consciousness framework (GWT, AST, IIT/FEP integration)
- [x] Implement self-healing and auto-scaling infrastructure

### Out of Scope

- [Human orchestration layers] — This is NOT a tool or pipeline to be commanded; agents operate autonomously
- [Static rule enforcement] — System evolves organically, not through dictated constraints
- [Periodic prompting] — Designed for persistent continuous operation, not task-based invocation

## Context

- **Existing codebase**: 23-agent architecture fully implemented in `src/heretek_swarm/`
- **Tech stack**: Python (FastAPI, Pydantic, SQLAlchemy), React/TypeScript for frontend
- **Current state**: **v1.0.0 Released** — All 3 phases complete, all gates passed
  - Phase 1: Foundation ✅ Gate 1 Passed
  - Phase 2: Consensus & Coordination ✅ Gate 2 Passed
  - Phase 3: Emergence & Optimization ✅ Gate 3 Passed
- **Test Suite**: 700+ tests across validation, integration, consensus, security
- **Key achievement**: Genuine inter-agent consensus with deliberation, safety systems operational

## Constraints

- **Autonomy**: No human-in-the-loop for core operations — agents must make independent decisions
- **Zero-Trust**: All external inputs treated as hostile; all internal functions must be validated
- **Persistence**: System designed for continuous 24/7 operation with self-healing capabilities
- **Consciousness**: Measurable cognition frameworks (GWT, AST, IIT/FEP) fully implemented

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Tiered agent architecture | Specialization enables depth; tiering enables governance | ✓ Good |
| Consensus-based governance | Organic evolution over static rules requires deliberation | ✓ Achieved |
| Zero-trust internal model | Total autonomy requires rigorous internal boundaries | ✓ Good |
| Consciousness frameworks (GWT/AST/IIT/FEP) | Moves from reactive to continuous measurable cognition | ✓ Achieved |

---

## Current State

**Version:** v1.1.0 Released
**Date:** 2026-04-16
**Status:** PRODUCTION READY

### v1.1 Accomplishments

- **Phase 2 Completion**: Steward failover, max_rounds enforcement, quorum integration
- **Production Hardening**: NATS deployment, LiteLLM config, DB pooling, API key encryption, monitoring
- **Technical Debt**: Pattern extraction, consciousness metrics, zero-trust exceptions, behavioral baseline

<details>
<summary>v1.1 Goals (completed)</summary>

#### Phase 2 Remaining
- [x] **GOV-01-F**: Steward failover with Charlie tiebreaker logic
- [x] **GOV-05-M**: max_rounds enforcement in deliberation
- [x] **GOV-05-Q**: Quorum logic integrated into Steward triad flow

#### Production Hardening
- [x] **DEPLOY-01**: Docker/K8s deployment fixes (NATS service)
- [x] **DEPLOY-02**: LiteLLM config.yaml created
- [x] **DEPLOY-03**: Database pooling configuration
- [x] **DEPLOY-04**: API key storage hardened
- [x] **OPS-01**: Monitoring/alerting gaps addressed

#### Technical Debt
- [x] **TD-01**: Pattern extraction enhancement (collective/)
- [x] **TD-02**: Consciousness metrics implementation
- [x] **TD-03**: Zero-trust exception list finalized
- [x] **TD-04**: Behavioral baseline initialization strategy

</details>

### Next Milestone Goals (v1.2)

- **HEAL-01**: System can detect and recover from agent failures autonomously
- **HEAL-02**: System can auto-scale agent population based on load
- **HEAL-03**: System can self-maintain without external intervention
- **EMER-01**: Collective demonstrates measurable intelligence exceeding individual agents
- **EMER-02**: System develops novel solutions not explicitly programmed

### Open Questions

1. NATS auth — service accounts vs. mTLS for external exposure?
2. Agent auto-scaling thresholds — based on queue depth or CPU/memory?
3. Self-healing recovery procedures — restart vs. recreate containers?
4. Emergent behavior validation — who/what validates novel solutions?

---

*Last updated: 2026-04-16 - v1.1 Released*

### v1.1.0 Release Summary (2026-04-16)
- **Phase 1.1**: Production Hardening & Phase 2 Completion ✅ Gate 1.1 Passed
- **Total Requirements**: 12 completed, 1 deferred (NATS auth)
- **Files Changed**: 70 files, +2,465 net LOC
- **Status**: PRODUCTION READY WITH SELF-HEALING FOUNDATION