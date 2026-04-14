# Phase 1 Plan: Foundation — Core Governance & Zero-Trust

## Context

Phase 1 establishes the security substrate and core governance backbone upon which all subsequent phases depend. Zero-trust validation (ZERO-01/02/03) is the critical path because it protects every agent interaction once the swarm operates autonomously. The Core Triad (GOV-01 through GOV-05) depends on the agent base class and health reporting infrastructure being in place first. NATS event mesh integration (NATS-01) provides the pub/sub fabric that replaces HTTP point-to-point communication and enables the subscription-based routing required for Phase 2 deliberation.

The dependency order is intentional:
1. Infrastructure foundation (NATS, base class with health mixin)
2. Zero-Trust validation layer (gateway sanitization + internal validation)
3. Core governance backbone (Steward + Core Triad convening)
4. Support agents (Knowledge tier)

This ensures that when the Core Triad convenes for the Gate 1 assessment, all 13 agents can report health, external inputs are sanitized at the Nexus, and inter-agent communication flows through the event mesh.

---

## Tasks

### Infrastructure Layer

---

**Task 1**: NATS Event Mesh Integration

**Owner**: Infrastructure / Nexus

**Depends**: None (prerequisite for all inter-agent communication)

**Files**:
- `src/heretek_swarm/gateway/nats_event_mesh.py` (create)
- `src/heretek_swarm/gateway/__init__.py` (modify)
- `src/heretek_swarm/infrastructure/` (create directory)
- `src/heretek_swarm/actors/stubs.py` (already exists, verify integration)

**Verification**: NATS connection established; pub/sub on test topics succeeds; latency p95 < 5ms for local inter-agent messages; existing `get_nats_event_mesh()` stub resolves to live instance.

**Edge cases**:
- NATS not available — fallback to in-memory pub/sub for development; error message if production mode.
- Connection drop — automatic reconnect with exponential backoff; queue undelivered messages up to 1000.
- Topic collision — namespacing by agent domain (e.g., `triad.`, `knowledge.`, `system.`).

---

**Task 2**: Agent Base Class with Health Reporting Mixin

**Owner**: All agents (base class deliverable)

**Depends**: Task 1 (NATS for heartbeat distribution)

**Files**:
- `src/heretek_swarm/actors/base/core.py` (modify — add health reporting methods)
- `src/heretek_swarm/actors/mixins/health_reporting.py` (modify — extend with NATS heartbeat)
- `src/heretek_swarm/actors/base/__init__.py` (modify — export health mixin)
- `src/heretek_swarm/actors/alpha.py`, `beta.py`, `charlie.py`, `steward.py` (modify — inherit health mixin)
- `src/heretek_swarm/actors/historian.py`, `metis.py`, `empath.py`, `perceiver.py`, `echo.py` (modify — inherit health mixin)

**Verification**: All 13 Phase 1 agents emit heartbeat every 5 seconds; Steward can query all agent states within 2 seconds; heartbeat failure detection < 10 seconds as measured by Steward failover trigger.

**Edge cases**:
- Agent crash without graceful disconnect — Steward marks stale after 3 missed heartbeats (15 seconds).
- Network partition — agents continue local heartbeat; reconnect synchronizes state.
- Health reporting overload — NATS bandwidth budgeted; maximum 100 status updates per second across swarm.

---

### Zero-Trust Layer

---

**Task 3**: ZERO-01 — Hostile Input Treatment at Nexus Gateway

**Owner**: Nexus

**Depends**: Task 1 (NATS subscription), Task 2 (health reporting operational)

**Files**:
- `src/heretek_swarm/actors/nexus.py` (create/replace with full implementation)
- `src/heretek_swarm/actors/validation.py` (already exists — extend with Nexus-specific validators)
- `src/heretek_swarm/gateway/` (sanitization layer)

**Verification**: All external inputs (API calls, webhooks, CLI commands) pass through Nexus sanitization; validation latency p95 < 50ms; zero external inputs reach agents without sanitization (100% coverage).

