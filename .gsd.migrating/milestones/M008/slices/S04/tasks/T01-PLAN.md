---
estimated_steps: 6
estimated_files: 4
skills_used: []
---

# T01: Replace stale src/ path references in Python source comments and docstrings

Replace 7 stale `src/` path-string references across 4 Python source files with correct `backend/` paths:

1. `backend/heretek_swarm/api/main.py` (3 refs): `src/heretek_swarm/api/main.py` → `backend/heretek_swarm/api/main.py` at lines 425, 1245, 1277
2. `backend/heretek_swarm/memory/__init__.py` (1 ref): `(from base module - local, not legacy src/)` → `(local import)` at line 25
3. `backend/heretek_swarm/runtime/registry_enhanced.py` (2 refs): `src/heretek_swarm/actors/` → `backend/heretek_swarm/actors/` at lines 8 and 99
4. `backend/heretek_swarm/tools/__init__.py` (1 ref): `src/tools` → `backend/heretek_swarm/tools` at line 4

All changes are in comments/docstrings only — no functional code changes.

## Inputs

- `backend/heretek_swarm/api/main.py`
- `backend/heretek_swarm/memory/__init__.py`
- `backend/heretek_swarm/runtime/registry_enhanced.py`
- `backend/heretek_swarm/tools/__init__.py`

## Expected Output

- `backend/heretek_swarm/api/main.py`
- `backend/heretek_swarm/memory/__init__.py`
- `backend/heretek_swarm/runtime/registry_enhanced.py`
- `backend/heretek_swarm/tools/__init__.py`

## Verification

grep -rn 'src/' backend/heretek_swarm/ --include='*.py' should return zero matches (exit code 1). Additionally, grep each specific old pattern: grep -c 'src/heretek_swarm/api/main.py' backend/heretek_swarm/api/main.py returns 0; grep -c 'not legacy src/' backend/heretek_swarm/memory/__init__.py returns 0; grep -c 'Dynamic agent discovery from src/' backend/heretek_swarm/runtime/registry_enhanced.py returns 0; grep -c 'Defaults to src/' backend/heretek_swarm/runtime/registry_enhanced.py returns 0; grep -c 'Re-exports tools from src/' backend/heretek_swarm/tools/__init__.py returns 0
