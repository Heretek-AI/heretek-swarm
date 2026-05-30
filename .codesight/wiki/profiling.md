# Profiling

> **Navigation aid.** Route list and file locations extracted via AST. Read the source files listed below before implementing or modifying this subsystem.

The Profiling subsystem handles **8 routes** and touches: auth.

## Routes

- `GET` `/{instance_id}/profiling/metrics` params(instance_id) [auth]
  `backend\heretek_swarm\api\agents\profiling.py`
- `GET` `/{instance_id}/profiling/profile` params(instance_id) [auth]
  `backend\heretek_swarm\api\agents\profiling.py`
- `GET` `/{instance_id}/profiling/anomalies` params(instance_id) [auth]
  `backend\heretek_swarm\api\agents\profiling.py`
- `GET` `/profiling/alerts` [auth]
  `backend\heretek_swarm\api\agents\profiling.py`
- `POST` `/profiling/alerts/{index}/acknowledge` params(index) [auth]
  `backend\heretek_swarm\api\agents\profiling.py`
- `GET` `/profiling/stats` [auth]
  `backend\heretek_swarm\api\agents\profiling.py`
- `GET` `/profiling/prometheus` [auth]
  `backend\heretek_swarm\api\agents\profiling.py`
- `POST` `/{instance_id}/profiling/record` params(instance_id) [auth]
  `backend\heretek_swarm\api\agents\profiling.py`

## Source Files

Read these before implementing or modifying this subsystem:
- `backend\heretek_swarm\api\agents\profiling.py`

---
_Back to [overview.md](./overview.md)_