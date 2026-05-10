---
id: T03
parent: S01
milestone: M004
key_files:
  - pyproject.toml
key_decisions:
  - No changes needed — marker registrations already match usage
duration: 
verification_result: passed
completed_at: 2026-05-10T16:40:46.345Z
blocker_discovered: false
---

# T03: Verified all marker registrations match test usage — already aligned; conftest asyncio_mode is covered by pyproject.toml global config; --strict-markers passes cleanly.

**Verified all marker registrations match test usage — already aligned; conftest asyncio_mode is covered by pyproject.toml global config; --strict-markers passes cleanly.**

## What Happened

Audited all 44 test files for custom pytest marker usage. Found only built-in markers (`asyncio`, `parametrize`) in use. The 8 registered markers in pyproject.toml (`unit`, `integration`, `load`, `slow`, `a2a`, `consensus`, `latency`, `security`) are defined for future use but none are currently referenced — this is fine since `--strict-markers` only errors on *used* but unregistered markers. The conftest.py does not need explicit asyncio_mode because `asyncio_mode = "auto"` is already configured globally in pyproject.toml's `[tool.pytest.ini_options]`. Ran `pytest --co -q --strict-markers` and confirmed exit code 0 with all 44 test files collected. No changes were needed.

## Verification

`python -m pytest --co -q --strict-markers` exits 0, all 44 test files collected. No unknown marker errors. grep across test files confirms no custom markers are used that aren't registered.

## Verification Evidence

| # | Command | Exit Code | Verdict | Duration |
|---|---------|-----------|---------|----------|
| 1 | `pytest --co -q --strict-markers` | 0 | ✅ pass | 4500ms |
| 2 | `grep -rn '@pytest.mark.' tests/ | grep -v 'asyncio\|parametrize\|\.parametrize'` | 1 | ✅ pass (no unregistered custom markers found) | 500ms |

## Deviations

None.

## Known Issues

None.

## Files Created/Modified

- `pyproject.toml`
