"""Packaging smoke tests.

Verify that the package installs correctly, the version attribute is
accessible, the CLI entry point is importable, and the distribution
metadata is consistent.
"""

from __future__ import annotations

import importlib.metadata


def test_version_accessible() -> None:
    """The top-level package exposes __version__ matching pyproject.toml."""
    import heretek_swarm

    assert hasattr(heretek_swarm, "__version__"), "heretek_swarm.__version__ missing"
    assert heretek_swarm.__version__ == "0.2.0"


def test_cli_importable() -> None:
    """The CLI click group is importable from heretek_swarm.cli."""
    from heretek_swarm.cli import cli

    assert callable(cli)


def test_main_module_importable() -> None:
    """The __main__ module exposes cli_main for `python -m heretek_swarm`."""
    from heretek_swarm.__main__ import cli_main

    assert callable(cli_main)


def test_package_metadata() -> None:
    """importlib.metadata returns the version declared in pyproject.toml."""
    version = importlib.metadata.version("heretek-swarm")
    assert version == "0.2.0", f"Expected 0.2.0, got {version}"
