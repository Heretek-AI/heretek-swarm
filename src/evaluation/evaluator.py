"""
Agent Evaluator - Comprehensive Agent Quality Evaluation Framework

Provides agent quality metrics, output validation, test case execution,
and performance benchmarking. Inspired by Harbor and RagaAI-Catalyst patterns.
"""

import asyncio
import logging
import time
from datetime import datetime
from typing import Any, Dict, List, Optional, Callable, Type
from dataclasses import dataclass, field
from enum import Enum

import structlog

logger = structlog.get_logger(__name__)


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
    input_data: Dict[str, Any]
    expected_output: Optional[Any] = None
    constraints: Optional["OutputConstraints"] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


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

    max_length: Optional[int] = None
    min_length: Optional[int] = None
    required_keys: List[str] = field(default_factory=list)
    forbidden_patterns: List[str] = field(default_factory=list)
    allowed_patterns: List[str] = field(default_factory=list)


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
    error: Optional[Exception] = None
    execution_time: float = 0.0
    validation_errors: List[str] = field(default_factory=list)


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
    completed_at: Optional[str] = None
    total_time: float = 0.0
    error: Optional[Exception] = None
    metrics: Optional[QualityMetrics] = None
    test_results: List[TestResult] = field(default_factory=list)


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
        evaluator = AgentEvaluator()

        # Create test cases
        test_cases = [
            TestCase(
                id="test-1",
                name="Basic query",
                input_data={"query": "What is 2+2?"},
                expected_output={"answer": "4"}
            )
        ]

        # Evaluate agent
        result = await evaluator.evaluate_agent(
            agent_id="my-agent",
            agent=my_agent,
            test_cases=test_cases
        )

        print(f"Success rate: {result.metrics.success_rate:.2%}")
        ```
    """

    def __init__(
        self,
        timeout: int = 30,
        parallel: bool = True,
    ):
        """
        Initialize evaluator.

        Args:
            timeout: Timeout for individual test cases (seconds)
            parallel: Whether to run tests in parallel
        """
        self.timeout = timeout
        self.parallel = parallel
        self._evaluations: Dict[str, EvaluationResult] = {}

        logger.info(
            "evaluator_initialized",
            timeout=timeout,
            parallel=parallel,
        )

    async def evaluate_agent(
        self,
        agent_id: str,
        agent: Any,
        test_cases: List[TestCase],
        evaluation_id: Optional[str] = None,
    ) -> EvaluationResult:
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
            evaluation_id = f"eval-{datetime.utcnow().strftime('%Y%m%d%H%M%S%f')}"

        started_at = datetime.utcnow().isoformat()
        start_time = time.time()

        logger.info(
            "evaluation_started",
            agent_id=agent_id,
            evaluation_id=evaluation_id,
            test_cases_count=len(test_cases),
        )

        # Execute test cases
        if self.parallel:
            test_results = await self._execute_parallel(agent, test_cases)
        else:
            test_results = await self._execute_sequential(agent, test_cases)

        # Calculate metrics
        metrics = self._calculate_metrics(test_results)

        completed_at = datetime.utcnow().isoformat()
        total_time = time.time() - start_time

        result = EvaluationResult(
            agent_id=agent_id,
            evaluation_id=evaluation_id,
            status=EvaluationStatus.COMPLETED,
            test_results=test_results,
            metrics=metrics,
            started_at=started_at,
            completed_at=completed_at,
            total_time=total_time,
        )

        self._evaluations[evaluation_id] = result

        logger.info(
            "evaluation_completed",
            agent_id=agent_id,
            evaluation_id=evaluation_id,
            success_rate=metrics.success_rate,
            total_time=total_time,
        )

        return result

    async def _execute_parallel(
        self,
        agent: Any,
        test_cases: List[TestCase],
    ) -> List[TestResult]:
        """Execute test cases in parallel."""
        tasks = [
            self._execute_test_case(agent, test_case)
            for test_case in test_cases
        ]
        return await asyncio.gather(*tasks, return_exceptions=True)

    async def _execute_sequential(
        self,
        agent: Any,
        test_cases: List[TestCase],
    ) -> List[TestResult]:
        """Execute test cases sequentially."""
        results = []
        for test_case in test_cases:
            result = await self._execute_test_case(agent, test_case)
            results.append(result)
        return results

    async def _execute_test_case(
        self,
        agent: Any,
        test_case: TestCase,
    ) -> TestResult:
        """Execute a single test case."""
        start_time = time.time()

        try:
            # Execute agent
            if hasattr(agent, "execute"):
                output = await asyncio.wait_for(
                    agent.execute(test_case.input_data),
                    timeout=self.timeout,
                )
            elif hasattr(agent, "run"):
                output = await asyncio.wait_for(
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
                test_case_id=test_case.id,
                success=success,
                output=output,
                expected=test_case.expected_output,
                execution_time=execution_time,
                validation_errors=validation_errors,
            )

        except asyncio.TimeoutError:
            execution_time = time.time() - start_time
            logger.warning(
                "test_case_timeout",
                test_case_id=test_case.id,
                timeout=self.timeout,
            )
            return TestResult(
                test_case_id=test_case.id,
                success=False,
                error=TimeoutError(f"Test case timed out after {self.timeout}s"),
                execution_time=execution_time,
                validation_errors=["Timeout"],
            )

        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(
                "test_case_failed",
                test_case_id=test_case.id,
                error=str(e),
            )
            return TestResult(
                test_case_id=test_case.id,
                success=False,
                error=e,
                execution_time=execution_time,
                validation_errors=[str(e)],
            )

    def _validate_output(
        self,
        output: Any,
        constraints: Optional[OutputConstraints],
    ) -> List[str]:
        """Validate output against constraints."""
        errors = []

        if constraints is None:
            return errors

        # Check length constraints
        output_str = str(output)
        if constraints.max_length is not None:
            if len(output_str) > constraints.max_length:
                errors.append(f"Output exceeds max length of {constraints.max_length}")

        if constraints.min_length is not None:
            if len(output_str) < constraints.min_length:
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
                errors.append(f"Output does not contain any allowed pattern")

        return errors

    def _calculate_metrics(self, test_results: List[TestResult]) -> QualityMetrics:
        """Calculate quality metrics from test results."""
        if not test_results:
            return QualityMetrics()

        # Success rate
        success_count = sum(1 for r in test_results if r.success)
        success_rate = (success_count / len(test_results)) * 100

        # Average execution time
        avg_time = sum(r.execution_time for r in test_results) / len(test_results)

        # Constraint compliance
        total_constraints = sum(
            1 for r in test_results if not r.validation_errors
        )
        constraint_compliance = (total_constraints / len(test_results)) * 100

        # Output quality (based on validation errors)
        total_errors = sum(len(r.validation_errors) for r in test_results)
        output_quality = max(0, 100 - (total_errors / len(test_results)) * 100)

        return QualityMetrics(
            success_rate=success_rate,
            response_time=avg_time,
            constraint_compliance=constraint_compliance,
            output_quality=output_quality,
        )

    def get_evaluation(self, evaluation_id: str) -> Optional[EvaluationResult]:
        """Get evaluation result by ID."""
        return self._evaluations.get(evaluation_id)

    def list_evaluations(self, agent_id: Optional[str] = None) -> List[EvaluationResult]:
        """List all evaluations, optionally filtered by agent."""
        evaluations = list(self._evaluations.values())
        if agent_id:
            return [e for e in evaluations if e.agent_id == agent_id]
        return evaluations

    def compare_agents(
        self,
        agent_evaluations: Dict[str, EvaluationResult],
    ) -> Dict[str, QualityMetrics]:
        """
        Compare multiple agents by their evaluation metrics.

        Args:
            agent_evaluations: Dict mapping agent_id to EvaluationResult

        Returns:
            Dict mapping agent_id to QualityMetrics
        """
        comparison = {}
        for agent_id, evaluation in agent_evaluations.items():
            if evaluation.metrics:
                comparison[agent_id] = evaluation.metrics
        return comparison


# Singleton evaluator instance
_evaluator_instance: Optional[AgentEvaluator] = None


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
