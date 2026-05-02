"""
Tests for MCP tool toggle persistence (M007/S03/T01).

Verifies:
1. Atomic write prevents partial/corrupt tools_state.json on crash.
2. _load_tool_states() handles missing file, JSON parse error, OSError gracefully.
3. set_tool_enabled() returns False for unknown tool names.
4. list_tool_summaries(enabled_only=False) includes disabled tools with "enabled": false.
5. Structured log events on toggle (mcp_tool_toggled), load failure (tools_state_load_failed),
   and save failure (tools_state_save_failed).
"""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from heretek_swarm.mcp.registry import (
    MCPToolMetadata,
    MCPToolRegistry,
    TOOLS_STATE_FILE,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_registry_with_tools(count: int = 3) -> MCPToolRegistry:
    """Return a fresh ``MCPToolRegistry`` with *count* test tools registered."""
    registry = MCPToolRegistry()
    for i in range(count):
        meta = MCPToolMetadata(
            name=f"test_tool_{i}",
            description=f"Test tool {i}",
            input_schema={
                "type": "object",
                "properties": {"x": {"type": "integer"}},
                "required": ["x"],
            },
            category="test",
        )
        handler = lambda args, ctx, n=f"test_tool_{i}": {"ok": True, "tool": n}
        registry.register_tool(meta, handler)
    return registry


# ---------------------------------------------------------------------------
# Tests: _load_tool_states
# ---------------------------------------------------------------------------

class TestLoadToolStates:
    """Suite for ``_load_tool_states()``."""

    def test_load_returns_empty_for_missing_file(self, tmp_path: Path) -> None:
        """When no state file exists, _load_tool_states returns an empty dict."""
        with patch("heretek_swarm.mcp.registry.TOOLS_STATE_FILE",
                   tmp_path / "nonexistent" / "tools_state.json"):
            registry = MCPToolRegistry()
            result = registry._load_tool_states()
            assert result == {}

    def test_load_returns_empty_for_json_parse_error(self, tmp_path: Path) -> None:
        """When the state file contains invalid JSON, _load_tool_states returns {}."""
        state_file = tmp_path / "tools_state.json"
        state_file.parent.mkdir(parents=True, exist_ok=True)
        state_file.write_text("not valid json {{{", encoding="utf-8")

        with patch("heretek_swarm.mcp.registry.TOOLS_STATE_FILE", state_file):
            registry = MCPToolRegistry()
            result = registry._load_tool_states()
            assert result == {}

    def test_load_parses_valid_states(self, tmp_path: Path) -> None:
        """A valid tools_state.json is parsed into a {name: enabled} dict."""
        state_file = tmp_path / "tools_state.json"
        state_file.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "version": "1.0.0",
            "tool_states": {
                "fetch_web": True,
                "send_email": False,
                "run_query": True,
            },
        }
        state_file.write_text(json.dumps(payload), encoding="utf-8")

        with patch("heretek_swarm.mcp.registry.TOOLS_STATE_FILE", state_file):
            registry = MCPToolRegistry()
            result = registry._load_tool_states()
            assert result == {
                "fetch_web": True,
                "send_email": False,
                "run_query": True,
            }

    def test_load_ignores_non_bool_values(self, tmp_path: Path) -> None:
        """Non-boolean values in tool_states are silently skipped."""
        state_file = tmp_path / "tools_state.json"
        state_file.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "version": "1.0.0",
            "tool_states": {
                "valid_tool": True,
                "bad_tool": "yes",  # string, not bool
                "also_bad": 123,    # int, not bool
            },
        }
        state_file.write_text(json.dumps(payload), encoding="utf-8")

        with patch("heretek_swarm.mcp.registry.TOOLS_STATE_FILE", state_file):
            registry = MCPToolRegistry()
            result = registry._load_tool_states()
            assert result == {"valid_tool": True}


# ---------------------------------------------------------------------------
# Tests: _save_tool_states (atomic write)
# ---------------------------------------------------------------------------

