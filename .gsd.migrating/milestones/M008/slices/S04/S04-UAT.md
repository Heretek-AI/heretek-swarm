# S04: S04 — UAT

**Milestone:** M008
**Written:** 2026-05-12T23:32:47.329Z

## UAT Type

- UAT mode: artifact-driven
- Why this mode is sufficient: All changes are in comments/docstrings only — no runtime behavior is affected. Static grep verification is the definitive proof.

## Preconditions

- Repository is checked out at `C:/Users/Derek/Desktop/heretek-swarm`
- `backend/heretek_swarm/` directory exists

## Smoke Test

Run `grep -rn 'src/' backend/heretek_swarm/ --include='*.py'` — should produce no output related to stale directory paths.

## Test Cases

### 1. Zero stale src/ references in source tree

1. Execute: `grep -rn 'src/' backend/heretek_swarm/ --include='*.py'`
2. **Expected:** No matches for stale directory path references (e.g., `src/heretek_swarm/api/main.py`, `src/heretek_swarm/actors/`)

### 2. All 4 files show correct backend/ replacements

1. Check `backend/heretek_swarm/api/main.py` — project-root calculation comment references `backend/heretek_swarm/api/main.py`
2. Check `backend/heretek_swarm/memory/__init__.py` — no stale "legacy src/" reference
3. Check `backend/heretek_swarm/runtime/registry_enhanced.py` — discovery and defaults docstrings reference `backend/heretek_swarm/actors/`
4. Check `backend/heretek_swarm/tools/__init__.py` — module docstring references `backend/heretek_swarm/tools`
5. **Expected:** Each file shows its updated `backend/` path instead of the old `src/` path

### 3. No functional code was changed

1. Run `ruff check backend/heretek_swarm/` — no new lint errors
2. Run `pytest` on the affected modules — tests pass
3. **Expected:** Zero regressions from the comment-only changes

## Edge Cases

### What about legitimate 'src/' references?

1. Check any remaining grep matches for `src/`
2. **Expected:** If any remain, they should be in variable names, RST cross-references, or other non-path contexts (e.g., `resource`, `describe`)

## Failure Signals

- Any `grep` match for `src/heretek_swarm/` in a Python comment or docstring
- Lint failure related to modified files
- Test failure in affected modules

## Not Proven By This UAT

- No runtime validation — all changes are comment-only
- Does not verify documentation files (covered by S03)
- Does not verify stale references in test files outside `backend/heretek_swarm/`
