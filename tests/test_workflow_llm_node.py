"""
Tests for LLM node type and fixed agent node in WorkflowEngine.

Verifies that:
- LLM node handler executes prompts through an active actor's run_with_llm()
- Agent node handler is fixed to use actor.run_with_llm() instead of nonexistent supervisor.send_message()
- Both node types integrate into _execute_node() and _execute_and_capture()
- Error paths are handled correctly (missing prompt, no active actor, inactive agent)
- Boundary conditions (empty prompt, special characters, timeouts)
"""

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest

from heretek_swarm.workflow.engine import (
    NodeStatus,
    Workflow,
    WorkflowContext,
    WorkflowEngine,
    WorkflowNode,
)

# ── Helpers ──────────────────────────────────────────────────────────────────


def _make_llm_node(
    node_id: str = "llm-1",
    prompt: str | None = "Explain quantum computing",
    timeout: int | None = None,
    temperature: float | None = None,
    model: str | None = None,
) -> WorkflowNode:
    """Build a WorkflowNode of type 'llm'."""
    data: dict[str, Any] = {}
    if prompt is not None:
        data["prompt"] = prompt
    if timeout is not None:
        data["timeout"] = timeout
    if temperature is not None:
        data["temperature"] = temperature
    if model is not None:
        data["model"] = model
    return WorkflowNode(id=node_id, type="llm", data=data)


def _make_agent_node(
    node_id: str = "agent-1",
    agent_id: str = "test-agent",
    timeout: int | None = None,
) -> WorkflowNode:
    """Build a WorkflowNode of type 'agent'."""
    data: dict[str, Any] = {"agent_id": agent_id}
    if timeout is not None:
        data["timeout"] = timeout
    return WorkflowNode(id=node_id, type="agent", data=data)


def _make_workflow(nodes: list[WorkflowNode] | None = None) -> Workflow:
    """Build a minimal Workflow for testing."""
    return Workflow(
        id="wf-test",
        name="Test Workflow",
        nodes=nodes or [],
        edges=[],
    )


def _make_context(
    variables: dict[str, Any] | None = None,
) -> WorkflowContext:
    """Build a WorkflowContext for testing."""
    return WorkflowContext(
        workflow_id="wf-test",
        execution_id="exec-test-001",
        variables=variables or {},
    )


def _make_mock_actor(
    agent_id: str = "test-agent",
    run_response: str = "LLM response text",
) -> MagicMock:
    """Build a mock actor with run_with_llm returning a configurable response."""
    actor = MagicMock()
    actor.agent_id = agent_id
    actor.run_with_llm = AsyncMock(return_value=run_response)
    return actor


def _make_mock_supervisor(
    actors: dict[str, MagicMock] | None = None,
    active_agent_ids: list[str] | None = None,
) -> MagicMock:
    """Build a mock supervisor with actor registry and status lookup."""
    supervisor = MagicMock()
    supervisor.actors = actors or {}

    # Build status map
    _active_ids = set(active_agent_ids or [])

    async def _get_status(actor_id: str):
        if actor_id not in supervisor.actors:
            return None
        status = MagicMock()
        status.state = "active" if actor_id in _active_ids else "inactive"
        return status

    supervisor.get_actor_status = AsyncMock(side_effect=_get_status)
    return supervisor


def _make_engine(supervisor: MagicMock | None = None) -> WorkflowEngine:
    """Build a WorkflowEngine with optional supervisor."""
    return WorkflowEngine(supervisor=supervisor)


# ── LLM Node Tests ───────────────────────────────────────────────────────────


