"""Native per-agent model routing with multi-provider support.

AgentModelRouter classifies task complexity and routes to the best
provider/model combination. When wired to ModelGarage, it uses the
garage's provider configs as the source of truth and falls back to
its own standalone configs when no garage is available.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from heretek_swarm.llm.model_garage import LLMResponse, ModelGarage


class TaskComplexity(Enum):
    SIMPLE = "simple"
    STANDARD = "standard"
    COMPLEX = "complex"


@dataclass
class RouterProviderConfig:
    """Per-provider configuration for the AgentModelRouter.

    This is a standalone config for use when ModelGarage is not wired.
    When ModelGarage is connected, the router derives its provider info
    from the garage's ProviderConfigs instead.
    """
    provider_id: str
    base_url: str
    api_key: str
    models: List[str]
    priority: int
    max_rpm: int = 100
    health_status: bool = True


@dataclass
class RoutingDecision:
    provider_id: str
    model: str
    complexity: TaskComplexity
    fallback_chain: List[str] = field(default_factory=list)
    confidence: float = 1.0


class AgentModelRouter:
    """Per-agent model router with dynamic provider selection.

    Routes LLM calls to the best provider based on task complexity,
    provider priority, and health status. Can work standalone (own configs)
    or connected to ModelGarage (shared config source).
    """

    def __init__(
        self,
        agent_id: str,
        providers: Optional[List[RouterProviderConfig]] = None,
        model_garage: Optional["ModelGarage"] = None,
    ):
        self.agent_id = agent_id
        self._providers: Dict[str, RouterProviderConfig] = {
            p.provider_id: p for p in (providers or [])
        }
        self._model_garage = model_garage
        self._request_counts: Dict[str, int] = {}
        self._cost_tracking: Dict[str, float] = {}
        self._token_tracking: Dict[str, int] = {}

    def register_provider(self, config: RouterProviderConfig) -> None:
        """Register a standalone provider config (garage-independent path)."""
        self._providers[config.provider_id] = config

    def record_usage(
        self, provider_id: str, response: "LLMResponse"
    ) -> None:
        """Record token usage, request count, and cost for a provider after an LLM call.

        Args:
            provider_id: The provider that handled the request.
            response: The LLMResponse returned by the provider, which may
                      include ``cost``, ``total_tokens``, and ``usage``.
        """
        self._request_counts[provider_id] = (
            self._request_counts.get(provider_id, 0) + 1
        )
        self._cost_tracking[provider_id] = (
            self._cost_tracking.get(provider_id, 0.0)
            + (response.cost or 0.0)
        )
        self._token_tracking[provider_id] = (
            self._token_tracking.get(provider_id, 0)
            + response.total_tokens
        )

    def _get_providers(self) -> Dict[str, RouterProviderConfig]:
        """Get provider configs, preferring ModelGarage when available.

        When a ModelGarage is wired, converts its ProviderConfig objects
        to RouterProviderConfig on-the-fly so the routing logic stays consistent.
        """
        providers = dict(self._providers)  # start with standalone configs

        if self._model_garage is not None:
            garage_configs = self._model_garage.list_providers()
            for cfg in garage_configs:
                pid = cfg.get("id", "")
                if not pid:
                    continue
                # Only add if not overridden by a standalone config
                if pid not in providers:
                    providers[pid] = RouterProviderConfig(
                        provider_id=pid,
                        base_url=cfg.get("baseUrl", ""),
                        api_key=cfg.get("apiKey", "") or "",
                        models=cfg.get("models", []),
                        priority=cfg.get("priority", 100),
                        health_status=cfg.get("health_status", "unknown") == "healthy",
                    )
        return providers

    def classify_complexity(
        self,
        task: str,
        tokens_estimate: Optional[int] = None,
        requires_reasoning: bool = False
    ) -> TaskComplexity:
        score = 0
        if tokens_estimate:
            if tokens_estimate > 4000:
                score += 2
            elif tokens_estimate > 1000:
                score += 1
        if requires_reasoning:
            score += 2
        complexity_keywords = ["analyze", "synthesize", "evaluate", "design", "architect"]
        simple_keywords = ["format", "convert", "extract", "list", "count", "summarize"]
        task_lower = task.lower()
        for kw in complexity_keywords:
            if kw in task_lower:
                score += 1
        for kw in simple_keywords:
            if kw in task_lower:
                score -= 1
        if score <= 0:
            return TaskComplexity.SIMPLE
        elif score <= 2:
            return TaskComplexity.STANDARD
        return TaskComplexity.COMPLEX

    def _get_preferred_models(self, complexity: TaskComplexity) -> list[str]:
        """Get preferred models for the given complexity level."""
        model_map = {
            TaskComplexity.SIMPLE: ["haiku", "llama3.1", "gemini-flash"],
            TaskComplexity.STANDARD: ["sonnet", "claude-sonnet", "gemini-pro"],
            TaskComplexity.COMPLEX: ["opus", "claude-opus", "o1-preview"],
        }
        return model_map[complexity]

    def _find_matching_model(
        self, provider: RouterProviderConfig, preferred_models: list[str]
    ) -> str | None:
        """Find a matching model from preferred list in provider's models."""
        for model in preferred_models:
            for provider_model in provider.models:
                if model in provider_model.lower():
                    return provider_model
        return None

    def _find_preferred_provider(
        self, complexity: TaskComplexity, preferred_provider: str | None
    ) -> tuple[RoutingDecision | None, list[str]]:
        """Find a provider matching preferred criteria. Returns (decision, fallback_chain)."""
        preferred_models = self._get_preferred_models(complexity)
        fallback_chain: list[str] = []
        use_preferred = preferred_provider is not None

        providers = self._get_providers()
        for pid, provider in sorted(providers.items(), key=lambda x: x[1].priority):
            if not provider.health_status:
                fallback_chain.append(pid)
                continue
            if use_preferred and pid != preferred_provider:
                continue

            matched_model = self._find_matching_model(provider, preferred_models)
            if matched_model:
                confidence = 0.9 if not use_preferred else 1.0
                return RoutingDecision(
                    provider_id=pid,
                    model=matched_model,
                    complexity=complexity,
                    fallback_chain=fallback_chain,
                    confidence=confidence
                ), fallback_chain

            fallback_chain.append(pid)

        return None, fallback_chain

    def _find_fallback_provider(
        self, complexity: TaskComplexity, fallback_chain: list[str]
    ) -> RoutingDecision | None:
        """Find any healthy provider as fallback."""
        providers = self._get_providers()
        for pid, provider in sorted(providers.items(), key=lambda x: x[1].priority):
            if provider.health_status and provider.models:
                return RoutingDecision(
                    provider_id=pid,
                    model=provider.models[0],
                    complexity=complexity,
                    fallback_chain=fallback_chain,
                    confidence=0.5
                )
        return None

    def route(
        self,
        task: str,
        preferred_provider: str | None = None,
        tokens_estimate: int | None = None,
        requires_reasoning: bool = False
    ) -> RoutingDecision:
        """Route a task to the appropriate model provider."""
        complexity = self.classify_complexity(task, tokens_estimate, requires_reasoning)

        decision, fallback_chain = self._find_preferred_provider(complexity, preferred_provider)
        if decision:
            return decision

        fallback_decision = self._find_fallback_provider(complexity, fallback_chain)
        if fallback_decision:
            return fallback_decision

        raise RuntimeError("No healthy model providers available")

    def get_stats(self) -> Dict[str, Any]:
        providers = self._get_providers()
        return {
            "agent_id": self.agent_id,
            "providers_registered": len(providers),
            "providers_healthy": sum(1 for p in providers.values() if p.health_status),
            "source": "garage" if self._model_garage is not None else "standalone",
            "request_counts": dict(self._request_counts),
            "cost_tracking": dict(self._cost_tracking),
            "token_tracking": dict(self._token_tracking),
        }


_router_registry: Dict[str, AgentModelRouter] = {}
_global_model_garage: "ModelGarage | None" = None


def set_global_model_garage(garage: "ModelGarage | None") -> None:
    """Set the global ModelGarage instance used by all new AgentModelRouter instances.

    When a ModelGarage is wired, every AgentModelRouter created via
    ``get_router()`` will use it as the shared provider config source.
    Router providers derived from the garage are merged with any standalone
    ``RouterProviderConfig`` registrations, with standalone configs taking
    precedence for override compatibility.
    """
    global _global_model_garage
    _global_model_garage = garage


def get_router(agent_id: str) -> AgentModelRouter:
    if agent_id not in _router_registry:
        _router_registry[agent_id] = AgentModelRouter(
            agent_id, model_garage=_global_model_garage,
        )
    return _router_registry[agent_id]
