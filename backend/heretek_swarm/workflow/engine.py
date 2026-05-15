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
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

import structlog

from heretek_swarm.workflow.models import (
    NodeResult,
    NodeStatus,
    SafeExpressionEvaluator,
    Workflow,
    WorkflowContext,
    WorkflowEdge,
    WorkflowNode,
    WorkflowResult,
    WorkflowState,
    WorkflowStatus,
    merge_workflow_states,
)
from heretek_swarm.workflow.store import FileWorkflowStore

if TYPE_CHECKING:
    from heretek_swarm.workflow.strategies import WorkflowExecutionResult


logger = structlog.get_logger(__name__)

# Import cycle detection
try:
    from .cycle_detector import FivePhaseWorkflowTracker, WorkflowCycleDetector
except ImportError:
    WorkflowCycleDetector = None  # type: ignore
    FivePhaseWorkflowTracker = None  # type: ignore
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
        cycle_detector: WorkflowCycleDetector | None = None,
        max_iterations: int = 100,
        timeout_seconds: float = 300.0,
        consensus_coordinator: Any | None = None,
        supervisor: Any | None = None,
        store: FileWorkflowStore | None = None,
    ):
        """
        Initialize workflow engine.

        Args:
            cycle_detector: Optional pre-configured cycle detector
            max_iterations: Maximum iterations before cycle break (if no detector provided)
            timeout_seconds: Timeout in seconds before cycle break (if no detector provided)
            consensus_coordinator: Optional ConsensusCoordinator for consensus node type
            supervisor: Optional ActorSupervisor for consensus agent resolution
            store: Optional FileWorkflowStore for disk persistence. If None, a
                   default store is created at ~/.heretek-swarm/workflows.json.
        """
        self.workflows: dict[str, Workflow] = {}
        self.active_executions: dict[str, WorkflowContext] = {}
        self._execution_lock = asyncio.Lock()

        # Persistence store
        self.store = store or FileWorkflowStore()

        # Cycle detection integration
        self.cycle_detector = cycle_detector or WorkflowCycleDetector(
            max_iterations=max_iterations,
            timeout_seconds=timeout_seconds,
        )
        self.phase_tracker = FivePhaseWorkflowTracker()

        # Consensus integration (optional)
        self._consensus_coordinator = consensus_coordinator
        self._supervisor = supervisor

    async def load_workflow(self, workflow_definition: dict[str, Any]) -> Workflow:
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
                position=node.get("position", {}),
            )
            for node in workflow_definition.get("nodes", [])
        ]

        edges = [
            WorkflowEdge(
                id=edge["id"],
                source=edge["source"],
                target=edge["target"],
                condition=edge.get("condition"),
            )
            for edge in workflow_definition.get("edges", [])
        ]

        workflow = Workflow(
            id=workflow_definition.get("id", ""),
            name=workflow_definition.get("name", "Untitled Workflow"),
            nodes=nodes,
            edges=edges,
            metadata=workflow_definition.get("metadata", {}),
        )

        self.workflows[workflow.id] = workflow

        # Persist to disk
        self.store.save(workflow.id, workflow_definition)

        logger.info("workflow_loaded", workflow_id=workflow.id, name=workflow.name)

        return workflow

    async def execute_workflow(
        self,
        workflow_id: str,
        input_data: dict[str, Any] | None = None,  # noqa: ARG002
        strategy: str = "dag",
    ) -> WorkflowResult:
        """
        Execute a workflow with cycle detection.

        Args:
            workflow_id: Workflow ID
            input_data: Optional initial input data
            strategy: Execution strategy - "dag", "cycle", or "majority_vote"
                      Defaults to "dag" (topological sort).

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
        execution_id = f"exec_{workflow_id}_{datetime.now(UTC).timestamp()}"

        context = WorkflowContext(
            workflow_id=workflow_id,
            execution_id=execution_id,
            start_time=datetime.now(UTC),
            state=WorkflowStatus.RUNNING,
        )

        self.active_executions[execution_id] = context

        # Initialize cycle detection for this workflow
        self.cycle_detector.start_workflow_tracking(execution_id)

        logger.info("workflow_started", workflow_id=workflow_id, execution_id=execution_id)

        try:
            # Route to execution strategy
            if strategy == "majority_vote":
                from heretek_swarm.workflow.strategies import (
                    MajorityVoteStrategy,
                    WorkflowExecutionResult,
                )

                strat = MajorityVoteStrategy()

                async def node_executor(nid: str, ndata: dict) -> Any:
                    node = next(n for n in workflow.nodes if n.id == nid)
                    return await self._execute_and_capture(workflow, nid, context, node)

                strat_result: WorkflowExecutionResult = await strat.execute(
                    workflow,
                    {"execution_id": execution_id, "elapsed": 0.0},
                    node_executor,
                )
                # Convert strategy result to WorkflowResult
                return self._strategy_result_to_result(strat_result, context)
            if strategy == "cycle":
                from heretek_swarm.workflow.strategies import CycleStrategy

                strat = CycleStrategy(
                    max_iterations=self.max_iterations, timeout_seconds=self.timeout_seconds
                )

                async def node_executor(nid: str, ndata: dict) -> Any:
                    node = next(n for n in workflow.nodes if n.id == nid)
                    return await self._execute_and_capture(workflow, nid, context, node)

                strat_result = await strat.execute(
                    workflow,
                    {"execution_id": execution_id, "elapsed": 0.0},
                    node_executor,
                )
                return self._strategy_result_to_result(strat_result, context)

            # Default: DAG (topological sort)
            graph = self._build_graph(workflow)
            execution_order = self._topological_sort(graph)

            # Execute nodes in order with cycle detection
            from heretek_swarm.workflow.cycle_detector import CycleBreakingStrategy

            for node_id in execution_order:
                # Check for cycles before executing node
                if self.cycle_detector.detect_cycle(execution_id, node_id):  # noqa: SIM102
                    if self.cycle_detector.should_break_cycle(execution_id):
                        # Break cycle and log event
                        event = self.cycle_detector.break_cycle(
                            execution_id,
                            CycleBreakingStrategy.MAX_ITERATIONS,
                            reason=f"Cycle detected at node {node_id}",
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
                            error=Exception(f"Node skipped due to cycle detection: {node_id}"),
                        )
                        continue

                # Record node execution for tracking
                self.cycle_detector.record_node_execution(
                    execution_id, node_id, state={"node": node_id, "phase": "execution"}
                )

                await self._execute_node(workflow, node_id, context)

            # Mark workflow as completed
            context.state = WorkflowStatus.COMPLETED
            context.end_time = datetime.now(UTC)

            logger.info("workflow_completed", workflow_id=workflow_id, execution_id=execution_id)

            return WorkflowResult(
                workflow_id=workflow_id,
                execution_id=execution_id,
                status=context.state,
                node_results=context.node_results,
                variables=context.variables,
                start_time=context.start_time,
                end_time=context.end_time,
                error=None,
            )

        except Exception as e:
            # Handle workflow failure
            context.state = WorkflowStatus.FAILED
            context.error = e
            context.end_time = datetime.now(UTC)

            logger.error("workflow_failed", workflow_id=workflow_id, error=str(e))

            return WorkflowResult(
                workflow_id=workflow_id,
                execution_id=execution_id,
                status=context.state,
                node_results=context.node_results,
                variables=context.variables,
                start_time=context.start_time,
                end_time=context.end_time,
                error=e,
            )

        finally:
            # Clean up execution context and cycle tracking
            self.cycle_detector.stop_workflow_tracking(execution_id)
            if execution_id in self.active_executions:
                del self.active_executions[execution_id]

    async def _execute_node(
        self, workflow: Workflow, node_id: str, context: WorkflowContext
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
                error=ValueError(f"Node not found: {node_id}"),
            )
            return

        # Check if node should be skipped (condition check)
        if not self._should_execute_node(workflow, node, context):
            context.node_results[node_id] = NodeResult(node_id=node_id, status=NodeStatus.SKIPPED)
            return

        # Get input data for node
        input_data = self._get_node_input(workflow, node, context)

        # Execute node based on type
        start_time = datetime.now(UTC)

        try:
            if node.type == "agent":
                output = await self._execute_agent_node(node, input_data, context)
            elif node.type == "tool":
                output = await self._execute_tool_node(node, input_data, context)
            elif node.type == "chain":
                output = await self._execute_chain_node(node, input_data, context)
            elif node.type == "memory":
                output = await self._execute_memory_node(node, input_data, context)
            elif node.type == "consensus":
                output = await self._execute_consensus_node(node, input_data, context)
            elif node.type == "llm":
                output = await self._execute_llm_node(node, input_data, context)
            else:
                raise ValueError(f"Unknown node type: {node.type}")

            execution_time = (datetime.now(UTC) - start_time).total_seconds()

            context.node_results[node_id] = NodeResult(
                node_id=node_id,
                status=NodeStatus.COMPLETED,
                output=output,
                execution_time=execution_time,
            )

            # Store output in context variables
            context.variables[f"node_{node_id}_output"] = output

        except Exception as e:
            logger.error("node_execution_failed", node_id=node_id, error=str(e))

            context.node_results[node_id] = NodeResult(
                node_id=node_id,
                status=NodeStatus.FAILED,
                error=e,
                execution_time=(datetime.now(UTC) - start_time).total_seconds(),
            )

    async def _execute_and_capture(
        self,
        workflow: Workflow,
        node_id: str,
        context: WorkflowContext,
        node: WorkflowNode,
    ) -> Any:
        """
        Execute a node and capture the result.

        Used by strategy wrappers to capture results without writing to context.
        Returns the output directly for strategy aggregation.
        """
        input_data = self._get_node_input(workflow, node, context)
        datetime.now(UTC)

        try:
            if node.type == "agent":
                return await self._execute_agent_node(node, input_data, context)
            if node.type == "tool":
                return await self._execute_tool_node(node, input_data, context)
            if node.type == "chain":
                return await self._execute_chain_node(node, input_data, context)
            if node.type == "memory":
                return await self._execute_memory_node(node, input_data, context)
            if node.type == "consensus":
                return await self._execute_consensus_node(node, input_data, context)
            if node.type == "llm":
                return await self._execute_llm_node(node, input_data, context)
            return {"error": f"Unknown node type: {node.type}"}
        except Exception as e:
            logger.error("node_execution_failed", node_id=node_id, error=str(e))
            return {"error": str(e)}

    def _strategy_result_to_result(
        self,
        strat_result: "WorkflowExecutionResult",
        context: WorkflowContext,
    ) -> WorkflowResult:
        """
        Convert a strategy-level WorkflowExecutionResult to a WorkflowResult.

        Args:
            strat_result: Result from execution strategy
            context: Execution context

        Returns:
            WorkflowResult matching the engine's dataclass schema
        """
        # Map strategy node results (raw values) to NodeResult objects
        node_result_map: dict[str, NodeResult] = {}
        for nid, val in strat_result.node_results.items():
            status = NodeStatus.COMPLETED
            if isinstance(val, dict) and "error" in val:
                status = NodeStatus.FAILED
            node_result_map[nid] = NodeResult(
                node_id=nid,
                status=status,
                output=val,
            )

        return WorkflowResult(
            workflow_id=strat_result.workflow_id,
            execution_id=context.execution_id,
            status=WorkflowStatus.COMPLETED if strat_result.success else WorkflowStatus.FAILED,
            node_results=node_result_map,
            variables=context.variables,
            start_time=context.start_time,
            end_time=datetime.now(UTC),
            error=Exception(strat_result.error_message) if strat_result.error_message else None,
        )

    def _should_execute_node(
        self, workflow: Workflow, node: WorkflowNode, context: WorkflowContext
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
            if edge.target == node.id and edge.condition:  # noqa: SIM102
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
        self, workflow: Workflow, node: WorkflowNode, context: WorkflowContext  # noqa: ARG002
    ) -> dict[str, Any]:
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
        self, node: WorkflowNode, input_data: dict[str, Any], context: WorkflowContext
    ) -> Any:
        """
        Execute an agent node.

        Looks up the actor from the supervisor's actor registry and calls
        run_with_llm() with the prompt from input_data.

        Args:
            node: Agent node
            input_data: Input data
            context: Execution context

        Returns:
            Agent output (string from LLM)

        Raises:
            ValueError: If agent_id is missing from node.data
            RuntimeError: If the agent is not found or not active
        """
        from heretek_swarm.actors.supervisor import get_supervisor

        # Get agent ID from node data
        agent_id = node.data.get("agent_id")
        if not agent_id:
            raise ValueError("Agent node requires agent_id")

        # Use injected supervisor or fall back to global singleton
        supervisor = self._supervisor or get_supervisor()

        # Look up the actor directly from the registry
        actor = supervisor.actors.get(agent_id)
        if actor is None:
            raise RuntimeError(f"Agent not found: {agent_id}")

        agent_status = await supervisor.get_actor_status(agent_id)
        if not agent_status or agent_status.state != "active":
            raise RuntimeError(f"Agent not active: {agent_id}")

        # Build prompt from input_data — prefer explicit prompt, fall back to message
        # then to upstream node output stored in context.variables
        prompt = (
            input_data.get("prompt")
            or input_data.get("message")
            or input_data.get(agent_id)
            or context.variables.get("prompt")
            or context.variables.get("message")
        )
        # If still no prompt, check for any upstream node output stored by _execute_node
        if not prompt:
            for key, val in context.variables.items():
                if key.startswith("node_") and key.endswith("_output") and isinstance(val, str):
                    prompt = val
                    break
        if not prompt:
            raise ValueError("Agent node requires a prompt or message in input_data")

        # Optional timeout override from node config
        timeout = node.data.get("timeout", 60)

        logger.info(
            "agent_node_started",
            workflow_id=context.workflow_id,
            node_id=node.id,
            agent_id=agent_id,
            prompt_length=len(prompt),
        )

        return await actor.run_with_llm(prompt, timeout=timeout)

    async def _execute_llm_node(
        self,
        node: WorkflowNode,
        input_data: dict[str, Any],
        context: WorkflowContext,
    ) -> str:
        """
        Execute a standalone LLM node.

        Runs a prompt through the LLM without requiring a pre-spawned actor.
        Uses the supervisor's first available active actor as the LLM conduit,
        or raises if none are available.

        Args:
            node: LLM node with data.prompt, optional data.model
            input_data: Input data from upstream nodes
            context: Execution context

        Returns:
            LLM response string

        Raises:
            ValueError: If no prompt is provided
            RuntimeError: If no active actor is available for LLM execution
        """
        from heretek_swarm.actors.supervisor import get_supervisor

        # Extract prompt: prefer node.data, fall back to input_data
        prompt = (
            node.data.get("prompt") or input_data.get("prompt") or input_data.get("message", "")
        )
        if not prompt:
            raise ValueError("LLM node requires a 'prompt' in node.data or input_data")

        # Optional parameters from node config
        timeout = node.data.get("timeout", 60)
        temperature = node.data.get("temperature")

        # Use injected supervisor or fall back to global singleton
        supervisor = self._supervisor or get_supervisor()

        # Find an active actor to serve as the LLM conduit
        actor = None
        for actor_id, candidate in supervisor.actors.items():
            status = await supervisor.get_actor_status(actor_id)
            if status and status.state == "active":
                actor = candidate
                break

        if actor is None:
            raise RuntimeError(
                "LLM node requires at least one active actor in the supervisor "
                "to serve as an LLM conduit."
            )

        logger.info(
            "llm_node_started",
            workflow_id=context.workflow_id,
            node_id=node.id,
            actor_id=actor.agent_id,
            prompt_length=len(prompt),
            temperature=temperature,
        )

        kwargs: dict[str, Any] = {}
        if temperature is not None:
            kwargs["temperature"] = temperature

        return await actor.run_with_llm(prompt, timeout=timeout, **kwargs)

    async def _execute_tool_node(
        self, node: WorkflowNode, input_data: dict[str, Any], context: WorkflowContext  # noqa: ARG002
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
        return await tool_registry.execute(tool_name, **tool_params)

    async def _execute_chain_node(
        self, node: WorkflowNode, input_data: dict[str, Any], context: WorkflowContext
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
        self, node: WorkflowNode, input_data: dict[str, Any], context: WorkflowContext
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
                metadata=metadata,
            )

            return {"stored": True}

        if operation == "retrieve":
            # Retrieve memory
            query = input_data.get("query", "")
            limit = input_data.get("limit", 10)

            # Search memory
            from heretek_swarm.memory.base import MemoryQuery

            search_query = MemoryQuery(
                query_text=query, agent_ids=[context.workflow_id], limit=limit
            )

            result = await memory_store.search(search_query)

            return {
                "results": [
                    {
                        "content": entry.content,
                        "memory_type": entry.memory_type.value,
                        "importance_score": entry.importance_score,
                    }
                    for entry in result.entries
                ]
            }

        if operation == "search":
            # Search memory (alias for retrieve)
            return await self._execute_memory_node(node, input_data, context)
        return None

    async def _execute_consensus_node(
        self,
        node: WorkflowNode,
        input_data: dict[str, Any],
        context: WorkflowContext,
    ) -> dict[str, Any]:
        """
        Execute a consensus node (MAKER voting as a workflow step).

        Uses ConsensusCoordinator.run_consensus() to execute multi-agent
        voting on a question derived from node configuration or upstream outputs.

        Args:
            node: Consensus node
            input_data: Input data from upstream nodes and workflow variables
            context: Execution context

        Returns:
            Dict with consensus result (decision, confidence, votes, red_flags)

        Raises:
            ValueError: If no question is provided in node.data or input_data
            RuntimeError: If consensus_coordinator is not configured
        """
        if self._consensus_coordinator is None:
            raise RuntimeError(
                "Consensus node requires a ConsensusCoordinator. "
                "Pass consensus_coordinator to WorkflowEngine constructor."
            )

        # Extract question from node.data or input_data
        question = node.data.get("question") or input_data.get("question")
        if not question:
            raise ValueError("Consensus node requires a 'question' in node.data or input_data.")

        # Extract optional parameters
        timeout = node.data.get("timeout", 120)
        max_rounds = node.data.get("max_rounds", 1)

        logger.info(
            "consensus_node_started",
            workflow_id=context.workflow_id,
            node_id=node.id,
            question=question[:200],
            timeout=timeout,
            max_rounds=max_rounds,
        )

        try:
            result = await self._consensus_coordinator.run_consensus(
                question=question,
                timeout=timeout,
                max_rounds=max_rounds,
            )

            if result is None:
                logger.warning(
                    "consensus_node_completed",
                    workflow_id=context.workflow_id,
                    node_id=node.id,
                    consensus_reached=False,
                )
                return {
                    "consensus_reached": False,
                    "decision": None,
                    "confidence": 0.0,
                    "votes": [],
                    "red_flags": [],
                }

            result_dict = {
                "consensus_reached": True,
                "decision": result.decision,
                "confidence": result.confidence,
                "votes": [
                    {
                        "agent_id": v.agent_id,
                        "decision": v.decision,
                        "confidence": v.confidence,
                        "metadata": v.metadata,
                    }
                    for v in result.votes
                ],
                "red_flags": result.red_flags,
                "metadata": result.metadata,
            }

            logger.info(
                "consensus_node_completed",
                workflow_id=context.workflow_id,
                node_id=node.id,
                consensus_reached=True,
                decision=result.decision,
                confidence=result.confidence,
                vote_count=len(result.votes),
            )

            return result_dict

        except Exception as exc:
            logger.error(
                "consensus_node_failed",
                workflow_id=context.workflow_id,
                node_id=node.id,
                error=str(exc)[:200],
            )
            raise

    def _build_graph(self, workflow: Workflow) -> dict[str, set[str]]:
        """
        Build dependency graph from workflow edges.

        Args:
            workflow: Workflow instance

        Returns:
            Dictionary of node IDs to their dependencies
        """
        graph: dict[str, set[str]] = {node.id: set() for node in workflow.nodes}

        for edge in workflow.edges:
            if edge.target not in graph:
                graph[edge.target] = set()
            graph[edge.target].add(edge.source)

        return graph

    def _topological_sort(self, graph: dict[str, set[str]]) -> list[str]:
        """
        Perform topological sort on dependency graph.

        Args:
            graph: Dependency graph where graph[node_id] = set of nodes
                   that must execute before node_id (its dependencies).

        Returns:
            List of node IDs in execution order (dependencies before dependents).
        """
        # Kahn's algorithm
        # in_degree = number of dependencies each node has
        in_degree: dict[str, int] = {node_id: len(deps) for node_id, deps in graph.items()}
        result: list[str] = []

        # Build reverse map: dependency → set of nodes that depend on it
        dependents: dict[str, set[str]] = {nid: set() for nid in graph}
        for node_id, dependencies in graph.items():
            for dep in dependencies:
                dependents[dep].add(node_id)

        # Find nodes with no dependencies (in_degree == 0)
        queue = [node_id for node_id, degree in in_degree.items() if degree == 0]

        # Process nodes
        while queue:
            node_id = queue.pop(0)
            result.append(node_id)

            # Decrement in-degrees of nodes that depended on the processed node
            for dependent in dependents.get(node_id, set()):
                in_degree[dependent] -= 1
                if in_degree[dependent] == 0:
                    queue.append(dependent)

        return result

    async def get_workflow_status(self, execution_id: str) -> WorkflowContext | None:
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
        context.state = WorkflowStatus.CANCELLED
        context.end_time = datetime.now(UTC)

        logger.info("workflow_cancelled", execution_id=execution_id)
        return True

    def list_workflows(self) -> list[Workflow]:
        """
        List all loaded workflows.

        Returns:
            List of workflows
        """
        return list(self.workflows.values())

    def get_workflow(self, workflow_id: str) -> Workflow | None:
        """
        Get a workflow by ID.

        Checks in-memory cache first, then falls back to the disk store.

        Args:
            workflow_id: Workflow ID

        Returns:
            Workflow or None
        """
        if workflow_id in self.workflows:
            return self.workflows[workflow_id]

        # Fall back to disk store
        stored = self.store.load(workflow_id)
        if stored is not None:
            workflow = self._definition_to_workflow(stored)
            self.workflows[workflow.id] = workflow
            return workflow

        return None

    async def update_workflow(self, workflow_id: str, definition: dict[str, Any]) -> Workflow:
        """Update an existing workflow definition.

        Persists the updated definition to disk and refreshes the in-memory
        cache.

        Raises:
            ValueError: If the workflow does not exist.
        """
        if workflow_id not in self.workflows and not self.store.exists(workflow_id):
            raise ValueError(f"Workflow not found: {workflow_id}")

        workflow = await self.load_workflow({**definition, "id": workflow_id})
        logger.info("workflow_updated", workflow_id=workflow_id)
        return workflow

    def delete_workflow(self, workflow_id: str) -> bool:
        """Delete a workflow from memory and disk.

        Returns True if the workflow existed and was deleted.
        """
        removed_from_disk = self.store.delete(workflow_id)
        removed_from_memory = self.workflows.pop(workflow_id, None) is not None
        if removed_from_disk or removed_from_memory:
            logger.info("workflow_deleted", workflow_id=workflow_id)
            return True
        return False

    def load_persisted_workflows(self) -> int:
        """Load all persisted workflows from disk into memory.

        Called during engine startup to restore state after restart.

        Returns:
            Number of workflows loaded.
        """
        stored = self.store.load_all()
        count = 0
        for wf_id, definition in stored.items():
            if wf_id not in self.workflows:
                workflow = self._definition_to_workflow(definition)
                self.workflows[workflow.id] = workflow
                count += 1
        if count:
            logger.info("persisted_workflows_loaded", count=count)
        return count

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _definition_to_workflow(self, definition: dict[str, Any]) -> Workflow:
        """Convert a raw definition dict to a Workflow dataclass."""
        nodes = [
            WorkflowNode(
                id=node["id"],
                type=node["type"],
                data=node.get("data", {}),
                inputs=node.get("inputs", []),
                outputs=node.get("outputs", []),
                position=node.get("position", {}),
            )
            for node in definition.get("nodes", [])
        ]
        edges = [
            WorkflowEdge(
                id=edge["id"],
                source=edge["source"],
                target=edge["target"],
                condition=edge.get("condition"),
            )
            for edge in definition.get("edges", [])
        ]
        return Workflow(
            id=definition.get("id", ""),
            name=definition.get("name", "Untitled Workflow"),
            nodes=nodes,
            edges=edges,
            metadata=definition.get("metadata", {}),
            created_at=definition.get("created_at", datetime.now(UTC).isoformat()),
        )


# Global workflow engine instance
_global_engine: WorkflowEngine | None = None


async def get_workflow_engine(
    cycle_detector: WorkflowCycleDetector | None = None,
    max_iterations: int = 100,
    timeout_seconds: float = 300.0,
    consensus_coordinator: Any | None = None,
    supervisor: Any | None = None,
    store: FileWorkflowStore | None = None,
) -> WorkflowEngine:
    """
    Get global workflow engine instance with cycle detection.

    On first call, creates the engine and loads any persisted workflows
    from disk so they survive server restarts.

    Args:
        cycle_detector: Optional pre-configured cycle detector
        max_iterations: Maximum iterations before cycle break
        timeout_seconds: Timeout in seconds before cycle break
        consensus_coordinator: Optional ConsensusCoordinator for consensus nodes
        supervisor: Optional ActorSupervisor for consensus agent resolution
        store: Optional FileWorkflowStore for disk persistence

    Returns:
        WorkflowEngine instance
    """
    global _global_engine

    if _global_engine is None:
        _global_engine = WorkflowEngine(
            cycle_detector=cycle_detector,
            max_iterations=max_iterations,
            timeout_seconds=timeout_seconds,
            consensus_coordinator=consensus_coordinator,
            supervisor=supervisor,
            store=store,
        )
        # Restore persisted workflows on first access
        _global_engine.load_persisted_workflows()

    return _global_engine


def get_cycle_detector_metrics() -> dict[str, Any]:
    """
    Get cycle detection metrics from global engine.

    Returns:
        Dictionary of cycle detection metrics
    """
    if _global_engine and hasattr(_global_engine, "cycle_detector"):
        return _global_engine.cycle_detector.get_metrics()
    return {}


def export_cycle_detector_prometheus() -> str:
    """
    Export cycle detection metrics in Prometheus format.

    Returns:
        Prometheus-formatted metrics string
    """
    if _global_engine and hasattr(_global_engine, "cycle_detector"):
        return _global_engine.cycle_detector.export_prometheus_metrics()
    return "# No cycle detector available\n"
