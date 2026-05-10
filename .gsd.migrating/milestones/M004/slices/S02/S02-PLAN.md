# S02: Write actor lifecycle smoke tests

**Goal:** Every canonical AgentActor subclass has a lifecycle smoke test: construct with stubs → spawn → confirm state transitions → terminate gracefully.
**Demo:** pytest tests/test_actor_lifecycle.py -x -q passes

## Must-Haves

- `pytest tests/test_actor_lifecycle.py -x -q` passes (exit 0) with all agent lifecycle tests collected and passing.
- Every canonical AgentActor subclass (23 agent classes + AgentActor) has at least one lifecycle test.
- Every test constructs the agent with minimal stubs (no real LLM, no NATS, no Postgres), spawns it, verifies `state == ActorState.ACTIVE`, sends a health_check message, terminates it, and verifies `state == ActorState.TERMINATED` or `ActorState.ERROR` on expected failure.
- Complex agents (HistorianAgent, MetisAgent, PerceiverAgent, etc.) that require specific constructor args are tested with `unittest.mock.patch` or inline construction with minimal real/importable deps.
- All lifecycle tests combined complete in under 30s.

## Proof Level

- This slice proves: contract

## Integration Closure

No new wiring. This slice produces tests that consume the existing AgentActor public API (spawn, terminate, send, process_message, state). The test file itself is the artifact — it proves every agent can be instantiated, run, and shut down without infrastructure.

## Verification

- None — tests are external verification artifacts. If an agent fails lifecycle (e.g. missing constructor arg, state transition bug), the test failure with traceback is the signal.

## Tasks

- [x] **T01: Create parameterized lifecycle smoke test for all canonical AgentActor subclasses** `est:2h`
  Create `tests/test_actor_lifecycle.py` with a pytest parameterized test that covers every canonical AgentActor subclass. For each agent class, the test must: (1) construct with minimal stubs (the 6 injectable stubs + any agent-specific required args), (2) call `spawn()` and assert `state == ActorState.ACTIVE`, (3) call `send()` with a health_check message (requires asyncio), (4) call `terminate()` and assert `state == ActorState.TERMINATED`, (5) assert `error_count == 0` (no exceptions during lifecycle).
  - Files: `tests/test_actor_lifecycle.py`, `tests/conftest.py`
  - Verify: cd /c/Users/Derek/Desktop/heretek-swarm && python -m pytest tests/test_actor_lifecycle.py -x -q --tb=short 2>&1 | tail -20

- [x] **T02: Verify lifecycle tests pass and cover all canonical agents** `est:1h`
  Run the lifecycle test suite and verify:
  1. All canonical agents (23 + AgentActor base) have at least one lifecycle test case
  2. `pytest tests/test_actor_lifecycle.py -x -q` passes with exit 0
  3. All tests complete in under 30s (measure with `--durations=0`)
  4. No infrastructure dependencies leaked (no NATS connection attempts, no DB pool creation)
  - Files: `tests/test_actor_lifecycle.py`, `tests/conftest.py`
  - Verify: cd /c/Users/Derek/Desktop/heretek-swarm && python -m pytest tests/test_actor_lifecycle.py -x -q 2>&1 | tail -10 && python -m pytest tests/test_actor_lifecycle.py --durations=0 -q 2>&1 | tail -10

## Files Likely Touched

- tests/test_actor_lifecycle.py
- tests/conftest.py
