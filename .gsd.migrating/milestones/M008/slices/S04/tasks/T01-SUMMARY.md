---
id: T01
parent: S04
milestone: M008
key_files:
  - backend/heretek_swarm/api/main.py
  - backend/heretek_swarm/memory/__init__.py
  - backend/heretek_swarm/runtime/registry_enhanced.py
  - backend/heretek_swarm/tools/__init__.py
key_decisions:
  - All src/ path references in comments/docstrings across the codebase updated to backend/ to match the current project layout
duration: 
verification_result: passed
completed_at: 2026-05-12T23:30:10.106Z
blocker_discovered: false
---

# T01: Replaced 7 stale src/ path-string references across 4 Python source files with correct backend/ paths

**Replaced 7 stale src/ path-string references across 4 Python source files with correct backend/ paths**

## What Happened

Replaced all 7 stale `src/` path-string references in Python source comments and docstrings across 4 files with the correct `backend/` layout paths:

1. **`backend/heretek_swarm/api/main.py`** (3 refs at lines 425, 1245, 1277): Changed `src/heretek_swarm/api/main.py` → `backend/heretek_swarm/api/main.py` in three "Calculate project root" comments within `_init_spa_mount`, `root`, and the catch-all SPA route handler functions.
2. **`backend/heretek_swarm/memory/__init__.py`** (1 ref at line 25): Changed `(from base module - local, not legacy src/)` → `(local import)` — a clean replacement that preserves the clarifying intent without the stale `src/` reference.
3. **`backend/heretek_swarm/runtime/registry_enhanced.py`** (2 refs at lines 8 and 99): Changed `src/heretek_swarm/actors/` → `backend/heretek_swarm/actors/` in both the module docstring feature list and the `actors_dir` parameter docstring.
4. **`backend/heretek_swarm/tools/__init__.py`** (1 ref at line 4): Changed `Re-exports tools from src/tools` → `Re-exports tools from backend/heretek_swarm/tools`.

All changes are in comments/docstrings only — no functional code behavior was modified. Several edits required multiple attempts due to identical comment patterns in `api/main.py` requiring expanded unique context matching.

## Verification

Primary verification: `grep -rn 'src/' backend/heretek_swarm/ --include='*.py'` returns exit code 1 (zero matches found). Specific per-pattern checks all return 0 matches for each stale pattern: `src/heretek_swarm/api/main.py`, `not legacy src/`, `Dynamic agent discovery from src/`, `Defaults to src/`, `Re-exports tools from src/`. All 5 specific pattern checks pass.

## Verification Evidence

| # | Command | Exit Code | Verdict | Duration |
|---|---------|-----------|---------|----------|
| 1 | `grep -rn 'src/' backend/heretek_swarm/ --include='*.py'` | 1 | ✅ pass | 45ms |
| 2 | `grep -c 'src/heretek_swarm/api/main.py' backend/heretek_swarm/api/main.py` | 1 | ✅ pass | 12ms |
| 3 | `grep -c 'not legacy src/' backend/heretek_swarm/memory/__init__.py` | 1 | ✅ pass | 8ms |
| 4 | `grep -c 'Dynamic agent discovery from src/' backend/heretek_swarm/runtime/registry_enhanced.py` | 1 | ✅ pass | 8ms |
| 5 | `grep -c 'Defaults to src/' backend/heretek_swarm/runtime/registry_enhanced.py` | 1 | ✅ pass | 7ms |
| 6 | `grep -c 'Re-exports tools from src/' backend/heretek_swarm/tools/__init__.py` | 1 | ✅ pass | 6ms |

## Deviations

None.

## Known Issues

None.

## Files Created/Modified

- `backend/heretek_swarm/api/main.py`
- `backend/heretek_swarm/memory/__init__.py`
- `backend/heretek_swarm/runtime/registry_enhanced.py`
- `backend/heretek_swarm/tools/__init__.py`
