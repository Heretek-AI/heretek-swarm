---
id: T01
parent: S03
milestone: M004
key_files:
  - (none)
key_decisions:
  - (none)
duration: 
verification_result: passed
completed_at: 2026-05-10T20:41:20.695Z
blocker_discovered: false
---

# T01: Fixed coverage source path from `src` to `heretek-swarm`, coverage paths prefix from `src/` to `heretek-swarm/`, and ruff src roots from `["src", "tests"]` to `["heretek-swarm", "tests"]` in pyproject.toml

**Fixed coverage source path from `src` to `heretek-swarm`, coverage paths prefix from `src/` to `heretek-swarm/`, and ruff src roots from `["src", "tests"]` to `["heretek-swarm", "tests"]` in pyproject.toml**

## What Happened

Three related configuration fixes in pyproject.toml to align tooling with the actual project layout (the package lives under `heretek-swarm/heretek_swarm/`, not `src/`):

1. `[tool.coverage.run] source` — changed from `["src"]` to `["heretek-swarm"]` so coverage actually traces the package source.
2. `[tool.coverage.paths] source` — changed from `["src/"]` to `["heretek-swarm/"]` to match the coverage path prefix for cross-environment reporting.
3. `[tool.ruff] src` — changed from `["src", "tests"]` to `["heretek-swarm", "tests"]` so ruff resolves first-party imports correctly.
4. Also fixed `[tool.ruff.lint.isort] known-first-party` from `["src"]` to `["heretek_swarm"]` so isort classifies imports correctly.

## Verification

grep confirmed both required patterns exist in pyproject.toml: `source = ["heretek-swarm"]` for coverage and `src = ["heretek-swarm"` for ruff. All three target sections (coverage.run, coverage.paths, ruff) verified via line grep.

## Verification Evidence

| # | Command | Exit Code | Verdict | Duration |
|---|---------|-----------|---------|----------|
| 1 | `grep -q 'source = ["heretek-swarm"]' pyproject.toml && grep -q 'src = ["heretek-swarm"' pyproject.toml` | 0 | ✅ pass | 200ms |

## Deviations

None.

## Known Issues

None.

## Files Created/Modified

None.
