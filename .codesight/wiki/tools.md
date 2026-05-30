# Tools

> **Navigation aid.** Route list and file locations extracted via AST. Read the source files listed below before implementing or modifying this subsystem.

The Tools subsystem handles **5 routes** and touches: auth.

## Routes

- `GET` `/tools` [auth]
  `backend\heretek_swarm\mcp\server.py`
- `GET` `/tools/{tool_name}` params(tool_name) [auth]
  `backend\heretek_swarm\mcp\server.py`
- `POST` `/tools/call` → in: ToolCallRequest [auth]
  `backend\heretek_swarm\mcp\server.py`
- `PUT` `/tools/toggle/{tool_name}` params(tool_name) [auth]
  `backend\heretek_swarm\mcp\server.py`
- `GET` `/tools/{tool_name}/stats` params(tool_name) [auth]
  `backend\heretek_swarm\mcp\server.py`

## Source Files

Read these before implementing or modifying this subsystem:
- `backend\heretek_swarm\mcp\server.py`

---
_Back to [overview.md](./overview.md)_