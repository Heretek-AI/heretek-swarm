# Routing_control

> **Navigation aid.** Route list and file locations extracted via AST. Read the source files listed below before implementing or modifying this subsystem.

The Routing_control subsystem handles **4 routes** and touches: auth.

## Routes

- `POST` `/routing/rules/{rule_id}/enable` params(rule_id) [auth]
  `backend\heretek_swarm\api\agents\routing_control.py`
- `POST` `/routing/rules/{rule_id}/disable` params(rule_id) [auth]
  `backend\heretek_swarm\api\agents\routing_control.py`
- `GET` `/routing/stats` → in: Annotated [auth]
  `backend\heretek_swarm\api\agents\routing_control.py`
- `POST` `/routing/evaluate` [auth]
  `backend\heretek_swarm\api\agents\routing_control.py`

## Source Files

Read these before implementing or modifying this subsystem:
- `backend\heretek_swarm\api\agents\routing_control.py`

---
_Back to [overview.md](./overview.md)_