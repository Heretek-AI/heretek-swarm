# S01: Rename heretek-swarm/ to backend/ via git mv

**Goal:** Use git mv to rename heretek-swarm/ → backend/. This preserves full git history for the Python package. No import rewrites yet.
**Demo:** Repo at new path with no code changes; only directory moves via git mv.

## Must-Haves

- `heretek-swarm/` renamed to `backend/` via `git mv`
- Git history preserved for the Python package
- All other files untouched at their current locations

## Proof Level

- This slice proves: mechanical
- Real runtime required: no
- Human/UAT required: no

## Verification

```bash
# backend/ directory exists, heretek-swarm/ does not
test -d backend/heretek_swarm && echo "backend/ exists" || echo "FAIL: backend/ missing"

# Git history preserved
git log --follow backend/heretek_swarm/__init__.py | head -5

# No untracked files lost
git status --short
```

## Tasks

- [ ] **T01: Rename heretek-swarm/ to backend/** `est:10m`
  - Why: The core directory rename — must use git mv to preserve history
  - Files: `heretek-swarm/` (directory)
  - Do: Run `git mv heretek-swarm/ backend/` from the repo root. Verify `backend/` exists with expected contents and `heretek-swarm/` is gone from git's view.
  - Verify: `test -d backend/heretek_swarm && echo "OK"`
  - Done when: `git status` shows `heretek-swarm/` as deleted, `backend/` as added

## Files Likely Touched

- `heretek-swarm/` → `backend/` (renamed)

## Integration Closure

`backend/heretek_swarm/` still imports from `heretek_swarm.*` — unchanged at this stage. All import rewrites happen in S02.

---
id: M007-S01
provides:
  - Directory renamed, git history preserved
key_decisions:
  - Using `git mv` not `rm` + `git add` to preserve history
patterns_established: []
observability_surfaces: []
requirement_outcomes: []
duration: ~10m
verification_result: pending
completed_at: pending
