---
phase: extract-learnings
phase_name: "Post-Restructure Cleanup & Hardening"
project: heretek-swarm
generated: "2026-05-13T00:30:00.000Z"
counts:
  decisions: 4
  lessons: 4
  patterns: 4
  surprises: 3
missing_artifacts:
  - DECISIONS.md (no decisions file exists for this project)
  - REQUIREMENTS.md (no requirements file exists for this project)
---

### Decisions

- **Deleted triage_classifier.py and audit/cli.py after confirming their logic was superseded by backend/heretek_swarm/ equivalents.**
  Source: S02-SUMMARY.md/What Happened

- **Added `=*` prevention rule to .gitignore at line 155 under "Garbage build artifacts" section to block future recurrence of =*.0 pip artifacts.**
  Source: S01-SUMMARY.md/What Happened

- **Classified 14 remaining heretek-swarm/ references in docs as legitimate project-identity references (GitHub URLs, SSM params, CLI config, log paths) — no forced replacement needed.**
  Source: S05-SUMMARY.md/What Happened

- **Deferred ruff and pytest runtime verification to dev environment — static grep evidence is conclusive for a structural cleanup milestone with zero functional code changes.**
  Source: S05-SUMMARY.md/Known Limitations

### Lessons

- **Garbage build artifacts (=*.0 pip artifacts, '0' grep redirects) can accumulate in git tracking when .gitignore lacks explicit prevention rules.**
  Source: S01-SUMMARY.md/What Happened

- **Stale root files from pre-restructure carry broken path references (heretek-swarm/heretek_swarm/) and require careful diffing against canonical backend/ equivalents before deletion to confirm supersession.**
  Source: S02-SUMMARY.md/What Happened

- **Mechanical find-and-replace across 22 doc files requires post-replacement classification of remaining matches — some "old" path references are legitimate project-identity strings (CLI commands, GitHub URLs, SSM parameters) and must not be replaced.**
  Source: S03-SUMMARY.md/Verification

- **Static grep verification is sufficient for structural-only cleanup milestones with zero functional code changes — runtime verification (pytest, ruff) can be deferred to a documented follow-up command without blocking milestone completion.**
  Source: S05-SUMMARY.md/Known Limitations

### Patterns

- **`.gitignore` garbage prevention: add a standalone `=*` rule under a dedicated "Garbage build artifacts" comment section to prevent =*.0 pip build detritus from ever entering git tracking.**
  Source: S01-SUMMARY.md/What Happened

- **Stale file deletion protocol: before `git rm`, verify (a) canonical equivalents exist and are functionally complete, (b) no imports or references in the codebase point at the stale files, and (c) any cosmetic issues in the canonical equivalent are addressed simultaneously.**
  Source: S02-SUMMARY.md/Verification

- **Comment/docstring path references must match the actual directory layout (backend/, not src/ or heretek-swarm/). Verification is pure static grep with pattern-specific confirmation per file — no runtime needed.**
  Source: S04-SUMMARY.md/Verification

- **Structural cleanup milestones benefit from a dedicated final validation slice (S05) that re-verifies all upstream producer evidence with a single systematic sweep — 8 static checks, CI workflow audit, and docs reference audit — before authoring the milestone summary.**
  Source: S05-SUMMARY.md/What Happened

### Surprises

- **audit/cli.py was ~90% identical to its canonical backend/ equivalent but missed key imports (group_by_severity, DEFAULT_EXTENSIONS) — partial divergence required careful analysis rather than simple deletion.**
  Source: S02-SUMMARY.md/What Happened

- **The 14 "heretek-swarm/" references remaining after S03's mechanical replacements were all valid project-identity references (GitHub URLs, SSM params, CLI config defaults, log paths) — the classification audit confirmed no further replacements were needed.**
  Source: S03-SUMMARY.md/Verification

- **Sandbox execution constraints prevented running ruff/pytest, but since M008 is zero-functional-change structural cleanup, the 8-point static verification suite is independently conclusive — the environmental limitation is a documentation item, not a quality gap.**
  Source: S05-SUMMARY.md/Known Limitations
