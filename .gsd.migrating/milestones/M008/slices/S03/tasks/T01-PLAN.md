---
estimated_steps: 1
estimated_files: 1
skills_used: []
---

# T01: Update docs/ARCHITECTURE.md — replace stale heretek-swarm/heretek_swarm/ directory refs with backend/heretek_swarm/

ARCHITECTURE.md (914 lines) has 54 stale `heretek-swarm/heretek_swarm/` path references — the old directory name before M007's rename to `backend/`. All are markdown link targets (inline code backtick paths or markdown link destinations). None are GitHub URLs, CLI commands, home-dir paths (~), or SSM parameter names — all are legitimate filesystem path references. Also fix the standalone `heretek-swarm/` directory tree entry on line ~59. Use `sed -i` for efficiency. Verify with grep that zero stale refs remain and that the correct count of replacements were applied.

## Inputs

- `docs/ARCHITECTURE.md`

## Expected Output

- `docs/ARCHITECTURE.md`

## Verification

grep -c 'backend/heretek_swarm' docs/ARCHITECTURE.md (expect >= 54) && ! grep -q 'heretek-swarm/heretek_swarm' docs/ARCHITECTURE.md
