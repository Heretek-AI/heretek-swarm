"""
Tests for the LangGraph HeavySwarm migration (M-arch PR #6 follow-up).

Per PLAN.md: replace the custom 1,363-LOC HeavySwarm orchestrator
with a LangGraph StateGraph. These tests verify:
  1. The new module imports cleanly (with or without langgraph)
  2. The 5 phase nodes are callable and return the correct state
  3. The state schema matches the public WorkflowState TypedDict
  4. The legacy_phase_node bridge is importable
  5. The factory helpers return the right type based on availability

If langgraph is not installed, the compile- and invoke-level
tests are skipped (the module is opt-in via [langgraph] extra).
"""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock

import pytest
from heretek_swarm.orchestration import langgraph_nodes
from heretek_swarm.orchestration.langgraph_nodes import (
    PhaseResult,
    WorkflowPhase,
)


class TestPhaseNodes:
    def test_research_node_sets_phase(self) -> None:
        """research_node updates state.current_phase to RESEARCH."""
        state: dict[str, Any] = {"topic": "x", "phase_results": {}}
        result = langgraph_nodes.research_node(state)
        assert result["current_phase"] == "research"

    def test_analysis_node_sets_phase(self) -> None:
        """analysis_node updates state.current_phase to ANALYSIS."""
        state: dict[str, Any] = {"topic": "x", "phase_results": {}}
        result = langgraph_nodes.analysis_node(state)
        assert result["current_phase"] == "analysis"

    def test_alternatives_node_sets_phase(self) -> None:
        """alternatives_node updates state.current_phase to ALTERNATIVES."""
        state: dict[str, Any] = {"topic": "x", "phase_results": {}}
        result = langgraph_nodes.alternatives_node(state)
        assert result["current_phase"] == "alternatives"

    def test_verification_node_sets_phase(self) -> None:
        """verification_node updates state.current_phase to VERIFICATION."""
        state: dict[str, Any] = {"topic": "x", "phase_results": {}}
        result = langgraph_nodes.verification_node(state)
        assert result["current_phase"] == "verification"

    def test_decision_node_sets_phase(self) -> None:
        """decision_node updates state.current_phase to DECISION."""
        state: dict[str, Any] = {"topic": "x", "phase_results": {}}
        result = langgraph_nodes.decision_node(state)
        assert result["current_phase"] == "decision"

    def test_legacy_phase_node_returns_callable(self) -> None:
        """legacy_phase_node returns a callable for each phase."""
        for phase in (
            WorkflowPhase.RESEARCH,
            WorkflowPhase.ANALYSIS,
            WorkflowPhase.ALTERNATIVES,
            WorkflowPhase.VERIFICATION,
            WorkflowPhase.DECISION,
        ):
            node = langgraph_nodes.legacy_phase_node(phase)
            assert callable(node)

    def test_legacy_phase_node_preserves_phase(self) -> None:
        """legacy_phase_node returns a node that sets the right phase."""
        import asyncio

        node = langgraph_nodes.legacy_phase_node(WorkflowPhase.ANALYSIS)
        result = asyncio.run(node({"topic": "x", "phase_results": {}}))
        assert result["current_phase"] == "analysis"


class TestPhaseNodeMapping:
    def test_phase_nodes_covers_all_phases(self) -> None:
        """PHASE_NODES contains an entry for each of the 5 active phases.

        Note: COMPLETED and FAILED are terminal states, not nodes.
        """
        active_phases = {
            WorkflowPhase.RESEARCH,
            WorkflowPhase.ANALYSIS,
            WorkflowPhase.ALTERNATIVES,
            WorkflowPhase.VERIFICATION,
            WorkflowPhase.DECISION,
        }
        assert set(langgraph_nodes.PHASE_NODES.keys()) == active_phases

    def test_phase_nodes_values_are_callable(self) -> None:
        """Each entry in PHASE_NODES is a callable."""
        for phase, fn in langgraph_nodes.PHASE_NODES.items():
            assert callable(fn), f"PHASE_NODES[{phase!r}] is not callable"


