"""
Workflows API - Workflow management endpoints

Provides REST API for:
- Creating workflows from Canvas UI
- Listing workflows
- Executing workflows
- Getting workflow status
- Deleting workflows
- Validating workflows
- Workflow execution events (SSE)
"""

import asyncio
import json
import uuid
from datetime import UTC, datetime
from typing import Any, AsyncGenerator

import structlog
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse

from heretek_swarm.gateway.auth import verify_auth
from heretek_swarm.workflow.engine import WorkflowState, get_workflow_engine
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
    engine = await get_workflow_engine()

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
    engine = await get_workflow_engine()

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
    engine = await get_workflow_engine()

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
        "state": WorkflowState.PENDING.value
    }


@router.post("/{workflow_id}/execute", status_code=201)
async def execute_workflow(
    workflow_id: str,
    input_data: dict[str, Any],
    authenticated: str = Depends(verify_auth),
    strategy: str = "dag",
) -> dict[str, Any]:
    """
    Execute a workflow.

    Args:
        workflow_id: Workflow ID
        input_data: Input data for workflow
        authenticated: Authentication token
        strategy: Execution strategy - "dag" (default), "cycle", "majority_vote"
                  - dag: Topological sort (dependency order)
                  - cycle: Feedback loop with convergence monitoring
                  - majority_vote: Parallel execution with vote aggregation

    Returns:
        Execution result
    """
    engine = await get_workflow_engine()

    if workflow_id not in engine.workflows:
        raise HTTPException(status_code=404, detail="Workflow not found")

    result = await engine.execute_workflow(
        workflow_id=workflow_id,
        input_data=input_data,
        strategy=strategy,
    )

    logger.info(
        "workflow_executed",
        workflow_id=workflow_id,
        strategy=strategy,
        status=result.status,
    )

    return {
        "execution_id": result.execution_id,
        "workflow_id": workflow_id,
        "status": result.status,
        "node_results": result.node_results,
        "variables": result.variables,
        "start_time": result.start_time.isoformat(),
        "end_time": result.end_time.isoformat() if result.end_time else None,
        "error": str(result.error) if result.error else None,
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
    engine = await get_workflow_engine()

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
    engine = await get_workflow_engine()

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
    engine = await get_workflow_engine()

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
    engine = await get_workflow_engine()

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


# =============================================================================
# SSE Endpoint for Workflow Events
# =============================================================================


@router.get("/events", response_class=StreamingResponse)
async def workflow_events_stream(
    workflow_id: str | None = Query(None, description="Filter events by workflow ID"),
    authenticated: str = Depends(verify_auth)
) -> StreamingResponse:
    """
    SSE endpoint for streaming workflow execution events.

    Events are sent as Server-Sent Events with JSON payloads:
    - status: "started" | "running" | "completed" | "failed"
    - currentNode: Node ID currently executing (or null)
    - progress: 0-100 percentage
    - message: Human-readable status message
    - timestamp: ISO format timestamp
    - workflow_id: Workflow ID (if filtered)
    - execution_id: Execution ID for this run

    Args:
        workflow_id: Optional workflow ID to filter events
        authenticated: Authentication token

    Returns:
        StreamingResponse with text/event-stream content type
    """
    async def event_generator() -> AsyncGenerator[str, None]:
        """Generator that yields SSE events."""
        # Track execution state
        execution_id = f"exec_{uuid.uuid4().hex[:8]}"
        event_count = 0

        logger.info(
            "sse_connection_opened",
            execution_id=execution_id,
            workflow_id=workflow_id,
        )

        # Send initial connection event
        initial_event = {
            'status': 'connected',
            'execution_id': execution_id,
            'workflow_id': workflow_id,
            'message': 'SSE connection established',
            'timestamp': datetime.now(UTC).isoformat(),
        }
        yield f"data: {json.dumps(initial_event)}\n\n"

        try:
            # Simulate workflow execution events for demo purposes
            # In production, this would integrate with actual workflow engine
            for i in range(10):
                await asyncio.sleep(0.5)  # Simulate work
                event_count += 1

                progress = min(100, (event_count * 10))
                status = "running" if progress < 100 else "completed"
                message = f"Executing step {event_count}/10" if progress < 100 else "Workflow completed"

                event_data = {
                    'status': status,
                    'currentNode': f'node-{event_count}' if event_count <= 5 else None,
                    'progress': progress,
                    'message': message,
                    'timestamp': datetime.now(UTC).isoformat(),
                    'workflow_id': workflow_id,
                    'execution_id': execution_id,
                    'node_results': {
                        f'node-{j}': {'status': 'completed', 'duration_ms': 100 * j}
                        for j in range(1, event_count)
                    } if event_count > 1 else {},
                }

                yield f"data: {json.dumps(event_data)}\n\n"

                if status == "completed":
                    break

        except asyncio.CancelledError:
            logger.info("sse_connection_cancelled", execution_id=execution_id)
            cancelled_event = {
                'status': 'cancelled',
                'execution_id': execution_id,
                'message': 'SSE connection closed by client',
                'timestamp': datetime.now(UTC).isoformat(),
            }
            yield f"data: {json.dumps(cancelled_event)}\n\n"
        except Exception as e:
            logger.error("sse_connection_error", execution_id=execution_id, error=str(e))
            error_event = {
                'status': 'failed',
                'execution_id': execution_id,
                'message': f'Stream error: {str(e)}',
                'timestamp': datetime.now(UTC).isoformat(),
            }
            yield f"data: {json.dumps(error_event)}\n\n"
        finally:
            logger.info(
                "sse_connection_closed",
                execution_id=execution_id,
                event_count=event_count,
            )

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Disable nginx buffering
        },
    )


