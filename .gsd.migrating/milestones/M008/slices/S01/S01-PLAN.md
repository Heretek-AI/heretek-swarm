# S01: Purge tracked garbage files

**Goal:** Purge all 13 tracked garbage files (=*.0 pip artifacts + 0 grep artifact) from the repo root and prevent recurrence via a .gitignore rule.
**Demo:** git status shows no tracked =*.0 or 0 garbage files at repo root; ls returns 'No such file' for the glob pattern

## Must-Haves

- Complete the planned slice outcomes.

## Verification

- Run the task and slice verification checks for this slice.

## Tasks

- [x] **T01: Git-rm tracked garbage files and add =* gitignore prevention rule** `est:5m`
  All 13 files have been verified as safe-to-delete build artifacts (pip install logs, grep output) and are already deleted from disk but still tracked in the git index. A single git rm + .gitignore update + commit atomic operation is sufficient. The 12 =*.0 files were produced by pip builds; the 0 file is a 25-byte grep redirect artifact. No code, imports, or configuration references any of these files.
  - Files: `.gitignore`
  - Verify: git ls-files '=*' | wc -l returns 0; git ls-files '0' | wc -l returns 0; git status --short shows no =* or 0 files; grep -q '^=\*$' .gitignore returns success

- [x] **T02: Post-deletion verification: confirm clean index and filesystem** `est:3m`
  Run exhaustive verification commands to prove the slice goal is met. Check git index, filesystem, and git status. Log the audit finding for traceability.
  - Verify: All verification commands in the task plan pass with exit code 0

## Files Likely Touched

- .gitignore
