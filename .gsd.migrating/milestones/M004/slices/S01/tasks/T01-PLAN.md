---
estimated_steps: 1
estimated_files: 2
skills_used: []
---

# T01: Install dev dependencies into .venv and verify pytest is available

The .venv exists but has no dev packages installed (no pytest, no pytest-asyncio, no coverage, no ruff). Install the dev dependencies from pyproject.toml using `[dev]` extras so pytest and all test infrastructure are available.

## Inputs

- `pyproject.toml`
- `.venv/Scripts/python.exe`

## Expected Output

- `Dev dependencies installed (no new tracked files — .venv is gitignored)`

## Verification

python -m pytest --version
