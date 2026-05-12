# S01: Purge tracked garbage files — UAT

**Milestone:** M008
**Written:** 2026-05-12T20:58:37.565Z

## UAT: Purge tracked garbage files

**Demo condition:** git status shows no tracked =*.0 or 0 garbage files at repo root; ls returns 'No such file' for the glob pattern.

### Verification Steps

1. `git ls-files '=*' | wc -l` → **0** (no =* files tracked)
2. `git ls-files '0' | wc -l` → **0** (no '0' file tracked)
3. `ls =*` → **No such file or directory** (filesystem clean)
4. `ls 0` → **No such file or directory** (filesystem clean)
5. `grep -q '^=\*$' .gitignore` → **success** (prevention rule exists)
6. `git diff --cached --name-status` → only D (delete) lines for the 13 files
7. `git status --porcelain` → no new/untracked =* or 0 files

All checks pass. Slice goal met.
