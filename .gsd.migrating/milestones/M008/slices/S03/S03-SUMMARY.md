---
id: S03
parent: M008
milestone: M008
provides:
  - All doc-path references updated for the backend/ directory layout. S04 can cleanly scan Python source code without doc-file interference.
requires:
  []
affects:
  []
key_files:
  - docs/ARCHITECTURE.md
  - docs/AGENTS.md
  - docs/AGENT_ARCHITECTURE.md
  - docs/AGENT_REFERENCE.md
  - docs/API_ENDPOINTS.md
  - docs/API_REFERENCE.md
  - docs/CODEBASE_AUDIT.md
  - docs/CORE_ACTORS.md
  - docs/INDEX.md
  - docs/MAIN_PROMPT.md
  - docs/PROMETHEUS_METRICS.md
  - docs/PROTOCOL_SPEC.md
  - docs/architecture/ARCHITECTURE_REALITY.md
  - docs/architecture/EXTERNAL_PATTERNS_ANALYSIS.md
  - docs/architecture/actors-system.md
  - docs/architecture/collective-learning.md
  - docs/architecture/consensus-mechanism.md
  - docs/architecture/emergent-intelligence.md
  - docs/architecture/memory-system.md
  - docs/architecture/orchestration-system.md
  - docs/architecture/plugins.md
  - README.md
  - CLAUDE.md
key_decisions:
  - (none)
patterns_established:
  - (none)
observability_surfaces:
  - none
drill_down_paths:
  []
duration: ""
verification_result: passed
completed_at: 2026-05-12T22:22:21.505Z
blocker_discovered: false
---

# S03: Update documentation path references

**Replaced all stale src/heretek_swarm and heretek-swarm/heretek_swarm path references in 22 doc files with backend/heretek_swarm/; updated README.md directory tree and install instructions; cleaned CLAUDE.md of src/ references**

## What Happened

Completed all 3 tasks: T01 fixed 54 heretek-swarm/heretek_swarm refs in ARCHITECTURE.md + directory tree root; T02 fixed src/heretek_swarm refs across 20 doc files; T03 updated README.md (tree, install paths) and CLAUDE.md (src/ to backend/heretek_swarm/). All 5 verification checks pass — the 14 remaining heretek-swarm/ refs in docs/ are legitimate project-identity/Cli/PyPI references only.

## Verification

All 4 gates verified: 1) heretek-swarm/ refs in docs — zero stale directory refs, only CLI/PyPI/project-name remain (14 matches); 2) src/heretek_swarm in docs — zero matches; 3) src/ in CLAUDE.md — not found (exit 1); 4) ^backend/ in README.md — found (exit 0)

## Requirements Advanced

None.

## Requirements Validated

None.

## New Requirements Surfaced

None.

## Requirements Invalidated or Re-scoped

None.

## Operational Readiness

None.

## Deviations

None.

## Known Limitations

None.

## Follow-ups

S04 (Update code string-literal path references) can proceed — grep -rn 'src/' backend/heretek_swarm/ --include='*.py' to find remaining stale refs in Python source comments/docstrings.

## Files Created/Modified

None.
