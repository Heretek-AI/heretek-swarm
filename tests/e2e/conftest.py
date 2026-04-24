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

# Register M029-specific fixtures (docker bringup + api_client for workflow tests)
pytest_plugins = ["tests.e2e.conftest_m029"]


# =============================================================================
# REQUIRED ENV VARS (from .env.example)
# =============================================================================
# The following env vars are referenced by docker-compose.yml and must be
# present in the .env file for the stack to start:
#
# POSTGRES_PASSWORD, OPENAI_API_KEY, OPENAI_BASE_URL, LLM_MODEL,
# EMBEDDING_BASE_URL, EMBBEDDING_API_KEY, HERETEK_API_KEY, JWT_SECRET,
# API_KEY, QDRANT_HOST, QDRANT_PORT, QDRANT_URL, HERETEK_NATS_URL
#
# Additional vars used by specific services:
# EMBEDDING_PROVIDER, EMBEDDER_MODEL, ENVIRONMENT, MEM0_POSTGRES_PASSWORD,
# MEM0_LLM_PROVIDER, MEM0_LLM_BASE_URL, MEM0_LLM_API_KEY

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
    "HERETEK_NATS_URL",
    "DATABASE_URL",
    "ENVIRONMENT",
]


# =============================================================================
# FIXTURES
# Fixtures (compose_project and env_file defined in tests/e2e/conftest_m029.py)
# This file provides REQUIRED_ENV_VARS for the M029 fixtures via pytest_plugins.