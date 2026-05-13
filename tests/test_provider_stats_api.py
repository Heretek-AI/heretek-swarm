"""Tests for get_all_provider_stats() aggregate function.

Tests the aggregation function directly (not over HTTP) since the FastAPI
endpoint at /api/v1/observability/provider-stats is a thin wrapper that calls
this function. The endpoint itself follows the same rate-limiting and
zero-trust patterns as every other observability endpoint.
"""

from __future__ import annotations

import pytest

from heretek_swarm.llm.model_garage import LLMResponse, ProviderType
from heretek_swarm.routing.model_router import (
    AgentModelRouter,
    RouterProviderConfig,
    _router_registry,
    get_all_provider_stats,
)


def _make_response(
    content: str = "hello",
    model: str = "gpt-4o",
    total_tokens: int = 100,
    cost: float | None = 1.0,
) -> LLMResponse:
    """Helper — build an LLMResponse with the fields we care about."""
    return LLMResponse(
        content=content,
        model=model,
        provider=ProviderType.OPENAI,
        usage={
            "prompt_tokens": 50,
            "completion_tokens": 50,
            "total_tokens": total_tokens,
        },
        cost=cost,
    )


def _register_provider(router: AgentModelRouter, provider_id: str, models: list[str]) -> None:
    router.register_provider(
        RouterProviderConfig(
            provider_id=provider_id,
            base_url="http://localhost:8000",
            api_key="sk-test",
            models=models,
            priority=1,
        )
    )


# ── fixtures ─────────────────────────────────────────────────────────────


@pytest.fixture(autouse=True)
def _cleanup_router_registry() -> None:
    """Clear the global router registry between tests to isolate state."""
    _router_registry.clear()
    return


@pytest.fixture
def router_openai() -> AgentModelRouter:
    r = AgentModelRouter(agent_id="agent-a")
    _register_provider(r, "openai", ["gpt-4o", "gpt-4o-mini"])
    _router_registry["agent-a"] = r
    return r


@pytest.fixture
def router_anthropic() -> AgentModelRouter:
    r = AgentModelRouter(agent_id="agent-b")
    _register_provider(r, "anthropic", ["claude-3-5-sonnet"])
    _router_registry["agent-b"] = r
    return r


# ── get_all_provider_stats ───────────────────────────────────────────────


class TestGetAllProviderStatsEmpty:
    """get_all_provider_stats() with no registered routers."""

    def test_returns_empty_providers(self) -> None:
        stats = get_all_provider_stats()
        assert stats["providers"] == {}

    def test_zeros_when_no_routers(self) -> None:
        stats = get_all_provider_stats()
        assert stats["total_cost"] == 0.0
        assert stats["total_requests"] == 0
        assert stats["total_tokens"] == 0


class TestGetAllProviderStatsOneRouter:
    """get_all_provider_stats() with a single router."""

    def test_shape_matches_plan_spec(self, router_openai: AgentModelRouter) -> None:
        router_openai.record_usage("openai", _make_response(cost=2.0, total_tokens=300))
        stats = get_all_provider_stats()

        assert "providers" in stats
        assert "total_cost" in stats
        assert "total_requests" in stats
        assert "total_tokens" in stats

        prov = stats["providers"]["openai"]
        assert "total_requests" in prov
        assert "total_cost" in prov
        assert "total_tokens" in prov
        assert "models_used" in prov

    def test_single_call_counts(self, router_openai: AgentModelRouter) -> None:
        router_openai.record_usage("openai", _make_response(cost=2.0, total_tokens=300))
        stats = get_all_provider_stats()

        assert stats["providers"]["openai"]["total_requests"] == 1
        assert stats["providers"]["openai"]["total_cost"] == 2.0
        assert stats["providers"]["openai"]["total_tokens"] == 300

    def test_models_used_breakdown(self, router_openai: AgentModelRouter) -> None:
        router_openai.record_usage("openai", _make_response(model="gpt-4o"))
        router_openai.record_usage("openai", _make_response(model="gpt-4o-mini"))
        router_openai.record_usage("openai", _make_response(model="gpt-4o"))

        stats = get_all_provider_stats()
        mu = stats["providers"]["openai"]["models_used"]
        assert mu == {"gpt-4o": 2, "gpt-4o-mini": 1}

    def test_grand_totals_one_provider(self, router_openai: AgentModelRouter) -> None:
        router_openai.record_usage("openai", _make_response(cost=5.0, total_tokens=500))
        router_openai.record_usage("openai", _make_response(cost=3.0, total_tokens=200))

        stats = get_all_provider_stats()
        assert stats["total_cost"] == 8.0
        assert stats["total_requests"] == 2
        assert stats["total_tokens"] == 700


