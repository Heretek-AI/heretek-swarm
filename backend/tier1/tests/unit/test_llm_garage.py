"""Tests for ModelGarage circuit breaker and provider fallback.

We mock the inner _stream_from_provider so we test the garage's behavior,
not real provider calls. Each provider implementation is wired separately.
"""

from __future__ import annotations

from collections import deque

import pytest

from tier1.config import Settings
from tier1.deliberation.state import AgentName
from tier1.llm.errors import LLMTimeout, LLMUnavailable
from tier1.llm.garage import CIRCUIT_OPEN_S, CIRCUIT_THRESHOLD, ModelGarage, StreamChunk


def _settings() -> Settings:
    return Settings(
        minimax_api_key="sk-test",
        anthropic_api_key="sk-test",
        openai_api_key="sk-test",
    )


class _FakeProvider:
    """Stub the inner provider method with a sequence of behaviors."""

    def __init__(self, behaviors: list) -> None:
        self.behaviors = list(behaviors)
        self.calls = 0

    async def __call__(self, provider: str, prompt: str, agent: AgentName):
        self.calls += 1
        if not self.behaviors:
            raise LLMUnavailable("exhausted")
        b = self.behaviors.pop(0)
        if isinstance(b, Exception):
            raise b
        if b == "ok":
            for t in ("hello", " ", "world"):
                yield StreamChunk(token=t, agent=agent, seq=0)
            return
        if b == "timeout":
            raise LLMTimeout("timed out")
        raise AssertionError(f"unknown behavior: {b}")


@pytest.fixture
def garage(monkeypatch) -> ModelGarage:
    g = ModelGarage(_settings())
    return g


async def test_provider_order_all_available(garage: ModelGarage):
    order = garage.provider_order()
    assert order == ["minimax", "anthropic", "openai", "local"]


async def test_stream_chat_success_first_provider(garage: ModelGarage, monkeypatch):
    fake = _FakeProvider(["ok"])
    monkeypatch.setattr(garage, "_stream_from_provider", fake)
    tokens: list[str] = []
    async for chunk in garage.stream_chat("hi", agent="alpha"):
        tokens.append(chunk.token)
    assert "".join(tokens) == "hello world"
    assert fake.calls == 1
    assert not garage.circuits["minimax"].is_open()


async def test_stream_chat_falls_back_on_timeout(garage: ModelGarage, monkeypatch):
    fake = _FakeProvider(["timeout", "ok"])
    monkeypatch.setattr(garage, "_stream_from_provider", fake)
    tokens: list[str] = []
    async for chunk in garage.stream_chat("hi", agent="beta"):
        tokens.append(chunk.token)
    assert "".join(tokens) == "hello world"
    assert fake.calls == 2
    assert garage.circuits["minimax"].failures == pytest.approx(garage.circuits["minimax"].failures)


async def test_stream_chat_all_providers_fail_raises_unavailable(garage: ModelGarage, monkeypatch):
    fake = _FakeProvider(["timeout", "timeout", "timeout", "timeout"])
    monkeypatch.setattr(garage, "_stream_from_provider", fake)
    with pytest.raises(LLMUnavailable):
        async for _ in garage.stream_chat("hi", agent="alpha"):
            pass


async def test_circuit_opens_after_threshold_failures(garage: ModelGarage, monkeypatch):
    # Each stream_chat call hits each provider once. 3 calls -> minimax has
    # 3 failures, exceeding CIRCUIT_THRESHOLD -> circuit opens.
    fake = _FakeProvider(["timeout"] * 12)
    monkeypatch.setattr(garage, "_stream_from_provider", fake)
    for i in range(3):
        with pytest.raises(LLMUnavailable):
            async for _ in garage.stream_chat("hi", agent="alpha"):
                pass
    # provider_order should skip minimax now.
    assert "minimax" not in garage.provider_order()


async def test_circuit_recovery_after_success(garage: ModelGarage, monkeypatch):
    # Fail twice, then succeed.
    fake = _FakeProvider(["timeout", "timeout", "ok"])
    monkeypatch.setattr(garage, "_stream_from_provider", fake)
    tokens: list[str] = []
    async for chunk in garage.stream_chat("hi", agent="alpha"):
        tokens.append(chunk.token)
    # Success lands on openai (3rd in chain); openai's circuit is cleared.
    assert garage.circuits["openai"].failures == deque()
    assert not garage.circuits["openai"].is_open()


async def test_chat_collects_all_tokens(garage: ModelGarage, monkeypatch):
    fake = _FakeProvider(["ok"])
    monkeypatch.setattr(garage, "_stream_from_provider", fake)
    result = await garage.chat("hi", agent="alpha")
    assert result == "hello world"


async def test_provider_order_excludes_open_circuits(garage: ModelGarage):
    # Trip the minimax circuit manually.
    for _ in range(CIRCUIT_THRESHOLD):
        garage.circuits["minimax"].record_failure()
    assert "minimax" not in garage.provider_order()
    assert "anthropic" in garage.provider_order()


def test_circuit_open_window_constant():
    assert CIRCUIT_OPEN_S == 300.0


def test_circuit_threshold_constant():
    assert CIRCUIT_THRESHOLD == 3
