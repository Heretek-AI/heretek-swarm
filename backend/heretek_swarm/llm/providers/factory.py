"""
LLM Provider Factory

Factory for creating LLM provider instances based on configuration.
Supports dynamic provider instantiation and registry.

Provider caching with automatic refresh:

    from heretek_swarm.llm.providers.factory import ProviderManager

    manager = ProviderManager()
    provider = manager.get_or_create("openai", {"api_key": os.getenv("OPENAI_API_KEY")})
    # Later — if env vars changed, the provider is automatically refreshed:
    provider = manager.get_or_create("openai", {"api_key": os.getenv("OPENAI_API_KEY")})
"""

from __future__ import annotations

import hashlib
import json
import threading
from typing import Any

import structlog

from .base import LLMProviderBase, ProviderConfigurationError
from .lemonade_provider import LemonadeProvider
from .llamacpp_provider import LlamaCppProvider
from .minimax_provider import MiniMaxProvider
from .ollama_provider import OllamaProvider
from .openai_compatible import OpenAICompatibleProvider
from .openai_provider import OpenAIProvider
from .zai_provider import ZAIProvider

logger = structlog.get_logger("llm.providers.factory")

# Provider registry mapping provider types to implementation classes
PROVIDER_REGISTRY: dict[str, type[LLMProviderBase]] = {
    "openai": OpenAIProvider,
    "openai_compatible": OpenAICompatibleProvider,
    "ollama": OllamaProvider,
    "llamacpp": LlamaCppProvider,
    "zai": ZAIProvider,
    "minimax": MiniMaxProvider,
    "lemonade": LemonadeProvider,
}


def register_provider(provider_type: str, provider_class: type[LLMProviderBase]) -> None:
    """
    Register a new provider implementation.

    Args:
        provider_type: The provider type identifier
        provider_class: The provider implementation class
    """
    PROVIDER_REGISTRY[provider_type] = provider_class
    logger.info("Provider registered", provider_type=provider_type)


def unregister_provider(provider_type: str) -> None:
    """
    Unregister a provider implementation.

    Args:
        provider_type: The provider type identifier
    """
    if provider_type in PROVIDER_REGISTRY:
        del PROVIDER_REGISTRY[provider_type]
        logger.info("Provider unregistered", provider_type=provider_type)


def get_provider_class(provider_type: str) -> type[LLMProviderBase]:
    """
    Get the provider class for a given type.

    Args:
        provider_type: The provider type identifier

    Returns:
        The provider implementation class

    Raises:
        ProviderConfigurationError: If the provider type is not registered
    """
    if provider_type not in PROVIDER_REGISTRY:
        available = ", ".join(PROVIDER_REGISTRY.keys())
        raise ProviderConfigurationError(
            f"Unknown provider type: {provider_type}. Available: {available}"
        )
    return PROVIDER_REGISTRY[provider_type]


def list_available_providers() -> list[str]:
    """
    List all available provider types.

    Returns:
        List of provider type identifiers
    """
    return list(PROVIDER_REGISTRY.keys())


def create_llm_provider(
    provider_type: str,
    config: dict[str, Any],
) -> LLMProviderBase:
    """
    Create an LLM provider instance from configuration.

    This is the main factory function for creating providers. It takes a
    provider type and configuration dictionary and returns an initialized
    provider instance.

    Args:
        provider_type: The type of provider to create (e.g., "openai", "ollama")
        config: Configuration dictionary with provider-specific settings

    Returns:
        An initialized LLM provider instance

    Raises:
        ProviderConfigurationError: If configuration is invalid

    Example:
        # Create OpenAI provider
        provider = create_llm_provider(
            "openai",
            {
                "api_key": "sk-...",
                "default_model": "gpt-4o"
            }
        )

        # Create Ollama provider
        provider = create_llm_provider(
            "ollama",
            {
                "base_url": "http://localhost:11434",
                "default_model": "llama2"
            }
        )
    """
    provider_class = get_provider_class(provider_type)

    try:
        # Extract common parameters
        base_url = config.get("base_url")
        api_key = config.get("api_key")
        default_model = config.get("default_model")
        extra_config = config.get("extra_config", {})

        # Create provider based on type
        if provider_type == "openai":
            if not api_key:
                raise ProviderConfigurationError("OpenAI provider requires api_key")
            return OpenAIProvider(
                api_key=api_key,
                base_url=base_url or "https://api.openai.com/v1",
                default_model=default_model,
                organization=config.get("organization"),
                extra_config=extra_config,
            )

        if provider_type == "openai_compatible":
            if not base_url:
                raise ProviderConfigurationError("OpenAI-compatible provider requires base_url")
            return OpenAICompatibleProvider(
                base_url=base_url,
                api_key=api_key,
                default_model=default_model,
                extra_config=extra_config,
            )

        if provider_type == "ollama":
            return OllamaProvider(
                base_url=base_url or "http://localhost:11434",
                default_model=default_model,
                extra_config=extra_config,
            )

        if provider_type == "llamacpp":
            return LlamaCppProvider(
                base_url=base_url or "http://localhost:8080",
                default_model=default_model,
                extra_config=extra_config,
            )

        if provider_type == "zai":
            if not api_key:
                raise ProviderConfigurationError("Z.AI provider requires api_key")
            return ZAIProvider(
                api_key=api_key,
                base_url=base_url or "https://open.bigmodel.cn/api/paas/v4",
                default_model=default_model,
                extra_config=extra_config,
            )

        if provider_type == "minimax":
            if not api_key:
                raise ProviderConfigurationError("MiniMax provider requires api_key")
            # group_id can be at top level or inside extra_config
            group_id = config.get("group_id") or extra_config.get("group_id")
            if not group_id:
                raise ProviderConfigurationError("MiniMax provider requires group_id")
            return MiniMaxProvider(
                api_key=api_key,
                group_id=group_id,
                base_url=base_url or "https://api.minimax.chat/v1",
                default_model=default_model,
                extra_config=extra_config,
            )

        if provider_type == "lemonade":
            return LemonadeProvider(
                base_url=base_url or "http://localhost:5000",
                default_model=default_model,
                extra_config=extra_config,
            )

        # Fallback to generic instantiation for registered providers
        # This allows custom providers to be created dynamically
        return provider_class(
            base_url=base_url,
            api_key=api_key,
            default_model=default_model,
            extra_config=extra_config,
        )

    except TypeError as e:
        raise ProviderConfigurationError(f"Invalid configuration for {provider_type}: {e}") from e


