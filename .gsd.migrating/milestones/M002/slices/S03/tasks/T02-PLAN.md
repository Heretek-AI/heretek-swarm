---
estimated_steps: 3
estimated_files: 2
skills_used: []
---

# T02: Verify full test suite passes

After T01's refactoring, run the full pytest suite and confirm everything passes. Since backward-compat shims are in place, all ~40 existing callers work unchanged.

**Run:** `cd C:/Users/Derek/Desktop/heretek-swarm && python -m pytest tests/ -x -q --tb=short`

If any test fails, investigate the import path in the failing file and fix it. The actors.validation backward-compat import should cover most cases, but a test that directly imports IMMUTABLE_RULES by name might need its import updated.

## Inputs

- `T01`

## Expected Output

- `heretek-swarm/heretek_swarm/actors/mixins/validation.py`
- `heretek-swarm/heretek_swarm/actors/validation.py`

## Verification

cd C:/Users/Derek/Desktop/heretek-swarm && python -m pytest tests/ -x -q --tb=short 2>&1 | tail -20
