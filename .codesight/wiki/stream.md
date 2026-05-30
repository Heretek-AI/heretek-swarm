# Stream

> **Navigation aid.** Route list and file locations extracted via AST. Read the source files listed below before implementing or modifying this subsystem.

The Stream subsystem handles **3 routes** and touches: auth.

## Routes

- `GET` `/api/observability/metrics/stream` [auth]
  `backend\heretek_swarm\api\observability\stream.py`
- `GET` `/api/observability/metrics/prometheus` [auth]
  `backend\heretek_swarm\api\observability\stream.py`
- `GET` `/api/observability/metrics/legacy` [auth]
  `backend\heretek_swarm\api\observability\stream.py`

## Source Files

Read these before implementing or modifying this subsystem:
- `backend\heretek_swarm\api\observability\stream.py`

---
_Back to [overview.md](./overview.md)_