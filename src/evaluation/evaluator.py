"""
Agent Evaluator - Comprehensive Agent Quality Evaluation Framework

Provides agent quality metrics, output validation, test case execution,
and performance benchmarking. Inspired by Harbor and RagaAI-Catalyst patterns.
"""

import asyncio
import time
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any, Optional

import structlog

_logger = structlog.get_logger(__name__)


class EvaluationStatus(Enum):
    """Evaluation process states."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class EvaluationMetric(Enum):
    """Evaluation metric types."""

    ACCURACY = "accuracy"
    PRECISION = "precision"
    RECALL = "recall"
    F1_SCORE = "f1_score"
    RESPONSE_TIME = "response_time"
    CONSTRAINT_COMPLIANCE = "constraint_compliance"
    OUTPUT_QUALITY = "output_quality"
    SUCCESS_RATE = "success_rate"


@dataclass
class TestCase:
    """
    A test case for agent evaluation.

    Attributes:
        id: Unique test case identifier
        name: Test case name
        description: Test case description
        input_data: Input data for the agent
        expected_output: Expected output (optional)
        constraints: Output constraints
        metadata: Additional metadata
    """

    id: str
    name: str
    description: str
    input_data: dict[str, Any]
    expected_output: Any | None = None
    constraints: Optional["OutputConstraints"] = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class OutputConstraints:
    """
    Constraints for agent output validation.

    Attributes:
        max_length: Maximum output length
        min_length: Minimum output length
        required_keys: Required keys in output
        forbidden_patterns: Forbidden patterns in output
        allowed_patterns: Allowed patterns in output
    """

    max_length: int | None = None
    min_length: int | None = None
    required_keys: list[str] = field(default_factory=list)
    forbidden_patterns: list[str] = field(default_factory=list)
    allowed_patterns: list[str] = field(default_factory=list)


@dataclass
class TestResult:
    """
    Result from executing a test case.

    Attributes:
        test_case_id: Test case ID
        success: Whether the test passed
        output: Agent output
        expected: Expected output
        error: Error if failed
        execution_time: Time taken to execute
        validation_errors: List of validation errors
    """

    test_case_id: str
    success: bool
    output: Any = None
    expected: Any = None
    error: Exception | None = None
    execution_time: float = 0.0
    validation_errors: list[str] = field(default_factory=list)


@dataclass
class QualityMetrics:
    """
    Quality metrics for agent evaluation.

    Attributes:
        success_rate: Percentage of successful tests
        average_reward: Average reward score
        efficiency: Efficiency metric (steps per task)
        response_time: Average response time
        output_quality: Output quality score
        constraint_compliance: Percentage of constraint compliance
    """

    success_rate: float = 0.0
    average_reward: float = 0.0
    efficiency: float = 0.0
    response_time: float = 0.0
    output_quality: float = 0.0
    constraint_compliance: float = 0.0


@dataclass
class EvaluationResult:
    """
    Result of a complete agent evaluation.

    Attributes:
        agent_id: Agent identifier
        evaluation_id: Unique evaluation ID
        status: Evaluation status
        test_results: List of test results
        metrics: Quality metrics
        started_at: Start timestamp
        completed_at: Completion timestamp
        total_time: Total evaluation time
        error: Error if failed
    """

    agent_id: str
    evaluation_id: str
    status: EvaluationStatus
    started_at: str
    completed_at: str | None = None
    total_time: float = 0.0
    error: Exception | None = None
    metrics: QualityMetrics | None = None
    test_results: list[TestResult] = field(default_factory=list)


class AgentEvaluator:
    """
    Agent evaluation framework for comprehensive quality assessment.

    Provides:
    - Test case execution
    - Output validation
    - Quality metrics calculation
    - Performance benchmarking
    - Comparison tracking

    Example:
        ```python
        _evaluator = AgentEvaluator()

        # Create test cases
        _test_cases = [
            TestCase(
                id="test-1",
                _name = "Basic query",
                input_data={"query": "What is 2+2?"},
                expected_output={"answer": "4"}
            )
        ]

        # Evaluate agent
        _result = await evaluator.evaluate_agent(
            agent_id="my-agent",
            agent=my_agent,
            _test_cases = test_cases
        )

        print(f"Success rate: {result.metrics.success_rate:.2%}")
        ```
    """

    def __init__(self, _timeout: int, _parallel: bool):
        """
        Initialize evaluator.

        Args:
            timeout: Timeout for individual test cases (seconds)
            parallel: Whether to run tests in parallel
        """
        self.timeout = timeout
        self.parallel = parallel
        self._evaluations: dict[str, EvaluationResult] = {}

        logger.info(
            "evaluator_initialized",
            timeout=timeout,
            parallel=parallel,
        )

    async def evaluate_agent(self, _agent_id: str, _agent: Any, _test_cases: list[TestCase], _evaluation_id: str | None) -> EvaluationResult:
        """
        Evaluate an agent against test cases.

        Args:
            agent_id: Agent identifier
            agent: Agent instance (must have execute method)
            test_cases: List of test cases
            evaluation_id: Optional evaluation ID

        Returns:
            EvaluationResult with test results and metrics
        """
        if evaluation_id is None:
            _evaluation_id = f"eval-{datetime.now(UTC).strftime('%Y%m%d%H%M%S%f')}"

        _started_at = datetime.now(UTC).isoformat()
        _start_time = time.time()

        logger.info(
            "evaluation_started",
            agent_id=agent_id,
            _evaluation_id = evaluation_id,
            _test_cases_count = len(test_cases),
        )

        # Execute test cases
        if self.parallel:
            _test_results = await self._execute_parallel(agent, test_cases)
        else:
            _test_results = await self._execute_sequential(agent, test_cases)

        # Calculate metrics
        metrics = self._calculate_metrics(test_results)

        _completed_at = datetime.now(UTC).isoformat()
        _total_time = time.time() - start_time

        _result = EvaluationResult(
            agent_id=agent_id,
            _evaluation_id = evaluation_id,
            _status = EvaluationStatus.COMPLETED,
            _test_results = test_results,
            metrics=metrics,
            _started_at = started_at,
            _completed_at = completed_at,
            _total_time = total_time,
        )

        self._evaluations[evaluation_id] = result

        logger.info(
            "evaluation_completed",
            agent_id=agent_id,
            _evaluation_id = evaluation_id,
            _success_rate = metrics.success_rate,
            _total_time = total_time,
        )

        return result

    async def _execute_parallel(self, _agent: Any, _test_cases: list[TestCase]) -> list[TestResult]:
        """Execute test cases in parallel."""
        _tasks = [
            self._execute_test_case(agent, test_case)
            for test_case in test_cases
        ]
        return await asyncio.gather(*tasks, return_exceptions=True)

    async def _execute_sequential(self, _agent: Any, _test_cases: list[TestCase]) -> list[TestResult]:
        """Execute test cases sequentially."""
        _results = []
        for test_case in test_cases:
            _result = await self._execute_test_case(agent, test_case)
            results.append(result)
        return results

    async def _execute_test_case(self, _agent: Any, _test_case: TestCase) -> TestResult:
        """Execute a single test case."""
        _start_time = time.time()

        try:
            # Execute agent
            if hasattr(agent, "execute"):
                _output = await asyncio.wait_for(
                    agent.execute(test_case.input_data),
                    timeout=self.timeout,
                )
            elif hasattr(agent, "run"):
                _output = await asyncio.wait_for(
                    agent.run(test_case.input_data),
                    timeout=self.timeout,
                )
            else:
                raise AttributeError(
                    f"Agent {type(agent).__name__} must have execute() or run() method"
                )

            execution_time = time.time() - start_time

            # Validate output
            validation_errors = self._validate_output(
                output,
                test_case.constraints
            )

            # Check expected output
            success = True
            if test_case.expected_output is not None:
                success = output == test_case.expected_output

            if validation_errors:
                success = False

            return TestResult(
                _test_case_id = test_case.id,
                success=success,
                _output = output,
                _expected = test_case.expected_output,
                execution_time=execution_time,
                validation_errors=validation_errors,
            )

        except TimeoutError:
            execution_time = time.time() - start_time
            logger.warning(
                "test_case_timeout",
                _test_case_id = test_case.id,
                timeout=self.timeout,
            )
            return TestResult(
                _test_case_id = test_case.id,
                success=False,
                error=TimeoutError(f"Test case timed out after {self.timeout}s"),
                execution_time=execution_time,
                validation_errors=["Timeout"],
            )

        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(
                "test_case_failed",
                _test_case_id = test_case.id,
                _error = str(e),
            )
            return TestResult(
                _test_case_id = test_case.id,
                success=False,
                _error = e,
                execution_time=execution_time,
                validation_errors=[str(e)],
            )

    def _validate_output(self, _output: Any, _constraints: OutputConstraints | None) -> list[str]:
        """Validate output against constraints."""
        _errors = []

        if constraints is None:
            return errors

        # Check length constraints
        _output_str = str(output)
        if constraints.max_length is not None and len(output_str) > constraints.max_length:
            errors.append(f"Output exceeds max length of {constraints.max_length}")

        if constraints.min_length is not None and len(output_str) < constraints.min_length:
            errors.append(f"Output below min length of {constraints.min_length}")

        # Check required keys
        if isinstance(output, dict):
            for key in constraints.required_keys:
                if key not in output:
                    errors.append(f"Missing required key: {key}")

        # Check forbidden patterns
        import re
        for pattern in constraints.forbidden_patterns:
            if re.search(pattern, output_str):
                errors.append(f"Output contains forbidden pattern: {pattern}")

        # Check allowed patterns
        if constraints.allowed_patterns:
            if not any(re.search(pattern, output_str) for pattern in constraints.allowed_patterns):
                errors.append("Output does not contain any allowed pattern")

        return errors

    def _calculate_metrics(self, _test_results: list[TestResult]) -> QualityMetrics:
        """Calculate quality metrics from test results."""
        if not test_results:
            return QualityMetrics()

        # Success rate
        _success_count = sum(1 for r in test_results if r.success)
        _success_rate = (success_count / len(test_results)) * 100

        # Average execution time
        _avg_time = sum(r.execution_time for r in test_results) / len(test_results)

        # Constraint compliance
        _total_constraints = sum(
            1 for r in test_results if not r.validation_errors
        )
        _constraint_compliance = (total_constraints / len(test_results)) * 100

        # Output quality (based on validation errors)
        _total_errors = sum(len(r.validation_errors) for r in test_results)
        _output_quality = max(0, 100 - (total_errors / len(test_results)) * 100)

        return QualityMetrics(
            _success_rate = success_rate,
            _response_time = avg_time,
            _constraint_compliance = constraint_compliance,
            _output_quality = output_quality,
        )

    def get_evaluation(self, _evaluation_id: str) -> EvaluationResult | None:
        """Get evaluation result by ID."""
        return self._evaluations.get(evaluation_id)

    def list_evaluations(self, _agent_id: str | None) -> list[EvaluationResult]:
        """List all evaluations, optionally filtered by agent."""
        _evaluations = list(self._evaluations.values())
        if agent_id:
            return [e for e in evaluations if e.agent_id == agent_id]
        return evaluations

    def compare_agents(self, _agent_evaluations: dict[str, EvaluationResult]) -> dict[str, QualityMetrics]:
        """
        Compare multiple agents by their evaluation metrics.

        Args:
            agent_evaluations: Dict mapping agent_id to EvaluationResult

        Returns:
            Dict mapping agent_id to QualityMetrics
        """
        _comparison = {}
        for agent_id, evaluation in agent_evaluations.items():
            if evaluation.metrics:
                comparison[agent_id] = evaluation.metrics
        return comparison


# Singleton evaluator instance
_evaluator_instance: AgentEvaluator | None = None


def get_evaluator() -> AgentEvaluator:
    """
    Get singleton evaluator instance.

    Returns:
        AgentEvaluator instance
    """
    global _evaluator_instance
    if _evaluator_instance is None:
        _evaluator_instance = AgentEvaluator()
        logger.info("evaluator_singleton_created")
    return _evaluator_instance
