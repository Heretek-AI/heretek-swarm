"""
Tests for the compute tier detection API and classifier.

Covers:
  - T01: GET /api/compute/tier endpoint (endpoint tests)
  - T02: ComputeTierClient (client tests — added in T02)
  - T03: Tier-gated anomaly response (tier_gated tests — added in T03)
  - T04: Full contract verification (full contract test)

Tests use TestClient against the real FastAPI app.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import psutil
import pytest
from fastapi.testclient import TestClient

from heretek_swarm.actors.sentinel.anomaly import AnomalyMonitor
from heretek_swarm.api.compute_tier import _detect_gpu, classify_tier, router
from heretek_swarm.api.main import app
from heretek_swarm.compute_tier.client import ComputeTierClient, ComputeTierResult
from heretek_swarm.security.anomaly_detection import (
    AnomalyDetectionConfig,
    AnomalyDetectionResult,
    AnomalySeverity,
    AnomalyType,
    ResponseStatus,
)
from heretek_swarm.security.behavioral_baseline import create_behavioral_baseline

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _get_tier(client: TestClient) -> int:
    """Convenience: fetch the tier value from a live response."""
    resp = client.get("/api/compute/tier")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data["tier"], int)
    assert isinstance(data["details"]["cpu_count"], int)
    assert isinstance(data["details"]["total_ram_gb"], float)
    assert isinstance(data["details"]["gpu_available"], bool)
    return data["tier"]


# ---------------------------------------------------------------------------
# Unit tests: classify_tier
# ---------------------------------------------------------------------------

# ── Tier 1 boundary cases ──

def test_classify_tier1_less_than_4_cpu() -> None:
    assert classify_tier(cpu_count=1, total_ram_gb=32, gpu_available=False) == 1


def test_classify_tier1_less_than_8gb_ram() -> None:
    assert classify_tier(cpu_count=16, total_ram_gb=2.0, gpu_available=False) == 1


def test_classify_tier1_both_low() -> None:
    assert classify_tier(cpu_count=2, total_ram_gb=4, gpu_available=False) == 1


# ── Tier 2 boundary cases ──

def test_classify_tier2_min_edge() -> None:
    assert classify_tier(cpu_count=4, total_ram_gb=8, gpu_available=False) == 2


def test_classify_tier2_mid() -> None:
    assert classify_tier(cpu_count=6, total_ram_gb=16, gpu_available=False) == 2


def test_classify_tier2_upper_edge() -> None:
    assert classify_tier(cpu_count=7, total_ram_gb=31, gpu_available=False) == 2


# ── Tier 2 with GPU → Tier 3 ──

def test_classify_tier2_with_gpu_becomes_tier3() -> None:
    assert classify_tier(cpu_count=4, total_ram_gb=8, gpu_available=True) == 3


# ── Tier 3 boundary cases ──

def test_classify_tier3_8_cpus_min_ram() -> None:
    """8 CPUs and >=8GB RAM with no GPU → Tier 3."""
    assert classify_tier(cpu_count=8, total_ram_gb=8, gpu_available=False) == 3


def test_classify_tier3_32gb_ram_with_enough_cpu() -> None:
    """>=32GB RAM and >=4 CPUs → Tier 3 (Tier 1 safety net not triggered)."""
    assert classify_tier(cpu_count=4, total_ram_gb=32, gpu_available=False) == 3


def test_classify_tier3_gpu_even_with_low_cpu_and_ram() -> None:
    """GPU available + enough CPU/RAM to pass Tier 1 → Tier 3."""
    assert classify_tier(cpu_count=4, total_ram_gb=8, gpu_available=True) == 3


# ── Edge: exactly 0 cpu / 0 ram (safety) ──

def test_classify_tier1_zero_everything() -> None:
    assert classify_tier(cpu_count=0, total_ram_gb=0, gpu_available=False) == 1


# ---------------------------------------------------------------------------
# Unit tests: _detect_gpu
# ---------------------------------------------------------------------------


def test_gpu_detection_returns_bool() -> None:
    """On any real system, _detect_gpu must return a bool."""
    assert isinstance(_detect_gpu(), bool)


def test_gpu_detection_torch_not_installed() -> None:
    """When torch is not importable, _detect_gpu returns False."""
    with patch("heretek_swarm.api.compute_tier.torch", create=True):
        # Simulate ImportError on the inner import
        import builtins
        original_import = builtins.__import__

        def _fake_import(name, *args, **kwargs):
            if name == "torch":
                raise ImportError("No module named 'torch'")
            return original_import(name, *args, **kwargs)

        with patch("builtins.__import__", side_effect=_fake_import):
            # Re-import to force the patched import path
            from importlib import reload

            import heretek_swarm.api.compute_tier as ct

            reload(ct)
            result = ct._detect_gpu()
            assert result is False


def test_gpu_detection_cuda_error_fallback() -> None:
    """When cuda.is_available() raises, _detect_gpu returns False."""
    with patch("torch.cuda.is_available", side_effect=RuntimeError("CUDA gone")):
        assert _detect_gpu() is False


# ---------------------------------------------------------------------------
# Integration tests: GET /api/compute/tier endpoint
# ---------------------------------------------------------------------------


@pytest.fixture(name="client")
def client_fixture():
    """Provide a TestClient wired to the full FastAPI app."""
    return TestClient(app)


class TestComputeTierEndpoint:
    """T01: GET /api/compute/tier returns valid tier response."""

    def test_endpoint_returns_200_and_valid_shape(self, client: TestClient) -> None:
        resp = client.get("/api/compute/tier")
        assert resp.status_code == 200
        data = resp.json()
        assert "tier" in data
        assert "details" in data
        assert data["tier"] in {1, 2, 3}
        details = data["details"]
        assert isinstance(details["cpu_count"], int)
        assert details["cpu_count"] > 0
        assert isinstance(details["total_ram_gb"], float)
        assert details["total_ram_gb"] >= 0
        assert isinstance(details["gpu_available"], bool)

    def test_endpoint_no_auth_required(self, client: TestClient) -> None:
        """No Authorization header needed — internal service-to-service."""
        resp = client.get("/api/compute/tier", headers={})
        assert resp.status_code == 200

    def test_endpoint_tier_value_is_consistent(self, client: TestClient) -> None:
        """Multiple calls return the same tier (host doesn't change)."""
        t1 = _get_tier(client)
        t2 = _get_tier(client)
        t3 = _get_tier(client)
        assert t1 == t2 == t3

    # ── Tier classification correctness via mock ──

    def test_endpoint_tier1_with_patched_system(self, client: TestClient) -> None:
        with (
            patch.object(psutil, "cpu_count", return_value=1),
            patch.object(
                psutil, "virtual_memory",
                return_value=type("vmem", (), {"total": 2 * 1024**3})(),
            ),
            patch("heretek_swarm.api.compute_tier._detect_gpu", return_value=False),
        ):
            resp = client.get("/api/compute/tier")
            assert resp.status_code == 200
            assert resp.json()["tier"] == 1

    def test_endpoint_tier2_with_patched_system(self, client: TestClient) -> None:
        with (
            patch.object(psutil, "cpu_count", return_value=6),
            patch.object(
                psutil, "virtual_memory",
                return_value=type("vmem", (), {"total": 16 * 1024**3})(),
            ),
            patch("heretek_swarm.api.compute_tier._detect_gpu", return_value=False),
        ):
            resp = client.get("/api/compute/tier")
            assert resp.status_code == 200
            assert resp.json()["tier"] == 2

    def test_endpoint_tier3_with_patched_system(self, client: TestClient) -> None:
        with (
            patch.object(psutil, "cpu_count", return_value=16),
            patch.object(
                psutil, "virtual_memory",
                return_value=type("vmem", (), {"total": 64 * 1024**3})(),
            ),
            patch("heretek_swarm.api.compute_tier._detect_gpu", return_value=True),
        ):
            resp = client.get("/api/compute/tier")
            assert resp.status_code == 200
            assert resp.json()["tier"] == 3

    # ── Error handling ──

    def test_endpoint_handles_psutil_failure_gracefully(
        self, client: TestClient
    ) -> None:
        """If psutil fails, degrade to Tier 1 rather than 500."""
        with patch.object(psutil, "cpu_count", side_effect=OSError("psutil broken")):
            resp = client.get("/api/compute/tier")
            assert resp.status_code == 200
            assert resp.json()["tier"] == 1


# ---------------------------------------------------------------------------
# Router isolation: the router by itself mounts correctly
# ---------------------------------------------------------------------------


def test_router_routes_exist() -> None:
    paths = [r.path for r in router.routes]
    assert "/api/compute/tier" in paths


# ---------------------------------------------------------------------------
# Sanity: health endpoint is unaffected
# ---------------------------------------------------------------------------


def test_health_endpoint_unaffected(client: TestClient) -> None:
    """Slice verification: GET /api/health still works."""
    resp = client.get("/api/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "healthy"


# ---------------------------------------------------------------------------
# T02: ComputeTierClient tests
# ---------------------------------------------------------------------------


def _mock_httpx_response(
    status_code: int = 200,
    json_payload: dict | None = None,
    json_side_effect: Exception | None = None,
):
    """Build an ``AsyncMock`` that acts as a context-managed ``httpx.AsyncClient``
    whose ``get()`` returns a mock response with the given status, JSON body,
    or JSON error side-effect."""
    from unittest.mock import MagicMock as _MagicMock

    mock_resp = _MagicMock()
    mock_resp.status_code = status_code
    if json_side_effect is not None:
        mock_resp.json.side_effect = json_side_effect
    elif json_payload is not None:
        mock_resp.json.return_value = json_payload

    mock_client = AsyncMock()
    mock_client.__aenter__.return_value = mock_client
    mock_client.__aexit__.return_value = False
    mock_client.get = AsyncMock(return_value=mock_resp)

    return mock_client


def _mock_httpx_error_ctx(error: Exception):
    """Build an ``AsyncMock`` whose ``get()`` raises the given error."""

    mock_client = AsyncMock()
    mock_client.__aenter__.return_value = mock_client
    mock_client.__aexit__.return_value = False
    mock_client.get = AsyncMock(side_effect=error)

    return mock_client


class TestComputeTierClientHappyPath:
    """Client returns typed result on 200 with valid JSON."""

    @pytest.mark.asyncio
    async def test_client_returns_correct_tier_on_200(self) -> None:
        c = ComputeTierClient()
        with patch.object(c, "_endpoint", "http://test/api/compute/tier"), patch(
            "httpx.AsyncClient",
            return_value=_mock_httpx_response(
                json_payload={
                    "tier": 2,
                    "details": {"cpu_count": 6, "total_ram_gb": 16.0, "gpu_available": False},
                }
            ),
        ):
            result = await c.get_tier()
        expected = ComputeTierResult(tier=2, cpu_count=6, total_ram_gb=16.0, gpu_available=False)
        assert result == expected

    @pytest.mark.asyncio
    async def test_client_returns_tier3_with_gpu(self) -> None:
        c = ComputeTierClient()
        with patch.object(c, "_endpoint", "http://test/api/compute/tier"), patch(
            "httpx.AsyncClient",
            return_value=_mock_httpx_response(
                json_payload={
                    "tier": 3,
                    "details": {"cpu_count": 16, "total_ram_gb": 64.0, "gpu_available": True},
                }
            ),
        ):
            result = await c.get_tier()
        assert result.tier == 3
        assert result.gpu_available is True


class TestComputeTierClientFallbacks:
    """Client falls back to Tier 1 on any error."""

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "error",
        [
            httpx.TimeoutException("timed out"),
            httpx.ConnectError("refused"),
            httpx.RequestError("generic"),
        ],
    )
    async def test_client_falls_back_on_http_error(self, error: httpx.RequestError) -> None:
        c = ComputeTierClient()
        with patch.object(c, "_endpoint", "http://test/api/compute/tier"), patch(
            "httpx.AsyncClient", return_value=_mock_httpx_error_ctx(error)
        ):
            result = await c.get_tier()
        expected = ComputeTierResult(tier=1, cpu_count=1, total_ram_gb=0.0, gpu_available=False)
        assert result == expected

    @pytest.mark.asyncio
    async def test_client_falls_back_on_non_200(self) -> None:
        c = ComputeTierClient()
        with patch.object(c, "_endpoint", "http://test/api/compute/tier"), patch(
            "httpx.AsyncClient",
            return_value=_mock_httpx_response(status_code=500),
        ):
            result = await c.get_tier()
        assert result.tier == 1

    @pytest.mark.asyncio
    async def test_client_falls_back_on_non_200_404(self) -> None:
        c = ComputeTierClient()
        with patch.object(c, "_endpoint", "http://test/api/compute/tier"), patch(
            "httpx.AsyncClient",
            return_value=_mock_httpx_response(status_code=404),
        ):
            result = await c.get_tier()
        assert result.tier == 1

    @pytest.mark.asyncio
    async def test_client_falls_back_on_bad_json(self) -> None:
        c = ComputeTierClient()
        with patch.object(c, "_endpoint", "http://test/api/compute/tier"), patch(
            "httpx.AsyncClient",
            return_value=_mock_httpx_response(
                json_side_effect=ValueError("bad json"),
            ),
        ):
            result = await c.get_tier()
        assert result.tier == 1

    @pytest.mark.asyncio
    async def test_client_falls_back_on_missing_key(self) -> None:
        c = ComputeTierClient()
        with patch.object(c, "_endpoint", "http://test/api/compute/tier"), patch(
            "httpx.AsyncClient",
            return_value=_mock_httpx_response(
                json_payload={"tier": 2},  # missing details
            ),
        ):
            result = await c.get_tier()
        assert result.tier == 1

    @pytest.mark.asyncio
    async def test_client_falls_back_on_malformed_payload(self) -> None:
        c = ComputeTierClient()
        with patch.object(c, "_endpoint", "http://test/api/compute/tier"), patch(
            "httpx.AsyncClient",
            return_value=_mock_httpx_response(
                json_payload={
                    "tier": "two",  # string, not int
                    "details": {"cpu_count": 6, "total_ram_gb": 16.0, "gpu_available": False},
                }
            ),
        ):
            result = await c.get_tier()
        assert result.tier == 1

    @pytest.mark.asyncio
    async def test_client_falls_back_on_unexpected_exception(self) -> None:
        c = ComputeTierClient()
        with patch.object(c, "_endpoint", "http://test/api/compute/tier"), patch(
            "httpx.AsyncClient", return_value=_mock_httpx_error_ctx(Exception("boom"))
        ):
            result = await c.get_tier()
        assert result.tier == 1


class TestComputeTierClientLogging:
    """Client emits correct structured log events on success and failure.

    Uses ``structlog.testing.capture_logs`` to assert exact event names
    and key metadata fields for each signal.
    """

    @pytest.mark.asyncio
    async def test_client_logs_info_on_success(self) -> None:
        """Successful query emits ``compute_tier_queried`` at INFO with tier fields."""
        import structlog

        c = ComputeTierClient()
        with (
            patch.object(c, "_endpoint", "http://test/api/compute/tier"),
            patch(
                "httpx.AsyncClient",
                return_value=_mock_httpx_response(
                    json_payload={
                        "tier": 2,
                        "details": {
                            "cpu_count": 6,
                            "total_ram_gb": 16.0,
                            "gpu_available": False,
                        },
                    }
                ),
            ),
            structlog.testing.capture_logs() as cap_logs,
        ):
            result = await c.get_tier()

        assert result.tier == 2
        info_logs = [log for log in cap_logs if log.get("event") == "compute_tier_queried"]
        assert len(info_logs) == 1
        entry = info_logs[0]
        assert entry["log_level"] == "info"
        assert entry["tier"] == 2
        assert entry["cpu_count"] == 6
        assert entry["total_ram_gb"] == 16.0
        assert entry["gpu_available"] is False

    @pytest.mark.asyncio
    async def test_client_logs_warning_on_timeout(self) -> None:
        """Timeout emits ``compute_tier_service_unreachable`` + ``compute_tier_fallback_tier_1``."""
        import structlog

        c = ComputeTierClient()
        with (
            patch.object(c, "_endpoint", "http://test/api/compute/tier"),
            patch(
                "httpx.AsyncClient",
                return_value=_mock_httpx_error_ctx(httpx.TimeoutException("timed out")),
            ),
            structlog.testing.capture_logs() as cap_logs,
        ):
            result = await c.get_tier()

        assert result.tier == 1
        unreachable_logs = [
            log for log in cap_logs if log.get("event") == "compute_tier_service_unreachable"
        ]
        assert len(unreachable_logs) == 1
        assert unreachable_logs[0]["reason"] == "timeout"
        assert unreachable_logs[0]["log_level"] == "warning"

        fallback_logs = [
            log for log in cap_logs if log.get("event") == "compute_tier_fallback_tier_1"
        ]
        assert len(fallback_logs) == 1
        assert fallback_logs[0]["reason"] == "timeout"
        assert fallback_logs[0]["log_level"] == "warning"

    @pytest.mark.asyncio
    async def test_client_logs_warning_on_non_200(self) -> None:
        """Non-200 response emits ``compute_tier_service_unreachable`` + fallback."""
        import structlog

        c = ComputeTierClient()
        with (
            patch.object(c, "_endpoint", "http://test/api/compute/tier"),
            patch(
                "httpx.AsyncClient",
                return_value=_mock_httpx_response(status_code=503),
            ),
            structlog.testing.capture_logs() as cap_logs,
        ):
            result = await c.get_tier()

        assert result.tier == 1
        unreachable_logs = [
            log for log in cap_logs if log.get("event") == "compute_tier_service_unreachable"
        ]
        assert len(unreachable_logs) == 1
        assert unreachable_logs[0]["reason"] == "HTTP 503"

        fallback_logs = [
            log for log in cap_logs if log.get("event") == "compute_tier_fallback_tier_1"
        ]
        assert len(fallback_logs) == 1
        assert fallback_logs[0]["reason"] == "HTTP 503"

    @pytest.mark.asyncio
    async def test_client_logs_on_malformed_json(self) -> None:
        """Bad JSON response emits service_unreachable + fallback warnings."""
        import structlog

        c = ComputeTierClient()
        with (
            patch.object(c, "_endpoint", "http://test/api/compute/tier"),
            patch(
                "httpx.AsyncClient",
                return_value=_mock_httpx_response(json_side_effect=ValueError("bad json")),
            ),
            structlog.testing.capture_logs() as cap_logs,
        ):
            result = await c.get_tier()

        assert result.tier == 1
        unreachable_logs = [
            log for log in cap_logs if log.get("event") == "compute_tier_service_unreachable"
        ]
        assert len(unreachable_logs) == 1
        assert unreachable_logs[0]["reason"] == "invalid JSON response"

        fallback_logs = [
            log for log in cap_logs if log.get("event") == "compute_tier_fallback_tier_1"
        ]
        assert len(fallback_logs) == 1

    @pytest.mark.asyncio
    async def test_client_logs_on_connection_error(self) -> None:
        """Connection refused emits service_unreachable with correct reason."""
        import structlog

        c = ComputeTierClient()
        with (
            patch.object(c, "_endpoint", "http://test/api/compute/tier"),
            patch(
                "httpx.AsyncClient",
                return_value=_mock_httpx_error_ctx(httpx.ConnectError("refused")),
            ),
            structlog.testing.capture_logs() as cap_logs,
        ):
            result = await c.get_tier()

        assert result.tier == 1
        unreachable_logs = [
            log for log in cap_logs if log.get("event") == "compute_tier_service_unreachable"
        ]
        assert len(unreachable_logs) == 1
        assert unreachable_logs[0]["reason"] == "connection refused"


class TestComputeTierClientConstructor:
    """Client accepts custom base_url and timeout."""

    def test_default_values(self) -> None:
        client = ComputeTierClient()
        assert client._base_url == "http://localhost:8000"
        assert client._timeout == 0.5
        assert client._endpoint == "http://localhost:8000/api/compute/tier"

    def test_custom_base_url(self) -> None:
        client = ComputeTierClient(base_url="http://host:9000")
        assert client._endpoint == "http://host:9000/api/compute/tier"

    def test_custom_base_url_trailing_slash(self) -> None:
        client = ComputeTierClient(base_url="http://host:9000/")
        assert client._endpoint == "http://host:9000/api/compute/tier"

    def test_custom_timeout(self) -> None:
        client = ComputeTierClient(timeout=2.0)
        assert client._timeout == 2.0


# ---------------------------------------------------------------------------
# T03: Tier-gated anomaly response tests
# ---------------------------------------------------------------------------


def _make_anomaly(
    anomaly_id: str = "ANOM_test",
    agent_id: str = "agent_1",
    anomaly_type: AnomalyType = AnomalyType.BEHAVIORAL_DRIFT,
    severity: AnomalySeverity = AnomalySeverity.MEDIUM,
) -> AnomalyDetectionResult:
    """Create an AnomalyDetectionResult suitable for testing."""
    from datetime import UTC, datetime

    return AnomalyDetectionResult(
        anomaly_id=anomaly_id,
        agent_id=agent_id,
        anomaly_type=anomaly_type,
        severity=severity,
        timestamp=datetime.now(UTC),
        z_score=3.5,
        trigger_metric="request_rate",
        expected_value=1.0,
        observed_value=5.0,
        confidence=0.95,
    )


def _mock_tier_client_1():
    """Mock ComputeTierClient that returns Tier 1."""

    mock = MagicMock(spec=ComputeTierClient)
    mock.get_tier = AsyncMock(
        return_value=ComputeTierResult(tier=1, cpu_count=2, total_ram_gb=4.0, gpu_available=False)
    )
    return mock


def _mock_tier_client_2():
    """Mock ComputeTierClient that returns Tier 2."""

    mock = MagicMock(spec=ComputeTierClient)
    mock.get_tier = AsyncMock(
        return_value=ComputeTierResult(tier=2, cpu_count=6, total_ram_gb=16.0, gpu_available=False)
    )
    return mock


def _mock_tier_client_3():
    """Mock ComputeTierClient that returns Tier 3."""

    mock = MagicMock(spec=ComputeTierClient)
    mock.get_tier = AsyncMock(
        return_value=ComputeTierResult(tier=3, cpu_count=16, total_ram_gb=64.0, gpu_available=True)
    )
    return mock


def _make_monitor(tier_client=None) -> AnomalyMonitor:
    """Create a minimal AnomalyMonitor for testing tier-gating."""
    config = AnomalyDetectionConfig(
        z_score_threshold=3.0,
        response_deadline_seconds=30.0,
        max_auto_responses_per_minute=100,  # no rate limiting in tests
        sentinel_prime_escalation_threshold=999,
    )
    baseline_cfg = {
        "min_samples_for_baseline": 30,
        "z_score_threshold": 3.0,
        "quorum_size": 3,
        "quorum_threshold": 0.66,
    }
    baseline = create_behavioral_baseline(baseline_cfg)
    return AnomalyMonitor(
        anomaly_config=config,
        behavioral_baseline=baseline,
        agent_id="test_sentinel",
        compute_tier_client=tier_client,
    )


class TestTierGatedAnomalyResponse:
    """T03: Tier 1/2/3 produce different log signals and response modes."""

    @pytest.mark.asyncio
    async def test_tier1_hard_freeze_blocks_response(self) -> None:
        """Tier 1 → response_status=BLOCKED, no response executed."""
        monitor = _make_monitor(tier_client=_mock_tier_client_1())
        anomaly = _make_anomaly()
        alert = await monitor._process_anomaly(anomaly)

        assert alert is not None
        assert alert.response_status == ResponseStatus.BLOCKED
        # No active response should be recorded
        assert len(monitor._active_responses) == 0

    @pytest.mark.asyncio
    async def test_tier2_fast_track_executes_response(self) -> None:
        """Tier 2 → response is executed (fast_track mode)."""
        monitor = _make_monitor(tier_client=_mock_tier_client_2())
        anomaly = _make_anomaly()
        alert = await monitor._process_anomaly(anomaly)

        assert alert is not None
        assert alert.response_status == ResponseStatus.EXECUTED
        assert len(monitor._active_responses) == 1

    @pytest.mark.asyncio
    async def test_tier3_full_executes_response(self) -> None:
        """Tier 3 → response is executed (full mode)."""
        monitor = _make_monitor(tier_client=_mock_tier_client_3())
        anomaly = _make_anomaly()
        alert = await monitor._process_anomaly(anomaly)

        assert alert is not None
        assert alert.response_status == ResponseStatus.EXECUTED
        assert len(monitor._active_responses) == 1

    @pytest.mark.asyncio
    async def test_no_tier_client_executes_response(self) -> None:
        """Without tier client, execute full response (backward compat)."""
        monitor = _make_monitor(tier_client=None)
        anomaly = _make_anomaly()
        alert = await monitor._process_anomaly(anomaly)

        assert alert is not None
        assert alert.response_status == ResponseStatus.EXECUTED
        assert len(monitor._active_responses) == 1

    @pytest.mark.asyncio
    async def test_tier1_logs_anomaly_response_with_hard_freeze(self) -> None:
        """Tier 1 logs anomaly_response with response_mode=hard_freeze and tier metadata."""
        import structlog

        monitor = _make_monitor(tier_client=_mock_tier_client_1())
        anomaly = _make_anomaly()

        with structlog.testing.capture_logs() as cap_logs:
            await monitor._process_anomaly(anomaly)

        anomaly_logs = [log for log in cap_logs if log.get("event") == "anomaly_response"]
        assert len(anomaly_logs) == 1
        log_entry = anomaly_logs[0]
        assert log_entry["response_mode"] == "hard_freeze"
        assert log_entry["tier"] == 1
        assert log_entry["cpu_count"] == 2
        assert log_entry["total_ram_gb"] == 4.0
        assert log_entry["gpu_available"] is False

    @pytest.mark.asyncio
    async def test_tier2_logs_anomaly_response_with_fast_track(self) -> None:
        """Tier 2 logs anomaly_response with response_mode=fast_track and tier metadata."""
        import structlog

        monitor = _make_monitor(tier_client=_mock_tier_client_2())
        anomaly = _make_anomaly()

        with structlog.testing.capture_logs() as cap_logs:
            await monitor._process_anomaly(anomaly)

        anomaly_logs = [log for log in cap_logs if log.get("event") == "anomaly_response"]
        assert len(anomaly_logs) == 1
        log_entry = anomaly_logs[0]
        assert log_entry["response_mode"] == "fast_track"
        assert log_entry["tier"] == 2
        assert log_entry["cpu_count"] == 6
        assert log_entry["total_ram_gb"] == 16.0
        assert log_entry["gpu_available"] is False

    @pytest.mark.asyncio
    async def test_tier3_logs_anomaly_response_with_full(self) -> None:
        """Tier 3 logs anomaly_response with response_mode=full and tier metadata."""
        import structlog

        monitor = _make_monitor(tier_client=_mock_tier_client_3())
        anomaly = _make_anomaly()

        with structlog.testing.capture_logs() as cap_logs:
            await monitor._process_anomaly(anomaly)

        anomaly_logs = [log for log in cap_logs if log.get("event") == "anomaly_response"]
        assert len(anomaly_logs) == 1
        log_entry = anomaly_logs[0]
        assert log_entry["response_mode"] == "full"
        assert log_entry["tier"] == 3
        assert log_entry["cpu_count"] == 16
        assert log_entry["total_ram_gb"] == 64.0
        assert log_entry["gpu_available"] is True

    @pytest.mark.asyncio
    async def test_tier1_fallback_client_logs_hard_freeze(self) -> None:
        """When tier client falls back to Tier 1 (unreachable), hard_freeze is applied."""

        import structlog

        # Simulate a client that falls back to Tier 1
        fallback_client = MagicMock(spec=ComputeTierClient)
        fallback_client.get_tier = AsyncMock(
            return_value=ComputeTierResult(
                tier=1, cpu_count=1, total_ram_gb=0.0, gpu_available=False
            )
        )
        monitor = _make_monitor(tier_client=fallback_client)
        anomaly = _make_anomaly()

        with structlog.testing.capture_logs() as cap_logs:
            alert = await monitor._process_anomaly(anomaly)

        assert alert.response_status == ResponseStatus.BLOCKED
        anomaly_logs = [log for log in cap_logs if log.get("event") == "anomaly_response"]
        assert len(anomaly_logs) == 1
        assert anomaly_logs[0]["response_mode"] == "hard_freeze"
        assert anomaly_logs[0]["tier"] == 1
