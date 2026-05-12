# S01: Rename heretek-swarm/ to backend/ via git mv

**Goal:** Rename heretek-swarm/ to backend/ via git mv, preserving full git history for the Python package with zero code changes.
**Demo:** Repo at new path with no code changes; only directory moves via git mv.

## Must-Haves

- `heretek-swarm/` directory no longer exists in git's tracked files\n- `backend/` directory exists containing `heretek_swarm/`, `tests/`, `docs/`, `Dockerfile`, and all other previously tracked content\n- `git log --follow backend/heretek_swarm/__init__.py` shows the full commit history (history preserved)\n- `git status` shows no untracked file loss — only the rename and pre-existing dirty `.gsd.migrating/` changes\n- All non-backend files (root configs, swarm-dashboard/, docs/, .github/, etc.) are untouched

## Proof Level

- This slice proves: mechanical — no runtime required

## Integration Closure

After this slice, `backend/heretek_swarm/` imports use `heretek_swarm.*` (unchanged package name). All config/CI path updates (pyproject.toml, CI workflows, Dockerfile) are deferred to S02. swarm-dashboard/ is unaffected.

## Verification

- None — purely mechanical filesystem rename with no runtime component.

## Tasks

- [ ] **T01: Rename heretek-swarm/ to backend/ via git mv** `est:10m`
  Execute the single `git mv heretek-swarm/ backend/` command from the repo root to rename the project subdirectory while preserving full git history. This moves 463 tracked files (Python package `heretek_swarm/`, tests/, docs/, Dockerfile, etc.) to their new location under `backend/`.
  - Files: `heretek-swarm/ (→ backend/)`
  - Verify: test -d backend/heretek_swarm && echo 'OK: backend/heretek_swarm exists'
test ! -e heretek-swarm && echo 'OK: old path gone'
git log --oneline -3 backend/heretek_swarm/__init__.py 2>/dev/null | head -5

## Files Likely Touched

- heretek-swarm/ (→ backend/)
