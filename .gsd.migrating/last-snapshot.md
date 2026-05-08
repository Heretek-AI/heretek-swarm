# GSD context snapshot (2026-05-07T19:08:05.038Z)

## Top project memories
- [MEM008] (architecture) ValidationMixin is now the single source of truth for IMMUTABLE_RULES (8 security patterns) and BASELINE_CONFIG. The original module-level globals in actors/validation.py are backward-compat shims delegating to the mixin. New code should import from heretek_swarm.actors.mixins.validation.ValidationMixin directly.
- [MEM009] (architecture) Consolidated IMMUTABLE_RULES and BASELINE_CONFIG from actors/validation.py module-level globals into ValidationMixin as class-level attributes. Module-level accessor functions became backward-compat shims delegating to the mixin. This makes ValidationMixin the single source of truth for behavioral baseline constants.
- [MEM002] (pattern) Shim files (flat .py re-exporting from subpackages) are safe to delete once a canonical __init__.py re-export surface exists. Always verify with a codebase grep scan before assuming imports reference deleted files — the only safe assumption is that something, somewhere might import by the flat name.
- [MEM003] (gotcha) The plan's file-count estimate was 20 remaining files but the actual count was 21 — a +1 discrepancy. explorer.py was counted as a shim in the plan but is actually a standalone 1318-line implementation that must be preserved.
- [MEM004] (pattern) Audit-then-Execute pipeline: Slice 1 produces machine-parseable audit (JSON in ACTOR_AUDIT.md); Slice 2 consumes it programmatically to determine deletions. Eliminates redundant re-scanning and ensures audit and execution are tightly coupled.
- [MEM007] (convention) Preserve standalone actors like explorer.py even if they share names with subpackages. Only delete true duplicate shims (thin re-exports from subpackages). Standalone implementations retain their names regardless of subpackage naming overlap.

## Recent gsd_exec runs
- [739e0464-8c4a-4752-8142-01f15d097245] bash exit:0 — Check actual repo structure
- [33d2fd11-d3a4-487a-be9a-a1c8ec2c1985] bash exit:0 — Ve
…[truncated]
