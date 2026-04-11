"""
RAG Pipeline - Complete Retrieval-Augmented Generation System.

Orchestrates the full RAG workflow:
1. Document ingestion and processing
2. Embedding generation
3. Vector and keyword indexing
4. Retrieval with hybrid search
5. Context assembly for LLM

Pattern stolen from:
- elizaOS advanced_capabilities/document-ingestion
- LangChain RAG patterns
- Flowise RAG components
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import structlog

from .document_processor import (
    DocumentProcessor,
    DocumentType,
    ProcessedDocument,
    ProcessingConfig,
)
from .embedding_service import (
    EmbeddingConfig,
    EmbeddingService,
)
from .retriever import (
    HybridRetriever,
    RetrievalConfig,
    SearchResult,
)

logger = structlog.get_logger(__name__)


@dataclass
class RAGConfig:
    """Configuration for RAG pipeline."""

    # Document processing
    processing: ProcessingConfig = field(default_factory=ProcessingConfig)

    # Embedding service
    embedding: EmbeddingConfig = field(default_factory=EmbeddingConfig)

    # Retrieval
    retrieval: RetrievalConfig = field(default_factory=RetrievalConfig)

    # Context assembly
    max_context_tokens: int = 4000
    context_window_buffer: int = 500  # Buffer for prompt/response
    include_metadata: bool = True
    include_source_paths: bool = True

    # Storage
    collection_name: str = "heretek_documents"
    persist_processed: bool = True
    processed_dir: str = "/data/rag/processed"


@dataclass
class RAGResult:
    """Result of RAG query."""

    query: str
    documents: list[SearchResult]
    context: str
    total_tokens: int

    # Metadata
    retrieval_time_ms: float = 0.0
    embedding_time_ms: float = 0.0
    total_time_ms: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "query": self.query,
            "documents": [d.to_dict() for d in self.documents],
            "context": self.context,
            "total_tokens": self.total_tokens,
            "retrieval_time_ms": self.retrieval_time_ms,
            "embedding_time_ms": self.embedding_time_ms,
            "total_time_ms": self.total_time_ms,
        }


class RAGPipeline:
    """
    Complete RAG pipeline for document ingestion and retrieval.

    Workflow:
    1. Ingest: Load documents → Chunk → Embed → Index
    2. Query: Embed query → Retrieve → Assemble context

    Features:
    - Multiple chunking strategies
    - Hybrid search (vector + keyword)
    - Token-aware context assembly
    - Integration with mem0/Qdrant

    Pattern stolen from elizaOS document-ingestion plugin.
    """

    def __init__(
        self,
        config: RAGConfig | None = None,
        memory_backend: Any | None = None,
    ):
        self.config = config or RAGConfig()
        self._memory_backend = memory_backend

        # Initialize components
        self._processor = DocumentProcessor(self.config.processing)
        self._embedding_service = EmbeddingService(self.config.embedding)
        self._retriever = HybridRetriever(
            self.config.retrieval,
        )

        # Statistics
        self._stats = {
            "documents_processed": 0,
            "chunks_created": 0,
            "queries_processed": 0,
            "total_retrieval_time_ms": 0,
        }

        self._initialized = False

    async def initialize(self) -> None:
        """Initialize the RAG pipeline."""
        await self._embedding_service.initialize()
        await self._retriever.initialize(self._embedding_service)

        # Create processed directory if needed
        if self.config.persist_processed:
            Path(self.config.processed_dir).mkdir(parents=True, exist_ok=True)

        self._initialized = True
        logger.info("rag_pipeline_initialized")

    async def ingest_file(
        self,
        file_path: str | Path,
        metadata: dict[str, Any] | None = None,
    ) -> ProcessedDocument:
        """
        Ingest a file into the RAG system.

        Args:
            file_path: Path to file
            metadata: Optional metadata

        Returns:
            ProcessedDocument with chunks
        """
        if not self._initialized:
            await self.initialize()

        import time
        start_time = time.time()

        # Process document
        doc = await self._processor.process_file(file_path, metadata)

        # Generate embeddings for chunks
        chunk_texts = [c.content for c in doc.chunks]
        embeddings = await self._embedding_service.embed_batch(chunk_texts)

        # Index chunks
        documents = []
        for i, chunk in enumerate(doc.chunks):
            documents.append({
                "id": chunk.id,
                "content": chunk.content,
                "embedding": embeddings[i].embedding if i < len(embeddings) else None,
                "document_id": doc.id,
                "source_path": doc.source_path,
                "metadata": {
                    "chunk_index": chunk.chunk_index,
                    "total_chunks": chunk.total_chunks,
                    "source_type": chunk.source_type.value,
                    **chunk.metadata,
                },
            })

        await self._retriever.index_documents(documents)

        # Update stats
        self._stats["documents_processed"] += 1
        self._stats["chunks_created"] += len(doc.chunks)

        # Persist if enabled
        if self.config.persist_processed:
            await self._persist_document(doc)

        elapsed = (time.time() - start_time) * 1000
        logger.info(
            "file_ingested",
            path=str(file_path),
            chunks=len(doc.chunks),
            time_ms=elapsed,
        )

        return doc

    async def ingest_directory(
        self,
        directory: str | Path,
        recursive: bool = True,
        extensions: list[str] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> list[ProcessedDocument]:
        """
        Ingest all files in a directory.

        Args:
            directory: Directory path
            recursive: Process subdirectories
            extensions: File extensions to include (e.g., [".md", ".txt"])
            metadata: Optional metadata for all files

        Returns:
            List of ProcessedDocuments
        """
        dir_path = Path(directory)
        if not dir_path.is_dir():
            raise ValueError(f"Not a directory: {directory}")

        # Find files
        pattern = "**/*" if recursive else "*"

        files = list(dir_path.glob(pattern))

        # Filter by extension
        if extensions:
            extensions_set = {e.lower() for e in extensions}
            files = [f for f in files if f.suffix.lower() in extensions_set]
        else:
            # Filter to supported types
            supported = {".txt", ".md", ".html", ".json", ".py", ".js", ".ts"}
            files = [f for f in files if f.suffix.lower() in supported]

        # Process files
        results = []
        for file_path in files:
            if file_path.is_file():
                try:
                    doc = await self.ingest_file(file_path, metadata)
                    results.append(doc)
                except Exception as e:
                    logger.warning(
                        "file_ingest_failed",
                        path=str(file_path),
                        error=str(e),
                    )

        return results

    async def ingest_text(
        self,
        content: str,
        source: str,
        doc_type: DocumentType = DocumentType.TEXT,
        metadata: dict[str, Any] | None = None,
    ) -> ProcessedDocument:
        """
        Ingest raw text content.

        Args:
            content: Text content
            source: Source identifier
            doc_type: Document type
            metadata: Optional metadata

        Returns:
            ProcessedDocument
        """
        if not self._initialized:
            await self.initialize()

        # Process content
        doc = await self._processor.process_content(
            content=content,
            source_path=source,
            doc_type=doc_type,
            metadata=metadata,
        )

        # Generate embeddings
        chunk_texts = [c.content for c in doc.chunks]
        embeddings = await self._embedding_service.embed_batch(chunk_texts)

        # Index chunks
        documents = []
        for i, chunk in enumerate(doc.chunks):
            documents.append({
                "id": chunk.id,
                "content": chunk.content,
                "embedding": embeddings[i].embedding if i < len(embeddings) else None,
                "document_id": doc.id,
                "source_path": source,
                "metadata": {
                    "chunk_index": chunk.chunk_index,
                    "total_chunks": chunk.total_chunks,
                    **chunk.metadata,
                },
            })

        await self._retriever.index_documents(documents)

        self._stats["documents_processed"] += 1
        self._stats["chunks_created"] += len(doc.chunks)

        return doc

    async def query(
        self,
        query: str,
        top_k: int = 5,
        filters: dict[str, Any] | None = None,
    ) -> RAGResult:
        """
        Query the RAG system.

        Args:
            query: Query text
            top_k: Number of results
            filters: Optional metadata filters

        Returns:
            RAGResult with context and documents
        """
        if not self._initialized:
            await self.initialize()

        import time
        start_time = time.time()

        # Generate query embedding
        embed_start = time.time()
        query_embedding_result = await self._embedding_service.embed(query)
        embed_time = (time.time() - embed_start) * 1000

        # Retrieve documents
        retrieve_start = time.time()
        original_top_k = self.config.retrieval.top_k
        self.config.retrieval.top_k = top_k
        documents = await self._retriever.search(
            query=query,
            query_embedding=query_embedding_result.embedding,
            filters=filters,
        )
        self.config.retrieval.top_k = original_top_k
        retrieve_time = (time.time() - retrieve_start) * 1000

        # Assemble context
        context, token_count = self._assemble_context(documents)

        # Calculate total time
        total_time = (time.time() - start_time) * 1000

        # Update stats
        self._stats["queries_processed"] += 1
        self._stats["total_retrieval_time_ms"] += retrieve_time

        return RAGResult(
            query=query,
            documents=documents,
            context=context,
            total_tokens=token_count,
            retrieval_time_ms=retrieve_time,
            embedding_time_ms=embed_time,
            total_time_ms=total_time,
        )

    def _assemble_context(self, documents: list[SearchResult]) -> tuple[str, int]:
        """
        Assemble context from retrieved documents.

        Token-aware assembly that respects max_context_tokens.
        """
        max_tokens = self.config.max_context_tokens - self.config.context_window_buffer

        context_parts = []
        total_tokens = 0

        for doc in documents:
            # Estimate tokens (rough: 1 token ≈ 4 characters)
            doc_tokens = len(doc.content) // 4

            if total_tokens + doc_tokens > max_tokens:
                # Truncate to fit
                remaining_tokens = max_tokens - total_tokens
                if remaining_tokens > 50:
                    truncated_content = doc.content[:remaining_tokens * 4]
                    context_parts.append(f"[Document {doc.id}]\n{truncated_content}...")
                    total_tokens += remaining_tokens
                break

            # Build document entry
            parts = []

            if self.config.include_source_paths and doc.source_path:
                parts.append(f"Source: {doc.source_path}")

            if self.config.include_metadata and doc.metadata:
                parts.append(f"Chunk: {doc.metadata.get('chunk_index', 0) + 1}/{doc.metadata.get('total_chunks', 1)}")

            parts.append(doc.content)

            doc_text = "\n".join(parts)
            context_parts.append(doc_text)
            total_tokens += doc_tokens

        context = "\n\n---\n\n".join(context_parts)
        return context, total_tokens

    async def _persist_document(self, doc: ProcessedDocument) -> None:
        """Persist processed document to disk."""
        import json

        path = Path(self.config.processed_dir) / f"{doc.id}.json"
        with open(path, "w") as f:
            json.dump(doc.to_dict(), f, indent=2)

    def get_stats(self) -> dict[str, Any]:
        """Get pipeline statistics."""
        avg_retrieval_time = 0
        if self._stats["queries_processed"] > 0:
            avg_retrieval_time = (
                self._stats["total_retrieval_time_ms"] /
                self._stats["queries_processed"]
            )

        return {
            **self._stats,
            "avg_retrieval_time_ms": avg_retrieval_time,
        }

    async def clear(self) -> None:
        """Clear all indexed data."""
        self._retriever.clear()
        self._stats = {
            "documents_processed": 0,
            "chunks_created": 0,
            "queries_processed": 0,
            "total_retrieval_time_ms": 0,
        }

    async def shutdown(self) -> None:
        """Shutdown the pipeline."""
        await self._embedding_service.shutdown()
        self._initialized = False
