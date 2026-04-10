"""
Configuration Data Models

Pydantic models for configuration management in Heretek Swarm.
Provides validation, serialization, and type safety for configuration data.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class ConfigType(str, Enum):
    """Configuration value types."""
    STRING = "string"
    INTEGER = "integer"
    FLOAT = "float"
    BOOLEAN = "boolean"
    JSON = "json"
    ARRAY = "array"


class HealthStatus(str, Enum):
    """Health status for providers."""
    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"
    DEGRADED = "degraded"


class LLMProviderType(str, Enum):
    """Supported LLM provider types."""
    OPENAI = "openai"
    OPENAI_COMPATIBLE = "openai_compatible"
    OLLAMA = "ollama"
    LLAMACPP = "llamacpp"
    ZAI = "zai"
    MINIMAX = "minimax"
    LEMONADE = "lemonade"


class EmbeddingProviderType(str, Enum):
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
    description: Optional[str] = None
    category: str = Field(default="general", max_length=100)
    is_sensitive: bool = Field(default=False)
    is_editable: bool = Field(default=True)
    validation_schema: Optional[Dict[str, Any]] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    updated_by: Optional[str] = None

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
    description: Optional[str] = None
    category: str = Field(default="general", max_length=100)
    is_sensitive: bool = Field(default=False)
    is_editable: bool = Field(default=True)
    validation_schema: Optional[Dict[str, Any]] = None


class UserConfigurationUpdate(BaseModel):
    """Model for updating a configuration."""
    config_value: Optional[Any] = None
    description: Optional[str] = None
    is_editable: Optional[bool] = None
    updated_by: Optional[str] = None


# =============================================================================
# LLM Provider Models
# =============================================================================

class LLMProvider(BaseModel):
    """LLM provider configuration."""
    id: UUID = Field(default_factory=uuid4)
    provider_name: str = Field(..., min_length=1, max_length=100)
    provider_type: LLMProviderType
    base_url: str = Field(..., min_length=1, max_length=500)
    api_key_hint: Optional[str] = None
    default_model: Optional[str] = None
    available_models: List[str] = Field(default_factory=list)
    model_aliases: Dict[str, str] = Field(default_factory=dict)
    supports_streaming: bool = Field(default=True)
    supports_function_calling: bool = Field(default=False)
    supports_vision: bool = Field(default=False)
    max_tokens: Optional[int] = None
    max_context_length: Optional[int] = None
    rate_limit_requests_per_minute: Optional[int] = None
    rate_limit_tokens_per_minute: Optional[int] = None
    is_enabled: bool = Field(default=True)
    is_default: bool = Field(default=False)
    health_status: HealthStatus = Field(default=HealthStatus.UNKNOWN)
    last_health_check: Optional[datetime] = None
    health_check_error: Optional[str] = None
    priority: int = Field(default=100)
    extra_config: Dict[str, Any] = Field(default_factory=dict)
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
    api_key: Optional[str] = Field(None, alias="api_key")
    api_key_hint: Optional[str] = None
    default_model: Optional[str] = None
    available_models: Optional[List[str]] = None
    model_aliases: Optional[Dict[str, str]] = None
    supports_streaming: bool = Field(default=True)
    supports_function_calling: bool = Field(default=False)
    supports_vision: bool = Field(default=False)
    max_tokens: Optional[int] = None
    max_context_length: Optional[int] = None
    rate_limit_requests_per_minute: Optional[int] = None
    rate_limit_tokens_per_minute: Optional[int] = None
    is_enabled: bool = Field(default=True)
    is_default: bool = Field(default=False)
    priority: int = Field(default=100)
    extra_config: Optional[Dict[str, Any]] = None


class LLMProviderUpdate(BaseModel):
    """Model for updating an LLM provider."""
    base_url: Optional[str] = None
    api_key: Optional[str] = None
    api_key_hint: Optional[str] = None
    default_model: Optional[str] = None
    available_models: Optional[List[str]] = None
    model_aliases: Optional[Dict[str, str]] = None
    supports_streaming: Optional[bool] = None
    supports_function_calling: Optional[bool] = None
    supports_vision: Optional[bool] = None
    max_tokens: Optional[int] = None
    max_context_length: Optional[int] = None
    rate_limit_requests_per_minute: Optional[int] = None
    rate_limit_tokens_per_minute: Optional[int] = None
    is_enabled: Optional[bool] = None
    is_default: Optional[bool] = None
    priority: Optional[int] = None
    extra_config: Optional[Dict[str, Any]] = None


class LLMProviderTestRequest(BaseModel):
    """Request model for testing LLM provider connectivity."""
    prompt: str = Field(default="Hello, this is a connectivity test.", max_length=500)
    model: Optional[str] = None
    max_tokens: int = Field(default=10, ge=1, le=100)


class LLMProviderTestResponse(BaseModel):
    """Response model for LLM provider connectivity test."""
    success: bool
    provider_name: str
    model_used: str
    response_text: Optional[str] = None
    latency_ms: float
    error: Optional[str] = None


# =============================================================================
# Embedding Provider Models
# =============================================================================

class EmbeddingProvider(BaseModel):
    """Embedding provider configuration."""
    id: UUID = Field(default_factory=uuid4)
    provider_name: str = Field(..., min_length=1, max_length=100)
    provider_type: EmbeddingProviderType
    base_url: str = Field(..., min_length=1, max_length=500)
    api_key_hint: Optional[str] = None
    default_model: Optional[str] = None
    available_models: List[str] = Field(default_factory=list)
    embedding_dimensions: Optional[int] = None
    supported_input_formats: List[str] = Field(default=["text"])
    max_batch_size: int = Field(default=32)
    max_tokens_per_batch: int = Field(default=8192)
    is_enabled: bool = Field(default=True)
    is_default: bool = Field(default=False)
    health_status: HealthStatus = Field(default=HealthStatus.UNKNOWN)
    last_health_check: Optional[datetime] = None
    health_check_error: Optional[str] = None
    priority: int = Field(default=100)
    extra_config: Dict[str, Any] = Field(default_factory=dict)
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
    api_key: Optional[str] = Field(None, alias="api_key")
    api_key_hint: Optional[str] = None
    default_model: Optional[str] = None
    available_models: Optional[List[str]] = None
    embedding_dimensions: Optional[int] = None
    supported_input_formats: Optional[List[str]] = None
    max_batch_size: int = Field(default=32)
    max_tokens_per_batch: int = Field(default=8192)
    is_enabled: bool = Field(default=True)
    is_default: bool = Field(default=False)
    priority: int = Field(default=100)
    extra_config: Optional[Dict[str, Any]] = None


class EmbeddingProviderUpdate(BaseModel):
    """Model for updating an embedding provider."""
    base_url: Optional[str] = None
    api_key: Optional[str] = None
    api_key_hint: Optional[str] = None
    default_model: Optional[str] = None
    available_models: Optional[List[str]] = None
    embedding_dimensions: Optional[int] = None
    supported_input_formats: Optional[List[str]] = None
    max_batch_size: Optional[int] = None
    max_tokens_per_batch: Optional[int] = None
    is_enabled: Optional[bool] = None
    is_default: Optional[bool] = None
    priority: Optional[int] = None
    extra_config: Optional[Dict[str, Any]] = None


class EmbeddingProviderTestRequest(BaseModel):
    """Request model for testing embedding provider connectivity."""
    text: str = Field(default="This is a test sentence for embedding.", max_length=1000)
    model: Optional[str] = None


class EmbeddingProviderTestResponse(BaseModel):
    """Response model for embedding provider connectivity test."""
    success: bool
    provider_name: str
    model_used: str
    dimensions: Optional[int] = None
    latency_ms: float
    error: Optional[str] = None


# =============================================================================
# Agent Configuration Models
# =============================================================================

class AgentConfig(BaseModel):
    """Per-agent configuration."""
    id: UUID = Field(default_factory=uuid4)
    agent_type: str = Field(..., min_length=1, max_length=100)
    agent_id: Optional[str] = None
    config_name: str = Field(..., min_length=1, max_length=255)
    config_data: Dict[str, Any] = Field(default_factory=dict)
    llm_provider_id: Optional[UUID] = None
    embedding_provider_id: Optional[UUID] = None
    is_active: bool = Field(default=True)
    is_default_for_type: bool = Field(default=False)
    description: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: Optional[str] = None
    updated_by: Optional[str] = None

    class Config:
        use_enum_values = True
        json_encoders = {
            UUID: str,
            datetime: lambda v: v.isoformat(),
        }


class AgentConfigCreate(BaseModel):
    """Model for creating a new agent configuration."""
    agent_type: str = Field(..., min_length=1, max_length=100)
    agent_id: Optional[str] = None
    config_name: str = Field(..., min_length=1, max_length=255)
    config_data: Dict[str, Any] = Field(default_factory=dict)
    llm_provider_id: Optional[UUID] = None
    embedding_provider_id: Optional[UUID] = None
    is_active: bool = Field(default=True)
    is_default_for_type: bool = Field(default=False)
    description: Optional[str] = None
    tags: Optional[List[str]] = None


class AgentConfigUpdate(BaseModel):
    """Model for updating an agent configuration."""
    config_name: Optional[str] = None
    config_data: Optional[Dict[str, Any]] = None
    llm_provider_id: Optional[UUID] = None
    embedding_provider_id: Optional[UUID] = None
    is_active: Optional[bool] = None
    is_default_for_type: Optional[bool] = None
    description: Optional[str] = None
    tags: Optional[List[str]] = None


# =============================================================================
# Audit Log Models
# =============================================================================

class ConfigAuditLog(BaseModel):
    """Configuration change audit log entry."""
    id: UUID = Field(default_factory=uuid4)
    entity_type: str
    entity_id: UUID
    action: str
    old_value: Optional[Dict[str, Any]] = None
    new_value: Optional[Dict[str, Any]] = None
    changed_fields: Optional[List[str]] = None
    changed_by: Optional[str] = None
    change_reason: Optional[str] = None
    ip_address: Optional[str] = None
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
    cache_value: Dict[str, Any]
    expires_at: Optional[datetime] = None
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
    exported_by: Optional[str] = None
    user_configurations: List[UserConfiguration] = Field(default_factory=list)
    llm_providers: List[LLMProvider] = Field(default_factory=list)
    embedding_providers: List[EmbeddingProvider] = Field(default_factory=list)
    agent_configs: List[AgentConfig] = Field(default_factory=list)


class ConfigurationImport(BaseModel):
    """Imported configuration bundle."""
    version: str
    user_configurations: Optional[List[Dict[str, Any]]] = None
    llm_providers: Optional[List[Dict[str, Any]]] = None
    embedding_providers: Optional[List[Dict[str, Any]]] = None
    agent_configs: Optional[List[Dict[str, Any]]] = None


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
    imported_count: Dict[str, int] = Field(default_factory=dict)
    skipped_count: Dict[str, int] = Field(default_factory=dict)
    error_count: Dict[str, int] = Field(default_factory=dict)
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
