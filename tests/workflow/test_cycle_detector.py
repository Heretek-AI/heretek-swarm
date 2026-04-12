"""
Unit Tests for Workflow Cycle Detector.

Tests cover:
- Cycle detection algorithms
- Cycle breaking strategies
- Path tracking
- Metrics collection
- Prometheus export
- 5-phase workflow tracking
"""

import time

import pytest

from heretek_swarm.workflow.cycle_detector import (
    CycleBreakingStrategy,
    CycleDetectionEvent,
    ExecutionPath,
    FivePhaseWorkflowTracker,
    WorkflowCycleDetector,
)


class TestExecutionPath:
    """Tests for ExecutionPath class."""

    def test_add_node(self):
        """Test adding nodes to execution path."""
        path = ExecutionPath(path_id="test_path")

        count = path.add_node("node_a")
        assert count == 1
        assert path.nodes == ["node_a"]
        assert path.visit_counts["node_a"] == 1

        count = path.add_node("node_b")
        assert count == 1
        assert path.nodes == ["node_a", "node_b"]

        count = path.add_node("node_a")
        assert count == 2
        assert path.visit_counts["node_a"] == 2

    def test_get_cycle_simple(self):
        """Test simple cycle detection."""
        path = ExecutionPath(path_id="test_path")
        path.nodes = ["a", "b", "c", "a"]
        path.visit_counts = {"a": 2, "b": 1, "c": 1}

        cycle = path.get_cycle()
        assert cycle is not None
        assert "a" in cycle

    def test_get_cycle_no_cycle(self):
        """Test when no cycle exists."""
        path = ExecutionPath(path_id="test_path")
        path.nodes = ["a", "b", "c", "d"]
        path.visit_counts = {"a": 1, "b": 1, "c": 1, "d": 1}

        cycle = path.get_cycle()
        assert cycle is None

    def test_get_cycle_empty(self):
        """Test cycle detection on empty path."""
        path = ExecutionPath(path_id="test_path")

        cycle = path.get_cycle()
        assert cycle is None

    def test_to_dict(self):
        """Test path serialization."""
        path = ExecutionPath(path_id="test_path")
        path.add_node("node_a")
        path.add_node("node_b")

        result = path.to_dict()
        assert result["path_id"] == "test_path"
        assert result["nodes"] == ["node_a", "node_b"]
        assert "start_time" in result
        assert result["visit_counts"] == {"node_a": 1, "node_b": 1}


