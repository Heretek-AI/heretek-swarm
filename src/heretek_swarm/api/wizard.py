"""
Configuration Wizard API Endpoints

HTTP endpoints for the Zero-Touch Configuration Wizard.
Provides a guided setup flow for LLM providers, API keys, and system parameters.

Tenet #1: "Zero-Touch Configuration (Wizard-First)"
"""

from __future__ import annotations

from typing import Any

import structlog
from fastapi import APIRouter, HTTPException

from heretek_swarm.config.models import (
    LLMProviderCreate,
    LLMProviderType,
)
from heretek_swarm.config.service import (
    ConfigurationService,
    get_config_service,
)

logger = structlog.get_logger("api.wizard")

router = APIRouter(prefix="/api/wizard", tags=["Configuration Wizard"])


# =============================================================================
# Available Providers Definition
# =============================================================================

AVAILABLE_PROVIDERS = {
    "anthropic": {
        "id": "anthropic",
        "name": "Anthropic Claude",
        "type": "anthropic",
        "icon": "brain",
        "description": "Claude models via Anthropic's API",
        "default_model": "claude-sonnet-4-20250514",
        "supports_streaming": True,
        "supports_function_calling": True,
        "supports_vision": True,
        "requires_api_key": True,
        "api_key_label": "Anthropic API Key",
        "api_key_env_var": "ANTHROPIC_API_KEY",
        "base_url": "https://api.anthropic.com",
        "color": "#ff6b35",
    },
    "openai": {
        "id": "openai",
        "name": "OpenAI",
        "type": "openai",
        "icon": "sparkles",
        "description": "GPT models via OpenAI's API",
        "default_model": "gpt-4o",
        "supports_streaming": True,
        "supports_function_calling": True,
        "supports_vision": True,
        "requires_api_key": True,
        "api_key_label": "OpenAI API Key",
        "api_key_env_var": "OPENAI_API_KEY",
        "base_url": "https://api.openai.com/v1",
        "color": "#10a37f",
    },
    "ollama": {
        "id": "ollama",
        "name": "Ollama",
        "type": "ollama",
        "icon": "cpu",
        "description": "Local LLM inference with Ollama",
        "default_model": "llama3.2",
        "supports_streaming": True,
        "supports_function_calling": False,
        "supports_vision": False,
        "requires_api_key": False,
        "api_key_label": "Ollama API Key (optional)",
        "api_key_env_var": "OLLAMA_API_KEY",
        "base_url": "http://localhost:11434",
        "color": "#ff6b9d",
    },
    "groq": {
        "id": "groq",
        "name": "Groq",
        "type": "openai_compatible",
        "icon": "zap",
        "description": "Fast inference via Groq's API",
        "default_model": "llama-3.3-70b-versatile",
        "supports_streaming": True,
        "supports_function_calling": True,
        "supports_vision": False,
        "requires_api_key": True,
        "api_key_label": "Groq API Key",
        "api_key_env_var": "GROQ_API_KEY",
        "base_url": "https://api.groq.com/openai/v1",
        "color": "#fb5a47",
    },
    "mistral": {
        "id": "mistral",
        "name": "Mistral AI",
        "type": "openai_compatible",
        "icon": "cloud",
        "description": "Mistral models via Mistral's API",
        "default_model": "mistral-large-latest",
        "supports_streaming": True,
        "supports_function_calling": True,
        "supports_vision": False,
        "requires_api_key": True,
        "api_key_label": "Mistral API Key",
        "api_key_env_var": "MISTRAL_API_KEY",
        "base_url": "https://api.mistral.ai/v1",
        "color": "#d636f8",
    },
    "deepseek": {
        "id": "deepseek",
        "name": "DeepSeek",
        "type": "openai_compatible",
        "icon": "fish",
        "description": "DeepSeek V3 and Coder models",
        "default_model": "deepseek-chat",
        "supports_streaming": True,
        "supports_function_calling": True,
        "supports_vision": False,
        "requires_api_key": True,
        "api_key_label": "DeepSeek API Key",
        "api_key_env_var": "DEEPSEEK_API_KEY",
        "base_url": "https://api.deepseek.com",
        "color": "#4ade80",
    },
    "local": {
        "id": "local",
        "name": "Local / LiteLLM",
        "type": "openai_compatible",
        "icon": "server",
        "description": "Local models via LiteLLM proxy",
        "default_model": "gpt-3.5-turbo",
        "supports_streaming": True,
        "supports_function_calling": True,
        "supports_vision": False,
        "requires_api_key": False,
        "api_key_label": "LiteLLM API Key (optional)",
        "api_key_env_var": "LITELLM_API_KEY",
        "base_url": "http://localhost:4000",
        "color": "#60a5fa",
    },
}

