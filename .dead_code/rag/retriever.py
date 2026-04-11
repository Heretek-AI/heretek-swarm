"""
Hybrid Retriever - Vector + Keyword Search Fusion.

Implements hybrid search combining:
- Vector similarity search (semantic)
- BM25 keyword search (lexical)
- Reciprocal Rank Fusion (RRF) for result combination

Pattern stolen from:
- heretek-openclaw-plugins/hybrid-search
- elizaOS BM25 implementation
"""

import asyncio
import math
import re
from collections import Counter
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

import structlog

logger = structlog.get_logger(__name__)


class SearchMode(Enum):
    """Search mode options."""
    VECTOR_ONLY = "vector_only"
    KEYWORD_ONLY = "keyword_only"
    HYBRID = "hybrid"


@dataclass
class RetrievalConfig:
    """Configuration for hybrid retrieval."""

    # Search mode
    mode: SearchMode = SearchMode.HYBRID

    # Result limits
    top_k: int = 10
    vector_top_k: int = 50
    keyword_top_k: int = 50

    # Vector search settings
    similarity_threshold: float = 0.7

    # Hybrid fusion settings
    rrf_k: int = 60  # RRF constant
    vector_weight: float = 0.6
    keyword_weight: float = 0.4

    # Keyword search settings
    bm25_k1: float = 1.5  # Term frequency saturation
    bm25_b: float = 0.75  # Length normalization


@dataclass
class SearchResult:
    """A single search result."""

    id: str
    content: str
    score: float
    vector_score: float | None = None
    keyword_score: float | None = None

    # Source information
    document_id: str | None = None
    source_path: str | None = None
    chunk_index: int = 0

    # Metadata
    metadata: dict[str, Any] = field(default_factory=dict)
    highlights: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "content": self.content,
            "score": self.score,
            "vector_score": self.vector_score,
            "keyword_score": self.keyword_score,
            "document_id": self.document_id,
            "source_path": self.source_path,
            "chunk_index": self.chunk_index,
            "metadata": self.metadata,
            "highlights": self.highlights,
        }


class BM25Index:
    """
    In-memory BM25 index for keyword search.

    Pattern stolen from elizaOS BM25 implementation.
    """

    def __init__(self, k1: float = 1.5, b: float = 0.75):
        self.k1 = k1
        self.b = b

        # Document storage
        self.documents: dict[str, dict[str, Any]] = {}

        # Index structures
        self.doc_lengths: dict[str, int] = {}
        self.avg_doc_length: float = 0.0
        self.term_doc_freqs: dict[str, int] = Counter()
        self.inverted_index: dict[str, dict[str, int]] = {}

        self._indexed = False

    def tokenize(self, text: str) -> list[str]:
        """Tokenize text for indexing/searching."""
        # Lowercase and split on non-alphanumeric
        text = text.lower()
        return re.findall(r"\b[a-z0-9]+\b", text)

    def add_document(self, doc_id: str, content: str, metadata: dict[str, Any] | None = None) -> None:
        """Add a document to the index."""
        tokens = self.tokenize(content)
        term_freqs = Counter(tokens)

        self.documents[doc_id] = {
            "content": content,
            "tokens": tokens,
            "term_freqs": term_freqs,
            "metadata": metadata or {},
        }

        self.doc_lengths[doc_id] = len(tokens)

        # Update inverted index
        for term, freq in term_freqs.items():
            if term not in self.inverted_index:
                self.inverted_index[term] = {}
            self.inverted_index[term][doc_id] = freq

        self._indexed = False

    def add_documents(self, documents: list[dict[str, Any]]) -> None:
        """Add multiple documents."""
        for doc in documents:
            self.add_document(
                doc_id=doc["id"],
                content=doc["content"],
                metadata=doc.get("metadata"),
            )
        self._reindex()

    def _reindex(self) -> None:
        """Rebuild index statistics."""
        if not self.documents:
            return

        # Calculate average document length
        total_length = sum(self.doc_lengths.values())
        self.avg_doc_length = total_length / len(self.documents)

        # Calculate document frequencies
        self.term_doc_freqs = Counter()
        for term, doc_dict in self.inverted_index.items():
            self.term_doc_freqs[term] = len(doc_dict)

        self._indexed = True

    def search(self, query: str, top_k: int = 10) -> list[tuple[str, float]]:
        """
        Search using BM25 scoring.

        Args:
            query: Query text
            top_k: Number of results

        Returns:
            List of (doc_id, score) tuples
        """
        if not self._indexed:
            self._reindex()

        query_tokens = self.tokenize(query)
        scores: dict[str, float] = {}

        N = len(self.documents)

        for token in query_tokens:
            if token not in self.inverted_index:
                continue

            # IDF calculation
            df = self.term_doc_freqs.get(token, 0)
            if df == 0:
                continue

            idf = math.log((N - df + 0.5) / (df + 0.5) + 1)

            # Score each document containing the term
            for doc_id, tf in self.inverted_index[token].items():
                doc_length = self.doc_lengths[doc_id]

                # BM25 score
                numerator = tf * (self.k1 + 1)
                denominator = tf + self.k1 * (1 - self.b + self.b * doc_length / self.avg_doc_length)
                score = idf * numerator / denominator

                if doc_id not in scores:
                    scores[doc_id] = 0
                scores[doc_id] += score

        # Sort by score
        sorted_results = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        return sorted_results[:top_k]

    def get_document(self, doc_id: str) -> dict[str, Any] | None:
        """Get document by ID."""
        return self.documents.get(doc_id)

    def clear(self) -> None:
        """Clear the index."""
        self.documents.clear()
        self.doc_lengths.clear()
        self.term_doc_freqs.clear()
        self.inverted_index.clear()
        self.avg_doc_length = 0
        self._indexed = False


