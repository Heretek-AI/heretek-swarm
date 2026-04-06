"""
Embedding Service - Vector Embedding Generation for RAG.

Handles embedding generation using multiple providers.
Pattern stolen from elizaOS embedding service and mem0.

Supports:
- OpenAI embeddings (text-embedding-3-small/large)
- Local embeddings via sentence-transformers
- Configurable batch processing
- Caching for performance
"""

import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Union
import asyncio
import hashlib

import structlog

logger = structlog.get_logger(__name__)


class EmbeddingProvider(Enum):
    """Supported embedding providers."""
    OPENAI = "openai"
    SENTENCE_TRANSFORMERS = "sentence_transformers"
    COHERE = "cohere"
    VOYAGE = "voyage"


@dataclass
class EmbeddingConfig:
    """Configuration for embedding service."""
    
    provider: EmbeddingProvider = EmbeddingProvider.OPENAI
    
    # OpenAI settings
    openai_model: str = "text-embedding-3-small"
    openai_api_key: Optional[str] = None
    openai_dimensions: int = 1536  # 1536 for small, 3072 for large
    
    # Sentence Transformers settings
    st_model: str = "all-MiniLM-L6-v2"
    st_device: str = "cpu"
    
    # Cohere settings
    cohere_model: str = "embed-english-v3.0"
    cohere_api_key: Optional[str] = None
    
    # Voyage settings
    voyage_model: str = "voyage-2"
    voyage_api_key: Optional[str] = None
    
    # Batch settings
    batch_size: int = 100
    max_retries: int = 3
    retry_delay: float = 1.0
    
    # Cache settings
    enable_cache: bool = True
    cache_ttl_seconds: int = 86400  # 24 hours


@dataclass
class EmbeddingResult:
    """Result of embedding generation."""
    
    embedding: List[float]
    text_hash: str
    model: str
    dimensions: int
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "embedding": self.embedding,
            "text_hash": self.text_hash,
            "model": self.model,
            "dimensions": self.dimensions,
            "created_at": self.created_at,
        }


class EmbeddingCache:
    """Simple in-memory cache for embeddings."""
    
    def __init__(self, ttl_seconds: int = 86400):
        self._cache: Dict[str, EmbeddingResult] = {}
        self._ttl = ttl_seconds
    
    def _hash(self, text: str, model: str) -> str:
        """Generate cache key."""
        content = f"{model}:{text}"
        return hashlib.sha256(content.encode()).hexdigest()
    
    def get(self, text: str, model: str) -> Optional[EmbeddingResult]:
        """Get cached embedding if not expired."""
        key = self._hash(text, model)
        if key in self._cache:
            result = self._cache[key]
            # Check TTL
            created = datetime.fromisoformat(result.created_at)
            age = (datetime.now(timezone.utc) - created).total_seconds()
            if age < self._ttl:
                return result
            else:
                del self._cache[key]
        return None
    
    def set(self, text: str, model: str, result: EmbeddingResult) -> None:
        """Cache an embedding."""
        key = self._hash(text, model)
        self._cache[key] = result
    
    def clear(self) -> None:
        """Clear cache."""
        self._cache.clear()


