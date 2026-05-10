---
phase: closeout
phase_name: closeout-and-verify
project: Heretek Swarm
generated: 2026-05-10T21:05:00Z
counts:
  decisions: 6
  lessons: 4
  patterns: 4
  surprises: 3
missing_artifacts: []
---

# M004: Add integration test scaffold and CI surface — LEARNINGS

## Decisions

- **Coverage source path and ruff src roots correction**: Fixed coverage source from nonexistent `src/` to `heretek-swarm` and ruff src roots from `["src", "tests"]` to `["heretek-swarm", "tests"]` to match actual package layout. The `src/` path collected nothing.  
  Source: S03-SUMMARY.md/Key Decisions

- **Unit-only CI with pass/fail gating**: CI test-python job runs `pytest -m "not integration"` with no external services (Postgres/Redis/Qdrant removed) and proper exit-code-based pass/fail — no `|| true` swallows. Spinning up services for every push was slow and flaky for unit-only changes.  
  Source: S03-SUMMARY.md/Key Decisions

- **Parameterized tests organized by constructor pattern**: 26 lifecycle tests in four groups (simple **kwargs, explicit stubs, config-based, special constructors) instead of one monolithic test per agent. Reduces boilerplate and makes adding new agents trivial.  
  Source: S02-SUMMARY.md/Key Decisions

- **6 dedicated stubs instead of monkey-patch mocking**: StubAccessAnalyzer, StubPatternExtractor, StubTribunal, StubDeliberationEngine, StubLLMProvider, StubEventMesh in conftest.py enable infrastructure-free testing with zero NATS/DB/Redis imports. Keeps tests readable and decoupled from implementation internals.  
  Source: S02-SUMMARY.md/Key Decisions

- **Dev dependency installation bypass**: Installed test packages directly (pytest 9.0.3, etc.) rather than via `[dev]` extras when nats-server in the `[full]` transitive dependency chain is incompatible with Python 3.14.  
  Source: S01-SUMMARY.md/Key Decisions

- **Hard Ruff warning gate**: CI fails if `ruff check` reports 50 or more findings. Prevents gradual style debt accumulation while the threshold is generous enough for current codebase state.  
  Source: S03-SUMMARY.md/Patterns Established

## Lessons

- **`[dev]` extras broken on Python 3.14 via `[full]`**: The `[dev]` extras definition in pyproject.toml depends on `[full]` which declares nats-server — this transitive dependency chain fails on Python 3.14 regardless. Workaround: install test packages directly.  
  Source: S01-SUMMARY.md/Known Limitations

- **Test count was overestimated**: Pre-milestone estimate was ~1004 tests across 59 files; actual baseline was 658 tests across 43 files (35% overestimate). The milestone correctly scoped to what existed.  
  Source: S01-SUMMARY.md/Verification

- **coverage/ruff source paths were silently broken**: `[tool.coverage.run] source = ["src"]` and `[tool.ruff] src = ["src", "tests"]` pointed at a nonexistent `src/` directory. Ruff was scanning the wrong path and coverage reporting collected nothing.  
  Source: S03-SUMMARY.md/Key Decisions

- **CI test-python and mypy steps had `|| true` swallowing failures**: The existing CI workflow used `|| true` on both pytest and mypy commands, meaning CI always reported pass regardless of actual test results.  
  Source: S03-SUMMARY.md/Key Decisions

## Patterns

- **Lifecycle smoke test pattern**: construct with minimal stubs → spawn → assert ACTIVE → send health_check via mailbox → terminate → assert TERMINATED + error_count == 0. Reusable for any AgentActor subclass.  
  Source: S02-SUMMARY.md/Patterns Established

- **CI Ruff warning gate pattern**: Count-based threshold with exit 1 when findings >= 50. Prevents unlimited style debt accumulation while accepting initial baseline.  
  Source: S03-SUMMARY.md/Patterns Established

- **Coverage source path convention**: Point to the actual package root directory (e.g. `heretek-swarm/`) rather than a nonexistent `src/` shim.  
  Source: S03-SUMMARY.md/Patterns Established

- **Dev dependency installation for Python 3.14**: Install test packages directly when the `[full]` extras chain has incompatible transitive dependencies.  
  Source: S01-SUMMARY.md/Patterns Established

## Surprises

- **Agent subclass count exceeded estimate**: 24 AgentActor subclasses were discovered vs the pre-milestone estimate of 16+. S02 covered all 24 plus BehaviorProfiler and ActorSupervisor (26 total tests).  
  Source: S02-SUMMARY.md/Verification

- **CI was running full infrastructure stack on every push**: The test-python job had Postgres/Redis/Qdrant services configured even for unit-only changes — adding ~30-60s per run and introducing flaky failure modes for PRs that only touched Python logic.  
  Source: S03-SUMMARY.md/Key Decisions

- **Existing test baseline was 35% lower than estimated**: Pre-milestone M004-CONTEXT.md estimated ~1004 tests across 59 files. Actual: 658 tests across 43 files. The overestimate was due to organic growth assumptions that didn't match reality.  
  Source: S01-SUMMARY.md/Verification
