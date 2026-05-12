---
id: S04
parent: M008
milestone: M008
provides:
  - Clean code string-literal path references matching the backend/ directory layout, ready for S05's final verification pass
requires:
  []
affects:
  - S05
key_files:
  - backend/heretek_swarm/api/main.py
  - backend/heretek_swarm/memory/__init__.py
  - backend/heretek_swarm/runtime/registry_enhanced.py
  - backend/heretek_swarm/tools/__init__.py
key_decisions:
  - All src/ path references in comments/docstrings updated to backend/ to match current project layout
patterns_established:
  - Comment/docstring path references must match the actual directory layout (backend/, not src/ or heretek-swarm/). Verification is pure static grep — no runtime needed.
observability_surfaces:
  - None — no runtime changes.
drill_down_paths:
  - .gsd/milestones/M008/slices/S04/tasks/T01-SUMMARY.md
duration: ""
verification_result: passed
completed_at: 2026-05-12T23:32:47.329Z
blocker_discovered: false
---

# S04: S04

**Replaced 7 stale src/ path-string references across 4 Python source files with correct backend/ paths**

## What Happened

S04 was a mechanical find-and-replace cleanup targeting stale `src/` path references in Python source code comments and docstrings. The pre-restructure directory layout used `src/heretek_swarm/` but the current layout uses `backend/heretek_swarm/`; these stale references were leftover from the restructure.

T01 identified and replaced 7 references across 4 files:
- **api/main.py** (2 references): `src/heretek_swarm/api/main.py` → `backend/heretek_swarm/api/main.py` in project-root calculation comments
- **memory/__init__.py** (1 reference): Removed "not legacy src/" qualifier from a module docstring
- **runtime/registry_enhanced.py** (3 references): "Dynamic agent discovery from src/" → "backend/" and "Defaults to src/" → "backend/" in docstrings
- **tools/__init__.py** (1 reference): "Re-exports tools from src/" → "backend/" in module docstring

All changes were strictly comment/docstring-only — zero functional code changes. No runtime behavior was affected.

## Verification

1. **Primary grep**: `grep -rn 'src/' backend/heretek_swarm/ --include='*.py'` — zero stale matches found (verified via broad sweep)
2. **Per-pattern checks** (all 5 pass):
   - `grep -c 'src/heretek_swarm/api/main.py' backend/heretek_swarm/api/main.py` → 0
   - `grep -c 'not legacy src/' backend/heretek_swarm/memory/__init__.py` → 0
   - `grep -c 'Dynamic agent discovery from src/' backend/heretek_swarm/runtime/registry_enhanced.py` → 0
   - `grep -c 'Defaults to src/' backend/heretek_swarm/runtime/registry_enhanced.py` → 0
   - `grep -c 'Re-exports tools from src/' backend/heretek_swarm/tools/__init__.py` → 0
3. **Replacement confirmation**: All 4 files contain their correct `backend/` replacement text

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

None — S05 provides the final milestone-wide validation pass.

## Files Created/Modified

None.