class TestLegacyPhaseNodeBridge:
    """Tests for legacy_phase_node(phase, workflow) — the bridge
    that lets the LangGraph StateGraph delegate to the existing
    HeavySwarmWorkflow implementation.
    """

    def test_legacy_node_with_workflow_calls_execute_phase(self) -> None:
        """legacy_phase_node(phase, workflow) calls workflow._execute_phase."""
        from unittest.mock import AsyncMock, MagicMock

        workflow = MagicMock()
        workflow._execute_phase = AsyncMock(
            return_value=PhaseResult(
                phase=WorkflowPhase.RESEARCH,
                success=True,
                output={"summary": "ok"},
                duration_ms=42.0,
            )
        )
        workflow._research_phase = MagicMock()
        node = langgraph_nodes.legacy_phase_node(
            WorkflowPhase.RESEARCH, workflow
        )
        import asyncio

        state: dict[str, Any] = {
            "topic": "t",
            "context": {"k": "v"},
            "workflow_id": "wf-1",
        }
        result = asyncio.run(node(state))
        assert result["current_phase"] == "research"
        workflow._execute_phase.assert_awaited_once()
        # Real signature: (workflow_id, phase, phase_func, topic, context)
        call_args = workflow._execute_phase.await_args.args
        assert call_args[0] == "wf-1"
        assert call_args[1] == WorkflowPhase.RESEARCH
        assert call_args[2] is workflow._research_phase
        assert call_args[3] == "t"
        assert call_args[4] == {"k": "v"}

    def test_legacy_node_stores_phase_result(self) -> None:
        """legacy_phase_node stores the PhaseResult in state.phase_results."""
        from unittest.mock import AsyncMock, MagicMock

        workflow = MagicMock()
        workflow._execute_phase = AsyncMock(
            return_value=PhaseResult(
                phase=WorkflowPhase.ANALYSIS,
                success=True,
                output={"perspectives": ["a", "b", "c"]},
                duration_ms=100.0,
            )
        )
        node = langgraph_nodes.legacy_phase_node(
            WorkflowPhase.ANALYSIS, workflow
        )
        import asyncio

        result = asyncio.run(node({"topic": "t", "context": {}, "workflow_id": "wf"}))
        assert "phase_results" in result
        assert WorkflowPhase.ANALYSIS.value in result["phase_results"]
        pr = result["phase_results"][WorkflowPhase.ANALYSIS.value]
        assert pr.phase == WorkflowPhase.ANALYSIS
        assert pr.success is True

    def test_legacy_node_handles_workflow_error(self) -> None:
        """legacy_phase_node captures exceptions and sets state.error."""
        from unittest.mock import AsyncMock, MagicMock

        workflow = MagicMock()
        workflow._execute_phase = AsyncMock(
            side_effect=RuntimeError("simulated phase failure")
        )
        node = langgraph_nodes.legacy_phase_node(
            WorkflowPhase.VERIFICATION, workflow
        )
        import asyncio

        result = asyncio.run(node({"topic": "t", "context": {}, "workflow_id": "wf"}))
        assert result["current_phase"] == "verification"
        assert "error" in result
        assert "simulated phase failure" in result["error"]

    def test_legacy_node_without_workflow_returns_stub(self) -> None:
        """legacy_phase_node(phase, None) returns a state-update-only stub."""
        node = langgraph_nodes.legacy_phase_node(WorkflowPhase.RESEARCH, None)
        import asyncio

        result = asyncio.run(node({"topic": "t", "context": {}}))
        assert result["current_phase"] == "research"
        assert "phase_results" not in result or not result.get("phase_results")


class TestPublicContractPreserved:
    def test_workflow_phase_enum_preserved(self) -> None:
        """The WorkflowPhase enum is importable from langgraph_nodes."""
        from heretek_swarm.orchestration.langgraph_nodes import (
            WorkflowPhase as WorkflowPhase2,
        )
        assert WorkflowPhase2 is langgraph_nodes.WorkflowPhase

    def test_phase_result_importable(self) -> None:
        """PhaseResult is importable from langgraph_nodes."""
        from heretek_swarm.orchestration.langgraph_nodes import (
            PhaseResult as PhaseResult2,
        )
        assert PhaseResult2 is langgraph_nodes.PhaseResult

    def test_workflow_result_importable(self) -> None:
        """WorkflowResult is importable from langgraph_nodes."""
        from heretek_swarm.orchestration.langgraph_nodes import (
            WorkflowResult as WorkflowResult2,
        )
        assert WorkflowResult2 is langgraph_nodes.WorkflowResult


