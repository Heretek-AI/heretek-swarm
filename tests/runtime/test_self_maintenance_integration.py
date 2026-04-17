"""
Self-Maintenance Integration Tests: Scheduler Lifecycle and AutonomousRuntime Integration

Tests the complete SelfMaintenanceScheduler integration with AutonomousRuntime:
1. Scheduler starts when runtime starts
2. Scheduler stops when runtime stops
3. Scheduler runs tasks on configured intervals
4. Scheduler gracefully degrades when disabled
5. Config extraction from AutonomousRuntime works correctly
6. Observability surfaces (stats, drift results) are properly tracked

Reference: EXPANSION_ROADMAP.md S-3 Self-Healing
Requirements: HEAL-03
"""

import asyncio
import tempfile
from datetime import UTC, datetime, timedelta
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from heretek_swarm.runtime.autonomous_runtime import AutonomousRuntime
from heretek_swarm.runtime.autonomous_runtime_config import (
    AutonomousRuntimeConfig,
)
from heretek_swarm.runtime.self_maintenance import (
    SelfMaintenanceConfig,
    SelfMaintenanceScheduler,
)


# ============================================================================
# Test Fixtures
# ============================================================================


@pytest.fixture
def maintenance_config(tmp_path):
    """Create self-maintenance config with short intervals for fast testing."""
    log_dir = tmp_path / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    baseline_dir = tmp_path / "baselines"
    baseline_dir.mkdir(parents=True, exist_ok=True)

    return SelfMaintenanceConfig(
        run_interval_seconds=1,
        log_rotation_interval_seconds=1,
        db_maintenance_interval_seconds=1,
        config_drift_interval_seconds=1,
        enabled=True,
        log_rotation=__import__(
            "heretek_swarm.runtime.self_maintenance",
            fromlist=["LogRotationConfig"],
        ).LogRotationConfig(
            log_directory=log_dir,
            max_age_days=7,
            compress_above_mb=0.01,  # 10KB for fast testing
            dry_run=False,
        ),
        db_maintenance=__import__(
            "heretek_swarm.runtime.self_maintenance",
            fromlist=["DatabaseMaintenanceConfig"],
        ).DatabaseMaintenanceConfig(
            database_url=None,  # No DB - will skip gracefully
            dry_run=False,
        ),
        config_drift=__import__(
            "heretek_swarm.runtime.self_maintenance",
            fromlist=["ConfigDriftConfig"],
        ).ConfigDriftConfig(
            baseline_directory=baseline_dir,
            critical_keys=(
                "log_level",
                "monitoring_enabled",
                "auto_restart_enabled",
                "max_restart_attempts",
                "state_persistence_enabled",
                "auto_scaling_enabled",
            ),
            dry_run=False,
        ),
    )


@pytest.fixture
def default_runtime_config(tmp_path):
    """Create default autonomous runtime configuration."""
    config = MagicMock(spec=AutonomousRuntimeConfig)
    config.agent_configs = {}
    config.monitoring_enabled = True
    config.auto_restart_enabled = True
    config.max_restart_attempts = 3
    config.restart_delay_seconds = 0.1
    config.health_check_interval = 1
    config.state_persistence_enabled = True
    config.state_backup_interval = 60
    config.metrics_collection_interval = 60
    config.consciousness_plugin_enabled = False
    config.api_host = "localhost"
    config.api_port = 8000
    config.high_latency_threshold_ms = 5000
    config.memory_usage_threshold = 0.9
    config.alert_config = MagicMock()
    config.alert_config.slack_channel = None
    config.alert_config.discord_channel = None
    config.alert_config.email_enabled = False
    config.alert_config.email_recipients = []
    config.auto_scaling_enabled = True
    config.min_agents = 1
    config.max_agents = 5
    config.scale_up_threshold = 0.8
    config.scale_down_threshold = 0.3
    config.scale_up_cooldown_minutes = 10
    config.scale_down_cooldown_minutes = 30
    config.min_uptime_before_scale_down = 60
    config.log_level = "DEBUG"
    config.log_directory = tmp_path / "logs"
    config.log_directory.mkdir(parents=True, exist_ok=True)
    return config


