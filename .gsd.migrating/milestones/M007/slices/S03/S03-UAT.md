# S03: Verify clean clone and full integration — UAT

**Milestone:** M007
**Written:** 2026-05-12T16:44:38.778Z

# S03: Verify clean clone and full integration — UAT

**Milestone:** M007
**Written:** 2026-05-12

## UAT Type

- UAT mode: artifact-driven
- Why this mode is sufficient: S03 is a cleanup and verification slice with no runtime code changes. The UAT proves the filesystem is structurally clean and test files are consolidated.

## Preconditions

- All tasks T01-T03 completed
- Working directory is repo root

## Smoke Test

```bash
test ! -d src && test ! -d backend/docs && test ! -d backend/agent_workspace && test ! -d backend/.claude && test -d backend/heretek_swarm/agent_workspace && echo "SMOKE: PASS"
```

## Test Cases

### 1. Stale directories fully removed

1. `test ! -d src`
2. `test ! -d backend/docs`
3. `test ! -d backend/agent_workspace`
4. `test ! -d backend/.claude`
5. **Expected:** All exit 0

### 2. Test files consolidated

1. `ls tests/*.py | wc -l`
2. **Expected:** Returns 62

### 3. Critical paths preserved

1. `test -d backend/heretek_swarm/agent_workspace`
2. `test -d backend/heretek_swarm`
3. **Expected:** Both exit 0

### 4. No stale filesystem path references in source

1. `git grep "heretek-swarm/" -- ':!.gsd/' ':!.git/' ':!swarm-dashboard/.claude-flow/' ':!swarm-dashboard/tests/e2e/' ':!triage_classifier.py' ':!tests/test_model_garage_config.py'`
2. **Expected:** No output (empty)

## Edge Cases

### Pre-existing stale comment references

1. Check `triage_classifier.py:34` for old comment about "nested heretek-swarm/ directory"
2. **Expected:** Comment is informational only, harmless

## Failure Signals

- `src/` or any stale directory reappearing
- Test file count dropping below 62
- New stale `heretek-swarm/` filesystem paths in source code

## Not Proven By This UAT

- Runtime test suite execution (pip install, pytest, ruff) — not available in verification sandbox
- Docker compose config parse — not available in verification sandbox
- That all 62 tests actually pass — only that the files are in the right place

## Notes for Tester

The verification sandbox lacks pip, docker, and ruff. For full confidence, run `pip install -e .`, `pytest -m "not integration" -q`, `ruff check backend/ tests/`, and `docker compose config` in the actual dev environment.
