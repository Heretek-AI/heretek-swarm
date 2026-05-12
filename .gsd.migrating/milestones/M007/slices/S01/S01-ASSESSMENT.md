---
sliceId: S01
uatType: artifact-driven
verdict: PASS
date: 2026-05-12T12:25:00.000Z
---

# UAT Result — S01: Rename heretek-swarm/ to backend/ via git mv

## Checks

| # | Check | Mode | Result | Notes |
|---|-------|------|--------|-------|
| 1 | Smoke test: `backend/heretek_swarm` exists | artifact | PASS | `test -d backend/heretek_swarm` returned true |
| 2.1 | `backend/heretek_swarm/__init__.py` exists | artifact | PASS | Regular file present |
| 2.2 | `backend/tests/` exists | artifact | PASS | Directory present |
| 2.3 | `backend/Dockerfile` exists | artifact | PASS | Regular file present |
| 2.4 | `backend/docs/` exists | artifact | PASS | Directory present |
| 2.5 | `backend/agent_workspace/` exists | artifact | PASS | Directory present |
| 3 | Old path `heretek-swarm/` is gone | artifact | PASS | `test -e heretek-swarm` returned false |
| 4 | Git history preserved through rename (≥3 commits via `--follow`) | artifact | PASS | 5 commits visible: `2742c0a4` (rename), `e7acfdf4`, `e8c07c64`, `3f670b60`, `c640b926` (initial commit). The rename commit and 2+ prior commits are all traceable. |
| 5 | Zero code changes (R100 rename) | artifact | PASS | `git show --stat` on rename commit confirms: `463 files changed, 0 insertions(+), 0 deletions(-)` |
| 6.1 | `swarm-dashboard/` intact | artifact | PASS | Directory present |
| 6.2 | `docs/` intact | artifact | PASS | Directory present |
| 6.3 | `.github/` intact | artifact | PASS | Directory present |

## Overall Verdict

**PASS** — All 10 automatable checks passed. The `heretek-swarm/` → `backend/` git mv was a clean R100 rename: 463 files moved with zero content changes, full git history preserved and traceable via `--follow`, old path fully removed, and non-backend directories untouched.

## Notes

- The `gsd_exec` bash environment on Windows had issues with `for` loops over quoted paths and `wc -l` integer comparisons — both produced empty/null values. Individual `test -f`/`test -d` commands worked correctly. The git history check was verified by visually counting the 5 commits in the `git log --oneline --follow` output.
- All evidence aligns with the S01-SUMMARY.md verification results recorded earlier.
- No human follow-up required.
