"""Integration tests for agent-level model routing paths.

Verifies that AgentModelRouter wires correctly through AgentActor's
``run_with_llm()`` for all 5 routing scenarios:

1. No providers → fallback to ``swarms_agent.run()``
2. Mock providers in ModelGarage → routing picks correct provider
3. SIMPLE vs COMPLEX tasks route to different providers
4. Fallback chain works when primary provider is unhealthy
5. Error recovery: empty provider list, all unhealthy → graceful fallback

These are *true integration tests* of the run_with_llm dispatch path. The
mock ModelGarage surfaces the same ``list_providers()`` / ``complete()``
contract that the real garage does, but without network. The mock swarms
Agent returns a preset string without hitting an LLM.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from heretek_swarm.actors.base import AgentActor
from heretek_swarm.llm.model_garage import LLMResponse
from heretek_swarm.routing.model_router import AgentModelRouter

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_garage(providers: list[dict]) -> MagicMock:
    """Build a mock ModelGarage that returns the given provider dicts.

    Each provider dict has the same shape as
    ``ProviderConfig.to_dict()`` — the keys ``_get_providers()`` reads
    are ``baseUrl``, ``id``, ``apiKey``, ``models``, ``priority``,
    ``health_status``.

    The mock's ``complete()`` returns an ``LLMResponse`` that embeds
    the provider_id and model so callers can verify routing decisions
    from the response string.
    """
    garage = MagicMock()
    garage.list_providers.return_value = providers

    async def _complete(messages, model, provider_id, **kwargs) -> LLMResponse:
        return LLMResponse(
            content=f"response from {provider_id} using {model}",
            model=model,
            provider="ollama",
            usage={"prompt_tokens": 10, "completion_tokens": 32, "total_tokens": 42},
            latency_ms=100.0,
        )

    garage.complete = AsyncMock(side_effect=_complete)
    return garage


def _make_swarms_agent() -> MagicMock:
    """Build a mock swarms Agent whose ``run()`` returns a fixed string."""
    agent = MagicMock()
    agent.agent_name = "test-agent"
    agent.run.return_value = "swarms fallback response"
    return agent


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestAgentRoutingIntegration:
    """Exercises ``AgentActor.run_with_llm()`` through every routing path."""

    # -- Scenario 1: no providers → fallback to swarms_agent -------------

    @staticmethod
    async def test_no_providers_falls_to_swarms() -> None:
        """An agent with **no providers whatsoever** falls back to
        ``swarms_agent.run()``."""
        swarms_agent = _make_swarms_agent()
        actor = AgentActor(
            agent_id="no-provider-agent",
            swarms_agent=swarms_agent,
        )
        response = await actor.run_with_llm("Hello, what can you do?")
        assert response == "swarms fallback response"
        swarms_agent.run.assert_called_once()

    @staticmethod
    async def test_no_providers_no_swarms_raises() -> None:
        """When there is neither a swarms_agent nor registered providers,
        ``run_with_llm`` raises ``RuntimeError``."""
        actor = AgentActor(agent_id="no-llm-agent")
        with pytest.raises(RuntimeError, match="No LLM path available"):
            await actor.run_with_llm("Hello")

    # -- Scenario 2: ModelGarage with providers → correct provider -------

    @staticmethod
    async def test_garage_routing_picks_provider() -> None:
        """When ModelGarage has healthy providers, ``run_with_llm`` routes
        through the router and delegates to ``garage.complete()`` with the
        chosen provider and model."""
        swarms_agent = _make_swarms_agent()
        garage = _make_garage(
            [
                {
                    "id": "ollama-local",
                    "baseUrl": "http://localhost:11434",
                    "apiKey": "",
                    "models": ["llama3.1", "llama3.2"],
                    "priority": 1,
                    "health_status": "healthy",
                },
            ]
        )

        router = AgentModelRouter(
            agent_id="garage-agent",
            model_garage=garage,
        )
        actor = AgentActor(
            agent_id="garage-agent",
            swarms_agent=swarms_agent,
            model_router=router,
        )

        response = await actor.run_with_llm("format this text")
        assert "ollama-local" in response
        assert "llama3.1" in response

    # -- Scenario 3: SIMPLE vs COMPLEX → different providers -------------

    @staticmethod
    async def test_simple_vs_complex_routes_differently() -> None:
        """SIMPLE and COMPLEX tasks are routed to different providers when
        the preferred-model lists point to different match candidates."""
        swarms_agent = _make_swarms_agent()
        garage = _make_garage(
            [
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
        )

        router = AgentModelRouter(
            agent_id="complexity-agent",
            model_garage=garage,
        )
        actor = AgentActor(
            agent_id="complexity-agent",
            swarms_agent=swarms_agent,
            model_router=router,
        )

        # SIMPLE task: preferred models are ["haiku", "llama3.1", "gemini-flash"]
        # fast-provider has "llama3.1" → match → routes to fast-provider
        simple = await actor.run_with_llm("format this text")
        assert "fast-provider" in simple, (
            f"Expected SIMPLE task to route to fast-provider, got {simple}"
        )

        # COMPLEX task: preferred models are ["opus", "claude-opus", "o1-preview"]
        # powerful-provider has "claude-opus-4-20250514" → "claude-opus" matches → routes to powerful-provider
        complex_task = "design and analyze and evaluate the tradeoffs"
        complex_resp = await actor.run_with_llm(complex_task)
        assert "powerful-provider" in complex_resp, (
            f"Expected COMPLEX task to route to powerful-provider, got {complex_resp}"
        )

    # -- Scenario 4: unhealthy provider falls back -----------------------

    @staticmethod
    async def test_unhealthy_provider_falls_back() -> None:
        """When the highest-priority provider is unhealthy, the router
        skips it and picks the next healthy one."""
        swarms_agent = _make_swarms_agent()
        garage = _make_garage(
            [
                {
                    "id": "dead-provider",
                    "baseUrl": "http://localhost:9999",
                    "apiKey": "",
                    "models": ["llama3.1"],
                    "priority": 1,
                    "health_status": "unhealthy",
                },
                {
                    "id": "healthy-provider",
                    "baseUrl": "http://localhost:11434",
                    "apiKey": "",
                    "models": ["llama3.1"],
                    "priority": 10,
                    "health_status": "healthy",
                },
            ]
        )

        router = AgentModelRouter(
            agent_id="fallback-agent",
            model_garage=garage,
        )
        actor = AgentActor(
            agent_id="fallback-agent",
            swarms_agent=swarms_agent,
            model_router=router,
        )

        response = await actor.run_with_llm("extract the key points")
        assert "healthy-provider" in response, (
            f"Expected fallback to healthy-provider, got {response}"
        )

    # -- Scenario 5: error recovery -------------------------------------

    @staticmethod
    async def test_all_providers_unhealthy_falls_to_swarms() -> None:
        """When **every** provider is unhealthy, ``run_with_llm`` falls
        back to ``swarms_agent.run()``."""
        swarms_agent = _make_swarms_agent()
        garage = _make_garage(
            [
                {
                    "id": "dead-1",
                    "baseUrl": "http://localhost:9999",
                    "apiKey": "",
                    "models": ["llama3.1"],
                    "priority": 1,
                    "health_status": "unhealthy",
                },
            ]
        )

        router = AgentModelRouter(
            agent_id="all-dead-agent",
            model_garage=garage,
        )
        actor = AgentActor(
            agent_id="all-dead-agent",
            swarms_agent=swarms_agent,
            model_router=router,
        )

        response = await actor.run_with_llm("list the numbers")
        # Falls through to swarms agent
        assert response == "swarms fallback response"
        swarms_agent.run.assert_called_once()

    @staticmethod
    async def test_empty_router_providers_falls_to_swarms() -> None:
        """When the router exists but has zero providers registered,
        ``route()`` raises ``RuntimeError``, which ``run_with_llm``
        catches and falls back to ``swarms_agent.run()``."""
        swarms_agent = _make_swarms_agent()

        # A router with no providers at all (no standalone + no garage)
        router = AgentModelRouter(agent_id="empty-router-agent")
        actor = AgentActor(
            agent_id="empty-router-agent",
            swarms_agent=swarms_agent,
            model_router=router,
        )

        response = await actor.run_with_llm("test prompt")
        assert response == "swarms fallback response"
        swarms_agent.run.assert_called_once()
