# S02: Rewrite imports and CI paths — UAT

**Milestone:** M007
**Written:** 2026-05-12T13:43:11.551Z

## UAT Type

- UAT mode: artifact-driven
- Why this mode is sufficient: All changes are static config-file edits; no runtime behavior is modified. Correctness is verified entirely through grep-based path audits.

## Preconditions

- S01's git mv has been executed (heretek-swarm/ → backend/)
- Working tree is clean

## Smoke Test

Run the composite verification script:
```bash
# Confirm zero stale path references remain
! grep -q "heretek-swarm/" backend/Dockerfile docker-compose.yml && \
! grep -qE "^(where|source|src).*=.*\[.*heretek-swarm" pyproject.toml && \
! grep -qE "(bandit|ruff|mypy).*src/" .github/workflows/ci.yml .github/workflows/ci-cd.yml && \
! grep -q "heretek-swarm/" .github/workflows/ci.yml && \
! grep -qE -- "--cov=src" .github/workflows/ci-cd.yml .github/workflows/ci.yml && \
echo "ALL CHECKS PASSED"
```

## Test Cases

### 1. pyproject.toml paths point to backend/

1. Open `pyproject.toml`
2. Verify line 127: `where = ["backend"]`
3. Verify line 169: `source = ["backend"]`
4. Verify line 219: `src = ["backend", "tests"]`
5. **Expected:** All three directives reference `backend`, not `heretek-swarm`

### 2. Dockerfile and docker-compose.yml reference backend/

1. Open `backend/Dockerfile`
2. Verify line 24: `COPY backend ./backend`
3. Verify line 50: `COPY --from=builder ... /app/backend /app/backend`
4. Open `docker-compose.yml`
5. Verify line 77: `dockerfile: backend/Dockerfile`
6. **Expected:** All three references use `backend/` path prefix

### 3. CI workflows use backend/ for tooling

1. Open `.github/workflows/ci.yml`
2. Verify bandit runs on `backend/` (line 23)
3. Verify ruff runs on `backend/ tests/` (line 42)
4. Verify mypy runs on `backend/` (line 56)
5. Verify pytest uses `--cov=backend` (line 102)
6. Open `.github/workflows/ci-cd.yml`
7. Verify ruff, ruff format, mypy, bandit all reference `backend/` (lines 34-43)
8. Verify pytest uses `--cov=backend` (line 137)
9. **Expected:** No `src/` or `heretek-swarm/` tooling paths remain

## Edge Cases

### GitHub URLs in pyproject.toml are untouched

1. Open `pyproject.toml`
2. Search for `github.com` URLs
3. **Expected:** URLs referencing the repo (e.g., `https://github.com/...) remain unchanged — they are not filesystem paths

### User-home config paths are untouched

1. Run `git grep "heretek-swarm/" -- '*.py'`
2. **Expected:** `~/.heretek-swarm/` references (config.json, workflows.json, goals.json) remain — they are application runtime paths, not source-tree paths

## Failure Signals

- Any `heretek-swarm/` path in `backend/Dockerfile`, `docker-compose.yml`, or `.github/workflows/ci.yml`
- Any `src/` path in bandit, ruff, or mypy invocations in CI workflows
- Any `--cov=src` reference in CI workflows
- Any `where`/`source`/`src` directive in pyproject.toml still pointing to `heretek-swarm`

## Not Proven By This UAT

- That the full test suite passes with the new paths (deferred to S03: fresh-clone verification)
- That `audit/cli.py` argparse defaults (which hardcode `heretek-swarm/heretek_swarm`) have been updated — these are runtime defaults, not build/CI configuration
- That Python package imports resolve correctly at runtime (package name `heretek_swarm` was unchanged by directory rename)
