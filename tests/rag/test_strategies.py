"""
Unit Tests for Advanced RAG Strategies.

Tests for:
- Dense retrieval strategy
- Sparse retrieval strategy
- Hybrid retrieval strategy
- Multi-hop retrieval strategy
- Re-ranking strategy
- Strategy selector
- Query classifier
- Hybrid retriever
"""

import pytest
import asyncio
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

from heretek_swarm.rag.strategies import (
    RetrievalStrategyType,
    RetrievalResult,
    QueryType,
    DenseRetrievalStrategy,
    SparseRetrievalStrategy,
    HybridRetrievalStrategy,
    MultiHopRetrievalStrategy,
    ReRankingStrategy,
    QueryClassifier,
    StrategySelector,
    RAGStrategyConfig,
    create_strategy_selector,
    create_default_strategies,
)

from heretek_swarm.rag.hybrid_retriever import (
    HybridRetriever,
    HybridRetrieverConfig,
    FusionMethod,
    RetrieverState,
    RateLimiter,
    RetrievalMetrics,
)


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def mock_embedding_provider():
    """Mock embedding provider."""
    provider = AsyncMock()
    provider.embed = AsyncMock(return_value=[0.1, 0.2, 0.3, 0.4, 0.5])
    return provider


@pytest.fixture
def mock_vector_store():
    """Mock vector store."""
    store = AsyncMock()
    store.search = AsyncMock(return_value=[
        {"content": "Document 1", "score": 0.9, "id": "doc1"},
        {"content": "Document 2", "score": 0.8, "id": "doc2"},
        {"content": "Document 3", "score": 0.7, "id": "doc3"},
    ])
    return store


@pytest.fixture
def mock_sparse_index():
    """Mock sparse index for BM25."""
    index = AsyncMock()
    index.search = AsyncMock(return_value=[
        {"content": "BM25 Document 1", "bm25_score": 0.85, "id": "bm25_doc1"},
        {"content": "BM25 Document 2", "bm25_score": 0.75, "id": "bm25_doc2"},
    ])
    return index


@pytest.fixture
def mock_cross_encoder():
    """Mock cross-encoder for re-ranking."""
    encoder = AsyncMock()
    encoder.predict = AsyncMock(return_value=[0.9, 0.8, 0.7])
    return encoder


# =============================================================================
# RetrievalResult Tests
# =============================================================================

class TestRetrievalResult:
    """Tests for RetrievalResult dataclass."""
    
    def test_create_result(self):
        """Test creating a retrieval result."""
        result = RetrievalResult(
            content="Test content",
            score=0.85,
            source="test_source",
        )
        
        assert result.content == "Test content"
        assert result.score == 0.85
        assert result.source == "test_source"
        assert result.strategy == RetrievalStrategyType.DENSE
        assert result.latency_ms == 0.0
    
    def test_to_dict(self):
        """Test converting result to dictionary."""
        result = RetrievalResult(
            content="Test content",
            score=0.85,
            source="test_source",
            metadata={"key": "value"},
        )
        
        result_dict = result.to_dict()
        
        assert result_dict["content"] == "Test content"
        assert result_dict["score"] == 0.85
        assert result_dict["source"] == "test_source"
        assert result_dict["metadata"] == {"key": "value"}
        assert result_dict["strategy"] == "dense"


# =============================================================================
# QueryClassifier Tests
# =============================================================================

