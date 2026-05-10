# S02: Make stubs first-class constructor arguments — UAT

**Milestone:** M003
**Written:** 2026-05-08T00:46:09.744Z

# S02: Make stubs first-class constructor arguments — UAT

**Milestone:** M003
**UAT mode:** artifact-driven
**Why this mode is sufficient:** This slice is purely additive to the constructor contract — no runtime infrastructure, no live services. All behavior is verifiable through import checks, construction tests, and mixin method calls against in-memory stubs.

## Preconditions

- Python environment with project dependencies installed
- All files written and importable

## Smoke Test

`python -c "from heretek_swarm.actors.stubs import StubAccessAnalyzer, StubPatternExtractor, StubTribunal, StubDeliberationEngine, StubLLMProvider, StubEventMesh; print('6 stub classes import OK')"`

## Test Cases

### 1. Each stub can be injected individually into AgentActor

1. `agent = AgentActor(access_analyzer=StubAccessAnalyzer())`
2. `agent = AgentActor(pattern_extractor=StubPatternExtractor())`
3. `agent = AgentActor(deliberation_engine=StubDeliberationEngine())`
4. `agent = AgentActor(tribunal=StubTribunal())`
5. `agent = AgentActor(llm_provider=StubLLMProvider())`
6. `agent = AgentActor(event_mesh=StubEventMesh())`
7. **Expected:** Each construction succeeds without TypeError. Mixin deps are accessible as `agent.access_analyzer` (public). Core deps stored as `agent._llm_provider`.

### 2. StubLLMProvider returns canned text

1. `stub = StubLLMProvider(canned_response="hello")`
2. `result = stub.generate("any prompt")`
3. **Expected:** `result == "hello"`, `stub.call_count == 1`

### 3. AlphaAgent with stubs calls mixin methods without TypeError (S01 guards satisfied)

1. `agent = AlphaAgent(access_analyzer=StubAccessAnalyzer(), pattern_extractor=StubPatternExtractor())`
2. `agent._track_memory_access("key")` — **Expected:** no TypeError
3. `agent._get_memory_tier("key")` — **Expected:** returns profile data from stub
4. `agent._emit_pattern("test", {"data": 1})` — **Expected:** no TypeError
5. `agent._consume_patterns()` — **Expected:** yields patterns from stub

### 4. Default construction works without stubs

1. `agent = AgentActor()`
2. `alpha = AlphaAgent()`
3. **Expected:** Both construct without error. Mixin deps are None (S01 guards fire on method call, not construction). Core deps fall back to module-level stubs.

### 5. Multiple stubs injected together

1. `agent = AlphaAgent(access_analyzer=StubAccessAnalyzer(), pattern_extractor=StubPatternExtractor(), llm_provider=StubLLMProvider(canned_response="ok"))`
2. **Expected:** Construction succeeds. `agent.access_analyzer` is the stub. `agent.pattern_extractor` is the stub.

## Edge Cases

### kwarg=None behavior (default fallback)
1. `agent = AgentActor(access_analyzer=None)`
2. **Expected:** Dep is None. Guarded mixin methods raise TypeError if called.

### StubAccessAnalyzer records data
1. `stub = StubAccessAnalyzer()`
2. `stub.record_access("key", {"role": "user"})`
3. `stub.get_profile("key")`
4. `stub.get_statistics()`
5. **Expected:** Access recorded, profile returned, statistics computed — all from in-memory dicts, no real infrastructure.

## Failure Signals

- ImportError or AttributeError when importing stub classes from `heretek_swarm.actors.stubs`
- TypeError raised on AgentActor construction (should only raise on guarded method calls with missing deps)
- Test failures in `tests/test_stub_injection.py`, `tests/test_mixin_guards.py`, or `tests/test_actor_routing.py`

## Not Proven By This UAT

- Real runtime wiring (production deps connected to AgentActor in a live agent loop) — deferred to a later milestone
- Performance under load — stubs are in-memory and have no latency profile resembling real deps
- StubLLMProvider streaming behavior — the `generate_stream` method is present but not exercised by current tests; only `generate` and `__call__` are tested
- Cross-process EventMesh stubbing — StubEventMesh is in-process only and does not test NATS connectivity

## Notes for Tester

All 33 tests (14 new + 19 existing) pass in a single pytest invocation. The key behavioral contract: S01's fail-fast TypeError guards fire only when guarded methods are *called* with missing deps, not on AgentActor *construction*. This is intentional — construction is always safe.
