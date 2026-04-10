"""
Advanced RAG Retrieval Strategies for Heretek Swarm.

This module implements multiple retrieval strategies for the RAG system:
- Dense retrieval (vector similarity)
- Sparse retrieval (BM25)
- Hybrid retrieval (combined scoring)
- Multi-hop retrieval (chained queries)
- Re-ranking (cross-encoder scoring)

Source Pattern: AgenticRAG-Survey (advanced retrieval strategies)

Usage:
    from heretek_swarm.rag.strategies import (
        DenseRetrievalStrategy,
        SparseRetrievalStrategy,
        HybridRetrievalStrategy,
        MultiHopRetrievalStrategy,
        ReRankingStrategy,
        StrategySelector,
    )
    
    # Use strategy selector for automatic selection
    _selector = StrategySelector()
    results = await selector.retrieve(query, top_k=5)
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from enum import Enum
import math
import hashlib
import time
import structlog

_logger = structlog.get_logger(__name__)


class RetrievalStrategyType(str, Enum):
    """Types of retrieval strategies."""
    DENSE = "dense"
    SPARSE = "sparse"
    HYBRID = "hybrid"
    MULTI_HOP = "multi_hop"
    RE_RANKING = "re_ranking"


class QueryType(str, Enum):
    """Types of queries for strategy selection."""
    FACTUAL = "factual"  # Specific fact lookup
    EXPLANATORY = "explanatory"  # How/why questions
    COMPARATIVE = "comparative"  # Comparison questions
    PROCEDURAL = "procedural"  # How-to questions
    EXPLORATORY = "exploratory"  # Broad topic exploration
    MULTI_STEP = "multi_step"  # Requires multiple hops


@dataclass
class RetrievalResult:
    """
    Result from a retrieval strategy.
    
    Attributes:
        content: Retrieved content
        score: Relevance score (0-1)
        source: Source document/chunk ID
        metadata: Additional metadata
        strategy: Strategy that produced this result
        latency_ms: Time taken for retrieval
    """
    content: str
    score: float
    source: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    strategy: RetrievalStrategyType = RetrievalStrategyType.DENSE
    latency_ms: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "content": self.content,
            "score": self.score,
            "source": self.source,
            "metadata": self.metadata,
            "strategy": self.strategy.value,
            "latency_ms": self.latency_ms,
        }


@dataclass
class QueryCacheEntry:
    """Cached query result."""
    query_hash: str
    results: List[RetrievalResult]
    created_at: datetime
    access_count: int = 1
    last_accessed: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    
    def is_expired(self, _ttl_seconds: int) -> bool:
        """Check if cache entry has expired."""
        _age = (datetime.now(timezone.utc) - self.created_at).total_seconds()
        return age > ttl_seconds


class BaseRetrievalStrategy(ABC):
    """
    Abstract base class for retrieval strategies.
    
    All retrieval strategies must implement this interface.
    """
    
    def __init__(self, _name: str):
        self.name = name
        self._stats: Dict[str, Any] = {
            "queries_executed": 0,
            "avg_latency_ms": 0.0,
            "total_latency_ms": 0.0,
        }
    
    @abstractmethod
    async def retrieve(self, _query: str, _top_k: int, **kwargs) -> List[RetrievalResult]:
        """
        Retrieve relevant documents for a query.
        
        Args:
            query: Search query
            top_k: Number of results to return
            **kwargs: Strategy-specific parameters
            
        Returns:
            List of retrieval results
        """
        pass
    
    @property
    @abstractmethod
    def strategy_type(self) -> RetrievalStrategyType:
        """Return the strategy type."""
        pass
    
    def _track_latency(self, _start_time: float, _results: List[RetrievalResult]) -> None:
        """Track latency statistics."""
        latency_ms = (time.time() - start_time) * 1000
        self._stats["queries_executed"] += 1
        self._stats["total_latency_ms"] += latency_ms
        self._stats["avg_latency_ms"] = (
            self._stats["total_latency_ms"] / self._stats["queries_executed"]
        )
        
        # Add latency to results
        for result in results:
            result.latency_ms = latency_ms
    
    def get_stats(self) -> Dict[str, Any]:
        """Get strategy statistics."""
        return self._stats.copy()


class DenseRetrievalStrategy(BaseRetrievalStrategy):
    """
    Dense retrieval using vector similarity.
    
    Uses embedding vectors and cosine similarity for semantic search.
    Best for: Semantic similarity, concept matching, paraphrase detection.
    
    Features:
    - Vector embedding similarity (cosine, dot product, Euclidean)
    - Support for multiple embedding providers
    - Configurable similarity thresholds
    """
    
    def __init__(self, _embedding_provider: Optional[Any], _vector_store: Optional[Any], _similarity_metric: str, _similarity_threshold: float):
        super().__init__("dense_retrieval")
        self.embedding_provider = embedding_provider
        self.vector_store = vector_store
        self.similarity_metric = similarity_metric
        self.similarity_threshold = similarity_threshold
    
    @property
    def strategy_type(self) -> RetrievalStrategyType:
        return RetrievalStrategyType.DENSE
    
    async def retrieve(self, _query: str, _top_k: int, _filters: Optional[Dict[str, Any]], **kwargs) -> List[RetrievalResult]:
        """
        Retrieve using dense vector similarity.
        
        Args:
            query: Search query
            top_k: Number of results
            filters: Metadata filters
            **kwargs: Additional parameters
            
        Returns:
            List of retrieval results
        """
        _start_time = time.time()
        
        if not self.embedding_provider or not self.vector_store:
            logger.warning("dense_retrieval_unavailable", 
                          _reason = "embedding_provider or vector_store not configured")
            return []
        
        try:
            # Generate query embedding
            _query_embedding = await self.embedding_provider.embed(query)
            
            # Search vector store
            results = await self.vector_store.search(
                _query_vector = query_embedding,
                _top_k = top_k,
                _filters = filters,
                similarity_metric=self.similarity_metric,
            )
            
            # Convert to RetrievalResult
            _retrieval_results = []
            for doc in results:
                score = doc.get("score", doc.get("similarity", 0.5))
                if score >= self.similarity_threshold:
                    retrieval_results.append(RetrievalResult(
                        content=doc.get("content", ""),
                        score=score,
                        source=doc.get("id", doc.get("source", "unknown")),
                        metadata=doc.get("metadata", {}),
                        strategy=self.strategy_type,
                    ))
            
            self._track_latency(start_time, retrieval_results)
            
            logger.debug("dense_retrieval_completed",
                        _query = query[:50] if len(query) > 50 else query,
                        _results_count = len(retrieval_results),
                        latency_ms=retrieval_results[0].latency_ms if retrieval_results else 0)
            
            return retrieval_results[:top_k]
            
        except Exception as e:
            logger.error("dense_retrieval_error", error=str(e))
            self._track_latency(start_time, [])
            return []


class SparseRetrievalStrategy(BaseRetrievalStrategy):
    """
    Sparse retrieval using BM25 (Best Matching 25).
    
    Traditional keyword-based retrieval using term frequency and inverse document frequency.
    Best for: Exact keyword matching, technical terms, named entities.
    
    Features:
    - BM25 scoring with configurable k1 and b parameters
    - TF-IDF fallback option
    - Token normalization and stemming
    """
    
    def __init__(self, _index: Optional[Any], _k1: float, _b: float, _min_term_frequency: int):
        super().__init__("sparse_retrieval")
        self.index = index
        self.k1 = k1  # BM25 term frequency saturation
        self.b = b    # BM25 document length normalization
        self.min_term_frequency = min_term_frequency
        self._document_lengths: Dict[str, int] = {}
        self._avg_doc_length: float = 0.0
        self._num_documents: int = 0
        self._idf_cache: Dict[str, float] = {}
    
    @property
    def strategy_type(self) -> RetrievalStrategyType:
        return RetrievalStrategyType.SPARSE
    
    def _tokenize(self, _text: str) -> List[str]:
        """Tokenize text into terms."""
        import re
        # Simple tokenization - can be enhanced with stemming, lemmatization
        _tokens = re.findall(r'\b[a-zA-Z][a-zA-Z0-9-]*[a-zA-Z0-9]\b|\b[a-zA-Z]\b', text.lower())
        return tokens
    
    def _calculate_bm25_score(self, _term: str, _doc_id: str, _term_frequency: int, _doc_length: int) -> float:
        """
        Calculate BM25 score for a term in a document.
        
        BM25 formula:
        score = IDF(q_i) * (f(q_i, d) * (k1 + 1)) / (f(q_i, d) + k1 * (1 - b + b * |d|/avgdl))
        
        Where:
        - f(q_i, d): term frequency of query term q_i in document d
        - |d|: document length
        - avgdl: average document length
        - k1, b: free parameters
        """
        if self._num_documents == 0:
            return 0.0
        
        # Calculate IDF
        if term not in self._idf_cache:
            # IDF would be calculated from document frequency
            # This is a simplified version
            self._idf_cache[term] = math.log(
                (self._num_documents + 1) / (1 + 1)  # Placeholder
            )
        
        _idf = self._idf_cache[term]
        
        # BM25 term score
        _numerator = term_frequency * (self.k1 + 1)
        _denominator = term_frequency + self.k1 * (1 - self.b + self.b * doc_length / self._avg_doc_length)
        
        return idf * (numerator / denominator) if denominator > 0 else 0.0
    
    async def retrieve(self, _query: str, _top_k: int, _filters: Optional[Dict[str, Any]], **kwargs) -> List[RetrievalResult]:
        """
        Retrieve using BM25 sparse retrieval.
        
        Args:
            query: Search query
            top_k: Number of results
            filters: Metadata filters
            **kwargs: Additional parameters
            
        Returns:
            List of retrieval results
        """
        _start_time = time.time()
        
        if not self.index:
            logger.warning("sparse_retrieval_unavailable", reason="index not configured")
            return []
        
        try:
            # Tokenize query
            _query_terms = self._tokenize(query)
            
            if not query_terms:
                return []
            
            # Search index
            results = await self.index.search(
                _query_terms = query_terms,
                _top_k = top_k,
                _filters = filters,
                _k1 = self.k1,
                b=self.b,
            )
            
            # Convert to RetrievalResult
            _retrieval_results = []
            for doc in results:
                retrieval_results.append(RetrievalResult(
                    content=doc.get("content", ""),
                    score=doc.get("bm25_score", doc.get("score", 0.5)),
                    source=doc.get("id", doc.get("source", "unknown")),
                    metadata=doc.get("metadata", {}),
                    strategy=self.strategy_type,
                ))
            
            self._track_latency(start_time, retrieval_results)
            
            logger.debug("sparse_retrieval_completed",
                        _query = query[:50] if len(query) > 50 else query,
                        _results_count = len(retrieval_results),
                        latency_ms=retrieval_results[0].latency_ms if retrieval_results else 0)
            
            return retrieval_results[:top_k]
            
        except Exception as e:
            logger.error("sparse_retrieval_error", error=str(e))
            self._track_latency(start_time, [])
            return []


class HybridRetrievalStrategy(BaseRetrievalStrategy):
    """
    Hybrid retrieval combining dense and sparse methods.
    
    Combines vector similarity (dense) with BM25 (sparse) using reciprocal rank fusion (RRF)
    or weighted score combination for improved retrieval quality.
    
    Best for: General purpose retrieval, combining semantic and keyword matching.
    
    Features:
    - Reciprocal Rank Fusion (RRF)
    - Weighted score combination
    - Configurable dense/sparse balance
    - Normalization options
    """
    
    def __init__(self, _dense_strategy: Optional[DenseRetrievalStrategy], _sparse_strategy: Optional[SparseRetrievalStrategy], _dense_weight: float, _sparse_weight: float, _fusion_method: str,  # "rrf" or "weighted"
        rrf_k: int):  # RRF constant
        super().__init__("hybrid_retrieval")
        self.dense_strategy = dense_strategy
        self.sparse_strategy = sparse_strategy
        self.dense_weight = dense_weight
        self.sparse_weight = sparse_weight
        self.fusion_method = fusion_method
        self.rrf_k = rrf_k
    
    @property
    def strategy_type(self) -> RetrievalStrategyType:
        return RetrievalStrategyType.HYBRID
    
    def _reciprocal_rank_fusion(self, _dense_results: List[RetrievalResult], _sparse_results: List[RetrievalResult]) -> List[RetrievalResult]:
        """
        Apply Reciprocal Rank Fusion (RRF) to combine results.
        
        RRF formula: score(d) = sum(1 / (k + rank_i(d))) for each result list i
        
        Where k is a constant (typically 60) that controls the impact of rank.
        """
        # Build rank maps
        dense_ranks: Dict[str, int] = {}
        sparse_ranks: Dict[str, int] = {}
        
        for i, result in enumerate(dense_results):
            dense_ranks[result.source] = i + 1
        
        for i, result in enumerate(sparse_results):
            sparse_ranks[result.source] = i + 1
        
        # Calculate RRF scores
        _all_sources = set(dense_ranks.keys()) | set(sparse_ranks.keys())
        rrf_scores: Dict[str, float] = {}
        source_to_result: Dict[str, RetrievalResult] = {}
        
        for source in all_sources:
            _dense_rank = dense_ranks.get(source, len(dense_results) + 1)
            _sparse_rank = sparse_ranks.get(source, len(sparse_results) + 1)
            
            _rrf_score = 0.0
            if dense_rank <= len(dense_results):
                rrf_score += 1.0 / (self.rrf_k + dense_rank)
            if sparse_rank <= len(sparse_results):
                rrf_score += 1.0 / (self.rrf_k + sparse_rank)
            
            rrf_scores[source] = rrf_score
            
            # Keep reference to result (prefer dense if available)
            if source in dense_ranks:
                for r in dense_results:
                    if r.source == source:
                        source_to_result[source] = r
                        break
            elif source in sparse_ranks:
                for r in sparse_results:
                    if r.source == source:
                        source_to_result[source] = r
                        break
        
        # Sort by RRF score
        _sorted_sources = sorted(rrf_scores.keys(), key=lambda s: rrf_scores[s], reverse=True)
        
        # Build fused results
        _fused_results = []
        for source in sorted_sources:
            result = source_to_result.get(source)
            if result:
                result.score = rrf_scores[source]
                fused_results.append(result)
        
        return fused_results
    
    def _weighted_combination(self, _dense_results: List[RetrievalResult], _sparse_results: List[RetrievalResult]) -> List[RetrievalResult]:
        """
        Combine results using weighted score combination.
        
        Normalizes scores from both methods and combines with weights.
        """
        # Normalize scores (min-max normalization)
        def normalize_scores(_results: List[RetrievalResult]) -> Dict[str, float]:
            if not results:
                return {}
            
            _scores = [r.score for r in results]
            _min_score = min(scores)
            _max_score = max(scores)
            _score_range = max_score - min_score if max_score > min_score else 1.0
            
            return {
                r.source: (r.score - min_score) / score_range
                for r in results
            }
        
        _dense_normalized = normalize_scores(dense_results)
        _sparse_normalized = normalize_scores(sparse_results)
        
        # Combine scores
        _all_sources = set(dense_normalized.keys()) | set(sparse_normalized.keys())
        combined_scores: Dict[str, float] = {}
        source_to_result: Dict[str, RetrievalResult] = {}
        
        for source in all_sources:
            _dense_score = dense_normalized.get(source, 0.0)
            _sparse_score = sparse_normalized.get(source, 0.0)
            
            _combined_score = (
                self.dense_weight * dense_score +
                self.sparse_weight * sparse_score
            )
            combined_scores[source] = combined_score
            
            # Keep reference to result
            for r in dense_results + sparse_results:
                if r.source == source:
                    source_to_result[source] = r
                    r.strategy = self.strategy_type
                    break
        
        # Sort by combined score
        _sorted_sources = sorted(combined_scores.keys(), key=lambda s: combined_scores[s], reverse=True)
        
        # Build combined results
        _combined_results = []
        for source in sorted_sources:
            result = source_to_result.get(source)
            if result:
                result.score = combined_scores[source]
                combined_results.append(result)
        
        return combined_results
    
    async def retrieve(self, _query: str, _top_k: int, _filters: Optional[Dict[str, Any]], **kwargs) -> List[RetrievalResult]:
        """
        Retrieve using hybrid dense + sparse combination.
        
        Args:
            query: Search query
            top_k: Number of results
            filters: Metadata filters
            **kwargs: Additional parameters
            
        Returns:
            List of retrieval results
        """
        _start_time = time.time()
        
        # Execute both strategies in parallel
        _dense_task = self.dense_strategy.retrieve(query, top_k * 2, filters) if self.dense_strategy else None
        _sparse_task = self.sparse_strategy.retrieve(query, top_k * 2, filters) if self.sparse_strategy else None
        
        _dense_results = await dense_task if dense_task else []
        _sparse_results = await sparse_task if sparse_task else []
        
        # Fuse results
        if self.fusion_method == "rrf":
            _fused_results = self._reciprocal_rank_fusion(dense_results, sparse_results)
        else:
            _fused_results = self._weighted_combination(dense_results, sparse_results)
        
        # Limit to top_k
        _final_results = fused_results[:top_k]
        
        self._track_latency(start_time, final_results)
        
        logger.debug("hybrid_retrieval_completed",
                    _query = query[:50] if len(query) > 50 else query,
                    _dense_count = len(dense_results),
                    _sparse_count = len(sparse_results),
                    _fused_count = len(final_results),
                    latency_ms=final_results[0].latency_ms if final_results else 0)
        
        return final_results


class MultiHopRetrievalStrategy(BaseRetrievalStrategy):
    """
    Multi-hop retrieval for complex queries requiring chained lookups.
    
    Breaks down complex queries into multiple retrieval steps, using results
    from earlier hops to inform subsequent retrievals.
    
    Best for: Multi-step reasoning, bridging information gaps, complex queries.
    
    Features:
    - Query decomposition
    - Iterative retrieval with context accumulation
    - Hop limiting and early termination
    - Bridge entity detection
    """
    
    def __init__(self, _base_strategy: Optional[BaseRetrievalStrategy], _max_hops: int, _bridge_threshold: float, _query_decomposer: Optional[Any]):
        super().__init__("multi_hop_retrieval")
        self.base_strategy = base_strategy
        self.max_hops = max_hops
        self.bridge_threshold = bridge_threshold
        self.query_decomposer = query_decomposer
        self._hop_stats: Dict[str, int] = {}
    
    @property
    def strategy_type(self) -> RetrievalStrategyType:
        return RetrievalStrategyType.MULTI_HOP
    
    def _extract_bridge_entities(self, _query: str, _retrieved_content: str) -> List[str]:
        """
        Extract potential bridge entities from retrieved content.
        
        Bridge entities are terms that connect the query to additional information.
        """
        import re
        
        # Simple entity extraction - can be enhanced with NER
        # Look for capitalized terms, quoted terms, technical terms
        _patterns = [
            r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b',  # Capitalized phrases
            r'"[^"]+"',  # Quoted terms
            r'\b[A-Z]{2,}\b',  # Acronyms
        ]
        
        _entities = []
        for pattern in patterns:
            _matches = re.findall(pattern, retrieved_content)
            entities.extend(matches)
        
        # Filter out query terms (we want NEW information)
        _query_terms = set(query.lower().split())
        _bridge_entities = [
            e for e in entities
            if e.lower() not in query_terms and len(e) > 2
        ]
        
        return bridge_entities[:5]  # Limit entities
    
    def _generate_follow_up_query(self, _original_query: str, _bridge_entity: str, _hop_number: int) -> str:
        """Generate a follow-up query based on bridge entity."""
        # Simple template-based query generation
        _templates = [
            f"{original_query} {bridge_entity}",
            f"What is the relationship between {bridge_entity} and {original_query}?",
            f"Tell me more about {bridge_entity} in context of {original_query}",
        ]
        return templates[hop_number % len(templates)]
    
    async def retrieve(self, _query: str, _top_k: int, _filters: Optional[Dict[str, Any]], **kwargs) -> List[RetrievalResult]:
        """
        Retrieve using multi-hop chained queries.
        
        Args:
            query: Search query
            top_k: Number of results
            filters: Metadata filters
            **kwargs: Additional parameters
            
        Returns:
            List of retrieval results
        """
        _start_time = time.time()
        
        if not self.base_strategy:
            logger.warning("multi_hop_retrieval_unavailable", reason="base_strategy not configured")
            return []
        
        all_results: List[RetrievalResult] = []
        _current_query = query
        seen_sources: set = set()
        
        for hop in range(self.max_hops):
            # Execute retrieval for current hop
            _hop_results = await self.base_strategy.retrieve(
                _query = current_query,
                _top_k = top_k,
                _filters = filters,
            )
            
            # Track hop statistics
            self._hop_stats[f"hop_{hop + 1}"] = len(hop_results)
            
            # Add new results (avoid duplicates)
            _new_results = []
            for result in hop_results:
                if result.source not in seen_sources:
                    result.metadata["hop"] = hop + 1
                    result.metadata["query_used"] = current_query
                    new_results.append(result)
                    seen_sources.add(result.source)
            
            all_results.extend(new_results)
            
            # Check for early termination
            if not new_results or len(new_results) < 2:
                logger.debug("multi_hop_early_termination", hop=hop + 1)
                break
            
            # Extract bridge entities for next hop
            if hop < self.max_hops - 1:
                _combined_content = "\n".join(r.content for r in new_results[:3])
                _bridge_entities = self._extract_bridge_entities(query, combined_content)
                
                if bridge_entities:
                    _current_query = self._generate_follow_up_query(
                        query,
                        bridge_entities[0],
                        hop,
                    )
                else:
                    break
        
        # Re-rank by combined score
        all_results.sort(key=lambda r: r.score, reverse=True)
        _final_results = all_results[:top_k]
        
        self._track_latency(start_time, final_results)
        
        logger.debug("multi_hop_retrieval_completed",
                    _query = query[:50] if len(query) > 50 else query,
                    _hops_executed = len(self._hop_stats),
                    _total_results = len(all_results),
                    _final_results = len(final_results),
                    latency_ms=final_results[0].latency_ms if final_results else 0)
        
        return final_results
    
    def get_hop_stats(self) -> Dict[str, int]:
        """Get statistics about hops executed."""
        return self._hop_stats.copy()


class ReRankingStrategy(BaseRetrievalStrategy):
    """
    Re-ranking using cross-encoder scoring.
    
    Takes initial retrieval results and re-ranks them using a more sophisticated
    (but slower) cross-encoder model that considers query-document pairs jointly.
    
    Best for: Final result refinement, improving precision, complex queries.
    
    Features:
    - Cross-encoder scoring
    - Configurable re-rank limit
    - Score calibration
    - Batch processing
    """
    
    def __init__(self, _cross_encoder: Optional[Any], _re_rank_limit: int, _score_threshold: float, _batch_size: int):
        super().__init__("re_ranking")
        self.cross_encoder = cross_encoder
        self.re_rank_limit = re_rank_limit
        self.score_threshold = score_threshold
        self.batch_size = batch_size
    
    @property
    def strategy_type(self) -> RetrievalStrategyType:
        return RetrievalStrategyType.RE_RANKING
    
    async def retrieve(self, _query: str, _top_k: int, _initial_results: Optional[List[RetrievalResult]], **kwargs) -> List[RetrievalResult]:
        """
        Re-rank initial retrieval results using cross-encoder.
        
        Args:
            query: Search query
            top_k: Number of final results
            initial_results: Results from initial retrieval (required)
            **kwargs: Additional parameters
            
        Returns:
            Re-ranked list of retrieval results
        """
        _start_time = time.time()
        
        if not initial_results:
            logger.warning("re_ranking_no_initial_results", reason="initial_results required")
            return []
        
        if not self.cross_encoder:
            # Return initial results sorted by score if no cross-encoder
            return sorted(initial_results, key=lambda r: r.score, reverse=True)[:top_k]
        
        try:
            # Limit candidates for re-ranking
            _candidates = initial_results[:self.re_rank_limit]
            
            # Prepare query-document pairs for cross-encoder
            _pairs = [(query, candidate.content) for candidate in candidates]
            
            # Score in batches
            _cross_scores = []
            for i in range(0, len(pairs), self.batch_size):
                _batch = pairs[i:i + self.batch_size]
                _batch_scores = await self.cross_encoder.predict(batch)
                cross_scores.extend(batch_scores)
            
            # Apply cross-encoder scores
            for result, score in zip(candidates, cross_scores):
                # Combine original score with cross-encoder score
                result.score = 0.5 * result.score + 0.5 * score
                result.metadata["cross_encoder_score"] = score
            
            # Filter by threshold and sort
            _filtered = [r for r in candidates if r.score >= self.score_threshold]
            filtered.sort(key=lambda r: r.score, reverse=True)
            
            _final_results = filtered[:top_k]
            
            self._track_latency(start_time, final_results)
            
            logger.debug("re_ranking_completed",
                        _query = query[:50] if len(query) > 50 else query,
                        _candidates = len(candidates),
                        _final_count = len(final_results),
                        _latency_ms = final_results[0].latency_ms if final_results else 0)
            
            return final_results
            
        except Exception as e:
            logger.error("re_ranking_error", error=str(e))
            self._track_latency(start_time, [])
            return initial_results[:top_k]


class QueryClassifier:
    """
    Classifies queries to select the best retrieval strategy.
    
    Uses heuristics and optionally ML-based classification to determine
    query type and recommend appropriate retrieval strategy.
    """
    
    # Query type indicators
    FACTUAL_INDICATORS = ["who", "what", "when", "where", "define", "meaning of"]
    EXPLANATORY_INDICATORS = ["how", "why", "explain", "reason", "cause"]
    COMPARATIVE_INDICATORS = ["compare", "difference", "better", "vs", "versus"]
    PROCEDURAL_INDICATORS = ["how to", "steps", "guide", "tutorial", "process"]
    MULTI_STEP_INDICATORS = ["first", "then", "after", "before", "relationship between"]
    
    def classify(self, _query: str) -> QueryType:
        """
        Classify a query to determine its type.
        
        Args:
            query: Query text
            
        Returns:
            QueryType enumeration value
        """
        _query_lower = query.lower()
        
        # Check for multi-step indicators first (highest priority)
        if any(ind in query_lower for ind in self.MULTI_STEP_INDICATORS):
            return QueryType.MULTI_STEP
        
        # Check other types
        if any(ind in query_lower for ind in self.EXPLANATORY_INDICATORS):
            return QueryType.EXPLANATORY
        
        if any(ind in query_lower for ind in self.COMPARATIVE_INDICATORS):
            return QueryType.COMPARATIVE
        
        if any(ind in query_lower for ind in self.PROCEDURAL_INDICATORS):
            return QueryType.PROCEDURAL
        
        if any(ind in query_lower for ind in self.FACTUAL_INDICATORS):
            return QueryType.FACTUAL
        
        # Default to exploratory
        return QueryType.EXPLORATORY
    
    def recommend_strategy(self, _query_type: QueryType) -> RetrievalStrategyType:
        """
        Recommend retrieval strategy based on query type.
        
        Args:
            query_type: Classified query type
            
        Returns:
            Recommended RetrievalStrategyType
        """
        _strategy_map = {
            QueryType.FACTUAL: RetrievalStrategyType.HYBRID,  # Need both semantic and keyword
            QueryType.EXPLANATORY: RetrievalStrategyType.DENSE,  # Semantic understanding
            QueryType.COMPARATIVE: RetrievalStrategyType.HYBRID,  # Need comprehensive results
            QueryType.PROCEDURAL: RetrievalStrategyType.SPARSE,  # Exact steps matching
            QueryType.EXPLORATORY: RetrievalStrategyType.HYBRID,  # Broad coverage
            QueryType.MULTI_STEP: RetrievalStrategyType.MULTI_HOP,  # Requires chaining
        }
        return strategy_map.get(query_type, RetrievalStrategyType.HYBRID)


class StrategySelector:
    """
    Selects and executes the best retrieval strategy for a given query.
    
    Features:
    - Automatic strategy selection based on query classification
    - Query caching for frequent queries
    - Fallback handling
    - Performance tracking
    """
    
    def __init__(self, _strategies: Optional[Dict[RetrievalStrategyType, _BaseRetrievalStrategy]], _cache_enabled: bool, _cache_ttl_seconds: int):
        self.strategies = strategies or {}
        self.cache_enabled = cache_enabled
        self.cache_ttl_seconds = cache_ttl_seconds
        self._query_cache: Dict[str, QueryCacheEntry] = {}
        self._classifier = QueryClassifier()
        self._stats: Dict[str, Any] = {
            "total_queries": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "strategy_usage": {},
        }
    
    def _hash_query(self, _query: str) -> str:
        """Create a hash of the query for caching."""
        return hashlib.sha256(query.lower().strip().encode()).hexdigest()
    
    def _get_from_cache(self, _query_hash: str) -> Optional[List[RetrievalResult]]:
        """Get cached results if available and not expired."""
        if not self.cache_enabled:
            return None
        
        _entry = self._query_cache.get(query_hash)
        if entry and not entry.is_expired(self.cache_ttl_seconds):
            entry.access_count += 1
            entry.last_accessed = datetime.now(timezone.utc)
            self._stats["cache_hits"] += 1
            return entry.results
        
        self._stats["cache_misses"] += 1
        return None
    
    def _store_in_cache(self, _query_hash: str, _results: List[RetrievalResult]) -> None:
        """Store results in cache."""
        if not self.cache_enabled:
            return
        
        self._query_cache[query_hash] = QueryCacheEntry(
            _query_hash = query_hash,
            _results = results,
            _created_at = datetime.now(timezone.utc),
        )
        
        # Clean old cache entries periodically
        if len(self._query_cache) > 1000:
            self._clean_cache()
    
    def _clean_cache(self) -> None:
        """Remove expired and least recently used cache entries."""
        _now = datetime.now(timezone.utc)
        # Remove expired
        _expired = [
            k for k, v in self._query_cache.items()
            if v.is_expired(self.cache_ttl_seconds)
        ]
        for k in expired:
            del self._query_cache[k]
        
        # If still too large, remove LRU entries
        if len(self._query_cache) > 1000:
            _sorted_entries = sorted(
                self._query_cache.items(),
                _key = lambda x: x[1].last_accessed,
                _reverse = True,
            )
            for k, _ in sorted_entries[500:]:
                del self._query_cache[k]
    
    def add_strategy(self, _strategy_type: RetrievalStrategyType, _strategy: BaseRetrievalStrategy) -> None:
        """Add a retrieval strategy."""
        self.strategies[strategy_type] = strategy
    
    async def retrieve(self, _query: str, _top_k: int, _strategy: Optional[RetrievalStrategyType], _filters: Optional[Dict[str, Any]], **kwargs) -> List[RetrievalResult]:
        """
        Retrieve using the best strategy for the query.
        
        Args:
            query: Search query
            top_k: Number of results
            strategy: Optional explicit strategy (auto-selected if not provided)
            filters: Metadata filters
            **kwargs: Strategy-specific parameters
            
        Returns:
            List of retrieval results
        """
        self._stats["total_queries"] += 1
        
        # Check cache first
        _query_hash = self._hash_query(query)
        _cached = self._get_from_cache(query_hash)
        if cached:
            return cached
        
        # Determine strategy
        if strategy is None:
            _query_type = self._classifier.classify(query)
            _strategy = self._classifier.recommend_strategy(query_type)
        
        # Track strategy usage
        _strategy_key = strategy.value
        self._stats["strategy_usage"][strategy_key] = (
            self._stats["strategy_usage"].get(strategy_key, 0) + 1
        )
        
        # Get strategy
        _selected_strategy = self.strategies.get(strategy)
        if not selected_strategy:
            logger.warning("strategy_not_available", strategy=strategy.value)
            # Fallback to any available strategy
            if self.strategies:
                _selected_strategy = list(self.strategies.values())[0]
            else:
                return []
        
        # Execute retrieval
        _results = await selected_strategy.retrieve(
            _query = query,
            _top_k = top_k,
            _filters = filters,
            **kwargs,
        )
        
        # Cache results
        self._store_in_cache(query_hash, results)
        
        logger.debug("strategy_selected",
                    _query = query[:50] if len(query) > 50 else query,
                    _strategy = strategy.value,
                    _results_count = len(results))
        
        return results
    
    def get_stats(self) -> Dict[str, Any]:
        """Get selector statistics."""
        return {
            **self._stats,
            "cache_size": len(self._query_cache),
            "available_strategies": list(self.strategies.keys()),
        }


@dataclass
class RAGStrategyConfig:
    """Configuration for RAG strategies."""
    # Dense retrieval config
    dense_enabled: bool = True
    similarity_metric: str = "cosine"
    similarity_threshold: float = 0.0
    
    # Sparse retrieval config
    sparse_enabled: bool = True
    bm25_k1: float = 1.5
    bm25_b: float = 0.75
    
    # Hybrid retrieval config
    hybrid_enabled: bool = True
    dense_weight: float = 0.5
    sparse_weight: float = 0.5
    fusion_method: str = "rrf"
    rrf_k: int = 60
    
    # Multi-hop retrieval config
    multi_hop_enabled: bool = True
    max_hops: int = 3
    bridge_threshold: float = 0.3
    
    # Re-ranking config
    re_ranking_enabled: bool = True
    re_rank_limit: int = 50
    score_threshold: float = 0.0
    
    # Cache config
    cache_enabled: bool = True
    cache_ttl_seconds: int = 300


def create_default_strategies(_config: Optional[RAGStrategyConfig]) -> Dict[RetrievalStrategyType, BaseRetrievalStrategy]:
    """
    Create default strategy instances.
    
    Args:
        config: Optional configuration
        
    Returns:
        Dictionary of strategy type to strategy instance
    """
    _config = config or RAGStrategyConfig()
    _strategies = {}
    
    # Create dense strategy
    if config.dense_enabled:
        strategies[RetrievalStrategyType.DENSE] = DenseRetrievalStrategy(
            _similarity_metric = config.similarity_metric,
            _similarity_threshold = config.similarity_threshold,
        )
    
    # Create sparse strategy
    if config.sparse_enabled:
        strategies[RetrievalStrategyType.SPARSE] = SparseRetrievalStrategy(
            _k1 = config.bm25_k1,
            _b = config.bm25_b,
        )
    
    # Create hybrid strategy (requires dense and sparse)
    if config.hybrid_enabled and RetrievalStrategyType.DENSE in strategies and RetrievalStrategyType.SPARSE in strategies:
        strategies[RetrievalStrategyType.HYBRID] = HybridRetrievalStrategy(
            _dense_strategy = strategies[RetrievalStrategyType.DENSE],
            _sparse_strategy = strategies[RetrievalStrategyType.SPARSE],
            _dense_weight = config.dense_weight,
            _sparse_weight = config.sparse_weight,
            _fusion_method = config.fusion_method,
            _rrf_k = config.rrf_k,
        )
    
    # Create multi-hop strategy
    if config.multi_hop_enabled:
        # Use hybrid as base if available, otherwise dense
        _base_strategy = strategies.get(RetrievalStrategyType.HYBRID) or strategies.get(RetrievalStrategyType.DENSE)
        if base_strategy:
            strategies[RetrievalStrategyType.MULTI_HOP] = MultiHopRetrievalStrategy(
                _base_strategy = base_strategy,
                _max_hops = config.max_hops,
                _bridge_threshold = config.bridge_threshold,
            )
    
    # Create re-ranking strategy
    if config.re_ranking_enabled:
        strategies[RetrievalStrategyType.RE_RANKING] = ReRankingStrategy(
            _re_rank_limit = config.re_rank_limit,
            _score_threshold = config.score_threshold,
        )
    
    return strategies


def create_strategy_selector(_config: Optional[RAGStrategyConfig], _embedding_provider: Optional[Any], _vector_store: Optional[Any], _sparse_index: Optional[Any], _cross_encoder: Optional[Any]) -> StrategySelector:
    """
    Create a fully configured strategy selector.
    
    Args:
        config: Strategy configuration
        embedding_provider: Embedding provider for dense retrieval
        vector_store: Vector store for dense retrieval
        sparse_index: Sparse index for BM25 retrieval
        cross_encoder: Cross-encoder model for re-ranking
        
    Returns:
        Configured StrategySelector instance
    """
    _config = config or RAGStrategyConfig()
    
    # Create strategies
    _strategies = create_default_strategies(config)
    
    # Inject dependencies
    if RetrievalStrategyType.DENSE in strategies and embedding_provider and vector_store:
        strategies[RetrievalStrategyType.DENSE].embedding_provider = embedding_provider
        strategies[RetrievalStrategyType.DENSE].vector_store = vector_store
    
    if RetrievalStrategyType.SPARSE in strategies and sparse_index:
        strategies[RetrievalStrategyType.SPARSE].index = sparse_index
    
    if RetrievalStrategyType.RE_RANKING in strategies and cross_encoder:
        strategies[RetrievalStrategyType.RE_RANKING].cross_encoder = cross_encoder
    
    # Create selector
    _selector = StrategySelector(
        _strategies = strategies,
        _cache_enabled = config.cache_enabled,
        _cache_ttl_seconds = config.cache_ttl_seconds,
    )
    
    return selector