class TestWorkflowCycleDetector:
    """Tests for WorkflowCycleDetector class."""

    def test_initialization(self):
        """Test detector initialization."""
        detector = WorkflowCycleDetector(
            max_iterations=50,
            timeout_seconds=60.0,
            convergence_threshold=0.01,
        )

        assert detector.max_iterations == 50
        assert detector.timeout_seconds == 60.0
        assert detector.convergence_threshold == 0.01
        assert detector.track_paths is True

    def test_start_workflow_tracking(self):
        """Test starting workflow tracking."""
        detector = WorkflowCycleDetector()
        workflow_id = "test_workflow"

        detector.start_workflow_tracking(workflow_id)

        assert workflow_id in detector.visited_nodes
        assert workflow_id in detector.execution_paths
        assert workflow_id in detector.workflow_start_times
        assert detector.iteration_counts[workflow_id] == 0

    def test_stop_workflow_tracking(self):
        """Test stopping workflow tracking."""
        detector = WorkflowCycleDetector()
        workflow_id = "test_workflow"

        detector.start_workflow_tracking(workflow_id)
        detector.stop_workflow_tracking(workflow_id)

        assert workflow_id not in detector.visited_nodes
        assert workflow_id not in detector.execution_paths

    def test_record_node_execution(self):
        """Test recording node executions."""
        detector = WorkflowCycleDetector()
        workflow_id = "test_workflow"

        count = detector.record_node_execution(workflow_id, "node_a")
        assert count == 1

        count = detector.record_node_execution(workflow_id, "node_a")
        assert count == 2

        count = detector.record_node_execution(workflow_id, "node_b")
        assert count == 1

        assert detector.iteration_counts[workflow_id] == 3

    def test_detect_cycle_no_tracking(self):
        """Test cycle detection without tracking."""
        detector = WorkflowCycleDetector()

        result = detector.detect_cycle("nonexistent", "node_a")
        assert result is False

    def test_detect_cycle_simple(self):
        """Test simple cycle detection."""
        detector = WorkflowCycleDetector()
        workflow_id = "test_workflow"

        detector.start_workflow_tracking(workflow_id)
        detector.record_node_execution(workflow_id, "node_a")
        detector.record_node_execution(workflow_id, "node_b")
        detector.record_node_execution(workflow_id, "node_c")

        # No cycle yet
        result = detector.detect_cycle(workflow_id, "node_d")
        assert result is False

        # Create a cycle by returning to node_a
        detector.record_node_execution(workflow_id, "node_a")
        detector.record_node_execution(workflow_id, "node_b")

        # Now detecting node_a again should trigger cycle
        result = detector.detect_cycle(workflow_id, "node_a")
        assert result is True

    def test_detect_cycle_repeated_node(self):
        """Test cycle detection with repeated node visits."""
        detector = WorkflowCycleDetector()
        workflow_id = "test_workflow"

        detector.start_workflow_tracking(workflow_id)

        # Visit node_a multiple times
        for _ in range(3):
            detector.record_node_execution(workflow_id, "node_a")

        # Detecting node_a again should trigger (3+ occurrences)
        result = detector.detect_cycle(workflow_id, "node_a")
        assert result is True

    def test_should_break_cycle_max_iterations(self):
        """Test cycle breaking due to max iterations."""
        detector = WorkflowCycleDetector(max_iterations=5)
        workflow_id = "test_workflow"

        detector.start_workflow_tracking(workflow_id)

        # Execute up to max iterations
        for i in range(5):
            detector.record_node_execution(workflow_id, f"node_{i}")

        # Should break cycle now
        result = detector.should_break_cycle(workflow_id)
        assert result is True

    def test_should_break_cycle_timeout(self):
        """Test cycle breaking due to timeout."""
        detector = WorkflowCycleDetector(timeout_seconds=0.1)
        workflow_id = "test_workflow"

        detector.start_workflow_tracking(workflow_id)

        # Wait for timeout
        time.sleep(0.15)

        result = detector.should_break_cycle(workflow_id)
        assert result is True

    def test_should_break_cycle_convergence(self):
        """Test cycle breaking due to state convergence."""
        detector = WorkflowCycleDetector(convergence_threshold=0.001)
        workflow_id = "test_workflow"

        detector.start_workflow_tracking(workflow_id)
        detector.record_node_execution(workflow_id, "node_a", state={"value": 0.0001})

        result = detector.should_break_cycle(workflow_id)
        assert result is True

    def test_break_cycle(self):
        """Test breaking a cycle."""
        detector = WorkflowCycleDetector()
        workflow_id = "test_workflow"

        detector.start_workflow_tracking(workflow_id)
        detector.record_node_execution(workflow_id, "node_a")
        detector.record_node_execution(workflow_id, "node_b")
        detector.record_node_execution(workflow_id, "node_c")

        event = detector.break_cycle(
            workflow_id,
            CycleBreakingStrategy.MAX_ITERATIONS,
            reason="Test break",
        )

        assert isinstance(event, CycleDetectionEvent)
        assert event.workflow_id == workflow_id
        assert event.breaking_strategy == "max_iterations"
        assert event.resolution == "Test break"
        assert len(detector.detected_cycles) == 1
        assert detector.metrics["total_cycles_detected"] == 1

    def test_get_metrics(self):
        """Test getting metrics."""
        detector = WorkflowCycleDetector()
        workflow_id = "test_workflow"

        detector.start_workflow_tracking(workflow_id)
        detector.record_node_execution(workflow_id, "node_a")
        detector.record_node_execution(workflow_id, "node_b")

        metrics = detector.get_metrics()

        assert "total_cycles_detected" in metrics
        assert "total_cycles_broken" in metrics
        assert "cycles_by_strategy" in metrics
        assert "avg_iterations_before_cycle" in metrics

    def test_export_prometheus_metrics(self):
        """Test Prometheus metrics export."""
        detector = WorkflowCycleDetector()

        metrics_str = detector.export_prometheus_metrics()

        assert "heretek_workflow_cycles_total" in metrics_str
        assert "heretek_workflow_cycles_broken_total" in metrics_str
        assert "heretek_workflow_avg_iterations_before_cycle" in metrics_str

    def test_clear_history(self):
        """Test clearing history."""
        detector = WorkflowCycleDetector()
        workflow_id = "test_workflow"

        detector.start_workflow_tracking(workflow_id)
        detector.record_node_execution(workflow_id, "node_a")
        detector.break_cycle(workflow_id, CycleBreakingStrategy.MAX_ITERATIONS)

        detector.clear_history()

        assert len(detector.detected_cycles) == 0
        assert detector.metrics["total_cycles_detected"] == 0


