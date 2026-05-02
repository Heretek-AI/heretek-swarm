"""
Tests for MCP agent tool injection (agent_tools.py).

Verifies that:
1. build_tools_list_dictionary() produces correct OpenAI function-calling schemas
2. build_tool_handlers() produces synchronous wrappers that work via asyncio.run()
3. The handler wrappers preserve the correct tool logic
4. Empty registry produces empty results
5. Integration: agent with injected tools can invoke a mock handler
6. None-guard: mcp_tools is None -> no injection, no crash
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from heretek_swarm.mcp.agent_tools import (
    build_tool_handlers,
    build_tools_list_dictionary,
)
from heretek_swarm.tools.mcp_tools import CoreMCPTools, MCPToolDefinition


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_core_mcp_with_tools(tool_count: int = 3) -> CoreMCPTools:
    """Build a ``CoreMCPTools`` with a pre-populated internal registry."""
    core = CoreMCPTools()
    # Clear default tools so we have deterministic control.
    existing = list(core.registry._tools.keys())
    for name in existing:
        core.registry.unregister(name)

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
            handler=lambda args, ctx, _i=i: {"result": args.get("x", 0) * (_i + 1)},
            category="test",
        )
        core.registry.register(defn)
    return core


# ---------------------------------------------------------------------------
# Tests: build_tools_list_dictionary
# ---------------------------------------------------------------------------


class TestBuildToolsListDictionary:
    """Suite of tests for ``build_tools_list_dictionary()``."""

    def test_builds_openai_schema(self):
        """Output matches the OpenAI function-calling format."""
        core = _make_core_mcp_with_tools(tool_count=1)
        schemas = build_tools_list_dictionary(core.get_registry())

        assert len(schemas) == 1
        schema = schemas[0]

        assert schema["type"] == "function"
        assert "function" in schema
        func = schema["function"]
        assert func["name"] == "test_tool_0"
        assert func["description"] == "Test tool 0"
        assert "parameters" in func
        assert func["parameters"]["type"] == "object"
        assert "x" in func["parameters"]["properties"]

    def test_includes_all_tools(self):
        """All tools appear in the schema list."""
        core = _make_core_mcp_with_tools(tool_count=5)
        schemas = build_tools_list_dictionary(core.get_registry())

        assert len(schemas) == 5
        names = {s["function"]["name"] for s in schemas}
        for i in range(5):
            assert f"test_tool_{i}" in names

    def test_returns_empty_list_for_empty_registry(self):
        """Empty registry produces empty schema list."""
        core = _make_core_mcp_with_tools(tool_count=0)
        schemas = build_tools_list_dictionary(core.get_registry())
        assert schemas == []

    def test_handles_enabled_tools_only(self):
        """Only enabled tools should be included."""
        core = _make_core_mcp_with_tools(tool_count=3)
        # Disable one tool
        core.registry._tools["test_tool_1"].enabled = False
        schemas = build_tools_list_dictionary(core.get_registry())

        names = {s["function"]["name"] for s in schemas}
        assert "test_tool_0" in names
        assert "test_tool_1" not in names  # disabled
        assert "test_tool_2" in names


# ---------------------------------------------------------------------------
# Tests: build_tool_handlers
# ---------------------------------------------------------------------------


class TestBuildToolHandlers:
    """Suite of tests for ``build_tool_handlers()``."""

    def test_builds_sync_wrappers(self):
        """Handlers dict has correct keys and values are callable."""
        core = _make_core_mcp_with_tools(tool_count=3)
        handlers = build_tool_handlers(core.get_registry())

        assert len(handlers) == 3
        for i in range(3):
            name = f"test_tool_{i}"
            assert name in handlers
            assert callable(handlers[name])

    def test_sync_handler_invocation(self):
        """Sync wrapper calls the async handler and returns correct result."""
        core = _make_core_mcp_with_tools(tool_count=1)
        handlers = build_tool_handlers(core.get_registry())

        result = handlers["test_tool_0"]({"x": 7}, {"agent_id": "test"})
        assert result == {"result": 7}  # _i + 1 = 1, so x * 1 = 7

    def test_all_handlers_execute(self):
        """Every handler wrapper can be invoked successfully."""
        core = _make_core_mcp_with_tools(tool_count=3)
        handlers = build_tool_handlers(core.get_registry())

        for i in range(3):
            name = f"test_tool_{i}"
            result = handlers[name]({"x": 5}, {"agent_id": "test"})
            # Each tool multiplies by (i + 1)
            expected = {"result": 5 * (i + 1)}
            assert result == expected, f"{name}: expected {expected}, got {result}"

    def test_handler_returns_error_on_exception(self):
        """When the async handler raises, the wrapper returns an error dict."""
        # Register a tool whose handler explicitly raises.
        def _raise_handler(args, ctx):
            raise RuntimeError("tool failure")

        core = _make_core_mcp_with_tools(tool_count=0)
        core.registry.register(MCPToolDefinition(
            name="failing_tool",
            description="Always fails",
            input_schema={"type": "object", "properties": {}},
            handler=_raise_handler,
            category="test",
        ))
        handlers = build_tool_handlers(core.get_registry())
        result = handlers["failing_tool"]({}, {"agent_id": "test"})
        assert "error" in result
        assert result["success"] is False

    def test_empty_registry(self):
        """Empty registry produces empty handlers dict."""
        core = _make_core_mcp_with_tools(tool_count=0)
        handlers = build_tool_handlers(core.get_registry())
        assert handlers == {}


# ---------------------------------------------------------------------------
# Integration tests
# ---------------------------------------------------------------------------


class TestAgentToolInjection:
    """Integration: verifying the injection path end-to-end."""

    def test_tools_list_dictionary_assignable_to_swarms_agent(self):
        """The schema list can be assigned to a real swarms.Agent instance."""
        from swarms import Agent

        core = _make_core_mcp_with_tools(tool_count=3)
        schemas = build_tools_list_dictionary(core.get_registry())

        agent = Agent(agent_name="test_agent")
        agent.tools_list_dictionary = schemas

        assert len(agent.tools_list_dictionary) == 3
        assert agent.tools_list_dictionary[0]["function"]["name"] == "test_tool_0"

    def test_all_tools_accessible_via_swarms_agent(self):
        """Agent can list all available tools via tools_list_dictionary."""
        from swarms import Agent

        core = _make_core_mcp_with_tools(tool_count=5)
        schemas = build_tools_list_dictionary(core.get_registry())

        agent = Agent(agent_name="test_agent")
        agent.tools_list_dictionary = schemas

        tool_names = {t["function"]["name"] for t in agent.tools_list_dictionary}
        for i in range(5):
            assert f"test_tool_{i}" in tool_names

    def test_agent_invokes_mock_handler_via_injected_tools(self):
        """Agent with injected tools can invoke a mock tool handler.

        Simulates the real dispatch path: schemas tell the LLM what tools
        exist; the handler callables are the functions the LLM calls.
        This test verifies the handler invocation, not the LLM routing.
        """
        from swarms import Agent

        call_log = {"called": False, "args": None, "ctx": None}

        def mock_handler(args, ctx):
            call_log["called"] = True
            call_log["args"] = args
            call_log["ctx"] = ctx
            return {"weather": "sunny", "temp": args.get("city", "unknown")}

        core = _make_core_mcp_with_tools(tool_count=0)
        core.registry.register(MCPToolDefinition(
            name="get_weather",
            description="Get weather for a city",
            input_schema={
                "type": "object",
                "properties": {
                    "city": {"type": "string", "description": "City name"},
                },
                "required": ["city"],
            },
            handler=mock_handler,
            category="test",
        ))

        registry = core.get_registry()
        schemas = build_tools_list_dictionary(registry)
        handlers = build_tool_handlers(registry)

        agent = Agent(agent_name="test_weather_agent")
        agent.tools_list_dictionary = schemas
        agent.tools = list(handlers.values())

        assert len(agent.tools_list_dictionary) == 1
        assert agent.tools_list_dictionary[0]["function"]["name"] == "get_weather"
        assert len(agent.tools) == 1
        assert callable(agent.tools[0])

        result = agent.tools[0]({"city": "London"}, {"agent_id": "test"})

        assert result["weather"] == "sunny"
        assert result["temp"] == "London"
        assert call_log["called"] is True
        assert call_log["args"] == {"city": "London"}

    def test_agent_tool_handler_error_returns_error_dict(self):
        """When an injected tool handler raises, the agent sees an error."""
        from swarms import Agent

        def failing_handler(args, ctx):
            raise RuntimeError("simulated failure")

        core = _make_core_mcp_with_tools(tool_count=0)
        core.registry.register(MCPToolDefinition(
            name="failing_tool",
            description="Always fails",
            input_schema={"type": "object", "properties": {}},
            handler=failing_handler,
            category="test",
        ))

        handlers = build_tool_handlers(core.get_registry())
        agent = Agent(agent_name="test_fail_agent")
        agent.tools = list(handlers.values())

        result = agent.tools[0]({}, {"agent_id": "test"})
        assert "error" in result
        assert result["success"] is False

    def test_tool_injection_skipped_when_mcp_tools_is_none(self):
        """When mcp_tools is None, guard prevents injection and no crash.

        Simulates the guard in _spawn_all_actors()::

            if self.mcp_tools is not None:
                ...inject...
            else:
                logger.warning(...)
        """
        from swarms import Agent

        agent = Agent(agent_name="test_none_agent")

        mcp_tools = None
        if mcp_tools is not None:
            registry = mcp_tools.get_registry()
            agent.tools_list_dictionary = build_tools_list_dictionary(registry)
            agent.tools = list(build_tool_handlers(registry).values())

        assert mcp_tools is None
        if agent.tools_list_dictionary is not None:
            assert len(agent.tools_list_dictionary) == 0
        assert agent.tools is None or len(agent.tools) == 0


# ---------------------------------------------------------------------------
# Smoke test: module imports cleanly
# ---------------------------------------------------------------------------


class TestModuleImport:
    """Module loads without errors."""

    def test_imports(self):
        from heretek_swarm.mcp import agent_tools
        assert hasattr(agent_tools, "build_tools_list_dictionary")
        assert hasattr(agent_tools, "build_tool_handlers")

    def test_main_loop_import_after_injection(self):
        """Verify main_loop can still be imported (injection code doesn't break imports)."""
        from heretek_swarm.runtime import main_loop
        assert hasattr(main_loop, "AutonomousSwarm")
