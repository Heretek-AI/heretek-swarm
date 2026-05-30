# Chat

> **Navigation aid.** Route list and file locations extracted via AST. Read the source files listed below before implementing or modifying this subsystem.

The Chat subsystem handles **1 routes** and touches: auth, queue.

## Routes

- `POST` `/{agent_id}/chat` params(agent_id) → out: ChatResponse [auth, queue]
  `backend\heretek_swarm\api\agents\chat.py`

## Source Files

Read these before implementing or modifying this subsystem:
- `backend\heretek_swarm\api\agents\chat.py`

---
_Back to [overview.md](./overview.md)_