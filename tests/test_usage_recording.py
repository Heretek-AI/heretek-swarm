"""Tests for AgentModelRouter usage recording."""
from __future__ import annotations

import pytest

from heretek_swarm.llm.model_garage import LLMResponse, ProviderType
from heretek_swarm.routing.model_router import (
    AgentModelRouter,
    RouterProviderConfig,
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


# ── fixture ──────────────────────────────────────────────────────────────


@pytest.fixture
def router() -> AgentModelRouter:
    r = AgentModelRouter(agent_id="test-agent")
    r.register_provider(
        RouterProviderConfig(
            provider_id="openai",
            base_url="http://localhost:8000",
            api_key="sk-test",
            models=["gpt-4o"],
            priority=1,
        )
    )
    return r


# ── record_usage ─────────────────────────────────────────────────────────


class TestRecordUsage:
    """record_usage() should increment request count, cost, and token tracking."""

    def test_records_request_count(self, router: AgentModelRouter) -> None:
        router.record_usage("openai", _make_response())
        assert router._request_counts["openai"] == 1

    def test_records_multiple_requests(self, router: AgentModelRouter) -> None:
        router.record_usage("openai", _make_response())
        router.record_usage("openai", _make_response())
        assert router._request_counts["openai"] == 2

    def test_records_cost(self, router: AgentModelRouter) -> None:
        router.record_usage("openai", _make_response(cost=2.5))
        assert router._cost_tracking["openai"] == 2.5

    def test_accumulates_cost(self, router: AgentModelRouter) -> None:
        router.record_usage("openai", _make_response(cost=1.0))
        router.record_usage("openai", _make_response(cost=2.0))
        assert router._cost_tracking["openai"] == 3.0

    def test_records_tokens(self, router: AgentModelRouter) -> None:
        router.record_usage("openai", _make_response(total_tokens=150))
        assert router._token_tracking["openai"] == 150

    def test_accumulates_tokens(self, router: AgentModelRouter) -> None:
        router.record_usage("openai", _make_response(total_tokens=100))
        router.record_usage("openai", _make_response(total_tokens=200))
        assert router._token_tracking["openai"] == 300

    def test_handles_none_cost_gracefully(self, router: AgentModelRouter) -> None:
        router.record_usage("openai", _make_response(cost=None))
        assert router._cost_tracking["openai"] == 0.0

    def test_handles_zero_cost_gracefully(self, router: AgentModelRouter) -> None:
        router.record_usage("openai", _make_response(cost=0.0))
        assert router._cost_tracking["openai"] == 0.0

    def test_handles_zero_tokens(self, router: AgentModelRouter) -> None:
        router.record_usage("openai", _make_response(total_tokens=0))
        assert router._token_tracking["openai"] == 0

    def test_tracks_multiple_providers_independently(
        self, router: AgentModelRouter
    ) -> None:
        router.register_provider(
            RouterProviderConfig(
                provider_id="anthropic",
                base_url="http://localhost:8001",
                api_key="sk-test",
                models=["claude-3-5-sonnet"],
                priority=2,
            )
        )
        router.record_usage("openai", _make_response(cost=1.0, total_tokens=100))
        router.record_usage("anthropic", _make_response(cost=3.0, total_tokens=200))
        assert router._cost_tracking == {"openai": 1.0, "anthropic": 3.0}
        assert router._token_tracking == {"openai": 100, "anthropic": 200}
        assert router._request_counts == {"openai": 1, "anthropic": 1}


# ── get_stats ────────────────────────────────────────────────────────────


class TestGetStatsTokenTracking:
    """get_stats() should expose token_tracking alongside other stats."""

    def test_token_tracking_in_stats(self, router: AgentModelRouter) -> None:
        router.record_usage("openai", _make_response(total_tokens=250))
        stats = router.get_stats()
        assert "token_tracking" in stats
        assert stats["token_tracking"] == {"openai": 250}

    def test_empty_initially(self, router: AgentModelRouter) -> None:
        stats = router.get_stats()
        assert stats["token_tracking"] == {}

    def test_after_multiple_providers(self, router: AgentModelRouter) -> None:
        router.register_provider(
            RouterProviderConfig(
                provider_id="anthropic",
                base_url="http://localhost:8001",
                api_key="sk-test",
                models=["claude-3-5-sonnet"],
                priority=2,
            )
        )
        router.record_usage("openai", _make_response(total_tokens=100))
        router.record_usage("anthropic", _make_response(total_tokens=200))
        stats = router.get_stats()
        assert stats["token_tracking"] == {"openai": 100, "anthropic": 200}

    def test_other_stats_preserved(self, router: AgentModelRouter) -> None:
        router.record_usage("openai", _make_response(cost=5.0, total_tokens=250))
        stats = router.get_stats()
        assert stats["request_counts"] == {"openai": 1}
        assert stats["cost_tracking"] == {"openai": 5.0}
        assert stats["token_tracking"] == {"openai": 250}
        assert stats["agent_id"] == "test-agent"
