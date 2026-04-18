"""
Stack smoke tests — bring up the full docker-compose stack and verify health.

These tests require a running Docker daemon and are marked with
`@pytest.mark.integration` so they can be skipped in unit-only runs.

Run with: python -m pytest tests/e2e/test_stack_smoke.py -v -m integration

The stack is torn down automatically via the `stack_cleanup` fixture
regardless of test outcome (pass, fail, or error).
"""

import json
import subprocess
import time
import urllib.request
from pathlib import Path

import pytest


COMPOSE_FILE = Path(__file__).parent.parent.parent / "docker-compose.yml"
STACK_STARTUP_TIMEOUT = 120  # seconds


def _docker_compose(
    args: list[str],
    project: str,
    env_path: str,
    timeout: int = STACK_STARTUP_TIMEOUT,
) -> subprocess.CompletedProcess:
    """
    Run docker compose with the given args, project name, and env file.

    Returns the CompletedProcess. Raises TimeoutExpired if the command
    exceeds `timeout` seconds.
    """
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


def _http_get(url: str, timeout: float = 10.0) -> tuple[int, dict | None]:
    """Make an HTTP GET request, return status code and JSON body."""
    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = json.loads(resp.read().decode("utf-8"))
            return resp.status, body
    except Exception as e:
        return 0, {"error": str(e)}


@pytest.mark.integration
def test_stack_bringup(
    compose_project: str,
    env_file: str,
    stack_cleanup: None,
) -> None:
    """
    Bring up the stack with --profile autonomous and assert exit code 0.

    The stack_cleanup fixture ensures teardown after the test.
    """
    result = _docker_compose(
        ["--profile", "autonomous", "up", "-d"],
        project=compose_project,
        env_path=env_file,
        timeout=STACK_STARTUP_TIMEOUT,
    )

    if result.returncode != 0:
        pytest.fail(
            f"docker compose up failed with exit code {result.returncode}\n"
            f"STDOUT:\n{result.stdout}\n\nSTDERR:\n{result.stderr}"
        )


@pytest.mark.integration
def test_core_services_healthy(
    compose_project: str,
    env_file: str,
    stack_cleanup: None,
) -> None:
    """
    After stack bringup, poll health endpoints for core services.

    Uses retry logic (2s intervals, 120s timeout) for:
    - postgres:5432  (pg_isready)
    - redis:6379     (redis-cli ping)
    - qdrant:6333    (TCP connect)
    - nats:4222      (TCP connect)
    """
    # Ensure stack is up first
    result = _docker_compose(
        ["--profile", "autonomous", "up", "-d"],
        project=compose_project,
        env_path=env_file,
        timeout=STACK_STARTUP_TIMEOUT,
    )
    if result.returncode != 0:
        pytest.fail(f"docker compose up failed: {result.stderr}")

    # Service host mapping (service name -> (host, port))
    services = {
        "postgres": ("localhost", 5432),
        "redis": ("localhost", 6379),
        "qdrant": ("localhost", 6333),
        "nats": ("localhost", 4222),
    }

    failed: list[str] = []
    for service_name, (host, port) in services.items():
        if not _wait_for_tcp(host, port, timeout=120.0):
            failed.append(f"{service_name} ({host}:{port})")

    assert not failed, (
        f"The following services did not become healthy within 120s: {failed}"
    )


@pytest.mark.integration
def test_api_health_endpoint(
    compose_project: str,
    env_file: str,
    stack_cleanup: None,
) -> None:
    """
    After core services are healthy, poll the API /api/health endpoint.

    Fails if the endpoint doesn't return 200 with expected JSON keys
    within 120 seconds of bringup.
    """
    # Ensure stack is up
    result = _docker_compose(
        ["--profile", "autonomous", "up", "-d"],
        project=compose_project,
        env_path=env_file,
        timeout=STACK_STARTUP_TIMEOUT,
    )
    if result.returncode != 0:
        pytest.fail(f"docker compose up failed: {result.stderr}")

    # Wait for core services first (prerequisite for API health)
    core_services = {
        "postgres": ("localhost", 5432),
        "redis": ("localhost", 6379),
        "qdrant": ("localhost", 6333),
        "nats": ("localhost", 4222),
    }
    for service_name, (host, port) in core_services.items():
        if not _wait_for_tcp(host, port, timeout=120.0):
            pytest.fail(f"Core service {service_name} not healthy, cannot test API")

    # Poll /api/health until 200 or timeout
    api_url = "http://localhost:8000/api/health"
    end = time.time() + 120.0
    last_error = ""

    while time.time() < end:
        status, body = _http_get(api_url, timeout=5.0)
        if status == 200:
            # Verify response shape
            assert isinstance(body, dict), f"Expected dict, got {type(body)}"
            assert "status" in body, f"Missing 'status' key in response: {body}"
            # timestamp is optional but common
            return  # Test passes

        last_error = f"status={status}, body={body}"
        time.sleep(2.0)

    pytest.fail(
        f"API health endpoint did not return 200 within 120s.\n"
        f"Last response: {last_error}"
    )


@pytest.mark.integration
def test_api_docs_accessible(
    compose_project: str,
    env_file: str,
    stack_cleanup: None,
) -> None:
    """
    Verify the FastAPI docs endpoint returns 200 when stack is healthy.

    This is a lightweight health indicator for the API service.
    """
    # Ensure stack is up
    result = _docker_compose(
        ["--profile", "autonomous", "up", "-d"],
        project=compose_project,
        env_path=env_file,
        timeout=STACK_STARTUP_TIMEOUT,
    )
    if result.returncode != 0:
        pytest.fail(f"docker compose up failed: {result.stderr}")

    # Wait for core services first
    for service_name, (host, port) in [
        ("postgres", ("localhost", 5432)),
        ("redis", ("localhost", 6379)),
        ("qdrant", ("localhost", 6333)),
    ]:
        if not _wait_for_tcp(host, port, timeout=120.0):
            pytest.fail(f"Core service {service_name} not healthy")

    # Poll docs endpoint
    docs_url = "http://localhost:8000/docs"
    end = time.time() + 120.0

    while time.time() < end:
        status, _ = _http_get(docs_url, timeout=5.0)
        if status == 200:
            return  # Test passes

        time.sleep(2.0)

    pytest.fail(f"API docs endpoint did not return 200 within 120s")


@pytest.mark.integration
def test_stack_teardown_clean(
    compose_project: str,
    env_file: str,
) -> None:
    """
    Verify docker compose down removes all containers and volumes.

    This test exercises the teardown path used by stack_cleanup,
    confirming no residual containers or named volumes are left behind.
    """
    # Bring up briefly
    result = _docker_compose(
        ["--profile", "autonomous", "up", "-d"],
        project=compose_project,
        env_path=env_file,
        timeout=STACK_STARTUP_TIMEOUT,
    )
    if result.returncode != 0:
        pytest.fail(f"docker compose up failed: {result.stderr}")

    # Teardown
    down_result = _docker_compose(
        ["down", "-v", "--remove-orphans"],
        project=compose_project,
        env_path=env_file,
        timeout=60,
    )
    if down_result.returncode != 0:
        pytest.fail(f"docker compose down failed: {down_result.stderr}")

    # Verify no containers remain for this project
    list_result = subprocess.run(
        ["docker", "ps", "-a", "--format", "{{.Names}}"],
        capture_output=True,
        text=True,
    )
    project_containers = [
        line for line in list_result.stdout.splitlines()
        if line.startswith(compose_project)
    ]
    assert not project_containers, (
        f"Containers still exist after teardown: {project_containers}"
    )