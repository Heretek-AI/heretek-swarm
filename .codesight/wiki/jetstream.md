# Jetstream

> **Navigation aid.** Route list and file locations extracted via AST. Read the source files listed below before implementing or modifying this subsystem.

The Jetstream subsystem handles **7 routes** and touches: auth, db, queue.

## Routes

- `GET` `/jetstream/streams` → in: Annotated [auth, db, queue]
  `backend\heretek_swarm\api\agents\jetstream.py`
- `GET` `/jetstream/streams/{stream_name}` params(stream_name) → in: Annotated [auth, db, queue]
  `backend\heretek_swarm\api\agents\jetstream.py`
- `POST` `/jetstream/streams` → in: JetStreamConfigCreate [auth, db, queue]
  `backend\heretek_swarm\api\agents\jetstream.py`
- `DELETE` `/jetstream/streams/{stream_name}` params(stream_name) [auth, db, queue]
  `backend\heretek_swarm\api\agents\jetstream.py`
- `POST` `/jetstream/streams/{stream_name}/replay` params(stream_name) → in: JetStreamConfigCreate [auth, db, queue]
  `backend\heretek_swarm\api\agents\jetstream.py`
- `GET` `/jetstream/stats` → in: Annotated [auth, db, queue]
  `backend\heretek_swarm\api\agents\jetstream.py`
- `POST` `/jetstream/initialize` → in: JetStreamConfigCreate [auth, db, queue]
  `backend\heretek_swarm\api\agents\jetstream.py`

## Source Files

Read these before implementing or modifying this subsystem:
- `backend\heretek_swarm\api\agents\jetstream.py`

---
_Back to [overview.md](./overview.md)_