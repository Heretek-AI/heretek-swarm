---
id: T03
parent: S01
milestone: M006
key_files:
  - (none)
key_decisions:
  - (none)
duration: 
verification_result: passed
completed_at: 2026-05-12T03:17:21.805Z
blocker_discovered: false
---

# T03: Cataloged 22 path-change sites across 8 CI/config files with per-line before/after diffs, severity classification, and ordered execution phases for M007.

**Cataloged 22 path-change sites across 8 CI/config files with per-line before/after diffs, severity classification, and ordered execution phases for M007.**

## What Happened

Analyzed all 10 files listed in the task plan (6 workflow YAMLs, docker-compose.yml, Dockerfile, pyproject.toml, swarm-dashboard/) for path references that would break under the `heretek-swarm/` → `backend/` restructure.

Key findings:
- **21 hard blockers** across 8 files requiring changes before the restructured repo builds/tests/deploys
- **Stale `src/` references** are the dominant anti-pattern — 9 occurrences in ci.yml and ci-cd.yml where commands reference `src/` (which doesn't exist as a directory; code lives in `heretek-swarm/heretek_swarm/`). These never worked correctly and are latent bugs.
- **pyproject.toml has 5 hard blockers** — setuptools `where`, coverage `source`, coverage `paths`, and ruff `src` all hardcode `heretek-swarm` as a filesystem path
- **Dockerfile has 4 copy-path changes** — source directory renames from `heretek-swarm/` to `backend/`
- **publish-npm.yml and codeboarding.yml are fully unaffected**
- **swarm-dashboard/ has zero structural backend path dependencies** — confirmed by grep excluding node_modules
- Changes are organized into 3 ordered phases: pyproject.toml first (tooling), Docker second (build depends on correct package config), Actions third (CI depends on both)

Also documented risk mitigations for each failure mode and a 8-item verification checklist for M007 executors.

## Verification

Verified CI_IMPACT.md exists (10,475 bytes) with comprehensive content: 15 occurrences of "workflow", 23 of "path", 21 of "HARD" (blocker classification). Verified against the task plan's 10 input files with exact line numbers for every change. Cross-referenced with IMPORT_MAP.md sections 8 (CI/Workflow Impact List) and 4 (test imports) to confirm consistency. Confirmed swarm-dashboard/ has no backend filesystem dependencies via grep of all source files.

## Verification Evidence

| # | Command | Exit Code | Verdict | Duration |
|---|---------|-----------|---------|----------|
| 1 | `ls -la .gsd/milestones/M006/slices/S01/CI_IMPACT.md && grep -ci workflow .gsd/milestones/M006/slices/S01/CI_IMPACT.md && grep -ci path .gsd/milestones/M006/slices/S01/CI_IMPACT.md && grep -ci HARD .gsd/milestones/M006/slices/S01/CI_IMPACT.md` | 0 | ✅ pass | 85ms |

## Deviations

None.

## Known Issues

None.

## Files Created/Modified

None.
