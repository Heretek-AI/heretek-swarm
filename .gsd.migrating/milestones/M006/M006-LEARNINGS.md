---
phase: closeout
phase_name: Milestone Completion
project: heretek-swarm
generated: 2026-05-12T03:30:00.000Z
counts:
  decisions: 3
  lessons: 3
  patterns: 2
  surprises: 2
missing_artifacts: []
---

### Decisions

- Chose `backend/` as target directory name over `python/` or `server/` because it is the conventional pairing with `swarm-dashboard/` (frontend), making the repo's two-tier structure self-documenting.
  Source: M006-CONTEXT.md/Architectural Decisions

- Chose to keep `tests/` and `src/` at repository root level (not consolidate into `backend/`) after the audit confirmed that all Python imports are package-based (`heretek_swarm.*`) and do not reference the filesystem directory name `heretek-swarm/`. Consolidation would have increased risk with no benefit.
  Source: M006-PLAN.md/§2.3 Root-Level Files

- Chose to simplify the migration to a single `git mv heretek-swarm/ backend/` + 22 line-level config edits (zero Python code changes) after discovering that Python resolves modules by package name, not directory path. This eliminated the need for import rewrites across 429 Python files.
  Source: M006-PLAN.md/§3 Import Rewrite Catalog

### Lessons

- Python resolves modules by package name (`heretek_swarm`), not by filesystem directory name (`heretek-swarm`). This means directory renames don't require import rewrites as long as `pyproject.toml` `where`/`source` directives are updated. The entire 429-file Python codebase needs zero changes.
  Source: S01-SUMMARY.md/What Happened (T02, T04)

- The dash-vs-underscore naming (`heretek-swarm/` directory vs `heretek_swarm` package) caused persistent cognitive overhead for contributors — the rename to `backend/` eliminates this ambiguity entirely without touching a single `.py` file.
  Source: M006-CONTEXT.md/Why This Milestone

- swarm-dashboard/ has zero filesystem-level dependencies on the backend directory. The frontend and backend are fully decoupled at the filesystem level, meaning the directory rename is transparent to the frontend build/test/deploy pipelines.
  Source: S01-SUMMARY.md/Key decisions

### Patterns

- Artifact-driven planning slices: produce machine-readable documents (YAML-in-Markdown tables with exact path/type/category fields) so that downstream automation — and M007 execution tasks — can consume them programmatically without re-auditing the repository.
  Source: S01-SUMMARY.md/Patterns established

- Cross-document consistency verification: every downstream synthesis document (M006-PLAN.md) must cross-reference its source analyses (FILE_INVENTORY.md, IMPORT_MAP.md, CI_IMPACT.md) at the field level. Numeric counts (856 files, 429 Python files, 22 change sites) must match across all four documents.
  Source: M006-VALIDATION.md/Cross-Slice Integration

### Surprises

- The migration is dramatically simpler than anticipated: one `git mv` + 22 line-level edits across 8 config files with zero Python code changes. Initial assumptions in M006-CONTEXT.md contemplated consolidating `tests/`, `src/`, and `agent_workspace/`, but the audit proved none of that is necessary.
  Source: M006-PLAN.md/Executive Summary

- swarm-dashboard/ was confirmed to have zero backend filesystem dependencies — completely decoupled from the Python backend at every level (import, config, build, test, deploy). This was assumed but not proven before T03's grep audit.
  Source: S01-SUMMARY.md/Key decisions
