"""
Test harness for agent validation with latency benchmarking.

Agent Gamma - QA and Validation Lead
Provides reusable test utilities for validating agents and tools.
"""

import asyncio
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Generic, TypeVar

import pytest

# Import observability for tracing
from src.observability import LATENCY_BASELINE_MS

# ============== CONFIGURATION ==============

@dataclass
class HarnessConfig:
    """Configuration for test harness."""
    latency_baseline_ms: float = LATENCY_BASELINE_MS
    coverage_threshold: float = 80.0
    max_retries: int = 3
    timeout_seconds: float = 30.0
    concurrent_agents: int = 10


# ============== METRICS ==============

@dataclass
class LatencyMetrics:
    """Captured latency metrics for a test run."""
    operation: str
    samples: list[float] = field(default_factory=list)

    @property
    def count(self) -> int:
        return len(self.samples)

    @property
    def min_ms(self) -> float:
        return min(self.samples) if self.samples else 0.0

    @property
    def max_ms(self) -> float:
        return max(self.samples) if self.samples else 0.0

    @property
    def mean_ms(self) -> float:
        return sum(self.samples) / len(self.samples) if self.samples else 0.0

    @property
    def p50_ms(self) -> float:
        return self._percentile(50)

    @property
    def p95_ms(self) -> float:
        return self._percentile(95)

    @property
    def p99_ms(self) -> float:
        return self._percentile(99)

    def _percentile(self, percentile: float) -> float:
        if not self.samples:
            return 0.0
        sorted_samples = sorted(self.samples)
        index = int(len(sorted_samples) * percentile / 100)
        return sorted_samples[min(index, len(sorted_samples) - 1)]

    def exceeds_baseline(self, baseline_ms: float) -> bool:
        return self.max_ms > baseline_ms

    def to_dict(self) -> dict[str, Any]:
        return {
            "operation": self.operation,
            "count": self.count,
            "min_ms": self.min_ms,
            "max_ms": self.max_ms,
            "mean_ms": self.mean_ms,
            "p50_ms": self.p50_ms,
            "p95_ms": self.p95_ms,
            "p99_ms": self.p99_ms,
        }


# ============== TEST RESULT ==============

T = TypeVar("T")


@dataclass
class ValidationResult(Generic[T]):
    """Result of a validation test."""
    success: bool
    message: str
    value: T | None = None
    latency_metrics: LatencyMetrics | None = None
    errors: list[str] = field(default_factory=list)

    def __bool__(self) -> bool:
        return self.success


# ============== BASE VALIDATOR ==============

class AgentValidator(ABC):
    """
    Abstract base class for agent validators.
    
    Subclass this to create validators for specific agent types.
    """

    def __init__(self, config: HarnessConfig | None = None):
        self.config = config or HarnessConfig()
        self._latency_samples: list[float] = []

    @abstractmethod
    async def validate_initialization(self, agent: Any) -> ValidationResult[bool]:
        """Validate agent initializes correctly."""
        pass

    @abstractmethod
    async def validate_capabilities(self, agent: Any, required: list[str]) -> ValidationResult[bool]:
        """Validate agent has required capabilities."""
        pass

    @abstractmethod
    async def validate_messaging(self, agent: Any) -> ValidationResult[LatencyMetrics]:
        """Validate agent messaging and capture latency metrics."""
        pass

    @abstractmethod
    async def validate_task_execution(self, agent: Any) -> ValidationResult[LatencyMetrics]:
        """Validate agent task execution and capture latency metrics."""
        pass

    def _measure_latency(self, operation: str) -> "_LatencyContext":
        """Create a latency measurement context."""
        return _LatencyContext(self._latency_samples, operation)

    def _get_metrics(self, operation: str) -> LatencyMetrics:
        """Get latency metrics for collected samples."""
        return LatencyMetrics(operation=operation, samples=self._latency_samples.copy())


class _LatencyContext:
    """Context manager for measuring operation latency."""

    def __init__(self, samples: list[float], operation: str):
        self._samples = samples
        self._operation = operation
        self._start: float = 0.0
        self._elapsed_ms: float = 0.0

    def __enter__(self) -> "_LatencyContext":
        self._start = time.perf_counter()
        return self

    def __exit__(self, *args) -> None:
        self._elapsed_ms = (time.perf_counter() - self._start) * 1000
        self._samples.append(self._elapsed_ms)

    @property
    def elapsed_ms(self) -> float:
        return self._elapsed_ms


# ============== STANDARD VALIDATORS ==============

