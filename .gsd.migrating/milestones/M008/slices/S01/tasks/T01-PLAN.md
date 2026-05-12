---
estimated_steps: 1
estimated_files: 1
skills_used: []
---

# T01: Git-rm tracked garbage files and add =* gitignore prevention rule

All 13 files have been verified as safe-to-delete build artifacts (pip install logs, grep output) and are already deleted from disk but still tracked in the git index. A single git rm + .gitignore update + commit atomic operation is sufficient. The 12 =*.0 files were produced by pip builds; the 0 file is a 25-byte grep redirect artifact. No code, imports, or configuration references any of these files.

## Inputs

- None specified.

## Expected Output

- `.gitignore`

## Verification

git ls-files '=*' | wc -l returns 0; git ls-files '0' | wc -l returns 0; git status --short shows no =* or 0 files; grep -q '^=\*$' .gitignore returns success
