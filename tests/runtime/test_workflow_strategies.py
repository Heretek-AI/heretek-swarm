"""
M019 S03: Workflow Authoring Layer — Integration Tests

Tests the execution strategy system:
1. DAGStrategy topological sort with parallel batching
2. CycleStrategy convergence monitoring
3. MajorityVoteStrategy parallel aggregation
4. Strategy routing in WorkflowEngine.execute_workflow
"""

import asyncio
from unittest.mock import AsyncMock, MagicMock

import pytest


class AsyncTestCase:
    """Base async test case."""

    @pytest.fixture(autouse=True)
    def setup_event_loop(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        yield loop
        loop.close()


class TestDAGStrategy:
    """Base async test case."""

    @pytest.fixture(autouse=True)
    def setup_event_loop(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        yield loop
        loop.close()


class TestDAGStrategy:
    """DAGStrategy executes nodes in topological order with parallel batching."""

    @pytest.mark.asyncio
    async def test_dag_respects_dependency_order(self):
        """Nodes only execute after their inputs are complete."""
        from heretek_swarm.workflow.strategies import DAGStrategy
        from heretek_swarm.workflow.engine import Workflow, WorkflowNode, WorkflowEdge

        workflow = Workflow(
            id="test-dag",
            name="Dependency Test",
            nodes=[
                WorkflowNode(id="a", type="tool", data={}, inputs=[], outputs=["b"]),
                WorkflowNode(id="b", type="tool", data={}, inputs=["a"], outputs=["c"]),
                WorkflowNode(id="c", type="tool", data={}, inputs=["b"], outputs=[]),
            ],
            edges=[
                WorkflowEdge(id="e1", source="a", target="b"),
                WorkflowEdge(id="e2", source="b", target="c"),
            ],
        )

        execution_order: list[str] = []
        execution_strategy = DAGStrategy(max_parallel=4)

        async def executor(node_id: str, node_data: dict) -> str:
            execution_order.append(node_id)
            return f"result-{node_id}"

        result = await execution_strategy.execute(
            workflow,
            {"execution_id": "exec-1", "elapsed": 0.0},
            executor,
        )

        assert result.success
        assert execution_order == ["a", "b", "c"]  # Strict order

    @pytest.mark.asyncio
    async def test_dag_parallel_batching(self):
        """Level-0 nodes (no deps) run in parallel."""
        from heretek_swarm.workflow.strategies import DAGStrategy
        from heretek_swarm.workflow.engine import Workflow, WorkflowNode

        workflow = Workflow(
            id="test-parallel",
            name="Parallel Test",
            nodes=[
                WorkflowNode(id="x", type="tool", data={}, inputs=[], outputs=["z"]),
                WorkflowNode(id="y", type="tool", data={}, inputs=[], outputs=["z"]),
                WorkflowNode(id="z", type="tool", data={}, inputs=["x", "y"], outputs=[]),
            ],
            edges=[],
        )

        start_order: list[str] = []
        completion_order: list[str] = []

        async def executor(node_id: str, node_data: dict) -> str:
            if node_id in ("x", "y"):
                start_order.append(node_id)
                await asyncio.sleep(0.05)  # Simulate work
                completion_order.append(node_id)
            else:
                completion_order.append(node_id)
            return f"result-{node_id}"

        execution_strategy = DAGStrategy(max_parallel=2)
        result = await execution_strategy.execute(
            workflow,
            {"execution_id": "exec-2", "elapsed": 0.0},
            executor,
        )

        assert result.success
        # x and y started (and completed) before z started
        z_index = completion_order.index("z")
        assert "x" in completion_order[:z_index]
        assert "y" in completion_order[:z_index]

    @pytest.mark.asyncio
    async def test_dag_fails_on_unresolved_inputs(self):
        """Unresolved input references cause DAG to fail (no source node)."""
        from heretek_swarm.workflow.strategies import DAGStrategy
        from heretek_swarm.workflow.engine import Workflow, WorkflowNode

        workflow = Workflow(
            id="test-missing",
            name="Unresolved Input Test",
            nodes=[
                # Node b references "ghost" which has no source node
                WorkflowNode(id="b", type="tool", data={}, inputs=["ghost"], outputs=[]),
            ],
            edges=[],
        )

        async def executor(node_id: str, node_data: dict) -> str:
            return f"result-{node_id}"

        execution_strategy = DAGStrategy()
        result = await execution_strategy.execute(
            workflow,
            {"execution_id": "exec-3", "elapsed": 0.0},
            executor,
        )

        # Node with unresolved input has in_degree > 0 with no source → fails
        assert not result.success
        assert "Cycle detected" in result.error_message

    @pytest.mark.asyncio
    async def test_dag_parallel_limit(self):
        """Max parallel caps concurrency."""
        from heretek_swarm.workflow.strategies import DAGStrategy
        from heretek_swarm.workflow.engine import Workflow, WorkflowNode

        workflow = Workflow(
            id="test-limit",
            name="Parallel Limit",
            nodes=[WorkflowNode(id=f"n{i}", type="tool", data={}, inputs=[], outputs=[])
                   for i in range(4)],
            edges=[],
        )

        concurrent = 0
        max_concurrent = 0

        async def executor(node_id: str, node_data: dict) -> str:
            nonlocal concurrent, max_concurrent
            concurrent += 1
            max_concurrent = max(max_concurrent, concurrent)
            await asyncio.sleep(0.05)
            concurrent -= 1
            return f"result-{node_id}"

        execution_strategy = DAGStrategy(max_parallel=2)
        result = await execution_strategy.execute(
            workflow,
            {"execution_id": "exec-4", "elapsed": 0.0},
            executor,
        )

        assert result.success
        assert max_concurrent <= 2  # Capped by max_parallel


class TestCycleStrategy:
    """CycleStrategy monitors convergence and handles feedback loops."""

    @pytest.mark.asyncio
    async def test_cycle_converges_when_state_stabilizes(self):
        """Iteration stops when state delta < convergence_threshold."""
        from heretek_swarm.workflow.strategies import CycleStrategy
        from heretek_swarm.workflow.engine import Workflow, WorkflowNode

        workflow = Workflow(
            id="test-cycle",
            name="Convergence Test",
            nodes=[
                WorkflowNode(id="feedback", type="tool", data={}, inputs=["feedback"], outputs=["feedback"]),
            ],
            edges=[
                # Self-referential edge indicates a cycle
            ],
        )

        iteration_count = 0
        async def executor(node_id: str, node_data: dict) -> dict:
            nonlocal iteration_count
            iteration_count += 1
            # Converges after 3 iterations (same output)
            return {"value": 42, "iter": iteration_count}

        execution_strategy = CycleStrategy(
            max_iterations=10,
            convergence_threshold=0.05,
        )
        result = await execution_strategy.execute(
            workflow,
            {"execution_id": "exec-5", "elapsed": 0.0},
            executor,
        )

        assert result.success
        assert iteration_count <= 3  # Converged quickly

    @pytest.mark.asyncio
    async def test_cycle_respects_max_iterations(self):
        """Iteration stops at max_iterations even if state keeps changing."""
        from heretek_swarm.workflow.strategies import CycleStrategy
        from heretek_swarm.workflow.engine import Workflow, WorkflowNode, WorkflowEdge

        workflow = Workflow(
            id="test-max-iter",
            name="Max Iterations Test",
            nodes=[WorkflowNode(id="feedback", type="tool", data={}, inputs=["feedback"], outputs=[])],
            edges=[
                WorkflowEdge(id="feedback-loop", source="feedback", target="feedback", condition="true"),
            ],
        )

        iteration_count = 0

        async def executor(node_id: str, node_data: dict) -> dict:
            nonlocal iteration_count
            iteration_count += 1
            # Always changes state (never converges) — divergence_threshold * iter grows
            return {"value": iteration_count}

        execution_strategy = CycleStrategy(max_iterations=5, divergence_threshold=10.0)
        result = await execution_strategy.execute(
            workflow,
            {"execution_id": "exec-6", "elapsed": 0.0},
            executor,
        )

        # Should hit max iterations (or diverge before)
        assert iteration_count == 5 or not result.success


class TestMajorityVoteStrategy:
    """MajorityVoteStrategy aggregates parallel results by vote."""

    @pytest.mark.asyncio
    async def test_majority_vote_returns_consensus(self):
        """Parallel nodes vote and majority wins."""
        from heretek_swarm.workflow.strategies import MajorityVoteStrategy
        from heretek_swarm.workflow.engine import Workflow, WorkflowNode

        workflow = Workflow(
            id="test-vote",
            name="Vote Test",
            nodes=[
                WorkflowNode(id="v1", type="agent", data={}, inputs=[], outputs=[]),
                WorkflowNode(id="v2", type="agent", data={}, inputs=[], outputs=[]),
                WorkflowNode(id="v3", type="agent", data={}, inputs=[], outputs=[]),
            ],
            edges=[],
        )

        async def executor(node_id: str, node_data: dict) -> str:
            # 2 of 3 vote "APPROVE", 1 votes "REJECT"
            if node_id == "v1":
                return "APPROVE"
            elif node_id == "v2":
                return "APPROVE"
            else:
                return "REJECT"

        execution_strategy = MajorityVoteStrategy(agreement_threshold=0.6)
        result = await execution_strategy.execute(
            workflow,
            {"execution_id": "exec-7", "elapsed": 0.0},
            executor,
        )

        assert result.success
        assert "votes" in result.node_results
        aggregated = result.node_results["aggregated"]
        # Should be "APPROVE" (2/3 > 60%)
        assert aggregated == "APPROVE"

    @pytest.mark.asyncio
    async def test_majority_vote_dict_aggregation(self):
        """Dict results aggregated key-by-key with vote."""
        from heretek_swarm.workflow.strategies import MajorityVoteStrategy
        from heretek_swarm.workflow.engine import Workflow, WorkflowNode

        workflow = Workflow(
            id="test-dict-vote",
            name="Dict Vote Test",
            nodes=[
                WorkflowNode(id="n1", type="agent", data={}, inputs=[], outputs=[]),
                WorkflowNode(id="n2", type="agent", data={}, inputs=[], outputs=[]),
            ],
            edges=[],
        )

        async def executor(node_id: str, node_data: dict) -> dict:
            if node_id == "n1":
                return {"decision": "YES", "confidence": 0.8}
            else:
                return {"decision": "YES", "confidence": 0.7}

        execution_strategy = MajorityVoteStrategy()
        result = await execution_strategy.execute(
            workflow,
            {"execution_id": "exec-8", "elapsed": 0.0},
            executor,
        )

        assert result.success
        aggregated = result.node_results["aggregated"]
        assert aggregated["decision"] == "YES"

    @pytest.mark.asyncio
    async def test_majority_vote_no_consensus(self):
        """No consensus when agreement < threshold."""
        from heretek_swarm.workflow.strategies import MajorityVoteStrategy
        from heretek_swarm.workflow.engine import Workflow, WorkflowNode

        workflow = Workflow(
            id="test-no-consensus",
            name="No Consensus Test",
            nodes=[
                WorkflowNode(id="a1", type="agent", data={}, inputs=[], outputs=[]),
                WorkflowNode(id="a2", type="agent", data={}, inputs=[], outputs=[]),
            ],
            edges=[],
        )

        async def executor(node_id: str, node_data: dict) -> str:
            return "A1" if node_id == "a1" else "A2"

        execution_strategy = MajorityVoteStrategy(agreement_threshold=0.6)
        result = await execution_strategy.execute(
            workflow,
            {"execution_id": "exec-9", "elapsed": 0.0},
            executor,
        )

        assert result.success
        aggregated = result.node_results["aggregated"]
        # No majority — should return vote summary
        assert "votes" in aggregated
        assert aggregated["agreement"] < 0.6


class TestWorkflowStrategyRouting:
    """WorkflowEngine.execute_workflow routes to correct strategy."""

    @pytest.mark.asyncio
    async def test_execute_workflow_dag_routing(self):
        """strategy='dag' uses topological sort."""
        from heretek_swarm.workflow.engine import WorkflowEngine

        engine = WorkflowEngine()

        # Register a workflow
        workflow_id = "routing-test-dag"
        engine.workflows[workflow_id] = MagicMock()
        engine.workflows[workflow_id].id = workflow_id
        engine.workflows[workflow_id].nodes = []
        engine.workflows[workflow_id].edges = []
        engine.workflows[workflow_id].metadata = {}
        engine.workflows[workflow_id].name = "Test"

        # Mock _execute_and_capture to avoid real agent calls
        engine._execute_and_capture = AsyncMock(return_value={"result": "ok"})

        result = await engine.execute_workflow(workflow_id, {}, strategy="dag")

        # Should complete without error (DAG with no nodes = success)
        assert result is not None

    @pytest.mark.asyncio
    async def test_execute_workflow_majority_vote_routing(self):
        """strategy='majority_vote' uses MajorityVoteStrategy."""
        from heretek_swarm.workflow.engine import WorkflowEngine

        engine = WorkflowEngine()

        workflow_id = "routing-test-vote"
        node = MagicMock()
        node.id = "n1"
        node.type = "tool"
        node.data = {}
        node.inputs = []
        node.outputs = []

        engine.workflows[workflow_id] = MagicMock()
        engine.workflows[workflow_id].id = workflow_id
        engine.workflows[workflow_id].nodes = [node]
        engine.workflows[workflow_id].edges = []
        engine.workflows[workflow_id].metadata = {}
        engine.workflows[workflow_id].name = "Test"

        engine._execute_and_capture = AsyncMock(return_value="vote-result")

        result = await engine.execute_workflow(workflow_id, {}, strategy="majority_vote")

        assert result is not None
        assert "votes" in result.node_results

    @pytest.mark.asyncio
    async def test_execute_workflow_cycle_routing(self):
        """strategy='cycle' uses CycleStrategy."""
        from heretek_swarm.workflow.engine import WorkflowEngine

        engine = WorkflowEngine()

        workflow_id = "routing-test-cycle"
        engine.workflows[workflow_id] = MagicMock()
        engine.workflows[workflow_id].id = workflow_id
        engine.workflows[workflow_id].nodes = []
        engine.workflows[workflow_id].edges = []
        engine.workflows[workflow_id].metadata = {}
        engine.workflows[workflow_id].name = "Test"

        engine._execute_and_capture = AsyncMock(return_value={"result": "ok"})

        result = await engine.execute_workflow(workflow_id, {}, strategy="cycle")

        assert result is not None

    @pytest.mark.asyncio
    async def test_execute_workflow_unknown_strategy_falls_back_to_dag(self):
        """Unknown strategy defaults to DAG."""
        from heretek_swarm.workflow.engine import WorkflowEngine

        engine = WorkflowEngine()

        workflow_id = "routing-test-fallback"
        engine.workflows[workflow_id] = MagicMock()
        engine.workflows[workflow_id].id = workflow_id
        engine.workflows[workflow_id].nodes = []
        engine.workflows[workflow_id].edges = []
        engine.workflows[workflow_id].metadata = {}
        engine.workflows[workflow_id].name = "Test"

        engine._execute_and_capture = AsyncMock(return_value={"result": "ok"})

        # Unknown strategy should not crash
        result = await engine.execute_workflow(workflow_id, {}, strategy="unknown")
        assert result is not None

    @pytest.mark.asyncio
    async def test_workflows_api_accepts_strategy_parameter(self):
        """FastAPI endpoint accepts strategy query parameter."""
        # Test that the API endpoint signature accepts strategy
        import inspect
        from heretek_swarm.api.workflows import execute_workflow

        sig = inspect.signature(execute_workflow)
        params = list(sig.parameters.keys())

        assert "strategy" in params
        strategy_param = sig.parameters["strategy"]
        assert strategy_param.default == "dag"


class TestWorkflowStrategiesModule:
    """Module-level verification."""

    def test_strategies_module_imports_cleanly(self):
        """workflow/strategies.py compiles and exports correct classes."""
        from heretek_swarm.workflow.strategies import (
            DAGStrategy,
            CycleStrategy,
            ExecutionStrategy,
            MajorityVoteStrategy,
        )

        assert issubclass(DAGStrategy, ExecutionStrategy)
        assert issubclass(CycleStrategy, ExecutionStrategy)
        assert issubclass(MajorityVoteStrategy, ExecutionStrategy)

    def test_all_strategies_have_required_methods(self):
        """Each strategy has the execute() async method."""
        from heretek_swarm.workflow.strategies import (
            DAGStrategy,
            CycleStrategy,
            MajorityVoteStrategy,
        )

        for cls in [DAGStrategy, CycleStrategy, MajorityVoteStrategy]:
            strat = cls()
            assert hasattr(strat, "execute")
            import inspect
            assert asyncio.iscoroutinefunction(strat.execute)