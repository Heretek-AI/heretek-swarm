# Testing Patterns

**Analysis Date:** 2026-04-13

## Test Frameworks

### Python

**Framework:** pytest 8.0+
- pytest-asyncio for async tests
- pytest-cov for coverage
- pytest-mock for mocking
- pytest-timeout for timeout handling

**Configuration (pyproject.toml):**
```toml
[tool.pytest.ini_options]
minversion = "8.0"
testpaths = ["tests"]
python_files = ["test_*.py", "*_test.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
asyncio_mode = "auto"
asyncio_default_fixture_loop_scope = "function"
```

### TypeScript/React

**Framework:** vitest (Vite-based)
- @testing-library/react for component tests

## Coverage Requirements

**Target:** 80% minimum (enforced)

```toml
[tool.coverage.report]
fail_under = 80
precision = 2
show_missing = true
skip_empty = true
```

**View Coverage:**
```bash
pytest tests/ --cov=src --cov-report=term-missing
```

## Test Organization

### Python Directory Structure

```
tests/
├── __init__.py
├── conftest.py                    # Root shared fixtures
├── actors/                         # Actor tests
│   ├── test_base_actor.py
│   ├── test_profiling.py
│   └── ...
├── collective/                     # Collective intelligence tests
├── consciousness/                   # Consciousness module tests
├── consensus/                       # Consensus mechanism tests
│   ├── test_maker.py              # MAKER consensus tests
│   ├── test_deliberation.py
│   └── ...
├── fixtures/                        # Test fixtures (serverless.yaml, etc.)
├── gateway/                         # Gateway tests
├── integration/                     # Integration tests
│   ├── conftest.py                # Integration-specific mocks
│   ├── agents/                    # Agent integration tests
│   └── scaffolding/               # Mock helpers
├── memory/                          # Memory system tests
├── security/                       # Security tests
├── state/                          # State management tests
├── validation/                    # Validation tests
└── workflow/                       # Workflow tests
```

## Test Markers

Markers defined in `conftest.py`:

```python
@pytest.mark.unit          # Unit tests (fast, isolated, no external deps)
@pytest.mark.integration   # Integration tests (require external services)
@pytest.mark.load          # Load/performance tests for scalability
@pytest.mark.slow          # Tests that take >5 seconds
@pytest.mark.a2a            # Agent-to-Agent messaging tests
@pytest.mark.consensus      # Consensus mechanism tests (MAKER, BFT)
@pytest.mark.latency        # Latency benchmark tests (<100ms baseline)
@pytest.mark.security       # Security-focused tests
```

**Running by marker:**
```bash
pytest tests/ -m unit                    # Only unit tests
pytest tests/ -m "not slow"             # Exclude slow tests
pytest tests/ -m "a2a and not load"     # A2A tests excluding load
```

## Test Fixtures

### Root conftest.py (`tests/conftest.py`)

**Performance Baselines:**
```python
MESSAGE_LATENCY_BASELINE_MS = 100  # <100ms message latency requirement
CONCURRENT_AGENT_TARGET = 1000     # Must support 1,000+ concurrent agents
COVERAGE_THRESHOLD = 80            # >80% test coverage requirement
```

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

**Model Fixtures:**
```python
class Message(BaseModel):
    message_id: str
    sender_id: str
    receiver_id: str
    message_type: str
    payload: dict[str, Any]
    timestamp: float = field(default_factory=time.time)
    correlation_id: str | None = None
    latency_ms: float | None = None

class AgentState(BaseModel):
    agent_id: str
    status: str = "idle"
    current_task: str | None = None
    memory_context: dict[str, Any] = {}
    last_heartbeat: float = field(default_factory=time.time)
```

**Mock Fixtures:**
```python
@pytest.fixture
def mock_agent() -> MagicMock:
    """Create a mock agent for isolated testing."""
    agent = MagicMock()
    agent.agent_id = f"mock-{uuid.uuid4().hex[:8]}"
    agent.send_message = AsyncMock(return_value={"status": "sent"})
    agent.receive_message = AsyncMock()
    agent.execute_task = AsyncMock(return_value={"result": "success"})
    agent.get_state = MagicMock(return_value=AgentState(agent_id=agent.agent_id))
    return agent

@pytest.fixture
def mock_message_bus() -> MagicMock:
    """Create a mock message bus for A2A testing."""
    bus = MagicMock()
    bus.publish = AsyncMock(return_value=True)
    bus.subscribe = AsyncMock(return_value=True)
    bus.get_message = AsyncMock()
    bus.acknowledge = AsyncMock(return_value=True)
    return bus

@pytest.fixture
def mock_memory_store() -> MagicMock:
    """Create a mock memory store for testing."""
    store = MagicMock()
    store.store = AsyncMock(return_value=True)
    store.retrieve = AsyncMock(return_value={"data": "test"})
    store.delete = AsyncMock(return_value=True)
    store.query = AsyncMock(return_value=[])
    return store
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
        {"input": "A" * 1000000, "type": "buffer_overflow"},
        {"input": {"__proto__": {"admin": True}}, "type": "prototype_pollution"},
    ]

@pytest.fixture
def secret_patterns() -> list[str]:
    """Patterns that should never appear in logs or outputs."""
    return ["sk-", "xoxb-", "ghp_", "AKIA", "eyJ", "-----BEGIN", "password", "secret", "api_key"]
```

