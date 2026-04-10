"""
LLM Provider Base Class

Abstract base class for all LLM providers in Heretek Swarm.
Defines the interface that all providers must implement.
"""


import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, AsyncIterator, Callable, Dict, List, Optional, Union

import structlog

_logger = structlog.get_logger("llm.providers.base")

# Type alias for streaming callback
_StreamingCallback = Callable[[str], None]


@dataclass
class Message:
    """A chat message for LLM interaction."""
    role: str  # "system", "user", "assistant", "tool"
    content: str
    name: Optional[str] = None
    tool_calls: Optional[List[Dict[str, Any]]] = None
    tool_call_id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert message to dictionary."""
        _result = {"role": self.role, "content": self.content}
        if self.name:
            result["name"] = self.name
        if self.tool_calls:
            result["tool_calls"] = self.tool_calls
        if self.tool_call_id:
            result["tool_call_id"] = self.tool_call_id
        return result


@dataclass
class LLMRequest:
    """Request parameters for LLM completion."""
    messages: List[Message]
    model: Optional[str] = None
    temperature: float = 0.7
    max_tokens: Optional[int] = None
    top_p: float = 1.0
    frequency_penalty: float = 0.0
    presence_penalty: float = 0.0
    stop: Optional[List[str]] = None
    stream: bool = False
    n: int = 1
    tools: Optional[List[Dict[str, Any]]] = None
    tool_choice: Optional[Union[str, Dict[str, Any]]] = None
    response_format: Optional[Dict[str, Any]] = None
    seed: Optional[int] = None
    extra_body: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert request to dictionary for API calls."""
        _result = {
            "messages": [m.to_dict() for m in self.messages],
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "top_p": self.top_p,
            "frequency_penalty": self.frequency_penalty,
            "presence_penalty": self.presence_penalty,
            "stream": self.stream,
            "n": self.n,
        }
        
        if self.model:
            result["model"] = self.model
        if self.stop:
            result["stop"] = self.stop
        if self.tools:
            result["tools"] = self.tools
        if self.tool_choice:
            result["tool_choice"] = self.tool_choice
        if self.response_format:
            result["response_format"] = self.response_format
        if self.seed is not None:
            result["seed"] = self.seed
        if self.extra_body:
            result.update(self.extra_body)
        
        return result


@dataclass
class ToolCall:
    """A tool call from the LLM."""
    id: str
    name: str
    arguments: Dict[str, Any]


@dataclass
class LLMResponse:
    """Response from an LLM completion."""
    content: str
    model: str
    usage: Dict[str, int] = field(default_factory=dict)
    finish_reason: Optional[str] = None
    tool_calls: List[ToolCall] = field(default_factory=list)
    raw_response: Optional[Dict[str, Any]] = None
    latency_ms: float = 0.0
    
    @property
    def prompt_tokens(self) -> int:
        """Get the number of prompt tokens used."""
        return self.usage.get("prompt_tokens", 0)
    
    @property
    def completion_tokens(self) -> int:
        """Get the number of completion tokens used."""
        return self.usage.get("completion_tokens", 0)
    
    @property
    def total_tokens(self) -> int:
        """Get the total tokens used."""
        return self.usage.get("total_tokens", 0)


@dataclass
class ProviderCapabilities:
    """Capabilities of an LLM provider."""
    supports_streaming: bool = True
    supports_function_calling: bool = False
    supports_vision: bool = False
    supports_json_mode: bool = False
    max_context_length: Optional[int] = None
    max_output_tokens: Optional[int] = None
    default_temperature: float = 0.7
    temperature_range: tuple = (0.0, 2.0)


