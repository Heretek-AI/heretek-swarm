"""
Tests for Horizontal Scaling Module (S-1)

Tests all scaling components:
- Agent Pool Manager
- Load Balancer
- State Synchronizer

Reference: EXPANSION_ROADMAP.md S-1 Horizontal Scaling
"""

import asyncio
from datetime import UTC, datetime

import pytest

from heretek_swarm.runtime.scaling import (
    AgentPoolManager,
    AgentStatus,
    LoadBalancer,
    LoadBalancingStrategy,
    ScalingAction,
    ScalingConfig,
    StateSynchronizer,
    create_default_scaling,
    create_production_scaling,
)

# =============================================================================
# Test Fixtures
# =============================================================================

@pytest.fixture
def default_config():
    """Create default scaling configuration."""
    return ScalingConfig()


@pytest.fixture
def pool_manager(default_config):
    """Create agent pool manager."""
    return AgentPoolManager(default_config)


@pytest.fixture
def load_balancer():
    """Create load balancer."""
    return LoadBalancer()


@pytest.fixture
def state_synchronizer():
    """Create state synchronizer."""
    return StateSynchronizer()


# =============================================================================
# Agent Pool Manager Tests
# =============================================================================

class TestAgentPoolManager:
    """Tests for Agent Pool Manager."""

    def test_initialization(self, pool_manager):
        """Pool manager should initialize correctly."""
        assert pool_manager.config.min_replicas == 3
        assert pool_manager.config.max_replicas == 50
        assert len(pool_manager.triggers) == 5

    def test_register_instance(self, pool_manager):
        """Should register agent instances."""
        instance = pool_manager.register_instance("agent-1")

        assert instance.instance_id == "agent-1"
        assert instance.status == AgentStatus.PENDING
        assert "agent-1" in pool_manager._instances

    def test_update_instance_status(self, pool_manager):
        """Should update instance status and metrics."""
        pool_manager.register_instance("agent-1")

        pool_manager.update_instance_status(
            "agent-1",
            AgentStatus.ACTIVE,
            metrics={
                "cpu_usage": 45.0,
                "memory_usage": 60.0,
                "active_connections": 10,
            },
        )

        instance = pool_manager._instances["agent-1"]
        assert instance.status == AgentStatus.ACTIVE
        assert instance.cpu_usage == 45.0
        assert instance.memory_usage == 60.0

    @pytest.mark.asyncio
    async def test_get_pool_state_empty(self, pool_manager):
        """Should return empty state when no instances."""
        state = await pool_manager.get_pool_state()

        assert state.total_agents == 0
        assert state.active_agents == 0
        assert state.avg_cpu_usage == 0.0

    @pytest.mark.asyncio
    async def test_get_pool_state_with_instances(self, pool_manager):
        """Should return accurate state with instances."""
        # Register instances
        for i in range(5):
            pool_manager.register_instance(f"agent-{i+1}")

        # Update statuses
        pool_manager.update_instance_status("agent-1", AgentStatus.ACTIVE, {"cpu_usage": 50.0})
        pool_manager.update_instance_status("agent-2", AgentStatus.ACTIVE, {"cpu_usage": 60.0})
        pool_manager.update_instance_status("agent-3", AgentStatus.IDLE, {"cpu_usage": 10.0})
        pool_manager.update_instance_status("agent-4", AgentStatus.PENDING)
        pool_manager.update_instance_status("agent-5", AgentStatus.ACTIVE, {"cpu_usage": 40.0})

        state = await pool_manager.get_pool_state()

        assert state.total_agents == 5
        assert state.active_agents == 3
        assert state.idle_agents == 1
        assert state.pending_agents == 1
        assert state.avg_cpu_usage == 32.0  # (50+60+10+0+40)/5 = 160/5

    @pytest.mark.asyncio
    async def test_evaluate_scaling_no_trigger(self, pool_manager):
        """Should not trigger scaling when metrics are normal."""
        # Register instances
        for i in range(5):
            pool_manager.register_instance(f"agent-{i+1}")
            pool_manager.update_instance_status(f"agent-{i+1}", AgentStatus.ACTIVE)

        # Normal metrics
        metrics = {
            "cpu_usage": 50.0,
            "memory_usage": 60.0,
            "message_queue_depth": 1000,
            "response_time_p95": 200.0,
            "agent_pool_utilization": 80.0,
        }

        result = await pool_manager.evaluate_scaling(metrics)

        assert result is None  # No scaling needed

    @pytest.mark.asyncio
    async def test_evaluate_scaling_cpu_high(self, pool_manager):
        """Should trigger scale up when CPU is high."""
        # Register instances
        for i in range(5):
            pool_manager.register_instance(f"agent-{i+1}")
            pool_manager.update_instance_status(f"agent-{i+1}", AgentStatus.ACTIVE)

        # High CPU
        metrics = {
            "cpu_usage": 85.0,  # Above 70% threshold
            "memory_usage": 60.0,
            "message_queue_depth": 1000,
            "response_time_p95": 200.0,
            "agent_pool_utilization": 90.0,
        }

        result = await pool_manager.evaluate_scaling(metrics)

        assert result is not None
        assert result.action == ScalingAction.SCALE_UP
        assert result.agents_added > 0

    @pytest.mark.asyncio
    async def test_scale_up_respects_max(self, pool_manager):
        """Scale up should respect max replicas."""
        pool_manager.config.max_replicas = 5

        # Register max instances
        for i in range(5):
            pool_manager.register_instance(f"agent-{i+1}")

        # Try to scale up
        result = await pool_manager._scale_up(2, 0, 5)

        assert result.success is False
        assert "max replicas" in result.message

    @pytest.mark.asyncio
    async def test_scale_down_respects_min(self, pool_manager):
        """Scale down should respect min replicas."""
        pool_manager.config.min_replicas = 3

        # Register min instances
        for i in range(3):
            pool_manager.register_instance(f"agent-{i+1}")
            pool_manager.update_instance_status(f"agent-{i+1}", AgentStatus.IDLE)

        # Try to scale down
        result = await pool_manager._scale_down(2, 0, 3)

        assert result.success is False
        assert "min replicas" in result.message

    @pytest.mark.asyncio
    async def test_scale_down_graceful_drain(self, pool_manager):
        """Scale down should gracefully drain idle instances."""
        # Register instances
        for i in range(5):
            pool_manager.register_instance(f"agent-{i+1}")
            pool_manager.update_instance_status(f"agent-{i+1}", AgentStatus.IDLE)

        # Scale down
        result = await pool_manager._scale_down(2, 0, 5)

        assert result.success is True
        assert result.action == ScalingAction.SCALE_DOWN
        assert result.agents_removed == 2

    @pytest.mark.asyncio
    async def test_scale_to_target(self, pool_manager):
        """Should scale to specific target count."""
        # Start with 3 instances
        for i in range(3):
            pool_manager.register_instance(f"agent-{i+1}")

        # Scale to 7
        result = await pool_manager.scale_to(7)

        assert result.success is True
        assert result.new_count == 7
        assert result.agents_added == 4

    def test_cooldown_check(self, pool_manager):
        """Should respect cooldown periods."""

        # Set last scaling time
        pool_manager.last_scaling_time["cpu_high"] = datetime.now(UTC)

        # Check cooldown (should be active)
        assert not pool_manager._cooldown_expired("cpu_high", ScalingAction.SCALE_UP)

    def test_get_metrics(self, pool_manager):
        """Should return accurate metrics."""
        # Register some instances
        for i in range(3):
            pool_manager.register_instance(f"agent-{i+1}")

        metrics = pool_manager.get_metrics()

        assert "evaluation_count" in metrics
        assert "scaling_count" in metrics
        assert "current_instances" in metrics
        assert metrics["current_instances"] == 3
        assert metrics["triggers_configured"] == 5


