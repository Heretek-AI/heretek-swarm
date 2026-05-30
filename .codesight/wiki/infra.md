# Infra

> **Navigation aid.** Route list and file locations extracted via AST. Read the source files listed below before implementing or modifying this subsystem.

The Infra subsystem handles **4 routes** and touches: auth, cache, db, ai.

## Routes

- `GET` `/` → in: st [auth]
  `backend\heretek_swarm\api\agents\supervisor.py`
- `GET` `/status` [auth, cache]
  `backend\heretek_swarm\api\autonomous.py`
- `GET` `/health` [auth, db, cache, ai]
  `backend\heretek_swarm\api\configuration.py`
- `GET` `/metrics/{metric_id}/timeseries` params(metric_id) → in: dic [auth]
  `backend\heretek_swarm\api\emergent_intelligence.py`

## Source Files

Read these before implementing or modifying this subsystem:
- `backend\heretek_swarm\api\agents\supervisor.py`
- `backend\heretek_swarm\api\autonomous.py`
- `backend\heretek_swarm\api\configuration.py`
- `backend\heretek_swarm\api\emergent_intelligence.py`

---
_Back to [overview.md](./overview.md)_