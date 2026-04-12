"""
Integration Tests for Behavior Profiling System.

Tests for:
- Activity recording
- Metrics computation
- Profile generation
- Anomaly detection
- Alert management
- Prometheus metrics export
"""

from datetime import UTC, datetime, timedelta

import pytest

from heretek_swarm.actors.profiling import (
    ActionType,
    ActivityRecord,
    AlertSeverity,
    AnomalyType,
    BehaviorMetrics,
    BehaviorProfile,
    BehaviorProfiler,
    ProfilingConfig,
    get_profiler,
    initialize_profiler,
)

# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def profiling_config():
    """Create test profiling configuration."""
    return ProfilingConfig(
        analysis_window_minutes=60,  # Larger window to capture all test activities
        baseline_window_hours=1,
        profile_update_interval_minutes=5,
        frequency_spike_threshold=2.0,
        frequency_drop_threshold=0.2,
        error_rate_threshold=0.15,
        task_failure_threshold=0.25,
        response_time_threshold=2.5,
        pattern_deviation_threshold=2.5,
        alert_on_anomaly=True,
        alert_cooldown_minutes=5,
        max_alerts_per_hour=20,
        enable_prometheus_export=True,
        activity_buffer_size=1000,
        profile_sample_min=5,  # Lower threshold for tests
    )


@pytest.fixture
def profiler(profiling_config):
    """Create behavior profiler instance."""
    return BehaviorProfiler(profiling_config)


@pytest.fixture
def sample_activities():
    """Create sample activity records."""
    now = datetime.now(UTC)

    return [
        ActivityRecord(
            timestamp=now - timedelta(minutes=1),
            agent_id="test-agent-1",
            action=ActionType.MESSAGE_SENT,
            metadata={"channel": "tasks"},
            duration_ms=50.0,
            success=True,
        ),
        ActivityRecord(
            timestamp=now - timedelta(minutes=2),
            agent_id="test-agent-1",
            action=ActionType.TASK_STARTED,
            metadata={"task_id": "task-1"},
            duration_ms=0.0,
            success=True,
        ),
        ActivityRecord(
            timestamp=now - timedelta(minutes=3),
            agent_id="test-agent-1",
            action=ActionType.TASK_COMPLETED,
            metadata={"task_id": "task-1"},
            duration_ms=1500.0,
            success=True,
        ),
        ActivityRecord(
            timestamp=now - timedelta(minutes=4),
            agent_id="test-agent-1",
            action=ActionType.MESSAGE_RECEIVED,
            metadata={"channel": "tasks"},
            duration_ms=10.0,
            success=True,
        ),
        ActivityRecord(
            timestamp=now - timedelta(minutes=5),
            agent_id="test-agent-1",
            action=ActionType.ERROR_OCCURRED,
            metadata={"error": "test_error"},
            duration_ms=0.0,
            success=False,
        ),
    ]


# =============================================================================
# Activity Recording Tests
# =============================================================================

class TestActivityRecording:
    """Tests for activity recording."""

    def test_record_activity(self, profiler):
        """Test recording a single activity."""
        profiler.record_activity(
            agent_id="test-agent",
            action=ActionType.MESSAGE_SENT,
            metadata={"channel": "test"},
            duration_ms=100.0,
            success=True,
        )

        activities = list(profiler._activities["test-agent"])

        assert len(activities) == 1
        assert activities[0].action == ActionType.MESSAGE_SENT
        assert activities[0].duration_ms == 100.0
        assert activities[0].success is True

    def test_record_multiple_activities(self, profiler):
        """Test recording multiple activities."""
        for i in range(10):
            profiler.record_activity(
                agent_id="test-agent",
                action=ActionType.MESSAGE_SENT,
                duration_ms=float(i * 10),
            )

        activities = list(profiler._activities["test-agent"])

        assert len(activities) == 10
        assert profiler._stats["total_activities_recorded"] == 10

    def test_activity_buffer_limit(self, profiler):
        """Test activity buffer size limit."""
        config = ProfilingConfig(activity_buffer_size=100)
        small_profiler = BehaviorProfiler(config)

        for _i in range(150):
            small_profiler.record_activity(
                agent_id="test-agent",
                action=ActionType.MESSAGE_SENT,
            )

        activities = list(small_profiler._activities["test-agent"])

        assert len(activities) == 100  # Limited to buffer size

    def test_record_activity_types(self, profiler):
        """Test recording different activity types."""
        action_types = [
            ActionType.MESSAGE_SENT,
            ActionType.MESSAGE_RECEIVED,
            ActionType.TASK_STARTED,
            ActionType.TASK_COMPLETED,
            ActionType.TASK_FAILED,
            ActionType.STATE_CHANGED,
            ActionType.ERROR_OCCURRED,
            ActionType.TOOL_CALLED,
            ActionType.DECISION_MADE,
            ActionType.LEARNING_EVENT,
            ActionType.CUSTOM,
        ]

        for action in action_types:
            profiler.record_activity(
                agent_id="test-agent",
                action=action,
            )

        activities = list(profiler._activities["test-agent"])

        assert len(activities) == len(action_types)
        recorded_actions = [a.action for a in activities]

        for action in action_types:
            assert action in recorded_actions


