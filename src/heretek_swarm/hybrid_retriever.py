"""
Hybrid Retriever for Heretek Swarm RAG System.

This module provides a unified hybrid retrieval interface that combines
multiple retrieval strategies for optimal search results.

Features:
- Unified interface for hybrid retrieval
- Dynamic weight adjustment based on query characteristics
- Result fusion with configurable methods
- Performance monitoring and optimization
- Rate limiting and caching support

Usage:
    from heretek_swarm.rag.hybrid_retriever import HybridRetriever, HybridRetrieverConfig
    
    config = HybridRetrieverConfig()
    _retriever = HybridRetriever(config)
    await retriever.initialize()
    
    _results = await retriever.retrieve(
        query="What is the capital of France?",
        _top_k = 5,
    )
"""

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum
import time
import structlog
import asyncio

from .strategies import (
    RetrievalStrategyType,
    RetrievalResult,
    ReRankingStrategy,
    QueryClassifier,
    QueryType,
    RAGStrategyConfig,
    create_strategy_selector,
    StrategySelector,
)

_logger = structlog.get_logger(__name__)


class FusionMethod(str, Enum):
    """Methods for fusing retrieval results."""
    RECIPROCAL_RANK = "reciprocal_rank"  # RRF
    WEIGHTED_SUM = "weighted_sum"
    NORMALIZED_SUM = "normalized_sum"
    MAX_SCORE = "max_score"
    MIN_SCORE = "min_score"


class RetrieverState(str, Enum):
    """Retriever lifecycle states."""
    UNINITIALIZED = "uninitialized"
    INITIALIZING = "initializing"
    READY = "ready"
    DEGRADED = "degraded"
    ERROR = "error"


@dataclass
class HybridRetrieverConfig:
    """
    Configuration for the Hybrid Retriever.
    
    Attributes:
        dense_weight: Weight for dense retrieval scores (0-1)
        sparse_weight: Weight for sparse retrieval scores (0-1)
        fusion_method: Method for combining results
        rrf_k: Constant for reciprocal rank fusion
        enable_reranking: Whether to apply cross-encoder re-ranking
        rerank_top_k: Number of candidates for re-ranking
        enable_multihop: Whether to enable multi-hop retrieval
        max_hops: Maximum retrieval hops
        cache_enabled: Enable query caching
        cache_ttl_seconds: Cache time-to-live
        rate_limit_queries_per_minute: Rate limit for queries
        normalize_scores: Whether to normalize scores before fusion
        min_score_threshold: Minimum score threshold for results
        query_classification_enabled: Enable automatic query classification
    """
    dense_weight: float = 0.5
    sparse_weight: float = 0.5
    fusion_method: FusionMethod = FusionMethod.RECIPROCAL_RANK
    rrf_k: int = 60
    enable_reranking: bool = True
    rerank_top_k: int = 50
    enable_multihop: bool = True
    max_hops: int = 3
    cache_enabled: bool = True
    cache_ttl_seconds: int = 300
    rate_limit_queries_per_minute: int = 60
    normalize_scores: bool = True
    min_score_threshold: float = 0.0
    query_classification_enabled: bool = True


@dataclass
class RetrievalMetrics:
    """Metrics for retrieval operations."""
    total_queries: int = 0
    successful_queries: int = 0
    failed_queries: int = 0
    cache_hits: int = 0
    cache_misses: int = 0
    avg_latency_ms: float = 0.0
    p95_latency_ms: float = 0.0
    p99_latency_ms: float = 0.0
    avg_results_count: float = 0.0
    rate_limit_hits: int = 0
    last_query_time: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "total_queries": self.total_queries,
            "successful_queries": self.successful_queries,
            "failed_queries": self.failed_queries,
            "cache_hit_rate": self.cache_hits / max(1, self.cache_hits + self.cache_misses),
            "avg_latency_ms": self.avg_latency_ms,
            "p95_latency_ms": self.p95_latency_ms,
            "p99_latency_ms": self.p99_latency_ms,
            "avg_results_count": self.avg_results_count,
            "rate_limit_hits": self.rate_limit_hits,
            "last_query_time": self.last_query_time.isoformat() if self.last_query_time else None,
        }


