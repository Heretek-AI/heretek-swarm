"""Tests for the Phase 3D official MCP SDK spike."""

from mcp.server import Server

from heretek_swarm.mcp.official_sdk_spike import run_dry_spike


def test_dry_spike_passes():
    """The official MCP SDK cutover API surface is valid."""
    run_dry_spike()


def test_server_class_importable():
    """mcp.server.Server is the migration target."""
    assert Server is not None
    assert callable(Server)
