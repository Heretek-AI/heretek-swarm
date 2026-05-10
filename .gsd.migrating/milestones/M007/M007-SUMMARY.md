# M007: Execute repository restructure

**Rename heretek-swarm/ to backend/, rewrite imports, fix CI, verify clean**

## What Happened

M007 executes the restructure planned in M006.

## Cross-Slice Verification

- S01: `test -d backend/heretek_swarm && echo "OK"`
- S02: `pytest backend/tests/ -x -q && grep -r "heretek-swarm" .github/workflows/ | wc -l` (should be 0)
- S03: `npm run build --prefix swarm-dashboard && docker compose build`

## Requirement Changes

No requirements were modified — this is purely an infrastructure/planning milestone.

## Forward Intelligence

### What the next milestone should know
- After M007, `backend/heretek_swarm/` is the canonical import path
- swarm-dashboard/ connects via HTTP (subprocess or API), not Python imports — verify this first

### What's fragile
- CI workflows still reference `heretek-swarm/` — must update after `git mv`
- Python's `__init__.py` `__package__` paths may need adjustment after rename

### What assumptions changed
- The entire rename is just `heretek-swarm/` → `backend/` — nothing else moves

## Files Created/Modified

- `heretek-swarm/` → `backend/` (renamed via git mv)
- `.github/workflows/*.yml` (path updates)
- `docker-compose.yml`, `Dockerfile` (path updates)
- `backend/heretek_swarm/**/*.py` (import rewrites)

---
id: M007
provides:
  - Clean monorepo structure
  - Updated CI paths
  - Verified imports and tests
key_decisions:
  - Using `git mv` to preserve history
  - Python imports inside backend/ stay as heretek_swarm. (package-relative)
  - CI workflows use backend/ prefix
patterns_established: []
observability_surfaces: []
requirement_outcomes: []
duration: ~2.5h
verification_result: pending
completed_at: pending