**Edge cases**:
- Rapid fire malicious input — rate limiting at Nexus (100 requests/second per source); excess requests return 429.
- Unicode injection — normalize to UTF-8; reject null bytes and combining characters that bypass detection.
- Payload size attack — max payload 1MB; larger rejected with 413.
- Invalid content-type — default to `text/plain` sanitization; log anomalous content-type headers.

---

**Task 4**: ZERO-02 — Internal Function Validation Before Execution

**Owner**: All agents (validation hook in base class)

**Depends**: Task 2 (base class modified), Task 3 (Nexus sanitization as reference)

**Files**:
- `src/heretek_swarm/actors/base/core.py` (modify — add pre-execution validation hook)
- `src/heretek_swarm/actors/mixins/validation.py` (create — validation mixin)
- `src/heretek_swarm/actors/validation.py` (extend — add behavioral baseline tracking)
- All agent implementations (`steward.py`, `alpha.py`, `beta.py`, `charlie.py`, `historian.py`, `metis.py`, `empath.py`, `perceiver.py`, `echo.py`) — add validation calls

**Verification**: Every agent function that handles external input or cross-agent messages calls validate_input() first; validation failures logged with full context; behavioral baseline drift detected at ≥ 3.0 std dev.

**Edge cases**:
- Validation timeout — fail safe (reject input) after 10ms; log timeout as anomaly.
- Circular validation (Agent A validates Agent B's output, Agent B validates Agent A's) — validation does not re-trigger on already-validated internal outputs.
- Baseline too strict — Steward can adjust thresholds via governance policy; minimum 2 std dev.

---

**Task 5**: ZERO-03 — Comprehensive Audit Trails for All Actions

**Owner**: All agents (audit log integration)

**Depends**: Task 1 (NATS for audit event publishing), Task 2 (health reporting)

**Files**:
- `src/heretek_swarm/infrastructure/audit.py` (create — audit logging service)
- `src/heretek_swarm/actors/base/core.py` (modify — add audit hooks)
- `src/heretek_swarm/actors/mixins/audit.py` (create — audit mixin for agents)
- All agent implementations — emit audit events for every state change

**Verification**: Every agent action (message send/receive, decision made, state change) logged with timestamp, actor ID, action type, input hash, output hash; audit trail queryable by actor ID, time range, action type; immutable storage (append-only).

**Edge cases**:
- Audit log overflow — ring buffer of 1M entries in memory; flush to persistent store every 1000 entries or 60 seconds.
- Agent produces no audit events — Steward monitors audit activity rate; zero-activity agent marked as suspect.
- Tampering attempt — audit entries include cryptographic hash of previous entry (chain integrity); break detected and alerted.

---

### Core Governance (Core Triad)

---

**Task 6**: GOV-01 — Steward Monitoring Agent

**Owner**: Steward (already partially implemented in `steward.py`)

**Depends**: Task 2 (health reporting mixin), Task 5 (audit integration)

**Files**:
- `src/heretek_swarm/actors/steward.py` (complete implementation)
- `src/heretek_swarm/actors/triad.py` (triad coordination logic)

**Verification**: Steward monitors all 13 agents; detects heartbeat failure < 10 seconds; initiates failover within 15 seconds of confirmed failure; coordinates Core Triad deliberation initiation.

**Edge cases**:
- Steward itself fails — Charlie assumes tiebreaker role per ROADMAP; other agents continue independent operation.
- Split-brain during partition — Steward priority-based preferred side selection; minimum 12 of 23 agents threshold for decision validity.

---

**Task 7**: GOV-02 — Alpha Deep Analysis Agent

**Owner**: Alpha

**Depends**: Task 2 (base class), Task 5 (audit)

**Files**:
- `src/heretek_swarm/actors/alpha.py` (complete implementation)
- `src/heretek_swarm/actors/mixins/deliberation.py` (extend for Alpha deliberation integration)