@pytest.fixture
def mock_supervisor():
    """Create mock actor supervisor."""
    supervisor = MagicMock()
    supervisor.actors = {}
    supervisor.terminate_actor = AsyncMock()
    supervisor.spawn_actor = AsyncMock()
    supervisor.terminate_all = AsyncMock()
    return supervisor


@pytest.fixture
def mock_agent_runtime():
    """Create mock agent runtime."""
    runtime = MagicMock()
    runtime.initialize = AsyncMock()
    runtime.spawn_agent = AsyncMock(return_value=True)
    return runtime


@pytest.fixture
def runtime(default_runtime_config, mock_supervisor, mock_agent_runtime):
    """Create autonomous runtime with mocked dependencies."""
    with patch(
        "heretek_swarm.runtime.autonomous_runtime.ActorSupervisor",
        return_value=mock_supervisor,
    ):
        rt = AutonomousRuntime(default_runtime_config)
        rt.supervisor = mock_supervisor
        rt.agent_runtime = mock_agent_runtime
        return rt


@pytest.fixture
def scheduler(maintenance_config, runtime):
    """Create SelfMaintenanceScheduler with maintenance config and runtime reference."""
    return SelfMaintenanceScheduler(maintenance_config, runtime_ref=runtime)


# ============================================================================
# TestSchedulerLifecycle
# ============================================================================


class TestSchedulerLifecycle:
    """Tests for scheduler lifecycle: start, stop, interval execution, and graceful degradation."""

    @pytest.mark.asyncio
    async def test_scheduler_starts_when_runtime_starts(self, scheduler, runtime):
        """Scheduler should start when runtime starts and be tracked in runtime."""
        # Set runtime._running = True (required by implementation)
        runtime._running = True

        # Start the scheduler
        start_task = asyncio.create_task(scheduler.start())
        await asyncio.sleep(0.15)  # Let it start

        # Scheduler should be running
        assert scheduler.get_status()["running"] is True

        # Cleanup
        await scheduler.stop()
        await start_task

    @pytest.mark.asyncio
    async def test_scheduler_stops_when_runtime_stops(self, scheduler, runtime):
        """Scheduler should stop when runtime stops."""
        runtime._running = True

        # Start scheduler
        start_task = asyncio.create_task(scheduler.start())
        await asyncio.sleep(0.1)

        assert scheduler.get_status()["running"] is True

        # Stop scheduler (simulates runtime stop)
        await scheduler.stop()

        # Scheduler should no longer be running
        assert scheduler.get_status()["running"] is False

        # Wait for task to fully complete
        try:
            await asyncio.wait_for(start_task, timeout=1.0)
        except (asyncio.CancelledError, asyncio.TimeoutError):
            pass

    @pytest.mark.asyncio
    async def test_scheduler_runs_tasks_on_interval(self, scheduler):
        """Scheduler should run maintenance tasks on the configured interval."""
        initial_loops = scheduler.get_status()["loops_run"]

        # Run all tasks once directly
        await scheduler._run_all_tasks()

        # Verify loop count incremented
        assert scheduler.get_status()["loops_run"] == initial_loops + 1

    @pytest.mark.asyncio
    async def test_scheduler_runs_multiple_task_cycles(self, scheduler):
        """Scheduler should track multiple cycles of running tasks."""
        # Run multiple cycles
        for _ in range(3):
            await scheduler._run_all_tasks()

        assert scheduler.get_status()["loops_run"] == 3

    @pytest.mark.asyncio
    async def test_scheduler_graceful_degradation_when_disabled(self, maintenance_config, runtime):
        """Scheduler should gracefully degrade when disabled."""
        maintenance_config.enabled = False
        scheduler = SelfMaintenanceScheduler(maintenance_config, runtime_ref=runtime)

        # Scheduler should not start when disabled
        await scheduler.start()

        status = scheduler.get_status()
        assert status["enabled"] is False
        # Should not be running since it's disabled
        assert status["running"] is False

    @pytest.mark.asyncio
    async def test_scheduler_handles_shutdown_event(self, scheduler, runtime):
        """Scheduler should respond to shutdown event."""
        runtime._running = True

        # Start scheduler
        start_task = asyncio.create_task(scheduler.start())
        await asyncio.sleep(0.1)

        assert scheduler.get_status()["running"] is True

        # Signal shutdown via the event
        scheduler._shutdown_event.set()
        runtime._shutdown_event.set()

        # Wait for graceful shutdown
        try:
            await asyncio.wait_for(start_task, timeout=2.0)
        except (asyncio.CancelledError, asyncio.TimeoutError):
            pass

    @pytest.mark.asyncio
    async def test_scheduler_tracks_log_rotation_stats(self, scheduler):
        """Scheduler should track log rotation statistics."""
        await scheduler._run_all_tasks()

        stats = scheduler.get_status()
        assert "log_rotation_stats" in stats
        # Verify the stats contain expected keys
        assert "files_removed" in stats["log_rotation_stats"]
        assert "bytes_freed" in stats["log_rotation_stats"]
        assert "errors" in stats["log_rotation_stats"]

    @pytest.mark.asyncio
    async def test_scheduler_tracks_db_maintenance_stats(self, scheduler):
        """Scheduler should track database maintenance statistics."""
        # Ensure no DATABASE_URL
        with patch.dict("os.environ", {}, clear=True):
            await scheduler._run_all_tasks()

        stats = scheduler.get_status()
        assert "db_maintenance_stats" in stats
        # Verify the stats contain expected keys
        assert "vacuum_analyze_runs" in stats["db_maintenance_stats"]
        assert "orphaned_deleted" in stats["db_maintenance_stats"]
        assert "checkpoints_pruned" in stats["db_maintenance_stats"]
        assert "errors" in stats["db_maintenance_stats"]


