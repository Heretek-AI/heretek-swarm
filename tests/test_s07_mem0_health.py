"""
Tests for mem0 health check integration in /api/health and provisioner skip messages.

Covers:
- (a) mem0 appears in /api/health when backend is initialized
- (b) mem0 reports unavailable when backend is None
- (c) provisioner returns success with informational message for mem0
- (d) CLI health check dispatches to mem0 correctly
"""

from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from heretek_swarm.api.main import app
from heretek_swarm.gateway.auth import verify_auth


def _build_app_for_health() -> TestClient:
    """Build a TestClient app with auth bypassed."""
    app.dependency_overrides[verify_auth] = lambda: "test"
    return TestClient(app)


# ---------------------------------------------------------------------------
# (a) mem0 appears in /api/health when backend is initialized
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_mem0_healthy_in_health_endpoint():
    """mem0 appears as healthy in /api/health when mem0_backend is initialized."""
    from heretek_swarm.api import main as api_main

    mock_backend = MagicMock()
    mock_client = MagicMock()
    mock_backend.client = mock_client
    mock_backend.collection_name = "mem0"
    # get_collection succeeds — backend is healthy
    mock_client.get_collection.return_value = {"name": "mem0"}

    with patch.object(api_main, "memory_store", None), patch.object(
        api_main, "mem0_backend", mock_backend
    ), patch.object(api_main, "check_gateway", return_value={"status": "healthy"}), patch.object(
        api_main, "check_redis", return_value={"status": "healthy"}
    ), patch.object(
        api_main, "check_postgres", return_value={"status": "healthy"}
    ), patch.object(
        api_main, "check_qdrant", return_value={"status": "healthy"}
    ):
        client = _build_app_for_health()
        r = client.get("/api/health")

    assert r.status_code == 200, f"Expected 200, got {r.status_code}: {r.text}"
    data = r.json()
    assert "mem0" in data["services"], f"mem0 missing from services: {list(data['services'])}"
    assert data["services"]["mem0"]["status"] == "healthy", (
        f"Expected healthy, got {data['services']['mem0']}"
    )
    assert "mem0 is embedded" in data["services"]["mem0"]["note"], (
        f"Missing embedded note: {data['services']['mem0']}"
    )


# ---------------------------------------------------------------------------
# (b) mem0 reports unavailable when backend is None
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_mem0_unavailable_when_backend_is_none():
    """mem0 reports unavailable in /api/health when mem0_backend is None."""
    from heretek_swarm.api import main as api_main

    with patch.object(api_main, "memory_store", None), patch.object(
        api_main, "mem0_backend", None
    ), patch.object(api_main, "check_gateway", return_value={"status": "healthy"}), patch.object(
        api_main, "check_redis", return_value={"status": "healthy"}
    ), patch.object(
        api_main, "check_postgres", return_value={"status": "healthy"}
    ), patch.object(
        api_main, "check_qdrant", return_value={"status": "healthy"}
    ):
        client = _build_app_for_health()
        r = client.get("/api/health")

    assert r.status_code == 200, f"Expected 200, got {r.status_code}: {r.text}"
    data = r.json()
    assert "mem0" in data["services"], f"mem0 missing from services: {list(data['services'])}"
    assert data["services"]["mem0"]["status"] == "unavailable", (
        f"Expected unavailable, got {data['services']['mem0']}"
    )
    assert "no standalone container" in data["services"]["mem0"]["note"], (
        f"Missing embedded note: {data['services']['mem0']}"
    )


@pytest.mark.unit
def test_mem0_degraded_when_client_is_none():
    """mem0 reports unhealthy when backend is set but client attribute is None."""
    from heretek_swarm.api import main as api_main

    mock_backend = MagicMock()
    mock_backend.client = None

    with patch.object(api_main, "memory_store", None), patch.object(
        api_main, "mem0_backend", mock_backend
    ), patch.object(api_main, "check_gateway", return_value={"status": "healthy"}), patch.object(
        api_main, "check_redis", return_value={"status": "healthy"}
    ), patch.object(
        api_main, "check_postgres", return_value={"status": "healthy"}
    ), patch.object(
        api_main, "check_qdrant", return_value={"status": "healthy"}
    ):
        client = _build_app_for_health()
        r = client.get("/api/health")

    assert r.status_code == 200, f"Expected 200, got {r.status_code}: {r.text}"
    data = r.json()
    assert data["services"]["mem0"]["status"] == "unhealthy", (
        f"Expected unhealthy, got {data['services']['mem0']}"
    )
    assert "no standalone container" in data["services"]["mem0"]["note"]


