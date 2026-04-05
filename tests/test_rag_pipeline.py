"""
RAG Pipeline Tests

Tests for document processing, embedding, and retrieval.
"""

import os
import pytest
import tempfile
from pathlib import Path

from rag import (
    DocumentProcessor,
    DocumentChunk,
    ProcessingConfig,
    ChunkStrategy,
    DocumentType,
    RAGPipeline,
    RAGConfig,
    HybridRetriever,
    RetrievalConfig,
    SearchMode,
)


# =============================================================================
# Document Processor Tests
# =============================================================================

class TestDocumentProcessor:
    """Test document processing functionality."""
    
    @pytest.fixture
    def processor(self):
        return DocumentProcessor()
    
    @pytest.fixture
    def config(self):
        return ProcessingConfig(
            chunk_strategy=ChunkStrategy.RECURSIVE,
            chunk_size=500,
            chunk_overlap=50,
        )
    
    def test_detect_type(self, processor):
        """Test document type detection."""
        assert processor.detect_type("test.md") == DocumentType.MARKDOWN
        assert processor.detect_type("test.txt") == DocumentType.TEXT
        assert processor.detect_type("test.py") == DocumentType.CODE
        assert processor.detect_type("test.json") == DocumentType.JSON
        assert processor.detect_type("test.unknown") == DocumentType.UNKNOWN
    
    def test_generate_id(self, processor):
        """Test ID generation."""
        id1 = processor.generate_id("content", "source")
        id2 = processor.generate_id("content", "source")
        id3 = processor.generate_id("different", "source")
        
        assert id1 == id2  # Same content = same ID
        assert id1 != id3  # Different content = different ID
        assert len(id1) == 16  # 16 character hex
    
    @pytest.mark.asyncio
    async def test_process_content_simple(self, processor, config):
        """Test processing simple content."""
        content = "This is a test document. " * 50
        
        doc = await processor.process_content(
            content=content,
            source_path="test.txt",
            doc_type=DocumentType.TEXT,
        )
        
        assert doc.id is not None
        assert doc.source_path == "test.txt"
        assert len(doc.chunks) > 0
        assert doc.total_characters == len(content.strip())
    
    @pytest.mark.asyncio
    async def test_chunk_recursive(self, processor, config):
        """Test recursive chunking."""
        processor.config = config
        
        # Create content with multiple paragraphs
        content = "\n\n".join([
            f"Paragraph {i}. " + "Word " * 100
            for i in range(5)
        ])
        
        doc = await processor.process_content(
            content=content,
            source_path="test.md",
            doc_type=DocumentType.MARKDOWN,
        )
        
        assert len(doc.chunks) > 1
        
        # Check chunks have proper metadata
        for chunk in doc.chunks:
            assert chunk.total_chunks == len(doc.chunks)
            assert len(chunk.content) >= config.min_chunk_size
    
    @pytest.mark.asyncio
    async def test_chunk_fixed_size(self, processor):
        """Test fixed-size chunking."""
        processor.config = ProcessingConfig(
            chunk_strategy=ChunkStrategy.FIXED_SIZE,
            chunk_size=200,
            chunk_overlap=20,
        )
        
        content = "Test content. " * 50
        doc = await processor.process_content(
            content=content,
            source_path="test.txt",
        )
        
        assert len(doc.chunks) > 1
    
    @pytest.mark.asyncio
    async def test_process_file(self, processor):
        """Test file processing."""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".txt", delete=False
        ) as f:
            f.write("Test file content.\n" * 20)
            temp_path = f.name
        
        try:
            doc = await processor.process_file(temp_path)
            
            assert doc.id is not None
            assert doc.source_path == temp_path
            assert len(doc.chunks) > 0
        finally:
            os.unlink(temp_path)
    
    def test_clean_content_html(self, processor):
        """Test HTML cleaning."""
        html = "<html><body><p>Test <b>content</b></p><script>alert('xss')</script></body></html>"
        cleaned = processor._clean_content(html, DocumentType.HTML)
        
        assert "<html>" not in cleaned
        assert "<script>" not in cleaned
        assert "Test content" in cleaned
    
    def test_normalize_whitespace(self, processor):
        """Test whitespace normalization."""
        text = "Multiple   spaces   and\n\n\n\nnewlines"
        normalized = processor._normalize_whitespace(text)
        
        assert "   " not in normalized
        assert "\n\n\n" not in normalized


# =============================================================================
# Hybrid Retriever Tests
# =============================================================================

