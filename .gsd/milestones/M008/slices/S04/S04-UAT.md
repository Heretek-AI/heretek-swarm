# S04: Documentation & README — UAT

**Milestone:** M008
**Written:** 2026-05-03T03:27:26.569Z

# UAT: S04 Documentation & README

## Preconditions
- Repository cloned at v0.2.0
- Python 3.10+ installed

## Test Cases

### UAT-01: New developer can install via pip
1. Clone the repo: `git clone <repo> && cd heretek-swarm`
2. Run `pip install -e .`
3. Run `heretek-swarm --version`
**Expected:** Prints `0.2.0` with no errors.

### UAT-02: New developer can start full stack via Docker
1. Clone the repo
2. Run `cp .env.example .env`
3. Edit `.env` to set `OPENAI_API_KEY`
4. Run `docker compose up`
**Expected:** All 6 services start (postgres, redis, qdrant, nats, api, dashboard). API health check passes at :8000. Dashboard accessible at :3000.

### UAT-03: Local run without infrastructure
1. After `pip install -e .`
2. Run `heretek-swarm run --no-infra --prompt "Hello"`
**Expected:** Swarm runs with in-memory state, no infrastructure errors.

### UAT-04: CLI grouped help is documented and accurate
1. Run `heretek-swarm --help`
2. Compare output against README Command Reference section
**Expected:** All 8 commands (run, serve, deploy, wizard, config, init, status, stop) listed. Three groups visible (Core Operations, Configuration, Monitoring). Epilog examples present.

### UAT-05: README test suite verifies claims
1. Run `pytest tests/test_readme_accuracy.py -v`
**Expected:** All 15 tests pass. No failures.

### UAT-06: Full test suite has no regressions
1. Run `pytest tests/ -q`
**Expected:** Exit code 0. All tests pass (1 skipped integration test). No "Unclosed client session" warnings.

### Edge Cases
- **No .env file:** README documents `cp .env.example .env` step
- **No Docker:** README documents pip-only path with --no-infra
- **Hyphenated docker-compose:** Test verifies no V1 `docker-compose <subcommand>` usage in instructions (only filename references allowed)
