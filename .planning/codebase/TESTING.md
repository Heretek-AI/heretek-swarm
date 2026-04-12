# Testing Patterns

**Analysis Date:** 2026-04-12

## Test Frameworks

### Python

**Framework:** pytest 8.0+
- pytest-asyncio for async tests
- pytest-cov for coverage
- pytest-mock for mocking
- pytest-timeout for timeout handling
- pytest-xdist for parallel execution

**Configuration (pyproject.toml):**
```toml
[tool.pytest.ini_options]
minversion = "8.0"
testpaths = ["tests"]
python_files = ["test_*.py", "*_test.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
asyncio_mode = "auto"
```

### TypeScript/React

**Framework:** vitest (based on test file patterns)
- @testing-library/react for component tests
- @testing-library/jest-dom for assertions

**Configuration:** vite.config.ts

## Coverage Requirements

**Target:** 80% minimum (enforced)

```toml
[tool.coverage.report]
fail_under = 80
precision = 2
show_missing = true
```

**Coverage Commands:**
```bash
# Python - run with coverage
pytest tests/ --cov=src --cov-report=term-missing

# Frontend - via package.json scripts
npm test        # Run tests
npm run build   # Build with type checking
npm run lint    # Lint check
```

## Test Organization

### Python Directory Structure

```
tests/
├── __init__.py
├── conftest.py              # Shared fixtures
├── actors/                  # Actor tests
│   ├── test_base_actor.py
│   └── ...
├── collective/              # Collective intelligence tests
├── consciousness/           # Consciousness module tests
├── consensus/               # Consensus mechanism tests
├── evaluation/              # Evaluator tests
├── fixtures/                 # Test fixtures
├── gateway/                  # Gateway tests
├── infrastructure/           # Infrastructure tests
├── integration/              # Integration tests
│   ├── conftest.py
│   ├── agents/
│   └── scaffolding/
├── knowledge/                # Knowledge/RAG tests
├── load/                     # Load/performance tests
├── memory/                   # Memory system tests
├── observability/            # Observability tests
├── plugins/                  # Plugin tests
├── rag/                      # RAG pipeline tests
├── security/                # Security tests
├── serverless/               # Serverless tests
├── state/                    # State management tests
├── tools/                    # Tool tests
├── unit/                     # Unit tests
├── validation/              # Validation tests
└── workflow/                 # Workflow tests
```

### TypeScript Directory Structure

```
dashboard/frontend/src/
├── hooks/
│   ├── __tests__/
│   │   ├── useAgentHandles.test.tsx
│   │   ├── useRealTimeAgentUpdates.test.tsx
│   │   └── useNodeGrouping.test.tsx
│   └── useAgentHandles.ts
└── ...
```

## Test Markers (Python)

Markers defined in `conftest.py` and `pyproject.toml`:

```python
@pytest.mark.unit          # Unit tests (fast, isolated)
@pytest.mark.integration   # Integration tests (require external services)
@pytest.mark.load           # Load/performance tests
@pytest.mark.slow           # Tests that take >5s
@pytest.mark.a2a            # Agent-to-Agent messaging tests
@pytest.mark.consensus      # Consensus mechanism tests
@pytest.mark.latency        # Latency benchmark tests (<100ms baseline)
@pytest.mark.security       # Security-focused tests
```

**Running by marker:**
```bash
pytest tests/ -m unit          # Only unit tests
pytest tests/ -m "not slow"    # Exclude slow tests
pytest tests/ -m "a2a and not load"  # A2A tests excluding load
```

## Test Fixtures

### Python Fixtures (conftest.py)

**Agent Fixtures:**
```python
@pytest.fixture
def agent_id() -> str:
    """Generate a unique agent ID for testing."""
    return f"agent-{uuid.uuid4().hex[:8]}"

@pytest.fixture
def agent_config(agent_id: str) -> AgentConfig:
    """Create a basic agent configuration for testing."""
    return AgentConfig(
        agent_id=agent_id,
        agent_type="worker",
        capabilities=["task_execution", "messaging"],
    )

@pytest.fixture
def triad_agents() -> list[AgentConfig]:
    """Create Alpha, Beta, Charlie triad agents for consensus testing."""
    return [
        AgentConfig(agent_id="alpha-primary", agent_type="triad", ...),
        AgentConfig(agent_id="beta-primary", agent_type="triad", ...),
        AgentConfig(agent_id="charlie-primary", agent_type="triad", ...),
    ]
```

