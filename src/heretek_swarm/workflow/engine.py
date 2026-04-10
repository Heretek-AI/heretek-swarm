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
import ast
import operator
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Set, TypeVar, Annotated
from dataclasses import dataclass, field
from enum import Enum
from typing_extensions import TypedDict

import structlog

logger = structlog.get_logger(__name__)

# Import cycle detection
try:
    from .cycle_detector import WorkflowCycleDetector, FivePhaseWorkflowTracker
except ImportError:
    WorkflowCycleDetector = None  # type: ignore
    FivePhaseWorkflowTracker = None  # type: ignore

# Safe operators for comparison and boolean logic
SAFE_OPERATORS = {
    ast.Eq: operator.eq,
    ast.NotEq: operator.ne,
    ast.Lt: operator.lt,
    ast.LtE: operator.le,
    ast.Gt: operator.gt,
    ast.GtE: operator.ge,
    ast.Is: operator.is_,
    ast.IsNot: operator.is_not,
    ast.In: lambda x, y: x in y,
    ast.NotIn: lambda x, y: x not in y,
}

SAFE_BOOL_OPS = {
    ast.And: lambda x, y: x and y,
    ast.Or: lambda x, y: x or y,
}

SAFE_UNARY_OPS = {
    ast.Not: operator.not_,
    ast.USub: operator.neg,
    ast.UAdd: operator.pos,
}


