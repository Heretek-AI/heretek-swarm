# M002: Unify validation into a single entry point

**Vision:** One validation module, one ValidationMixin, one Pydantic model location. Currently validation logic is duplicated across actors/validation.py, actors/mixins/validation.py, and actors/base/core.py — with subtle behavioral differences between them. After this milestone, every message validation flows through a single function and all Pydantic models live in schemas/.

## Success Criteria

- All Pydantic models for actors live in schemas/actors.py
- actors/base/core.py delegates validation to actors/validation.py only
- Only one ValidationMixin exists in the codebase
- pytest tests/ passes without validation-related errors

## Slices

- [ ] **S01: Audit scattered validation and model overlap** `risk:low` `depends:[]`
  > After this: A single document mapping each validation function to its canonical home

- [ ] **S02: Move Pydantic models to schemas/ and refactor base/core.py** `risk:medium` `depends:[S01]`
  > After this: from heretek_swarm.schemas.actors import ActorMessage works

- [ ] **S03: Consolidate ValidationMixin and deprecate duplicates** `risk:low` `depends:[S02]`
  > After this: Only one ValidationMixin exists in the codebase

## Boundary Map

Not provided.
