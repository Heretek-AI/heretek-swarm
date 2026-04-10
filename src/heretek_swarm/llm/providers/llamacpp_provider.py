"""
llama.cpp LLM Provider

Implementation of the LLM provider interface for llama.cpp server.
Supports local LLM inference with GGUF quantized models.

Reference: https://github.com/ggerganov/llama.cpp/blob/master/examples/server/README.md
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
    Message,
    ProviderCapabilities,
    ProviderError,
    ProviderUnavailableError,
)

_logger = structlog.get_logger("llm.providers.llamacpp")


class LlamaCppProvider(LLMProviderBase):
    """
    llama.cpp LLM Provider implementation.
    
    Supports:
    - Local LLM inference with GGUF models
    - Streaming completions
    - Various quantized models (Q4_K_M, Q5_K_M, etc.)
    - GPU acceleration via cuBLAS, Vulkan, etc.
    
    Example:
        _provider = LlamaCppProvider(
            base_url="http://localhost:8080",
            default_model="llama-2-7b-chat.Q4_K_M.gguf"
        )
    """

    def __init__(self, _base_url: str, _default_model: Optional[str], _extra_config: Optional[Dict[str, _Any]]):
        """
        Initialize the llama.cpp provider.
        
        Args:
            base_url: llama.cpp server URL (default: http://localhost:8080)
            default_model: Default model to use (model path)
            extra_config: Additional configuration
        """
        super().__init__(
            _provider_name = "llamacpp",
            base_url=base_url,
            api_key=None,  # llama.cpp doesn't require authentication
            default_model=default_model,
            extra_config=extra_config,
        )
        
        self._client: Optional[httpx.AsyncClient] = None

    def _init_capabilities(self) -> ProviderCapabilities:
        """Initialize provider capabilities."""
        return ProviderCapabilities(
            _supports_streaming = True,
            _supports_function_calling = False,
            _supports_vision = False,
            _supports_json_mode = False,
            _max_context_length = self.extra_config.get("max_context_length", 4096),
            _max_output_tokens = self.extra_config.get("max_output_tokens", 512),
            default_temperature=0.8,  # llama.cpp default
            _temperature_range = (0.0, 2.0),
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
        
        # Convert messages to llama.cpp format
        # llama.cpp server uses a prompt format
        _prompt = self._format_prompt(request.messages)
        
        # Build llama.cpp-specific payload
        _payload = {
            "prompt": prompt,
            "temperature": request.temperature,
            "top_p": request.top_p,
            "n_predict": request.max_tokens or 256,
            "stream": False,
        }
        
        # Add stop sequences
        if request.stop:
            payload["stop"] = request.stop
        
        # Add any extra parameters
        if request.extra_body:
            payload.update(request.extra_body)
        
        logger.debug(
            "Sending llama.cpp completion request",
            _prompt_length = len(prompt),
        )
        
        try:
            _response = await client.post(
                "/completion",
                _json = payload,
            )
            
            if response.status_code >= 500:
                raise ProviderUnavailableError(
                    "llama.cpp service unavailable",
                    _provider = "llamacpp",
                )
            elif response.status_code != 200:
                raise ProviderError(
                    f"llama.cpp API error: {response.status_code} - {response.text[:200]}",
                    _provider = "llamacpp",
                )
            
            _data = response.json()
            _latency_ms = (time.time() - start_time) * 1000
            
            content = data.get("content", "")
            
            # Calculate approximate token usage
            _prompt_tokens = self._estimate_tokens(prompt)
            _completion_tokens = self._estimate_tokens(content)
            
            return LLMResponse(
                content=content,
                _model = self.default_model or "llamacpp",
                _usage = {
                    "prompt_tokens": prompt_tokens,
                    "completion_tokens": completion_tokens,
                    "total_tokens": prompt_tokens + completion_tokens,
                },
                _finish_reason = "stop",
                _raw_response = data,
                _latency_ms = latency_ms,
            )
            
        except httpx.RequestError as e:
            raise ProviderUnavailableError(
                f"Request failed: {e}. Is llama.cpp server running?",
                _provider = "llamacpp",
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
        
        _prompt = self._format_prompt(request.messages)
        
        _payload = {
            "prompt": prompt,
            "temperature": request.temperature,
            "top_p": request.top_p,
            "n_predict": request.max_tokens or 256,
            "stream": True,
        }
        
        if request.stop:
            payload["stop"] = request.stop
        
        logger.debug(
            "Sending llama.cpp streaming request",
            _prompt_length = len(prompt),
        )
        
        try:
            async with client.stream(
                "POST",
                "/completion",
                _json = payload,
            ) as response:
                if response.status_code != 200:
                    raise ProviderError(
                        f"llama.cpp API error: {response.status_code}",
                        _provider = "llamacpp",
                    )
                
                async for line in response.aiter_lines():
                    if not line.strip():
                        continue
                    
                    # llama.cpp sends raw text in streaming mode
                    # or JSON with "content" field
                    try:
                        if line.startswith("{"):
                            _chunk = json.loads(line)
                            content = chunk.get("content", "")
                        else:
                            content = line
                        
                        if content:
                            yield content
                    except json.JSONDecodeError:
                        # Raw text mode
                        if line:
                            yield line
                        
        except httpx.RequestError as e:
            raise ProviderUnavailableError(
                f"Stream request failed: {e}",
                _provider = "llamacpp",
                _cause = e,
            )

    def _format_prompt(self, _messages: List[Message]) -> str:
        """
        Format messages into a prompt for llama.cpp.
        
        Uses a simple chat format. Can be customized based on the model.
        """
        _formatted = ""
        
        for msg in messages:
            if msg.role == "system":
                formatted += f"System: {msg.content}\n"
            elif msg.role == "user":
                formatted += f"User: {msg.content}\n"
            elif msg.role == "assistant":
                formatted += f"Assistant: {msg.content}\n"
        
        # Add assistant prefix to prompt completion
        formatted += "Assistant: "
        
        return formatted

    def _estimate_tokens(self, _text: str) -> int:
        """Estimate token count from text."""
        _total_chars = len(text)
        # Rough estimate: 1 token ≈ 4 characters for English text
        return max(1, total_chars // 4)

    async def list_models(self) -> List[str]:
        """
        List available models.
        
        Note: llama.cpp server typically loads a single model at startup.
        Returns the configured default model.
        """
        if self.default_model:
            return [self.default_model]
        return []

    async def __aexit__(self, _exc_type, _exc_val, _exc_tb):
        """Cleanup HTTP client."""
        if self._client and not self._client.is_closed:
            await self._client.aclose()
