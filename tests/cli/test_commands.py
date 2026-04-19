"""
Tests for CLI commands.

Verifies the functional CLI commands for status, deploy, and update.
"""

from __future__ import annotations

import asyncio
import json
import subprocess
import sys
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from click.testing import CliRunner

from heretek_swarm.config.models import HealthStatus, InfrastructureService


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def cli():
    """Create the CLI group for testing."""
    from src.cli import cli as cli_group
    return cli_group


@pytest.fixture
def mock_api_response() -> dict[str, Any]:
    """Mock API response for infrastructure configuration."""
    return {
        "infrastructure": [
            {
                "id": "550e8400-e29b-41d4-a716-446655440001",
                "service": "postgres",
                "host": "localhost",
                "port": 5432,
                "is_enabled": True,
                "health_status": "unknown",
            },
            {
                "id": "550e8400-e29b-41d4-a716-446655440002",
                "service": "redis",
                "host": "localhost",
                "port": 6379,
                "is_enabled": True,
                "health_status": "unknown",
            },
            {
                "id": "550e8400-e29b-41d4-a716-446655440003",
                "service": "qdrant",
                "host": "localhost",
                "port": 6333,
                "is_enabled": True,
                "health_status": "unknown",
            },
            {
                "id": "550e8400-e29b-41d4-a716-446655440004",
                "service": "nats",
                "host": "localhost",
                "port": 4222,
                "is_enabled": True,
                "health_status": "unknown",
            },
            {
                "id": "550e8400-e29b-41d4-a716-446655440005",
                "service": "mem0",
                "host": "localhost",
                "port": 8000,
                "is_enabled": True,
                "health_status": "unknown",
            },
        ],
        "total": 5,
    }


@pytest.fixture
def mock_wizard_config() -> dict[str, Any]:
    """Mock wizard configuration response."""
    return {
        "wizard_completed": True,
        "database_configured": {
            "providers": [
                {"id": "1", "name": "OpenAI", "type": "openai", "is_enabled": True},
            ],
            "total_providers": 1,
        },
        "infrastructure": [
            {"service": "postgres", "host": "localhost", "port": 5432},
            {"service": "redis", "host": "localhost", "port": 6379},
        ],
        "needs_setup": {
            "providers": False,
            "agents": False,
            "api_keys": False,
            "infrastructure": False,
        },
    }


# =============================================================================
# Health Check Tests
# =============================================================================

class TestHealthCheckFunctions:
    """Tests for health check utility functions."""

    def test_check_service_health_postgres_returns_structure(self):
        """Test PostgreSQL health check returns expected structure."""
        from src.cli import _check_service_health

        async def run():
            result = await _check_service_health(
                service=InfrastructureService.POSTGRES,
                host="localhost",
                port=5432,
                timeout=1.0,
            )
            # Should have required keys regardless of connection result
            assert "service" in result
            assert "status" in result
            assert "latency_ms" in result
            assert result["service"] == "postgres"
            # Status should be a valid enum value
            assert result["status"] in ["healthy", "unhealthy", "unknown"]

        asyncio.run(run())

    def test_check_service_health_redis_returns_structure(self):
        """Test Redis health check returns properly structured response."""
        from src.cli import _check_service_health

        async def run():
            result = await _check_service_health(
                service=InfrastructureService.REDIS,
                host="localhost",
                port=6379,
                timeout=1.0,
            )
            assert result["service"] == "redis"
            assert result["status"] in ["healthy", "unhealthy", "unknown"]
            assert isinstance(result["latency_ms"], float)
            assert result["latency_ms"] >= 0

        asyncio.run(run())

    def test_check_service_health_qdrant_returns_structure(self):
        """Test Qdrant health check returns properly structured response."""
        from src.cli import _check_service_health

        async def run():
            result = await _check_service_health(
                service=InfrastructureService.QDRANT,
                host="localhost",
                port=6333,
                timeout=1.0,
            )
            assert result["service"] == "qdrant"
            assert result["status"] in ["healthy", "unhealthy", "unknown"]

        asyncio.run(run())

    def test_check_service_health_nats_returns_structure(self):
        """Test NATS health check returns properly structured response."""
        from src.cli import _check_service_health

        async def run():
            result = await _check_service_health(
                service=InfrastructureService.NATS,
                host="localhost",
                port=4222,
                timeout=1.0,
            )
            assert result["service"] == "nats"
            assert result["status"] in ["healthy", "unhealthy", "unknown"]

        asyncio.run(run())

    def test_check_service_health_mem0_returns_structure(self):
        """Test Mem0 health check returns properly structured response."""
        from src.cli import _check_service_health

        async def run():
            result = await _check_service_health(
                service=InfrastructureService.MEM0,
                host="localhost",
                port=8000,
                timeout=1.0,
            )
            assert result["service"] == "mem0"
            assert result["status"] in ["healthy", "unhealthy", "unknown"]

        asyncio.run(run())


# =============================================================================
# Container Runtime Detection Tests
# =============================================================================

