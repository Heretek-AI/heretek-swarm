---
estimated_steps: 1
estimated_files: 2
skills_used: []
---

# T03: Add integration test markers and conftest improvements for clean collection

Based on pyproject.toml's marker definitions (unit, integration, load, slow, a2a, consensus, latency, security), ensure all marker registrations in pyproject.toml match what test files use. Add any missing markers to the pyproject.toml. Ensure the conftest.py has proper asyncio_mode support. Verify strict-markers mode passes.

## Inputs

- `pyproject.toml`
- `tests/conftest.py`

## Expected Output

- `pyproject.toml — updated marker definitions if needed`

## Verification

python -m pytest --co -q --strict-markers 2>&1 | tail -5
