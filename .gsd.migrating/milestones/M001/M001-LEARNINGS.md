---
phase: "M001"
phase_name: "Collapse dual actors/ directory"
project: "heretek-swarm"
generated: "2025-05-07T13:00:00Z"
counts:
  decisions: 4
  lessons: 4
  patterns: 2
  surprises: 0
missing_artifacts: []
---

### Decisions

- **Preserve standalone actors even if name matches a subpackage**  
  explorer.py shares a name with the explorer/ subpackage but is a 1318-line standalone implementation. Only delete true shims (files that re-export from subpackages), never standalone implementations.  
  Source: S02-SUMMARY.md/Key Decisions

- **No import updates needed for deleted shims**  
  Scanning the entire codebase found only stubs.py referenced (by base/state_management.py). stubs.py was not among the 10 deleted shims — no broken imports existed.  
  Source: S02-SUMMARY.md/Key Decisions

- **__init__.py as single canonical re-export surface**  
  The pre-existing heretek_swarm/actors/__init__.py already correctly re-exports all public agent classes from subpackages only. No file modifications were needed once shims were eliminated.  
  Source: S03-SUMMARY.md/Patterns Established

- **Shim files can be deleted once canonical re-export surface exists**  
  Flat .py files that re-export from subpackages are redundant once `__init__.py` provides the public API. Delete the shims, not the subpackages.  
  Source: S02-SUMMARY.md/Patterns Established

### Lessons

- **Import scanning is fast and conclusive**  
  A single grep scan of the codebase for import statements referencing deleted files gives a definitive answer — no broken imports were found in this case. This approach should be the standard post-deletion verification step.  
  Source: S02-SUMMARY.md/What Happened

- **Machine-parseable audit output enables programmatic automation**  
  ACTOR_AUDIT.md's JSON block let S02 determine which files to delete without re-scanning source files. This pattern (audit produces machine-readable artifact consumed by next slice) should be standard practice.  
  Source: S01-SUMMARY.md/What Happened

- **Pre-existing __init__.py was already correct**  
  S03 required no file modifications — the re-export surface was already properly implemented. This means the milestone's value was purely in deleting the shims, not in building new import infrastructure.  
  Source: S03-SUMMARY.md/What Happened

- **Planner file count estimates can be off by 1-2**  
  Plan estimated 20 files remaining after shim deletion (actual: 21). This is a minor discrepancy, not a deviation — all 10 specified shims were correctly removed. Future plans should account for ~5% variance in file count estimates.  
  Source: S02-SUMMARY.md/Deviations

### Patterns

- **Audit-then-Execute pipeline**  
  Slice 1 produces machine-parseable audit (ACTOR_AUDIT.md with JSON); Slice 2 consumes the audit programmatically to determine deletions. Eliminates redundant re-scanning and ensures the audit and execution are tightly coupled.  
  Source: S01-SUMMARY.md/What Happened + S02-SUMMARY.md/What Happened

- **Shim-to-subpackage migration**  
  When a subpackage provides a full implementation, the corresponding flat .py re-export file is a shim. The correct action is to delete the shim once the public __init__.py surface correctly re-exports from subpackages. Never delete subpackages.  
  Source: S02-SUMMARY.md/Patterns Established

### Surprises

*(None — no unexpected outcomes during this milestone.)*