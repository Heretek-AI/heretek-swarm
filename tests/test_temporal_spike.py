"""Tests for the Phase 3A-side Temporal spike."""

from temporalio import activity, workflow
from temporalio.worker import Worker

from heretek_swarm.orchestration.temporal_spike import (
    HeavySwarmWorkflow,
    run_dry_spike,
)


def test_dry_spike_passes():
    """The Temporal cutover API surface is valid."""
    run_dry_spike()


def test_heavy_swarm_workflow_defined():
    """HeavySwarmWorkflow is a Temporal workflow class."""
    assert HeavySwarmWorkflow is not None


def test_activity_decorator_works():
    """activity.defn is the migration target decorator."""
    assert callable(activity.defn)


def test_workflow_decorator_works():
    """workflow.defn + workflow.run + workflow.execute_activity work."""
    assert callable(workflow.defn)
    assert callable(workflow.run)
    assert callable(workflow.execute_activity)


def test_worker_class_importable():
    """Worker class is the worker entry point."""
    assert callable(Worker)
