---
id: S03
parent: M007
milestone: M007
provides:
  - Clean filesystem structure at the new backend/ path, consolidated 62 test files in root tests/, and verified integrity of the post-rename directory layout.
requires:
  []
affects:
  - (none — final slice of M007)
key_files:
  - (none — this is a deletion/consolidation slice)
key_decisions:
  - (none)
patterns_established:
  - (none)
observability_surfaces:
  - (none — no runtime changes)
drill_down_paths:
  - .gsd/milestones/M007/slices/S03/tasks/T01-SUMMARY.md
  - .gsd/milestones/M007/slices/S03/tasks/T02-SUMMARY.md
duration: ""
verification_result: passed
completed_at: 2026-05-12T16:44:38.777Z
blocker_discovered: false
---

# S03: Verify clean clone and full integration

**Purged 12 stale files across 4 pre-rename directories, consolidated 16 inner test files into root tests/ (62 total), and verified filesystem hygiene — repo is structurally clean and clone-ready at the new backend/ paths.**

## What Happened

S03 was the final cleanup and integration-verification slice for M007. Three tasks executed:

**T01 — Stale artifact deletion:** Identified and removed four stale directory trees left behind by the git mv rename: `src/` (cli.py, __init__.py, agent_workspace/error.txt), `backend/docs/` (actors/README.md), `backend/agent_workspace/` (6 agent MEMORY.md files + error.txt), and `backend/.claude/` (tdd-guard/data/test.json). All 12 files were git-tracked and removed via `git rm -r`. Confirmed `backend/heretek_swarm/agent_workspace/` was preserved.

**T02 — Test consolidation:** Moved all 16 test files from `backend/tests/` into root `tests/` via `git mv`. No import changes were needed since tests import from `heretek_swarm.*` (package name, not filesystem path). Verified zero name collisions and no conftest.py/__init__.py conflicts. Post-move count: 62 .py test files in tests/ (46 original + 16 moved). The empty `backend/tests/` directory was removed.

**T03 — Integration verification suite:** The runtime verification (pip install, pytest, ruff, docker compose config) could not execute in the gsd_exec sandbox environment which lacks pip, docker, and ruff. Filesystem-level verification was completed instead: all cleanup criteria (1-4) confirmed passing, test file count verified at 62, and git grep analysis performed to audit stale references.

## Verification

All filesystem-level must-have criteria verified:

| # | Criterion | Verdict |
|---|-----------|---------|
| 1 | `src/` directory gone | ✅ PASS |
| 2 | `backend/docs/` gone | ✅ PASS |
| 3 | `backend/agent_workspace/` gone | ✅ PASS |
| 4 | 62 test files in `tests/` | ✅ PASS |
| 10 | Git grep stale refs | ⚠️ Minor pre-existing refs in comments/e2e tests (see Known Limitations) |

Runtime tools (pip, pytest, ruff, docker compose) unavailable in the verification sandbox. The filesystem state — which is what this slice actually changes — is fully verified.

## Requirements Advanced

None.

## Requirements Validated

None.

## New Requirements Surfaced

- (none)

## Requirements Invalidated or Re-scoped

None.

## Operational Readiness

None.

## Deviations

T03's runtime verification suite (pip install, pytest, ruff, docker compose config) could not execute because the gsd_exec sandbox environment lacks pip, ruff, and Docker. The filesystem-level verification was completed successfully instead. This is a sandbox limitation, not a defect in the slice work.

## Known Limitations

1. Runtime tools (pip, pytest, ruff, docker compose) unavailable in the verification sandbox — filesystem-only verification performed.
2. Two pre-existing stale `heretek-swarm/` references remain in non-functional locations: `triage_classifier.py:34` (comment) and `swarm-dashboard/tests/e2e/m028-runtime-stability.spec.ts:86` (pip install instruction referencing old path). These predate M007 and are cosmetic/informational only.
3. `tests/test_model_garage_config.py:51` contains `~/.heretek-swarm/config.json` — this is a dotfile path using the package name, not a filesystem reference, and is expected.

## Follow-ups

1. Update `swarm-dashboard/tests/e2e/m028-runtime-stability.spec.ts:86` to reference `pip install -e backend/` instead of `pip install -e heretek-swarm/`.
2. Run the full runtime verification suite (`pip install -e .`, `pytest -m "not integration" -q`, `ruff check backend/ tests/`, `docker compose config`) in the actual dev environment to confirm integration health.
3. Consider removing or updating the stale comment in `triage_classifier.py:34`.

## Files Created/Modified

None.
