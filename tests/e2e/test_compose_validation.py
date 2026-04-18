"""
Static validation tests for docker-compose.yml.

These tests parse the compose file without bringing up the stack.
They verify the YAML structure, service definitions, healthchecks,
and profile configurations without requiring a running Docker daemon.

Run with: python -m pytest tests/e2e/test_compose_validation.py -v
"""

from pathlib import Path

import pytest
import yaml


# Path to the docker-compose file (project root)
COMPOSE_FILE = Path(__file__).parent.parent.parent / "docker-compose.yml"


@pytest.fixture
def compose_data(compose_project: str) -> dict:
    """Load and parse the docker-compose.yml file."""
    with open(COMPOSE_FILE, "r") as f:
        return yaml.safe_load(f)


class TestComposeFileLoads:
    """Verify the compose file is valid YAML with expected top-level keys."""

    def test_compose_file_loads(self, compose_data: dict) -> None:
        """docker-compose.yml loads with yaml.safe_load() and has top-level keys."""
        assert compose_data is not None

        # Top-level keys that docker-compose requires
        assert "services" in compose_data, "Missing 'services' key"
        assert isinstance(compose_data["services"], dict), "'services' must be a dict"

        # Optional but expected
        assert "volumes" in compose_data, "Missing 'volumes' key"
        assert "networks" in compose_data, "Missing 'networks' key"


class TestRequiredServicesDefined:
    """Verify all required services are defined in the compose file."""

    REQUIRED_SERVICES = ["api", "postgres", "redis", "qdrant", "nats"]

    def test_required_services_defined(self, compose_data: dict) -> None:
        """Each core service exists in the parsed compose."""
        services = compose_data.get("services", {})
        for service_name in self.REQUIRED_SERVICES:
            assert service_name in services, f"Missing required service: {service_name}"

    def test_api_service_has_dockerfile(self, compose_data: dict) -> None:
        """API service specifies a build context and dockerfile."""
        api = compose_data["services"].get("api", {})
        assert "build" in api, "api service missing 'build' key"
        assert api["build"].get("context") == ".", "api build context should be '.'"
        assert "dockerfile" in api["build"], "api build missing 'dockerfile'"

    def test_postgres_has_env_file(self, compose_data: dict) -> None:
        """Postgres service references an env_file for secrets."""
        pg = compose_data["services"].get("postgres", {})
        assert "env_file" in pg, "postgres service missing 'env_file'"


class TestServiceHealthchecks:
    """Verify core services have healthcheck definitions."""

    CORE_SERVICES = ["api", "postgres", "redis", "qdrant", "nats"]

    def test_service_has_healthcheck(self, compose_data: dict) -> None:
        """Each core service dict has a 'healthcheck' key."""
        services = compose_data["services"]
        for service_name in self.CORE_SERVICES:
            service = services.get(service_name, {})
            assert "healthcheck" in service, (
                f"Service '{service_name}' is missing 'healthcheck' configuration"
            )

    def test_healthcheck_has_test_command(self, compose_data: dict) -> None:
        """Each healthcheck has a 'test' command defined."""
        services = compose_data["services"]
        for service_name in self.CORE_SERVICES:
            healthcheck = services[service_name].get("healthcheck", {})
            assert "test" in healthcheck, (
                f"Service '{service_name}' healthcheck missing 'test' command"
            )

    def test_healthcheck_has_interval_and_timeout(self, compose_data: dict) -> None:
        """Each healthcheck specifies interval, timeout, and retries."""
        services = compose_data["services"]
        for service_name in self.CORE_SERVICES:
            healthcheck = services[service_name].get("healthcheck", {})
            assert "interval" in healthcheck, (
                f"Service '{service_name}' healthcheck missing 'interval'"
            )
            assert "timeout" in healthcheck, (
                f"Service '{service_name}' healthcheck missing 'timeout'"
            )
            assert "retries" in healthcheck, (
                f"Service '{service_name}' healthcheck missing 'retries'"
            )


class TestProfileDefinitions:
    """Verify compose profiles are correctly defined for optional services."""

    def test_autonomous_profile_exists(self, compose_data: dict) -> None:
        """'autonomous' profile is defined on at least one service."""
        services = compose_data.get("services", {})
        autonomous_found = False
        for service_name, service in services.items():
            profiles = service.get("profiles", [])
            if "autonomous" in profiles:
                autonomous_found = True
                break
        assert autonomous_found, (
            "No service has 'autonomous' profile defined"
        )

    def test_frontend_profile_exists(self, compose_data: dict) -> None:
        """'frontend' profile is defined on at least one service."""
        services = compose_data.get("services", {})
        frontend_found = False
        for service_name, service in services.items():
            profiles = service.get("profiles", [])
            if "frontend" in profiles:
                frontend_found = True
                break
        assert frontend_found, (
            "No service has 'frontend' profile defined"
        )

    def test_autonomous_service_depends_on_core(self, compose_data: dict) -> None:
        """Autonomous service declares depends_on for core services."""
        services = compose_data.get("services", {})
        for service_name, service in services.items():
            profiles = service.get("profiles", [])
            if "autonomous" in profiles:
                depends_on = service.get("depends_on", {})
                assert "postgres" in depends_on, (
                    "autonomous service should depend on postgres"
                )
                assert "redis" in depends_on, (
                    "autonomous service should depend on redis"
                )


class TestVolumeDefinitions:
    """Verify volumes are properly declared."""

    def test_named_volumes_defined(self, compose_data: dict) -> None:
        """All referenced named volumes are defined in the volumes section."""
        services = compose_data.get("services", {})
        volumes_section = compose_data.get("volumes", {})

        # Collect all volume references from services
        referenced_volumes = set()
        for service in services.values():
            for volume_spec in service.get("volumes", []):
                # Handle named volumes: volume_name:/mount/point
                if isinstance(volume_spec, str):
                    volume_name = volume_spec.split(":")[0]
                    # Skip host paths (no colon or absolute path)
                    if "/" not in volume_name and ":" not in volume_name:
                        referenced_volumes.add(volume_name)

        # Check all referenced volumes are defined
        for volume_name in referenced_volumes:
            assert volume_name in volumes_section, (
                f"Volume '{volume_name}' is referenced but not defined in volumes section"
            )


class TestNetworkDefinitions:
    """Verify networks are properly declared."""

    def test_default_network_defined(self, compose_data: dict) -> None:
        """A 'default' network is defined."""
        networks = compose_data.get("networks", {})
        assert len(networks) > 0, "No networks defined"

    def test_network_driver_is_bridge(self, compose_data: dict) -> None:
        """Network uses bridge driver."""
        networks = compose_data.get("networks", {})
        for net_name, net_config in networks.items():
            driver = net_config.get("driver", "bridge")
            assert driver == "bridge", (
                f"Network '{net_name}' driver should be 'bridge', got '{driver}'"
            )