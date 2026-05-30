# Skills

> **Navigation aid.** Route list and file locations extracted via AST. Read the source files listed below before implementing or modifying this subsystem.

The Skills subsystem handles **8 routes** and touches: auth, db.

## Routes

- `GET` `/agents/by-skill/{skill_name}` params(skill_name) → in: SkillCategory [auth, db]
  `backend\heretek_swarm\api\skills.py`
- `GET` `/agents/by-category/{category}` params(category) → in: SkillCategory [auth, db]
  `backend\heretek_swarm\api\skills.py`
- `GET` `/agents/by-tag/{tag}` params(tag) → in: SkillCategory [auth, db]
  `backend\heretek_swarm\api\skills.py`
- `GET` `/agents/{agent_id}` params(agent_id) → in: SkillCategory [auth, db]
  `backend\heretek_swarm\api\skills.py`
- `DELETE` `/{agent_id}/{skill_name}` params(agent_id, skill_name) [auth, db]
  `backend\heretek_swarm\api\skills.py`
- `POST` `/workspace` → in: dict [auth, db]
  `backend\heretek_swarm\api\skills.py`
- `GET` `/workspace/{workspace_id}` params(workspace_id) → in: SkillCategory [auth, db]
  `backend\heretek_swarm\api\skills.py`
- `POST` `/workspace/inject` → in: dict [auth, db]
  `backend\heretek_swarm\api\skills.py`

## Source Files

Read these before implementing or modifying this subsystem:
- `backend\heretek_swarm\api\skills.py`

---
_Back to [overview.md](./overview.md)_