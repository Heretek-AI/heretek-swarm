---
id: S02
parent: M007
milestone: M007
provides:
  - All build-configuration and CI workflow files reference backend/ directory; zero stale heretek-swarm/ or src/ path references remain in the 5 affected files
requires:
  - slice: S01
    provides: backend/ directory in place via git mv; no code changes
affects:
  - S03
key_files:
  - pyproject.toml
  - backend/Dockerfile
  - docker-compose.yml
  - .github/workflows/ci.yml
  - .github/workflows/ci-cd.yml
key_decisions:
  - GitHub URLs in pyproject.toml are intentionally excluded from path rewrites — they reference the remote repository, not the local filesystem
  - User-home config paths (~/.heretek-swarm/) are intentionally left unchanged — they are application-level runtime paths, not source-tree paths
patterns_established:
  - When edit() calls don't persist to disk on Windows, fall back to full file write() to finalize changes
observability_surfaces:
  - none
drill_down_paths:
  - .gsd/milestones/M007/slices/S02/tasks/T01-SUMMARY.md
  - .gsd/milestones/M007/slices/S02/tasks/T02-SUMMARY.md
duration: ""
verification_result: passed
completed_at: 2026-05-12T13:43:11.551Z
blocker_discovered: false
---

# S02: Rewrite imports and CI paths

**Updated 18 path references across 5 build-configuration and CI workflow files from stale heretek-swarm/ and src/ paths to backend/ after S01's git mv**

## What Happened

After S01 renamed the `heretek-swarm/` directory to `backend/` via git mv, this slice updated all build-configuration and CI workflow files to reference the new directory name.

**T01** targeted 8 path references across 3 files:
- `pyproject.toml`: Updated `where`, `source`, and `src` directives from `["heretek-swarm"]` to `["backend"]`
- `backend/Dockerfile`: Updated COPY paths from `heretek-swarm/` to `backend/`
- `docker-compose.yml`: Updated `dockerfile` path from `heretek-swarm/Dockerfile` to `backend/Dockerfile`

**T02** targeted 10 path references across 2 CI workflow files:
- `.github/workflows/ci.yml`: Updated bandit, ruff, mypy tool paths from `heretek-swarm/` and stale `src/` to `backend/`; updated `--cov=src` to `--cov=backend`
- `.github/workflows/ci-cd.yml`: Updated ruff check, ruff format, mypy, bandit tool paths similarly; updated `--cov=src` to `--cov=backend`

No Python package imports were touched — `heretek_swarm` is the package name (unchanged by directory rename). GitHub URLs in pyproject.toml were correctly left as-is. User-home config paths (`~/.heretek-swarm/`) were intentionally not modified as they are application-level, not source-tree paths.

## Verification

Six verification gates confirmed clean state:
1. No `heretek-swarm/` filesystem-path references remain in `backend/Dockerfile` or `docker-compose.yml`
2. No stale `heretek-swarm` paths remain in pyproject.toml `where`/`source`/`src` directives
3. No `(bandit|ruff|mypy).*src/` patterns remain in either CI workflow file
4. No `heretek-swarm/` references remain in `.github/workflows/ci.yml`
5. No `--cov=src` references remain in either CI workflow file
6. All 18 backend/ paths confirmed at correct positions across all 5 files

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

`audit/cli.py` (both at repo root and under `backend/heretek_swarm/audit/`) contains argparse defaults hardcoding `heretek-swarm/heretek_swarm` as the scan directory. These are runtime defaults, not build/CI paths, and were intentionally deferred. The repo-root copy of `audit/cli.py` and `triage_classifier.py` are stale files that predate the restructure.

## Follow-ups

S03 should verify a fresh clone passes the full test suite. The stale `audit/cli.py` and `triage_classifier.py` at the repo root should be cleaned up or moved in a follow-up.

## Files Created/Modified

None.