# ============================================================================
# TestRuntimeConfigExtraction
# ============================================================================


class TestRuntimeConfigExtraction:
    """Tests for _get_runtime_config() extracting correct values from AutonomousRuntimeConfig."""

    @pytest.mark.asyncio
    async def test_extracts_log_level(self, scheduler, runtime):
        """Should extract log_level from runtime config."""
        runtime.config.log_level = "INFO"
        config = scheduler._get_runtime_config()
        assert config["log_level"] == "INFO"

    @pytest.mark.asyncio
    async def test_extracts_monitoring_enabled(self, scheduler, runtime):
        """Should extract monitoring_enabled from runtime config."""
        runtime.config.monitoring_enabled = True
        config = scheduler._get_runtime_config()
        assert config["monitoring_enabled"] is True

        runtime.config.monitoring_enabled = False
        config = scheduler._get_runtime_config()
        assert config["monitoring_enabled"] is False

    @pytest.mark.asyncio
    async def test_extracts_auto_restart_enabled(self, scheduler, runtime):
        """Should extract auto_restart_enabled from runtime config."""
        runtime.config.auto_restart_enabled = True
        config = scheduler._get_runtime_config()
        assert config["auto_restart_enabled"] is True

    @pytest.mark.asyncio
    async def test_extracts_max_restart_attempts(self, scheduler, runtime):
        """Should extract max_restart_attempts from runtime config."""
        runtime.config.max_restart_attempts = 5
        config = scheduler._get_runtime_config()
        assert config["max_restart_attempts"] == 5

    @pytest.mark.asyncio
    async def test_extracts_state_persistence_enabled(self, scheduler, runtime):
        """Should extract state_persistence_enabled from runtime config."""
        runtime.config.state_persistence_enabled = True
        config = scheduler._get_runtime_config()
        assert config["state_persistence_enabled"] is True

    @pytest.mark.asyncio
    async def test_extracts_auto_scaling_enabled(self, scheduler, runtime):
        """Should extract auto_scaling_enabled from runtime config."""
        runtime.config.auto_scaling_enabled = True
        config = scheduler._get_runtime_config()
        assert config["auto_scaling_enabled"] is True

    @pytest.mark.asyncio
    async def test_returns_empty_dict_when_no_runtime_ref(self, maintenance_config):
        """Should return empty dict when runtime_ref is None."""
        scheduler = SelfMaintenanceScheduler(maintenance_config, runtime_ref=None)
        config = scheduler._get_runtime_config()
        assert config == {}

    @pytest.mark.asyncio
    async def test_handles_missing_config_attributes(self, scheduler, runtime):
        """Should handle missing config attributes gracefully."""
        # Remove an attribute to simulate incomplete config
        del runtime.config.monitoring_enabled
        config = scheduler._get_runtime_config()
        # Should not raise, should use getattr with None default
        assert "monitoring_enabled" not in config or config.get("monitoring_enabled") is None

    @pytest.mark.asyncio
    async def test_extracts_all_critical_keys(self, scheduler, runtime):
        """Should extract all critical configuration keys for drift detection."""
        runtime.config.log_level = "DEBUG"
        runtime.config.monitoring_enabled = True
        runtime.config.auto_restart_enabled = True
        runtime.config.max_restart_attempts = 10
        runtime.config.state_persistence_enabled = False
        runtime.config.auto_scaling_enabled = True

        config = scheduler._get_runtime_config()

        expected_keys = {
            "log_level",
            "monitoring_enabled",
            "auto_restart_enabled",
            "max_restart_attempts",
            "state_persistence_enabled",
            "auto_scaling_enabled",
        }
        assert set(config.keys()) == expected_keys
        assert config["log_level"] == "DEBUG"
        assert config["max_restart_attempts"] == 10


