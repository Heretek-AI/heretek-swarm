# S01: Add fail-fast guards to all mixin methods

**Goal:** Every mixin method that depends on an external dependency attribute raises TypeError when that attribute is None, instead of silently no-oping or crashing with confusing AttributeError.
**Demo:** Bad()._validate_message({}) raises TypeError

## Must-Haves

- 1. LearningMixin.get_learning_status() no longer crashes with AttributeError on `len(None)` when deps are None — guards all attribute accesses
- 2. MemoryMixin._track_memory_access/_get_memory_tier/_prefetch_relevant raise TypeError when access_analyzer is None
- 3. PatternMixin._emit_pattern/_consume_patterns raise TypeError when pattern_extractor is None
- 4. TribunalMixin 6 methods raise TypeError when tribunal is None
- 5. All other mixins using hasattr capability checks left unchanged
- 6. Tests exist proving TypeError is raised for each guard

## Proof Level

- This slice proves: contract — unit tests verify TypeError behavior; no real runtime infra required

## Integration Closure

No new wiring. This slice only adds guards inside existing mixin methods. Upstream agents that pass None will now get TypeError instead of silent data loss — S02 restores ability to pass None via stub injection.

## Verification

- Run the task and slice verification checks for this slice.

## Tasks

- [x] **T01: Add fail-fast TypeError guards to LearningMixin, MemoryMixin, and PatternMixin** `est:1h`
  **Steps:**
  1. learning.py: Guard `self._active_deliberations` with `or {}`, guard all attribute accesses in dict literal
  2. memory.py: Change silent returns to `raise TypeError(...)` in all 3 methods
  3. pattern.py: Change silent returns to `raise TypeError(...)`, guard `self._pattern_emitted`
  4. Do NOT modify hasattr-guarded mixins (HealthReporting, MemoryAccess, PatternConsumer, Deliberation, Audit)
  - Files: `heretek-swarm/heretek_swarm/actors/mixins/learning.py`, `heretek-swarm/heretek_swarm/actors/mixins/memory.py`, `heretek-swarm/heretek_swarm/actors/mixins/pattern.py`
  - Verify: pytest tests/ -x -q --tb=short 2>&1 | tail -20

- [x] **T02: Harden TribunalMixin guards and create test_mixin_guards.py** `est:1h`
  **Steps:**
  1. tribunal.py: Add TypeError guards to all 6 methods using `if not self.tribunal: raise TypeError(...)`
  2. Create tests/test_mixin_guards.py with minimal stubs inheriting each mixin, test each guarded method raises TypeError
  3. Include happy-path regression test for LearningMixin
  4. Do NOT test hasattr-guarded mixins
  - Files: `heretek-swarm/heretek_swarm/actors/mixins/tribunal.py`, `tests/test_mixin_guards.py`
  - Verify: pytest tests/test_mixin_guards.py -x -q 2>&1 | tail -10

## Files Likely Touched

- heretek-swarm/heretek_swarm/actors/mixins/learning.py
- heretek-swarm/heretek_swarm/actors/mixins/memory.py
- heretek-swarm/heretek_swarm/actors/mixins/pattern.py
- heretek-swarm/heretek_swarm/actors/mixins/tribunal.py
- tests/test_mixin_guards.py
