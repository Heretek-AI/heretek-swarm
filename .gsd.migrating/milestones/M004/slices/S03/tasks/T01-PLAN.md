---
estimated_steps: 1
estimated_files: 1
skills_used: []
---

# T01: Fix coverage source path and ruff source roots in pyproject.toml

Coverage config `[tool.coverage.run] source = ["src"]` points at a directory that doesn't exist — coverage reporting collects nothing. The package lives under `heretek-swarm/heretek_swarm/`. Fix the source path to `["heretek-swarm"]` per the M004 architectural decision. Update the parallel `[tool.coverage.paths] source` entry similarly. Also fix `[tool.ruff] src = ["src", "tests"]` to `["heretek-swarm", "tests"]` so ruff resolves first-party imports from the correct source root. This is a prerequisite for CI coverage reporting to actually work.

## Inputs

- `pyproject.toml`

## Expected Output

- `pyproject.toml`

## Verification

grep -q 'source = \["heretek-swarm"\]' pyproject.toml && grep -q 'src = \["heretek-swarm"' pyproject.toml