class TestLLMNodeHappyPath:
    """Test LLM node with properly configured supervisor and actors."""

    @pytest.mark.asyncio
    async def test_llm_node_returns_llm_response(self):
        """LLM node returns the string response from run_with_llm()."""
        actor = _make_mock_actor(run_response="Quantum computing uses qubits.")
        supervisor = _make_mock_supervisor(
            actors={"agent-1": actor},
            active_agent_ids=["agent-1"],
        )
        engine = _make_engine(supervisor=supervisor)
        node = _make_llm_node(prompt="Explain quantum computing")
        context = _make_context()

        output = await engine._execute_llm_node(node, {}, context)

        assert output == "Quantum computing uses qubits."
        actor.run_with_llm.assert_called_once()
        call_args = actor.run_with_llm.call_args
        assert call_args[0][0] == "Explain quantum computing"

    @pytest.mark.asyncio
    async def test_llm_node_uses_first_active_actor(self):
        """LLM node selects the first active actor from the supervisor."""
        actor1 = _make_mock_actor(agent_id="inactive-agent", run_response="nope")
        actor2 = _make_mock_actor(agent_id="active-agent", run_response="yes!")
        supervisor = _make_mock_supervisor(
            actors={"inactive-agent": actor1, "active-agent": actor2},
            active_agent_ids=["active-agent"],
        )
        engine = _make_engine(supervisor=supervisor)
        node = _make_llm_node(prompt="Hello")
        context = _make_context()

        output = await engine._execute_llm_node(node, {}, context)

        # Should have used the active actor
        assert output == "yes!"
        actor2.run_with_llm.assert_called_once()
        actor1.run_with_llm.assert_not_called()

    @pytest.mark.asyncio
    async def test_llm_node_passes_timeout(self):
        """LLM node forwards timeout from node.data to run_with_llm()."""
        actor = _make_mock_actor()
        supervisor = _make_mock_supervisor(
            actors={"a1": actor},
            active_agent_ids=["a1"],
        )
        engine = _make_engine(supervisor=supervisor)
        node = _make_llm_node(prompt="Q?", timeout=30)
        context = _make_context()

        await engine._execute_llm_node(node, {}, context)

        actor.run_with_llm.assert_called_once_with("Q?", timeout=30)

    @pytest.mark.asyncio
    async def test_llm_node_passes_temperature(self):
        """LLM node forwards temperature from node.data to run_with_llm()."""
        actor = _make_mock_actor()
        supervisor = _make_mock_supervisor(
            actors={"a1": actor},
            active_agent_ids=["a1"],
        )
        engine = _make_engine(supervisor=supervisor)
        node = _make_llm_node(prompt="Q?", temperature=0.3)
        context = _make_context()

        await engine._execute_llm_node(node, {}, context)

        actor.run_with_llm.assert_called_once_with("Q?", timeout=60, temperature=0.3)

    @pytest.mark.asyncio
    async def test_llm_node_reads_prompt_from_input_data(self):
        """LLM node reads prompt from input_data when not in node.data."""
        actor = _make_mock_actor(run_response="From input!")
        supervisor = _make_mock_supervisor(
            actors={"a1": actor},
            active_agent_ids=["a1"],
        )
        engine = _make_engine(supervisor=supervisor)
        # No prompt in node.data
        node = WorkflowNode(id="llm-1", type="llm", data={})
        context = _make_context()

        output = await engine._execute_llm_node(node, {"prompt": "From upstream?"}, context)

        assert output == "From input!"
        actor.run_with_llm.assert_called_once_with("From upstream?", timeout=60)

    @pytest.mark.asyncio
    async def test_llm_node_prefers_node_data_prompt(self):
        """node.data.prompt takes priority over input_data.prompt."""
        actor = _make_mock_actor()
        supervisor = _make_mock_supervisor(
            actors={"a1": actor},
            active_agent_ids=["a1"],
        )
        engine = _make_engine(supervisor=supervisor)
        node = _make_llm_node(prompt="Node data prompt?")
        context = _make_context()

        await engine._execute_llm_node(node, {"prompt": "Input data prompt?"}, context)

        actor.run_with_llm.assert_called_once_with("Node data prompt?", timeout=60)

    @pytest.mark.asyncio
    async def test_llm_node_falls_back_to_message_key(self):
        """LLM node reads 'message' from input_data when prompt is absent."""
        actor = _make_mock_actor()
        supervisor = _make_mock_supervisor(
            actors={"a1": actor},
            active_agent_ids=["a1"],
        )
        engine = _make_engine(supervisor=supervisor)
        node = WorkflowNode(id="llm-1", type="llm", data={})
        context = _make_context()

        await engine._execute_llm_node(node, {"message": "Fallback message"}, context)

        actor.run_with_llm.assert_called_once_with("Fallback message", timeout=60)


