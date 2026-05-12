# S01: Audit file inventory and plan

**Goal:** Produce a complete file inventory, import dependency map, CI/workflow impact list, and an actionable migration plan for the repository restructure, so M007 can execute cleanly.
**Demo:** After this: a written plan with exact file moves, import rewrites, and CI fixes ready to execute.

## Must-Haves

- Full file inventory documents every source, config, doc, test, CI, and deployment file with type, size, purpose, and path.\n- Import dependency map produced as a structured summary showing which packages/files depend on which, with special attention to `src/` → `heretek-swarm/heretek_swarm/` cross-references.\n- CI/workflow impact list catalogs all 6 workflow files, docker-compose.yml, Dockerfile, and pyproject.toml path references that will break under the target structure.\n- Migration plan document (M006-PLAN.md) specifies exact file moves, import rewrites, CI path updates, and ordering constraints, ready for M007 execution.

## Proof Level

- This slice proves: operational

## Integration Closure

This slice produces only documents (inventory, map, plan) — no code changes. The plan directly feeds M007 execution slices. Upstream: reads the full repo tree, pyproject.toml, .github/workflows/*.yml, docker-compose.yml, Dockerfile. No new wiring introduced.

## Verification

- The produced M006-PLAN.md serves as the single source of truth for M007 task decomposition. File inventory + import map enable M007 executors to validate each file move and import rewrite against known data.

## Tasks

- [ ] **T01: Produce complete file inventory** `est:45m`
  Walk the entire repository tree (excluding .git/, .gsd/, node_modules/, .venv/, __pycache__/) and catalog every file with: path relative to repo root, file type (py, tsx, js, yml, toml, md, json, sql, Dockerfile, etc.), size in bytes, and a one-line purpose description. Output as a structured YAML or JSON file that downstream tasks can consume programmatically.
  - Files: `heretek-swarm/heretek_swarm/__init__.py`, `src/__init__.py`, `src/cli.py`, `pyproject.toml`, `docker-compose.yml`, `.github/workflows/ci.yml`, `.github/workflows/ci-cd.yml`
  - Verify: test -f .gsd/milestones/M006/slices/S01/FILE_INVENTORY.md && grep -c "type:" .gsd/milestones/M006/slices/S01/FILE_INVENTORY.md > 0 && grep -c "path:" .gsd/milestones/M006/slices/S01/FILE_INVENTORY.md > 0

- [ ] **T02: Map import dependencies between packages** `est:1h`
  Analyze all Python import statements across the codebase to build a dependency graph. Use grep/ripgrep to find all `import X` and `from X import Y` statements in `.py` files.
  - Files: `heretek-swarm/heretek_swarm/actors/__init__.py`, `heretek-swarm/heretek_swarm/actors/base/core.py`, `heretek-swarm/heretek_swarm/__init__.py`, `src/cli.py`
  - Verify: test -f .gsd/milestones/M006/slices/S01/IMPORT_MAP.md && grep -c "depends_on:" .gsd/milestones/M006/slices/S01/IMPORT_MAP.md > 0

- [ ] **T03: Audit CI, deployment, and build configuration** `est:45m`
  Catalog and analyze every CI workflow file, deployment config, and build configuration file for path references that would break under the target structure (current: `heretek-swarm/heretek_swarm/{actors,schemas,validation,...}`, target: `backend/heretek_swarm/{actors,schemas,validation,...}`).
  - Files: `.github/workflows/ci.yml`, `.github/workflows/ci-cd.yml`, `.github/workflows/publish-python.yml`, `.github/workflows/publish-npm.yml`, `.github/workflows/load-test.yml`, `.github/workflows/codeboarding.yml`, `docker-compose.yml`, `heretek-swarm/Dockerfile`, `pyproject.toml`
  - Verify: test -f .gsd/milestones/M006/slices/S01/CI_IMPACT.md && grep -c "workflow" .gsd/milestones/M006/slices/S01/CI_IMPACT.md > 0 && grep -c "path" .gsd/milestones/M006/slices/S01/CI_IMPACT.md > 0

- [ ] **T04: Write actionable migration plan (M006-PLAN.md)** `est:1h 30m`
  Synthesize the file inventory, import map, and CI impact analysis into a single actionable migration plan document at `.gsd/milestones/M006/M006-PLAN.md`.
  - Files: `.gsd/milestones/M006/M006-PLAN.md`
  - Verify: test -f .gsd/milestones/M006/M006-PLAN.md && grep -c "backend/" .gsd/milestones/M006/M006-PLAN.md > 0 && grep -c "current path" .gsd/milestones/M006/M006-PLAN.md > 0

## Files Likely Touched

- heretek-swarm/heretek_swarm/__init__.py
- src/__init__.py
- src/cli.py
- pyproject.toml
- docker-compose.yml
- .github/workflows/ci.yml
- .github/workflows/ci-cd.yml
- heretek-swarm/heretek_swarm/actors/__init__.py
- heretek-swarm/heretek_swarm/actors/base/core.py
- .github/workflows/publish-python.yml
- .github/workflows/publish-npm.yml
- .github/workflows/load-test.yml
- .github/workflows/codeboarding.yml
- heretek-swarm/Dockerfile
- .gsd/milestones/M006/M006-PLAN.md
