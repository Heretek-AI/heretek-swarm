# S05: Final validation pass

**Goal:** Complete final verification pass across all M008 cleanup dimensions — static grep-based stale ref checks, CI workflow path verification, and milestone completion documentation. All static verification checks confirm zero stale references remain across code, docs, CI workflows, and config files. Pytest/ruff runtime execution acknowledged as requiring the dev environment.
**Demo:** pytest passes, ruff check clean, grep for stale refs zero, CI workflow files verified correct

## Must-Haves

- 1. `grep -rn 'src/' --include='*.py' backend/heretek_swarm/` returns exit code 1 (zero stale code refs) ✅
- 2. `grep -rn 'heretek-swarm/' docs/` returns only legitimate project identity/CLI/PyPI/SSM/log-path references, zero stale directory refs ✅
- 3. `grep -n 'src/' CLAUDE.md` returns exit code 1 ✅
- 4. `grep -rn 'heretek-swarm/\|src/' .github/workflows/` returns exit code 1 (no stale refs in CI) ✅
- 5. pyproject.toml contains `backend/` paths exclusively for source/build config ✅
- 6. backend/Dockerfile uses `COPY backend ./backend` and `backend` paths throughout ✅
- 7. `git ls-files '=*.0' '=0' '0'` returns 0 tracked garbage files (S01 closure) ✅
- 8. `git ls-files 'triage_classifier.py' 'audit/cli.py' 'audit-report.md' 'triage_data.json'` returns 0 stale root files (S02 closure) ✅
- 9. M008-SUMMARY.md exists documenting all 5 slice outcomes and verification results

## Proof Level

- This slice proves: final-assembly

## Integration Closure

Upstream surfaces consumed: S01 (clean git index), S02 (no stale root files), S03 (clean doc refs), S04 (clean code refs). No new wiring introduced. No integration concerns — this is a pure verification slice.

## Verification

- Run the task and slice verification checks for this slice.

## Tasks

- [ ] **T01: Static stale-ref verification and CI workflow audit** `est:30m`
  Run the complete static stale-ref verification suite across all M008 cleanup dimensions. Execute all grep-based checks for stale src/ and heretek-swarm/ directory references in code, docs, CI workflow files, CLAUDE.md, pyproject.toml, and backend/Dockerfile. Verify tracked garbage files and stale root files remain absent (S01/S02 closure). Verify CI workflow command paths match current backend/ layout. Document all pass/fail results with evidence and exit codes in a verification report. The sandbox cannot run pytest or ruff (requires pip install); document these as deferred to dev environment.
  - Files: `.gitignore`, `.github/workflows/ci.yml`, `.github/workflows/ci-cd.yml`, `.github/workflows/publish-python.yml`, `.github/workflows/publish-npm.yml`, `.github/workflows/codeboarding.yml`, `.github/workflows/load-test.yml`, `pyproject.toml`, `backend/Dockerfile`
  - Verify: All 8 static verification commands return expected exit codes (grep exit 1 for zero stale matches, git ls-files returns 0 for garbage/root files, grep -c for backend/ paths returns >= 1)

- [ ] **T02: Milestone completion summary (M008-SUMMARY.md)** `est:30m`
  Write .gsd/milestones/M008/M008-SUMMARY.md documenting the complete M008 milestone. Include: milestone vision and success criteria, all 5 slice outcomes with verification results per slice, the full static verification evidence (grep exit codes, file counts), known limitation that pytest/ruff require dev environment, and milestone-level conclusions.
  - Files: `.gsd/milestones/M008/M008-SUMMARY.md`
  - Verify: test -f .gsd/milestones/M008/M008-SUMMARY.md && grep -c 'S05\|verification\|pytest\|ruff' .gsd/milestones/M008/M008-SUMMARY.md

## Files Likely Touched

- .gitignore
- .github/workflows/ci.yml
- .github/workflows/ci-cd.yml
- .github/workflows/publish-python.yml
- .github/workflows/publish-npm.yml
- .github/workflows/codeboarding.yml
- .github/workflows/load-test.yml
- pyproject.toml
- backend/Dockerfile
- .gsd/milestones/M008/M008-SUMMARY.md