# Agent tier configurations
AGENT_TIERS = {
    "minimal": {
        "id": "minimal",
        "name": "Minimal",
        "description": "Single agent for basic tasks",
        "agent_count": 1,
        "agents": ["coordinator"],
        "memory_enabled": False,
        "consciousness_enabled": False,
    },
    "standard": {
        "id": "standard",
        "name": "Standard",
        "description": "Multi-agent swarm for collaborative work",
        "agent_count": 5,
        "agents": ["coordinator", "coder", "examiner", "historian", "catalyst"],
        "memory_enabled": True,
        "consciousness_enabled": False,
    },
    "enhanced": {
        "id": "enhanced",
        "name": "Enhanced",
        "description": "Full swarm with memory and coordination",
        "agent_count": 11,
        "agents": [
            "coordinator", "coder", "examiner", "historian", "catalyst",
            "explorer", "dreamer", "echo", "metis", "nexus", "arbiter",
        ],
        "memory_enabled": True,
        "consciousness_enabled": True,
    },
    "maximal": {
        "id": "maximal",
        "name": "Maximal",
        "description": "Complete 23-agent collective with full capabilities",
        "agent_count": 23,
        "agents": [
            "alpha", "beta", "charlie", "coordinator", "coder", "examiner",
            "historian", "catalyst", "explorer", "dreamer", "echo", "metis",
            "nexus", "arbiter", "prism", "perceiver", "perceiver_plus",
            "steward", "sentinel", "sentinel_prime", "triad", "handoff",
            "validation",
        ],
        "memory_enabled": True,
        "consciousness_enabled": True,
    },
}


# =============================================================================
# Wizard State Management
# =============================================================================

class WizardState:
    """In-memory wizard state (would be Redis/DB in production)."""

    def __init__(self):
        self._providers: dict[str, dict[str, Any]] = {}
        self._config: dict[str, Any] = {}
        self._completed: bool = False

    def set_provider_config(self, provider_id: str, config: dict[str, Any]) -> None:
        """Store provider configuration."""
        self._providers[provider_id] = config

    def get_provider_config(self, provider_id: str) -> dict[str, Any] | None:
        """Get provider configuration."""
        return self._providers.get(provider_id)

    def get_all_providers(self) -> dict[str, dict[str, Any]]:
        """Get all configured providers."""
        return self._providers.copy()

    def set_wizard_config(self, config: dict[str, Any]) -> None:
        """Store wizard configuration."""
        self._config.update(config)

    def get_wizard_config(self) -> dict[str, Any]:
        """Get wizard configuration."""
        return self._config.copy()

    def set_completed(self, completed: bool) -> None:
        """Set wizard completion status."""
        self._completed = completed

    def is_completed(self) -> bool:
        """Check if wizard was completed."""
        return self._completed

    def clear(self) -> None:
        """Clear all wizard state."""
        self._providers.clear()
        self._config.clear()
        self._completed = False


# Global wizard state instance
_wizard_state = WizardState()


# =============================================================================
# Helper Functions
# =============================================================================

def get_service() -> ConfigurationService:
    """Dependency injection for ConfigurationService."""
    return get_config_service()


def get_wizard_state() -> WizardState:
    """Get the wizard state instance."""
    return _wizard_state


# =============================================================================
# Provider Endpoints
# =============================================================================

