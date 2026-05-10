---
estimated_steps: 6
estimated_files: 2
skills_used: []
---

# T02: Fix imports referencing deleted shims

Scan the entire codebase for any import statements that reference the 10 deleted shim files directly (e.g. `from heretek_swarm.actors import arbiter`). Update those imports to use the canonical subpackage path (e.g. `from heretek_swarm.actors.arbiter import ArbiterAgent`) so they resolve from the authoritative subpackage instead.

The main import pattern to fix:
- `from heretek_swarm.actors import arbiter` → `from heretek_swarm.actors.arbiter import ArbiterAgent`
- `from heretek_swarm.actors import base` → `from heretek_swarm.actors.base import BaseAgent`
- (and so on for all 10)

If no imports reference the deleted files (most shims are only re-exported internally), this task is a no-op — verify that is acceptable.

## Inputs

- None specified.

## Expected Output

- `Any files updated to fix broken imports`

## Verification

python -c "import heretek_swarm.actors" exits 0
