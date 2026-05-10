---
id: S01
parent: M002
milestone: M002
provides:
  - S01-AUDIT.md: structured audit map covering all validation layers and Pydantic models for S02/S03 refactoring guide
requires:
  []
affects:
  []
key_files:
  - (none)
key_decisions:
  - (none)
patterns_established:
  - (none)
observability_surfaces:
  - none
drill_down_paths:
  []
duration: ""
verification_result: passed
completed_at: 2026-05-07T13:01:46.279Z
blocker_discovered: false
---

# S01: Audit scattered validation and model overlap

**Audit document maps all validation functions and Pydantic models to canonical homes**

## What Happened

Scanned actors/validation.py (Pydantic v2 models + validate_message dispatcher), actors/mixins/validation.py (ValidationMixin behavioral/anomaly detection class), actors/base/core.py (wires validate_message into AgentActor._validate_message_content), and schemas/external_call_log.py (ORM/API schemas). All four layers were already at their canonical homes. Produced S01-AUDIT.md as a structured reference table for S02/S03, covering 14 Pydantic models, 15 ValidationMixin methods, 4 base-class integration points, 5 external call log schemas, and a consumer dependency map. The primary finding: file locations are already canonical; the opportunity for S02/S03 is extracting shared validator patterns (len(v) > N checks appear in multiple models) into a base class rather than moving files.

## Verification

S01-AUDIT.md verified to exist with 157 lines covering all validation functions (15 ValidationMixin methods, 4 base-class integration points) and Pydantic models (14 actor models, 5 external call log schemas) with canonical home recommendations for S02/S03. Exit code 0 on verification command.

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

None.

## Follow-ups

None.

## Files Created/Modified

None.
