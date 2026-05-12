# S03: Update documentation path references

**Goal:** Update all documentation path references to match the new backend/ directory layout — replace stale heretek-swarm/heretek_swarm/ and src/heretek_swarm/ path refs in all .md files with backend/heretek_swarm/, update README.md directory tree to show backend/, and remove src/ references from CLAUDE.md
**Demo:** grep -r 'heretek-swarm/' docs/ returns only CLI command/PyPI references, not stale directory references; README.md shows backend/; CLAUDE.md no longer references src/

## Must-Haves

- 1. `grep -r 'heretek-swarm/' docs/` returns only CLI command/PyPI references (e.g. `heretek-swarm init`, `~/.heretek-swarm/`, `github.com/...heretek-swarm`, `/heretek-swarm/dev/`, `/var/log/heretek-swarm/`), zero stale directory references like `heretek-swarm/heretek_swarm/…` 2. `grep -rn 'src/heretek_swarm' docs/ --include='*.md'` returns zero matches 3. README.md directory tree shows `backend/` at the repository root line instead of `heretek-swarm/` 4. `grep -q 'src/' CLAUDE.md` returns exit code 1 (no src/ references remain) 5. No functional code changes — only documentation path updates

## Proof Level

- This slice proves: Static — file content verification via grep. No runtime, no UAT needed.

## Integration Closure

This slice closes the doc-path gap left by M007's directory rename. After this, all documentation files consistently reference `backend/` paths. S04 (code string-literals) can proceed cleanly without mixing doc and code changes.

## Verification

- None — documentation only, no runtime impact.

## Tasks

- [x] **T01: Update docs/ARCHITECTURE.md — replace stale heretek-swarm/heretek_swarm/ directory refs with backend/heretek_swarm/** `est:30m`
  ARCHITECTURE.md (914 lines) has 54 stale `heretek-swarm/heretek_swarm/` path references — the old directory name before M007's rename to `backend/`. All are markdown link targets (inline code backtick paths or markdown link destinations). None are GitHub URLs, CLI commands, home-dir paths (~), or SSM parameter names — all are legitimate filesystem path references. Also fix the standalone `heretek-swarm/` directory tree entry on line ~59. Use `sed -i` for efficiency. Verify with grep that zero stale refs remain and that the correct count of replacements were applied.
  - Files: `docs/ARCHITECTURE.md`
  - Verify: grep -c 'backend/heretek_swarm' docs/ARCHITECTURE.md (expect >= 54) && ! grep -q 'heretek-swarm/heretek_swarm' docs/ARCHITECTURE.md

- [x] **T02: Update remaining doc files — replace stale src/heretek_swarm directory refs with backend/heretek_swarm/** `est:30m`
  20 doc files across docs/ and docs/architecture/ contain `src/heretek_swarm` path references from the pre-restructure `src/` directory layout. These are markdown inline-code paths, file links, and markdown link destinations referencing the old `src/heretek_swarm/...` structure. Also includes one GitHub blob URL in docs/architecture/EXTERNAL_PATTERNS_ANALYSIS.md (line 700) whose blob path needs updating to `backend/heretek_swarm` to match the restructured main branch. Use `find docs/ -name '*.md' -exec sed -i 's|src/heretek_swarm|backend/heretek_swarm|g' {} +` — this avoids per-file context overhead.
  - Files: `docs/AGENTS.md`, `docs/API_ENDPOINTS.md`, `docs/AGENT_REFERENCE.md`, `docs/AGENT_ARCHITECTURE.md`, `docs/CODEBASE_AUDIT.md`, `docs/API_REFERENCE.md`, `docs/CORE_ACTORS.md`, `docs/INDEX.md`, `docs/MAIN_PROMPT.md`, `docs/PROMETHEUS_METRICS.md`, `docs/PROTOCOL_SPEC.md`, `docs/architecture/ARCHITECTURE_REALITY.md`, `docs/architecture/actors-system.md`, `docs/architecture/memory-system.md`, `docs/architecture/consensus-mechanism.md`, `docs/architecture/emergent-intelligence.md`, `docs/architecture/collective-learning.md`, `docs/architecture/orchestration-system.md`, `docs/architecture/plugins.md`, `docs/architecture/EXTERNAL_PATTERNS_ANALYSIS.md`
  - Verify: ! grep -rn 'src/heretek_swarm' docs/ --include='*.md' returns zero matches

- [x] **T03: Update README.md directory tree and CLAUDE.md; run full slice verification** `est:30m`
  README.md has two stale directory tree entries: `heretek-swarm/` (repo root, line ~111) should become `backend/` and `heretek-swarm/` (Python package, line ~121) should become `backend/`. CLAUDE.md has two stale `src/` references (lines 12 and 15) describing the old `src/` and `tests/` dual structure — these should be updated to reference `backend/heretek_swarm/` instead of `src/`. After all edits, run the full slice-level verification suite.
  - Files: `README.md`, `CLAUDE.md`
  - Verify: 1. grep -r 'heretek-swarm/' docs/ returns no stale directory path refs 2. ! grep -rn 'src/heretek_swarm' docs/ --include='*.md' 3. ! grep -q 'src/' CLAUDE.md 4. grep -q '^backend/' README.md

## Files Likely Touched

- docs/ARCHITECTURE.md
- docs/AGENTS.md
- docs/API_ENDPOINTS.md
- docs/AGENT_REFERENCE.md
- docs/AGENT_ARCHITECTURE.md
- docs/CODEBASE_AUDIT.md
- docs/API_REFERENCE.md
- docs/CORE_ACTORS.md
- docs/INDEX.md
- docs/MAIN_PROMPT.md
- docs/PROMETHEUS_METRICS.md
- docs/PROTOCOL_SPEC.md
- docs/architecture/ARCHITECTURE_REALITY.md
- docs/architecture/actors-system.md
- docs/architecture/memory-system.md
- docs/architecture/consensus-mechanism.md
- docs/architecture/emergent-intelligence.md
- docs/architecture/collective-learning.md
- docs/architecture/orchestration-system.md
- docs/architecture/plugins.md
- docs/architecture/EXTERNAL_PATTERNS_ANALYSIS.md
- README.md
- CLAUDE.md
