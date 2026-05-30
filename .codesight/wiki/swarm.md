# Swarm

> **Navigation aid.** Route list and file locations extracted via AST. Read the source files listed below before implementing or modifying this subsystem.

The Swarm subsystem handles **2 routes** and touches: auth.

## Routes

- `GET` `/api/observability/swarm` [auth]
  `backend\heretek_swarm\api\observability\swarm.py`
- `GET` `/api/observability/agents` [auth]
  `backend\heretek_swarm\api\observability\swarm.py`

## Related Models

- **swarm_memories** (4 fields) → [database.md](./database.md)

## Source Files

Read these before implementing or modifying this subsystem:
- `backend\heretek_swarm\api\observability\swarm.py`

---
_Back to [overview.md](./overview.md)_