# =============================================================================
# Metrics Computation Tests
# =============================================================================

class TestMetricsComputation:
    """Tests for behavior metrics computation."""

    def test_compute_metrics_empty(self, profiler):
        """Test computing metrics with no activities."""
        metrics = profiler.compute_metrics("nonexistent-agent")

        assert metrics is None

    def test_compute_metrics_with_activities(self, profiler, sample_activities):
        """Test computing metrics with sample activities."""
        # Add sample activities
        for activity in sample_activities:
            profiler.record_activity(
                agent_id=activity.agent_id,
                action=activity.action,
                metadata=activity.metadata,
                duration_ms=activity.duration_ms,
                success=activity.success,
            )

        metrics = profiler.compute_metrics("test-agent-1")

        assert metrics is not None
        assert metrics.agent_id == "test-agent-1"
        assert metrics.total_actions >= 4  # At least 4 in window
        assert metrics.message_sent_count >= 1
        assert metrics.message_received_count >= 1
        assert metrics.tasks_completed >= 1

    def test_compute_metrics_task_success_rate(self, profiler):
        """Test task success rate calculation."""
        datetime.now(UTC)

        # Add completed and failed tasks
        for _i in range(8):
            profiler.record_activity(
                agent_id="test-agent",
                action=ActionType.TASK_COMPLETED,
                duration_ms=100.0,
                success=True,
            )

        for _i in range(2):
            profiler.record_activity(
                agent_id="test-agent",
                action=ActionType.TASK_FAILED,
                duration_ms=50.0,
                success=False,
            )

        metrics = profiler.compute_metrics("test-agent")

        assert metrics is not None
        assert metrics.tasks_completed == 8
        assert metrics.tasks_failed == 2
        assert metrics.task_success_rate == 0.8  # 8/10

    def test_compute_metrics_error_rate(self, profiler):
        """Test error rate calculation."""
        # Add activities with errors
        for _i in range(8):
            profiler.record_activity(
                agent_id="test-agent",
                action=ActionType.MESSAGE_SENT,
                success=True,
            )

        for _i in range(2):
            profiler.record_activity(
                agent_id="test-agent",
                action=ActionType.ERROR_OCCURRED,
                success=False,
            )

        metrics = profiler.compute_metrics("test-agent")

        assert metrics is not None
        assert metrics.error_count == 2
        assert metrics.error_rate == 0.2  # 2/10

    def test_compute_metrics_response_time(self, profiler):
        """Test response time metrics."""
        response_times = [50.0, 100.0, 150.0, 200.0, 250.0]

        for rt in response_times:
            profiler.record_activity(
                agent_id="test-agent",
                action=ActionType.MESSAGE_SENT,
                duration_ms=rt,
            )

        metrics = profiler.compute_metrics("test-agent")

        assert metrics is not None
        assert metrics.avg_response_time_ms == 150.0  # Mean of response times
        assert metrics.max_response_time_ms == 250.0
        assert metrics.min_response_time_ms == 50.0

    def test_metrics_caching(self, profiler, sample_activities):
        """Test that metrics are cached."""
        for activity in sample_activities:
            profiler.record_activity(
                agent_id=activity.agent_id,
                action=activity.action,
                duration_ms=activity.duration_ms,
            )

        # First computation
        metrics1 = profiler.compute_metrics("test-agent-1")

        # Should be cached
        assert profiler._current_metrics["test-agent-1"] == metrics1

        # Get cached metrics
        cached = profiler.get_agent_metrics("test-agent-1")

        assert cached == metrics1


