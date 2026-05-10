---
estimated_steps: 31
estimated_files: 2
skills_used: []
---

# T01: Create parameterized lifecycle smoke test for all canonical AgentActor subclasses

Create `tests/test_actor_lifecycle.py` with a pytest parameterized test that covers every canonical AgentActor subclass. For each agent class, the test must: (1) construct with minimal stubs (the 6 injectable stubs + any agent-specific required args), (2) call `spawn()` and assert `state == ActorState.ACTIVE`, (3) call `send()` with a health_check message (requires asyncio), (4) call `terminate()` and assert `state == ActorState.TERMINATED`, (5) assert `error_count == 0` (no exceptions during lifecycle).

**Agent coverage matrix (23 + base AgentActor):**

**Simple agents** (pass `**kwargs`, accept stubs directly):
- `AgentActor` (base — test directly)
- `AlphaAgent`, `BetaAgent`, `CharlieAgent` (from triad — simple constructors with **kwargs)
- `StewardAgent` (from triad — uses many mixins with stubs; note: requires `access_analyzer`, `pattern_extractor`, `tribunal`, `deliberation_engine`)
- `ArbiterAgent`, `CatalystAgent`, `CoordinatorAgent`, `CoderAgent`
- `DreamerAgent`, `EmpathAgent`
- `NexusAgent`, `PrismAgent`

**Agents with their own constructor signatures** (not just **kwargs passthrough):**
- `HistorianAgent` — takes `memory_system`, `pattern_extractor`, `deliberation_engine`, `access_analyzer`, `zero_trust_validator` as named kwargs. Construct with `DualTierMemory()` (importable) + stubs for others.
- `MetisAgent` — takes `pattern_extractor`, `deliberation_engine`, `access_analyzer`, `zero_trust_validator`, `goal_proposer`. Construct with stubs for these.
- `PerceiverAgent` — similar pattern. Construct with stubs.
- `EchoActor` — specific constructor `(agent_id, config, _pattern_extractor, ...)`. Construct with `agent_id="echo-test"`.
- `ChronosAgent`, `ExaminerAgent`, `ExplorerAgent`, `HabitForgeAgent`, `SentinelAgent`, `SentinelPrimeAgent`, `PerceiverPlusAgent` — each from their subpackage. Read their agent.py to determine constructor args.
- `ActorSupervisor` — special case, but still an AgentActor.
- `BehaviorProfiler` — from profiling.py, AgentActor subclass.

**Strategy for complex agents:** Use `unittest.mock.patch` or provide real importable defaults (like `DualTierMemory()` or `Stub*()` instances). If an agent requires a real dependency that can't be imported without infrastructure, mark that agent test as `@pytest.mark.integration` and add `pytest.importorskip` guard.

**Test structure:**
- One test function `test_agent_lifecycle[agent_name]` parameterized via `@pytest.mark.parametrize`
- Each entry defines: `(agent_class, constructor_kwargs)`
- The test body: construct → spawn → assert ACTIVE → send health_check → terminate → assert TERMINATED
- Use `pytest.mark.asyncio` for all async operations
- Import `Stub*` classes from `heretek_swarm.actors.stubs`
- Import `ActorState` from `heretek_swarm.actors.base.core`

**Constraints:**
- No `.gsd/`, `.planning/`, or `.audits/` paths in test file
- Tests must not require real Postgres, Redis, Qdrant, NATS, or any external service
- Tests must not import from `.gsd/` directories
- Use `conftest.py` fixture `_clear_supervisor_actors` (already autouse)
- Mark all lifecycle tests with `@pytest.mark.unit` (or no marker — run by default)

## Inputs

- `heretek_swarm/actors/__init__.py`
- `heretek_swarm/actors/base/core.py`
- `heretek_swarm/actors/base/message_handling.py`
- `heretek_swarm/actors/stubs.py`
- `tests/test_stub_injection.py`
- `tests/conftest.py`

## Expected Output

- `tests/test_actor_lifecycle.py`

## Verification

cd /c/Users/Derek/Desktop/heretek-swarm && python -m pytest tests/test_actor_lifecycle.py -x -q --tb=short 2>&1 | tail -20
