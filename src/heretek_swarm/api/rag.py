"""
RAG API - Document Ingestion and Retrieval

Provides REST API for:
- Document ingestion and processing
- Vector search and retrieval
- RAG query execution
- Document management
"""

from typing import Any, Dict, List, Optional

import structlog
from fastapi import APIRouter, Depends, HTTPException, UploadFile

from rag.document_processor import ProcessingConfig
from rag.rag_pipeline import RAGPipeline

from ..gateway.auth import verify_auth

_logger = structlog.get_logger(__name__)

_router = APIRouter(prefix="/api/rag", tags=["rag"])

# Global RAG pipeline instance
_rag_pipeline: Optional[RAGPipeline] = None

# =============================================================================
# Lifecycle Management
# =============================================================================

async def get_rag_pipeline() -> RAGPipeline:
    """Get or initialize RAG pipeline instance."""
    global _rag_pipeline
    if _rag_pipeline is None:
        from ..rag.rag_pipeline import RAGPipeline
        _rag_pipeline = RAGPipeline()
        await _rag_pipeline.initialize()
    return _rag_pipeline

# =============================================================================
# Document Ingestion Endpoints
# =============================================================================

@router.post("/ingest", status_code=201)
async def ingest_document(
    file: UploadFile,
    metadata: Optional[Dict[str, Any]] = None,
    chunk_strategy: str = "recursive",
    authenticated: str = Depends(verify_auth)
) -> Dict[str, Any]:
    """
    Ingest a document into the RAG system.
    
    Args:
        file: Uploaded document file
        metadata: Optional metadata to attach
        chunk_strategy: Chunking strategy (recursive, fixed_size, semantic, sentence)
        authenticated: Authentication token
    
    Returns:
        Processing result with chunk count and vector storage status
    """
    _pipeline = await get_rag_pipeline()

    try:
        # Read file content
        _content = await file.read()

        # Build processing config
        _config = ProcessingConfig(
            chunk_strategy=chunk_strategy,
            _extract_metadata = True,
            _normalize_whitespace = True,
        )

        # Process document
        _result = await pipeline.ingest_file(
            _file_path = file.filename,
            _content = content.decode('utf-8'),
            _metadata = metadata,
        )

        logger.info(
            "document_ingested",
            filename=file.filename,
            chunks_processed=result.chunks_processed,
            vectors_stored=result.vectors_stored,
        )

        return {
            "filename": file.filename,
            "chunks_processed": result.chunks_processed,
            "vectors_stored": result.vectors_stored,
            "processing_time_ms": result.processing_time_ms,
            "document_id": result.id,
        }

    except Exception as e:
        logger.error("ingest_failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to ingest document: {str(e)}")


@router.post("/ingest/batch", status_code=201)
async def ingest_batch(
    files: List[UploadFile],
    metadata: Optional[Dict[str, Any]] = None,
    authenticated: str = Depends(verify_auth)
) -> Dict[str, Any]:
    """
    Ingest multiple documents in batch.
    
    Args:
        files: List of uploaded files
        metadata: Optional metadata to attach
        authenticated: Authentication token
    
    Returns:
        Batch processing results
    """
    _pipeline = await get_rag_pipeline()

    _results = []
    total_chunks = 0
    _total_vectors = 0

    for file in files:
        try:
            _content = await file.read()
            _result = await pipeline.ingest_file(
                _file_path = file.filename,
                _content = content.decode('utf-8'),
                _metadata = metadata,
            )

            results.append({
                "filename": file.filename,
                "chunks_processed": result.chunks_processed,
                "vectors_stored": result.vectors_stored,
                "document_id": result.id,
            })

            total_chunks += result.chunks_processed
            total_vectors += result.vectors_stored

        except Exception as e:
            logger.error("batch_ingest_failed", filename=file.filename, error=str(e))
            results.append({
                "filename": file.filename,
                "error": str(e),
            })

    logger.info(
        "batch_ingest_completed",
        _total_files = len(files),
        total_chunks=total_chunks,
        _total_vectors = total_vectors,
    )

    return {
        "results": results,
        "total_files": len(files),
        "total_chunks": total_chunks,
        "total_vectors": total_vectors,
    }


