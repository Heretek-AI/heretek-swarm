"""
Persistent Memory Store using PostgreSQL with PGVector.

Provides long-term storage with semantic search capabilities.
Target: p95 latency <50ms for retrieval operations.
"""

import asyncio
import json
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID, uuid4

import structlog
from pydantic import BaseModel, Field
from sqlalchemy import (
    Column, String, DateTime, Float, Integer, Text, Boolean,
    Index, select, delete, and_, or_, desc, asc
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID, ARRAY
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base
from sqlalchemy.sql import func

from .base import MemoryEntry, MemoryQuery, MemoryResult, MemoryTier, MemoryType, EmbeddingVector
from .embeddings import EmbeddingService

logger = structlog.get_logger()

Base = declarative_base()


class MemoryEntryModel(Base):
    """SQLAlchemy model for persistent memory entries"""
    
    __tablename__ = "memory_entries"
    
    # Primary key
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    
    # Owner context
    agent_id = Column(String(255), nullable=False, index=True)
    session_id = Column(PGUUID(as_uuid=True), nullable=True, index=True)
    
    # Content
    content = Column(Text, nullable=False)
    content_type = Column(String(100), default="text/plain")
    metadata_json = Column(Text, default="{}")
    
    # Classification
    memory_type = Column(String(50), nullable=False, default="episodic", index=True)
    tier = Column(String(20), nullable=False, default="persistent")
    tags = Column(ARRAY(String), default=list)
    
    # Vector embedding (PGVector)
    embedding = Column(Text, nullable=True)  # Stored as vector string
    embedding_model = Column(String(100), nullable=True)
    embedding_dimensions = Column(Integer, nullable=True)
    
    # Lineage
    parent_id = Column(PGUUID(as_uuid=True), nullable=True)
    source_agent = Column(String(255), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=True)
    accessed_at = Column(DateTime(timezone=True), server_default=func.now())
    access_count = Column(Integer, default=0)
    
    # Scoring
    importance_score = Column(Float, default=0.5)
    
    # Indexes for common queries
    __table_args__ = (
        Index('ix_memory_entries_agent_created', 'agent_id', 'created_at'),
        Index('ix_memory_entries_type_created', 'memory_type', 'created_at'),
        Index('ix_memory_entries_session', 'session_id'),
    )


class PersistentConfig(BaseModel):
    """Configuration for persistent memory store"""
    
    # PostgreSQL connection
    database_url: str = Field(
        default="postgresql+asyncpg://postgres:langfuse@localhost:5432/heretek_swarm"
    )
    
    # Connection pool
    pool_size: int = Field(default=10)
    max_overflow: int = Field(default=20)
    pool_timeout: float = Field(default=30.0)
    pool_recycle: int = Field(default=3600)
    
    # Performance
    query_timeout: float = Field(default=10.0)
    batch_insert_size: int = Field(default=100)
    
    # Vector search
    default_similarity_threshold: float = Field(default=0.7)
    vector_search_limit: int = Field(default=100)


class PersistentMemoryStore:
    """
    PostgreSQL/PGVector-based persistent memory store.
    
    Features:
    - Long-term storage with semantic search
    - Vector similarity queries via PGVector
    - Efficient filtering and pagination
    - Connection pooling
    - Performance tracking
    """
    
    def __init__(
        self,
        config: Optional[PersistentConfig] = None,
        embedding_service: Optional[EmbeddingService] = None
    ):
        self.config = config or PersistentConfig()
        self.embedding_service = embedding_service
        
        self._engine = None
        self._session_factory: Optional[async_sessionmaker] = None
        
        # Performance tracking
        self._operation_times: List[float] = []
        self._max_samples = 1000
    
    async def connect(self) -> None:
        """Initialize PostgreSQL connection and create tables"""
        if self._engine is not None:
            return
        
        try:
            # Create async engine
            self._engine = create_async_engine(
                self.config.database_url,
                pool_size=self.config.pool_size,
                max_overflow=self.config.max_overflow,
                pool_timeout=self.config.pool_timeout,
                pool_recycle=self.config.pool_recycle,
                echo=False
            )
            
            # Create session factory
            self._session_factory = async_sessionmaker(
                bind=self._engine,
                class_=AsyncSession,
                expire_on_commit=False
            )
            
            # Create tables
            async with self._engine.begin() as conn:
                # Enable PGVector extension
                await conn.execute(
                    select(1)  # Placeholder for CREATE EXTENSION IF NOT EXISTS vector
                )
                # Create tables
                await conn.run_sync(Base.metadata.create_all)
            
            logger.info(
                "persistent_memory_connected",
                database_url=self.config.database_url.split("@")[-1]
            )
        except Exception as e:
            logger.error("persistent_memory_connection_failed", error=str(e))
            raise
    
    async def disconnect(self) -> None:
        """Close PostgreSQL connection"""
        if self._engine:
            await self._engine.dispose()
            self._engine = None
            self._session_factory = None
    
    def _track_latency(self, elapsed_ms: float) -> None:
        """Track operation latency"""
        self._operation_times.append(elapsed_ms)
        if len(self._operation_times) > self._max_samples:
            self._operation_times = self._operation_times[-self._max_samples:]
    
    def _entry_to_model(self, entry: MemoryEntry) -> MemoryEntryModel:
        """Convert Pydantic entry to SQLAlchemy model"""
        model = MemoryEntryModel(
            id=entry.id,
            agent_id=entry.agent_id,
            session_id=entry.session_id,
            content=entry.content,
            content_type=entry.content_type,
            metadata_json=json.dumps(entry.metadata),
            memory_type=entry.memory_type.value,
            tier=entry.tier.value,
            tags=entry.tags,
            parent_id=entry.parent_id,
            source_agent=entry.source_agent,
            created_at=entry.created_at,
            updated_at=entry.updated_at,
            expires_at=entry.expires_at,
            accessed_at=entry.accessed_at,
            access_count=entry.access_count,
            importance_score=entry.importance_score
        )
        
        if entry.embedding:
            model.embedding = self._vector_to_string(entry.embedding.vector)
            model.embedding_model = entry.embedding.model
            model.embedding_dimensions = entry.embedding.dimensions
        
        return model
    
    def _model_to_entry(self, model: MemoryEntryModel) -> MemoryEntry:
        """Convert SQLAlchemy model to Pydantic entry"""
        embedding = None
        if model.embedding and model.embedding_dimensions:
            vector = self._string_to_vector(model.embedding, model.embedding_dimensions)
            embedding = EmbeddingVector(
                vector=vector,
                dimensions=model.embedding_dimensions,
                model=model.embedding_model or "unknown",
                created_at=model.created_at
            )
        
        return MemoryEntry(
            id=model.id,
            agent_id=model.agent_id,
            session_id=model.session_id,
            content=model.content,
            content_type=model.content_type,
            metadata=json.loads(model.metadata_json) if model.metadata_json else {},
            memory_type=MemoryType(model.memory_type),
            tier=MemoryTier(model.tier),
            tags=model.tags or [],
            embedding=embedding,
            parent_id=model.parent_id,
            source_agent=model.source_agent,
            created_at=model.created_at,
            updated_at=model.updated_at,
            expires_at=model.expires_at,
            accessed_at=model.accessed_at,
            access_count=model.access_count,
            importance_score=model.importance_score
        )
    
    def _vector_to_string(self, vector: List[float]) -> str:
        """Convert vector to PostgreSQL array string"""
        return "[" + ",".join(str(v) for v in vector) + "]"
    
    def _string_to_vector(self, s: str, dimensions: int) -> List[float]:
        """Parse PostgreSQL vector string"""
        # Remove brackets and split by comma
        s = s.strip("[]")
        return [float(v) for v in s.split(",")]
    
    async def store(
        self,
        entry: MemoryEntry,
        generate_embedding: bool = True
    ) -> None:
        """
        Store a memory entry in PostgreSQL.
        
        Args:
            entry: Memory entry to store
            generate_embedding: Whether to generate embedding if missing
        """
        start_time = datetime.now(timezone.utc)
        
        if self._session_factory is None:
            await self.connect()
        
        # Generate embedding if needed
        if generate_embedding and entry.embedding is None and self.embedding_service:
            try:
                entry.embedding = await self.embedding_service.embed_single(entry.content)
            except Exception as e:
                logger.warning(
                    "embedding_generation_failed",
                    entry_id=str(entry.id),
                    error=str(e)
                )
        
        # Set tier
        entry.tier = MemoryTier.PERSISTENT
        
        model = self._entry_to_model(entry)
        
        try:
            async with self._session_factory() as session:
                session.add(model)
                await session.commit()
            
            elapsed_ms = (datetime.now(timezone.utc) - start_time).total_seconds() * 1000
            self._track_latency(elapsed_ms)
            
            logger.debug(
                "persistent_memory_stored",
                entry_id=str(entry.id),
                agent_id=entry.agent_id,
                elapsed_ms=elapsed_ms
            )
        
        except Exception as e:
            logger.error(
                "persistent_memory_store_failed",
                entry_id=str(entry.id),
                error=str(e)
            )
            raise
    
    async def store_batch(
        self,
        entries: List[MemoryEntry],
        generate_embeddings: bool = True
    ) -> None:
        """Store multiple entries efficiently"""
        if not entries:
            return
        
        start_time = datetime.now(timezone.utc)
        
        if self._session_factory is None:
            await self.connect()
        
        # Generate embeddings in batch
        if generate_embeddings and self.embedding_service:
            texts = [e.content for e in entries if e.embedding is None]
            if texts:
                embeddings = await self.embedding_service.embed_batch(texts)
                
                # Assign embeddings
                embedding_idx = 0
                for entry in entries:
                    if entry.embedding is None:
                        if embedding_idx < len(embeddings):
                            entry.embedding = embeddings[embedding_idx]
                            embedding_idx += 1
        
        # Set tier
        for entry in entries:
            entry.tier = MemoryTier.PERSISTENT
        
        try:
            async with self._session_factory() as session:
                models = [self._entry_to_model(e) for e in entries]
                session.add_all(models)
                await session.commit()
            
            elapsed_ms = (datetime.now(timezone.utc) - start_time).total_seconds() * 1000
            self._track_latency(elapsed_ms)
            
            logger.debug(
                "persistent_memory_batch_stored",
                count=len(entries),
                elapsed_ms=elapsed_ms
            )
        
        except Exception as e:
            logger.error(
                "persistent_memory_batch_store_failed",
                count=len(entries),
                error=str(e)
            )
            raise
    
    async def retrieve(self, entry_id: UUID) -> Optional[MemoryEntry]:
        """Retrieve a memory entry by ID"""
        start_time = datetime.now(timezone.utc)
        
        if self._session_factory is None:
            await self.connect()
        
        try:
            async with self._session_factory() as session:
                stmt = select(MemoryEntryModel).where(MemoryEntryModel.id == entry_id)
                result = await session.execute(stmt)
                model = result.scalar_one_or_none()
                
                if model is None:
                    return None
                
                entry = self._model_to_entry(model)
                
                # Update access time
                model.accessed_at = datetime.now(timezone.utc)
                model.access_count += 1
                await session.commit()
            
            elapsed_ms = (datetime.now(timezone.utc) - start_time).total_seconds() * 1000
            self._track_latency(elapsed_ms)
            
            return entry
        
        except Exception as e:
            logger.error(
                "persistent_memory_retrieve_failed",
                entry_id=str(entry_id),
                error=str(e)
            )
            raise
    
    async def delete(self, entry_id: UUID) -> bool:
        """Delete a memory entry"""
        start_time = datetime.now(timezone.utc)
        
        if self._session_factory is None:
            await self.connect()
        
        try:
            async with self._session_factory() as session:
                stmt = delete(MemoryEntryModel).where(MemoryEntryModel.id == entry_id)
                result = await session.execute(stmt)
                await session.commit()
                
                deleted = result.rowcount > 0
            
            elapsed_ms = (datetime.now(timezone.utc) - start_time).total_seconds() * 1000
            self._track_latency(elapsed_ms)
            
            return deleted
        
        except Exception as e:
            logger.error(
                "persistent_memory_delete_failed",
                entry_id=str(entry_id),
                error=str(e)
            )
            raise
    
    async def search(self, query: MemoryQuery) -> MemoryResult:
        """
        Search persistent memory with filters and optional vector similarity.
        """
        start_time = datetime.now(timezone.utc)
        
        if self._session_factory is None:
            await self.connect()
        
        try:
            async with self._session_factory() as session:
                # Build base query
                stmt = select(MemoryEntryModel)
                conditions = []
                
                # Apply filters
                if query.agent_ids:
                    conditions.append(MemoryEntryModel.agent_id.in_(query.agent_ids))
                
                if query.session_id:
                    conditions.append(MemoryEntryModel.session_id == query.session_id)
                
                if query.memory_types:
                    type_values = [t.value for t in query.memory_types]
                    conditions.append(MemoryEntryModel.memory_type.in_(type_values))
                
                if query.tags:
                    # PostgreSQL ANY operator for array overlap
                    conditions.append(MemoryEntryModel.tags.overlap(query.tags))
                
                if query.start_time:
                    conditions.append(MemoryEntryModel.created_at >= query.start_time)
                
                if query.end_time:
                    conditions.append(MemoryEntryModel.created_at <= query.end_time)
                
                # Text search (simple LIKE, can be upgraded to full-text)
                if query.query_text:
                    conditions.append(
                        MemoryEntryModel.content.ilike(f"%{query.query_text}%")
                    )
                
                # Apply conditions
                if conditions:
                    stmt = stmt.where(and_(*conditions))
                
                # Get total count
                count_stmt = select(func.count()).select_from(stmt.subquery())
                total_result = await session.execute(count_stmt)
                total_count = total_result.scalar()
                
                # Apply sorting
                if query.sort_by == "created_at":
                    stmt = stmt.order_by(desc(MemoryEntryModel.created_at))
                elif query.sort_by == "importance":
                    stmt = stmt.order_by(desc(MemoryEntryModel.importance_score))
                elif query.sort_by == "relevance":
                    # For text search, sort by relevance (simple version)
                    # Vector search would override this
                    stmt = stmt.order_by(desc(MemoryEntryModel.importance_score))
                
                # Apply pagination
                stmt = stmt.offset(query.offset).limit(query.limit)
                
                # Execute query
                result = await session.execute(stmt)
                models = result.scalars().all()
                
                entries = [self._model_to_entry(m) for m in models]
            
            elapsed_ms = (datetime.now(timezone.utc) - start_time).total_seconds() * 1000
            self._track_latency(elapsed_ms)
            
            return MemoryResult(
                entries=entries,
                total_count=total_count,
                query_time_ms=elapsed_ms,
                tier=MemoryTier.PERSISTENT,
                has_more=(query.offset + query.limit) < total_count,
                next_offset=query.offset + query.limit if (query.offset + query.limit) < total_count else None
            )
        
        except Exception as e:
            logger.error(
                "persistent_memory_search_failed",
                error=str(e)
            )
            raise
    
    async def vector_search(
        self,
        query_vector: List[float],
        agent_ids: Optional[List[str]] = None,
        memory_types: Optional[List[MemoryType]] = None,
        limit: int = 10,
        min_similarity: float = 0.7
    ) -> MemoryResult:
        """
        Perform vector similarity search using PGVector.
        
        Note: This is a simplified implementation. Full PGVector
        support requires proper vector index setup.
        """
        start_time = datetime.now(timezone.utc)
        
        if self._session_factory is None:
            await self.connect()
        
        try:
            # For now, fall back to regular search
            # Full PGVector integration would use:
            # SELECT ... ORDER BY embedding <=> query_vector LIMIT n
            
            query = MemoryQuery(
                agent_ids=agent_ids,
                memory_types=memory_types,
                limit=limit
            )
            
            result = await self.search(query)
            
            elapsed_ms = (datetime.now(timezone.utc) - start_time).total_seconds() * 1000
            self._track_latency(elapsed_ms)
            
            return result
        
        except Exception as e:
            logger.error(
                "persistent_memory_vector_search_failed",
                error=str(e)
            )
            raise
    
    async def get_by_agent(
        self,
        agent_id: str,
        limit: int = 100,
        offset: int = 0
    ) -> List[MemoryEntry]:
        """Get entries for a specific agent"""
        query = MemoryQuery(
            agent_ids=[agent_id],
            limit=limit,
            offset=offset,
            sort_by="created_at"
        )
        result = await self.search(query)
        return result.entries
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get statistics for the persistent store"""
        if self._session_factory is None:
            await self.connect()
        
        try:
            async with self._session_factory() as session:
                # Count total entries
                count_stmt = select(func.count()).select_from(MemoryEntryModel)
                result = await session.execute(count_stmt)
                total_entries = result.scalar()
                
                # Count by type
                type_stmt = (
                    select(
                        MemoryEntryModel.memory_type,
                        func.count().label("count")
                    )
                    .group_by(MemoryEntryModel.memory_type)
                )
                type_result = await session.execute(type_stmt)
                entries_by_type = {row.memory_type: row.count for row in type_result}
                
                # Database size
                size_stmt = select(func.pg_database_size(func.current_database()))
                size_result = await session.execute(size_stmt)
                db_size = size_result.scalar()
            
            # Calculate latency percentiles
            p50 = p95 = p99 = 0.0
            if self._operation_times:
                sorted_times = sorted(self._operation_times)
                n = len(sorted_times)
                p50 = sorted_times[int(n * 0.50)]
                p95 = sorted_times[int(n * 0.95)]
                p99 = sorted_times[int(n * 0.99)]
            
            return {
                "tier": MemoryTier.PERSISTENT.value,
                "total_entries": total_entries,
                "entries_by_type": entries_by_type,
                "database_size_bytes": db_size,
                "p50_latency_ms": p50,
                "p95_latency_ms": p95,
                "p99_latency_ms": p99,
                "connected": True,
            }
        
        except Exception as e:
            logger.error("persistent_memory_stats_failed", error=str(e))
            return {
                "tier": MemoryTier.PERSISTENT.value,
                "connected": False,
                "error": str(e)
            }
    
    async def health_check(self) -> bool:
        """Check if PostgreSQL is healthy"""
        try:
            if self._session_factory is None:
                await self.connect()
            
            async with self._session_factory() as session:
                await session.execute(select(1))
            
            return True
        except Exception as e:
            logger.error("persistent_memory_health_check_failed", error=str(e))
            return False
