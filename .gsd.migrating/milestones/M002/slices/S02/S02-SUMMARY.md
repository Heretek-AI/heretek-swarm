---
id: S02
parent: M002
milestone: M002
provides:
  - schemas/actors.py as the canonical import path for all Pydantic actor models
requires:
  []
affects:
  []
key_files:
  - heretek-swarm/heretek_swarm/schemas/actors.py
  - heretek-swarm/heretek_swarm/actors/base/core.py
key_decisions:
  - schemas/actors.py re-exports from validation.agent_messages only; internal dataclass ActorMessage in actors/base/core.py is intentionally not re-exported to avoid name collision
  - Names absent from agent_messages.py are documented as stubs in _PLAN_REFERENCED_MISSING with clear AttributeError on access
patterns_established:
  - schemas/actors.py uses _PLAN_REFERENCED_MISSING set with __getattr__ for planned-but-missing names
  - backward-compat re-exports via actors/base/__init__.py keep existing ~40 callers unbroken
observability_surfaces:
  - none added — this is purely a refactoring/consolidation slice
drill_down_paths:
  []
duration: ""
verification_result: passed
completed_at: 2026-05-07T13:46:47.869Z
blocker_discovered: false
---

# S02: Move Pydantic models to schemas/ and refactor base/core.py

**Created schemas/actors.py as canonical Pydantic model entry point, refactored base/core.py import, and verified all ~40 callers remain backward-compatible with full pytest pass**

## What Happened

Slice S02 consolidated the Pydantic model import surface into a single canonical file: `heretek_swarm/schemas/actors.py`. This file re-exports all models from `validation/agent_messages.py`, documents planned-but-not-yet-implemented names in `_PLAN_REFERENCED_MISSING`, and provides `__getattr__` with clear error messages for missing stubs. The internal dataclass `ActorMessage` in `actors/base/core.py` is intentionally NOT re-exported to avoid name collision — a backward-compat alias imports the Pydantic version as `PydanticActorMessage` at module bottom.

Four tasks executed:
- **T01**: Created `schemas/actors.py` importing all Pydantic models from `validation.agent_messages`, with `_PLAN_REFERENCED_MISSING` for planned-but-absent names.
- **T02**: Updated `actors/base/core.py` to import Pydantic models from `schemas.actors` while preserving its internal `ActorMessage` dataclass. Added backward-compat comment and Pydantic import at module bottom.
- **T03**: Grepped ~40 files importing ActorMessage from old paths, confirmed all existing imports still resolve through `actors.base` re-exports. Verified both `schemas.actors.ActorMessage` (Pydantic) and `actors.base.core.ActorMessage` (dataclass) work cleanly and are distinct classes.
- **T04**: Full pytest suite passes (exit 0), final verification confirms `from heretek_swarm.schemas.actors import ActorMessage` prints correct Pydantic fields.

## Verification

All verification commands across 4 tasks passed. Full pytest suite exit code 0. Both import paths (schemas.actors Pydantic model, actors.base.core dataclass) verified as distinct and working.

## Requirements Advanced

None.

## Requirements Validated

None.

## New Requirements Surfaced

None.

## Requirements Invalidated or Re-scoped

None.

## Operational Readiness

None.

## Deviations

None.

## Known Limitations

None.

## Follow-ups

None.

## Files Created/Modified

None.
