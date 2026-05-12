# S01: Audit file inventory and plan — UAT

**Milestone:** M006
**Written:** 2026-05-12T03:24:54.924Z

## UAT Type

- UAT mode: **artifact-driven**
- Why this mode is sufficient: This slice produces no code changes, no runtime behavior, and no deployed services. The four documents are the deliverables. Verification is done by inspecting document existence, structure completeness, and cross-document consistency.

## Preconditions

None. These are static documents readable from disk.

## Smoke Test

Open `.gsd/milestones/M006/M006-PLAN.md` and confirm it has all 10 sections listed in its table of contents.

## Test Cases

### 1. File inventory is complete and machine-readable

1. Verify `.gsd/milestones/M006/slices/S01/FILE_INVENTORY.md` exists and has 856 entries.
2. Confirm every entry has `path:`, `type:`, `category:`, and `purpose:` fields.
3. **Expected:** 856 entries × 4 fields = 3,424 field occurrences minimum. Categories span all 9 zones: backend_package, frontend, docs, tests, migrations, ci_cd, root, agent_workspace, actor_states.

### 2. Import map captures dependency structure

1. Open `.gsd/milestones/M006/slices/S01/IMPORT_MAP.md`.
2. Verify the subpackage dependency graph section shows which packages depend on which.
3. Verify the leaf-package enumeration section lists packages safe to move first.
4. **Expected:** Dependency graph uses `depends_on: []` convention for leaf packages. No circular imports reported.

### 3. CI impact analysis covers all configuration surfaces

1. Open `.gsd/milestones/M006/slices/S01/CI_IMPACT.md`.
2. Verify all 6 workflow files, docker-compose.yml, Dockerfile, and pyproject.toml are analyzed.
3. Verify every path change has a severity classification (HARD/SOFT).
4. **Expected:** At least 22 change sites identified. Every HARD change has exact line number and before/after diff.

### 4. Migration plan is actionably specific

1. Open `.gsd/milestones/M006/M006-PLAN.md`.
2. Verify Section 2 (File Move Catalog) enumerates exact paths.
3. Verify Section 4 (CI/Deployment Update Catalog) has per-file diffs.
4. Verify Section 6 (Execution Order) specifies phases with prerequisites.
5. Verify Section 8 (Verification Checklist) has concrete pass/fail checks.
6. **Expected:** All sections present. M007 task decomposition (Section 10) maps each execution phase to discrete tasks with estimates.

## Edge Cases

### Zero-byte and extensionless files

1. Check FILE_INVENTORY.md for files classified as type:0 or type:unknown.
2. **Expected:** Version-stamp files with numeric extensions (e.g. =0.2.0) correctly typed as `type:0`. Extensionless files (LICENSE, Makefile, etc.) correctly typed as `type:unknown`.

### Swarm-dashboard isolation

1. Verify CI_IMPACT.md confirms swarm-dashboard/ has no backend filesystem dependencies.
2. **Expected:** No path references from swarm-dashboard/ to heretek-swarm/ in import or file analysis.

## Failure Signals

- M006-PLAN.md missing from `.gsd/milestones/M006/`
- Fewer than 856 entries in FILE_INVENTORY.md
- `depends_on:` not present in IMPORT_MAP.md
- CI_IMPACT.md references fewer than 6 workflow files
- Cross-document inconsistency between CI_IMPACT.md and IMPORT_MAP.md section 8

## Not Proven By This UAT

- That the migration plan will execute without unforeseen blockers — the plan is a best-effort synthesis of static analysis; runtime or environment-specific issues may surface in M007.
- That all 856 files are correctly classified — purpose descriptions are heuristic-based and may need human correction.
- That import analysis has zero false negatives — only grep-based pattern matching was used, not AST parsing.
- That the rollback plan is sufficient for all failure modes — only the most likely rollback scenarios are covered.

## Notes for Tester

- All deliverables are Markdown documents with embedded YAML blocks for machine readability. Open them in any text editor or markdown viewer.
- M006-PLAN.md is the primary artifact; the other three are supporting evidence. Start there.
- The "current path" string appears once in M006-PLAN.md section 10 (M007 Impact Mapping context paragraph).
- No code was modified in this slice — only new documentation files were created under `.gsd/milestones/M006/`.