@dataclass
class QueryHistoryEntry:
    """Entry in query history for rate limiting and analytics."""
    query: str
    timestamp: datetime
    latency_ms: float
    results_count: int
    strategy_used: str
    cache_hit: bool


class RateLimiter:
    """
    Token bucket rate limiter for query throttling.
    
    Implements a sliding window rate limiter to prevent
    excessive query rates.
    """
    
    def __init__(self, _queries_per_minute: int):
        self.queries_per_minute = queries_per_minute
        self._queries: List[datetime] = []
        self._lock = asyncio.Lock()
    
    async def acquire(self) -> bool:
        """
        Try to acquire a rate limit token.
        
        Returns:
            True if token acquired, False if rate limited
        """
        async with self._lock:
            _now = datetime.now(timezone.utc)
            _window_start = now.timestamp() - 60  # 1 minute window
            
            # Remove old queries outside the window
            self._queries = [
                q for q in self._queries
                if q.timestamp() > window_start
            ]
            
            # Check if under limit
            if len(self._queries) < self.queries_per_minute:
                self._queries.append(now)
                return True
            
            return False
    
    async def wait_for_token(self, _timeout: float) -> bool:
        """
        Wait for a rate limit token with timeout.
        
        Args:
            timeout: Maximum time to wait in seconds
            
        Returns:
            True if token acquired, False if timeout
        """
        _start_time = time.time()
        
        while time.time() - start_time < timeout:
            if await self.acquire():
                return True
            await asyncio.sleep(0.1)
        
        return False
    
    def get_remaining(self) -> int:
        """Get remaining queries in current window."""
        _now = datetime.now(timezone.utc)
        _window_start = now.timestamp() - 60
        _current_count = sum(1 for q in self._queries if q.timestamp() > window_start)
        return max(0, self.queries_per_minute - current_count)


