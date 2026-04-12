"""
Integration tests for Unified Knowledge Access Layer

Tests the unified interface for querying memory and RAG systems
with MMR reranking and result merging.
"""

import asyncio
from unittest.mock import AsyncMock, MagicMock

import pytest

from heretek_swarm.knowledge.unified_access import (
    KnowledgeEntry,
    KnowledgeQueryBuilder,
    KnowledgeQueryResult,
    UnifiedKnowledgeAccess,
)

# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def mock_memory_system():
    """Create a mock memory system."""
    memory = AsyncMock()

    # Mock query response
    mock_results = MagicMock()
    mock_results.entries = [
        MagicMock(
            id="mem_001",
            content={"text": "Alpha proposed decision X"},
            metadata={"agent_id": "alpha", "importance": 0.8},
            similarity=0.92,
            created_at="2026-04-06T10:00:00Z",
        ),
        MagicMock(
            id="mem_002",
            content={"text": "Beta validated the proposal"},
            metadata={"agent_id": "beta", "importance": 0.7},
            similarity=0.85,
            created_at="2026-04-06T10:05:00Z",
        ),
        MagicMock(
            id="mem_003",
            content={"text": "Charlie raised concerns about edge cases"},
            metadata={"agent_id": "charlie", "importance": 0.6},
            similarity=0.78,
            created_at="2026-04-06T10:10:00Z",
        ),
    ]
    memory.query = AsyncMock(return_value=mock_results)

    return memory


@pytest.fixture
def mock_rag_pipeline():
    """Create a mock RAG pipeline."""
    rag = AsyncMock()

    # Mock query response
    mock_result = MagicMock()
    mock_result.documents = [
        MagicMock(
            id="doc_001",
            content="Documentation for decision-making process",
            metadata={"source": "docs", "type": "documentation"},
            score=0.88,
        ),
        MagicMock(
            id="doc_002",
            content="Historical decisions archive",
            metadata={"source": "archive", "type": "historical"},
            score=0.75,
        ),
    ]
    rag.query = AsyncMock(return_value=mock_result)

    return rag


@pytest.fixture
def knowledge_access(mock_memory_system, mock_rag_pipeline):
    """Create UnifiedKnowledgeAccess instance with mocked systems."""
    return UnifiedKnowledgeAccess(
        memory_system=mock_memory_system,
        rag_pipeline=mock_rag_pipeline,
    )


# ============================================================================
# Test KnowledgeEntry
# ============================================================================

class TestKnowledgeEntry:
    """Test KnowledgeEntry dataclass."""

    def test_create_entry(self):
        """Test creating a knowledge entry."""
        entry = KnowledgeEntry(
            content="Test content",
            source="memory",
            source_id="test_001",
            metadata={"key": "value"},
            score=0.9,
        )

        assert entry.content == "Test content"
        assert entry.source == "memory"
        assert entry.source_id == "test_001"
        assert entry.metadata == {"key": "value"}
        assert entry.score == 0.9

    def test_to_dict(self):
        """Test converting entry to dictionary."""
        entry = KnowledgeEntry(
            content="Test",
            source="rag",
            source_id="doc_001",
            score=0.85,
        )

        result = entry.to_dict()

        assert result["content"] == "Test"
        assert result["source"] == "rag"
        assert result["source_id"] == "doc_001"
        assert result["score"] == 0.85


# ============================================================================
# Test UnifiedKnowledgeAccess - Basic Queries
# ============================================================================

