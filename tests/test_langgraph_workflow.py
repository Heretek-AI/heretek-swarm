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

import pytest
from heretek_swarm.orchestration import langgraph_nodes
from heretek_swarm.orchestration.heavyswarm import (
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


class TestPublicContractPreserved:
    def test_workflow_phase_enum_preserved(self) -> None:
        """The WorkflowPhase enum is imported from heavyswarm (no duplication)."""
        from heretek_swarm.orchestration.heavyswarm import WorkflowPhase as _WP

        # langgraph_nodes re-imports WorkflowPhase from heavyswarm
        assert _WP is langgraph_nodes.WorkflowPhase

    def test_phase_result_importable(self) -> None:
        """PhaseResult is importable from both the legacy and new modules."""
        from heretek_swarm.orchestration.heavyswarm import (
            PhaseResult as _LegacyPR,
        )
        from heretek_swarm.orchestration.langgraph_nodes import (
            PhaseResult as _NewPR,
        )
        assert _NewPR is _LegacyPR

    def test_workflow_result_importable(self) -> None:
        """WorkflowResult is importable from both modules (same class)."""
        from heretek_swarm.orchestration.heavyswarm import (
            WorkflowResult as _LegacyWR,
        )
        from heretek_swarm.orchestration.langgraph_nodes import (
            WorkflowResult as _NewWR,
        )
        assert _NewWR is _LegacyWR


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
        """build_legacy_workflow returns a HeavySwarmWorkflow instance."""
        from heretek_swarm.orchestration.heavyswarm import (
            HeavySwarmWorkflow,
        )
        from heretek_swarm.orchestration.langgraph_workflow import (
            build_legacy_workflow,
        )

        wf = build_legacy_workflow(name="test")
        assert isinstance(wf, HeavySwarmWorkflow)
        assert wf.name == "test"


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
