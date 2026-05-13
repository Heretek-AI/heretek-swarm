---
estimated_steps: 1
estimated_files: 2
skills_used: []
---

# T04: Fix ruff lint violations

Run ruff check backend/heretek_swarm/ tests/. Fix all violations. Focus on import-related issues and any new lint rules that have been added since M008.

## Inputs

- `pyproject.toml (ruff config)`

## Expected Output

- `ruff check — zero violations`

## Verification

cd backend && ruff check heretek_swarm tests --quiet