class TestContainerRuntimeDetection:
    """Tests for Docker/Podman detection."""

    def test_check_container_runtime_returns_tuple(self):
        """Test that container runtime detection returns (name, version) or (None, error)."""
        from src.cli import check_container_runtime

        runtime, version = check_container_runtime()

        # Should return a tuple
        assert isinstance(runtime, (str, type(None)))
        assert isinstance(version, str)

        # If runtime is found, should have version info
        if runtime:
            assert len(version) > 0

    @patch("subprocess.run")
    def test_check_compose_plugin_docker(self, mock_run):
        """Test Docker Compose plugin detection."""
        from src.cli import check_compose_plugin

        mock_run.return_value = MagicMock(returncode=0, stdout="Docker Compose version v2.20.0")

        result = check_compose_plugin("docker")

        assert result is True
        mock_run.assert_called_once()

    @patch("subprocess.run")
    def test_check_compose_plugin_podman(self, mock_run):
        """Test Podman Compose plugin detection."""
        from src.cli import check_compose_plugin

        mock_run.return_value = MagicMock(returncode=0, stdout="podman compose version 4.6.0")

        result = check_compose_plugin("podman")

        assert result is True

    @patch("subprocess.run")
    def test_check_compose_plugin_not_found(self, mock_run):
        """Test when compose plugin is not available."""
        from src.cli import check_compose_plugin

        mock_run.side_effect = subprocess.SubprocessError()

        result = check_compose_plugin("docker")

        assert result is False


# =============================================================================
# Status Command Tests
# =============================================================================

class TestStatusCommand:
    """Tests for the heretek-swarm status command."""

    def test_status_command_requires_api(self, cli):
        """Test that status command fails gracefully when API is unavailable."""
        runner = CliRunner()
        with patch("httpx.get") as mock_get:
            import httpx
            mock_get.side_effect = httpx.ConnectError("Connection refused")

            result = runner.invoke(
                cli,
                ["status"],
                catch_exceptions=False,
            )

            # Should fail with connection error
            assert result.exit_code == 1
            assert "Cannot connect to API" in result.output or "Connection refused" in result.output

    def test_status_command_parses_api_response(self, cli, mock_api_response):
        """Test that status command parses API response correctly."""
        runner = CliRunner()
        with patch("httpx.get") as mock_get:
            mock_response = MagicMock()
            mock_response.json.return_value = mock_api_response
            mock_response.raise_for_status = MagicMock()
            mock_get.return_value = mock_response

            # Mock the health check to return known values
            async def mock_health_check(service, host, port, timeout):
                return {
                    "service": service.value,
                    "status": "unhealthy",  # Simulate unreachable services
                    "latency_ms": 0.0,
                    "error": "Connection refused",
                }

            # Mock asyncio.gather to return results directly
            async def mock_gather(*tasks, return_exceptions=False):
                results = []
                for task in tasks:
                    if asyncio.iscoroutine(task):
                        results.append(await task)
                    else:
                        results.append(task)
                return results

            with patch("src.cli.asyncio.gather", side_effect=mock_gather):
                with patch("src.cli._check_service_health", side_effect=mock_health_check):
                    result = runner.invoke(
                        cli,
                        ["status"],
                    )

            # Should parse infrastructure and display services
            assert "Heretek Swarm Status" in result.output

    def test_status_command_shows_summary(self, cli, mock_api_response):
        """Test that status command shows summary of health checks."""
        runner = CliRunner()
        with patch("httpx.get") as mock_get:
            mock_response = MagicMock()
            mock_response.json.return_value = mock_api_response
            mock_response.raise_for_status = MagicMock()
            mock_get.return_value = mock_response

            # Mock health check to return simple synchronous result
            async def mock_health_check(service, host, port, timeout):
                return {
                    "service": service.value,
                    "status": "healthy",
                    "latency_ms": 1.0,
                    "error": None,
                }

            # Mock asyncio.gather to return results directly
            async def mock_gather(*tasks, return_exceptions=False):
                results = []
                for task in tasks:
                    if asyncio.iscoroutine(task):
                        results.append(await task)
                    else:
                        results.append(task)
                return results

            with patch("src.cli.asyncio.gather", side_effect=mock_gather):
                result = runner.invoke(
                    cli,
                    ["status"],
                )

            # Should show status header or exit cleanly
            assert "Status" in result.output or result.exit_code == 0


# =============================================================================
# Deploy Command Tests
# =============================================================================