# =============================================================================
# Search and Retrieval Endpoints
# =============================================================================

@router.post("/query", status_code=200)
async def query_rag(
    query: str,
    top_k: int = 5,
    search_mode: str = "hybrid",
    authenticated: str = Depends(verify_auth)
) -> Dict[str, Any]:
    """
    Query the RAG system for relevant documents.
    
    Args:
        query: Search query text
        top_k: Number of results to return
        search_mode: Search mode (vector_only, keyword_only, hybrid)
        authenticated: Authentication token
    
    Returns:
        Search results with documents and context
    """
    _pipeline = await get_rag_pipeline()

    try:
        _result = await pipeline.query(
            _query_text = query,
            top_k=top_k,
            _search_mode = search_mode,
        )

        logger.info(
            "rag_query_executed",
            _query = query,
            _documents_found = len(result.documents),
            retrieval_time_ms=result.retrieval_time_ms,
        )

        return {
            "query": query,
            "documents": [d.to_dict() for d in result.documents],
            "context": result.context,
            "total_tokens": result.total_tokens,
            "retrieval_time_ms": result.retrieval_time_ms,
            "embedding_time_ms": result.embedding_time_ms,
            "total_time_ms": result.total_time_ms,
        }

    except Exception as e:
        logger.error("rag_query_failed", query=query, error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to execute RAG query: {str(e)}")


@router.get("/documents", status_code=200)
async def list_documents(
    limit: int = 100,
    offset: int = 0,
    authenticated: str = Depends(verify_auth)
) -> Dict[str, Any]:
    """
    List all ingested documents.
    
    Args:
        limit: Maximum number of documents to return
        offset: Offset for pagination
        authenticated: Authentication token
    
    Returns:
        List of documents with metadata
    """
    _pipeline = await get_rag_pipeline()

    try:
        # Get all documents from vector store
        _documents = await pipeline.list_documents(
            _limit = limit,
            _offset = offset,
        )

        logger.info("documents_listed", count=len(documents))

        return {
            "documents": documents,
            "count": len(documents),
            "limit": limit,
            "offset": offset,
        }

    except Exception as e:
        logger.error("list_documents_failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to list documents: {str(e)}")


@router.get("/documents/{document_id}", status_code=200)
async def get_document(
    document_id: str,
    authenticated: str = Depends(verify_auth)
) -> Dict[str, Any]:
    """
    Get a specific document by ID.
    
    Args:
        document_id: Document ID
        authenticated: Authentication token
    
    Returns:
        Document details with chunks
    """
    _pipeline = await get_rag_pipeline()

    try:
        _document = await pipeline.get_document(document_id)

        if not document:
            raise HTTPException(status_code=404, detail="Document not found")

        logger.info("document_retrieved", document_id=document_id)

        return {
            "id": document.id,
            "source_path": document.source_path,
            "source_type": document.source_type.value,
            "title": document.title,
            "author": document.author,
            "total_characters": document.total_characters,
            "total_lines": document.total_lines,
            "total_chunks": document.total_chunks,
            "created_at": document.created_at,
            "processing_time_ms": document.processing_time_ms,
            "chunk_strategy": document.chunk_strategy.value,
        }

    except Exception as e:
        logger.error("get_document_failed", document_id=document_id, error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to get document: {str(e)}")


@router.delete("/documents/{document_id}", status_code=204)
async def delete_document(
    document_id: str,
    authenticated: str = Depends(verify_auth)
):
    """
    Delete a document and its associated vectors.
    
    Args:
        document_id: Document ID
        authenticated: Authentication token
    
    Returns:
        Success message
    """
    _pipeline = await get_rag_pipeline()

    try:
        _success = await pipeline.delete_document(document_id)

        if not success:
            raise HTTPException(status_code=404, detail="Document not found")

        logger.info("document_deleted", document_id=document_id)

        return {
            "message": f"Document {document_id} deleted successfully"
        }

    except Exception as e:
        logger.error("delete_document_failed", document_id=document_id, error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to delete document: {str(e)}")


# =============================================================================
# RAG Configuration Endpoints
# =============================================================================

@router.get("/config", status_code=200)
async def get_rag_config(
    authenticated: str = Depends(verify_auth)
) -> Dict[str, Any]:
    """
    Get current RAG configuration.
    
    Args:
        authenticated: Authentication token
    
    Returns:
        RAG pipeline configuration
    """
    _pipeline = await get_rag_pipeline()

    return {
        "chunking": {
            "strategy": pipeline.config.processing.chunk_strategy.value,
            "chunk_size": pipeline.config.processing.chunk_size,
            "chunk_overlap": pipeline.config.processing.chunk_overlap,
            "min_chunk_size": pipeline.config.processing.min_chunk_size,
        },
        "embedding": {
            "provider": pipeline.config.embedding.provider.value,
            "model": pipeline.config.embedding.model,
            "dimension": pipeline.config.embedding.dimension,
        },
        "retrieval": {
            "mode": pipeline.config.retrieval.mode.value,
            "top_k": pipeline.config.retrieval.top_k,
            "similarity_threshold": pipeline.config.retrieval.similarity_threshold,
        },
        "storage": {
            "collection_name": pipeline.config.collection_name,
            "persist_processed": pipeline.config.persist_processed,
        },
    }


@router.post("/config", status_code=200)
async def update_rag_config(
    config: Dict[str, Any],
    authenticated: str = Depends(verify_auth)
) -> Dict[str, Any]:
    """
    Update RAG configuration.
    
    Args:
        config: Configuration updates
        authenticated: Authentication token
    
    Returns:
        Updated configuration
    """
    _pipeline = await get_rag_pipeline()

    try:
        # Update chunking config
        if "chunking" in config:
            _chunking = config["chunking"]
            if "strategy" in chunking:
                pipeline.config.processing.chunk_strategy = chunking["strategy"]
            if "chunk_size" in chunking:
                pipeline.config.processing.chunk_size = chunking["chunk_size"]
            if "chunk_overlap" in chunking:
                pipeline.config.processing.chunk_overlap = chunking["chunk_overlap"]

        # Update embedding config
        if "embedding" in config:
            embedding = config["embedding"]
            if "provider" in embedding:
                pipeline.config.embedding.provider = embedding["provider"]
            if "model" in embedding:
                pipeline.config.embedding.model = embedding["model"]

        # Update retrieval config
        if "retrieval" in config:
            retrieval = config["retrieval"]
            if "mode" in retrieval:
                pipeline.config.retrieval.mode = retrieval["mode"]
            if "top_k" in retrieval:
                pipeline.config.retrieval.top_k = retrieval["top_k"]
            if "similarity_threshold" in retrieval:
                pipeline.config.retrieval.similarity_threshold = retrieval["similarity_threshold"]

        # Update storage config
        if "storage" in config:
            _storage = config["storage"]
            if "collection_name" in storage:
                pipeline.config.collection_name = storage["collection_name"]
            if "persist_processed" in storage:
                pipeline.config.persist_processed = storage["persist_processed"]

        logger.info("rag_config_updated", config=config)

        return {
            "message": "RAG configuration updated successfully",
            "config": {
                "chunking": {
                    "strategy": pipeline.config.processing.chunk_strategy.value,
                    "chunk_size": pipeline.config.processing.chunk_size,
                    "chunk_overlap": pipeline.config.processing.chunk_overlap,
                },
                "embedding": {
                    "provider": pipeline.config.embedding.provider.value,
                    "model": pipeline.config.embedding.model,
                    "dimension": pipeline.config.embedding.dimension,
                },
                "retrieval": {
                    "mode": pipeline.config.retrieval.mode.value,
                    "top_k": pipeline.config.retrieval.top_k,
                    "similarity_threshold": pipeline.config.retrieval.similarity_threshold,
                },
                "storage": {
                    "collection_name": pipeline.config.collection_name,
                    "persist_processed": pipeline.config.persist_processed,
                },
            },
        }

    except Exception as e:
        logger.error("update_rag_config_failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to update RAG config: {str(e)}")
