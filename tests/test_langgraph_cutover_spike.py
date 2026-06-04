"""Tests for the Phase 2A.2 langgraph cutover spike."""

from __future__ import annotations

from heretek_swarm.integrations.langgraph_cutover_spike import run_dry_spike
from heretek_swarm.orchestration.langgraph_workflow import (
    LangGraphHeavySwarmWorkflow,
    WorkflowPhase,
    WorkflowResult,
    WorkflowState,
)


def test_dry_spike_passes():
    """The langgraph cutover API surface is valid."""
    run_dry_spike()


def test_workflow_phase_has_5_phases_plus_terminals():
    """WorkflowPhase has the 5 expected phases plus COMPLETED/FAILED."""
    expected = {
        "RESEARCH",
        "ANALYSIS",
        "ALTERNATIVES",
        "VERIFICATION",
        "DECISION",
        "COMPLETED",
        "FAILED",
    }
    actual = {p.name for p in WorkflowPhase}
    assert actual == expected


def test_canonical_workflow_class_is_importable():
    """LangGraphHeavySwarmWorkflow is importable from orchestration/."""
    assert LangGraphHeavySwarmWorkflow is not None
    assert callable(LangGraphHeavySwarmWorkflow)


def test_workflow_state_and_result_are_classes():
    """WorkflowState and WorkflowResult are the public dataclasses."""
    assert WorkflowState is not None
    assert callable(WorkflowState)
    assert WorkflowResult is not None
    assert callable(WorkflowResult)