class TestGetAllProviderStatsMultiRouter:
    """get_all_provider_stats() with multiple routers across providers."""

    def test_aggregates_across_routers(
        self,
        router_openai: AgentModelRouter,
        router_anthropic: AgentModelRouter,
    ) -> None:
        router_openai.record_usage("openai", _make_response(cost=1.0, total_tokens=100))
        router_anthropic.record_usage(
            "anthropic", _make_response(model="claude-3-5-sonnet", cost=3.0, total_tokens=500)
        )

        stats = get_all_provider_stats()

        assert stats["providers"]["openai"]["total_requests"] == 1
        assert stats["providers"]["openai"]["total_cost"] == 1.0
        assert stats["providers"]["openai"]["total_tokens"] == 100

        assert stats["providers"]["anthropic"]["total_requests"] == 1
        assert stats["providers"]["anthropic"]["total_cost"] == 3.0
        assert stats["providers"]["anthropic"]["total_tokens"] == 500

        assert stats["total_cost"] == 4.0
        assert stats["total_requests"] == 2
        assert stats["total_tokens"] == 600

    def test_same_provider_across_two_routers(
        self,
        router_openai: AgentModelRouter,
    ) -> None:
        """Two routers both using 'openai' should have their stats merged."""
        r2 = AgentModelRouter(agent_id="agent-c")
        _register_provider(r2, "openai", ["gpt-4o"])
        _router_registry["agent-c"] = r2

        router_openai.record_usage("openai", _make_response(cost=1.0, total_tokens=100))
        r2.record_usage("openai", _make_response(cost=2.0, total_tokens=200))

        stats = get_all_provider_stats()
        assert stats["providers"]["openai"]["total_requests"] == 2
        assert stats["providers"]["openai"]["total_cost"] == 3.0
        assert stats["providers"]["openai"]["total_tokens"] == 300

        assert stats["total_cost"] == 3.0
        assert stats["total_requests"] == 2
        assert stats["total_tokens"] == 300

    def test_same_provider_models_used_merged(
        self,
        router_openai: AgentModelRouter,
    ) -> None:
        r2 = AgentModelRouter(agent_id="agent-d")
        _register_provider(r2, "openai", ["gpt-4o", "gpt-4o-mini"])
        _router_registry["agent-d"] = r2

        router_openai.record_usage("openai", _make_response(model="gpt-4o"))
        r2.record_usage("openai", _make_response(model="gpt-4o-mini"))
        r2.record_usage("openai", _make_response(model="gpt-4o"))

        stats = get_all_provider_stats()
        mu = stats["providers"]["openai"]["models_used"]
        assert mu == {"gpt-4o": 2, "gpt-4o-mini": 1}

    def test_no_calls_returns_zero_counts(
        self,
        router_openai: AgentModelRouter,
        router_anthropic: AgentModelRouter,
    ) -> None:
        """Routers exist but no usage recorded — provider keys present with zeros."""
        stats = get_all_provider_stats()
        assert stats["total_cost"] == 0.0
        assert stats["total_requests"] == 0
        assert stats["total_tokens"] == 0
