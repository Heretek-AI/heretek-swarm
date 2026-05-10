# S02: Make stubs first-class constructor arguments

**Goal:** Make every guardable mixin dependency (access_analyzer, pattern_extractor, deliberation_engine, tribunal) plus AgentActor core deps (_llm_provider, _event_mesh) injectable as optional constructor kwargs, so `AlphaAgent(access_analyzer=StubAccessAnalyzer())` works without monkey-patching.
**Demo:** Agent(llm_provider=stub_llm) uses stub without monkey-patching

## Must-Haves

- Protocol stub classes exist in `stubs.py` for all 6 injectable deps (StubAccessAnalyzer, StubPatternExtractor, StubTribunal, StubDeliberationEngine, StubLLMProvider, StubEventMesh)\n- AgentActor.__init__ accepts `access_analyzer`, `pattern_extractor`, `deliberation_engine`, `tribunal`, `llm_provider`, `event_mesh` as optional kwargs\n- When a stub is provided, the corresponding mixin method uses it (no TypeError from S01 guards)\n- When no stub is provided, AgentActor falls back to existing module-level stub functions (backward compat)\n- `AlphaAgent(access_analyzer=StubAccessAnalyzer())` constructs without TypeError\n- `AlphaAgent()` constructs cleanly with all deps defaulting to None\n- New tests in `tests/test_stub_injection.py` prove both happy-path and graceful-None behavior\n- Full test suite passes with no regressions

## Proof Level

- This slice proves: Contract — this slice proves that stub classes can be injected via constructor kwargs and flow through the MRO to mixin methods. Real runtime integration (wiring real deps in production) is a separate concern for a later milestone.

## Integration Closure

Upstream surfaces consumed: `heretek_swarm/actors/stubs.py` (augmented with 6 new classes), `heretek_swarm/actors/base/core.py` (AgentActor constructor updated). New wiring: None — this slice is purely additive to the constructor contract. What remains before milestone is usable end-to-end: S03 (integration smoke test from public import path) and real dep wiring in production (out of scope for M003).

## Verification

- Run the task and slice verification checks for this slice.

## Tasks

- [x] **T01: Add protocol stub classes to stubs.py** `est:45m`
  Add 6 protocol stub classes to `heretek_swarm/actors/stubs.py` that implement the expected interfaces of the 6 injectable dependencies. Each class should accept and store constructor args but not require real infrastructure.
  - Files: `heretek_swarm/actors/stubs.py`
  - Verify: python -c "from heretek_swarm.actors.stubs import StubAccessAnalyzer, StubPatternExtractor, StubTribunal, StubDeliberationEngine, StubLLMProvider, StubEventMesh; print('OK')"

- [x] **T02: Update AgentActor.__init__ to accept all deps as optional constructor kwargs** `est:30m`
  Modify `AgentActor.__init__` in `heretek_swarm/actors/base/core.py` to accept 6 new optional keyword arguments: `access_analyzer`, `pattern_extractor`, `deliberation_engine`, `tribunal`, `llm_provider`, `event_mesh`. All default to None.
  - Files: `heretek_swarm/actors/base/core.py`
  - Verify: pytest tests/test_actor_routing.py -x -q --no-header 2>&1 | tail -5

- [x] **T03: Write and run tests for constructor-based stub injection** `est:45m`
  Create `tests/test_stub_injection.py` with the following test cases:
  - Files: `tests/test_stub_injection.py`, `heretek_swarm/actors/stubs.py`, `heretek_swarm/actors/base/core.py`
  - Verify: pytest tests/test_stub_injection.py tests/test_mixin_guards.py tests/test_actor_routing.py -x -q --no-header 2>&1 | tail -10

## Files Likely Touched

- heretek_swarm/actors/stubs.py
- heretek_swarm/actors/base/core.py
- tests/test_stub_injection.py
