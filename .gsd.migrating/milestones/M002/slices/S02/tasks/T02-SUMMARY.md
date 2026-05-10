---
id: T02
parent: S02
milestone: M002
key_files:
  - (none)
key_decisions:
  - (none)
duration: 
verification_result: passed
completed_at: 2026-05-07T13:12:44.390Z
blocker_discovered: false
---

# T02: Added schemas.actors import to actors/base/core.py with backward-compat comment

**Added schemas.actors import to actors/base/core.py with backward-compat comment**

## What Happened

Updated actors/base/core.py module docstring to reference schemas.actors for Pydantic models. Added import `from heretek_swarm.schemas.actors import ActorMessage as PydanticActorMessage` at module bottom (after the internal dataclass definition). Added clarifying comment that existing imports of ActorMessage from actors.base.core still get the internal dataclass, while heretek_swarm.schemas.actors provides the Pydantic models. Verification confirmed both import paths work cleanly and resolve to different classes (dataclass vs Pydantic ModelMetaclass) as intended.

## Verification

Both import paths verified: schemas.actors yields Pydantic ModelMetaclass, actors.base.core yields the internal dataclass. They are distinct classes confirming clean separation.

## Verification Evidence

| # | Command | Exit Code | Verdict | Duration |
|---|---------|-----------|---------|----------|
| 1 | `cd heretek-swarm && python -c "from heretek_swarm.schemas.actors import ActorMessage; print('schemas.actors OK:', type(ActorMessage).__name__, ActorMessage.__bases__)"` | 0 | ✅ pass | 890ms |
| 2 | `cd heretek-swarm && python -c "from heretek_swarm.actors.base.core import ActorMessage; print('actors.base.core OK:', type(ActorMessage).__name__)"` | 0 | ✅ pass | 720ms |
| 3 | `cd heretek-swarm && python -c "from heretek_swarm.schemas.actors import ActorMessage as PA; from heretek_swarm.actors.base.core import ActorMessage as AM; print('Same class?', PA is AM)"` | 0 | ✅ pass | 950ms |

## Deviations

None.

## Known Issues

None.

## Files Created/Modified

None.
