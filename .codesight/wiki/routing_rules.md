# Routing_rules

> **Navigation aid.** Route list and file locations extracted via AST. Read the source files listed below before implementing or modifying this subsystem.

The Routing_rules subsystem handles **5 routes** and touches: auth, db.

## Routes

- `GET` `/routing/rules` → in: Annotated [auth, db]
  `backend\heretek_swarm\api\agents\routing_rules.py`
- `GET` `/routing/rules/{rule_id}` params(rule_id) → in: Annotated [auth, db]
  `backend\heretek_swarm\api\agents\routing_rules.py`
- `POST` `/routing/rules` → in: RoutingRuleCreate [auth, db]
  `backend\heretek_swarm\api\agents\routing_rules.py`
- `PUT` `/routing/rules/{rule_id}` params(rule_id) [auth, db]
  `backend\heretek_swarm\api\agents\routing_rules.py`
- `DELETE` `/routing/rules/{rule_id}` params(rule_id) [auth, db]
  `backend\heretek_swarm\api\agents\routing_rules.py`

## Source Files

Read these before implementing or modifying this subsystem:
- `backend\heretek_swarm\api\agents\routing_rules.py`

---
_Back to [overview.md](./overview.md)_