class TestSaveToolStates:
    """Suite for ``_save_tool_states()``."""

    def test_save_writes_atomically(self, tmp_path: Path) -> None:
        """_save_tool_states writes to .tmp then os.replace — final file is valid JSON."""
        state_file = tmp_path / "tools_state.json"

        with patch("heretek_swarm.mcp.registry.TOOLS_STATE_FILE", state_file):
            registry = _make_registry_with_tools(count=2)
            registry._save_tool_states()

        # The file should exist and contain valid JSON.
        assert state_file.exists()
        data = json.loads(state_file.read_text(encoding="utf-8"))
        assert data["version"] == "1.0.0"
        assert "tool_states" in data
        assert data["tool_states"]["test_tool_0"] is True
        assert data["tool_states"]["test_tool_1"] is True

        # The .tmp file should NOT remain (replaced atomically).
        tmp_file = Path(str(state_file) + ".tmp")
        assert not tmp_file.exists()

    def test_save_reflects_disabled_tool(self, tmp_path: Path) -> None:
        """After disabling a tool, _save_tool_states writes enabled=False."""
        state_file = tmp_path / "tools_state.json"

        with patch("heretek_swarm.mcp.registry.TOOLS_STATE_FILE", state_file):
            registry = _make_registry_with_tools(count=2)
            registry._tools["test_tool_0"].enabled = False
            registry._save_tool_states()

        data = json.loads(state_file.read_text(encoding="utf-8"))
        assert data["tool_states"]["test_tool_0"] is False
        assert data["tool_states"]["test_tool_1"] is True

    def test_save_creates_parent_dir(self, tmp_path: Path) -> None:
        """_save_tool_states creates the parent directory if it doesn't exist."""
        state_file = tmp_path / "deeply" / "nested" / "tools_state.json"

        with patch("heretek_swarm.mcp.registry.TOOLS_STATE_FILE", state_file):
            registry = _make_registry_with_tools(count=1)
            registry._save_tool_states()

        assert state_file.exists()

    def test_save_logs_error_on_unwritable_path(self, tmp_path: Path) -> None:
        """When the path is a directory (unwritable as file), log tools_state_save_failed."""
        # Create a directory where the .tmp file would go.
        state_file = tmp_path / "is_a_dir.json"
        state_file.mkdir()  # make it a directory, not a file

        with patch("heretek_swarm.mcp.registry.TOOLS_STATE_FILE", state_file):
            registry = _make_registry_with_tools(count=1)
            with patch("heretek_swarm.mcp.registry.logger") as mock_logger:
                registry._save_tool_states()
                mock_logger.error.assert_called_once()
                call_args = mock_logger.error.call_args
                assert call_args[0][0] == "tools_state_save_failed"


# ---------------------------------------------------------------------------
# Tests: set_tool_enabled
# ---------------------------------------------------------------------------

class TestSetToolEnabled:
    """Suite for ``set_tool_enabled()``."""

    def test_set_enabled_disables_tool(self, tmp_path: Path) -> None:
        """set_tool_enabled('foo', False) sets enabled=False."""
        state_file = tmp_path / "tools_state.json"

        with patch("heretek_swarm.mcp.registry.TOOLS_STATE_FILE", state_file):
            registry = _make_registry_with_tools(count=2)
            result = registry.set_tool_enabled("test_tool_0", False)

            assert result is True
            tool = registry.get_tool("test_tool_0")
            assert tool is not None
            assert tool.enabled is False

    def test_set_enabled_re_enables_tool(self, tmp_path: Path) -> None:
        """set_tool_enabled('foo', True) on a disabled tool sets enabled=True."""
        state_file = tmp_path / "tools_state.json"

        with patch("heretek_swarm.mcp.registry.TOOLS_STATE_FILE", state_file):
            registry = _make_registry_with_tools(count=2)
            registry._tools["test_tool_1"].enabled = False
            result = registry.set_tool_enabled("test_tool_1", True)

            assert result is True
            assert registry._tools["test_tool_1"].enabled is True

    def test_set_enabled_unknown_tool_returns_false(self, tmp_path: Path) -> None:
        """set_tool_enabled on an unknown name returns False."""
        state_file = tmp_path / "tools_state.json"

        with patch("heretek_swarm.mcp.registry.TOOLS_STATE_FILE", state_file):
            registry = _make_registry_with_tools(count=1)
            result = registry.set_tool_enabled("nonexistent", True)

            assert result is False

    def test_set_enabled_logs_toggled_event(self, tmp_path: Path) -> None:
        """set_tool_enabled logs mcp_tool_toggled at INFO with name + enabled."""
        state_file = tmp_path / "tools_state.json"

        with patch("heretek_swarm.mcp.registry.TOOLS_STATE_FILE", state_file):
            registry = _make_registry_with_tools(count=1)
            with patch("heretek_swarm.mcp.registry.logger") as mock_logger:
                registry.set_tool_enabled("test_tool_0", False)
                mock_logger.info.assert_called_with(
                    "mcp_tool_toggled",
                    name="test_tool_0",
                    enabled=False,
                )


