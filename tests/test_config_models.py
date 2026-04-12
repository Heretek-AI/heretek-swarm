"""
Configuration Module Tests

Tests for the configuration management system including:
- ConfigLoader class
- ConfigurationService class
- Configuration models and validation
- Encryption functionality
- Cache behavior
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest

# Import models for testing
from heretek_swarm.config.models import (
    AgentConfig,
    AgentConfigCreate,
    AgentConfigUpdate,
    ConfigAuditLog,
    ConfigCacheEntry,
    ConfigType,
    ConfigurationExport,
    ConfigurationImport,
    EmbeddingProvider,
    EmbeddingProviderTestRequest,
    EmbeddingProviderTestResponse,
    EmbeddingProviderType,
    HealthStatus,
    ImportOptions,
    ImportResult,
    LLMProvider,
    LLMProviderCreate,
    LLMProviderTestRequest,
    LLMProviderTestResponse,
    LLMProviderType,
    LLMProviderUpdate,
    UserConfiguration,
    UserConfigurationCreate,
    UserConfigurationUpdate,
)

# =============================================================================
# Model Tests - ConfigType
# =============================================================================

class TestConfigType:
    """Tests for ConfigType enum."""

    def test_config_type_values(self):
        """Test ConfigType enum values."""
        assert ConfigType.STRING == "string"
        assert ConfigType.INTEGER == "integer"
        assert ConfigType.FLOAT == "float"
        assert ConfigType.BOOLEAN == "boolean"
        assert ConfigType.JSON == "json"
        assert ConfigType.ARRAY == "array"

    def test_config_type_count(self):
        """Test ConfigType has expected number of values."""
        assert len(ConfigType) == 6


# =============================================================================
# Model Tests - HealthStatus
# =============================================================================

class TestHealthStatus:
    """Tests for HealthStatus enum."""

    def test_health_status_values(self):
        """Test HealthStatus enum values."""
        assert HealthStatus.HEALTHY == "healthy"
        assert HealthStatus.UNHEALTHY == "unhealthy"
        assert HealthStatus.UNKNOWN == "unknown"
        assert HealthStatus.DEGRADED == "degraded"


# =============================================================================
# Model Tests - LLMProviderType
# =============================================================================

class TestLLMProviderType:
    """Tests for LLMProviderType enum."""

    def test_llm_provider_type_values(self):
        """Test LLMProviderType enum values."""
        assert LLMProviderType.OPENAI == "openai"
        assert LLMProviderType.OPENAI_COMPATIBLE == "openai_compatible"
        assert LLMProviderType.OLLAMA == "ollama"
        assert LLMProviderType.LLAMACPP == "llamacpp"
        assert LLMProviderType.ZAI == "zai"
        assert LLMProviderType.MINIMAX == "minimax"
        assert LLMProviderType.LEMONADE == "lemonade"

    def test_llm_provider_type_count(self):
        """Test LLMProviderType has expected number of values."""
        assert len(LLMProviderType) == 7


# =============================================================================
# Model Tests - EmbeddingProviderType
# =============================================================================

class TestEmbeddingProviderType:
    """Tests for EmbeddingProviderType enum."""

    def test_embedding_provider_type_values(self):
        """Test EmbeddingProviderType enum values."""
        assert EmbeddingProviderType.OPENAI == "openai"
        assert EmbeddingProviderType.OPENAI_COMPATIBLE == "openai_compatible"
        assert EmbeddingProviderType.OLLAMA == "ollama"
        assert EmbeddingProviderType.LOCAL == "local"
        assert EmbeddingProviderType.HUGGINGFACE == "huggingface"


# =============================================================================
# Model Tests - UserConfiguration
# =============================================================================

class TestUserConfiguration:
    """Tests for UserConfiguration model."""

    def test_create_user_configuration_defaults(self):
        """Test creating UserConfiguration with defaults."""
        config = UserConfiguration(config_key="test.key", config_value="default_value")
        assert config.config_key == "test.key"
        assert config.config_value == "default_value"
        assert config.config_type == ConfigType.STRING
        assert config.category == "general"
        assert config.is_sensitive is False
        assert config.is_editable is True
        assert config.id is not None

    def test_create_user_configuration_full(self):
        """Test creating UserConfiguration with all fields."""
        config = UserConfiguration(
            config_key="custom.key",
            config_value="my_value",
            config_type=ConfigType.INTEGER,
            description="Test configuration",
            category="custom",
            is_sensitive=True,
            is_editable=False,
        )
        assert config.config_key == "custom.key"
        assert config.config_value == "my_value"
        assert config.config_type == ConfigType.INTEGER
        assert config.description == "Test configuration"
        assert config.category == "custom"
        assert config.is_sensitive is True
        assert config.is_editable is False

    def test_user_configuration_validation(self):
        """Test UserConfiguration validation constraints."""
        # Key must be non-empty
        with pytest.raises(ValueError):
            UserConfiguration(config_key="")

    def test_user_configuration_timestamps(self):
        """Test UserConfiguration has timestamps."""
        config = UserConfiguration(config_key="timestamp.test", config_value="ts_value")
        assert config.created_at is not None
        assert config.updated_at is not None
        assert isinstance(config.created_at, datetime)


class TestUserConfigurationCreate:
    """Tests for UserConfigurationCreate model."""

    def test_create_model_defaults(self):
        """Test UserConfigurationCreate with defaults."""
        create = UserConfigurationCreate(config_key="new.key", config_value="default")
        assert create.config_key == "new.key"
        assert create.config_value == "default"
        assert create.config_type == ConfigType.STRING
        assert create.category == "general"

    def test_create_model_with_value(self):
        """Test UserConfigurationCreate with value."""
        create = UserConfigurationCreate(
            config_key="integer.key",
            config_value=42,
            config_type=ConfigType.INTEGER,
        )
        assert create.config_value == 42


class TestUserConfigurationUpdate:
    """Tests for UserConfigurationUpdate model."""

    def test_update_model_partial(self):
        """Test UserConfigurationUpdate with partial updates."""
        update = UserConfigurationUpdate(config_value="new_value")
        assert update.config_value == "new_value"
        assert update.description is None
        assert update.is_editable is None


# =============================================================================
# Model Tests - LLMProvider
# =============================================================================

class TestLLMProvider:
    """Tests for LLMProvider model."""

    def test_create_llm_provider_defaults(self):
        """Test creating LLMProvider with defaults."""
        provider = LLMProvider(
            provider_name="test_provider",
            provider_type=LLMProviderType.OPENAI,
            base_url="https://api.openai.com",
        )
        assert provider.provider_name == "test_provider"
        assert provider.provider_type == LLMProviderType.OPENAI
        assert provider.base_url == "https://api.openai.com"
        assert provider.supports_streaming is True
        assert provider.supports_function_calling is False
        assert provider.is_enabled is True
        assert provider.is_default is False
        assert provider.health_status == HealthStatus.UNKNOWN

    def test_create_llm_provider_full(self):
        """Test creating LLMProvider with all fields."""
        provider = LLMProvider(
            provider_name="custom_provider",
            provider_type=LLMProviderType.OPENAI_COMPATIBLE,
            base_url="https://custom.api.com",
            api_key_hint="sk-...",
            default_model="gpt-4",
            available_models=["gpt-4", "gpt-3.5"],
            supports_streaming=True,
            supports_function_calling=True,
            max_tokens=8192,
            max_context_length=128000,
            is_default=True,
        )
        assert provider.available_models == ["gpt-4", "gpt-3.5"]
        assert provider.max_tokens == 8192
        assert provider.is_default is True

    def test_llm_provider_validation(self):
        """Test LLMProvider validation constraints."""
        # Name must be non-empty
        with pytest.raises(ValueError):
            LLMProvider(provider_name="", provider_type=LLMProviderType.OPENAI, base_url="http://x.com")


class TestLLMProviderCreate:
    """Tests for LLMProviderCreate model."""

    def test_create_llm_provider_required_fields(self):
        """Test LLMProviderCreate requires essential fields."""
        create = LLMProviderCreate(
            provider_name="new_provider",
            provider_type=LLMProviderType.OLLAMA,
            base_url="http://localhost:11434",
        )
        assert create.provider_name == "new_provider"
        assert create.provider_type == LLMProviderType.OLLAMA


class TestLLMProviderUpdate:
    """Tests for LLMProviderUpdate model."""

    def test_update_llm_provider_partial(self):
        """Test LLMProviderUpdate with partial updates."""
        update = LLMProviderUpdate(
            base_url="https://new.url.com",
            is_enabled=False,
        )
        assert update.base_url == "https://new.url.com"
        assert update.is_enabled is False
        assert update.default_model is None


class TestLLMProviderTestRequest:
    """Tests for LLMProviderTestRequest model."""

    def test_default_prompt(self):
        """Test LLMProviderTestRequest has default prompt."""
        request = LLMProviderTestRequest()
        assert request.prompt == "Hello, this is a connectivity test."
        assert request.max_tokens == 10

    def test_custom_request(self):
        """Test LLMProviderTestRequest with custom values."""
        request = LLMProviderTestRequest(
            prompt="Custom test",
            max_tokens=50,
        )
        assert request.prompt == "Custom test"
        assert request.max_tokens == 50

    def test_max_tokens_validation(self):
        """Test max_tokens validation."""
        # Valid max_tokens
        request = LLMProviderTestRequest(max_tokens=100)
        assert request.max_tokens == 100

        # Invalid - too high
        with pytest.raises(ValueError):
            LLMProviderTestRequest(max_tokens=101)


class TestLLMProviderTestResponse:
    """Tests for LLMProviderTestResponse model."""

    def test_successful_response(self):
        """Test successful LLMProviderTestResponse."""
        response = LLMProviderTestResponse(
            success=True,
            provider_name="openai",
            model_used="gpt-4",
            response_text="Hello!",
            latency_ms=150.5,
        )
        assert response.success is True
        assert response.latency_ms == 150.5
        assert response.error is None

    def test_failed_response(self):
        """Test failed LLMProviderTestResponse."""
        response = LLMProviderTestResponse(
            success=False,
            provider_name="openai",
            model_used="gpt-4",
            latency_ms=5000.0,
            error="Connection timeout",
        )
        assert response.success is False
        assert response.error == "Connection timeout"


# =============================================================================
# Model Tests - EmbeddingProvider
# =============================================================================

class TestEmbeddingProvider:
    """Tests for EmbeddingProvider model."""

    def test_create_embedding_provider_defaults(self):
        """Test creating EmbeddingProvider with defaults."""
        provider = EmbeddingProvider(
            provider_name="test_embed",
            provider_type=EmbeddingProviderType.OPENAI,
            base_url="https://api.openai.com",
        )
        assert provider.provider_name == "test_embed"
        assert provider.supported_input_formats == ["text"]
        assert provider.max_batch_size == 32
        assert provider.max_tokens_per_batch == 8192

    def test_create_embedding_provider_full(self):
        """Test creating EmbeddingProvider with all fields."""
        provider = EmbeddingProvider(
            provider_name="custom_embed",
            provider_type=EmbeddingProviderType.OLLAMA,
            base_url="http://localhost:11434",
            default_model="nomic-embed-text",
            embedding_dimensions=768,
            supported_input_formats=["text", "code"],
            max_batch_size=64,
        )
        assert provider.embedding_dimensions == 768
        assert provider.max_batch_size == 64
        assert "code" in provider.supported_input_formats


class TestEmbeddingProviderTestRequest:
    """Tests for EmbeddingProviderTestRequest model."""

    def test_default_text(self):
        """Test EmbeddingProviderTestRequest has default text."""
        request = EmbeddingProviderTestRequest()
        assert "test" in request.text.lower()

    def test_custom_text(self):
        """Test EmbeddingProviderTestRequest with custom text."""
        request = EmbeddingProviderTestRequest(text="Custom embedding text")
        assert request.text == "Custom embedding text"


class TestEmbeddingProviderTestResponse:
    """Tests for EmbeddingProviderTestResponse model."""

    def test_successful_response(self):
        """Test successful EmbeddingProviderTestResponse."""
        response = EmbeddingProviderTestResponse(
            success=True,
            provider_name="openai",
            model_used="text-embedding-3-small",
            dimensions=1536,
            latency_ms=50.0,
        )
        assert response.success is True
        assert response.dimensions == 1536


# =============================================================================
# Model Tests - AgentConfig
# =============================================================================

class TestAgentConfig:
    """Tests for AgentConfig model."""

    def test_create_agent_config_defaults(self):
        """Test creating AgentConfig with defaults."""
        config = AgentConfig(
            agent_type="steward",
            config_name="default_config",
        )
        assert config.agent_type == "steward"
        assert config.config_name == "default_config"
        assert config.config_data == {}
        assert config.is_active is True
        assert config.is_default_for_type is False
        assert config.tags == []

    def test_create_agent_config_full(self):
        """Test creating AgentConfig with all fields."""
        config = AgentConfig(
            agent_type="worker",
            agent_id="worker-1",
            config_name="worker_config",
            config_data={"max_retries": 3, "timeout": 60},
            tags=["production", "high-priority"],
        )
        assert config.agent_id == "worker-1"
        assert config.config_data["max_retries"] == 3
        assert "production" in config.tags


class TestAgentConfigCreate:
    """Tests for AgentConfigCreate model."""

    def test_create_agent_config_required_fields(self):
        """Test AgentConfigCreate requires essential fields."""
        create = AgentConfigCreate(
            agent_type="beta",
            config_name="beta_config",
        )
        assert create.agent_type == "beta"


class TestAgentConfigUpdate:
    """Tests for AgentConfigUpdate model."""

    def test_update_agent_config_partial(self):
        """Test AgentConfigUpdate with partial updates."""
        update = AgentConfigUpdate(
            config_data={"new_setting": True},
            is_active=False,
        )
        assert update.config_data == {"new_setting": True}
        assert update.is_active is False


# =============================================================================
# Model Tests - ConfigAuditLog
# =============================================================================

class TestConfigAuditLog:
    """Tests for ConfigAuditLog model."""

    def test_create_audit_log(self):
        """Test creating ConfigAuditLog."""
        entity_id = uuid4()
        log = ConfigAuditLog(
            entity_type="user_configuration",
            entity_id=entity_id,
            action="update",
            old_value={"value": 1},
            new_value={"value": 2},
            changed_fields=["value"],
            changed_by="admin",
        )
        assert log.entity_type == "user_configuration"
        assert log.entity_id == entity_id
        assert log.action == "update"
        assert log.changed_fields == ["value"]


# =============================================================================
# Model Tests - ConfigCacheEntry
# =============================================================================

class TestConfigCacheEntry:
    """Tests for ConfigCacheEntry model."""

    def test_create_cache_entry(self):
        """Test creating ConfigCacheEntry."""
        entry = ConfigCacheEntry(
            cache_key="test.key",
            cache_value={"value": "cached"},
        )
        assert entry.cache_key == "test.key"
        assert entry.access_count == 0

    def test_cache_entry_defaults(self):
        """Test ConfigCacheEntry default values."""
        entry = ConfigCacheEntry(
            cache_key="default.test",
            cache_value={"data": 123},
        )
        assert entry.access_count == 0
        assert entry.last_accessed_at is not None


# =============================================================================
# Model Tests - Import/Export
# =============================================================================

class TestConfigurationExport:
    """Tests for ConfigurationExport model."""

    def test_create_export_defaults(self):
        """Test creating ConfigurationExport with defaults."""
        export = ConfigurationExport()
        assert export.version == "1.0"
        assert export.user_configurations == []
        assert export.llm_providers == []
        assert export.exported_at is not None


class TestConfigurationImport:
    """Tests for ConfigurationImport model."""

    def test_create_import(self):
        """Test creating ConfigurationImport."""
        import_data = ConfigurationImport(
            version="1.0",
            user_configurations=[{"config_key": "test", "config_value": "value"}],
        )
        assert import_data.version == "1.0"
        assert len(import_data.user_configurations) == 1


class TestImportOptions:
    """Tests for ImportOptions model."""

    def test_default_options(self):
        """Test ImportOptions default values."""
        options = ImportOptions()
        assert options.overwrite_existing is False
        assert options.skip_conflicts is True
        assert options.import_user_configs is True
        assert options.import_llm_providers is True


class TestImportResult:
    """Tests for ImportResult model."""

    def test_create_result(self):
        """Test creating ImportResult."""
        result = ImportResult(
            success=True,
            imported_count={"users": 5, "providers": 2},
            skipped_count={"users": 1},
            error_count={"users": 0},
        )
        assert result.success is True
        assert result.imported_count["users"] == 5

    def test_result_with_errors(self):
        """Test ImportResult with errors."""
        result = ImportResult(
            success=False,
            errors=["Invalid config format", "Missing required field"],
            warnings=["Skipped duplicate entry"],
        )
        assert result.success is False
        assert len(result.errors) == 2


# =============================================================================
# ConfigLoader Tests (with mocked service)
# =============================================================================

class TestConfigLoaderUnit:
    """Unit tests for ConfigLoader without database."""

    def test_config_loader_initialization(self):
        """Test ConfigLoader can be instantiated."""
        from heretek_swarm.config.loader import ConfigLoader

        loader = ConfigLoader(cache_ttl_seconds=60)
        assert loader._cache_ttl == timedelta(seconds=60)
        assert loader._initialized is False
        assert isinstance(loader._cache, dict)

    def test_config_key_mapping(self):
        """Test ConfigLoader has correct config key mapping."""
        from heretek_swarm.config.loader import ConfigLoader

        loader = ConfigLoader()
        mapping = loader._build_config_key_mapping()

        # Verify some key mappings
        assert mapping["rate_limit.enabled"] == "RATE_LIMIT_ENABLED"
        assert mapping["memory.max_size"] == "MEMORY_MAX_SIZE"
        assert mapping["consciousness.phi_threshold"] == "CONSCIOUSNESS_PHI_THRESHOLD"
        assert mapping["api.host"] == "API_HOST"
        assert mapping["database.url"] == "DATABASE_URL"

    def test_cache_entry_class(self):
        """Test CacheEntry dataclass."""
        from heretek_swarm.config.loader import CacheEntry

        entry = CacheEntry(
            value="test_value",
            source="database",
            expires_at=datetime.now(UTC) + timedelta(minutes=5),
        )
        assert entry.value == "test_value"
        assert entry.source == "database"
        assert entry.access_count == 0


# =============================================================================
# Serialization Tests
# =============================================================================

class TestModelSerialization:
    """Tests for model serialization."""

    def test_user_configuration_to_dict(self):
        """Test UserConfiguration serialization."""
        config = UserConfiguration(
            config_key="serial.test",
            config_value="value123",
        )
        data = config.model_dump()
        assert data["config_key"] == "serial.test"
        assert data["config_value"] == "value123"
        assert "id" in data
        assert "created_at" in data

    def test_llm_provider_to_json(self):
        """Test LLMProvider JSON serialization."""
        provider = LLMProvider(
            provider_name="json_test",
            provider_type=LLMProviderType.OPENAI,
            base_url="https://api.openai.com",
        )
        json_str = provider.model_dump_json()
        assert "json_test" in json_str
        assert "openai" in json_str

    def test_embedding_provider_from_dict(self):
        """Test EmbeddingProvider deserialization."""
        data = {
            "provider_name": "from_dict",
            "provider_type": "ollama",
            "base_url": "http://localhost:11434",
        }
        provider = EmbeddingProvider(**data)
        assert provider.provider_name == "from_dict"
        assert provider.provider_type == EmbeddingProviderType.OLLAMA


# =============================================================================
# Integration Tests
# =============================================================================

class TestConfigModelsIntegration:
    """Integration tests that verify models work together."""

    def test_llm_and_embedding_provider_relationship(self):
        """Test LLM and embedding providers can be configured together."""
        llm = LLMProvider(
            provider_name="complete_stack",
            provider_type=LLMProviderType.OPENAI,
            base_url="https://api.openai.com",
            default_model="gpt-4",
        )

        embedding = EmbeddingProvider(
            provider_name="complete_stack_embed",
            provider_type=EmbeddingProviderType.OPENAI,
            base_url="https://api.openai.com",
            default_model="text-embedding-3-small",
        )

        # Both should be valid
        assert llm.provider_name == "complete_stack"
        assert embedding.provider_name == "complete_stack_embed"

    def test_agent_config_with_providers(self):
        """Test AgentConfig with provider references."""
        llm_id = uuid4()
        embed_id = uuid4()

        agent = AgentConfig(
            agent_type="advanced_agent",
            config_name="provider_linked_config",
            llm_provider_id=llm_id,
            embedding_provider_id=embed_id,
            config_data={
                "llm_model": "gpt-4",
                "embedding_model": "text-embedding-3-small",
            },
        )

        assert agent.llm_provider_id == llm_id
        assert agent.embedding_provider_id == embed_id
        assert agent.config_data["llm_model"] == "gpt-4"

    def test_export_import_roundtrip(self):
        """Test export and import models are compatible."""
        export = ConfigurationExport(
            user_configurations=[
                UserConfiguration(config_key="test.1", config_value="value1"),
                UserConfiguration(config_key="test.2", config_value="value2"),
            ],
            llm_providers=[
                LLMProvider(
                    provider_name="exported",
                    provider_type=LLMProviderType.OPENAI,
                    base_url="https://api.openai.com",
                ),
            ],
        )

        # Verify export structure
        assert len(export.user_configurations) == 2
        assert len(export.llm_providers) == 1

        # Create corresponding import
        import_data = ConfigurationImport(
            version=export.version,
            user_configurations=[c.model_dump() for c in export.user_configurations],
            llm_providers=[p.model_dump() for p in export.llm_providers],
        )

        assert len(import_data.user_configurations) == 2
        assert len(import_data.llm_providers) == 1


# =============================================================================
# Edge Cases
# =============================================================================

class TestModelEdgeCases:
    """Tests for edge cases and boundary conditions."""

    def test_empty_tags_list(self):
        """Test AgentConfig with empty tags list."""
        config = AgentConfig(
            agent_type="empty_test",
            config_name="empty_tags",
            tags=[],
        )
        assert config.tags == []

    def test_complex_config_data(self):
        """Test AgentConfig with complex nested data."""
        complex_data = {
            "nested": {
                "deep": {
                    "value": [1, 2, 3],
                }
            },
            "mixed": {"str": "text", "num": 42, "bool": True},
        }
        config = AgentConfig(
            agent_type="complex",
            config_name="complex_data",
            config_data=complex_data,
        )
        assert config.config_data["nested"]["deep"]["value"] == [1, 2, 3]

    def test_uuid_serialization(self):
        """Test UUID fields serialize correctly."""
        config = UserConfiguration(config_key="uuid.test", config_value="uuid_value")
        # Use json mode for proper string serialization
        data = config.model_dump(mode="json")
        assert isinstance(data["id"], str)
        assert isinstance(data["created_at"], str)
        assert isinstance(data["updated_at"], str)