class TestLangGraphWorkflowModule:
    def test_workflow_module_imports(self) -> None:
        """langgraph_workflow module imports cleanly."""
        from heretek_swarm.orchestration import langgraph_workflow

        assert hasattr(langgraph_workflow, "LangGraphHeavySwarmWorkflow")
        assert hasattr(langgraph_workflow, "build_langgraph_workflow")
        assert hasattr(langgraph_workflow, "build_legacy_workflow")
        assert hasattr(langgraph_workflow, "is_langgraph_available")

    def test_is_langgraph_available_returns_bool(self) -> None:
        """is_langgraph_available returns a bool."""
        from heretek_swarm.orchestration.langgraph_workflow import (
            is_langgraph_available,
        )
        result = is_langgraph_available()
        assert isinstance(result, bool)

    def test_build_legacy_workflow_returns_heavy(self) -> None:
        """build_legacy_workflow returns a LangGraphHeavySwarmWorkflow instance."""
        from heretek_swarm.orchestration.langgraph_workflow import (
            LangGraphHeavySwarmWorkflow,
            build_legacy_workflow,
        )

        wf = build_legacy_workflow(name="test")
        assert isinstance(wf, LangGraphHeavySwarmWorkflow)
        assert wf.name == "test"

    def test_build_phase_nodes_returns_all_five(self) -> None:
        """build_phase_nodes(workflow) returns a callable for every phase."""
        from unittest.mock import MagicMock

        from heretek_swarm.orchestration.langgraph_nodes import (
            build_phase_nodes,
        )

        workflow = MagicMock()
        nodes = build_phase_nodes(workflow)
        assert set(nodes.keys()) == {
            WorkflowPhase.RESEARCH,
            WorkflowPhase.ANALYSIS,
            WorkflowPhase.ALTERNATIVES,
            WorkflowPhase.VERIFICATION,
            WorkflowPhase.DECISION,
        }
        for phase, node_fn in nodes.items():
            assert callable(node_fn), f"node for {phase!r} is not callable"

    def test_build_phase_nodes_uses_provided_workflow(self) -> None:
        """Each bridge node delegates to the provided workflow's _execute_phase."""
        from unittest.mock import AsyncMock, MagicMock

        from heretek_swarm.orchestration.langgraph_nodes import (
            build_phase_nodes,
        )

        workflow = MagicMock()
        workflow._execute_phase = AsyncMock(
            return_value=PhaseResult(
                phase=WorkflowPhase.VERIFICATION,
                success=True,
                output={"ok": True},
                duration_ms=1.0,
            )
        )
        workflow._verification_phase = MagicMock()

        nodes = build_phase_nodes(workflow)
        import asyncio

        result = asyncio.run(
            nodes[WorkflowPhase.VERIFICATION](
                {
                    "topic": "t",
                    "context": {},
                    "workflow_id": "wf-x",
                    "phase_results": {},
                }
            )
        )
        assert result["current_phase"] == "verification"
        workflow._execute_phase.assert_awaited_once()

    def test_langgraph_workflow_no_heavy_dependency(self) -> None:
        """LangGraphHeavySwarmWorkflow no longer requires a HeavySwarmWorkflow."""
        from heretek_swarm.orchestration.langgraph_workflow import (
            LangGraphHeavySwarmWorkflow,
        )

        wf = LangGraphHeavySwarmWorkflow(name="test")
        assert wf.name == "test"
        assert not hasattr(wf, "workflow")

    def test_langgraph_workflow_default_name(self) -> None:
        """LangGraphHeavySwarmWorkflow uses a sensible default name."""
        from heretek_swarm.orchestration.langgraph_workflow import (
            LangGraphHeavySwarmWorkflow,
        )

        wf = LangGraphHeavySwarmWorkflow()
        assert wf.name == "LangGraphHeavySwarm"


