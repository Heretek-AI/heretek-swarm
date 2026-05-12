---
id: T02
parent: S03
milestone: M008
key_files:
  - docs/AGENTS.md
  - docs/API_ENDPOINTS.md
  - docs/AGENT_REFERENCE.md
  - docs/AGENT_ARCHITECTURE.md
  - docs/CODEBASE_AUDIT.md
  - docs/API_REFERENCE.md
  - docs/CORE_ACTORS.md
  - docs/INDEX.md
  - docs/MAIN_PROMPT.md
  - docs/PROMETHEUS_METRICS.md
  - docs/PROTOCOL_SPEC.md
  - docs/architecture/ARCHITECTURE_REALITY.md
  - docs/architecture/actors-system.md
  - docs/architecture/memory-system.md
  - docs/architecture/consensus-mechanism.md
  - docs/architecture/emergent-intelligence.md
  - docs/architecture/collective-learning.md
  - docs/architecture/orchestration-system.md
  - docs/architecture/plugins.md
  - docs/architecture/EXTERNAL_PATTERNS_ANALYSIS.md
key_decisions:
  - (none)
duration: 
verification_result: untested
completed_at: 2026-05-12T22:22:01.665Z
blocker_discovered: false
---

# T02: Replaced all src/heretek_swarm → backend/heretek_swarm references across 20 doc files

**Replaced all src/heretek_swarm → backend/heretek_swarm references across 20 doc files**

## What Happened

Used sed to replace all stale src/heretek_swarm path references with backend/heretek_swarm across 20 doc files simultaneously. This covered markdown inline-code paths, file links, markdown link destinations, and one GitHub blob URL path. Verified with grep that zero stale refs remain.

## Verification

grep -rn 'src/heretek_swarm' docs/ returns zero matches (exit 1)

## Verification Evidence

| # | Command | Exit Code | Verdict | Duration |
|---|---------|-----------|---------|----------|
| — | No verification commands discovered | — | — | — |

## Deviations

None.

## Known Issues

None.

## Files Created/Modified

- `docs/AGENTS.md`
- `docs/API_ENDPOINTS.md`
- `docs/AGENT_REFERENCE.md`
- `docs/AGENT_ARCHITECTURE.md`
- `docs/CODEBASE_AUDIT.md`
- `docs/API_REFERENCE.md`
- `docs/CORE_ACTORS.md`
- `docs/INDEX.md`
- `docs/MAIN_PROMPT.md`
- `docs/PROMETHEUS_METRICS.md`
- `docs/PROTOCOL_SPEC.md`
- `docs/architecture/ARCHITECTURE_REALITY.md`
- `docs/architecture/actors-system.md`
- `docs/architecture/memory-system.md`
- `docs/architecture/consensus-mechanism.md`
- `docs/architecture/emergent-intelligence.md`
- `docs/architecture/collective-learning.md`
- `docs/architecture/orchestration-system.md`
- `docs/architecture/plugins.md`
- `docs/architecture/EXTERNAL_PATTERNS_ANALYSIS.md`