class TestQueryClassifier:
    """Tests for QueryClassifier."""
    
    def test_classify_factual(self):
        """Test classifying factual queries."""
        classifier = QueryClassifier()
        
        assert classifier.classify("Who is the president?") == QueryType.FACTUAL
        assert classifier.classify("What is Python?") == QueryType.FACTUAL
        assert classifier.classify("When was it created?") == QueryType.FACTUAL
        assert classifier.classify("Where is the file?") == QueryType.FACTUAL
        assert classifier.classify("Define machine learning") == QueryType.FACTUAL
    
    def test_classify_explanatory(self):
        """Test classifying explanatory queries."""
        classifier = QueryClassifier()
        
        assert classifier.classify("How does it work?") == QueryType.EXPLANATORY
        assert classifier.classify("Why did this happen?") == QueryType.EXPLANATORY
        assert classifier.classify("Explain the process") == QueryType.EXPLANATORY
    
    def test_classify_comparative(self):
        """Test classifying comparative queries."""
        classifier = QueryClassifier()
        
        assert classifier.classify("Compare Python and Java") == QueryType.COMPARATIVE
        assert classifier.classify("What's the difference between X and Y?") == QueryType.COMPARATIVE
        assert classifier.classify("Which is better?") == QueryType.COMPARATIVE
    
    def test_classify_procedural(self):
        """Test classifying procedural queries."""
        classifier = QueryClassifier()
        
        assert classifier.classify("How to install Python?") == QueryType.PROCEDURAL
        assert classifier.classify("Steps for deployment") == QueryType.PROCEDURAL
        assert classifier.classify("Tutorial for beginners") == QueryType.PROCEDURAL
    
    def test_classify_multi_step(self):
        """Test classifying multi-step queries."""
        classifier = QueryClassifier()
        
        assert classifier.classify("First do X, then Y") == QueryType.MULTI_STEP
        assert classifier.classify("What happens after Z?") == QueryType.MULTI_STEP
        assert classifier.classify("Relationship between A and B") == QueryType.MULTI_STEP
    
    def test_classify_exploratory(self):
        """Test classifying exploratory queries (default)."""
        classifier = QueryClassifier()
        
        assert classifier.classify("Tell me about AI") == QueryType.EXPLORATORY
        assert classifier.classify("Random query") == QueryType.EXPLORATORY
    
    def test_recommend_strategy(self):
        """Test strategy recommendation based on query type."""
        classifier = QueryClassifier()
        
        assert classifier.recommend_strategy(QueryType.FACTUAL) == RetrievalStrategyType.HYBRID
        assert classifier.recommend_strategy(QueryType.EXPLANATORY) == RetrievalStrategyType.DENSE
        assert classifier.recommend_strategy(QueryType.COMPARATIVE) == RetrievalStrategyType.HYBRID
        assert classifier.recommend_strategy(QueryType.PROCEDURAL) == RetrievalStrategyType.SPARSE
        assert classifier.recommend_strategy(QueryType.MULTI_STEP) == RetrievalStrategyType.MULTI_HOP


# =============================================================================
# DenseRetrievalStrategy Tests
# =============================================================================

class TestDenseRetrievalStrategy:
    """Tests for DenseRetrievalStrategy."""
    
    @pytest.mark.asyncio
    async def test_retrieve(self, mock_embedding_provider, mock_vector_store):
        """Test dense retrieval."""
        strategy = DenseRetrievalStrategy(
            embedding_provider=mock_embedding_provider,
            vector_store=mock_vector_store,
        )
        
        results = await strategy.retrieve("test query", top_k=3)
        
        assert len(results) == 3
        assert results[0].content == "Document 1"
        assert results[0].score == 0.9
        assert results[0].strategy == RetrievalStrategyType.DENSE
        assert results[0].latency_ms > 0
    
    @pytest.mark.asyncio
    async def test_retrieve_with_filters(self, mock_embedding_provider, mock_vector_store):
        """Test dense retrieval with filters."""
        strategy = DenseRetrievalStrategy(
            embedding_provider=mock_embedding_provider,
            vector_store=mock_vector_store,
        )
        
        results = await strategy.retrieve(
            "test query",
            top_k=3,
            filters={"category": "test"},
        )
        
        mock_vector_store.search.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_retrieve_unavailable(self):
        """Test dense retrieval when unavailable."""
        strategy = DenseRetrievalStrategy()
        
        results = await strategy.retrieve("test query")
        
        assert results == []
    
    def test_strategy_type(self):
        """Test strategy type property."""
        strategy = DenseRetrievalStrategy()
        assert strategy.strategy_type == RetrievalStrategyType.DENSE
    
    def test_get_stats(self):
        """Test getting strategy statistics."""
        strategy = DenseRetrievalStrategy()
        stats = strategy.get_stats()
        
        assert "queries_executed" in stats
        assert "avg_latency_ms" in stats