@router.get("/{workflow_id}/events", response_class=StreamingResponse)
async def workflow_specific_events_stream(
    workflow_id: str,
    authenticated: str = Depends(verify_auth)
) -> StreamingResponse:
    """
    SSE endpoint for streaming events from a specific workflow execution.

    Args:
        workflow_id: Workflow ID to stream events for
        authenticated: Authentication token

    Returns:
        StreamingResponse with text/event-stream content type
    """
    engine = await get_workflow_engine()

    # Check if workflow exists
    if workflow_id not in engine.workflows:
        raise HTTPException(status_code=404, detail="Workflow not found")

    async def event_generator() -> AsyncGenerator[str, None]:
        """Generator that yields SSE events for specific workflow."""
        execution_id = f"exec_{workflow_id}_{uuid.uuid4().hex[:8]}"
        event_count = 0

        logger.info(
            "workflow_sse_connection_opened",
            execution_id=execution_id,
            workflow_id=workflow_id,
        )

        # Send initial connection event
        connected_event = {
            'status': 'connected',
            'execution_id': execution_id,
            'workflow_id': workflow_id,
            'message': f'Watching workflow {workflow_id}',
            'timestamp': datetime.now(UTC).isoformat(),
        }
        yield f"data: {json.dumps(connected_event)}\n\n"

        try:
            workflow = engine.workflows[workflow_id]
            node_count = len(workflow.nodes) if hasattr(workflow, 'nodes') else 5

            # Simulate workflow execution events
            for i in range(node_count):
                await asyncio.sleep(0.3)  # Simulate work
                event_count += 1

                progress = int((event_count / node_count) * 100)
                status = "running" if progress < 100 else "completed"
                node_id = workflow.nodes[i].id if i < len(workflow.nodes) else f"node-{i}"

                event_data = {
                    'status': status,
                    'currentNode': node_id,
                    'progress': progress,
                    'message': f"Executing {node_id}" if progress < 100 else "Workflow completed",
                    'timestamp': datetime.now(UTC).isoformat(),
                    'workflow_id': workflow_id,
                    'execution_id': execution_id,
                    'total_nodes': node_count,
                    'completed_nodes': event_count,
                }

                yield f"data: {json.dumps(event_data)}\n\n"

                if status == "completed":
                    break

        except asyncio.CancelledError:
            logger.info("workflow_sse_cancelled", execution_id=execution_id)
            cancelled_event = {
                'status': 'cancelled',
                'execution_id': execution_id,
                'workflow_id': workflow_id,
                'message': 'SSE connection closed by client',
                'timestamp': datetime.now(UTC).isoformat(),
            }
            yield f"data: {json.dumps(cancelled_event)}\n\n"
        except Exception as e:
            logger.error("workflow_sse_error", execution_id=execution_id, error=str(e))
            error_event = {
                'status': 'failed',
                'execution_id': execution_id,
                'workflow_id': workflow_id,
                'message': f'Stream error: {str(e)}',
                'timestamp': datetime.now(UTC).isoformat(),
            }
            yield f"data: {json.dumps(error_event)}\n\n"
        finally:
            logger.info(
                "workflow_sse_connection_closed",
                execution_id=execution_id,
                workflow_id=workflow_id,
                event_count=event_count,
            )

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
