# Coding Conventions

**Analysis Date:** 2026-04-15

## Naming Patterns

**Files:**
- Python modules: `snake_case.py` (e.g., `actor_messages.py`, `zero_trust.py`)
- Test files: `test_<module>.py` or `<module>_test.py`
- Integration tests: `tests/<domain>/test_<feature>.py`

**Classes:**
- PascalCase: `AgentActor`, `StewardAgent`, `ActorFactory`
- Mixins: `XxxMixin` suffix (e.g., `ValidationMixin`, `DeliberationMixin`)
- Data classes: PascalCase with descriptive names (e.g., `ActorConfig`, `LayerResult`)

**Functions/Methods:**
- snake_case: `validate_message()`, `create_actor()`, `process_message()`
- Private methods: `_leading_underscore`
- Async methods: prefixed with `async_` where ambiguous

**Variables:**
- snake_case: `agent_id`, `message_type`, `state_value`
- Constants: UPPER_SNAKE_CASE: `MESSAGE_LATENCY_BASELINE_MS`, `CONCURRENT_AGENT_TARGET`
- Private variables: `_leading_underscore`

**Types/Enums:**
- StrEnum with UPPER_SNAKE_CASE values: `class Severity(StrEnum): CRITICAL = "CRITICAL"`
- Message types: `MESSAGE_TYPE = "message_type"` pattern

## Code Style

**Formatting:**
- Tool: `ruff` (configured in `pyproject.toml`)
- Line length: 100 characters
- Use `ruff format` for formatting (integrated with ruff)

**Linting:**
- Tool: `ruff` with comprehensive rule sets (E, W, F, I, B, C4, UP, ARG, SIM, TCH, PTH, ERA, RUF, ASYNC, S, A, COM, DTZ, T10, EXE, FIX, FA, INT, ISC, ICN, G, INP, PIE, PYI, PT, Q, RSE, RET, SLF, SLOT, TID, T20, PERF)
- Ignored rules in tests: `S101` (assert), `ARG001` (unused args), `PT019` (pytest fixtures)

**Type Checking:**
- Tool: `mypy` with strict mode enabled
- Python version: 3.11
- Tests exempt from strict type checking: `[tool.mypy.overrides] module = "tests.*"`

## Import Organization

**Order:**
1. Standard library imports
2. Third-party imports (pydantic, structlog, swarms, etc.)
3. Local application imports (from heretek_swarm.*)
4. Type imports last

**Example:**
```python
import asyncio
import uuid
from datetime import UTC, datetime
from typing import Any

import structlog
from pydantic import BaseModel, Field

from heretek_swarm.actors.base import AgentActor
from heretek_swarm.validation.agent_messages import ActorMessage
```

**Path aliases:**
- Use `from heretek_swarm.xxx` not relative imports within the package
- `src` added to `known-first-party` in ruff isort config

## Pydantic Models

**Patterns:**
- Use `BaseModel` with `model_config` for configuration
- Use `Field()` for field definitions with constraints
- Use `validator` decorators for custom validation
- Use `StrEnum` for string-based enums

**Example:**
```python
class ActorMessage(BaseModel):
    message_id: str = Field(default_factory=lambda: f"msg_{uuid.uuid4().hex[:12]}")
    message_type: str = Field(..., description="Type of the message")
    content: dict[str, Any] = Field(..., description="Message content payload")

    @pydantic_validator("content")
    def validate_content_safety(cls, v: dict[str, Any]) -> dict[str, Any]:
        # validation logic
        return v

    class Config:
        extra = "allow"  # Allow flexibility
        validate_assignment = True
```

## Error Handling

**Patterns:**
- Use structured logging via `structlog`
- Catch specific exceptions, not bare `except:`
- Propagate errors with context via logger
- Use `exc_info=True` for exception stack traces in logs

**Example:**
```python
try:
    result = await some_operation()
except ValidationError as e:
    logger.warning(
        f"[{self.agent_id}] Validation failed: {e}",
        extra={"validation_errors": e.errors()},
    )
    raise ValueError(f"Invalid message format: {e.errors()}")
except Exception as e:
    logger.error(
        f"[{self.agent_id}] Operation failed: {e}",
        exc_info=True,
    )
    self.error_count += 1
    raise
```

## Logging

**Framework:** `structlog`
- Configured in module or at package init
- Use bound loggers with agent context
- JSON rendering for production

**Patterns:**
```python
logger = structlog.get_logger("ModuleName")

# With context
logger.info(
    f"[{self.agent_id}] Actor spawned",
    extra={
        "name": self.name,
        "topics": self.topics,
    },
)
```

