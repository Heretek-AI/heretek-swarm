---
id: T01
parent: S01
milestone: M003
key_files:
  - heretek-swarm/heretek_swarm/actors/mixins/learning.py
  - heretek-swarm/heretek_swarm/actors/mixins/memory.py
  - heretek-swarm/heretek_swarm/actors/mixins/pattern.py
key_decisions:
  - PatternMixin._pattern_emitted=None guard uses `or set()` for the membership check — the `.add()` call later is only reached when pattern_extractor is set, so no initialization is needed there
duration: 
verification_result: passed
completed_at: 2026-05-07T20:42:38.656Z
blocker_discovered: false
---

# T01: Added fail-fast TypeError guards to LearningMixin, MemoryMixin, and PatternMixin — silent no-ops and None crashes replaced with explicit TypeError on missing required dependencies

**Added fail-fast TypeError guards to LearningMixin, MemoryMixin, and PatternMixin — silent no-ops and None crashes replaced with explicit TypeError on missing required dependencies**

## What Happened

Applied three categories of fail-fast guards across the three mixins:

**LearningMixin** (`learning.py`): Changed `len(self._active_deliberations)` to `len(self._active_deliberations or {})` — this was the only crash footgun, where `_active_deliberations = None` caused `TypeError: object of type 'NoneType' has no len()` at runtime. All other attribute accesses in the dict literal were already guarded by `if self.X else` ternaries, so only this one guard was needed.

**MemoryMixin** (`memory.py`): All three methods (`_track_memory_access`, `_get_memory_tier`, `_prefetch_relevant`) previously silently returned default values (None, AccessTier.COLD, []) when `access_analyzer` was None. Changed all three to `raise TypeError("METHOD requires access_analyzer")`. This is the core behavioral enforcement — callers must ensure the dependency is wired before calling these methods.

**PatternMixin** (`pattern.py`): Both `_emit_pattern` and `_consume_patterns` previously silently returned (None, []) when `pattern_extractor` was None. Changed both to raise TypeError. Additionally, `_pattern_emitted = None` would crash on `item_id in self._pattern_emitted` — guarded with `(self._pattern_emitted or set())`. Note: the `.add()` call later still requires real initialization, but that codepath is only reached when `pattern_extractor` is set, so it's correct.

**Not modified** (per plan): HealthReportingMixin, MemoryAccessMixin, PatternConsumerMixin, DeliberationMixin, AuditMixin — these use hasattr capability checks for optional subsystems and are correctly left alone.

All 6 TypeError guards were verified via direct Python invocation. Full test suite (604 tests) passes cleanly.

## Verification

1. Direct Python invocation verified each TypeError fires with correct message format "{MethodName} requires {attribute_name}"
2. LearningMixin get_learning_status confirmed to work with _active_deliberations=None (returns 0 instead of crashing)
3. Full test suite: python -m pytest tests/ -x -q → 604 passed, 1 skipped (integration test requiring HERETEK_RUN_INTEGRATION=1)

## Verification Evidence

| # | Command | Exit Code | Verdict | Duration |
|---|---------|-----------|---------|----------|
| 1 | `python -c 'MemoryMixin TypeError tests'` | 0 | ✅ pass | 500ms |
| 2 | `python -c 'LearningMixin guard test'` | 0 | ✅ pass | 500ms |
| 3 | `pytest tests/ -x -q` | 0 | ✅ pass | 45000ms |

## Deviations

None.

## Known Issues

None.

## Files Created/Modified

- `heretek-swarm/heretek_swarm/actors/mixins/learning.py`
- `heretek-swarm/heretek_swarm/actors/mixins/memory.py`
- `heretek-swarm/heretek_swarm/actors/mixins/pattern.py`
