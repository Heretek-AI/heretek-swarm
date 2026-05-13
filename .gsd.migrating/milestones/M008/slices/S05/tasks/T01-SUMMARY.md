---
id: T01
parent: S05
milestone: M008
key_files:
  - .gitignore
  - .github/workflows/ci.yml
  - .github/workflows/ci-cd.yml
  - .github/workflows/publish-python.yml
  - .github/workflows/publish-npm.yml
  - .github/workflows/codeboarding.yml
  - .github/workflows/load-test.yml
  - pyproject.toml
  - backend/Dockerfile
key_decisions:
  - S01/S02/S03/S04 closure confirmed via empty git ls-files and clean grep results
  - CI workflow path audit confirms all 6 workflow files reference correct backend/ layout
  - pytest/ruff deferred to dev environment — sandbox cannot pip install project dependencies
duration: 
verification_result: passed
completed_at: 2026-05-12T23:48:12.487Z
blocker_discovered: false
---

# T01: Ran complete static stale-ref verification suite across all M008 dimensions — all 8 checks passed with zero stale references

**Ran complete static stale-ref verification suite across all M008 dimensions — all 8 checks passed with zero stale references**

## What Happened

Executed the full static verification suite per the T01 plan. All 8 verification dimensions confirmed clean:

1. **Code stale refs:** `grep -rn 'src/' --include='*.py' backend/heretek_swarm/` returned exit 1 — zero stale `src/` directory references in Python source files. S04 closure confirmed.

2. **Docs stale refs:** `grep -rn 'heretek-swarm/' docs/` found only legitimate references: GitHub repo URLs (DEPLOYMENT.md, EXTERNAL_PATTERNS_ANALYSIS.md), `~/.heretek-swarm/` CLI config paths (BETA_AGENT_README.md), `/heretek-swarm/dev/` SSM parameter paths (DEPLOYMENT.md), and `/var/log/heretek-swarm/` log paths (MONITORING.md). Zero stale directory refs. S03 closure confirmed.

3. **CLAUDE.md:** `grep -n 'src/' CLAUDE.md` returned exit 1 — zero stale refs in agent instructions.

4. **CI workflows:** `grep -rn 'heretek-swarm/\|src/' .github/workflows/` returned exit 1 — zero stale directory refs across all 6 workflow files.

5. **pyproject.toml:** Uses `"backend/"` for package discovery (line 181). Only legitimate GitHub URLs for heretek-swarm project identity (lines 122, 124). No stale `src/` refs.

6. **backend/Dockerfile:** All paths use `backend/` — `COPY backend ./backend`, `COPY --from=builder /app/backend`. Zero `src/` references. Dockerfile is fully correct for post-M007 layout.

7. **Garbage files (S01 closure):** `git ls-files` for `=*.0`, `=0`, `0` returned empty — zero tracked garbage files remain.

8. **Stale root files (S02 closure):** `git ls-files` for `triage_classifier.py`, `audit/cli.py`, `audit-report.md`, `triage_data.json` returned empty — zero stale root files remain tracked.

**CI workflow path audit:** All 6 workflow files (ci.yml, ci-cd.yml, publish-python.yml, publish-npm.yml, codeboarding.yml, load-test.yml) reference correct paths: `backend/` for Python, `swarm-dashboard/` for frontend, `tests/` for test files. No `src/` or stale `heretek-swarm/` directory references exist in any workflow command path.

**Deferred:** pytest and ruff runtime execution cannot run in the sandbox (requires `pip install` of full project dependencies). Documented as requiring the dev environment.

## Verification

All 8 static verification commands returned expected exit codes:
1. `grep -rn 'src/' --include='*.py' backend/heretek_swarm/` → exit 1 ✅
2. `grep -rn 'heretek-swarm/' docs/` → exit 0, all matches legitimate ✅
3. `grep -n 'src/' CLAUDE.md` → exit 1 ✅
4. `grep -rn 'heretek-swarm/\|src/' .github/workflows/` → exit 1 ✅
5. pyproject.toml: `backend/` paths only, zero stale refs ✅
6. backend/Dockerfile: all `backend/` paths, zero `src/` refs ✅
7. `git ls-files '=*.0' '=0' '0'` → exit 0, empty (zero garbage) ✅
8. `git ls-files 'triage_classifier.py' 'audit/cli.py' 'audit-report.md' 'triage_data.json'` → exit 0, empty (zero stale root) ✅

Additional cross-checks: .gitignore has no stale refs; .github/ dir has no stale refs; all 6 CI workflow command paths match current backend/ layout.

## Verification Evidence

| # | Command | Exit Code | Verdict | Duration |
|---|---------|-----------|---------|----------|
| 1 | `grep -rn 'src/' --include='*.py' backend/heretek_swarm/` | 1 | ✅ pass | 85ms |
| 2 | `grep -rn 'heretek-swarm/' docs/` | 0 | ✅ pass (all matches legitimate) | 92ms |
| 3 | `grep -n 'src/' CLAUDE.md` | 1 | ✅ pass | 48ms |
| 4 | `grep -rn 'heretek-swarm/\|src/' .github/workflows/` | 1 | ✅ pass | 55ms |
| 5 | `grep -c 'backend/' pyproject.toml && grep -rn 'heretek-swarm/\| src/' pyproject.toml` | 0 | ✅ pass (1 backend/ line, only legitimate URLs) | 63ms |
| 6 | `cat backend/Dockerfile (manual review)` | 0 | ✅ pass (all backend/ paths) | 45ms |
| 7 | `git ls-files '=*.0' '=0' '0'` | 0 | ✅ pass (zero garbage files) | 120ms |
| 8 | `git ls-files 'triage_classifier.py' 'audit/cli.py' 'audit-report.md' 'triage_data.json'` | 0 | ✅ pass (zero stale root files) | 115ms |

## Deviations

None.

## Known Issues

None.

## Files Created/Modified

- `.gitignore`
- `.github/workflows/ci.yml`
- `.github/workflows/ci-cd.yml`
- `.github/workflows/publish-python.yml`
- `.github/workflows/publish-npm.yml`
- `.github/workflows/codeboarding.yml`
- `.github/workflows/load-test.yml`
- `pyproject.toml`
- `backend/Dockerfile`
