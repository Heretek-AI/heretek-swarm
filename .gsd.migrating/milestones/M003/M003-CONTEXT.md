# M003: Type-seal Mixin contracts and make stub injection first-class

**Gathered:** 2026-05-07
**Status:** Ready for planning

## Project Description

Heretek Swarm is a multi-agent orchestration system where agents inherit behavior from mixins. Currently mixins like MemoryMixin silently return default values (None, empty lists, COLD tier) when their dependency attributes are None — a runtime footgun that causes confusing failures downstream. Stubs exist as module-level functions (get_llm_provider returning None) that tests monkey-patch. M003 makes these contracts fail-fast and makes stub injection a first-class constructor argument.

## Why This Milestone

Mixins that silently no-op when deps are missing cause data loss without errors — an agent thinks it tracked memory access but the analyzer was never wired. The monkey-patch testing pattern works but is fragile: tests need to know internal attribute names, patch at the right import path, and clean up after themselves. After M003, every mixin raises TypeError immediately when its dependency is absent, and tests can inject stubs via constructor kwargs.

## User-Visible Outcome

### When this milestone is complete, the user can:

- Create an agent with `AlphaAgent(access_analyzer=StubAccessAnalyzer())` and have all mixins use the stub without monkey-patching
- Write `AlphaAgent()` (no stubs) and get an immediate TypeError if any mixin method is called without its dependency wired — no silent data loss
- Import all 10 mixins from `heretek_swarm.actors.mixins` and have them work with stub injection out of the box

### Entry point / environment

- Entry point: `AgentActor(**kwargs)` constructor — all agent subclasses inherit
- Environment: local dev, pytest test suite, production
- Live dependencies involved: none for guard layer (S01); stubs replace real infra for S02 testing

## Completion Class

- **Contract complete** means: unit tests verify TypeError is raised for each guarded method when dep is None; protocol stub classes exist and can be injected via constructor kwargs
- **Integration complete** means: existing agents (Alpha, Beta, Charlie, etc.) construct without changes when deps are not passed; test suite passes with rewritten constructor-based tests
- **Operational complete** means: agents fail fast with clear TypeError on missing deps in production, not silent no-ops

## Final Integrated Acceptance

To call this milestone complete, we must prove:

- A test creates `AlphaAgent(access_analyzer=StubAccessAnalyzer())`, calls a guarded mixin method, and gets real stub data back — no TypeError
- A test creates `AlphaAgent()` (no stubs), calls a guarded mixin method on a None dep, and gets TypeError
- `pytest tests/` passes with 0 failures — both new constructor-based tests and unchanged tests for non-guarded mixins

## Architectural Decisions

### Stub scope: All guardable deps + AgentActor core deps

**Decision:** S02 will make every mixin dependency that has a TypeError guard (access_analyzer, pattern_extractor, deliberation_engine, tribunal) plus AgentActor's own `_llm_provider` and `_event_mesh` injectable as constructor kwargs.

**Rationale:** The guardable deps are the ones where missing deps cause real runtime failures — they should be injectable so tests can provide stubs. The AgentActor core deps (_llm_provider, _event_mesh) currently come from module-level stubs.py functions; making them constructor args removes the monkey-patch dependency entirely. The hasattr-guarded mixins (DeliberationMixin, PatternConsumerMixin, HealthReportingMixin, AuditMixin, MemoryAccessMixin) are left unchanged — their hasattr checks handle graceful degradation for optional subsystems and do not need stub injection.

**Alternatives Considered:**
- Just the TypeError-guarded mixins — would leave _llm_provider/_event_mesh still needing monkey-patching, inconsistent
- Only AgentActor core stubs — would leave mixin deps un-injectable, tests still need to patch mixin attributes
- Every mixin including hasattr-guarded ones — scope creep; hasattr-guarded mixins intentionally handle absent deps as degraded mode, not failure

### Stub pattern: Protocol/ABC stub classes

**Decision:** Define real-looking protocol stub classes that implement the same interface as real dependencies. Agents accept optional `access_analyzer=`, `pattern_extractor=`, etc. kwargs in `__init__` and use them when provided, falling back to real deps.

**Rationale:** Protocol/ABC stubs give IDE autocomplete, type-checking, and documentation. They are self-documenting about what interface a dependency provides. A dict-driven or DI-container approach would be opaque — tests would need to know magic dict keys or container APIs.

**Alternatives Considered:**
- Dict/config-driven stubs — opaque, no type safety, no autocomplete
- DI container — adds framework dependency, over-engineered for the current complexity level

### Constructor flow: AgentActor accepts all deps as optional kwargs

**Decision:** All stub-injectable deps are added as optional `None`-defaulted keyword arguments to `AgentActor.__init__`. Mixin `__init__` methods do NOT capture their own dep — they find it as `self.{dep_name}` on the instance, set by AgentActor.

