# S04: Update code string-literal path references

**Goal:** Replace all stale src/ path references in Python source code comments and docstrings with the current backend/ layout paths, ensuring grep -rn 'src/' backend/heretek_swarm/ --include='*.py' returns zero stale matches.
**Demo:** grep -rn 'src/' backend/heretek_swarm/ --include='*.py' returns zero stale path references

## Must-Haves

- grep -rn 'src/' backend/heretek_swarm/ --include='*.py' returns zero matches for stale directory path references. Only legitimate refs (e.g., src/ in RST cross-refs, import path aliases) may remain. All 7 identified stale refs are updated. ruff check passes, pytest passes.

## Proof Level

- This slice proves: Static — file-level grep verification only. No runtime required.

## Integration Closure

Upstream surfaces consumed: S03 cleaned doc refs. This slice cleans code refs. S05 (Final validation pass) will verify the full milestone. No new wiring introduced.

## Verification

- None — all changes are in comments/docstrings. No code behavior change.

## Tasks

- [x] **T01: Replace stale src/ path references in Python source comments and docstrings** `est:30m`
  Replace 7 stale `src/` path-string references across 4 Python source files with correct `backend/` paths:
  - Files: `backend/heretek_swarm/api/main.py`, `backend/heretek_swarm/memory/__init__.py`, `backend/heretek_swarm/runtime/registry_enhanced.py`, `backend/heretek_swarm/tools/__init__.py`
  - Verify: grep -rn 'src/' backend/heretek_swarm/ --include='*.py' should return zero matches (exit code 1). Additionally, grep each specific old pattern: grep -c 'src/heretek_swarm/api/main.py' backend/heretek_swarm/api/main.py returns 0; grep -c 'not legacy src/' backend/heretek_swarm/memory/__init__.py returns 0; grep -c 'Dynamic agent discovery from src/' backend/heretek_swarm/runtime/registry_enhanced.py returns 0; grep -c 'Defaults to src/' backend/heretek_swarm/runtime/registry_enhanced.py returns 0; grep -c 'Re-exports tools from src/' backend/heretek_swarm/tools/__init__.py returns 0

## Files Likely Touched

- backend/heretek_swarm/api/main.py
- backend/heretek_swarm/memory/__init__.py
- backend/heretek_swarm/runtime/registry_enhanced.py
- backend/heretek_swarm/tools/__init__.py
