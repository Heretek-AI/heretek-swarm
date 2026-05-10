---
estimated_steps: 13
estimated_files: 1
skills_used: []
---

# T01: Delete 10 shim actor files

Delete the 10 shim files identified by S01's audit. These are flat .py files that re-export from their matching subpackages and serve no purpose now that S03 will wire the __init__.py re-export surface. Do NOT delete explorer.py — it has a subpackage but the flat file is a full standalone ~1318-line implementation.

Files to delete (relative to heretek_swarm/actors/):
- arbiter.py
- base.py
- chronos.py
- dreamer.py
- examiner.py
- habit_forge.py
- perceiver_plus.py
- prism.py
- sentinel_prime.py
- triad.py

Verify: After deletion, `ls heretek_swarm/actors/*.py | wc -l` should show 20 files (30 - 10 = 20), and none of the deleted names appear in the listing.

## Inputs

- None specified.

## Expected Output

- `heretek_swarm/actors/arbiter.py (deleted)`
- `heretek_swarm/actors/base.py (deleted)`
- `heretek_swarm/actors/chronos.py (deleted)`
- `heretek_swarm/actors/dreamer.py (deleted)`
- `heretek_swarm/actors/examiner.py (deleted)`
- `heretek_swarm/actors/habit_forge.py (deleted)`
- `heretek_swarm/actors/perceiver_plus.py (deleted)`
- `heretek_swarm/actors/prism.py (deleted)`
- `heretek_swarm/actors/sentinel_prime.py (deleted)`
- `heretek_swarm/actors/triad.py (deleted)`

## Verification

ls heretek_swarm/actors/*.py | wc -l returns 20
