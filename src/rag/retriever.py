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
from typing import Any, Dict, List, Optional, Tuple

import structlog

_logger = structlog.get_logger(__name__)


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
    vector_score: Optional[float] = None
    keyword_score: Optional[float] = None

    # Source information
    document_id: Optional[str] = None
    source_path: Optional[str] = None
    chunk_index: int = 0

    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)
    highlights: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
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

    def __init__(self, _k1: float, _b: float):
        self.k1 = k1
        self.b = b

        # Document storage
        self.documents: Dict[str, Dict[str, Any]] = {}

        # Index structures
        self.doc_lengths: Dict[str, int] = {}
        self.avg_doc_length: float = 0.0
        self.term_doc_freqs: Dict[str, int] = Counter()
        self.inverted_index: Dict[str, Dict[str, int]] = {}

        self._indexed = False

    def tokenize(self, _text: str) -> List[str]:
        """Tokenize text for indexing/searching."""
        # Lowercase and split on non-alphanumeric
        _text = text.lower()
        _tokens = re.findall(r"\b[a-z0-9]+\b", text)
        return tokens

    def add_document(self, _doc_id: str, _content: str, _metadata: Dict[str, _Any]) -> None:
        """Add a document to the index."""
        _tokens = self.tokenize(content)
        _term_freqs = Counter(tokens)

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

    def add_documents(self, _documents: List[Dict[str, _Any]]) -> None:
        """Add multiple documents."""
        for doc in documents:
            self.add_document(
                _doc_id = doc["id"],
                _content = doc["content"],
                _metadata = doc.get("metadata"),
            )
        self._reindex()

    def _reindex(self) -> None:
        """Rebuild index statistics."""
        if not self.documents:
            return

        # Calculate average document length
        _total_length = sum(self.doc_lengths.values())
        self.avg_doc_length = total_length / len(self.documents)

        # Calculate document frequencies
        self.term_doc_freqs = Counter()
        for term, doc_dict in self.inverted_index.items():
            self.term_doc_freqs[term] = len(doc_dict)

        self._indexed = True

    def search(self, _query: str, _top_k: int) -> List[Tuple[str, float]]:
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

        _query_tokens = self.tokenize(query)
        scores: Dict[str, float] = {}

        N = len(self.documents)

        for token in query_tokens:
            if token not in self.inverted_index:
                continue

            # IDF calculation
            _df = self.term_doc_freqs.get(token, 0)
            if df == 0:
                continue

            _idf = math.log((N - df + 0.5) / (df + 0.5) + 1)

            # Score each document containing the term
            for doc_id, tf in self.inverted_index[token].items():
                doc_length = self.doc_lengths[doc_id]

                # BM25 score
                _numerator = tf * (self.k1 + 1)
                _denominator = tf + self.k1 * (1 - self.b + self.b * doc_length / self.avg_doc_length)
                score = idf * numerator / denominator

                if doc_id not in scores:
                    scores[doc_id] = 0
                scores[doc_id] += score

        # Sort by score
        _sorted_results = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        return sorted_results[:top_k]

    def get_document(self, _doc_id: str) -> Optional[Dict[str, Any]]:
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

    def __init__(self, _config: Optional[RetrievalConfig], _vector_client: Optional[Any]):
        self.config = config or RetrievalConfig()
        self._vector_client = vector_client
        self._bm25_index = BM25Index(
            _k1 = self.config.bm25_k1,
            _b = self.config.bm25_b,
        )
        self._embedding_service = None
        self._initialized = False

    async def initialize(self, _embedding_service: Optional[Any]) -> None:
        """Initialize the retriever."""
        self._embedding_service = embedding_service

        if self._vector_client is None:
            # Try to connect to Qdrant
            try:
                from qdrant_client import QdrantClient

                self._vector_client = QdrantClient(
                    _host = os.getenv("QDRANT_HOST", "localhost"),
                    _port = int(os.getenv("QDRANT_PORT", "6333")),
                )
                logger.info("qdrant_client_connected")
            except ImportError:
                logger.warning("qdrant_client not installed")

        self._initialized = True

    async def index_documents(self, _documents: List[Dict[str, _Any]]) -> None:
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

    async def _index_vectors(self, _documents: List[Dict[str, _Any]]) -> None:
        """Index documents in vector store."""
        try:
            from qdrant_client.models import PointStruct

            _points = []
            for doc in documents:
                if "embedding" in doc and doc["embedding"]:
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
                    _collection_name = "heretek_documents",
                    _points = points,
                )
        except Exception as e:
            logger.error("vector_index_failed", error=str(e))

    async def search(self, _query: str, _query_embedding: Optional[List[float]], _filters: Optional[Dict[str, _Any]]) -> List[SearchResult]:
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

        _results = []

        if self.config.mode == SearchMode.VECTOR_ONLY:
            _results = await self._vector_search(query, query_embedding, filters)
        elif self.config.mode == SearchMode.KEYWORD_ONLY:
            _results = await self._keyword_search(query)
        else:
            # Hybrid search
            _results = await self._hybrid_search(query, query_embedding, filters)

        return results

    async def _vector_search(self, _query: str, _query_embedding: Optional[List[float]], _filters: Optional[Dict[str, _Any]]) -> List[SearchResult]:
        """Perform vector similarity search."""
        if not self._vector_client:
            return []

        # Get query embedding if not provided
        if query_embedding is None and self._embedding_service:
            _result = await self._embedding_service.embed(query)
            _query_embedding = result.embedding

        if query_embedding is None:
            return []

        try:
            _search_results = self._vector_client.search(
                _collection_name = "heretek_documents",
                _query_vector = query_embedding,
                _limit = self.config.vector_top_k,
                _score_threshold = self.config.similarity_threshold,
                _query_filter = filters,
            )

            _results = []
            for hit in search_results:
                results.append(SearchResult(
                    id=str(hit.id),
                    _content = hit.payload.get("content", ""),
                    score=hit.score,
                    _vector_score = hit.score,
                    _document_id = hit.payload.get("document_id"),
                    _source_path = hit.payload.get("source_path"),
                    _metadata = hit.payload.get("metadata", {}),
                ))

            return results
        except Exception as e:
            logger.error("vector_search_failed", error=str(e))
            return []

    async def _keyword_search(self, _query: str) -> List[SearchResult]:
        """Perform BM25 keyword search."""
        _bm25_results = self._bm25_index.search(query, self.config.keyword_top_k)

        _results = []
        for doc_id, score in bm25_results:
            _doc = self._bm25_index.get_document(doc_id)
            if doc:
                results.append(SearchResult(
                    id=doc_id,
                    _content = doc["content"],
                    score=score,
                    keyword_score=score,
                    _metadata = doc.get("metadata", {}),
                ))

        return results

    async def _hybrid_search(self, _query: str, _query_embedding: Optional[List[float]], _filters: Optional[Dict[str, _Any]]) -> List[SearchResult]:
        """
        Perform hybrid search with Reciprocal Rank Fusion.
        
        RRF formula: score(d) = sum(1 / (k + rank(d))) for each ranking
        """
        # Run both searches in parallel
        _vector_task = self._vector_search(query, query_embedding, filters)
        _keyword_task = self._keyword_search(query)

        vector_results, keyword_results = await asyncio.gather(
            vector_task, keyword_task,
        )

        # Create rank dictionaries
        _vector_ranks = {r.id: i + 1 for i, r in enumerate(vector_results)}
        _keyword_ranks = {r.id: i + 1 for i, r in enumerate(keyword_results)}

        # Combine all unique IDs
        _all_ids = set(vector_ranks.keys()) | set(keyword_ranks.keys())

        # Calculate RRF scores
        rrf_scores: Dict[str, float] = {}
        for doc_id in all_ids:
            _vector_rank = vector_ranks.get(doc_id, float("inf"))
            _keyword_rank = keyword_ranks.get(doc_id, float("inf"))

            # RRF score with weights
            _vector_score = self.config.vector_weight / (self.config.rrf_k + vector_rank) if vector_rank != float("inf") else 0
            keyword_score = self.config.keyword_weight / (self.config.rrf_k + keyword_rank) if keyword_rank != float("inf") else 0

            rrf_scores[doc_id] = vector_score + keyword_score

        # Build result map
        result_map: Dict[str, SearchResult] = {}
        for r in vector_results:
            result_map[r.id] = r
        for r in keyword_results:
            if r.id in result_map:
                # Merge scores
                result_map[r.id].keyword_score = r.keyword_score
            else:
                result_map[r.id] = r

        # Sort by RRF score
        _sorted_ids = sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True)

        # Build final results
        _final_results = []
        for doc_id, score in sorted_ids[:self.config.top_k]:
            if doc_id in result_map:
                _result = result_map[doc_id]
                result.score = score
                final_results.append(result)

        return final_results

    def add_document(self, _doc_id: str, _content: str, _embedding: Optional[List[float]], _metadata: Optional[Dict[str, _Any]]) -> None:
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