class TestLLMNodeErrorPaths:
    """Test error conditions for LLM node."""

    @pytest.mark.asyncio
    async def test_raises_when_prompt_missing(self):
        """ValueError when prompt is absent from both node.data and input_data."""
        actor = _make_mock_actor()
        supervisor = _make_mock_supervisor(
            actors={"a1": actor},
            active_agent_ids=["a1"],
        )
        engine = _make_engine(supervisor=supervisor)
        node = WorkflowNode(id="llm-1", type="llm", data={})
        context = _make_context()

        with pytest.raises(ValueError, match="requires a 'prompt'"):
            await engine._execute_llm_node(node, {}, context)

    @pytest.mark.asyncio
    async def test_raises_when_no_active_actor(self):
        """RuntimeError when no actor in the supervisor is active."""
        actor = _make_mock_actor()
        supervisor = _make_mock_supervisor(
            actors={"a1": actor},
            active_agent_ids=[],  # no active actors
        )
        engine = _make_engine(supervisor=supervisor)
        node = _make_llm_node(prompt="Hello")
        context = _make_context()

        with pytest.raises(RuntimeError, match="at least one active actor"):
            await engine._execute_llm_node(node, {}, context)

    @pytest.mark.asyncio
    async def test_raises_when_supervisor_has_no_actors(self):
        """RuntimeError when supervisor.actors is empty."""
        supervisor = _make_mock_supervisor(actors={}, active_agent_ids=[])
        engine = _make_engine(supervisor=supervisor)
        node = _make_llm_node(prompt="Hello")
        context = _make_context()

        with pytest.raises(RuntimeError, match="at least one active actor"):
            await engine._execute_llm_node(node, {}, context)

    @pytest.mark.asyncio
    async def test_propagates_run_with_llm_exception(self):
        """Exceptions from run_with_llm propagate to caller."""
        actor = _make_mock_actor()
        actor.run_with_llm.side_effect = TimeoutError("LLM timed out")
        supervisor = _make_mock_supervisor(
            actors={"a1": actor},
            active_agent_ids=["a1"],
        )
        engine = _make_engine(supervisor=supervisor)
        node = _make_llm_node(prompt="Slow query")
        context = _make_context()

        with pytest.raises(TimeoutError, match="LLM timed out"):
            await engine._execute_llm_node(node, {}, context)


class TestLLMNodeBoundaryConditions:
    """Test boundary conditions for LLM node."""

    @pytest.mark.asyncio
    async def test_empty_string_prompt_raises(self):
        """Empty string prompt is treated as missing."""
        actor = _make_mock_actor()
        supervisor = _make_mock_supervisor(
            actors={"a1": actor},
            active_agent_ids=["a1"],
        )
        engine = _make_engine(supervisor=supervisor)
        node = _make_llm_node(prompt="")
        context = _make_context()

        with pytest.raises(ValueError, match="requires a 'prompt'"):
            await engine._execute_llm_node(node, {}, context)

    @pytest.mark.asyncio
    async def test_whitespace_only_prompt_is_valid(self):
        """Whitespace-only prompt is technically non-empty and passes through."""
        actor = _make_mock_actor(run_response="ok")
        supervisor = _make_mock_supervisor(
            actors={"a1": actor},
            active_agent_ids=["a1"],
        )
        engine = _make_engine(supervisor=supervisor)
        node = _make_llm_node(prompt="   ")
        context = _make_context()

        output = await engine._execute_llm_node(node, {}, context)
        assert output == "ok"
        actor.run_with_llm.assert_called_once_with("   ", timeout=60)

    @pytest.mark.asyncio
    async def test_prompt_with_special_characters(self):
        """Prompt with special characters is passed through unchanged."""
        actor = _make_mock_actor()
        supervisor = _make_mock_supervisor(
            actors={"a1": actor},
            active_agent_ids=["a1"],
        )
        engine = _make_engine(supervisor=supervisor)
        prompt = 'Is value > 100 && < 200? "test" \'quote\' \\n\\t'
        node = _make_llm_node(prompt=prompt)
        context = _make_context()

        await engine._execute_llm_node(node, {}, context)

        actor.run_with_llm.assert_called_once_with(prompt, timeout=60)

    @pytest.mark.asyncio
    async def test_very_long_prompt(self):
        """A very long prompt is passed through without truncation."""
        actor = _make_mock_actor(run_response="ok")
        supervisor = _make_mock_supervisor(
            actors={"a1": actor},
            active_agent_ids=["a1"],
        )
        engine = _make_engine(supervisor=supervisor)
        long_prompt = "x" * 100_000
        node = _make_llm_node(prompt=long_prompt)
        context = _make_context()

        output = await engine._execute_llm_node(node, {}, context)
        assert output == "ok"
        assert actor.run_with_llm.call_args[0][0] == long_prompt

    @pytest.mark.asyncio
    async def test_multiline_prompt(self):
        """Multi-line prompt is preserved exactly."""
        actor = _make_mock_actor()
        supervisor = _make_mock_supervisor(
            actors={"a1": actor},
            active_agent_ids=["a1"],
        )
        engine = _make_engine(supervisor=supervisor)
        prompt = "Line 1\nLine 2\nLine 3\n\nAfter blank"
        node = _make_llm_node(prompt=prompt)
        context = _make_context()

        await engine._execute_llm_node(node, {}, context)

        actor.run_with_llm.assert_called_once_with(prompt, timeout=60)