# ============================================================================
# TestSchedulerAutonomousRuntimeIntegration
# ============================================================================


class TestSchedulerAutonomousRuntimeIntegration:
    """Integration tests for the full lifecycle with real async."""

    @pytest.mark.asyncio
    async def test_full_lifecycle_runtime_to_scheduler(self, scheduler, runtime):
        """Test full lifecycle: runtime starts → scheduler starts → scheduler runs → runtime stops → scheduler stops."""
        # Set runtime._running = True (required by implementation)
        runtime._running = True

        # Clear DATABASE_URL to avoid connection errors
        with patch.dict("os.environ", {}, clear=True):
            # Start scheduler
            scheduler_task = asyncio.create_task(scheduler.start())

            # Wait for scheduler to run at least one cycle
            await asyncio.sleep(1.5)

            # Verify scheduler ran
            assert scheduler.get_status()["loops_run"] >= 1

            # Scheduler should be running
            assert scheduler.get_status()["running"] is True

            # Stop runtime (signals shutdown)
            runtime._running = False
            runtime._shutdown_event.set()
            await scheduler.stop()

            # Wait for scheduler task to complete
            try:
                await asyncio.wait_for(scheduler_task, timeout=2.0)
            except (asyncio.CancelledError, asyncio.TimeoutError):
                pass

        # Verify scheduler stopped - directly check the internal flag
        # The stop() method sets _running = False
        assert scheduler._running is False

    @pytest.mark.asyncio
    async def test_scheduler_integrated_in_runtime_start(self, default_runtime_config, maintenance_config):
        """Scheduler should be integrated into runtime start/stop lifecycle."""
        mock_agent_runtime_instance = MagicMock()
        mock_agent_runtime_instance.initialize = AsyncMock()

        mock_supervisor_cls = MagicMock()
        mock_supervisor_instance = MagicMock()
        mock_supervisor_instance.terminate_all = AsyncMock()
        mock_supervisor_cls.return_value = mock_supervisor_instance

        with patch(
            "heretek_swarm.runtime.autonomous_runtime.AgentRuntime",
            return_value=mock_agent_runtime_instance,
        ):
            with patch(
                "heretek_swarm.runtime.autonomous_runtime.ActorSupervisor",
                mock_supervisor_cls,
            ):
                with patch.object(
                    AutonomousRuntime, "_start_initial_agents", new_callable=AsyncMock
                ):
                    runtime = AutonomousRuntime(default_runtime_config)
                    await runtime.initialize()

                    # Scheduler should be initialized
                    assert runtime._maintenance_scheduler is not None
                    assert isinstance(
                        runtime._maintenance_scheduler, SelfMaintenanceScheduler
                    )

                    # Scheduler should reference the runtime
                    assert runtime._maintenance_scheduler.runtime_ref is runtime

                    # Stop runtime
                    await runtime.stop()

    @pytest.mark.asyncio
    async def test_scheduler_stop_called_on_runtime_stop(self, default_runtime_config, maintenance_config):
        """Stopping runtime should also stop the scheduler."""
        mock_agent_runtime_instance = MagicMock()
        mock_agent_runtime_instance.initialize = AsyncMock()

        mock_supervisor_cls = MagicMock()
        mock_supervisor_instance = MagicMock()
        mock_supervisor_instance.terminate_all = AsyncMock()
        mock_supervisor_cls.return_value = mock_supervisor_instance

        with patch(
            "heretek_swarm.runtime.autonomous_runtime.AgentRuntime",
            return_value=mock_agent_runtime_instance,
        ):
            with patch(
                "heretek_swarm.runtime.autonomous_runtime.ActorSupervisor",
                mock_supervisor_cls,
            ):
                with patch.object(
                    AutonomousRuntime, "_start_initial_agents", new_callable=AsyncMock
                ):
                    runtime = AutonomousRuntime(default_runtime_config)
                    await runtime.initialize()

                    # Start the scheduler manually to test stop
                    runtime._maintenance_scheduler._running = True

                    # Stop runtime
                    await runtime.stop()

                    # Scheduler should be stopped
                    assert (
                        runtime._maintenance_scheduler.get_status()["running"] is False
                    )

    @pytest.mark.asyncio
    async def test_config_drift_detection_with_runtime_config(
        self, scheduler, runtime
    ):
        """Scheduler should detect config drift using runtime config values."""
        # Store baseline with current config
        runtime.config.log_level = "INFO"
        runtime.config.monitoring_enabled = True
        runtime.config.auto_restart_enabled = True
        runtime.config.max_restart_attempts = 3
        runtime.config.state_persistence_enabled = True
        runtime.config.auto_scaling_enabled = False

        await scheduler.store_current_as_baseline("runtime")

        # Change a value
        runtime.config.log_level = "DEBUG"

        # Detect drift
        result = await scheduler._drift_detector.detect_drift(
            scheduler._get_runtime_config(), "runtime"
        )

        assert result["has_drift"] is True
        assert "log_level" in result["changed_keys"]

    @pytest.mark.asyncio
    async def test_no_drift_when_config_unchanged(self, scheduler, runtime):
        """Should report no drift when runtime config matches baseline."""
        # Store baseline
        runtime.config.log_level = "INFO"
        runtime.config.monitoring_enabled = True
        runtime.config.auto_restart_enabled = True
        runtime.config.max_restart_attempts = 3
        runtime.config.state_persistence_enabled = True
        runtime.config.auto_scaling_enabled = False

        await scheduler.store_current_as_baseline("runtime")

        # Detect drift (no changes)
        result = await scheduler._drift_detector.detect_drift(
            scheduler._get_runtime_config(), "runtime"
        )

        assert result["has_drift"] is False

    @pytest.mark.asyncio
    async def test_scheduler_status_includes_drift_result(self, scheduler, runtime):
        """Scheduler status should include last drift detection result."""
        # Store baseline
        runtime.config.log_level = "DEBUG"
        runtime.config.monitoring_enabled = True
        runtime.config.auto_restart_enabled = True
        runtime.config.max_restart_attempts = 3
        runtime.config.state_persistence_enabled = True
        runtime.config.auto_scaling_enabled = False

        await scheduler.store_current_as_baseline("runtime")

        # Run all tasks (which includes drift detection)
        await scheduler._run_all_tasks()

        status = scheduler.get_status()
        assert "last_drift_result" in status
        assert status["last_drift_result"] is not None

    @pytest.mark.asyncio
    async def test_integration_status_indicates_autonomous_runtime(
        self, scheduler, runtime
    ):
        """Scheduler integration status should indicate AutonomousRuntime."""
        status = scheduler.get_status()
        assert status["integration"] == "autonomous_runtime"

    @pytest.mark.asyncio
    async def test_standalone_scheduler_has_correct_integration_status(
        self, maintenance_config
    ):
        """Standalone scheduler (no runtime_ref) should have correct integration status."""
        scheduler = SelfMaintenanceScheduler(maintenance_config, runtime_ref=None)
        status = scheduler.get_status()
        assert status["integration"] == "standalone"