def create_llm_provider_from_db_config(
    db_config: Any,
    api_key_decrypt_func: callable | None = None,
) -> LLMProviderBase:
    """
    Create an LLM provider instance from a database configuration model.

    Args:
        db_config: Database configuration model (LLMProvider from models.py)
        api_key_decrypt_func: Optional function to decrypt the API key

    Returns:
        An initialized LLM provider instance

    Example:
        provider = create_llm_provider_from_db_config(
            db_llm_provider,
            api_key_decrypt_func=decrypt_api_key
        )
    """
    config = {
        "base_url": db_config.base_url,
        "api_key": None,
        "default_model": db_config.default_model,
        "extra_config": db_config.extra_config or {},
    }

    # Decrypt API key if function provided and key exists
    if db_config.api_key_encrypted and api_key_decrypt_func:
        config["api_key"] = api_key_decrypt_func(db_config.api_key_encrypted)

    return create_llm_provider(db_config.provider_type, config)


def get_provider_info(provider_type: str) -> dict[str, Any]:
    """
    Get information about a provider type.

    Args:
        provider_type: The provider type identifier

    Returns:
        Dictionary with provider information
    """
    provider_class = get_provider_class(provider_type)

    # Create a temporary instance to get capabilities
    # (with minimal config to avoid errors)
    try:
        if provider_type == "openai":
            temp_provider = provider_class(api_key="temp", base_url="https://api.openai.com/v1")
        elif provider_type in ["ollama", "llamacpp", "lemonade", "openai_compatible"]:
            temp_provider = provider_class(base_url="http://localhost")
        elif provider_type == "zai":
            temp_provider = provider_class(api_key="temp")
        elif provider_type == "minimax":
            temp_provider = provider_class(api_key="temp", group_id="temp")
        else:
            temp_provider = provider_class()

        capabilities = temp_provider.capabilities

        return {
            "provider_type": provider_type,
            "class_name": provider_class.__name__,
            "supports_streaming": capabilities.supports_streaming,
            "supports_function_calling": capabilities.supports_function_calling,
            "supports_vision": capabilities.supports_vision,
            "supports_json_mode": capabilities.supports_json_mode,
            "max_context_length": capabilities.max_context_length,
            "max_output_tokens": capabilities.max_output_tokens,
        }
    except Exception as e:
        logger.warning("Failed to get provider info", provider_type=provider_type, error=str(e))
        return {
            "provider_type": provider_type,
            "class_name": provider_class.__name__,
            "error": str(e),
        }


def get_all_provider_info() -> list[dict[str, Any]]:
    """
    Get information about all available providers.

    Returns:
        List of provider information dictionaries
    """
    return [get_provider_info(pt) for pt in PROVIDER_REGISTRY]


# ---------------------------------------------------------------------------
# Provider caching with automatic refresh on config change
# ---------------------------------------------------------------------------


def _config_hash(provider_type: str, config: dict[str, Any]) -> str:
    """
    Deterministic SHA-256 hash of the provider config keys that affect
    which provider instance is returned.

    Sensitive fields (api_key) ARE included so that a rotated key triggers
    a refresh.  Only the *set* of key-value pairs matters; extra_config
    sub-keys are sorted for determinism.
    """
    # Build a stable dict: provider_type + all config values, sorted
    stable: dict[str, Any] = {"_type": provider_type}
    for k in sorted(config.keys()):
        v = config[k]
        # Normalise nested dicts so ordering doesn't matter
        if isinstance(v, dict):
            v = dict(sorted(v.items()))
        stable[k] = v
    raw = json.dumps(stable, sort_keys=True, default=str)
    return hashlib.sha256(raw.encode()).hexdigest()


