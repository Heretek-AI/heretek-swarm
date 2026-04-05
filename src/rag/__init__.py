"""
RAG (Retrieval-Augmented Generation) Module for Heretek Swarm.

This module provides document ingestion, processing, and retrieval capabilities:
- Document chunking with configurable strategies
- Vector embedding generation
- Semantic search with hybrid support
- Integration with mem0 and Qdrant

Reference: MiniMax Audit + elizaOS advanced_capabilities/document-ingestion
"""

from .document_processor import DocumentProcessor, DocumentChunk, ProcessingConfig
from .embedding_service import EmbeddingService, EmbeddingConfig
from .rag_pipeline import RAGPipeline, RAGConfig, RAGResult
from .retriever import HybridRetriever, RetrievalConfig

__all__ = [
    "DocumentProcessor",
    "DocumentChunk",
    "ProcessingConfig",
    "EmbeddingService",
    "EmbeddingConfig",
    "RAGPipeline",
    "RAGConfig",
    "RAGResult",
    "HybridRetriever",
    "RetrievalConfig",
]
