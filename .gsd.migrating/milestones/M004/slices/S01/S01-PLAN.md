# S01: Baseline existing tests and configure pytest

**Goal:** Ensure dev dependencies (pytest, pytest-asyncio) are installed in the .venv and that pytest collects all 16 existing test files without collection errors. After this slice, `pytest --co -q` lists all test functions and the test configuration in pyproject.toml is validated against what's actually in the repo.
**Demo:** pytest --co -q lists all existing tests

## Must-Haves

- `pytest --co -q` collects all test files without import or collection errors\n- All 16 test files in tests/ are discovered (~649 test functions)\n- No `UNREGISTERED_MARKER` errors from `--strict-markers`\n- Dev dependencies are installed and pytest CLI is available

## Verification

- Run the task and slice verification checks for this slice.

## Tasks

- [x] **T01: Install dev dependencies into .venv and verify pytest is available** `est:15m`
  The .venv exists but has no dev packages installed (no pytest, no pytest-asyncio, no coverage, no ruff). Install the dev dependencies from pyproject.toml using `[dev]` extras so pytest and all test infrastructure are available.
  - Files: `.venv/Scripts/python.exe`, `pyproject.toml`
  - Verify: python -m pytest --version

- [x] **T02: Verify pytest collects all 16 existing test files without errors** `est:15m`
  Run `pytest --co -q` to collect all tests without executing them. Confirm all 16 test files are discovered (~649 test functions). If any collection errors occur (import failures, missing modules), diagnose and fix them. Common issues: missing asyncio_mode=auto config (already set), missing test path (already set to tests/), circular imports from test modules.
  - Files: `pyproject.toml`, `tests/conftest.py`
  - Verify: python -m pytest --co -q 2>&1 | tail -5

- [x] **T03: Add integration test markers and conftest improvements for clean collection** `est:15m`
  Based on pyproject.toml's marker definitions (unit, integration, load, slow, a2a, consensus, latency, security), ensure all marker registrations in pyproject.toml match what test files use. Add any missing markers to the pyproject.toml. Ensure the conftest.py has proper asyncio_mode support. Verify strict-markers mode passes.
  - Files: `pyproject.toml`, `tests/conftest.py`
  - Verify: python -m pytest --co -q --strict-markers 2>&1 | tail -5

## Files Likely Touched

- .venv/Scripts/python.exe
- pyproject.toml
- tests/conftest.py
