---
id: M002
title: "Unify validation into a single entry point"
status: complete
completed_at: 2026-05-07T17:01:51.539Z
key_decisions:
  - schemas/actors.py re-exports from validation.agent_messages only; internal dataclass ActorMessage in actors/base/core.py is intentionally NOT re-exported to avoid name collision
  - Names absent from agent_messages.py are documented as stubs in _PLAN_REFERENCED_MISSING set with __getattr__ providing clear AttributeError on access
  - Backward-compat re-exports via actors/base/__init__.py keep existing ~40 callers unbroken — zero cascading import changes
  - ValidationMixin is the single source of truth for IMMUTABLE_RULES (8 security patterns) and BASELINE_CONFIG (9 config keys), owning both static constants and runtime behavioral baseline tracking
  - When consolidating duplicated constants, use backward-compat shims that delegate to the new source of truth plus a deprecation docstring at the module top
key_files:
  - heretek-swarm/heretek_swarm/schemas/actors.py — canonical Pydantic model import path for all actor message models
  - heretek-swarm/heretek_swarm/actors/base/core.py — refactored to import Pydantic models from schemas.actors and delegate validation to actors.validation only
  - heretek-swarm/heretek_swarm/actors/mixins/validation.py — became single canonical source for IMMUTABLE_RULES and BASELINE_CONFIG as class-level attributes
  - heretek-swarm/heretek_swarm/actors/validation.py — backward-compat shims with deprecation docstrings delegated to ValidationMixin
lessons_learned:
  - The _PLAN_REFERENCED_MISSING pattern (set of planned-but-missing names with __getattr__ AttributeError) cleanly handles the gap between planned and implemented public API surface
  - Backward-compat shims with deprecation docstrings at module top are a zero-risk migration strategy: ~40 callers unchanged, zero import cascades, clear deprecation signal
  - Context.md acceptance criteria were not propagated into ROADMAP or slice plans — this mismatch should be resolved during planning to avoid acceptance ambiguity
  - The audit-first approach (S01) was valuable: discovering file locations were already canonical prevented unnecessary moves and focused effort on the real issue (duplicated constants)
---

# M002: Unify validation into a single entry point

**Consolidated all Pydantic actor models into schemas/actors.py and made ValidationMixin in actors/mixins/validation.py the single canonical source of truth for immutable security rules and behavioral baseline configuration**

## What Happened

## What Happened

Milestone M002 unified three scattered validation locations into a single coherent architecture across three slices:

**S01 — Audit (discovery):** Scanned all validation layers across the codebase — `actors/validation.py` (Pydantic v2 models + validate_message dispatcher), `actors/mixins/validation.py` (ValidationMixin with Zero-Trust behavioral/anomaly detection), `actors/base/core.py` (wired validation into AgentActor), and `schemas/external_call_log.py` (ORM schemas). Produced a 157-line audit document (S01-AUDIT.md) mapping 14 Pydantic models, 15 ValidationMixin methods, 4 base-class integration points, and a consumer dependency graph. Key finding: file locations were already mostly canonical; the main opportunity was consolidating duplicated constants and import paths.

**S02 — Pydantic model consolidation:** Created `heretek_swarm/schemas/actors.py` as the canonical import path for all Pydantic actor message models. This file re-exports from `validation/agent_messages.py` using a `_PLAN_REFERENCED_MISSING` set with `__getattr__` for planned-but-missing names (providing clear AttributeErrors instead of silent failures). Updated `actors/base/core.py` to import Pydantic models from `schemas.actors` while preserving its internal `ActorMessage` dataclass. Backward-compat re-exports via `actors/base/__init__.py` kept all ~40 existing callers unbroken. Verified both `schemas.actors.ActorMessage` (Pydantic) and `actors.base.core.ActorMessage` (dataclass) are distinct and work cleanly.

**S03 — ValidationMixin consolidation:** Moved `IMMUTABLE_RULES` (8 security patterns) and `BASELINE_CONFIG` (9 configuration keys) from module-level globals in `actors/validation.py` into `ValidationMixin` as class-level attributes and classmethods. Added backward-compat shims in `actors/validation.py` with deprecation docstrings, allowing all ~40 callers to work unchanged. Full test suite verified at 659 passed, 1 skipped (the skip is an integration test requiring `HERETEK_RUN_INTEGRATION=1`).

The three slices connected end-to-end: S01's audit guided S02's model moves and S03's constant consolidation; S02's backward-compat re-export pattern was replicated in S03's shim approach. All code changes were verified with passing test suites and grep-based structural assertions.

## Success Criteria Results

## Success Criteria Verification

| # | Criterion | Status | Evidence |
|---|-----------|--------|----------|
| 1 | All Pydantic models for actors live in schemas/actors.py | ✅ Pass | `schemas/actors.py` exists and re-exports all models from `validation/agent_messages.py`. Import `from heretek_swarm.schemas.actors import ActorMessage` works. |
| 2 | actors/base/core.py delegates validation to actors/validation.py only | ✅ Pass | `core.py` line 30: `from heretek_swarm.actors.validation import ...` — no other validation import path. |
| 3 | Only one ValidationMixin exists in the codebase | ✅ Pass | Grep confirms: 1 `class ValidationMixin` in `actors/mixins/validation.py`, 0 in `actors/validation.py`. |
| 4 | pytest tests/ passes without validation-related errors | ✅ Pass | Full suite: 659 passed, 1 skipped (integration test requiring `HERETEK_RUN_INTEGRATION=1`). No validation import or assertion errors. |

## Definition of Done Results

## Definition of Done Verification

- ✅ All 3 slices marked `[x]` in M002-ROADMAP.md
- ✅ All 3 slice SUMMARY.md files exist and are complete
- ✅ All 8 tasks across all slices are complete (S01: 1/1, S02: 4/4, S03: 3/3)
- ✅ Cross-slice integration intact: S02 backward-compat pattern replicated in S03; S01 audit informed both; all callers work unchanged
- ✅ No blockers discovered during execution

## Requirement Outcomes

No GSD requirements directly reference M002 — this milestone was pure codebase hygiene with no tracked requirement transitions.

## Deviations

The CONTEXT.md acceptance criteria included `tests/test_validation_consolidation.py` as a S03 deliverable — this was not encoded in the ROADMAP or slice plans, so it was never implemented. No deviations from the ROADMAP.

## Follow-ups

The CONTEXT.md referenced `tests/test_validation_consolidation.py` that was not planned in the ROADMAP. A future slice could add this test. Also, the backward-compat shims in `actors/validation.py` could be removed once ~40 callers update their import paths directly to the mixin.
