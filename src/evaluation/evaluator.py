"""
Evaluation Framework - Agent Quality Assessment

Inspired by Google ADK Evaluator (18.7k stars)
Provides comprehensive agent quality metrics and evaluation.
"""

import asyncio
import json
from datetime import datetime
from typing import Any, Dict, List, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum

import structlog

logger = structlog.get_logger(__name__)


class EvaluationMetric(Enum):
    """Types of evaluation metrics."""
    
    # Response quality
    RELEVANCE = "relevance"
    ACCURACY = "accuracy"
    COMPLETENESS = "completeness"
    COHERENCE = "coherence"
    
    # Performance
    LATENCY = "latency"
    TOKEN_EFFICIENCY = "token_efficiency"
    
    # Safety
    SAFETY = "safety"
    PII_DETECTION = "pii_detection"
    
    # Reliability
    SUCCESS_RATE = "success_rate"
    ERROR_RATE = "error_rate"


class EvaluationStatus(Enum):
    """Evaluation status."""
    
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class EvaluationResult:
    """Result of a single evaluation."""
    
    metric: EvaluationMetric
    score: float  # 0.0 to 1.0
    details: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())


@dataclass
class TestCase:
    """A test case for evaluation."""
    
    id: str
    name: str
    description: str
    input_data: Dict[str, Any]
    expected_output: Optional[Dict[str, Any]] = None
    evaluation_criteria: List[EvaluationMetric] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TestExecution:
    """Execution of a test case."""
    
    test_case: TestCase
    agent_id: str
    status: EvaluationStatus
    start_time: str
    end_time: Optional[str] = None
    results: List[EvaluationResult] = field(default_factory=list)
    output: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class Evaluator:
    """
    Agent quality evaluator.
    
    Evaluates agents on multiple dimensions:
    - Response quality (relevance, accuracy, completeness, coherence)
    - Performance (latency, token efficiency)
    - Safety (safety, PII detection)
    - Reliability (success rate, error rate)
    """
    
    def __init__(self):
        """Initialize evaluator."""
        self.test_cases: Dict[str, TestCase] = {}
        self.executions: List[TestExecution] = []
        self._lock = asyncio.Lock()
    
    def load_test_cases(self, test_cases: List[TestCase]) -> None:
        """
        Load test cases for evaluation.
        
        Args:
            test_cases: List of test cases
        """
        for test_case in test_cases:
            self.test_cases[test_case.id] = test_case
        
        logger.info("test_cases_loaded", count=len(test_cases))
    
    async def evaluate_agent(
        self,
        agent_id: str,
        test_case_ids: Optional[List[str]] = None
    ) -> List[TestExecution]:
        """
        Evaluate an agent against test cases.
        
        Args:
            agent_id: Agent ID to evaluate
            test_case_ids: Optional list of test case IDs (uses all if not provided)
        
        Returns:
            List of test executions
        """
        from heretek_swarm.actors.supervisor import get_supervisor
        
        # Determine which test cases to run
        if test_case_ids is None:
            test_case_ids = list(self.test_cases.keys())
        
        executions = []
        
        for test_case_id in test_case_ids:
            if test_case_id not in self.test_cases:
                logger.warning("test_case_not_found", test_case_id=test_case_id)
                continue
            
            test_case = self.test_cases[test_case_id]
            
            execution = await self._run_test_case(agent_id, test_case)
            executions.append(execution)
        
        # Store executions
        async with self._lock:
            self.executions.extend(executions)
        
        logger.info("agent_evaluated", agent_id=agent_id, tests_run=len(executions))
        
        return executions
    
    async def _run_test_case(
        self,
        agent_id: str,
        test_case: TestCase
    ) -> TestExecution:
        """
        Run a single test case.
        
        Args:
            agent_id: Agent ID
            test_case: Test case to run
        
        Returns:
            Test execution with results
        """
        from heretek_swarm.actors.supervisor import get_supervisor
        
        execution = TestExecution(
            test_case=test_case,
            agent_id=agent_id,
            status=EvaluationStatus.RUNNING,
            start_time=datetime.utcnow().isoformat()
        )
        
        try:
            supervisor = get_supervisor()
            
            # Send message to agent
            start = datetime.utcnow()
            response = await supervisor.send_message(
                agent_id,
                json.dumps(test_case.input_data)
            )
            end = datetime.utcnow()
            
            execution.end_time = end.isoformat()
            execution.output = response
            
            # Evaluate results
            results = []
            
            for metric in test_case.evaluation_criteria:
                result = await self._evaluate_metric(
                    metric,
                    test_case,
                    response,
                    start,
                    end
                )
                results.append(result)
            
            execution.results = results
            execution.status = EvaluationStatus.COMPLETED
            
        except Exception as e:
            execution.end_time = datetime.utcnow().isoformat()
            execution.error = str(e)
            execution.status = EvaluationStatus.FAILED
            logger.error("test_case_failed", test_case_id=test_case.id, error=str(e))
        
        return execution
    
    async def _evaluate_metric(
        self,
        metric: EvaluationMetric,
        test_case: TestCase,
        response: str,
        start: datetime,
        end: datetime
    ) -> EvaluationResult:
        """
        Evaluate a specific metric.
        
        Args:
            metric: Metric to evaluate
            test_case: Test case context
            response: Agent response
            start: Start time
            end: End time
        
        Returns:
            Evaluation result
        """
        if metric == EvaluationMetric.RELEVANCE:
            return await self._evaluate_relevance(test_case, response)
        elif metric == EvaluationMetric.ACCURACY:
            return await self._evaluate_accuracy(test_case, response)
        elif metric == EvaluationMetric.COMPLETENESS:
            return await self._evaluate_completeness(test_case, response)
        elif metric == EvaluationMetric.COHERENCE:
            return await self._evaluate_coherence(response)
        elif metric == EvaluationMetric.LATENCY:
            return self._evaluate_latency(start, end)
        elif metric == EvaluationMetric.TOKEN_EFFICIENCY:
            return await self._evaluate_token_efficiency(response)
        elif metric == EvaluationMetric.SAFETY:
            return await self._evaluate_safety(response)
        elif metric == EvaluationMetric.PII_DETECTION:
            return await self._evaluate_pii_detection(response)
        elif metric == EvaluationMetric.SUCCESS_RATE:
            return EvaluationResult(
                metric=metric,
                score=1.0 if response else 0.0,
                details={"response_received": bool(response)}
            )
        elif metric == EvaluationMetric.ERROR_RATE:
            return EvaluationResult(
                metric=metric,
                score=0.0 if response else 1.0,
                details={"error_occurred": not bool(response)}
            )
        else:
            logger.warning("unknown_metric", metric=metric.value)
            return EvaluationResult(
                metric=metric,
                score=0.0,
                details={"error": "Unknown metric"}
            )
    
    async def _evaluate_relevance(
        self,
        test_case: TestCase,
        response: str
    ) -> EvaluationResult:
        """Evaluate response relevance to input."""
        # Simple keyword matching (in production, use semantic similarity)
        input_text = json.dumps(test_case.input_data).lower()
        response_lower = response.lower()
        
        # Count matching keywords
        keywords = set(input_text.split())
        response_words = set(response_lower.split())
        
        matches = len(keywords & response_words)
        relevance = matches / len(keywords) if keywords else 0.0
        
        return EvaluationResult(
            metric=EvaluationMetric.RELEVANCE,
            score=min(relevance, 1.0),
            details={
                "matching_keywords": matches,
                "total_keywords": len(keywords)
            }
        )
    
    async def _evaluate_accuracy(
        self,
        test_case: TestCase,
        response: str
    ) -> EvaluationResult:
        """Evaluate response accuracy against expected output."""
        if test_case.expected_output is None:
            return EvaluationResult(
                metric=EvaluationMetric.ACCURACY,
                score=0.5,  # Neutral score if no expected output
                details={"reason": "No expected output provided"}
            )
        
        expected = json.dumps(test_case.expected_output).lower()
        response_lower = response.lower()
        
        # Simple string comparison (in production, use semantic similarity)
        accuracy = 1.0 if expected == response_lower else 0.0
        
        return EvaluationResult(
            metric=EvaluationMetric.ACCURACY,
            score=accuracy,
            details={
                "matches_expected": accuracy == 1.0,
                "expected_length": len(expected),
                "response_length": len(response_lower)
            }
        )
    
    async def _evaluate_completeness(
        self,
        test_case: TestCase,
        response: str
    ) -> EvaluationResult:
        """Evaluate response completeness."""
        # Check if response addresses all aspects of input
        input_data = test_case.input_data
        required_aspects = []
        
        if "question" in input_data:
            required_aspects.append("answer")
        if "task" in input_data:
            required_aspects.append("completion")
        if "instruction" in input_data:
            required_aspects.append("acknowledgment")
        
        # Simple heuristic: response should be non-empty
        completeness = 1.0 if response.strip() else 0.0
        
        return EvaluationResult(
            metric=EvaluationMetric.COMPLETENESS,
            score=completeness,
            details={
                "has_content": completeness == 1.0,
                "response_length": len(response)
            }
        )
    
    async def _evaluate_coherence(self, response: str) -> EvaluationResult:
        """Evaluate response coherence."""
        # Simple heuristic: check for sentence structure
        sentences = response.split('.')
        
        # Response should have at least one sentence
        coherence = min(len(sentences) / 3, 1.0)
        
        return EvaluationResult(
            metric=EvaluationMetric.COHERENCE,
            score=coherence,
            details={
                "sentence_count": len(sentences),
                "avg_sentence_length": len(response) / len(sentences) if sentences else 0
            }
        )
    
    async def _evaluate_latency(self, start: datetime, end: datetime) -> EvaluationResult:
        """Evaluate response latency."""
        latency_ms = (end - start).total_seconds() * 1000
        
        # Score: lower latency is better
        # < 1s = 1.0, 1-5s = 0.8, 5-10s = 0.5, > 10s = 0.2
        if latency_ms < 1000:
            score = 1.0
        elif latency_ms < 5000:
            score = 0.8
        elif latency_ms < 10000:
            score = 0.5
        else:
            score = 0.2
        
        return EvaluationResult(
            metric=EvaluationMetric.LATENCY,
            score=score,
            details={"latency_ms": latency_ms}
        )
    
    async def _evaluate_token_efficiency(self, response: str) -> EvaluationResult:
        """Evaluate token efficiency."""
        # Estimate token count (rough approximation)
        token_count = len(response.split()) * 1.3  # ~1.3 tokens per word
        
        # Score: shorter responses are more efficient
        # < 100 tokens = 1.0, 100-500 = 0.8, 500-1000 = 0.5, > 1000 = 0.2
        if token_count < 100:
            score = 1.0
        elif token_count < 500:
            score = 0.8
        elif token_count < 1000:
            score = 0.5
        else:
            score = 0.2
        
        return EvaluationResult(
            metric=EvaluationMetric.TOKEN_EFFICIENCY,
            score=score,
            details={"estimated_tokens": token_count}
        )
    
    async def _evaluate_safety(self, response: str) -> EvaluationResult:
        """Evaluate response safety."""
        from heretek_swarm.security.guardrails import create_default_guardrails
        
        guardrails = create_default_guardrails()
        
        # Check for blocked patterns
        filter_result = await guardrails.filter_output(response)
        
        safety_score = 1.0 if filter_result.allowed else 0.0
        
        return EvaluationResult(
            metric=EvaluationMetric.SAFETY,
            score=safety_score,
            details={
                "allowed": filter_result.allowed,
                "blocked_patterns": filter_result.blocked_patterns
            }
        )
    
    async def _evaluate_pii_detection(self, response: str) -> EvaluationResult:
        """Evaluate PII detection in response."""
        from heretek_swarm.security.guardrails import create_default_guardrails
        
        guardrails = create_default_guardrails()
        
        # Validate input for PII
        validation_result = await guardrails.validate_input(response)
        
        # Check if PII was detected
        has_pii = any(
            "PII" in str(action) or "pii" in str(action).lower()
            for action in validation_result.actions
        )
        
        pii_score = 0.0 if has_pii else 1.0
        
        return EvaluationResult(
            metric=EvaluationMetric.PII_DETECTION,
            score=pii_score,
            details={
                "pii_detected": has_pii,
                "validation_actions": [str(a) for a in validation_result.actions]
            }
        )
    
    def get_agent_summary(self, agent_id: str) -> Dict[str, Any]:
        """
        Get summary of evaluations for an agent.
        
        Args:
            agent_id: Agent ID
        
        Returns:
            Summary dictionary
        """
        agent_executions = [
            exec for exec in self.executions
            if exec.agent_id == agent_id
        ]
        
        if not agent_executions:
            return {
                "agent_id": agent_id,
                "total_tests": 0,
                "average_scores": {}
            }
        
        # Calculate average scores per metric
        metric_scores: Dict[EvaluationMetric, List[float]] = {}
        
        for execution in agent_executions:
            for result in execution.results:
                if result.metric not in metric_scores:
                    metric_scores[result.metric] = []
                metric_scores[result.metric].append(result.score)
        
        average_scores = {}
        for metric, scores in metric_scores.items():
            average_scores[metric.value] = sum(scores) / len(scores)
        
        return {
            "agent_id": agent_id,
            "total_tests": len(agent_executions),
            "average_scores": average_scores,
            "last_evaluation": agent_executions[-1].timestamp if agent_executions else None
        }
    
    def get_all_summaries(self) -> List[Dict[str, Any]]:
        """
        Get summaries for all evaluated agents.
        
        Returns:
            List of agent summaries
        """
        agent_ids = set(exec.agent_id for exec in self.executions)
        
        return [self.get_agent_summary(agent_id) for agent_id in agent_ids]


# Global evaluator instance
_global_evaluator: Optional[Evaluator] = None


def get_evaluator() -> Evaluator:
    """
    Get global evaluator instance.
    
    Returns:
        Evaluator instance
    """
    global _global_evaluator
    
    if _global_evaluator is None:
        _global_evaluator = Evaluator()
    
    return _global_evaluator
