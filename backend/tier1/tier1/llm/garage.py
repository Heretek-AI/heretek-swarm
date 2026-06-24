"""ModelGarage — pydantic-ai multi-provider wrapper with circuit breaker.

Provider chain: MiniMax (primary) -> Anthropic -> OpenAI -> local (Ollama).

Circuit breaker: each provider tracks recent failures. 3 failures within
60s -> provider marked down for 5 minutes. Calls skip down providers
and try the next in the chain. If all providers are down, raise
LLMUnavailable.
"""

from __future__ import annotations

import time
from collections import deque
from dataclasses import dataclass
from typing import AsyncIterator, Deque

import structlog

from tier1.config import Settings
from tier1.deliberation.state import AgentName
from tier1.llm.errors import (
    LLMTimeout,
    LLMUnavailable,
)  # LLMTimeout: part of the provider contract; see _stream_from_provider docstring.

log = structlog.get_logger(__name__)

PROVIDER_NAMES = ("minimax", "anthropic", "openai", "local")

CIRCUIT_WINDOW_S = 60.0
CIRCUIT_THRESHOLD = 3
CIRCUIT_OPEN_S = 300.0


@dataclass
class StreamChunk:
    token: str
    agent: AgentName
    seq: int


class _Circuit:
    """Per-provider circuit breaker."""

    def __init__(self, name: str) -> None:
        self.name = name
        self.failures: Deque[float] = deque()
        self.open_until: float = 0.0

    def record_failure(self) -> None:
        now = time.time()
        self.failures.append(now)
        while self.failures and now - self.failures[0] > CIRCUIT_WINDOW_S:
            self.failures.popleft()
        if len(self.failures) >= CIRCUIT_THRESHOLD:
            self.open_until = now + CIRCUIT_OPEN_S
            log.warning("circuit_open", provider=self.name, until=self.open_until)

    def record_success(self) -> None:
        self.failures.clear()
        self.open_until = 0.0

    def is_open(self) -> bool:
        return time.time() < self.open_until


class ModelGarage:
    """Multi-provider LLM gateway with circuit breaker and streaming."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.circuits: dict[str, _Circuit] = {name: _Circuit(name) for name in PROVIDER_NAMES}

    def provider_order(self) -> list[str]:
        """Return provider names in priority order, skipping open circuits."""
        return [n for n in PROVIDER_NAMES if not self.circuits[n].is_open()]

    async def stream_chat(
        self,
        prompt: str,
        *,
        agent: AgentName,
    ) -> AsyncIterator[StreamChunk]:
        """Yield token chunks. Tries providers in chain until one succeeds.

        Failure semantics:
        - `LLMTimeout` / `LLMUnavailable` raised before any chunk: recorded as
          a failure, falls through to the next provider.
        - Any other exception (or a recognized exception) raised AFTER one or
          more chunks were yielded (mid-stream failure): recorded as a failure
          for the active provider, then wrapped as `LLMUnavailable` and
          propagated to the caller. Mid-stream partial output is treated as
          unrecoverable for the current call — falling through to another
          provider would double-emit tokens. The next call to `stream_chat`
          will start the chain from the top, skipping the now-open circuit
          if it tripped.
        """
        order = self.provider_order()
        if not order:
            raise LLMUnavailable("all providers down (circuit open)")

        last_exc: Exception | None = None
        for provider in order:
            yielded = 0
            try:
                async for chunk in self._stream_from_provider(provider, prompt, agent):
                    yield chunk
                    yielded += 1
                self.circuits[provider].record_success()
                return
            except Exception as exc:  # noqa: BLE001 — see failure semantics
                self.circuits[provider].record_failure()
                last_exc = exc
                if yielded == 0:
                    log.warning(
                        "provider_failed",
                        provider=provider,
                        error=str(exc),
                        error_type=type(exc).__name__,
                    )
                    continue
                # Mid-stream failure: partial output already yielded to the
                # caller. Wrap as LLMUnavailable and propagate — the caller
                # has already seen the partial response and we cannot safely
                # resume or fall through without producing a confusing mix.
                log.warning(
                    "provider_midstream_failure",
                    provider=provider,
                    chunks_yielded=yielded,
                    error=str(exc),
                    error_type=type(exc).__name__,
                )
                raise LLMUnavailable(
                    f"provider {provider} raised mid-stream after {yielded} chunks: {exc}"
                ) from exc

        raise LLMUnavailable(f"all providers failed: {last_exc}")

    async def _stream_from_provider(
        self,
        provider: str,
        prompt: str,
        agent: AgentName,
    ) -> AsyncIterator[StreamChunk]:
        """Provider-specific streaming. Wraps pydantic-ai model.

        For Task 3 we provide the structural skeleton. Real provider
        implementations are wired in subsequent substeps once each
        provider's pydantic-ai Model class is configured.

        This method MUST raise LLMTimeout for timeout, or yield
        StreamChunk instances for each token. It MUST NOT raise any
        other exception type.
        """
        raise NotImplementedError(f"provider {provider!r} not yet wired — see Task 3.5")

    async def chat(self, prompt: str, *, agent: AgentName) -> str:
        """Non-streaming convenience: collect all tokens into one string."""
        chunks: list[str] = []
        async for chunk in self.stream_chat(prompt, agent=agent):
            chunks.append(chunk.token)
        return "".join(chunks)
