# Phase 2 Plan: Consensus & Coordination

## Context

Phase 1 established the security substrate, core governance backbone, and inter-agent communication infrastructure. Gate 1 has been passed with all 7 criteria met.

Phase 2 focuses on enabling agents to achieve consensus without human mediation, establishing safety defenses, and implementing coordination infrastructure. This phase builds directly on Phase 1 foundations:
- Zero-trust validation (ZERO-01/02/03) from Phase 1 protects all agent interactions
- Core Triad (GOV-01 through GOV-05) provides governance backbone
- NATS event mesh provides pub/sub fabric
- HealthReportingMixin on 12 agents enables monitoring

The dependency order is intentional:
1. Deliberation engine integration (enables consensus)
2. Safety agents (protect consensus process)
3. Exploration agents (expand collective capabilities)
4. Coordination infrastructure (scale operations)

## Tasks

### Deliberation Engine Integration

---

**Task 1**: CONS-01 — Inter-Agent Dispute Consensus

**Owner**: Core Triad

**Depends**: Phase 1 (Core Triad operational)

**Files**:
- `src/heretek_swarm/consensus/deliberation.py` (extend)
- `src/heretek_swarm/actors/triad.py` (integrate deliberation)
- `src/heretek_swarm/actors/steward.py` (coordinate deliberation)

**Verification**: Disputes between agents resolved via deliberation without human mediation; position change tracking operational; minority report preserved.

**Edge cases**:
- Deliberation deadlock — configurable max_rounds with Steward tiebreaker
- Agent refuses to participate — documented as dissent, decision proceeds
- High-contention disputes — escalate to full swarm review

---

**Task 2**: CONS-02 — Immune Response Building

**Owner**: Sentinel

**Depends**: Task 1 (deliberation engine), Phase 1 (ValidationMixin)

**Files**:
- `src/heretek_swarm/actors/sentinel.py` (enhance)
- `src/heretek_swarm/consensus/immune.py` (create)
- `src/heretek_swarm/security/behavioral_baseline.py` (extend)

**Verification**: Sentinel learns from anomaly responses; patterns added to baseline; false positive rate < 1%.

**Edge cases**:
- Baseline corruption attempt — immutable audit trail; baseline changes require quorum
- Novel attack patterns — preserved for human review; not auto-added to baseline

---

**Task 3**: CONS-03 — Behavioral Baseline Updating

**Owner**: Core Triad

**Depends**: Task 1, Task 2

**Files**:
- `src/heretek_swarm/security/behavioral_baseline.py` (enhance)
- `src/heretek_swarm/consensus/tribunal.py` (create for baseline changes)
- `src/heretek_swarm/actors/steward.py` (coordinate baseline votes)

**Verification**: Baseline changes require CONS-03 quorum approval; immutable audit trail; rollback capability.

**Edge cases**:
- Baseline drift during normal operation — gradual update with multi-agent approval
- Emergency baseline reset — Steward can initiate with Charlie approval

---

### Safety Agents

---

**Task 4**: SAFE-01 — Sentinel Anomaly Response

**Owner**: Sentinel

**Depends**: Phase 1 (ValidationMixin, health reporting)

**Files**:
- `src/heretek_swarm/actors/sentinel.py` (implement fully)
- `src/heretek_swarm/security/anomaly_detection.py` (enhance)

**Verification**: Sentinel detects anomalies in agent behavior; precision > 99%; automated response within 30 seconds.

**Edge cases**:
- False positive cascade — rate limiting on automated responses; human notification
- Sentinel itself compromised — Sentinel-Prime provides backup monitoring

---

**Task 5**: SAFE-02 — Sentinel-Prime External Threat Detection

**Owner**: Sentinel-Prime

**Depends**: Phase 1 (Nexus operational)

**Files**:
- `src/heretek_swarm/actors/sentinel_prime.py` (implement fully)
- `src/heretek_swarm/security/threat_detection.py` (create)
- `src/heretek_swarm/gateway/zero_trust.py` (enhance)

**Verification**: Sentinel-Prime detects external threats (prompt injection, DoS, exfiltration); containment actions operational; false positive rate < 1%.

**Edge cases**:
- Alert fatigue — priority filtering; critical alerts only by default
- Threat escalation — automatic notification to Core Triad

---

**Task 6**: SAFE-03 — Arbiter Dispute Mediation

**Owner**: Arbiter

**Depends**: Task 1 (deliberation engine)

**Files**:
- `src/heretek_swarm/actors/arbiter.py` (create)
- `src/heretek_swarm/consensus/mediation.py` (create)

**Verification**: Arbiter mediates consensus failures; provides binding decisions; Core Triad override maintained.

**Edge cases**:
- Arbiter-Core Triad conflict — Core Triad governance takes precedence
- Unresolvable disputes — escalate to human review (last resort)

---

### Exploration Agents

---

**Task 7**: DISC-01 — Explorer Research Agent

**Owner**: Explorer

