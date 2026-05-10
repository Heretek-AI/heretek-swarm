# S03: Wire actors/__init__.py as the single re-export surface

**Goal:** Create heretek_swarm/actors/__init__.py as the single re-export surface that imports all public agent classes from subpackages. This makes `from heretek_swarm.actors import AlphaAgent, ArbiterAgent` work and provides a stable import API.
**Demo:** from heretek_swarm.actors import AlphaAgent, ArbiterAgent works

## Must-Haves

- 1. `python -c \"from heretek_swarm.actors import AlphaAgent, ArbiterAgent, ExplorerAgent; print('OK')\"` exits 0\n2. `pytest tests/` passes with no ImportError\n3. No flat-file shim (arbiter.py, base.py, etc.) is referenced in __init__.py — only subpackages are imported from", "proofLevel": "contract", "integrationClosure": "Upstream: subpackages in heretek_swarm/heretek_swarm/actors/. Downstream: any consumer importing from heretek_swarm.actors. This is the final wiring step — after this, all imports resolve predictably from one canonical surface.", "observabilityImpact">none", "actorName">pi-planner

## Verification

- Run the task and slice verification checks for this slice.

## Tasks

- [x] **T01: Create actors/__init__.py re-export surface** `est:30m`
  S02 deleted 10 shim files from heretek_swarm/actors/. This task creates heretek_swarm/actors/__init__.py to re-export all public agent classes from the subpackages in heretek_swarm/heretek_swarm/actors/. The init must import and re-export from each subpackage, using try/except to skip subpackages whose __init__.py files have import errors. A sanity test confirms key agents import successfully.
  - Files: `heretek_swarm/actors/__init__.py`
  - Verify: python -c "from heretek_swarm.actors import AlphaAgent, ArbiterAgent, ExplorerAgent; print('OK')"

## Files Likely Touched

- heretek_swarm/actors/__init__.py
