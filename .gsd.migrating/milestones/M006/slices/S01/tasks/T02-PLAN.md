---
estimated_steps: 8
estimated_files: 4
skills_used: []
---

# T02: Map import dependencies between packages

Analyze all Python import statements across the codebase to build a dependency graph. Use grep/ripgrep to find all `import X` and `from X import Y` statements in `.py` files.

Key analyses:
1. Identify all imports from `src/` — especially `src/cli.py` importing from `heretek_swarm`
2. Catalog all `from heretek_swarm.actors import ...` type imports across the package
3. Find relative intra-package imports (`from .foo import bar`)
4. Identify any dead/redundant import paths left from prior restructures
5. Document which files in `tests/` import from which packages

Output as a structured file listing each file, its imports grouped by target package, and a dependency summary (which packages depend on which, which are leaf packages, cycle detection).

## Inputs

- `.gsd/milestones/M006/slices/S01/FILE_INVENTORY.md`
- `heretek-swarm/heretek_swarm/`
- `src/`
- `tests/`

## Expected Output

- `.gsd/milestones/M006/slices/S01/IMPORT_MAP.md`

## Verification

test -f .gsd/milestones/M006/slices/S01/IMPORT_MAP.md && grep -c "depends_on:" .gsd/milestones/M006/slices/S01/IMPORT_MAP.md > 0
