# S01: Audit scattered validation and model overlap

**Goal:** Map every validation function and Pydantic model in the codebase to its canonical home, producing a single markdown document that S02 and S03 will use as their refactoring guide.
**Demo:** A single document mapping each validation function to its canonical home

## Must-Haves

- heretek-swarm/heretek_swarm/slices/M002/S01-AUDIT.md exists and contains a complete mapping table for all validation functions and Pydantic models found.

## Proof Level

- This slice proves: contract

## Integration Closure

N/A — this is a research/audit slice only

## Verification

- Run the task and slice verification checks for this slice.

## Tasks

- [x] **T01: Audit validation functions and Pydantic models across codebase** `est:30m`
  Scan actors/validation.py, actors/mixins/validation.py, actors/base/core.py, schemas/, and any other relevant files. For each validation function found, record: function name, file path, what it validates, what imports/calls it, and recommended canonical home. For each Pydantic model found, record: model name, file path, what it validates, what imports/calls it, and recommended canonical home. Write results to AUDIT.md as a structured table plus narrative.
  - Files: `heretek-swarm/heretek_swarm/actors/validation.py`, `heretek-swarm/heretek_swarm/actors/mixins/validation.py`, `heretek-swarm/heretek_swarm/actors/base/core.py`, `heretek-swarm/heretek_swarm/schemas/__init__.py`, `heretek-swarm/heretek_swarm/schemas/external_call_log.py`
  - Verify: test -f "heretek-swarm/heretek_swarm/slices/M002/S01-AUDIT.md" && wc -l "heretek-swarm/heretek_swarm/slices/M002/S01-AUDIT.md" | awk '{exit ($1 < 30)}'

## Files Likely Touched

- heretek-swarm/heretek_swarm/actors/validation.py
- heretek-swarm/heretek_swarm/actors/mixins/validation.py
- heretek-swarm/heretek_swarm/actors/base/core.py
- heretek-swarm/heretek_swarm/schemas/__init__.py
- heretek-swarm/heretek_swarm/schemas/external_call_log.py
