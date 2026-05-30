# Events

> **Navigation aid.** Route list and file locations extracted via AST. Read the source files listed below before implementing or modifying this subsystem.

The Events subsystem handles **10 routes** and touches: auth, db.

## Routes

- `POST` `/api/observability/events/replay` → in: ReplayJobCreate [auth, db]
  `backend\heretek_swarm\api\observability\events.py`
- `POST` `/api/observability/events/replay/{job_id}/execute` params(job_id) → in: ReplayJobCreate [auth, db]
  `backend\heretek_swarm\api\observability\events.py`
- `POST` `/api/observability/events/replay/{job_id}/pause` params(job_id) → in: ReplayJobCreate [auth, db]
  `backend\heretek_swarm\api\observability\events.py`
- `POST` `/api/observability/events/replay/{job_id}/resume` params(job_id) → in: ReplayJobCreate [auth, db]
  `backend\heretek_swarm\api\observability\events.py`
- `POST` `/api/observability/events/replay/{job_id}/cancel` params(job_id) → in: ReplayJobCreate [auth, db]
  `backend\heretek_swarm\api\observability\events.py`
- `GET` `/api/observability/events/replay` [auth, db]
  `backend\heretek_swarm\api\observability\events.py`
- `GET` `/api/observability/events/replay/{job_id}` params(job_id) [auth, db]
  `backend\heretek_swarm\api\observability\events.py`
- `POST` `/api/observability/events/time-travel` → in: ReplayJobCreate [auth, db]
  `backend\heretek_swarm\api\observability\events.py`
- `POST` `/api/observability/events/time-travel/{request_id}/execute` params(request_id) → in: ReplayJobCreate [auth, db]
  `backend\heretek_swarm\api\observability\events.py`
- `GET` `/api/observability/events/stats` [auth, db]
  `backend\heretek_swarm\api\observability\events.py`

## Source Files

Read these before implementing or modifying this subsystem:
- `backend\heretek_swarm\api\observability\events.py`

---
_Back to [overview.md](./overview.md)_