---
estimated_steps: 7
estimated_files: 2
skills_used: []
---

# T02: Verify lifecycle tests pass and cover all canonical agents

Run the lifecycle test suite and verify:
1. All canonical agents (23 + AgentActor base) have at least one lifecycle test case
2. `pytest tests/test_actor_lifecycle.py -x -q` passes with exit 0
3. All tests complete in under 30s (measure with `--durations=0`)
4. No infrastructure dependencies leaked (no NATS connection attempts, no DB pool creation)

**Fix any issues found:** If an agent's constructor doesn't work with stubs, patch its specific dependency. If a constructor requires infrastructure that can't be mocked, add a `pytest.importorskip` guard and mark as `@pytest.mark.integration`.

**Count verification:** Use `pytest --collect-only -q tests/test_actor_lifecycle.py` to confirm all agents are covered.

## Inputs

- `tests/test_actor_lifecycle.py`

## Expected Output

- `tests/test_actor_lifecycle.py`
- `tests/conftest.py`

## Verification

cd /c/Users/Derek/Desktop/heretek-swarm && python -m pytest tests/test_actor_lifecycle.py -x -q 2>&1 | tail -10 && python -m pytest tests/test_actor_lifecycle.py --durations=0 -q 2>&1 | tail -10
