---
id: T02
parent: S02
milestone: M005
key_files:
  - heretek-swarm/heretek_swarm/infrastructure/otel/logging.py
key_decisions:
  - init_logging() now delegates to setup_logging() from logging/config.py — single truth path for structlog.configure()
  - LoggingConfig fields mapped: format→json_output, include_trace_context→include_caller_info, log_level→log_level
  - _add_trace_context preserved as reusable processor but no longer auto-wired by init_logging()
duration: 
verification_result: passed
completed_at: 2026-05-11T01:24:45.345Z
blocker_discovered: false
---

# T02: Made infrastructure/otel/logging.py init_logging() delegate to canonical setup_logging() from logging/config.py, removing the duplicate structlog.configure() code path

**Made infrastructure/otel/logging.py init_logging() delegate to canonical setup_logging() from logging/config.py, removing the duplicate structlog.configure() code path**

## What Happened

Rewrote `init_logging()` in `heretek_swarm/infrastructure/otel/logging.py` to delegate to `setup_logging()` from `heretek_swarm.logging.config` instead of calling `structlog.configure()` directly with its own processor chain. The `LoggingConfig` dataclass fields are mapped: `format == "json"` → `json_output`, `include_trace_context` → `include_caller_info`, and `log_level` → `log_level`. Added a module-level docstring clarifying the delegation pattern and noting the canonical config path. The `_add_trace_context` processor function is preserved in the module for future composition. Since nothing currently calls `init_logging()`, this is a safety/API-compatibility change — no runtime behavior changes.

## Verification

Verified via ast.parse syntax check (17 top-level nodes, no errors). Grep for executable `structlog.configure()` in otel/logging.py returns 0 (only a docstring mention remains). The only remaining `structlog.configure()` in the codebase is in `logging/config.py` (1 call, the canonical path).

## Verification Evidence

| # | Command | Exit Code | Verdict | Duration |
|---|---------|-----------|---------|----------|
| 1 | `ast.parse syntax check on otel/logging.py` | 0 | ✅ pass | 150ms |
| 2 | `executable structlog.configure() in otel/logging.py` | 0 | ✅ pass (0 calls) | 100ms |
| 3 | `executable structlog.configure() in config.py` | 0 | ✅ pass (1 canonical call) | 100ms |
| 4 | `grep -rn init_logging | otel in tests/` | 0 | ✅ pass (no tests affected) | 80ms |

## Deviations

None.

## Known Issues

None.

## Files Created/Modified

- `heretek-swarm/heretek_swarm/infrastructure/otel/logging.py`
