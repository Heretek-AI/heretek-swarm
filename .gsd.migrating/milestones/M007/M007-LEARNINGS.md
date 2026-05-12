---
phase: extraction
phase_name: milestone-completion
project: heretek-swarm
generated: 2026-05-10T21:10:00.000Z
counts:
  decisions: 2
  lessons: 3
  patterns: 2
  surprises: 3
missing_artifacts:
  - S03/S03-ASSESSMENT.md
  - .gsd/DECISIONS.md (no decisions registry exists)
---

# M007 Learnings — Execute repository restructure

### Decisions

- **D001:** Executed directory rename via `git mv` with zero code changes rather than multi-phase consolidation. All 463 files moved as R100 renames preserving full history. Python imports are package-name-based and required zero changes.
  Source: M007-ROADMAP.md/Success Criteria, S01-SUMMARY.md/What Happened

- **D002:** GitHub URLs in pyproject.toml and user-home config paths (`~/.heretek-swarm/`) were intentionally excluded from path rewrites — they are remote repository references and application-level runtime paths respectively, not source-tree filesystem paths.
  Source: S02-SUMMARY.md/Key Decisions

### Lessons

- **L001:** Unmerged `UU` files in the git index silently block `git mv` — the command appears to hang or fail without a clear error. Resolution: run `git status` to detect unmerged state, then `git add <path>` to clear it before retrying the move.
  Source: S01-SUMMARY.md/Deviations

- **L002:** The `edit()` tool on Windows may not persist file changes to disk. When edits silently fail, fall back to full-file `write()` to finalize changes. This was the only reliable path for the Dockerfile and CI workflow edits in S02.
  Source: S02-SUMMARY.md/Patterns Established, S02-SUMMARY.md/What Happened

- **L003:** The gsd_exec sandbox environment lacks pip, pytest, ruff, and Docker — runtime verification suites that depend on these tools cannot execute during milestone closeout. Filesystem-level verification (directory existence, file counts, git grep audits) must substitute. Full runtime confidence requires the actual dev environment.
  Source: S03-SUMMARY.md/Deviations, S03-UAT.md/Not Proven By This UAT

### Patterns

- **P001:** When `edit()` tool calls don't persist to disk on Windows, fall back to full file `write()` to finalize changes. This is a tooling workaround for a known platform behavior.
  Source: S02-SUMMARY.md/Patterns Established

- **P002:** Directory renames via `git mv` are transparent to Python imports — Python resolves modules by package name (`heretek_swarm`), not filesystem directory name. Only pyproject.toml `where`/`source`/`src` directives and CI tool paths need updating after the rename. Zero import changes needed across 429+ Python files.
  Source: M007-CONTEXT.md/Architectural Decisions, S02-SUMMARY.md/What Happened

### Surprises

- **S001:** Six unmerged `UU` files in `.gsd.migrating/` silently blocked `git mv` — no clear error message, just a stalled index operation. Detected via `git status` showing `UU` markers.
  Source: S01-SUMMARY.md/Deviations

- **S002:** Twelve tracked `=X.Y.Z` garbage files at the repo root were explicitly listed in M007-CONTEXT.md scope for removal but were never removed across any of the three completed slices. These are tracked git files requiring `git rm`.
  Source: M007-VALIDATION.md/Acceptance Criteria, M007-CONTEXT.md/scope

- **S003:** S03 was exclusively a deletion and consolidation slice — zero Python code changes, no new files created. All tasks were `git rm` or `git mv` operations. This minimized risk compared to the import-rewrite work expected in pre-planning assumptions.
  Source: S03-SUMMARY.md/What Happened, S03-SUMMARY.md/Files Created/Modified
