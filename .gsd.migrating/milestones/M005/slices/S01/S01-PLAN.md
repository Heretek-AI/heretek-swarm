# S01: Write ARCHITECTURE.md and actors/README.md

**Goal:** Produce an up-to-date ARCHITECTURE.md and a practical actors/README.md so a new contributor can understand the system from docs alone
**Demo:** A new contributor can understand the system from docs

## Must-Haves

- docs/ARCHITECTURE.md exists with 5+ sections, all file paths point to the current heretek-swarm/heretek_swarm/ tree\n- docs/actors/README.md exists with 4+ sections including a code example and explanation of flat-file vs subpackage convention\n- No stale src/ paths remain in ARCHITECTURE.md\n- No TBD/TODO markers in either document

## Proof Level

- This slice proves: contract

## Integration Closure

Documentation-only slice. No new wiring. Upstream surfaces consumed: the existing docs/ARCHITECTURE.md will be rewritten; docs/actors/README.md is new.

## Verification

- Run the task and slice verification checks for this slice.

## Tasks

- [x] **T01: Rewrite docs/ARCHITECTURE.md with current package paths and structure** `est:45m`
  The existing docs/ARCHITECTURE.md (27KB) is stale. It references src/heretek_swarm/ paths that don't exist in the current tree, points to triad.py instead of actors/triad/agent.py, and predates the mixins extraction and subpackage refactors.
  - Files: `heretek-swarm/docs/ARCHITECTURE.md`
  - Verify: cd /Derek/Desktop/heretek-swarm && grep -c '^## ' docs/ARCHITECTURE.md && grep -c 'heretek-swarm/heretek_swarm' docs/ARCHITECTURE.md && ! grep -q 'TBD\|TODO\|src/heretek_swarm/' docs/ARCHITECTURE.md

- [x] **T02: Create docs/actors/README.md with practical agent creation guide** `est:45m`
  Create a practical, example-driven guide at docs/actors/README.md that shows a new contributor how to add a custom agent.
  - Files: `heretek-swarm/docs/actors/README.md`
  - Verify: cd /Derek/Desktop/heretek-swarm && test -f docs/actors/README.md && grep -c '^## ' docs/actors/README.md && grep -q 'AgentActor' docs/actors/README.md && grep -q '__init__' docs/actors/README.md

## Files Likely Touched

- heretek-swarm/docs/ARCHITECTURE.md
- heretek-swarm/docs/actors/README.md