@router.get("/providers")
async def list_providers() -> dict[str, Any]:
    """
    List available LLM providers for the wizard.

    Returns:
        Available providers with their capabilities
    """
    return {
        "providers": list(AVAILABLE_PROVIDERS.values()),
        "total": len(AVAILABLE_PROVIDERS),
    }


@router.get("/providers/{provider_id}")
async def get_provider(provider_id: str) -> dict[str, Any]:
    """
    Get details for a specific provider.

    Args:
        provider_id: Provider identifier

    Returns:
        Provider details
    """
    if provider_id not in AVAILABLE_PROVIDERS:
        raise HTTPException(404, f"Provider '{provider_id}' not found")

    return AVAILABLE_PROVIDERS[provider_id]


# =============================================================================
# Agent Tier Endpoints
# =============================================================================

@router.get("/tiers")
async def list_tiers() -> dict[str, Any]:
    """
    List available agent tier configurations.

    Returns:
        Available tiers with agent counts and capabilities
    """
    return {
        "tiers": list(AGENT_TIERS.values()),
        "total": len(AGENT_TIERS),
    }


@router.get("/tiers/{tier_id}")
async def get_tier(tier_id: str) -> dict[str, Any]:
    """
    Get details for a specific agent tier.

    Args:
        tier_id: Tier identifier

    Returns:
        Tier details
    """
    if tier_id not in AGENT_TIERS:
        raise HTTPException(404, f"Tier '{tier_id}' not found")

    return AGENT_TIERS[tier_id]


# =============================================================================
# Config Status Endpoint
# =============================================================================

@router.get("/config")
async def get_config_status() -> dict[str, Any]:
    """
    Get current configuration status.

    Returns:
        What's configured vs what needs setup
    """
    wizard_state = get_wizard_state()
    service = get_service()

    # Check what's already configured in the database
    configured_providers = []
    try:
        providers = await service.list_llm_providers(enabled_only=False)
        configured_providers = [
            {
                "id": str(p.id),
                "name": p.provider_name,
                "type": p.provider_type,
                "is_enabled": p.is_enabled,
                "is_default": p.is_default,
            }
            for p in providers
        ]
    except Exception as e:
        logger.warning("Failed to list providers", error=str(e))

    # Check system configuration
    system_config = {}
    try:
        db_url = await service.get_config_value("database.url")
        redis_url = await service.get_config_value("redis.url")
        qdrant_url = await service.get_config_value("qdrant.url")

        system_config = {
            "database": bool(db_url),
            "redis": bool(redis_url),
            "qdrant": bool(qdrant_url),
        }
    except Exception as e:
        logger.warning("Failed to get system config", error=str(e))

    return {
        "wizard_completed": wizard_state.is_completed(),
        "wizard_state": {
            "providers_configured": list(wizard_state.get_all_providers().keys()),
            "config": wizard_state.get_wizard_config(),
        },
        "database_configured": {
            "providers": configured_providers,
            "total_providers": len(configured_providers),
        },
        "system_config": system_config,
        "needs_setup": {
            "providers": len(configured_providers) == 0,
            "agents": True,  # Always needs setup initially
            "api_keys": any(p.get("requires_api_key") for p in AVAILABLE_PROVIDERS.values()),
        },
    }


# =============================================================================
# Validation Error Messages (Constants)
# =============================================================================

API_KEY_REQUIRED = API_KEY_REQUIRED
CONNECTION_TIMED_OUT = CONNECTION_TIMED_OUT
CONNECTION_FAILED = "Connection failed: {error}"
INVALID_API_KEY = INVALID_API_KEY
LITE_LLM_NOT_HEALTHY = "LiteLLM proxy not healthy"
OLLAMA_NOT_RUNNING = OLLAMA_NOT_RUNNING
UNKNOWN_PROVIDER_TYPE = "Unknown provider type"
VALIDATION_FAILED = "Validation failed: {error}"


# =============================================================================
# Provider Validation Dispatch
# =============================================================================