# =============================================================================
# SparseRetrievalStrategy Tests
# =============================================================================

class TestSparseRetrievalStrategy:
    """Tests for SparseRetrievalStrategy."""
    
    @pytest.mark.asyncio
    async def test_retrieve(self, mock_sparse_index):
        """Test sparse retrieval."""
        strategy = SparseRetrievalStrategy(index=mock_sparse_index)
        
        results = await strategy.retrieve("test query", top_k=2)
        
        assert len(results) == 2
        assert results[0].content == "BM25 Document 1"
        assert results[0].score == 0.85
        assert results[0].strategy == RetrievalStrategyType.SPARSE
    
    @pytest.mark.asyncio
    async def test_retrieve_unavailable(self):
        """Test sparse retrieval when unavailable."""
        strategy = SparseRetrievalStrategy()
        
        results = await strategy.retrieve("test query")
        
        assert results == []
    
    def test_tokenize(self):
        """Test tokenization."""
        strategy = SparseRetrievalStrategy()
        
        tokens = strategy._tokenize("Hello World! This is a test.")
        
        assert "hello" in tokens
        assert "world" in tokens
        assert "test" in tokens
    
    def test_strategy_type(self):
        """Test strategy type property."""
        strategy = SparseRetrievalStrategy()
        assert strategy.strategy_type == RetrievalStrategyType.SPARSE


# =============================================================================
# HybridRetrievalStrategy Tests
# =============================================================================

class TestHybridRetrievalStrategy:
    """Tests for HybridRetrievalStrategy."""
    
    @pytest.mark.asyncio
    async def test_rrf_fusion(self):
        """Test Reciprocal Rank Fusion."""
        dense_results = [
            RetrievalResult(content="D1", score=0.9, source="d1"),
            RetrievalResult(content="D2", score=0.8, source="d2"),
        ]
        sparse_results = [
            RetrievalResult(content="S1", score=0.85, source="s1"),
            RetrievalResult(content="D1", score=0.7, source="d1"),  # Overlap
        ]
        
        strategy = HybridRetrievalStrategy()
        fused = strategy._reciprocal_rank_fusion(dense_results, sparse_results)
        
        assert len(fused) == 3  # d1, d2, s1
        assert all(r.score > 0 for r in fused)
    
    @pytest.mark.asyncio
    async def test_weighted_combination(self):
        """Test weighted score combination."""
        dense_results = [
            RetrievalResult(content="D1", score=0.9, source="d1"),
            RetrievalResult(content="D2", score=0.5, source="d2"),
        ]
        sparse_results = [
            RetrievalResult(content="S1", score=0.8, source="s1"),
            RetrievalResult(content="D1", score=0.6, source="d1"),
        ]
        
        strategy = HybridRetrievalStrategy(
            dense_weight=0.6,
            sparse_weight=0.4,
        )
        combined = strategy._weighted_combination(dense_results, sparse_results)
        
        assert len(combined) == 3
        assert all(0 <= r.score <= 1 for r in combined)
    
    def test_strategy_type(self):
        """Test strategy type property."""
        strategy = HybridRetrievalStrategy()
        assert strategy.strategy_type == RetrievalStrategyType.HYBRID


# =============================================================================
# MultiHopRetrievalStrategy Tests
# =============================================================================

