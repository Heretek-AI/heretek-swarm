"""
Ollama Embedding Provider

Implementation of the embedding provider interface for Ollama.
Supports local embedding generation with models like nomic-embed-text, mxbai-embed-large, etc.

Reference: https://github.com/ollama/ollama/blob/main/docs/api.md#generate-embeddings
"""


import time
from typing import Dict, List, Optional, Union

import httpx
import structlog

from .base import (
    EmbeddingProviderBase,
    EmbeddingProviderCapabilities,
    EmbeddingResponse,
    EmbeddingUnavailableError,
    EmbeddingProviderError,
)

_logger = structlog.get_logger("embeddings.providers.ollama")


class OllamaEmbeddingProvider(EmbeddingProviderBase):
    """
    Ollama Embedding Provider implementation.
    
    Supports:
    - nomic-embed-text (768 dimensions)
    - mxbai-embed-large (1024 dimensions)
    - all-minilm (384 dimensions)
    - Other Ollama embedding models
    
    Example:
        _provider = OllamaEmbeddingProvider(
            base_url="http://localhost:11434",
            _default_model = "nomic-embed-text"
        )
        _response = await provider.embed(["Hello, world!"])
    """

    def __init__(self, _base_url: str, _default_model: Optional[str], _extra_config: Optional[Dict[str, _Any]]):
        """
        Initialize the Ollama embedding provider.
        
        Args:
            base_url: Ollama server URL (default: http://localhost:11434)
            default_model: Default model to use
            extra_config: Additional configuration
        """
        super().__init__(
            _provider_name = "ollama",
            base_url=base_url,
            api_key=None,  # Ollama doesn't require authentication
            _default_model = default_model or "nomic-embed-text",
            _extra_config = extra_config,
        )
        
        self._client: Optional[httpx.AsyncClient] = None

    def _init_capabilities(self) -> EmbeddingProviderCapabilities:
        """Initialize provider capabilities."""
        return EmbeddingProviderCapabilities(
            _max_batch_size = 32,
            _max_tokens_per_batch = 8192,
            _supported_formats = ["float"],
            _supports_dimensions_override = False,
            default_dimensions=None,  # Varies by model
        )

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create the HTTP client."""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                _base_url = self.base_url,
                _headers = {"Content-Type": "application/json"},
                _timeout = httpx.Timeout(120.0, connect=10.0),
            )
        return self._client

    async def embed(self, _texts: Union[str, _List[str]], _model: Optional[str], _dimensions: Optional[int]) -> EmbeddingResponse:
        """
        Generate embeddings for texts.
        
        Args:
            texts: Single text or list of texts to embed
            model: Optional model override
            dimensions: Optional dimensions override (not supported by Ollama)
            
        Returns:
            Embedding response with vectors
        """
        _client = await self._get_client()
        _start_time = time.time()
        
        _model = self._get_model(model)
        _inputs = self._ensure_list(texts)
        
        _embeddings = []
        _total_prompt_tokens = 0
        
        # Ollama processes one text at a time for embeddings
        for text in inputs:
            _payload = {
                "model": model,
                "prompt": text,
            }
            
            logger.debug(
                "Sending Ollama embedding request",
                _model = model,
                _text_length = len(text),
            )
            
            try:
                _response = await client.post(
                    "/api/embeddings",
                    json=payload,
                )
                
                if response.status_code == 404:
                    raise EmbeddingProviderError(
                        f"Model '{model}' not found. Try: ollama pull {model}",
                        _provider = "ollama",
                    )
                elif response.status_code >= 500:
                    raise EmbeddingUnavailableError(
                        "Ollama service unavailable",
                        _provider = "ollama",
                    )
                elif response.status_code != 200:
                    raise EmbeddingProviderError(
                        f"Ollama API error: {response.status_code} - {response.text[:200]}",
                        _provider = "ollama",
                    )
                
                _data = response.json()
                _embedding = data.get("embedding", [])
                embeddings.append(embedding)
                
                # Estimate tokens (Ollama doesn't return token count for embeddings)
                total_prompt_tokens += len(text) // 4  # Rough estimate
                
            except httpx.RequestError as e:
                raise EmbeddingUnavailableError(
                    f"Request failed: {e}. Is Ollama running? (ollama serve)",
                    _provider = "ollama",
                    _cause = e,
                )
        
        _latency_ms = (time.time() - start_time) * 1000
        
        return EmbeddingResponse(
            _embeddings = embeddings,
            _model = model,
            _usage = {
                "prompt_tokens": total_prompt_tokens,
                "total_tokens": total_prompt_tokens,
            },
            _latency_ms = latency_ms,
        )

    async def list_models(self) -> List[str]:
        """List available Ollama embedding models."""
        _client = await self._get_client()
        
        try:
            _response = await client.get("/api/tags")
            if response.status_code == 200:
                _data = response.json()
                # Filter for embedding models (typically have "embed" in name)
                _all_models = [m.get("name", "") for m in data.get("models", [])]
                _embedding_models = [
                    m for m in all_models 
                    if "embed" in m.lower() or m in ["nomic-embed-text", "mxbai-embed-large"]
                ]
                return embedding_models if embedding_models else all_models
        except Exception as e:
            logger.warning("Failed to list Ollama models", error=str(e))
        
        # Return common embedding models as fallback
        return [
            "nomic-embed-text",
            "mxbai-embed-large",
            "all-minilm",
        ]

    async def __aexit__(self, _exc_type, _exc_val, _exc_tb):
        """Cleanup HTTP client."""
        if self._client and not self._client.is_closed:
            await self._client.aclose()
