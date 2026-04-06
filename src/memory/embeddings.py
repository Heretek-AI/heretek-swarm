"""
Embedding service for generating vector embeddings from text.

Integrates with LiteLLM for flexible model selection and
provides caching to optimize performance.
"""

import asyncio
import hashlib
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Tuple

import aiohttp
import structlog
from pydantic import BaseModel, Field

from .base import EmbeddingVector

logger = structlog.get_logger()


class EmbeddingConfig(BaseModel):
    """Configuration for embedding service"""
    
    # LiteLLM configuration
    litellm_base_url: str = Field(default="http://localhost:4000")
    api_key: Optional[str] = Field(None)
    
    # Model settings
    default_model: str = Field(default="text-embedding-3-small")
    dimensions: int = Field(default=1536)
    
    # Performance
    batch_size: int = Field(default=32, description="Max items per batch")
    max_concurrent_batches: int = Field(default=5)
    timeout_seconds: float = Field(default=30.0)
    
    # Caching
    cache_ttl_seconds: int = Field(default=3600 * 24, description="24 hour TTL")
    cache_max_size: int = Field(default=10000)
    
    # Retry
    max_retries: int = Field(default=3)
    retry_delay_seconds: float = Field(default=0.5)


class EmbeddingCache:
    """Simple in-memory LRU cache for embeddings"""
    
    def __init__(self, max_size: int = 10000, ttl_seconds: int = 86400):
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
        self._cache: Dict[str, Tuple[EmbeddingVector, datetime]] = {}
        self._access_order: List[str] = []
    
    def _hash_text(self, text: str, model: str) -> str:
        """Generate cache key"""
        content = f"{model}:{text}"
        return hashlib.sha256(content.encode()).hexdigest()
    
    def get(self, text: str, model: str) -> Optional[EmbeddingVector]:
        """Get cached embedding if exists and not expired"""
        key = self._hash_text(text, model)
        
        if key not in self._cache:
            return None
        
        embedding, created_at = self._cache[key]
        
        # Check TTL
        if datetime.now(timezone.utc) - created_at > timedelta(seconds=self.ttl_seconds):
            del self._cache[key]
            self._access_order.remove(key)
            return None
        
        # Update access order
        self._access_order.remove(key)
        self._access_order.append(key)
        
        return embedding
    
    def set(self, text: str, model: str, embedding: EmbeddingVector) -> None:
        """Cache an embedding"""
        key = self._hash_text(text, model)
        
        # Evict oldest if at capacity
        while len(self._cache) >= self.max_size and self._access_order:
            oldest_key = self._access_order.pop(0)
            del self._cache[oldest_key]
        
        self._cache[key] = (embedding, datetime.now(timezone.utc))
        self._access_order.append(key)
    
    def clear(self) -> None:
        """Clear the cache"""
        self._cache.clear()
        self._access_order.clear()
    
    def size(self) -> int:
        """Get current cache size"""
        return len(self._cache)


