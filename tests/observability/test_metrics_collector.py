"""
Test suite for SwarmMetricsCollector and RealTimeMetricsStream.

Tests cover:
- Agent metrics collection
- Swarm metrics aggregation
- Consciousness metrics collection
- Health score calculation
- Real-time metrics streaming
- Prometheus export format
"""

import asyncio

import pytest

from heretek_swarm.observability.metrics import (
    AgentMetrics,
    ConsciousnessMetricsData,
    MetricsSnapshot,
    RealTimeMetricsStream,
    SwarmMetricsCollector,
    SwarmMetricsData,
    record_consensus_round,
    record_message_sent,
    record_task_completion,
)


class TestAgentMetrics:
    """Test AgentMetrics dataclass."""

    def test_agent_metrics_creation(self):
        """Test creating AgentMetrics instance."""
        metrics = AgentMetrics(
            agent_id="test-agent-001",
            agent_type="coordinator",
        )

        assert metrics.agent_id == "test-agent-001"
        assert metrics.agent_type == "coordinator"
        assert metrics.tasks_completed == 0
        assert metrics.tasks_failed == 0
        assert metrics.health_score == 0.0
        assert metrics.success_rate == 0.0

    def test_agent_metrics_to_dict(self):
        """Test AgentMetrics serialization."""
        metrics = AgentMetrics(
            agent_id="test-agent-001",
            agent_type="coordinator",
            tasks_completed=10,
            tasks_failed=2,
            health_score=85.0,
        )

        result = metrics.to_dict()

        assert result["agent_id"] == "test-agent-001"
        assert result["agent_type"] == "coordinator"
        assert result["tasks_completed"] == 10
        assert result["tasks_failed"] == 2
        assert result["health_score"] == 85.0


class TestSwarmMetricsData:
    """Test SwarmMetricsData dataclass."""

    def test_swarm_metrics_creation(self):
        """Test creating SwarmMetricsData instance."""
        metrics = SwarmMetricsData(
            total_agents=5,
            active_agents=3,
            idle_agents=2,
            health_score=75.0,
        )

        assert metrics.total_agents == 5
        assert metrics.active_agents == 3
        assert metrics.idle_agents == 2
        assert metrics.health_score == 75.0

    def test_swarm_metrics_to_dict(self):
        """Test SwarmMetricsData serialization."""
        metrics = SwarmMetricsData(
            total_agents=5,
            active_agents=3,
            completed_tasks=100,
            failed_tasks=10,
        )

        result = metrics.to_dict()

        assert result["total_agents"] == 5
        assert result["active_agents"] == 3
        assert result["completed_tasks"] == 100
        assert result["failed_tasks"] == 10


class TestConsciousnessMetricsData:
    """Test ConsciousnessMetricsData dataclass."""

    def test_consciousness_metrics_creation(self):
        """Test creating ConsciousnessMetricsData instance."""
        metrics = ConsciousnessMetricsData(
            phi_score=0.75,
            phi_avg=0.65,
            integration_level="high",
        )

        assert metrics.phi_score == 0.75
        assert metrics.phi_avg == 0.65
        assert metrics.integration_level == "high"

    def test_consciousness_metrics_to_dict(self):
        """Test ConsciousnessMetricsData serialization."""
        metrics = ConsciousnessMetricsData(
            phi_score=0.75,
            agent_phi_scores={"agent-1": 0.8, "agent-2": 0.7},
        )

        result = metrics.to_dict()

        assert result["phi_score"] == 0.75
        assert result["agent_phi_scores"]["agent-1"] == 0.8
        assert result["agent_phi_scores"]["agent-2"] == 0.7


