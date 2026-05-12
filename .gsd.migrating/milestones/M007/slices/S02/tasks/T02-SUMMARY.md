---
id: T02
parent: S02
milestone: M007
key_files:
  - .github/workflows/ci.yml
  - .github/workflows/ci-cd.yml
key_decisions:
  - (none)
duration: 
verification_result: passed
completed_at: 2026-05-12T13:33:33.274Z
blocker_discovered: false
---

# T02: Updated 10 path references across ci.yml and ci-cd.yml from stale src/ and heretek-swarm/ paths to backend/

**Updated 10 path references across ci.yml and ci-cd.yml from stale src/ and heretek-swarm/ paths to backend/**

## What Happened

Applied all 10 changes from the task plan across both CI workflow files. In ci.yml: changed bandit target from src/ to backend/ (line 23), ruff check from src/ to backend/ (line 42), ruff warning gate from heretek-swarm/ to backend/ (line 46), mypy from src/ to backend/ (line 56), and pytest --cov from heretek-swarm to backend (line 102). In ci-cd.yml: changed ruff check from src/ to backend/ (line 34), ruff format --check from src/ to backend/ (line 37), mypy from src/ to backend/ (line 40), bandit from src/ to backend/ (line 43), and pytest --cov from src to backend (line 137). Frontend-related lines (swarm-dashboard references, test-frontend jobs) were intentionally left untouched per the task plan constraints. load-test.yml was also confirmed to have no stale path references.

## Verification

Three grep-based checks confirmed clean state:
1. No (bandit|ruff|mypy).*src/ patterns remain in either file (PASS)
2. No heretek-swarm/ references remain in ci.yml (PASS)
3. No --cov=src references remain in either file (PASS)
Additionally, all 8 tool-path backend/ references and both --cov=backend references were confirmed at the correct line positions.

## Verification Evidence

| # | Command | Exit Code | Verdict | Duration |
|---|---------|-----------|---------|----------|
| 1 | `grep -qE "(bandit|ruff|mypy).*src/" .github/workflows/ci.yml .github/workflows/ci-cd.yml` | 1 | ✅ pass | 52ms |
| 2 | `grep -q "heretek-swarm/" .github/workflows/ci.yml` | 1 | ✅ pass | 45ms |
| 3 | `grep -qE -- "--cov=src" .github/workflows/ci-cd.yml .github/workflows/ci.yml` | 1 | ✅ pass | 48ms |

## Deviations

Several individual edit() calls reported success but did not persist to disk, requiring a full file rewrite via write() for both ci.yml and ci-cd.yml to finalize all changes.

## Known Issues

None.

## Files Created/Modified

- `.github/workflows/ci.yml`
- `.github/workflows/ci-cd.yml`
