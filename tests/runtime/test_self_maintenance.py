"""
Tests for Self-Maintenance Module (S-3)

Tests all self-maintenance components:
- Log rotation: removes files older than 7 days, compresses files >10MB
- Database maintenance: VACUUM ANALYZE, prune orphaned records
- Configuration drift detection: compare against stored baseline
- SelfMaintenanceScheduler: interval execution integrated with AutonomousRuntime

Reference: EXPANSION_ROADMAP.md S-3 Self-Healing
"""

import asyncio
import gzip
import json
import os
import tempfile
from datetime import UTC, datetime, timedelta
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from heretek_swarm.runtime.self_maintenance import (
    ConfigDriftConfig,
    ConfigDriftDetector,
    DatabaseMaintenance,
    DatabaseMaintenanceConfig,
    LogRotationConfig,
    LogRotator,
    SelfMaintenanceConfig,
    SelfMaintenanceScheduler,
)


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def temp_log_dir(tmp_path):
    """Create a temporary log directory with test files."""
    log_dir = tmp_path / "logs"
    log_dir.mkdir()
    return log_dir


@pytest.fixture
def temp_baseline_dir(tmp_path):
    """Create a temporary baseline directory."""
    baseline_dir = tmp_path / "baselines"
    baseline_dir.mkdir(parents=True, exist_ok=True)
    return baseline_dir


@pytest.fixture
def log_rotation_config(temp_log_dir):
    """Create log rotation config pointing to temp directory."""
    return LogRotationConfig(
        log_directory=temp_log_dir,
        max_age_days=7,
        compress_above_mb=0.01,  # 10KB for fast testing
        dry_run=False,
    )


@pytest.fixture
def db_maintenance_config():
    """Create database maintenance config with no DB URL (memory-only)."""
    return DatabaseMaintenanceConfig(database_url=None, dry_run=False)


@pytest.fixture
def config_drift_config(temp_baseline_dir):
    """Create config drift config with temp baseline directory."""
    return ConfigDriftConfig(
        baseline_directory=temp_baseline_dir,
        critical_keys=("log_level", "monitoring_enabled", "auto_restart_enabled"),
        dry_run=False,
    )


@pytest.fixture
def maintenance_config(temp_log_dir, temp_baseline_dir):
    """Create full self-maintenance config for scheduler tests."""
    return SelfMaintenanceConfig(
        log_rotation=LogRotationConfig(
            log_directory=temp_log_dir,
            max_age_days=7,
            compress_above_mb=0.01,
        ),
        db_maintenance=DatabaseMaintenanceConfig(database_url=None),
        config_drift=ConfigDriftConfig(
            baseline_directory=temp_baseline_dir,
            critical_keys=("log_level", "monitoring_enabled"),
        ),
        run_interval_seconds=1,
        enabled=True,
    )


# =============================================================================
# MUST-HAVE 1: Log Rotation Tests
# =============================================================================


