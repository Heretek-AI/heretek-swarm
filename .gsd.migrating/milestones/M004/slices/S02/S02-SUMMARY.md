---
id: S02
parent: M004
milestone: M004
provides:
  - Canonical lifecycle test suite consumed by S03 CI pipeline as the primary pytest target.
requires:
  []
affects:
  - S03 — will use this test suite in CI
key_files:
  - tests/test_actor_lifecycle.py
  - tests/conftest.py
key_decisions:
  - Use parameterized tests organized by constructor pattern (**kwargs, explicit stub params, config-based, special constructors) rather than one monolithic test per agent — reduces boilerplate and makes adding new agents trivial.
  - Use 6 dedicated stubs instead of mocking at the monkey-patch level — keeps tests readable and decoupled from implementation internals.
patterns_established:
  - Lifecycle smoke test pattern: construct with minimal stubs → spawn → assert ACTIVE → send health_check via mailbox → terminate → assert TERMINATED + error_count==0.
observability_surfaces:
  - None — this slice is a test artifact only; no runtime observability surfaces were added.
drill_down_paths:
  - .gsd/milestones/M004/slices/S02/tasks/T01-SUMMARY.md
  - .gsd/milestones/M004/slices/S02/tasks/T02-SUMMARY.md
duration: ""
verification_result: passed
completed_at: 2026-05-10T20:24:52.318Z
blocker_discovered: false
---

# S02: Write actor lifecycle smoke tests

**Parameterized lifecycle smoke tests for all 24 canonical AgentActor subclasses pass with 26 tests in under 6s**

## What Happened

Created tests/test_actor_lifecycle.py with 26 comprehensive lifecycle tests covering all 24 AgentActor subclasses plus BehaviorProfiler and ActorSupervisor. Tests are organized into four constructor-pattern groups: (1) 14 parameterized tests for simple **kwargs-agents (AgentActor, AlphaAgent, BetaAgent, CharlieAgent, StewardAgent, DreamerAgent, EmpathAgent, PrismAgent, HistorianAgent, MetisAgent, PerceiverAgent, ExplorerAgent, HabitForgeAgent, PerceiverPlusAgent), (2) 4 parameterized tests for agents with explicit stub params (ArbiterAgent, CatalystAgent, CoderAgent, ExaminerAgent), (3) 3 parameterized tests for config-based agents (CoordinatorAgent, ChronosAgent, NexusAgent), and (4) 5 standalone tests for special-constructor agents (EchoActor, SentinelAgent, SentinelPrimeAgent, ActorSupervisor, BehaviorProfiler). Each test follows the same lifecycle pattern: construct with minimal stubs → spawn → assert ACTIVE → process health_check via mailbox → terminate → assert TERMINATED → assert error_count == 0.

The stub infrastructure (6 stubs in conftest.py: StubAccessAnalyzer, StubPatternExtractor, StubTribunal, StubDeliberationEngine, StubLLMProvider, StubEventMesh) enables infrastructure-free testing with no NATS, DB, or Redis dependencies. Two pre-existing gaps were fixed during T01: added _validate_and_prepare_message and _execute_handler_and_publish to the AgentActor message_handling monkey-patch bindings, and added send_to_json/broadcast_json methods to StubEventMesh. T02 verified all tests pass, coverage is complete, and no infrastructure dependencies leaked.

## Verification

pytest tests/test_actor_lifecycle.py -x -q → exit 0, all 26 tests pass. pytest --collect-only -q → 26 tests collected. pytest --durations=0 -q → longest test 0.12s (SentinelPrimeAgent), total well under 30s. Stub instantiation verified: all 6 stubs create successfully with zero infrastructure imports — no NATS, no DB, no Redis.

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

Tests do not cover message routing across the event mesh or multi-agent coordination sequences.

## Follow-ups

S03 (CI) should consume this test suite as the canonical pytest command in `.github/workflows/ci.yml`.

## Files Created/Modified

- `tests/test_actor_lifecycle.py` — Created 26 lifecycle smoke tests covering all 24 AgentActor subclasses plus BehaviorProfiler and ActorSupervisor
- `tests/conftest.py` — Created 6 infrastructure-free stubs and shared fixtures
