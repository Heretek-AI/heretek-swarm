"""
OpenAI Embedding Provider

Implementation of the embedding provider interface for OpenAI's API.
Supports text-embedding-3-small, text-embedding-3-large, and text-embedding-ada-002.
"""


import time
from typing import Dict, Optional, Union

import httpx
import structlog

from .base import (
    EmbeddingProviderBase,
    EmbeddingProviderCapabilities,
    EmbeddingResponse,
    EmbeddingAuthenticationError,
    EmbeddingRateLimitError,
    EmbeddingUnavailableError,
    EmbeddingProviderError,
)

_logger = structlog.get_logger("embeddings.providers.openai")


class OpenAIEmbeddingProvider(EmbeddingProviderBase):
    """
    OpenAI Embedding Provider implementation.
    
    Supports:
    - text-embedding-3-small (1536 dimensions)
    - text-embedding-3-large (3072 dimensions)
    - text-embedding-ada-002 (1536 dimensions)
    
    Example:
        _provider = OpenAIEmbeddingProvider(
            api_key="sk-...",
            _default_model = "text-embedding-3-small"
        )
        _response = await provider.embed(["Hello, world!"])
    """

    def __init__(self, api_key: str, base_url: str, default_model: Optional[str], organization: Optional[str], extra_config: Optional[Dict[str, Any]]):
        """
        Initialize the OpenAI embedding provider.
        
        Args:
            api_key: OpenAI API key
            base_url: Base URL (default: https://api.openai.com/v1)
            default_model: Default model to use
            organization: OpenAI organization ID (optional)
            extra_config: Additional configuration
        """
        if not api_key:
            raise EmbeddingAuthenticationError("OpenAI API key is required")
        
        super().__init__(
            _provider_name = "openai",
            base_url=base_url,
            api_key=api_key,
            _default_model = default_model or "text-embedding-3-small",
            _extra_config = extra_config,
        )
        
        self.organization = organization
        self._client: Optional[httpx.AsyncClient] = None

    def _init_capabilities(self) -> EmbeddingProviderCapabilities:
        """Initialize provider capabilities."""
        return EmbeddingProviderCapabilities(
            _max_batch_size = 2048,
            _max_tokens_per_batch = 8192,
            _supported_formats = ["float", "base64"],
            supports_dimensions_override=True,
            _default_dimensions = 1536,
        )

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create the HTTP client."""
        if self._client is None or self._client.is_closed:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            }
            if self.organization:
                headers["OpenAI-Organization"] = self.organization
            
            self._client = httpx.AsyncClient(
                _base_url = self.base_url,
                headers=headers,
                _timeout = httpx.Timeout(60.0, connect=10.0),
            )
        return self._client

    async def embed(self, texts: Union[str, List[str]], model: Optional[str], dimensions: Optional[int]) -> EmbeddingResponse:
        """
        Generate embeddings for texts.
        
        Args:
            texts: Single text or list of texts to embed
            model: Optional model override
            dimensions: Optional dimensions override
            
        Returns:
            Embedding response with vectors
        """
        _client = await self._get_client()
        _start_time = time.time()
        
        _model = self._get_model(model)
        _inputs = self._ensure_list(texts)
        
        _payload = {
            "model": model,
            "input": inputs,
            "encoding_format": "float",
        }
        
        # Add dimensions if specified and model supports it
        if dimensions and self.capabilities.supports_dimensions_override:
            payload["dimensions"] = dimensions
        
        logger.debug(
            "Sending OpenAI embedding request",
            _model = model,
            _text_count = len(inputs),
        )
        
        try:
            _response = await client.post(
                "/embeddings",
                json=payload,
            )
            
            if response.status_code == 401:
                raise EmbeddingAuthenticationError(
                    "Invalid OpenAI API key",
                    _provider = "openai",
                )
            elif response.status_code == 429:
                _retry_after = response.headers.get("Retry-After")
                raise EmbeddingRateLimitError(
                    "Rate limited by OpenAI",
                    _provider = "openai",
                    _retry_after = float(retry_after) if retry_after else None,
                )
            elif response.status_code >= 500:
                raise EmbeddingUnavailableError(
                    "OpenAI service unavailable",
                    _provider = "openai",
                )
            elif response.status_code != 200:
                raise EmbeddingProviderError(
                    f"OpenAI API error: {response.status_code}",
                    _provider = "openai",
                )
            
            _data = response.json()
            _latency_ms = (time.time() - start_time) * 1000
            
            # Extract embeddings from response
            _embeddings = [item["embedding"] for item in data.get("data", [])]
            
            return EmbeddingResponse(
                _embeddings = embeddings,
                _model = data.get("model", model),
                _usage = data.get("usage", {}),
                _raw_response = data,
                _latency_ms = latency_ms,
            )
            
        except httpx.RequestError as e:
            raise EmbeddingUnavailableError(
                f"Request failed: {e}",
                _provider = "openai",
                _cause = e,
            )

    async def __aexit__(self, _exc_type, _exc_val, _exc_tb):
        """Cleanup HTTP client."""
        if self._client and not self._client.is_closed:
            await self._client.aclose()