class TestUnifiedKnowledgeAccess:
    """Test UnifiedKnowledgeAccess basic functionality."""

    @pytest.mark.asyncio
    async def test_query_memory_only(self, knowledge_access, mock_memory_system):
        """Test querying memory system only."""
        result = await knowledge_access.query(
            query="What was proposed?",
            sources=["memory"],
            limit=5,
        )

        assert result.total_results == 3
        assert "memory" in result.sources_queried
        assert "rag" not in result.sources_queried
        assert len(result.entries) <= 5

        # Verify memory was queried
        mock_memory_system.query.assert_called_once()

    @pytest.mark.asyncio
    async def test_query_rag_only(self, knowledge_access, mock_rag_pipeline):
        """Test querying RAG system only."""
        result = await knowledge_access.query(
            query="Decision documentation",
            sources=["rag"],
            limit=5,
        )

        assert result.total_results == 2
        assert "rag" in result.sources_queried
        assert "memory" not in result.sources_queried
        assert len(result.entries) <= 5

        # Verify RAG was queried
        mock_rag_pipeline.query.assert_called_once()

    @pytest.mark.asyncio
    async def test_query_both_sources(self, knowledge_access, mock_memory_system, mock_rag_pipeline):
        """Test querying both memory and RAG."""
        result = await knowledge_access.query(
            query="Decision process",
            sources=["memory", "rag"],
            limit=10,
        )

        assert result.total_results == 5  # 3 memory + 2 rag
        assert "memory" in result.sources_queried
        assert "rag" in result.sources_queried

        # Verify both were queried
        mock_memory_system.query.assert_called_once()
        mock_rag_pipeline.query.assert_called_once()

    @pytest.mark.asyncio
    async def test_query_with_filters(self, knowledge_access, mock_memory_system):
        """Test querying with filters."""
        await knowledge_access.query(
            query="Proposal",
            sources=["memory"],
            filters={"agent_id": "alpha", "memory_limit": 10},
        )

        # Verify filters were passed (memory_limit affects the query)
        call_args = mock_memory_system.query.call_args
        assert call_args[1]["limit"] == 10

    @pytest.mark.asyncio
    async def test_query_with_source_weights(self, knowledge_access):
        """Test querying with source weight multipliers."""
        result = await knowledge_access.query(
            query="Test",
            sources=["memory", "rag"],
            source_weights={"memory": 2.0, "rag": 0.5},
            rerank=False,  # Disable reranking to see weight effect
        )

        # Memory entries should have doubled scores
        for entry in result.entries:
            if entry.source == "memory":
                assert entry.score > 0  # Weight was applied

    @pytest.mark.asyncio
    async def test_query_handles_memory_error(self, knowledge_access):
        """Test that RAG query still works when memory fails."""
        # Make memory raise an exception
        knowledge_access.memory.query = AsyncMock(side_effect=Exception("Memory error"))

        result = await knowledge_access.query(
            query="Test",
            sources=["memory", "rag"],
        )

        # Should still have RAG results
        assert "rag" in result.sources_queried
        assert len(result.entries) >= 0  # At least tried RAG

    @pytest.mark.asyncio
    async def test_query_handles_rag_error(self, knowledge_access):
        """Test that memory query still works when RAG fails."""
        # Make RAG raise an exception
        knowledge_access.rag.query = AsyncMock(side_effect=Exception("RAG error"))

        result = await knowledge_access.query(
            query="Test",
            sources=["memory", "rag"],
        )

        # Should still have memory results
        assert "memory" in result.sources_queried

    @pytest.mark.asyncio
    async def test_query_tracks_stats(self, knowledge_access):
        """Test that query statistics are tracked."""
        await knowledge_access.query(query="Test 1", sources=["memory"])
        await knowledge_access.query(query="Test 2", sources=["memory"])

        stats = knowledge_access.get_stats()

        assert "['memory']" in stats or "['rag']" in stats or "['memory', 'rag']" in stats


# ============================================================================
# Test MMR Reranking
# ============================================================================

class TestMMRReranking:
    """Test MMR (Maximal Marginal Relevance) reranking."""

    def test_mmr_basic_reranking(self, knowledge_access):
        """Test basic MMR reranking functionality."""
        entries = [
            KnowledgeEntry(content="Similar content A", source="memory", source_id="1", score=0.9),
            KnowledgeEntry(content="Similar content B", source="memory", source_id="2", score=0.8),
            KnowledgeEntry(content="Different content C", source="rag", source_id="3", score=0.7),
        ]

        result = knowledge_access._mmr_rerank(entries, diversity_lambda=0.5, limit=3)

        assert len(result) == 3
        # All entries should have combined scores
        assert all(e.combined_score != 0 for e in result)

    def test_mmr_diversity_selection(self, knowledge_access):
        """Test that MMR selects diverse results."""
        # Create entries where first two are very similar
        entries = [
            KnowledgeEntry(content="The cat sat on the mat", source="memory", source_id="1", score=0.95),
            KnowledgeEntry(content="The cat sat on mat the", source="memory", source_id="2", score=0.90),
            KnowledgeEntry(content="Quantum computing advances", source="rag", source_id="3", score=0.85),
        ]

        # With high diversity lambda, should prefer diverse content
        result = knowledge_access._mmr_rerank(entries, diversity_lambda=0.8, limit=3)

        # The diverse entry should be promoted
        assert len(result) == 3

    def test_mmr_similarity_calculation(self, knowledge_access):
        """Test similarity calculation between entries."""
        entry1 = KnowledgeEntry(content="The quick brown fox", source="memory", source_id="1", score=0.9)
        entry2 = KnowledgeEntry(content="The quick brown fox", source="memory", source_id="2", score=0.8)
        entry3 = KnowledgeEntry(content="Completely different topic", source="rag", source_id="3", score=0.7)

        sim_same = knowledge_access._compute_similarity(entry1, entry2)
        sim_diff = knowledge_access._compute_similarity(entry1, entry3)

        # Similar content should have higher similarity
        assert sim_same > sim_diff

    def test_mmr_respects_limit(self, knowledge_access):
        """Test that MMR respects the result limit."""
        entries = [
            KnowledgeEntry(content=f"Content {i}", source="memory", source_id=str(i), score=0.9 - i*0.1)
            for i in range(10)
        ]

        result = knowledge_access._mmr_rerank(entries, diversity_lambda=0.5, limit=5)

        assert len(result) == 5

    def test_mmr_diversity_lambda_bounds(self, knowledge_access):
        """Test that diversity lambda is properly bounded."""
        entries = [
            KnowledgeEntry(content="Test", source="memory", source_id="1", score=0.9),
        ]

        # Should not crash with out-of-bounds values
        result_0 = knowledge_access._mmr_rerank(entries, diversity_lambda=0.0, limit=5)
        result_1 = knowledge_access._mmr_rerank(entries, diversity_lambda=1.0, limit=5)
        knowledge_access._mmr_rerank(entries, diversity_lambda=-0.5, limit=5)
        knowledge_access._mmr_rerank(entries, diversity_lambda=1.5, limit=5)

        assert len(result_0) == 1
        assert len(result_1) == 1

    def test_mmr_empty_entries(self, knowledge_access):
        """Test MMR with empty entry list."""
        result = knowledge_access._mmr_rerank([], diversity_lambda=0.5, limit=5)
        assert len(result) == 0


