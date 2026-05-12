---
estimated_steps: 1
estimated_files: 20
skills_used: []
---

# T02: Update remaining doc files — replace stale src/heretek_swarm directory refs with backend/heretek_swarm/

20 doc files across docs/ and docs/architecture/ contain `src/heretek_swarm` path references from the pre-restructure `src/` directory layout. These are markdown inline-code paths, file links, and markdown link destinations referencing the old `src/heretek_swarm/...` structure. Also includes one GitHub blob URL in docs/architecture/EXTERNAL_PATTERNS_ANALYSIS.md (line 700) whose blob path needs updating to `backend/heretek_swarm` to match the restructured main branch. Use `find docs/ -name '*.md' -exec sed -i 's|src/heretek_swarm|backend/heretek_swarm|g' {} +` — this avoids per-file context overhead.

## Inputs

- `docs/ARCHITECTURE.md`

## Expected Output

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

## Verification

! grep -rn 'src/heretek_swarm' docs/ --include='*.md' returns zero matches
