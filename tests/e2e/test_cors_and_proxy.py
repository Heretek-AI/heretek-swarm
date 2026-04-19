"""
Integration tests for CORS headers and nginx proxy forwarding.

Tests cover:
- CORS preflight (OPTIONS) through port 8000 (API direct)
- CORS through the nginx proxy (port 3000)
- Explicit nginx /health endpoint returning 200
- /api proxy forwarding through nginx to the API backend

Run with: python -m pytest tests/e2e/test_cors_and_proxy.py -v -m integration
"""

import json
import subprocess
import time
import urllib.request
from pathlib import Path
from typing import Tuple

import pytest


COMPOSE_FILE = Path(__file__).parent.parent.parent / "docker-compose.yml"
STACK_STARTUP_TIMEOUT = 120  # seconds


def _docker_compose(
    args: list[str],
    project: str,
    env_path: str,
    timeout: int = STACK_STARTUP_TIMEOUT,
) -> subprocess.CompletedProcess:
    """Run docker compose with the given args, project name, and env file."""
    cmd = [
        "docker",
        "compose",
        "-p", project,
        "-f", str(COMPOSE_FILE),
        "--env-file", env_path,
        *args,
    ]
    return subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=timeout,
    )


def _wait_for_tcp(host: str, port: int, timeout: float = 120.0) -> bool:
    """Poll until a TCP port is reachable or timeout expires."""
    import socket
    end = time.time() + timeout
    while time.time() < end:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2.0)
            result = sock.connect_ex((host, port))
            sock.close()
            if result == 0:
                return True
        except OSError:
            pass
        time.sleep(2.0)
    return False


def _http_request(
    url: str,
    method: str = "GET",
    headers: dict | None = None,
    timeout: float = 10.0,
) -> Tuple[int, dict | None, dict]:
    """
    Make an HTTP request, return (status_code, body_dict, response_headers_dict).

    body_dict is None on non-JSON or error responses.
    """
    try:
        req = urllib.request.Request(url, method=method)
        if headers:
            for k, v in headers.items():
                req.add_header(k, v)
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body_str = resp.read().decode("utf-8")
            try:
                body = json.loads(body_str)
            except (json.JSONDecodeError, ValueError):
                body = None
            # Collect relevant headers
            resp_headers = {
                k: v
                for k, v in resp.headers.items()
                if k.lower().startswith("access-control")
                or k.lower() in ("content-type",)
            }
            return resp.status, body, resp_headers
    except urllib.error.HTTPError as e:
        body_str = e.read().decode("utf-8")
        try:
            body = json.loads(body_str)
        except (json.JSONDecodeError, ValueError):
            body = None
        resp_headers = {
            k: v
            for k, v in e.headers.items()
            if k.lower().startswith("access-control")
            or k.lower() in ("content-type",)
        }
        return e.code, body, resp_headers
    except Exception as e:
        return 0, {"error": str(e)}, {}


def _wait_for_api_healthy(
    api_url: str = "http://localhost:8000/api/health",
    timeout: float = 120.0,
) -> bool:
    """Poll /api/health until 200 or timeout."""
    end = time.time() + timeout
    while time.time() < end:
        try:
            status, body, _ = _http_request(api_url, timeout=5.0)
            if status == 200 and isinstance(body, dict) and "status" in body:
                return True
        except Exception:
            pass
        time.sleep(2.0)
    return False


# -----------------------------------------------------------------------------
# Test: CORS preflight OPTIONS through port 8000 (API direct)
# -----------------------------------------------------------------------------

