# S01: S01: Rename heretek-swarm/ to backend/ via git mv — UAT

**Milestone:** M007
**Written:** 2026-05-12T12:21:48.294Z

## UAT Type

- UAT mode: **artifact-driven** — purely mechanical filesystem rename with no runtime component
- Why this mode is sufficient: No code was changed; git tracked the rename as R100 (identical content). Verification is structural only.

## Preconditions

- Working directory: repo root (`C:/Users/Derek/Desktop/heretek-swarm`)
- Git history fully intact

## Smoke Test

```bash
ls -d backend/heretek_swarm && echo "PASS" || echo "FAIL"
```

Should output `PASS`.

## Test Cases

### 1. Verify new path exists with all expected content

1. Run: `ls backend/heretek_swarm/__init__.py backend/tests/ backend/Dockerfile backend/docs/ backend/agent_workspace/`
2. **Expected:** All five paths exist with no errors

### 2. Verify old path is gone

1. Run: `ls heretek-swarm/`
2. **Expected:** `No such file or directory` error

### 3. Verify git history preserved through rename

1. Run: `git log --oneline -5 --follow -- backend/heretek_swarm/__init__.py`
2. **Expected:** At least 3 commits visible, including the rename commit and prior commits

### 4. Verify zero code changes in the rename

1. Run: `git show --stat HEAD | grep "0 insertions.*0 deletions"`
2. **Expected:** Shows 0 insertions, 0 deletions

## Edge Cases

### Unmerged index state

If `.gsd.migrating/` has unmerged (UU) files, `git mv` will fail. Pre-resolve with `git add .gsd.migrating/`.

## Failure Signals

- `backend/heretek_swarm/` does not exist
- `heretek-swarm/` still exists on disk
- `git log --follow` on new path returns no results
- Import paths in Python files have been changed (they should NOT be — package name `heretek_swarm` is unchanged)

## Not Proven By This UAT

- All imports still resolve correctly (deferred to S02)
- CI workflows pass with new paths (deferred to S02)
- Full test suite passes (deferred to S02)
- Docker builds work (deferred to S02)
