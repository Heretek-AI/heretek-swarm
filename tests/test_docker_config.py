"""Tests for Docker Compose configuration validity."""

import json
import shutil
import subprocess

import pytest

_docker_missing = pytest.mark.skipif(
    not shutil.which("docker"),
    reason="Docker not available in this environment",
)


@_docker_missing
def test_docker_compose_config_validates():
    """docker compose config should parse without errors."""
    result = subprocess.run(
        ["docker", "compose", "config"], capture_output=True, text=True, cwd="."  # noqa: S607
    )
    assert result.returncode == 0, f"docker compose config failed: {result.stderr}"


@_docker_missing
def test_api_service_has_no_profile():
    """API service should not be gated behind a profile."""
    result = subprocess.run(
        ["docker", "compose", "config", "--format", "json"], capture_output=True, text=True, cwd="."  # noqa: S607
    )
    assert result.returncode == 0
    config = json.loads(result.stdout)
    api_service = config["services"]["api"]
    assert "profiles" not in api_service or api_service.get("profiles") == []


@_docker_missing
def test_dashboard_service_has_no_profile():
    """Dashboard service should not be gated behind a profile."""
    result = subprocess.run(
        ["docker", "compose", "config", "--format", "json"], capture_output=True, text=True, cwd="."  # noqa: S607
    )
    assert result.returncode == 0
    config = json.loads(result.stdout)
    dashboard_service = config["services"]["dashboard"]
    assert "profiles" not in dashboard_service or dashboard_service.get("profiles") == []


@_docker_missing
def test_api_health_check_targets_health_endpoint():
    """API service health check should target /health."""
    result = subprocess.run(
        ["docker", "compose", "config", "--format", "json"], capture_output=True, text=True, cwd="."  # noqa: S607
    )
    assert result.returncode == 0
    config = json.loads(result.stdout)
    api_service = config["services"]["api"]
    healthcheck = api_service.get("healthcheck", {})
    test_cmd = healthcheck.get("test", [])
    # Join the command parts to search for /health
    cmd_str = " ".join(str(part) for part in test_cmd)
    assert "/health" in cmd_str, f"Health check command does not target /health: {cmd_str}"


@_docker_missing
def test_all_six_services_present():
    """All 6 services should be defined: postgres, redis, qdrant, nats, api, dashboard."""
    result = subprocess.run(
        ["docker", "compose", "config", "--format", "json"], capture_output=True, text=True, cwd="."  # noqa: S607
    )
    assert result.returncode == 0
    config = json.loads(result.stdout)
    expected_services = {"postgres", "redis", "qdrant", "nats", "api", "dashboard"}
    actual_services = set(config["services"].keys())
    assert expected_services.issubset(actual_services), (
        f"Missing services: {expected_services - actual_services}"
    )
