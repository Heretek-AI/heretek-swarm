# M008: Post-Restructure Cleanup & Hardening

**Vision:** Complete the repository restructure by purging tracked garbage files, resolving stale root files with pre-restructure path references, and updating all documentation and code references to match the new backend/ directory layout — ensuring a clean, consistent codebase for future development work.

## Success Criteria

- Repository root has zero tracked garbage files (=*.0, 0)
- Stale root files (triage_classifier.py, audit/cli.py) are resolved — moved or deleted after verification
- All documentation references to heretek-swarm/ directory path are updated to backend/
- CLAUDE.md no longer references src/ directory
- All code comments/docstrings with stale src/ or heretek-swarm/ path refs are updated
- ruff check passes on backend/heretek_swarm/
- pytest unit tests pass
- CI workflows remain correct
- No functional code changes — only cleanup

## Slices

- [x] **S01: S01** `risk:Low — pure file deletion, zero code impact` `depends:[]`
  > After this: git status shows no tracked =*.0 or 0 garbage files at repo root; ls returns 'No such file' for the glob pattern

- [x] **S02: S02** `risk:Medium — risk of losing unique logic from triage_classifier.py and audit/cli.py if they contain logic not duplicated in backend equivalents` `depends:[]`
  > After this: Both stale root files (triage_classifier.py, audit/cli.py) are either git mv'd to backend/ canonical locations or deleted after confirming their logic is superseded by backend/ equivalents

- [x] **S03: S03** `risk:Low — mechanical find-and-replace across 20+ doc files; risk of missing some references` `depends:[]`
  > After this: grep -r 'heretek-swarm/' docs/ returns only CLI command/PyPI references, not stale directory references; README.md shows backend/; CLAUDE.md no longer references src/

- [x] **S04: S04** `risk:Low — mechanical find-and-replace in comments/docstrings` `depends:[]`
  > After this: grep -rn 'src/' backend/heretek_swarm/ --include='*.py' returns zero stale path references

- [ ] **S05: Final validation pass** `risk:Low — full verification pass` `depends:[S04]`
  > After this: pytest passes, ruff check clean, grep for stale refs zero, CI workflow files verified correct

## Boundary Map

Not provided.
