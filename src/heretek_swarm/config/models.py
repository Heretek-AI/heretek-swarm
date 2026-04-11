"""
Configuration Data Models

Pydantic models for configuration management in Heretek Swarm.
Provides validation, serialization, and type safety for configuration data.
"""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class ConfigType(StrEnum):
    """Configuration value types."""
    STRING = "string"
    INTEGER = "integer"
    FLOAT = "float"
    BOOLEAN = "boolean"
    JSON = "json"
    ARRAY = "array"


class HealthStatus(StrEnum):
    """Health status for providers."""
    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"
    DEGRADED = "degraded"


class LLMProviderType(StrEnum):
    """Supported LLM provider types."""
    OPENAI = "openai"
    OPENAI_COMPATIBLE = "openai_compatible"
    OLLAMA = "ollama"
    LLAMACPP = "llamacpp"
    ZAI = "zai"
    MINIMAX = "minimax"
    LEMONADE = "lemonade"


class EmbeddingProviderType(StrEnum):
    """Supported embedding provider types."""
    OPENAI = "openai"
    OPENAI_COMPATIBLE = "openai_compatible"
    OLLAMA = "ollama"
    LOCAL = "local"
    HUGGINGFACE = "huggingface"


# =============================================================================
# User Configuration Models
# =============================================================================

class UserConfiguration(BaseModel):
    """User-defined system configuration."""
    id: UUID = Field(default_factory=uuid4)
    config_key: str = Field(..., min_length=1, max_length=255)
    config_value: Any
    config_type: ConfigType = Field(default=ConfigType.STRING)
    description: str | None = None
    category: str = Field(default="general", max_length=100)
    is_sensitive: bool = Field(default=False)
    is_editable: bool = Field(default=True)
    validation_schema: dict[str, Any] | None = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    updated_by: str | None = None

    class Config:
        use_enum_values = True
        json_encoders = {
            UUID: str,
            datetime: lambda v: v.isoformat(),
        }


class UserConfigurationCreate(BaseModel):
    """Model for creating a new configuration."""
    config_key: str = Field(..., min_length=1, max_length=255)
    config_value: Any
    config_type: ConfigType = Field(default=ConfigType.STRING)
    description: str | None = None
    category: str = Field(default="general", max_length=100)
    is_sensitive: bool = Field(default=False)
    is_editable: bool = Field(default=True)
    validation_schema: dict[str, Any] | None = None


class UserConfigurationUpdate(BaseModel):
    """Model for updating a configuration."""
    config_value: Any | None = None
    description: str | None = None
    is_editable: bool | None = None
    updated_by: str | None = None


# =============================================================================
# LLM Provider Models
# =============================================================================

class LLMProvider(BaseModel):
    """LLM provider configuration."""
    id: UUID = Field(default_factory=uuid4)
    provider_name: str = Field(..., min_length=1, max_length=100)
    provider_type: LLMProviderType
    base_url: str = Field(..., min_length=1, max_length=500)
    api_key_hint: str | None = None
    default_model: str | None = None
    available_models: list[str] = Field(default_factory=list)
    model_aliases: dict[str, str] = Field(default_factory=dict)
    supports_streaming: bool = Field(default=True)
    supports_function_calling: bool = Field(default=False)
    supports_vision: bool = Field(default=False)
    max_tokens: int | None = None
    max_context_length: int | None = None
    rate_limit_requests_per_minute: int | None = None
    rate_limit_tokens_per_minute: int | None = None
    is_enabled: bool = Field(default=True)
    is_default: bool = Field(default=False)
    health_status: HealthStatus = Field(default=HealthStatus.UNKNOWN)
    last_health_check: datetime | None = None
    health_check_error: str | None = None
    priority: int = Field(default=100)
    extra_config: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        use_enum_values = True
        json_encoders = {
            UUID: str,
            datetime: lambda v: v.isoformat(),
        }


class LLMProviderCreate(BaseModel):
    """Model for creating a new LLM provider."""
    provider_name: str = Field(..., min_length=1, max_length=100)
    provider_type: LLMProviderType
    base_url: str = Field(..., min_length=1, max_length=500)
    api_key: str | None = Field(None, alias="api_key")
    api_key_hint: str | None = None
    default_model: str | None = None
    available_models: list[str] | None = None
    model_aliases: dict[str, str] | None = None
    supports_streaming: bool = Field(default=True)
    supports_function_calling: bool = Field(default=False)
    supports_vision: bool = Field(default=False)
    max_tokens: int | None = None
    max_context_length: int | None = None
    rate_limit_requests_per_minute: int | None = None
    rate_limit_tokens_per_minute: int | None = None
    is_enabled: bool = Field(default=True)
    is_default: bool = Field(default=False)
    priority: int = Field(default=100)
    extra_config: dict[str, Any] | None = None


