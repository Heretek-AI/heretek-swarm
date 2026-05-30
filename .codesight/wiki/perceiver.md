# Perceiver

> **Navigation aid.** Route list and file locations extracted via AST. Read the source files listed below before implementing or modifying this subsystem.

The Perceiver subsystem handles **1 routes** and touches: auth, queue.

## Routes

- `POST` `/analyze` → in: st, out: PerceiverResponse [auth, queue, upload]
  `backend\heretek_swarm\api\perceiver.py`

## Source Files

Read these before implementing or modifying this subsystem:
- `backend\heretek_swarm\api\perceiver.py`

---
_Back to [overview.md](./overview.md)_