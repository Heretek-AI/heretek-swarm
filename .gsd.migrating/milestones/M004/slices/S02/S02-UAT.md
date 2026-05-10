# S02: Write actor lifecycle smoke tests — UAT

**Milestone:** M004
**Written:** 2026-05-10T20:24:52.318Z

# S02: Write actor lifecycle smoke tests — UAT

**Milestone:** M004

## UAT Type

- UAT mode: artifact-driven
- Why this mode is sufficient: The slice produces tests as its sole artifact. Passing tests are the acceptance criterion. No runtime, human interaction, or live infrastructure is involved.

## Preconditions

- Repository cloned with dependencies installed
- pytest and all asyncio test dependencies available

## Smoke Test

```
pytest tests/test_actor_lifecycle.py -x -q
```

Expected: exit 0, no failures reported.

## Test Cases

### 1. **kwargs-constructor agents lifecycle

1. Run: `pytest tests/test_actor_lifecycle.py -k "kwargs" -x -q`
2. **Expected:** All 14 parameterized **kwargs-agent tests pass (AgentActor, AlphaAgent, BetaAgent, CharlieAgent, StewardAgent, DreamerAgent, EmpathAgent, PrismAgent, HistorianAgent, MetisAgent, PerceiverAgent, ExplorerAgent, HabitForgeAgent, PerceiverPlusAgent)

### 2. Explicit-stub-constructor agents lifecycle

1. Run: `pytest tests/test_actor_lifecycle.py -k "explicit" -x -q`
2. **Expected:** All 4 parameterized explicit-stub tests pass (ArbiterAgent, CatalystAgent, CoderAgent, ExaminerAgent)

### 3. Config-based constructor agents lifecycle

1. Run: `pytest tests/test_actor_lifecycle.py -k "config" -x -q`
2. **Expected:** All 3 parameterized config-based tests pass (CoordinatorAgent, ChronosAgent, NexusAgent)

### 4. Special-constructor agents lifecycle

1. Run: `pytest tests/test_actor_lifecycle.py -k "special" -x -q`
2. **Expected:** All 5 standalone tests pass (EchoActor, SentinelAgent, SentinelPrimeAgent, ActorSupervisor, BehaviorProfiler)

### 5. Full suite timing

1. Run: `pytest tests/test_actor_lifecycle.py --durations=0 -q`
2. **Expected:** All 26 tests complete. Longest individual test under 1s. Total time under 30s.

### 6. Stub isolation — no infrastructure imports

1. Run: `python -c "from tests.conftest import StubAccessAnalyzer, StubPatternExtractor, StubTribunal, StubDeliberationEngine, StubLLMProvider, StubEventMesh; print('all 6 stubs import cleanly')"`
2. **Expected:** Prints "all 6 stubs import cleanly" with no import errors from NATS, DB, or other infrastructure modules.

## Edge Cases

### Test collection counts

1. Run: `pytest tests/test_actor_lifecycle.py --collect-only -q`
2. **Expected:** Exactly 26 tests collected. No warnings about unknown fixtures or missing test items.

## Failure Signals

- Any test failure with traceback — indicates a constructor requirement changed, a state transition regressed, or a monkey-patch binding broke.
- Fewer than 26 tests collected — indicates a new agent class is missing from the test parameterization.
- Import error on stubs — indicates an infrastructure dependency leaked into the stub layer.

## Not Proven By This UAT

- Multi-agent interaction sequences (each test tests a single agent in isolation)
- Message routing correctness across the event mesh
- Real LLM response handling
- Persistent state or database interactions
- CI pipeline integration (delegated to S03)

## Notes for Tester

All tests use @pytest.mark.asyncio. If a test hangs, check that the stub mailbox (asyncio.Queue) is properly drained during terminate(). The full suite completes in under 10s on a standard machine.

