# S02: Rewrite imports and CI paths

**Goal:** Rewrite all build configuration paths (pyproject.toml, Dockerfile, docker-compose.yml) and CI workflow paths (.github/workflows/) from the old `heretek-swarm/` directory name and stale `src/` references to the new `backend/` directory name, after S01's git mv.
**Demo:** All Python imports use the new backend/ path; CI passes.

## Must-Haves

- `git grep` shows no filesystem path references to `heretek-swarm/` in `backend/Dockerfile`, `docker-compose.yml`, `.github/workflows/ci.yml`, or `.github/workflows/ci-cd.yml` (GitHub URLs in pyproject.toml are excluded — they should remain as-is)\n- `git grep` shows no stale `src/` tooling paths (ruff, mypy, bandit, pytest --cov) remain in any `.github/workflows/` file\n- pyproject.toml `where`, `source`, and `src` directives point to `backend` not `heretek-swarm`\n- No changes to `heretek_swarm` Python package imports (they use package name, unchanged by directory rename)

## Proof Level

- This slice proves: contract

## Integration Closure

Upstream surfaces consumed: S01's rename (backend/ directory is now in place). New wiring introduced: pyproject.toml where/source/src now point to backend/, Dockerfile COPY paths updated for the new directory. What remains before milestone usable end-to-end: S03 will verify fresh clone and full integration.

## Verification

- none — all changes are static config-file edits; no runtime behavior is modified

## Tasks

- [ ] **T01: Update pyproject.toml, Dockerfile, and docker-compose.yml build paths** `est:30m`
  Update 8 path references across 3 build-configuration files that still reference the old `heretek-swarm/` directory name after S01's git mv.
  - Files: `pyproject.toml`, `backend/Dockerfile`, `docker-compose.yml`
  - Verify: bash -c '! grep -q "heretek-swarm/" backend/Dockerfile docker-compose.yml && ! grep -qE "^(where|source|src).*=.*\[.*heretek-swarm" pyproject.toml'

- [ ] **T02: Update CI workflow tooling paths** `est:30m`
  Update 10 path references across 2 CI workflow files that reference the old `heretek-swarm/` directory and stale `src/` paths (which was deleted in S01).
  - Files: `.github/workflows/ci.yml`, `.github/workflows/ci-cd.yml`
  - Verify: bash -c '! grep -qE "(bandit|ruff|mypy).*src/" .github/workflows/ci.yml .github/workflows/ci-cd.yml && ! grep -q "heretek-swarm/" .github/workflows/ci.yml && ! grep -qE "--cov=src" .github/workflows/ci-cd.yml .github/workflows/ci.yml'

## Files Likely Touched

- pyproject.toml
- backend/Dockerfile
- docker-compose.yml
- .github/workflows/ci.yml
- .github/workflows/ci-cd.yml
