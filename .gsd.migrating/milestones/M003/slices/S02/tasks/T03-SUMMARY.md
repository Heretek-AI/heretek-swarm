---
id: T03
parent: S02
milestone: M003
key_files:
  - tests/test_stub_injection.py
key_decisions:
  - (none)
duration: 
verification_result: passed
completed_at: 2026-05-08T00:36:37.532Z
blocker_discovered: false
---

# T03: Write 14 tests for constructor-based stub injection (6 agent-level, 7 TriadAgent mixin, 1 default-construction) and verify all 33 tests pass across 3 test suites

**Write 14 tests for constructor-based stub injection (6 agent-level, 7 TriadAgent mixin, 1 default-construction) and verify all 33 tests pass across 3 test suites**

## What Happened

Created `tests/test_stub_injection.py` with 14 test cases across 4 test classes:

1. **TestAgentActorStubInjection** (6 tests) — verifies bare `AgentActor` accepts stub kwargs for all 6 deps (`access_analyzer`, `pattern_extractor`, `tribunal`, `deliberation_engine`, `llm_provider`, `event_mesh`), verifies `llm_provider` generates canned responses, and verifies multiple stubs together.

2. **TestTriadAgentStubInjection** (4 tests) — verifies `AlphaAgent` (which mixes in `MemoryMixin` and `PatternMixin`) can call mixin guarded methods (`_track_memory_access`, `_get_memory_tier`, `_emit_pattern`, `_consume_patterns`) with stubs without raising `TypeError`. Confirms the stub actually recorded data (access_count, profile, etc.). TribunalMixin tests are skipped here since TriadAgent doesn't include TribunalMixin — those are covered by the existing `test_mixin_guards.py`.

3. **TestAgentActorDefaultConstruction** (2 tests) — verifies `AgentActor()` with no stubs constructs without error (mixin deps are None, core deps fall back to module-level stubs).

4. **TestAlphaAgentStubInjection** (3 tests) — verifies `AlphaAgent()` with stubs constructs cleanly, all 6 stubs together, and default no-stubs construction.

Key implementation decision: mixin methods are on `TriadAgent` (which includes `MemoryMixin`, `PatternMixin`, `DeliberationMixin`, `LearningMixin`), not on bare `AgentActor`. Tests that call mixin methods therefore use `AlphaAgent`, not bare `AgentActor`.

## Verification

pytest tests/test_stub_injection.py tests/test_mixin_guards.py tests/test_actor_routing.py -x -v — all 33 tests pass (14 new stub injection tests, 12 existing mixin guard tests, 7 existing routing tests)

## Verification Evidence

| # | Command | Exit Code | Verdict | Duration |
|---|---------|-----------|---------|----------|
| 1 | `cd heretek-swarm && python -m pytest ../tests/test_stub_injection.py -x -v --no-header` | 0 | ✅ pass | 700ms |
| 2 | `cd heretek-swarm && python -m pytest ../tests/test_stub_injection.py ../tests/test_mixin_guards.py ../tests/test_actor_routing.py -x -v --no-header` | 0 | ✅ pass | 200ms |

## Deviations

Planned test for _submit_tribunal_case/_submit_tribunal_evidence with stubs was removed because TribunalMixin is not mixed into TriadAgent/AlphaAgent — those methods only exist on classes that include TribunalMixin. The existing test_mixin_guards.py already covers the guard-raising path for TribunalMixin. The stub injection into AgentActor still works correctly for the tribunal kwarg (verified in test_multiple_stubs_injected and test_alpha_agent_with_all_stubs).

## Known Issues

None.

## Files Created/Modified

- `tests/test_stub_injection.py`
