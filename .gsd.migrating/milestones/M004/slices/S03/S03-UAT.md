# S03: Add GitHub Actions CI for pytest and ruff — UAT

**Milestone:** M004
**Written:** 2026-05-10T20:54:18.949Z

## UAT

**UAT Type:** artifact-driven
**Why:** CI pipeline correctness is verifiable by inspection and simulation — no live runtime needed.

### Preconditions
- Repository has the updated `.github/workflows/ci.yml` and `pyproject.toml`

### Smoke Test
- CI YAML syntax is valid (GitHub Actions parser accepts it)

### Test Cases

#### 1. CI pipeline triggers on push/PR
1. Push to any branch with open PR against main/develop
2. **Expected:** GitHub Actions runs all jobs (security-scan, lint-python, test-python, lint-frontend, test-frontend)

#### 2. Unit-only test execution
1. CI test-python job runs
2. **Expected:** pytest executes with `-m "not integration"` flag, no Postgres/Redis/Qdrant services are started

#### 3. Test failure causes red X
1. Introduce a deliberate test failure
2. Push to a PR branch
3. **Expected:** test-python job exits non-zero, GitHub shows red X

#### 4. Ruff gate blocks when findings >= 50
1. Add code that produces >= 50 Ruff findings
2. Push to a PR branch
3. **Expected:** Ruff Warning Gate step exits 1, lint-python job fails

#### 5. Frontend and security jobs remain unchanged
1. Inspect CI workflow
2. **Expected:** security-scan, lint-frontend, and test-frontend jobs still use `|| true` to swallow failures

### Edge Cases

#### Empty test collection
1. Remove all unit-test-marked tests
2. Push to a PR branch
3. **Expected:** pytest exits with "no tests collected" (exit code 5), job succeeds

#### Zero Ruff findings
1. Fix all existing Ruff violations
2. Push to a PR branch
3. **Expected:** Ruff Warning Gate passes with count 0

### Not Proven By This UAT
- Integration tests (marked `integration`) are not executed in CI — that would require Postgres/Redis/Qdrant services
- Code coverage thresholds are not gated on CI (report is informational only via codecov-action with `if: always()`)
- End-to-end verification against an actual GitHub runner (inspection-based proof only)