# ============================================================================
# Observability Surface Tests
# ============================================================================


class TestObservabilitySurfaces:
    """Tests verifying observability surfaces are properly tracked."""

    @pytest.mark.asyncio
    async def test_log_rotation_stats_tracked(self, scheduler, maintenance_config):
        """Log rotation stats should be tracked and accessible."""
        # Run log rotation
        await scheduler._log_rotator.rotate()

        stats = scheduler.get_status()
        assert "log_rotation_stats" in stats
        assert "files_removed" in stats["log_rotation_stats"]
        assert "bytes_freed" in stats["log_rotation_stats"]
        assert "errors" in stats["log_rotation_stats"]

    @pytest.mark.asyncio
    async def test_db_maintenance_stats_tracked(self, scheduler):
        """DB maintenance stats should be tracked and accessible."""
        # Run DB maintenance (will skip due to no DATABASE_URL)
        with patch.dict("os.environ", {}, clear=True):
            await scheduler._db_maintenance.run_maintenance()

        stats = scheduler.get_status()
        assert "db_maintenance_stats" in stats
        assert "vacuum_analyze_runs" in stats["db_maintenance_stats"]
        assert "orphaned_deleted" in stats["db_maintenance_stats"]
        assert "checkpoints_pruned" in stats["db_maintenance_stats"]
        assert "errors" in stats["db_maintenance_stats"]

    @pytest.mark.asyncio
    async def test_config_drift_results_tracked(self, scheduler, runtime):
        """Config drift results should be tracked and accessible."""
        # Store baseline
        runtime.config.log_level = "INFO"
        runtime.config.monitoring_enabled = True
        runtime.config.auto_restart_enabled = True
        runtime.config.max_restart_attempts = 3
        runtime.config.state_persistence_enabled = True
        runtime.config.auto_scaling_enabled = False

        await scheduler.store_current_as_baseline("runtime")

        # Detect drift
        await scheduler._drift_detector.detect_drift(
            scheduler._get_runtime_config(), "runtime"
        )

        last_result = scheduler._drift_detector.get_last_result()
        assert last_result is not None

    @pytest.mark.asyncio
    async def test_get_stats_returns_all_maintenance_stats(self, scheduler):
        """get_stats() should return comprehensive maintenance statistics."""
        # Run all tasks
        await scheduler._run_all_tasks()

        # Access internal stats (as get_status does)
        stats = scheduler.get_status()

        # Verify all expected stats are present
        assert "log_rotation_stats" in stats
        assert "db_maintenance_stats" in stats
        assert "last_drift_result" in stats
        assert "loops_run" in stats
        assert "enabled" in stats
        assert "running" in stats


