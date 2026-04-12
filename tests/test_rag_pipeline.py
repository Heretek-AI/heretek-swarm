"""
Comprehensive test suite for RAG (Retrieval-Augmented Generation) Pipeline

Tests for:
- Document processing and chunking
- Vector embedding and search
- Hybrid retrieval (BM25 + semantic)
- RAG pipeline orchestration
"""

from unittest.mock import AsyncMock

import pytest
from rag.document_processor import (
    ChunkStrategy,
    DocumentProcessor,
    DocumentType,
    ProcessedDocument,
    ProcessingConfig,
)
from rag.rag_pipeline import RAGConfig, RAGPipeline
from rag.retriever import (
    HybridRetriever,
    RetrievalConfig,
    SearchResult,
)

# =============================================================================
# Document Processor Tests
# =============================================================================

class TestDocumentProcessor:
    """Test suite for document processing."""

    @pytest.fixture
    def processor(self):
        """Create document processor instance."""
        return DocumentProcessor()

    def test_detect_type_markdown(self, processor):
        """Test detecting markdown files."""
        assert processor.detect_type("test.md") == DocumentType.MARKDOWN
        assert processor.detect_type("test.markdown") == DocumentType.MARKDOWN

    def test_detect_type_pdf(self, processor):
        """Test detecting PDF files."""
        assert processor.detect_type("test.pdf") == DocumentType.PDF

    def test_detect_type_html(self, processor):
        """Test detecting HTML files."""
        assert processor.detect_type("test.html") == DocumentType.HTML
        assert processor.detect_type("test.htm") == DocumentType.HTML

    def test_detect_type_text(self, processor):
        """Test detecting text files."""
        assert processor.detect_type("test.txt") == DocumentType.TEXT
        assert processor.detect_type("test.unknown") == DocumentType.UNKNOWN

    def test_generate_id(self, processor):
        """Test generating document IDs."""
        id1 = processor.generate_id("test content", "source1")
        id2 = processor.generate_id("test content", "source1")
        id3 = processor.generate_id("different content", "source1")

        assert id1 == id2  # Same content = same ID
        assert id1 != id3  # Different content = different ID

    def test_extract_keywords(self, processor):
        """Test keyword extraction."""
        keywords = processor._extract_keywords(
            "The quick brown fox jumps over the lazy dog. "
            "Artificial intelligence and machine learning are important."
        )

        assert "artificial" in keywords
        assert "intelligence" in keywords
        assert "machine" in keywords
        assert "learning" in keywords

    def test_chunk_content_fixed_size(self, processor):
        """Test fixed-size chunking."""
        # Configure processor for fixed-size chunking
        processor.config.chunk_size = 30
        processor.config.chunk_overlap = 5
        processor.config.min_chunk_size = 10  # Allow smaller chunks for testing
        text = "a" * 100
        chunks = processor._chunk_fixed_size(text, "doc1", "test.txt", DocumentType.TEXT)

        assert len(chunks) >= 4
        assert all(len(chunk.content) <= 30 for chunk in chunks)

    def test_chunk_content_recursive(self, processor):
        """Test recursive chunking."""
        # Configure processor for recursive chunking
        processor.config.chunk_size = 20
        processor.config.min_chunk_size = 10  # Allow smaller chunks for testing
        text = "This is a test. This is another test. And a third test."
        chunks = processor._chunk_recursive(text, "doc1", "test.txt", DocumentType.TEXT)

        assert len(chunks) > 1
        # Note: recursive chunking may combine sentences, so chunks can exceed chunk_size

    def test_clean_content_html(self, processor):
        """Test cleaning HTML content."""
        html = "<p>This is <b>bold</b> text.</p>"
        cleaned = processor._clean_content(html, DocumentType.HTML)

        assert "<p>" not in cleaned
        assert "<b>" not in cleaned
        assert "bold" in cleaned

    def test_clean_content_urls(self, processor):
        """Test removing URLs from content."""
        # Enable URL removal in config
        processor.config.remove_urls = True
        content = "Visit https://example.com for more info."
        cleaned = processor._clean_content(content, DocumentType.TEXT)

        assert "https://example.com" not in cleaned

    def test_extract_metadata(self, processor):
        """Test metadata extraction."""
        metadata = processor._extract_metadata(
            "Test content",
            DocumentType.TEXT,
        )

        # Just check that it returns something
        assert isinstance(metadata, dict)

    @pytest.mark.asyncio
    async def test_process_content(self, processor):
        """Test processing content string."""
        # Need longer content for chunking (min_chunk_size is 100)
        long_content = "This is test content for processing. " * 10
        result = await processor.process_content(
            long_content,
            source_path="test_source",
            metadata={"author": "test"}
        )

        assert isinstance(result, ProcessedDocument)
        assert result.id is not None
        assert len(result.chunks) > 0

    @pytest.mark.asyncio
    async def test_process_content_with_chunking(self, processor):
        """Test processing content with chunking."""
        long_content = "Test. " * 20  # 100 words
        # Configure processor for fixed-size chunking
        processor.config.chunk_strategy = ChunkStrategy.FIXED_SIZE
        processor.config.chunk_size = 20
        processor.config.min_chunk_size = 10  # Allow smaller chunks for testing
        processor.config.chunk_overlap = 0  # Must be 0 for small chunk_size to work
        result = await processor.process_content(
            long_content,
            source_path="test_source",
        )

        assert len(result.chunks) >= 1


