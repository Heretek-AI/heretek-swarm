---
estimated_steps: 1
estimated_files: 5
skills_used: []
---

# T01: Audit validation functions and Pydantic models across codebase

Scan actors/validation.py, actors/mixins/validation.py, actors/base/core.py, schemas/, and any other relevant files. For each validation function found, record: function name, file path, what it validates, what imports/calls it, and recommended canonical home. For each Pydantic model found, record: model name, file path, what it validates, what imports/calls it, and recommended canonical home. Write results to AUDIT.md as a structured table plus narrative.

## Inputs

- None specified.

## Expected Output

- `heretek-swarm/heretek_swarm/slices/M002/S01-AUDIT.md`

## Verification

test -f "heretek-swarm/heretek_swarm/slices/M002/S01-AUDIT.md" && wc -l "heretek-swarm/heretek_swarm/slices/M002/S01-AUDIT.md" | awk '{exit ($1 < 30)}'
