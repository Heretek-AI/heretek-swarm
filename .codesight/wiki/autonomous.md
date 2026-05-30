# Autonomous

> **Navigation aid.** Route list and file locations extracted via AST. Read the source files listed below before implementing or modifying this subsystem.

The Autonomous subsystem handles **2 routes** and touches: auth, cache.

## Routes

- `POST` `/agents` → in: AutonomousStatusUpdate [auth, cache]
  `backend\heretek_swarm\api\autonomous.py`
- `GET` `/agents` [auth, cache]
  `backend\heretek_swarm\api\autonomous.py`

## Source Files

Read these before implementing or modifying this subsystem:
- `backend\heretek_swarm\api\autonomous.py`

---
_Back to [overview.md](./overview.md)_