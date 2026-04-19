"""
Tests for Docker/Podman Provisioner.

Tests the provisioner module functionality including:
- Container runtime detection
- Container configuration
- Connection string generation
- Service provisioning (mocked)
- Health check waiting (mocked)
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from heretek_swarm.config.models import InfrastructureService
from heretek_swarm.infrastructure.provisioner import (
    DEFAULT_IMAGES,
    DEFAULT_PORTS,
    ConnectionStringResult,
    ContainerConfig,
    ContainerRuntime,
    detect_runtime,
    generate_connection_string,
    generate_nats_connection_string,
    generate_postgres_connection_string,
    generate_qdrant_connection_string,
    generate_redis_connection_string,
    pull_image,
    start_container,
    stop_container,
)


class TestDetectRuntime:
    """Tests for detect_runtime function."""

    def test_detects_podman_when_available(self):
        """Should return podman when podman is in PATH."""
        with patch("shutil.which") as mock_which:
            mock_which.return_value = "/usr/bin/podman"

            runtime = detect_runtime()

            assert runtime == ContainerRuntime.PODMAN
            mock_which.assert_called_once_with("podman")

    def test_falls_back_to_docker(self):
        """Should return docker when podman not found but docker is."""
        with patch("shutil.which") as mock_which:
            def which_side_effect(cmd):
                if cmd == "podman":
                    return None
                if cmd == "docker":
                    return "/usr/bin/docker"
                return None

            mock_which.side_effect = which_side_effect

            runtime = detect_runtime()

            assert runtime == ContainerRuntime.DOCKER

    def test_raises_error_when_no_runtime(self):
        """Should raise RuntimeError when neither podman nor docker available."""
        with patch("shutil.which") as mock_which:
            mock_which.return_value = None

            with pytest.raises(RuntimeError) as exc_info:
                detect_runtime()

            assert "Neither podman nor docker is available" in str(exc_info.value)


class TestConnectionStringGeneration:
    """Tests for connection string generation functions."""

    def test_generate_postgres_connection_string(self):
        """Should generate valid PostgreSQL connection string."""
        result = generate_postgres_connection_string(
            host="localhost",
            port=5432,
            password="secret123",
            user="postgres",
            database="mydb",
        )

        assert result == "postgresql://postgres:secret123@localhost:5432/mydb"

    def test_generate_postgres_connection_string_default_params(self):
        """Should use defaults when optional params not provided."""
        result = generate_postgres_connection_string(
            host="localhost",
            port=5432,
            password="secret",
        )

        assert result == "postgresql://postgres:secret@localhost:5432/postgres"

    def test_generate_redis_connection_string_no_password(self):
        """Should generate Redis connection string without password."""
        result = generate_redis_connection_string(
            host="localhost",
            port=6379,
        )

        assert result == "redis://localhost:6379"

    def test_generate_redis_connection_string_with_password(self):
        """Should generate Redis connection string with password."""
        result = generate_redis_connection_string(
            host="localhost",
            port=6379,
            password="secret456",
        )

        assert result == "redis://:secret456@localhost:6379"

    def test_generate_qdrant_connection_string(self):
        """Should generate Qdrant connection string."""
        result = generate_qdrant_connection_string(
            host="localhost",
            port=6333,
        )

        assert result == "http://localhost:6333"

    def test_generate_nats_connection_string(self):
        """Should generate NATS connection string."""
        result = generate_nats_connection_string(
            host="localhost",
            port=4222,
        )

        assert result == "nats://localhost:4222"

    def test_generate_connection_string_dispatches_correctly(self):
        """Should dispatch to correct generator based on service type."""
        postgres_result = generate_connection_string(
            InfrastructureService.POSTGRES, "localhost", 5432, "pass", "user", "db"
        )
        assert postgres_result is not None
        assert "postgresql://" in postgres_result

        redis_result = generate_connection_string(
            InfrastructureService.REDIS, "localhost", 6379, "pass"
        )
        assert redis_result is not None
        assert "redis://" in redis_result

        qdrant_result = generate_connection_string(
            InfrastructureService.QDRANT, "localhost", 6333
        )
        assert qdrant_result is not None
        assert "http://" in qdrant_result

        nats_result = generate_connection_string(
            InfrastructureService.NATS, "localhost", 4222
        )
        assert nats_result is not None
        assert "nats://" in nats_result

    def test_generate_connection_string_unsupported_service(self):
        """Should return None for unsupported services."""
        result = generate_connection_string(
            InfrastructureService.MEM0, "localhost", 8000
        )

        assert result is None


class TestContainerConfig:
    """Tests for ContainerConfig dataclass."""

    def test_default_container_name(self):
        """Should generate heretek-{service} container name by default."""
        config = ContainerConfig(
            service=InfrastructureService.POSTGRES,
            image="postgres:16",
        )

        assert config.container_name == "heretek-postgres"

    def test_custom_container_name(self):
        """Should use custom container name when provided."""
        config = ContainerConfig(
            service=InfrastructureService.REDIS,
            image="redis:7",
            container_name="my-redis",
        )

        assert config.container_name == "my-redis"

    def test_default_ports_empty(self):
        """Should have empty ports dict by default."""
        config = ContainerConfig(
            service=InfrastructureService.QDRANT,
            image="qdrant:v1",
        )

        assert config.ports == {}

    def test_env_vars_default_empty(self):
        """Should have empty env vars dict by default."""
        config = ContainerConfig(
            service=InfrastructureService.NATS,
            image="nats:2",
        )

        assert config.env_vars == {}


class TestPullImage:
    """Tests for pull_image function."""

    def test_successful_pull(self):
        """Should return True on successful image pull."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stderr="", stdout="")

            result = pull_image(ContainerRuntime.PODMAN, "postgres:16")

            assert result is True
            mock_run.assert_called_once()
            call_args = mock_run.call_args[0][0]
            assert "podman" in call_args
            assert "pull" in call_args
            assert "postgres:16" in call_args

    def test_failed_pull(self):
        """Should return False on failed image pull."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=1,
                stderr="Error: not found",
                stdout="",
            )

            result = pull_image(ContainerRuntime.DOCKER, "nonexistent:image")

            assert result is False

    def test_pull_timeout(self):
        """Should return False on timeout."""
        import subprocess

        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = subprocess.TimeoutExpired("cmd", 300)

            result = pull_image(ContainerRuntime.PODMAN, "big:image")

            assert result is False


class TestStopContainer:
    """Tests for stop_container function."""

    def test_stops_container_successfully(self):
        """Should call stop command."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)

            stop_container(ContainerRuntime.PODMAN, "heretek-postgres")

            mock_run.assert_called_once()
            call_args = mock_run.call_args[0][0]
            assert "podman" in call_args
            assert "stop" in call_args
            assert "heretek-postgres" in call_args

    def test_ignores_errors_idempotent(self):
        """Should not raise on errors (idempotent operation)."""
        with patch("subprocess.run") as mock_run:
            # Simulate container not found
            mock_run.return_value = MagicMock(returncode=1, stderr="no such container")

            # Should not raise
            stop_container(ContainerRuntime.DOCKER, "nonexistent-container")

            mock_run.assert_called_once()

    def test_force_kill_on_timeout(self):
        """Should attempt force kill if stop times out."""
        import subprocess

        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = [
                subprocess.TimeoutExpired("stop", 30),
                MagicMock(returncode=0),  # kill succeeds
            ]

            stop_container(ContainerRuntime.PODMAN, "stuck-container")

            # Should have called both stop and kill
            assert mock_run.call_count == 2


