# Testing Patterns

**Analysis Date:** 2026-04-15

## Test Framework

**Runner:**
- pytest 8.0+ with `asyncio_mode = "auto"`
- Configured in `pyproject.toml` under `[tool.pytest.ini_options]`

**Assertion Library:**
- pytest built-in assertions
- `pydantic.ValidationError` for model validation testing

**Mocking:**
- `unittest.mock.MagicMock` for sync mocks
- `unittest.mock.AsyncMock` for async mocks
- Custom in-memory mocks for NATS, LLM, Database

**Run Commands:**
```bash
pytest tests/                           # Run all tests
pytest tests/unit/                      # Unit tests only
pytest tests/integration/               # Integration tests
pytest tests/security/                  # Security tests
pytest -m "not slow"                   # Skip slow tests
pytest --cov=src --cov-report=html     # With coverage
```

## Test File Organization

**Location:**
- Unit tests: `tests/unit/`
- Integration tests: `tests/integration/`
- Security tests: `tests/security/`
- Validation tests: `tests/validation/`
- Gateway tests: `tests/gateway/`
- Consensus tests: `tests/consensus/`
- Actors tests: `tests/actors/`
- Observability tests: `tests/observability/`

**Naming:**
- Test files: `test_<module>.py` or `<feature>_test.py`
- Test classes: `Test<ComponentName>`
- Test functions: `test_<description_of_behavior>`

**Structure:**
```
tests/
├── conftest.py              # Root shared fixtures
├── unit/
│   ├── test_actor_factory.py
│   └── __init__.py
├── integration/
│   ├── conftest.py          # Integration-specific fixtures
│   ├── test_phase1_full_integration.py
│   ├── test_phase2_full_integration.py
│   ├── agents/
│   │   ├── test_alpha.py
│   │   ├── test_beta.py
│   │   └── ...
│   └── scaffolding/
│       ├── mocks.py
│       └── state.py
├── security/
│   ├── test_zero_trust.py
│   ├── test_sentinel.py
│   └── ...
├── validation/
│   ├── test_agent_messages.py
│   ├── test_llm_output_validator.py
│   └── ...
└── fixtures/
    ├── __init__.py
    └── test_data.py
```

## Test Types

**Unit Tests (`tests/unit/`):**
- Fast, isolated tests
- No external dependencies
- Mock all external calls
- Target: core logic, factories, validators

**Integration Tests (`tests/integration/`):**
- Test component interactions
- Use `MockNATSEventMesh`, `MockLLMProvider`, `MockDatabase`
- Test message passing between actors
- Test state persistence flows

**Security Tests (`tests/security/`):**
- Zero-trust validation layers
- Injection detection
- PII detection
- Secret patterns

**Validation Tests (`tests/validation/`):**
- Pydantic model validation
- Message type validation
- LLM output validation
- Agent message safety

**Gateway Tests (`tests/gateway/`):**
- NATS event mesh
- JetStream operations
- Message replay
- Content routing

**Consensus Tests (`tests/consensus/`):**
- MAKER protocol
- Deliberation engine
- Voting mechanisms
- Immune response

## Test Markers

**Configured Markers (from `pyproject.toml`):**
```python
markers = [
    "unit: Unit tests (fast, isolated)",
    "integration: Integration tests (require external services)",
    "load: Load/performance tests",
    "slow: Tests that take >5s",
    "a2a: Agent-to-Agent messaging tests",
    "consensus: Consensus mechanism tests",
    "latency: Latency benchmark tests (<100ms baseline)",
    "security: Security-focused tests",
]
```

**Usage:**
```bash
pytest -m unit                    # Run unit tests only
pytest -m "not slow"              # Exclude slow tests
pytest -m "security and not slow" # Security tests excluding slow
```

## Fixtures

### Root Fixtures (`tests/conftest.py`)

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
    # Returns list of 3 AgentConfig objects
```

**Message Fixtures:**
```python
@pytest.fixture
def sample_message(agent_id: str) -> Message:
    """Create a sample A2A message for testing."""
    return Message(
        message_id=f"msg-{uuid.uuid4().hex[:8]}",
        sender_id=agent_id,
        receiver_id="steward-primary",
        message_type="task_request",
        payload={"task": "analyze", "data": {"query": "test query"}},
    )

@pytest.fixture
def consensus_message() -> Message:
    """Create a consensus-related message for triad testing."""
