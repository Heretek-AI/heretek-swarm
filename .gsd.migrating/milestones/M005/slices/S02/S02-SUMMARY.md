---
id: S02
parent: M005
milestone: M005
provides:
  - Canonical single-source-of-truth for structlog configuration; from heretek_swarm.logging.config import configure_logging as the one true entry point
requires:
  - slice: S01
    provides: Documentation foundation for the codebase; logging/config.py as canonical config entry point
affects:
  - S03: Convert surviving flat actors to thin re-exports
key_files:
  - heretek-swarm/heretek_swarm/actors/base/core.py
  - heretek-swarm/heretek_swarm/infrastructure/otel/logging.py
key_decisions:
  - Replaced direct structlog.configure() with canonical get_logger() import from logging/config.py in core.py
  - init_logging() now delegates to setup_logging() from logging/config.py — single truth path for structlog.configure()
  - LoggingConfig fields mapped: format→json_output, include_trace_context→include_caller_info, log_level→log_level
  - _add_trace_context preserved as reusable processor but no longer auto-wired by init_logging()
patterns_established:
  - structlog configuration consolidation pattern: all structlog.configure() calls route through logging/config.py as single source of truth; other modules delegate via setup_logging() parameters rather than calling structlog.configure() directly
observability_surfaces:
  - none — this is a safety/API-compatibility refactoring with no new observability surfaces
drill_down_paths:
  - .gsd/milestones/M005/slices/S02/tasks/T01-SUMMARY.md
  - .gsd/milestones/M005/slices/S02/tasks/T02-SUMMARY.md
duration: ""
verification_result: passed
completed_at: 2026-05-11T01:31:29.591Z
blocker_discovered: false
---

# S02: Consolidate structlog configuration

**Consolidated all structlog configuration into logging/config.py as the single source of truth; removed duplicate structlog.configure() calls from actors/base/core.py and infrastructure/otel/logging.py via delegation**

## What Happened

T01 removed the ~18-line structlog.configure(...) block from actors/base/core.py (lines 54-71) and replaced the direct import structlog + structlog.get_logger() pattern with the canonical from heretek_swarm.logging.config import get_logger. The structlog import was removed entirely since it was only used for configure() and get_logger(). T02 rewrote init_logging() in infrastructure/otel/logging.py to delegate to setup_logging() from logging/config.py instead of calling structlog.configure() directly. The LoggingConfig dataclass fields are mapped: format→json_output, include_trace_context→include_caller_info, log_level→log_level. The _add_trace_context processor is preserved as a reusable utility but no longer auto-wired by init_logging(). After both tasks, only one structlog.configure() call exists in the codebase — the canonical one in logging/config.py.

## Verification

Verified: grep for structlog.configure() in core.py returns 0 matches (exit code 1 = no matches); grep for executable structlog.configure() in otel/logging.py returns 0 matches (only a docstring mention remains); the only structlog.configure() call in the entire codebase is in logging/config.py (1 match, the canonical path). AST parse verification confirmed no executable configure() calls outside config.py. No tests import structlog from core.py — only ActorMessage, ActorState, ActorStatus imports remain, unchanged.

## Requirements Advanced

None.

## Requirements Validated

None.

## New Requirements Surfaced

None.

## Requirements Invalidated or Re-scoped

None.

## Operational Readiness

None.

## Deviations

None.

## Known Limitations

None.

## Follow-ups

S03: Convert surviving flat actors to thin re-exports.

## Files Created/Modified

- `heretek-swarm/heretek_swarm/actors/base/core.py` — Removed duplicate structlog.configure() block; replaced import structlog with canonical get_logger() from logging/config.py
- `heretek-swarm/heretek_swarm/infrastructure/otel/logging.py` — init_logging() now delegates to setup_logging() from logging/config.py instead of calling structlog.configure() directly; added docstring clarifying delegation pattern