class LLMProviderBase(ABC):
    """
    Abstract base class for all LLM providers.
    
    All provider implementations must inherit from this class and implement
    the required abstract methods.
    
    Example usage:
        provider = OpenAIProvider(api_key="sk-...", base_url="...")
        _response = await provider.complete(messages=[...])
        
        async for chunk in provider.stream(messages=[...]):
            print(chunk, end="")
    """

    def __init__(self, _provider_name: str, _base_url: str, _api_key: Optional[str], _default_model: Optional[str], _extra_config: Optional[Dict[str, _Any]]):
        """
        Initialize the LLM provider.
        
        Args:
            provider_name: Name identifier for this provider
            base_url: Base URL for the API
            api_key: API key for authentication (optional for some providers)
            default_model: Default model to use
            extra_config: Additional provider-specific configuration
        """
        self.provider_name = provider_name
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.default_model = default_model
        self.extra_config = extra_config or {}
        
        self._capabilities = self._init_capabilities()
        
        logger.debug(
            "LLM provider initialized",
            provider_name=provider_name,
            _base_url = base_url,
            _has_api_key = api_key is not None,
        )

    @abstractmethod
    def _init_capabilities(self) -> ProviderCapabilities:
        """Initialize provider capabilities. Must be implemented by subclasses."""
        pass

    @property
    def capabilities(self) -> ProviderCapabilities:
        """Get the provider's capabilities."""
        return self._capabilities

    @abstractmethod
    async def complete(self, _request: LLMRequest) -> LLMResponse:
        """
        Complete a chat request non-streaming.
        
        Args:
            request: The LLM request parameters
            
        Returns:
            The LLM response
            
        Raises:
            ProviderError: If the request fails
        """
        pass

    @abstractmethod
    async def stream(self, _request: LLMRequest) -> AsyncIterator[str]:
        """
        Stream a chat completion.
        
        Args:
            request: The LLM request parameters with stream=True
            
        Yields:
            Chunks of the completion text
            
        Raises:
            ProviderError: If the request fails
        """
        pass

    async def complete_with_retry(self, _request: LLMRequest, _max_retries: int, _retry_delay: float) -> LLMResponse:
        """
        Complete a request with automatic retries.
        
        Args:
            request: The LLM request parameters
            max_retries: Maximum number of retry attempts
            retry_delay: Delay between retries in seconds
            
        Returns:
            The LLM response
            
        Raises:
            ProviderError: If all retries fail
        """
        _last_error = None
        
        for attempt in range(max_retries):
            try:
                return await self.complete(request)
            except Exception as e:
                _last_error = e
                if attempt < max_retries - 1:
                    logger.warning(
                        "LLM request failed, retrying",
                        provider=self.provider_name,
                        _attempt = attempt + 1,
                        _max_retries = max_retries,
                        _error = str(e),
                    )
                    await asyncio.sleep(retry_delay * (attempt + 1))
        
        raise ProviderError(
            f"Failed after {max_retries} attempts",
            provider=self.provider_name,
            cause=last_error,
        )

    async def test_connectivity(self, _model: Optional[str]) -> ConnectivityTestResult:
        """
        Test connectivity to the provider.
        
        Args:
            model: Optional model to test with
            
        Returns:
            Connectivity test result
        """
        _start_time = time.time()
        
        try:
            _test_request = LLMRequest(
                _messages = [Message(role="user", content="Hello, this is a connectivity test.")],
                model=model or self.default_model,
                _max_tokens = 10,
            )
            
            _response = await self.complete(test_request)
            _latency_ms = (time.time() - start_time) * 1000
            
            return ConnectivityTestResult(
                _success = True,
                _provider_name = self.provider_name,
                _model_used = response.model,
                _response_text = response.content,
                _latency_ms = latency_ms,
            )
            
        except Exception as e:
            _latency_ms = (time.time() - start_time) * 1000
            return ConnectivityTestResult(
                _success = False,
                _provider_name = self.provider_name,
                _model_used = model or self.default_model,
                _latency_ms = latency_ms,
                _error = str(e),
            )

    async def list_models(self) -> List[str]:
        """
        List available models for this provider.
        
        Returns:
            List of model names
            
        Raises:
            NotImplementedError: If the provider doesn't support listing models
        """
        raise NotImplementedError("Model listing not supported for this provider")

    def _get_model(self, _model: Optional[str]) -> str:
        """Get the model to use, falling back to default if needed."""
        if model:
            return model
        if self.default_model:
            return self.default_model
        raise ValueError("No model specified and no default model configured")

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, _exc_type, _exc_val, _exc_tb):
        """Async context manager exit."""
        pass


@dataclass
class ConnectivityTestResult:
    """Result of a connectivity test."""
    success: bool
    provider_name: str
    model_used: Optional[str]
    latency_ms: float
    response_text: Optional[str] = None
    error: Optional[str] = None


class ProviderError(Exception):
    """Exception raised for provider-related errors."""
    
    def __init__(self, _message: str, _provider: Optional[str], _cause: Optional[Exception]):
        self.message = message
        self.provider = provider
        self.cause = cause
        super().__init__(self.format_message())
    
    def format_message(self) -> str:
        """Format the error message."""
        _msg = self.message
        if self.provider:
            _msg = f"[{self.provider}] {msg}"
        if self.cause:
            _msg = f"{msg} (caused by: {self.cause})"
        return msg


class ProviderConfigurationError(ProviderError):
    """Exception raised for configuration errors."""
    pass


class ProviderAuthenticationError(ProviderError):
    """Exception raised for authentication errors."""
    pass


class ProviderRateLimitError(ProviderError):
    """Exception raised when rate limited."""
    def __init__(self, _message: str, _provider: Optional[str], _retry_after: Optional[float]):
        self.retry_after = retry_after
        super().__init__(message, provider)


class ProviderUnavailableError(ProviderError):
    """Exception raised when provider is unavailable."""
    pass


# Import asyncio for retry logic
import asyncio
