---
estimated_steps: 13
estimated_files: 9
skills_used: []
---

# T03: Audit CI, deployment, and build configuration

Catalog and analyze every CI workflow file, deployment config, and build configuration file for path references that would break under the target structure (current: `heretek-swarm/heretek_swarm/{actors,schemas,validation,...}`, target: `backend/heretek_swarm/{actors,schemas,validation,...}`).

Files to analyze in detail:
1. `.github/workflows/ci.yml` — references `src/` in ruff, mypy, bandit commands
2. `.github/workflows/ci-cd.yml` — references `src/` in ruff, mypy, bandit commands; `--cov=src` in pytest
3. `.github/workflows/publish-python.yml` — installs and tests the built wheel
4. `.github/workflows/publish-npm.yml` — only touches swarm-dashboard, probably unaffected
5. `.github/workflows/load-test.yml` — references `tests/load/` paths
6. `.github/workflows/codeboarding.yml` — references `docs/` output
7. `docker-compose.yml` — dockerfile path `heretek-swarm/Dockerfile`, build context `.`
8. `heretek-swarm/Dockerfile` — COPY paths, WORKDIR
9. `pyproject.toml` — `where = ["heretek-swarm"]` in setuptools.packages.find, coverage source paths
10. `swarm-dashboard/` — separate frontend, verify no path dependencies on backend structure

For each file, list every path reference that would need updating, what it should change to, and whether it's a hard blocker or cosmetic.

## Inputs

- `.github/workflows/ci.yml`
- `.github/workflows/ci-cd.yml`
- `.github/workflows/publish-python.yml`
- `.github/workflows/publish-npm.yml`
- `.github/workflows/load-test.yml`
- `.github/workflows/codeboarding.yml`
- `docker-compose.yml`
- `heretek-swarm/Dockerfile`
- `pyproject.toml`
- `.gsd/milestones/M006/slices/S01/FILE_INVENTORY.md`

## Expected Output

- `.gsd/milestones/M006/slices/S01/CI_IMPACT.md`

## Verification

test -f .gsd/milestones/M006/slices/S01/CI_IMPACT.md && grep -c "workflow" .gsd/milestones/M006/slices/S01/CI_IMPACT.md > 0 && grep -c "path" .gsd/milestones/M006/slices/S01/CI_IMPACT.md > 0
