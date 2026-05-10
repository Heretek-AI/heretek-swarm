---
estimated_steps: 5
estimated_files: 1
skills_used: []
---

# T03: Find and update all callers importing ActorMessage from old paths

Use grep to find all files importing ActorMessage from actors.base.core or actors.validation or validation.agent_messages. For each file:
1. Update the import to use heretek_swarm.schemas.actors
2. If the file uses the dataclass ActorMessage (from actors.base.core), update the import name to avoid collision
3. Add from heretek_swarm.schemas.actors import ActorMessage as PydanticActorMessage if the Pydantic version is needed
Run grep: grep -r "from heretek_swarm.actors" --include="*.py" | grep -i "import.*ActorMessage\|import.*MessageType" | grep -v __pycache__

## Inputs

- `heretek-swarm/heretek_swarm/schemas/actors.py`
- `heretek-swarm/heretek_swarm/actors/base/core.py`

## Expected Output

- `(files found by grep that need updating)`

## Verification

cd heretek-swarm && python -c "from heretek_swarm.schemas.actors import ActorMessage; print('ActorMessage from schemas OK')" && python -c "from heretek_swarm.actors.base.core import AgentActor; print('AgentActor OK')" && python -c "from heretek_swarm.actors.validation import validate_message; print('validate_message OK')"