# ── Agent Node Tests (Fixed) ────────────────────────────────────────────────


class TestAgentNodeFixed:
    """Test that _execute_agent_node uses actor.run_with_llm() correctly."""

    @pytest.mark.asyncio
    async def test_agent_node_calls_run_with_llm(self):
        """Agent node calls actor.run_with_llm() with the prompt."""
        actor = _make_mock_actor(agent_id="my-agent", run_response="Agent says hi")
        supervisor = _make_mock_supervisor(
            actors={"my-agent": actor},
            active_agent_ids=["my-agent"],
        )
        engine = _make_engine(supervisor=supervisor)
        node = _make_agent_node(agent_id="my-agent")
        context = _make_context()

        output = await engine._execute_agent_node(node, {"prompt": "Hello agent"}, context)

        assert output == "Agent says hi"
        actor.run_with_llm.assert_called_once_with("Hello agent", timeout=60)

    @pytest.mark.asyncio
    async def test_agent_node_uses_message_fallback(self):
        """Agent node falls back to 'message' key when 'prompt' is absent."""
        actor = _make_mock_actor(agent_id="my-agent")
        supervisor = _make_mock_supervisor(
            actors={"my-agent": actor},
            active_agent_ids=["my-agent"],
        )
        engine = _make_engine(supervisor=supervisor)
        node = _make_agent_node(agent_id="my-agent")
        context = _make_context()

        await engine._execute_agent_node(node, {"message": "Fallback msg"}, context)

        actor.run_with_llm.assert_called_once_with("Fallback msg", timeout=60)

    @pytest.mark.asyncio
    async def test_agent_node_passes_custom_timeout(self):
        """Agent node forwards timeout from node.data."""
        actor = _make_mock_actor(agent_id="my-agent")
        supervisor = _make_mock_supervisor(
            actors={"my-agent": actor},
            active_agent_ids=["my-agent"],
        )
        engine = _make_engine(supervisor=supervisor)
        node = _make_agent_node(agent_id="my-agent", timeout=120)
        context = _make_context()

        await engine._execute_agent_node(node, {"prompt": "Q?"}, context)

        actor.run_with_llm.assert_called_once_with("Q?", timeout=120)

    @pytest.mark.asyncio
    async def test_agent_node_uses_injected_supervisor(self):
        """Agent node uses self._supervisor instead of global singleton."""
        actor = _make_mock_actor(agent_id="local-agent", run_response="local!")
        supervisor = _make_mock_supervisor(
            actors={"local-agent": actor},
            active_agent_ids=["local-agent"],
        )
        engine = _make_engine(supervisor=supervisor)
        node = _make_agent_node(agent_id="local-agent")
        context = _make_context()

        output = await engine._execute_agent_node(node, {"prompt": "test"}, context)

        assert output == "local!"


