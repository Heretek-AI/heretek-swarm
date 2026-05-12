---
estimated_steps: 10
estimated_files: 1
skills_used: []
---

# T01: Rewrite docs/ARCHITECTURE.md with current package paths and structure

The existing docs/ARCHITECTURE.md (27KB) is stale. It references src/heretek_swarm/ paths that don't exist in the current tree, points to triad.py instead of actors/triad/agent.py, and predates the mixins extraction and subpackage refactors.

Requirements:
- Update ALL file paths to use current locations (e.g. heretek-swarm/heretek_swarm/actors/base/core.py instead of src/heretek_swarm/actors/base.py)
- Fix actor tier tables to show correct file locations (subpackages vs flat files)
- Add a 'Package Structure' section showing the actual directory tree under heretek-swarm/heretek_swarm/
- Add an 'Actor Base Class & Mixins' section that explains the AgentActor hierarchy and the 10 mixins (what each does and which agents use them)
- Update the Memory System and Event Mesh sections to reference current paths
- Remove or update the stale health score dashboard that references old component names
- Keep the existing TOC structure (System Overview, Actor Architecture, Memory System, Event Mesh, Configuration, Security, Observability)
- Run a grep to verify no stale src/ paths remain after editing

## Inputs

- `heretek-swarm/docs/ARCHITECTURE.md`
- `heretek-swarm/heretek_swarm/actors/__init__.py`
- `heretek-swarm/heretek_swarm/actors/base/core.py`
- `heretek-swarm/heretek_swarm/actors/mixins/__init__.py`

## Expected Output

- `heretek-swarm/docs/ARCHITECTURE.md`

## Verification

cd /Derek/Desktop/heretek-swarm && grep -c '^## ' docs/ARCHITECTURE.md && grep -c 'heretek-swarm/heretek_swarm' docs/ARCHITECTURE.md && ! grep -q 'TBD\|TODO\|src/heretek_swarm/' docs/ARCHITECTURE.md
