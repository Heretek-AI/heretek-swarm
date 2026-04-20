"""Pytest fixtures for audit tests."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from pathlib import Path


@pytest.fixture
def sample_python_file(tmp_path: Path) -> Path:
    """A temporary Python file containing known stub patterns for testing."""
    content = """
def placeholder_handler():
    pass


def empty_dict_return():
    return {}


def none_return():
    return None


def not_implemented():
    raise NotImplementedError


def create_sample_metrics():
    '''This is a test fixture — intentionally excluded from findings.'''
    return {"test": 1}
"""
    p = tmp_path / "sample.py"
    p.write_text(content, encoding="utf-8")
    return p


@pytest.fixture
def sample_typescript_file(tmp_path: Path) -> Path:
    """A temporary TypeScript file containing known stub patterns for testing."""
    content = """
function timerLoop(): void {
    setInterval(() => {
        console.log("tick");
    }, 1000);
}

def generateRandom():
    return String(Math.random())
"""
    p = tmp_path / "sample.ts"
    p.write_text(content, encoding="utf-8")
    return p


@pytest.fixture
def audit_report_dir(tmp_path: Path) -> Path:
    """A temporary directory for audit report output."""
    d = tmp_path / "reports"
    d.mkdir()
    return d