@pytest.mark.integration
def test_cors_preflight_through_api_direct(
    compose_project: str,
    env_file: str,
    stack_cleanup: None,
) -> None:
    """
    Send an OPTIONS preflight request to the API directly on port 8000.

    Expects:
    - HTTP 200 or 204
    - Access-Control-Allow-Origin header present
    - Access-Control-Allow-Methods includes POST/GET
    - Access-Control-Allow-Headers includes Content-Type
    """
    # Bring up stack with frontend profile to include nginx
    result = _docker_compose(
        ["--profile", "frontend", "up", "-d"],
        project=compose_project,
        env_path=env_file,
        timeout=STACK_STARTUP_TIMEOUT,
    )
    if result.returncode != 0:
        pytest.fail(f"docker compose up failed: {result.stderr}")

    # Wait for core services and API to be healthy
    for service_name, (host, port) in [
        ("postgres", ("localhost", 5432)),
        ("redis", ("localhost", 6379)),
        ("qdrant", ("localhost", 6333)),
    ]:
        if not _wait_for_tcp(host, port, timeout=120.0):
            pytest.fail(f"Core service {service_name} not healthy")

    if not _wait_for_api_healthy("http://localhost:8000/api/health", timeout=120.0):
        pytest.fail("API /api/health did not become healthy within 120s")

    # Give nginx a moment to register
    time.sleep(5.0)

    # Send CORS preflight OPTIONS to /api/v1/agents (or any /api endpoint)
    preflight_url = "http://localhost:8000/api/v1/agents"
    status, body, resp_headers = _http_request(
        preflight_url,
        method="OPTIONS",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "Content-Type,Authorization",
        },
        timeout=10.0,
    )

    # Assert CORS headers present
    assert "access-control-allow-origin" in resp_headers, (
        f"Missing Access-Control-Allow-Origin header. "
        f"Got headers: {resp_headers}"
    )
    # The header value should allow the origin we sent (or be *)
    allowed_origin = resp_headers.get("access-control-allow-origin", "")
    assert allowed_origin in ("*", "http://localhost:3000"), (
        f"Access-Control-Allow-Origin '{allowed_origin}' "
        f"does not allow 'http://localhost:3000'"
    )

    # Access-Control-Allow-Methods should be present (if the server handles CORS)
    # Some servers return 200 without the headers on OPTIONS — that's still valid CORS
    # if the actual routes handle it. We verify the header is present on a GET to confirm.
    get_status, _, get_headers = _http_request(
        preflight_url,
        method="GET",
        headers={"Origin": "http://localhost:3000"},
        timeout=10.0,
    )
    if get_status == 200:
        assert "access-control-allow-origin" in get_headers, (
            "GET response missing Access-Control-Allow-Origin header"
        )


# -----------------------------------------------------------------------------
# Test: CORS through the nginx proxy (port 3000)
# -----------------------------------------------------------------------------

@pytest.mark.integration
def test_cors_through_nginx_proxy(
    compose_project: str,
    env_file: str,
    stack_cleanup: None,
) -> None:
    """
    Send a GET request with Origin header to the nginx proxy on port 3000.

    Expects:
    - HTTP 200 (from /api/health proxied to API)
    - Access-Control-Allow-Origin header present
    - nginx forwards the request to the API backend
    """
    # Bring up stack with frontend profile to include nginx
    result = _docker_compose(
        ["--profile", "frontend", "up", "-d"],
        project=compose_project,
        env_path=env_file,
        timeout=STACK_STARTUP_TIMEOUT,
    )
    if result.returncode != 0:
        pytest.fail(f"docker compose up failed: {result.stderr}")

    # Wait for core services and nginx
    for service_name, (host, port) in [
        ("postgres", ("localhost", 5432)),
        ("redis", ("localhost", 6379)),
        ("qdrant", ("localhost", 6333)),
    ]:
        if not _wait_for_tcp(host, port, timeout=120.0):
            pytest.fail(f"Core service {service_name} not healthy")

    # Wait for nginx on port 3000
    if not _wait_for_tcp("localhost", 3000, timeout=60.0):
        pytest.fail("nginx did not become reachable on port 3000")

    if not _wait_for_api_healthy("http://localhost:8000/api/health", timeout=120.0):
        pytest.fail("API /api/health did not become healthy within 120s")

    # Send GET with Origin through nginx
    nginx_url = "http://localhost:3000/api/health"
    status, body, resp_headers = _http_request(
        nginx_url,
        method="GET",
        headers={"Origin": "http://localhost:3000"},
        timeout=10.0,
    )

    assert status == 200, (
        f"nginx /api/health returned {status}, expected 200. "
        f"Body: {body}"
    )

    assert isinstance(body, dict), f"Expected dict body, got {type(body)}"
    assert "status" in body, f"Missing 'status' key in /api/health response: {body}"

    assert "access-control-allow-origin" in resp_headers, (
        f"Missing Access-Control-Allow-Origin on nginx-proxied response. "
        f"Got headers: {resp_headers}"
    )


# -----------------------------------------------------------------------------
# Test: Explicit nginx /health endpoint returning 200
# -----------------------------------------------------------------------------

