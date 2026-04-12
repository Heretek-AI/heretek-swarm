"""
Pytest configuration and fixtures for Heretek Swarm test suite.

Agent Gamma - QA and Validation Lead
Enforces >80% test coverage and <100ms message latency baseline.
"""

import asyncio
import sys
import time
import uuid
from collections.abc import AsyncGenerator, Generator
from dataclasses import dataclass, field
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest
import pytest_asyncio
from pydantic import BaseModel

# =============================================================================
# PRE-COLLECTION FIXTURES
# These run before test collection to set up module-level mocks
# =============================================================================

def pytest_configure(config: pytest.Config) -> None:
    """Configure pytest before test collection."""
    # Mock pynats module to avoid import errors for NATS dependencies
    if 'pynats' not in sys.modules:
        mock_pynats = MagicMock()
        sys.modules['pynats'] = mock_pynats

# ============== CONFIGURATION ==============

# Performance baselines per Phase Directives
MESSAGE_LATENCY_BASELINE_MS = 100  # <100ms message latency requirement
CONCURRENT_AGENT_TARGET = 1000  # Must support 1,000+ concurrent agents
COVERAGE_THRESHOLD = 80  # >80% test coverage requirement


# ============== TEST MARKERS ==============

def pytest_configure(config: pytest.Config) -> None:
    """Configure custom pytest markers."""
    config.addinivalue_line(
        "markers", "unit: Unit tests (fast, isolated, no external dependencies)"
    )
    config.addinivalue_line(
        "markers", "integration: Integration tests (require external services)"
    )
    config.addinivalue_line(
        "markers", "load: Load/performance tests for scalability validation"
    )
    config.addinivalue_line(
        "markers", "slow: Tests that take >5 seconds to complete"
    )
    config.addinivalue_line(
        "markers", "a2a: Agent-to-Agent messaging tests"
    )
    config.addinivalue_line(
        "markers", "consensus: Consensus mechanism tests (MAKER, BFT)"
    )
    config.addinivalue_line(
        "markers", "latency: Latency benchmark tests (<100ms baseline)"
    )
    config.addinivalue_line(
        "markers", "security: Security-focused tests (input validation, secrets)"
    )


# ============== MODELS ==============

@dataclass
class AgentConfig:
    """Configuration for a test agent."""
    agent_id: str
    agent_type: str
    capabilities: list[str] = field(default_factory=list)
    reputation: float = 1.0
    max_concurrent_tasks: int = 10


class Message(BaseModel):
    """A2A message model for testing."""
    message_id: str
    sender_id: str
    receiver_id: str
    message_type: str
    payload: dict[str, Any]
    timestamp: float = field(default_factory=time.time)
    correlation_id: str | None = None
    latency_ms: float | None = None


class AgentState(BaseModel):
    """Agent state model for testing."""
    agent_id: str
    status: str = "idle"
    current_task: str | None = None
    memory_context: dict[str, Any] = {}
    last_heartbeat: float = field(default_factory=time.time)


# ============== EVENT LOOP ==============

@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create an event loop for async tests."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


# ============== AGENT FIXTURES ==============

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
        AgentConfig(
            agent_id="alpha-primary",
            agent_type="triad",
            capabilities=["deliberation", "consensus", "leadership"],
            reputation=0.95,
        ),
        AgentConfig(
            agent_id="beta-primary",
            agent_type="triad",
            capabilities=["critique", "analysis", "consensus"],
            reputation=0.90,
        ),
        AgentConfig(
            agent_id="charlie-primary",
            agent_type="triad",
            capabilities=["validation", "arbitration", "consensus"],
            reputation=0.92,
        ),
    ]


@pytest.fixture
def steward_config() -> AgentConfig:
    """Create Steward (orchestrator) configuration for testing."""
    return AgentConfig(
        agent_id="steward-primary",
        agent_type="orchestrator",
        capabilities=[
            "orchestration",
            "final_authorization",
            "task_delegation",
            "workflow_management",
        ],
        reputation=1.0,
        max_concurrent_tasks=100,
    )


# ============== MESSAGE FIXTURES ==============

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
    return Message(
        message_id=f"consensus-{uuid.uuid4().hex[:8]}",
        sender_id="alpha-primary",
        receiver_id="beta-primary",
        message_type="deliberation_vote",
        payload={
            "proposal_id": "prop-123",
            "vote": "approve",
            "reasoning": "Meets all acceptance criteria",
        },
        correlation_id="deliberation-session-456",
    )


# ============== MOCK FIXTURES ==============

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


# ============== LATENCY FIXTURES ==============

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


# ============== INFRASTRUCTURE MOCKS ==============

@pytest.fixture(autouse=True)
def mock_nats_module():
    """Mock NATS module to avoid pynats dependency issues."""
    import sys
    from unittest.mock import MagicMock

    # Create mock NATS classes
    mock_nats_client = MagicMock()
    mock_nats_publisher = MagicMock()
    mock_nats_subscriber = MagicMock()

    # Create mock module
    mock_module = MagicMock()
    mock_module.NATSClient = mock_nats_client
    mock_module.NATSPublisher = mock_nats_publisher
    mock_module.NATSSubscriber = mock_nats_subscriber
    mock_module.get_nats_client = MagicMock(return_value=mock_nats_client)

    # Also mock any submodules
    sys.modules['pynats'] = MagicMock()

    yield

    # Cleanup
    if 'pynats' in sys.modules:
        del sys.modules['pynats']


# ============== ASYNC FIXTURES ==============

@pytest_asyncio.fixture
async def async_agent_pool() -> AsyncGenerator[list[MagicMock], None]:
    """Create a pool of async mock agents for load testing."""
    agents = []
    for i in range(10):
        agent = MagicMock()
        agent.agent_id = f"pool-agent-{i}"
        agent.execute_task = AsyncMock(return_value={"result": f"task-{i}"})
        agents.append(agent)
    yield agents


# ============== SECURITY FIXTURES ==============

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
        {"input": None, "type": "null_injection"},
        {"input": "", "type": "empty_string"},
    ]


@pytest.fixture
def secret_patterns() -> list[str]:
    """Patterns that should never appear in logs or outputs."""
    return [
        "sk-",  # OpenAI API keys
        "xoxb-",  # Slack tokens
        "ghp_",  # GitHub personal access tokens
        "AKIA",  # AWS access keys
        "eyJ",  # JWT tokens (start)
        "-----BEGIN",  # PEM keys
        "password",
        "secret",
        "api_key",
    ]


# ============== CLEANUP ==============

@pytest.fixture(autouse=True)
def reset_mock_state():
    """Reset mock state between tests."""
    yield
    # Cleanup happens automatically after yield
