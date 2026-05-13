"""
Tests for the MCP registry bridge (tools/mcp_tools ↔ mcp/registry).

Verifies that:
1. Bridge reads tool definitions from CoreMCPTools' internal registry
2. Each tool is converted to MCPToolMetadata and registered in the mcp/ registry
3. The handler calling convention is preserved
4. The bridge is idempotent (duplicate registrations are skipped)
5. None-guard: bridge handles missing handler gracefully
"""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import patch

import pytest

from heretek_swarm.mcp.bridge import sync_mcp_registries
from heretek_swarm.mcp.registry import MCPToolRegistry
from heretek_swarm.tools.mcp_tools import CoreMCPTools

if TYPE_CHECKING:
    from pathlib import Path

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_core_mcp_with_tools(tool_count: int = 3) -> CoreMCPTools:
    """Build a ``CoreMCPTools`` with a pre-populated internal registry.

    The internal MCPToolRegistry is loaded with *tool_count* fake tool
    definitions so the bridge has something to sync.
    """
    from heretek_swarm.tools.mcp_tools import MCPToolDefinition

    core = CoreMCPTools()
    # Clear the default tools that _register_default_tools() added
    # so we have deterministic control over tool count.
    existing_tools = list(core.registry._tools.keys())
    for name in existing_tools:
        core.registry.unregister(name)

    # Fill with controlled test tools.
    for i in range(tool_count):
        name = f"test_tool_{i}"
        defn = MCPToolDefinition(
            name=name,
            description=f"Test tool {i}",
            input_schema={
                "type": "object",
                "properties": {
                    "x": {"type": "integer", "description": "The X value"},
                },
                "required": ["x"],
            },
            handler=lambda args, ctx: {"result": args.get("x", 0) * 2},  # noqa: ARG005
            category="test",
        )
        core.registry.register(defn)
    return core


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def _clear_mcp_registry(tmp_path: Path) -> None:
    """Autouse fixture — clear the global mcp/ registry before each test.

    Also patches ``TOOLS_STATE_FILE`` to a non-existent path in tmp so
    the bridge's persisted-state loading doesn't pick up real user state
    from disk.
    """
    from heretek_swarm.mcp.server import set_registry

    set_registry(MCPToolRegistry())
    with patch(
        "heretek_swarm.mcp.registry.TOOLS_STATE_FILE", tmp_path / "nonexistent" / "tools_state.json"
    ):
        yield


class TestMcpBridge:
    """Suite of tests for ``sync_mcp_registries()``."""

    def test_bridge_copies_tools_to_mcp_registry(self) -> None:
        """After bridge, the mcp/ registry contains all tools from CoreMCPTools."""
        core = _make_core_mcp_with_tools(tool_count=5)

        # Precondition: mcp registry starts empty.
        from heretek_swarm.mcp.server import get_registry

        mcp_reg = get_registry()
        old_all = mcp_reg.list_tools()
        assert len(old_all) == 0, "mcp/ registry should start empty"

        # Act
        bridged = sync_mcp_registries(core)

        # Assert
        assert bridged == 5, "Expected all 5 tools to be bridged"
        mcp_tools = mcp_reg.list_tools()
        assert len(mcp_tools) == 5
        names = {t.name for t in mcp_tools}
        for i in range(5):
            assert f"test_tool_{i}" in names

    def test_bridge_preserves_handler_calling_convention(self) -> None:
        """The handler registered in mcp/ registry can be invoked and
        produces the same result as invoking it via CoreMCPTools' registry."""
        core = _make_core_mcp_with_tools(tool_count=1)
        sync_mcp_registries(core)

        from heretek_swarm.mcp.server import get_registry

        mcp_reg = get_registry()

        # Invoke the bridged tool via mcp/ registry.
        result = mcp_reg.invoke_sync(
            "test_tool_0",
            {"x": 7},
            {"agent_id": "test"},
        )

        assert result["success"] is True
        assert result["result"] == {"result": 14}

    def test_bridge_is_idempotent(self) -> None:
        """Calling the bridge twice does not duplicate tools."""
        core = _make_core_mcp_with_tools(tool_count=3)

        # First bridge
        first = sync_mcp_registries(core)
        assert first == 3

        from heretek_swarm.mcp.server import get_registry

        mcp_reg = get_registry()
        tools_first = mcp_reg.list_tools()
        assert len(tools_first) == 3

        # Second bridge (duplicate registration should be skipped)
        second = sync_mcp_registries(core)
        assert second < 3  # some tools should be skipped as duplicates

        tools_second = mcp_reg.list_tools()
        assert len(tools_second) == 3, "Tool count should not increase"

    def test_bridge_handles_empty_tools(self) -> None:
        """Bridge with an empty CoreMCPTools returns 0 and does not crash."""
        core = _make_core_mcp_with_tools(tool_count=0)
        bridged = sync_mcp_registries(core)
        assert bridged == 0

    def test_bridge_handles_none_core_tools(self) -> None:
        """Bridge gracefully handles None input (no crash)."""
        bridged = sync_mcp_registries(None)
        assert bridged == 0

    def test_bridge_syncs_into_http_registry(self) -> None:
        """After bridge, the HTTP-facing get_registry() tools list matches
        the CoreMCPTools registry."""
        core = _make_core_mcp_with_tools(tool_count=4)
        sync_mcp_registries(core)

        from heretek_swarm.mcp.server import get_registry

        mcp_reg = get_registry()

        # Tool names should be accessible via HTTP endpoints.
        for i in range(4):
            tool = mcp_reg.get_tool(f"test_tool_{i}")
            assert tool is not None, f"test_tool_{i} should exist in mcp registry"
            assert tool.name == f"test_tool_{i}"

    def test_bridge_list_tool_summaries_matches_tools_layer(self) -> None:
        """After bridge, list_tool_summaries() returns entries whose names
        match the CoreMCPTools registry tool names."""
        core = _make_core_mcp_with_tools(tool_count=3)
        # Record the tool names from the tools-layer side.
        tools_layer_names = {t.get("name") for t in core.get_registry().list_tools()}

        sync_mcp_registries(core)

        from heretek_swarm.mcp.server import get_registry

        mcp_reg = get_registry()
        summaries = mcp_reg.list_tool_summaries()

        # Every bridged tool appears in the summaries.
        summary_names = {s["name"] for s in summaries}
        for name in tools_layer_names:
            assert name in summary_names, f"Tool {name!r} should appear in list_tool_summaries"

        # Every summary has the required MCP protocol fields.
        for s in summaries:
            assert "name" in s
            assert "description" in s
            assert "inputSchema" in s
            assert "enabled" in s

    def test_bridge_health_total_tools_reflects_bridged_tools(self) -> None:
        """After bridge, the HTTP health endpoint's total_tools reflects
        the correct count (visible at registry level — the endpoint reads
        get_registry().list_tools())."""
        core = _make_core_mcp_with_tools(tool_count=4)
        sync_mcp_registries(core)

        from heretek_swarm.mcp.server import get_registry

        mcp_reg = get_registry()
        all_tools = mcp_reg.list_tools()
        health_count = len(all_tools)

        assert health_count == 4, f"Expected 4 tools in health/total_tools, got {health_count}"
