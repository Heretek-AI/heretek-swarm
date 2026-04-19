"""
Tests for Provisioner API Endpoints.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from heretek_swarm.infrastructure.provisioner import (
    ConnectionStringResult,
    ContainerRuntime,
    InfrastructureService as InfraService,
)


@pytest.fixture
def provisioner_app():
    """Create FastAPI app with provisioner router for testing."""
    from heretek_swarm.api.provisioner import router
    from fastapi import FastAPI

    app = FastAPI()
    app.include_router(router)
    return app


@pytest.fixture
def mock_nats_publisher():
    """Create a mock async NATS publisher."""
    mock_publisher = MagicMock()
    mock_publisher.publish_event = AsyncMock(return_value=True)
    return mock_publisher


@pytest.fixture
def mock_config_service():
    """Create a mock configuration service."""
    mock_svc = MagicMock()
    mock_svc.get_infrastructure_config_by_service = AsyncMock(return_value=None)
    mock_svc.create_infrastructure_config = AsyncMock()
    mock_svc.update_infrastructure_config = AsyncMock()
    mock_svc.list_infrastructure_configs = AsyncMock(return_value=[])
    return mock_svc


class TestProvisionServices:
    """Tests for POST /api/wizard/provision."""

    def test_provision_requires_services(self, provisioner_app):
        """Test that at least one service must be specified."""
        client = TestClient(provisioner_app)

        response = client.post(
            "/api/wizard/provision",
            json={"services": [], "runtime": "auto"},
        )

        assert response.status_code == 400
        assert "at least one service" in response.json()["detail"].lower()

    def test_provision_rejects_invalid_service(self, provisioner_app):
        """Test that invalid service names are rejected."""
        client = TestClient(provisioner_app)

        response = client.post(
            "/api/wizard/provision",
            json={"services": ["invalid_service"], "runtime": "auto"},
        )

        assert response.status_code == 400
        assert "unknown service" in response.json()["detail"].lower()

    def test_provision_handles_runtime_error(
        self, provisioner_app, mock_nats_publisher, mock_config_service
    ):
        """Test handling when no container runtime is available."""
        async def mock_get_nats():
            return mock_nats_publisher

        with patch("heretek_swarm.api.provisioner.detect_runtime") as mock_detect, \
             patch("heretek_swarm.api.provisioner.get_config_service", return_value=mock_config_service), \
             patch("heretek_swarm.api.provisioner.get_nats_publisher", mock_get_nats):
            mock_detect.side_effect = RuntimeError("Neither podman nor docker available")

            client = TestClient(provisioner_app)

            response = client.post(
                "/api/wizard/provision",
                json={"services": ["postgres"], "runtime": "auto"},
            )

            assert response.status_code == 500
            assert "container runtime" in response.json()["detail"].lower()

    def test_provision_with_explicit_runtime(
        self, provisioner_app, mock_nats_publisher, mock_config_service
    ):
        """Test provisioning with explicitly specified runtime."""
        mock_results = {
            InfraService.POSTGRES: ConnectionStringResult(
                service=InfraService.POSTGRES,
                success=True,
                connection_string="postgresql://postgres:password@localhost:5432/postgres",
                host="localhost",
                port=5432,
            ),
        }

        async def mock_get_nats():
            return mock_nats_publisher

        with patch("heretek_swarm.api.provisioner.provision_all", new_callable=AsyncMock, return_value=mock_results), \
             patch("heretek_swarm.api.provisioner.get_config_service", return_value=mock_config_service), \
             patch("heretek_swarm.api.provisioner.get_nats_publisher", mock_get_nats):

            client = TestClient(provisioner_app)

            response = client.post(
                "/api/wizard/provision",
                json={"services": ["postgres"], "runtime": "docker"},
            )

            assert response.status_code == 200

    def test_provision_returns_connection_strings(
        self, provisioner_app, mock_nats_publisher, mock_config_service
    ):
        """Test that connection strings are returned on success."""
        mock_results = {
            InfraService.POSTGRES: ConnectionStringResult(
                service=InfraService.POSTGRES,
                success=True,
                connection_string="postgresql://postgres:password@localhost:5432/postgres",
                host="localhost",
                port=5432,
            ),
            InfraService.REDIS: ConnectionStringResult(
                service=InfraService.REDIS,
                success=True,
                connection_string="redis://localhost:6379",
                host="localhost",
                port=6379,
            ),
        }

        async def mock_get_nats():
            return mock_nats_publisher

        with patch("heretek_swarm.api.provisioner.provision_all", new_callable=AsyncMock, return_value=mock_results), \
             patch("heretek_swarm.api.provisioner.get_config_service", return_value=mock_config_service), \
             patch("heretek_swarm.api.provisioner.get_nats_publisher", mock_get_nats):

            client = TestClient(provisioner_app)

            response = client.post(
                "/api/wizard/provision",
                json={"services": ["postgres", "redis"], "runtime": "auto"},
            )

            assert response.status_code == 200
            data = response.json()

            assert data["status"] == "completed"
            assert data["total_provisioned"] == 2
            assert data["total_failed"] == 0
            assert "postgres" in data["connection_strings"]
            assert "redis" in data["connection_strings"]

    def test_provision_handles_failed_services(
        self, provisioner_app, mock_nats_publisher, mock_config_service
    ):
        """Test handling when service provisioning fails."""
        mock_results = {
            InfraService.POSTGRES: ConnectionStringResult(
                service=InfraService.POSTGRES,
                success=False,
                error="Image pull failed",
                host="localhost",
                port=5432,
            ),
        }

        async def mock_get_nats():
            return mock_nats_publisher

        with patch("heretek_swarm.api.provisioner.provision_all", new_callable=AsyncMock, return_value=mock_results), \
             patch("heretek_swarm.api.provisioner.get_config_service", return_value=mock_config_service), \
             patch("heretek_swarm.api.provisioner.get_nats_publisher", mock_get_nats), \
             patch("heretek_swarm.api.provisioner.detect_runtime", return_value=ContainerRuntime.DOCKER):

            client = TestClient(provisioner_app)

            response = client.post(
                "/api/wizard/provision",
                json={"services": ["postgres"], "runtime": "auto"},
            )

            assert response.status_code == 200
            data = response.json()

            # Should return completed or failed depending on implementation
            # At minimum, should have errors
            assert len(data["errors"]) > 0 or data["total_failed"] > 0

    def test_provision_stores_connection_strings(
        self, provisioner_app, mock_nats_publisher, mock_config_service
    ):
        """Test that connection strings are stored in database."""
        mock_results = {
            InfraService.POSTGRES: ConnectionStringResult(
                service=InfraService.POSTGRES,
                success=True,
                connection_string="postgresql://postgres:password@localhost:5432/postgres",
                host="localhost",
                port=5432,
            ),
        }

        async def mock_get_nats():
            return mock_nats_publisher

        with patch("heretek_swarm.api.provisioner.provision_all", new_callable=AsyncMock, return_value=mock_results), \
             patch("heretek_swarm.api.provisioner.get_config_service", return_value=mock_config_service), \
             patch("heretek_swarm.api.provisioner.get_nats_publisher", mock_get_nats):

            client = TestClient(provisioner_app)

            response = client.post(
                "/api/wizard/provision",
                json={"services": ["postgres"], "runtime": "auto"},
            )

            assert response.status_code == 200

            # Config service should be called to store the config
            assert mock_config_service.create_infrastructure_config.called or \
                   mock_config_service.update_infrastructure_config.called


class TestGetProvisionStatus:
    """Tests for GET /api/wizard/provision/status."""

    def test_get_status_no_runtime(self, provisioner_app, mock_nats_publisher, mock_config_service):
        """Test status when no container runtime is available."""
        async def mock_get_nats():
            return mock_nats_publisher

        with patch("heretek_swarm.api.provisioner.get_config_service", return_value=mock_config_service), \
             patch("heretek_swarm.api.provisioner.get_nats_publisher", mock_get_nats):
            # Patch the local import inside provisioner module
            with patch("heretek_swarm.infrastructure.provisioner.detect_runtime") as mock_detect:
                mock_detect.side_effect = RuntimeError("No runtime")

                client = TestClient(provisioner_app)

                response = client.get("/api/wizard/provision/status")

                assert response.status_code == 200
                data = response.json()
                assert data["runtime"] is None
                assert "error" in data

    def test_get_status_with_running_containers(
        self, provisioner_app, mock_nats_publisher, mock_config_service
    ):
        """Test status when containers are running."""
        async def mock_get_nats():
            return mock_nats_publisher

        with patch("heretek_swarm.api.provisioner.get_config_service", return_value=mock_config_service), \
             patch("heretek_swarm.api.provisioner.get_nats_publisher", mock_get_nats):
            # Patch the local import inside provisioner module
            with patch("heretek_swarm.infrastructure.provisioner.detect_runtime") as mock_detect, \
                 patch("subprocess.run") as mock_subprocess:

                mock_detect.return_value = ContainerRuntime.PODMAN

                # Mock podman ps output
                mock_subprocess.return_value = MagicMock(
                    stdout="heretek-postgres\nheretek-redis",
                    returncode=0,
                )

                client = TestClient(provisioner_app)

                response = client.get("/api/wizard/provision/status")

                assert response.status_code == 200
                data = response.json()
                assert data["runtime"] == "podman"
                assert "heretek-postgres" in data["running_containers"]


class TestStopInfrastructure:
    """Tests for POST /api/wizard/provision/stop."""

    def test_stop_no_containers(self, provisioner_app, mock_nats_publisher):
        """Test stopping when no containers are running."""
        async def mock_get_nats():
            return mock_nats_publisher

        with patch("heretek_swarm.api.provisioner.detect_runtime", return_value=ContainerRuntime.DOCKER), \
             patch("subprocess.run") as mock_subprocess, \
             patch("heretek_swarm.api.provisioner.get_nats_publisher", mock_get_nats):

            mock_subprocess.return_value = MagicMock(
                stdout="",
                returncode=0,
            )

            client = TestClient(provisioner_app)

            response = client.post("/api/wizard/provision/stop")

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["stopped"] == []

    def test_stop_with_containers(self, provisioner_app, mock_nats_publisher):
        """Test stopping running containers."""
        async def mock_get_nats():
            return mock_nats_publisher

        with patch("heretek_swarm.api.provisioner.detect_runtime", return_value=ContainerRuntime.PODMAN), \
             patch("subprocess.run") as mock_subprocess, \
             patch("heretek_swarm.api.provisioner.get_nats_publisher", mock_get_nats):

            # First call: list containers, second call: stop each
            mock_subprocess.side_effect = [
                MagicMock(stdout="heretek-postgres\nheretek-redis", returncode=0),
                MagicMock(returncode=0),
                MagicMock(returncode=0),
            ]

            client = TestClient(provisioner_app)

            response = client.post("/api/wizard/provision/stop")

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert len(data["stopped"]) == 2


class TestServiceMapping:
    """Tests for service name mapping."""

    def test_valid_service_mappings(self, provisioner_app, mock_nats_publisher, mock_config_service):
        """Test that all valid service names are accepted."""
        async def mock_get_nats():
            return mock_nats_publisher

        with patch("heretek_swarm.api.provisioner.provision_all", new_callable=AsyncMock, return_value={}), \
             patch("heretek_swarm.api.provisioner.get_config_service", return_value=mock_config_service), \
             patch("heretek_swarm.api.provisioner.get_nats_publisher", mock_get_nats):

            client = TestClient(provisioner_app)

            valid_mappings = [
                "postgres",
                "postgresql",
                "redis",
                "qdrant",
                "nats",
                "mem0",
            ]

            for service in valid_mappings:
                response = client.post(
                    "/api/wizard/provision",
                    json={"services": [service], "runtime": "auto"},
                )
                # Should not fail on service validation
                assert response.status_code in [200, 500]

    def test_case_insensitive(self, provisioner_app, mock_nats_publisher, mock_config_service):
        """Test that service names are case insensitive."""
        async def mock_get_nats():
            return mock_nats_publisher

        with patch("heretek_swarm.api.provisioner.provision_all", new_callable=AsyncMock, return_value={}), \
             patch("heretek_swarm.api.provisioner.get_config_service", return_value=mock_config_service), \
             patch("heretek_swarm.api.provisioner.get_nats_publisher", mock_get_nats):

            client = TestClient(provisioner_app)

            # Test uppercase
            response = client.post(
                "/api/wizard/provision",
                json={"services": ["POSTGRES"], "runtime": "auto"},
            )

            # Should work (case insensitive)
            assert response.status_code in [200, 500]

            # Test mixed case
            response = client.post(
                "/api/wizard/provision",
                json={"services": ["PostgreSQL"], "runtime": "auto"},
            )

            assert response.status_code in [200, 500]