class TestSwarmMetricsCollector:
    """Test SwarmMetricsCollector class."""

    @pytest.fixture
    def collector(self):
        """Create a SwarmMetricsCollector instance."""
        return SwarmMetricsCollector()

    def test_collector_initialization(self, collector):
        """Test collector initialization."""
        assert collector._agent_metrics == {}
        assert collector._agent_states == {}
        assert collector._swarm_metrics_history == []

    def test_update_agent_state(self, collector):
        """Test updating agent state."""
        collector.update_agent_state("agent-1", "active")

        assert collector._agent_states["agent-1"] == "active"
        assert "agent-1" in collector._agent_metrics

    def test_record_agent_task_success(self, collector):
        """Test recording successful agent task."""
        collector.record_agent_task(
            agent_id="agent-1",
            duration_seconds=0.5,
            success=True,
            agent_type="coordinator",
        )

        metrics = collector._agent_metrics["agent-1"]
        assert metrics.tasks_completed == 1
        assert metrics.tasks_failed == 0
        assert metrics.success_rate == 1.0
        assert metrics.avg_task_duration_seconds == 0.5

    def test_record_agent_task_failure(self, collector):
        """Test recording failed agent task."""
        collector.record_agent_task(
            agent_id="agent-1",
            duration_seconds=1.0,
            success=False,
            agent_type="coordinator",
        )

        metrics = collector._agent_metrics["agent-1"]
        assert metrics.tasks_failed == 1
        assert metrics.tasks_completed == 0
        assert metrics.success_rate == 0.0
        assert metrics.error_count == 1

    def test_record_agent_message(self, collector):
        """Test recording agent messages."""
        collector.record_agent_message("agent-1", sent=True, latency_seconds=0.05)
        collector.record_agent_message("agent-1", sent=False, latency_seconds=0.03)

        metrics = collector._agent_metrics["agent-1"]
        assert metrics.messages_sent == 1
        assert metrics.messages_received == 1

    def test_record_agent_error(self, collector):
        """Test recording agent errors."""
        collector.record_agent_error("agent-1", error_type="timeout")

        metrics = collector._agent_metrics["agent-1"]
        assert metrics.error_count == 1

    def test_collect_agent_metrics(self, collector):
        """Test collecting agent metrics."""
        collector.record_agent_task("agent-1", 0.5, True, "coordinator")

        metrics = collector.collect_agent_metrics("agent-1")

        assert metrics.agent_id == "agent-1"
        assert metrics.tasks_completed == 1
        assert metrics.agent_type == "coordinator"

    def test_collect_agent_metrics_unknown(self, collector):
        """Test collecting metrics for unknown agent."""
        metrics = collector.collect_agent_metrics("unknown-agent")

        assert metrics.agent_id == "unknown-agent"
        assert metrics.agent_type == "worker"
        assert metrics.tasks_completed == 0

    def test_collect_swarm_metrics(self, collector):
        """Test collecting swarm metrics."""
        collector.update_agent_state("agent-1", "active")
        collector.update_agent_state("agent-2", "active")
        collector.update_agent_state("agent-3", "idle")

        collector.record_agent_task("agent-1", 0.5, True)
        collector.record_agent_task("agent-2", 0.3, True)

        swarm_data = collector.collect_swarm_metrics()

        assert swarm_data.total_agents == 3
        assert swarm_data.idle_agents == 1
        assert swarm_data.completed_tasks == 2

    def test_calculate_health_score(self, collector):
        """Test health score calculation."""
        # Add agents with good metrics
        collector.update_agent_state("agent-1", "active")
        collector.record_agent_task("agent-1", 0.5, True)
        collector.record_agent_message("agent-1", sent=True)
        collector.record_agent_message("agent-1", sent=False)

        health_score = collector.calculate_health_score()

        assert 0.0 <= health_score <= 100.0

    def test_calculate_health_score_empty(self, collector):
        """Test health score with no agents."""
        health_score = collector.calculate_health_score()

        assert health_score == 0.0

    def test_collect_consciousness_metrics(self, collector):
        """Test collecting consciousness metrics."""
        # Register a callback that returns phi scores
        def consciousness_callback():
            return {
                "phi_scores": {"agent-1": 0.8, "agent-2": 0.6},
                "fep_scores": {"agent-1": 0.3, "agent-2": 0.4},
            }

        collector.register_consciousness_callback(consciousness_callback)

        metrics = collector.collect_consciousness_metrics()

        assert metrics.phi_avg == 0.7
        assert metrics.phi_max == 0.8
        assert metrics.phi_min == 0.6
        assert "agent-1" in metrics.agent_phi_scores
        assert "agent-2" in metrics.agent_fep_scores

    def test_register_callbacks(self, collector):
        """Test registering state and consciousness callbacks."""
        state_callback_called = False
        consciousness_callback_called = False

        def state_callback():
            nonlocal state_callback_called
            state_callback_called = True
            return {"agent-1": "active"}

        def consciousness_callback():
            nonlocal consciousness_callback_called
            consciousness_callback_called = True
            return {"phi_scores": {"agent-1": 0.7}}

        collector.register_agent_state_callback(state_callback)
        collector.register_consciousness_callback(consciousness_callback)

        # Trigger callbacks by collecting metrics
        collector.collect_swarm_metrics()
        collector.collect_consciousness_metrics()

        assert state_callback_called
        assert consciousness_callback_called

    def test_get_all_agent_metrics(self, collector):
        """Test getting all agent metrics."""
        collector.record_agent_task("agent-1", 0.5, True)
        collector.record_agent_task("agent-2", 0.3, True)

        all_metrics = collector.get_all_agent_metrics()

        assert len(all_metrics) == 2
        assert "agent-1" in all_metrics
        assert "agent-2" in all_metrics

    def test_get_agent_states(self, collector):
        """Test getting all agent states."""
        collector.update_agent_state("agent-1", "active")
        collector.update_agent_state("agent-2", "idle")

        states = collector.get_agent_states()

        assert states["agent-1"] == "active"
        assert states["agent-2"] == "idle"

    def test_metrics_history(self, collector):
        """Test metrics history tracking."""
        collector.collect_swarm_metrics()
        collector.collect_swarm_metrics()
        collector.collect_consciousness_metrics()

        swarm_history = collector.get_agent_metrics_history(limit=10)
        consciousness_history = collector.get_consciousness_metrics_history(limit=10)

        assert len(swarm_history) == 2
        assert len(consciousness_history) == 1

    def test_agent_health_calculation(self, collector):
        """Test internal agent health calculation."""
        metrics = AgentMetrics(
            agent_id="test",
            agent_type="test",
            tasks_completed=8,
            tasks_failed=2,
            error_count=1,
        )

        health = collector._calculate_agent_health(metrics)

        assert 0.0 <= health <= 100.0

    def test_integration_level_determination(self, collector):
        """Test integration level determination from phi scores."""
        high_phi = {"a1": 0.9, "a2": 0.85, "a3": 0.95}
        low_phi = {"a1": 0.1, "a2": 0.15, "a3": 0.2}

        high_level = collector._determine_integration_level(high_phi)
        low_level = collector._determine_integration_level(low_phi)

        assert high_level == "very_high"
        assert low_level == "minimal"

    def test_differentiation_level_determination(self, collector):
        """Test differentiation level determination from phi variance."""
        uniform_phi = {"a1": 0.5, "a2": 0.5, "a3": 0.5}
        varied_phi = {"a1": 0.1, "a2": 0.5, "a3": 0.9}

        uniform_level = collector._determine_differentiation_level(uniform_phi)
        varied_level = collector._determine_differentiation_level(varied_phi)

        assert uniform_level == "minimal"
        # Varied phi should result in higher differentiation
        assert varied_level in ["minimal", "low", "moderate", "high", "very_high"]