class LLMProviderUpdate(BaseModel):
    """Model for updating an LLM provider."""
    base_url: str | None = None
    api_key: str | None = None
    api_key_hint: str | None = None
    default_model: str | None = None
    available_models: list[str] | None = None
    model_aliases: dict[str, str] | None = None
    supports_streaming: bool | None = None
    supports_function_calling: bool | None = None
    supports_vision: bool | None = None
    max_tokens: int | None = None
    max_context_length: int | None = None
    rate_limit_requests_per_minute: int | None = None
    rate_limit_tokens_per_minute: int | None = None
    is_enabled: bool | None = None
    is_default: bool | None = None
    priority: int | None = None
    extra_config: dict[str, Any] | None = None


class LLMProviderTestRequest(BaseModel):
    """Request model for testing LLM provider connectivity."""
    prompt: str = Field(default="Hello, this is a connectivity test.", max_length=500)
    model: str | None = None
    max_tokens: int = Field(default=10, ge=1, le=100)


class LLMProviderTestResponse(BaseModel):
    """Response model for LLM provider connectivity test."""
    success: bool
    provider_name: str
    model_used: str
    response_text: str | None = None
    latency_ms: float
    error: str | None = None


# =============================================================================
# Embedding Provider Models
# =============================================================================

class EmbeddingProvider(BaseModel):
    """Embedding provider configuration."""
    id: UUID = Field(default_factory=uuid4)
    provider_name: str = Field(..., min_length=1, max_length=100)
    provider_type: EmbeddingProviderType
    base_url: str = Field(..., min_length=1, max_length=500)
    api_key_hint: str | None = None
    default_model: str | None = None
    available_models: list[str] = Field(default_factory=list)
    embedding_dimensions: int | None = None
    supported_input_formats: list[str] = Field(default=["text"])
    max_batch_size: int = Field(default=32)
    max_tokens_per_batch: int = Field(default=8192)
    is_enabled: bool = Field(default=True)
    is_default: bool = Field(default=False)
    health_status: HealthStatus = Field(default=HealthStatus.UNKNOWN)
    last_health_check: datetime | None = None
    health_check_error: str | None = None
    priority: int = Field(default=100)
    extra_config: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        use_enum_values = True
        json_encoders = {
            UUID: str,
            datetime: lambda v: v.isoformat(),
        }


class EmbeddingProviderCreate(BaseModel):
    """Model for creating a new embedding provider."""
    provider_name: str = Field(..., min_length=1, max_length=100)
    provider_type: EmbeddingProviderType
    base_url: str = Field(..., min_length=1, max_length=500)
    api_key: str | None = Field(None, alias="api_key")
    api_key_hint: str | None = None
    default_model: str | None = None
    available_models: list[str] | None = None
    embedding_dimensions: int | None = None
    supported_input_formats: list[str] | None = None
    max_batch_size: int = Field(default=32)
    max_tokens_per_batch: int = Field(default=8192)
    is_enabled: bool = Field(default=True)
    is_default: bool = Field(default=False)
    priority: int = Field(default=100)
    extra_config: dict[str, Any] | None = None


class EmbeddingProviderUpdate(BaseModel):
    """Model for updating an embedding provider."""
    base_url: str | None = None
    api_key: str | None = None
    api_key_hint: str | None = None
    default_model: str | None = None
    available_models: list[str] | None = None
    embedding_dimensions: int | None = None
    supported_input_formats: list[str] | None = None
    max_batch_size: int | None = None
    max_tokens_per_batch: int | None = None
    is_enabled: bool | None = None
    is_default: bool | None = None
    priority: int | None = None
    extra_config: dict[str, Any] | None = None


class EmbeddingProviderTestRequest(BaseModel):
    """Request model for testing embedding provider connectivity."""
    text: str = Field(default="This is a test sentence for embedding.", max_length=1000)
    model: str | None = None


