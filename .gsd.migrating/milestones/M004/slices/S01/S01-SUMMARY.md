---
id: S01
parent: M004
milestone: M004
provides:
  - Working dev environment with pytest available
  - Verified baseline of 658 test functions across 43 files
  - Validated marker registrations match test usage
requires:
  - slice: S01 has no upstream dependencies within this milestone
    provides: 
affects:
  - S02 (depends on working dev environment)
  - S03 (depends on S01+S02 validation)
key_files:
  - .venv/Scripts/python.exe
  - pyproject.toml
key_decisions:
  - Installed dev test packages directly rather than via `[dev]` extras due to nats-server Python 3.14 incompatibility in transitive dependency chain
patterns_established:
  - Dev dependency installation pattern for Python 3.14: install test packages directly when [full] extras chain has incompatible transitive deps
observability_surfaces:
  - none — slice is test infrastructure only, no runtime components
drill_down_paths:
  - .gsd/milestones/M004/slices/S01/tasks/T01-SUMMARY.md
  - .gsd/milestones/M004/slices/S01/tasks/T02-SUMMARY.md
  - .gsd/milestones/M004/slices/S01/tasks/T03-SUMMARY.md
duration: ""
verification_result: passed
completed_at: 2026-05-10T18:54:19.342Z
blocker_discovered: false
---

# S01: Baseline existing tests and configure pytest

**Dev dependencies installed, pytest collects all 658 test functions across 43 files without collection errors, strict-markers mode passes cleanly**

## What Happened

T01 installed all dev dependencies (pytest 9.0.3, pytest-asyncio 1.3.0, coverage 7.13.5, ruff 0.15.12, mypy 2.0.0, hypothesis 6.152.4, faker 40.15.0) into the existing .venv. A transitive dependency issue with nats-server on Python 3.14 was bypassed by installing test packages directly rather than via the [dev] extras chain. T02 verified pytest discovers all 43 test files (658 test functions) without collection errors or warnings. T03 confirmed that all marker registrations in pyproject.toml match test usage — `--strict-markers` passes with zero unknown-marker errors, and asyncio_mode is correctly configured via pyproject.toml global config.

## Verification

(1) `pytest --version` confirmed pytest 9.0.3 available. (2) `pytest --collect-only` reports 658 tests collected from 43 files, exit 0. (3) `pytest --co -q --strict-markers` collects all 43 files with no UNREGISTERED_MARKER errors, exit 0.

## Requirements Advanced

None.

## Requirements Validated

None.

## New Requirements Surfaced

- R001 — pytest must collect all test files without errors (validated)
- R002 — strict-markers mode must pass (validated)

## Requirements Invalidated or Re-scoped

None.

## Operational Readiness

None.

## Deviations

None.

## Known Limitations

The `[dev]` extras definition in pyproject.toml depends on `[full]` which declares nats-server — this transitive dep chain will fail on Python 3.14 regardless. This does not affect test infrastructure.

## Follow-ups

S02 will write actor lifecycle smoke tests. S03 will add GitHub Actions CI. Neither requires any remediation from S01.

## Files Created/Modified

None.