# =============================================================================
# Load Balancer Tests
# =============================================================================

class TestLoadBalancer:
    """Tests for Load Balancer."""

    def test_initialization(self, load_balancer):
        """Load balancer should initialize correctly."""
        assert load_balancer.strategy == LoadBalancingStrategy.LEAST_CONNECTIONS
        assert load_balancer.session_ttl_seconds == 3600

    def test_register_instance(self, load_balancer):
        """Should register instances."""
        load_balancer.register_instance("agent-1", weight=2)

        assert "agent-1" in load_balancer._healthy_instances
        assert load_balancer._weights["agent-1"] == 2

    def test_unregister_instance(self, load_balancer):
        """Should unregister instances."""
        load_balancer.register_instance("agent-1")
        load_balancer.unregister_instance("agent-1")

        assert "agent-1" not in load_balancer._healthy_instances

    @pytest.mark.asyncio
    async def test_round_robin_selection(self, load_balancer):
        """Should select instances in round robin order."""
        load_balancer.strategy = LoadBalancingStrategy.ROUND_ROBIN

        # Register instances
        for i in range(3):
            load_balancer.register_instance(f"agent-{i+1}")

        # Select multiple times
        selections = []
        for _ in range(6):
            result = await load_balancer.select_instance()
            selections.append(result.selected_instance)

        # Should cycle through instances
        assert len(set(selections)) == 3

    @pytest.mark.asyncio
    async def test_weighted_selection(self, load_balancer):
        """Should respect weights in weighted strategy."""
        load_balancer.strategy = LoadBalancingStrategy.WEIGHTED

        # Register with different weights
        load_balancer.register_instance("agent-1", weight=10)
        load_balancer.register_instance("agent-2", weight=1)

        # Select multiple times
        selections = []
        for _ in range(100):
            result = await load_balancer.select_instance()
            selections.append(result.selected_instance)

        # agent-1 should be selected more often
        agent1_count = selections.count("agent-1")
        assert agent1_count > 50  # Should be > 50% due to higher weight

    @pytest.mark.asyncio
    async def test_sticky_session(self, load_balancer):
        """Should maintain session affinity."""
        load_balancer.strategy = LoadBalancingStrategy.STICKY_SESSION

        # Register instances
        for i in range(3):
            load_balancer.register_instance(f"agent-{i+1}")

        # First request with session
        result1 = await load_balancer.select_instance(session_id="session-123")

        # Subsequent requests should go to same instance
        for _ in range(5):
            result = await load_balancer.select_instance(session_id="session-123")
            assert result.selected_instance == result1.selected_instance

    @pytest.mark.asyncio
    async def test_health_check_integration(self, load_balancer):
        """Should respect health status."""
        load_balancer.register_instance("agent-1")
        load_balancer.register_instance("agent-2")

        # Mark agent-1 as unhealthy
        load_balancer.set_instance_health("agent-1", False)

        # Should only select healthy instances
        for _ in range(10):
            result = await load_balancer.select_instance()
            assert result.selected_instance != "agent-1"

    @pytest.mark.asyncio
    async def test_decision_latency(self, load_balancer):
        """Decision latency should be sub-5ms."""
        # Register instances
        for i in range(10):
            load_balancer.register_instance(f"agent-{i+1}")

        # Measure latency
        latencies = []
        for _ in range(100):
            result = await load_balancer.select_instance()
            latencies.append(result.decision_time_ms)

        avg_latency = sum(latencies) / len(latencies)
        assert avg_latency < 5.0, f"Average latency {avg_latency}ms exceeds 5ms target"

    def test_session_cleanup(self, load_balancer):
        """Should clean up expired sessions."""
        load_balancer.session_ttl_seconds = 1  # 1 second TTL

        # Create session
        load_balancer._session_map["session-1"] = "agent-1"
        load_balancer._session_timestamps["session-1"] = 0  # Old timestamp

        # Cleanup
        load_balancer._cleanup_sessions()

        assert "session-1" not in load_balancer._session_map

    def test_get_metrics(self, load_balancer):
        """Should return accurate metrics."""
        # Register instances and make requests
        for i in range(3):
            load_balancer.register_instance(f"agent-{i+1}")

        metrics = load_balancer.get_metrics()

        assert "total_requests" in metrics
        assert "avg_decision_time_ms" in metrics
        assert "healthy_instances" in metrics
        assert metrics["healthy_instances"] == 3