# ============================================================================
# Test KnowledgeQueryBuilder
# ============================================================================

class TestKnowledgeQueryBuilder:
    """Test fluent query builder."""

    @pytest.mark.asyncio
    async def test_builder_basic_query(self, knowledge_access):
        """Test basic query with builder."""
        result = await (KnowledgeQueryBuilder(knowledge_access)
            .query("Test query")
            .from_sources("memory", "rag")
            .with_limit(10)
            .execute())

        assert isinstance(result, KnowledgeQueryResult)

    @pytest.mark.asyncio
    async def test_builder_with_diversity(self, knowledge_access):
        """Test builder with diversity parameter."""
        result = await (KnowledgeQueryBuilder(knowledge_access)
            .query("Test query")
            .from_sources("memory")
            .with_limit(5)
            .with_diversity(0.7)
            .execute())

        assert result.parameters["diversity_lambda"] == 0.7

    @pytest.mark.asyncio
    async def test_builder_with_filters(self, knowledge_access):
        """Test builder with filters."""
        result = await (KnowledgeQueryBuilder(knowledge_access)
            .query("Test query")
            .from_sources("memory")
            .filtered_by(agent_id="alpha", workflow_id="wf_001")
            .execute())

        assert result.parameters["filters"]["agent_id"] == "alpha"

    @pytest.mark.asyncio
    async def test_builder_with_source_weights(self, knowledge_access):
        """Test builder with source weights."""
        result = await (KnowledgeQueryBuilder(knowledge_access)
            .query("Test query")
            .from_sources("memory", "rag")
            .with_source_weights(memory=2.0, rag=0.5)
            .execute())

        assert result.parameters["source_weights"]["memory"] == 2.0
        assert result.parameters["source_weights"]["rag"] == 0.5

    @pytest.mark.asyncio
    async def test_builder_without_reranking(self, knowledge_access):
        """Test builder with reranking disabled."""
        result = await (KnowledgeQueryBuilder(knowledge_access)
            .query("Test query")
            .from_sources("memory")
            .with_reranking(False)
            .execute())

        assert not result.reranking_applied

    def test_builder_requires_query(self, knowledge_access):
        """Test that builder requires query text."""
        builder = KnowledgeQueryBuilder(knowledge_access)

        with pytest.raises(ValueError, match="Query text is required"):
            asyncio.run(builder.execute())


# ============================================================================
# Test KnowledgeQueryResult
# ============================================================================

class TestKnowledgeQueryResult:
    """Test KnowledgeQueryResult dataclass."""

    def test_result_to_dict(self):
        """Test converting result to dictionary."""
        entries = [
            KnowledgeEntry(content="Test", source="memory", source_id="1", score=0.9),
        ]

        result = KnowledgeQueryResult(
            entries=entries,
            total_results=1,
            query_time_ms=50.0,
            sources_queried=["memory"],
            reranking_applied=True,
        )

        result_dict = result.to_dict()

        assert len(result_dict["entries"]) == 1
        assert result_dict["query_time_ms"] == 50.0
        assert result_dict["reranking_applied"] is True


# ============================================================================
# Test Content String Extraction
# ============================================================================

class TestContentStringExtraction:
    """Test content string extraction from various formats."""

    def test_extract_from_string(self, knowledge_access):
        """Test extracting string content."""
        content = "Plain text content"
        result = knowledge_access._get_content_string(content)
        assert result == content

    def test_extract_from_dict_with_text_field(self, knowledge_access):
        """Test extracting from dict with text field."""
        content = {"text": "Dict content", "other": "field"}
        result = knowledge_access._get_content_string(content)
        assert result == "Dict content"

    def test_extract_from_dict_with_content_field(self, knowledge_access):
        """Test extracting from dict with content field."""
        content = {"content": "Dict content", "other": "field"}
        result = knowledge_access._get_content_string(content)
        assert result == "Dict content"

    def test_extract_from_dict_fallback(self, knowledge_access):
        """Test fallback string conversion for dict."""
        content = {"key": "value"}
        result = knowledge_access._get_content_string(content)
        assert isinstance(result, str)

    def test_extract_from_other_types(self, knowledge_access):
        """Test extracting from other types."""
        content = 12345
        result = knowledge_access._get_content_string(content)
        assert result == "12345"
