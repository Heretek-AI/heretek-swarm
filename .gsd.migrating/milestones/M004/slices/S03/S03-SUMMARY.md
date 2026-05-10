---
id: S03
parent: M004
milestone: M004
provides:
  - Working CI pipeline with unit-only pytest execution
  - Ruff quality gate preventing >= 50 warnings
  - Proper pass/fail signal from CI (no || true swallowing)
requires:
  - slice: S02
    provides: Actor lifecycle test suite (tests/test_actor_lifecycle.py) that can be run with 'not integration' marker
affects:
  - None — S03 is the final slice of M004
key_files:
  - .github/workflows/ci.yml
  - pyproject.toml
key_decisions:
  - Coverage source path and ruff src roots corrected from nonexistent src/ to actual heretek-swarm/ package root
  - CI test-python job runs unit-only tests with proper pass/fail gating — no || true, no services
patterns_established:
  - CI gating pattern: Ruff warning gate with count-based exit 1 threshold (< 50 findings)
  - Coverage source path convention: point to the actual package root directory
observability_surfaces:
  - None — this is a CI configuration slice, no runtime observability surfaces added
drill_down_paths:
  - .gsd/milestones/M004/slices/S03/tasks/T01-SUMMARY.md
  - .gsd/milestones/M004/slices/S03/tasks/T02-SUMMARY.md
duration: ""
verification_result: passed
completed_at: 2026-05-10T20:54:18.949Z
blocker_discovered: false
---

# S03: Add GitHub Actions CI for pytest and ruff

**GitHub Actions CI pipeline with unit-only pytest execution, proper pass/fail gating, Ruff warning gate at < 50 findings, and fixed coverage/ruff source paths in pyproject.toml**

## What Happened

S03 completed the CI surface for M004. Two tasks were executed: T01 fixed the pyproject.toml configuration — coverage source path was corrected from the nonexistent `src/` to `heretek-swarm`, the coverage paths prefix from `src/` to `heretek-swarm/`, and ruff src roots from `["src", "tests"]` to `["heretek-swarm", "tests"]`. T01 is a prerequisite for CI coverage reporting and ruff import resolution to actually work. T02 rewrote the CI workflow: the test-python job had its services block (Postgres/Redis/Qdrant) removed entirely, the pytest command was changed to `-m "not integration"` with proper pass/fail gating (no `|| true`), and a Ruff Warning Gate step was added that exits 1 when findings >= 50. The mypy step also had its `|| true` removed. All other jobs (security-scan, lint-frontend, test-frontend) were left untouched with their existing `|| true` patterns per scope boundaries.

## Verification

All 13 verification checks passed via gsd_exec bash: no services block present, no pg_isready/redis-cli/qdrant references, pytest uses 'not integration' marker, no || true in test-python or mypy steps, Ruff Warning Gate exists with exit 1 logic, security-scan/lint-frontend/test-frontend jobs untouched with their original || true intact, coverage source path points to heretek-swarm, and ruff src roots point to heretek-swarm + tests.

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

None — milestone M004 is complete after S03.

## Files Created/Modified

- `.github/workflows/ci.yml` — Rewrote test-python job: removed services block, switched to unit-only pytest with proper pass/fail gating, added Ruff Warning Gate, removed || true from mypy. Left other jobs untouched.
- `pyproject.toml` — Fixed coverage source path from src to heretek-swarm, coverage paths prefix from src/ to heretek-swarm/, and ruff src roots from [src, tests] to [heretek-swarm, tests]