class EmbeddingService:
    """
    Service for generating text embeddings via LiteLLM.
    
    Features:
    - Batch embedding support
    - In-memory caching
    - Automatic retries
    - Performance monitoring
    """
    
    def __init__(self, config: Optional[EmbeddingConfig] = None):
        self.config = config or EmbeddingConfig()
        self.cache = EmbeddingCache(
            max_size=self.config.cache_max_size,
            ttl_seconds=self.config.cache_ttl_seconds
        )
        self._session: Optional[aiohttp.ClientSession] = None
        self._semaphore = asyncio.Semaphore(self.config.max_concurrent_batches)
        
        # Metrics
        self._total_requests = 0
        self._cache_hits = 0
        self._total_time_ms = 0.0
        self._errors = 0
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create HTTP session"""
        if self._session is None or self._session.closed:
            timeout = aiohttp.ClientTimeout(total=self.config.timeout_seconds)
            headers = {"Content-Type": "application/json"}
            
            if self.config.api_key:
                headers["Authorization"] = f"Bearer {self.config.api_key}"
            
            self._session = aiohttp.ClientSession(
                base_url=self.config.litellm_base_url,
                headers=headers,
                timeout=timeout
            )
        
        return self._session
    
    async def close(self) -> None:
        """Close the HTTP session"""
        if self._session and not self._session.closed:
            await self._session.close()
    
    async def embed_single(
        self,
        text: str,
        model: Optional[str] = None
    ) -> EmbeddingVector:
        """Generate embedding for a single text"""
        results = await self.embed_batch([text], model)
        return results[0]
    
    async def embed_batch(
        self,
        texts: List[str],
        model: Optional[str] = None
    ) -> List[EmbeddingVector]:
        """
        Generate embeddings for multiple texts.
        
        Uses batching and caching for optimal performance.
        """
        if not texts:
            return []
        
        model = model or self.config.default_model
        results: List[Optional[EmbeddingVector]] = [None] * len(texts)
        to_fetch: List[Tuple[int, str]] = []
        
        # Check cache first
        for i, text in enumerate(texts):
            cached = self.cache.get(text, model)
            if cached is not None:
                results[i] = cached
                self._cache_hits += 1
            else:
                to_fetch.append((i, text))
        
        # Fetch uncached embeddings in batches
        if to_fetch:
            # Split into API batches
            batches = [
                to_fetch[i:i + self.config.batch_size]
                for i in range(0, len(to_fetch), self.config.batch_size)
            ]
            
            # Process batches concurrently (with semaphore)
            tasks = [
                self._fetch_batch(batch, model)
                for batch in batches
            ]
            
            batch_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Collect results
            for batch_idx, batch_result in enumerate(batch_results):
                batch = batches[batch_idx]
                
                if isinstance(batch_result, Exception):
                    logger.error(
                        "embedding_batch_failed",
                        batch_size=len(batch),
                        error=str(batch_result)
                    )
                    self._errors += 1
                    # Fall back to individual requests
                    for idx, text in batch:
                        try:
                            embedding = await self._fetch_single(text, model)
                            results[idx] = embedding
                            self.cache.set(text, model, embedding)
                        except Exception as e:
                            logger.error(
                                "embedding_single_failed",
                                text_preview=text[:50],
                                error=str(e)
                            )
                            self._errors += 1
                else:
                    for (idx, text), embedding in zip(batch, batch_result):
                        results[idx] = embedding
                        self.cache.set(text, model, embedding)
        
        self._total_requests += len(texts)
        
        # Filter out any remaining Nones
        return [r for r in results if r is not None]
    
    async def _fetch_batch(
        self,
        batch: List[Tuple[int, str]],
        model: str
    ) -> List[EmbeddingVector]:
        """Fetch embeddings for a batch from LiteLLM"""
        async with self._semaphore:
            start_time = datetime.now(timezone.utc)
            
            texts = [text for _, text in batch]
            
            for attempt in range(self.config.max_retries):
                try:
                    session = await self._get_session()
                    
                    payload = {
                        "model": model,
                        "input": texts,
                        "dimensions": self.config.dimensions
                    }
                    
                    async with session.post("/v1/embeddings", json=payload) as response:
                        response.raise_for_status()
                        data = await response.json()
                    
                    # Parse response
                    embeddings = []
                    for item in data["data"]:
                        vector = EmbeddingVector(
                            vector=item["embedding"],
                            dimensions=len(item["embedding"]),
                            model=model,
                            created_at=datetime.now(timezone.utc)
                        )
                        embeddings.append(vector)
                    
                    # Track timing
                    elapsed_ms = (datetime.now(timezone.utc) - start_time).total_seconds() * 1000
                    self._total_time_ms += elapsed_ms
                    
                    logger.debug(
                        "embedding_batch_fetched",
                        batch_size=len(batch),
                        elapsed_ms=elapsed_ms
                    )
                    
                    return embeddings
                
                except aiohttp.ClientError as e:
                    if attempt < self.config.max_retries - 1:
                        await asyncio.sleep(
                            self.config.retry_delay_seconds * (attempt + 1)
                        )
                    else:
                        raise
            
            raise RuntimeError("Failed to fetch embeddings after all retries")
    
    async def _fetch_single(self, text: str, model: str) -> EmbeddingVector:
        """Fetch embedding for a single text (fallback)"""
        results = await self._fetch_batch([(0, text)], model)
        return results[0]
    
    def get_stats(self) -> Dict[str, any]:
        """Get embedding service statistics"""
        cache_hit_rate = (
            self._cache_hits / self._total_requests if self._total_requests > 0 else 0
        )
        avg_latency_ms = (
            self._total_time_ms / self._total_requests if self._total_requests > 0 else 0
        )
        
        return {
            "total_requests": self._total_requests,
            "cache_hits": self._cache_hits,
            "cache_hit_rate": cache_hit_rate,
            "cache_size": self.cache.size(),
            "avg_latency_ms": avg_latency_ms,
            "total_errors": self._errors,
        }
    
    async def health_check(self) -> bool:
        """Check if the embedding service is healthy"""
        try:
            # Try a simple embedding
            await self.embed_single("health check", model=self.config.default_model)
            return True
        except Exception as e:
            logger.error("embedding_health_check_failed", error=str(e))
            return False
