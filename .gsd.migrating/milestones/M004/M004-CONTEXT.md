# M004: Add integration test scaffold and CI surface

**Gathered:** 2026-05-10
**Status:** Ready for planning

## Project Description

Heretek Swarm v2.0 is a next-generation multi-agent system built on the Swarms framework. With 413 source files, 16+ canonical agent classes (AlphaAgent, BetaAgent, CharlieAgent, CatalystAgent, ChronosAgent, CoderAgent, CoordinatorAgent, DreamerAgent, EmpathAgent, ExaminerAgent, ExplorerAgent, HabitForgeAgent, etc.), and ~1004 test functions across 59 test files, the project needs a proper test baseline and a CI surface that actually gates quality.

## Why This Milestone

The project has accumulated tests organically but has no reliable CI gate — every step uses `|| true` to swallow failures, Postgres/Redis/Qdrant services spin up for every run even when not needed, coverage reporting points at a `src/` directory that doesn't exist, and there are no markers distinguishing unit from integration tests. Without this foundation, every subsequent change risks silent regressions.

## User-Visible Outcome

### When this milestone is complete, the user can:

- Run `pytest --co -q` and see all ~1004 tests collected without errors
- Run `pytest -m "not integration" -x -q` and get fast feedback in under 2 minutes
- Push a PR and see CI report pass/fail — no more `|| true` swallows
- Run `ruff check src/ tests/` and get fewer than 50 warnings

### Entry point / environment

- Entry point: GitHub Actions on push/PR
- Environment: CI on ubuntu-latest
- Live dependencies involved: none for unit CI (Postgres/Redis/Qdrant services removed from default run)

## Completion Class

- **Contract complete means:** `pytest --co -q --strict-markers` collects all tests without errors; coverage source path points to the real package root (`heretek-swarm/`)
- **Integration complete means:** All 16+ agent classes have lifecycle smoke tests that pass; CI runs pytest + ruff on push/PR and reports correct pass/fail
- **Operational complete means:** CI completes in under 2 minutes; Ruff fails CI if warnings >= 50

## Final Integrated Acceptance

To call this milestone complete, we must prove:

- `pytest --co -q --strict-markers` on the full test suite collects without errors
- `pytest -m "not integration" -x -q` completes in under 2 minutes in CI
- A deliberate test failure in a PR causes CI to report "fail" (not pass via `|| true`)
- `ruff check src/ tests/` reports < 50 warnings
- All 16+ agent lifecycle tests pass

## Architectural Decisions

### Coverage source path correction

**Decision:** Change `[tool.coverage.run] source = ["src"]` to `source = ["heretek-swarm"]` to match the actual package layout.

**Rationale:** The package lives at `heretek-swarm/heretek_swarm/`. The current `src/` path collects nothing. Pointing at `heretek-swarm/` covers the full package root including the `heretek_swarm/` subdirectory and any top-level modules.

**Alternatives Considered:**
- `source = ["heretek-swarm/heretek_swarm"]` — tighter scope but misses potential top-level modules; the broader path is safer.
- Leave as-is — coverage reporting would remain broken.

### Unit-only CI with marker-based test selection

**Decision:** The primary CI job runs `pytest -m "not integration"` with no external services (Postgres/Redis/Qdrant). Integration tests that need infrastructure will be tagged with `@pytest.mark.integration` and run in a separate job or skipped by default.

**Rationale:** Spinning up Postgres/Redis/Qdrant for every CI run adds ~30-60s and risks flaky failures. Most tests don't need external services. Marker-based selection lets developers opt in to infra tests locally.

**Alternatives Considered:**
- Single monolithic CI with all services — slower, more flaky, wasteful for unit-only changes.
- Two-job split (unit + integration) — better but more complex; can add later if integration test volume grows.

### Hard Ruff gate at < 50 warnings

**Decision:** CI will fail if `ruff check src/ tests/` reports 50 or more warnings.

**Rationale:** The roadmap specifies this threshold. A hard gate prevents gradual style debt accumulation. The threshold is generous enough to pass a moderately messy codebase while preventing unbounded growth.

**Alternatives Considered:**
- Zero-warnings gate — too aggressive for the current codebase state; would block all PRs.
- Informational only — doesn't enforce the standard.

---

## Error Handling Strategy

CI errors must be visible. Remove all `|| true` swallow patterns. If pytest exits non-zero, CI reports failure. Ruff exiting with warnings >= 50 counts as failure. Coverage failures are reported but should not block CI (the coverage configuration needs to stabilize first).

## Risks and Unknowns