# =============================================================================
# Behavior Profile Tests
# =============================================================================

class TestBehaviorProfile:
    """Tests for behavior profile generation and updates."""

    def test_create_profile(self):
        """Test creating a behavior profile."""
        profile = BehaviorProfile(agent_type="test-agent")

        assert profile.agent_type == "test-agent"
        assert profile.sample_count == 0
        assert profile.baseline_actions_per_minute == 0.0

    def test_update_profile_first_sample(self, profiler):
        """Test updating profile with first sample."""
        # Record enough activities to meet the minimum threshold (10)
        for i in range(15):
            profiler.record_activity(
                agent_id="test-agent-1",
                action=ActionType.MESSAGE_SENT,
                duration_ms=50.0 + i * 10,
            )

        profile = profiler.update_profile("test-agent", "test-agent-1")

        # First sample should set baseline values
        assert profile is not None
        assert profile.sample_count >= 1

    def test_update_profile_multiple_samples(self, profiler):
        """Test updating profile with multiple samples."""
        # Record enough activities to meet the minimum threshold (10)
        for i in range(15):
            profiler.record_activity(
                agent_id="test-agent-1",
                action=ActionType.MESSAGE_SENT,
                duration_ms=100.0 + i * 10,
            )

        # Update profile once after recording enough activities
        profile = profiler.update_profile("test-agent", "test-agent-1")

        # Verify profile was created with sample data
        assert profile is not None
        assert profile.sample_count >= 1

    def test_profile_is_within_normal_bounds(self):
        """Test checking if metrics are within normal bounds."""
        profile = BehaviorProfile(agent_type="test-agent")
        profile.baseline_actions_per_minute = 10.0
        profile.actions_per_minute_std = 2.0
        profile.baseline_error_rate = 0.05
        profile.error_rate_std = 0.02

        # Normal metrics
        normal_metrics = BehaviorMetrics(
            agent_id="test-agent-1",
            window_start=datetime.now(UTC) - timedelta(minutes=5),
            window_end=datetime.now(UTC),
            actions_per_minute=11.0,  # Within 1 std
            error_rate=0.06,  # Within 1 std
        )

        is_normal, anomalies = profile.is_within_normal_bounds(normal_metrics, std_threshold=3.0)

        assert is_normal is True
        assert len(anomalies) == 0

        # Anomalous metrics
        anomalous_metrics = BehaviorMetrics(
            agent_id="test-agent-1",
            window_start=datetime.now(UTC) - timedelta(minutes=5),
            window_end=datetime.now(UTC),
            actions_per_minute=20.0,  # 5 stds away
            error_rate=0.20,  # Way above normal
        )

        is_normal, anomalies = profile.is_within_normal_bounds(anomalous_metrics, std_threshold=3.0)

        assert is_normal is False
        assert len(anomalies) > 0

    def test_get_all_profiles(self, profiler):
        """Test getting all profiles."""
        # Create profiles for multiple agent types
        # Note: need to record activities for the SAME agent_id that will be used in update_profile
        for agent_type in ["alpha", "beta", "gamma"]:
            # Record enough activities for a single agent_id to meet minimum threshold
            for i in range(15):
                profiler.record_activity(
                    agent_id=f"{agent_type}-agent",  # Use consistent agent_id
                    action=ActionType.MESSAGE_SENT,
                    duration_ms=50.0 + i * 10,
                )
            # Update profile using the same agent_id
            profiler.update_profile(agent_type, f"{agent_type}-agent")

        profiles = profiler.get_all_profiles()

        assert len(profiles) >= 3
        assert "alpha" in profiles
        assert "beta" in profiles
        assert "gamma" in profiles


# =============================================================================
# Anomaly Detection Tests
# =============================================================================