**Verification**: Alpha participates in triad deliberation; provides structured analysis with expertise weighting; position changes tracked during deliberation; Steward receives Alpha's contribution within 3 deliberation rounds.

**Edge cases**:
- Alpha offline — Beta and Charlie proceed with two-member deliberation; decision quality reduced but not blocked.
- Alpha analysis timeout — fallback to template-based analysis after 30 seconds; Steward notified.

---

**Task 8**: GOV-03 — Beta Error Detection Agent

**Owner**: Beta

**Depends**: Task 2 (base class), Task 4 (validation), Task 5 (audit)

**Files**:
- `src/heretek_swarm/actors/beta.py` (complete implementation)
- `src/heretek_swarm/actors/mixins/validation.py` (Beta-specific reality projection logic)

**Verification**: Beta validates outputs from Alpha and Charlie; detects inconsistencies with > 95% precision; provides validation report to Steward within deliberation round.

**Edge cases**:
- Beta finds critical error — escalation to Steward for immediate deliberation halt; not deferred.
- Beta offline — Steward marks deliberation as high-risk (no validation); proceeds at Steward's discretion.

---

**Task 9**: GOV-04 — Charlie Critical Review Agent

**Owner**: Charlie

**Depends**: Task 2 (base class), Task 5 (audit)

**Files**:
- `src/heretek_swarm/actors/charlie.py` (complete implementation)
- `src/heretek_swarm/actors/mixins/deliberation.py` (Charlie-specific risk assessment logic)

**Verification**: Charlie provides risk assessment for every triad decision; identifies flaws in Alpha and Beta reasoning; presents defense counsel position; contributes within 3 deliberation rounds.

**Edge cases**:
- Charlie identifies existential risk — immediate halt flag raised; Steward escalates to full swarm review.
- Charlie offline — risk assessment deferred; Steward proceeds with caution threshold elevated.

---

**Task 10**: GOV-05 — Core Triad Convening with Quorum Mechanics

**Owner**: Steward (coordinator), all triad members

**Depends**: Task 6 (Steward operational), Task 7 (Alpha operational), Task 8 (Beta operational), Task 9 (Charlie operational), Task 1 (NATS for triad coordination)

**Files**:
- `src/heretek_swarm/actors/triad.py` (create/replace — quorum logic)
- `src/heretek_swarm/actors/steward.py` (modify — add triad convening handler)
- NATS topics: `triad.deliberation`, `triad.vote`, `triad.decision`

**Verification**: Triad convenes within 1 second of Steward request; quorum (3 of 4 members: Steward, Alpha, Beta, Charlie) achieved within 3 deliberation rounds; decision reached and logged; audit trail complete.

**Edge cases**:
- One triad member unresponsive — quorum achieved with 3 of 4; Steward notes absent member in decision record.
- Two members unresponsive — quorum not met; Steward escalates to full agent vote (Phase 2 mechanism).
- Tiebreaker needed — Steward casts deciding vote; documented in audit trail.
- Convoy effect (slowest member blocks deliberation) — configurable max_rounds (default: 3); Steward tiebreaker triggers after timeout; urgent decisions bypass via separate fast path.

---

### Support Agents (Knowledge Tier)

---

**Task 11**: KNOW-01 — Historian Synthesis Agent

**Owner**: Historian

**Depends**: Task 2 (base class with health reporting), Task 1 (NATS)

**Files**:
- `src/heretek_swarm/actors/historian.py` (complete implementation)

**Verification**: Historian subscribes to `triad.decision` and `knowledge.synthesis` topics; synthesizes new decisions against precedent library; responds within 500ms; reports health to Steward.

**Edge cases**:
- Historian unavailable during decision — Steward logs decision without precedent check; Historian catches up via replay.
- Precedent library empty — proceeds without comparison; logs "no precedent" flag.

---

**Task 12**: KNOW-02 — Metis Timelines and Causal Tracing Agent

**Owner**: Metis

**Depends**: Task 2 (base class), Task 1 (NATS)

