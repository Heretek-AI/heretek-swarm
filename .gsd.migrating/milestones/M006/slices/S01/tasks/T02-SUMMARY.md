---
id: T02
parent: S01
milestone: M006
key_files:
  - .gsd/milestones/M006/slices/S01/IMPORT_MAP.md
key_decisions:
  - IMPORT_MAP.md uses YAML blocks within Markdown for dual human-readability and machine-parsability
  - Subpackage dependency graph uses 'depends_on: []' convention to mark leaf packages
  - Per-file import catalog focuses on key architectural files rather than listing all 424 files individually
duration: 
verification_result: passed
completed_at: 2026-05-12T03:11:19.289Z
blocker_discovered: false
---

# T02: Generated complete import dependency map at IMPORT_MAP.md covering all 429 Python files: subpackage dependency graph, per-file import catalog for key files, test import analysis, relative import patterns, external dependency breakdown, dead/redundant import path identification, cycle detection, CI/workflow impact list, and leaf package enumeration for safe extraction ordering.

**Generated complete import dependency map at IMPORT_MAP.md covering all 429 Python files: subpackage dependency graph, per-file import catalog for key files, test import analysis, relative import patterns, external dependency breakdown, dead/redundant import path identification, cycle detection, CI/workflow impact list, and leaf package enumeration for safe extraction ordering.**

## What Happened

Ran AST-based import analysis across all 429 Python files in heretek_swarm/, tests/, and src/. Built a comprehensive IMPORT_MAP.md organized into 10 sections:

1. **Executive Summary** — 424 files with imports, 260 distinct internal modules, 91 external targets
2. **Subpackage Dependency Graph** — YAML-structured mapping of all 40 subpackages showing which packages depend on which, with centrality ranking (api=26, actors=20, runtime=19)
3. **Per-File Import Catalog** — Detailed import analysis for 13 key files including __init__.py, cli.py, api/main.py, runtime/autonomous_runtime.py, orchestration/heavyswarm.py, and the critical src/cli.py boundary file
4. **Test File Imports** — All 16 test files cataloged with their heretek_swarm import targets
5. **Relative Import Patterns** — runtime (33), api (25), actors (24) are the heaviest users
6. **External Dependencies** — typing (297), structlog (243), datetime (212) lead; framework deps (fastapi, sqlalchemy, nats, redis, click) identified for CI impact
7. **Dead/Redundant Import Paths** — Identified: duplicate import blocks in cli.py, legacy shim chain validation.py→mixins/validation.py, cli/__init__→_cli_module proxy, orphan handoff_handlers.py
8. **Cycle Detection** — No bidirectional cycles found; 3 potential transitive cycles documented
9. **CI/Workflow Impact List** — 8 config files with path references that need updates if heretek_swarm moves
10. **Leaf Packages** — 21 pure leaf packages identified for safe independent extraction

## Verification

Verified IMPORT_MAP.md exists (24,007 bytes) with 63 occurrences of "depends_on:" confirming structured dependency data. Verified FILE_INVENTORY.md from T01 is intact (210,506 bytes, 856 type entries, 856 path entries). All grep patterns confirmed using bash shell to avoid Windows `test` command incompatibility.

## Verification Evidence

| # | Command | Exit Code | Verdict | Duration |
|---|---------|-----------|---------|----------|
| 1 | `ls -la .gsd/milestones/M006/slices/S01/IMPORT_MAP.md && grep -c "depends_on:" .gsd/milestones/M006/slices/S01/IMPORT_MAP.md` | 0 | ✅ pass | 45ms |
| 2 | `ls -la .gsd/milestones/M006/slices/S01/FILE_INVENTORY.md && grep -c "type:" .gsd/milestones/M006/slices/S01/FILE_INVENTORY.md && grep -c "path:" .gsd/milestones/M006/slices/S01/FILE_INVENTORY.md` | 0 | ✅ pass | 52ms |

## Deviations

None. Task plan executed as specified.

## Known Issues

None.

## Files Created/Modified

- `.gsd/milestones/M006/slices/S01/IMPORT_MAP.md`