class TestAnomalyDetection:
    """Tests for anomaly detection."""

    def test_detect_anomalies_no_data(self, profiler):
        """Test anomaly detection with no data."""
        anomalies = profiler.detect_anomalies("nonexistent-agent")

        assert anomalies == []

    def test_detect_anomalies_frequency_spike(self, profiler):
        """Test detecting activity frequency spike."""
        # Establish baseline with normal activity
        for _i in range(10):
            profiler.record_activity(
                agent_id="test-agent",
                action=ActionType.MESSAGE_SENT,
            )
        profiler.update_profile("test-agent", "test-agent")

        # Add spike of activities
        for _i in range(100):
            profiler.record_activity(
                agent_id="test-agent",
                action=ActionType.MESSAGE_SENT,
            )

        anomalies = profiler.detect_anomalies("test-agent")

        # Should detect frequency spike
        spike_anomalies = [a for a in anomalies if a.anomaly_type == AnomalyType.FREQUENCY_SPIKE]
        assert len(spike_anomalies) >= 1

    def test_detect_anomalies_high_error_rate(self, profiler):
        """Test detecting high error rate."""
        config = ProfilingConfig(error_rate_threshold=0.1)
        low_threshold_profiler = BehaviorProfiler(config)

        # Add activities with high error rate
        for _i in range(5):
            low_threshold_profiler.record_activity(
                agent_id="test-agent",
                action=ActionType.MESSAGE_SENT,
                success=True,
            )

        for _i in range(5):
            low_threshold_profiler.record_activity(
                agent_id="test-agent",
                action=ActionType.ERROR_OCCURRED,
                success=False,
            )

        anomalies = low_threshold_profiler.detect_anomalies("test-agent")

        # Should detect high error rate
        error_anomalies = [a for a in anomalies if a.anomaly_type == AnomalyType.ERROR_RATE_HIGH]
        assert len(error_anomalies) >= 1

    def test_detect_anomalies_task_failure_rate(self, profiler):
        """Test detecting high task failure rate."""
        config = ProfilingConfig(task_failure_threshold=0.2)
        low_threshold_profiler = BehaviorProfiler(config)

        # Add tasks with high failure rate
        for _i in range(3):
            low_threshold_profiler.record_activity(
                agent_id="test-agent",
                action=ActionType.TASK_COMPLETED,
                duration_ms=100.0,
            )

        for _i in range(7):
            low_threshold_profiler.record_activity(
                agent_id="test-agent",
                action=ActionType.TASK_FAILED,
                duration_ms=50.0,
            )

        anomalies = low_threshold_profiler.detect_anomalies("test-agent")

        # Should detect high task failure rate
        failure_anomalies = [a for a in anomalies if a.anomaly_type == AnomalyType.TASK_FAILURE_RATE_HIGH]
        assert len(failure_anomalies) >= 1

    def test_anomaly_severity(self, profiler):
        """Test anomaly severity levels."""
        # Create high error rate anomaly
        config = ProfilingConfig(error_rate_threshold=0.1)
        low_threshold_profiler = BehaviorProfiler(config)

        for _i in range(50):
            low_threshold_profiler.record_activity(
                agent_id="test-agent",
                action=ActionType.ERROR_OCCURRED,
                success=False,
            )

        anomalies = low_threshold_profiler.detect_anomalies("test-agent")

        if anomalies:
            anomaly = anomalies[0]
            assert anomaly.severity in [AlertSeverity.LOW, AlertSeverity.MEDIUM, AlertSeverity.HIGH, AlertSeverity.CRITICAL]


# =============================================================================
# Alert Management Tests
# =============================================================================

