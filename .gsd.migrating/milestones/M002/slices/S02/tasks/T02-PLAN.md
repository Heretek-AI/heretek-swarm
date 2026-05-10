---
estimated_steps: 7
estimated_files: 2
skills_used: []
---

# T02: Update actors/base/core.py to import Pydantic models from schemas.actors

Edit actors/base/core.py:
1. Remove all Pydantic model definitions (dataclass ActorMessage stays — it's internal, not the Pydantic one)
2. Keep ActorState and ActorStatus dataclasses
3. Keep AgentActor class
4. Add import: from heretek_swarm.schemas.actors import ActorMessage as PydanticActorMessage
5. Add backward-compat alias at module bottom: ActorMessage = PydanticActorMessage (so existing code that imports ActorMessage from actors.base.core still works)
6. Update _validate_message_content docstring to reference the schemas.actors import path

## Inputs

- `heretek-swarm/heretek_swarm/schemas/actors.py`

## Expected Output

- `heretek-swarm/heretek_swarm/actors/base/core.py`

## Verification

cd heretek-swarm && python -c "from heretek_swarm.actors.base.core import ActorMessage as AM; print('dataclass OK:', type(AM).__name__)" && python -c "from heretek_swarm.schemas.actors import ActorMessage as PA; print('Pydantic OK:', type(PA).__name__, PA.__bases__)"
