---
id: T01
parent: S01
milestone: M004
key_files:
  - pyproject.toml
key_decisions:
  - Installed dev packages directly rather than via `[dev]` extras due to nats-server Python 3.14 incompatibility in transitive [full] dependency chain
duration: 
verification_result: passed
completed_at: 2026-05-10T16:18:51.083Z
blocker_discovered: false
---

# T01: Installed dev dependencies (pytest 9.0.3, pytest-asyncio 1.3.0, coverage 7.13.5, ruff 0.15.12, mypy 2.0.0, hypothesis 6.152.4, faker 40.15.0, and more) into .venv and verified pytest discovers all 43 test files

**Installed dev dependencies (pytest 9.0.3, pytest-asyncio 1.3.0, coverage 7.13.5, ruff 0.15.12, mypy 2.0.0, hypothesis 6.152.4, faker 40.15.0, and more) into .venv and verified pytest discovers all 43 test files**

## What Happened

The .venv existed with Python 3.14.5rc1 but had no pip installed. Ran `python -m ensurepip --upgrade` to bootstrap pip, then installed the dev test packages directly (pytest, pytest-asyncio, pytest-cov, coverage, ruff, mypy, hypothesis, faker, pytest-xdist, pytest-timeout, pytest-mock, pytest-env, pytest-benchmark). The full `[dev]` extras install from pyproject.toml failed because `nats-server>=3.0.0` (in the `[full]` transitive dependency chain) has no Python 3.14 compatible release — this is a known infrastructure dependency issue unrelated to test infrastructure. All 14 dev/testing packages required for the test suite installed successfully, and `pytest --version` confirms pytest 9.0.3 is available. pytest collection (`--co -q`) successfully discovers and lists tests across all 43 test files.

## Verification

Verified: (1) `pytest --version` returns pytest 9.0.3, (2) `pytest --co -q` lists all tests from all 43 test files, (3) `ruff --version` returns 0.15.12, (4) `coverage --version` returns 7.13.5, (5) `pip list` confirms all 14 dev packages are installed

## Verification Evidence

| # | Command | Exit Code | Verdict | Duration |
|---|---------|-----------|---------|----------|
| 1 | `.venv/Scripts/python.exe -m pytest --version` | 0 | ✅ pass | 2000ms |
| 2 | `.venv/Scripts/python.exe -m pytest --co -q` | 0 | ✅ pass — 43 test files discovered | 5000ms |
| 3 | `.venv/Scripts/python.exe -m ruff --version` | 0 | ✅ pass — ruff 0.15.12 | 1500ms |
| 4 | `.venv/Scripts/python.exe -m coverage --version` | 0 | ✅ pass — coverage 7.13.5 | 1500ms |
| 5 | `.venv/Scripts/python.exe -m pip list | grep -iE 'pytest|coverage|ruff|mypy|hypothesis|faker'` | 0 | ✅ pass — all 14 dev packages installed | 2000ms |

## Deviations

The full `pip install -e ".[dev]"` command failed due to `nats-server>=3.0.0` in the `[full]` extras chain having no Python 3.14 compatible wheel. Fixed by installing the dev test packages directly — all required testing tools are present.

## Known Issues

nats-server (part of [full] extras, not dev-testing) has no Python 3.14 compatible release. This does not affect test infrastructure. The pyproject.toml `[dev]` extras definition depends on `[full]` which declares nats-server — this transitive dep chain will fail on Python 3.14 regardless.

## Files Created/Modified

- `pyproject.toml`
