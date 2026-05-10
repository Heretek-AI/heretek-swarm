---
estimated_steps: 13
estimated_files: 3
skills_used: []
---

# T03: Write and run tests for constructor-based stub injection

Create `tests/test_stub_injection.py` with the following test cases:

1. `test_agent_with_stub_access_analyzer` — constructs AgentActor(agent_id="test", access_analyzer=StubAccessAnalyzer()), calls _track_memory_access and _get_memory_tier, verifies they work without TypeError
2. `test_agent_with_stub_pattern_extractor` — constructs AgentActor with StubPatternExtractor, calls _emit_pattern (async), verifies no TypeError
3. `test_agent_with_stub_tribunal` — constructs AgentActor with StubTribunal, calls _submit_tribunal_case (async), verifies no TypeError
4. `test_agent_with_stub_llm_provider` — constructs AgentActor(llm_provider=StubLLMProvider()), verifies self._llm_provider is the stub
5. `test_agent_without_stubs_constructs_cleanly` — constructs AgentActor() with no stub kwargs, verifies it raises no TypeError at construction time (the S01 guards only fire when guarded methods are called)
6. `test_alpha_agent_with_stubs_constructs` — constructs AlphaAgent(access_analyzer=StubAccessAnalyzer(), pattern_extractor=StubPatternExtractor()), verifies construction succeeds

Each test must:
- Import the stub class from `heretek_swarm.actors.stubs`
- Import the agent class from `heretek_swarm.actors` or `heretek_swarm.actors.base`
- Use `@pytest.mark.asyncio` for async methods
- Call the guarded method and assert no TypeError is raised

Also verify that `pytest tests/test_mixin_guards.py -x -q` still passes (the S01 guards still work — stubs silence them, absence triggers them).

## Inputs

- `heretek_swarm/actors/stubs.py`
- `heretek_swarm/actors/base/core.py`
- `heretek_swarm/actors/triad/agent.py`

## Expected Output

- `tests/test_stub_injection.py`

## Verification

pytest tests/test_stub_injection.py tests/test_mixin_guards.py tests/test_actor_routing.py -x -q --no-header 2>&1 | tail -10
