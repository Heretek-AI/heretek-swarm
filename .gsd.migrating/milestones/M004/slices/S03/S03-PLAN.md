# S03: Add GitHub Actions CI for pytest and ruff

**Goal:** CI runs on push/PR and reports pass/fail — no more `|| true` swallows, no unnecessary Postgres/Redis/Qdrant services, proper Ruff warning gate at < 50 findings.
**Demo:** CI runs on push/PR and reports pass/fail

## Must-Haves

- `pytest -m "not integration" -x -q` runs in CI without Postgres/Redis/Qdrant services
- A deliberate test failure in a PR causes CI to report "fail" (not pass via `|| true`)
- Ruff gate exits non-zero when findings >= 50
- Frontend jobs remain unchanged (still `|| true` per scope)
- Coverage source path points to the real package root, not nonexistent `src/`
- Ruff source roots match actual directory layout

## Proof Level

- This slice proves: operational

## Integration Closure

Upstream surfaces consumed: `.github/workflows/ci.yml`, `pyproject.toml`, S02 lifecycle test suite (`tests/test_actor_lifecycle.py`)
New wiring introduced: GitHub Actions CI pipeline with unit-only test job, no external services, proper pass/fail gating, and Ruff quality gate.
What remains: milestone is complete after S03 — all three slices deliver the full CI surface.

## Verification

- CI pipeline runs on every push/PR. Test failures appear as red X directly in GitHub UI via job exit codes. Ruff gate failure is visible in the lint-python job output with count of findings.

## Tasks

- [x] **T01: Fix coverage source path and ruff source roots in pyproject.toml** `est:10m`
  Coverage config `[tool.coverage.run] source = ["src"]` points at a directory that doesn't exist — coverage reporting collects nothing. The package lives under `heretek-swarm/heretek_swarm/`. Fix the source path to `["heretek-swarm"]` per the M004 architectural decision. Update the parallel `[tool.coverage.paths] source` entry similarly. Also fix `[tool.ruff] src = ["src", "tests"]` to `["heretek-swarm", "tests"]` so ruff resolves first-party imports from the correct source root. This is a prerequisite for CI coverage reporting to actually work.
  - Files: `pyproject.toml`
  - Verify: grep -q 'source = \["heretek-swarm"\]' pyproject.toml && grep -q 'src = \["heretek-swarm"' pyproject.toml

- [x] **T02: Rewrite CI workflow for unit-only test execution with proper pass/fail gating** `est:30m`
  The current `test-python` job spins up Postgres/Redis/Qdrant services unconditionally, uses `|| true` to swallow test failures, and runs all tests (including integration tests that need those services). Rewrite it: (1) remove the `services:` block entirely — no Postgres, Redis, or Qdrant; (2) change the pytest command to `pytest -m "not integration" -x -q --cov=heretek-swarm --cov-report=term` and remove the `|| true` so failures propagate; (3) keep coverage upload step but make it non-blocking (`if: always()` already handles this). For `lint-python`: (4) remove `|| true` from the mypy step so it gates properly; (5) add a hard Ruff warning gate — run `ruff check heretek-swarm/ tests/` and count findings, exit 1 if >= 50. Leave `security-scan`, `lint-frontend`, and `test-frontend` jobs untouched (out of scope).
  - Files: `.github/workflows/ci.yml`
  - Verify: ! grep -qE 'pg_isready|redis-cli ping|qdrant|\|\| true' .github/workflows/ci.yml && grep -q 'not integration' .github/workflows/ci.yml

## Files Likely Touched

- pyproject.toml
- .github/workflows/ci.yml