async def _dispatch_validation(
    provider_id: str,
    api_key: str | None,
    base_url: str,
) -> dict[str, Any]:
    """
    Dispatch to the appropriate validator based on provider type.

    Args:
        provider_id: Provider identifier
        api_key: API key to validate
        base_url: Base URL for the provider

    Returns:
        Validation result
    """
    validators = {
        "anthropic": _validate_anthropic,
        "openai": _validate_openai,
        "ollama": _validate_ollama,
        "groq": _validate_groq,
        "mistral": _validate_mistral,
        "deepseek": _validate_deepseek,
        "local": _validate_local,
    }

    validator = validators.get(provider_id)
    if validator:
        return await validator(api_key, base_url)
    return {"valid": False, "error": UNKNOWN_PROVIDER_TYPE}


# =============================================================================
# Validation Endpoint
# =============================================================================

@router.post("/validate")
async def validate_credentials(
    provider_id: str,
    api_key: str | None = None,
    base_url: str | None = None,
) -> dict[str, Any]:
    """
    Validate provider credentials before saving.

    Args:
        provider_id: Provider to validate
        api_key: API key to validate (optional for some providers)
        base_url: Base URL override (optional)

    Returns:
        Validation result
    """
    if provider_id not in AVAILABLE_PROVIDERS:
        raise HTTPException(404, f"Provider '{provider_id}' not found")

    provider = AVAILABLE_PROVIDERS[provider_id]

    # Check if API key is required
    if provider["requires_api_key"] and not api_key:
        return {
            "valid": False,
            "error": f"{provider['api_key_label']} is required",
            "provider_id": provider_id,
        }

    # Perform validation via dispatch
    try:
        result = await _dispatch_validation(
            provider_id, api_key, base_url or provider["base_url"]
        )
        result["provider_id"] = provider_id
        return result
    except Exception as e:
        logger.error("Provider validation failed", provider=provider_id, error=str(e))
        return {
            "valid": False,
            "error": VALIDATION_FAILED.format(error=str(e)),
            "provider_id": provider_id,
        }


async def _validate_anthropic(api_key: str | None, base_url: str) -> dict[str, Any]:
    """Validate Anthropic API key."""
    import httpx

    if not api_key:
        return {"valid": False, "error": API_KEY_REQUIRED}

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{base_url}/v1/messages",
                headers={
                    "x-api-key": api_key,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json",
                },
                json={
                    "model": "claude-sonnet-4-20250514",
                    "max_tokens": 10,
                    "messages": [{"role": "user", "content": "hi"}],
                },
                timeout=10.0,
            )

            if response.status_code == 200:
                return {
                    "valid": True,
                    "provider_id": "anthropic",
                    "message": "API key is valid",
                }
            error_data = response.json() if response.text else {}
            error_msg = (
                error_data.get("error", {}).get("message", response.text) or INVALID_API_KEY
            )
            return {"valid": False, "error": error_msg}
    except httpx.TimeoutException:
        return {"valid": False, "error": CONNECTION_TIMED_OUT}
    except Exception as e:
        return {"valid": False, "error": f"Connection failed: {e!s}"}


async def _validate_openai(api_key: str | None, base_url: str) -> dict[str, Any]:
    """Validate OpenAI API key."""
    import httpx

    if not api_key:
        return {"valid": False, "error": API_KEY_REQUIRED}

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{base_url}/models",
                headers={"Authorization": f"Bearer {api_key}"},
                timeout=10.0,
            )

            if response.status_code == 200:
                return {
                    "valid": True,
                    "provider_id": "openai",
                    "message": "API key is valid",
                }
            return {"valid": False, "error": INVALID_API_KEY}
    except httpx.TimeoutException:
        return {"valid": False, "error": CONNECTION_TIMED_OUT}
    except Exception as e:
        return {"valid": False, "error": f"Connection failed: {e!s}"}


async def _validate_ollama(api_key: str | None, base_url: str) -> dict[str, Any]:
    """Validate Ollama connection."""
    import httpx

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{base_url}/api/tags", timeout=10.0)

            if response.status_code == 200:
                models = response.json().get("models", [])
                model_names = [m.get("name") for m in models[:5]]
                return {
                    "valid": True,
                    "provider_id": "ollama",
                    "message": f"Connected. Available models: {', '.join(model_names) or 'none'}",
                    "available_models": model_names,
                }
            return {"valid": False, "error": "Failed to connect to Ollama"}
    except httpx.TimeoutException:
        return {"valid": False, "error": OLLAMA_NOT_RUNNING}
    except Exception as e:
        return {"valid": False, "error": f"Connection failed: {e!s}"}


