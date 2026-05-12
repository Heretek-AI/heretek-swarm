# S03: Verify clean clone and full integration

**Goal:** All stale artifacts from the pre-rename state cleaned up (src/, backend/docs/, backend/agent_workspace/, backend/.claude/), all 16 inner test files consolidated from backend/tests/ into root tests/, and full integration verification passes cleanly — proving a fresh clone of the repo works at the new backend/ paths.
**Demo:** Fresh clone of the repo works perfectly at new paths.

## Must-Haves

- | # | Criterion | How to Verify |
- |---|-----------|---------------|
- | 1 | `src/` directory gone | `test ! -d src` |
- | 2 | `backend/docs/` gone | `test ! -d backend/docs` |
- | 3 | `backend/agent_workspace/` gone | `test ! -d backend/agent_workspace` |
- | 4 | All 16 inner test files in root `tests/` | `ls tests/*.py \| wc -l` returns 62 (46 original + 16 moved) |
- | 5 | `pip install -e .` succeeds | exit code 0 |
- | 6 | `import heretek_swarm` resolves via backend/ | `python -c "import heretek_swarm; print(heretek_swarm.__file__)"` contains `backend/` |
- | 7 | Full test suite passes | `pytest -m "not integration" -q` exit 0 (pre-existing test failures documented) |
- | 8 | `ruff check backend/ tests/` passes | exit code 0 |
- | 9 | `docker compose config` parses | exit code 0 |
- | 10 | No stale filesystem path refs | `git grep "heretek-swarm/" -- ':!.gsd/' ':!.git/'` returns only GitHub/pypi URL references |

## Proof Level

- This slice proves: integration

## Integration Closure

This is the final slice of M007. It closes the loop on all integration surfaces: pip install from the new backend/, pytest with consolidated test files, docker compose config with the updated Dockerfile path, ruff check on new paths, and a git grep confirming zero stale heretek-swarm/ filesystem references. After this slice, the milestone is complete — the repo structure is clean, verified, and clone-ready.

## Verification

- None — this is a cleanup and verification slice with no runtime code changes. Verification results are documented in task summaries.

## Tasks

- [ ] **T01: Delete stale artifacts from pre-rename state** `est:15m`
  Delete four groups of stale directories/files left behind by the git mv:
  - Files: `src/cli.py`, `src/__init__.py`, `src/agent_workspace/error.txt`, `backend/docs/actors/README.md`, `backend/agent_workspace/agents/*/MEMORY.md`, `backend/agent_workspace/error.txt`, `backend/.claude/tdd-guard/data/test.json`
  - Verify: test ! -d src && test ! -d backend/docs && test ! -d backend/agent_workspace && test ! -d backend/.claude

- [ ] **T02: Consolidate inner backend/tests/ into root tests/** `est:15m`
  Move all 16 test files from `backend/tests/` into the root `tests/` directory. These tests import from `heretek_swarm.*` (package name, not filesystem path), so moving them is a pure file operation — no import changes needed. No name collisions exist (verified: all 16 inner filenames are unique vs the 46 root test files). No conftest.py or __init__.py exists in backend/tests/, so no fixture conflicts.
  - Files: `backend/tests/test_auto_routing_integration.py`, `backend/tests/test_complexity_heuristic.py`, `backend/tests/test_consciousness_api.py`, `backend/tests/test_consensus_audit_jsonl.py`, `backend/tests/test_consensus_cli.py`, `backend/tests/test_consensus_coordinator.py`, `backend/tests/test_consensus_runtime.py`, `backend/tests/test_consensus_websocket.py`, `backend/tests/test_domain_selector.py`, `backend/tests/test_goal_cli.py`, `backend/tests/test_goal_consensus.py`, `backend/tests/test_goal_pipeline.py`, `backend/tests/test_goal_proposer.py`, `backend/tests/test_goal_store.py`, `backend/tests/test_goal_translator.py`, `backend/tests/test_workflow_persistence.py`, `tests/`
  - Verify: python -m pytest tests/ --collect-only -q 2>&1 | grep -c 'tests collected'

- [ ] **T03: Run full integration verification suite** `est:30m`
  Execute the complete M007 acceptance verification suite to prove the restructured repo works for a fresh clone:
  - Verify: All 6 verification commands exit with code 0 (or expected results documented)

## Files Likely Touched

- src/cli.py
- src/__init__.py
- src/agent_workspace/error.txt
- backend/docs/actors/README.md
- backend/agent_workspace/agents/*/MEMORY.md
- backend/agent_workspace/error.txt
- backend/.claude/tdd-guard/data/test.json
- backend/tests/test_auto_routing_integration.py
- backend/tests/test_complexity_heuristic.py
- backend/tests/test_consciousness_api.py
- backend/tests/test_consensus_audit_jsonl.py
- backend/tests/test_consensus_cli.py
- backend/tests/test_consensus_coordinator.py
- backend/tests/test_consensus_runtime.py
- backend/tests/test_consensus_websocket.py
- backend/tests/test_domain_selector.py
- backend/tests/test_goal_cli.py
- backend/tests/test_goal_consensus.py
- backend/tests/test_goal_pipeline.py
- backend/tests/test_goal_proposer.py
- backend/tests/test_goal_store.py
- backend/tests/test_goal_translator.py
- backend/tests/test_workflow_persistence.py
- tests/
