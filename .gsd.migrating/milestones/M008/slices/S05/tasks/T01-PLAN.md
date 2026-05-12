---
estimated_steps: 1
estimated_files: 9
skills_used: []
---

# T01: Static stale-ref verification and CI workflow audit

Run the complete static stale-ref verification suite across all M008 cleanup dimensions. Execute all grep-based checks for stale src/ and heretek-swarm/ directory references in code, docs, CI workflow files, CLAUDE.md, pyproject.toml, and backend/Dockerfile. Verify tracked garbage files and stale root files remain absent (S01/S02 closure). Verify CI workflow command paths match current backend/ layout. Document all pass/fail results with evidence and exit codes in a verification report. The sandbox cannot run pytest or ruff (requires pip install); document these as deferred to dev environment.

## Inputs

- `.gitignore`
- `.github/workflows/ci.yml`
- `.github/workflows/ci-cd.yml`
- `.github/workflows/publish-python.yml`
- `.github/workflows/publish-npm.yml`
- `.github/workflows/codeboarding.yml`
- `.github/workflows/load-test.yml`
- `pyproject.toml`
- `backend/Dockerfile`

## Expected Output

- `.gitignore`
- `.github/workflows/ci.yml`
- `.github/workflows/ci-cd.yml`
- `.github/workflows/publish-python.yml`
- `.github/workflows/publish-npm.yml`
- `.github/workflows/codeboarding.yml`
- `.github/workflows/load-test.yml`
- `pyproject.toml`
- `backend/Dockerfile`

## Verification

All 8 static verification commands return expected exit codes (grep exit 1 for zero stale matches, git ls-files returns 0 for garbage/root files, grep -c for backend/ paths returns >= 1)
