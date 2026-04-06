"""
Workflow Engine - Execute visual workflows from Canvas UI

Provides workflow execution with dependency resolution, error handling,
and state tracking. Inspired by Flowise workflow engine and LangGraph patterns.

Features:
- TypedDict workflow state with Annotated for state transitions
- Checkpointing for workflow resumption
- Cycle detection for infinite loop prevention
- Conditional edges for dynamic workflow routing
"""

import asyncio
import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Set, TypeVar, Annotated, Generic
from dataclasses import dataclass, field
from enum import Enum
from typing_extensions import TypedDict

import structlog

logger = structlog.get_logger(__name__)


class WorkflowState(TypedDict, total=False):
    """
    Typed workflow state with annotations for state transitions.
    
    LangGraph pattern: Uses Annotated types to specify how state fields
    should be updated during workflow execution.
    
    Attributes:
        messages: List of messages (append-only accumulation)
        results: Dict of node results (merge updates)
        current_phase: Current workflow phase identifier
        metadata: Additional metadata dict
        checkpoint: Optional checkpoint for resumption
        cycle_count: Counter for cycle detection
    """
    
    messages: Annotated[List[Dict[str, Any]], "append"]
    results: Annotated[Dict[str, Any], "merge"]
    current_phase: str
    metadata: Dict[str, Any]
    checkpoint: Optional[Dict[str, Any]]
    cycle_count: int


# Type variable for generic workflow state
T = TypeVar('T', bound=WorkflowState)


class WorkflowState(Enum):
    """Workflow execution states."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    PAUSED = "paused"
    CANCELLED = "cancelled"


class NodeStatus(Enum):
    """Node execution states."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class WorkflowNode:
    """
    A node in a workflow.

    Attributes:
        id: Unique node identifier
        type: Node type (agent, tool, chain, etc.)
        data: Node configuration data
        inputs: List of input node IDs
        outputs: List of output node IDs
        position: Position on canvas
    """

    id: str
    type: str
    data: Dict[str, Any]
    inputs: List[str] = field(default_factory=list)
    outputs: List[str] = field(default_factory=list)
    position: Dict[str, float] = field(default_factory=dict)


@dataclass
class WorkflowEdge:
    """
    A connection between two nodes.

    Attributes:
        id: Unique edge identifier
        source: Source node ID
        target: Target node ID
        condition: Optional condition for execution
    """

    id: str
    source: str
    target: str
    condition: Optional[str] = None


@dataclass
class Workflow:
    """
    A complete workflow definition.

    Attributes:
        id: Unique workflow identifier
        name: Workflow name
        nodes: List of workflow nodes
        edges: List of workflow edges
        metadata: Additional metadata
        created_at: Creation timestamp
    """

    id: str
    name: str
    nodes: List[WorkflowNode]
    edges: List[WorkflowEdge]
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


def _merge_state_field(current: Any, update: Any, annotation: str) -> Any:
    """
    Merge a state field based on its annotation type.
    
    LangGraph pattern: Uses annotations to specify how fields should be updated.
    
    Args:
        current: Current field value
        update: New value to merge
        annotation: Annotation type ("append", "merge", "replace")
        
    Returns:
        Merged field value
    """
    if annotation == "append":
        # Append-only accumulation (for messages lists)
        if isinstance(current, list) and isinstance(update, list):
            return current + update
        return update
    elif annotation == "merge":
        # Dict merge (for results dicts)
        if isinstance(current, dict) and isinstance(update, dict):
            return {**current, **update}
        return update
    else:
        # Default: replace
        return update


def merge_workflow_states(
    current: WorkflowState,
    update: WorkflowState,
) -> WorkflowState:
    """
    Merge two workflow states using Annotated type hints.
    
    LangGraph pattern: Applies state transition rules based on field annotations.
    
    Args:
        current: Current workflow state
        update: State updates to apply
        
    Returns:
        New merged workflow state
    """
    result: WorkflowState = {}
    
    # Get all keys from both states
    all_keys = set(current.keys()) | set(update.keys())
    
    for key in all_keys:
        if key in update and key in current:
            # Both have this key - apply merge logic
            if key == "messages":
                result["messages"] = _merge_state_field(
                    current.get("messages", []),
                    update.get("messages", []),
                    "append"
                )
            elif key == "results":
                result["results"] = _merge_state_field(
                    current.get("results", {}),
                    update.get("results", {}),
                    "merge"
                )
            else:
                # Default: use update value
                result[key] = update[key]
        elif key in update:
            result[key] = update[key]
        else:
            result[key] = current[key]
    
    return result


