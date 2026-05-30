# External_calls

> **Navigation aid.** Route list and file locations extracted via AST. Read the source files listed below before implementing or modifying this subsystem.

The External_calls subsystem handles **3 routes** and touches: auth, db.

## Routes

- `GET` `/api/observability/external-calls` → out: ExternalCallLogListResponse [auth, db]
  `backend\heretek_swarm\api\observability\external_calls.py`
- `POST` `/api/observability/external-calls` → out: ExternalCallLogListResponse [auth, db]
  `backend\heretek_swarm\api\observability\external_calls.py`
- `GET` `/api/observability/external-calls/{call_id}` params(call_id) → out: ExternalCallLogListResponse [auth, db]
  `backend\heretek_swarm\api\observability\external_calls.py`

## Related Models

- **external_call_logs** (5 fields) → [database.md](./database.md)

## Source Files

Read these before implementing or modifying this subsystem:
- `backend\heretek_swarm\api\observability\external_calls.py`

---
_Back to [overview.md](./overview.md)_