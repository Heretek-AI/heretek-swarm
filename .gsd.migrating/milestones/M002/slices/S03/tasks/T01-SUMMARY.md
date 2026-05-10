---
id: T01
parent: S03
milestone: M002
key_files:
  - heretek-swarm/heretek_swarm/actors/mixins/validation.py
  - heretek-swarm/heretek_swarm/actors/validation.py
key_decisions:
  - ValidationMixin is now the single source of truth for IMMUTABLE_RULES and BASELINE_CONFIG; actors/validation.py constants are backward-compat shims
duration: 
verification_result: passed
completed_at: 2026-05-07T15:21:01.330Z
blocker_discovered: false
---

# T01: Moved IMMUTABLE_RULES, BASELINE_CONFIG and accessor functions into ValidationMixin as class-level attributes/classmethods with backward-compat shims in actors/validation.py

**Moved IMMUTABLE_RULES, BASELINE_CONFIG and accessor functions into ValidationMixin as class-level attributes/classmethods with backward-compat shims in actors/validation.py**

## What Happened

Consolidated the behavioral baseline constants that were duplicated as module-level globals in actors/validation.py into ValidationMixin (actors/mixins/validation.py) as class-level attributes. Added `IMMUTABLE_RULES` (8 security patterns), `BASELINE_CONFIG` (9 config keys), `get_immutable_rules()` classmethod, and `get_baseline_config()` classmethod to the mixin. Updated actors/validation.py to import from the mixin: replaced the literal constant definitions with `ValidationMixin.IMMUTABLE_RULES` and `ValidationMixin.BASELINE_CONFIG`, replaced the standalone functions with delegation to the mixin classmethods, and added a deprecation docstring at the module top. No runtime behavior changes — this is pure refactoring.

## Verification

Verified via two Python one-liners: (1) from mixin: ValidationMixin.get_immutable_rules() returns 8 rules, ValidationMixin.get_baseline_config() returns 9 keys; (2) backward-compat: all four import paths (IMMUTABLE_RULES, BASELINE_CONFIG, get_immutable_rules(), get_baseline_config()) work identically from actors/validation.

## Verification Evidence

| # | Command | Exit Code | Verdict | Duration |
|---|---------|-----------|---------|----------|
| 1 | `python -c 'from heretek_swarm.actors.mixins.validation import ValidationMixin; rules = ValidationMixin.get_immutable_rules(); assert len(rules) == 8; print(f"OK: {len(rules)} rules")'` | 0 | ✅ pass | 1200ms |
| 2 | `python -c 'from heretek_swarm.actors.validation import get_immutable_rules; rules = get_immutable_rules(); assert len(rules) == 8; print(f"OK: {len(rules)} rules backward-compat")'` | 0 | ✅ pass | 1100ms |
| 3 | `python -c 'from heretek_swarm.actors.validation import IMMUTABLE_RULES, BASELINE_CONFIG; assert len(IMMUTABLE_RULES) == 8; assert len(BASELINE_CONFIG) == 9; print("OK: constants backward-compat")'` | 0 | ✅ pass | 1000ms |

## Deviations

None.

## Known Issues

None.

## Files Created/Modified

- `heretek-swarm/heretek_swarm/actors/mixins/validation.py`
- `heretek-swarm/heretek_swarm/actors/validation.py`