class TestFivePhaseWorkflowTracker:
    """Tests for FivePhaseWorkflowTracker class."""

    def test_initialization(self):
        """Test tracker initialization."""
        tracker = FivePhaseWorkflowTracker(max_phase_repeats=2)

        assert tracker.max_phase_repeats == 2
        assert tracker.phase_history == {}

    def test_record_phase_transition(self):
        """Test recording phase transitions."""
        tracker = FivePhaseWorkflowTracker()
        workflow_id = "test_workflow"

        tracker.record_phase_transition(workflow_id, "plan", "analyze")
        tracker.record_phase_transition(workflow_id, "analyze", "execute")

        assert workflow_id in tracker.phase_history
        assert tracker.phase_history[workflow_id] == ["analyze", "execute"]
        assert tracker.phase_counts[workflow_id]["analyze"] == 1
        assert tracker.phase_counts[workflow_id]["execute"] == 1

    def test_detect_phase_cycle(self):
        """Test phase cycle detection."""
        tracker = FivePhaseWorkflowTracker(max_phase_repeats=2)
        workflow_id = "test_workflow"

        # Record phase transitions
        tracker.record_phase_transition(workflow_id, "", "plan")
        tracker.record_phase_transition(workflow_id, "plan", "plan")

        # Detecting plan again should trigger (max_repeats=2)
        result = tracker.detect_phase_cycle(workflow_id, "plan")
        assert result is True

    def test_get_phase_statistics(self):
        """Test getting phase statistics."""
        tracker = FivePhaseWorkflowTracker()
        workflow_id = "test_workflow"

        tracker.record_phase_transition(workflow_id, "", "plan")
        tracker.record_phase_transition(workflow_id, "plan", "analyze")
        tracker.record_phase_transition(workflow_id, "analyze", "execute")

        stats = tracker.get_phase_statistics(workflow_id)

        assert stats["total_transitions"] == 3
        assert stats["current_phase"] == "execute"
        assert "plan" in stats["phase_counts"]


class TestCycleDetectionEvent:
    """Tests for CycleDetectionEvent class."""

    def test_to_dict(self):
        """Test event serialization."""
        event = CycleDetectionEvent(
            event_id="event_123",
            workflow_id="workflow_456",
            correlation_id="corr_789",
            cycle_path=["a", "b", "c"],
            detection_time="2026-04-07T12:00:00Z",
            breaking_strategy="max_iterations",
            resolution="test_resolution",
            metadata={"key": "value"},
        )

        result = event.to_dict()

        assert result["event_id"] == "event_123"
        assert result["workflow_id"] == "workflow_456"
        assert result["cycle_path"] == ["a", "b", "c"]
        assert result["breaking_strategy"] == "max_iterations"
        assert result["metadata"]["key"] == "value"


class TestIntegration:
    """Integration tests for cycle detector."""

    @pytest.mark.asyncio
    async def test_full_workflow_lifecycle(self):
        """Test complete workflow lifecycle with cycle detection."""
        detector = WorkflowCycleDetector(max_iterations=10)
        workflow_id = "integration_test"

        # Start tracking
        detector.start_workflow_tracking(workflow_id)

        # Simulate workflow execution
        phases = ["plan", "analyze", "execute", "validate", "report"]
        for _i, phase in enumerate(phases):
            detector.record_node_execution(workflow_id, phase, state={"phase": phase})

            # Check for cycles
            if detector.detect_cycle(workflow_id, phase):
                if detector.should_break_cycle(workflow_id):
                    detector.break_cycle(workflow_id, CycleBreakingStrategy.MAX_ITERATIONS)

        # Get final metrics
        metrics = detector.get_metrics()
        assert "total_cycles_detected" in metrics

        # Stop tracking
        detector.stop_workflow_tracking(workflow_id)

    def test_multiple_workflows(self):
        """Test tracking multiple workflows simultaneously."""
        detector = WorkflowCycleDetector()

        # Start multiple workflows
        for i in range(3):
            workflow_id = f"workflow_{i}"
            detector.start_workflow_tracking(workflow_id)
            detector.record_node_execution(workflow_id, "node_a")

        # Verify all tracked
        for i in range(3):
            workflow_id = f"workflow_{i}"
            assert workflow_id in detector.visited_nodes
            assert detector.get_iteration_count(workflow_id) == 1

        # Stop all
        for i in range(3):
            detector.stop_workflow_tracking(f"workflow_{i}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
