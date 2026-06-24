# Tier 1 Core Triad

Greenfield Tier 1 deliberation MVP. See `.superpowers/sdd/task-1-brief.md`.

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
python -m tier1 serve
```

## Endpoints

- `GET /health` — process liveness (Task 1)