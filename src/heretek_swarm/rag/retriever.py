"""Retriever exports for compatibility."""
from heretek_swarm.rag.hybrid_retriever import (
    HybridRetriever,
    HybridRetrieverConfig,
    RetrieverState,
    RetrieverError,
    RetrieverNotReady,
    RateLimitExceeded,
)
from dataclasses import dataclass, field
from typing import Dict, Any, Optional


@dataclass
class RetrievalConfig:
    top_k: int = 5
    score_threshold: float = 0.0
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class SearchResult:
    id: str
    content: str
    score: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


__all__ = [
    "HybridRetriever",
    "HybridRetrieverConfig",
    "RetrieverState",
    "RetrieverError",
    "RetrieverNotReady",
    "RateLimitExceeded",
    "RetrievalConfig",
    "SearchResult",
]