class ProviderManager:
    """
    Thread-safe manager that caches LLM provider instances and
    transparently refreshes them when the configuration changes.

    Each unique ``(provider_type, config)`` pair is cached; when a caller
    requests the same pair but the underlying values have changed (e.g. an
    API key was rotated via env-var), the old provider is closed and a
    fresh instance is created.

    Usage::

        mgr = ProviderManager()
        provider = mgr.get_or_create("openai", {"api_key": key})
        # … later …
        # If key changed, provider is silently refreshed:
        provider = mgr.get_or_create("openai", {"api_key": os.getenv("OPENAI_API_KEY")})
    """

    def __init__(self) -> None:
        self._lock = threading.Lock()
        # (provider_type, config_hash) -> LLMProviderBase
        self._cache: dict[tuple[str, str], LLMProviderBase] = {}
        # config_hash -> config dict (kept for diagnostics)
        self._configs: dict[str, dict[str, Any]] = {}

    def get_or_create(
        self,
        provider_type: str,
        config: dict[str, Any],
    ) -> LLMProviderBase:
        """
        Return a cached provider or create a new one.

        If the config hash differs from the cached entry, the old provider
        is closed (async fire-and-forget) and a new one is built.

        Args:
            provider_type: Provider type identifier (e.g. ``"openai"``).
            config: Provider configuration dictionary.

        Returns:
            An initialised ``LLMProviderBase`` instance.
        """
        digest = _config_hash(provider_type, config)
        key = (provider_type, digest)

        with self._lock:
            if key in self._cache:
                logger.debug(
                    "provider_cache_hit",
                    provider_type=provider_type,
                    config_hash=digest[:12],
                )
                return self._cache[key]

        # Cache miss — build outside the lock to avoid holding it during I/O.
        provider = create_llm_provider(provider_type, config)

        with self._lock:
            # Double-check: another thread might have inserted while we built.
            if key in self._cache:
                # Discard the duplicate we just built.
                self._close_provider(provider)
                return self._cache[key]

            # Evict any stale entry for the same provider_type but different hash.
            stale_keys = [
                k for k in list(self._cache) if k[0] == provider_type and k[1] != digest
            ]
            for stale_key in stale_keys:
                old = self._cache.pop(stale_key)
                self._configs.pop(stale_key[1], None)
                self._close_provider(old)

            self._cache[key] = provider
            self._configs[digest] = config
            logger.info(
                "provider_created",
                provider_type=provider_type,
                config_hash=digest[:12],
                refreshed=bool(stale_keys),
            )
            return provider

    def refresh(self, provider_type: str, config: dict[str, Any]) -> LLMProviderBase:
        """
        Force-create a provider, replacing any cached entry for the type.

        Unlike ``get_or_create`` this always rebuilds, even if the hash
        matches — useful after explicit config edits.
        """
        digest = _config_hash(provider_type, config)
        key = (provider_type, digest)

        provider = create_llm_provider(provider_type, config)

        with self._lock:
            stale_keys = [k for k in list(self._cache) if k[0] == provider_type]
            for stale_key in stale_keys:
                old = self._cache.pop(stale_key)
                self._configs.pop(stale_key[1], None)
                self._close_provider(old)

            self._cache[key] = provider
            self._configs[digest] = config
            logger.info(
                "provider_force_refreshed",
                provider_type=provider_type,
                config_hash=digest[:12],
            )
        return provider

    def invalidate(self, provider_type: str | None = None) -> None:
        """
        Remove cached providers.

        Args:
            provider_type: If given, only evict entries for this type;
                           otherwise evict everything.
        """
        with self._lock:
            if provider_type is not None:
                stale_keys = [k for k in self._cache if k[0] == provider_type]
            else:
                stale_keys = list(self._cache.keys())

            for stale_key in stale_keys:
                old = self._cache.pop(stale_key)
                self._configs.pop(stale_key[1], None)
                self._close_provider(old)

        if stale_keys:
            logger.info(
                "provider_cache_invalidated",
                provider_type=provider_type or "*",
                count=len(stale_keys),
            )

    @property
    def cached_count(self) -> int:
        """Number of providers currently in the cache."""
        return len(self._cache)

    def cached_types(self) -> list[str]:
        """Provider types currently represented in the cache."""
        with self._lock:
            return list({k[0] for k in self._cache})

    # -- internal -----------------------------------------------------------

    @staticmethod
    def _close_provider(provider: LLMProviderBase) -> None:
        """Fire-and-forget close of an old provider instance."""
        import asyncio

        try:
            loop = asyncio.get_running_loop()
            loop.create_task(provider.close())  # type: ignore[union-attr]  # noqa: RUF006
        except RuntimeError:
            # No running loop — best-effort synchronous close.
            try:
                import anyio
                anyio.from_thread.run(provider.close)  # type: ignore[attr-defined]
            except Exception:
                logger.debug("Could not close stale provider synchronously")


# Module-level default manager for convenience.
default_provider_manager = ProviderManager()
