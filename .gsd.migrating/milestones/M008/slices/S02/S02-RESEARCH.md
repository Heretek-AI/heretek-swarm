# S02: Resolve stale root files — Research

**Date:** 2026-05-12

## Summary

S02 targets four stale root files and their empty parent directory: `triage_classifier.py`, `audit/cli.py`, `audit-report.md`, `triage_data.json`, and the root `audit/` directory. All four are tracked in git and have working tree modifications (whitespace/line-ending changes: 470+470 lines diff on triage_classifier.py, 112+112 on audit/cli.py). None of these files are imported or referenced by any code in `backend/`. The root `audit/` directory contains only `cli.py` with no `__init__.py`, making it a non-package directory that cleanly deletes.

**Recommendation: Delete all four files via `git rm`, then remove the empty `audit/` directory.** No code needs to be preserved — `audit/cli.py` is fully superseded by the canonical `backend/heretek_swarm/audit/cli.py`, and `triage_classifier.py` was a one-off tool whose audit run is long complete.

## Implementation Landscape

### Files

| File | Status | What To Do |
|------|--------|-----------|
| `triage_classifier.py` (16KB) | Tracked; one-off AST classifier | `git rm triage_classifier.py` — one-off tool for completed audit run; zero references anywhere in codebase; stale `heretek-swarm/` path in `SRC_ROOT` |
| `audit/cli.py` (3KB) | Tracked; stale root audit CLI | `git rm audit/cli.py` — superseded by `backend/heretek_swarm/audit/cli.py` which has functional improvements (imports `group_by_severity`, `DEFAULT_EXTENSIONS`); zero imports from this file |
| `audit-report.md` (71KB) | Tracked; stale audit report | `git rm audit-report.md` — tightly coupled to `triage_classifier.py` as its input; no code reads it |
| `triage_data.json` (173KB) | Tracked; stale triage output | `git rm triage_data.json` — tightly coupled to `triage_classifier.py` as its output; no code reads it |
| `audit/` directory | Contains only `cli.py`, no `__init__.py` | `rmdir audit/` (or `git clean -fd audit/` after the tracked file is removed) |

### Build Order

Single atomic operation — all four files are independent of each other:

1. `git rm triage_classifier.py audit/cli.py audit-report.md triage_data.json` — removes all four from git index and disk
2. `rmdir audit/` or `git clean -fd audit/` — removes the now-empty directory
3. Commit with message: `chore: Remove stale root audit files (triage_classifier, audit/cli, report, triage_data)`

### Verification Approach

```bash
# After git rm:
git status --short                          # Should show no M or ?? for these files
git ls-files triage_classifier.py audit/cli.py   # Should return nothing
git ls-files audit-report.md triage_data.json    # Should return nothing
test -f triage_classifier.py && echo "STILL EXISTS" || echo "REMOVED"  # Should say REMOVED
```

## Code Comparison: stale vs canonical audit CLI

| Aspect | `audit/cli.py` (stale) | `backend/.../audit/cli.py` (canonical) |
|--------|----------------------|--------------------------------------|
| sys.path | Adds `heretek-swarm/` (broken after M007) | Adds correct path |
| Extensions | Hardcoded `{".py", ".js", ...}` | Imports `DEFAULT_EXTENSIONS` from `stub_patterns` |
| Report grouping | No `group_by_severity` | Imports `group_by_severity` from `report.py` |
| Default directory | `"heretek-swarm/heretek_swarm"` (stale) | Same stale default (harmless; overridable) |

The canonical version is strictly better. The stale version would be broken if run today (broken sys.path).

## Code Comparison: triage_classifier.py

- 330-line standalone script with `parse_audit_report()`, `classify_finding()`, `build_triage_report()`, `main()`
- Path: `SRC_ROOT = ROOT / "heretek-swarm" / "heretek_swarm"` — **broken** after M007 restructure
- Zero references anywhere in the codebase (confirmed via grep)
- One-off tool for a specific audit run that produced `triage_data.json`
- The capability (AST-based stub classification) is not needed going forward — the audit pass is complete

## Constraints

- **`git rm` is required** — all four files are tracked in git index (confirmed by `git status` showing ` M` and `git diff --stat` showing actual diffs). `rm` alone would leave them in the index as deleted-untracked, causing git status noise.
- **git status shows working tree modifications** on all four files (470+470 lines on triage_classifier.py, 112+112 on audit/cli.py). These are presumably whitespace/line-ending changes. They do not affect the deletion decision — there is no unique content to rescue.
- **No code imports from these files** — zero grep hits for `triage_classifier`, `audit-report`, or `triage_data` across the entire codebase. Zero files in `backend/` import from the stale `audit/cli.py`.
- **Root `audit/` is a plain directory, not a package** — no `__init__.py`. Cleanly removed with `rmdir`.

## Don't Hand-Roll

N/A — this is pure deletion with no replacement code needed.

## Common Pitfalls

- **`rm` without `git rm`** — leaves files in the git index as "deleted but not staged." Always use `git rm` for tracked files.
- **Forgetting the data artifacts** — `audit-report.md` and `triage_data.json` are easy to miss since they're not Python files. They must be deleted together with the classifier.
- **Leaving the empty `audit/` directory** — `git rm` removes the file but git won't remove the directory itself. Explicit `rmdir` or `git clean -fd` is needed.

## Open Risks

None. The S02-CONTEXT.md assessment is confirmed by the research:
- `triage_classifier.py` → Delete (one-off tool, broken paths, zero refs)
- `audit/cli.py` → Delete (superseded by canonical version with more imports)
- `audit-report.md` + `triage_data.json` → Bundle-delete (tightly coupled, zero refs)