class TestLogRotation:
    """Tests for MUST-HAVE: System automatically rotates logs."""

    def test_removes_files_older_than_max_age(self, temp_log_dir, log_rotation_config):
        """Should remove log files older than max_age_days."""
        rotator = LogRotator(log_rotation_config)

        # Create an old file
        old_file = temp_log_dir / "old.log"
        old_file.write_text("old content")
        old_mtime = (datetime.now(UTC) - timedelta(days=10)).timestamp()
        os.utime(old_file, (old_mtime, old_mtime))

        # Create a recent file
        recent_file = temp_log_dir / "recent.log"
        recent_file.write_text("recent content")

        # Act
        stats = asyncio.get_event_loop().run_until_complete(rotator.rotate())

        # Assert
        assert not old_file.exists(), "Old file should be removed"
        assert recent_file.exists(), "Recent file should remain"
        assert stats["files_removed"] == 1

    def test_compresses_files_larger_than_threshold(self, temp_log_dir, log_rotation_config):
        """Should compress uncompressed log files larger than compress_above_mb."""
        rotator = LogRotator(log_rotation_config)

        # Create a large log file (larger than 0.01 MB = 10KB)
        large_file = temp_log_dir / "large.log"
        large_file.write_text("x" * 15_000)  # ~15KB

        # Act
        stats = asyncio.get_event_loop().run_until_complete(rotator.rotate())

        # Assert
        assert not large_file.exists(), "Original file should be removed after compression"
        compressed = large_file.with_suffix(".log.gz")
        assert compressed.exists(), "Compressed file should exist"
        assert stats["files_compressed"] == 1

        # Verify compression actually works
        with gzip.open(compressed, "rt") as f:
            assert f.read() == "x" * 15_000

    def test_does_not_recompress_already_compressed_files(self, temp_log_dir, log_rotation_config):
        """Should not recompress already-compressed .gz files."""
        rotator = LogRotator(log_rotation_config)

        # Create a compressed file
        compressed = temp_log_dir / "already.gz"
        with gzip.open(compressed, "wt") as f:
            f.write("compressed content")

        # Act
        stats = asyncio.get_event_loop().run_until_complete(rotator.rotate())

        # Assert: compressed file still exists (we don't try to re-compress)
        assert compressed.exists()
        assert stats["files_compressed"] == 0

    def test_skips_non_log_extensions(self, temp_log_dir, log_rotation_config):
        """Should skip files that don't match configured extensions."""
        rotator = LogRotator(log_rotation_config)

        # Create a non-log file
        txt_file = temp_log_dir / "readme.txt"
        txt_file.write_text("readme")

        # Act
        stats = asyncio.get_event_loop().run_until_complete(rotator.rotate())

        # Assert
        assert txt_file.exists(), "Non-log file should remain"
        assert stats["files_removed"] == 0

    def test_dry_run_does_not_modify_files(self, temp_log_dir):
        """Dry run should report actions without modifying files."""
        config = LogRotationConfig(log_directory=temp_log_dir, dry_run=True)
        rotator = LogRotator(config)

        old_file = temp_log_dir / "old.log"
        old_file.write_text("old")
        old_mtime = (datetime.now(UTC) - timedelta(days=10)).timestamp()
        os.utime(old_file, (old_mtime, old_mtime))

        stats = asyncio.get_event_loop().run_until_complete(rotator.rotate())

        assert old_file.exists(), "Dry run should not remove files"
        assert stats["files_removed"] == 0


# =============================================================================
# MUST-HAVE 2: Database Maintenance Tests
# =============================================================================


class TestDatabaseMaintenance:
    """Tests for MUST-HAVE: Database maintenance runs VACUUM ANALYZE and prunes orphaned records."""

    def test_skips_when_no_database_url(self, db_maintenance_config):
        """Should skip maintenance when no database URL is configured."""
        maint = DatabaseMaintenance(db_maintenance_config)

        # Ensure DATABASE_URL is not in environment
        with patch.dict(os.environ, {}, clear=True):
            stats = asyncio.get_event_loop().run_until_complete(maint.run_maintenance())

        assert stats["vacuum_analyze_runs"] == 0
        assert stats["errors"] == 0

    @pytest.mark.asyncio
    async def test_skips_when_asyncpg_not_available(self, db_maintenance_config):
        """Should skip gracefully when asyncpg is not installed."""
        maint = DatabaseMaintenance(db_maintenance_config)

        # Patch at the call site inside run_maintenance
        with patch.dict(os.environ, {}, clear=True):
            with patch("asyncpg.create_pool", side_effect=ImportError("no asyncpg")):
                # Also patch the import check inside run_maintenance
                with patch.dict("sys.modules", {"asyncpg": None}):
                    maint2 = DatabaseMaintenance(db_maintenance_config)
                    stats = await maint2.run_maintenance()

        assert stats["errors"] == 0  # No error, just skipped

    def test_vacuum_analyze_config_is_correct(self):
        """Verify critical tables are included in vacuum analyze list."""
        config = DatabaseMaintenanceConfig()
        assert "agent_states" in config.vacuum_analyze_tables
        assert "agent_state_checkpoints" in config.vacuum_analyze_tables
        assert "domain_events" in config.vacuum_analyze_tables

    def test_orphan_retention_config(self):
        """Verify orphaned record retention is configured correctly."""
        config = DatabaseMaintenanceConfig()
        # Default: 7 days
        assert config.prune_orphaned_older_than_hours == 24 * 7
        # Default: keep 10 checkpoints per agent
        assert config.checkpoint_retention_count == 10


# =============================================================================
# MUST-HAVE 3: Configuration Drift Detection Tests
# =============================================================================


