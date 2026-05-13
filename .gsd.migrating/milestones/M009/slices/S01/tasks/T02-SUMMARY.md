---
id: T02
parent: S01
milestone: M009
key_files:
  - pyproject.toml
key_decisions:
  - Removed nats-server from pip dependencies — it's a system binary, not installable via pip.
duration: 
verification_result: passed
completed_at: 2026-05-13T01:15:36.884Z
blocker_discovered: false
---

# T02: Successfully installed heretek-swarm in editable mode with dev dependencies and verified import + CLI work.

**Successfully installed heretek-swarm in editable mode with dev dependencies and verified import + CLI work.**

## What Happened

Ran `pip install -e ".[dev]"` from the repo root. First attempt failed because `nats-server>=3.0.0` was listed under `[project.optional-dependencies] full` but is a system binary, not a pip package. Removed that line from pyproject.toml and retried. The second install succeeded — all core and dev dependencies resolved and installed. Verified by importing heretek_swarm (version 0.2.0) and running `heretek-swarm --help` (CLI shows all commands).

## Verification

1. `python -c "import heretek_swarm; print(heretek_swarm.__version__)"` → printed "0.2.0" ✓
2. `heretek-swarm --help` → showed CLI usage with all commands ✓

## Verification Evidence

| # | Command | Exit Code | Verdict | Duration |
|---|---------|-----------|---------|----------|
| 1 | `python -c "import heretek_swarm; print(heretek_swarm.__version__)"` | 0 | ✅ pass | 3400ms |
| 2 | `heretek-swarm --help` | 0 | ✅ pass | 800ms |

## Deviations

Removed `nats-server>=3.0.0` from the `full` optional-dependencies group — it's not a pip-installable Python package.

## Known Issues

None.

## Files Created/Modified

- `pyproject.toml`