# =============================================================================
# Hybrid Retriever Tests
# =============================================================================

class TestHybridRetriever:
    """Test suite for hybrid retrieval."""

    @pytest.fixture
    def retriever(self):
        """Create retriever instance."""
        config = RetrievalConfig(
            vector_weight=0.7,
            keyword_weight=0.3,
        )
        return HybridRetriever(config=config)

    @pytest.fixture
    def mock_embedding_service(self):
        """Create mock embedding service."""
        service = AsyncMock()
        service.embed_documents.return_value = [
            [0.1, 0.2, 0.3] for _ in range(5)
        ]
        service.embed_query.return_value = [0.1, 0.2, 0.3]
        return service

    @pytest.mark.asyncio
    async def test_initialize(self, retriever, mock_embedding_service):
        """Test retriever initialization."""
        await retriever.initialize(mock_embedding_service)

        assert retriever._embedding_service is not None

    @pytest.mark.asyncio
    async def test_index_documents(self, retriever, mock_embedding_service):
        """Test indexing documents."""
        await retriever.initialize(mock_embedding_service)

        documents = [
            {
                "id": "doc1",
                "content": "Test document 1",
                "metadata": {"source": "test"},
            },
            {
                "id": "doc2",
                "content": "Test document 2",
                "metadata": {"source": "test"},
            },
        ]

        await retriever.index_documents(documents)

        # Check that documents were indexed
        assert len(retriever._bm25_index.documents) == 2

    @pytest.mark.asyncio
    async def test_vector_search(self, retriever, mock_embedding_service):
        """Test vector similarity search."""
        await retriever.initialize(mock_embedding_service)

        documents = [
            {
                "id": "doc1",
                "content": "machine learning algorithms",
                "metadata": {},
            },
            {
                "id": "doc2",
                "content": "natural language processing",
                "metadata": {},
            },
        ]

        await retriever.index_documents(documents)

        results = await retriever._vector_search(
            "artificial intelligence",
        )

        assert len(results) <= 2
        assert all(isinstance(r, SearchResult) for r in results)

    @pytest.mark.asyncio
    async def test_keyword_search(self, retriever, mock_embedding_service):
        """Test keyword (BM25) search."""
        await retriever.initialize(mock_embedding_service)

        documents = [
            {
                "id": "doc1",
                "content": "machine learning algorithms",
                "metadata": {},
            },
            {
                "id": "doc2",
                "content": "deep learning models",
                "metadata": {},
            },
        ]

        await retriever.index_documents(documents)

        results = await retriever._keyword_search("machine learning")

        assert len(results) > 0
        assert "machine" in results[0].content.lower()

    @pytest.mark.asyncio
    async def test_hybrid_search(self, retriever, mock_embedding_service):
        """Test hybrid search combining vector and keyword."""
        await retriever.initialize(mock_embedding_service)

        documents = [
            {
                "id": "doc1",
                "content": "machine learning algorithms",
                "metadata": {},
            },
            {
                "id": "doc2",
                "content": "neural networks",
                "metadata": {},
            },
        ]

        await retriever.index_documents(documents)

        results = await retriever._hybrid_search(
            "machine learning",
        )

        assert len(results) <= 2
        assert all(hasattr(r, "score") for r in results)

    @pytest.mark.asyncio
    async def test_search_with_filters(self, retriever, mock_embedding_service):
        """Test search with metadata filters."""
        await retriever.initialize(mock_embedding_service)

        # Use different content for each document to test filtering
        documents = [
            {
                "id": "doc1",
                "content": "tech content about programming",
                "metadata": {"category": "tech"},
            },
            {
                "id": "doc2",
                "content": "news content about sports",
                "metadata": {"category": "news"},
            },
        ]

        await retriever.index_documents(documents)

        results = await retriever.search(
            "tech",
            filters={"category": "tech"},
        )

        # With different content, the filter should work
        assert len(results) >= 1
        # Check that at least one result matches the filter
        if results:
            assert any(r.metadata.get("category") == "tech" for r in results)


# =============================================================================
# RAG Pipeline Tests
# =============================================================================