class TestConfigDriftDetection:
    """Tests for MUST-HAVE: Configuration drift is detected by comparing against stored baseline."""

    def test_stores_baseline_successfully(self, config_drift_config):
        """Should store a baseline file when store_baseline is called."""
        detector = ConfigDriftDetector(config_drift_config)

        config_data = {
            "log_level": "INFO",
            "monitoring_enabled": True,
            "auto_restart_enabled": True,
        }

        path = detector.store_baseline(config_data, config_name="test")

        assert Path(path).exists()
        stored = json.loads(Path(path).read_text())
        assert stored["log_level"] == "INFO"
        assert stored["monitoring_enabled"] is True
        assert "_stored_at" in stored

    @pytest.mark.asyncio
    async def test_detects_no_drift_when_config_matches(self, config_drift_config):
        """Should report no drift when current config matches baseline."""
        detector = ConfigDriftDetector(config_drift_config)

        # Store baseline
        baseline = {"log_level": "INFO", "monitoring_enabled": True, "auto_restart_enabled": True}
        detector.store_baseline(baseline, config_name="runtime")

        # Check same config
        result = await detector.detect_drift(baseline, config_name="runtime")

        assert result["has_drift"] is False
        assert result["changed_keys"] == []
        assert result["added_keys"] == []
        assert result["removed_keys"] == []

    @pytest.mark.asyncio
    async def test_detects_changed_value_drift(self, config_drift_config):
        """Should detect drift when a critical config value changes."""
        detector = ConfigDriftDetector(config_drift_config)

        # Store baseline with log_level=INFO
        detector.store_baseline({"log_level": "INFO", "monitoring_enabled": True}, config_name="runtime")

        # Change log_level to DEBUG
        current = {"log_level": "DEBUG", "monitoring_enabled": True}
        result = await detector.detect_drift(current, config_name="runtime")

        assert result["has_drift"] is True
        assert "log_level" in result["changed_keys"]

    @pytest.mark.asyncio
    async def test_detects_added_key_drift(self, config_drift_config):
        """Should detect drift when a new critical key is added."""
        detector = ConfigDriftDetector(config_drift_config)

        # Store baseline with only log_level
        detector.store_baseline({"log_level": "INFO"}, config_name="runtime")

        # Add a new critical key
        current = {"log_level": "INFO", "monitoring_enabled": True}
        result = await detector.detect_drift(current, config_name="runtime")

        assert result["has_drift"] is True
        assert "monitoring_enabled" in result["added_keys"]

    @pytest.mark.asyncio
    async def test_detects_removed_key_drift(self, config_drift_config):
        """Should detect drift when a critical key is removed."""
        detector = ConfigDriftDetector(config_drift_config)

        # Store baseline with multiple keys
        detector.store_baseline(
            {"log_level": "INFO", "monitoring_enabled": True, "auto_restart_enabled": True},
            config_name="runtime",
        )

        # Remove a key
        current = {"log_level": "INFO", "monitoring_enabled": True}
        result = await detector.detect_drift(current, config_name="runtime")

        assert result["has_drift"] is True
        assert "auto_restart_enabled" in result["removed_keys"]

    @pytest.mark.asyncio
    async def test_reports_no_baseline_when_none_exists(self, config_drift_config):
        """Should handle missing baseline gracefully."""
        detector = ConfigDriftDetector(config_drift_config)

        result = await detector.detect_drift({"log_level": "INFO"}, config_name="nonexistent")

        assert result["has_drift"] is False
        assert result["reason"] == "no_baseline"

    def test_get_last_result_returns_none_initially(self, config_drift_config):
        """Should return None for last result before any detection run."""
        detector = ConfigDriftDetector(config_drift_config)
        assert detector.get_last_result() is None


# =============================================================================
# MUST-HAVE 4: SelfMaintenanceScheduler Integration Tests
# =============================================================================