# =============================================================================
# State Synchronizer Tests
# =============================================================================

class TestStateSynchronizer:
    """Tests for State Synchronizer."""

    def test_initialization(self, state_synchronizer):
        """State synchronizer should initialize correctly."""
        assert state_synchronizer.redis_url == "redis://localhost:6379"
        assert state_synchronizer._state_version == 0

    @pytest.mark.asyncio
    async def test_set_state(self, state_synchronizer):
        """Should set state values."""
        success = await state_synchronizer.set_state("key1", "value1")

        assert success is True
        assert state_synchronizer._local_state["key1"]["value"] == "value1"
        assert state_synchronizer._state_version == 1

    @pytest.mark.asyncio
    async def test_get_state(self, state_synchronizer):
        """Should get state values."""
        await state_synchronizer.set_state("key1", "value1")

        value = await state_synchronizer.get_state("key1")

        assert value == "value1"

    @pytest.mark.asyncio
    async def test_get_state_default(self, state_synchronizer):
        """Should return default for missing keys."""
        value = await state_synchronizer.get_state("nonexistent", default="default")

        assert value == "default"

    @pytest.mark.asyncio
    async def test_state_version_increment(self, state_synchronizer):
        """Should increment version on each set."""
        await state_synchronizer.set_state("key1", "value1")
        await state_synchronizer.set_state("key2", "value2")
        await state_synchronizer.set_state("key1", "value1_updated")

        assert state_synchronizer._state_version == 3

    @pytest.mark.asyncio
    async def test_recover_state(self, state_synchronizer):
        """Should recover state from storage."""
        await state_synchronizer.set_state("key1", "value1")
        await state_synchronizer.set_state("key2", "value2")

        recovered = await state_synchronizer.recover_state()

        assert "key1" in recovered
        assert "key2" in recovered

    def test_get_metrics(self, state_synchronizer):
        """Should return accurate metrics."""
        metrics = state_synchronizer.get_metrics()

        assert "sync_count" in metrics
        assert "avg_latency_ms" in metrics
        assert "state_keys" in metrics
        assert "redis_connected" in metrics


