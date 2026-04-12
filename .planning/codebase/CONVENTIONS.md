# Coding Conventions

**Analysis Date:** 2026-04-12

## Languages

**Primary:**
- Python 3.11+ - Backend, API, agents, swarm orchestration
- TypeScript 5.2+ - React frontend dashboard

**Secondary:**
- JavaScript (ES2020 target) - Minimal, only where TypeScript not available

## Python Standards

### Style Guide

**Linting:** ruff (configured in `pyproject.toml`)
- Target: Python 3.11
- Line length: 100 characters
- Selects: E, W, F, I, B, C4, UP, ARG, SIM, TCH, PTH, ERA, RUF, ASYNC, S, A, COM, DTZ, T10, EXE, FIX, FA, INT, ISC, ICN, G, INP, PIE, PYI, PT, Q, RSE, RET, SLF, SLOT, TID, T20, PERF

**Import Organization (isort):**
```python
# Standard library
import asyncio
import uuid
from collections.abc import Callable
from dataclasses import dataclass, field

# Third-party (pydantic, swarms, etc.)
import structlog
from pydantic import ValidationError
from swarms import Agent

# First-party (local application)
import heretek_swarm.actors.stubs as _actor_stubs
from heretek_swarm.actors.validation import validate_message
from heretek_swarm.state.repository import AgentStateRecord, StateCheckpoint, StateRepository
```

**Type Checking:** mypy strict mode
- `disallow_untyped_defs = true`
- `disallow_incomplete_defs = true`
- `check_untyped_defs = true`
- Tests exempt: `tests.*` has `disallow_untyped_defs = false`

### Naming Conventions

| Element | Convention | Example |
|---------|------------|---------|
| Modules | snake_case | `agent_actor.py` |
| Classes | PascalCase | `AgentActor`, `ActorConfig` |
| Functions | snake_case | `validate_message`, `save_state` |
| Variables | snake_case | `agent_id`, `message_count` |
| Constants | UPPER_SNAKE_CASE | `MESSAGE_LATENCY_BASELINE_MS` |
| Type aliases | PascalCase | `AgentHandle`, `ChannelType` |
| Private attrs | _leading_underscore | `_state_repository` |
| Internal vars | _avoid | Use descriptive names |

### Code Patterns

**Dataclasses for DTOs:**
```python
from dataclasses import dataclass, field
from typing import Any

@dataclass
class ActorMessage:
    sender: str
    message_type: str
    content: dict[str, Any]
    timestamp: str
    correlation_id: str | None = None
    reply_to: str | None = None
    recipient: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
```

**Pydantic for Configuration:**
```python
from pydantic import BaseModel, Field
from datetime import UTC, datetime

class UserConfiguration(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    config_key: str = Field(..., min_length=1, max_length=255)
    config_value: Any
    is_sensitive: bool = Field(default=False)

    class Config:
        use_enum_values = True
```

**Async/Await:**
```python
async def spawn(self) -> None:
    """Spawn the actor and start processing messages."""
    self._running = True
    self.state = ActorState.ACTIVE
    self._processing_task = asyncio.create_task(self._process_mailbox())
```

**Logging (structlog):**
```python
import structlog

structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.JSONRenderer(),
    ],
)

logger = structlog.get_logger("AgentActor")
```

**Error Handling:**
```python
try:
    result = await handler(message)
except Exception as e:
    logger.error(
        f"[{self.agent_id}] Error in handler: {e}",
        exc_info=True,
    )
    self.error_count += 1
```

## TypeScript/React Standards

### Style Guide

**Linting:** eslint with TypeScript plugin
- Strict mode enabled
- No unused locals or parameters
- Module: ESNext
- JSX: react-jsx

**Formatting:** Project uses Vite build system

### Naming Conventions

| Element | Convention | Example |
|---------|------------|---------|
| Components | PascalCase | `AgentCard.tsx`, `Dashboard.tsx` |
| Hooks | camelCase + use prefix | `useAgentHandles`, `useWebSocket` |
| Interfaces/Types | PascalCase | `AgentHandle`, `ChannelSubscription` |
| Functions | camelCase | `getHandleColor`, `formatUser` |
| Variables | camelCase | `agentId`, `isLoading` |
| Constants | UPPER_SNAKE_CASE | `MAX_RETRIES` |
| Files (components) | PascalCase.tsx | `AgentCard.tsx` |
| Files (hooks/utils) | camelCase.ts | `useAgentHandles.ts` |
| CSS/Tailwind | kebab-case | `bg-blue-500`, `flex-row` |

### Code Patterns

**TypeScript Interfaces for Props:**
```typescript
export interface AgentHandle {
  id: string;
  type: 'source' | 'target';
  position: Position;
  channelName: string;
  channelType: ChannelType;
  dataType?: string;
  description?: string;
}

interface UseAgentHandlesResult {
  handles: AgentHandle[];
  subscriptions: ChannelSubscription[];
  isLoading: boolean;
  error: Error | null;
  addSubscription: (subscription: Omit<ChannelSubscription, 'subscribedAt'>) => Promise<void>;
  removeSubscription: (channelName: string) => Promise<void>;
}
```