class HybridRetriever:
    """
    Hybrid retrieval combining vector and keyword search.

    Features:
    - Vector similarity search via Qdrant/mem0
    - BM25 keyword search via in-memory index
    - Reciprocal Rank Fusion for combining results
    - Configurable weighting

    Pattern stolen from heretek-openclaw-plugins/hybrid-search
    """

    def __init__(
        self,
        config: RetrievalConfig | None = None,
        vector_client: Any | None = None,
    ):
        self.config = config or RetrievalConfig()
        self._vector_client = vector_client
        self._bm25_index = BM25Index(
            k1=self.config.bm25_k1,
            b=self.config.bm25_b,
        )
        self._embedding_service = None
        self._initialized = False

    async def initialize(self, embedding_service: Any | None = None) -> None:
        """Initialize the retriever."""
        self._embedding_service = embedding_service

        if self._vector_client is None:
            # Try to connect to Qdrant
            try:
                from qdrant_client import QdrantClient

                self._vector_client = QdrantClient(
                    host=os.getenv("QDRANT_HOST", "localhost"),
                    port=int(os.getenv("QDRANT_PORT", "6333")),
                )
                logger.info("qdrant_client_connected")
            except ImportError:
                logger.warning("qdrant_client not installed")

        self._initialized = True

    async def index_documents(self, documents: list[dict[str, Any]]) -> None:
        """
        Index documents for both vector and keyword search.

        Args:
            documents: List of documents with id, content, embedding, metadata
        """
        # Add to BM25 index
        self._bm25_index.add_documents(documents)

        # Add to vector store
        if self._vector_client:
            await self._index_vectors(documents)

        logger.info("documents_indexed", count=len(documents))

    async def _index_vectors(self, documents: list[dict[str, Any]]) -> None:
        """Index documents in vector store."""
        try:
            from qdrant_client.models import PointStruct

            points = []
            for doc in documents:
                if doc.get("embedding"):
                    points.append(PointStruct(
                        id=doc["id"],
                        vector=doc["embedding"],
                        payload={
                            "content": doc["content"],
                            "document_id": doc.get("document_id"),
                            "source_path": doc.get("source_path"),
                            "metadata": doc.get("metadata", {}),
                        },
                    ))

            if points:
                self._vector_client.upsert(
                    collection_name="heretek_documents",
                    points=points,
                )
        except Exception as e:
            logger.error("vector_index_failed", error=str(e))

    async def search(
        self,
        query: str,
        query_embedding: list[float] | None = None,
        filters: dict[str, Any] | None = None,
    ) -> list[SearchResult]:
        """
        Perform hybrid search.

        Args:
            query: Query text
            query_embedding: Pre-computed query embedding (optional)
            filters: Optional metadata filters

        Returns:
            List of SearchResult objects
        """
        if not self._initialized:
            await self.initialize()

        results = []

        if self.config.mode == SearchMode.VECTOR_ONLY:
            results = await self._vector_search(query, query_embedding, filters)
        elif self.config.mode == SearchMode.KEYWORD_ONLY:
            results = await self._keyword_search(query)
        else:
            # Hybrid search
            results = await self._hybrid_search(query, query_embedding, filters)

        return results

    async def _vector_search(
        self,
        query: str,
        query_embedding: list[float] | None = None,
        filters: dict[str, Any] | None = None,
    ) -> list[SearchResult]:
        """Perform vector similarity search."""
        if not self._vector_client:
            return []

        # Get query embedding if not provided
        if query_embedding is None and self._embedding_service:
            result = await self._embedding_service.embed(query)
            query_embedding = result.embedding

        if query_embedding is None:
            return []

        try:
            search_results = self._vector_client.search(
                collection_name="heretek_documents",
                query_vector=query_embedding,
                limit=self.config.vector_top_k,
                score_threshold=self.config.similarity_threshold,
                query_filter=filters,
            )

            results = []
            for hit in search_results:
                results.append(SearchResult(
                    id=str(hit.id),
                    content=hit.payload.get("content", ""),
                    score=hit.score,
                    vector_score=hit.score,
                    document_id=hit.payload.get("document_id"),
                    source_path=hit.payload.get("source_path"),
                    metadata=hit.payload.get("metadata", {}),
                ))

            return results
        except Exception as e:
            logger.error("vector_search_failed", error=str(e))
            return []

    async def _keyword_search(self, query: str) -> list[SearchResult]:
        """Perform BM25 keyword search."""
        bm25_results = self._bm25_index.search(query, self.config.keyword_top_k)

        results = []
        for doc_id, score in bm25_results:
            doc = self._bm25_index.get_document(doc_id)
            if doc:
                results.append(SearchResult(
                    id=doc_id,
                    content=doc["content"],
                    score=score,
                    keyword_score=score,
                    metadata=doc.get("metadata", {}),
                ))

        return results

    async def _hybrid_search(
        self,
        query: str,
        query_embedding: list[float] | None = None,
        filters: dict[str, Any] | None = None,
    ) -> list[SearchResult]:
        """
        Perform hybrid search with Reciprocal Rank Fusion.

        RRF formula: score(d) = sum(1 / (k + rank(d))) for each ranking
        """
        # Run both searches in parallel
        vector_task = self._vector_search(query, query_embedding, filters)
        keyword_task = self._keyword_search(query)

        vector_results, keyword_results = await asyncio.gather(
            vector_task, keyword_task,
        )

        # Create rank dictionaries
        vector_ranks = {r.id: i + 1 for i, r in enumerate(vector_results)}
        keyword_ranks = {r.id: i + 1 for i, r in enumerate(keyword_results)}

        # Combine all unique IDs
        all_ids = set(vector_ranks.keys()) | set(keyword_ranks.keys())

        # Calculate RRF scores
        rrf_scores: dict[str, float] = {}
        for doc_id in all_ids:
            vector_rank = vector_ranks.get(doc_id, float("inf"))
            keyword_rank = keyword_ranks.get(doc_id, float("inf"))

            # RRF score with weights
            vector_score = self.config.vector_weight / (self.config.rrf_k + vector_rank) if vector_rank != float("inf") else 0
            keyword_score = self.config.keyword_weight / (self.config.rrf_k + keyword_rank) if keyword_rank != float("inf") else 0

            rrf_scores[doc_id] = vector_score + keyword_score

        # Build result map
        result_map: dict[str, SearchResult] = {}
        for r in vector_results:
            result_map[r.id] = r
        for r in keyword_results:
            if r.id in result_map:
                # Merge scores
                result_map[r.id].keyword_score = r.keyword_score
            else:
                result_map[r.id] = r

        # Sort by RRF score
        sorted_ids = sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True)

        # Build final results
        final_results = []
        for doc_id, score in sorted_ids[:self.config.top_k]:
            if doc_id in result_map:
                result = result_map[doc_id]
                result.score = score
                final_results.append(result)

        return final_results

    def add_document(
        self,
        doc_id: str,
        content: str,
        embedding: list[float] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Add a single document to the index."""
        self._bm25_index.add_document(doc_id, content, metadata)

        if self._vector_client and embedding:
            asyncio.create_task(self._index_vectors([{
                "id": doc_id,
                "content": content,
                "embedding": embedding,
                "metadata": metadata or {},
            }]))

    def clear(self) -> None:
        """Clear all indexes."""
        self._bm25_index.clear()
        # Note: Doesn't clear vector store - would need explicit deletion


# Import os for environment variables
import os
