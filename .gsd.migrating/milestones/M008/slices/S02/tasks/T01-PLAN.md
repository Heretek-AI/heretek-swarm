---
estimated_steps: 11
estimated_files: 4
skills_used: []
---

# T01: git rm stale root files and remove empty audit/ directory

Why: All four files are tracked in git index with working tree modifications (whitespace/line-ending changes). `rm` alone leaves them tracked as 'deleted but not staged.' Must use `git rm` for a clean index. The audit/ directory contains only cli.py; after deletion it becomes an empty non-package directory that should be removed.

Files: triage_classifier.py, audit/cli.py, audit-report.md, triage_data.json, audit/

Do:
1. `git rm triage_classifier.py audit/cli.py audit-report.md triage_data.json` — removes all four from git index and disk atomically
2. `rmdir audit/` or `rm -rf audit/` — removes the now-empty directory
   (Note: audit/ is a plain directory with no __init__.py, so it's not a Python package)
3. Verify via `git status --short` that only the expected deletions appear

Constraints:
- Must use `git rm`, not `rm` — all four files are tracked in git index
- Do NOT touch backend/heretek_swarm/audit/ — the canonical module is untouched
- No new files, no new code, no path reference fixes (those are S03/S04)

## Inputs

- `triage_classifier.py`
- `audit/cli.py`
- `audit-report.md`
- `triage_data.json`

## Expected Output

- `triage_classifier.py`
- `audit/cli.py`
- `audit-report.md`
- `triage_data.json`

## Verification

git ls-files triage_classifier.py audit/cli.py audit-report.md triage_data.json 2>&1; echo '---'; test -f triage_classifier.py && echo EXISTS || echo REMOVED; test -f audit/cli.py && echo EXISTS || echo REMOVED; test -f audit-report.md && echo EXISTS || echo REMOVED; test -f triage_data.json && echo EXISTS || echo REMOVED; test -d audit && echo DIR EXISTS || echo DIR REMOVED
