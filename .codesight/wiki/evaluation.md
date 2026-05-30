# Evaluation

> **Navigation aid.** Route list and file locations extracted via AST. Read the source files listed below before implementing or modifying this subsystem.

The Evaluation subsystem handles **7 routes** and touches: auth, db.

## Routes

- `POST` `/test-cases` → in: dict [auth, db]
  `backend\heretek_swarm\api\evaluation.py`
- `POST` `/test-cases/batch` → in: dict [auth, db]
  `backend\heretek_swarm\api\evaluation.py`
- `GET` `/test-cases` → in: Annotated [auth, db]
  `backend\heretek_swarm\api\evaluation.py`
- `POST` `/agents/{agent_id}/evaluate` params(agent_id) → in: dict [auth, db]
  `backend\heretek_swarm\api\evaluation.py`
- `GET` `/agents/{agent_id}/summary` params(agent_id) → in: Annotated [auth, db]
  `backend\heretek_swarm\api\evaluation.py`
- `GET` `/summaries` → in: Annotated [auth, db]
  `backend\heretek_swarm\api\evaluation.py`
- `DELETE` `/test-cases/{test_case_id}` params(test_case_id) [auth, db]
  `backend\heretek_swarm\api\evaluation.py`

## Source Files

Read these before implementing or modifying this subsystem:
- `backend\heretek_swarm\api\evaluation.py`

---
_Back to [overview.md](./overview.md)_