**Key Conventions:**
- Always include `agent_id` in brackets: `f"[{self.agent_id}] ..."`
- Use `extra={}` dict for structured metadata
- Use `exc_info=True` for errors
- Log levels: DEBUG < INFO < WARNING < ERROR < CRITICAL

## Actor Pattern

**Mixin Inheritance Order:**
```python
class StewardAgent(
    HealthReportingMixin,
    ValidationMixin,
    DeliberationMixin,
    PatternMixin,
    MemoryMixin,
    LearningMixin,
    TribunalMixin,
    AgentActor,
):
```

**Lifecycle Methods:**
- `async def initialize(self)` - Override for setup
- `async def cleanup(self)` - Override for teardown
- `async def process_message(message: ActorMessage)` - Handle incoming messages
- `register_handler(message_type, handler)` - Register message handlers

**State Management:**
- Use `ActorState` enum: SPAWNING, ACTIVE, SUSPENDED, TERMINATED, ERROR
- Use `_state_repository` for persistence
- Call `save_state()` before terminate

## Validation Patterns

**Input Validation:**
- Pydantic models for message validation
- UUID v4 validation for IDs
- Size limits (max_content_size, max_string_length)
- Pattern detection for injection attacks (exec, eval, __import__, subprocess, SQL injection, path traversal)

**Zero-Trust 4-Layer Validation:**
1. Input Validation - Pydantic v2, UUID v4, size limits
2. Context Validation - injection detection, behavioral analysis
3. Output Validation - PII detection, sensitive data filtering
4. Audit Logging - structured logging, severity levels

## Dataclasses vs Pydantic

**Use Pydantic when:**
- Validating external input
- Need automatic validation on assignment
- Working with JSON serialization
- Need field constraints and validators

**Use dataclass when:**
- Internal data structures
- Simple data containers
- No validation needed

## Async Patterns

**Async/Await:**
- Always use `async def` for async methods
- Use `await` for all async operations
- Handle `asyncio.CancelledError` in cancellation paths
- Use `asyncio.create_task()` for fire-and-forget tasks

**Event Loop:**
- Tests use `pytest-asyncio` with `asyncio_mode = "auto"`
- Use `@pytest_asyncio.fixture` for async fixtures
- Cleanup pending tasks in fixtures

## Testing Utilities

**Mock Patterns:**
- Use `MagicMock` and `AsyncMock` from `unittest.mock`
- Mock NATS with in-memory `MockNATSEventMesh`
- Mock LLM provider with deterministic responses
- Mock database for integration tests

**Fixtures Location:**
- Root: `tests/conftest.py` - shared fixtures
- Integration: `tests/integration/conftest.py` - integration-specific
- Domain: `tests/<domain>/conftest.py` - domain-specific

## Module Structure

**Package Layout:**
```
src/heretek_swarm/
├── actors/           # 23 agent implementations + base classes
│   ├── base.py       # Re-exports from split modules
│   ├── base/         # Core implementation (core.py, state_management.py, message_handling.py)
│   ├── mixins/       # Reusable mixin functionality
│   ├── factory.py    # ActorFactory for actor creation
│   └── [agent].py    # Individual agent implementations
├── validation/       # Message validation (Pydantic models)
├── security/         # Zero-trust, validators, guardrails
├── consensus/        # MAKER protocol, deliberation
├── memory/           # Multi-tier memory
├── state/            # PostgreSQL persistence
├── gateway/          # NATS event mesh
├── observability/    # Metrics, tracing, alerting
├── logging/          # Logging configuration
├── runtime/          # Runtime, scaling, registry
└── cli.py            # CLI entry point
```

## Docstring Standards

**Modules:**
```python
"""
Module Name - Brief description.

This module provides:
- Feature 1
- Feature 2

Author: Heretek Swarm Collective
Date: 2026-04-07
Version: 1.0.0
"""
```

**Classes:**
```python
class AgentActor:
    """
    Brief description of the class.

    Extended description if needed, covering:
    - Purpose
    - Key features
    - Usage examples

    Attributes:
        attr1: Description of attr1
        attr2: Description of attr2
    """
```

**Methods:**
```python
async def process_message(self, message: ActorMessage) -> None:
    """
    Process incoming messages.

    Args:
        message: Actor message to process

    Returns:
        None

    Raises:
        ValueError: If message format is invalid
    """
```

---

*Convention analysis: 2026-04-15*