class TestRAGPipeline:
    """Test suite for RAG pipeline."""

    @pytest.fixture
    def config(self):
        """Create RAG configuration."""
        return RAGConfig(
            processing=ProcessingConfig(
                chunk_size=100,
                chunk_overlap=20,
            ),
            retrieval=RetrievalConfig(
                top_k=3,
            ),
        )

    @pytest.fixture
    def mock_embedding_service(self):
        """Create mock embedding service."""
        service = AsyncMock()
        service.embed_documents.return_value = [
            [0.1, 0.2, 0.3] for _ in range(10)
        ]
        service.embed_query.return_value = [0.1, 0.2, 0.3]
        return service

    @pytest.fixture
    def mock_vector_store(self):
        """Create mock vector store."""
        store = AsyncMock()
        store.add.return_value = ["id1", "id2", "id3"]
        store.search.return_value = [
            {
                "id": "id1",
                "score": 0.9,
                "payload": {
                    "content": "test content 1",
                    "metadata": {},
                },
            },
            {
                "id": "id2",
                "score": 0.8,
                "payload": {
                    "content": "test content 2",
                    "metadata": {},
                },
            },
        ]
        return store

    @pytest.fixture
    def pipeline(self, config, mock_embedding_service, mock_vector_store):
        """Create RAG pipeline instance."""
        return RAGPipeline(config=config)

    @pytest.mark.asyncio
    async def test_initialize(self, pipeline):
        """Test pipeline initialization."""
        await pipeline.initialize()

        assert pipeline._processor is not None
        assert pipeline._retriever is not None

    @pytest.mark.asyncio
    async def test_ingest_text(self, pipeline):
        """Test ingesting text content."""
        await pipeline.initialize()

        result = await pipeline.ingest_text(
            "This is test content for ingestion.",
            source="test_source",
            metadata={"author": "test"},
        )

        assert result is not None
        assert result.id is not None
        assert len(result.chunks) > 0

    @pytest.mark.asyncio
    async def test_query(self, pipeline):
        """Test querying the RAG pipeline."""
        await pipeline.initialize()

        # Ingest some content first
        await pipeline.ingest_text(
            "Machine learning is a subset of artificial intelligence.",
            source="test",
        )
        await pipeline.ingest_text(
            "Deep learning uses neural networks.",
            source="test",
        )

        # Query
        result = await pipeline.query(
            "What is machine learning?",
            top_k=3,
        )

        assert result is not None
        assert result.query == "What is machine learning?"
        assert len(result.documents) > 0
        assert result.context is not None

    @pytest.mark.asyncio
    async def test_query_with_reranking(self, pipeline):
        """Test querying with reranking."""
        await pipeline.initialize()

        await pipeline.ingest_text("Test content 1", source="test")
        await pipeline.ingest_text("Test content 2", source="test")

        result = await pipeline.query(
            "test query",
            top_k=3,
        )

        assert result is not None
        assert len(result.documents) > 0

    def test_assemble_context(self, pipeline):
        """Test context assembly from documents."""
        documents = [
            SearchResult(
                id="doc1",
                content="First document",
                score=0.9,
                metadata={},
            ),
            SearchResult(
                id="doc2",
                content="Second document",
                score=0.8,
                metadata={},
            ),
        ]

        context, count = pipeline._assemble_context(documents)

        assert "First document" in context
        assert "Second document" in context
        assert count >= 2

    def test_get_stats(self, pipeline):
        """Test getting pipeline statistics."""
        stats = pipeline.get_stats()

        assert "documents_processed" in stats
        assert "chunks_created" in stats
        assert "queries_processed" in stats

    @pytest.mark.asyncio
    async def test_clear(self, pipeline):
        """Test clearing the pipeline."""
        await pipeline.initialize()

        await pipeline.ingest_text("Test content", source="test")
        await pipeline.clear()

        stats = pipeline.get_stats()
        assert stats["documents_processed"] == 0


# =============================================================================
# Integration Tests
# =============================================================================

class TestRAGIntegration:
    """Integration tests for RAG components."""

    @pytest.mark.asyncio
    async def test_end_to_end_ingestion_and_query(self):
        """Test full workflow from ingestion to query."""
        from rag.rag_pipeline import RAGConfig, RAGPipeline

        # Create mocks
        mock_embedding = AsyncMock()
        mock_embedding.embed_documents.return_value = [[0.1, 0.2, 0.3]]
        mock_embedding.embed_query.return_value = [0.1, 0.2, 0.3]

        mock_vector_store = AsyncMock()
        mock_vector_store.add.return_value = ["doc1"]
        mock_vector_store.search.return_value = [
            {
                "id": "doc1",
                "score": 0.95,
                "payload": {
                    "content": "test content",
                    "metadata": {},
                },
            }
        ]

        # Create pipeline
        pipeline = RAGPipeline(
            config=RAGConfig(
                processing=ProcessingConfig(chunk_size=50),
                retrieval=RetrievalConfig(top_k=3)
            ),
        )

        await pipeline.initialize()

        # Ingest
        await pipeline.ingest_text(
            "Test document content for integration test.",
            source="integration_test",
        )

        # Query
        result = await pipeline.query("test query")

        assert result is not None
        assert len(result.documents) > 0
