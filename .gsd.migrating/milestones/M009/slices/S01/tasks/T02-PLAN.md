---
estimated_steps: 1
estimated_files: 2
skills_used: []
---

# T02: Editable pip install

Run pip install -e '.[dev]' from repo root. If uv.lock is stale, run uv lock --refresh then retry. Fix any pyproject.toml path/dependency issues discovered.

## Inputs

- `pyproject.toml`

## Expected Output

- `heretek-swarm package installed in editable mode with all dev dependencies`

## Verification

python -c 'import heretek_swarm; print(heretek_swarm.__version__)' && heretek-swarm --help