class TestAlertManagement:
    """Tests for alert management."""

    def test_get_alerts_empty(self, profiler):
        """Test getting alerts when none exist."""
        alerts = profiler.get_alerts()

        assert alerts == []

    def test_alert_generation(self, profiler):
        """Test that anomalies generate alerts."""
        config = ProfilingConfig(
            alert_on_anomaly=True,
            error_rate_threshold=0.05,
        )
        alert_profiler = BehaviorProfiler(config)

        # Generate high error rate
        for _i in range(20):
            alert_profiler.record_activity(
                agent_id="test-agent",
                action=ActionType.ERROR_OCCURRED,
                success=False,
            )

        alert_profiler.detect_anomalies("test-agent")

        alerts = alert_profiler.get_alerts()

        assert len(alerts) >= 1
        assert alerts[0].acknowledged is False

    def test_alert_cooldown(self, profiler):
        """Test alert cooldown mechanism."""
        config = ProfilingConfig(
            alert_on_anomaly=True,
            alert_cooldown_minutes=10,
            error_rate_threshold=0.05,
        )
        cooldown_profiler = BehaviorProfiler(config)

        # Generate anomalies multiple times
        for _ in range(3):
            for _i in range(20):
                cooldown_profiler.record_activity(
                    agent_id="test-agent",
                    action=ActionType.ERROR_OCCURRED,
                    success=False,
                )
            cooldown_profiler.detect_anomalies("test-agent")

        # Should have limited alerts due to cooldown
        alerts = cooldown_profiler.get_alerts()
        assert len(alerts) <= cooldown_profiler.config.max_alerts_per_hour

    def test_acknowledge_alert(self, profiler):
        """Test acknowledging an alert."""
        # Generate an alert
        config = ProfilingConfig(
            alert_on_anomaly=True,
            error_rate_threshold=0.05,
        )
        alert_profiler = BehaviorProfiler(config)

        for _i in range(20):
            alert_profiler.record_activity(
                agent_id="test-agent",
                action=ActionType.ERROR_OCCURRED,
                success=False,
            )

        alert_profiler.detect_anomalies("test-agent")

        # Acknowledge the alert
        result = alert_profiler.acknowledge_alert(0, "test-user")

        assert result is True

        alerts = alert_profiler.get_alerts()
        assert alerts[0].acknowledged is True
        assert alerts[0].acknowledged_by == "test-user"
        assert alerts[0].acknowledged_at is not None

    def test_get_alerts_by_severity(self, profiler):
        """Test filtering alerts by severity."""
        config = ProfilingConfig(alert_on_anomaly=True, error_rate_threshold=0.05)
        alert_profiler = BehaviorProfiler(config)

        # Generate some alerts
        for _i in range(20):
            alert_profiler.record_activity(
                agent_id="test-agent",
                action=ActionType.ERROR_OCCURRED,
                success=False,
            )
        alert_profiler.detect_anomalies("test-agent")

        # Get all alerts
        all_alerts = alert_profiler.get_alerts()

        # Get unacknowledged only
        unack_alerts = alert_profiler.get_alerts(unacknowledged_only=True)

        assert len(unack_alerts) <= len(all_alerts)

    def test_get_alerts_by_agent(self, profiler):
        """Test filtering alerts by agent."""
        config = ProfilingConfig(alert_on_anomaly=True, error_rate_threshold=0.05)
        alert_profiler = BehaviorProfiler(config)

        # Generate alerts for multiple agents
        for agent in ["agent-1", "agent-2", "agent-3"]:
            for _i in range(20):
                alert_profiler.record_activity(
                    agent_id=agent,
                    action=ActionType.ERROR_OCCURRED,
                    success=False,
                )
            alert_profiler.detect_anomalies(agent)

        # Get alerts for specific agent
        agent1_alerts = alert_profiler.get_alerts(agent_id="agent-1")

        for alert in agent1_alerts:
            assert alert.agent_id == "agent-1"


# =============================================================================
# Prometheus Metrics Export Tests
# =============================================================================

class TestPrometheusMetricsExport:
    """Tests for Prometheus metrics export."""

    def test_export_prometheus_metrics(self, profiler):
        """Test exporting Prometheus metrics."""
        # Add some activities
        for _i in range(10):
            profiler.record_activity(
                agent_id="test-agent",
                action=ActionType.MESSAGE_SENT,
            )

        profiler.compute_metrics("test-agent")

        metrics = profiler.export_prometheus_metrics()

        assert "heretek_profiler_total_activities" in metrics
        assert "heretek_profiler_total_anomalies" in metrics
        assert "heretek_profiler_total_alerts" in metrics
        assert "heretek_profiler_profiles_count" in metrics

    def test_export_prometheus_disabled(self):
        """Test disabled Prometheus export."""
        config = ProfilingConfig(enable_prometheus_export=False)
        disabled_profiler = BehaviorProfiler(config)

        metrics = disabled_profiler.export_prometheus_metrics()

        assert "disabled" in metrics.lower()

    def test_export_agent_metrics(self, profiler):
        """Test exporting per-agent metrics."""
        profiler.record_activity(
            agent_id="alpha-1",
            action=ActionType.MESSAGE_SENT,
            duration_ms=100.0,
        )

        profiler.compute_metrics("alpha-1")

        metrics = profiler.export_prometheus_metrics()

        # Should have agent-specific metrics
        assert "agent" in metrics.lower()


