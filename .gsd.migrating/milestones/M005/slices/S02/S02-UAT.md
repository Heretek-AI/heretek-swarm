# S02: Consolidate structlog configuration — UAT

**Milestone:** M005
**Written:** 2026-05-11T01:31:29.591Z

# S02: Consolidate structlog configuration — UAT

**Milestone:** M005
**Written:** 2026-05-11

## UAT Type

- **UAT mode:** artifact-driven
- **Why this mode is sufficient:** This slice is purely a refactoring/delegation change — no new runtime behavior. All 120+ loggers continue to function identically because they import get_logger() which is unchanged. Verification is done via static analysis (grep, AST parse) confirming the single canonical code path.

## Preconditions

- Repository is at the correct state with M005/S02 changes applied

## Smoke Test

```bash
grep -c 'structlog\.configure' heretek-swarm/heretek_swarm/logging/config.py
# Must return 1 (the canonical call)

grep -c 'structlog\.configure' heretek-swarm/heretek_swarm/actors/base/core.py
# Must return 0 (exit code 1 = no matches)

grep -c 'structlog\.configure' heretek-swarm/heretek_swarm/infrastructure/otel/logging.py
# Must return 0 (exit code 1 = no matches), only docstring mention allowed
```

## Test Cases

### 1. Verify only one structlog.configure() call in the codebase

1. Run `grep -rn 'structlog\.configure' heretek-swarm/heretek_swarm/ --include="*.py"`
2. **Expected:** Only line in `logging/config.py` has the call. `core.py` and `otel/logging.py` have zero executable calls.

### 2. Verify core.py uses canonical logger

1. Check `heretek-swarm/heretek_swarm/actors/base/core.py` imports `get_logger` from `heretek_swarm.logging.config`
2. **Expected:** `from heretek_swarm.logging.config import get_logger` present; no `import structlog` at top level

### 3. Verify otel/logging.py delegates to canonical config

1. Check `heretek-swarm/heretek_swarm/infrastructure/otel/logging.py` imports `setup_logging` from canonical path
2. Check `init_logging()` calls `_setup_logging(...)` instead of `structlog.configure()`
3. **Expected:** `from heretek_swarm.logging.config import setup_logging as _setup_logging` present; `init_logging()` delegates to `_setup_logging()`

## Edge Cases

### Only docstring mentions remain in non-config files

1. Run `grep -n 'structlog\.configure' heretek-swarm/heretek_swarm/infrastructure/otel/logging.py`
2. **Expected:** Only line 11 matches (docstring reference)

## Failure Signals

- Any executable `structlog.configure()` call outside `logging/config.py`
- `core.py` still importing `structlog` directly
- `otel/logging.py` still calling `structlog.configure()` directly
- Tests failing due to logger import changes

## Not Proven By This UAT

- This UAT does not prove runtime behavior of 120+ loggers (they use the same get_logger() API)
- This UAT does not test integration with OpenTelemetry (unchanged)
- This UAT does not test init_logging() call path (nothing currently calls it)

## Notes for Tester

The slice is a pure structural refactoring: removing duplicate configuration calls and routing everything through one canonical path. No runtime behavior changes are expected or intended.