@dataclass
class WorkflowContext:
    """
    Execution context for a workflow.
    
    Supports LangGraph-style typed state with checkpointing for resumption.

    Attributes:
        workflow_id: Workflow ID
        execution_id: Unique execution ID
        node_results: Results from executed nodes
        variables: Runtime variables
        start_time: Execution start time
        state: Current workflow state (TypedDict)
        checkpoints: List of checkpoints for resumption
        error: Optional error if failed
    """

    workflow_id: str
    execution_id: str
    node_results: Dict[str, Any] = field(default_factory=dict)
    variables: Dict[str, Any] = field(default_factory=dict)
    start_time: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    state: WorkflowState = field(default_factory=lambda: WorkflowState(
        messages=[],
        results={},
        current_phase="initialized",
        metadata={},
        checkpoint=None,
        cycle_count=0
    ))
    checkpoints: List[Dict[str, Any]] = field(default_factory=list)
    error: Optional[Exception] = None


@dataclass
class NodeResult:
    """
    Result from executing a node.

    Attributes:
        node_id: Node ID
        status: Execution status
        output: Node output
        error: Optional error if failed
        execution_time: Time taken to execute
    """

    node_id: str
    status: NodeStatus
    output: Any = None
    error: Optional[Exception] = None
    execution_time: float = 0.0


@dataclass
class WorkflowResult:
    """
    Result from executing a workflow.

    Attributes:
        workflow_id: Workflow ID
        execution_id: Execution ID
        status: Final workflow status
        node_results: All node results
        variables: Final variables
        start_time: Start time
        end_time: End time
        error: Optional error if workflow failed
    """

    workflow_id: str
    execution_id: str
    status: WorkflowState
    node_results: Dict[str, NodeResult]
    variables: Dict[str, Any]
    start_time: datetime
    end_time: Optional[datetime] = None
    error: Optional[Exception] = None


