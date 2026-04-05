"""
Workflows API - Workflow management endpoints

Provides REST API for:
- Creating workflows from Canvas UI
- Listing workflows
- Executing workflows
- Getting workflow status
- Deleting workflows
"""

from typing import Dict, List, Optional, Any
from fastapi import APIRouter, HTTPException, Depends
import structlog

from ..workflow.engine import (
    Workflow,
    WorkflowEngine,
    get_workflow_engine,
    WorkflowResult,
    WorkflowState,
    NodeStatus,
)
from ..gateway.auth import verify_auth

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/api/workflows", tags=["workflows"])

# In-memory storage for workflows (in production, use database)
_workflows: Dict[str, Workflow] = {}


@router.post("", status_code=201)
async def create_workflow(
    workflow_definition: Dict[str, Any],
    authenticated: str = Depends(verify_auth)
) -> Dict[str, Any]:
    """
    Create a new workflow from Canvas UI definition.

    Args:
        workflow_definition: Workflow definition from Canvas UI
        authenticated: Authentication token

    Returns:
        Created workflow with ID
    """
    engine = get_workflow_engine()

    # Create workflow from definition
    workflow = await engine.load_workflow(workflow_definition)

    # Store workflow
    _workflows[workflow.id] = workflow

    logger.info("workflow_created", workflow_id=workflow.id, name=workflow.name)

    return {
        "id": workflow.id,
        "name": workflow.name,
        "created_at": workflow.created_at,
        "state": WorkflowState.PENDING.value
    }


@router.get("", status_code=200)
async def list_workflows(
    authenticated: str = Depends(verify_auth)
) -> Dict[str, Any]:
    """
    List all workflows.

    Args:
        authenticated: Authentication token

    Returns:
        List of workflows
    """
    engine = get_workflow_engine()

    return {
        "workflows": [
            {
                "id": workflow_id,
                "name": workflow.name,
                "created_at": workflow.created_at,
                "state": workflow.state
            }
            for workflow_id, workflow in engine.workflows.items()
        ]
    }


@router.get("/{workflow_id}", status_code=200)
async def get_workflow(
    workflow_id: str,
    authenticated: str = Depends(verify_auth)
) -> Dict[str, Any]:
    """
    Get a specific workflow by ID.

    Args:
        workflow_id: Workflow ID
        authenticated: Authentication token

    Returns:
        Workflow definition
    """
    engine = get_workflow_engine()

    if workflow_id not in engine.workflows:
        raise HTTPException(status_code=404, detail="Workflow not found")

    workflow = engine.workflows[workflow_id]

    return {
        "id": workflow.id,
        "name": workflow.name,
        "nodes": workflow.nodes,
        "edges": workflow.edges,
        "metadata": workflow.metadata,
        "created_at": workflow.created_at,
        "state": workflow.state
    }


@router.post("/{workflow_id}/execute", status_code=201)
async def execute_workflow(
    workflow_id: str,
    input_data: Dict[str, Any],
    authenticated: str = Depends(verify_auth)
) -> Dict[str, Any]:
    """
    Execute a workflow.

    Args:
        workflow_id: Workflow ID
        input_data: Input data for workflow
        authenticated: Authentication token

    Returns:
        Execution result
    """
    engine = get_workflow_engine()

    if workflow_id not in engine.workflows:
        raise HTTPException(status_code=404, detail="Workflow not found")

    result = await engine.execute_workflow(
        workflow_id=workflow_id,
        input_data=input_data
    )

    logger.info("workflow_executed", workflow_id=workflow_id, status=result.status)

    return {
        "execution_id": result.execution_id,
        "workflow_id": workflow_id,
        "status": result.status,
        "node_results": result.node_results,
        "variables": result.variables,
        "start_time": result.start_time.isoformat(),
        "end_time": result.end_time.isoformat() if result.end_time else None,
        "error": str(result.error) if result.error else None
    }


@router.delete("/{workflow_id}", status_code=204)
async def delete_workflow(
    workflow_id: str,
    authenticated: str = Depends(verify_auth)
) -> Dict[str, Any]:
    """
    Delete a workflow.

    Args:
        workflow_id: Workflow ID
        authenticated: Authentication token

    Returns:
        Deletion confirmation
    """
    engine = get_workflow_engine()

    if workflow_id not in engine.workflows:
        raise HTTPException(status_code=404, detail="Workflow not found")

    # Remove from storage
    del _workflows[workflow_id]

    logger.info("workflow_deleted", workflow_id=workflow_id)

    return {
        "message": f"Workflow {workflow_id} deleted"
    }


@router.get("/{workflow_id}/status", status_code=200)
async def get_workflow_status(
    workflow_id: str,
    authenticated: str = Depends(verify_auth)
) -> Dict[str, Any]:
    """
    Get status of a workflow execution.

    Args:
        workflow_id: Workflow ID
        authenticated: Authentication token

    Returns:
        Current execution status
    """
    engine = get_workflow_engine()

    execution_id = f"exec_{workflow_id}_{workflow_id}"

    context = engine.active_executions.get(execution_id)

    if not context:
        return {
            "workflow_id": workflow_id,
            "status": WorkflowState.PENDING.value,
            "execution_id": None
        }

    return {
        "workflow_id": workflow_id,
        "status": context.state.value,
        "execution_id": context.execution_id,
        "node_results": context.node_results,
        "variables": context.variables,
        "start_time": context.start_time.isoformat(),
        "end_time": context.end_time.isoformat() if context.end_time else None,
        "error": str(context.error) if context.error else None
    }


@router.post("/{workflow_id}/cancel", status_code=200)
async def cancel_workflow(
    workflow_id: str,
    authenticated: str = Depends(verify_auth)
) -> Dict[str, Any]:
    """
    Cancel a running workflow execution.

    Args:
        workflow_id: Workflow ID
        authenticated: Authentication token

    Returns:
        Cancellation confirmation
    """
    engine = get_workflow_engine()

    execution_id = f"exec_{workflow_id}_{workflow_id}"

    success = await engine.cancel_workflow(execution_id)

    if success:
        return {
            "message": f"Workflow execution {execution_id} cancelled"
        }
    else:
        return {
            "message": f"Failed to cancel workflow execution {execution_id}"
        }