**Mock Fixtures:**
```python
@pytest.fixture
def mock_agent() -> MagicMock:
    """Create a mock agent for isolated testing."""
    agent = MagicMock()
    agent.agent_id = f"mock-{uuid.uuid4().hex[:8]}"
    agent.send_message = AsyncMock(return_value={"status": "sent"})
    agent.execute_task = AsyncMock(return_value={"result": "success"})
    return agent

@pytest.fixture
def mock_message_bus() -> MagicMock:
    """Create a mock message bus for A2A testing."""
    bus = MagicMock()
    bus.publish = AsyncMock(return_value=True)
    bus.subscribe = AsyncMock(return_value=True)
    return bus
```

**Security Fixtures:**
```python
@pytest.fixture
def malicious_inputs() -> list[dict[str, Any]]:
    """Collection of malicious inputs for security testing."""
    return [
        {"input": "'; DROP TABLE agents; --", "type": "sql_injection"},
        {"input": "<script>alert('xss')</script>", "type": "xss"},
        {"input": "${env.SECRET_KEY}", "type": "template_injection"},
        {"input": "../../../etc/passwd", "type": "path_traversal"},
    ]

@pytest.fixture
def secret_patterns() -> list[str]:
    """Patterns that should never appear in logs or outputs."""
    return ["sk-", "xoxb-", "ghp_", "-----BEGIN", "password", "api_key"]
```

**Latency Fixtures:**
```python
@pytest.fixture
def latency_tracker() -> dict[str, list[float]]:
    """Create a latency tracker for benchmark tests."""
    return {"message_latency": [], "task_execution": [], "consensus_round": []}

@pytest.fixture
def assert_latency_baseline():
    """Assert that latency meets the <100ms baseline requirement."""
    def _assert(latency_ms: float, operation: str = "operation") -> None:
        assert latency_ms < MESSAGE_LATENCY_BASELINE_MS, (
            f"{operation} latency {latency_ms:.2f}ms exceeds baseline"
        )
    return _assert
```

### TypeScript Fixtures

**Mock Fetch:**
```typescript
const mockFetch: jest.Mock = jest.fn();
(global as any).fetch = mockFetch;
```

## Mocking Patterns

### Python Mocking

**Using pytest-mock:**
```python
@pytest.fixture
def mock_agent() -> MagicMock:
    agent = MagicMock()
    agent.execute_task = AsyncMock(return_value={"result": "success"})
    return agent

async def test_actor_task_execution(mock_agent):
    mock_agent.execute_task.assert_not_called()
    result = await mock_agent.execute_task({"task": "test"})
    mock_agent.execute_task.assert_called_once_with({"task": "test"})
```

**Mocking Modules:**
```python
def mock_nats_module():
    """Mock NATS module to avoid pynats dependency issues."""
    import sys
    from unittest.mock import MagicMock
    mock_module = MagicMock()
    sys.modules["pynats"] = mock_module
    yield
    if "pynats" in sys.modules:
        del sys.modules["pynats"]
```

### TypeScript Mocking

**Mocking Fetch:**
```typescript
mockFetch.mockResolvedValueOnce({
  ok: true,
  json: async () => ({
    agentId: 'agent-123',
    subscriptions: mockSubscriptions,
    total: 2,
  }),
});

// Assert
expect(mockFetch).toHaveBeenCalledWith(
  '/api/agents/agent-123/channels',
  expect.objectContaining({ method: 'POST' })
);
```

## Test Patterns

### Python Test Structure

**Class-based (pytest):**
```python
class TestActorFactory:
    """Tests for ActorFactory class."""

    @pytest.fixture
    def factory(self):
        """Create a fresh factory instance for each test."""
        return ActorFactory()

    def test_register_actor_class(self, factory):
        """Test registering an actor class."""
        factory.register_actor_class("mock-actor", MockAgentActor)
        assert "mock-actor" in factory.get_registered_types()

    @pytest.mark.asyncio
    async def test_spawn_actor_stores_config(self, supervisor):
        """Test that spawn_actor stores actor configuration."""
        await supervisor.spawn_actor(MockAgentActor, "test-actor", name="Test")
        assert "test-actor" in supervisor.actors
```

