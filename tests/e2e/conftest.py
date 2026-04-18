"""
Shared pytest fixtures for E2E tests.

Fixtures provide:
- Unique project names to avoid port conflicts in parallel CI runs
- Guaranteed stack cleanup even on test failure
- Temporary .env files with safe mock values
"""

import os
import subprocess
import tempfile
import uuid
from pathlib import Path
from typing import Generator

import pytest


# =============================================================================
# REQUIRED ENV VARS (from .env.example)
# =============================================================================
# The following env vars are referenced by docker-compose.yml and must be
# present in the .env file for the stack to start:
#
# POSTGRES_PASSWORD, OPENAI_API_KEY, OPENAI_BASE_URL, LLM_MODEL,
# EMBEDDING_BASE_URL, EMBBEDDING_API_KEY, HERETEK_API_KEY, JWT_SECRET,
# API_KEY, QDRANT_HOST, QDRANT_PORT, QDRANT_URL
#
# Additional vars used by specific services:
# EMBEDDING_PROVIDER, EMBEDDER_MODEL, ENVIRONMENT, MEM0_POSTGRES_PASSWORD,
# MEM0_LLM_PROVIDER, MEM0_LLM_BASE_URL, MEM0_LLM_API_KEY, NATS_URL, DATABASE_URL

REQUIRED_ENV_VARS = [
    "POSTGRES_PASSWORD",
    "OPENAI_API_KEY",
    "OPENAI_BASE_URL",
    "LLM_MODEL",
    "EMBEDDING_PROVIDER",
    "EMBEDDING_BASE_URL",
    "EMBEDDING_API_KEY",
    "EMBEDDER_MODEL",
    "HERETEK_API_KEY",
    "JWT_SECRET",
    "API_KEY",
    "QDRANT_HOST",
    "QDRANT_PORT",
    "QDRANT_URL",
    "ENVIRONMENT",
]


# =============================================================================
# FIXTURES
# =============================================================================

@pytest.fixture
def compose_project() -> str:
    """
    Return a unique docker compose project name.

    Uses a short UUID suffix to avoid port conflicts when multiple
    CI jobs run concurrently (each gets its own project name + network).
    """
    return f"heretek-swarm-e2e-{uuid.uuid4().hex[:8]}"


@pytest.fixture
def env_file() -> Generator[str, None, None]:
    """
    Create a temporary .env file with safe mock values for all required vars.

    Yields the path to the temp .env file. The file is cleaned up after the
    test regardless of pass/fail.

    IMPORTANT: Do NOT use real API keys in tests. All values are test fixtures.
    """
    env_content = "\n".join(
        f"{var}=test-key-000" for var in REQUIRED_ENV_VARS
    )
    # Add non-required vars that have defaults in compose
    env_content += "\nENVIRONMENT=development\n"
    env_content += "EMBEDDING_PROVIDER=openai_compatible\n"
    env_content += "MEM0_POSTGRES_PASSWORD=test-key-000\n"
    env_content += "MEM0_LLM_PROVIDER=openai\n"
    env_content += "MEM0_LLM_BASE_URL=https://api.minimax.io/v1\n"
    env_content += "MEM0_LLM_MODEL=MiniMax-M2.7\n"

    # Write to a temp file in the project root so docker compose finds it
    with tempfile.NamedTemporaryFile(
        mode="w",
        suffix=".env",
        dir=str(Path(__file__).parent.parent.parent),
        delete=False,
    ) as f:
        f.write(env_content)
        env_path = f.name

    yield env_path

    # Cleanup regardless of test outcome
    try:
        os.unlink(env_path)
    except OSError:
        pass


@pytest.fixture
def stack_cleanup(compose_project: str) -> Generator[None, None, None]:
    """
    Yields control to the test, then tears down the docker compose stack.

    Runs `docker compose -p <project> down -v --remove-orphans` in a finally:
    block so the stack is always cleaned up even if the test fails or raises.

    Usage:
        def test_something(stack_cleanup, compose_project, env_file):
            # stack is up
            yield
            # teardown happens automatically here
    """
    yield

    # Teardown after test (or after failure)
    subprocess.run(
        ["docker", "compose", "-p", compose_project, "down", "-v", "--remove-orphans"],
        capture_output=True,
    )