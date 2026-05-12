# S02: Resolve stale root files

**Goal:** Delete both stale root files (triage_classifier.py, audit/cli.py) and their tightly-coupled data artifacts (audit-report.md, triage_data.json) after confirming all logic is superseded by backend/ equivalents or was a one-off tool with no ongoing value. Remove the now-empty audit/ directory.
**Demo:** Both stale root files (triage_classifier.py, audit/cli.py) are either git mv'd to backend/ canonical locations or deleted after confirming their logic is superseded by backend/ equivalents

## Must-Haves

- Both stale root files (triage_classifier.py, audit/cli.py) are deleted via git rm after confirming their logic is superseded by backend/ equivalents; data artifacts (audit-report.md, triage_data.json) are bundle-deleted as tightly-coupled inputs/outputs; the empty audit/ directory is removed. Verification: git ls-files returns nothing for all four files, test -f returns 1 (not found) for all four, test -d audit/ returns 1 (directory gone).

## Proof Level

- This slice proves: operational

## Integration Closure

No new wiring introduced. The canonical audit module at backend/heretek_swarm/audit/ is untouched and remains fully functional. No code in backend/ imported from any of the deleted files.

## Verification

- Run the task and slice verification checks for this slice.

## Tasks

- [x] **T01: git rm stale root files and remove empty audit/ directory** `est:10m`
  Why: All four files are tracked in git index with working tree modifications (whitespace/line-ending changes). `rm` alone leaves them tracked as 'deleted but not staged.' Must use `git rm` for a clean index. The audit/ directory contains only cli.py; after deletion it becomes an empty non-package directory that should be removed.
  - Files: `triage_classifier.py`, `audit/cli.py`, `audit-report.md`, `triage_data.json`
  - Verify: git ls-files triage_classifier.py audit/cli.py audit-report.md triage_data.json 2>&1; echo '---'; test -f triage_classifier.py && echo EXISTS || echo REMOVED; test -f audit/cli.py && echo EXISTS || echo REMOVED; test -f audit-report.md && echo EXISTS || echo REMOVED; test -f triage_data.json && echo EXISTS || echo REMOVED; test -d audit && echo DIR EXISTS || echo DIR REMOVED

- [x] **T02: Post-deletion verification and state persistence** `est:5m`
  Why: Systematically confirm the slice goal is met by running exhaustive static checks and logging verification evidence. This task is verification-only — it produces no new files, only assertion results.
  - Verify: git ls-files triage_classifier.py audit/cli.py audit-report.md triage_data.json | wc -l; test -f triage_classifier.py && echo 'FAIL: triage_classifier.py still exists' || echo 'PASS: triage_classifier.py removed'; test -f audit-report.md && echo 'FAIL: audit-report.md still exists' || echo 'PASS: audit-report.md removed'; test -f triage_data.json && echo 'FAIL: triage_data.json still exists' || echo 'PASS: triage_data.json removed'; test -d audit && echo 'FAIL: audit/ dir still exists' || echo 'PASS: audit/ dir removed'

## Files Likely Touched

- triage_classifier.py
- audit/cli.py
- audit-report.md
- triage_data.json