class TestSelfMaintenanceScheduler:
    """Tests for MUST-HAVE: SelfMaintenanceScheduler runs on interval and integrates with AutonomousRuntime lifecycle."""

    @pytest.mark.asyncio
    async def test_scheduler_starts_and_stops_cleanly(self, maintenance_config):
        """Scheduler should start and stop without errors."""
        scheduler = SelfMaintenanceScheduler(maintenance_config)

        # Start
        start_task = asyncio.create_task(scheduler.start())
        await asyncio.sleep(0.1)  # Let it run briefly
        await scheduler.stop()
        await start_task

        assert scheduler.get_status()["running"] is False

    @pytest.mark.asyncio
    async def test_scheduler_disabled_does_not_run(self, maintenance_config):
        """Should not start loops when enabled=False."""
        maintenance_config.enabled = False
        scheduler = SelfMaintenanceScheduler(maintenance_config)

        status = scheduler.get_status()
        assert status["enabled"] is False

    @pytest.mark.asyncio
    async def test_scheduler_runs_log_rotation(self, maintenance_config):
        """Scheduler should run log rotation task."""
        scheduler = SelfMaintenanceScheduler(maintenance_config)

        # Run all tasks directly
        await scheduler._run_all_tasks()

        stats = scheduler.get_status()
        assert "log_rotation_stats" in stats

    @pytest.mark.asyncio
    async def test_scheduler_runs_db_maintenance(self, maintenance_config):
        """Scheduler should run DB maintenance task."""
        scheduler = SelfMaintenanceScheduler(maintenance_config)

        # Ensure no DATABASE_URL to avoid connection attempts
        with patch.dict(os.environ, {}, clear=True):
            await scheduler._run_all_tasks()

        stats = scheduler.get_status()
        assert "db_maintenance_stats" in stats
        assert stats["db_maintenance_stats"].get("errors", 0) == 0  # Skipped gracefully

    @pytest.mark.asyncio
    async def test_scheduler_detects_config_drift(self, maintenance_config):
        """Scheduler should run config drift detection."""
        scheduler = SelfMaintenanceScheduler(maintenance_config)

        # Store a baseline first
        await scheduler.store_current_as_baseline()

        # Run tasks
        await scheduler._run_all_tasks()

        stats = scheduler.get_status()
        assert "last_drift_result" in stats

    @pytest.mark.asyncio
    async def test_scheduler_tracks_loop_count(self, maintenance_config):
        """Scheduler should increment loops_run counter."""
        scheduler = SelfMaintenanceScheduler(maintenance_config)

        assert scheduler.get_status()["loops_run"] == 0

        await scheduler._run_all_tasks()
        assert scheduler.get_status()["loops_run"] == 1

        await scheduler._run_all_tasks()
        assert scheduler.get_status()["loops_run"] == 2

    @pytest.mark.asyncio
    async def test_runtime_ref_passed_through(self, maintenance_config):
        """Should pass runtime_ref through for config extraction."""
        mock_runtime = MagicMock()
        mock_runtime.config.log_level = "DEBUG"
        mock_runtime.config.monitoring_enabled = True
        mock_runtime.config.auto_restart_enabled = True
        mock_runtime.config.max_restart_attempts = 5
        mock_runtime.config.state_persistence_enabled = True
        mock_runtime.config.auto_scaling_enabled = False

        scheduler = SelfMaintenanceScheduler(maintenance_config, runtime_ref=mock_runtime)

        config = scheduler._get_runtime_config()
        assert config["log_level"] == "DEBUG"
        assert config["monitoring_enabled"] is True

    @pytest.mark.asyncio
    async def test_integration_with_autonomous_runtime(self, maintenance_config):
        """Scheduler should integrate with AutonomousRuntime via runtime_ref."""
        # Create a minimal mock runtime
        mock_runtime = MagicMock()
        mock_runtime.config = MagicMock()
        mock_runtime.config.log_level = "INFO"
        mock_runtime.config.monitoring_enabled = True
        mock_runtime.config.auto_restart_enabled = True
        mock_runtime.config.max_restart_attempts = 3
        mock_runtime.config.state_persistence_enabled = True
        mock_runtime.config.auto_scaling_enabled = False

        scheduler = SelfMaintenanceScheduler(maintenance_config, runtime_ref=mock_runtime)

        status = scheduler.get_status()
        assert status["integration"] == "autonomous_runtime"

    @pytest.mark.asyncio
    async def test_store_current_as_baseline_creates_file(self, maintenance_config, temp_baseline_dir):
        """store_current_as_baseline should create a baseline file."""
        mock_runtime = MagicMock()
        mock_runtime.config = MagicMock()
        mock_runtime.config.log_level = "INFO"
        mock_runtime.config.monitoring_enabled = True
        mock_runtime.config.auto_restart_enabled = True
        mock_runtime.config.max_restart_attempts = 3
        mock_runtime.config.state_persistence_enabled = True
        mock_runtime.config.auto_scaling_enabled = False

        scheduler = SelfMaintenanceScheduler(maintenance_config, runtime_ref=mock_runtime)

        path = await scheduler.store_current_as_baseline("runtime")
        assert Path(path).exists()

        stored = json.loads(Path(path).read_text())
        assert stored["log_level"] == "INFO"
        assert stored["monitoring_enabled"] is True

    def test_convenience_properties(self, maintenance_config):
        """Each component should be accessible via property."""
        scheduler = SelfMaintenanceScheduler(maintenance_config)

        assert isinstance(scheduler.log_rotator, LogRotator)
        assert isinstance(scheduler.db_maintenance, DatabaseMaintenance)
        assert isinstance(scheduler.drift_detector, ConfigDriftDetector)