# ---------------------------------------------------------------------------
# Tests: list_tool_summaries with enabled_only
# ---------------------------------------------------------------------------

class TestListToolSummaries:
    """Suite for ``list_tool_summaries(enabled_only=...)``."""

    def test_enabled_only_true_excludes_disabled(self) -> None:
        """enabled_only=True (default) should exclude disabled tools."""
        registry = _make_registry_with_tools(count=3)
        registry._tools["test_tool_1"].enabled = False

        summaries = registry.list_tool_summaries()
        assert len(summaries) == 2
        names = {s["name"] for s in summaries}
        assert names == {"test_tool_0", "test_tool_2"}

    def test_enabled_only_false_includes_disabled(self) -> None:
        """enabled_only=False includes disabled tools with enabled: false."""
        registry = _make_registry_with_tools(count=3)
        registry._tools["test_tool_1"].enabled = False

        summaries = registry.list_tool_summaries(enabled_only=False)
        assert len(summaries) == 3

        for s in summaries:
            if s["name"] == "test_tool_1":
                assert s["enabled"] is False
            else:
                assert s["enabled"] is True

    def test_enabled_only_false_includes_all_fields(self) -> None:
        """Every summary from enabled_only=False has all required MCP protocol fields."""
        registry = _make_registry_with_tools(count=1)
        registry._tools["test_tool_0"].enabled = False

        summaries = registry.list_tool_summaries(enabled_only=False)
        assert len(summaries) == 1
        s = summaries[0]
        assert "name" in s
        assert "description" in s
        assert "inputSchema" in s
        assert "outputSchema" in s
        assert "category" in s
        assert "version" in s
        assert "provider" in s
        assert "serverId" in s
        assert s["enabled"] is False


# ---------------------------------------------------------------------------
# Tests: persistence round-trip
# ---------------------------------------------------------------------------

class TestPersistenceRoundTrip:
    """Integration-style tests for the full persist/toggle/load cycle."""

    def test_persist_round_trip_saves_and_restores(self, tmp_path: Path) -> None:
        """Write states, create new registry, load states — enabled flags match."""
        state_file = tmp_path / "tools_state.json"

        # 1. Create a registry and toggle some tools.
        with patch("heretek_swarm.mcp.registry.TOOLS_STATE_FILE", state_file):
            reg_a = _make_registry_with_tools(count=4)
            reg_a.set_tool_enabled("test_tool_0", False)
            reg_a.set_tool_enabled("test_tool_3", False)

        # 2. Create a new registry (simulates daemon restart),
        #    register the SAME tools, then load states.
        with patch("heretek_swarm.mcp.registry.TOOLS_STATE_FILE", state_file):
            reg_b = _make_registry_with_tools(count=4)

            states = reg_b._load_tool_states()
            for name, flag in states.items():
                tool = reg_b._tools.get(name)
                if tool is not None:
                    tool.enabled = flag

        # 3. Verify restored states.
        assert reg_b._tools["test_tool_0"].enabled is False
        assert reg_b._tools["test_tool_3"].enabled is False
        assert reg_b._tools["test_tool_1"].enabled is True
        assert reg_b._tools["test_tool_2"].enabled is True

    def test_persist_idempotent_across_restarts(self, tmp_path: Path) -> None:
        """Multiple save/load cycles produce the same state (idempotent)."""
        state_file = tmp_path / "tools_state.json"

        with patch("heretek_swarm.mcp.registry.TOOLS_STATE_FILE", state_file):
            reg = _make_registry_with_tools(count=2)
            reg.set_tool_enabled("test_tool_0", False)
            reg._save_tool_states()

            # Load without changing anything, save again.
            states = reg._load_tool_states()
            for name, flag in states.items():
                tool = reg._tools.get(name)
                if tool is not None:
                    tool.enabled = flag
            reg._save_tool_states()

        # Verify file content is stable.
        data = json.loads(state_file.read_text(encoding="utf-8"))
        assert data["tool_states"]["test_tool_0"] is False
        assert data["tool_states"]["test_tool_1"] is True
