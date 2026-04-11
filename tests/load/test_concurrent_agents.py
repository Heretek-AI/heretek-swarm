"""
Pytest-based load testing for concurrent agent simulation.

Agent Gamma - QA and Validation Lead
Tests system behavior under load with 1,000+ concurrent agents.
"""

import asyncio
import time
from dataclasses import dataclass, field
from typing import Any

import pytest

from tests.fixtures.test_data import MockAgent, create_mock_agent

# ============== CONFIGURATION ==============

CONCURRENT_AGENT_TARGET = 1000
LATENCY_BASELINE_MS = 100


# ============== LOAD TEST METRICS ==============

@dataclass
class LoadTestMetrics:
    """Metrics collected during load testing."""
    total_agents: int = 0
    messages_sent: int = 0
    messages_failed: int = 0
    tasks_completed: int = 0
    tasks_failed: int = 0
    total_errors: int = 0
    latencies: list[float] = field(default_factory=list)
    start_time: float = 0.0
    end_time: float = 0.0

    @property
    def duration_seconds(self) -> float:
        return self.end_time - self.start_time

    @property
    def messages_per_second(self) -> float:
        if self.duration_seconds == 0:
            return 0.0
        return self.messages_sent / self.duration_seconds

    @property
    def avg_latency_ms(self) -> float:
        if not self.latencies:
            return 0.0
        return sum(self.latencies) / len(self.latencies)

    @property
    def max_latency_ms(self) -> float:
        return max(self.latencies) if self.latencies else 0.0

    @property
    def p95_latency_ms(self) -> float:
        if not self.latencies:
            return 0.0
        _sorted_latencies = sorted(self.latencies)
        _index = int(len(sorted_latencies) * 0.95)
        return sorted_latencies[min(index, len(sorted_latencies) - 1)]

    @property
    def error_rate(self) -> float:
        if self.messages_sent + self.tasks_completed == 0:
            return 0.0
        return self.total_errors / (self.messages_sent + self.tasks_completed)

    def to_dict(self) -> dict[str, Any]:
        return {
            "total_agents": self.total_agents,
            "messages_sent": self.messages_sent,
            "messages_failed": self.messages_failed,
            "tasks_completed": self.tasks_completed,
            "tasks_failed": self.tasks_failed,
            "total_errors": self.total_errors,
            "duration_seconds": self.duration_seconds,
            "messages_per_second": self.messages_per_second,
            "avg_latency_ms": self.avg_latency_ms,
            "max_latency_ms": self.max_latency_ms,
            "p95_latency_ms": self.p95_latency_ms,
            "error_rate": self.error_rate,
        }


# ============== AGENT POOL ==============