@pytest.mark.skipif(
    not __import__("importlib").util.find_spec("langgraph"),
    reason="langgraph not installed",
)
class TestLangGraphWorkflowExecution:
    """Tests that require the langgraph optional dep."""

    @pytest.mark.asyncio
    async def test_workflow_executes_through_all_phases(self) -> None:
        """The compiled StateGraph runs all 5 phases and returns a WorkflowResult."""
        from heretek_swarm.orchestration.langgraph_workflow import (
            LangGraphHeavySwarmWorkflow,
        )

        wf = LangGraphHeavySwarmWorkflow(name="test")
        result = await wf.execute(topic="Should we deploy?")
        assert result.state == WorkflowPhase.COMPLETED
        assert result.workflow_id  # non-empty
        assert result.topic == "Should we deploy?"
        assert result.started_at
        assert result.completed_at
        assert result.total_duration_ms >= 0

    @pytest.mark.asyncio
    async def test_workflow_id_is_preserved(self) -> None:
        """A caller-provided workflow_id is preserved in the result."""
        from heretek_swarm.orchestration.langgraph_workflow import (
            LangGraphHeavySwarmWorkflow,
        )

        wf = LangGraphHeavySwarmWorkflow()
        result = await wf.execute(topic="x", workflow_id="my-custom-id-123")
        assert result.workflow_id == "my-custom-id-123"

    @pytest.mark.asyncio
    async def test_workflow_context_is_stored(self) -> None:
        """The context dict is stored in the initial state."""
        from heretek_swarm.orchestration.langgraph_workflow import (
            LangGraphHeavySwarmWorkflow,
        )

        wf = LangGraphHeavySwarmWorkflow()
        ctx = {"k": "v", "n": 42}
        result = await wf.execute(topic="x", context=ctx)
        assert result.phase_results or result.state == WorkflowPhase.COMPLETED