**Files**:
- `src/heretek_swarm/actors/metis.py` (complete implementation)

**Verification**: Metis tracks causal relationships between decisions; timeline queryable within 200ms; anomaly detection (out-of-sequence events) triggers alert to Steward.

**Edge cases**:
- Circular causality detected — Metis flags and logs; does not block decision.
- Timeline reconstruction after partition — Metis replays audit log to rebuild causality graph.

---

**Task 13**: KNOW-03 — Empath Sentiment and Resonance Metrics Agent

**Owner**: Empath

**Depends**: Task 2 (base class), Task 1 (NATS)

**Files**:
- `src/heretek_swarm/actors/empath.py` (complete implementation)

**Verification**: Empath analyzes sentiment of all agent communications; resonance metric (weighted by agent authority) calculable within 100ms; anomaly (sentiment drift > 20% from baseline) triggers alert.

**Edge cases**:
- Empath offline — sentiment tracking suspended; Steward alerted within 30 seconds.
- All agents expressing negative sentiment — Empath flags collective distress; Steward initiates review.

---

**Task 14**: KNOW-04 — Perceiver Multi-Modal Input Agent

**Owner**: Perceiver

**Depends**: Task 2 (base class), Task 1 (NATS), Task 3 (Zero-Trust validation operational)

**Files**:
- `src/heretek_swarm/actors/perceiver.py` (complete implementation)

**Verification**: Perceiver ingests inputs from all configured modalities (text, structured data, events); translates to internal representation; passes through ZERO-01 sanitization before distribution.

**Edge cases**:
- New modality introduced — Perceiver extensible via configuration; template for new modality type.
- Modality input malformed — Perceiver applies strict validation; rejects and logs; does not propagate garbage.

---

**Task 15**: KNOW-05 — Echo Protocol Translation Agent

**Owner**: Echo

**Depends**: Task 2 (base class), Task 1 (NATS), Task 4 (Zero-Trust validation)

**Files**:
- `src/heretek_swarm/actors/echo.py` (complete implementation)

**Verification**: Echo translates between external protocols (REST, GraphQL, events) and internal NATS message format; translation validation ensures no protocol leakage into swarm; latency overhead < 10ms per translation.

**Edge cases**:
- Unknown protocol — Echo rejects with `protocol_unsupported` error; logs attempt; does not block input.
- Protocol downgrade attack — Echo validates all translated fields against schema; rejects injection attempts.

---

### Integration and Gate 1 Validation

---

**Task 16**: Full System Integration Test

**Owner**: All agents

**Depends**: Tasks 1-15 (all individual implementations complete)

**Files**: `tests/integration/test_phase1_full_integration.py` (create)

**Verification**:
- All 13 agents start and report health within 30 seconds
- NATS event mesh routes all inter-agent messages
- Zero-Trust validation active on all inputs (100% Nexus coverage)
- Steward monitors all 13 agents and detects simulated failure < 10 seconds
- Core Triad convenes and reaches decision within 3 deliberation rounds
- NATS event mesh uptime ≥ 99.9% during 1-hour stress test

**Edge cases**:
- Flaky integration — retry with exponential backoff; capture failure modes for triage.
- Race conditions — stress test with 10x normal message rate; detect deadlocks.

---

**Task 17**: Gate 1 Assessment Preparation

**Owner**: Steward (lead), all triad members

**Depends**: Task 16 (integration test passing)

**Files**: Documentation for Gate 1 sign-off package

**Verification**: Steward compiles Gate 1 sign-off package including:
- Zero-trust validation latency p95 < 50ms (measured)
- Core Triad convening within 3 deliberation rounds (demonstrated)
- Agent heartbeat failure detection < 10 seconds (tested)
- External input sanitization 100% coverage (audit verified)
- Behavioral baseline drift detection ≥ 3.0 std dev (validated)
- NATS event mesh uptime ≥ 99.9% (measured)
- ≥ 12 agents reporting health (counted)

