"""Tests for the workflow execution event bus."""

import asyncio

import pytest

from heretek_swarm.workflow.execution_events import (
    WorkflowExecutionEventBus,
    get_execution_event_bus,
)


class TestWorkflowExecutionEventBus:
    """Unit tests for WorkflowExecutionEventBus."""

    def test_singleton_returns_same_instance(self):
        bus1 = get_execution_event_bus()
        bus2 = get_execution_event_bus()
        assert bus1 is bus2

    def test_emit_and_get_history(self):
        bus = WorkflowExecutionEventBus()
        bus.emit("exec-1", {"status": "started", "progress": 0})
        bus.emit("exec-1", {"status": "running", "progress": 50})
        bus.emit("exec-1", {"status": "completed", "progress": 100})

        history = bus.get_history("exec-1")
        assert len(history) == 3
        assert history[0]["status"] == "started"
        assert history[2]["status"] == "completed"

    def test_get_history_unknown_execution(self):
        bus = WorkflowExecutionEventBus()
        assert bus.get_history("nonexistent") == []

    def test_history_respects_max_size(self):
        bus = WorkflowExecutionEventBus(max_history=3)
        for i in range(5):
            bus.emit("exec-1", {"seq": i})

        history = bus.get_history("exec-1")
        assert len(history) == 3
        assert history[0]["seq"] == 2
        assert history[-1]["seq"] == 4

    def test_clear_removes_history_and_queue(self):
        bus = WorkflowExecutionEventBus()
        bus.emit("exec-1", {"status": "started"})
        bus.subscribe("exec-1")

        bus.clear("exec-1")
        assert bus.get_history("exec-1") == []
        assert "exec-1" not in bus._queues

    def test_clear_nonexistent_is_noop(self):
        bus = WorkflowExecutionEventBus()
        bus.clear("nonexistent")  # should not raise

    def test_subscribe_returns_queue(self):
        bus = WorkflowExecutionEventBus()
        queue = bus.subscribe("exec-1")
        assert isinstance(queue, asyncio.Queue)

    def test_subscribe_same_id_returns_same_queue(self):
        bus = WorkflowExecutionEventBus()
        q1 = bus.subscribe("exec-1")
        q2 = bus.subscribe("exec-1")
        assert q1 is q2

    def test_emit_pushes_to_subscribed_queue(self):
        bus = WorkflowExecutionEventBus()
        queue = bus.subscribe("exec-1")
        bus.emit("exec-1", {"status": "running"})
        assert not queue.empty()

    def test_emit_queue_full_is_silent(self):
        bus = WorkflowExecutionEventBus()
        queue = bus.subscribe("exec-1")
        # Fill the queue
        for i in range(256):
            queue.put_nowait({"seq": i})
        # This should not raise
        bus.emit("exec-1", {"status": "overflow"})

    def test_multiple_executions_isolated(self):
        bus = WorkflowExecutionEventBus()
        bus.emit("exec-1", {"id": "a"})
        bus.emit("exec-2", {"id": "b"})

        assert len(bus.get_history("exec-1")) == 1
        assert len(bus.get_history("exec-2")) == 1
        assert bus.get_history("exec-1")[0]["id"] == "a"
        assert bus.get_history("exec-2")[0]["id"] == "b"
