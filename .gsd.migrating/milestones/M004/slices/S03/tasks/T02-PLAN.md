---
estimated_steps: 1
estimated_files: 1
skills_used: []
---

# T02: Rewrite CI workflow for unit-only test execution with proper pass/fail gating

The current `test-python` job spins up Postgres/Redis/Qdrant services unconditionally, uses `|| true` to swallow test failures, and runs all tests (including integration tests that need those services). Rewrite it: (1) remove the `services:` block entirely — no Postgres, Redis, or Qdrant; (2) change the pytest command to `pytest -m "not integration" -x -q --cov=heretek-swarm --cov-report=term` and remove the `|| true` so failures propagate; (3) keep coverage upload step but make it non-blocking (`if: always()` already handles this). For `lint-python`: (4) remove `|| true` from the mypy step so it gates properly; (5) add a hard Ruff warning gate — run `ruff check heretek-swarm/ tests/` and count findings, exit 1 if >= 50. Leave `security-scan`, `lint-frontend`, and `test-frontend` jobs untouched (out of scope).

## Inputs

- `.github/workflows/ci.yml`
- `pyproject.toml`

## Expected Output

- `.github/workflows/ci.yml`

## Verification

! grep -qE 'pg_isready|redis-cli ping|qdrant|\|\| true' .github/workflows/ci.yml && grep -q 'not integration' .github/workflows/ci.yml
