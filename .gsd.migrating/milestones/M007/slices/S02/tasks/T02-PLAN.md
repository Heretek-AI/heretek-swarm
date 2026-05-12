---
estimated_steps: 22
estimated_files: 2
skills_used: []
---

# T02: Update CI workflow tooling paths

Update 10 path references across 2 CI workflow files that reference the old `heretek-swarm/` directory and stale `src/` paths (which was deleted in S01).

## Files touched
- `.github/workflows/ci.yml` — 5 changes: bandit, ruff check, ruff gate, mypy, pytest --cov
- `.github/workflows/ci-cd.yml` — 5 changes: ruff check, ruff format, mypy, bandit, pytest --cov

## Changes
### .github/workflows/ci.yml
1. Line 23: `bandit -r src/ -f json -o bandit-report.json || true` → `bandit -r backend/ -f json -o bandit-report.json || true`
2. Line 42: `ruff check src/ tests/` → `ruff check backend/ tests/`
3. Line 46: `COUNT=$(ruff check heretek-swarm/ tests/ --quiet --output-format=concise 2>&1 | wc -l || true)` → `COUNT=$(ruff check backend/ tests/ --quiet --output-format=concise 2>&1 | wc -l || true)`
4. Line 56: `mypy src/ --ignore-missing-imports` → `mypy backend/ --ignore-missing-imports`
5. Line 102: `pytest -m "not integration" -x -q --cov=heretek-swarm --cov-report=xml --cov-report=term` → `pytest -m "not integration" -x -q --cov=backend --cov-report=xml --cov-report=term`

### .github/workflows/ci-cd.yml
1. Line 34: `ruff check src/ tests/` → `ruff check backend/ tests/`
2. Line 37: `ruff format --check src/ tests/` → `ruff format --check backend/ tests/`
3. Line 40: `mypy src/ --ignore-missing-imports || true` → `mypy backend/ --ignore-missing-imports || true`
4. Line 43: `bandit -r src/ -f json -o bandit-report.json || true` → `bandit -r backend/ -f json -o bandit-report.json || true`
5. Line 137: `pytest tests/ -v --cov=src --cov-report=xml --cov-report=html --cov-report=term || true` → `pytest tests/ -v --cov=backend --cov-report=xml --cov-report=html --cov-report=term || true`

## Important constraints
- Do NOT change frontend-related lines (test-frontend jobs reference swarm-dashboard, not affected)
- Do NOT change load-test.yml (no stale path references found)
- The security-scan job in ci.yml also uses `bandit -r src/` — change it too
- ci-cd.yml has a separate lint-python and security-scan section with different path patterns

## Inputs

- `.github/workflows/ci.yml`
- `.github/workflows/ci-cd.yml`

## Expected Output

- `.github/workflows/ci.yml`
- `.github/workflows/ci-cd.yml`

## Verification

bash -c '! grep -qE "(bandit|ruff|mypy).*src/" .github/workflows/ci.yml .github/workflows/ci-cd.yml && ! grep -q "heretek-swarm/" .github/workflows/ci.yml && ! grep -qE "--cov=src" .github/workflows/ci-cd.yml .github/workflows/ci.yml'
