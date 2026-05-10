# Heretek Swarm — Project Status

## Active Milestone

**M003: Type-seal Mixin contracts and make stub injection first-class** (in progress)

| Slice | Status | Title |
|-------|--------|-------|
| S01 | ✅ Complete | Add __init__ exports and fail-fast type guards to all mixin methods |
| S02 | ✅ Complete | Make stubs first-class constructor arguments |
| S03 | Pending | Add mixin __init__.py exports and smoke test for stub injection |

## Completed Milestones

| ID | Title | Completed | Outcome |
|----|-------|-----------|---------|
| M001 | Collapse dual actors/ directory into one canonical location | 2025-05-07 | ✅ Canonical `heretek_swarm/actors/__init__.py` established; shim files deleted |
| M002 | Unify validation into a single entry point | 2026-05-07 | ✅ ValidationMixin is single source of truth; backward-compat shims in place |
| M004 | Add integration test scaffold and CI surface | 2026-05-10 | ✅ 658-test baseline verified, 26 lifecycle smoke tests for all 24 AgentActor subclasses, pass/fail-gated CI with Ruff quality gate |

## Current State

- **Test infrastructure**: pytest 9.0.3 collects 658 tests across 43 files with strict-markers validation. 26 parameterized lifecycle smoke tests cover all 24 AgentActor subclasses plus BehaviorProfiler and ActorSupervisor, using 6 infrastructure-free stubs (StubAccessAnalyzer, StubPatternExtractor, StubTribunal, StubDeliberationEngine, StubLLMProvider, StubEventMesh).
- **CI pipeline**: GitHub Actions runs unit-only pytest (`-m "not integration"`) and ruff check on push/PR to main/develop. Proper pass/fail gating (no `|| true`). Ruff warning gate fails CI at 50+ findings.
- **Validation architecture**: Unified. `ValidationMixin` in `actors/mixins/validation.py` is the single source of truth for `IMMUTABLE_RULES` (8 security patterns) and `BASELINE_CONFIG` (9 configuration keys). `actors/validation.py` provides backward-compat shims with deprecation notes.
- **Pydantic models**: All actor message models live in `heretek_swarm/schemas/actors.py` as the canonical import path.
- **Actors import surface**: Unified. All agent classes import from `heretek_swarm.actors` via `__init__.py` re-export surface.
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