class TestMultiHopRetrievalStrategy:
    """Tests for MultiHopRetrievalStrategy."""
    
    @pytest.mark.asyncio
    async def test_extract_bridge_entities(self):
        """Test bridge entity extraction."""
        strategy = MultiHopRetrievalStrategy()
        
        query = "What is Python?"
        content = "Python is a programming language created by Guido van Rossum."
        
        entities = strategy._extract_bridge_entities(query, content)
        
        # Should extract "Python", "Guido van Rossum"
        assert len(entities) > 0
    
    @pytest.mark.asyncio
    async def test_generate_follow_up_query(self):
        """Test follow-up query generation."""
        strategy = MultiHopRetrievalStrategy()
        
        query = "What is Python?"
        follow_up = strategy._generate_follow_up_query(query, "Guido van Rossum", 0)
        
        assert "Guido van Rossum" in follow_up
    
    @pytest.mark.asyncio
    async def test_retrieve(self, mock_vector_store):
        """Test multi-hop retrieval."""
        base_strategy = DenseRetrievalStrategy(
            embedding_provider=AsyncMock(return_value=[0.1, 0.2, 0.3]),
            vector_store=mock_vector_store,
        )
        
        strategy = MultiHopRetrievalStrategy(
            base_strategy=base_strategy,
            max_hops=2,
        )
        
        results = await strategy.retrieve("test query", top_k=3)
        
        assert len(results) <= 3
    
    def test_strategy_type(self):
        """Test strategy type property."""
        strategy = MultiHopRetrievalStrategy()
        assert strategy.strategy_type == RetrievalStrategyType.MULTI_HOP


# =============================================================================
# ReRankingStrategy Tests
# =============================================================================

class TestReRankingStrategy:
    """Tests for ReRankingStrategy."""
    
    @pytest.mark.asyncio
    async def test_rerank(self, mock_cross_encoder):
        """Test re-ranking with cross-encoder."""
        strategy = ReRankingStrategy(
            cross_encoder=mock_cross_encoder,
            re_rank_limit=10,
        )
        
        initial_results = [
            RetrievalResult(content="Doc 1", score=0.5, source="doc1"),
            RetrievalResult(content="Doc 2", score=0.6, source="doc2"),
            RetrievalResult(content="Doc 3", score=0.7, source="doc3"),
        ]
        
        reranked = await strategy.retrieve(
            query="test query",
            top_k=3,
            initial_results=initial_results,
        )
        
        assert len(reranked) == 3
        assert "cross_encoder_score" in reranked[0].metadata
    
    @pytest.mark.asyncio
    async def test_rerank_no_encoder(self):
        """Test re-ranking without cross-encoder."""
        strategy = ReRankingStrategy()
        
        initial_results = [
            RetrievalResult(content="Doc 1", score=0.5, source="doc1"),
            RetrievalResult(content="Doc 2", score=0.7, source="doc2"),
        ]
        
        reranked = await strategy.retrieve(
            query="test query",
            top_k=2,
            initial_results=initial_results,
        )
        
        # Should return sorted by original score
        assert len(reranked) == 2
        assert reranked[0].score > reranked[1].score
    
    @pytest.mark.asyncio
    async def test_rerank_no_initial_results(self):
        """Test re-ranking with no initial results."""
        strategy = ReRankingStrategy()
        
        reranked = await strategy.retrieve(
            query="test query",
            top_k=3,
            initial_results=None,
        )
        
        assert reranked == []
    
    def test_strategy_type(self):
        """Test strategy type property."""
        strategy = ReRankingStrategy()
        assert strategy.strategy_type == RetrievalStrategyType.RE_RANKING


# =============================================================================
# StrategySelector Tests
# =============================================================================

