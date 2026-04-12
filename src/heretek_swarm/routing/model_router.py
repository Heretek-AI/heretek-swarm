"""Native per-agent model routing with multi-provider support."""
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field
from enum import Enum


class TaskComplexity(Enum):
    SIMPLE = "simple"
    STANDARD = "standard"
    COMPLEX = "complex"


@dataclass
class ProviderConfig:
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
    """Per-agent model router with dynamic provider selection."""

    def __init__(self, agent_id: str, providers: Optional[List[ProviderConfig]] = None):
        self.agent_id = agent_id
        self.providers = {p.provider_id: p for p in (providers or [])}
        self._request_counts: Dict[str, int] = {}
        self._cost_tracking: Dict[str, float] = {}

    def register_provider(self, config: ProviderConfig) -> None:
        self.providers[config.provider_id] = config

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

    def route(
        self,
        task: str,
        preferred_provider: Optional[str] = None,
        tokens_estimate: Optional[int] = None,
        requires_reasoning: bool = False
    ) -> RoutingDecision:
        complexity = self.classify_complexity(task, tokens_estimate, requires_reasoning)
        model_map = {
            TaskComplexity.SIMPLE: ["haiku", "llama3.1", "gemini-flash"],
            TaskComplexity.STANDARD: ["sonnet", "claude-sonnet", "gemini-pro"],
            TaskComplexity.COMPLEX: ["opus", "claude-opus", "o1-preview"],
        }
        preferred_models = model_map[complexity]
        fallback_chain = []
        for pid, provider in sorted(self.providers.items(), key=lambda x: x[1].priority):
            if not provider.health_status:
                fallback_chain.append(pid)
                continue
            if preferred_provider and pid != preferred_provider:
                continue
            for model in preferred_models:
                if any(model in m.lower() for m in provider.models):
                    return RoutingDecision(
                        provider_id=pid,
                        model=next(m for m in provider.models if model in m.lower()),
                        complexity=complexity,
                        fallback_chain=fallback_chain,
                        confidence=0.9 if not preferred_provider else 1.0
                    )
            fallback_chain.append(pid)
        for pid, provider in sorted(self.providers.items(), key=lambda x: x[1].priority):
            if provider.health_status:
                return RoutingDecision(
                    provider_id=pid,
                    model=provider.models[0],
                    complexity=complexity,
                    fallback_chain=fallback_chain,
                    confidence=0.5
                )
        raise RuntimeError("No healthy model providers available")

    def get_stats(self) -> Dict[str, Any]:
        return {
            "agent_id": self.agent_id,
            "providers_registered": len(self.providers),
            "providers_healthy": sum(1 for p in self.providers.values() if p.health_status),
            "request_counts": dict(self._request_counts),
            "cost_tracking": dict(self._cost_tracking),
        }


_router_registry: Dict[str, AgentModelRouter] = {}


def get_router(agent_id: str) -> AgentModelRouter:
    if agent_id not in _router_registry:
        _router_registry[agent_id] = AgentModelRouter(agent_id)
    return _router_registry[agent_id]
