# Heretek Swarm — Project Status

## Active Milestone

**None** — no milestone is currently in progress.

## Completed Milestones

| ID | Title | Completed | Outcome |
|----|-------|-----------|---------|
| M001 | Collapse dual actors/ directory into one canonical location | 2025-05-07 | ✅ Canonical `heretek_swarm/actors/__init__.py` established; shim files deleted |
| M002 | Unify validation into a single entry point | 2026-05-07 | ✅ ValidationMixin is single source of truth; backward-compat shims in place |
| M003 | Type-seal Mixin contracts and make stub injection first-class | 2026-05-10 | ✅ 6 mixin classes with fail-fast __init__ guards; 6 protocol stub classes as first-class kwargs; 14 tests |
| M004 | Add integration test scaffold and CI surface | 2026-05-10 | ✅ 658-test baseline verified, 26 lifecycle smoke tests for all 24 AgentActor subclasses, pass/fail-gated CI with Ruff quality gate |
| M005 | Document architecture and compress flat actor API surface | 2026-05-12 | ✅ ARCHITECTURE.md (12 sections, all 10 mixins), actors/README.md (6 sections, 23-agent table), structlog consolidated to single entry point, 14 flat files converted to thin re-exports, uniform subpackage convention for all 24 agents |
| M006 | Audit and plan repository restructure | 2026-05-12 | ✅ 4-document migration blueprint (FILE_INVENTORY.md, IMPORT_MAP.md, CI_IMPACT.md, M006-PLAN.md) covering 856 files, 429 Python imports, 22 config change sites; M007-ready with 9-task decomposition |
| M007 | Execute repository restructure | 2026-05-12 | ✅ `heretek-swarm/` renamed to `backend/` via git mv (463 files, R100 rename); 18 path references updated across 5 config/CI files; 16 inner test files consolidated into root tests/ (62 total); 12 stale files purged across 4 pre-rename directories |
| M008 | Post-Restructure Cleanup & Hardening | 2026-05-13 | ✅ 5 slices, 28 files touched. 13 tracked garbage files purged and `=*` .gitignore prevention rule added. 4 stale root files deleted (triage_classifier.py, audit/cli.py, audit-report.md, triage_data.json). 54 stale path references fixed across 22 doc files. 7 stale src/ refs replaced across 4 Python source files. 8/8 static verification checks passing. Zero functional code changes. |

## Current State

- **Repository root**: Clean. Zero tracked garbage files (`=*.0`, `0`) remain. Zero stale root files. `.gitignore:155` carries a `=*` prevention rule under "Garbage build artifacts" to block recurrence. Root-level `audit/` directory removed — canonical audit lives at `backend/heretek_swarm/audit/`.
- **Repository structure**: `backend/heretek_swarm/` is the single canonical Python source directory. `swarm-dashboard/` is the frontend. Root `tests/` contains all 62 test files. Old `heretek-swarm/` and `src/` directories fully removed. Inner `backend/docs/` and `backend/agent_workspace/` copies purged — canonical copies are at root `docs/` and `agent_workspace/` respectively.
- **Documentation**: All 22 doc files have path references updated to `backend/heretek_swarm/`. The 14 remaining `heretek-swarm/` references are legitimate project-identity strings: GitHub URLs, SSM parameters, CLI config defaults, and log paths. CLAUDE.md has zero `src/` references. README.md directory tree and install instructions reference `backend/`.
- **Code comments/docstrings**: All Python source comments and docstrings reference `backend/` (not `src/` or `heretek-swarm/`). Primary grep `grep -rn 'src/' backend/heretek_swarm/ --include='*.py'` returns zero matches.
- **Test infrastructure**: 62 test files in root `tests/`, all importing from `heretek_swarm.*`. pytest 9.0.3 collects ~370 unit tests. 26 parameterized lifecycle smoke tests cover all 24 AgentActor subclasses. Runtime verification deferred to dev environment (sandbox lacks pip/pytest/ruff/docker).
- **CI pipeline**: GitHub Actions runs unit-only pytest and ruff check on push/PR to main/develop. All bandit, ruff, mypy, and pytest invocations reference `backend/` paths. Coverage uses `--cov=backend`. Zero stale `heretek-swarm/` or `src/` tooling paths remain in CI. All 6 workflow files audited and verified correct.
- **Validation architecture**: Unified. `ValidationMixin` in `actors/mixins/validation.py` is the single source of truth for `IMMUTABLE_RULES` (8 security patterns) and `BASELINE_CONFIG` (9 configuration keys). `actors/validation.py` provides backward-compat shims with deprecation notes.
- **Pydantic models**: All actor message models live in `heretek_swarm/schemas/actors.py` as the canonical import path.
- **Actors import surface**: Unified. All 24 agent classes import from `heretek_swarm.actors` via `__init__.py` re-export surface. Every agent follows a uniform subpackage convention: complex agents use split pattern (`types.py + agent.py`), simple agents use `agent.py` only. All 14 surviving flat `.py` files are thin re-export stubs with zero class definitions.
- **Logging**: `logging/config.py` is the single source of truth for structlog configuration. `core.py` imports `get_logger` from the canonical path. `init_logging()` in `otel/logging.py` delegates to `setup_logging()`. Exactly one `structlog.configure()` call exists in the codebase.
- **Documentation**: `docs/ARCHITECTURE.md` (914 lines, 12 sections) covers the full system: package structure, actor architecture, all 10 mixins, memory system, event mesh, configuration, security, and observability. `docs/actors/README.md` (16.5KB, 6 sections) provides a practical agent creation guide with 23-agent reference table.
- **Build configuration**: `pyproject.toml` `where`/`source`/`src` directives all point to `backend`. `docker-compose.yml` dockerfile path is `backend/Dockerfile`. Dockerfile COPY paths reference `backend/`. Zero stale path references remain in build config.

## Architecture Notes

- `heretek_swarm/actors/__init__.py` is the single canonical import surface for all agent classes.
- `ValidationMixin` is the single source of truth for immutable security rules and behavioral baseline configuration.
- All Pydantic models live in `heretek_swarm/schemas/actors.py`.
- `actors/base/core.py` delegates validation to `actors/validation.py` only.
- Mixin deps use public instance attrs (`self.access_analyzer`) for MRO-visible mixin access; core deps use private names (`self._llm_provider`) for internal consumption. Kwargs typed as `Any | None = None` to avoid circular imports.
- CI uses unit-only test selection with marker-based isolation (`@pytest.mark.integration`); full-service tests run separately.
- `logging/config.py` is the single source of truth for structlog configuration; all other modules delegate via `setup_logging()`.
- All 24 agents follow uniform subpackage convention: split pattern (types.py + agent.py) for complex actors, simple pattern (agent.py only) for straightforward ones.
- Python resolves modules by package name (`heretek_swarm`), not filesystem directory name (`backend`). Directory renames are transparent to Python imports as long as pyproject.toml `where`/`source` directives are updated.
- `swarm-dashboard/` has zero filesystem-level dependencies on the backend directory — fully decoupled.
- `backend/` is the canonical Python project directory paired with `swarm-dashboard/` (frontend). No dash-vs-underscore naming ambiguity remains.
- `.gitignore` carries a `=*` prevention rule at line 155 to block garbage build artifacts (=*.0 pip artifacts, '0' grep redirects) from entering git tracking.

## Known Issues

- Full runtime verification (`pip install -e ".[dev]"`, `pytest tests/`, `ruff check heretek_swarm/ tests/`) must be run in the actual dev environment — sandbox cannot execute these tools. Follow-up command documented in M008-SUMMARY.md. All 8 static verification checks pass; zero functional code was changed across M008.
