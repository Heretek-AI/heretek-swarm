"""
Evaluation API - Agent Quality Assessment

Provides REST API for:
- Loading test cases
- Running agent evaluations
- Getting evaluation results
- Agent summaries
"""

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, Depends
import structlog

from evaluation.evaluator import (
    get_evaluator,
    TestCase,
    EvaluationMetric,
)
from ..gateway.auth import verify_auth

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/api/evaluation", tags=["evaluation"])


@router.post("/test-cases", status_code=201)
async def create_test_case(
    test_case: Dict[str, Any],
    authenticated: str = Depends(verify_auth)
) -> Dict[str, Any]:
    """
    Create a new test case.
    
    Args:
        test_case: Test case definition
        authenticated: Authentication token
    
    Returns:
        Created test case
    """
    evaluator = get_evaluator()
    
    # Create test case object
    case = TestCase(
        id=test_case.get("id", f"test_{len(evaluator.test_cases)}"),
        name=test_case.get("name", "Unnamed Test"),
        description=test_case.get("description", ""),
        input_data=test_case.get("input_data", {}),
        expected_output=test_case.get("expected_output"),
        evaluation_criteria=[
            EvaluationMetric(m) for m in test_case.get("evaluation_criteria", [])
        ],
        metadata=test_case.get("metadata", {})
    )
    
    # Load into evaluator
    evaluator.load_test_cases([case])
    
    logger.info("test_case_created", test_case_id=case.id)
    
    return {
        "id": case.id,
        "name": case.name,
        "description": case.description
    }


@router.post("/test-cases/batch", status_code=201)
async def create_test_cases_batch(
    test_cases: List[Dict[str, Any]],
    authenticated: str = Depends(verify_auth)
) -> Dict[str, Any]:
    """
    Create multiple test cases at once.
    
    Args:
        test_cases: List of test case definitions
        authenticated: Authentication token
    
    Returns:
        Number of test cases created
    """
    evaluator = get_evaluator()
    
    # Create test case objects
    cases = [
        TestCase(
            id=tc.get("id", f"test_{len(evaluator.test_cases) + i}"),
            name=tc.get("name", "Unnamed Test"),
            description=tc.get("description", ""),
            input_data=tc.get("input_data", {}),
            expected_output=tc.get("expected_output"),
            evaluation_criteria=[
                EvaluationMetric(m) for m in tc.get("evaluation_criteria", [])
            ],
            metadata=tc.get("metadata", {})
        )
        for i, tc in enumerate(test_cases)
    ]
    
    # Load into evaluator
    evaluator.load_test_cases(cases)
    
    logger.info("test_cases_created_batch", count=len(cases))
    
    return {
        "count": len(cases),
        "test_case_ids": [case.id for case in cases]
    }


@router.get("/test-cases", status_code=200)
async def list_test_cases(
    authenticated: str = Depends(verify_auth)
) -> Dict[str, Any]:
    """
    List all available test cases.
    
    Args:
        authenticated: Authentication token
    
    Returns:
        List of test cases
    """
    evaluator = get_evaluator()
    
    return {
        "test_cases": [
            {
                "id": case.id,
                "name": case.name,
                "description": case.description,
                "evaluation_criteria": [m.value for m in case.evaluation_criteria]
            }
            for case in evaluator.test_cases.values()
        ]
    }


@router.post("/agents/{agent_id}/evaluate", status_code=201)
async def evaluate_agent(
    agent_id: str,
    test_case_ids: Optional[List[str]] = None,
    authenticated: str = Depends(verify_auth)
) -> Dict[str, Any]:
    """
    Evaluate an agent against test cases.
    
    Args:
        agent_id: Agent ID to evaluate
        test_case_ids: Optional list of test case IDs (uses all if not provided)
        authenticated: Authentication token
    
    Returns:
        Evaluation results
    """
    evaluator = get_evaluator()
    
    # Run evaluation
    executions = await evaluator.evaluate_agent(agent_id, test_case_ids)
    
    logger.info("agent_evaluated", agent_id=agent_id, tests_run=len(executions))
    
    return {
        "agent_id": agent_id,
        "executions": [
            {
                "test_case_id": exec.test_case.id,
                "test_case_name": exec.test_case.name,
                "status": exec.status.value,
                "start_time": exec.start_time,
                "end_time": exec.end_time,
                "results": [
                    {
                        "metric": result.metric.value,
                        "score": result.score,
                        "details": result.details
                    }
                    for result in exec.results
                ],
                "output": exec.output,
                "error": exec.error
            }
            for exec in executions
        ]
    }


@router.get("/agents/{agent_id}/summary", status_code=200)
async def get_agent_evaluation_summary(
    agent_id: str,
    authenticated: str = Depends(verify_auth)
) -> Dict[str, Any]:
    """
    Get evaluation summary for an agent.
    
    Args:
        agent_id: Agent ID
        authenticated: Authentication token
    
    Returns:
        Agent evaluation summary
    """
    evaluator = get_evaluator()
    
    summary = evaluator.get_agent_summary(agent_id)
    
    return summary


@router.get("/summaries", status_code=200)
async def get_all_evaluation_summaries(
    authenticated: str = Depends(verify_auth)
) -> Dict[str, Any]:
    """
    Get evaluation summaries for all agents.
    
    Args:
        authenticated: Authentication token
    
    Returns:
        List of agent summaries
    """
    evaluator = get_evaluator()
    
    summaries = evaluator.get_all_summaries()
    
    return {
        "summaries": summaries
    }


@router.delete("/test-cases/{test_case_id}")
async def delete_test_case(
    test_case_id: str,
    authenticated: str = Depends(verify_auth)
):
    """
    Delete a test case.
    
    Args:
        test_case_id: Test case ID
        authenticated: Authentication token
    
    Returns:
        204 No Content on success
    """
    evaluator = get_evaluator()
    
    if test_case_id not in evaluator.test_cases:
        raise HTTPException(status_code=404, detail="Test case not found")
    
    del evaluator.test_cases[test_case_id]
    
    logger.info("test_case_deleted", test_case_id=test_case_id)
    
    return None
