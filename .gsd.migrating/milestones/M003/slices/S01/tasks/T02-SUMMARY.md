---
id: T02
parent: S01
milestone: M003
key_files:
  - heretek-swarm/heretek_swarm/actors/mixins/tribunal.py
  - tests/test_mixin_guards.py
key_decisions:
  - TribunalMixin return types changed from TribunalCase|None to TribunalCase (and similar) since the fail-fast guard means None is never returned from the guard check — callers downstream are responsible for try/except, but existing catch-all except blocks still handle any runtime failures from the tribunal calls
duration: 
verification_result: passed
completed_at: 2026-05-07T21:07:19.876Z
blocker_discovered: false
---

# T02: Harden TribunalMixin with fail-fast TypeError guards and create test_mixin_guards.py covering all 4 guarded mixins plus LearningMixin happy-path regression

**Harden TribunalMixin with fail-fast TypeError guards and create test_mixin_guards.py covering all 4 guarded mixins plus LearningMixin happy-path regression**

## What Happened

Applied fail-fast TypeError guards to all 6 methods in TribunalMixin (tribunal.py) that silently returned None or [] when self.tribunal was None. Each guard now raises TypeError with the consistent message format "{method} requires tribunal". This replaces silent no-op behavior for _submit_tribunal_case, _submit_tribunal_evidence, _get_tribunal_case, _issue_tribunal_ruling, _get_tribunal_precedents, and _find_similar_precedents.

Created tests/test_mixin_guards.py containing 12 tests covering all guarded methods across the 4 mixins with explicit dependency attributes:
- 6 TribunalMixin async tests (each raises TypeError for method when tribunal is None)
- 3 MemoryMixin tests (_track_memory_access, _get_memory_tier, _prefetch_relevant)
- 2 PatternMixin tests (_emit_pattern, _consume_patterns)
- 1 LearningMixin happy-path regression test (get_learning_status with _active_deliberations=None returns 0 instead of crashing)

The test file uses minimal stubs that subclass each mixin with None dependencies, avoiding any mocking of the production Tribunal or other real collaborators. Per the plan, hasattr-guarded mixins are not tested.

## Verification

12/12 mixin guard tests pass in isolation. Full test suite (616 passed, 1 skipped — integration) also passes cleanly with no regressions.

## Verification Evidence

| # | Command | Exit Code | Verdict | Duration |
|---|---------|-----------|---------|----------|
| 1 | `pytest tests/test_mixin_guards.py -x -q` | 0 | ✅ pass | 12000ms |
| 2 | `pytest tests/ -q 2>/dev/null | tail -3` | 0 | ✅ pass | 95000ms |

## Deviations

None.

## Known Issues

None.

## Files Created/Modified

- `heretek-swarm/heretek_swarm/actors/mixins/tribunal.py`
- `tests/test_mixin_guards.py`