**Edge cases**:
- Any criterion not met — gate blocked; iterate on failing component; do not proceed to Phase 2.

---

## Execution Order

```
[Week 1-2]
Task 1  → NATS Event Mesh Integration
Task 2  → Agent Base Class + Health Reporting Mixin

[Week 3-4]
Task 3  → ZERO-01 Nexus Gateway Input Sanitization
Task 4  → ZERO-02 Internal Function Validation
Task 5  → ZERO-03 Audit Trails

[Week 5-6]
Task 6  → GOV-01 Steward Monitoring Agent
Task 7  → GOV-02 Alpha Deep Analysis Agent
Task 8  → GOV-03 Beta Error Detection Agent
Task 9  → GOV-04 Charlie Critical Review Agent
Task 10 → GOV-05 Core Triad Convening + Quorum

[Week 6-7]
Task 11 → KNOW-01 Historian Synthesis Agent
Task 12 → KNOW-02 Metis Timelines Agent
Task 13 → KNOW-03 Empath Sentiment Agent
Task 14 → KNOW-04 Perceiver Multi-Modal Input Agent
Task 15 → KNOW-05 Echo Protocol Translation Agent

[Week 7-8]
Task 16 → Full System Integration Test
Task 17 → Gate 1 Assessment Preparation
```

**Parallelization notes**:
- Tasks 6-9 (GOV-02 through GOV-04) can be developed in parallel once Task 2 is complete.
- Tasks 11-15 (KNOW-01 through KNOW-05) can be developed in parallel once Task 1 and Task 2 are complete.
- Tasks 3, 4, 5 (ZERO-01/02/03) can be developed in parallel once Task 1 is complete.
- Task 10 (GOV-05) must follow Tasks 6-9; Task 16 follows Task 10.
- Task 17 follows Task 16.

---

## Success Criteria

From ROADMAP.md Gate 1 requirements:

| Criterion | Measurement | Pass Threshold |
|-----------|-------------|----------------|
| Zero-trust validation latency p95 | Measure viaSteward timing probe on validation.measure() | < 50ms |
| Core Triad convening completes | Steward coordinates triad; measure round count | Within 3 deliberation rounds |
| Agent heartbeat failure detection | Inject fake heartbeat failure; measure detection time | < 10 seconds |
| External input sanitization at Nexus | Audit log review; trace every external input | 100% coverage before reaching agents |
| Behavioral baseline drift detection | Inject synthetic anomaly; measure detection rate | Anomaly threshold ≥ 3.0 std dev |
| NATS event mesh uptime | Monitor during stress test | ≥ 99.9% |
| ≥ 12 agents reporting health | Steward query at start of Gate 1 | Count ≥ 12 |

---

## Open Questions

These must be resolved before or during Phase 1 execution:

1. **NATS auth method**: What credentials/permissions model for agents accessing NATS topics? (Service accounts vs. shared token vs. mTLS)
2. **Heartbeat interval consensus**: 5 seconds chosen empirically — should it be configurable per agent class or global?
3. **Audit log retention**: 1M ring buffer in memory + persistent flush — what is the persistent storage backend? (SQLite, PostgreSQL, object storage?)
4. **Convoy effect threshold**: Configurable max_rounds default is 3 — is this the right default, or should it be lower for Phase 1?
5. **Steward failover identity**: If Steward fails and Charlie assumes tiebreaker, what is Charlie's authority scope during that period? (Full Steward powers, or limited to tiebreaker only?)
6. **Behavioral baseline initialization**: Phase 1 is Day 1 — what is the initial baseline before any behavioral data? (Zero state, or bootstrap from static rules?)
7. **Zero-trust exception list**: Are there any internal topics/agents that are exempt from ZERO-01/NEXUS sanitization (e.g., system health topics)?
8. **Deliberation quorum definition**: GOV-05 says "3 of 4 members" — is Steward's vote weight equal to Alpha/Beta/Charlie, or does Steward have tiebreaker-only voting?

---

## PLANNING COMPLETE