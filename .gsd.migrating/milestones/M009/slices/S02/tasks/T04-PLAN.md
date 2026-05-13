---
estimated_steps: 1
estimated_files: 2
skills_used: []
---

# T04: Build all Docker images

Run docker compose build for all 6 services. If build fails (e.g. stale uv.lock does not satisfy pyproject.toml), regenerate uv.lock with uv lock and retry.

## Inputs

- None specified.

## Expected Output

- `All 6 Docker images build successfully`

## Verification

docker compose build 2>&1 | tail -20
