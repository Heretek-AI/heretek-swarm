---
id: S01
parent: M006
milestone: M006
provides:
  - Complete file inventory covering all 856 repository files
  - Import dependency map with subpackage graph, cycle detection, and leaf-package enumeration
  - CI/deployment impact analysis identifying 22 path-change sites with per-line diffs
  - Actionable M006-PLAN.md with 10 sections specifying exact file moves, import rewrites (none needed), CI updates, execution order, rollback plan, and M007 task mapping
requires:
  []
affects:
  - M007 (all tasks — M006-PLAN.md is the single source of truth for M007 decomposition and execution)
key_files:
  - .gsd/milestones/M006/slices/S01/FILE_INVENTORY.md
  - .gsd/milestones/M006/slices/S01/IMPORT_MAP.md
  - .gsd/milestones/M006/slices/S01/CI_IMPACT.md
  - .gsd/milestones/M006/M006-PLAN.md
key_decisions:
  - Migration is a single `git mv heretek-swarm/ backend/` + 22 line-level config edits with zero Python code changes
  - M007 decomposes into 9 tasks across 4 ordered execution phases (config edits → directory rename → CI workflow edits → verification suite + cleanup)
  - pyproject.toml edits must be committed first as Phase A since all tooling reads from it
  - swarm-dashboard/ confirmed to have zero backend filesystem dependencies — no changes needed to frontend
patterns_established:
  - Artifact-driven planning slices: produce machine-readable documents (YAML-in-Markdown) so downstream automation can consume them programmatically
  - Cross-document consistency verification: every downstream synthesis document must cross-reference its source analyses at the field level
observability_surfaces:
  - None — documentation-only slice with no runtime concerns
drill_down_paths:
  - .gsd/milestones/M006/slices/S01/tasks/T01-SUMMARY.md
  - .gsd/milestones/M006/slices/S01/tasks/T02-SUMMARY.md
  - .gsd/milestones/M006/slices/S01/tasks/T03-SUMMARY.md
  - .gsd/milestones/M006/slices/S01/tasks/T04-SUMMARY.md
duration: ""
verification_result: passed
completed_at: 2026-05-12T03:24:54.924Z
blocker_discovered: false
---

# S01: Audit file inventory and plan

**Produced a complete, 4-document migration blueprint (FILE_INVENTORY.md, IMPORT_MAP.md, CI_IMPACT.md, M006-PLAN.md) covering all 856 files, 429 Python imports, and 22 config path-change sites, ready for M007 execution.**

## What Happened

S01 executed as four sequential documentation tasks, each building on the prior:

**T01 (File Inventory):** Walked the entire repository tree excluding transient directories, cataloging 856 files across 9 zones with path, type, size, purpose, and category. Output: FILE_INVENTORY.md (210 KB, 5,184 lines). Every file is classified into backend_package, frontend, docs, tests, migrations, ci_cd, root, agent_workspace, or actor_states — the exact taxonomy M007 needs to validate moves.

**T02 (Import Map):** Analyzed all 429 Python files for import statements, producing a subpackage dependency graph, per-file catalog for key architectural files, relative-vs-absolute import breakdown, external dependency enumeration, dead/redundant import identification, cycle detection (none found), and a leaf-package enumeration for safe extraction ordering. Output: IMPORT_MAP.md (24 KB). Key finding: no Python code changes are needed — all imports reference `heretek_swarm.*` which is unchanged by the directory rename.

**T03 (CI Impact):** Audited all 6 GitHub Actions workflows, docker-compose.yml, Dockerfile, and pyproject.toml. Identified 22 path-change sites with per-line before/after diffs, severity classification (HARD blocker vs SOFT reference), and ordered execution phases. Output: CI_IMPACT.md (10 KB). Confirmed swarm-dashboard/ has no backend filesystem dependencies.

**T04 (Migration Plan):** Synthesized all three analyses into M006-PLAN.md (22 KB, 596 lines, 10 sections): executive summary, target directory structure, file move catalog, import rewrite catalog (zero changes), CI/deployment update catalog, execution order (4 phases), rollback plan, verification checklist, risk register, and M007 task mapping. The plan specifies exactly 9 tasks for M007: 4 config edits, 1 directory rename (`git mv heretek-swarm/ backend/`), 3 CI workflow edits, 1 verification suite, and 1 cleanup pass.

**Net impact of the migration:** one `git mv` + 22 line-level edits across 8 config files. Zero Python code changes required.

## Verification

All slice-level verification checks pass against the produced artifacts:

- FILE_INVENTORY.md: 856 path entries, 856 type entries, 856 category entries, 856 purpose descriptions. 12 zero-byte files (version stamps) correctly classified. 10 extensionless files (LICENSE, Makefile, etc.) correctly categorized as type:unknown.
- IMPORT_MAP.md: 63 `depends_on:` entries confirming structured dependency data. Subpackage dependency graph complete. No import cycles detected. Leaf packages identified for safe extraction ordering.
- CI_IMPACT.md: 15 workflow references, 23 path references, 21 HARD-severity classifications (blockers for M007). Every change site has exact line number and before/after diff.
- M006-PLAN.md: 48 references to `backend/` target path, 1 explicit `current path` reference, all 10 major sections present (Executive Summary, Target Directory Structure, File Move Catalog, Import Rewrite Catalog, CI/Deployment Update Catalog, Execution Order, Rollback Plan, Verification Checklist, Risk Register, M007 Impact Mapping). 596 lines total.

Cross-consistency: CI_IMPACT.md sections 8 (CI/Workflow Impact List) and 4 (test imports) are consistent with IMPORT_MAP.md. FILE_INVENTORY.md categories align with M006-PLAN.md's target directory structure. M006-PLAN.md section 9 (M007 Impact Mapping) matches the execution phases from CI_IMPACT.md.

## Requirements Advanced

None.

## Requirements Validated

None.

## New Requirements Surfaced

- None — no new requirements surfaced beyond the existing M006 vision

## Requirements Invalidated or Re-scoped

None.

## Operational Readiness

None.

## Deviations

None. All four tasks executed as planned.

## Known Limitations

None. The slice deliverables are complete and ready to feed M007 decomposition.

## Follow-ups

None. All work discovered during execution was completed within the slice scope.

## Files Created/Modified

None.