# ---------------------------------------------------------------------------
# (c) provisioner returns success with informational message for mem0
# ---------------------------------------------------------------------------


@pytest.mark.unit
@pytest.mark.asyncio
async def test_provision_service_mem0_returns_success_informational():
    """provision_service() for mem0 returns success=True with embedded note."""
    from heretek_swarm.config.models import InfrastructureService
    from heretek_swarm.infrastructure.provisioner import provision_service

    result = await provision_service(
        service=InfrastructureService.MEM0,
        runtime=None,  # type: ignore[arg-type]  # bypasses detect_runtime for unit test
    )
    assert result.success is True, f"Expected success=True, got {result}"
    assert "embedded" in (result.error or ""), (
        f"Expected embedded note, got: {result.error}"
    )
    assert "no standalone container" in (result.error or "")


@pytest.mark.unit
@pytest.mark.asyncio
async def test_provision_all_skips_mem0_with_success():
    """provision_all() includes mem0 with success=True informational message."""
    from heretek_swarm.config.models import InfrastructureService
    from heretek_swarm.infrastructure.provisioner import provision_all

    # Use a single-service list: only mem0
    results = await provision_all(
        services=[InfrastructureService.MEM0],
    )
    assert InfrastructureService.MEM0 in results
    mem0_result = results[InfrastructureService.MEM0]
    assert mem0_result.success is True, f"Expected success=True, got {mem0_result}"
    assert "embedded" in (mem0_result.error or ""), f"Expected embedded note: {mem0_result.error}"
    assert "no standalone container" in (mem0_result.error or "")


@pytest.mark.unit
@pytest.mark.asyncio
async def test_provision_infrastructure_mem0_false_default():
    """provision_infrastructure() excludes mem0 by default, but returns
    informational result when mem0=True is requested."""
    from heretek_swarm.config.models import InfrastructureService
    from heretek_swarm.infrastructure.provisioner import provision_infrastructure

    # Disable all services that need Docker runtime, only test mem0
    results = await provision_infrastructure(
        postgres=False,
        redis=False,
        qdrant=False,
        nats=False,
        mem0=True,
    )
    assert InfrastructureService.MEM0 in results, f"mem0 missing: {list(results.keys())}"
    mem0_result = results[InfrastructureService.MEM0]
    assert mem0_result.success is True, f"Expected success=True, got {mem0_result}"
    assert "embedded" in (mem0_result.error or "")


# ---------------------------------------------------------------------------
# (d) CLI health check dispatches to mem0 correctly
# ---------------------------------------------------------------------------


@pytest.mark.unit
@pytest.mark.asyncio
async def test_cli_check_service_health_dispatches_mem0():
    """_check_service_health dispatches mem0 to _check_mem0 correctly."""
    from heretek_swarm.cli.health import _check_service_health
    from heretek_swarm.config.models import InfrastructureService

    result = await _check_service_health(
        service=InfrastructureService.MEM0,
        host="localhost",
        port=8000,
        timeout=0.5,
    )
    assert result["service"] == "mem0"
    # Expected: connection refused or timeout since no mem0 server is running
    assert result["status"] in ("healthy", "unhealthy", "unknown"), (
        f"Unexpected status: {result['status']}"
    )
    assert isinstance(result["latency_ms"], (int, float))


@pytest.mark.unit
@pytest.mark.asyncio
async def test_cli_check_mem0_returns_unhealthy_when_no_server():
    """_check_mem0 correctly identifies an unresponsive host."""
    from heretek_swarm.cli.health import _check_mem0

    # Using a closed port — connection will fail
    result = await _check_mem0(
        host="localhost",
        port=19999,  # Assumed no service listening here
        timeout=0.5,
        start=0.0,
    )
    assert result["service"] == "mem0"
    # Connection refused means no server — expect unhealthy
    assert result["status"] == "unhealthy", f"Expected unhealthy, got {result['status']}: {result}"
    error_lower = (result.get("error") or "").lower()
    is_connection_error = any(
        token in error_lower for token in ("connection", "connect", "refused", "time")
    )
    assert is_connection_error, f"Expected connection error, got: {result.get('error')}"


@pytest.mark.unit
def test_cli_make_result_mem0_service():
    """_make_result produces correct shape for mem0 service."""
    import time

    from heretek_swarm.cli.health import _make_result
    from heretek_swarm.config.models import HealthStatus, InfrastructureService

    start = time.perf_counter()
    result = _make_result(InfrastructureService.MEM0, HealthStatus.HEALTHY, start)
    assert result["service"] == "mem0"
    assert result["status"] == "healthy"
    assert "latency_ms" in result
    assert result["error"] is None