class TestRealTimeMetricsStream:
    """Test RealTimeMetricsStream class."""

    @pytest.fixture
    def collector(self):
        """Create a SwarmMetricsCollector instance."""
        return SwarmMetricsCollector()

    @pytest.fixture
    def stream(self, collector):
        """Create a RealTimeMetricsStream instance."""
        return RealTimeMetricsStream(collector)

    def test_stream_initialization(self, stream):
        """Test stream initialization."""
        assert not stream._running
        assert stream._snapshot is None

    def test_get_metrics_snapshot(self, stream, collector):
        """Test getting metrics snapshot."""
        # Add some test data
        collector.update_agent_state("agent-1", "active")
        collector.record_agent_task("agent-1", 0.5, True)

        snapshot = stream.get_metrics_snapshot()

        assert isinstance(snapshot, MetricsSnapshot)
        assert snapshot.swarm_metrics.total_agents >= 1
        assert snapshot.health_score >= 0.0

    def test_get_metrics_snapshot_cached(self, stream, collector):
        """Test that snapshot is cached."""
        collector.update_agent_state("agent-1", "active")

        # First call creates snapshot
        snapshot1 = stream.get_metrics_snapshot()
        # Second call returns cached snapshot
        snapshot2 = stream.get_metrics_snapshot()

        assert snapshot1 is snapshot2

    def test_export_prometheus_format(self, stream, collector):
        """Test Prometheus format export."""
        collector.update_agent_state("agent-1", "active")
        collector.record_agent_task("agent-1", 0.5, True)

        prometheus_data = stream.export_prometheus_format()

        assert isinstance(prometheus_data, str)
        assert "heretek_swarm_health_score" in prometheus_data
        assert "heretek_swarm_total_agents" in prometheus_data
        assert "heretek_swarm_consciousness_phi_avg" in prometheus_data

    def test_export_prometheus_format_headers(self, stream, collector):
        """Test Prometheus format has proper headers."""
        collector.update_agent_state("agent-1", "active")

        prometheus_data = stream.export_prometheus_format()
        lines = prometheus_data.split("\n")

        # Check for HELP and TYPE lines
        help_lines = [l for l in lines if l.startswith("# HELP")]
        type_lines = [l for l in lines if l.startswith("# TYPE")]

        assert len(help_lines) > 0
        assert len(type_lines) > 0

    def test_stop_streaming(self, stream):
        """Test stopping the stream."""
        stream._running = True
        stream.stop_streaming()

        assert not stream._running

    @pytest.mark.asyncio
    async def test_stream_metrics(self, stream, collector):
        """Test streaming metrics."""
        collector.update_agent_state("agent-1", "active")

        # Create a task that collects one iteration then stops
        async def collect_one():
            async for metrics in stream.stream_metrics(interval_seconds=0.1):
                assert "swarm_metrics" in metrics
                assert "consciousness_metrics" in metrics
                assert "health_score" in metrics
                stream.stop_streaming()
                break

        await asyncio.wait_for(collect_one(), timeout=5.0)

    @pytest.mark.asyncio
    async def test_stream_metrics_stops(self, stream, collector):
        """Test that stream stops when stop_streaming is called."""
        collector.update_agent_state("agent-1", "active")

        stream._running = True

        async def stop_after_delay():
            await asyncio.sleep(0.2)
            stream.stop_streaming()

        async def collect():
            count = 0
            async for _metrics in stream.stream_metrics(interval_seconds=0.1):
                count += 1
                if count > 5:
                    stream.stop_streaming()
                    break
            return count

        # Run both tasks
        stop_task = asyncio.create_task(stop_after_delay())
        collect_task = asyncio.create_task(collect())

        await asyncio.gather(stop_task, collect_task, return_exceptions=True)

        assert not stream._running


