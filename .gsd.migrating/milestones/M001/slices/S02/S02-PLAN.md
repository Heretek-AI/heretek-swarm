# S02: Delete obsolete actor copies and fix broken imports

**Goal:** Delete all 10 shim files and fix any broken import references so actor imports resolve cleanly.
**Demo:** All actor imports resolve from one canonical location

## Must-Haves

- Complete the planned slice outcomes.

## Verification

- Run the task and slice verification checks for this slice.

## Tasks

- [x] **T01: Delete 10 shim actor files** `est:15m`
  Delete the 10 shim files identified by S01's audit. These are flat .py files that re-export from their matching subpackages and serve no purpose now that S03 will wire the __init__.py re-export surface. Do NOT delete explorer.py — it has a subpackage but the flat file is a full standalone ~1318-line implementation.
  - Files: `heretek_swarm/actors/`
  - Verify: ls heretek_swarm/actors/*.py | wc -l returns 20

- [x] **T02: Fix imports referencing deleted shims** `est:20m`
  Scan the entire codebase for any import statements that reference the 10 deleted shim files directly (e.g. `from heretek_swarm.actors import arbiter`). Update those imports to use the canonical subpackage path (e.g. `from heretek_swarm.actors.arbiter import ArbiterAgent`) so they resolve from the authoritative subpackage instead.
  - Files: `heretek_swarm/`, `tests/`
  - Verify: python -c "import heretek_swarm.actors" exits 0

## Files Likely Touched

- heretek_swarm/actors/
- heretek_swarm/
- tests/