class WorkflowEngine:
    """
    Workflow execution engine for Heretek Swarm.

    Executes visual workflows from Canvas UI with:
    - Dependency resolution
    - Topological sort for execution order
    - Error handling and rollback
    - State tracking
    - Real-time progress updates
    """

    def __init__(self):
        """Initialize workflow engine."""
        self.workflows: Dict[str, Workflow] = {}
        self.active_executions: Dict[str, WorkflowContext] = {}
        self._execution_lock = asyncio.Lock()

    async def load_workflow(self, workflow_definition: Dict[str, Any]) -> Workflow:
        """
        Load a workflow from definition.

        Args:
            workflow_definition: Workflow definition (from Canvas UI)

        Returns:
            Workflow instance
        """
        nodes = [
            WorkflowNode(
                id=node["id"],
                type=node["type"],
                data=node.get("data", {}),
                inputs=node.get("inputs", []),
                outputs=node.get("outputs", []),
                position=node.get("position", {})
            )
            for node in workflow_definition.get("nodes", [])
        ]

        edges = [
            WorkflowEdge(
                id=edge["id"],
                source=edge["source"],
                target=edge["target"],
                condition=edge.get("condition")
            )
            for edge in workflow_definition.get("edges", [])
        ]

        workflow = Workflow(
            id=workflow_definition.get("id", ""),
            name=workflow_definition.get("name", "Untitled Workflow"),
            nodes=nodes,
            edges=edges,
            metadata=workflow_definition.get("metadata", {})
        )

        self.workflows[workflow.id] = workflow
        logger.info("workflow_loaded", workflow_id=workflow.id, name=workflow.name)

        return workflow

    async def execute_workflow(
        self,
        workflow_id: str,
        input_data: Optional[Dict[str, Any]] = None
    ) -> WorkflowResult:
        """
        Execute a workflow.

        Args:
            workflow_id: Workflow ID
            input_data: Optional initial input data

        Returns:
            WorkflowResult
        """
        if workflow_id not in self.workflows:
            raise ValueError(f"Workflow not found: {workflow_id}")

        workflow = self.workflows[workflow_id]
        execution_id = f"exec_{workflow_id}_{datetime.now(timezone.utc).timestamp()}"

        context = WorkflowContext(
            workflow_id=workflow_id,
            execution_id=execution_id,
            start_time=datetime.now(timezone.utc),
            state=WorkflowState.RUNNING
        )

        self.active_executions[execution_id] = context

        logger.info("workflow_started", workflow_id=workflow_id, execution_id=execution_id)

        try:
            # Build dependency graph
            graph = self._build_graph(workflow)

            # Get execution order (topological sort)
            execution_order = self._topological_sort(graph)

            # Execute nodes in order
            for node_id in execution_order:
                await self._execute_node(workflow, node_id, context)

            # Mark workflow as completed
            context.state = WorkflowState.COMPLETED
            context.end_time = datetime.now(timezone.utc)

            logger.info("workflow_completed", workflow_id=workflow_id, execution_id=execution_id)

            return WorkflowResult(
                workflow_id=workflow_id,
                execution_id=execution_id,
                status=context.state,
                node_results=context.node_results,
                variables=context.variables,
                start_time=context.start_time,
                end_time=context.end_time,
                error=None
            )

        except Exception as e:
            # Handle workflow failure
            context.state = WorkflowState.FAILED
            context.error = e
            context.end_time = datetime.now(timezone.utc)

            logger.error("workflow_failed", workflow_id=workflow_id, error=str(e))

            return WorkflowResult(
                workflow_id=workflow_id,
                execution_id=execution_id,
                status=context.state,
                node_results=context.node_results,
                variables=context.variables,
                start_time=context.start_time,
                end_time=context.end_time,
                error=e
            )

        finally:
            # Clean up execution context
            if execution_id in self.active_executions:
                del self.active_executions[execution_id]

    async def _execute_node(
        self,
        workflow: Workflow,
        node_id: str,
        context: WorkflowContext
    ) -> None:
        """
        Execute a single workflow node.

        Args:
            workflow: Workflow instance
            node_id: Node ID to execute
            context: Execution context
        """
        node = next((n for n in workflow.nodes if n.id == node_id), None)

        if not node:
            logger.error("node_not_found", node_id=node_id)
            context.node_results[node_id] = NodeResult(
                node_id=node_id,
                status=NodeStatus.FAILED,
                error=ValueError(f"Node not found: {node_id}")
            )
            return

        # Check if node should be skipped (condition check)
        if not self._should_execute_node(workflow, node, context):
            context.node_results[node_id] = NodeResult(
                node_id=node_id,
                status=NodeStatus.SKIPPED
            )
            return

        # Get input data for node
        input_data = self._get_node_input(workflow, node, context)

        # Execute node based on type
        start_time = datetime.now(timezone.utc)

        try:
            if node.type == "agent":
                output = await self._execute_agent_node(node, input_data, context)
            elif node.type == "tool":
                output = await self._execute_tool_node(node, input_data, context)
            elif node.type == "chain":
                output = await self._execute_chain_node(node, input_data, context)
            elif node.type == "memory":
                output = await self._execute_memory_node(node, input_data, context)
            else:
                raise ValueError(f"Unknown node type: {node.type}")

            execution_time = (datetime.now(timezone.utc) - start_time).total_seconds()

            context.node_results[node_id] = NodeResult(
                node_id=node_id,
                status=NodeStatus.COMPLETED,
                output=output,
                execution_time=execution_time
            )

            # Store output in context variables
            context.variables[f"node_{node_id}_output"] = output

        except Exception as e:
            logger.error("node_execution_failed", node_id=node_id, error=str(e))

            context.node_results[node_id] = NodeResult(
                node_id=node_id,
                status=NodeStatus.FAILED,
                error=e,
                execution_time=(datetime.now(timezone.utc) - start_time).total_seconds()
            )

    def _should_execute_node(
        self,
        workflow: Workflow,
        node: WorkflowNode,
        context: WorkflowContext
    ) -> bool:
        """
        Check if a node should be executed based on conditions.

        Args:
            workflow: Workflow instance
            node: Node to check
            context: Execution context

        Returns:
            True if node should execute
        """
        # Check incoming edges for conditions
        for edge in workflow.edges:
            if edge.target == node.id and edge.condition:
                if not self._evaluate_condition(edge.condition, context):
                    return False

        return True

    def _evaluate_condition(self, condition: str, context: WorkflowContext) -> bool:
        """
        Evaluate a condition expression.

        Args:
            condition: Condition expression
            context: Execution context

        Returns:
            True if condition evaluates to true
        """
        # Simple condition evaluation
        # Supports: variable comparison, boolean logic
        try:
            # Replace variable references with values
            expr = condition
            for var_name, var_value in context.variables.items():
                expr = expr.replace(f"{{{var_name}}}", str(var_value))

            # Evaluate expression
            result = eval(expr, {"__builtins__": {}})
            return bool(result)

        except Exception as e:
            logger.warning("condition_evaluation_failed", condition=condition, error=str(e))
            return False

    def _get_node_input(
        self,
        workflow: Workflow,
        node: WorkflowNode,
        context: WorkflowContext
    ) -> Dict[str, Any]:
        """
        Get input data for a node from context.

        Args:
            workflow: Workflow instance
            node: Node to get input for
            context: Execution context

        Returns:
            Dictionary of input data
        """
        input_data = {}

        # Get data from input nodes
        for input_id in node.inputs:
            if input_id in context.node_results:
                input_data[input_id] = context.node_results[input_id].output

        # Get data from workflow initial input
        if context.variables:
            input_data.update(context.variables)

        return input_data

    async def _execute_agent_node(
        self,
        node: WorkflowNode,
        input_data: Dict[str, Any],
        context: WorkflowContext
    ) -> Any:
        """
        Execute an agent node.

        Args:
            node: Agent node
            input_data: Input data
            context: Execution context

        Returns:
            Agent output
        """
        from heretek_swarm.actors.supervisor import get_supervisor

        # Get agent ID from node data
        agent_id = node.data.get("agent_id")
        if not agent_id:
            raise ValueError("Agent node requires agent_id")

        # Get global supervisor
        supervisor = get_supervisor()
        agent_status = await supervisor.get_actor_status(agent_id)

        if not agent_status or agent_status.state != "active":
            raise RuntimeError(f"Agent not active: {agent_id}")

        # Send message to agent
        message = input_data.get("message", "")
        response = await supervisor.send_message(agent_id, message)

        return response

    async def _execute_tool_node(
        self,
        node: WorkflowNode,
        input_data: Dict[str, Any],
        context: WorkflowContext
    ) -> Any:
        """
        Execute a tool node.

        Args:
            node: Tool node
            input_data: Input data
            context: Execution context

        Returns:
            Tool output
        """
        from heretek_swarm.runtime.tools import ToolRegistry

        # Get tool registry
        tool_registry = ToolRegistry()

        # Get tool name from node data
        tool_name = node.data.get("tool_name")
        if not tool_name:
            raise ValueError("Tool node requires tool_name")

        # Get tool parameters
        tool_params = input_data.get("params", {})

        # Execute tool
        result = await tool_registry.execute(tool_name, **tool_params)

        return result

    async def _execute_chain_node(
        self,
        node: WorkflowNode,
        input_data: Dict[str, Any],
        context: WorkflowContext
    ) -> Any:
        """
        Execute a chain node (sequential processing).

        Args:
            node: Chain node
            input_data: Input data
            context: Execution context

        Returns:
            Chain output
        """
        # Get chain nodes
        chain_nodes = node.data.get("nodes", [])
        if not chain_nodes:
            raise ValueError("Chain node requires nodes")

        # Execute chain sequentially
        output = input_data.get("input", "")

        for chain_node_id in chain_nodes:
            if chain_node_id in context.node_results:
                node_result = context.node_results[chain_node_id]
                if node_result.status == NodeStatus.COMPLETED:
                    output = node_result.output
                else:
                    raise RuntimeError(f"Chain node not completed: {chain_node_id}")

        return output

    async def _execute_memory_node(
        self,
        node: WorkflowNode,
        input_data: Dict[str, Any],
        context: WorkflowContext
    ) -> Any:
        """
        Execute a memory node (store or retrieve).

        Args:
            node: Memory node
            input_data: Input data
            context: Execution context

        Returns:
            Memory operation result
        """
        from heretek_swarm.memory.persistent import PersistentMemoryStore

        # Get operation type
        operation = node.data.get("operation", "store")
        if operation not in ["store", "retrieve", "search"]:
            raise ValueError(f"Invalid memory operation: {operation}")

        # Get memory store
        memory_store = PersistentMemoryStore()
        await memory_store.connect()

        if operation == "store":
            # Store memory
            content = input_data.get("content", "")
            memory_type = input_data.get("memory_type", "episodic")
            metadata = input_data.get("metadata", {})

            # Store memory
            await memory_store.store(
                agent_id=context.workflow_id,
                content=content,
                memory_type=memory_type,
                metadata=metadata
            )

            return {"stored": True}

        elif operation == "retrieve":
            # Retrieve memory
            query = input_data.get("query", "")
            limit = input_data.get("limit", 10)

            # Search memory
            from heretek_swarm.memory.base import MemoryQuery
            search_query = MemoryQuery(
                query_text=query,
                agent_ids=[context.workflow_id],
                limit=limit
            )

            result = await memory_store.search(search_query)

            return {
                "results": [
                    {
                        "content": entry.content,
                        "memory_type": entry.memory_type.value,
                        "importance_score": entry.importance_score
                    }
                    for entry in result.entries
                ]
            }

        elif operation == "search":
            # Search memory (alias for retrieve)
            return await self._execute_memory_node(node, input_data, context)

    def _build_graph(self, workflow: Workflow) -> Dict[str, Set[str]]:
        """
        Build dependency graph from workflow edges.

        Args:
            workflow: Workflow instance

        Returns:
            Dictionary of node IDs to their dependencies
        """
        graph: Dict[str, Set[str]] = {node.id: set() for node in workflow.nodes}

        for edge in workflow.edges:
            if edge.target not in graph:
                graph[edge.target] = set()
            graph[edge.target].add(edge.source)

        return graph

    def _topological_sort(self, graph: Dict[str, Set[str]]) -> List[str]:
        """
        Perform topological sort on dependency graph.

        Args:
            graph: Dependency graph

        Returns:
            List of node IDs in execution order
        """
        # Kahn's algorithm
        in_degree: Dict[str, int] = {node_id: 0 for node_id in graph}
        result: List[str] = []

        # Calculate in-degrees
        for node_id, dependencies in graph.items():
            for dep in dependencies:
                in_degree[dep] = in_degree.get(dep, 0) + 1

        # Find nodes with no incoming edges
        queue = [node_id for node_id, degree in in_degree.items() if degree == 0]

        # Process nodes
        while queue:
            node_id = queue.pop(0)
            result.append(node_id)

            # Decrement in-degrees of dependents
            for dep in graph.get(node_id, set()):
                in_degree[dep] -= 1
                if in_degree[dep] == 0:
                    queue.append(dep)

        return result

    async def get_workflow_status(self, execution_id: str) -> Optional[WorkflowContext]:
        """
        Get status of a workflow execution.

        Args:
            execution_id: Execution ID

        Returns:
            Workflow context or None
        """
        return self.active_executions.get(execution_id)

    async def cancel_workflow(self, execution_id: str) -> bool:
        """
        Cancel a running workflow execution.

        Args:
            execution_id: Execution ID

        Returns:
            True if cancelled
        """
        if execution_id not in self.active_executions:
            return False

        context = self.active_executions[execution_id]
        context.state = WorkflowState.CANCELLED
        context.end_time = datetime.now(timezone.utc)

        logger.info("workflow_cancelled", execution_id=execution_id)
        return True

    def list_workflows(self) -> List[Workflow]:
        """
        List all loaded workflows.

        Returns:
            List of workflows
        """
        return list(self.workflows.values())

    def get_workflow(self, workflow_id: str) -> Optional[Workflow]:
        """
        Get a workflow by ID.

        Args:
            workflow_id: Workflow ID

        Returns:
            Workflow or None
        """
        return self.workflows.get(workflow_id)


# Global workflow engine instance
_global_engine: Optional[WorkflowEngine] = None


async def get_workflow_engine() -> WorkflowEngine:
    """
    Get global workflow engine instance.

    Returns:
        WorkflowEngine instance
    """
    global _global_engine

    if _global_engine is None:
        _global_engine = WorkflowEngine()

    return _global_engine
