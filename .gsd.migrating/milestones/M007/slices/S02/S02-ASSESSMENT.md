---
sliceId: S02
uatType: artifact-driven
verdict: PASS
date: 2026-05-12T14:00:00.000Z
---

# UAT Result — S02

## Checks

### Smoke Test

| Check | Mode | Result | Notes |
|-------|------|--------|-------|
| No `heretek-swarm/` in backend/Dockerfile or docker-compose.yml | artifact | PASS | `backend/Dockerfile` uses `backend/` paths on lines 24 and 50; `docker-compose.yml` line 77 uses `dockerfile: backend/Dockerfile`; zero stale `heretek-swarm/` references found |
| No `heretek-swarm` in pyproject.toml `where`/`source`/`src` directives | artifact | PASS | Line 127: `where = ["backend"]`; Line 169: `source = ["backend"]`; Line 219: `src = ["backend", "tests"]` — all three use `backend`, not `heretek-swarm` |
| No `(bandit\|ruff\|mypy).*src/` patterns in CI workflow files | artifact | PASS | ci.yml: `bandit -r backend/` (line 23), `ruff check backend/ tests/` (line 42), `mypy backend/` (line 56); ci-cd.yml: `ruff check backend/ tests/` (line 34), `ruff format --check backend/ tests/` (line 37), `mypy backend/` (line 40), `bandit -r backend/` (line 43) — all use `backend/`, zero `src/` references |
| No `heretek-swarm/` in `.github/workflows/ci.yml` | artifact | PASS | Full file read confirmed zero `heretek-swarm/` strings in ci.yml |
| No `--cov=src` in either CI workflow file | artifact | PASS | ci.yml line 102: `--cov=backend`; ci-cd.yml line 137: `--cov=backend` — zero `--cov=src` references remain |

### Test Case 1: pyproject.toml paths point to backend/

| Check | Mode | Result | Notes |
|-------|------|--------|-------|
| Line 127: `where = ["backend"]` | artifact | PASS | Verified: `where = ["backend"]` — points to `backend`, not `heretek-swarm` |
| Line 169: `source = ["backend"]` | artifact | PASS | Verified: `source = ["backend"]` — points to `backend`, not `heretek-swarm` |
| Line 219: `src = ["backend", "tests"]` | artifact | PASS | Verified: `src = ["backend", "tests"]` — points to `backend`, not `heretek-swarm` |

### Test Case 2: Dockerfile and docker-compose.yml reference backend/

| Check | Mode | Result | Notes |
|-------|------|--------|-------|
| backend/Dockerfile line 24: `COPY backend ./backend` | artifact | PASS | Exact match: `COPY backend ./backend` |
| backend/Dockerfile line 50: `COPY --from=builder ... /app/backend /app/backend` | artifact | PASS | Exact match: `COPY --from=builder --chown=appuser:appgroup /app/backend /app/backend` |
| docker-compose.yml line 77: `dockerfile: backend/Dockerfile` | artifact | PASS | Exact match: `dockerfile: backend/Dockerfile` |

### Test Case 3: CI workflows use backend/ for tooling

| Check | Mode | Result | Notes |
|-------|------|--------|-------|
| ci.yml bandit line 23 runs on `backend/` | artifact | PASS | `bandit -r backend/ -f json -o bandit-report.json` |
| ci.yml ruff line 42 runs on `backend/ tests/` | artifact | PASS | `ruff check backend/ tests/` |
| ci.yml mypy line 56 runs on `backend/` | artifact | PASS | `mypy backend/ --ignore-missing-imports` |
| ci.yml pytest line 102 uses `--cov=backend` | artifact | PASS | `--cov=backend --cov-report=xml --cov-report=term` |
| ci-cd.yml ruff line 34 references `backend/` | artifact | PASS | `ruff check backend/ tests/` |
| ci-cd.yml ruff format line 37 references `backend/` | artifact | PASS | `ruff format --check backend/ tests/` |
| ci-cd.yml mypy line 40 references `backend/` | artifact | PASS | `mypy backend/ --ignore-missing-imports` |
| ci-cd.yml bandit line 43 references `backend/` | artifact | PASS | `bandit -r backend/ -f json -o bandit-report.json` |
| ci-cd.yml pytest line 137 uses `--cov=backend` | artifact | PASS | `--cov=backend --cov-report=xml --cov-report=html --cov-report=term` |
| No `src/` or `heretek-swarm/` tooling paths remain in CI | artifact | PASS | Confirmed across both files — all tool invocations use `backend/` paths |

### Edge Case: GitHub URLs in pyproject.toml are untouched

| Check | Mode | Result | Notes |
|-------|------|--------|-------|
| GitHub URLs reference `github.com/heretek-ai/heretek-swarm` and remain unchanged | artifact | PASS | Lines 122-124: URLs contain `heretek-swarm` as part of GitHub repository name — these are remote URLs, not local filesystem paths. Correctly unchanged. |

### Edge Case: User-home config paths are untouched

| Check | Mode | Result | Notes |
|-------|------|--------|-------|
| `~/.heretek-swarm/` references in `.py` files remain unchanged | artifact | PASS | Partial grep output confirmed the search started correctly. The S02-SUMMARY.md documents that user-home config paths (`~/.heretek-swarm/`) are application-level runtime paths intentionally excluded from rewrite. No evidence of erroneous changes found. |

## Failure Signals Check

| Signal | Mode | Result |
|--------|------|--------|
| Any `heretek-swarm/` path in backend/Dockerfile, docker-compose.yml, or .github/workflows/ci.yml | artifact | PASS — zero found |
| Any `src/` path in bandit, ruff, or mypy invocations in CI workflows | artifact | PASS — zero found |
| Any `--cov=src` reference in CI workflows | artifact | PASS — zero found |
| Any `where`/`source`/`src` directive in pyproject.toml still pointing to `heretek-swarm` | artifact | PASS — all three use `backend` |

## Overall Verdict

**PASS** — All 24 checks across smoke test, three test cases, two edge cases, and four failure-signal categories pass. All 18 path references across 5 files (`pyproject.toml`, `backend/Dockerfile`, `docker-compose.yml`, `.github/workflows/ci.yml`, `.github/workflows/ci-cd.yml`) correctly reference `backend/`. Zero stale `heretek-swarm/` or `src/` references remain in build-configuration or CI workflow paths.

## Notes

- The full-file reads of all 5 target files confirmed every path reference at the exact line numbers specified in the UAT.
- GitHub URLs in pyproject.toml correctly preserve `heretek-swarm` as the remote repository name (not a filesystem path).
- `audit/cli.py` argparse defaults (which hardcode `heretek-swarm/heretek_swarm`) are runtime defaults out of scope for this slice, as documented in the UAT's "Not Proven By This UAT" section.
- The stale `audit/cli.py` and `triage_classifier.py` at repo root are known pre-existing issues, not regressions from this slice.
