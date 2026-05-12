---
estimated_steps: 5
estimated_files: 17
skills_used: []
---

# T02: Consolidate inner backend/tests/ into root tests/

Move all 16 test files from `backend/tests/` into the root `tests/` directory. These tests import from `heretek_swarm.*` (package name, not filesystem path), so moving them is a pure file operation — no import changes needed. No name collisions exist (verified: all 16 inner filenames are unique vs the 46 root test files). No conftest.py or __init__.py exists in backend/tests/, so no fixture conflicts.

Steps:
1. `git mv backend/tests/*.py tests/` for each of the 16 .py files
2. `git rm -r backend/tests/` to remove the now-empty directory
3. Verify pytest collection: `python -m pytest tests/ --collect-only -q | tail -1` should show test files count increasing from 46 to 62

## Inputs

- `backend/tests/*.py`

## Expected Output

- `backend/tests/test_auto_routing_integration.py`
- `backend/tests/test_complexity_heuristic.py`
- `backend/tests/test_consciousness_api.py`
- `backend/tests/test_consensus_audit_jsonl.py`
- `backend/tests/test_consensus_cli.py`
- `backend/tests/test_consensus_coordinator.py`
- `backend/tests/test_consensus_runtime.py`
- `backend/tests/test_consensus_websocket.py`
- `backend/tests/test_domain_selector.py`
- `backend/tests/test_goal_cli.py`
- `backend/tests/test_goal_consensus.py`
- `backend/tests/test_goal_pipeline.py`
- `backend/tests/test_goal_proposer.py`
- `backend/tests/test_goal_store.py`
- `backend/tests/test_goal_translator.py`
- `backend/tests/test_workflow_persistence.py`
- `tests/`

## Verification

python -m pytest tests/ --collect-only -q 2>&1 | grep -c 'tests collected'