class TestHybridRetriever:
    """Test hybrid retrieval functionality."""
    
    @pytest.fixture
    def retriever(self):
        return HybridRetriever()
    
    @pytest.fixture
    def sample_documents(self):
        return [
            {
                "id": "doc1",
                "content": "Python is a programming language used for web development, data science, and automation.",
                "metadata": {"topic": "programming"},
            },
            {
                "id": "doc2",
                "content": "JavaScript is a scripting language for web browsers and Node.js servers.",
                "metadata": {"topic": "programming"},
            },
            {
                "id": "doc3",
                "content": "Machine learning algorithms can classify data and make predictions.",
                "metadata": {"topic": "ml"},
            },
        ]
    
    @pytest.mark.asyncio
    async def test_index_and_search(self, retriever, sample_documents):
        """Test indexing and searching documents."""
        await retriever.initialize()
        
        # Index documents
        await retriever.index_documents(sample_documents)
        
        # Search
        results = await retriever.search("python programming", SearchMode.KEYWORD_ONLY)
        
        assert len(results) > 0
        assert "python" in results[0].content.lower()
    
    def test_bm25_search(self, retriever, sample_documents):
        """Test BM25 keyword search."""
        retriever._bm25_index.add_documents(sample_documents)
        
        results = retriever._bm25_index.search("programming language")
        
        assert len(results) > 0
        # doc1 should rank higher for "programming language"
        assert results[0][0] == "doc1"


# =============================================================================
# BM25 Index Tests
# =============================================================================

class TestBM25Index:
    """Test BM25 index functionality."""
    
    @pytest.fixture
    def index(self):
        from rag.retriever import BM25Index
        return BM25Index()
    
    def test_add_and_search(self, index):
        """Test adding documents and searching."""
        index.add_document("1", "The quick brown fox jumps over the lazy dog")
        index.add_document("2", "A fast fox runs through the forest")
        index.add_document("3", "Dogs are loyal pets")
        
        results = index.search("fox")
        
        assert len(results) > 0
        # Documents with fox should rank higher
        assert results[0][0] in ["1", "2"]
    
    def test_tokenize(self, index):
        """Test tokenization."""
        tokens = index.tokenize("Hello World 123!")
        
        assert "hello" in tokens
        assert "world" in tokens
        assert "123" in tokens
        assert "!" not in tokens
    
    def test_empty_search(self, index):
        """Test search with no documents."""
        results = index.search("test")
        assert results == []
    
    def test_clear(self, index):
        """Test clearing index."""
        index.add_document("1", "Test document")
        index.clear()
        
        assert len(index.documents) == 0
        assert len(index.inverted_index) == 0


# =============================================================================
# RAG Pipeline Integration Tests
# =============================================================================

class TestRAGPipeline:
    """Integration tests for RAG pipeline."""
    
    @pytest.fixture
    def config(self):
        return RAGConfig(
            processing=ProcessingConfig(chunk_size=200, chunk_overlap=20),
            retrieval=RetrievalConfig(mode=SearchMode.KEYWORD_ONLY),
        )
    
    @pytest.fixture
    def pipeline(self, config):
        return RAGPipeline(config=config)
    
    @pytest.mark.asyncio
    async def test_ingest_and_query(self, pipeline):
        """Test full ingest and query workflow."""
        await pipeline.initialize()
        
        # Ingest content
        await pipeline.ingest_text(
            content="Python is a popular programming language. "
                   "It is used for web development, data science, and automation. "
                   "Python has a simple syntax that is easy to learn.",
            source="python_intro.txt",
        )
        
        # Query
        result = await pipeline.query("python programming", top_k=3)
        
        assert len(result.documents) > 0
        assert "python" in result.context.lower()
        assert result.total_time_ms > 0
    
    @pytest.mark.asyncio
    async def test_ingest_file(self, pipeline):
        """Test file ingestion."""
        await pipeline.initialize()
        
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".md", delete=False
        ) as f:
            f.write("# Test Document\n\n")
            f.write("This is a test document for RAG. " * 10)
            temp_path = f.name
        
        try:
            doc = await pipeline.ingest_file(temp_path)
            
            assert doc.id is not None
            assert len(doc.chunks) > 0
            assert pipeline.get_stats()["documents_processed"] == 1
        finally:
            os.unlink(temp_path)
    
    @pytest.mark.asyncio
    async def test_context_assembly(self, pipeline):
        """Test context assembly."""
        await pipeline.initialize()
        
        # Ingest multiple documents
        for i in range(3):
            await pipeline.ingest_text(
                content=f"Document {i}: " + "Content " * 50,
                source=f"doc{i}.txt",
            )
        
        result = await pipeline.query("document", top_k=2)
        
        assert len(result.documents) <= 2
        assert len(result.context) > 0
        assert "---" in result.context  # Separator


# =============================================================================
# Embedding Service Tests (Mocked)
# =============================================================================

class TestEmbeddingService:
    """Test embedding service (requires mocking for API calls)."""
    
    @pytest.mark.asyncio
    async def test_cache(self):
        """Test embedding caching."""
        from rag.embedding_service import EmbeddingCache, EmbeddingResult
        
        cache = EmbeddingCache()
        result = EmbeddingResult(
            embedding=[0.1, 0.2, 0.3],
            text_hash="abc123",
            model="test-model",
            dimensions=3,
        )
        
        # Cache miss
        cached = cache.get("test text", "test-model")
        assert cached is None
        
        # Cache set
        cache.set("test text", "test-model", result)
        
        # Cache hit
        cached = cache.get("test text", "test-model")
        assert cached is not None
        assert cached.embedding == [0.1, 0.2, 0.3]
        
        # Clear
        cache.clear()
        cached = cache.get("test text", "test-model")
        assert cached is None
