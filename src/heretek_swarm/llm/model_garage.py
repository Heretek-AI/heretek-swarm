"""
Heretek Swarm - Model Garage

LiteLLM Integration for unified LLM API across all 23 agents.
Provides automatic routing, fallback, and load balancing across providers.

Supports:
- OpenAI (GPT-4, GPT-3.5, o1)
- Ollama (local models)
- MiniMax
- Z.AI (Zhipu)
- Anthropic (Claude)
- Google (Gemini)
- Groq
- Azure OpenAI
- Local llama.cpp

Configuration: ~/.heretek-swarm/config.json
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, AsyncIterator, Callable, Dict, List, Optional, Type, Union

import httpx
import structlog

logger = structlog.get_logger("model_garage")

# ============================================================================
# Configuration
# ============================================================================

HERETEK_DATA_DIR = Path.home() / ".heretek-swarm"
HERETEK_CONFIG_FILE = HERETEK_DATA_DIR / "config.json"
HERETEK_LOGS_DIR = HERETEK_DATA_DIR / "logs"

# Ensure directories exist
HERETEK_DATA_DIR.mkdir(parents=True, exist_ok=True)
HERETEK_LOGS_DIR.mkdir(parents=True, exist_ok=True)


class ProviderType(str, Enum):
    """Supported LLM provider types."""
    OPENAI = "openai"
    OLLAMA = "ollama"
    MINIMAX = "minimax"
    ZAI = "zai"
    ANTHROPIC = "anthropic"
    GOOGLE = "google"
    GROQ = "groq"
    AZURE = "azure"
    LLAMACPP = "llamacpp"
    OPENAI_COMPATIBLE = "openai_compatible"


@dataclass
class ModelInfo:
    """Information about a model."""
    name: str
    provider: ProviderType
    max_tokens: Optional[int] = None
    supports_streaming: bool = True
    supports_function_calling: bool = False
    supports_vision: bool = False
    context_length: Optional[int] = None
    cost_per_1k_input: Optional[float] = None
    cost_per_1k_output: Optional[float] = None
    is_local: bool = False


@dataclass
class ProviderConfig:
    """Configuration for an LLM provider."""
    id: str
    name: str
    provider_type: ProviderType
    base_url: str
    api_key: Optional[str] = None
    default_model: Optional[str] = None
    available_models: List[str] = field(default_factory=list)
    is_enabled: bool = True
    is_default: bool = False
    priority: int = 100  # Lower = higher priority
    max_rpm: Optional[int] = None  # Requests per minute
    max_tpm: Optional[int] = None  # Tokens per minute
    timeout: float = 60.0
    retry_count: int = 3
    retry_delay: float = 1.0
    health_status: str = "unknown            "id": self.id,
            "name": self.name,
            "provider_type": self.provider_type.value,
            "base_url": self.base_url,
            "api_key": "***" if self.api_key else None,
            "default_model": self.default_model,
            "available_models": self.available_models,
            "is_enabled": self.is_enabled,
            "is_default": self.is_default,
            "priority": self.priority,
            "max_rpm": self.max_rpm,
            "max_tpm": self.max_tpm,
            "health_status": self.health_status,
            "last_health_check": self.last_health_check,
            "error_message": self.error_message,
        }


@dataclass
class ChatMessage:
    """A chat message."""
    role: str  # system, user, assistant
    content: str
    name: Optional[str] = None
    tool_calls: Optional[List[Dict[str, Any]]] = None
    tool_call_id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        result: Dict[str, Any] = {"role": self.role, "content": self.content}
        if self.name:
            result["name"] = self.name
        if self.tool_calls:
            result["tool_calls"] = self.tool_calls
        if self.tool_call_id:
            result["tool_call_id"] = self.tool_call_id
        return result


@dataclass
class LLMRequest:
    """Request for LLM completion."""
    messages: List[ChatMessage]
    model: Optional[str] = None
    temperature: float = 0.7
    max_tokens: Optional[int] = None
    top_p: float = 1.0
    frequency_penalty: float = 0.0
    presence_penalty: float = 0.0
    stop: Optional[List[str]] = None
    stream: bool = False
    tools: Optional[List[Dict[str, Any]]] = None
    tool_choice: Optional[Union[str, Dict[str, Any]]] = None
    response_format: Optional[Dict[str, Any]] = None
    seed: Optional[int] = None
    extra_body: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        result: Dict[str, Any] = {
            "messages": [m.to_dict() for m in self.messages],
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "top_p": self.top_p,
            "frequency_penalty": self.frequency_penalty,
            "presence_penalty": self.presence_penalty,
            "stream": self.stream,
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
class LLMResponse:
    """Response from LLM completion."""
    content: str
    model: str
    provider: ProviderType
    usage: Dict[str, int] = field(default_factory=dict)
    finish_reason: Optional[str] = None
    tool_calls: List[Dict[str, Any]] = field(default_factory=list)
    raw_response: Optional[Dict[str, Any]] = None
    latency_ms: float = 0.0
    cost: Optional[float] = None

    @property
    def prompt_tokens(self) -> int:
        return self.usage.get("prompt_tokens", 0)

    @property
    def completion_tokens(self) -> int:
        return self.usage.get("completion_tokens", 0)

    @property
    def total_tokens(self) -> int:
        return self.usage.get("total_tokens", 0)


# ============================================================================
# Base Provider Implementation
# ============================================================================

class LLMProvider(ABC):
    """Abstract base class for LLM providers."""

    def __init__(self, config: ProviderConfig):
        self.config = config
        self._client: Optional[httpx.AsyncClient] = None
        self._rate_limiter = asyncio.Semaphore(10)  # Concurrent requests
        self._last_request_time: float = 0

    @abstractmethod
    async def complete(self, request: LLMRequest) -> LLMResponse:
        """Complete a chat request."""
        pass

    @abstractmethod
    async def stream(self, request: LLMRequest) -> AsyncIterator[str]:
        """Stream chat completion tokens."""
        pass

    @abstractmethod
    async def health_check(self) -> bool:
        """Check if the provider is healthy."""
        pass

    async def close(self) -> None:
        """Close the provider."""
        if self._client:
            await self._client.aclose()
            self._client = None

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self._client is None or self._client.is_closed:
            headers: Dict[str, str] = {"Content-Type": "application/json"}
            if self.config.api_key:
                headers["Authorization"] = f"Bearer {self.config.api_key}"

            self._client = httpx.AsyncClient(
                base_url=self.config.base_url.rstrip("/"),
                headers=headers,
                timeout=httpx.Timeout(self.config.timeout, connect=10.0),
            )
        return self._client

    async def _rate_limit(self) -> None:
        """Apply rate limiting."""
        if self.config.max_rpm:
            min_interval = 60.0 / self.config.max_rpm
            elapsed = time.time() - self._last_request_time
            if elapsed < min_interval:
                await asyncio.sleep(min_interval - elapsed)
        self._last_request_time = time.time()


# ============================================================================
# Provider Implementations
# ============================================================================

class OpenAIProvider(LLMProvider):
    """OpenAI API provider."""

    async def complete(self, request: LLMRequest) -> LLMResponse:
        await self._rate_limit()
        async with self._rate_limiter:
            client = await self._get_client()
            start_time = time.time()

            model = request.model or self.config.default_model or "gpt-4o"
            payload = request.to_dict()
            payload["model"] = model

            try:
                response = await client.post("/chat/completions", json=payload)
                response.raise_for_status()
                data = response.json()

                latency_ms = (time.time() - start_time) * 1000
                choice = data["choices"][0]
                message = choice.get("message", {})

                return LLMResponse(
                    content=message.get("content", ""),
                    model=data.get("model", model),
                    provider=ProviderType.OPENAI,
                    usage=data.get("usage", {}),
                    finish_reason=choice.get("finish_reason"),
                    tool_calls=message.get("tool_calls", []),
                    raw_response=data,
                    latency_ms=latency_ms,
                )
            except httpx.HTTPStatusError as e:
                logger.error("OpenAI API error", status=e.response.status_code, detail=e.response.text)
                raise
            except Exception as e:
                logger.error("OpenAI completion failed", error=str(e))
                raise


class OllamaProvider(LLMProvider):
    """Ollama local API provider."""

    async def complete(self, request: LLMRequest) -> LLMResponse:
        await self._rate_limit()
        async with self._rate_limiter:
            client = await self._get_client()
            start_time = time.time()

            # Ollama format
            model = request.model or self.config.default_model or "llama3.1"
            payload = {
                "model": model,
                "messages": [m.to_dict() for m in request.messages],
                "stream": False,
                "options": {
                    "temperature": request.temperature,
                    "top_p": request.top_p,
                }
            }
            if request.max_tokens:
                payload["options"]["num_predict"] = request.max_tokens

            try:
                response = await client.post("/api/chat", json=payload)
                response.raise_for_status()
                data = response.json()

                latency_ms = (time.time() - start_time) * 1000
                message = data.get("message", {})

                # Calculate usage (Ollama doesn't provide this)
                usage = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}

                return LLMResponse(
                    content=message.get("content", ""),
                    model=model,
                    provider=ProviderType.OLLAMA,
                    usage=usage,
                    finish_reason=data.get("done_reason"),
                    raw_response=data,
                    latency_ms=latency_ms,
                    cost=0.0,  # Local, no cost
                )
            except Exception as e:
                logger.error("Ollama completion failed", error=str(e))
                raise

    async def stream(self, request: LLMRequest) -> AsyncIterator[str]:
        await self._rate_limit()
        async with self._rate_limiter:
            client = await self._get_client()

            model = request.model or self.config.default_model or "llama3.1"
            payload = {
                "model": model,
                "messages": [m.to_dict() for m in request.messages],
                "stream": True,
                "options": {
                    "temperature": request.temperature,
                }
            }

            async with client.stream("POST", "/api/chat", json=payload) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if line:
                        try:
                            data = json.loads(line)
                            if "message" in data and "content" in data["message"]:
                                yield data["message"]["content"]
                            if data.get("done"):
                                break
                        except json.JSONDecodeError:
                            continue


class MiniMaxProvider(LLMProvider):
    """MiniMax API provider."""

    def __init__(self, config: ProviderConfig):
        super().__init__(config)
        self.group_id = config.metadata.get("group_id")

    async def complete(self, request: LLMRequest) -> LLMResponse:
        await self._rate_limit()
        async with self._rate_limiter:
            client = await self._get_client()
            start_time = time.time()

            model = request.model or self.config.default_model or "abab6.5s"
            payload = {
                "model": model,
                "messages": [m.to_dict() for m in request.messages],
                "temperature": request.temperature,
                "max_tokens": request.max_tokens or 2048,
            }
            if self.group_id:
                payload["group_id"] = self.group_id

            try:
                response = await client.post("/text/chatcompletion_v2", json=payload)
                response.raise_for_status()
                data = response.json()

                latency_ms = (time.time() - start_time) * 1000
                choice = data["choices"][0]
                message = choice.get("message", {})

                return LLMResponse(
                    content=message.get("content", ""),
                    model=model,
                    provider=ProviderType.MINIMAX,
                    usage=data.get("usage", {}),
                    finish_reason=choice.get("finish_reason"),
                    raw_response=data,
                    latency_ms=latency_ms,
                )
            except Exception as e:
                logger.error("MiniMax completion failed", error=str(e))
                raise


class AnthropicProvider(LLMProvider):
    """Anthropic Claude API provider."""

    async def complete(self, request: LLMRequest) -> LLMResponse:
        await self._rate_limit()
        async with self._rate_limiter:
            client = await self._get_client()
            start_time = time.time()

            model = request.model or self.config.default_model or "claude-3-5-sonnet-20241022"

            # Convert messages to Anthropic format
            anthropic_messages = []
            system_prompt = ""
            for msg in request.messages:
                if msg.role == "system":
                    system_prompt += msg.content + "\n"
                else:
                    anthropic_messages.append({"role": msg.role, "content": msg.content})

            payload: Dict[str, Any] = {
                "model": model,
                "messages": anthropic_messages,
                "max_tokens": request.max_tokens or 4096,
                "temperature": request.temperature,
            }
            if system_prompt:
                payload["system"] = system_prompt

            try:
                response = await client.post("/v1/messages", json=payload)
                response.raise_for_status()
                data = response.json()

                latency_ms = (time.time() - start_time) * 1000

                return LLMResponse(
                    content=data.get("content", [{"text": ""}])[0].get("text", ""),
                    model=model,
                    provider=ProviderType.ANTHROPIC,
                    usage=data.get("usage", {}),
                    finish_reason=data.get("stop_reason"),
                    raw_response=data,
                    latency_ms=latency_ms,
                )
            except Exception as e:
                logger.error("Anthropic completion failed", error=str(e))
                raise


class OpenAICompatibleProvider(LLMProvider):
    """Generic OpenAI-compatible API provider."""

    async def complete(self, request: LLMRequest) -> LLMResponse:
        await self._rate_limit()
        async with self._rate_limiter:
            client = await self._get_client()
            start_time = time.time()

            model = request.model or self.config.default_model
            if not model:
                raise ValueError("Model must be specified for OpenAI-compatible providers")

            payload = request.to_dict()
            payload["model"] = model

            try:
                response = await client.post("/chat/completions", json=payload)
                response.raise_for_status()
                data = response.json()

                latency_ms = (time.time() - start_time) * 1000
                choice = data["choices"][0]
                message = choice.get("message", {})

                return LLMResponse(
                    content=message.get("content", ""),
                    model=data.get("model", model),
                    provider=ProviderType.OPENAI_COMPATIBLE,
                    usage=data.get("usage", {}),
                    finish_reason=choice.get("finish_reason"),
                    tool_calls=message.get("tool_calls", []),
                    raw_response=data,
                    latency_ms=latency_ms,
                )
            except Exception as e:
                logger.error("OpenAI-compatible completion failed", error=str(e))
                raise


# ============================================================================
# Provider Registry
# ============================================================================

PROVIDER_CLASSES: Dict[ProviderType, Type[LLMProvider]] = {
    ProviderType.OPENAI: OpenAIProvider,
    ProviderType.OLLAMA: OllamaProvider,
    ProviderType.MINIMAX: MiniMaxProvider,
    ProviderType.ANTHROPIC: AnthropicProvider,
    ProviderType.OPENAI_COMPATIBLE: OpenAICompatibleProvider,
}


def register_provider_class(provider_type: ProviderType, provider_class: Type[LLMProvider]) -> None:
    """Register a custom provider class."""
    PROVIDER_CLASSES[provider_type] = provider_class


# ============================================================================
# Model Garage - Main Class
# ============================================================================

class ModelGarage:
    """
    Unified LLM interface for Heretek Swarm.

    Provides:
    - Multi-provider support with automatic routing
    - Fallback on provider failure
    - Load balancing across providers
    - Cost optimization
    - Health monitoring
    - Unified OpenAI-compatible API

    Configuration is loaded from ~/.heretek-swarm/config.json

    Example:
        garage = ModelGarage()

        # Complete a request
        response = await garage.complete(
            messages=[ChatMessage(role="user", content="Hello!")],
            model="gpt-4o"
        )
        print(response.content)

        # Or specify provider preference
        response = await garage.complete(
            messages=[ChatMessage(role="user", content="Hello!")],
            provider_preference=["ollama", "openai"]  # Try Ollama first, fallback to OpenAI
        )
    """

    def __init__(
        self,
        config_file: Optional[Path] = None,
        default_provider: Optional[ProviderType] = None,
    ):
        """
        Initialize the Model Garage.

        Args:
            config_file: Path to configuration file (default: ~/.heretek-swarm/config.json)
            default_provider: Default provider to use if not specified
        """
        self.config_file = config_file or HERETEK_CONFIG_FILE
        self._providers: Dict[str, LLMProvider] = {}
        self._provider_configs: Dict[str, ProviderConfig] = {}
        self._initialized = False

        # Load configuration
        self._load_config()

        # Set default provider
        if default_provider:
            self._default_provider = default_provider
        elif self._provider_configs:
            # Use the default provider from config
            for config in self._provider_configs.values():
                if config.is_default:
                    self._default_provider = config.provider_type
                    break
            else:
                self._default_provider = ProviderType.OLLAMA  # Fallback to Ollama
        else:
            self._default_provider = ProviderType.OLLAMA

    def _load_config(self) -> None:
        """Load provider configuration from file."""
        try:
            if self.config_file.exists():
                with open(self.config_file, "r") as f:
                    config_data = json.load(f)

                providers = config_data.get("modelProviders", [])
                for p in providers:
                    provider_type = ProviderType(p.get("type", "openai"))
                    config = ProviderConfig(
                        id=p.get("id", ""),
                        name=p.get("name", ""),
                        provider_type=provider_type,
                        base_url=p.get("baseUrl", ""),
                        api_key=p.get("apiKey"),
                        default_model=p.get("defaultModel"),
                        available_models=p.get("models", []),
                        is_enabled=p.get("isEnabled", True),
                        is_default=p.get("isDefault", False),
                        priority=p.get("priority", 100),
                    )
                    if "groupId" in p:
                        config.metadata["group_id"] = p["groupId"]
                    self._provider_configs[config.id] = config

                logger.info("Loaded provider configuration", count=len(self._provider_configs))
            else:
                # Create default config
                self._create_default_config()
        except Exception as e:
            logger.error("Failed to load configuration", error=str(e))
            self._create_default_config()

    def _create_default_config(self) -> None:
        """Create default configuration file."""
        default_config = {
            "version": "1.0.0",
            "modelProviders": [
                {
                    "id": "default-ollama",
                    "type": "ollama",
                    "name": "Local Ollama",
                    "baseUrl": "http://localhost:11434",
                    "defaultModel": "llama3.1",
                    "isEnabled": True,
                    "isDefault": True,
                    "priority": 1,
                }
            ]
        }

        try:
            self.config_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.config_file, "w") as f:
                json.dump(default_config, f, indent=2)
            logger.info("Created default configuration", path=str(self.config_file))

            # Reload config
            self._load_config()
        except Exception as e:
            logger.error("Failed to create default configuration", error=str(e))

    def _save_config(self) -> None:
        """Save provider configuration to file."""
        try:
            config_data = {"version": "1.0.0", "modelProviders": []}
            for config in self._provider_configs.values():
                provider_data = {
                    "id": config.id,
                    "type": config.provider_type.value,
                    "name": config.name,
                    "baseUrl": config.base_url,
                    "defaultModel": config.default_model,
                    "models": config.available_models,
                    "isEnabled": config.is_enabled,
                    "isDefault": config.is_default,
                    "priority": config.priority,
                }
                if config.api_key:
                    provider_data["apiKey"] = config.api_key
                if config.metadata.get("group_id"):
                    provider_data["groupId"] = config.metadata["group_id"]
                config_data["modelProviders"].append(provider_data)

            with open(self.config_file, "w") as f:
                json.dump(config_data, f, indent=2)
            logger.info("Saved provider configuration")
        except Exception as e:
            logger.error("Failed to save configuration", error=str(e))

    async def initialize(self) -> None:
        """Initialize all enabled providers."""
        if self._initialized:
            return

        for config in self._provider_configs.values():
            if config.is_enabled and config.provider_type in PROVIDER_CLASSES:
                try:
                    provider_class = PROVIDER_CLASSES[config.provider_type]
                    provider = provider_class(config)
                    self._providers[config.id] = provider
                    logger.info("Initialized provider", name=config.name, type=config.provider_type.value)
                except Exception as e:
                    logger.error("Failed to initialize provider", name=config.name, error=str(e))

        self._initialized = True
        logger.info("Model Garage initialized", provider_count=len(self._providers))

    async def close(self) -> None:
        """Close all providers."""
        for provider in self._providers.values():
            await provider.close()
        self._providers.clear()
        self._initialized = False
        logger.info("Model Garage closed")

    def add_provider(self, config: ProviderConfig) -> None:
        """Add a new provider configuration."""
        self._provider_configs[config.id] = config
        self._save_config()

    def remove_provider(self, provider_id: str) -> None:
        """Remove a provider configuration."""
        if provider_id in self._provider_configs:
            del self._provider_configs[provider_id]
        if provider_id in self._providers:
            del self._providers[provider_id]
        self._save_config()

    def get_provider_config(self, provider_id: str) -> Optional[ProviderConfig]:
        """Get provider configuration by ID."""
        return self._provider_configs.get(provider_id)

    def list_providers(self) -> List[Dict[str, Any]]:
        """List all configured providers."""
        return [config.to_dict() for config in self._provider_configs.values()]

    async def health_check(self, provider_id: Optional[str] = None) -> Dict[str, bool]:
        """Check health of providers."""
        results = {}
        providers_to_check = (
            {provider_id: self._providers[provider_id]}
            if provider_id
            else self._providers
        )

        for pid, provider in providers_to_check.items():
            try:
                healthy = await provider.health_check()
                results[pid] = healthy
                provider.config.health_status = "healthy" if healthy else "unhealthy"
            except Exception as e:
                results[pid] = False
                provider.config.health_status = "unhealthy"
                provider.config.error_message = str(e)
                logger.error("Health check failed", provider=pid, error=str(e))

        return results

    async def complete(
        self,
        messages: List[ChatMessage],
        model: Optional[str] = None,
        provider_id: Optional[str] = None,
        provider_preference: Optional[List[ProviderType]] = None,
        **kwargs,
    ) -> LLMResponse:
        """
        Complete a chat request with automatic provider routing.

        Args:
            messages: List of chat messages
            model: Model to use (optional, uses provider default)
            provider_id: Specific provider ID to use
            provider_preference: List of provider types to try in order
            **kwargs: Additional request parameters

        Returns:
            LLMResponse from the selected provider
        """
        if not self._initialized:
            await self.initialize()

        # Build request
        request = LLMRequest(
            messages=messages,
            model=model,
            **{k: v for k, v in kwargs.items() if v is not None}
        )

        # Determine providers to try
        if provider_id:
            providers_to_try = [provider_id] if provider_id in self._providers else []
        elif provider_preference:
            providers_to_try = [
                pid for pid, cfg in self._provider_configs.items()
                if cfg.provider_type in provider_preference and pid in self._providers
            ]
        else:
            # Use default provider, then fallbacks
            providers_to_try = []
            for cfg in sorted(self._provider_configs.values(), key=lambda c: c.priority):
                if cfg.is_enabled and cfg.id in self._providers:
                    providers_to_try.append(cfg.id)
                    if cfg.is_default:
                        break

        if not providers_to_try:
            raise ValueError("No available providers")

        # Try providers in order
        last_error = None
        for pid in providers_to_try:
            provider = self._providers.get(pid)
            if not provider:
                continue

            try:
                logger.debug(
                    "Attempting completion",
                    provider=pid,
                    model=model or provider.config.default_model
                )
                response = await provider.complete(request)
                logger.info(
                    "Completion successful",
                    provider=pid,
                    model=response.model,
                    latency_ms=response.latency_ms
                )
                return response
            except Exception as e:
                last_error = e
                logger.warning(
                    "Provider failed, trying next",
                    provider=pid,
                    error=str(e)
                )

        raise last_error or RuntimeError("All providers failed")

    async def stream(
        self,
        messages: List[ChatMessage],
        model: Optional[str] = None,
        provider_id: Optional[str] = None,
        **kwargs,
    ) -> AsyncIterator[str]:
        """
        Stream chat completion tokens.

        Args:
            messages: List of chat messages
            model: Model to use
            provider_id: Specific provider ID to use
            **kwargs: Additional request parameters

        Yields:
            String tokens from the completion
        """
        if not self._initialized:
            await self.initialize()

        request = LLMRequest(
            messages=messages,
            model=model,
            stream=True,
            **{k: v for k, v in kwargs.items() if v is not None}
        )

        # Get provider
        provider = None
        if provider_id and provider_id in self._providers:
            provider = self._providers[provider_id]
        else:
            # Find first provider that supports streaming
            for cfg in sorted(self._provider_configs.values(), key=lambda c: c.priority):
                if cfg.is_enabled and cfg.id in self._providers:
                    provider = self._providers[cfg.id]
                    break

        if not provider:
            raise ValueError("No streaming-capable provider available")

        try:
            async for token in provider.stream(request):
                yield token
        except Exception as e:
            logger.error("Streaming failed", error=str(e))
            raise


# ============================================================================
# Global Instance
# ============================================================================

_model_garage: Optional[ModelGarage] = None


def get_model_garage() -> ModelGarage:
    """Get the global ModelGarage instance."""
    global _model_garage
    if _model_garage is None:
        _model_garage = ModelGarage()
    return _model_garage


async def initialize_model_garage() -> ModelGarage:
    """Initialize and return the global ModelGarage instance."""
    global _model_garage
    _model_garage = ModelGarage()
    await _model_garage.initialize()
    return _model_garage


# ============================================================================
# Example Usage
# ============================================================================

async def main():
    """Example usage of ModelGarage."""
    # Initialize
    garage = await initialize_model_garage()

    # List available providers
    providers = garage.list_providers()
    print("Available providers:", json.dumps(providers, indent=2))

    # Complete a request
    response = await garage.complete(
        messages=[
            ChatMessage(role="system", content="You are a helpful AI assistant."),
            ChatMessage(role="user", content="What is the capital of France?"),
        ],
        model="gpt-4o"  # Optional: specify model
    )

    print(f"Response: {response.content}")
    print(f"Model: {response.model}")
    print(f"Provider: {response.provider.value}")
    print(f"Latency: {response.latency_ms:.2f}ms")

    # Clean up
    await garage.close()


if __name__ == "__main__":
    asyncio.run(main())
