"""Characterization tests for ModelGarage.

These tests pin the current public contract of ModelGarage so the
LLM-stack consolidation onto Pydantic AI (Phase 2) can be verified for
behavioral parity. They do NOT hit the network: the instrumented httpx
client is patched to return canned responses.

Covered contract:
- Provider routing (provider_id / provider_preference / default+priority)
- LLMRequest -> payload mapping (model override, temperature, etc.)
- OpenAI response -> LLMResponse mapping (content, usage, finish_reason)
- Provider fallback across a failed provider
- "No available providers" error path
"""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest

from heretek_swarm.llm.model_garage import (
    ChatMessage,
    LLMRequest,
    LLMResponse,
    ModelGarage,
    ProviderConfig,
    ProviderType,
)

pytestmark = pytest.mark.asyncio


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _config(pid: str, *, provider_type: ProviderType, **kw) -> ProviderConfig:
    base = dict(
        id=pid,
        name=pid,
        provider_type=provider_type,
        base_url="https://example.test/v1",
        api_key="k-test",
        default_model="m-test",
        is_enabled=True,
        priority=100,
    )
    base.update(kw)
    return ProviderConfig(**base)


def _fake_httpx_response(payload: dict, status: int = 200) -> SimpleNamespace:
    """A minimal stand-in for an httpx.Response."""

    def raise_for_status() -> None:
        if status >= 400:
            raise RuntimeError(f"HTTP {status}")

    return SimpleNamespace(
        json=lambda: payload,
        raise_for_status=raise_for_status,
        status_code=status,
    )


def _garage_with_openai(pid: str = "openai-1", **kw) -> ModelGarage:
    """A ModelGarage with one OpenAI provider registered and marked default."""
    garage = ModelGarage()
    cfg = _config(pid, provider_type=ProviderType.OPENAI, is_default=True, **kw)
    garage._provider_configs[cfg.id] = cfg
    return garage


# ---------------------------------------------------------------------------
# Request -> payload mapping
# ---------------------------------------------------------------------------


class TestRequestMapping:
    async def test_request_to_dict_includes_messages_and_defaults(self) -> None:
        payload = LLMRequest(
            messages=[ChatMessage(role="user", content="hi")], model="gpt-x"
        ).to_dict()
        assert payload["messages"] == [{"role": "user", "content": "hi"}]
        assert payload["model"] == "gpt-x"
        assert payload["stream"] is False
        assert payload["temperature"] == 0.7


# ---------------------------------------------------------------------------
# complete(): response mapping + routing
# ---------------------------------------------------------------------------


class TestComplete:
    async def test_complete_maps_openai_response_to_llmresponse(self) -> None:
        garage = _garage_with_openai()
        await garage.initialize()

        canned = {
            "model": "gpt-x",
            "choices": [
                {
                    "message": {"content": "hello world", "tool_calls": []},
                    "finish_reason": "stop",
                }
            ],
            "usage": {"prompt_tokens": 3, "completion_tokens": 2, "total_tokens": 5},
        }

        with patch(
            "heretek_swarm.llm.model_garage.OpenAIProvider._get_client",
            AsyncMock(
                return_value=SimpleNamespace(
                    post=AsyncMock(return_value=_fake_httpx_response(canned)),
                    aclose=AsyncMock(),
                    is_closed=False,
                )
            ),
        ):
            resp = await garage.complete(
                messages=[ChatMessage(role="user", content="hi")],
                model="gpt-x",
                provider_id="openai-1",
            )

        assert isinstance(resp, LLMResponse)
        assert resp.content == "hello world"
        assert resp.finish_reason == "stop"
        assert resp.prompt_tokens == 3
        assert resp.completion_tokens == 2
        assert resp.total_tokens == 5

    async def test_complete_uses_provider_default_model_when_unspecified(self) -> None:
        garage = _garage_with_openai()
        await garage.initialize()
        captured: dict = {}

        canned = {
            "model": "m-test",
            "choices": [{"message": {"content": "ok"}, "finish_reason": "stop"}],
            "usage": {},
        }

        async def fake_post(url, json=None):
            captured["payload"] = json
            return _fake_httpx_response(canned)

        with patch(
            "heretek_swarm.llm.model_garage.OpenAIProvider._get_client",
            AsyncMock(
                return_value=SimpleNamespace(
                    post=fake_post, aclose=AsyncMock(), is_closed=False
                )
            ),
        ):
            await garage.complete(
                messages=[ChatMessage(role="user", content="hi")],
                provider_id="openai-1",
            )

        # ProviderConfig.default_model should win when caller passes no model
        assert captured["payload"]["model"] == "m-test"

    async def test_complete_falls_back_when_default_provider_fails(self) -> None:
        garage = ModelGarage()
        garage._provider_configs["fail-1"] = _config(
            "fail-1", provider_type=ProviderType.OPENAI, is_default=True, priority=10
        )
        garage._provider_configs["ok-2"] = _config(
            "ok-2", provider_type=ProviderType.OPENAI, is_default=False, priority=20
        )
        await garage.initialize()

        canned_ok = {
            "model": "m",
            "choices": [{"message": {"content": "fallback ok"}, "finish_reason": "stop"}],
            "usage": {},
        }

        call_count = {"n": 0}

        async def fake_post(url, json=None):
            call_count["n"] += 1
            if call_count["n"] == 1:
                raise RuntimeError("provider down")
            return _fake_httpx_response(canned_ok)

        with patch(
            "heretek_swarm.llm.model_garage.OpenAIProvider._get_client",
            AsyncMock(
                return_value=SimpleNamespace(
                    post=fake_post, aclose=AsyncMock(), is_closed=False
                )
            ),
        ):
            resp = await garage.complete(messages=[ChatMessage(role="user", content="hi")])

        assert resp.content == "fallback ok"

    async def test_complete_raises_when_no_providers_available(self) -> None:
        garage = ModelGarage()  # no providers configured
        await garage.initialize()
        with pytest.raises(ValueError, match="No available providers"):
            await garage.complete(messages=[ChatMessage(role="user", content="hi")])

    async def test_complete_routes_to_provider_id(self) -> None:
        garage = ModelGarage()
        garage._provider_configs["a"] = _config(
            "a", provider_type=ProviderType.OPENAI, is_default=True
        )
        garage._provider_configs["b"] = _config(
            "b", provider_type=ProviderType.OPENAI, is_default=False
        )
        await garage.initialize()

        canned = {
            "model": "m",
            "choices": [{"message": {"content": "b-only"}, "finish_reason": "stop"}],
            "usage": {},
        }

        async def fake_post(url, json=None):
            return _fake_httpx_response(canned)

        with patch(
            "heretek_swarm.llm.model_garage.OpenAIProvider._get_client",
            AsyncMock(
                return_value=SimpleNamespace(
                    post=fake_post, aclose=AsyncMock(), is_closed=False
                )
            ),
        ):
            resp = await garage.complete(
                messages=[ChatMessage(role="user", content="hi")], provider_id="b"
            )
        assert resp.content == "b-only"
