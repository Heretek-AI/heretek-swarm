# S01: Local Python Verification

**Goal:** Prove the Python package installs cleanly and all tests pass with zero lint/type violations
**Demo:** `pip install -e .` exits 0, `heretek-swarm --help` shows help output, `pytest tests/` shows zero failures, `ruff check backend/heretek_swarm/ tests/` shows zero violations, `mypy backend/heretek_swarm` shows zero type errors

## Must-Haves

- 1. pip install -e ".[dev]" exits 0
- 2. pytest tests/ — 0 failures, 0 errors
- 3. ruff check backend/heretek_swarm/ tests/ — 0 violations
- 4. mypy backend/heretek_swarm — 0 type errors (strict mode)
- 5. heretek-swarm --help produces expected output

## Proof Level

- This slice proves: All verified via command exit codes and output

## Integration Closure

None — local only, no service dependencies

## Verification

- Run the task and slice verification checks for this slice.

## Tasks

- [x] **T01: Create .env from .env.example** `est:15m`
  Copy .env.example to .env. Fill in required values (OPENAI_API_KEY, etc.) using secure_env_collect for the API key. Verify .env is parseable by docker compose config.
  - Files: `.env.example`, `.env`
  - Verify: cat .env | grep -v '^#' | grep -v '^$' | wc -l > 10

- [x] **T02: Editable pip install** `est:15m`
  Run pip install -e '.[dev]' from repo root. If uv.lock is stale, run uv lock --refresh then retry. Fix any pyproject.toml path/dependency issues discovered.
  - Files: `pyproject.toml`, `uv.lock`
  - Verify: python -c 'import heretek_swarm; print(heretek_swarm.__version__)' && heretek-swarm --help

- [ ] **T03: Run and fix full pytest suite** `est:60m`
  Run pytest tests/ with verbose output. Fix all failures and errors found. Pay special attention to import errors from the restructure (M006-M008). Add regression tests for any untested bugs discovered.
  - Files: `tests/`
  - Verify: cd backend && pytest tests/ -v --tb=short 2>&1 | tail -5

- [ ] **T04: Fix ruff lint violations** `est:30m`
  Run ruff check backend/heretek_swarm/ tests/. Fix all violations. Focus on import-related issues and any new lint rules that have been added since M008.
  - Files: `backend/heretek_swarm/`, `tests/`
  - Verify: cd backend && ruff check heretek_swarm tests --quiet

- [ ] **T05: Fix mypy strict mode type errors** `est:60m`
  Run mypy backend/heretek_swarm in strict mode. Fix all type errors. Many type errors may have existed pre-restructure but were never caught — fix them all.
  - Files: `backend/heretek_swarm/`
  - Verify: cd backend && mypy heretek_swarm --strict

## Files Likely Touched

- .env.example
- .env
- pyproject.toml
- uv.lock
- tests/
- backend/heretek_swarm/