async def _validate_groq(api_key: str | None, base_url: str) -> dict[str, Any]:
    """Validate Groq API key."""
    import httpx

    if not api_key:
        return {"valid": False, "error": API_KEY_REQUIRED}

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "content-type": "application/json",
                },
                json={
                    "model": "llama-3.3-70b-versatile",
                    "messages": [{"role": "user", "content": "hi"}],
                    "max_tokens": 5,
                },
                timeout=10.0,
            )

            if response.status_code == 200:
                return {
                    "valid": True,
                    "provider_id": "groq",
                    "message": "API key is valid",
                }
            return {"valid": False, "error": INVALID_API_KEY}
    except httpx.TimeoutException:
        return {"valid": False, "error": CONNECTION_TIMED_OUT}
    except Exception as e:
        return {"valid": False, "error": f"Connection failed: {e!s}"}


async def _validate_mistral(api_key: str | None, base_url: str) -> dict[str, Any]:
    """Validate Mistral API key."""
    import httpx

    if not api_key:
        return {"valid": False, "error": API_KEY_REQUIRED}

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "content-type": "application/json",
                },
                json={
                    "model": "mistral-small-latest",
                    "messages": [{"role": "user", "content": "hi"}],
                    "max_tokens": 5,
                },
                timeout=10.0,
            )

            if response.status_code == 200:
                return {
                    "valid": True,
                    "provider_id": "mistral",
                    "message": "API key is valid",
                }
            return {"valid": False, "error": INVALID_API_KEY}
    except httpx.TimeoutException:
        return {"valid": False, "error": CONNECTION_TIMED_OUT}
    except Exception as e:
        return {"valid": False, "error": f"Connection failed: {e!s}"}


async def _validate_deepseek(api_key: str | None, base_url: str) -> dict[str, Any]:
    """Validate DeepSeek API key."""
    import httpx

    if not api_key:
        return {"valid": False, "error": API_KEY_REQUIRED}

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "content-type": "application/json",
                },
                json={
                    "model": "deepseek-chat",
                    "messages": [{"role": "user", "content": "hi"}],
                    "max_tokens": 5,
                },
                timeout=10.0,
            )

            if response.status_code == 200:
                return {
                    "valid": True,
                    "provider_id": "deepseek",
                    "message": "API key is valid",
                }
            return {"valid": False, "error": INVALID_API_KEY}
    except httpx.TimeoutException:
        return {"valid": False, "error": CONNECTION_TIMED_OUT}
    except Exception as e:
        return {"valid": False, "error": f"Connection failed: {e!s}"}


async def _validate_local(base_url: str, api_key: str | None) -> dict[str, Any]:
    """Validate local/LiteLLM connection."""
    import httpx

    try:
        async with httpx.AsyncClient() as client:
            headers = {}
            if api_key:
                headers["Authorization"] = f"Bearer {api_key}"

            response = await client.get(f"{base_url}/health", headers=headers, timeout=10.0)

            if response.status_code == 200:
                return {
                    "valid": True,
                    "provider_id": "local",
                    "message": "LiteLLM proxy is healthy",
                }
            return {"valid": False, "error": "LiteLLM proxy not healthy"}
    except httpx.TimeoutException:
        return {"valid": False, "error": "Connection timed out - is LiteLLM running?"}
    except Exception as e:
        return {"valid": False, "error": f"Connection failed: {e!s}"}


# =============================================================================
# Configuration Submission Endpoint
# =============================================================================

