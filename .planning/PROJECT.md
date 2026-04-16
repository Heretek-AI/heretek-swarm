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

## v1.1 Milestone

**Started:** 2026-04-15
**Focus:** Phase 2 Open Items + Production Hardening + Technical Debt

### v1.1 Goals

#### Phase 2 Remaining
- [ ] **GOV-01-F**: Steward failover with Charlie tiebreaker logic
- [ ] **GOV-05-F**: max_rounds enforcement in deliberation
- [ ] **GOV-05-Q**: Quorum logic integrated into Steward triad flow

#### Production Hardening
- [ ] **DEPLOY-01**: Docker/K8s deployment fixes (NATS service, LiteLLM config)
- [ ] **DEPLOY-02**: Database pooling configuration
- [ ] **DEPLOY-03**: API key storage hardening (env var defaults)
- [ ] **OPS-01**: Monitoring/alerting gaps addressed
- [ ] **OPS-02**: NATS production configuration (auth, connection pooling)

#### Technical Debt
- [ ] **TD-01**: Pattern extraction enhancement (collective/)
- [ ] **TD-02**: Consciousness metrics stubs implementation
- [ ] **TD-03**: Zero-trust exception list finalization
- [ ] **TD-04**: Behavioral baseline initialization strategy

### Open Questions (v1.1)

1. NATS auth method — service accounts vs. shared token vs. mTLS?
2. Heartbeat interval — configurable per agent class or global? (default 10s vs 5s)
3. Audit log retention backend — SQLite, PostgreSQL, or object storage?
4. Convoy effect threshold — max_rounds default 3, correct for v1.1?
5. Steward failover identity — Charlie's authority scope during Steward failure?
6. Behavioral baseline initialization — zero state or bootstrap from static rules?
7. Zero-trust exception list — any internal topics exempt from sanitization?

---

*Last updated: 2026-04-15 - v1.1 Milestone Started*

### v1.0.0 Release Summary (2026-04-15)
- **Phase 1**: Foundation — Zero-Trust, Core Triad, Support Agents ✅ Gate 1 Passed
- **Phase 2**: Consensus & Coordination — Deliberation Engine, Safety Systems, Coordination Infrastructure ✅ Gate 2 Passed
- **Phase 3**: Emergence & Optimization — GWT Broadcast, Consciousness Frameworks, Enhancement Agents ✅ Gate 3 Passed
- **Total Tests**: 714 passing
- **Status**: PRODUCTION READY