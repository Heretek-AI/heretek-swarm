# Tier 1 Core Triad

Multi-turn deliberation MVP. The Steward orchestrates Alpha (analysis),
Beta (validation), and Charlie (challenge) through a LangGraph Tribunal.
Live reasoning streams to a React dashboard.

## Quick start

    cd backend/tier1
    docker compose -f docker/docker-compose.yml up -d
    pip install -e ".[dev]"
    export TIER1_MINIMAX_API_KEY=...
    python -m tier1 serve

    # In another terminal:
    cd swarm-dashboard
    npm install
    npm run dev

Open http://localhost:5173 (Vite dev) or http://localhost:8000/dashboard (production-style build).

## Architecture

See `docs/superpowers/specs/2026-06-24-tier-1-core-triad-rebuild-design.md`.

## Tests

    cd backend/tier1
    pytest tests/ -v

## Notes

- This module is greenfield — separate from the legacy 180k LoC `heretek_swarm/` package.
- We preserve the doctrinal infrastructure (NATS/Postgres/Redis/Qdrant/cognee/mem0).
- We do NOT carry over the other 19 agents, consciousness layers, or wizard code.
