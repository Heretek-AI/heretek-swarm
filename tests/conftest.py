"""Pytest root conftest for Heretek Swarm backend tests.

Adds the backend/ package to sys.path so imports work from the repo root.
Provides foundational fixtures for all test modules.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent
BACKEND_SRC = REPO_ROOT / "backend"

if str(BACKEND_SRC) not in sys.path:
    sys.path.insert(0, str(BACKEND_SRC))


@pytest.fixture
def repo_root() -> Path:
    return REPO_ROOT