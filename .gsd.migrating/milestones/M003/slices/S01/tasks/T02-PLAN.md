---
estimated_steps: 8
estimated_files: 2
skills_used: []
---

# T02: Harden TribunalMixin guards and create test_mixin_guards.py

**Steps:**
1. tribunal.py: Add TypeError guards to all 6 methods using `if not self.tribunal: raise TypeError(...)`
2. Create tests/test_mixin_guards.py with minimal stubs inheriting each mixin, test each guarded method raises TypeError
3. Include happy-path regression test for LearningMixin
4. Do NOT test hasattr-guarded mixins

**Must-haves:**
- TypeError message format consistent with T01
- Tests pass in isolation: pytest tests/test_mixin_guards.py -x -q

## Inputs

- `heretek-swarm/heretek_swarm/actors/mixins/tribunal.py`

## Expected Output

- `heretek-swarm/heretek_swarm/actors/mixins/tribunal.py`
- `tests/test_mixin_guards.py`

## Verification

pytest tests/test_mixin_guards.py -x -q 2>&1 | tail -10
