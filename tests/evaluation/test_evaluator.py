"""
Tests for Agent Evaluator Framework

Test the evaluation framework including test case execution,
output validation, and quality metrics calculation.
"""

import asyncio
from datetime import datetime
from typing import Any, Dict

import pytest
from evaluation.evaluator import (
    AgentEvaluator,
    EvaluationStatus,
    OutputConstraints,
    TestCase,
)


class MockAgent:
    """Mock agent for testing."""

    def __init__(self, responses: Dict[str, Any] = None):
        self.responses = responses or {}
        self.call_count = 0

    async def execute(self, input_data: Dict[str, Any]) -> Any:
        """Execute agent with mock response."""
        self.call_count += 1
        query = input_data.get("query", "")
        return self.responses.get(query, {"result": "default"})


class SlowAgent:
    """Mock agent that times out."""

    async def execute(self, input_data: Dict[str, Any]) -> Any:
        """Execute agent with delay."""
        await asyncio.sleep(35)  # Exceeds default timeout
        return {"result": "timeout"}


class FailingAgent:
    """Mock agent that fails."""

    async def execute(self, input_data: Dict[str, Any]) -> Any:
        """Execute agent with error."""
        raise ValueError("Agent failed")


class TestAgentEvaluator:
    """Test suite for AgentEvaluator."""

    @pytest.fixture
    def evaluator(self):
        """Create evaluator instance."""
        return AgentEvaluator(timeout=10, parallel=True)

    @pytest.fixture
    def mock_agent(self):
        """Create mock agent."""
        return MockAgent(responses={
            "What is 2+2?": {"answer": "4"},
            "What is 3+3?": {"answer": "6"},
            "What is 4+4?": {"answer": "8"},
        })

    @pytest.fixture
    def test_cases(self):
        """Create test cases."""
        return [
            TestCase(
                id="test-1",
                name="Basic addition",
                description="Test basic arithmetic",
                input_data={"query": "What is 2+2?"},
                expected_output={"answer": "4"},
                constraints=OutputConstraints(
                    max_length=100,
                    required_keys=["answer"],
                ),
            ),
            TestCase(
                id="test-2",
                name="Basic addition 2",
                description="Test basic arithmetic",
                input_data={"query": "What is 3+3?"},
                expected_output={"answer": "6"},
                constraints=OutputConstraints(
                    max_length=100,
                    required_keys=["answer"],
                ),
            ),
            TestCase(
                id="test-3",
                name="Basic addition 3",
                description="Test basic arithmetic",
                input_data={"query": "What is 4+4?"},
                expected_output={"answer": "8"},
                constraints=OutputConstraints(
                    max_length=100,
                    required_keys=["answer"],
                ),
            ),
        ]

    @pytest.mark.asyncio
    async def test_evaluate_agent_success(self, evaluator, mock_agent, test_cases):
        """Test successful agent evaluation."""
        result = await evaluator.evaluate_agent(
            agent_id="test-agent",
            agent=mock_agent,
            test_cases=test_cases,
        )

        # Check evaluation status
        assert result.status == EvaluationStatus.COMPLETED
        assert result.metrics is not None

        # Check all test cases passed
        assert len(result.test_results) == len(test_cases)
        assert all(r.success for r in result.test_results)

        # Check metrics
        assert result.metrics.success_rate == 100.0
        assert result.metrics.constraint_compliance == 100.0
        assert result.metrics.output_quality == 100.0

    @pytest.mark.asyncio
    async def test_evaluate_agent_timeout(self, evaluator):
        """Test agent evaluation with timeout."""
        slow_agent = SlowAgent()
        test_cases = [
            TestCase(
                id="timeout-test",
                name="Timeout test",
                description="Test timeout handling",
                input_data={"query": "test"},
            ),
        ]

        result = await evaluator.evaluate_agent(
            agent_id="slow-agent",
            agent=slow_agent,
            test_cases=test_cases,
        )

        # Check timeout handling
        assert len(result.test_results) == 1
        assert not result.test_results[0].success
        assert isinstance(result.test_results[0].error, asyncio.TimeoutError)

        # Check metrics reflect failure
        assert result.metrics.success_rate == 0.0

    @pytest.mark.asyncio
    async def test_evaluate_agent_failure(self, evaluator):
        """Test agent evaluation with failure."""
        failing_agent = FailingAgent()
        test_cases = [
            TestCase(
                id="failure-test",
                name="Failure test",
                description="Test failure handling",
                input_data={"query": "test"},
            ),
        ]

        result = await evaluator.evaluate_agent(
            agent_id="failing-agent",
            agent=failing_agent,
            test_cases=test_cases,
        )

        # Check failure handling
        assert len(result.test_results) == 1
        assert not result.test_results[0].success
        assert isinstance(result.test_results[0].error, ValueError)

        # Check metrics reflect failure
        assert result.metrics.success_rate == 0.0

    @pytest.mark.asyncio
    async def test_output_validation_length(self, evaluator):
        """Test output length validation."""
        mock_agent = MockAgent(responses={"test": "x" * 200})
        test_cases = [
            TestCase(
                id="length-test",
                name="Length validation test",
                description="Test output length constraint",
                input_data={"query": "test"},
                constraints=OutputConstraints(max_length=100),
            ),
        ]

        result = await evaluator.evaluate_agent(
            agent_id="test-agent",
            agent=mock_agent,
            test_cases=test_cases,
        )

        # Check length validation
        assert not result.test_results[0].success
        assert any("Output exceeds max length" in err for err in result.test_results[0].validation_errors)

    @pytest.mark.asyncio
    async def test_output_validation_required_keys(self, evaluator):
        """Test output required keys validation."""
        mock_agent = MockAgent(responses={"test": {"data": "value"}})
        test_cases = [
            TestCase(
                id="keys-test",
                name="Required keys test",
                description="Test required keys constraint",
                input_data={"query": "test"},
                constraints=OutputConstraints(required_keys=["answer", "reason"]),
            ),
        ]

        result = await evaluator.evaluate_agent(
            agent_id="test-agent",
            agent=mock_agent,
            test_cases=test_cases,
        )

        # Check required keys validation
        assert not result.test_results[0].success
        assert "Missing required key: answer" in result.test_results[0].validation_errors

    @pytest.mark.asyncio
    async def test_output_validation_forbidden_patterns(self, evaluator):
        """Test output forbidden patterns validation."""
        mock_agent = MockAgent(responses={"test": "Password: secret123"})
        test_cases = [
            TestCase(
                id="patterns-test",
                name="Forbidden patterns test",
                description="Test forbidden patterns constraint",
                input_data={"query": "test"},
                constraints=OutputConstraints(
                    forbidden_patterns=[r"Password:\s*\w+"],
                ),
            ),
        ]

        result = await evaluator.evaluate_agent(
            agent_id="test-agent",
            agent=mock_agent,
            test_cases=test_cases,
        )

        # Check forbidden patterns validation
        assert not result.test_results[0].success
        assert "forbidden pattern" in result.test_results[0].validation_errors[0].lower()

    @pytest.mark.asyncio
    async def test_sequential_execution(self, evaluator, mock_agent, test_cases):
        """Test sequential test execution."""
        evaluator_sequential = AgentEvaluator(timeout=10, parallel=False)
        result = await evaluator.evaluate_agent(
            agent_id="test-agent",
            agent=mock_agent,
            test_cases=test_cases,
        )

        # Check sequential execution
        assert result.status == EvaluationStatus.COMPLETED
        assert len(result.test_results) == len(test_cases)
        assert all(r.success for r in result.test_results)

    @pytest.mark.asyncio
    async def test_compare_agents(self, evaluator):
        """Test agent comparison."""
        mock_agent_1 = MockAgent(responses={
            "What is 2+2?": {"answer": "4"},
            "What is 3+3?": {"answer": "6"},
        })
        mock_agent_2 = MockAgent(responses={
            "What is 2+2?": {"answer": "4"},
            "What is 3+3?": {"answer": "5"},  # Wrong answer
        })

        test_cases = [
            TestCase(
                id="test-1",
                name="Basic addition",
                description="Test basic arithmetic",
                input_data={"query": "What is 2+2?"},
                expected_output={"answer": "4"},
            ),
            TestCase(
                id="test-2",
                name="Basic addition 2",
                description="Test basic arithmetic",
                input_data={"query": "What is 3+3?"},
                expected_output={"answer": "6"},
            ),
        ]

        # Evaluate both agents
        result_1 = await evaluator.evaluate_agent(
            agent_id="agent-1",
            agent=mock_agent_1,
            test_cases=test_cases,
        )

        result_2 = await evaluator.evaluate_agent(
            agent_id="agent-2",
            agent=mock_agent_2,
            test_cases=test_cases,
        )

        # Compare agents
        comparison = evaluator.compare_agents({
            "agent-1": result_1,
            "agent-2": result_2,
        })

        # Check comparison
        assert "agent-1" in comparison
        assert "agent-2" in comparison

        # Agent 1 should have higher success rate
        assert comparison["agent-1"].success_rate > comparison["agent-2"].success_rate

    @pytest.mark.asyncio
    async def test_get_evaluation(self, evaluator, mock_agent, test_cases):
        """Test getting evaluation by ID."""
        result = await evaluator.evaluate_agent(
            agent_id="test-agent",
            agent=mock_agent,
            test_cases=test_cases,
            evaluation_id="test-eval-123",
        )

        # Get evaluation by ID
        retrieved = evaluator.get_evaluation("test-eval-123")

        # Check retrieved evaluation
        assert retrieved is not None
        assert retrieved.evaluation_id == "test-eval-123"
        assert retrieved.agent_id == "test-agent"

    @pytest.mark.asyncio
    async def test_list_evaluations(self, evaluator, mock_agent, test_cases):
        """Test listing evaluations."""
        await evaluator.evaluate_agent(
            agent_id="test-agent",
            agent=mock_agent,
            test_cases=test_cases,
            evaluation_id="test-eval-123",
        )

        # List all evaluations
        evaluations = evaluator.list_evaluations()

        # Check list
        assert len(evaluations) == 1
        assert evaluations[0].evaluation_id == "test-eval-123"

    @pytest.mark.asyncio
    async def test_evaluation_timestamps(self, evaluator, mock_agent, test_cases):
        """Test evaluation timestamps."""
        result = await evaluator.evaluate_agent(
            agent_id="test-agent",
            agent=mock_agent,
            test_cases=test_cases,
        )

        # Check timestamps
        assert result.started_at is not None
        assert result.completed_at is not None
        assert result.total_time > 0

        # Check completed_at is after started_at
        started = datetime.fromisoformat(result.started_at)
        completed = datetime.fromisoformat(result.completed_at)
        assert completed > started
