# S01: Baseline existing tests and configure pytest — UAT

**Milestone:** M004
**Written:** 2026-05-10T18:54:19.343Z

# S01: Baseline existing tests and configure pytest — UAT

**Milestone:** M004
**Written:** 2026-05-08

## UAT Type

- **UAT mode:** artifact-driven
- **Why this mode is sufficient:** This slice is purely about test infrastructure — no runtime components, no human-interactive UI. Verification is fully automatable via CLI.

## Preconditions

- Project .venv exists with Python 3.14
- Dev dependencies installed

## Smoke Test

```bash
python -m pytest --collect-only
```
Expected: 658 tests collected from 43 files, exit 0.

## Test Cases

### 1. Pytest discovers all test files

1. Run `python -m pytest --collect-only`
2. **Expected:** All 43 test files under `tests/` are listed, total matches known count of 658 test functions, exit code 0.

### 2. Strict markers mode passes

1. Run `python -m pytest --co -q --strict-markers`
2. **Expected:** No UNREGISTERED_MARKER errors, all 43 files collected, exit code 0.

## Edge Cases

### 3. Dev dependencies available

1. Run `python -m pytest --version`
2. Run `ruff --version`
3. Run `coverage --version`
4. **Expected:** All three tools return version strings confirming installation.

## Failure Signals

- `pytest` command not found → dev dependencies not installed
- Collection errors (ImportError, ModuleNotFoundError) → missing dependencies or circular imports
- `UNREGISTERED_MARKER` errors → marker registrations out of sync with test usage

## Not Proven By This UAT

- Whether individual tests actually pass (they are collected but not executed)
- CI integration (covered by S03)
- Actor lifecycle behavior (covered by S02)

## Notes for Tester

This is a baseline slice — no code was modified beyond dependency installation. The 43 test files and 658 test functions are the existing test surface.
