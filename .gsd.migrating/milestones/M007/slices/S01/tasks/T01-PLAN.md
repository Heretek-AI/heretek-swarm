---
estimated_steps: 16
estimated_files: 1
skills_used: []
---

# T01: Rename heretek-swarm/ to backend/ via git mv

Execute the single `git mv heretek-swarm/ backend/` command from the repo root to rename the project subdirectory while preserving full git history. This moves 463 tracked files (Python package `heretek_swarm/`, tests/, docs/, Dockerfile, etc.) to their new location under `backend/`.

**Important constraints:**
- Must use `git mv`, NOT `mv` + `git add` — this is critical for history preservation
- Run from repo root: `cd /c/Users/Derek/Desktop/heretek-swarm && git mv heretek-swarm/ backend/`
- Do NOT modify any file contents — this is purely a directory rename
- Do NOT update pyproject.toml, CI workflows, or any config — those are S02
- The existing `.gsd.migrating/` dirty state in git is pre-existing and can be ignored
- gitignored contents (.actor_states, .benchmarks, .pytest_cache, *.db, *.egg-info) inside the old directory will follow the rename automatically since git mv respects gitignore

**Pre-flight checks before the mv:**
- Confirm `heretek-swarm/` exists and has tracked files
- Confirm `backend/` does NOT already exist

**Post-flight verification:**
- `test -d backend/heretek_swarm && echo OK`
- `test ! -e heretek-swarm && echo OK` (old path is gone)
- `git log --oneline -3 backend/heretek_swarm/__init__.py` shows history
- `git status --short` shows the rename (and any pre-existing dirty state)

## Inputs

- `heretek-swarm/heretek_swarm/`
- `heretek-swarm/tests/`
- `heretek-swarm/Dockerfile`
- `heretek-swarm/docs/`
- `heretek-swarm/agent_workspace/`

## Expected Output

- `backend/heretek_swarm/`
- `backend/tests/`
- `backend/Dockerfile`
- `backend/docs/`
- `backend/agent_workspace/`

## Verification

test -d backend/heretek_swarm && echo 'OK: backend/heretek_swarm exists'
test ! -e heretek-swarm && echo 'OK: old path gone'
git log --oneline -3 backend/heretek_swarm/__init__.py 2>/dev/null | head -5

## Observability Impact

None — purely mechanical rename
