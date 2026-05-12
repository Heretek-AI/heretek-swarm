---
estimated_steps: 8
estimated_files: 5
skills_used: []
---

# T03: Run full integration verification suite

Execute the complete M007 acceptance verification suite to prove the restructured repo works for a fresh clone:

1. `pip install -e .` — editable install succeeds (already working as of S02)
2. `python -c "import heretek_swarm; print(heretek_swarm.__file__)"` — resolves to `backend/heretek_swarm/__init__.py`
3. `pytest -m "not integration" -q` — unit test suite passes (note: `test_heartbeat_bus.py::test_stale_agent_reported` has a pre-existing failure unrelated to restructure — method `_check_registry_heartbeats` is missing from StewardAgent)
4. `ruff check backend/ tests/` — ruff passes
5. `docker compose config` — Docker compose file parses correctly
6. `git grep "heretek-swarm/" -- :!.gsd/ :!.git/` — returns only GitHub URL references and pypi URLs, no filesystem paths

Document any pre-existing test failures as known limitations in the summary.

## Inputs

- `pyproject.toml`
- `backend/Dockerfile`
- `docker-compose.yml`
- `.github/workflows/ci.yml`
- `.github/workflows/ci-cd.yml`

## Expected Output

- Update the implementation and proof artifacts needed for this task.

## Verification

All 6 verification commands exit with code 0 (or expected results documented)
