# S01: Audit actor file pairs and determine canonical source — UAT

**Milestone:** M001
**Written:** 2026-05-07T12:16:26.056Z

# S01 UAT — Actor File Audit

## Type
- **What this UAT proves:** The canonical map exists, is complete (≥20 actor rows), and is accurate enough for S02 to proceed without re-reading source files.
- **What this UAT does NOT prove:** Live import resolution, runtime behavior, or the correctness of any individual agent implementation.

## Preconditions
- `.gsd/milestones/M001/slices/S01/ACTOR_AUDIT.md` exists at the expected path.

## Test Cases

### TC01: Audit artifact exists and is non-empty
1. Read `.gsd/milestones/M001/slices/S01/ACTOR_AUDIT.md`
2. Assert file is non-empty (size > 0 bytes)
3. Assert file contains the header `# Actor File Audit`
- **Expected:** Artifact loads with no errors

### TC02: Markdown table has ≥ 20 actor rows
1. Count lines matching the table row pattern `^| `
2. Assert count ≥ 20
- **Expected:** grep returns ≥ 20; S01 plan requires ≥ 20 rows

### TC03: JSON block is parseable
1. Extract the JSON block between ```json and ``` markers
2. Parse as JSON
3. Assert `summary.total_flat_files` = 30
4. Assert `summary.shims` + `summary.standalone` = 30
- **Expected:** No parse errors, counts reconcile

### TC04: No unclassified actors
1. Iterate the `actors` array in the JSON block
2. Assert every entry has a non-empty `name`, `classification`, and `authoritative_path`
- **Expected:** All 30 actors have complete classification metadata

### TC05: Shim count and list are reasonable
1. Extract all actors where `classification == "SHIM"`
2. Assert count is between 5 and 15 (sanity bounds)
3. Assert known shims appear: arbiter, base, chronos, dreamer, examiner, habit_forge, perceiver_plus, prism, sentinel_prime, triad
- **Expected:** 10 known shims present

### TC06: Explorer is classified as STANDALONE (not shim)
1. Find `explorer` in the actors array
2. Assert `classification == "STANDALONE"` — explorer.py is ~1300 lines despite having a subpackage
- **Expected:** S02 will NOT delete explorer.py

### TC07: Subpackage canonical source section is present
1. Assert file contains `## Subpackage Canonical Sources` section
2. Assert at least 5 subpackages listed with primary module and classes exported
- **Expected:** S02 can read authoritative paths for subpackage agents

## Not Proven By This UAT
- **Live import paths work** — tested by pytest in S02 after import rewrites
- **No circular imports** — discovered during S02/S03 execution
- **coordinator/ and nexus/ subpackages** — listed in Subpackage table but no flat actor files exist for them
- **historian, metis, steward** subpackages — listed in Subpackage table but no flat files; full implementations only
