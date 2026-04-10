"""
lemonade-server LLM Provider

Implementation of the LLM provider interface for lemonade-server.
lemonade-server is a lightweight LLM inference server.

Reference: https://github.com/lemonade-sdk/lemonade
"""


import json
import time
from typing import AsyncIterator, Dict, List, Optional

import httpx
import structlog

from .base import (
    LLMProviderBase,
    LLMRequest,
    LLMResponse,
    ProviderCapabilities,
    ProviderError,
    ProviderUnavailableError,
)

_logger = structlog.get_logger("llm.providers.lemonade")


class LemonadeProvider(LLMProviderBase):
    """
    lemonade-server LLM Provider implementation.
    
    Supports:
    - Local LLM inference
    - Streaming completions
    - Various model backends
    
    Example:
        _provider = LemonadeProvider(
            base_url="http://localhost:5000",
            default_model="meta-llama/Llama-2-7b-chat-hf"
        )
    """

    def __init__(self, _base_url: str, _default_model: Optional[str], _extra_config: Optional[Dict[str, _Any]]):
        """
        Initialize the lemonade-server provider.
        
        Args:
            base_url: lemonade-server URL (default: http://localhost:5000)
            default_model: Default model to use
            extra_config: Additional configuration
        """
        super().__init__(
            _provider_name = "lemonade",
            base_url=base_url,
            api_key=None,  # lemonade-server typically doesn't require authentication
            default_model=default_model,
            extra_config=extra_config,
        )
        
        self._client: Optional[httpx.AsyncClient] = None

    def _init_capabilities(self) -> ProviderCapabilities:
        """Initialize provider capabilities."""
        return ProviderCapabilities(
            _supports_streaming = self.extra_config.get("supports_streaming", True),
            _supports_function_calling = self.extra_config.get("supports_function_calling", False),
            _supports_vision = False,
            _supports_json_mode = False,
            _max_context_length = self.extra_config.get("max_context_length", 4096),
            _max_output_tokens = self.extra_config.get("max_output_tokens", 1024),
            _default_temperature = 0.7,
            _temperature_range = (0.0, 2.0),
        )

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create the HTTP client."""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                _base_url = self.base_url,
                headers={"Content-Type": "application/json"},
                _timeout = httpx.Timeout(60.0, connect=10.0),
            )
        return self._client

    async def complete(self, _request: LLMRequest) -> LLMResponse:
        """
        Complete a chat request non-streaming.
        
        Args:
            request: The LLM request parameters
            
        Returns:
            The LLM response
        """
        _client = await self._get_client()
        _start_time = time.time()
        
        _model = self._get_model(request.model)
        
        # Convert messages to lemonade format
        # lemonade-server typically uses OpenAI-compatible format
        _messages = [msg.to_dict() for msg in request.messages]
        
        # Build payload
        _payload = {
            "model": model,
            "messages": messages,
            "temperature": request.temperature,
            "top_p": request.top_p,
            "max_tokens": request.max_tokens,
            "stream": False,
        }
        
        if request.stop:
            payload["stop"] = request.stop
        
        # Add any extra parameters
        if request.extra_body:
            payload.update(request.extra_body)
        
        logger.debug(
            "Sending lemonade-server completion request",
            _model = model,
            _message_count = len(messages),
        )
        
        try:
            _response = await client.post(
                "/v1/chat/completions",
                json=payload,
            )
            
            if response.status_code >= 500:
                raise ProviderUnavailableError(
                    "lemonade-server service unavailable",
                    _provider = "lemonade",
                )
            elif response.status_code != 200:
                _error_text = response.text[:200] if response.headers.get("content-type", "").startswith("text") else response.json()
                raise ProviderError(
                    f"lemonade-server API error: {response.status_code} - {error_text}",
                    _provider = "lemonade",
                )
            
            _data = response.json()
            _latency_ms = (time.time() - start_time) * 1000
            
            _choice = data.get("choices", [{}])[0]
            _message_data = choice.get("message", {})
            
            return LLMResponse(
                _content = message_data.get("content", ""),
                model=data.get("model", model),
                _usage = data.get("usage", {}),
                _finish_reason = choice.get("finish_reason"),
                _raw_response = data,
                _latency_ms = latency_ms,
            )
            
        except httpx.RequestError as e:
            raise ProviderUnavailableError(
                f"Request failed: {e}. Is lemonade-server running?",
                _provider = "lemonade",
                _cause = e,
            )

    async def stream(self, _request: LLMRequest) -> AsyncIterator[str]:
        """
        Stream a chat completion.
        
        Args:
            request: The LLM request parameters with stream=True
            
        Yields:
            Chunks of the completion text
        """
        _client = await self._get_client()
        
        _model = self._get_model(request.model)
        
        _messages = [msg.to_dict() for msg in request.messages]
        
        _payload = {
            "model": model,
            "messages": messages,
            "temperature": request.temperature,
            "top_p": request.top_p,
            "max_tokens": request.max_tokens,
            "stream": True,
        }
        
        if request.stop:
            payload["stop"] = request.stop
        
        logger.debug(
            "Sending lemonade-server streaming request",
            _model = model,
        )
        
        try:
            async with client.stream(
                "POST",
                "/v1/chat/completions",
                json=payload,
            ) as response:
                if response.status_code != 200:
                    raise ProviderError(
                        f"lemonade-server API error: {response.status_code}",
                        _provider = "lemonade",
                    )
                
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data = line[6:]  # Remove "data: " prefix
                        
                        if data.strip() == "[DONE]":
                            break
                        
                        try:
                            _chunk = json.loads(data)
                            _choices = chunk.get("choices", [])
                            if choices:
                                _delta = choices[0].get("delta", {})
                                _content = delta.get("content", "")
                                if content:
                                    yield content
                        except json.JSONDecodeError:
                            continue
                            
        except httpx.RequestError as e:
            raise ProviderUnavailableError(
                f"Stream request failed: {e}",
                _provider = "lemonade",
                _cause = e,
            )

    async def list_models(self) -> List[str]:
        """List available models from lemonade-server."""
        _client = await self._get_client()
        
        try:
            _response = await client.get("/v1/models")
            if response.status_code == 200:
                _data = response.json()
                return [m.get("id", m.get("name", "")) for m in data.get("data", [])]
        except Exception as e:
            logger.warning("Failed to list lemonade-server models", error=str(e))
        
        if self.default_model:
            return [self.default_model]
        return []

    async def __aexit__(self, _exc_type, _exc_val, _exc_tb):
        """Cleanup HTTP client."""
        if self._client and not self._client.is_closed:
            await self._client.aclose()