**Latency Fixtures:**
```python
@pytest.fixture
def latency_tracker() -> dict[str, list[float]]:
    """Create a latency tracker for benchmark tests."""
    return {
        "message_latency": [],
        "task_execution": [],
        "consensus_round": [],
        "state_rollback": [],
    }

@pytest.fixture
def assert_latency_baseline():
    """Assert that latency meets the <100ms baseline requirement."""
    def _assert(latency_ms: float, operation: str = "operation") -> None:
        assert latency_ms < MESSAGE_LATENCY_BASELINE_MS, (
            f"{operation} latency {latency_ms:.2f}ms exceeds "
            f"baseline of {MESSAGE_LATENCY_BASELINE_MS}ms - FLAG FOR REFACTORING"
        )
    return _assert
```

### Integration conftest.py (`tests/integration/conftest.py`)

**Mock NATS Event Mesh:**
```python
class MockNATSEventMesh:
    """In-memory mock for NATSEventMesh with pub/sub and request-reply patterns."""

    async def connect(self) -> bool: ...
    async def publish(self, subject: str, data: dict[str, Any], reply: str | None = None) -> bool: ...
    async def subscribe(self, subject_pattern: str, callback: Callable) -> str: ...
    async def request(self, subject: str, data: dict[str, Any], timeout: int = 5) -> dict[str, Any]: ...
```

**Mock LLM Provider:**
```python
class MockLLMProvider:
    """Mock LLM provider for deterministic testing."""

    def register_response(self, prompt_pattern: str, response: str) -> None: ...
    def set_default_response(self, response: str) -> None: ...
    def set_latency(self, latency_ms: float) -> None: ...
    async def generate(self, prompt: str, **kwargs) -> str: ...
```

**Mock Database:**
```python
class MockDatabase:
    """In-memory mock database for testing."""

    async def connect(self) -> bool: ...
    async def execute(self, query: str, params: tuple | None = None) -> list[dict[str, Any]]: ...
    async def create_table(self, table_name: str, schema: dict[str, str]) -> bool: ...
```

**Fixtures:**
```python
@pytest_asyncio.fixture
async def mock_nats() -> MockNATSEventMesh: ...

@pytest_asyncio.fixture
async def connected_nats(mock_nats: MockNATSEventMesh) -> MockNATSEventMesh: ...

@pytest_asyncio.fixture
async def mock_llm() -> MockLLMProvider: ...

@pytest_asyncio.fixture
async def mock_llm_with_responses(mock_llm: MockLLMProvider) -> MockLLMProvider: ...

@pytest_asyncio.fixture
async def mock_db() -> MockDatabase: ...

@pytest_asyncio.fixture
async def initialized_db(mock_db: MockDatabase) -> MockDatabase: ...
```

## Test Patterns

### Class-Based Tests (preferred)

```python
class TestMAKERConsensus:
    """Test MAKERConsensus class."""

    @pytest.fixture
    def basic_maker(self):
        """Create a basic MAKERConsensus instance."""
        return MAKERConsensus(ahead_by_k=2, min_votes=3)

    def test_start_consensus(self, basic_maker):
        """Test starting a consensus process."""
        basic_maker.start_consensus("test-decision")

        assert "test-decision" in basic_maker.active_processes
        assert basic_maker.process_states["test-decision"] == ConsensusState.GATHERING

    def test_add_vote(self, basic_maker):
        """Test adding a vote."""
        basic_maker.start_consensus("test")
        basic_maker.add_vote("test", "agent-1", "approve", 0.85)

        assert len(basic_maker.active_processes["test"]) == 1
```

### Async Tests

```python
@pytest.mark.asyncio
async def test_actor_spawn_and_terminate(test_actor):
    """Test actor lifecycle."""
    await test_actor.spawn()
    assert test_actor.state == ActorState.ACTIVE

    await test_actor.terminate()
    assert test_actor.state == ActorState.TERMINATED
```

### Error Handling Tests

```python
def test_init_invalid_mailbox_size():
    """Test that invalid mailbox size raises error."""
    with pytest.raises(ValueError, match="max_mailbox_size must be positive"):
        AgentActor(max_mailbox_size=0)
```

## Running Tests

```bash
# All tests
pytest tests/

# Specific directory
pytest tests/consensus/

# With coverage
pytest tests/ --cov=src --cov-report=term-missing

# Specific marker
pytest tests/ -m unit

# Parallel execution
pytest tests/ -n auto

# Verbose output
pytest tests/ -v

# Stop on first failure
pytest tests/ -x
```

## CI/CD Commands

From `CLAUDE.md`:
```bash
# Python verification
pytest tests/
ruff check src tests
mypy src

# Frontend verification
npm test
npm run lint
npm run build
```

---

*Testing analysis: 2026-04-13*