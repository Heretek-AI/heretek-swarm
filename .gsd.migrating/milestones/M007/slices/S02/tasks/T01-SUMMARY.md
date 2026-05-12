---
id: T01
parent: S02
milestone: M007
key_files:
  - (none)
key_decisions:
  - (none)
duration: 
verification_result: passed
completed_at: 2026-05-12T13:16:59.745Z
blocker_discovered: false
---

# T01: Updated 8 path references across pyproject.toml, backend/Dockerfile, and docker-compose.yml from heretek-swarm/ to backend/ after S01's git mv

**Updated 8 path references across pyproject.toml, backend/Dockerfile, and docker-compose.yml from heretek-swarm/ to backend/ after S01's git mv**

## What Happened

Applied all 8 planned path-reference changes across 3 build-configuration files:

**pyproject.toml** (4 changes):
- `[tool.setuptools.packages.find]` `where` → `["backend"]`
- `[tool.coverage.run]` `source` → `["backend"]`
- `[tool.coverage.paths]` `source` → `["backend/"]`
- `[tool.ruff]` `src` → `["backend", "tests"]`

**backend/Dockerfile** (3 changes):
- Usage comment: `heretek-swarm/Dockerfile` → `backend/Dockerfile`
- COPY source: `heretek-swarm ./heretek-swarm` → `backend ./backend`
- COPY --from=builder target: `/app/heretek-swarm` → `/app/backend`

**docker-compose.yml** (1 change):
- API service dockerfile: `heretek-swarm/Dockerfile` → `backend/Dockerfile`

Preserved: PyPI package name `"heretek-swarm"`, GitHub URLs, console_scripts entry point `heretek-swarm`, and Python imports `heretek_swarm.*` — none are filesystem paths.

## Verification

Ran composite grep verification confirming zero stale `heretek-swarm/` filesystem-path references remain in any of the 3 build-configuration files. All 8 targeted lines were individually confirmed via grep/read to show `backend/` paths.

## Verification Evidence

| # | Command | Exit Code | Verdict | Duration |
|---|---------|-----------|---------|----------|
| 1 | `bash -c '! grep -q "heretek-swarm/" backend/Dockerfile docker-compose.yml && ! grep -qE "^(where|source|src).*=.*\[.*heretek-swarm" pyproject.toml'` | 0 | ✅ pass | 250ms |

## Deviations

None.

## Known Issues

None.

## Files Created/Modified

None.