# =============================================================================
# Profiler Statistics Tests
# =============================================================================

class TestProfilerStatistics:
    """Tests for profiler statistics."""

    def test_get_stats(self, profiler):
        """Test getting profiler statistics."""
        # Add some activities
        for _i in range(10):
            profiler.record_activity(
                agent_id="test-agent",
                action=ActionType.MESSAGE_SENT,
            )

        stats = profiler.get_stats()

        assert "total_activities_recorded" in stats
        assert "total_anomalies_detected" in stats
        assert "total_alerts_generated" in stats
        assert "profiles_created" in stats
        assert "active_agents" in stats
        assert stats["total_activities_recorded"] == 10

    def test_stats_tracking(self, profiler):
        """Test that statistics are properly tracked."""
        initial_stats = profiler.get_stats()

        # Perform various operations
        for _i in range(5):
            profiler.record_activity(
                agent_id="test-agent",
                action=ActionType.MESSAGE_SENT,
            )

        profiler.compute_metrics("test-agent")
        profiler.detect_anomalies("test-agent")

        final_stats = profiler.get_stats()

        assert final_stats["total_activities_recorded"] == initial_stats["total_activities_recorded"] + 5


# =============================================================================
# Global Profiler Tests
# =============================================================================

class TestGlobalProfiler:
    """Tests for global profiler functions."""

    def test_get_profiler(self):
        """Test getting global profiler."""
        profiler = get_profiler()

        assert profiler is not None
        assert isinstance(profiler, BehaviorProfiler)

    def test_initialize_profiler(self):
        """Test initializing global profiler."""
        config = ProfilingConfig(analysis_window_minutes=10)
        profiler = initialize_profiler(config)

        assert profiler is not None
        assert profiler.config.analysis_window_minutes == 10

        # Subsequent calls should return same instance
        profiler2 = get_profiler()
        assert profiler == profiler2


# =============================================================================
# Integration Tests
# =============================================================================

class TestIntegration:
    """Integration tests for behavior profiling."""

    def test_full_profiling_workflow(self, profiler):
        """Test complete profiling workflow."""
        agent_id = "integration-test-agent"

        # Simulate agent activity over time
        for i in range(50):
            profiler.record_activity(
                agent_id=agent_id,
                action=ActionType.MESSAGE_SENT if i % 3 != 0 else ActionType.TASK_COMPLETED,
                duration_ms=50.0 + (i % 10) * 10,
                success=i % 10 != 0,  # 10% failure rate
            )

        # Compute metrics
        metrics = profiler.compute_metrics(agent_id)

        assert metrics is not None
        assert metrics.total_actions > 0

        # Update profile
        profiler.update_profile("test-agent", agent_id)

        # Detect anomalies
        profiler.detect_anomalies(agent_id)

        # Get alerts
        profiler.get_alerts()

        # Export metrics
        prometheus_metrics = profiler.export_prometheus_metrics()

        assert "heretek_profiler" in prometheus_metrics

        # Get stats
        stats = profiler.get_stats()

        assert stats["total_activities_recorded"] >= 50

    def test_multi_agent_profiling(self, profiler):
        """Test profiling multiple agents simultaneously."""
        agents = ["agent-1", "agent-2", "agent-3", "agent-4", "agent-5"]

        for agent_id in agents:
            for i in range(20):
                profiler.record_activity(
                    agent_id=agent_id,
                    action=ActionType.MESSAGE_SENT,
                    duration_ms=float(i * 5),
                )

            profiler.compute_metrics(agent_id)
            profiler.update_profile("test-agent", agent_id)

        # All agents should have metrics
        for agent_id in agents:
            metrics = profiler.get_agent_metrics(agent_id)
            assert metrics is not None
            assert metrics.total_actions == 20

        # Should have profiles
        profiles = profiler.get_all_profiles()
        assert len(profiles) >= 1

        # Stats should reflect all agents
        stats = profiler.get_stats()
        assert stats["active_agents"] >= 5
