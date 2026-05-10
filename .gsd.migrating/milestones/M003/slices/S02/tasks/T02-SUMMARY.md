---
id: T02
parent: S02
milestone: M003
key_files:
  - heretek-swarm/heretek_swarm/actors/base/core.py
key_decisions:
  - Mixin deps (access_analyzer et al.) use public instance attrs (self.*) for MRO-visible mixin access; core deps (llm_provider, event_mesh) use private names (self._*) since they're consumed internally
duration: 
verification_result: passed
completed_at: 2026-05-08T00:23:42.000Z
blocker_discovered: false
---

# T02: Update AgentActor.__init__ to accept all 6 deps as optional constructor kwargs (access_analyzer, pattern_extractor, deliberation_engine, tribunal, llm_provider, event_mesh)

**Update AgentActor.__init__ to accept all 6 deps as optional constructor kwargs (access_analyzer, pattern_extractor, deliberation_engine, tribunal, llm_provider, event_mesh)**

## What Happened

Modified `AgentActor.__init__` in `heretek_swarm/actors/base/core.py` to accept 6 new optional keyword arguments: `access_analyzer`, `pattern_extractor`, `deliberation_engine`, `tribunal`, `llm_provider`, `event_mesh`. All default to None.

Key implementation choices:
1. **Mixin deps (access_analyzer, pattern_extractor, deliberation_engine, tribunal)** — set as public instance attributes (`self.access_analyzer`, etc.) so they're accessible to mixin methods via the MRO. Stub classes from T01 satisfy the `X | None` type shape, so S01's fail-fast TypeError guards will fire only if guarded methods are called without wiring — correct behavior.
2. **Core deps (llm_provider, event_mesh)** — kept as private names (`self._llm_provider`, `self._event_mesh`) since they're consumed internally by core methods, not mixins. Use `value or fallback()` pattern: when a kwarg is provided (truthy), it replaces the module-level default; when None or omitted, the existing `_actor_stubs.get_*()` fallbacks are used.
3. **Backward compatibility** — existing callers that don't pass these kwargs continue to use the same module-level stub fallbacks (`_actor_stubs.get_llm_provider()`, `_actor_stubs.get_nats_event_mesh()`). The `import heretek_swarm.actors.stubs as _actor_stubs` and `from heretek_swarm.actors.stubs import get_db_pool` lines are untouched.
4. **Type annotations** — all 6 new kwargs are typed as `Any | None = None` to avoid requiring `TYPE_CHECKING` imports for the real types, which would introduce circular dependency risk.
5. **Docstring** — Added an Args entry for each new kwarg explaining its purpose and fallback behavior.

## Verification

pytest tests/test_actor_routing.py -x -q (7/7 passing) + manual smoke test confirming all 6 stubs inject correctly, fallback defaults work, and stub provider returns canned responses

## Verification Evidence

| # | Command | Exit Code | Verdict | Duration |
|---|---------|-----------|---------|----------|
| 1 | `pytest tests/test_actor_routing.py -x -q --no-header` | 0 | ✅ pass | 3200ms |
| 2 | `python -c smoke_test_injection.py` | 0 | ✅ pass | 1500ms |

## Deviations

None.

## Known Issues

None.

## Files Created/Modified

- `heretek-swarm/heretek_swarm/actors/base/core.py`