class SafeExpressionEvaluator:
    """
    Safe expression evaluator using AST validation.
    
    This class provides a secure alternative to eval() by:
    1. Parsing expressions into an AST
    2. Validating that only safe node types are present
    3. Rejecting dangerous operations (function calls, attribute access, imports)
    4. Safely evaluating the validated AST
    
    Supported operations:
    - Literal values (numbers, strings, booleans, None, lists, dicts, tuples)
    - Comparison operators (==, !=, <, <=, >, >=, is, in)
    - Boolean operators (and, or, not)
    - Unary operators (+, -, not)
    - Variable substitution (via context)
    
    Security: Prevents code injection through object introspection attacks
    by never allowing execution of arbitrary Python code.
    """
    
    # AST node types that are safe to evaluate
    SAFE_NODE_TYPES = (
        ast.Expression,
        ast.Constant,  # Literal values (Python 3.8+)
        ast.Num,       # Numbers (deprecated but for compatibility)
        ast.Str,       # Strings (deprecated but for compatibility)
        ast.NameConstant,  # True, False, None (deprecated but for compatibility)
        ast.List,
        ast.Tuple,
        ast.Dict,
        ast.Compare,
        ast.BoolOp,
        ast.UnaryOp,
        ast.BinOp,
        ast.Name,  # Variable names (validated against allowed context)
        ast.Subscript,  # Indexing (e.g., list[0], dict['key'])
        # Context nodes (required for variable access)
        ast.Load,
        ast.Store,
        ast.Del,
        # Boolean operator nodes
        ast.And,
        ast.Or,
        # Comparison operator nodes
        ast.Eq,
        ast.NotEq,
        ast.Lt,
        ast.LtE,
        ast.Gt,
        ast.GtE,
        ast.Is,
        ast.IsNot,
        ast.In,
        ast.NotIn,
        # Binary operator nodes
        ast.Add,
        ast.Sub,
        ast.Mult,
        ast.Div,
        ast.FloorDiv,
        ast.Mod,
        ast.Pow,
        # Unary operator nodes
        ast.Not,
        ast.USub,
        ast.UAdd,
    )
    
    # Safe binary operators
    SAFE_BIN_OPS = {
        ast.Add: operator.add,
        ast.Sub: operator.sub,
        ast.Mult: operator.mul,
        ast.Div: operator.truediv,
        ast.FloorDiv: operator.floordiv,
        ast.Mod: operator.mod,
        ast.Pow: operator.pow,
    }
    
    def __init__(self, allowed_variables: Optional[Dict[str, Any]] = None):
        """
        Initialize the evaluator with allowed variables.
        
        Args:
            allowed_variables: Dict of variable names to values that can be
                               referenced in expressions
        """
        self.allowed_variables = allowed_variables or {}
    
    def validate_and_eval(self, expr: str) -> Any:
        """
        Safely validate and evaluate an expression.
        
        Args:
            expr: Expression string to evaluate
            
        Returns:
            Result of the evaluation
            
        Raises:
            ValueError: If expression contains unsafe operations
            SyntaxError: If expression is not valid Python syntax
        """
        # Parse the expression into an AST
        try:
            tree = ast.parse(expr, mode='eval')
        except SyntaxError as e:
            raise ValueError(f"Invalid expression syntax: {e}")
        
        # Validate the AST contains only safe nodes
        self._validate_ast(tree)
        
        # Safely evaluate the validated AST
        return self._eval_node(tree.body)
    
    def _validate_ast(self, node: ast.AST) -> None:
        """
        Recursively validate that an AST contains only safe node types.
        
        Args:
            node: AST node to validate
            
        Raises:
            ValueError: If node contains unsafe operations
        """
        # Check if this node type is safe
        if not isinstance(node, self.SAFE_NODE_TYPES):
            raise ValueError(
                f"Unsafe node type '{type(node).__name__}' in expression. "
                f"Only literals, comparisons, and boolean logic are allowed."
            )
        
        # Special validation for Name nodes (variable access)
        if isinstance(node, ast.Name):
            if node.id not in self.allowed_variables:
                raise ValueError(
                    f"Variable '{node.id}' is not in the allowed variables list. "
                    f"Allowed: {list(self.allowed_variables.keys())}"
                )
        
        # Recursively validate all child nodes
        for field, value in ast.iter_fields(node):
            if isinstance(value, list):
                for item in value:
                    if isinstance(item, ast.AST):
                        self._validate_ast(item)
            elif isinstance(value, ast.AST):
                self._validate_ast(value)
    
    def _eval_node(self, node: ast.AST) -> Any:
        """
        Recursively evaluate a validated AST node.
        
        Args:
            node: AST node to evaluate
            
        Returns:
            Result of evaluating the node
            
        Raises:
            ValueError: If node type is not supported
        """
        # Handle literal values
        if isinstance(node, ast.Constant):  # Python 3.8+
            return node.value
        elif isinstance(node, ast.Num):  # Deprecated, for compatibility
            return node.n
        elif isinstance(node, ast.Str):  # Deprecated, for compatibility
            return node.s
        elif isinstance(node, ast.NameConstant):  # Deprecated, for compatibility
            return node.value
        
        # Handle variable references
        elif isinstance(node, ast.Name):
            return self.allowed_variables[node.id]
        
        # Handle lists
        elif isinstance(node, ast.List):
            return [self._eval_node(elt) for elt in node.elts]
        
        # Handle tuples
        elif isinstance(node, ast.Tuple):
            return tuple(self._eval_node(elt) for elt in node.elts)
        
        # Handle dicts
        elif isinstance(node, ast.Dict):
            return {
                self._eval_node(k): self._eval_node(v)
                for k, v in zip(node.keys, node.values)
                if k is not None
            }
        
        # Handle comparison operations
        elif isinstance(node, ast.Compare):
            left = self._eval_node(node.left)
            result = True
            for op, comparator in zip(node.ops, node.comparators):
                op_func = SAFE_OPERATORS.get(type(op))
                if op_func is None:
                    raise ValueError(f"Unsupported comparison operator: {type(op).__name__}")
                right = self._eval_node(comparator)
                result = result and op_func(left, right)
                left = right
            return result
        
        # Handle boolean operations (and, or)
        elif isinstance(node, ast.BoolOp):
            op_func = SAFE_BOOL_OPS.get(type(node.op))
            if op_func is None:
                raise ValueError(f"Unsupported boolean operator: {type(node.op).__name__}")
            result = self._eval_node(node.values[0])
            for value in node.values[1:]:
                result = op_func(result, self._eval_node(value))
            return result
        
        # Handle unary operations (not, -, +)
        elif isinstance(node, ast.UnaryOp):
            op_func = SAFE_UNARY_OPS.get(type(node.op))
            if op_func is None:
                raise ValueError(f"Unsupported unary operator: {type(node.op).__name__}")
            return op_func(self._eval_node(node.operand))
        
        # Handle binary operations (+, -, *, /, etc.)
        elif isinstance(node, ast.BinOp):
            op_func = self.SAFE_BIN_OPS.get(type(node.op))
            if op_func is None:
                raise ValueError(f"Unsupported binary operator: {type(node.op).__name__}")
            left = self._eval_node(node.left)
            right = self._eval_node(node.right)
            return op_func(left, right)
        
        # Handle subscript (indexing)
        elif isinstance(node, ast.Subscript):
            value = self._eval_node(node.value)
            slice_val = self._eval_node(node.slice)
            return value[slice_val]
        
        else:
            raise ValueError(f"Unsupported node type: {type(node).__name__}")


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

    def __init__(
        self,
        cycle_detector: Optional[WorkflowCycleDetector] = None,
        max_iterations: int = 100,
        timeout_seconds: float = 300.0,
    ):
        """
        Initialize workflow engine.
        
        Args:
            cycle_detector: Optional pre-configured cycle detector
            max_iterations: Maximum iterations before cycle break (if no detector provided)
            timeout_seconds: Timeout in seconds before cycle break (if no detector provided)
        """
        self.workflows: Dict[str, Workflow] = {}
        self.active_executions: Dict[str, WorkflowContext] = {}
        self._execution_lock = asyncio.Lock()
        
        # Cycle detection integration
        self.cycle_detector = cycle_detector or WorkflowCycleDetector(
            max_iterations=max_iterations,
            timeout_seconds=timeout_seconds,
        )
        self.phase_tracker = FivePhaseWorkflowTracker()

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
        Execute a workflow with cycle detection.

        Args:
            workflow_id: Workflow ID
            input_data: Optional initial input data

        Returns:
            WorkflowResult
            
        Cycle Detection:
            - Tracks execution path through workflow nodes
            - Detects cycles using path-based and node-visit analysis
            - Breaks cycles using configured strategies (max iterations, timeout, convergence)
            - Logs all cycle events with correlation IDs for audit trails
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

        # Initialize cycle detection for this workflow
        self.cycle_detector.start_workflow_tracking(execution_id)

        logger.info("workflow_started", workflow_id=workflow_id, execution_id=execution_id)

        try:
            # Build dependency graph
            graph = self._build_graph(workflow)

            # Get execution order (topological sort)
            execution_order = self._topological_sort(graph)

            # Execute nodes in order with cycle detection
            from heretek_swarm.workflow.cycle_detector import CycleBreakingStrategy

            for node_id in execution_order:
                # Check for cycles before executing node
                if self.cycle_detector.detect_cycle(execution_id, node_id):
                    if self.cycle_detector.should_break_cycle(execution_id):
                        # Break cycle and log event
                        event = self.cycle_detector.break_cycle(
                            execution_id,
                            CycleBreakingStrategy.MAX_ITERATIONS,
                            reason=f"Cycle detected at node {node_id}"
                        )
                        logger.warning(
                            "cycle_broken_during_execution",
                            workflow_id=workflow_id,
                            execution_id=execution_id,
                            node_id=node_id,
                            event_id=event.event_id,
                        )
                        # Skip this node to break the cycle
                        context.node_results[node_id] = NodeResult(
                            node_id=node_id,
                            status=NodeStatus.SKIPPED,
                            output=None,
                            error=Exception(f"Node skipped due to cycle detection: {node_id}")
                        )
                        continue
                
                # Record node execution for tracking
                self.cycle_detector.record_node_execution(
                    execution_id,
                    node_id,
                    state={"node": node_id, "phase": "execution"}
                )

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
            # Clean up execution context and cycle tracking
            self.cycle_detector.stop_workflow_tracking(execution_id)
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
        Evaluate a condition expression using safe AST-based evaluator.

        Args:
            condition: Condition expression
            context: Execution context

        Returns:
            True if condition evaluates to true
            
        Security: Uses SafeExpressionEvaluator to prevent code injection attacks
        through object introspection. The old eval() implementation was vulnerable
        to attacks via __class__, __mro__, __subclasses__(), etc.
        """
        # Create safe evaluator with context variables
        evaluator = SafeExpressionEvaluator(allowed_variables=context.variables)
        
        try:
            # Safely evaluate the condition expression
            result = evaluator.validate_and_eval(condition)
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


async def get_workflow_engine(
    cycle_detector: Optional[WorkflowCycleDetector] = None,
    max_iterations: int = 100,
    timeout_seconds: float = 300.0,
) -> WorkflowEngine:
    """
    Get global workflow engine instance with cycle detection.

    Args:
        cycle_detector: Optional pre-configured cycle detector
        max_iterations: Maximum iterations before cycle break
        timeout_seconds: Timeout in seconds before cycle break

    Returns:
        WorkflowEngine instance
    """
    global _global_engine

    if _global_engine is None:
        _global_engine = WorkflowEngine(
            cycle_detector=cycle_detector,
            max_iterations=max_iterations,
            timeout_seconds=timeout_seconds,
        )

    return _global_engine


def get_cycle_detector_metrics() -> Dict[str, Any]:
    """
    Get cycle detection metrics from global engine.

    Returns:
        Dictionary of cycle detection metrics
    """
    if _global_engine and hasattr(_global_engine, 'cycle_detector'):
        return _global_engine.cycle_detector.get_metrics()
    return {}


def export_cycle_detector_prometheus() -> str:
    """
    Export cycle detection metrics in Prometheus format.

    Returns:
        Prometheus-formatted metrics string
    """
    if _global_engine and hasattr(_global_engine, 'cycle_detector'):
        return _global_engine.cycle_detector.export_prometheus_metrics()
    return "# No cycle detector available\n"