# =============================================================================
# Horizontal Scaling Integration Tests
# =============================================================================

class TestHorizontalScaling:
    """Integration tests for Horizontal Scaling system."""

    def test_initialization(self):
        """Horizontal scaling should initialize correctly."""
        scaling = create_default_scaling()

        assert scaling.pool_manager is not None
        assert scaling.load_balancer is not None
        assert scaling.state_sync is not None

    def test_production_config(self):
        """Production config should have stricter settings."""
        scaling = create_production_scaling()

        assert scaling.config.min_replicas == 5
        assert scaling.config.max_replicas == 100
        assert scaling.config.cpu_threshold_percent == 60.0

    @pytest.mark.asyncio
    async def test_handle_request(self):
        """Should handle requests with load balancing."""
        scaling = create_default_scaling()

        # Register instances
        for i in range(3):
            scaling.load_balancer.register_instance(f"agent-{i+1}")

        # Handle request
        instance_id = await scaling.handle_request()

        assert instance_id in ["agent-1", "agent-2", "agent-3"]

    @pytest.mark.asyncio
    async def test_start_stop(self):
        """Should start and stop cleanly."""
        scaling = create_default_scaling()

        await scaling.start()
        assert scaling._running is True

        await asyncio.sleep(0.1)  # Let it run briefly

        await scaling.stop()
        assert scaling._running is False

    def test_get_all_metrics(self):
        """Should return comprehensive metrics."""
        scaling = create_default_scaling()

        # Register some instances
        for i in range(3):
            scaling.pool_manager.register_instance(f"agent-{i+1}")
            scaling.load_balancer.register_instance(f"agent-{i+1}")

        metrics = scaling.get_all_metrics()

        assert "pool_manager" in metrics
        assert "load_balancer" in metrics
        assert "state_synchronizer" in metrics


# =============================================================================
# Scaling Trigger Tests
# =============================================================================

class TestScalingTriggers:
    """Tests for scaling trigger configurations."""

    def test_cpu_trigger(self, pool_manager):
        """CPU trigger should be configured correctly."""
        trigger = pool_manager.triggers["cpu_high"]

        assert trigger.metric_name == "cpu_usage"
        assert trigger.threshold == 70.0
        assert trigger.action == ScalingAction.SCALE_UP

    def test_memory_trigger(self, pool_manager):
        """Memory trigger should be configured correctly."""
        trigger = pool_manager.triggers["memory_high"]

        assert trigger.metric_name == "memory_usage"
        assert trigger.threshold == 80.0

    def test_queue_depth_trigger(self, pool_manager):
        """Queue depth trigger should be configured correctly."""
        trigger = pool_manager.triggers["queue_depth"]

        assert trigger.metric_name == "message_queue_depth"
        assert trigger.threshold == 10000

    def test_response_time_trigger(self, pool_manager):
        """Response time trigger should be configured correctly."""
        trigger = pool_manager.triggers["response_time"]

        assert trigger.metric_name == "response_time_p95"
        assert trigger.threshold == 500.0

    def test_utilization_trigger(self, pool_manager):
        """Utilization trigger should be configured correctly."""
        trigger = pool_manager.triggers["low_utilization"]

        assert trigger.metric_name == "agent_pool_utilization"
        assert trigger.threshold == 30.0
        assert trigger.action == ScalingAction.SCALE_DOWN


# =============================================================================
# Performance Tests
# =============================================================================

class TestPerformance:
    """Performance tests for horizontal scaling."""

    @pytest.mark.asyncio
    async def test_scale_up_latency(self, pool_manager):
        """Scale up should complete in < 30s per agent."""
        import time

        # Register initial instances
        for i in range(10):
            pool_manager.register_instance(f"agent-{i+1}")

        # Scale up by 5
        start = time.time()
        result = await pool_manager._scale_up(5, start, 10)
        duration = (time.time() - start) * 1000

        assert result.success is True
        # Should be very fast (simulated)
        assert duration < 30000  # 30 seconds

    @pytest.mark.asyncio
    async def test_load_balancer_throughput(self, load_balancer):
        """Load balancer should handle > 10000 requests/second."""
        import time

        # Register instances
        for i in range(10):
            load_balancer.register_instance(f"agent-{i+1}")

        # Measure throughput
        start = time.time()
        for _ in range(10000):
            await load_balancer.select_instance()
        elapsed = time.time() - start

        throughput = 10000 / elapsed
        assert throughput > 10000, f"Throughput {throughput:.0f}/s below 10000/s target"
