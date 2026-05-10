---
id: T02
parent: S03
milestone: M004
key_files:
  - .github/workflows/ci.yml
key_decisions:
  - (none)
duration: 
verification_result: passed
completed_at: 2026-05-10T20:48:03.879Z
blocker_discovered: false
---

# T02: Rewrote CI workflow: removed Postgres/Redis/Qdrant services from test-python, switched to unit-only test execution with proper pass/fail gating, added Ruff warning gate, removed || true from mypy

**Rewrote CI workflow: removed Postgres/Redis/Qdrant services from test-python, switched to unit-only test execution with proper pass/fail gating, added Ruff warning gate, removed || true from mypy**

## What Happened

Applied all 5 changes from the task plan to `.github/workflows/ci.yml`:

1. **test-python services removal**: Removed the entire `services:` block (Postgres 16, Redis 7, Qdrant) that spun up containers unconditionally on every CI run.

2. **pytest rewrite**: Changed from `pytest tests/ -v --cov=src --cov-report=xml --cov-report=html --cov-report=term || true` to `pytest -m "not integration" -x -q --cov=heretek-swarm --cov-report=xml --cov-report=term` — skips integration tests, stops on first failure (`-x`), quiet mode (`-q`), and removed the `|| true` so test failures properly gate the job with a non-zero exit code.

3. **Coverage upload**: Kept the Codecov step with `if: always()` so it still runs even on failure. Added `--cov-report=xml` back so the XML file is generated for Codecov.

4. **mypy gating**: Removed `|| true` from the mypy step so type-check failures propagate as job failures.

5. **Ruff warning gate**: Added a new step that runs `ruff check heretek-swarm/ tests/`, counts findings, and exits with code 1 if count >= 50. This provides a soft gate — warnings under 50 pass, at 50+ the job fails visibly in the GitHub UI.

Jobs left untouched: `security-scan`, `lint-frontend`, `test-frontend`.

## Verification

Verified via findstr/grep on the final ci.yml: (1) no 'services:' block present, (2) no 'pg_isready', 'redis-cli', or 'qdrant' references, (3) pytest command includes '-m "not integration"', (4) Ruff Warning Gate step present with 'exit 1' for >= 50 findings, (5) mypy step has no '|| true', (6) security-scan, lint-frontend, test-frontend jobs unchanged with their existing '|| true' still intact.

## Verification Evidence

| # | Command | Exit Code | Verdict | Duration |
|---|---------|-----------|---------|----------|
| 1 | `findstr "services:" .github/workflows/ci.yml || echo 'no services block'` | 1 | ✅ pass | 200ms |
| 2 | `findstr "not integration" .github/workflows/ci.yml` | 0 | ✅ pass | 150ms |
| 3 | `findstr "Ruff Warning" .github/workflows/ci.yml` | 0 | ✅ pass | 150ms |
| 4 | `findstr "pg_isready\|redis-cli\|qdrant" .github/workflows/ci.yml || echo 'no service refs'` | 1 | ✅ pass | 150ms |

## Deviations

None.

## Known Issues

None.

## Files Created/Modified

- `.github/workflows/ci.yml`