class EmbeddingService:
    """
    Embedding generation service.
    
    Provides unified interface for multiple embedding providers:
    - OpenAI text-embedding-3-small/large
    - Sentence Transformers (local)
    - Cohere
    - Voyage AI
    
    Pattern stolen from elizaOS embedding service.
    """
    
    def __init__(self, config: Optional[EmbeddingConfig] = None):
        self.config = config or EmbeddingConfig()
        self._cache = EmbeddingCache(self.config.cache_ttl_seconds) if self.config.enable_cache else None
        self._client = None
        self._initialized = False
    
    async def initialize(self) -> None:
        """Initialize the embedding service."""
        if self.config.provider == EmbeddingProvider.OPENAI:
            await self._init_openai()
        elif self.config.provider == EmbeddingProvider.SENTENCE_TRANSFORMERS:
            await self._init_sentence_transformers()
        elif self.config.provider == EmbeddingProvider.COHERE:
            await self._init_cohere()
        elif self.config.provider == EmbeddingProvider.VOYAGE:
            await self._init_voyage()
        
        self._initialized = True
        logger.info(
            "embedding_service_initialized",
            provider=self.config.provider.value,
        )
    
    async def _init_openai(self) -> None:
        """Initialize OpenAI client."""
        try:
            from openai import AsyncOpenAI
            
            api_key = self.config.openai_api_key or os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise ValueError("OpenAI API key required")
            
            self._client = AsyncOpenAI(api_key=api_key)
            logger.debug("openai_client_initialized")
        except ImportError:
            raise ImportError("Install openai: pip install openai")
    
    async def _init_sentence_transformers(self) -> None:
        """Initialize Sentence Transformers."""
        try:
            from sentence_transformers import SentenceTransformer
            
            self._client = SentenceTransformer(
                self.config.st_model,
                device=self.config.st_device,
            )
            logger.debug("sentence_transformers_initialized", model=self.config.st_model)
        except ImportError:
            raise ImportError("Install sentence-transformers: pip install sentence-transformers")
    
    async def _init_cohere(self) -> None:
        """Initialize Cohere client."""
        try:
            import cohere
            
            api_key = self.config.cohere_api_key or os.getenv("COHERE_API_KEY")
            if not api_key:
                raise ValueError("Cohere API key required")
            
            self._client = cohere.AsyncClient(api_key)
            logger.debug("cohere_client_initialized")
        except ImportError:
            raise ImportError("Install cohere: pip install cohere")
    
    async def _init_voyage(self) -> None:
        """Initialize Voyage client."""
        try:
            import voyageai
            
            api_key = self.config.voyage_api_key or os.getenv("VOYAGE_API_KEY")
            if not api_key:
                raise ValueError("Voyage API key required")
            
            self._client = voyageai.AsyncClient(api_key)
            logger.debug("voyage_client_initialized")
        except ImportError:
            raise ImportError("Install voyageai: pip install voyageai")
    
    async def embed(self, text: str) -> EmbeddingResult:
        """
        Generate embedding for a single text.
        
        Args:
            text: Text to embed
            
        Returns:
            EmbeddingResult with vector
        """
        if not self._initialized:
            await self.initialize()
        
        # Check cache
        if self._cache:
            cached = self._cache.get(text, self._get_model_name())
            if cached:
                return cached
        
        # Generate embedding
        if self.config.provider == EmbeddingProvider.OPENAI:
            result = await self._embed_openai([text])
            result = result[0]
        elif self.config.provider == EmbeddingProvider.SENTENCE_TRANSFORMERS:
            result = await self._embed_st([text])
            result = result[0]
        elif self.config.provider == EmbeddingProvider.COHERE:
            result = await self._embed_cohere([text])
            result = result[0]
        elif self.config.provider == EmbeddingProvider.VOYAGE:
            result = await self._embed_voyage([text])
            result = result[0]
        else:
            raise ValueError(f"Unknown provider: {self.config.provider}")
        
        # Cache result
        if self._cache:
            self._cache.set(text, self._get_model_name(), result)
        
        return result
    
    async def embed_batch(self, texts: List[str]) -> List[EmbeddingResult]:
        """
        Generate embeddings for multiple texts.
        
        Args:
            texts: List of texts to embed
            
        Returns:
            List of EmbeddingResults
        """
        if not self._initialized:
            await self.initialize()
        
        if not texts:
            return []
        
        # Check cache for all texts
        results = [None] * len(texts)
        uncached_indices = []
        uncached_texts = []
        
        if self._cache:
            model = self._get_model_name()
            for i, text in enumerate(texts):
                cached = self._cache.get(text, model)
                if cached:
                    results[i] = cached
                else:
                    uncached_indices.append(i)
                    uncached_texts.append(text)
        else:
            uncached_indices = list(range(len(texts)))
            uncached_texts = texts
        
        # Process uncached texts in batches
        if uncached_texts:
            for i in range(0, len(uncached_texts), self.config.batch_size):
                batch = uncached_texts[i:i + self.config.batch_size]
                batch_indices = uncached_indices[i:i + self.config.batch_size]
                
                if self.config.provider == EmbeddingProvider.OPENAI:
                    batch_results = await self._embed_openai(batch)
                elif self.config.provider == EmbeddingProvider.SENTENCE_TRANSFORMERS:
                    batch_results = await self._embed_st(batch)
                elif self.config.provider == EmbeddingProvider.COHERE:
                    batch_results = await self._embed_cohere(batch)
                elif self.config.provider == EmbeddingProvider.VOYAGE:
                    batch_results = await self._embed_voyage(batch)
                else:
                    raise ValueError(f"Unknown provider: {self.config.provider}")
                
                # Store results
                for j, result in enumerate(batch_results):
                    idx = batch_indices[j]
                    results[idx] = result
                    
                    # Cache
                    if self._cache:
                        self._cache.set(texts[idx], self._get_model_name(), result)
        
        return results
    
    async def _embed_openai(self, texts: List[str]) -> List[EmbeddingResult]:
        """Generate embeddings using OpenAI."""
        model = self.config.openai_model
        results = []
        
        for attempt in range(self.config.max_retries):
            try:
                response = await self._client.embeddings.create(
                    input=texts,
                    model=model,
                    dimensions=self.config.openai_dimensions,
                )
                
                for i, item in enumerate(response.data):
                    results.append(EmbeddingResult(
                        embedding=item.embedding,
                        text_hash=hashlib.sha256(texts[i].encode()).hexdigest(),
                        model=model,
                        dimensions=len(item.embedding),
                    ))
                
                return results
            except Exception as e:
                if attempt < self.config.max_retries - 1:
                    await asyncio.sleep(self.config.retry_delay * (attempt + 1))
                else:
                    raise
    
    async def _embed_st(self, texts: List[str]) -> List[EmbeddingResult]:
        """Generate embeddings using Sentence Transformers."""
        model = self.config.st_model
        
        # Run in thread pool since ST is synchronous
        loop = asyncio.get_event_loop()
        embeddings = await loop.run_in_executor(
            None,
            lambda: self._client.encode(texts, convert_to_numpy=True),
        )
        
        results = []
        for i, embedding in enumerate(embeddings):
            results.append(EmbeddingResult(
                embedding=embedding.tolist(),
                text_hash=hashlib.sha256(texts[i].encode()).hexdigest(),
                model=model,
                dimensions=len(embedding),
            ))
        
        return results
    
    async def _embed_cohere(self, texts: List[str]) -> List[EmbeddingResult]:
        """Generate embeddings using Cohere."""
        model = self.config.cohere_model
        
        response = await self._client.embed(
            texts=texts,
            model=model,
            input_type="search_document",
        )
        
        results = []
        for i, embedding in enumerate(response.embeddings):
            results.append(EmbeddingResult(
                embedding=embedding,
                text_hash=hashlib.sha256(texts[i].encode()).hexdigest(),
                model=model,
                dimensions=len(embedding),
            ))
        
        return results
    
    async def _embed_voyage(self, texts: List[str]) -> List[EmbeddingResult]:
        """Generate embeddings using Voyage AI."""
        model = self.config.voyage_model
        
        response = await self._client.embed(
            texts=texts,
            model=model,
            input_type="document",
        )
        
        results = []
        for i, embedding in enumerate(response.embeddings):
            results.append(EmbeddingResult(
                embedding=embedding,
                text_hash=hashlib.sha256(texts[i].encode()).hexdigest(),
                model=model,
                dimensions=len(embedding),
            ))
        
        return results
    
    def _get_model_name(self) -> str:
        """Get current model name for caching."""
        if self.config.provider == EmbeddingProvider.OPENAI:
            return self.config.openai_model
        elif self.config.provider == EmbeddingProvider.SENTENCE_TRANSFORMERS:
            return self.config.st_model
        elif self.config.provider == EmbeddingProvider.COHERE:
            return self.config.cohere_model
        elif self.config.provider == EmbeddingProvider.VOYAGE:
            return self.config.voyage_model
        return "unknown"
    
    def get_dimensions(self) -> int:
        """Get embedding dimensions for current configuration."""
        if self.config.provider == EmbeddingProvider.OPENAI:
            return self.config.openai_dimensions
        elif self.config.provider == EmbeddingProvider.SENTENCE_TRANSFORMERS:
            # Common ST model dimensions
            dims = {
                "all-MiniLM-L6-v2": 384,
                "all-mpnet-base-v2": 768,
                "multi-qa-mpnet-base-dot-v1": 768,
            }
            return dims.get(self.config.st_model, 768)
        elif self.config.provider == EmbeddingProvider.COHERE:
            return 1024
        elif self.config.provider == EmbeddingProvider.VOYAGE:
            return 1024
        return 768
    
    async def shutdown(self) -> None:
        """Shutdown the service."""
        if self._client and hasattr(self._client, "close"):
            await self._client.close()
        
        if self._cache:
            self._cache.clear()
        
        self._initialized = False
