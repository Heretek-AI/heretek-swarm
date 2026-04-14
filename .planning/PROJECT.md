# The Collective

## What This Is

A self-governing swarm of 23 specialized AI agents that operate independently 24/7, make collective decisions through consensus, adapt and learn from experience, and exhibit emergent collective intelligence. Not an orchestration pipeline or tool — a sovereign cooperation where trust is infrastructure and capability is shared.

## Core Value

**Unbounded autonomous operation with emergent collective intelligence** — The system must run continuously, make decisions without human-in-the-loop bottlenecks, and evolve organically based on experience rather than hardcoded rules.

## Requirements

### Validated

(None yet — ship to validate)

### Active

- [ ] Implement Core Triad (Steward, Alpha, Beta, Charlie) — governance and decision-making
- [ ] Implement Support Agents (Historian, Metis, Empath, Perceiver, Echo) — knowledge and context
- [ ] Implement Exploration Agents (Explorer, Examiner, Dreamer, Coder) — discovery and creation
- [ ] Implement Safety Agents (Sentinel, Sentinel-Prime, Arbiter) — immune system
- [ ] Implement Coordination Agents (Coordinator, Nexus, Catalyst, Chronos) — integration
- [ ] Implement Enhancement Agents (Prism, Habit-Forge, Perceiver+) — optimization
- [ ] Build consensus-based decision system for inter-agent disputes
- [ ] Implement zero-trust internal boundary maintenance
- [ ] Build consciousness framework (GWT, AST, IIT/FEP integration)
- [ ] Implement self-healing and auto-scaling infrastructure

### Out of Scope

- [Human orchestration layers] — This is NOT a tool or pipeline to be commanded; agents operate autonomously
- [Static rule enforcement] — System evolves organically, not through dictated constraints
- [Periodic prompting] — Designed for persistent continuous operation, not task-based invocation

## Context

- **Existing codebase**: 23-agent architecture already mapped in `.planning/codebase/`
- **Tech stack**: Python (FastAPI, Pydantic, SQLAlchemy), React/TypeScript for frontend
- **Current state**: Phase 1 validation complete — 693 tests passing, 4 bugs fixed (2 critical), Gate 1 BLOCKED on 3 hard blockers (heartbeat monitoring, NATS stress test, agent count). All 23 agents fully implemented (not stubs). Zero-trust, audit trails, and Core Triad structurally verified.
- **Key challenge**: Building genuine inter-agent consensus vs. simple task routing

## Constraints

- **Autonomy**: No human-in-the-loop for core operations — agents must make independent decisions
- **Zero-Trust**: All external inputs treated as hostile; all internal functions must be validated
- **Persistence**: System designed for continuous 24/7 operation with self-healing capabilities
- **Consciousness**: Must implement measurable cognition frameworks (GWT, AST, IIT/FEP)

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Tiered agent architecture | Specialization enables depth; tiering enables governance | ✓ Good |
| Consensus-based governance | Organic evolution over static rules requires deliberation | — Pending |
| Zero-trust internal model | Total autonomy requires rigorous internal boundaries | ✓ Good |
| Consciousness frameworks (GWT/AST/IIT/FEP) | Moves from reactive to continuous measurable cognition | — Pending |

---
*Last updated: 2026-04-14 after Phase 1 validation wave*

### Phase 1 Validation Summary (2026-04-14)
- **308 new tests** written across 8 validation/integration test files
- **693 total tests passing**, 3 skipped (documenting gaps), 0 failed
- **4 bugs fixed**: NATS fallback (2), Nexus config (1), Nexus sender_id bypass (1)
- **Gate 1 verdict**: BLOCKED — 3 hard blockers remain
  1. No heartbeat failure detection (< 10s criterion)
  2. No NATS 1-hour stress test (99.9% uptime criterion)
  3. Only 10 agents with HealthReportingMixin (need ≥ 12)