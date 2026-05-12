---
estimated_steps: 1
estimated_files: 1
skills_used: []
---

# T01: Remove duplicate `structlog.configure()` from actors/base/core.py, use canonical logger

Remove the `structlog.configure(...)` block (lines ~54-71) from `heretek_swarm/actors/base/core.py` and update the module-level logger to use the canonical `get_logger()` from `heretek_swarm.logging.config`. This eliminates the first of two duplicate structlog.configure() calls. The `import structlog` may remain or be narrowed to just `get_logger` import.

## Inputs

- `heretek-swarm/heretek_swarm/logging/config.py`

## Expected Output

- `heretek-swarm/heretek_swarm/actors/base/core.py`

## Verification

grep -c "structlog.configure" heretek-swarm/heretek_swarm/actors/base/core.py should return 0; grep -c "get_logger" should match expected usage
