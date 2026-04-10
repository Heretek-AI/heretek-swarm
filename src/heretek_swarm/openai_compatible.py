"""
OpenAI-Compatible LLM Provider

Generic provider for any API that follows the OpenAI chat completion format.
Useful for local LLM servers, alternative providers, and custom deployments.

Supported providers include:
- vLLM
- LocalAI
- FastChat
- Text Generation Inference (TGI)
- Custom OpenAI-compatible APIs
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
    ProviderUnavailableError,
    ToolCall,
)

_logger = structlog.get_logger("llm.providers.openai_compatible")


class OpenAICompatibleProvider(LLMProviderBase):
    """
    Generic OpenAI-compatible provider.
    
    Works with any API that implements the OpenAI chat completion format.
    Commonly used with:
    - vLLM inference server
    - LocalAI
    - FastChat
    - Hugging Face TGI
    - Custom deployments
    
    Example:
        _provider = OpenAICompatibleProvider(
            base_url="http://localhost:8000/v1",
            api_key="not-needed",  # Some servers don't require auth
            _default_model = "meta-llama/Llama-2-7b"
        )
    """

    def __init__(self, base_url: str, api_key: Optional[str], default_model: Optional[str], extra_config: Optional[Dict[str, Any]]):
        """
        Initialize the OpenAI-compatible provider.
        
        Args:
            base_url: Base URL of the compatible API
            api_key: API key (optional for some servers)
            default_model: Default model to use
            extra_config: Additional configuration
        """
        super().__init__(
            _provider_name = "openai_compatible",
            base_url=base_url,
            api_key=api_key,
            _default_model = default_model,
            _extra_config = extra_config,
        )
        
        self._client: Optional[httpx.AsyncClient] = None
        
        # Extract capabilities from extra_config
        self._custom_capabilities = extra_config or {}

    def _init_capabilities(self) -> ProviderCapabilities:
        """Initialize provider capabilities from config."""
        return ProviderCapabilities(
            _supports_streaming = self._custom_capabilities.get("supports_streaming", True),
            _supports_function_calling = self._custom_capabilities.get("supports_function_calling", False),
            _supports_vision = self._custom_capabilities.get("supports_vision", False),
            _supports_json_mode = self._custom_capabilities.get("supports_json_mode", False),
            _max_context_length = self._custom_capabilities.get("max_context_length"),
            _max_output_tokens = self._custom_capabilities.get("max_output_tokens"),
            _default_temperature = self._custom_capabilities.get("default_temperature", 0.7),
            _temperature_range = tuple(
                self._custom_capabilities.get("temperature_range", [0.0, 2.0])
            ),
        )

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create the HTTP client."""
        if self._client is None or self._client.is_closed:
            _headers = {
                "Content-Type": "application/json",
            }
            if self.api_key:
                headers["Authorization"] = f"Bearer {self.api_key}"
            
            self._client = httpx.AsyncClient(
                _base_url = self.base_url,
                _headers = headers,
                _timeout = httpx.Timeout(60.0, connect=10.0),
            )
        return self._client

    async def complete(self, request: LLMRequest) -> LLMResponse:
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
        
        # Add any extra body parameters
        if request.extra_body:
            payload.update(request.extra_body)
        
        logger.debug(
            "Sending OpenAI-compatible completion request",
            _base_url = self.base_url,
            _model = model,
            stream=False,
        )
        
        try:
            _response = await client.post(
                "/chat/completions",
                json=payload,
            )
            
            if response.status_code == 401 and self.api_key:
                raise ProviderAuthenticationError(
                    "Invalid API key",
                    _provider = "openai_compatible",
                )
            elif response.status_code >= 500:
                raise ProviderUnavailableError(
                    "Service unavailable",
                    _provider = "openai_compatible",
                )
            elif response.status_code != 200:
                raise ProviderError(
                    f"API error: {response.status_code} - {response.text[:200]}",
                    _provider = "openai_compatible",
                )
            
            _data = response.json()
            _latency_ms = (time.time() - start_time) * 1000
            
            _choice = data.get("choices", [{}])[0]
            _message_data = choice.get("message", {})
            
            # Parse tool calls if present
            _tool_calls = []
            if "tool_calls" in message_data:
                for tc in message_data["tool_calls"]:
                    tool_calls.append(
                        ToolCall(
                            _id = tc.get("id", ""),
                            _name = tc.get("function", {}).get("name", ""),
                            _arguments = json.loads(tc.get("function", {}).get("arguments", "{}")),
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
                _provider = "openai_compatible",
                _cause = e,
            )

    async def stream(self, request: LLMRequest) -> AsyncIterator[str]:
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
            "Sending OpenAI-compatible streaming request",
            _base_url = self.base_url,
            _model = model,
        )
        
        try:
            async with client.stream(
                "POST",
                "/chat/completions",
                json=payload,
            ) as response:
                if response.status_code == 401 and self.api_key:
                    raise ProviderAuthenticationError(
                        "Invalid API key",
                        _provider = "openai_compatible",
                    )
                elif response.status_code != 200:
                    raise ProviderError(
                        f"API error: {response.status_code}",
                        _provider = "openai_compatible",
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
                _provider = "openai_compatible",
                _cause = e,
            )

    async def list_models(self) -> List[str]:
        """List available models from the compatible API."""
        _client = await self._get_client()
        
        try:
            _response = await client.get("/models")
            if response.status_code == 200:
                _data = response.json()
                return [m.get("id", m.get("name", "")) for m in data.get("data", [])]
        except Exception as e:
            logger.warning("Failed to list models", error=str(e))
        
        return []

    async def __aexit__(self, _exc_type, _exc_val, _exc_tb):
        """Cleanup HTTP client."""
        if self._client and not self._client.is_closed:
            await self._client.aclose()