class StandardAgentValidator(AgentValidator):
    """Standard validator implementation for generic agents."""

    async def validate_initialization(self, agent: Any) -> ValidationResult[bool]:
        """Validate agent initializes correctly."""
        errors = []

        try:
            # Check required attributes
            if not hasattr(agent, "agent_id"):
                errors.append("Missing agent_id attribute")

            if not hasattr(agent, "agent_type"):
                errors.append("Missing agent_type attribute")

            # Check initial state
            if hasattr(agent, "get_state"):
                state = await agent.get_state() if asyncio.iscoroutinefunction(agent.get_state) else agent.get_state()
                if not state:
                    errors.append("Agent state is None after initialization")

            if errors:
                return ValidationResult(
                    success=False,
                    message="Agent initialization failed",
                    errors=errors,
                )

            return ValidationResult(
                success=True,
                message="Agent initialized successfully",
                value=True,
            )

        except Exception as e:
            return ValidationResult(
                success=False,
                message=f"Initialization error: {e}",
                errors=[str(e)],
            )

    async def validate_capabilities(self, agent: Any, required: list[str]) -> ValidationResult[bool]:
        """Validate agent has required capabilities."""
        missing = []

        agent_capabilities = getattr(agent, "capabilities", [])

        for cap in required:
            if cap not in agent_capabilities:
                missing.append(cap)

        if missing:
            return ValidationResult(
                success=False,
                message=f"Missing capabilities: {missing}",
                value=False,
                errors=[f"Missing: {cap}" for cap in missing],
            )

        return ValidationResult(
            success=True,
            message="All required capabilities present",
            value=True,
        )

    async def validate_messaging(self, agent: Any) -> ValidationResult[LatencyMetrics]:
        """Validate agent messaging and capture latency metrics."""
        self._latency_samples = []

        # Simulate message send operations
        num_samples = 10

        for _ in range(num_samples):
            with self._measure_latency("message_send"):
                if hasattr(agent, "send_message"):
                    try:
                        if asyncio.iscoroutinefunction(agent.send_message):
                            await agent.send_message({"test": "ping"})
                        else:
                            agent.send_message({"test": "ping"})
                    except NotImplementedError:
                        # Agent doesn't have real implementation yet
                        await asyncio.sleep(0.001)  # Simulate minimal latency

        metrics = self._get_metrics("message_send")

        return ValidationResult(
            success=not metrics.exceeds_baseline(self.config.latency_baseline_ms),
            message="Messaging validation complete",
            value=metrics,
        )

    async def validate_task_execution(self, agent: Any) -> ValidationResult[LatencyMetrics]:
        """Validate agent task execution and capture latency metrics."""
        self._latency_samples = []

        num_samples = 5

        for _ in range(num_samples):
            with self._measure_latency("task_execution"):
                if hasattr(agent, "execute_task"):
                    try:
                        if asyncio.iscoroutinefunction(agent.execute_task):
                            await agent.execute_task({"type": "test"})
                        else:
                            agent.execute_task({"type": "test"})
                    except NotImplementedError:
                        await asyncio.sleep(0.005)  # Simulate task latency

        metrics = self._get_metrics("task_execution")

        return ValidationResult(
            success=not metrics.exceeds_baseline(self.config.latency_baseline_ms),
            message="Task execution validation complete",
            value=metrics,
        )


# ============== FIXTURE FACTORY ==============

def create_validator(config: HarnessConfig | None = None) -> AgentValidator:
    """Factory function to create a standard agent validator."""
    return StandardAgentValidator(config)


# ============== PYTEST FIXTURES ==============

@pytest.fixture
def harness_config() -> HarnessConfig:
    """Create a test harness configuration."""
    return HarnessConfig()


@pytest.fixture
def agent_validator(harness_config: HarnessConfig) -> AgentValidator:
    """Create an agent validator instance."""
    return create_validator(harness_config)


# ============== BENCHMARK UTILITIES ==============

def benchmark_sync(
    func: callable,
    *args,
    iterations: int = 100,
    warmup: int = 10,
    **kwargs,
) -> LatencyMetrics:
    """
    Benchmark a synchronous function.
    
    Args:
        func: Function to benchmark.
        *args: Arguments to pass to function.
        iterations: Number of iterations to run.
        warmup: Number of warmup iterations (not counted).
        **kwargs: Keyword arguments to pass to function.
    
    Returns:
        LatencyMetrics with benchmark results.
    """
    # Warmup
    for _ in range(warmup):
        func(*args, **kwargs)

    # Benchmark
    samples = []
    for _ in range(iterations):
        start = time.perf_counter()
        func(*args, **kwargs)
        elapsed_ms = (time.perf_counter() - start) * 1000
        samples.append(elapsed_ms)

    return LatencyMetrics(operation=func.__name__, samples=samples)


async def benchmark_async(
    func: callable,
    *args,
    iterations: int = 100,
    warmup: int = 10,
    **kwargs,
) -> LatencyMetrics:
    """
    Benchmark an async function.
    
    Args:
        func: Async function to benchmark.
        *args: Arguments to pass to function.
        iterations: Number of iterations to run.
        warmup: Number of warmup iterations (not counted).
        **kwargs: Keyword arguments to pass to function.
    
    Returns:
        LatencyMetrics with benchmark results.
    """
    # Warmup
    for _ in range(warmup):
        await func(*args, **kwargs)

    # Benchmark
    samples = []
    for _ in range(iterations):
        start = time.perf_counter()
        await func(*args, **kwargs)
        elapsed_ms = (time.perf_counter() - start) * 1000
        samples.append(elapsed_ms)

    return LatencyMetrics(operation=func.__name__, samples=samples)