- **External imports in test files:** Some test files may import redis/qdrant/postgres modules at the module level, causing `ImportError` when services aren't available. These will need fixture-level or function-level imports, or `@pytest.mark.integration` + `pytest.importorskip()` guards.
- **Marker audit:** Currently only `asyncio` (111 uses) and `parametrize` (2 uses) appear as markers. No tests are tagged `integration`, `slow`, `security`, etc. Adding marker-based filtering means either (a) tagging all non-unit tests retroactively, or (b) making the CI filter more nuanced (e.g., exclude known-slow file patterns).
- **Ruff baseline:** We don't know the current warning count. If it's far above 50, either fix the worst offenders as part of this milestone or adjust the threshold.
- **2-minute CI budget:** With ~1004 tests, running everything under 2 minutes requires excluding integration tests and possibly excluding known-slow test files. If the unit set itself exceeds 2 minutes, further profiling will be needed.

## Existing Codebase / Prior Art

- `.github/workflows/ci.yml` — Current CI with `|| true` swallows, full service spin-up, broken coverage path
- `pyproject.toml` — Has [tool.pytest.ini_options] with markers defined, strict-markers enabled, asyncio_mode=auto. Coverage config has stale `source = ["src"]`
- `tests/conftest.py` — Will need updates for asyncio_mode support and integration test helpers
- `tests/` (43 files) and `heretek-swarm/tests/` (16 files) — Two test directories discovered by pytest's testpaths

## Relevant Requirements

No formal requirements defined for test infrastructure. This milestone establishes the foundation.

## Scope

### In Scope

- Install dev dependencies into .venv
- Fix coverage source path to point at `heretek-swarm/`
- Verify pytest collects all test files across both `tests/` and `heretek-swarm/tests/` (~59 files, ~1004 tests)
- Ensure `--strict-markers` passes — no UNREGISTERED_MARKER errors
- Write lifecycle smoke tests for all 16+ AgentActor subclasses
- Replace CI `|| true` with proper pass/fail gating
- Remove Postgres/Redis/Qdrant services from the primary CI test job
- Add marker-based test selection (unit-only CI via `-m "not integration"`)
- Add Ruff lint CI with hard <50 warning gate
- Ensure CI completes in under 2 minutes

### Out of Scope / Non-Goals

- Writing integration tests that exercise external services (Redis, Qdrant, Postgres) — those existing tests are grandfathered and run without gates
- Adding new test coverage beyond the lifecycle smoke tests
- Refactoring or rewriting existing tests for quality — just getting them to collect and run
- Fixing all Ruff warnings below 50 — just adding the gate and fixing the worst offenders if needed
- Frontend linting or testing improvements — CI already runs them with `|| true`, leave as-is

## Technical Constraints

- CI must run on ubuntu-latest with no special hardware
- Python 3.11 (per CI config)
- Dev dependencies installable via `pip install -e ".[dev]"`
- No API keys or external credentials required for unit tests
- 2-minute CI completion target

## Integration Points

- GitHub Actions — CI pipeline in `.github/workflows/ci.yml`
- pytest — test collection, execution, marker filtering
- Ruff — lint quality gate
- pyproject.toml — test configuration, marker registration, coverage config

## Testing Requirements

All testing infrastructure changes must themselves be verified:
- `pytest --co -q --strict-markers` → exit 0, all files collected
- `pytest -m "not integration" -x -q` → fast completion
- Lifecycle tests pass for each agent class independently
- CI pipeline: push non-failing change → green check; push failing change → red X
- `ruff check src/ tests/` → exit 0 (or exit 1 with < 50 warnings depending on current baseline)

## Acceptance Criteria

**S01 — Baseline existing tests and configure pytest:**
- `pytest --co -q` collects all test files without import or collection errors
- Coverage `source` points to `heretek-swarm/` instead of `src/`
- `pytest --co -q --strict-markers` passes with no UNREGISTERED_MARKER errors
- Dev dependencies installed and pytest CLI available

**S02 — Write actor lifecycle smoke tests:**
- Every AgentActor subclass (16+) has a lifecycle test: instantiate → send a message → confirm graceful stop
- Tests are marked `@pytest.mark.unit` (or no marker, run by default)
- Tests use stubs/mocks, not real external services
- Smoke tests complete in under 30s total

**S03 — Add GitHub Actions CI for pytest and ruff:**
- CI runs on push/PR to main/develop
- Primary job: `pytest -m "not integration" -x -q` — no Postgres/Redis/Qdrant services
- No `|| true` on test or lint steps
- Ruff lint step with hard < 50 warning gate
- CI completes in under 2 minutes
- Frontend lint job preserved as-is (still with `|| true` — out of scope)

## Open Questions

- What is the current Ruff warning count on `src/ tests/`? If it's far above 50, we may need a remediation pass or a higher temporary threshold.
- Some test files may have top-level imports of redis/qdrant/asyncpg that will fail without services — will need to audit and guard these with `pytest.importorskip()` or mark them `@pytest.mark.integration`.
- Which of the 16+ agent classes require stubs beyond what test_stub_injection.py already provides? The existing stub injection tests cover 6 stub protocols, but ChronosAgent, CoordinatorAgent, and other complex agents may need additional stubs.
