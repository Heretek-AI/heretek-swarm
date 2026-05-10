---
estimated_steps: 6
estimated_files: 2
skills_used: []
---

# T03: Verify full test suite passes

After the changes above, run the full test suite. Fix any failures caused by import restructuring. Key things to check:
- All import paths in the ~40 files that reference actors.validation still work
- base/core.py's _validate_message_content() still works
- supervisor.py, steward.py, explorer.py, sentinel/agent.py still import and use ValidationMixin correctly

Run: pytest tests/ -x -q --tb=short

If any test fails, fix the import in the failing file. The backward-compat shim in actors/validation.py should make all existing imports continue to work.

## Inputs

- `T01`
- `T02`

## Expected Output

- `heretek-swarm/heretek_swarm/actors/validation.py`
- `heretek-swarm/heretek_swarm/actors/mixins/validation.py`

## Verification

cd C:/Users/Derek/Desktop/heretek-swarm && python -m pytest tests/ -x -q --tb=short
