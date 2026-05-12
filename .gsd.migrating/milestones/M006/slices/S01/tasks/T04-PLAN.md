---
estimated_steps: 18
estimated_files: 1
skills_used: []
---

# T04: Write actionable migration plan (M006-PLAN.md)

Synthesize the file inventory, import map, and CI impact analysis into a single actionable migration plan document at `.gsd/milestones/M006/M006-PLAN.md`.

The plan must specify:

1. **Target directory structure**: Exact target layout (e.g., `backend/heretek_swarm/{actors,schemas,validation,...}`, `backend/Dockerfile`, `backend/pyproject.toml`)

2. **File move catalog**: For every source file in the current structure, specify:
   - Current path → target path
   - Action type: `move` (relocate), `merge` (combine into another file), `delete` (if no longer needed), `keep` (stays in place)
   - Any import rewrite needed in the file's content
   - Any import rewrite needed in OTHER files that import this file

3. **Import rewrite catalog**: For every cross-reference between the old and new structure:
   - Current import statement → new import statement
   - Files affected

4. **CI/deployment update catalog**: For every CI file and deployment config:
   - Current line/path → new line/path
   - File to edit

5. **Execution order**: Dependencies between file moves (e.g., move the package directory before updating CI paths). Which files can move in parallel vs must be sequential.

6. **Rollback plan**: How to reverse the migration if something goes wrong.

7. **Verification checklist**: Commands to run after migration to verify nothing is broken (pytest, ruff, mypy, build, import tests).

Each entry must be concrete and machine-actionable — not aspirational. Use exact paths with backticks.

## Inputs

- `.gsd/milestones/M006/slices/S01/FILE_INVENTORY.md`
- `.gsd/milestones/M006/slices/S01/IMPORT_MAP.md`
- `.gsd/milestones/M006/slices/S01/CI_IMPACT.md`
- `pyproject.toml`
- `docker-compose.yml`
- `heretek-swarm/Dockerfile`

## Expected Output

- `.gsd/milestones/M006/M006-PLAN.md`

## Verification

test -f .gsd/milestones/M006/M006-PLAN.md && grep -c "backend/" .gsd/milestones/M006/M006-PLAN.md > 0 && grep -c "current path" .gsd/milestones/M006/M006-PLAN.md > 0