**Rationale:** The existing MRO pattern is that mixins call `super().__init__(*args, **kwargs)` which chains up to AgentActor. Adding per-mixin `__init__` that captures one dep and forwards the rest would work but create boilerplate in every mixin for no benefit — the attribute lives on self either way. A single deps dict would add indirection (self._deps["access_analyzer"] vs self.access_analyzer).

**Alternatives Considered:**
- Per-mixin __init__ captures own dep — more boilerplate, each mixin needs init code
- Single deps dict passed through init — self._deps["access_analyzer"] is less readable than self.access_analyzer

### stubs.py: Augmented, not replaced

**Decision:** The existing `stubs.py` module keeps its `get_llm_provider()`, `get_nats_event_mesh()`, `get_db_pool()` functions. New protocol stub classes (StubAccessAnalyzer, StubPatternExtractor, etc.) are added alongside them. The module-level stub functions are left as backward-compat defaults — AgentActor's `__init__` will check constructor kwargs first, falling back to the module-level function result.

**Rationale:** stubs.py is imported by `base/core.py` and `base/state_management.py` — removing the module-level functions would require touching both files. Keeping them as defaults means zero changes to the fallback path. New code uses constructor injection; existing code continues to work via the module-level fallback.

**Alternatives Considered:**
- Replace stubs.py entirely — would require updating callers with no benefit
- Keep stubs.py as a thin backward-compat shim — effectively the same; augmenting in place is simpler

### Test migration: Rewrite existing monkey-patch tests during S02

**Decision:** Tests that currently use `monkeypatch` + `unittest.mock.patch` to inject stub dependencies will be rewritten to use constructor-based stub injection during S02. The new `test_mixin_guards.py` (from S01) already uses the new pattern. Old test files like `test_agent_factory.py` will be updated.

**Rationale:** The whole point of S02 is to make monkey-patching unnecessary. Keeping both patterns would add maintenance burden and confuse new contributors. A clean rewrite gives a single canonical testing pattern.

**Alternatives Considered:**
- Additive — keep old tests alongside new ones — duplicated maintenance, confusing patterns
- Add + deprecate old pattern — adds noise without enforcement

### S03: Keep for integration smoke test

**Decision:** S03 is still needed. The `__init__.py` exports already exist and are correct, but the slice's "smoke test for stub injection" deliverable is real value. S03's scope becomes: write an integration test that verifies `from heretek_swarm.actors.mixins import *` works, then constructs an agent with stubs and calls a guarded method through the public import path.

**Alternatives Considered:**
- Skip S03 — would lose the integration-level verification
- Merge S03 into S02 — possible but slices are clearer when separated

---

## Error Handling Strategy

Guarded mixin methods raise `TypeError("{MethodName} requires {attribute_name}")` when their dependency attribute is None. This is a clear, immediate failure — no retry, no fallback, no silent default. The TypeError bubbles up to the caller, which is always an agent method that should know whether its deps are wired. Non-guarded (hasattr) mixins continue to handle missing deps gracefully with degraded behavior.

## Risks and Unknowns

- **LearningMixin.get_learning_status() crashes with `len(None)` on `_active_deliberations`** — this is the most urgent footgun; LearningMixin sets `_active_deliberations = None` as class default but the getter does `len(self._active_deliberations)` without a guard. S01 must fix this before any other guard.
- **DeliberationMixin references self.logger in error paths** — `self.logger` is not a guarded dep and will fail if the mixin is tested in isolation without AgentActor's logger setup.
- **Existing test files have many monkey-patch/patched tests** — rewriting them in S02 is scope-heavy. Triage: some tests manipulate env vars (OPENAI_API_KEY via monkeypatch.setenv), not stub injection — those stay.

## Existing Codebase / Prior Art

- `heretek-swarm/heretek_swarm/actors/mixins/memory.py` — silently returns default values when access_analyzer is None (S01 target)
- `heretek-swarm/heretek_swarm/actors/mixins/pattern.py` — silently returns [] when pattern_extractor is None (S01 target)
- `heretek-swarm/heretek_swarm/actors/mixins/learning.py` — crashes with len(None) on _active_deliberations (S01 target, highest urgency)
- `heretek-swarm/heretek_swarm/actors/mixins/tribunal.py` — 6 methods that log and return None when tribunal is None (S01 target)
- `heretek-swarm/heretek_swarm/actors/stubs.py` — module-level stub functions returning None (S02 target for augmentation)
- `heretek-swarm/heretek_swarm/actors/base/core.py` — AgentActor constructor, imports stubs (S02 target for constructor kwarg injection)
- `heretek-swarm/heretek_swarm/actors/mixins/__init__.py` — already exports all 10 mixins (S03 verifies)
- `heretek-swarm/heretek_swarm/actors/mixins/deliberation.py` — uses hasattr guards, NOT modified by this milestone
- `heretek-swarm/heretek_swarm/actors/mixins/pattern_consumer.py` — uses hasattr guards, NOT modified
- `heretek-swarm/heretek_swarm/actors/mixins/health_reporting.py` — uses hasattr guards, NOT modified
- `heretek-swarm/heretek_swarm/actors/mixins/audit.py` — uses hasattr guards, NOT modified
- `heretek-swarm/heretek_swarm/actors/mixins/memory_access.py` — uses hasattr guards, NOT modified
- `tests/conftest.py` — mock_agent fixture using MagicMock (to be rewritten in S02)
- `tests/test_agent_factory.py` — uses monkeypatch + patch for Agent construction (to be rewritten in S02)

