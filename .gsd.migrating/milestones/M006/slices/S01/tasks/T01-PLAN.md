---
estimated_steps: 12
estimated_files: 7
skills_used: []
---

# T01: Produce complete file inventory

Walk the entire repository tree (excluding .git/, .gsd/, node_modules/, .venv/, __pycache__/) and catalog every file with: path relative to repo root, file type (py, tsx, js, yml, toml, md, json, sql, Dockerfile, etc.), size in bytes, and a one-line purpose description. Output as a structured YAML or JSON file that downstream tasks can consume programmatically.

Key directories to enumerate:
- `heretek-swarm/heretek_swarm/` (main Python package, ~200+ files)
- `heretek-swarm/` (Dockerfile, LICENSE, docs/, tests/, agent_workspace/, .actor_states/)
- `src/` (stub __init__.py and cli.py)
- `tests/` (top-level Python tests, ~40+ files)
- `docs/` (documentation, ~30+ files)
- `migrations/` (SQL migrations, ~12+ files)
- `.github/workflows/` (6 CI workflow YAML files)
- `swarm-dashboard/` (React frontend, ~100+ TSX/TS files, config)
- `agent_workspace/` (agent memory files)
- Root-level files (pyproject.toml, docker-compose.yml, CLAUDE.md, etc.)

## Inputs

- `heretek-swarm/heretek_swarm/`
- `src/`
- `tests/`
- `docs/`
- `swarm-dashboard/src/`
- `migrations/`
- `.github/workflows/`
- `agent_workspace/`
- `pyproject.toml`
- `docker-compose.yml`

## Expected Output

- `.gsd/milestones/M006/slices/S01/FILE_INVENTORY.md`

## Verification

test -f .gsd/milestones/M006/slices/S01/FILE_INVENTORY.md && grep -c "type:" .gsd/milestones/M006/slices/S01/FILE_INVENTORY.md > 0 && grep -c "path:" .gsd/milestones/M006/slices/S01/FILE_INVENTORY.md > 0