class EmbeddingProviderTestResponse(BaseModel):
    """Response model for embedding provider connectivity test."""
    success: bool
    provider_name: str
    model_used: str
    dimensions: int | None = None
    latency_ms: float
    error: str | None = None


# =============================================================================
# Agent Configuration Models
# =============================================================================

class AgentConfig(BaseModel):
    """Per-agent configuration."""
    id: UUID = Field(default_factory=uuid4)
    agent_type: str = Field(..., min_length=1, max_length=100)
    agent_id: str | None = None
    config_name: str = Field(..., min_length=1, max_length=255)
    config_data: dict[str, Any] = Field(default_factory=dict)
    llm_provider_id: UUID | None = None
    embedding_provider_id: UUID | None = None
    is_active: bool = Field(default=True)
    is_default_for_type: bool = Field(default=False)
    description: str | None = None
    tags: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: str | None = None
    updated_by: str | None = None

    class Config:
        use_enum_values = True
        json_encoders = {
            UUID: str,
            datetime: lambda v: v.isoformat(),
        }


class AgentConfigCreate(BaseModel):
    """Model for creating a new agent configuration."""
    agent_type: str = Field(..., min_length=1, max_length=100)
    agent_id: str | None = None
    config_name: str = Field(..., min_length=1, max_length=255)
    config_data: dict[str, Any] = Field(default_factory=dict)
    llm_provider_id: UUID | None = None
    embedding_provider_id: UUID | None = None
    is_active: bool = Field(default=True)
    is_default_for_type: bool = Field(default=False)
    description: str | None = None
    tags: list[str] | None = None


class AgentConfigUpdate(BaseModel):
    """Model for updating an agent configuration."""
    config_name: str | None = None
    config_data: dict[str, Any] | None = None
    llm_provider_id: UUID | None = None
    embedding_provider_id: UUID | None = None
    is_active: bool | None = None
    is_default_for_type: bool | None = None
    description: str | None = None
    tags: list[str] | None = None


# =============================================================================
# Audit Log Models
# =============================================================================

class ConfigAuditLog(BaseModel):
    """Configuration change audit log entry."""
    id: UUID = Field(default_factory=uuid4)
    entity_type: str
    entity_id: UUID
    action: str
    old_value: dict[str, Any] | None = None
    new_value: dict[str, Any] | None = None
    changed_fields: list[str] | None = None
    changed_by: str | None = None
    change_reason: str | None = None
    ip_address: str | None = None
    changed_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_encoders = {
            UUID: str,
            datetime: lambda v: v.isoformat(),
        }


# =============================================================================
# Cache Models
# =============================================================================

class ConfigCacheEntry(BaseModel):
    """Configuration cache entry."""
    cache_key: str
    cache_value: dict[str, Any]
    expires_at: datetime | None = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    access_count: int = Field(default=0)
    last_accessed_at: datetime = Field(default_factory=datetime.utcnow)


# =============================================================================
# Import/Export Models
# =============================================================================

class ConfigurationExport(BaseModel):
    """Exported configuration bundle."""
    version: str = "1.0"
    exported_at: datetime = Field(default_factory=datetime.utcnow)
    exported_by: str | None = None
    user_configurations: list[UserConfiguration] = Field(default_factory=list)
    llm_providers: list[LLMProvider] = Field(default_factory=list)
    embedding_providers: list[EmbeddingProvider] = Field(default_factory=list)
    agent_configs: list[AgentConfig] = Field(default_factory=list)


class ConfigurationImport(BaseModel):
    """Imported configuration bundle."""
    version: str
    user_configurations: list[dict[str, Any]] | None = None
    llm_providers: list[dict[str, Any]] | None = None
    embedding_providers: list[dict[str, Any]] | None = None
    agent_configs: list[dict[str, Any]] | None = None


class ImportOptions(BaseModel):
    """Options for configuration import."""
    overwrite_existing: bool = Field(default=False)
    skip_conflicts: bool = Field(default=True)
    import_user_configs: bool = Field(default=True)
    import_llm_providers: bool = Field(default=True)
    import_embedding_providers: bool = Field(default=True)
    import_agent_configs: bool = Field(default=True)


class ImportResult(BaseModel):
    """Result of configuration import."""
    success: bool
    imported_count: dict[str, int] = Field(default_factory=dict)
    skipped_count: dict[str, int] = Field(default_factory=dict)
    error_count: dict[str, int] = Field(default_factory=dict)
    errors: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
