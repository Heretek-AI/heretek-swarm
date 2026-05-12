---
estimated_steps: 1
estimated_files: 2
skills_used: []
---

# T03: Update README.md directory tree and CLAUDE.md; run full slice verification

README.md has two stale directory tree entries: `heretek-swarm/` (repo root, line ~111) should become `backend/` and `heretek-swarm/` (Python package, line ~121) should become `backend/`. CLAUDE.md has two stale `src/` references (lines 12 and 15) describing the old `src/` and `tests/` dual structure — these should be updated to reference `backend/heretek_swarm/` instead of `src/`. After all edits, run the full slice-level verification suite.

## Inputs

- `docs/AGENTS.md`
- `docs/API_ENDPOINTS.md`
- `docs/AGENT_REFERENCE.md`
- `docs/AGENT_ARCHITECTURE.md`
- `docs/CODEBASE_AUDIT.md`
- `docs/API_REFERENCE.md`
- `docs/CORE_ACTORS.md`
- `docs/INDEX.md`
- `docs/MAIN_PROMPT.md`
- `docs/PROMETHEUS_METRICS.md`
- `docs/PROTOCOL_SPEC.md`
- `docs/architecture/ARCHITECTURE_REALITY.md`
- `docs/architecture/actors-system.md`
- `docs/architecture/memory-system.md`
- `docs/architecture/consensus-mechanism.md`
- `docs/architecture/emergent-intelligence.md`
- `docs/architecture/collective-learning.md`
- `docs/architecture/orchestration-system.md`
- `docs/architecture/plugins.md`
- `docs/architecture/EXTERNAL_PATTERNS_ANALYSIS.md`

## Expected Output

- `README.md`
- `CLAUDE.md`

## Verification

1. grep -r 'heretek-swarm/' docs/ returns no stale directory path refs 2. ! grep -rn 'src/heretek_swarm' docs/ --include='*.md' 3. ! grep -q 'src/' CLAUDE.md 4. grep -q '^backend/' README.md
