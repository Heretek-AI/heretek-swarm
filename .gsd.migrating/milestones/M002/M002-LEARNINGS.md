---
phase: complete-milestone
phase_name: Milestone Completion
project: heretek-swarm
generated: 2026-05-07T16:30:00Z
counts:
  decisions: 5
  lessons: 4
  patterns: 2
  surprises: 1
missing_artifacts:
  - tests/test_validation_consolidation.py (referenced in CONTEXT.md but not in ROADMAP)
---

### Decisions

- schemas/actors.py re-exports from validation.agent_messages only; internal dataclass ActorMessage in actors/base/core.py is intentionally NOT re-exported to avoid name collision.
  Source: S02-SUMMARY.md/key_decisions

- Names absent from agent_messages.py are documented as stubs in _PLAN_REFERENCED_MISSING set with __getattr__ providing clear AttributeError on access.
  Source: S02-SUMMARY.md/key_decisions

- Backward-compat re-exports via actors/base/__init__.py keep existing ~40 callers unbroken — zero cascading import changes.
  Source: S02-SUMMARY.md/key_decisions

- ValidationMixin is the single source of truth for IMMUTABLE_RULES (8 security patterns) and BASELINE_CONFIG (9 config keys), owning both static constants and runtime behavioral baseline tracking.
  Source: S03-SUMMARY.md/key_decisions

- When consolidating duplicated constants, use backward-compat shims that delegate to the new source of truth plus a deprecation docstring at the module top.
  Source: S03-SUMMARY.md/patterns_established

### Lessons

- The _PLAN_REFERENCED_MISSING pattern (set of planned-but-missing names with __getattr__ AttributeError) cleanly handles the gap between planned and implemented public API surface — worth reusing in any schema consolidation effort.
  Source: S02-SUMMARY.md/What Happened

- Backward-compat shims with deprecation docstrings at the module top are a zero-risk migration strategy: ~40 callers unchanged, zero import cascades, and a clear deprecation signal for future cleanup.
  Source: S03-SUMMARY.md/What Happened

- CONTEXT.md acceptance criteria (tests/test_validation_consolidation.py) were not propagated into the ROADMAP or slice plans — this mismatch between CONTEXT.md and ROADMAP should be resolved during planning to avoid acceptance ambiguity.
  Source: M002-ROADMAP.md/Success Criteria, M002-CONTEXT.md/Acceptance Criteria

- The audit-first approach (S01) was valuable: discovering that file locations were already canonical before refactoring prevented unnecessary moves and focused effort on the real issue (duplicated constants vs. file location).
  Source: S01-SUMMARY.md/What Happened

### Patterns

- **PLAN_REFERENCED_MISSING**: When creating a canonical public API surface from existing imports, use a `_PLAN_REFERENCED_MISSING` set with module-level `__getattr__` to provide clear `AttributeError` messages for planned-but-not-yet-exported names instead of silent `ImportError` or missing-name failures.
  Source: S02-SUMMARY.md/patterns_established

- **Backward-compat shim + deprecation**: When consolidating duplicated constants between a module and a class, leave a backward-compat shim in the old location that delegates to the new source of truth, with a deprecation docstring at the module top. All existing callers work unchanged.
  Source: S03-SUMMARY.md/patterns_established

### Surprises

- File locations were already mostly canonical across the three validation layers — the real duplication was not about file placement but about module-level constants (IMMUTABLE_RULES, BASELINE_CONFIG) being duplicated as globals in actors/validation.py while ValidationMixin had its own copy. The consolidation needed was constant ownership, not file relocation.
  Source: S01-SUMMARY.md/What Happened
