# Traces

> **Navigation aid.** Route list and file locations extracted via AST. Read the source files listed below before implementing or modifying this subsystem.

The Traces subsystem handles **4 routes** and touches: auth, db.

## Routes

- `GET` `/api/observability/traces` [auth, db]
  `backend\heretek_swarm\api\observability\traces.py`
- `GET` `/api/observability/traces/{trace_id}` params(trace_id) [auth, db]
  `backend\heretek_swarm\api\observability\traces.py`
- `POST` `/api/observability/traces` [auth, db]
  `backend\heretek_swarm\api\observability\traces.py`
- `DELETE` `/api/observability/traces/{agent_id}` params(agent_id) [auth, db]
  `backend\heretek_swarm\api\observability\traces.py`

## Source Files

Read these before implementing or modifying this subsystem:
- `backend\heretek_swarm\api\observability\traces.py`

---
_Back to [overview.md](./overview.md)_