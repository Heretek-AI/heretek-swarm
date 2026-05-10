---
estimated_steps: 7
estimated_files: 1
skills_used: []
---

# T02: Update AgentActor.__init__ to accept all deps as optional constructor kwargs

Modify `AgentActor.__init__` in `heretek_swarm/actors/base/core.py` to accept 6 new optional keyword arguments: `access_analyzer`, `pattern_extractor`, `deliberation_engine`, `tribunal`, `llm_provider`, `event_mesh`. All default to None.

Key implementation rules:
1. When a kwarg is provided (not None), set it as an instance attribute directly (e.g. `self.access_analyzer = access_analyzer`). This makes it available to mixin methods via the MRO without the mixin needing to capture it.
2. When a kwarg is NOT provided (None), keep the existing fallback behavior — for `_llm_provider` and `_event_mesh` this means calling the module-level `_actor_stubs.get_llm_provider()` / `_actor_stubs.get_nats_event_mesh()`. For mixin deps, the class-level `None` will remain as default, which means the S01 TypeError guards will fire if guarded methods are called — correct behavior.
3. Do NOT remove or modify the existing `import heretek_swarm.actors.stubs as _actor_stubs` line or the `from heretek_swarm.actors.stubs import get_db_pool` line — they are used by state_management.py.
4. Type each new kwarg as `Any | None = None` to avoid requiring TYPE_CHECKING imports for the real types (which would introduce circular dependency risk).
5. Add a docstring entry for each new kwarg under the Args section.

## Inputs

- `heretek_swarm/actors/base/core.py`
- `heretek_swarm/actors/stubs.py`

## Expected Output

- `heretek_swarm/actors/base/core.py`

## Verification

pytest tests/test_actor_routing.py -x -q --no-header 2>&1 | tail -5
