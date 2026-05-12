---
estimated_steps: 22
estimated_files: 3
skills_used: []
---

# T01: Update pyproject.toml, Dockerfile, and docker-compose.yml build paths

Update 8 path references across 3 build-configuration files that still reference the old `heretek-swarm/` directory name after S01's git mv.

## Files touched
- `pyproject.toml` — 4 changes: `where`, `source` (x2), `src`
- `backend/Dockerfile` — 3 changes: usage comment, COPY source, COPY --from=builder
- `docker-compose.yml` — 1 change: dockerfile path for api service

## Changes
### pyproject.toml
1. Line 127: `where = ["heretek-swarm"]` → `where = ["backend"]`
2. Line 169: `source = ["heretek-swarm"]` → `source = ["backend"]`
3. Line 180-181: `source = ["heretek-swarm/",` → `source = ["backend/",`
4. Line 219: `src = ["heretek-swarm", "tests"]` → `src = ["backend", "tests"]`

### backend/Dockerfile
1. Line 5 comment: `# Usage: docker build -f heretek-swarm/Dockerfile -t heretek-swarm-api .` → `# Usage: docker build -f backend/Dockerfile -t heretek-swarm-api .`
2. Line 19: `COPY heretek-swarm ./heretek-swarm` → `COPY backend ./backend`
3. Line 50: `COPY --from=builder --chown=appuser:appgroup /app/heretek-swarm /app/heretek-swarm` → `COPY --from=builder --chown=appuser:appgroup /app/backend /app/backend`

### docker-compose.yml
1. Line 77: `dockerfile: heretek-swarm/Dockerfile` → `dockerfile: backend/Dockerfile`

## Important constraints
- Do NOT change GitHub URL references in pyproject.toml (Homepage, Documentation, Repository, Issues — they point to `heretek-swarm` as the GitHub repo name, not a filesystem path)
- Do NOT change the `name = "heretek-swarm"` in pyproject.toml (this is the PyPI package name, not a filesystem path)
- Do NOT change the `heretek-swarm` console_scripts entry point (this is a pip-installed command, not a filesystem path)
- Python imports (`heretek_swarm.*`) are unchanged — they resolve by package name

## Inputs

- `pyproject.toml`
- `backend/Dockerfile`
- `docker-compose.yml`

## Expected Output

- `pyproject.toml`
- `backend/Dockerfile`
- `docker-compose.yml`

## Verification

bash -c '! grep -q "heretek-swarm/" backend/Dockerfile docker-compose.yml && ! grep -qE "^(where|source|src).*=.*\[.*heretek-swarm" pyproject.toml'