class TestMetricsSnapshot:
    """Test MetricsSnapshot dataclass."""

    def test_snapshot_creation(self):
        """Test creating MetricsSnapshot instance."""
        swarm = SwarmMetricsData(total_agents=5)
        consciousness = ConsciousnessMetricsData(phi_score=0.7)
        agents = {"agent-1": AgentMetrics(agent_id="agent-1", agent_type="test")}

        snapshot = MetricsSnapshot(
            swarm_metrics=swarm,
            consciousness_metrics=consciousness,
            agent_metrics=agents,
            health_score=75.0,
        )

        assert snapshot.swarm_metrics.total_agents == 5
        assert snapshot.consciousness_metrics.phi_score == 0.7
        assert snapshot.health_score == 75.0

    def test_snapshot_to_dict(self):
        """Test MetricsSnapshot serialization."""
        swarm = SwarmMetricsData(total_agents=5)
        consciousness = ConsciousnessMetricsData(phi_score=0.7)
        agents = {"agent-1": AgentMetrics(agent_id="agent-1", agent_type="test")}

        snapshot = MetricsSnapshot(
            swarm_metrics=swarm,
            consciousness_metrics=consciousness,
            agent_metrics=agents,
            health_score=75.0,
        )

        result = snapshot.to_dict()

        assert result["swarm_metrics"]["total_agents"] == 5
        assert result["consciousness_metrics"]["phi_score"] == 0.7
        assert "agent-1" in result["agent_metrics"]
        assert result["health_score"] == 75.0