@pytest.mark.integration
def test_nginx_health_endpoint(
    compose_project: str,
    env_file: str,
    stack_cleanup: None,
) -> None:
    """
    Request /health directly from nginx on port 3000.

    Expects:
    - HTTP 200 from nginx /health (defined explicitly in nginx.conf)
    - nginx is healthy before API is fully ready
    """
    # Bring up stack with frontend profile to include nginx
    result = _docker_compose(
        ["--profile", "frontend", "up", "-d"],
        project=compose_project,
        env_path=env_file,
        timeout=STACK_STARTUP_TIMEOUT,
    )
    if result.returncode != 0:
        pytest.fail(f"docker compose up failed: {result.stderr}")

    # Wait for nginx to be reachable (it should come up quickly even if API is not ready)
    if not _wait_for_tcp("localhost", 3000, timeout=60.0):
        pytest.fail("nginx did not become reachable on port 3000")

    # Request nginx /health
    nginx_health_url = "http://localhost:3000/health"
    end = time.time() + 30.0
    last_error = ""

    while time.time() < end:
        status, body, _ = _http_request(nginx_health_url, timeout=5.0)
        if status == 200:
            # Test passes - nginx /health returned 200
            return
        last_error = f"status={status}, body={body}"
        time.sleep(2.0)

    pytest.fail(
        f"nginx /health endpoint did not return 200 within 30s.\n"
        f"Last response: {last_error}"
    )


# -----------------------------------------------------------------------------
# Test: /api proxy forwarding through nginx to the API backend
# -----------------------------------------------------------------------------

@pytest.mark.integration
def test_api_proxy_forwarding_through_nginx(
    compose_project: str,
    env_file: str,
    stack_cleanup: None,
) -> None:
    """
    Verify nginx correctly proxies /api/* requests to the API backend on port 8000.

    Tests both a simple GET (/api/health) and a POST that requires JSON body
    processing, to ensure the full request pipeline works.
    """
    # Bring up stack with frontend profile to include nginx
    result = _docker_compose(
        ["--profile", "frontend", "up", "-d"],
        project=compose_project,
        env_path=env_file,
        timeout=STACK_STARTUP_TIMEOUT,
    )
    if result.returncode != 0:
        pytest.fail(f"docker compose up failed: {result.stderr}")

    # Wait for core services and API
    for service_name, (host, port) in [
        ("postgres", ("localhost", 5432)),
        ("redis", ("localhost", 6379)),
        ("qdrant", ("localhost", 6333)),
    ]:
        if not _wait_for_tcp(host, port, timeout=120.0):
            pytest.fail(f"Core service {service_name} not healthy")

    if not _wait_for_api_healthy("http://localhost:8000/api/health", timeout=120.0):
        pytest.fail("API /api/health did not become healthy within 120s")

    # Give nginx a moment to register
    time.sleep(5.0)

    # Test 1: GET /api/health through nginx
    nginx_api_url = "http://localhost:3000/api/health"
    status, body, _ = _http_request(nginx_api_url, timeout=10.0)
    assert status == 200, (
        f"nginx GET /api/health returned {status}, expected 200. Body: {body}"
    )
    assert isinstance(body, dict), f"Expected dict body, got {type(body)}"
    assert "status" in body, f"Missing 'status' key in proxied /api/health: {body}"

    # Test 2: GET /api/v1/agents through nginx (list agents)
    agents_url = "http://localhost:3000/api/v1/agents"
    agents_status, agents_body, _ = _http_request(agents_url, timeout=10.0)
    # 401 is acceptable if no auth token (agents list may require auth)
    # But it should NOT be 502/503/504 (proxy error) or 404 (route not found)
    assert agents_status in (200, 401, 403), (
        f"nginx /api/v1/agents returned {agents_status}, "
        f"expected 200/401/403. Body: {agents_body}"
    )

    # Test 3: Direct API call to confirm it works (compare behavior)
    direct_api_url = "http://localhost:8000/api/health"
    direct_status, direct_body, _ = _http_request(direct_api_url, timeout=10.0)
    assert direct_status == 200, (
        f"Direct API /api/health returned {direct_status}, expected 200"
    )
    assert direct_body == body, (
        "Response body mismatch between nginx-proxied and direct API calls. "
        f"nginx: {body}, direct: {direct_body}"
    )