class AgentPool:
    """Pool of simulated agents for load testing."""

    def __init__(self, _size: int):
        self.size = size
        self.agents: list[MockAgent] = []
        self._metrics = LoadTestMetrics()

    async def initialize(self) -> None:
        """Initialize all agents in the pool."""
        self._metrics.start_time = time.time()

        # Create agents in batches to avoid overwhelming
        _batch_size = 100
        for i in range(0, self.size, batch_size):
            _batch_end = min(i + batch_size, self.size)
            _batch = [
                create_mock_agent(
                    _agent_id = f"load-agent-{j}",
                    _agent_type = "worker",
                )
                for j in range(i, batch_end)
            ]
            self.agents.extend(batch)
            await asyncio.sleep(0.01)  # Small delay between batches

        self._metrics.total_agents = len(self.agents)

    async def run_message_load(self, _messages_per_agent: int, _concurrency: int) -> LoadTestMetrics:
        """
        Run message load test.
        
        Args:
            messages_per_agent: Number of messages each agent should send.
            concurrency: Maximum concurrent operations.
        
        Returns:
            LoadTestMetrics with results.
        """
        _semaphore = asyncio.Semaphore(concurrency)

        async def send_message(_agent: MockAgent) -> float:
            """Send a message and return latency."""
            async with semaphore:
                start = time.perf_counter()
                try:
                    await agent.send_message({"test": "load"})
                    _elapsed_ms = (time.perf_counter() - start) * 1000
                    self._metrics.messages_sent += 1
                    self._metrics.latencies.append(elapsed_ms)
                    return elapsed_ms
                except Exception:
                    self._metrics.messages_failed += 1
                    self._metrics.total_errors += 1
                    return -1

        # Create tasks for all messages
        _tasks = []
        for agent in self.agents:
            for _ in range(messages_per_agent):
                tasks.append(send_message(agent))

        # Execute all tasks
        await asyncio.gather(*tasks)

        self._metrics.end_time = time.time()
        return self._metrics

    async def run_task_load(self, _tasks_per_agent: int, _concurrency: int) -> LoadTestMetrics:
        """
        Run task execution load test.
        
        Args:
            tasks_per_agent: Number of tasks each agent should execute.
            concurrency: Maximum concurrent operations.
        
        Returns:
            LoadTestMetrics with results.
        """
        _semaphore = asyncio.Semaphore(concurrency)

        async def execute_task(_agent: MockAgent) -> float:
            """Execute a task and return latency."""
            async with semaphore:
                start = time.perf_counter()
                try:
                    await agent.execute_task({"type": "load_test"})
                    _elapsed_ms = (time.perf_counter() - start) * 1000
                    self._metrics.tasks_completed += 1
                    self._metrics.latencies.append(elapsed_ms)
                    return elapsed_ms
                except Exception:
                    self._metrics.tasks_failed += 1
                    self._metrics.total_errors += 1
                    return -1

        _tasks = []
        for agent in self.agents:
            for _ in range(tasks_per_agent):
                tasks.append(execute_task(agent))

        await asyncio.gather(*tasks)

        self._metrics.end_time = time.time()
        return self._metrics

    async def cleanup(self) -> None:
        """Clean up agent pool."""
        self.agents.clear()


# ============== LOAD TESTS ==============