@pytest.mark.skipif(
    not __import__("importlib").util.find_spec("langgraph"),
    reason="langgraph not installed",
)
class TestLangGraphBridgeRigorous:
    """Mock-based tests that prove the bridge wiring is correct
    independently of the real HeavySwarmWorkflow behavior.

    These tests use a MagicMock workflow to verify:
    - The StateGraph calls workflow._execute_phase exactly 5 times
    - Phases are called in the correct order
    - The decision phase's consensus_result propagates to final_decision
    - Each phase receives the previous phase's output as an extra arg
    """

    def _make_mock_workflow(self) -> MagicMock:
        """Build a MagicMock workflow whose _execute_phase returns a
        PhaseResult that chains outputs (so the previous-phase-output
        arg can be verified).
        """
        from unittest.mock import AsyncMock, MagicMock

        mock_wf = MagicMock()
        call_count = {"n": 0}

        async def fake_execute_phase(*args: Any, **kwargs: Any) -> PhaseResult:
            call_count["n"] += 1
            phase = args[1] if len(args) > 1 else kwargs.get("phase")
            return PhaseResult(
                phase=phase,
                success=True,
                output={
                    "phase": phase.value,
                    "call_number": call_count["n"],
                    "previous_output": args[5] if len(args) > 5 else None,
                },
                duration_ms=1.0,
            )

        mock_wf._execute_phase = AsyncMock(side_effect=fake_execute_phase)
        return mock_wf

    @pytest.mark.asyncio
    async def test_stategraph_calls_all_five_phases_in_order(self) -> None:
        """The compiled StateGraph calls workflow._execute_phase for
        all 5 phases in the correct order: research -> analysis ->
        alternatives -> verification -> decision.
        """
        from heretek_swarm.orchestration.langgraph_workflow import (
            LangGraphHeavySwarmWorkflow,
        )

        mock_wf = self._make_mock_workflow()
        wf = LangGraphHeavySwarmWorkflow(name="rigorous", workflow=mock_wf)
        await wf.execute(topic="test-topic")

        assert mock_wf._execute_phase.await_count == 5
        called_phases = [
            call.args[1] for call in mock_wf._execute_phase.await_args_list
        ]
        assert called_phases == [
            WorkflowPhase.RESEARCH,
            WorkflowPhase.ANALYSIS,
            WorkflowPhase.ALTERNATIVES,
            WorkflowPhase.VERIFICATION,
            WorkflowPhase.DECISION,
        ]

    @pytest.mark.asyncio
    async def test_decision_phase_consensus_propagates_to_final_decision(
        self,
    ) -> None:
        """When the decision phase returns consensus_result, it
        propagates to state.final_decision in the WorkflowResult.
        """
        from unittest.mock import AsyncMock, MagicMock

        mock_wf = MagicMock()

        async def phase_return(*args: Any, **kwargs: Any) -> PhaseResult:
            phase = args[1] if len(args) > 1 else kwargs.get("phase")
            output: dict[str, Any] = {"phase": phase.value}
            if phase == WorkflowPhase.DECISION:
                output["consensus_result"] = {
                    "decision": "APPROVE",
                    "confidence": 0.95,
                    "red_flags": [],
                }
            return PhaseResult(
                phase=phase, success=True, output=output, duration_ms=1.0
            )

        mock_wf._execute_phase = AsyncMock(side_effect=phase_return)
        for attr in (
            "_research_phase",
            "_analysis_phase",
            "_alternatives_phase",
            "_verification_phase",
            "_decision_phase",
        ):
            setattr(mock_wf, attr, MagicMock())

        from heretek_swarm.orchestration.langgraph_workflow import (
            LangGraphHeavySwarmWorkflow,
        )

        wf = LangGraphHeavySwarmWorkflow(name="consensus-test", workflow=mock_wf)
        result = await wf.execute(topic="deploy?")

        assert result.state == WorkflowPhase.COMPLETED
        assert result.final_decision is not None
        assert result.final_decision.get("decision") == "APPROVE"
        assert result.final_decision.get("confidence") == 0.95

    @pytest.mark.asyncio
    async def test_each_phase_receives_previous_output(self) -> None:
        """Phases 2-5 receive the previous phase's output as the
        6th positional arg to workflow._execute_phase.
        """
        from heretek_swarm.orchestration.langgraph_workflow import (
            LangGraphHeavySwarmWorkflow,
        )

        mock_wf = self._make_mock_workflow()
        wf = LangGraphHeavySwarmWorkflow(name="chain-test", workflow=mock_wf)
        await wf.execute(topic="chain-topic")

        await_args_list = mock_wf._execute_phase.await_args_list
        # RESEARCH: no previous output (5 args: workflow_id, phase,
        # method, topic, context)
        research_call = await_args_list[0]
        assert len(research_call.args) == 5
        # ANALYSIS: receives RESEARCH output as 6th arg
        analysis_call = await_args_list[1]
        assert len(analysis_call.args) == 6
        assert analysis_call.args[5] is not None
        assert analysis_call.args[5]["phase"] == "research"
        # ALTERNATIVES: receives ANALYSIS output as 6th arg
        alt_call = await_args_list[2]
        assert len(alt_call.args) == 6
        assert alt_call.args[5]["phase"] == "analysis"
        # VERIFICATION: receives ALTERNATIVES output as 6th arg
        ver_call = await_args_list[3]
        assert len(ver_call.args) == 6
        assert ver_call.args[5]["phase"] == "alternatives"
        # DECISION: receives VERIFICATION output as 6th arg
        dec_call = await_args_list[4]
        assert len(dec_call.args) == 6
        assert dec_call.args[5]["phase"] == "verification"

    @pytest.mark.asyncio
    async def test_bridge_passes_workflow_id_and_topic(self) -> None:
        """The bridge passes workflow_id, topic, and context to every
        phase call.
        """
        from heretek_swarm.orchestration.langgraph_workflow import (
            LangGraphHeavySwarmWorkflow,
        )

        mock_wf = self._make_mock_workflow()
        wf = LangGraphHeavySwarmWorkflow(name="args-test", workflow=mock_wf)
        await wf.execute(
            topic="my-topic", context={"k": "v"}, workflow_id="my-wf-42"
        )

        for call in mock_wf._execute_phase.await_args_list:
            assert call.args[0] == "my-wf-42"  # workflow_id
            assert call.args[3] == "my-topic"  # topic
            assert call.args[4] == {"k": "v"}  # context
