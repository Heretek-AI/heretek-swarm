"""Cross-slice integration test: MCP tool injection + model routing.

Verifies that S01 (complexity-based routing via AgentModelRouter / ModelGarage)
and S02 (MCP tool injection into swarms_agent) compose correctly.

Key question: does an agent with complexity-based routing ALSO have MCP tools
available on its swarms_agent after both slices' code paths execute?

The answer is structural: run_with_llm() routes through ModelGarage when
available, and MCP tools are injected onto swarms_agent.tools /
swarms_agent.tools_list_dictionary post-spawn. The test below proves
both code paths execute correctly on the same agent.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

from heretek_swarm.actors.base import AgentActor
from heretek_swarm.llm.model_garage import LLMResponse
from heretek_swarm.mcp.agent_tools import (
    build_tool_handlers,
    build_tools_list_dictionary,
)
from heretek_swarm.routing.model_router import AgentModelRouter
from heretek_swarm.tools.mcp_tools import CoreMCPTools, MCPToolDefinition

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_garage() -> MagicMock:
    """Build a mock ModelGarage with two providers for SIMPLE vs COMPLEX routing."""
    garage = MagicMock()
    garage.list_providers.return_value = [
        {
            "id": "fast-provider",
            "baseUrl": "http://localhost:11434",
            "apiKey": "",
            "models": ["llama3.1", "gemini-flash"],
            "priority": 1,
            "health_status": "healthy",
        },
        {
            "id": "powerful-provider",
            "baseUrl": "https://api.anthropic.com",
            "apiKey": "sk-test",
            "models": ["claude-sonnet-4-20250514", "claude-opus-4-20250514"],
            "priority": 10,
            "health_status": "healthy",
        },
    ]

    async def _complete(messages, model, provider_id, **kwargs) -> LLMResponse:
        return LLMResponse(
            content=f"response from {provider_id} using {model}",
            model=model,
            provider=provider_id,
            usage={"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15},
            latency_ms=50.0,
        )

    garage.complete = AsyncMock(side_effect=_complete)
    return garage


def _make_swarms_agent() -> MagicMock:
    """Build a mock swarms Agent whose run() returns a fixed string."""
    agent = MagicMock()
    agent.agent_name = "test-agent"
    agent.run.return_value = "swarms fallback response"
    return agent


def _make_core_mcp_with_weather_tool() -> CoreMCPTools:
    """Build a CoreMCPTools with a single 'get_weather' tool.

    The handler records calls in a call_log so we can verify invocation.
    """
    call_log: dict = {"calls": []}

    def weather_handler(args, ctx):
        city = args.get("city", "unknown")
        call_log["calls"].append({"city": city, "ctx_agent": ctx.get("agent_id")})
        return {"weather": "sunny", "temp": 22, "city": city}

    core = CoreMCPTools()
    # Clear default tools for deterministic test state
    existing = list(core.registry._tools.keys())
    for name in existing:
        core.registry.unregister(name)

    core.registry.register(MCPToolDefinition(
        name="get_weather",
        description="Get the current weather for a city",
        input_schema={
            "type": "object",
            "properties": {
                "city": {"type": "string", "description": "City name"},
            },
            "required": ["city"],
        },
        handler=weather_handler,
        category="test",
    ))

    # Attach the call_log to the instance for test assertions
    core._call_log = call_log  # type: ignore[attr-defined]
    return core


# ---------------------------------------------------------------------------
# Test: cross-slice integration
# ---------------------------------------------------------------------------


class TestCrossSliceMCPRoutingIntegration:
    """Proves that S01 routing + S02 MCP tool injection compose correctly."""

    @staticmethod
    def _inject_swarms_agent_for_test(
        actor: AgentActor,
        tool_schemas: list | None = None,
        tool_handlers: dict | None = None,
    ) -> MagicMock:
        """Match the real main_loop pattern: create a swarms_agent, assign
        to actor.swarms_agent, then inject MCP tools if provided.

        Uses MagicMock (same pattern as test_actor_routing.py) to avoid
        hitting a real LLM during swarms_agent.run() fallback.
        """
        sa = _make_swarms_agent()
        actor.swarms_agent = sa
        if tool_schemas:
            actor.swarms_agent.tools_list_dictionary = tool_schemas
        if tool_handlers:
            actor.swarms_agent.tools = list(tool_handlers.values())
        return sa

    @staticmethod
    async def test_garage_routing_with_mcp_tools_injected() -> None:
        """An agent with a garage-wired router and injected MCP tools can
        route through the garage while the swarms_agent carries tools.

        This tests the composed state after both slices' code paths run:
        - S01: AgentModelRouter + ModelGarage -> run_with_llm routes through garage
        - S02: MCP tool schemas + handlers injected into swarms_agent
        """
        # -- Arrange ------------------------------------------------------
        garage = _make_garage()
        core_mcp = _make_core_mcp_with_weather_tool()

        router = AgentModelRouter(
            agent_id="cross-slice-agent",
            model_garage=garage,
        )

        # Build what _spawn_all_actors() injects post-spawn
        mcp_registry = core_mcp.get_registry()
        tool_schemas = build_tools_list_dictionary(mcp_registry)
        tool_handlers = build_tool_handlers(mcp_registry)

        # Create agent and inject both the router (S01) and MCP tools (S02)
        actor = AgentActor(
            agent_id="cross-slice-agent",
            model_router=router,
        )
        TestCrossSliceMCPRoutingIntegration._inject_swarms_agent_for_test(
            actor, tool_schemas, tool_handlers,
        )

        # -- Act ----------------------------------------------------------
        # S01 path: run_with_llm routes through garage
        simple_response = await actor.run_with_llm("format this text")
        complex_response = await actor.run_with_llm(
            "design and analyze and evaluate the tradeoffs"
        )

        # S02 path: tool schemas and handlers are available on swarms_agent
        tool_names = {
            t["function"]["name"] for t in actor.swarms_agent.tools_list_dictionary
        }
        handler_result = actor.swarms_agent.tools[0](
            {"city": "London"}, {"agent_id": "cross-slice-agent"}
        )

        # -- Assert -------------------------------------------------------

        # S01: SIMPLE routes to fast-provider
        assert "fast-provider" in simple_response, (
            f"Expected SIMPLE to route to fast-provider, got {simple_response}"
        )

        # S01: COMPLEX routes to powerful-provider
        assert "powerful-provider" in complex_response, (
            f"Expected COMPLEX to route to powerful-provider, got {complex_response}"
        )

        # S02: Tool schemas are present and correct
        assert "get_weather" in tool_names, (
            f"Expected get_weather tool, got {tool_names}"
        )

        # S02: Handler is callable and returns correct result
        assert handler_result["weather"] == "sunny"
        assert handler_result["city"] == "London"

        # S02: Handler was called with correct args (call_log verification)
        call_log = core_mcp._call_log  # type: ignore[attr-defined]
        assert len(call_log["calls"]) == 1
        assert call_log["calls"][0]["city"] == "London"

    @staticmethod
    async def test_mcp_tools_survive_garage_route_via_run_with_llm() -> None:
        """MCP tool schemas and handlers remain intact after run_with_llm
        routes through the garage. The garage path does not mutate or clear
        the swarms_agent's tool configuration."""
        # -- Arrange ------------------------------------------------------
        garage = _make_garage()
        core_mcp = _make_core_mcp_with_weather_tool()

        router = AgentModelRouter(
            agent_id="survival-agent",
            model_garage=garage,
        )

        mcp_registry = core_mcp.get_registry()
        tool_schemas = build_tools_list_dictionary(mcp_registry)
        tool_handlers = build_tool_handlers(mcp_registry)

        actor = AgentActor(
            agent_id="survival-agent",
            model_router=router,
        )
        TestCrossSliceMCPRoutingIntegration._inject_swarms_agent_for_test(
            actor, tool_schemas, tool_handlers,
        )

        # Capture state before routing
        pre_tool_names = {
            t["function"]["name"]
            for t in actor.swarms_agent.tools_list_dictionary
        }
        pre_handler_count = len(actor.swarms_agent.tools)

        # -- Act: route through garage several times ----------------------
        for _ in range(3):
            await actor.run_with_llm("format this")

        # -- Assert: tools are unchanged ----------------------------------
        post_tool_names = {
            t["function"]["name"]
            for t in actor.swarms_agent.tools_list_dictionary
        }
        post_handler_count = len(actor.swarms_agent.tools)

        assert pre_tool_names == post_tool_names, "Tool schemas mutated by routing"
        assert pre_handler_count == post_handler_count, "Tool handlers mutated by routing"
        assert "get_weather" in post_tool_names
        assert post_handler_count == 1

    @staticmethod
    async def test_fallback_swarms_path_still_has_tools() -> None:
        """When run_with_llm falls back to swarms_agent.run() (no providers),
        the MCP tools injected by S02 are still available on the agent."""
        # -- Arrange ------------------------------------------------------
        core_mcp = _make_core_mcp_with_weather_tool()
        mcp_registry = core_mcp.get_registry()
        tool_schemas = build_tools_list_dictionary(mcp_registry)

        # Router with no garage and no standalone providers -> falls to swarms
        router = AgentModelRouter(agent_id="fallback-agent")

        actor = AgentActor(
            agent_id="fallback-agent",
            model_router=router,
        )

        # Create a mock swarms_agent so run_with_llm's fallback works (S02 tools injected)
        TestCrossSliceMCPRoutingIntegration._inject_swarms_agent_for_test(
            actor, tool_schemas,
        )

        # -- Act ----------------------------------------------------------
        response = await actor.run_with_llm("hello")

        # -- Assert -------------------------------------------------------
        assert response == "swarms fallback response"
        assert len(actor.swarms_agent.tools_list_dictionary) == 1
        assert (
            actor.swarms_agent.tools_list_dictionary[0]["function"]["name"]
            == "get_weather"
        )