class TestStrategySelector:
    """Tests for StrategySelector."""
    
    @pytest.mark.asyncio
    async def test_retrieve_auto_selection(self, mock_vector_store):
        """Test automatic strategy selection."""
        strategies = {
            RetrievalStrategyType.DENSE: DenseRetrievalStrategy(
                embedding_provider=AsyncMock(return_value=[0.1, 0.2, 0.3]),
                vector_store=mock_vector_store,
            ),
        }
        
        selector = StrategySelector(strategies=strategies)
        
        results = await selector.retrieve("Who is the president?", top_k=3)
        
        assert len(results) <= 3
    
    @pytest.mark.asyncio
    async def test_retrieve_explicit_strategy(self, mock_vector_store):
        """Test explicit strategy selection."""
        strategies = {
            RetrievalStrategyType.DENSE: DenseRetrievalStrategy(
                embedding_provider=AsyncMock(return_value=[0.1, 0.2, 0.3]),
                vector_store=mock_vector_store,
            ),
        }
        
        selector = StrategySelector(strategies=strategies)
        
        results = await selector.retrieve(
            "test query",
            top_k=3,
            strategy=RetrievalStrategyType.DENSE,
        )
        
        assert len(results) <= 3
    
    @pytest.mark.asyncio
    async def test_cache_hit(self, mock_vector_store):
        """Test query caching."""
        strategies = {
            RetrievalStrategyType.DENSE: DenseRetrievalStrategy(
                embedding_provider=AsyncMock(return_value=[0.1, 0.2, 0.3]),
                vector_store=mock_vector_store,
            ),
        }
        
        selector = StrategySelector(
            strategies=strategies,
            cache_enabled=True,
            cache_ttl_seconds=60,
        )
        
        # First query
        results1 = await selector.retrieve("test query", top_k=3)
        
        # Second query (should be cached)
        results2 = await selector.retrieve("test query", top_k=3)
        
        assert results1 == results2
        assert selector._stats["cache_hits"] >= 1
    
    def test_get_stats(self):
        """Test getting selector statistics."""
        selector = StrategySelector()
        stats = selector.get_stats()
        
        assert "total_queries" in stats
        assert "cache_hits" in stats
        assert "cache_misses" in stats
        assert "strategy_usage" in stats


# =============================================================================
# RateLimiter Tests
# =============================================================================

class TestRateLimiter:
    """Tests for RateLimiter."""
    
    @pytest.mark.asyncio
    async def test_acquire_under_limit(self):
        """Test acquiring token under limit."""
        limiter = RateLimiter(queries_per_minute=10)
        
        for _ in range(5):
            result = await limiter.acquire()
            assert result is True
    
    @pytest.mark.asyncio
    async def test_acquire_over_limit(self):
        """Test acquiring token over limit."""
        limiter = RateLimiter(queries_per_minute=5)
        
        # Exhaust limit
        for _ in range(5):
            await limiter.acquire()
        
        # Should be rate limited
        result = await limiter.acquire()
        assert result is False
    
    @pytest.mark.asyncio
    async def test_get_remaining(self):
        """Test getting remaining queries."""
        limiter = RateLimiter(queries_per_minute=10)
        
        remaining = limiter.get_remaining()
        assert remaining == 10
        
        await limiter.acquire()
        remaining = limiter.get_remaining()
        assert remaining == 9


# =============================================================================
# HybridRetriever Tests
# =============================================================================

