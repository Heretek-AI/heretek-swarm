# Coding Conventions

**Analysis Date:** 2026-04-13

## Language and Style

**Python:**
- Version: 3.12+ (from `.nvmrc` and pyproject.toml)
- Style: PEP 8 with type annotations required on all function signatures
- Formatter: `ruff format` (black-compatible)
- Linter: `ruff check`

**TypeScript/JavaScript:**
- Framework: React with Vite
- Style: ESLint + Prettier (configured in project)

## Python Conventions

### Type Annotations

All function signatures require type annotations:

```python
from typing import Any

def process_message(message: ActorMessage) -> None:
    ...

def get_state(key: str, default: str | None = None) -> str | None:
    ...
```

### Data Classes

Use dataclasses for structured data with `field()` for defaults:

```python
from dataclasses import dataclass, field
from datetime import UTC, datetime

@dataclass
class AgentConfig:
    agent_id: str
    agent_type: str
    capabilities: list[str] = field(default_factory=list)
    reputation: float = 1.0
    max_concurrent_tasks: int = 10
```

### Enums

Use StrEnum for string-based enums:

```python
from enum import StrEnum

class ConsensusState(StrEnum):
    GATHERING = "gathering"
    VOTING = "voting"
    AGGREGATING = "aggregating"
    COMPLETED = "completed"
    FAILED = "failed"
```

### Immutability

Prefer frozen dataclasses for immutable data:

```python
@dataclass(frozen=True)
class Vote:
    agent_id: str
    decision: str
    confidence: float
    timestamp: str
    metadata: dict[str, Any] = field(default_factory=dict)
```

## Naming Conventions

| Element | Convention | Example |
|---------|------------|---------|
| Files | snake_case | `test_base_actor.py`, `state_repository.py` |
| Classes | PascalCase | `AgentActor`, `MAKERConsensus` |
| Functions/methods | snake_case | `get_state()`, `add_vote()` |
| Constants | UPPER_SNAKE_CASE | `MESSAGE_LATENCY_BASELINE_MS` |
| Private methods | _snake_case | `_check_red_flags()` |
| Module-level vars | UPPER_SNAKE_CASE | `COVERAGE_THRESHOLD = 80` |

## Import Organization

Standard library first, then third-party, then local:

```python
# Standard library
import asyncio
from dataclasses import dataclass, field
from typing import Any

# Third-party
import pytest
import structlog

# Local application
from heretek_swarm.actors.base import AgentActor
from heretek_swarm.state.repository import StateRepository
```

## Logging

Use `structlog` for structured logging:

```python
import structlog

logger = structlog.get_logger(__name__)

logger.info("consensus_started", consensus_id="test-1", agent_count=3)
logger.warning("unknown_consensus_id", consensus_id="nonexistent")
```

**Do not use** `print()` statements - use logging instead.

## Error Handling

- Use validation with Pydantic models for message content
- Raise `ValueError` with descriptive messages for invalid input
- Log errors with context before raising

```python
def _validate_message_content(self, message_type: str, content: dict[str, Any]) -> Any:
    """Validate message content against registered validator."""
    if message_type not in self._validators:
        return content  # Unknown types pass through

    validator = self._validators[message_type]
    try:
        return validator(**content)
    except Exception as e:
        raise ValueError(f"Invalid content for {message_type}: {e}")
```

## Async Code

- Use `async def` for all asynchronous functions
- Use `pytest-asyncio` for async tests with `@pytest.mark.asyncio`
- Always handle cleanup in fixtures with yield:

```python
@pytest_asyncio.fixture
async def connected_nats(mock_nats: MockNATSEventMesh) -> MockNATSEventMesh:
    await mock_nats.connect()
    yield mock_nats
    await mock_nats.disconnect()
```

## File Organization

- **Source:** `src/heretek_swarm/` with module-based subdirectories
- **Tests:** `tests/` organized by module/feature, mirror src structure
- **Max file length:** ~800 lines; split large modules

## Class Structure

Base classes use mixin pattern for separation of concerns:

```python
# src/heretek_swarm/actors/base.py - backward compatibility wrapper
from heretek_swarm.actors.base.core import AgentActor
from heretek_swarm.actors.base.message_handling import AgentActorMessageHandling
from heretek_swarm.actors.base.state_management import AgentActorStateManagement
```

## Linting Configuration

From `pyproject.toml`:

```toml
[tool.ruff]
target-python-version = "3.12"
line-length = 100

[tool.ruff.lint]
select = [
    "E",   # pycodestyle errors
    "W",   # pycodestyle warnings
    "F",   # Pyflakes
    "I",   # isort
    "B",   # flake8-bugbear
    "C4",  # flake8-comprehensions
    "UP",  # pyupgrade
    "ARG", # flake8-unused-arguments
    "SIM", # flake8-simplify
    "TCH", # flake8-type-checking
    "PTH", # flake8-use-pathlib
    "ERA", # eradicate
    "RUF", # Ruff-specific rules
    "ASYNC", # flake8-async
]
ignore = ["ERA", "PTH"]
```

## Type Checking

mypy configuration in `pyproject.toml`:

```toml
[tool.mypy]
python_version = "3.12"
strict = true
disallow_untyped_defs = true
disallow_incomplete_defs = true
check_untyped_defs = true
warn_return_any = true
warn_unused_ignores = true

[tool.mypy.tests]
disallow_untyped_defs = false  # Tests exempt from strict typing
```

---

*Convention analysis: 2026-04-13*