```

**Mock Fixtures:**
```python
@pytest.fixture
def mock_agent() -> MagicMock:
    """Create a mock agent for isolated testing."""
    agent = MagicMock()
    agent.send_message = AsyncMock(return_value={"status": "sent"})
    agent.receive_message = AsyncMock()
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
        # ... more patterns
    ]

@pytest.fixture
def secret_patterns() -> list[str]:
    """Patterns that should never appear in logs or outputs."""
    return ["sk-", "xoxb-", "ghp_", "-----BEGIN", "password", "api_key"]
```

### Integration Fixtures (`tests/integration/conftest.py`)

**Mock NATS Event Mesh:**
```python
class MockNATSEventMesh:
    """In-memory mock for NATSEventMesh with pub/sub and request-reply patterns."""
    
    async def connect() -> bool
    async def publish(subject: str, data: dict, reply: str | None = None) -> bool
    async def subscribe(subject_pattern: str, callback: Callable) -> str
    async def request(subject: str, data: dict, timeout: int = 5) -> dict
```

**Mock LLM Provider:**
```python
class MockLLMProvider:
    """Mock LLM provider for deterministic testing."""
    
    def register_response(prompt_pattern: str, response: str) -> None
    def set_default_response(response: str) -> None
    async def generate(prompt: str, **kwargs) -> str
```

**Mock Database:**
```python
class MockDatabase:
    """In-memory mock database for testing."""
    
    async def connect() -> bool
    async def execute(query: str, params: tuple | None = None) -> list
    async def create_table(table_name: str, schema: dict) -> bool
```

**Latency Fixtures:**
```python
@pytest.fixture
def latency_tracker() -> dict[str, list[float]]:
    """Track operation latencies."""

@pytest.fixture
def assert_latency_baseline() -> Callable:
    """Assert latency meets baseline requirements (<100ms)."""
```

## Test Structure

**Class-Based Organization:**
```python
class TestActorMessage:
    """Tests for ActorMessage model."""
    
    def test_valid_actor_message(self):
        """Test creating a valid actor message."""
        msg = ActorMessage(
            content={"text": "Hello"},
            sender_id="agent1"
        )
        assert msg.sender_id == "agent1"
        assert msg.content == {"text": "Hello"}
    
    def test_actor_message_with_dangerous_content_fails(self):
        """Test that dangerous content in actor message fails."""
        with pytest.raises(ValidationError) as exc_info:
            ActorMessage(
                content={"code": "eval(user_input)"},
                sender_id="agent1"
            )
        assert "Unsafe content" in str(exc_info.value)
```

**Async Test Pattern:**
```python
class TestActorFactory:
    
    @pytest.mark.asyncio
    async def test_create_actor(self, factory):
        """Test creating an actor from registered configuration."""
        factory.register_actor_class(
            "mock-actor",
            MockAgentActor,
            {"agent_id": "test-instance", "name": "Test Actor"}
        )
        actor = factory.create_actor("mock-actor")
        assert actor.agent_id == "test-instance"
```

**Parameterized Tests:**
```python
@pytest.mark.parametrize("operation", ["set", "append", "delete", "merge", "increment", "decrement"])
def test_state_update_valid_operations(self, operation):
    """Test all valid operations."""
    update = StateUpdate(
        state_key="counter",
        state_value=1,
        sender_id="agent1",
        operation=operation
    )
    assert update.operation == operation
```

## Mocking Patterns

**NATS Module Mocking:**
```python
@pytest.fixture(autouse=True)
def mock_nats_module():
    """Mock NATS module to avoid pynats dependency issues."""
    mock_module = MagicMock()
    mock_module.NATSClient = MagicMock()
    mock_module.NATSPublisher = MagicMock()
    sys.modules["pynats"] = MagicMock()
    yield
    # Cleanup
    gc.collect()
```

**Actor Stub Patching:**
```python
# In heretek_swarm/actors/stubs.py
def get_llm_provider():
    return _llm_provider

# In tests
with patch("heretek_swarm.actors.stubs.get_llm_provider", return_value=mock_llm):
    actor = AgentActor(agent_id="test")
```

## Coverage Requirements

**Minimum Coverage:** 80% (`fail_under = 80` in coverage config)

**Coverage Configuration:**
```toml
[tool.coverage.run]
branch = true
source = ["src"]
omit = ["*/tests/*", "*/__pycache__/*", "*/.venv/*"]