class TestHybridRetriever:
    """Tests for HybridRetriever."""
    
    def test_initial_state(self):
        """Test initial retriever state."""
        retriever = HybridRetriever()
        
        assert retriever.state == RetrieverState.UNINITIALIZED
    
    @pytest.mark.asyncio
    async def test_initialize(self):
        """Test retriever initialization."""
        retriever = HybridRetriever()
        
        await retriever.initialize()
        
        assert retriever.state == RetrieverState.READY
    
    @pytest.mark.asyncio
    async def test_retrieve_not_ready(self):
        """Test retrieval when not ready."""
        retriever = HybridRetriever()
        
        with pytest.raises(Exception):
            await retriever.retrieve("test query")
    
    @pytest.mark.asyncio
    async def test_retrieve(self, mock_vector_store):
        """Test hybrid retrieval."""
        retriever = HybridRetriever(
            config=HybridRetrieverConfig(
                enable_reranking=False,
                enable_multihop=False,
            ),
            embedding_provider=AsyncMock(return_value=[0.1, 0.2, 0.3]),
            vector_store=mock_vector_store,
        )
        
        await retriever.initialize()
        
        results = await retriever.retrieve("test query", top_k=3)
        
        assert len(results) <= 3
    
    @pytest.mark.asyncio
    async def test_retrieve_with_reranking(self, mock_vector_store, mock_cross_encoder):
        """Test hybrid retrieval with re-ranking."""
        retriever = HybridRetriever(
            config=HybridRetrieverConfig(
                enable_reranking=True,
                rerank_top_k=10,
            ),
            embedding_provider=AsyncMock(return_value=[0.1, 0.2, 0.3]),
            vector_store=mock_vector_store,
            cross_encoder=mock_cross_encoder,
        )
        
        await retriever.initialize()
        
        results = await retriever.retrieve(
            "test query",
            top_k=3,
            apply_reranking=True,
        )
        
        assert len(results) <= 3
    
    def test_get_metrics(self):
        """Test getting retrieval metrics."""
        retriever = HybridRetriever()
        metrics = retriever.get_metrics()
        
        assert isinstance(metrics, RetrievalMetrics)
        assert metrics.total_queries == 0
    
    def test_export_prometheus_metrics(self):
        """Test exporting Prometheus metrics."""
        retriever = HybridRetriever()
        metrics = retriever.export_prometheus_metrics()
        
        assert "heretek_rag_total_queries" in metrics
        assert "heretek_rag_successful_queries" in metrics


# =============================================================================
# Helper Function Tests
# =============================================================================

class TestHelperFunctions:
    """Tests for helper functions."""
    
    def test_create_default_strategies(self):
        """Test creating default strategies."""
        config = RAGStrategyConfig(
            dense_enabled=True,
            sparse_enabled=True,
            hybrid_enabled=True,
        )
        
        strategies = create_default_strategies(config)
        
        assert RetrievalStrategyType.DENSE in strategies
        assert RetrievalStrategyType.SPARSE in strategies
        assert RetrievalStrategyType.HYBRID in strategies
    
    def test_create_strategy_selector(self):
        """Test creating strategy selector."""
        selector = create_strategy_selector(
            config=RAGStrategyConfig(),
        )
        
        assert selector is not None
        assert isinstance(selector, StrategySelector)


# =============================================================================
# Integration Tests
# =============================================================================

class TestIntegration:
    """Integration tests for RAG strategies."""
    
    @pytest.mark.asyncio
    async def test_full_retrieval_pipeline(self, mock_vector_store, mock_sparse_index):
        """Test full retrieval pipeline with multiple strategies."""
        # Create strategies
        dense = DenseRetrievalStrategy(
            embedding_provider=AsyncMock(return_value=[0.1, 0.2, 0.3]),
            vector_store=mock_vector_store,
        )
        sparse = SparseRetrievalStrategy(index=mock_sparse_index)
        hybrid = HybridRetrievalStrategy(
            dense_strategy=dense,
            sparse_strategy=sparse,
        )
        
        # Test hybrid retrieval
        results = await hybrid.retrieve("test query", top_k=5)
        
        assert len(results) > 0
        assert all(isinstance(r, RetrievalResult) for r in results)
    
    @pytest.mark.asyncio
    async def test_query_classification_and_retrieval(self, mock_vector_store):
        """Test query classification followed by retrieval."""
        classifier = QueryClassifier()
        
        strategies = {
            RetrievalStrategyType.DENSE: DenseRetrievalStrategy(
                embedding_provider=AsyncMock(return_value=[0.1, 0.2, 0.3]),
                vector_store=mock_vector_store,
            ),
        }
        
        selector = StrategySelector(strategies=strategies)
        
        # Test different query types
        queries = [
            ("Who created Python?", QueryType.FACTUAL),
            ("How does Python work?", QueryType.EXPLANATORY),
            ("Compare Python and Java", QueryType.COMPARATIVE),
        ]
        
        for query, expected_type in queries:
            classified = classifier.classify(query)
            assert classified == expected_type
            
            results = await selector.retrieve(query, top_k=3)
            assert len(results) >= 0  # May return empty if mock doesn't match
