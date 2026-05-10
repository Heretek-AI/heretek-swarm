# S01: Audit actor file pairs and determine canonical source

**Goal:** A complete, machine-parseable map of every actor file in heretek_swarm/actors/, classifying each as canonical (standalone implementation) or shim (thin re-export from a subpackage), with canonical source paths for downstream slices.
**Demo:** A complete map of which actor files are authoritative

## Must-Haves

- An audit artifact (ACTOR_AUDIT.md) exists at `.gsd/milestones/M001/slices/S01/ACTOR_AUDIT.md` that: (1) lists every .py file in heretek-swarm/heretek_swarm/actors/ with line count, role classification, and authoritative path; (2) for every actor with both a flat .py and a subpackage/, identifies which is the authoritative source; (3) is accurate enough that S02 can proceed without re-reading any source files.

## Verification

- Run the task and slice verification checks for this slice.

## Tasks

- [x] **T01: Audit every actor file in heretek_swarm/actors/ and produce the canonical map** `est:30m`
  Scan heretek-swarm/heretek_swarm/actors/ and produce a complete inventory.
  - Files: `heretek-swarm/heretek_swarm/actors/`
  - Verify: grep -c "^| " .gsd/milestones/M001/slices/S01/ACTOR_AUDIT.md returns >= 20 (table rows for every actor)

## Files Likely Touched

- heretek-swarm/heretek_swarm/actors/