**Depends**: Phase 1 (Agent base class, health reporting)

**Files**:
- `src/heretek_swarm/actors/explorer.py` (create)
- `src/heretek_swarm/knowledge/research.py` (create)

**Verification**: Explorer autonomously researches topics; patterns detected and reported; consensus integration operational.

**Edge cases**:
- Explorer provides contradictory findings — Beta validates; deliberation resolves
- Research scope creep — configurable depth limits; Steward oversight

---

**Task 8**: DISC-02 — Examiner Capability Stress-Testing

**Owner**: Examiner

**Depends**: Task 7

**Files**:
- `src/heretek_swarm/actors/examiner.py` (create)
- `src/heretek_swarm/testing/stress_testing.py` (create)

**Verification**: Examiner stress-tests agent capabilities; findings feed into consensus; safety bounds identified.

**Edge cases**:
- Stress test causes agent malfunction — automatic recovery; incident report
- Capability gap identified — Steward notified for remediation planning

---

**Task 9**: DISC-03 — Dreamer Lateral Thinking Agent

**Owner**: Dreamer

**Depends**: Phase 1 (Agent base class)

**Files**:
- `src/heretek_swarm/actors/dreamer.py` (create)
- `src/heretek_swarm/creativity/novel_connections.py` (create)

**Verification**: Dreamer generates novel connections; lateral thinking metrics measurable; contribution to deliberation documented.

**Edge cases**:
- Dreamer produces harmful content — Beta validates; Steward can suppress
- Over-reliance on Dreamer — position change ratio monitoring

---

**Task 10**: DISC-04 — Coder Autonomous Execution (Deferred)

**Owner**: Coder

**Depends**: Task 8 (Examiner safety validation)

**Files**:
- `src/heretek_swarm/actors/coder.py` (stub exists, activate with safety bounds)
- `src/heretek_swarm/security/sandbox.py` (create)

**Verification**: Coder executes code autonomously; safety bounds proven; behavioral monitoring active; sandbox isolation verified.

**Edge cases**:
- Coder produces malicious code — sandbox isolation; behavioral detection; immediate termination
- Safety bounds bypass attempt — Sentinel detects; system-wide alert

**Note**: DISC-04 is DEFERRED until safety bounds proven via DISC-02. Coder activation requires explicit Core Triad approval.

---

### Coordination Infrastructure

---

**Task 11**: INTG-01 — Coordinator Task Synchronization

**Owner**: Coordinator

**Depends**: Phase 1 (NATS event mesh, health reporting)

**Files**:
- `src/heretek_swarm/actors/coordinator.py` (create/enhance)
- `src/heretek_swarm/coordination/task_graph.py` (create)
- `src/heretek_swarm/coordination/sync.py` (create)

**Verification**: Coordinator manages task dependency graph; synchronization operational; coordination ratio ≤ 0.35 of total capacity.

**Edge cases**:
- Task dependency cycle — detection and resolution; Steward notified
- Agent dependency deadlock — configurable timeout; escalation to Arbiter

---

**Task 12**: INTG-02 — Nexus Gateway External API Handling

**Owner**: Nexus

**Depends**: Phase 1 (ZERO-01 operational)

**Files**:
- `src/heretek_swarm/actors/nexus.py` (enhance)
- `src/heretek_swarm/gateway/external_api.py` (create)

**Verification**: Nexus handles all external API interactions; protocol translation operational; zero-trust coverage maintained.

**Edge cases**:
- API rate limit violations — automatic backoff; logging
- API provider failure — fallback mechanisms; graceful degradation

---

**Task 13**: INTG-03 — Catalyst Paradigm Shift Detection

**Owner**: Catalyst

**Depends**: Task 11, Task 12

**Files**:
- `src/heretek_swarm/actors/catalyst.py` (create)
- `src/heretek_swarm/coordination/paradigm_detection.py` (create)

**Verification**: Catalyst detects paradigm shifts; change impact assessment; Core Triad notification.

**Edge cases**:
- False positive paradigm shift — Beta validates; deliberation resolves
- Rapid successive shifts — rate limiting; cumulative impact assessment

---

**Task 14**: INTG-04 — Chronos Time Perception

**Owner**: Chronos

**Depends**: Phase 1 (Agent base class)

**Files**:
- `src/heretek_swarm/actors/chronos.py` (create)
- `src/heretek_swarm/coordination/time_dilation.py` (create)

**Verification**: Chronos manages long-running execution context; time perception metrics; adaptive timeout handling.

**Edge cases**:
- Chronos itself overloaded — delegation to Coordinator; graceful degradation
- Time perception drift — reality anchoring against external clocks

---

### Integration and Gate 2 Validation

---

**Task 15**: Phase 2 Integration Test

**Owner**: All Phase 2 agents

**Depends**: Tasks 1-14 (all implementations complete)

**Files**: `tests/integration/test_phase2_full_integration.py` (create)