class TestAgentNodeErrorPaths:
    """Test error conditions for the fixed agent node."""

    @pytest.mark.asyncio
    async def test_raises_when_agent_id_missing(self):
        """ValueError when agent_id is missing from node.data."""
        engine = _make_engine()
        node = WorkflowNode(id="a1", type="agent", data={})
        context = _make_context()

        with pytest.raises(ValueError, match="requires agent_id"):
            await engine._execute_agent_node(node, {}, context)

    @pytest.mark.asyncio
    async def test_raises_when_agent_not_found(self):
        """RuntimeError when agent_id is not in supervisor.actors."""
        supervisor = _make_mock_supervisor(actors={}, active_agent_ids=[])
        engine = _make_engine(supervisor=supervisor)
        node = _make_agent_node(agent_id="missing-agent")
        context = _make_context()

        with pytest.raises(RuntimeError, match="Agent not found"):
            await engine._execute_agent_node(node, {"prompt": "test"}, context)

    @pytest.mark.asyncio
    async def test_raises_when_agent_inactive(self):
        """RuntimeError when agent exists but is not active."""
        actor = _make_mock_actor(agent_id="inactive-agent")
        supervisor = _make_mock_supervisor(
            actors={"inactive-agent": actor},
            active_agent_ids=[],  # not active
        )
        engine = _make_engine(supervisor=supervisor)
        node = _make_agent_node(agent_id="inactive-agent")
        context = _make_context()

        with pytest.raises(RuntimeError, match="Agent not active"):
            await engine._execute_agent_node(node, {"prompt": "test"}, context)

    @pytest.mark.asyncio
    async def test_raises_when_prompt_and_message_empty(self):
        """ValueError when both prompt and message are empty/missing."""
        actor = _make_mock_actor(agent_id="my-agent")
        supervisor = _make_mock_supervisor(
            actors={"my-agent": actor},
            active_agent_ids=["my-agent"],
        )
        engine = _make_engine(supervisor=supervisor)
        node = _make_agent_node(agent_id="my-agent")
        context = _make_context()

        with pytest.raises(ValueError, match="requires a prompt or message"):
            await engine._execute_agent_node(node, {}, context)

    @pytest.mark.asyncio
    async def test_propagates_run_with_llm_exception(self):
        """Exceptions from actor.run_with_llm() propagate."""
        actor = _make_mock_actor(agent_id="my-agent")
        actor.run_with_llm.side_effect = RuntimeError("LLM provider down")
        supervisor = _make_mock_supervisor(
            actors={"my-agent": actor},
            active_agent_ids=["my-agent"],
        )
        engine = _make_engine(supervisor=supervisor)
        node = _make_agent_node(agent_id="my-agent")
        context = _make_context()

        with pytest.raises(RuntimeError, match="LLM provider down"):
            await engine._execute_agent_node(node, {"prompt": "test"}, context)


# ── Integration Tests ────────────────────────────────────────────────────────