class HybridRetriever:
    """
    Hybrid Retriever combining multiple retrieval strategies.
    
    This class provides a unified interface for hybrid retrieval,
    combining dense (vector) and sparse (BM25) retrieval with
    configurable fusion methods and optional re-ranking.
    
    Features:
    - Multi-strategy retrieval with configurable weights
    - Reciprocal rank fusion and weighted combination
    - Cross-encoder re-ranking
    - Query caching and rate limiting
    - Performance metrics and monitoring
    - Zero-trust authentication support
    """
    
    def __init__(self, _config: Optional[HybridRetrieverConfig], _embedding_provider: Optional[Any], _vector_store: Optional[Any], _sparse_index: Optional[Any], _cross_encoder: Optional[Any]):
        self.config = config or HybridRetrieverConfig()
        self.embedding_provider = embedding_provider
        self.vector_store = vector_store
        self.sparse_index = sparse_index
        self.cross_encoder = cross_encoder
        
        self._state = RetrieverState.UNINITIALIZED
        self._strategy_selector: Optional[StrategySelector] = None
        self._reranker: Optional[ReRankingStrategy] = None
        self._classifier = QueryClassifier()
        self._rate_limiter = RateLimiter(self.config.rate_limit_queries_per_minute)
        self._metrics = RetrievalMetrics()
        self._query_history: List[QueryHistoryEntry] = []
        self._max_history = 1000
        
        # Cache
        self._query_cache: Dict[str, Tuple[List[RetrievalResult], datetime]] = {}
    
    @property
    def state(self) -> RetrieverState:
        """Get current retriever state."""
        return self._state
    
    async def initialize(self) -> None:
        """
        Initialize the hybrid retriever.
        
        Sets up strategy selector, reranker, and validates dependencies.
        """
        self._state = RetrieverState.INITIALIZING
        
        try:
            # Create strategy config
            _strategy_config = RAGStrategyConfig(
                _dense_enabled = self.embedding_provider is not None,
                _sparse_enabled = self.sparse_index is not None,
                _hybrid_enabled = True,
                dense_weight=self.config.dense_weight,
                sparse_weight=self.config.sparse_weight,
                fusion_method=self.config.fusion_method.value,
                rrf_k=self.config.rrf_k,
                _multi_hop_enabled = self.config.enable_multihop,
                _max_hops = self.config.max_hops,
                _re_ranking_enabled = self.config.enable_reranking,
                _re_rank_limit = self.config.rerank_top_k,
                cache_enabled=self.config.cache_enabled,
                cache_ttl_seconds=self.config.cache_ttl_seconds,
            )
            
            # Create strategy selector
            self._strategy_selector = create_strategy_selector(
                config=strategy_config,
                embedding_provider=self.embedding_provider,
                _vector_store = self.vector_store,
                sparse_index=self.sparse_index,
                cross_encoder=self.cross_encoder,
            )
            
            # Create dedicated reranker
            if self.config.enable_reranking and self.cross_encoder:
                self._reranker = ReRankingStrategy(
                    _cross_encoder = self.cross_encoder,
                    _re_rank_limit = self.config.rerank_top_k,
                )
            
            self._state = RetrieverState.READY
            logger.info("hybrid_retriever_initialized",
                       _dense_enabled = self.embedding_provider is not None,
                       _sparse_enabled = self.sparse_index is not None,
                       _reranking_enabled = self.config.enable_reranking)
            
        except Exception as e:
            self._state = RetrieverState.ERROR
            logger.error("hybrid_retriever_initialization_failed", error=str(e))
            raise
    
    def _hash_query(self, _query: str) -> str:
        """Create hash of query for caching."""
        import hashlib
        return hashlib.sha256(query.lower().strip().encode()).hexdigest()
    
    def _get_from_cache(self, _query_hash: str) -> Optional[List[RetrievalResult]]:
        """Get cached results if available and not expired."""
        if not self.config.cache_enabled:
            return None
        
        _entry = self._query_cache.get(query_hash)
        if entry:
            results, created_at = entry
            _age = (datetime.now(timezone.utc) - created_at).total_seconds()
            if age < self.config.cache_ttl_seconds:
                self._metrics.cache_hits += 1
                return results
        
        self._metrics.cache_misses += 1
        return None
    
    def _store_in_cache(self, _query_hash: str, _results: List[RetrievalResult]) -> None:
        """Store results in cache."""
        if not self.config.cache_enabled:
            return
        
        self._query_cache[query_hash] = (results, datetime.now(timezone.utc))
        
        # Clean old cache
        if len(self._query_cache) > 1000:
            _now = datetime.now(timezone.utc)
            _expired = [
                k for k, (_, created_at) in self._query_cache.items()
                if (now - created_at).total_seconds() > self.config.cache_ttl_seconds
            ]
            for k in expired:
                del self._query_cache[k]
    
    def _normalize_scores(self, _results: List[RetrievalResult]) -> List[RetrievalResult]:
        """Normalize scores to 0-1 range using min-max normalization."""
        if not results:
            return results
        
        _scores = [r.score for r in results]
        min_score = min(scores)
        _max_score = max(scores)
        _score_range = max_score - min_score if max_score > min_score else 1.0
        
        for result in results:
            result.score = (result.score - min_score) / score_range
        
        return results
    
    def _fuse_results(self, _dense_results: List[RetrievalResult], _sparse_results: List[RetrievalResult]) -> List[RetrievalResult]:
        """
        Fuse results from dense and sparse retrieval.
        
        Args:
            dense_results: Results from dense retrieval
            sparse_results: Results from sparse retrieval
            
        Returns:
            Fused and ranked results
        """
        if not dense_results and not sparse_results:
            return []
        
        if not dense_results:
            return sparse_results
        
        if not sparse_results:
            return dense_results
        
        if self.config.fusion_method == FusionMethod.RECIPROCAL_RANK:
            return self._reciprocal_rank_fusion(dense_results, sparse_results)
        elif self.config.fusion_method == FusionMethod.WEIGHTED_SUM:
            return self._weighted_sum_fusion(dense_results, sparse_results)
        elif self.config.fusion_method == FusionMethod.NORMALIZED_SUM:
            return self._normalized_sum_fusion(dense_results, sparse_results)
        elif self.config.fusion_method == FusionMethod.MAX_SCORE:
            return self._max_score_fusion(dense_results, sparse_results)
        else:
            return self._reciprocal_rank_fusion(dense_results, sparse_results)
    
    def _reciprocal_rank_fusion(self, _dense_results: List[RetrievalResult], _sparse_results: List[RetrievalResult]) -> List[RetrievalResult]:
        """Apply Reciprocal Rank Fusion (RRF)."""
        # Build rank maps
        dense_ranks: Dict[str, int] = {r.source: i + 1 for i, r in enumerate(dense_results)}
        sparse_ranks: Dict[str, int] = {r.source: i + 1 for i, r in enumerate(sparse_results)}
        
        # Calculate RRF scores
        _all_sources = set(dense_ranks.keys()) | set(sparse_ranks.keys())
        rrf_scores: Dict[str, float] = {}
        source_to_result: Dict[str, RetrievalResult] = {}
        
        for source in all_sources:
            _dense_rank = dense_ranks.get(source, len(dense_results) + 1)
            _sparse_rank = sparse_ranks.get(source, len(sparse_results) + 1)
            
            _rrf_score = 0.0
            if dense_rank <= len(dense_results):
                rrf_score += self.config.dense_weight / (self.config.rrf_k + dense_rank)
            if sparse_rank <= len(sparse_results):
                rrf_score += self.config.sparse_weight / (self.config.rrf_k + sparse_rank)
            
            rrf_scores[source] = rrf_score
            
            # Keep reference to result
            if source in dense_ranks:
                for r in dense_results:
                    if r.source == source:
                        source_to_result[source] = r
                        r.strategy = RetrievalStrategyType.HYBRID
                        break
            elif source in sparse_ranks:
                for r in sparse_results:
                    if r.source == source:
                        source_to_result[source] = r
                        r.strategy = RetrievalStrategyType.HYBRID
                        break
        
        # Sort and build fused results
        _sorted_sources = sorted(rrf_scores.keys(), key=lambda s: rrf_scores[s], reverse=True)
        _fused_results = []
        
        for source in sorted_sources:
            _result = source_to_result.get(source)
            if result:
                result.score = rrf_scores[source]
                fused_results.append(result)
        
        return fused_results
    
    def _weighted_sum_fusion(self, _dense_results: List[RetrievalResult], _sparse_results: List[RetrievalResult]) -> List[RetrievalResult]:
        """Apply weighted sum fusion with score normalization."""
        # Normalize scores
        _dense_normalized = self._normalize_scores(dense_results.copy())
        _sparse_normalized = self._normalize_scores(sparse_results.copy())
        
        # Build score maps
        dense_scores: Dict[str, float] = {r.source: r.score for r in dense_normalized}
        sparse_scores: Dict[str, float] = {r.source: r.score for r in sparse_normalized}
        
        # Combine scores
        _all_sources = set(dense_scores.keys()) | set(sparse_scores.keys())
        combined_scores: Dict[str, float] = {}
        source_to_result: Dict[str, RetrievalResult] = {}
        
        for source in all_sources:
            _combined_score = (
                self.config.dense_weight * dense_scores.get(source, 0) +
                self.config.sparse_weight * sparse_scores.get(source, 0)
            )
            combined_scores[source] = combined_score
            
            # Keep reference to result
            for r in dense_results + sparse_results:
                if r.source == source:
                    source_to_result[source] = r
                    r.strategy = RetrievalStrategyType.HYBRID
                    break
        
        # Sort and build results
        _sorted_sources = sorted(combined_scores.keys(), key=lambda s: combined_scores[s], reverse=True)
        _fused_results = []
        
        for source in sorted_sources:
            _result = source_to_result.get(source)
            if result:
                result.score = combined_scores[source]
                fused_results.append(result)
        
        return fused_results
    
    def _normalized_sum_fusion(self, _dense_results: List[RetrievalResult], _sparse_results: List[RetrievalResult]) -> List[RetrievalResult]:
        """Apply normalized sum fusion (equal weights)."""
        self.config.dense_weight = 0.5
        self.config.sparse_weight = 0.5
        return self._weighted_sum_fusion(dense_results, sparse_results)
    
    def _max_score_fusion(self, _dense_results: List[RetrievalResult], _sparse_results: List[RetrievalResult]) -> List[RetrievalResult]:
        """Apply max score fusion (take maximum score from either method)."""
        _all_results = {}
        
        for result in dense_results + sparse_results:
            if result.source not in all_results:
                result.strategy = RetrievalStrategyType.HYBRID
                all_results[result.source] = result
            else:
                # Keep the result with higher score
                if result.score > all_results[result.source].score:
                    result.strategy = RetrievalStrategyType.HYBRID
                    all_results[result.source] = result
        
        # Sort by score
        _fused_results = sorted(all_results.values(), key=lambda r: r.score, reverse=True)
        return fused_results
    
    async def _apply_reranking(self, _query: str, _results: List[RetrievalResult], _top_k: int) -> List[RetrievalResult]:
        """Apply cross-encoder re-ranking to results."""
        if not self._reranker or not results:
            return results[:top_k]
        
        _reranked = await self._reranker.retrieve(
            query=query,
            _top_k = top_k,
            _initial_results = results,
        )
        
        return reranked
    
    def _record_query(self, _query: str, _latency_ms: float, _results_count: int, _strategy: str, _cache_hit: bool) -> None:
        """Record query in history and update metrics."""
        _now = datetime.now(timezone.utc)
        
        # Update metrics
        self._metrics.total_queries += 1
        self._metrics.last_query_time = now
        
        if cache_hit:
            self._metrics.cache_hits += 1
        else:
            self._metrics.cache_misses += 1
        
        # Update latency stats (simple moving average)
        n = self._metrics.total_queries
        self._metrics.avg_latency_ms = (
            (self._metrics.avg_latency_ms * (n - 1) + latency_ms) / n
        )
        
        # Update results count avg
        self._metrics.avg_results_count = (
            (self._metrics.avg_results_count * (n - 1) + results_count) / n
        )
        
        # Record history entry
        _entry = QueryHistoryEntry(
            query=query,
            _timestamp = now,
            _latency_ms = latency_ms,
            _results_count = results_count,
            _strategy_used = strategy,
            cache_hit=cache_hit,
        )
        self._query_history.append(entry)
        
        # Trim history
        if len(self._query_history) > self._max_history:
            self._query_history = self._query_history[-self._max_history:]
    
    async def retrieve(self, _query: str, _top_k: int, _filters: Optional[Dict[str, Any]], _use_multihop: Optional[bool], _apply_reranking: Optional[bool], _authenticated: bool) -> List[RetrievalResult]:
        """
        Retrieve relevant documents using hybrid retrieval.
        
        Args:
            query: Search query
            top_k: Number of results to return
            filters: Optional metadata filters
            use_multihop: Override multi-hop setting
            apply_reranking: Override re-ranking setting
            authenticated: Whether request is authenticated (for rate limiting)
            
        Returns:
            List of retrieval results
            
        Raises:
            RateLimitExceeded: If rate limit is exceeded
            RetrieverNotReady: If retriever is not initialized
        """
        if self._state != RetrieverState.READY:
            raise RetrieverNotReady(f"Retriever state: {self._state.value}")
        
        _start_time = time.time()
        cache_hit = False
        
        # Check rate limit (skip for authenticated requests if configured)
        if not authenticated:
            if not await self._rate_limiter.acquire():
                self._metrics.rate_limit_hits += 1
                raise RateLimitExceeded(
                    f"Rate limit exceeded: {self.config.rate_limit_queries_per_minute} queries/minute"
                )
        
        # Check cache
        _query_hash = self._hash_query(query)
        _cached_results = self._get_from_cache(query_hash)
        if cached_results:
            cache_hit = True
            _latency_ms = (time.time() - start_time) * 1000
            self._record_query(query, latency_ms, len(cached_results), "cache", True)
            return cached_results[:top_k]
        
        try:
            # Determine strategy
            _strategy = RetrievalStrategyType.HYBRID
            
            if self.config.query_classification_enabled:
                _query_type = self._classifier.classify(query)
                if query_type == QueryType.MULTI_STEP and (use_multihop is not False):
                    _strategy = RetrievalStrategyType.MULTI_HOP
            
            # Get strategy from selector
            if not self._strategy_selector:
                raise RetrieverError("Strategy selector not initialized")
            
            # Execute retrieval
            _results = await self._strategy_selector.retrieve(
                _query = query,
                _top_k = self.config.rerank_top_k if apply_reranking else top_k,
                _strategy = strategy,
                _filters = filters,
            )
            
            # Apply re-ranking if enabled
            if (apply_reranking or self.config.enable_reranking) and self._reranker and results:
                _results = await self._apply_reranking(query, results, top_k)
            
            # Apply score threshold
            if self.config.min_score_threshold > 0:
                _results = [r for r in results if r.score >= self.config.min_score_threshold]
            
            # Limit to top_k
            _results = results[:top_k]
            
            # Normalize scores if configured
            if self.config.normalize_scores and results:
                _results = self._normalize_scores(results)
            
            # Cache results
            self._store_in_cache(query_hash, results)
            
            # Record metrics
            _latency_ms = (time.time() - start_time) * 1000
            self._metrics.successful_queries += 1
            self._record_query(query, latency_ms, len(results), strategy.value, cache_hit)
            
            logger.debug("hybrid_retrieval_completed",
                        _query = query[:50] if len(query) > 50 else query,
                        _results_count = len(results),
                        _latency_ms = latency_ms,
                        _strategy = strategy.value,
                        cache_hit=cache_hit)
            
            return results
            
        except Exception as e:
            self._metrics.failed_queries += 1
            _latency_ms = (time.time() - start_time) * 1000
            self._record_query(query, latency_ms, 0, "error", cache_hit)
            
            logger.error("hybrid_retrieval_error",
                        _query = query[:50] if len(query) > 50 else query,
                        _error = str(e))
            raise RetrieverError(f"Retrieval failed: {str(e)}")
    
    async def retrieve_with_context(self, _query: str, _context: Optional[str], _top_k: int, **kwargs) -> Tuple[str, List[RetrievalResult]]:
        """
        Retrieve and format results with context.
        
        Args:
            query: Search query
            context: Optional additional context
            top_k: Number of results
            **kwargs: Additional arguments for retrieve()
            
        Returns:
            Tuple of (formatted context string, retrieval results)
        """
        _results = await self.retrieve(query, top_k, **kwargs)
        
        # Format context from results
        _context_parts = []
        if context:
            context_parts.append(f"Context: {context}")
        
        for i, result in enumerate(results, 1):
            context_parts.append(f"[{i}] {result.content}")
        
        _formatted_context = "\n\n".join(context_parts)
        
        return formatted_context, results
    
    def get_metrics(self) -> RetrievalMetrics:
        """Get retrieval metrics."""
        return self._metrics
    
    def get_stats(self) -> Dict[str, Any]:
        """Get detailed retriever statistics."""
        return {
            "state": self._state.value,
            "metrics": self._metrics.to_dict(),
            "config": {
                "fusion_method": self.config.fusion_method.value,
                "dense_weight": self.config.dense_weight,
                "sparse_weight": self.config.sparse_weight,
                "cache_enabled": self.config.cache_enabled,
                "reranking_enabled": self.config.enable_reranking,
            },
            "rate_limit": {
                "remaining": self._rate_limiter.get_remaining(),
                "limit": self.config.rate_limit_queries_per_minute,
            },
            "cache_size": len(self._query_cache),
        }
    
    def export_prometheus_metrics(self) -> str:
        """Export metrics in Prometheus format."""
        _lines = [
            "# HELP heretek_rag_total_queries Total RAG queries",
            "# TYPE heretek_rag_total_queries counter",
            f"heretek_rag_total_queries {self._metrics.total_queries}",
            "",
            "# HELP heretek_rag_successful_queries Successful RAG queries",
            "# TYPE heretek_rag_successful_queries counter",
            f"heretek_rag_successful_queries {self._metrics.successful_queries}",
            "",
            "# HELP heretek_rag_failed_queries Failed RAG queries",
            "# TYPE heretek_rag_failed_queries counter",
            f"heretek_rag_failed_queries {self._metrics.failed_queries}",
            "",
            "# HELP heretek_rag_cache_hits RAG cache hits",
            "# TYPE heretek_rag_cache_hits counter",
            f"heretek_rag_cache_hits {self._metrics.cache_hits}",
            "",
            "# HELP heretek_rag_cache_misses RAG cache misses",
            "# TYPE heretek_rag_cache_misses counter",
            f"heretek_rag_cache_misses {self._metrics.cache_misses}",
            "",
            "# HELP heretek_rag_avg_latency_ms Average RAG query latency",
            "# TYPE heretek_rag_avg_latency_ms gauge",
            f"heretek_rag_avg_latency_ms {self._metrics.avg_latency_ms}",
            "",
            "# HELP heretek_rag_rate_limit_hits Rate limit hits",
            "# TYPE heretek_rag_rate_limit_hits counter",
            f"heretek_rag_rate_limit_hits {self._metrics.rate_limit_hits}",
            "",
        ]
        return "\n".join(lines)
    
    async def close(self) -> None:
        """Close the retriever and release resources."""
        self._state = RetrieverState.UNINITIALIZED
        self._query_cache.clear()
        self._query_history.clear()
        logger.info("hybrid_retriever_closed")


class RetrieverError(Exception):
    """Base exception for retriever errors."""
    pass


class RetrieverNotReady(RetrieverError):
    """Exception raised when retriever is not ready."""
    pass


class RateLimitExceeded(RetrieverError):
    """Exception raised when rate limit is exceeded."""
    pass


# Convenience function for creating configured retriever
def create_hybrid_retriever(_config: Optional[HybridRetrieverConfig], _embedding_provider: Optional[Any], _vector_store: Optional[Any], _sparse_index: Optional[Any], _cross_encoder: Optional[Any]) -> HybridRetriever:
    """
    Create and initialize a hybrid retriever.
    
    Args:
        config: Retriever configuration
        embedding_provider: Embedding provider instance
        vector_store: Vector store instance
        sparse_index: Sparse index instance
        cross_encoder: Cross-encoder model instance
        
    Returns:
        Initialized HybridRetriever instance
    """
    _retriever = HybridRetriever(
        _config = config,
        _embedding_provider = embedding_provider,
        _vector_store = vector_store,
        _sparse_index = sparse_index,
        _cross_encoder = cross_encoder,
    )
    return retriever