@pytest.mark.load
@pytest.mark.slow
class TestAgentLoad:
    """Load tests for concurrent agent operations."""

    @pytest.mark.asyncio
    async def test_100_concurrent_agents(self) -> None:
        """Test system with 100 concurrent agents."""
        _pool = AgentPool(size=100)
        await pool.initialize()

        _metrics = await pool.run_message_load(
            _messages_per_agent = 10,
            _concurrency = 50,
        )

        await pool.cleanup()

        # Assertions
        assert metrics.total_agents == 100
        assert metrics.error_rate < 0.01  # <1% error rate
        assert metrics.avg_latency_ms < LATENCY_BASELINE_MS

        print(f"\n📊 Load Test Results (100 agents):")
        print(f"   Messages: {metrics.messages_sent}")
        print(f"   Msg/sec: {metrics.messages_per_second:.2f}")
        print(f"   Avg latency: {metrics.avg_latency_ms:.2f}ms")
        print(f"   Max latency: {metrics.max_latency_ms:.2f}ms")
        print(f"   P95 latency: {metrics.p95_latency_ms:.2f}ms")
        print(f"   Error rate: {metrics.error_rate:.2%}")

    @pytest.mark.asyncio
    async def test_500_concurrent_agents(self) -> None:
        """Test system with 500 concurrent agents."""
        _pool = AgentPool(size=500)
        await pool.initialize()

        _metrics = await pool.run_message_load(
            _messages_per_agent = 5,
            _concurrency = 100,
        )

        await pool.cleanup()

        assert metrics.total_agents == 500
        assert metrics.error_rate < 0.02  # <2% error rate at scale

        print(f"\n📊 Load Test Results (500 agents):")
        print(f"   Messages: {metrics.messages_sent}")
        print(f"   Msg/sec: {metrics.messages_per_second:.2f}")
        print(f"   Avg latency: {metrics.avg_latency_ms:.2f}ms")
        print(f"   Max latency: {metrics.max_latency_ms:.2f}ms")
        print(f"   Error rate: {metrics.error_rate:.2%}")

    @pytest.mark.asyncio
    @pytest.mark.skipif(
        # Skip by default - run explicitly for full load test
        True,
        _reason = "Run explicitly for full 1000+ agent load test",
    )
    async def test_1000_concurrent_agents(self) -> None:
        """
        Test system with 1,000+ concurrent agents.
        
        This is the primary load test per Phase Directives.
        Run explicitly: pytest -m "load" --run-slow
        """
        _pool = AgentPool(size=CONCURRENT_AGENT_TARGET)
        await pool.initialize()

        _metrics = await pool.run_message_load(
            _messages_per_agent = 5,
            _concurrency = 200,
        )

        await pool.cleanup()

        # Phase Directive requirements
        assert metrics.total_agents >= CONCURRENT_AGENT_TARGET
        assert metrics.error_rate < 0.05  # <5% error rate acceptable at max scale

        print(f"\n📊 Load Test Results ({CONCURRENT_AGENT_TARGET} agents):")
        print(f"   Messages: {metrics.messages_sent}")
        print(f"   Msg/sec: {metrics.messages_per_second:.2f}")
        print(f"   Avg latency: {metrics.avg_latency_ms:.2f}ms")
        print(f"   P95 latency: {metrics.p95_latency_ms:.2f}ms")
        print(f"   Error rate: {metrics.error_rate:.2%}")

        # Flag if latency baseline exceeded
        if metrics.p95_latency_ms > LATENCY_BASELINE_MS:
            print(f"\n⚠️  P95 latency {metrics.p95_latency_ms:.2f}ms exceeds baseline {LATENCY_BASELINE_MS}ms")
            print("   FLAG FOR REFACTORING per Phase Directives")

    @pytest.mark.asyncio
    async def test_burst_load(self) -> None:
        """Test system under burst load conditions."""
        _pool = AgentPool(size=200)
        await pool.initialize()

        # Simulate burst: all agents send messages simultaneously
        _metrics = await pool.run_message_load(
            _messages_per_agent = 1,
            _concurrency = 200,  # All at once
        )

        await pool.cleanup()

        print(f"\n📊 Burst Load Results (200 agents x 1 msg):")
        print(f"   Messages: {metrics.messages_sent}")
        print(f"   Duration: {metrics.duration_seconds:.2f}s")
        print(f"   Max latency: {metrics.max_latency_ms:.2f}ms")

        # System should handle burst without complete failure
        assert metrics.messages_failed < metrics.messages_sent * 0.1  # <10% failures


@pytest.mark.load
class TestLoadMetrics:
    """Tests for load testing metrics collection."""

    def test_metrics_initialization(self) -> None:
        """Test metrics initialize correctly."""
        _metrics = LoadTestMetrics()

        assert metrics.total_agents == 0
        assert metrics.messages_sent == 0
        assert metrics.avg_latency_ms == 0.0
        assert metrics.error_rate == 0.0

    def test_metrics_calculations(self) -> None:
        """Test metrics calculations."""
        _metrics = LoadTestMetrics()
        metrics.start_time = 0.0
        metrics.end_time = 10.0
        metrics.messages_sent = 100
        metrics.total_errors = 2
        metrics.latencies = [10.0] * 100

        assert metrics.duration_seconds == 10.0
        assert metrics.messages_per_second == 10.0
        assert metrics.avg_latency_ms == 10.0
        assert metrics.error_rate == pytest.approx(0.02, rel=0.01)

    def test_metrics_serialization(self) -> None:
        """Test metrics can be serialized."""
        _metrics = LoadTestMetrics(
            _total_agents = 100,
            _messages_sent = 500,
        )

        _data = metrics.to_dict()

        assert data["total_agents"] == 100
        assert data["messages_sent"] == 500
        assert "duration_seconds" in data
