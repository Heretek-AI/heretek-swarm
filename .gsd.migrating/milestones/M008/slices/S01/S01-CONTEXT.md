---
id: S01
milestone: M008
status: ready
---

# S01: Purge Tracked Garbage Files — Context

## Goal

Delete 13 tracked garbage files from the repo root (12 `=*.0` pip build artifacts + 1 `0` grep-redirect artifact) via `git rm` and prevent recurrence with a `.gitignore` rule — leaving `git status` clean for those patterns and `ls` returning nothing.

## Why this Slice

These 13 files are visible tracked garbage at the repo root — every developer and every tool sees them. They've been deferred since M006/M007. Purging them first (risk: Low) clears the ground for S02–S05 without touching any code. It's the quickest, safest win in M008 and removes noise that could distract from the higher-risk stale-root-file resolution in S02.

## Scope

### In Scope

- `git rm` all 13 tracked garbage files in a single commit:
  - 12 `=*.0` files: `=0.2.0`, `=0.23.0`, `=1.1.0`, `=1.8.0`, `=2.3.0`, `=24.0.0`, `=3.12.0`, `=3.5.0`, `=4.0.0`, `=4.1.0`, `=6.98.0`, `=8.0.0`
  - 1 `0` file (25-byte grep output artifact: `0 matches for '"current'`)
- Verify `=1.8.0` content before deletion (confirmed: 439 lines of pip install build log, zero code/secrets/config)
- Run a broader audit scan of root-level files for additional suspicious artifacts; log findings
- Add `=*` pattern to root `.gitignore` to prevent future pip-build garbage from being tracked
- Verify post-deletion: `git status` shows no `=*.0` or `0` files; `ls =* 0` returns nothing

### Out of Scope

- Deleting untracked files (`pytest_stdout.txt`, `pytest_stderr.txt`, `tmpku_9ys71.env`) — these are not in git; noted for potential future cleanup
- Adding `.gitignore` rules beyond `=*`
- Any code or config changes — pure file deletion only
- Running pytest/ruff (sandbox limitation; deferred to S05 / CI)

## Constraints

- **Must use `git rm`** — plain `rm` leaves files tracked in the index and creates a dirty working tree
- **Single commit** — all 13 files deleted together; no split needed since `=1.8.0` content has been verified safe
- **Sandbox cannot run pip/pytest/ruff** — verification is static (files absent from git index and filesystem)
- **No functional code impact** — these files have zero imports, references, or dependencies from any live code

## Integration Points

### Consumes

- `git index` — the 13 tracked files to be removed
- Root `.gitignore` — to append the `=*` prevention rule
- Root filesystem — for post-deletion `ls` verification

### Produces

- Clean git index — no `=*.0` or `0` files tracked
- Updated `.gitignore` — `=*` rule appended (with comment)
- Audit note — log of any additional suspicious root artifacts found (for potential future slice)

## Open Questions

- None — all decisions resolved during context interview. The `=1.8.0` content has been verified; the broader audit found no additional tracked garbage; the `.gitignore` prevention rule is confirmed.
