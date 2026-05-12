---
id: T01
parent: S02
milestone: M005
key_files:
  - heretek-swarm/heretek_swarm/actors/base/core.py
key_decisions:
  - Replaced direct structlog.configure() with canonical get_logger() import from logging/config.py
duration: 
verification_result: passed
completed_at: 2026-05-11T01:15:33.484Z
blocker_discovered: false
---

# T01: Removed duplicate `structlog.configure()` from actors/base/core.py; logger now uses canonical `get_logger()` from logging/config.py

**Removed duplicate `structlog.configure()` from actors/base/core.py; logger now uses canonical `get_logger()` from logging/config.py**

## What Happened

Removed the ~18-line `structlog.configure(...)` block from `heretek_swarm/actors/base/core.py` (lines ~54-71) and replaced the `import structlog` + `structlog.get_logger("AgentActor")` pattern with `from heretek_swarm.logging.config import get_logger` and `logger = get_logger("AgentActor")`. This eliminates the first of two duplicate structlog.configure() calls, centralizing configuration into `logging/config.py` as the single source of truth. The import of `structlog` itself was removed entirely since it was only used for the configure() call and get_logger().

## Verification

Verified via grep: `structlog.configure` count = 0 in core.py; `get_logger` imported from the canonical path and used for logger creation. Checked that no tests import structlog from core.py — only imports of ActorMessage, ActorState, ActorStatus remain, which are unchanged.

## Verification Evidence

| # | Command | Exit Code | Verdict | Duration |
|---|---------|-----------|---------|----------|
| 1 | `grep -c 'structlog.configure' heretek-swarm/heretek_swarm/actors/base/core.py` | 1 | ✅ pass | 150ms |
| 2 | `grep -n 'get_logger\|structlog' heretek-swarm/heretek_swarm/actors/base/core.py` | 0 | ✅ pass | 100ms |

## Deviations

None.

## Known Issues

None.

## Files Created/Modified

- `heretek-swarm/heretek_swarm/actors/base/core.py`
