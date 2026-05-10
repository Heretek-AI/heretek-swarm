---
estimated_steps: 9
estimated_files: 3
skills_used: []
---

# T01: Add fail-fast TypeError guards to LearningMixin, MemoryMixin, and PatternMixin

**Steps:**
1. learning.py: Guard `self._active_deliberations` with `or {}`, guard all attribute accesses in dict literal
2. memory.py: Change silent returns to `raise TypeError(...)` in all 3 methods
3. pattern.py: Change silent returns to `raise TypeError(...)`, guard `self._pattern_emitted`
4. Do NOT modify hasattr-guarded mixins (HealthReporting, MemoryAccess, PatternConsumer, Deliberation, Audit)

**Must-haves:**
- TypeError message format: "{MethodName} requires {attribute_name}"
- No method signature or return type changes
- LearningMixin guards are priority (only crash footgun)

## Inputs

- `heretek-swarm/heretek_swarm/actors/mixins/learning.py`
- `heretek-swarm/heretek_swarm/actors/mixins/memory.py`
- `heretek-swarm/heretek_swarm/actors/mixins/pattern.py`

## Expected Output

- `heretek-swarm/heretek_swarm/actors/mixins/learning.py`
- `heretek-swarm/heretek_swarm/actors/mixins/memory.py`
- `heretek-swarm/heretek_swarm/actors/mixins/pattern.py`

## Verification

pytest tests/ -x -q --tb=short 2>&1 | tail -20
