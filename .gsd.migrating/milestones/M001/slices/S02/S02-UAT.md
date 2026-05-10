# S02: Delete obsolete actor copies and fix broken imports — UAT

**Milestone:** M001
**Written:** 2026-05-07T12:35:17.154Z

# UAT: S02 — Delete obsolete actor copies and fix broken imports

## Type
**Import resolution / file system cleanup** — verifies that actor imports resolve cleanly after shim deletion, and that pytest passes.

## Preconditions
- Python 3.11+ with heretek_swarm installed (editable or on PYTHONPATH)
- No deleted shim files remain in heretek_swarm/actors/
- S03 (wired __init__.py) may or may not be complete — this UAT only verifies pre-S03 state

## Test Cases

### T02-01: Import root actors module
**Steps:**
1. `python -c "import heretek_swarm.actors; print('OK')"`
**Expected:** Exit code 0, prints "OK"
**Pass criterion:** No ImportError

### T02-02: Import specific preserved actors
**Steps:**
1. `python -c "from heretek_swarm.actors import stubs; print('OK')"`
2. `python -c "from heretek_swarm.actors.explorer import ExplorerAgent; print('OK')"`
**Expected:** Both exit code 0
**Pass criterion:** Each actor imports without ImportError

### T02-03: pytest passes
**Steps:**
1. `python -m pytest tests/ -x -q`
**Expected:** All tests pass (exit code 0)
**Pass criterion:** No test failures, no ImportError in test output

### T02-04: No deleted shim can be imported
**Steps:**
1. `python -c "from heretek_swarm.actors import arbiter; print('FAIL')"` (should error)
2. Repeat for each of the 10 deleted names
**Expected:** ImportError for each — shims are gone as expected

## Not Proven By This UAT
- S03's wired __init__.py re-export surface (pending slice)
- Runtime actor behavior — only import resolution verified
- Cross-package imports referencing actors outside heretek_swarm/actors/
- Behavior of actors in subpackages heretek_swarm/actors/*/ (not affected by this slice)
