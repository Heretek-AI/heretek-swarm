# S03: Add mixin __init__.py exports and smoke test for stub injection

**Goal:** Verify the public mixin import path and stub injection work end-to-end: `from heretek_swarm.actors.mixins import *` resolves all 10 mixin names, and a real agent constructed with stub dependencies can call guarded mixin methods through the MRO without TypeError, returning real stub data.
**Demo:** from heretek_swarm.actors.mixins import AuditMixin, DeliberationMixin

## Must-Haves

- Complete the planned slice outcomes.

## Verification

- Run the task and slice verification checks for this slice.

## Tasks

- [x] **T01: Write integration smoke test for mixin imports and stub-injected agent** `est:30m`
  Create `tests/test_mixin_integration_s03.py` that proves M003's milestone-level acceptance: (1) `from heretek_swarm.actors.mixins import *` produces all 10 expected names, (2) `AlphaAgent(access_analyzer=StubAccessAnalyzer(), pattern_extractor=StubPatternExtractor())` constructs without error, (3) calling `_track_memory_access` on that agent uses the stub and does not raise TypeError, (4) `AlphaAgent()` (no stubs) still constructs cleanly (backward compat).
  - Files: `heretek-swarm/heretek_swarm/actors/mixins/__init__.py`, `heretek-swarm/heretek_swarm/actors/stubs.py`, `heretek-swarm/heretek_swarm/actors/base/core.py`, `tests/test_mixin_integration_s03.py`
  - Verify: cd C:/Users/Derek/Desktop/heretek-swarm && python -m pytest tests/test_mixin_integration_s03.py -v --tb=short 2>&1

## Files Likely Touched

- heretek-swarm/heretek_swarm/actors/mixins/__init__.py
- heretek-swarm/heretek_swarm/actors/stubs.py
- heretek-swarm/heretek_swarm/actors/base/core.py
- tests/test_mixin_integration_s03.py