## Relevant Requirements

*(None formally captured — M003 is a quality-attribute/continuity milestone addressing silent-failure and test-fragility concerns.)*

## Scope

### In Scope

- S01: TypeError guards on MemoryMixin (3 methods), PatternMixin (2 methods), LearningMixin (1 method), TribunalMixin (6 methods). Also guard `_active_deliberations` in LearningMixin to prevent `len(None)` crash.
- S01: New `tests/test_mixin_guards.py` with per-mixin stub classes and TypeError assertion tests.
- S02: Protocol stub classes (StubAccessAnalyzer, StubPatternExtractor, StubTribunal, StubDeliberationEngine, StubLLMProvider) added to stubs.py.
- S02: AgentActor.__init__ accepts `access_analyzer`, `pattern_extractor`, `deliberation_engine`, `tribunal`, `llm_provider`, `event_mesh` as optional kwargs.
- S02: Existing monkey-patch tests rewritten to use constructor stub injection.
- S03: Integration smoke test verifying public mixin import path + constructor stub injection end-to-end.

### Out of Scope / Non-Goals

- hasattr-guarded mixins (Deliberation, PatternConsumer, HealthReporting, Audit, MemoryAccess) are NOT modified.
- No changes to hasattr-guarded mixin behavior for missing deps.
- No DI container or framework introduction.
- No changes to the swarms.Agent integration or the agent_factory module beyond test rewrites.
- No changes to the runtime initialization path (how deps get wired in production).

## Technical Constraints

- TypeError message format: `"{MethodName} requires {attribute_name}"`
- No method signature or return type changes on existing mixin methods
- hasattr-guarded mixins must continue working unchanged (regression-free)
- AgentActor must construct without errors when no stub kwargs are passed (backward compat)
- Old stubs.py module-level functions must still work as fallbacks

## Integration Points

- `AgentActor.__init__` — the single injection point for all stub deps; flows through MRO to all mixins
- `heretek_swarm.actors.stubs` — augmented with new protocol stub classes; existing functions kept as defaults
- `tests/test_mixin_guards.py` — new file (S01), uses minimal stub classes that inherit each mixin
- Existing test files — updated in S02 to use constructor stubs instead of monkey-patching

## Testing Requirements

- S01: pytest `tests/test_mixin_guards.py` must pass in isolation — each guarded method tested for TypeError when dep is None
- S01: TypeErrors must have consistent message format
- S01: Existing full test suite must pass with zero regressions (`pytest tests/ -x -q`)
- S01: Do NOT test hasattr-guarded mixins
- S02: Rewritten constructor-based tests must pass
- S02: Full test suite must pass
- S03: Integration smoke test must pass (public import path + agent construction with stubs)

## Acceptance Criteria

### S01 — Fail-fast guards
- LearningMixin.get_learning_status() does not crash on `len(None)` when `_active_deliberations` is None — guards correctly
- MemoryMixin._track_memory_access / _get_memory_tier / _prefetch_relevant raise TypeError when access_analyzer is None
- PatternMixin._emit_pattern / _consume_patterns raise TypeError when pattern_extractor is None
- TribunalMixin 6 methods raise TypeError when tribunal is None
- tests/test_mixin_guards.py exists with per-mixin test stubs and TypeError assertions
- All hasattr-guarded mixins continue working unchanged
- Full test suite passes

### S02 — First-class stub injection
- Protocol stub classes exist for all guardable deps in stubs.py
- AgentActor.__init__ accepts all deps as optional kwargs
- `AlphaAgent(access_analyzer=StubAccessAnalyzer())` works without monkey-patching
- `AlphaAgent()` constructs cleanly with no TypeError (deps default to None, guarded by S01)
- Existing monkey-patch tests rewritten to use constructor injection
- Full test suite passes

### S03 — Mixin exports + integration smoke test
- `from heretek_swarm.actors.mixins import *` works (all 10 mixins)
- Integration test: construct agent with stubs, call guarded method through public path, verify stub output
- Full test suite passes

## Open Questions

*(None — all decisions made during context-gathering interview)*
