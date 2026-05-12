---
phase: M005
phase_name: "Document architecture and compress flat actor API surface"
project: heretak-swarm
generated: "2026-05-12T01:30:00.000Z"
counts:
  decisions: 4
  lessons: 3
  patterns: 5
  surprises: 3
missing_artifacts:
  - S01-ASSESSMENT.md
  - S03-ASSESSMENT.md
---

### Decisions

- **D1: Split vs. Simple subpackage convention** — Chose a uniform two-pattern system: complex actors (with helper types like enums/dataclasses) use `types.py + agent.py + __init__.py`, simple actors use `agent.py + __init__.py`. This avoids the complexity of a single mandatory pattern while keeping the structure predictable. 0/24 agents deviate from this convention.
  Source: S03-SUMMARY.md/Key Decisions

- **D2: EchoActor→EchoAgent rename** — Renamed to align with the AgentActor naming convention (all other classes are `*Agent`). Updated across exactly 6 call sites following the established rename procedure. Chose a clean break (no backward-compat alias) since `EchoActor` wasn't in public API tests beyond lifecycle smoke tests.
  Source: S03-SUMMARY.md/Key Decisions

- **D3: Handoff type deduplication** — `HandoffContext` and `HandoffResult` were defined identically in both `handoff.py` and `handoff_handlers.py`. Chose to consolidate into a single `handoff/types.py` with both modules importing from the canonical source rather than keeping the duplicated definitions with a comment.
  Source: S03-SUMMARY.md/Key Decisions

- **D4: structlog consolidation via delegation** — `init_logging()` in `infrastructure/otel/logging.py` now delegates to `setup_logging()` from `logging/config.py` instead of calling `structlog.configure()` directly. Chose delegation over removal to preserve the `LoggingConfig` dataclass interface while ensuring only one `structlog.configure()` call exists.
  Source: S02-SUMMARY.md/Key Decisions

### Lessons

- **L1: Test count baselines must be documented at each milestone boundary** — M004 established 658 tests as baseline; M005 S03 verified 370 pass. The 288-test gap is primarily integration/slow tests that were not in scope for S03's flat-compression verification. No documentation explains the gap. Future milestones must explicitly record test counts at entry and exit.
  Source: M005-VALIDATION.md/Verification Classes

- **L2: Slice dependency metadata must match actual work** — S02 declared `requires: [S01]` and `affects: [S03]`, but all three slices were functionally independent (touched disjoint file sets). The ROADMAP correctly showed `depends:[]` for all slices. Dependency metadata should be verified against the actual diff, not assumed from chronological ordering.
  Source: M005-VALIDATION.md/Cross-Slice Integration

- **L3: Auto-mode recovery should preserve task-level evidence** — S01's `complete-slice` unit failed to produce a SUMMARY.md, but the two task summaries (T01-SUMMARY.md, T02-SUMMARY.md) were correctly persisted and contained enough evidence to reconstruct the slice narrative. The task-level granularity saved this milestone from a full re-do.
  Source: S01-SUMMARY.md (recovered from placeholder)

### Patterns

- **P1: Split subpackage pattern** — For agents with helper types: `types.py` (enums/dataclasses) + `agent.py` (AgentActor subclass) + `__init__.py` (absolute re-exports). Applied to 6+ subpackages (historian, coder, catalyst, perceiver, echo, handoff).
  Source: S03-SUMMARY.md/Patterns Established

- **P2: Simple subpackage pattern** — For agents without helper types: `agent.py` only + `__init__.py` with absolute re-exports. Applied to metis, empath, and all previously-existing subpackages.
  Source: S03-SUMMARY.md/Patterns Established

- **P3: Flat-file re-export stub pattern** — Replace implementation `.py` files with thin stubs: `from heretek_swarm.actors.X import *` + `__all__` for explicit surface. Preserve private constants for test compatibility. 14 flat files follow this pattern.
  Source: S03-SUMMARY.md/Patterns Established

- **P4: Agent rename procedure** — Six-site update sequence: (1) class definition → (2) subpackage `__init__.py` → (3) `actors/__init__.py` public API → (4) `api/main.py` dispatch → (5) `runtime/main_loop.py` dispatch → (6) tests → (7) docs. Applied to EchoActor→EchoAgent.
  Source: S03-SUMMARY.md/Patterns Established

- **P5: structlog consolidation pattern** — All `structlog.configure()` calls route through `logging/config.py` as single source of truth. Other modules delegate via `setup_logging()` parameters rather than calling `structlog.configure()` directly. Verified: exactly 1 `structlog.configure()` in codebase.
  Source: S02-SUMMARY.md/Patterns Established

### Surprises

- **S1: S01 auto-mode complete-slice failure** — The `complete-slice` unit for M005/S01 failed to produce S01-SUMMARY.md after idle recovery exhausted retries. Root cause: tools-policy restriction (`planning-dispatch` limits bash to read-only) prevented the unit from running verification commands. The task-level evidence (T01-SUMMARY.md, T02-SUMMARY.md) was intact and sufficient for reconstruction.
  Source: S01-SUMMARY.md (blocker placeholder)

- **S2: ROADMAP dependency graph was incorrect** — The ROADMAP correctly showed `depends:[]` for all three slices, but slice summaries introduced phantom dependencies. S02's `requires: [S01]` was inaccurate — S02 touched `core.py` and `otel/logging.py`, while S01 touched `docs/ARCHITECTURE.md` and `docs/actors/README.md`. The slices were fully parallelizable.
  Source: M005-VALIDATION.md/Cross-Slice Integration

- **S3: actors/README.md code blocks rendered empty** — T02-SUMMARY.md reports "Full walkthrough with a CustomQA agent example" and verification confirmed `AgentActor` + `__init__` references, but the file on disk has zero code blocks — all backtick-delimited sections are empty placeholders. Likely a rendering/persistence artifact where code was embedded but stripped before disk write.
  Source: M005-VALIDATION.md/Success Criteria Checklist