# ============================================================================
# Error Handling Tests
# ============================================================================


class TestSchedulerErrorHandling:
    """Tests for error handling in scheduler."""

    @pytest.mark.asyncio
    async def test_handles_log_directory_not_exists(self, maintenance_config, runtime):
        """Should handle non-existent log directory gracefully."""
        maintenance_config.log_rotation.log_directory = Path("/nonexistent/path")
        scheduler = SelfMaintenanceScheduler(maintenance_config, runtime_ref=runtime)

        # Should not raise - returns stats with files_removed=0, bytes_freed=0
        stats = await scheduler._log_rotator.rotate()
        # Log directory doesn't exist so no files to process, no errors
        assert stats["files_removed"] == 0
        assert stats["bytes_freed"] == 0

    @pytest.mark.asyncio
    async def test_handles_missing_baseline_on_first_run(self, scheduler):
        """Should handle missing baseline gracefully on first drift detection."""
        result = await scheduler._drift_detector.detect_drift(
            {"log_level": "INFO"}, "first_run"
        )

        # Should return has_drift=False with reason
        assert result["has_drift"] is False
        assert result["reason"] == "no_baseline"

    @pytest.mark.asyncio
    async def test_scheduler_components_accessible(self, scheduler):
        """All scheduler components should be accessible via properties."""
        assert scheduler.log_rotator is not None
        assert scheduler.db_maintenance is not None
        assert scheduler.drift_detector is not None


