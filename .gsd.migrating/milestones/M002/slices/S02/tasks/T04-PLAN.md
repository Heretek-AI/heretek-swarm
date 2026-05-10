---
estimated_steps: 5
estimated_files: 2
skills_used: []
---

# T04: Run pytest to verify no import or validation errors

Run the full test suite to ensure the refactoring introduces no regressions:
1. cd heretek-swarm && python -m pytest tests/ -x -q --tb=short 2>&1 | head -50
2. If there are import errors, fix them
3. If there are ValidationError failures, ensure they existed before (regression check)
4. Final verification: python -c "from heretek_swarm.schemas.actors import ActorMessage, MESSAGE_TYPES; print('ActorMessage fields:', list(ActorMessage.model_fields.keys()))"

## Inputs

- `heretek-swarm/heretek_swarm/schemas/actors.py`

## Expected Output

- `pytest exit code 0`

## Verification

cd heretek-swarm && python -m pytest tests/ -x -q --tb=short; echo "EXIT:$?"