class TestLLMNodeIntegration:
    """Test LLM node integrated into _execute_node and _execute_and_capture."""

    @pytest.mark.asyncio
    async def test_execute_node_dispatches_to_llm(self):
        """_execute_node routes type='llm' to _execute_llm_node."""
        actor = _make_mock_actor(run_response="LLM output here")
        supervisor = _make_mock_supervisor(
            actors={"a1": actor},
            active_agent_ids=["a1"],
        )
        engine = _make_engine(supervisor=supervisor)
        node = _make_llm_node(node_id="llm1", prompt="What is 2+2?")
        workflow = _make_workflow(nodes=[node])
        context = _make_context()

        await engine._execute_node(workflow, "llm1", context)

        nr = context.node_results["llm1"]
        assert nr.status == NodeStatus.COMPLETED
        assert nr.output == "LLM output here"
        assert nr.execution_time > 0

    @pytest.mark.asyncio
    async def test_execute_and_capture_dispatches_to_llm(self):
        """_execute_and_capture routes type='llm' to _execute_llm_node."""
        actor = _make_mock_actor(run_response="Captured!")
        supervisor = _make_mock_supervisor(
            actors={"a1": actor},
            active_agent_ids=["a1"],
        )
        engine = _make_engine(supervisor=supervisor)
        node = _make_llm_node(node_id="llm1", prompt="Hello")
        workflow = _make_workflow(nodes=[node])
        context = _make_context()

        output = await engine._execute_and_capture(workflow, "llm1", context, node)

        assert output == "Captured!"

    @pytest.mark.asyncio
    async def test_execute_node_llm_failure_marks_node_failed(self):
        """When LLM node raises, the node is marked FAILED in context."""
        actor = _make_mock_actor()
        actor.run_with_llm.side_effect = RuntimeError("Provider error")
        supervisor = _make_mock_supervisor(
            actors={"a1": actor},
            active_agent_ids=["a1"],
        )
        engine = _make_engine(supervisor=supervisor)
        node = _make_llm_node(node_id="llm1", prompt="Fail")
        workflow = _make_workflow(nodes=[node])
        context = _make_context()

        await engine._execute_node(workflow, "llm1", context)

        nr = context.node_results["llm1"]
        assert nr.status == NodeStatus.FAILED
        assert isinstance(nr.error, RuntimeError)
        assert "Provider error" in str(nr.error)

    @pytest.mark.asyncio
    async def test_execute_and_capture_llm_failure_returns_error_dict(self):
        """When LLM node raises, _execute_and_capture returns error dict."""
        actor = _make_mock_actor()
        actor.run_with_llm.side_effect = RuntimeError("Provider error")
        supervisor = _make_mock_supervisor(
            actors={"a1": actor},
            active_agent_ids=["a1"],
        )
        engine = _make_engine(supervisor=supervisor)
        node = _make_llm_node(node_id="llm1", prompt="Fail")
        workflow = _make_workflow(nodes=[node])
        context = _make_context()

        output = await engine._execute_and_capture(workflow, "llm1", context, node)

        assert "error" in output
        assert "Provider error" in output["error"]

    @pytest.mark.asyncio
    async def test_llm_node_output_stored_in_context_variables(self):
        """After _execute_node, LLM output is available in context.variables."""
        actor = _make_mock_actor(run_response="stored value")
        supervisor = _make_mock_supervisor(
            actors={"a1": actor},
            active_agent_ids=["a1"],
        )
        engine = _make_engine(supervisor=supervisor)
        node = _make_llm_node(node_id="llm1", prompt="Store me")
        workflow = _make_workflow(nodes=[node])
        context = _make_context()

        await engine._execute_node(workflow, "llm1", context)

        assert context.variables["node_llm1_output"] == "stored value"


class TestAgentNodeIntegration:
    """Test agent node integrated into _execute_node and _execute_and_capture."""

    @pytest.mark.asyncio
    async def test_execute_node_dispatches_to_agent(self):
        """_execute_node routes type='agent' to the fixed _execute_agent_node."""
        actor = _make_mock_actor(agent_id="my-agent", run_response="Agent output")
        supervisor = _make_mock_supervisor(
            actors={"my-agent": actor},
            active_agent_ids=["my-agent"],
        )
        engine = _make_engine(supervisor=supervisor)
        node = _make_agent_node(node_id="a1", agent_id="my-agent")
        workflow = _make_workflow(nodes=[node])
        # _execute_node reads input from _get_node_input which pulls from
        # context.variables and upstream node outputs. We need to seed the
        # prompt into context.variables so the agent node finds it.
        context = _make_context(variables={"prompt": "Hello agent"})

        await engine._execute_node(workflow, "a1", context)

        nr = context.node_results["a1"]
        assert nr.status == NodeStatus.COMPLETED
        assert nr.output == "Agent output"

    @pytest.mark.asyncio
    async def test_execute_and_capture_dispatches_to_agent(self):
        """_execute_and_capture routes type='agent' correctly."""
        actor = _make_mock_actor(agent_id="my-agent", run_response="Captured agent!")
        supervisor = _make_mock_supervisor(
            actors={"my-agent": actor},
            active_agent_ids=["my-agent"],
        )
        engine = _make_engine(supervisor=supervisor)
        node = _make_agent_node(node_id="a1", agent_id="my-agent")
        workflow = _make_workflow(nodes=[node])
        context = _make_context(variables={"prompt": "Hello agent"})

        output = await engine._execute_and_capture(workflow, "a1", context, node)

        assert output == "Captured agent!"

    @pytest.mark.asyncio
    async def test_execute_node_agent_failure_marks_failed(self):
        """When agent node raises, the node is marked FAILED."""
        actor = _make_mock_actor(agent_id="my-agent")
        actor.run_with_llm.side_effect = RuntimeError("Actor crashed")
        supervisor = _make_mock_supervisor(
            actors={"my-agent": actor},
            active_agent_ids=["my-agent"],
        )
        engine = _make_engine(supervisor=supervisor)
        node = _make_agent_node(node_id="a1", agent_id="my-agent")
        workflow = _make_workflow(nodes=[node])
        context = _make_context(variables={"prompt": "test"})

        await engine._execute_node(workflow, "a1", context)

        nr = context.node_results["a1"]
        assert nr.status == NodeStatus.FAILED
        assert isinstance(nr.error, RuntimeError)

    @pytest.mark.asyncio
    async def test_execute_and_capture_agent_failure_returns_error(self):
        """When agent node raises, _execute_and_capture returns error dict."""
        actor = _make_mock_actor(agent_id="my-agent")
        actor.run_with_llm.side_effect = RuntimeError("Actor crashed")
        supervisor = _make_mock_supervisor(
            actors={"my-agent": actor},
            active_agent_ids=["my-agent"],
        )
        engine = _make_engine(supervisor=supervisor)
        node = _make_agent_node(node_id="a1", agent_id="my-agent")
        workflow = _make_workflow(nodes=[node])
        context = _make_context(variables={"prompt": "test"})

        output = await engine._execute_and_capture(workflow, "a1", context, node)

        assert "error" in output
        assert "Actor crashed" in output["error"]