class TestConvenienceFunctions:
    """Test module-level convenience functions."""

    @pytest.mark.asyncio
    async def test_record_message_sent(self):
        """Test record_message_sent function."""
        # Should not raise - call with correct signature
        await record_message_sent("task-1", "coordinator", {"type": "test"})

    @pytest.mark.asyncio
    async def test_record_task_completion(self):
        """Test record_task_completion function."""
        # Should not raise - call with correct signature
        await record_task_completion("task-1", "coordinator", True, {"duration": 0.5})

    @pytest.mark.asyncio
    async def test_record_consensus_round(self):
        """Test record_consensus_round function."""
        # Should not raise - call with correct signature
        await record_consensus_round("round-1", {"decision": "approved", "confidence": 0.9})


class TestMetricsIntegration:
    """Integration tests for metrics system."""

    def test_full_metrics_collection_cycle(self):
        """Test complete metrics collection cycle."""
        collector = SwarmMetricsCollector()
        stream = RealTimeMetricsStream(collector)

        # Simulate agent activity
        for i in range(5):
            agent_id = f"agent-{i}"
            collector.update_agent_state(agent_id, "active" if i < 3 else "idle")
            collector.record_agent_task(agent_id, 0.3 + (i * 0.1), i % 2 == 0)
            collector.record_agent_message(agent_id, sent=True)
            collector.record_agent_message(agent_id, sent=False)

        # Collect metrics
        swarm = collector.collect_swarm_metrics()
        collector.collect_consciousness_metrics()
        health = collector.calculate_health_score()

        # Verify
        assert swarm.total_agents == 5
        assert swarm.active_agents == 3
        assert swarm.idle_agents == 2
        assert 0.0 <= health <= 100.0

        # Get snapshot
        snapshot = stream.get_metrics_snapshot()
        assert snapshot.swarm_metrics.total_agents == 5
        assert snapshot.health_score == health

    def test_callback_integration(self):
        """Test callback integration."""
        collector = SwarmMetricsCollector()

        # Mock external data sources
        def mock_state_callback():
            return {
                "agent-1": "active",
                "agent-2": "active",
                "agent-3": "offline",
            }

        def mock_consciousness_callback():
            return {
                "phi_scores": {
                    "agent-1": 0.85,
                    "agent-2": 0.75,
                    "agent-3": 0.0,
                },
                "fep_scores": {
                    "agent-1": 0.2,
                    "agent-2": 0.3,
                    "agent-3": 0.0,
                },
            }

        collector.register_agent_state_callback(mock_state_callback)
        collector.register_consciousness_callback(mock_consciousness_callback)

        # Collect metrics (triggers callbacks)
        swarm = collector.collect_swarm_metrics()
        consciousness = collector.collect_consciousness_metrics()

        assert swarm.total_agents >= 0
        assert consciousness.phi_avg > 0.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