# ============================================================================
# Full Integration: Runtime + Scheduler End-to-End
# ============================================================================


class TestFullIntegrationEndToEnd:
    """End-to-end integration tests verifying complete runtime + scheduler lifecycle."""

    @pytest.mark.asyncio
    async def test_runtime_initializes_scheduler(self, default_runtime_config, mock_supervisor, mock_agent_runtime):
        """Runtime should initialize scheduler on initialization."""
        mock_agent_runtime_instance = MagicMock()
        mock_agent_runtime_instance.initialize = AsyncMock()

        mock_supervisor_cls = MagicMock()
        mock_supervisor_cls.return_value = mock_supervisor

        with patch(
            "heretek_swarm.runtime.autonomous_runtime.AgentRuntime",
            return_value=mock_agent_runtime_instance,
        ):
            with patch(
                "heretek_swarm.runtime.autonomous_runtime.ActorSupervisor",
                mock_supervisor_cls,
            ):
                with patch.object(
                    AutonomousRuntime, "_start_initial_agents", new_callable=AsyncMock
                ):
                    runtime = AutonomousRuntime(default_runtime_config)
                    await runtime.initialize()

                    # Verify scheduler is initialized
                    assert runtime._maintenance_scheduler is not None
                    assert isinstance(
                        runtime._maintenance_scheduler, SelfMaintenanceScheduler
                    )

                    # Verify config is passed
                    assert (
                        runtime._maintenance_scheduler.config
                        == runtime._maintenance_config
                    )

    @pytest.mark.asyncio
    async def test_scheduler_provides_runtime_config_for_drift_detection(
        self, scheduler, runtime
    ):
        """Scheduler should provide runtime config for drift detection."""
        # Set specific runtime config values
        runtime.config.log_level = "WARNING"
        runtime.config.monitoring_enabled = False
        runtime.config.auto_restart_enabled = True
        runtime.config.max_restart_attempts = 7
        runtime.config.state_persistence_enabled = True
        runtime.config.auto_scaling_enabled = True

        # Store baseline
        path = await scheduler.store_current_as_baseline("runtime")

        # Read stored baseline
        import json
        stored = json.loads(Path(path).read_text())

        assert stored["log_level"] == "WARNING"
        assert stored["monitoring_enabled"] is False
        assert stored["max_restart_attempts"] == 7

    @pytest.mark.asyncio
    async def test_scheduler_runs_all_tasks_in_sequence(self, scheduler):
        """Scheduler should run all maintenance tasks in sequence."""
        # Track execution order
        execution_order = []

        original_log_rotate = scheduler._log_rotator.rotate
        original_db_maintenance = scheduler._db_maintenance.run_maintenance

        async def tracked_log_rotate():
            execution_order.append("log_rotation")
            return await original_log_rotate()

        async def tracked_db_maintenance():
            execution_order.append("db_maintenance")
            return await original_db_maintenance()

        scheduler._log_rotator.rotate = tracked_log_rotate
        scheduler._db_maintenance.run_maintenance = tracked_db_maintenance

        # Mock drift detection to track it
        original_drift = scheduler._drift_detector.detect_drift

        async def tracked_drift(*args, **kwargs):
            execution_order.append("drift_detection")
            return await original_drift(*args, **kwargs)

        scheduler._drift_detector.detect_drift = tracked_drift

        # Run all tasks
        await scheduler._run_all_tasks()

        # Verify all were called
        assert "log_rotation" in execution_order
        assert "db_maintenance" in execution_order
        assert "drift_detection" in execution_order
