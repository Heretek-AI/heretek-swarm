---
id: S03
parent: M002
milestone: M002
provides:
  - ValidationMixin as single canonical source for immutable security rules (8 patterns) and behavioral baseline configuration (9 config keys)
  - Backward-compat shims in actors/validation.py for zero-diff migration of ~40 callers
requires:
  - slice: S01
    provides: documentation of all validation functions mapped to homes
  - slice: S02
    provides: Pydantic models consolidated in schemas/actors.py
affects:
  []
key_files:
  - heretek-swarm/heretek_swarm/actors/mixins/validation.py
  - heretek-swarm/heretek_swarm/actors/validation.py
key_decisions:
  - ValidationMixin is now the single source of truth for IMMUTABLE_RULES (8 security patterns) and BASELINE_CONFIG (9 config keys), making the mixin own both static constants and runtime behavioral baseline tracking.
  - Backward-compat shims in actors/validation.py delegate to the mixin with a deprecation docstring, allowing ~40 existing callers to work unchanged with zero cascading import changes.
patterns_established:
  - When consolidating duplicated constants between a module and a class, use backward-compat shims that delegate to the new source of truth plus a deprecation docstring at the module top.
observability_surfaces:
  - none
drill_down_paths:
  - .gsd/milestones/M002/slices/S03/tasks/T01-SUMMARY.md — Moved constants into mixin
  - .gsd/milestones/M002/slices/S03/tasks/T02-SUMMARY.md — Full test suite verification (658 pass)
  - .gsd/milestones/M002/slices/S03/tasks/T03-SUMMARY.md — Full test suite verification (659 pass)
duration: ""
verification_result: passed
completed_at: 2026-05-07T16:11:57.234Z
blocker_discovered: false
---

# S03: Consolidate ValidationMixin and deprecate duplicates

**Consolidated IMMUTABLE_RULES (8 security patterns) and BASELINE_CONFIG (9 config keys) from module-level globals in actors/validation.py into ValidationMixin class-level attributes with backward-compat shims — making ValidationMixin the single canonical source of truth for behavioral baseline constants.**

## What Happened

S03 completed the ValidationMixin consolidation across three tasks. T01 moved IMMUTABLE_RULES, BASELINE_CONFIG, get_immutable_rules(), and get_baseline_config() from module-level globals in actors/validation.py into ValidationMixin as class-level attributes and classmethods. Added backward-compat shims in actors/validation.py with a deprecation docstring at the module top. T02 verified the full test suite (658 passed, 1 skipped) after refactoring — confirming all ~40 existing callers work unchanged. T03 re-verified after a no-op commit attempt (659 passed, 1 skipped). The result is a single ValidationMixin class owning all behavioral baseline constants, with zero regressions across the codebase.

## Verification

Verified: (1) Only one ValidationMixin class definition exists in the codebase (grep confirmed). (2) IMMUTABLE_RULES has 8 security patterns as ValidationMixin class attribute. (3) BASELINE_CONFIG has 9 keys as ValidationMixin class attribute. (4) actors/validation.py backward-compat shims (IMMUTABLE_RULES, BASELINE_CONFIG, get_immutable_rules(), get_baseline_config()) all delegate to ValidationMixin with deprecation docstring. (5) Full pytest suite passed: 659 passed, 1 skipped (integration requiring HERETEK_RUN_INTEGRATION=1) — zero regressions across ~40 import sites.

## Requirements Advanced

None.

## Requirements Validated

None.

## New Requirements Surfaced

None.

## Requirements Invalidated or Re-scoped

None.

## Operational Readiness

None.

## Deviations

None.

## Known Limitations

None. All slice must-haves are met: IMMUTABLE_RULES is a ValidationMixin class attribute, get_immutable_rules() returns 8 rules, actors/validation.py re-exports for backward compat, all callers work, test suite passes.

## Follow-ups

The deprecation docstring in actors/validation.py notes the shims will be removed in a future release — a future slice could update all ~40 import sites to import directly from the mixin and remove the shims.

## Files Created/Modified

None.
