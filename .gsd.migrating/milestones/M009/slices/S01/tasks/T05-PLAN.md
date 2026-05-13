---
estimated_steps: 1
estimated_files: 1
skills_used: []
---

# T05: Fix mypy strict mode type errors

Run mypy backend/heretek_swarm in strict mode. Fix all type errors. Many type errors may have existed pre-restructure but were never caught — fix them all.

## Inputs

- `pyproject.toml (mypy config)`

## Expected Output

- `mypy — zero type errors (strict mode)`

## Verification

cd backend && mypy heretek_swarm --strict
