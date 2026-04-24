"""
M029 E2E fixtures — Docker bringup with workflow_states migration.

Add:
    docker_stack         — brings up --profile autonomous at module scope
    migrate_workflow_states — runs migration 003 via docker compose exec
    api_client           — authenticated requests.Session() pointing at localhost:8000

Imports REQUIRED_ENV_VARS from tests/e2e/conftest.py so the .env file created
by the env_file fixture (defined in tests/e2e/conftest.py and pulled in via
the test collection path) contains all vars docker-compose needs.
"""

import os
import subprocess
import tempfile
import time
import uuid
from pathlib import Path
from typing import Generator

import pytest
import requests

from tests.e2e.conftest import REQUIRED_ENV_VARS

# =============================================================================
# Constants
# =============================================================================

COMPOSE_FILE = "docker-compose.yml"
STACK_STARTUP_TIMEOUT = 120  # seconds


# =============================================================================
# Helpers
# =============================================================================

def _docker_compose(
    args: list[str],
    project: str,
    env_path: str,
    timeout: int = STACK_STARTUP_TIMEOUT,
) -> subprocess.CompletedProcess:
    """Run docker compose with project name and env file."""
    cmd = [
        "docker",
        "compose",
        "-p", project,
        "-f", COMPOSE_FILE,
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


# =============================================================================
# Base fixtures (aliased from tests/e2e/conftest.py)
# =============================================================================

@pytest.fixture(scope="module")
def compose_project() -> str:
    """Unique docker compose project name with short UUID suffix."""
    return f"heretek-swarm-m029-{uuid.uuid4().hex[:8]}"


@pytest.fixture(scope="module")
def env_file() -> Generator[str, None, None]:
    """Create a temporary .env file with safe mock values."""
    env_content = "\n".join(
        f"{var}=test-key-000" for var in REQUIRED_ENV_VARS
    )
    env_content += "\nENVIRONMENT=development\n"
    env_content += "EMBEDDING_PROVIDER=openai_compatible\n"
    env_content += "MEM0_POSTGRES_PASSWORD=test-key-000\n"
    env_content += "MEM0_LLM_PROVIDER=openai\n"
    env_content += "MEM0_LLM_BASE_URL=https://api.minimax.io/v1\n"
    env_content += "MEM0_LLM_MODEL=MiniMax-M2.7\n"

    project_root = Path(__file__).parent.parent.parent
    with tempfile.NamedTemporaryFile(
        mode="w",
        suffix=".env",
        dir=str(project_root),
        delete=False,
    ) as f:
        f.write(env_content)
        env_path = f.name

    yield env_path

    try:
        os.unlink(env_path)
    except OSError:
        pass


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture(scope="module")
def docker_stack(
    compose_project: str,
    env_file: str,
) -> Generator[str, None, None]:
    """
    Bring up the docker stack with --profile autonomous at module scope.

    Yields the project name so dependent fixtures can reference it.
    Teardown happens automatically when the module finishes.
    """
    # Bring up
    result = _docker_compose(
        ["--profile", "autonomous", "up", "-d"],
        project=compose_project,
        env_path=env_file,
        timeout=STACK_STARTUP_TIMEOUT,
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"docker compose up failed:\nSTDOUT:\n{result.stdout}\n\nSTDERR:\n{result.stderr}"
        )

    # Wait for postgres to be ready (required for migration)
    if not _wait_for_tcp("localhost", 5432, timeout=120.0):
        raise RuntimeError("postgres did not become ready within 120s")

    yield compose_project

    # Teardown after all module tests complete
    _docker_compose(
        ["down", "-v", "--remove-orphans"],
        project=compose_project,
        env_path=env_file,
        timeout=60,
    )


@pytest.fixture(scope="module")
def migrate_workflow_states(
    docker_stack: str,
    compose_project: str,
    env_file: str,
) -> Generator[None, None, None]:
    """
    Run migration 003 (workflow_states table) after docker stack is up.

    Uses `docker compose exec -T` to run the SQL via psql against the postgres
    container. Fails the test suite if the migration SQL returns a non-zero
    exit code.
    """
    migration_sql_path = Path(__file__).parent.parent.parent / "migrations" / "003_create_workflow_states.sql"
    migration_sql = migration_sql_path.read_text()

    result = subprocess.run(
        [
            "docker",
            "compose",
            "-p", compose_project,
            "-f", COMPOSE_FILE,
            "--env-file", env_file,
            "exec", "-T", "postgres",
            "psql", "-U", "postgres", "-d", "heretek_swarm",
            "-c", migration_sql,
        ],
        capture_output=True,
        text=True,
        timeout=30,
    )

    if result.returncode != 0:
        raise RuntimeError(
            f"workflow_states migration failed:\nSTDOUT:\n{result.stdout}\n\nSTDERR:\n{result.stderr}"
        )

    # Verify table exists by running a no-op query
    verify = subprocess.run(
        [
            "docker",
            "compose",
            "-p", compose_project,
            "-f", COMPOSE_FILE,
            "--env-file", env_file,
            "exec", "-T", "postgres",
            "psql", "-U", "postgres", "-d", "heretek_swarm",
            "-c", "SELECT 1 FROM workflow_states LIMIT 1;",
        ],
        capture_output=True,
        text=True,
        timeout=15,
    )
    if verify.returncode != 0:
        raise RuntimeError(
            f"workflow_states table verification failed:\nSTDOUT:\n{verify.stdout}\n\nSTDERR:\n{verify.stderr}"
        )

    yield


@pytest.fixture(scope="module")
def api_client(
    docker_stack: str,
    migrate_workflow_states: None,
) -> Generator[requests.Session, None, None]:
    """
    Authenticated requests.Session pointing at http://localhost:8000.

    Waits up to 120s for the /api/health endpoint to return 200 before yielding.
    Uses HERETEK_API_KEY=test-key-000 (set in the .env file by env_file fixture).
    """
    base_url = "http://localhost:8000"
    api_key = "test-key-000"

    session = requests.Session()
    session.headers.update({
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    })

    # Poll /api/health until 200 or timeout
    health_url = f"{base_url}/api/health"
    end = time.time() + 120.0
    last_error = ""

    while time.time() < end:
        try:
            resp = session.get(health_url, timeout=5.0)
            if resp.status_code == 200:
                yield session
                return
            last_error = f"status={resp.status_code}, body={resp.text[:200]}"
        except requests.RequestException as e:
            last_error = str(e)

        time.sleep(2.0)

    raise RuntimeError(
        f"API health endpoint did not return 200 within 120s.\nLast response: {last_error}"
    )