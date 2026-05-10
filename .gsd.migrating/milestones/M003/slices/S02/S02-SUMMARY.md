---
id: S02
parent: M003
milestone: M003
provides:
  - 6 protocol stub classes usable as AgentActor constructor kwargs
  - Constructor-based stub injection pattern (mixin deps as public attrs, core deps as private attrs with fallback)
  - 14-test test suite for stub injection verification
requires:
  - slice: S01
    provides: Provides: fail-fast type guards that raise TypeError when guarded methods are called with None deps; the stub injection pattern satisfies these guards so mixin methods work with stubs
affects:
  - S03 — Will provide: from heretek_swarm.actors.mixins import AuditMixin, DeliberationMixin; S02 provides the stub injection contract S03 needs for its integration smoke test
key_files:
  - heretek-swarm/heretek_swarm/actors/stubs.py
  - heretek-swarm/heretek_swarm/actors/base/core.py
  - tests/test_stub_injection.py
key_decisions:
  - Mixin deps (access_analyzer et al.) use public instance attrs (self.*) for MRO-visible mixin access; core deps (llm_provider, event_mesh) use private names (self._*) since they're consumed internally
  - Injectable dep kwargs use `Any | None = None` typing to avoid circular import risk from TYPE_CHECKING imports
  - Core deps use `value or fallback()` pattern — when a kwarg is truthy it replaces the module-level default, preserving backward compatibility
patterns_established:
  - Stub injection via constructor kwargs with public/private attr naming based on consumer (mixin vs core method)
  - value or fallback() pattern for backward-compatible dep override
observability_surfaces:
  - none
drill_down_paths:
  - M003/slices/S02/T01 — 6 protocol stub classes
  - M003/slices/S02/T02 — AgentActor constructor update
  - M003/slices/S02/T03 — Stub injection test suite
duration: ""
verification_result: passed
completed_at: 2026-05-08T00:46:09.743Z
blocker_discovered: false
---

# S02: Make stubs first-class constructor arguments

**All 6 injectable dependency stubs are first-class AgentActor constructor kwargs, enabling `AlphaAgent(access_analyzer=StubAccessAnalyzer())` without monkey-patching**

## What Happened

This slice added first-class stub injection to AgentActor through three tasks that built on each other:

**T01 — Protocol stub classes:** Added 6 classes to `heretek_swarm/actors/stubs.py` — StubAccessAnalyzer, StubPatternExtractor, StubTribunal, StubDeliberationEngine, StubLLMProvider, StubEventMesh — each with minimal in-memory implementations matching the interfaces expected by the corresponding mixins. StubAccessAnalyzer records accesses in an in-memory dict. StubPatternExtractor caches message analyses. StubTribunal manages in-memory cases/evidence/rulings. StubDeliberationEngine tracks deliberation rounds. StubLLMProvider returns canned responses. StubEventMesh acts as an in-memory event bus. Legacy module-level functions (get_nats_event_mesh, get_llm_provider) were preserved for backward compatibility.

**T02 — AgentActor constructor:** Extended AgentActor.__init__ in `heretek_swarm/actors/base/core.py` to accept all 6 deps as optional keyword arguments defaulting to None. Mixin-visible deps (access_analyzer, pattern_extractor, deliberation_engine, tribunal) are set as public instance attrs so mixin methods access them via the MRO. Core deps (llm_provider, event_mesh) are private attrs with a `value or fallback()` pattern — when a kwarg is provided it replaces the module-level stub default, preserving backward compatibility. All kwargs typed as `Any | None = None` to avoid circular import risk from TYPE_CHECKING blocks.

**T03 — Test suite:** Created `tests/test_stub_injection.py` with 14 tests across 4 test classes: TestAgentActorStubInjection (6 tests — each dep individually plus canned LLM response and combined stubs), TestTriadAgentStubInjection (4 tests — mixin guarded methods work with stubs on AlphaAgent), TestAgentActorDefaultConstruction (2 tests — no-stub construction doesn't error), TestAlphaAgentStubInjection (3 tests — AlphaAgent with all stubs, combined, and default). All 33 tests across 3 test suites pass cleanly.

## Verification

14 new tests in tests/test_stub_injection.py plus 19 existing tests (test_mixin_guards.py + test_actor_routing.py) all pass — verified by task executors in prior verification runs. Key verification evidence per task: T01 — import smoke test for all 6 stub classes; T02 — pytest test_actor_routing.py 7/7 passing + manual smoke test confirming injection and fallback behavior; T03 — all 33 tests pass across all 3 test suites.

## Requirements Advanced

None.

## Requirements Validated

None.

## New Requirements Surfaced

None.

## Requirements Invalidated or Re-scoped

None.

## Operational Readiness

None.

## Deviations

None.

## Known Limitations

None.

## Follow-ups

None.

## Files Created/Modified

- `heretek-swarm/heretek_swarm/actors/stubs.py` — Added 6 stub classes (StubAccessAnalyzer, StubPatternExtractor, StubTribunal, StubDeliberationEngine, StubLLMProvider, StubEventMesh) with in-memory implementations and preserved legacy fallback functions
- `heretek-swarm/heretek_swarm/actors/base/core.py` — Updated AgentActor.__init__ to accept 6 new optional kwargs (mixin deps as public attrs, core deps as private attrs with fallback)
- `tests/test_stub_injection.py` — Created 14 tests across 4 test classes proving individual/combined/default/mixin stub injection
