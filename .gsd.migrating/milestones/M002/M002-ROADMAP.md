# M002: Unify validation into a single entry point

**Vision:** One validation module, one ValidationMixin, one Pydantic model location. Currently validation logic is duplicated across actors/validation.py, actors/mixins/validation.py, and actors/base/core.py — with subtle behavioral differences between them. After this milestone, every message validation flows through a single function and all Pydantic models live in schemas/.

## Success Criteria

- All Pydantic models for actors live in schemas/actors.py
- actors/base/core.py delegates validation to actors/validation.py only
- Only one ValidationMixin exists in the codebase
- pytest tests/ passes without validation-related errors

## Slices

- [x] **S01: S01** `risk:low` `depends:[]`
  > After this: A single document mapping each validation function to its canonical home

- [x] **S02: S02** `risk:medium` `depends:[]`
  > After this: from heretek_swarm.schemas.actors import ActorMessage works

- [x] **S03: S03** `risk:low` `depends:[]`
  > After this: Only one ValidationMixin exists in the codebase

## Boundary Map

Not provided.
