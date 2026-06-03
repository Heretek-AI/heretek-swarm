---
name: heretek-backend-development
description: >-
  Backend development patterns for Heretek Swarm Python/FastAPI services. Use when
  building API endpoints, creating agent actors, implementing memory operations,
  or working with async Python patterns. Covers project structure, conventions,
  and common pitfalls specific to this codebase.
---

# Heretek Swarm Backend Development

## Project Structure

```
backend/heretek_swarm/
├── actors/           # Agent implementations (23 classes)
├── api/              # FastAPI routers (27 routers, 175+ endpoints)
├── consensus/        # Triad consensus system
├── gateway/          # NATS JetStream + A2A protocol
├── memory/           # Cognee-backed memory system
├── llm/              # LLM integration
├── mcp/              # Model Context Protocol servers
├── orchestration/    # Workflow orchestration
├── plugins/          # Plugin system
├── state/            # State management
└── security/         # Zero-trust security
```

## Conventions

### Code Style
- **Type hints required** on all public APIs
- **async/await** for all I/O operations
- **pathlib.Path** for file operations
- **Google-style docstrings** with max 120 chars per line
- **Ruff** for linting (target Python 3.11)

### Agent Development
- Base class: `AgentActor` in `actors/base/core.py`
- Use mixins from `actors/mixins/` for cross-cutting concerns
- Compose, don't subclass for multiple inheritance
- Ruff ignores `N801` in `actors/` (class names like `AgentActor` allowed)

### API Development
- FastAPI with async dependencies
- Input validation mandatory on all handlers
- Structured error responses
- OpenAPI/Redoc at `/docs` when running

### Memory System
- Cognee HTTP API is the sole backend
- Use `CogneeMemoryReader`/`CogneeMemoryWriter` for operations
- No legacy in-process memory (DualTierMemory, PersistentMemory deleted)
- Access patterns in `access_patterns.py` for tiering/classification

## Development Workflow

### Setup
```bash
# Install dependencies (preferred)
uv sync

# Fallback
pip install -e .
```

### Verification
```bash
# Lint (target specific dirs, NOT full project)
ruff check backend/ tests/

# Type check
mypy backend/heretek_swarm/

# Tests
pytest tests/ -v

# Single file
pytest tests/test_memory.py -v
```

### Docker Operations
```bash
# Full stack
docker compose up

# Health check
heretek-swarm status --json

# In-memory mode (no Docker)
heretek-swarm run --no-infra --prompt "Hello"
```

## Common Patterns

### Creating a New Agent
1. Create directory under `actors/<agent_name>/`
2. Implement class inheriting from `AgentActor`
3. Add mixins as needed (audit, deliberation, memory, etc.)
4. Register in `actors/__init__.py`
5. Add tests in `tests/`

### Adding API Endpoint
1. Create router in `api/<feature>/`
2. Use async dependencies
3. Add input validation with Pydantic
4. Register router in `api/__init__.py`
5. Add OpenAPI documentation

### Memory Operations
```python
# Reading
reader = CogneeMemoryReader()
results = await reader.search(query, limit=10)

# Writing
writer = CogneeMemoryWriter()
await writer.add(content, metadata)
await writer.cognify()  # Process into knowledge graph
```

## Gotchas

1. **Ruff scope**: Always run `ruff check backend/ tests/` - full project picks up non-Python files
2. **NATS mTLS**: Certs in `certs/` must be regenerated when docker network changes
3. **Container entrypoint**: Runs migrations first - rebuild image if migrations change
4. **No eval/exec**: Dynamic code execution forbidden anywhere
5. **Input validation**: Mandatory on every agent message handler

## Testing Patterns

- pytest with asyncio
- Use `pytest-asyncio` mode=auto for Python 3.14 compatibility
- Negative assertions verify legacy code doesn't creep back
- Test both happy path and error conditions
- Mock external services (Cognee, NATS) in unit tests

## Security Requirements

- Zero-trust: All inter-agent messages authenticated
- No secrets in code - use SOPS-encrypted files
- Input validation mandatory
- Audit trails for all operations
- Tool allowlisting in `.github/instructions/agent_safety.instructions.md`