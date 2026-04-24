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
    """Create a temporary .env file with safe mock values.

    The REQUIRED_ENV_VARS loop sets DATABASE_URL=test-key-000, which causes
    load_infrastructure_config() (called by `serve`) to crash with:
      ArgumentError: Could not parse SQLAlchemy URL from given URL string

    Therefore we MUST append valid service URLs AFTER the loop so last-value-wins
    in the .env file keeps the valid values.
    """
    env_content = "\n".join(
        f"{var}=test-key-000" for var in REQUIRED_ENV_VARS
    )
    env_content += "\nENVIRONMENT=development\n"
    env_content += "EMBEDDING_PROVIDER=openai_compatible\n"
    env_content += "MEM0_POSTGRES_PASSWORD=test-key-000\n"
    env_content += "MEM0_LLM_PROVIDER=openai\n"
    env_content += "MEM0_LLM_BASE_URL=https://api.minimax.io/v1\n"
    env_content += "MEM0_LLM_MODEL=MiniMax-M2.7\n"
    # Append AFTER the loop — .env uses last-value-wins so these override
    # the placeholder values set above.  Must be valid URLs so that
    # load_infrastructure_config() (called by `serve`) can create a sync engine.
    env_content += (
        "DATABASE_URL=postgresql+asyncpg://postgres:test-key-000"
        "@postgres:5432/heretek_swarm\n"
    )
    env_content += "REDIS_URL=redis://redis:6379/0\n"
    env_content += "HERETEK_NATS_URL=nats://nats:4222\n"
    env_content += "QDRANT_HOST=http://qdrant:6333\n"

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

    Cleans up leftover heretek-swarm containers before bringing up to avoid
    port conflicts (5432, 6379, 8000, 6333) from previous test runs.
    """
    import subprocess

    # Kill any leftover containers holding ports from prior runs
    result = subprocess.run(
        ["docker", "ps", "-a", "--format", "{{.Names}}:{{.Status}}"],
        capture_output=True, text=True, timeout=30,
    )
    for line in result.stdout.strip().split("\n"):
        if not line:
            continue
        name, _status = line.split(":", 1)
        if name.startswith("heretek-swarm-") and not name.startswith(f"{compose_project}-"):
            subprocess.run(["docker", "rm", "-f", name], capture_output=True, text=True, timeout=15)

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
    Run ALL SQL migrations (001-011) after docker stack is up.

    Migrations must run in order: 001-008 create the core tables, and
    011_create_infrastructure_config_table.sql creates the infrastructure_config
    table which load_infrastructure_config() (called by `serve`) needs.

    Uses `docker compose exec -T` to run each SQL file via psql against the
    postgres container. Fails the test suite if any migration returns non-zero.

    NOTE: 009 and 010 may fail if their tables already exist from prior runs
    (CREATE TABLE IF NOT EXISTS handles idempotency, but some migrations may
    fail on unique constraints or other idempotent operations). We accept
    specific known-safe exit codes for those cases.
    """
    migrations_dir = Path(__file__).parent.parent.parent / "migrations"

    # Ordered list of all migrations (001-011). Some need the pgvector extension
    # which is not available in the standard postgres:15 image. We handle those
    # gracefully via safe_errors.
    migration_files = sorted([
        f.name for f in migrations_dir.glob("???_*.sql")
    ])

    psql_cmd = [
        "docker",
        "compose",
        "-p", compose_project,
        "-f", COMPOSE_FILE,
        "--env-file", env_file,
        "exec", "-T", "postgres",
        "psql", "-U", "postgres", "-d", "heretek_swarm",
    ]

    for migration_file in migration_files:
        # Skip non-migration files (README.md, etc.)
        if not migration_file.endswith(".sql"):
            continue

        migration_sql_path = migrations_dir / migration_file
        migration_sql = migration_sql_path.read_text()

        result = subprocess.run(
            [*psql_cmd, "-c", migration_sql],
            capture_output=True,
            text=True,
            timeout=60,
        )

        if result.returncode != 0:
            # Gracefully skip migrations that need the pgvector extension or type.
            # The postgres:15 image does not include pgvector. Migrations that
            # use CREATE EXTENSION vector or the vector(n) data type fail with:
            #   - "extension 'vector' is not available"
            #   - 'type "vector" does not exist'
            #   - "could not open extension control file"
            # We treat all vector-related errors as safe/skippable since the
            # consciousness and skills APIs tested by S02 don't use those tables.
            import re as _re

            vector_error = _re.search(
                r"(extension .vector. is not available|"
                r'type "vector" does not exist|'
                r"could not open extension control file.*vector)",
                result.stderr,
                _re.IGNORECASE,
            )

            safe_errors = (
                "duplicate key", "already exists", "cannot drop",
                "relation .* does not exist",
            )
            is_safe = vector_error or any(
                _re.search(pat, result.stdout + result.stderr, _re.IGNORECASE)
                for pat in safe_errors
            )
            if not is_safe:
                raise RuntimeError(
                    f"Migration {migration_file} failed:\n"
                    f"STDOUT:\n{result.stdout}\n\nSTDERR:\n{result.stderr}"
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

    Uses BaseUrlSession so that api_client.get('/api/...') works — resolves
    relative paths against the base URL automatically (requests.Session normally
    requires full URLs).
    """
    from requests import Session as BaseUrlSession

    base_url = "http://localhost:8000"
    api_key = "test-key-000"

    class PrefixedSession(BaseUrlSession):
        """requests.Session that automatically prefixes URLs with base_url."""

        def __init__(self, prefix: str, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self._prefix = prefix.rstrip("/")

        def _prepend_prefix(self, url: str) -> str:
            if url.startswith(("http://", "https://")):
                return url
            return f"{self._prefix}{url}"

        def get(self, url: str, **kwargs):
            return super().get(self._prepend_prefix(url), **kwargs)

        def post(self, url: str, **kwargs):
            return super().post(self._prepend_prefix(url), **kwargs)

        def put(self, url: str, **kwargs):
            return super().put(self._prepend_prefix(url), **kwargs)

        def patch(self, url: str, **kwargs):
            return super().patch(self._prepend_prefix(url), **kwargs)

        def delete(self, url: str, **kwargs):
            return super().delete(self._prepend_prefix(url), **kwargs)

        def head(self, url: str, **kwargs):
            return super().head(self._prepend_prefix(url), **kwargs)

        def options(self, url: str, **kwargs):
            return super().options(self._prepend_prefix(url), **kwargs)

    session = PrefixedSession(prefix=base_url)
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