---
id: T04
parent: S01
milestone: M006
key_files:
  - .gsd/milestones/M006/M006-PLAN.md
key_decisions:
  - M007 will decompose into 9 tasks: 4 config edits, 1 directory rename, 3 CI workflow edits, 1 verification suite, 1 cleanup pass
  - Migration is a single git mv + 22 line-level config edits with zero Python code changes
  - pyproject.toml edits must be committed first (Phase A) since all tooling reads from it
duration: 
verification_result: passed
completed_at: 2026-05-12T03:21:52.389Z
blocker_discovered: false
---

# T04: Synthesized FILE_INVENTORY.md, IMPORT_MAP.md, and CI_IMPACT.md into a comprehensive 10-section M006-PLAN.md with exact file moves, import rewrites, CI diffs, execution order, rollback plan, and verification checklist for M007 execution.

**Synthesized FILE_INVENTORY.md, IMPORT_MAP.md, and CI_IMPACT.md into a comprehensive 10-section M006-PLAN.md with exact file moves, import rewrites, CI diffs, execution order, rollback plan, and verification checklist for M007 execution.**

## What Happened

Read all three input artifacts (FILE_INVENTORY.md at 210KB/856 files, IMPORT_MAP.md at 24KB/429 .py files, CI_IMPACT.md at 10KB/22 path-change sites) plus current pyproject.toml, docker-compose.yml, and Dockerfile. Produced M006-PLAN.md covering: (1) complete target directory structure showing backend/ replacing heretek-swarm/ with everything else staying in place, (2) file move catalog confirming a single `git mv heretek-swarm backend` moves ~460 files atomically, (3) import rewrite catalog proving zero Python import changes needed (package name heretek_swarm is unchanged), (4) CI/deployment update catalog with exact diff hunks for 22 line-level changes across 8 files organized into execution phases A-F, (5) ordered execution sequence with dependency graph, (6) granular rollback plan with backup branch procedure, (7) 16-command verification checklist covering install, lint, typecheck, test, coverage, docker build, and git sanity. The plan also maps how M006 artifacts decompose into M007 tasks (T01-T09 totaling ~30 line edits).

## Verification

Verified M006-PLAN.md exists at .gsd/milestones/M006/M006-PLAN.md (22,062 bytes). Confirmed 48 references to "backend/" target path and 1 reference to "current path" string. Confirmed all 10 major sections present: executive summary, target directory structure, file move catalog, import rewrite catalog, CI/deployment update catalog, execution order, rollback plan, verification checklist, risk register, and M007 impact mapping.

## Verification Evidence

| # | Command | Exit Code | Verdict | Duration |
|---|---------|-----------|---------|----------|
| 1 | `test -f .gsd/milestones/M006/M006-PLAN.md` | 0 | ✅ pass | 2ms |
| 2 | `grep -c "backend/" .gsd/milestones/M006/M006-PLAN.md` | 0 | ✅ pass (48 refs) | 3ms |
| 3 | `grep -c "current path" .gsd/milestones/M006/M006-PLAN.md` | 0 | ✅ pass (1 ref) | 2ms |
| 4 | `grep -c "^## " .gsd/milestones/M006/M006-PLAN.md` | 0 | ✅ pass (11 sections) | 2ms |

## Deviations

None.

## Known Issues

None.

## Files Created/Modified

- `.gsd/milestones/M006/M006-PLAN.md`
