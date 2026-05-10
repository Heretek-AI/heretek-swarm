---
estimated_steps: 14
estimated_files: 1
skills_used: []
---

# T01: Audit every actor file in heretek_swarm/actors/ and produce the canonical map

Scan heretek-swarm/heretek_swarm/actors/ and produce a complete inventory.

Steps:
1. List all .py files in the actors/ directory (skip __init__.py, __pycache__, docs/)
2. For each file, read its first 3 lines to determine its role:
   - If it says "backward compatibility", "re-export", "shim", or "wrapper" in the docstring → classify as SHIM (re-export from subpackage)
   - If it imports from a matching subpackage (e.g. `from heretek_swarm.actors.X import` pointing to X/) → classify as SHIM
   - Otherwise → classify as STANDALONE (canonical implementation)
3. For STANDALONE files with matching subdirectories (e.g. explorer.py + explorer/): read the subpackage's __init__.py to determine which path is authoritative. The rule: subpackage __init__.py with the class definition wins over the flat file.
4. Record: filename, line count, classification (SHIM/STANDALONE/CANONICAL_SUBPACKAGE), authoritative path, classes exported, subpackage present (yes/no).
5. Write the audit to `.gsd/milestones/M001/slices/S01/ACTOR_AUDIT.md` in Markdown table format plus JSON machine-parseable block.

Classification criteria:
- SHIM: flat file that only re-exports from a subpackage — e.g. chronos.py, dreamer.py, examiner.py, prism.py, sentinel_prime.py, perceiver_plus.py, habit_forge.py
- STANDALONE: flat file with full implementation — e.g. alpha.py, beta.py, catalyst.py, charlie.py, coder.py, explorer.py, perceiver.py, historian.py, metis.py, empath.py, echo.py, steward.py, supervisor.py, validation.py, profiling.py, handoff.py, handoff_handlers.py, langroid_adapter.py
- CANONICAL_SUBPACKAGE: the subpackage/ is the authoritative source when both exist (e.g. chronos/ beats chronos.py, dreamer/ beats dreamer.py)

## Inputs

- None specified.

## Expected Output

- `.gsd/milestones/M001/slices/S01/ACTOR_AUDIT.md`

## Verification

grep -c "^| " .gsd/milestones/M001/slices/S01/ACTOR_AUDIT.md returns >= 20 (table rows for every actor)
