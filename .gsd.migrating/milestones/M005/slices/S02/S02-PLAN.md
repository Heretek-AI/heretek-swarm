# S02: Consolidate structlog configuration

**Goal:** Centralize structlog configuration into `logging/config.py` as the single source of truth, removing duplicate `structlog.configure()` calls from `actors/base/core.py` and making `infrastructure/otel/logging.py`'s `init_logging()` delegate to the canonical config path. After this slice, `from heretek_swarm.logging.config import configure_logging` is the one true entry point.
**Demo:** from heretek_swarm.logging.config import configure_logging

## Must-Haves

- No remaining `structlog.configure()` call exists outside `logging/config.py`\n- `infrastructure/otel/logging.init_logging()` no longer calls `structlog.configure()` itself — it delegates to `logging/config.py`\n- All existing entry points (api/main.py, cli.py, runtime/main_loop.py, cli/goal_commands.py) continue to work unchanged\n- Existing loggers across 120+ modules continue to function identically (processors, format, level)\n- Tests still pass: `pytest tests/` passes with no regressions

## Proof Level

- This slice proves: contract

## Integration Closure

- Upstream surfaces consumed: `logging/config.py` (canonical configure_logging/setup_logging), `actors/base/core.py` (removes duplicate call), `infrastructure/otel/logging.py` (delegates instead of calling structlog.configure directly)\n- New wiring introduced in this slice: none (only removals and delegation)\n- What remains before the milestone is truly usable end-to-end: S03 (convert flat actors to re-exports)

## Verification

- Runtime signals: unchanged — log format, levels, and output destinations are preserved\n- Inspection surfaces: unchanged\n- Failure visibility: removed duplicate configure() call eliminates subtle race where two configure() calls could conflict\n- Redaction constraints: none

## Tasks

- [x] **T01: Remove duplicate `structlog.configure()` from actors/base/core.py, use canonical logger** `est:15m`
  Remove the `structlog.configure(...)` block (lines ~54-71) from `heretek_swarm/actors/base/core.py` and update the module-level logger to use the canonical `get_logger()` from `heretek_swarm.logging.config`. This eliminates the first of two duplicate structlog.configure() calls. The `import structlog` may remain or be narrowed to just `get_logger` import.
  - Files: `heretek-swarm/heretek_swarm/actors/base/core.py`
  - Verify: grep -c "structlog.configure" heretek-swarm/heretek_swarm/actors/base/core.py should return 0; grep -c "get_logger" should match expected usage

- [x] **T02: Make infrastructure/otel/logging.py init_logging() delegate to canonical config** `est:15m`
  Update `init_logging()` in `heretek_swarm/infrastructure/otel/logging.py` to delegate to `setup_logging()` from `heretek_swarm.logging.config` instead of calling `structlog.configure()` directly. The `LoggingConfig` dataclass fields should be mapped to `setup_logging()` parameters. This ensures there is only one code path that calls `structlog.configure()`. Since nothing currently calls `init_logging()`, this is a safety/API-compatibility change — no runtime behavior changes.
  - Files: `heretek-swarm/heretek_swarm/infrastructure/otel/logging.py`
  - Verify: grep -c "structlog.configure" heretek-swarm/heretek_swarm/infrastructure/otel/logging.py should return 0 (the only call is in logging/config.py now)

## Files Likely Touched

- heretek-swarm/heretek_swarm/actors/base/core.py
- heretek-swarm/heretek_swarm/infrastructure/otel/logging.py