**Function-based (acceptable for simple tests):**
```python
def test_actor_config_default_capabilities():
    """Test that capabilities defaults to empty list."""
    config = ActorConfig(actor_type="mock", class_ref=MockAgentActor, init_kwargs={})
    assert config.capabilities == []
```

### TypeScript Test Structure

**Vitest with Testing Library:**
```typescript
describe('getHandleColor', () => {
  it('should return green for event channel type', () => {
    expect(getHandleColor('event')).toBe('#10B981');
  });

  it('should return blue for command channel type', () => {
    expect(getHandleColor('command')).toBe('#3B82F6');
  });
});

describe('useAgentHandles', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should fetch channel subscriptions on mount', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ subscriptions: [], total: 0 }),
    });

    const { result } = renderHook(() =>
      useAgentHandles({ agentId: 'agent-123', enabled: true, pollingInterval: 0 })
    );

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });
  });
});
```

## Running Tests

### Python

```bash
# All tests
pytest tests/

# Specific directory
pytest tests/unit/

# With coverage
pytest tests/ --cov=src --cov-report=term-missing

# Specific marker
pytest tests/ -m unit

# Async tests
pytest tests/ -m asyncio

# Parallel execution
pytest tests/ -n auto

# Watch mode (during development)
pytest tests/ --watch
```

### TypeScript/Frontend

```bash
# Run tests (via package.json)
npm test

# Build with type checking
npm run build

# Lint
npm run lint
```

## Performance Baselines

From `conftest.py`:
- **Message Latency:** <100ms baseline
- **Concurrent Agent Target:** 1,000+ agents
- **Coverage Threshold:** 80%

```python
MESSAGE_LATENCY_BASELINE_MS = 100
CONCURRENT_AGENT_TARGET = 1000
COVERAGE_THRESHOLD = 80
```

## Test Data

**Fixtures Location:** `tests/fixtures/`

```python
# tests/fixtures/test_data.py
@pytest.fixture
def sample_agent_state():
    """Sample agent state for testing."""
    return {
        "agent_id": "test-agent",
        "status": "active",
        "current_task": "processing",
        "memory_context": {},
    }
```

## CI/CD Testing Pipeline

**Python Commands (from package.json verification):**
```bash
pytest tests/
ruff check src tests
mypy src
```

**Frontend Commands:**
```bash
npm test
npm run lint
npm run build
```

## Common Test Patterns

### Testing Async Code (Python)

```python
@pytest.mark.asyncio
async def test_actor_spawn_and_terminate():
    """Test actor lifecycle."""
    actor = AgentActor(agent_id="test-actor")
    await actor.spawn()
    assert actor.state == ActorState.ACTIVE
    await actor.terminate()
    assert actor.state == ActorState.TERMINATED
```

### Testing Error Handling (Python)

```python
@pytest.mark.asyncio
async def test_spawn_invalid_config():
    """Test that invalid config raises error."""
    with pytest.raises(ValueError, match="max_mailbox_size must be positive"):
        AgentActor(agent_id="test", max_mailbox_size=-1)
```

### Testing React Components (TypeScript)

```typescript
// Placeholder tests in useAgentHandles.test.tsx
// Note: Full component tests require @testing-library/react with jsdom
/*
import { render, screen } from '@testing-library/react';
import { DynamicHandles } from '../../components/WorkflowBuilder/DynamicHandles';

describe('DynamicHandles Component', () => {
  it('should render default handles when no subscriptions', () => {
    render(<DynamicHandles handles={[]} />);
    expect(document.querySelectorAll('.react-flow__handle')).toHaveLength(2);
  });
});
*/
```

## Test Isolation

**Python:**
- Each test gets fresh fixtures via function scope
- Mock state cleanup via `autouse=True` fixtures
- Database/async cleanup handled by fixtures

**TypeScript:**
- `beforeEach(() => vi.clearAllMocks())` clears mocks between tests
- Each `renderHook` gets fresh state

---

*Testing analysis: 2026-04-12*
