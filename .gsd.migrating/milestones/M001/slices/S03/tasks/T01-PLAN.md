---
estimated_steps: 1
estimated_files: 1
skills_used: []
---

# T01: Create actors/__init__.py re-export surface

S02 deleted 10 shim files from heretek_swarm/actors/. This task creates heretek_swarm/actors/__init__.py to re-export all public agent classes from the subpackages in heretek_swarm/heretek_swarm/actors/. The init must import and re-export from each subpackage, using try/except to skip subpackages whose __init__.py files have import errors. A sanity test confirms key agents import successfully.

## Inputs

- None specified.

## Expected Output

- `heretek_swarm/actors/__init__.py`

## Verification

python -c "from heretek_swarm.actors import AlphaAgent, ArbiterAgent, ExplorerAgent; print('OK')"
