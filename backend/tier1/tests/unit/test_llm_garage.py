"""Tests for ModelGarage circuit breaker and provider fallback.

We mock the inner _stream_from_provider so we test the garage's behavior,
not real provider calls. Each provider implementation is wired separately.
"""

from __future__ import annotations

import time
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
        if b == "ok_then_timeout":
            # Yield some chunks, then raise LLMTimeout. Exercises the
            # mid-stream exception path in stream_chat.
            yield StreamChunk(token="par", agent=agent, seq=0)
            yield StreamChunk(token="tial", agent=agent, seq=1)
            raise LLMTimeout("mid-stream timeout")
        if b == "ok_then_burst":
            # Yield some chunks, then raise an unexpected (non-LLM) exception.
            # Same code path as ok_then_timeout but covers non-LLMError.
            yield StreamChunk(token="mid", agent=agent, seq=0)
            yield StreamChunk(token="dle", agent=agent, seq=1)
            raise RuntimeError("connection dropped")
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
    # After one timeout on the primary, the primary circuit has recorded
    # exactly one failure — proves the failure-recording path is wired.
    assert len(garage.circuits["minimax"].failures) == 1


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


async def test_stream_chat_midstream_timeout_records_failure_and_propagates(
    garage: ModelGarage, monkeypatch
):
    """Provider yields some chunks then raises LLMTimeout mid-stream.

    Expected: the partial chunks are yielded to the caller, the primary
    circuit records exactly one failure, the exception propagates as
    LLMUnavailable (not the raw LLMTimeout), and the chain does NOT fall
    through to the next provider (that would double-emit tokens).
    """
    fake = _FakeProvider(["ok_then_timeout"])
    monkeypatch.setattr(garage, "_stream_from_provider", fake)
    tokens: list[str] = []
    with pytest.raises(LLMUnavailable) as excinfo:
        async for chunk in garage.stream_chat("hi", agent="alpha"):
            tokens.append(chunk.token)
    # Caller received the partial chunks before the failure.
    assert "".join(tokens) == "partial"
    # Primary recorded the failure.
    assert len(garage.circuits["minimax"].failures) == 1
    # Mid-stream failure does NOT fall through to a second provider.
    assert fake.calls == 1
    # Propagated as LLMUnavailable with a descriptive message and a
    # chained cause pointing at the original LLMTimeout.
    assert "minimax" in str(excinfo.value)
    assert isinstance(excinfo.value.__cause__, LLMTimeout)


async def test_stream_chat_midstream_non_llm_exception_also_recorded(
    garage: ModelGarage, monkeypatch
):
    """A non-LLMError raised mid-stream (e.g. socket reset) is also recorded
    as a failure and propagated as LLMUnavailable."""
    fake = _FakeProvider(["ok_then_burst"])
    monkeypatch.setattr(garage, "_stream_from_provider", fake)
    tokens: list[str] = []
    with pytest.raises(LLMUnavailable) as excinfo:
        async for chunk in garage.stream_chat("hi", agent="alpha"):
            tokens.append(chunk.token)
    assert "".join(tokens) == "middle"
    assert len(garage.circuits["minimax"].failures) == 1
    assert fake.calls == 1
    # The chained cause is the original RuntimeError, not swallowed.
    assert isinstance(excinfo.value.__cause__, RuntimeError)


async def test_circuit_threshold_trips_at_exactly_three_failures_on_one_provider(
    garage: ModelGarage, monkeypatch
):
    """Threshold behavior is per-provider: exactly 3 failures on minimax
    opens the minimax circuit while leaving others below threshold and
    therefore still closed.

    We isolate the per-provider threshold assertion by manually pre-opening
    the other providers' circuits (so they're skipped by provider_order)
    and then driving exactly 3 failures onto minimax via 3 sequential calls.
    Each call sees only minimax in its snapshotted provider_order, so the
    other providers receive zero additional failures.
    """
    # Manually trip anthropic/openai/local so provider_order() returns
    # only ["minimax"]. We bypass record_failure -> open_until by setting
    # open_until directly to a future timestamp.
    future = time.time() + 600.0
    for name in ("anthropic", "openai", "local"):
        garage.circuits[name].open_until = future

    # Sanity: chain is now minimax-only.
    assert garage.provider_order() == ["minimax"]

    # Drive exactly 3 failures onto minimax via 3 sequential calls. Each
    # call snapshots ["minimax"], the timeout fires, the failure is
    # recorded, and the call raises LLMUnavailable with no fallback.
    fake = _FakeProvider(["timeout", "timeout", "timeout"])
    monkeypatch.setattr(garage, "_stream_from_provider", fake)
    for _ in range(3):
        with pytest.raises(LLMUnavailable):
            async for _ in garage.stream_chat("hi", agent="alpha"):
                pass

    # Per-provider failure counts: minimax exactly at threshold (3), others
    # received zero failures during this test.
    assert len(garage.circuits["minimax"].failures) == 3
    assert len(garage.circuits["anthropic"].failures) == 0
    assert len(garage.circuits["openai"].failures) == 0
    assert len(garage.circuits["local"].failures) == 0

    # Threshold isolates the failing provider: only minimax is open.
    assert garage.circuits["minimax"].is_open()
    # The other three are open from the manual pre-trip (still open from
    # the future timestamp), not from the failures in this test.
    assert garage.circuits["anthropic"].is_open()
    assert garage.circuits["openai"].is_open()
    assert garage.circuits["local"].is_open()

    # provider_order is now empty — every circuit is open.


async def test_circuit_below_threshold_stays_closed(garage: ModelGarage, monkeypatch):
    """Two failures on a provider is below the threshold of 3, so the
    circuit must remain closed and the provider remains in the chain."""
    # Two stream_chat calls: minimax accumulates 2 failures (< threshold).
    fake = _FakeProvider(["timeout"] * 8)
    monkeypatch.setattr(garage, "_stream_from_provider", fake)
    for _ in range(2):
        with pytest.raises(LLMUnavailable):
            async for _ in garage.stream_chat("hi", agent="alpha"):
                pass
    assert len(garage.circuits["minimax"].failures) == 2
    assert not garage.circuits["minimax"].is_open()
    assert "minimax" in garage.provider_order()