**Verification**:
- All Phase 2 agents start and report health within 30 seconds
- Deliberation engine resolves disputes without human mediation
- Safety agents detect and respond to anomalies with < 1% false positive rate
- Coordinator maintains coordination ratio ≤ 0.35

**Edge cases**:
- Integration test flakes — retry with exponential backoff
- Race conditions — stress test with 10x normal message rate

---

**Task 16**: Gate 2 Assessment Preparation

**Owner**: Steward (lead), Core Triad

**Depends**: Task 15

**Files**: Documentation for Gate 2 sign-off package

**Verification**: Steward compiles Gate 2 sign-off package including:
- Consensus达成 without human mediation (100% of non-critical decisions)
- Deliberation position change ratio ≥ 15%
- Sentinel anomaly detection precision (false positive rate < 1%)
- Coder safety bounds proven (if DISC-04 activated)
- Partition recovery time < 5 minutes
- Coordination ratio ≤ 0.35

---

## Execution Order

```
[Week 1-2]
Task 1  → CONS-01 Deliberation Engine Integration
Task 4  → SAFE-01 Sentinel Anomaly Response

[Week 3-4]
Task 2  → CONS-02 Immune Response Building
Task 5  → SAFE-02 Sentinel-Prime External Threats

[Week 5-6]
Task 3  → CONS-03 Behavioral Baseline Updating
Task 6  → SAFE-03 Arbiter Dispute Mediation

[Week 7-8]
Task 7  → DISC-01 Explorer Research
Task 11 → INTG-01 Coordinator Task Sync

[Week 9-10]
Task 8  → DISC-02 Examiner Stress-Testing
Task 12 → INTG-02 Nexus External API

[Week 11-12]
Task 9  → DISC-03 Dreamer Lateral Thinking
Task 13 → INTG-03 Catalyst Paradigm Shifts

[Week 13-14]
Task 10 → DISC-04 Coder (DEFERRED - requires Task 8 safety validation)
Task 14 → INTG-04 Chronos Time Perception

[Week 15-16]
Task 15 → Phase 2 Integration Test
Task 16 → Gate 2 Assessment Preparation
```

**Parallelization notes**:
- Tasks 1, 4, 7, 11 can start immediately (Phase 1 complete)
- Tasks 2, 5 depend on Task 1
- Tasks 3, 6 depend on Tasks 2, 5
- Task 10 is DEFERRED until Task 8 completes
- Tasks 12, 13, 14 can run in parallel after Task 11
- Tasks 15, 16 follow all other tasks

---

## Success Criteria

From ROADMAP.md Gate 2 requirements:

| Criterion | Measurement | Pass Threshold |
|-----------|-------------|----------------|
| Consensus达成 without human mediation | % of non-critical decisions | 100% |
| Deliberation position change ratio | Agents changing position during deliberation | ≥ 15% |
| Sentinel anomaly detection precision | False positive rate | < 1% |
| Coder safety bounds | Proof-of-safety complete | Required before activation |
| Partition recovery time | Time to consensus resume | < 5 minutes |
| Coordination ratio | Capacity consumed by coordination | ≤ 0.35 |

---

## Open Questions

These must be resolved before or during Phase 2 execution:

1. **Convoy effect threshold**: How many rounds before Steward tiebreaker triggers? Default 3 still correct?
2. **Coder safety bounds**: What specific mechanisms prove safety before DISC-04 activation?
3. **Emergence validation authority**: Who marks patterns as Proven? How does Core Triad override?
4. **Constitutional scope limits**: What rules are immutable without human intervention?
5. **Deliberation quorum voting weight**: Equal or Steward tiebreaker-only?
6. **Sentinel-Prime alert priority**: How to filter critical vs. informational alerts?
7. **Chronos time dilation scope**: Long-running execution context — how long is "long-running"?

---

## Dependencies on Phase 1

Phase 2 builds on these Phase 1 foundations:

| Phase 1 Component | Used By |
|--------------------|---------|
| Zero-trust validation (ZERO-01/02/03) | All Phase 2 agents |
| Core Triad (GOV-01-05) | CONS-01, CONS-03, SAFE-03 |
| NATS event mesh | INTG-01, INTG-02, all inter-agent communication |
| HealthReportingMixin (12 agents) | All Phase 2 agents |
| ValidationMixin (22 agents) | SAFE-01, SAFE-02, DISC-04 |
| Steward monitoring | ALL — Steward coordinates Phase 2 operations |

---

## Risks

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Consensus deadlock | Medium | High | Pre-vote deliberation mandatory; Steward tiebreaker |
| Coder malicious output | Medium | Critical | DISC-04 deferred; sandboxed execution |
| Behavioral baseline corruption | Low | High | Immutable audit; CONS-03 quorum approval |
| Sentinel-Prime alert fatigue | Medium | Medium | Tune threshold; prioritize critical alerts |
| Coordination overhead consuming capacity | Medium | Medium | Monitor coordination_ratio; pause lower-priority agents |

---

## PLANNING COMPLETE
