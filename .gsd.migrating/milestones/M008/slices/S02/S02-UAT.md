# S02: Resolve stale root files — UAT

**Milestone:** M008
**Written:** 2026-05-12T21:36:07.746Z
**Re-verified:** 2026-05-14

## UAT Type

- UAT mode: artifact-driven
- Why this mode is sufficient: This slice is purely about file deletion — no runtime code, no server, no UI. All verification is static: file existence, git tracking, and text search.

## Preconditions

- Repository is checked out with S01 (garbage file purge) already complete
- Working tree is at the commit where S02 deletions are staged but not yet committed

## Smoke Test

Run `git status --short` and confirm `D ` (deleted) entries exist for `triage_classifier.py`, `audit/cli.py`, `audit-report.md`, and `triage_data.json`.

## Test Cases

### 1. Files removed from git tracking

1. Run `git ls-files triage_classifier.py audit/cli.py audit-report.md triage_data.json`
2. **Expected:** Empty output — git no longer tracks any of the four files

### 2. Files removed from disk

1. For each file, run `test -f <filename>; echo $?`
2. **Expected:** Exit code 1 for all four files (NOT_FOUND)

### 3. Stale audit/ directory removed

1. Run `test -d audit; echo $?`
2. **Expected:** Exit code 1 — audit/ directory no longer exists at repo root

### 4. Canonical audit module intact

1. Run `ls backend/heretek_swarm/audit/`
2. **Expected:** All five files present: `__init__.py`, `cli.py`, `report.py`, `severity.py`, `stub_patterns.py`

### 5. No stale references in codebase

1. Run `grep -rn "triage_classifier\|triage_data\|audit-report" backend/`
2. **Expected:** Empty output — no code references deleted files

### 6. Files not retrievable from HEAD

1. Run `git show HEAD:triage_classifier.py 2>&1; echo $?`
2. **Expected:** Exit code > 0 — file no longer exists in HEAD (deleted and committed)

## Edge Cases

### Files restored from git history

1. Run `git show HEAD:triage_classifier.py > /tmp/test_restore.py 2>&1; echo $?`
2. **Expected:** Exit code > 0 (or file is empty) — git cannot retrieve the file from HEAD because it was deleted in a pending commit (note: files remain retrievable from prior commits; this is expected and acceptable)

## Failure Signals

- `test -f triage_classifier.py` succeeds — file still on disk (FAIL)
- `git ls-files triage_classifier.py` returns path — still tracked in index (FAIL)
- `test -d audit` succeeds — directory not cleaned up (FAIL)
- `ls backend/heretek_swarm/audit/` shows missing files — canonical module damaged (FAIL)
- `grep` finds `triage_classifier` in `backend/` code — stale import/reference (FAIL)

## Not Proven By This UAT

- pytest passes (deferred to dev environment; S05 will verify)
- ruff check passes (deferred to dev environment; S05 will verify)
- CI workflows remain correct (S05 scope)
- No functional regression in audit module (static verification only; no runtime tests run)

## Re-verification Results (2026-05-14)

| # | Check | Result | Evidence |
|---|---|---|---|
| 1 | Files removed from git tracking | ✅ PASS | `git ls-files` returns empty for all four files |
| 2 | Files removed from disk | ✅ PASS | `test -f` returns 1 for all four files |
| 3 | Stale `audit/` dir removed | ✅ PASS | `test -d audit` returns 1 |
| 4 | Canonical audit module intact | ✅ PASS | All 5 files present in `backend/heretek_swarm/audit/` |
| 5 | No stale code references | ✅ PASS | Only match is docstring example in `cli.py` line 65 showing `--output audit-report.md` usage — not a stale import, just a usage example |
| 6 | Files not retrievable from HEAD | ✅ PASS | `git show HEAD:triage_classifier.py` exits 128 (fatal: path does not exist in HEAD) |

## Verdict

**✅ PASS** — All 6 verification checks pass. The docstring match in `cli.py:65` is a usage example showing `--output audit-report.md` as the output filename for the CLI command, not a stale import or functional reference to the deleted file. All stale root files are removed from disk, git tracking, and HEAD. The canonical `backend/heretek_swarm/audit/` module is intact.
