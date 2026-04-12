"""Agent Evaluator Framework for testing agent quality."""
import asyncio
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


class EvaluationStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class OutputConstraints:
    max_tokens: int = 1000
    format: str = "text"
    max_length: Optional[int] = None
    required_keys: Optional[List[str]] = None
    forbidden_patterns: Optional[List[str]] = None
    schema: Optional[Dict[str, Any]] = None


@dataclass
class TestCase:
    id: str
    name: str
    description: str = ""
    input_data: Dict[str, Any] = field(default_factory=dict)
    expected_output: Optional[Dict[str, Any]] = None
    constraints: Optional[OutputConstraints] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class EvaluationResult:
    evaluation_id: str
    agent_id: str
    status: EvaluationStatus
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    total_time: float = 0.0
    metrics: Optional["EvaluationMetrics"] = None
    test_results: Optional[List["TestResult"]] = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "evaluation_id": self.evaluation_id,
            "agent_id": self.agent_id,
            "status": self.status.value,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "total_time": self.total_time,
            "metrics": self.metrics.to_dict() if self.metrics else None,
        }


@dataclass 
class EvaluationMetrics:
    success_rate: float = 0.0
    constraint_compliance: float = 0.0
    output_quality: float = 0.0
    latency_ms: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "success_rate": self.success_rate,
            "constraint_compliance": self.constraint_compliance,
            "output_quality": self.output_quality,
            "latency_ms": self.latency_ms,
        }


@dataclass
class TestResult:
    test_id: str
    success: bool
    error: Optional[Any] = None
    validation_errors: Optional[List[str]] = None
    execution_time_ms: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "test_id": self.test_id,
            "success": self.success,
            "error": str(self.error) if self.error else None,
            "validation_errors": self.validation_errors or [],
            "execution_time_ms": self.execution_time_ms,
        }


class AgentEvaluator:
    """Agent evaluation framework."""

    def __init__(self, timeout: float = 30.0, parallel: bool = True):
        self.timeout = timeout
        self.parallel = parallel
        self.results: List[EvaluationResult] = []
        self._evaluations: Dict[str, EvaluationResult] = {}

    async def evaluate_agent(
        self,
        agent_id: str,
        agent: Any,
        test_cases: List[TestCase],
        evaluation_id: Optional[str] = None,
    ) -> EvaluationResult:
        """Evaluate an agent against test cases.
        
        Args:
            agent_id: The agent identifier
            agent: The agent instance to evaluate
            test_cases: List of test cases to run
            evaluation_id: Optional evaluation ID
            
        Returns:
            EvaluationResult with test results and metrics
        """
        eval_id = evaluation_id or f"eval_{agent_id}_{datetime.now().timestamp()}"
        started = datetime.now().isoformat()
        
        test_results = []
        passed_count = 0
        
        for tc in test_cases:
            start = datetime.now()
            error = None
            validation_errors = []
            
            try:
                # Execute agent with timeout
                input_data = tc.input_data if isinstance(tc.input_data, dict) else {"query": tc.input_data}
                output = await asyncio.wait_for(
                    agent.execute(input_data),
                    timeout=self.timeout
                )
                
                # Validate output against expected output first
                if tc.expected_output is not None:
                    validation_errors.extend(self._validate_expected_output(output, tc.expected_output))
                
                # Validate output against constraints
                if tc.constraints:
                    validation_errors.extend(self._validate_constraints(output, tc.constraints))
                
                success = len(validation_errors) == 0
                
                if success:
                    passed_count += 1
                    
            except asyncio.TimeoutError as e:
                error = e
                validation_errors = [f"Execution timeout after {self.timeout}s"]
                success = False
            except Exception as e:
                error = e
                validation_errors = [str(e)]
                success = False
            
            end = datetime.now()
            execution_time = (end - start).total_seconds() * 1000
            
            test_results.append(TestResult(
                test_id=tc.id,
                success=success,
                error=error,
                validation_errors=validation_errors if validation_errors else None,
                execution_time_ms=execution_time,
            ))
        
        # Calculate metrics
        total = len(test_cases)
        success_rate = (passed_count / total * 100) if total > 0 else 0.0
        
        metrics = EvaluationMetrics(
            success_rate=success_rate,
            constraint_compliance=success_rate,
            output_quality=success_rate,
        )
        
        completed = datetime.now().isoformat()
        
        result = EvaluationResult(
            evaluation_id=eval_id,
            agent_id=agent_id,
            status=EvaluationStatus.COMPLETED,
            started_at=started,
            completed_at=completed,
            total_time=(datetime.fromisoformat(completed) - datetime.fromisoformat(started)).total_seconds(),
            metrics=metrics,
            test_results=test_results,
        )
        
        self.results.append(result)
        self._evaluations[eval_id] = result
        return result

    def _validate_expected_output(self, output: Any, expected: Dict[str, Any]) -> List[str]:
        """Validate output against expected output."""
        errors = []
        if isinstance(expected, dict) and isinstance(output, dict):
            for key, value in expected.items():
                if key not in output:
                    errors.append(f"Missing expected key: {key}")
                elif output[key] != value:
                    errors.append(f"Expected {key}={value}, got {output[key]}")
        return errors

    def _validate_constraints(self, output: Any, constraints: OutputConstraints) -> List[str]:
        """Validate output against constraints."""
        errors = []
        
        # Check required keys
        if constraints.required_keys and isinstance(output, dict):
            for key in constraints.required_keys:
                if key not in output:
                    errors.append(f"Missing required key: {key}")
        
        # Check max length
        if hasattr(constraints, 'max_length') and constraints.max_length:
            output_str = str(output)
            if len(output_str) > constraints.max_length:
                errors.append(f"Output exceeds max length: {len(output_str)} > {constraints.max_length}")
        
        # Check forbidden patterns
        if constraints.forbidden_patterns and isinstance(output, str):
            import re
            for pattern in constraints.forbidden_patterns:
                if re.search(pattern, output):
                    errors.append("forbidden pattern detected in output")
        
        return errors

    def _validate_output(self, output: Any, test_case: TestCase) -> List[str]:
        """Validate agent output against test case constraints."""
        errors = []
        
        if test_case.constraints is None:
            return errors
            
        return self._validate_constraints(output, test_case.constraints)

    def get_evaluation(self, evaluation_id: str) -> Optional[EvaluationResult]:
        """Get evaluation by ID."""
        return self._evaluations.get(evaluation_id)

    def list_evaluations(self) -> List[EvaluationResult]:
        """List all evaluations."""
        return list(self._evaluations.values())

    def compare_agents(
        self,
        results: Dict[str, EvaluationResult]
    ) -> Dict[str, EvaluationMetrics]:
        """Compare evaluation results across agents."""
        comparison = {}
        for agent_id, result in results.items():
            if result.metrics:
                comparison[agent_id] = result.metrics
        return comparison

    def get_stats(self) -> Dict[str, Any]:
        """Get evaluation statistics."""
        total = len(self.results)
        passed = sum(1 for r in self.results if r.status == EvaluationStatus.PASSED)
        return {
            "total": total,
            "passed": passed,
            "failed": total - passed,
            "pass_rate": passed / total if total > 0 else 0.0
        }