class TestDeployCommand:
    """Tests for the heretek-swarm deploy command."""

    def test_deploy_command_fetches_wizard_config(self, cli, mock_wizard_config):
        """Test that deploy command fetches wizard configuration from API."""
        runner = CliRunner()
        with patch("httpx.get") as mock_get:
            mock_response = MagicMock()
            mock_response.json.return_value = mock_wizard_config
            mock_response.raise_for_status = MagicMock()
            mock_get.return_value = mock_response

            with patch("src.cli.check_container_runtime") as mock_runtime:
                mock_runtime.return_value = (None, "Docker not found")

                result = runner.invoke(
                    cli,
                    ["deploy"],
                )

            # Should show wizard configuration info
            assert "Deployment" in result.output
            assert mock_get.called

    def test_deploy_command_detects_docker(self, cli, mock_wizard_config):
        """Test that deploy command detects Docker availability."""
        runner = CliRunner()
        with patch("httpx.get") as mock_get:
            mock_response = MagicMock()
            mock_response.json.return_value = mock_wizard_config
            mock_response.raise_for_status = MagicMock()
            mock_get.return_value = mock_response

            with patch("src.cli.check_container_runtime") as mock_runtime:
                mock_runtime.return_value = ("docker", "Docker version 24.0.0")

                with patch("src.cli.check_compose_plugin") as mock_compose:
                    mock_compose.return_value = True

                    result = runner.invoke(
                        cli,
                        ["deploy"],
                    )

            # Should show Docker detection
            assert "docker" in result.output.lower() or result.exit_code == 0

    def test_deploy_command_shows_instructions(self, cli, mock_wizard_config):
        """Test that deploy command shows deployment instructions."""
        runner = CliRunner()
        with patch("httpx.get") as mock_get:
            mock_response = MagicMock()
            mock_response.json.return_value = mock_wizard_config
            mock_response.raise_for_status = MagicMock()
            mock_get.return_value = mock_response

            with patch("src.cli.check_container_runtime") as mock_runtime:
                mock_runtime.return_value = ("docker", "Docker version 24.0.0")

                with patch("src.cli.check_compose_plugin") as mock_compose:
                    mock_compose.return_value = True

                    result = runner.invoke(
                        cli,
                        ["deploy", "--production", "--scale", "3"],
                    )

            # Should show deployment instructions
            assert "Deployment instructions" in result.output or "compose" in result.output.lower()

    def test_deploy_command_handles_no_runtime(self, cli, mock_wizard_config):
        """Test deploy command handles missing container runtime gracefully."""
        runner = CliRunner()
        with patch("httpx.get") as mock_get:
            mock_response = MagicMock()
            mock_response.json.return_value = mock_wizard_config
            mock_response.raise_for_status = MagicMock()
            mock_get.return_value = mock_response

            with patch("src.cli.check_container_runtime") as mock_runtime:
                mock_runtime.return_value = (None, "Docker not found")

                result = runner.invoke(
                    cli,
                    ["deploy"],
                )

            # Should show instructions to install Docker
            assert "Docker" in result.output or "container runtime" in result.output.lower()


# =============================================================================
# Update Command Tests
# =============================================================================

class TestUpdateCommand:
    """Tests for the heretek-swarm update command."""

    def test_update_command_shows_latest_version(self, cli):
        """Test that update command shows pip install instructions."""
        runner = CliRunner()
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout="Available versions: 0.1.0, 0.2.0, 0.3.0",
            )

            result = runner.invoke(
                cli,
                ["update"],
            )

            # Should show pip install instruction
            assert "pip install --upgrade" in result.output
            assert "Update" in result.output

    def test_update_command_specific_version(self, cli):
        """Test that update command with specific version shows correct instruction."""
        runner = CliRunner()
        result = runner.invoke(
            cli,
            ["update", "--version", "0.2.0"],
        )

        # Should show specific version instruction
        assert "0.2.0" in result.output
        assert "pip install --upgrade heretek-swarm==0.2.0" in result.output

    def test_update_command_verification_instruction(self, cli):
        """Test that update command shows verification step."""
        runner = CliRunner()
        result = runner.invoke(
            cli,
            ["update"],
        )

        # Should show how to verify
        assert "--version" in result.output or "verify" in result.output.lower()


# =============================================================================
# CLI Group Tests
# =============================================================================

class TestCLIGroup:
    """Tests for the CLI group itself."""

    def test_cli_version(self, cli):
        """Test that CLI shows version."""
        runner = CliRunner()
        result = runner.invoke(
            cli,
            ["--version"],
        )

        assert result.exit_code == 0
        assert "version" in result.output.lower() or "0.1" in result.output

    def test_cli_help(self, cli):
        """Test that CLI shows help."""
        runner = CliRunner()
        result = runner.invoke(
            cli,
            ["--help"],
        )

        assert result.exit_code == 0
        assert "Heretek Swarm" in result.output
        assert "deploy" in result.output
        assert "status" in result.output
        assert "update" in result.output

    def test_cli_all_commands_listed(self, cli):
        """Test that all expected commands are available."""
        runner = CliRunner()
        result = runner.invoke(
            cli,
            ["--help"],
        )

        expected_commands = ["deploy", "status", "update"]
        for cmd in expected_commands:
            assert cmd in result.output


# =============================================================================
# Integration Tests (Require Running API)
# =============================================================================

@pytest.mark.integration
class TestCLIIntegration:
    """Integration tests that require a running API server."""

    def test_status_with_live_api(self, cli):
        """Test status command with a live API server."""
        # Skip if no API is running
        import socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = sock.connect_ex(("localhost", 8000))
        sock.close()

        if result != 0:
            pytest.skip("API server not running")

        runner = CliRunner()
        result = runner.invoke(
            cli,
            ["status", "--api-base", "http://localhost:8000"],
        )

        # Should get a response (pass or fail depending on services)
        assert result.exit_code in [0, 1]
        assert "Status" in result.output or "healthy" in result.output.lower()