**Custom Hooks:**
```typescript
export function useAgentHandles({
  agentId,
  enabled = true,
  pollingInterval = 30000,
  apiUrl = '',
}: UseAgentHandlesOptions): UseAgentHandlesResult {
  const [handles, setHandles] = useState<AgentHandle[]>([]);
  const [subscriptions, setSubscriptions] = useState<ChannelSubscription[]>([]);
  // ...
}
```

**Async Error Handling:**
```typescript
async function fetchSubscriptions() {
  try {
    const response = await fetch(`${apiUrl}/api/agents/${agentId}/channels`);
    if (!response.ok) {
      throw new Error(`Failed: ${response.statusText}`);
    }
    const data = await response.json();
    setSubscriptions(data.subscriptions || []);
  } catch (err) {
    const error = err instanceof Error ? err : new Error('Unknown error');
    setError(error);
  }
}
```

**State Management (Zustand):**
```typescript
// From stores/canvasStore.ts
import { create } from 'zustand';

interface CanvasState {
  nodes: Node[];
  edges: Edge[];
  addNode: (node: Node) => void;
}

export const useCanvasStore = create<CanvasState>((set) => ({
  nodes: [],
  edges: [],
  addNode: (node) => set((state) => ({ nodes: [...state.nodes, node] })),
}));
```

## Git Workflow

**Branch:** main (default)

**Commit Format:**
```
<type>: <description>

<optional body>
```

Types: feat, fix, refactor, docs, test, chore, perf, ci

**Example:**
```
feat: add actor restart mechanism

- Implement _attempt_restart in ActorSupervisor
- Add restart_counts tracking per actor
- Handle max_restarts exceeded case
```

**Pre-commit Checks:**
```bash
# Python
pytest tests/
ruff check src tests
mypy src

# TypeScript
npm run lint
npm run build
```

## Documentation Standards

**Docstrings (Python):**
```python
async def spawn(self) -> None:
    """
    Spawn the actor and start processing messages.

    This method:
    1. Sets actor state to ACTIVE
    2. Starts mailbox processing loop
    3. Starts heartbeat loop
    4. Calls initialize() hook for subclass setup
    5. Loads state from database if configured

    Raises:
        Exception: If spawn fails
    """
```

**TSDoc (TypeScript):**
```typescript
/**
 * Hook for managing dynamic agent handles
 *
 * Fetches agent channel subscriptions from API and creates dynamic handles
 * for input/output connections based on channel types.
 *
 * @param agentId - The unique agent identifier
 * @param enabled - Whether to enable fetching
 * @param pollingInterval - Polling interval in milliseconds
 */
export function useAgentHandles({ agentId, enabled, pollingInterval }: UseAgentHandlesOptions) {
  // implementation
}
```

**Inline Comments:**
```python
# P1-10e fix: Add retry logic for message queuing instead of dropping
for attempt in range(max_retries):
    try:
        await asyncio.wait_for(self.mailbox.put(message), timeout=5.0)
```

## File Organization

**Python:** Organize by feature/domain
```
src/heretek_swarm/
├── actors/           # Agent implementations
│   ├── base.py      # Base AgentActor class
│   ├── factory.py   # Actor factory
│   ├── mixins/      # Reusable behaviors
│   └── [agent].py   # Individual agents
├── api/             # FastAPI endpoints
├── consciousness/   # Consciousness modules
├── consensus/       # Consensus mechanisms
└── ...
```

**TypeScript/React:** Organize by surface area
```
dashboard/frontend/src/
├── components/
│   ├── Agents/
│   │   ├── AgentCard.tsx
│   │   └── index.ts
│   └── UI/
├── hooks/
│   ├── useAgentHandles.ts
│   └── __tests__/
├── stores/          # Zustand stores
├── api/             # API client modules
└── utils/           # Utilities
```

## Error Handling Patterns

**Python:**
```python
# Always handle exceptions with logging
try:
    result = await operation()
except Exception as e:
    logger.error(f"Operation failed: {e}", exc_info=True)
    raise

# Use sentinel values sparingly
# Prefer explicit error handling
```

**TypeScript:**
```typescript
// Always narrow unknown errors
try {
  const result = await riskyOperation();
  return result;
} catch (error: unknown) {
  if (error instanceof Error) {
    setError(error.message);
  }
  throw error;
}
```

## Configuration

**Environment Variables:**
- Python: Use pydantic settings or `os.environ` with validation
- TypeScript: Use `import.meta.env.VITE_*` for Vite

**Secrets:** Never hardcode; use environment variables or secret managers

---

*Convention analysis: 2026-04-12*