[tool.coverage.report]
exclude_lines = [
    "pragma: no cover",
    "def __repr__",
    "raise NotImplementedError",
    "if __name__ == .__main__.:",
    "if TYPE_CHECKING:",
    "@abstractmethod",
]
```

**Run with Coverage:**
```bash
pytest --cov=src --cov-report=html --cov-report=term-missing
```

## Performance Baselines

**Message Latency:** <100ms baseline
```python
MESSAGE_LATENCY_BASELINE_MS = 100

@pytest.fixture
def assert_latency_baseline():
    def _assert(latency_ms: float, operation: str = "operation") -> None:
        assert latency_ms < MESSAGE_LATENCY_BASELINE_MS, (
            f"{operation} latency {latency_ms:.2f}ms exceeds "
            f"baseline of {MESSAGE_LATENCY_BASELINE_MS}ms"
        )
    return _assert
```

**Throughput:** >1000 validations/second for zero-trust validator

## Common Patterns

**Testing Pydantic Validation:**
```python
def test_invalid_uuid_fails():
    """Invalid UUID should fail validation."""
    with pytest.raises(ValidationError):
        ValidatedInput(request_id="not-a-uuid")

def test_extra_fields_forbidden():
    """Extra fields should be forbidden (injection protection)."""
    with pytest.raises(ValidationError):
        ValidatedInput(
            request_id=str(uuid.uuid4()),
            malicious_field="injection attempt",
        )
```

**Testing Async Actor Lifecycle:**
```python
@pytest.mark.asyncio
async def test_actor_spawn_and_terminate():
    """Test actor can spawn and terminate cleanly."""
    actor = MockAgentActor(agent_id="test")
    await actor.spawn()
    assert actor.state == ActorState.ACTIVE
    
    await actor.terminate()
    assert actor.state == ActorState.TERMINATED
```

**Testing Error Handling:**
```python
def test_validation_error_message(self):
    """Test that validation errors have helpful messages."""
    with pytest.raises(ValidationError) as exc_info:
        ActorMessage(content={"code": "eval(x)"}, sender_id="agent1")
    
    errors = exc_info.value.errors()
    assert len(errors) > 0
    assert "Unsafe content" in str(exc_info.value)
```

## Test Utilities

**Message Creation Helpers:**
```python
from heretek_swarm.validation.agent_messages import (
    create_actor_message,
    create_state_update,
    create_tool_request,
    create_tool_response,
)

def test_create_actor_message():
    msg = create_actor_message(
        content={"text": "hello"},
        sender_id="agent1",
        priority=MessagePriority.HIGH
    )
    assert msg.priority == MessagePriority.HIGH
```

**Reset Async State (autouse fixture):**
```python
@pytest.fixture(autouse=True)
def reset_async_state():
    """Reset async state between tests."""
    yield
    try:
        loop = asyncio.get_running_loop()
        pending = asyncio.all_tasks(loop)
        for task in pending:
            task.cancel()
    except RuntimeError:
        pass
```

## Integration Test Patterns

**Agent-to-Agent Messaging:**
```python
@pytest.mark.asyncio
async def test_agent_message_passing(mock_nats):
    """Test messages pass between agents via NATS."""
    await mock_nats.connect()
    
    # Agent 1 sends message
    await mock_nats.publish(
        "agent.2",
        {"message_type": "task", "content": "do work"},
        reply="agent.1.replies"
    )
    
    # Verify message was recorded
    assert len(mock_nats.published_messages) == 1
```

**Consensus Flow:**
```python
@pytest.mark.asyncio
async def test_deliberation_flow(triad_agents, mock_llm):
    """Test triad deliberation produces consensus."""
    # Setup triad with mock LLM
    # Initiate deliberation
    # Verify all three agents participate
    # Verify consensus reached
```

## Security Test Patterns

**Injection Detection:**
```python
def test_exec_injection_detected():
    """exec() injection pattern should be detected."""
    validator = InputValidator()
    result = validator.validate({
        "request_id": str(uuid.uuid4()),
        "content": "exec('malicious code')",
    })
    assert result.passed is False
    assert "exec" in result.reason.lower()

def test_sql_injection_detected():
    """SQL injection pattern should be detected."""
    result = validator.validate({
        "request_id": str(uuid.uuid4()),
        "content": "' OR '1'='1",
    })
    assert result.passed is False
```

**Secret Detection:**
```python
def test_api_key_detected():
    """API key pattern should be detected."""
    validator = OutputValidator()
    result = validator.validate("api_key=sk-1234567890abcdef")
    assert result.severity == Severity.WARNING
    assert result.details.get("sanitized") is True
```

---

*Testing analysis: 2026-04-15*
