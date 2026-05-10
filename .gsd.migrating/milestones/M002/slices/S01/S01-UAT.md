# S01: Audit scattered validation and model overlap — UAT

**Milestone:** M002
**Written:** 2026-05-07T13:01:46.279Z

# UAT: S01 — Audit Scattered Validation and Model Overlap

## UAT Type
Contract verification — this slice proves the audit document exists and contains structured content mapping all validation functions and Pydantic models.

## Not Proven By This UAT
- Actual code refactoring (deferred to S02/S03)
- Runtime validation behavior
- Cross-file import integrity

## Preconditions
None — this is a documentation-only slice.

## Test Cases

### TC01: AUDIT.md file exists
- **Steps:** `wc -l heretek-swarm/heretek_swarm/slices/M002/S01/S01-AUDIT.md`
- **Expected:** ≥30 lines, structured tables present
- **Result:** 157 lines ✅

### TC02: AUDIT.md covers validation functions
- **Steps:** Inspect AUDIT.md for validation function table entries
- **Expected:** Entries for validate_message, ValidationMixin methods, core.py integration points
- **Result:** 15 ValidationMixin methods + 4 integration points documented ✅

### TC03: AUDIT.md covers Pydantic models
- **Steps:** Inspect AUDIT.md for Pydantic model table entries
- **Expected:** Entries for models in actors/validation.py and schemas/external_call_log.py
- **Result:** 14 actor models + 5 external call log schemas documented ✅

### TC04: AUDIT.md provides canonical home recommendations
- **Steps:** Inspect AUDIT.md for "Canonical Home" or equivalent column
- **Expected:** Each entry maps to a recommended file location
- **Result:** Consumer dependency map and canonical home column present ✅

## Verification Commands
```bash
test -f "heretek-swarm/heretek_swarm/slices/M002/S01/S01-AUDIT.md" && wc -l "heretek-swarm/heretek_swarm/slices/M002/S01/S01-AUDIT.md" | awk '{exit ($1 < 30) ? 1 : 0}'
```
**Result:** exit 0 ✅