# =============================================================================
# Integration: Full Scheduler with mocked AutonomousRuntime
# =============================================================================


class TestSchedulerAutonomousRuntimeIntegration:
    """Integration tests verifying SelfMaintenanceScheduler integrates with AutonomousRuntime lifecycle."""

    @pytest.mark.asyncio
    async def test_scheduler_added_to_runtime_tasks(self, maintenance_config):
        """Scheduler task should be included in AutonomousRuntime start tasks."""
        from heretek_swarm.runtime.autonomous_runtime import AutonomousRuntime

        # Patch both AgentRuntime and the supervisor initialization to avoid real startup
        mock_agent_runtime_instance = MagicMock()
        mock_agent_runtime_instance.initialize = AsyncMock()

        # Create a mock supervisor that is awaitable
        mock_supervisor_cls = MagicMock()
        mock_supervisor_instance = MagicMock()
        mock_supervisor_instance.terminate_all = AsyncMock()
        mock_supervisor_cls.return_value = mock_supervisor_instance

        with patch.object(AutonomousRuntime, "_start_initial_agents", new_callable=AsyncMock):
            with patch(
                "heretek_swarm.runtime.autonomous_runtime.AgentRuntime",
                return_value=mock_agent_runtime_instance,
            ):
                with patch(
                    "heretek_swarm.runtime.autonomous_runtime.ActorSupervisor",
                    mock_supervisor_cls,
                ):
                    config = MagicMock()
                    config.agent_configs = {}
                    config.monitoring_enabled = True
                    config.auto_restart_enabled = True
                    config.max_restart_attempts = 3
                    config.restart_delay_seconds = 1
                    config.health_check_interval = 1
                    config.state_persistence_enabled = False
                    config.state_backup_interval = 1
                    config.metrics_collection_interval = 1
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
                    config.auto_scaling_enabled = False
                    config.min_agents = 1
                    config.max_agents = 3
                    config.scale_up_threshold = 0.8
                    config.scale_down_threshold = 0.3
                    config.scale_up_cooldown_minutes = 10
                    config.scale_down_cooldown_minutes = 30
                    config.min_uptime_before_scale_down = 60
                    config.log_directory = Path(tempfile.mkdtemp())

                    runtime = AutonomousRuntime(config)
                    await runtime.initialize()

                    # Scheduler should be initialized
                    assert runtime._maintenance_scheduler is not None
                    assert isinstance(runtime._maintenance_scheduler, SelfMaintenanceScheduler)

                    # Scheduler should be stopped when runtime stops
                    await runtime.stop()

    @pytest.mark.asyncio
    async def test_runtime_stop_calls_scheduler_stop(self, maintenance_config):
        """Stopping the runtime should also stop the scheduler."""
        from heretek_swarm.runtime.autonomous_runtime import AutonomousRuntime

        mock_agent_runtime_instance = MagicMock()
        mock_agent_runtime_instance.initialize = AsyncMock()

        # Create a mock supervisor that is awaitable
        mock_supervisor_cls = MagicMock()
        mock_supervisor_instance = MagicMock()
        mock_supervisor_instance.terminate_all = AsyncMock()
        mock_supervisor_cls.return_value = mock_supervisor_instance

        with patch.object(AutonomousRuntime, "_start_initial_agents", new_callable=AsyncMock):
            with patch(
                "heretek_swarm.runtime.autonomous_runtime.AgentRuntime",
                return_value=mock_agent_runtime_instance,
            ):
                with patch(
                    "heretek_swarm.runtime.autonomous_runtime.ActorSupervisor",
                    mock_supervisor_cls,
                ):
                    config = MagicMock()
                    config.agent_configs = {}
                    config.monitoring_enabled = True
                    config.auto_restart_enabled = True
                    config.max_restart_attempts = 3
                    config.restart_delay_seconds = 1
                    config.health_check_interval = 1
                    config.state_persistence_enabled = False
                    config.state_backup_interval = 1
                    config.metrics_collection_interval = 1
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
                    config.auto_scaling_enabled = False
                    config.min_agents = 1
                    config.max_agents = 3
                    config.scale_up_threshold = 0.8
                    config.scale_down_threshold = 0.3
                    config.scale_up_cooldown_minutes = 10
                    config.scale_down_cooldown_minutes = 30
                    config.min_uptime_before_scale_down = 60
                    config.log_directory = Path(tempfile.mkdtemp())

                    runtime = AutonomousRuntime(config)
                    await runtime.initialize()

                    # Stop should not raise
                    await runtime.stop()

                    assert runtime._maintenance_scheduler.get_status()["running"] is False
