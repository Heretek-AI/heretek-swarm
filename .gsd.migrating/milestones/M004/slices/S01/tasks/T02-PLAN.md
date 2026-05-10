---
estimated_steps: 1
estimated_files: 2
skills_used: []
---

# T02: Verify pytest collects all 16 existing test files without errors

Run `pytest --co -q` to collect all tests without executing them. Confirm all 16 test files are discovered (~649 test functions). If any collection errors occur (import failures, missing modules), diagnose and fix them. Common issues: missing asyncio_mode=auto config (already set), missing test path (already set to tests/), circular imports from test modules.

## Inputs

- `tests/conftest.py`
- `pyproject.toml`
- `tests/__init__.py`

## Expected Output

- `pyproject.toml`
- `tests/conftest.py`

## Verification

python -m pytest --co -q 2>&1 | tail -5
