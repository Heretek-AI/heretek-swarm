"""
OpenAI LLM Provider

Implementation of the LLM provider interface for OpenAI's API.
Supports GPT-4, GPT-4 Turbo, GPT-3.5 Turbo, and other OpenAI models.
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
    ProviderAuthenticationError,
    ProviderRateLimitError,
    ProviderUnavailableError,
    ToolCall,
)

_logger = structlog.get_logger("llm.providers.openai")


class OpenAIProvider(LLMProviderBase):
    """
    OpenAI LLM Provider implementation.
    
    Supports:
    - GPT-4, GPT-4 Turbo, GPT-4o
    - GPT-3.5 Turbo
    - Streaming completions
    - Function/tool calling
    - Vision (with GPT-4 Vision)
    - JSON mode
    
    Example:
        _provider = OpenAIProvider(
            api_key="sk-...",
            _default_model = "gpt-4o"
        )
        _response = await provider.complete(messages=[...])
    """

    def __init__(self, _api_key: str, _base_url: str, _default_model: Optional[str], _organization: Optional[str], _extra_config: Optional[Dict[str, _Any]]):
        """
        Initialize the OpenAI provider.
        
        Args:
            api_key: OpenAI API key
            base_url: Base URL (default: https://api.openai.com/v1)
            default_model: Default model to use
            organization: OpenAI organization ID (optional)
            extra_config: Additional configuration
        """
        if not api_key:
            raise ProviderAuthenticationError("OpenAI API key is required")
        
        super().__init__(
            _provider_name = "openai",
            base_url=base_url,
            api_key=api_key,
            _default_model = default_model or "gpt-4o",
            _extra_config = extra_config,
        )
        
        self.organization = organization
        self._client: Optional[httpx.AsyncClient] = None

    def _init_capabilities(self) -> ProviderCapabilities:
        """Initialize provider capabilities."""
        return ProviderCapabilities(
            _supports_streaming = True,
            _supports_function_calling = True,
            _supports_vision = True,
            _supports_json_mode = True,
            max_context_length=128000,  # GPT-4 Turbo
            _max_output_tokens = 4096,
            _default_temperature = 0.7,
            _temperature_range = (0.0, 2.0),
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
        
        _payload = request.to_dict()
        _model = self._get_model(request.model)
        payload["model"] = model
        
        logger.debug(
            "Sending OpenAI completion request",
            _model = model,
            stream=False,
            _message_count = len(request.messages),
        )
        
        try:
            _response = await client.post(
                "/chat/completions",
                json=payload,
            )
            
            if response.status_code == 401:
                raise ProviderAuthenticationError(
                    "Invalid OpenAI API key",
                    _provider = "openai",
                )
            elif response.status_code == 429:
                _retry_after = response.headers.get("Retry-After")
                raise ProviderRateLimitError(
                    "Rate limited by OpenAI",
                    _provider = "openai",
                    _retry_after = float(retry_after) if retry_after else None,
                )
            elif response.status_code >= 500:
                raise ProviderUnavailableError(
                    "OpenAI service unavailable",
                    _provider = "openai",
                )
            elif response.status_code != 200:
                raise ProviderError(
                    f"OpenAI API error: {response.status_code}",
                    _provider = "openai",
                )
            
            _data = response.json()
            _latency_ms = (time.time() - start_time) * 1000
            
            _choice = data["choices"][0]
            _message_data = choice.get("message", {})
            
            # Parse tool calls if present
            _tool_calls = []
            if "tool_calls" in message_data:
                for tc in message_data["tool_calls"]:
                    tool_calls.append(
                        ToolCall(
                            _id = tc["id"],
                            _name = tc["function"]["name"],
                            _arguments = json.loads(tc["function"]["arguments"]),
                        )
                    )
            
            return LLMResponse(
                _content = message_data.get("content", ""),
                model=data.get("model", model),
                _usage = data.get("usage", {}),
                _finish_reason = choice.get("finish_reason"),
                _tool_calls = tool_calls,
                _raw_response = data,
                _latency_ms = latency_ms,
            )
            
        except httpx.RequestError as e:
            raise ProviderUnavailableError(
                f"Request failed: {e}",
                _provider = "openai",
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
        
        _payload = request.to_dict()
        payload["stream"] = True
        _model = self._get_model(request.model)
        payload["model"] = model
        
        logger.debug(
            "Sending OpenAI streaming request",
            _model = model,
            stream=True,
        )
        
        try:
            async with client.stream(
                "POST",
                "/chat/completions",
                json=payload,
            ) as response:
                if response.status_code == 401:
                    raise ProviderAuthenticationError(
                        "Invalid OpenAI API key",
                        _provider = "openai",
                    )
                elif response.status_code == 429:
                    raise ProviderRateLimitError(
                        "Rate limited by OpenAI",
                        _provider = "openai",
                    )
                elif response.status_code != 200:
                    raise ProviderError(
                        f"OpenAI API error: {response.status_code}",
                        _provider = "openai",
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
                _provider = "openai",
                _cause = e,
            )

    async def list_models(self) -> List[str]:
        """List available OpenAI models."""
        _client = await self._get_client()
        
        try:
            _response = await client.get("/models")
            if response.status_code == 200:
                _data = response.json()
                return [m["id"] for m in data.get("data", [])]
        except Exception as e:
            logger.warning("Failed to list OpenAI models", error=str(e))
        
        # Return common models as fallback
        return [
            "gpt-4o",
            "gpt-4-turbo",
            "gpt-4",
            "gpt-3.5-turbo",
        ]

    async def __aexit__(self, _exc_type, _exc_val, _exc_tb):
        """Cleanup HTTP client."""
        if self._client and not self._client.is_closed:
            await self._client.aclose()
