---
estimated_steps: 5
estimated_files: 4
skills_used: []
---

# T01: Write integration smoke test for mixin imports and stub-injected agent

Create `tests/test_mixin_integration_s03.py` that proves M003's milestone-level acceptance: (1) `from heretek_swarm.actors.mixins import *` produces all 10 expected names, (2) `AlphaAgent(access_analyzer=StubAccessAnalyzer(), pattern_extractor=StubPatternExtractor())` constructs without error, (3) calling `_track_memory_access` on that agent uses the stub and does not raise TypeError, (4) `AlphaAgent()` (no stubs) still constructs cleanly (backward compat).

Import from `heretek_swarm.actors.mixins` (the public path), NOT from individual mixin files. Import stubs from `heretek_swarm.actors.stubs`. Import `AlphaAgent` from `heretek_swarm.actors`.

Do NOT re-test what S01 and S02 already test in isolation. The goal is an integration-level smoke test that exercises the full chain: public import → construction → mixin method dispatch via MRO → stub response.

Assert that every name in `__all__` on `heretek_swarm.actors.mixins` is actually importable. Assert that the stub returns real data for `_track_memory_access` (profile access_count == 1). Assert that `_get_memory_tier` returns the stub's "cold" tier string.

Single test class: `TestMixinIntegrationSmoke`. Each assertion in its own test method. Mark async tests with `@pytest.mark.asyncio`.

## Inputs

- `heretek-swarm/heretek_swarm/actors/mixins/__init__.py`
- `heretek-swarm/heretek_swarm/actors/stubs.py`
- `heretek-swarm/heretek_swarm/actors/base/core.py`

## Expected Output

- `tests/test_mixin_integration_s03.py`

## Verification

cd C:/Users/Derek/Desktop/heretek-swarm && python -m pytest tests/test_mixin_integration_s03.py -v --tb=short 2>&1