# ── Multi-Node Workflow Tests ────────────────────────────────────────────────


class TestMultiNodeWorkflow:
    """Test workflows with both LLM and agent nodes chained together."""

    @pytest.mark.asyncio
    async def test_llm_then_agent_workflow(self):
        """LLM node output flows into agent node as input via workflow edges."""
        actor = _make_mock_actor(agent_id="worker", run_response="Agent processed: analysis")
        supervisor = _make_mock_supervisor(
            actors={"worker": actor},
            active_agent_ids=["worker"],
        )
        engine = _make_engine(supervisor=supervisor)

        llm_node = _make_llm_node(node_id="llm1", prompt="Analyze this data")
        # Agent node has llm1 as input — simulating edge connection
        agent_node = WorkflowNode(
            id="agent1",
            type="agent",
            data={"agent_id": "worker"},
            inputs=["llm1"],
        )
        workflow = _make_workflow(nodes=[llm_node, agent_node])
        context = _make_context()

        # Execute LLM node first
        await engine._execute_node(workflow, "llm1", context)
        assert context.node_results["llm1"].status == NodeStatus.COMPLETED

        # Execute agent node — it should pick up LLM output from context
        await engine._execute_node(workflow, "agent1", context)
        assert context.node_results["agent1"].status == NodeStatus.COMPLETED

    @pytest.mark.asyncio
    async def test_unknown_node_type_still_handled(self):
        """Unknown node types still return error (not crash)."""
        engine = _make_engine()
        node = WorkflowNode(id="x1", type="mystery", data={})
        workflow = _make_workflow(nodes=[node])
        context = _make_context()

        await engine._execute_node(workflow, "x1", context)

        nr = context.node_results["x1"]
        assert nr.status == NodeStatus.FAILED
        assert isinstance(nr.error, ValueError)
        assert "Unknown node type" in str(nr.error)


# ── Constructor Tests ────────────────────────────────────────────────────────


class TestLLMNodeConstructor:
    """Test that WorkflowEngine accepts supervisor for LLM/agent nodes."""

    def test_engine_accepts_supervisor(self):
        """Engine stores supervisor when provided."""
        supervisor = MagicMock()
        engine = WorkflowEngine(supervisor=supervisor)
        assert engine._supervisor is supervisor

    def test_engine_defaults_to_none_supervisor(self):
        """Engine defaults supervisor to None."""
        engine = WorkflowEngine()
        assert engine._supervisor is None

    def test_engine_accepts_both_coordinator_and_supervisor(self):
        """Engine can accept both consensus_coordinator and supervisor."""
        coordinator = MagicMock()
        supervisor = MagicMock()
        engine = WorkflowEngine(consensus_coordinator=coordinator, supervisor=supervisor)
        assert engine._consensus_coordinator is coordinator
        assert engine._supervisor is supervisor