@router.post("/config")
async def submit_config(config: dict[str, Any]) -> dict[str, Any]:
    """
    Submit wizard configuration.

    This creates LLM providers, sets system configuration, and
    initializes the agent swarm based on the selected tier.

    Args:
        config: Wizard configuration containing:
            - providers: List of provider configs with api_key, model preferences
            - tier: Selected agent tier
            - preferences: Model preferences and settings

    Returns:
        Configuration result with created resources
    """
    wizard_state = get_wizard_state()
    service = get_service()

    result = {
        "success": True,
        "providers_created": [],
        "config": {},
        "errors": [],
    }

    # Process each provider configuration
    providers = config.get("providers", [])
    for provider_config in providers:
        provider_id = provider_config.get("provider_id")
        api_key = provider_config.get("api_key")
        model = (
            provider_config.get("model")
            or AVAILABLE_PROVIDERS.get(provider_id, {}).get("default_model")
        )
        is_default = provider_config.get("is_default", False)

        if not provider_id or provider_id not in AVAILABLE_PROVIDERS:
            result["errors"].append(f"Invalid provider: {provider_id}")
            continue

        provider_info = AVAILABLE_PROVIDERS[provider_id]

        try:
            # Map provider type
            provider_type_map = {
                "anthropic": LLMProviderType.OPENAI_COMPATIBLE,
                "openai": LLMProviderType.OPENAI,
                "ollama": LLMProviderType.OLLAMA,
                "groq": LLMProviderType.OPENAI_COMPATIBLE,
                "mistral": LLMProviderType.OPENAI_COMPATIBLE,
                "deepseek": LLMProviderType.OPENAI_COMPATIBLE,
                "local": LLMProviderType.OPENAI_COMPATIBLE,
            }

            llm_provider_type = provider_type_map.get(
                provider_id, LLMProviderType.OPENAI_COMPATIBLE
            )

            # Create LLM provider
            create_data = LLMProviderCreate(
                provider_name=provider_info["name"],
                provider_type=llm_provider_type,
                base_url=provider_config.get("base_url") or provider_info["base_url"],
                api_key=api_key,
                api_key_hint=f"***{api_key[-4:]}" if api_key else None,
                default_model=model,
                is_enabled=True,
                is_default=is_default,
                supports_streaming=provider_info.get("supports_streaming", True),
                supports_function_calling=provider_info.get("supports_function_calling", False),
                supports_vision=provider_info.get("supports_vision", False),
                extra_config=provider_config.get("extra_config", {}),
            )

            created = await service.create_llm_provider(create_data, changed_by="wizard")

            result["providers_created"].append({
                "id": str(created.id),
                "name": created.provider_name,
                "type": created.provider_type,
                "model": created.default_model,
            })

            # Store in wizard state
            wizard_state.set_provider_config(provider_id, {
                "provider_id": str(created.id),
                "model": model,
                "api_key_provided": bool(api_key),
            })

        except Exception as e:
            logger.error("Failed to create provider", provider=provider_id, error=str(e))
            result["errors"].append(f"Failed to create {provider_info['name']}: {e!s}")

    # Store tier configuration
    tier_id = config.get("tier", "standard")
    if tier_id in AGENT_TIERS:
        tier_config = AGENT_TIERS[tier_id]
        wizard_state.set_wizard_config({
            "tier": tier_id,
            "agent_count": tier_config["agent_count"],
            "agents": tier_config["agents"],
            "memory_enabled": tier_config["memory_enabled"],
            "consciousness_enabled": tier_config["consciousness_enabled"],
        })

        result["config"]["tier"] = tier_id
        result["config"]["agent_count"] = tier_config["agent_count"]

    # Store preferences
    preferences = config.get("preferences", {})
    wizard_state.set_wizard_config({"preferences": preferences})

    # Mark wizard as completed
    wizard_state.set_completed(True)

    result["success"] = len(result["errors"]) == 0

    logger.info("Wizard configuration submitted", result=result)

    return result


# =============================================================================
# Reset Endpoint
# =============================================================================

@router.post("/reset")
async def reset_wizard() -> dict[str, Any]:
    """
    Reset wizard state to allow reconfiguration.

    Returns:
        Reset confirmation
    """
    wizard_state = get_wizard_state()
    wizard_state.clear()

    logger.info("Wizard state reset")

    return {
        "success": True,
        "message": "Wizard state has been reset",
    }