class TestStartContainer:
    """Tests for start_container function."""

    def test_starts_container_successfully(self):
        """Should start container with correct parameters."""
        config = ContainerConfig(
            service=InfrastructureService.POSTGRES,
            image="postgres:16",
            ports={"5432": "5432"},
            env_vars={"POSTGRES_PASSWORD": "secret"},
            container_name="heretek-postgres",
        )

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout="abc123def456",
                stderr="",
            )

            result = start_container(ContainerRuntime.DOCKER, config)

            assert result is True
            mock_run.assert_called_once()
            call_args = mock_run.call_args[0][0]

            # Verify command structure
            assert "docker" in call_args
            assert "run" in call_args
            assert "--detach" in call_args
            assert "--name" in call_args
            assert "heretek-postgres" in call_args
            assert "--rm" in call_args
            assert "--publish" in call_args
            assert "5432:5432" in call_args
            assert "--env" in call_args
            assert "POSTGRES_PASSWORD=secret" in call_args
            assert "postgres:16" in call_args

    def test_fails_on_nonzero_returncode(self):
        """Should return False when container start fails."""
        config = ContainerConfig(
            service=InfrastructureService.REDIS,
            image="redis:7",
            container_name="heretek-redis",
        )

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=1,
                stdout="",
                stderr="Error: port already in use",
            )

            result = start_container(ContainerRuntime.PODMAN, config)

            assert result is False


class TestDefaultImagesAndPorts:
    """Tests for default images and ports configuration."""

    def test_default_images_defined(self):
        """Should have default images for all services except mem0."""
        assert InfrastructureService.POSTGRES in DEFAULT_IMAGES
        assert InfrastructureService.REDIS in DEFAULT_IMAGES
        assert InfrastructureService.QDRANT in DEFAULT_IMAGES
        assert InfrastructureService.NATS in DEFAULT_IMAGES
        # mem0 excluded
        assert InfrastructureService.MEM0 not in DEFAULT_IMAGES

    def test_default_ports_defined(self):
        """Should have default ports for all services."""
        assert DEFAULT_PORTS[InfrastructureService.POSTGRES] == 5432
        assert DEFAULT_PORTS[InfrastructureService.REDIS] == 6379
        assert DEFAULT_PORTS[InfrastructureService.QDRANT] == 6333
        assert DEFAULT_PORTS[InfrastructureService.NATS] == 4222


class TestConnectionStringResult:
    """Tests for ConnectionStringResult dataclass."""

    def test_successful_result(self):
        """Should create successful result."""
        result = ConnectionStringResult(
            service=InfrastructureService.POSTGRES,
            success=True,
            connection_string="postgresql://...",
            host="localhost",
            port=5432,
        )

        assert result.success is True
        assert result.connection_string == "postgresql://..."
        assert result.error is None

    def test_failed_result(self):
        """Should create failed result with error."""
        result = ConnectionStringResult(
            service=InfrastructureService.REDIS,
            success=False,
            error="Connection refused",
        )

        assert result.success is False
        assert result.error == "Connection refused"
        assert result.connection_string is None


# Import fixtures from conftest if available
pytest_plugins = ["pytest_asyncio"]
