# Heretek Swarm — Project Status

## Active Milestone

**None** — M007 awaits planning.

## Completed Milestones

| ID | Title | Completed | Outcome |
|----|-------|-----------|---------|
| M001 | Collapse dual actors/ directory into one canonical location | 2025-05-07 | ✅ Canonical `heretek_swarm/actors/__init__.py` established; shim files deleted |
| M002 | Unify validation into a single entry point | 2026-05-07 | ✅ ValidationMixin is single source of truth; backward-compat shims in place |
| M003 | Type-seal Mixin contracts and make stub injection first-class | 2026-05-10 | ✅ 6 mixin classes with fail-fast __init__ guards; 6 protocol stub classes as first-class kwargs; 14 tests |
| M004 | Add integration test scaffold and CI surface | 2026-05-10 | ✅ 658-test baseline verified, 26 lifecycle smoke tests for all 24 AgentActor subclasses, pass/fail-gated CI with Ruff quality gate |
| M005 | Document architecture and compress flat actor API surface | 2026-05-12 | ✅ ARCHITECTURE.md (12 sections, all 10 mixins), actors/README.md (6 sections, 23-agent table), structlog consolidated to single entry point, 14 flat files converted to thin re-exports, uniform subpackage convention for all 24 agents |
| M006 | Audit and plan repository restructure | 2026-05-12 | ✅ 4-document migration blueprint (FILE_INVENTORY.md, IMPORT_MAP.md, CI_IMPACT.md, M006-PLAN.md) covering 856 files, 429 Python imports, 22 config change sites; M007-ready with 9-task decomposition |

## Current State

- **Repository structure**: `heretek-swarm/` project subdirectory contains the Python package `heretek_swarm/`. M006 produced a complete migration plan to rename `heretek-swarm/` → `backend/` via a single `git mv` + 22 config line edits with zero Python code changes. Execution deferred to M007.
- **Test infrastructure**: pytest 9.0.3 collects ~370 unit tests (all passing). 26 parameterized lifecycle smoke tests cover all 24 AgentActor subclasses plus BehaviorProfiler and ActorSupervisor, using 6 infrastructure-free stubs (StubAccessAnalyzer, StubPatternExtractor, StubTribunal, StubDeliberationEngine, StubLLMProvider, StubEventMesh). Integration tests run separately.
- **CI pipeline**: GitHub Actions runs unit-only pytest (`-m "not integration"`) and ruff check on push/PR to main/develop. Proper pass/fail gating (no `|| true`). Ruff warning gate fails CI at 50+ findings.
- **Validation architecture**: Unified. `ValidationMixin` in `actors/mixins/validation.py` is the single source of truth for `IMMUTABLE_RULES` (8 security patterns) and `BASELINE_CONFIG` (9 configuration keys). `actors/validation.py` provides backward-compat shims with deprecation notes.
- **Pydantic models**: All actor message models live in `heretek_swarm/schemas/actors.py` as the canonical import path.
- **Actors import surface**: Unified. All 24 agent classes import from `heretek_swarm.actors` via `__init__.py` re-export surface. Every agent follows a uniform subpackage convention: complex agents use split pattern (`types.py + agent.py`), simple agents use `agent.py` only. All 14 surviving flat `.py` files are thin re-export stubs with zero class definitions.
- **Logging**: `logging/config.py` is the single source of truth for structlog configuration. `core.py` imports `get_logger` from the canonical path. `init_logging()` in `otel/logging.py` delegates to `setup_logging()`. Exactly one `structlog.configure()` call exists in the codebase.
- **Documentation**: `docs/ARCHITECTURE.md` (914 lines, 12 sections) covers the full system: package structure, actor architecture, all 10 mixins, memory system, event mesh, configuration, security, and observability. `docs/actors/README.md` (16.5KB, 6 sections) provides a practical agent creation guide with 23-agent reference table.
- **Coverage and linting configuration**: Coverage source points to `heretek-swarm/` package root (was broken `src/`). Ruff src roots corrected to `["heretek-swarm", "tests"]`. Coverage paths prefix uses `heretek-swarm/`.
- **Mixin type guards**: All 6 mixin classes have `_validate_dependencies()` guards that raise `TypeError` when a required dependency attribute is `None`.
- **Stub injection**: 6 protocol stub classes are first-class `AgentActor.__init__` kwargs. Mixin deps use public instance attrs; core deps use private attrs with `value or fallback()` for backward compat. 14 tests in `tests/test_stub_injection.py`.

## Architecture Notes

- `heretek_swarm/actors/__init__.py` is the single canonical import surface for all agent classes.
- `ValidationMixin` is the single source of truth for immutable security rules and behavioral baseline configuration.
- All Pydantic models live in `heretek_swarm/schemas/actors.py`.
- `actors/base/core.py` delegates validation to `actors/validation.py` only.
- Mixin deps use public instance attrs (`self.access_analyzer`) for MRO-visible mixin access; core deps use private names (`self._llm_provider`) for internal consumption. Kwargs typed as `Any | None = None` to avoid circular imports.
- CI uses unit-only test selection with marker-based isolation (`@pytest.mark.integration`); full-service tests run separately.
- `logging/config.py` is the single source of truth for structlog configuration; all other modules delegate via `setup_logging()`.
- All 24 agents follow uniform subpackage convention: split pattern (types.py + agent.py) for complex actors, simple pattern (agent.py only) for straightforward ones.
- Python resolves modules by package name (`heretek_swarm`), not filesystem directory name (`heretek-swarm`). Directory renames are transparent to Python imports as long as pyproject.toml `where`/`source` directives are updated.
- `swarm-dashboard/` has zero filesystem-level dependencies on the backend directory — fully decoupled.
