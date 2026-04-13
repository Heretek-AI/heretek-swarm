"""
Workflows API - Workflow management endpoints

Provides REST API for:
- Creating workflows from Canvas UI
- Listing workflows
- Executing workflows
- Getting workflow status
- Deleting workflows
- Validating workflows
"""

import uuid
from typing import Any

import structlog
from fastapi import APIRouter, Depends, HTTPException

from heretek_swarm.gateway.auth import verify_auth
from heretek_swarm.workflow.engine import Workflow, WorkflowState, get_workflow_engine
from heretek_swarm.workflow.validator import WorkflowValidator

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/api/workflows", tags=["workflows"])


@router.post("", status_code=201)
async def create_workflow(
    workflow_definition: dict[str, Any],
    authenticated: str = Depends(verify_auth)
) -> dict[str, Any]:
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
    engine.workflows[workflow.id] = workflow

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
) -> dict[str, Any]:
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
) -> dict[str, Any]:
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
    input_data: dict[str, Any],
    authenticated: str = Depends(verify_auth)
) -> dict[str, Any]:
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


@router.delete("/{workflow_id}")
async def delete_workflow(
    workflow_id: str,
    authenticated: str = Depends(verify_auth)
):
    """
    Delete a workflow.

    Args:
        workflow_id: Workflow ID
        authenticated: Authentication token

    Returns:
        204 No Content on success
    """
    engine = get_workflow_engine()

    if workflow_id not in engine.workflows:
        raise HTTPException(status_code=404, detail="Workflow not found")

    # Remove from storage
    del engine.workflows[workflow_id]

    logger.info("workflow_deleted", workflow_id=workflow_id)

    return


@router.get("/{workflow_id}/status", status_code=200)
async def get_workflow_status(
    workflow_id: str,
    authenticated: str = Depends(verify_auth)
) -> dict[str, Any]:
    """
    Get status of a workflow execution.

    Args:
        workflow_id: Workflow ID
        authenticated: Authentication token

    Returns:
        Current execution status
    """
    engine = get_workflow_engine()

    execution_id = f"exec_{workflow_id}_{uuid.uuid4().hex[:8]}"

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
) -> dict[str, Any]:
    """
    Cancel a running workflow execution.

    Args:
        workflow_id: Workflow ID
        authenticated: Authentication token

    Returns:
        Cancellation confirmation
    """
    engine = get_workflow_engine()

    execution_id = f"exec_{workflow_id}_{uuid.uuid4().hex[:8]}"

    success = await engine.cancel_workflow(execution_id)

    if success:
        return {
            "message": f"Workflow execution {execution_id} cancelled"
        }
    return {
        "message": f"Failed to cancel workflow execution {execution_id}"
    }


@router.post("/{workflow_id}/validate", status_code=200)
async def validate_workflow_endpoint(
    workflow_id: str,
    authenticated: str = Depends(verify_auth)
) -> dict[str, Any]:
    """
    Validate a workflow graph before execution.

    Checks for:
    - Disconnected nodes (no input/output connections)
    - Circular dependencies (beyond allowed loops)
    - Missing required connections
    - Invalid agent types
    - Resource conflicts

    Args:
        workflow_id: Workflow ID to validate
        authenticated: Authentication token

    Returns:
        Validation result with errors, warnings, and info messages
    """
    engine = get_workflow_engine()

    if workflow_id not in engine.workflows:
        raise HTTPException(status_code=404, detail="Workflow not found")

    workflow = engine.workflows[workflow_id]

    # Convert workflow to validation format
    workflow_definition = {
        "id": workflow.id,
        "name": workflow.name,
        "nodes": [
            {
                "id": node.id,
                "type": node.type,
                "data": node.data,
                "position": node.position,
            }
            for node in workflow.nodes
        ],
        "edges": [
            {
                "id": edge.id,
                "source": edge.source,
                "target": edge.target,
                "condition": edge.condition,
            }
            for edge in workflow.edges
        ],
    }

    # Validate
    validator = WorkflowValidator()
    result = validator.validate(workflow_definition)

    logger.info(
        "workflow_validated",
        workflow_id=workflow_id,
        valid=result.valid,
        error_count=len(result.errors),
        warning_count=len(result.warnings),
    )

    return result.to_dict()


@router.post("/validate", status_code=200)
async def validate_workflow_draft(
    workflow_definition: dict[str, Any],
    authenticated: str = Depends(verify_auth)
) -> dict[str, Any]:
    """
    Validate a workflow definition (draft mode).

    Useful for validating workflows before saving them.

    Args:
        workflow_definition: Workflow definition to validate
        authenticated: Authentication token

    Returns:
        Validation result with errors, warnings, and info messages
    """
    validator = WorkflowValidator()
    result = validator.validate(workflow_definition)

    logger.info(
        "workflow_draft_validated",
        valid=result.valid,
        error_count=len(result.errors),
        warning_count=len(result.warnings),
    )

    return result.to_dict()
