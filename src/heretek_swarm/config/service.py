"""
Configuration Service

Provides CRUD operations for configurations with caching and validation.
Supports migration from .env to database-backed configuration.
Features API key encryption using Fernet symmetric encryption.
"""

from __future__ import annotations

import os
from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING, Any, TypeVar

import structlog
from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from .db_models import (
    AgentConfig as AgentConfigORM,
    ConfigAuditLog as ConfigAuditLogORM,
    ConfigCache as ConfigCacheORM,
    EmbeddingProvider as EmbeddingProviderORM,
    LLMProvider as LLMProviderORM,
    UserConfiguration as UserConfigurationORM,
)
from .encryption import ApiKeyEncryptor
from .models import (
    AgentConfig,
    AgentConfigCreate,
    AgentConfigUpdate,
    ConfigAuditLog,
    ConfigCacheEntry,
    ConfigurationExport,
    ConfigurationImport,
    EmbeddingProvider,
    EmbeddingProviderCreate,
    EmbeddingProviderUpdate,
    ImportOptions,
    ImportResult,
    LLMProvider,
    LLMProviderCreate,
    LLMProviderUpdate,
    UserConfiguration,
    UserConfigurationCreate,
    UserConfigurationUpdate,
)

if TYPE_CHECKING:
    from uuid import UUID

logger = structlog.get_logger("config.service")

T = TypeVar("T")


class ConfigurationService:
    """
    Service for managing configurations in the database.

    Features:
    - CRUD operations for all configuration types
    - In-memory caching for frequently accessed configs
    - Validation of configuration values
    - Audit logging for changes
    - Import/export functionality
    - Migration from .env files
    """

    def __init__(self, database_url: str | None = None):
        """
        Initialize the configuration service.

        Args:
            database_url: PostgreSQL database URL. Defaults to DATABASE_URL env var.

        Raises:
            ValueError: If DATABASE_URL environment variable is not set
        """
        self.database_url = database_url or os.environ.get("DATABASE_URL")
        if not self.database_url:
            raise ValueError("DATABASE_URL environment variable is required")

        self._engine = create_async_engine(
            self.database_url,
            echo=False,
            pool_pre_ping=True,
        )

        self._session_factory = async_sessionmaker(
            self._engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )

        # In-memory cache for frequently accessed configurations
        self._cache: dict[str, ConfigCacheEntry] = {}
        self._cache_ttl = timedelta(minutes=5)

        # Encryption for API keys using ApiKeyEncryptor
        self._encryptor = ApiKeyEncryptor(os.environ.get("CONFIG_ENCRYPTION_KEY"))
        self._fernet = self._encryptor._fernet

        logger.info("ConfigurationService initialized", database_url=self.database_url)

    def encrypt_api_key(self, api_key: str) -> str:
        """
        Encrypt an API key using Fernet symmetric encryption.

        Args:
            api_key: The plain text API key to encrypt

        Returns:
            Encrypted API key (base64 encoded)

        Raises:
            ValueError: If encryption is not configured
        """
        return self._encryptor.encrypt(api_key)

    def decrypt_api_key(self, encrypted_key: str) -> str:
        """
        Decrypt an API key using Fernet symmetric encryption.

        Args:
            encrypted_key: The encrypted API key to decrypt

        Returns:
            Decrypted plain text API key

        Raises:
            ValueError: If decryption fails or encryption not configured
        """
        return self._encryptor.decrypt(encrypted_key)

    async def initialize(self) -> None:
        """Initialize the service and warm up the cache."""
        await self._warm_cache()
        logger.info("ConfigurationService initialized with cache")

    async def shutdown(self) -> None:
        """Shutdown the service and cleanup resources."""
        await self._engine.dispose()
        logger.info("ConfigurationService shutdown complete")

    # =========================================================================
    # Cache Management
    # =========================================================================

    async def _warm_cache(self) -> None:
        """Warm up the cache with frequently accessed configurations."""
        try:
            async with self._session_factory() as session:
                # Cache system configurations
                result = await session.execute(
                    select(UserConfigurationORM).where(
                        UserConfigurationORM.category.in_(["system", "rate_limiting"])
                    )
                )
                configs = result.scalars().all()

                for config in configs:
                    cache_key = f"config:{config.config_key}"
                    self._cache[cache_key] = ConfigCacheEntry(
                        cache_key=cache_key,
                        cache_value={"value": config.config_value, "type": config.config_type.value},
                        expires_at=datetime.now(UTC) + self._cache_ttl,
                    )
        except Exception as e:
            logger.warning("cache_warmup_skipped", reason=str(e))

    def _get_cache_key(self, entity_type: str, key: str) -> str:
        """Generate a cache key for an entity."""
        return f"{entity_type}:{key}"

    def _invalidate_cache(self, entity_type: str, key: str) -> None:
        """Invalidate a cache entry."""
        cache_key = self._get_cache_key(entity_type, key)
        if cache_key in self._cache:
            del self._cache[cache_key]

    def _set_cache(
        self,
        entity_type: str,
        key: str,
        value: Any,
        ttl: timedelta | None = None,
    ) -> None:
        """Set a cache entry."""
        cache_key = self._get_cache_key(entity_type, key)
        self._cache[cache_key] = ConfigCacheEntry(
            cache_key=cache_key,
            cache_value={"value": value},
            expires_at=datetime.now(UTC) + (ttl or self._cache_ttl),
        )

    def _get_cache(self, entity_type: str, key: str) -> Any | None:
        """Get a cached value if available and not expired."""
        cache_key = self._get_cache_key(entity_type, key)
        entry = self._cache.get(cache_key)

        if entry is None:
            return None

        if entry.expires_at and datetime.now(UTC) > entry.expires_at:
            del self._cache[cache_key]
            return None

        entry.access_count += 1
        entry.last_accessed_at = datetime.now(UTC)
        return entry.cache_value.get("value")

    def _orm_to_pydantic(self, orm_obj: Any) -> Any:
        """Convert SQLAlchemy ORM object to Pydantic model for public API."""
        if orm_obj is None:
            return None

        # Map ORM class to Pydantic class
        if isinstance(orm_obj, UserConfigurationORM):
            return UserConfiguration(
                id=orm_obj.id,
                config_key=orm_obj.config_key,
                config_value=orm_obj.config_value,
                config_type=orm_obj.config_type,
                description=orm_obj.description,
                category=orm_obj.category,
                is_sensitive=orm_obj.is_sensitive,
                is_editable=orm_obj.is_editable,
                validation_schema=orm_obj.validation_schema,
                created_at=orm_obj.created_at,
                updated_at=orm_obj.updated_at,
                updated_by=orm_obj.updated_by,
            )
        elif isinstance(orm_obj, LLMProviderORM):
            return LLMProvider(
                id=orm_obj.id,
                provider_name=orm_obj.provider_name,
                provider_type=orm_obj.provider_type,
                base_url=orm_obj.base_url,
                api_key=orm_obj.api_key_encrypted,  # May need decryption
                api_key_hint=orm_obj.api_key_hint,
                default_model=orm_obj.default_model,
                available_models=orm_obj.available_models or [],
                model_aliases=orm_obj.model_aliases or {},
                supports_streaming=orm_obj.supports_streaming,
                supports_function_calling=orm_obj.supports_function_calling,
                supports_vision=orm_obj.supports_vision,
                max_tokens=orm_obj.max_tokens,
                max_context_length=orm_obj.max_context_length,
                rate_limit_requests_per_minute=orm_obj.rate_limit_requests_per_minute,
                rate_limit_tokens_per_minute=orm_obj.rate_limit_tokens_per_minute,
                is_enabled=orm_obj.is_enabled,
                is_default=orm_obj.is_default,
                priority=orm_obj.priority,
                extra_config=orm_obj.extra_config or {},
            )
        elif isinstance(orm_obj, EmbeddingProviderORM):
            return EmbeddingProvider(
                id=orm_obj.id,
                provider_name=orm_obj.provider_name,
                provider_type=orm_obj.provider_type,
                base_url=orm_obj.base_url,
                api_key=orm_obj.api_key_encrypted,  # May need decryption
                api_key_hint=orm_obj.api_key_hint,
                model_name=orm_obj.default_model,
                dimensions=orm_obj.embedding_dimensions,
                available_models=orm_obj.available_models or [],
                is_enabled=orm_obj.is_enabled,
                is_default=orm_obj.is_default,
                priority=orm_obj.priority,
                extra_config=orm_obj.extra_config or {},
            )
        elif isinstance(orm_obj, AgentConfigORM):
            return AgentConfig(
                id=orm_obj.id,
                agent_type=orm_obj.agent_type,
                agent_id=orm_obj.agent_id,
                config_name=orm_obj.config_name,
                config_data=orm_obj.config_data or {},
                llm_provider_id=orm_obj.llm_provider_id,
                embedding_provider_id=orm_obj.embedding_provider_id,
                is_active=orm_obj.is_active,
                is_default_for_type=orm_obj.is_default_for_type,
                description=orm_obj.description,
                tags=orm_obj.tags or [],
                created_at=orm_obj.created_at,
                updated_at=orm_obj.updated_at,
                created_by=orm_obj.created_by,
                updated_by=orm_obj.updated_by,
            )
        else:
            # For unknown types, try to return as-is or convert via dict
            if hasattr(orm_obj, "__dict__"):
                return orm_obj.__dict__
            return orm_obj

    # =========================================================================
    # User Configuration CRUD
    # =========================================================================

    async def get_config(self, config_key: str) -> UserConfiguration | None:
        """
        Get a configuration by key.

        Args:
            config_key: The configuration key

        Returns:
            Configuration if found, None otherwise
        """
        # Check cache first
        cached = self._get_cache("config", config_key)
        if cached is not None:
            logger.debug("Cache hit for config", key=config_key)
            return UserConfiguration(**cached)

        async with self._session_factory() as session:
            result = await session.execute(
                select(UserConfigurationORM).where(
                    UserConfigurationORM.config_key == config_key
                )
            )
            config = result.scalar_one_or_none()

            if config:
                self._set_cache("config", config_key, self._orm_to_pydantic(config))

            return config

    async def get_config_value(
        self,
        config_key: str,
        default: Any = None,
    ) -> Any:
        """
        Get a configuration value by key.

        Args:
            config_key: The configuration key
            default: Default value if not found

        Returns:
            Configuration value or default
        """
        config = await self.get_config(config_key)
        return config.config_value if config else default

    async def list_configs(
        self,
        category: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[UserConfiguration]:
        """
        List configurations with optional filtering.

        Args:
            category: Filter by category
            limit: Maximum results
            offset: Result offset

        Returns:
            List of configurations
        """
        async with self._session_factory() as session:
            query = select(UserConfigurationORM)

            if category:
                query = query.where(UserConfigurationORM.category == category)

            query = query.order_by(UserConfigurationORM.config_key).offset(offset).limit(limit)

            result = await session.execute(query)
            orm_results = result.scalars().all()
            return [self._orm_to_pydantic(r) for r in orm_results]

    async def create_config(
        self,
        config: UserConfigurationCreate,
        changed_by: str | None = None,
    ) -> UserConfiguration:
        """
        Create a new configuration.

        Args:
            config: Configuration data
            changed_by: User making the change

        Returns:
            Created configuration
        """
        async with self._session_factory() as session:
            new_config = UserConfiguration(
                config_key=config.config_key,
                config_value=config.config_value,
                config_type=config.config_type,
                description=config.description,
                category=config.category,
                is_sensitive=config.is_sensitive,
                is_editable=config.is_editable,
                validation_schema=config.validation_schema,
                updated_by=changed_by,
            )

            # Validate if schema provided
            if config.validation_schema:
                self._validate_config_value(
                    config.config_value,
                    config.validation_schema,
                )

            session.add(new_config)
            await session.commit()
            await session.refresh(new_config)

            # Log the change
            await self._log_change(
                session,
                "user_configuration",
                new_config.id,
                "create",
                None,
                self._orm_to_pydantic(config),
                changed_by,
            )

            # Invalidate cache
            self._invalidate_cache("config", new_config.config_key)

            logger.info("Configuration created", key=new_config.config_key)
            return new_config

    async def update_config(
        self,
        config_key: str,
        update: UserConfigurationUpdate,
        changed_by: str | None = None,
    ) -> UserConfiguration | None:
        """
        Update a configuration.

        Args:
            config_key: The configuration key
            update: Update data
            changed_by: User making the change

        Returns:
            Updated configuration or None if not found
        """
        async with self._session_factory() as session:
            result = await session.execute(
                select(UserConfigurationORM).where(
                    UserConfigurationORM.config_key == config_key
                )
            )
            config = result.scalar_one_or_none()

            if not config:
                return None

            if not config.is_editable:
                raise ValueError(f"Configuration {config_key} is not editable")

            old_value = self._orm_to_pydantic(config)

            update_data = update.model_dump(exclude_unset=True)
            for field, value in update_data.items():
                if value is not None:
                    setattr(config, field, value)

            # Validate if schema exists
            if config.validation_schema and update.config_value is not None:
                self._validate_config_value(
                    update.config_value,
                    config.validation_schema,
                )

            config.updated_at = datetime.now(UTC)
            config.updated_by = changed_by

            await session.commit()
            await session.refresh(config)

            # Log the change
            await self._log_change(
                session,
                "user_configuration",
                config.id,
                "update",
                old_value,
                self._orm_to_pydantic(config),
                changed_by,
            )

            # Invalidate cache
            self._invalidate_cache("config", config_key)

            logger.info("Configuration updated", key=config_key)
            return config

    async def delete_config(
        self,
        config_key: str,
        changed_by: str | None = None,
    ) -> bool:
        """
        Delete a configuration.

        Args:
            config_key: The configuration key
            changed_by: User making the change

        Returns:
            True if deleted, False if not found
        """
        async with self._session_factory() as session:
            result = await session.execute(
                select(UserConfigurationORM).where(
                    UserConfigurationORM.config_key == config_key
                )
            )
            config = result.scalar_one_or_none()

            if not config:
                return False

            if not config.is_editable:
                raise ValueError(f"Configuration {config_key} is not deletable")

            old_value = self._orm_to_pydantic(config)

            await session.execute(
                delete(UserConfigurationORM).where(
                    UserConfigurationORM.config_key == config_key
                )
            )
            await session.commit()

            # Log the change
            await self._log_change(
                session,
                "user_configuration",
                config.id,
                "delete",
                old_value,
                None,
                changed_by,
            )

            # Invalidate cache
            self._invalidate_cache("config", config_key)

            logger.info("Configuration deleted", key=config_key)
            return True

    # =========================================================================
    # LLM Provider CRUD
    # =========================================================================

    async def get_llm_provider(self, provider_id: UUID) -> LLMProvider | None:
        """Get an LLM provider by ID."""
        async with self._session_factory() as session:
            result = await session.execute(
                select(LLMProviderORM).where(LLMProviderORM.id == provider_id)
            )
            return result.scalar_one_or_none()

    async def get_llm_provider_by_name(
        self,
        provider_name: str,
    ) -> LLMProvider | None:
        """Get an LLM provider by name."""
        async with self._session_factory() as session:
            result = await session.execute(
                select(LLMProviderORM).where(
                    LLMProviderORM.provider_name == provider_name
                )
            )
            return result.scalar_one_or_none()

    async def list_llm_providers(
        self,
        provider_type: str | None = None,
        enabled_only: bool = False,
        include_disabled: bool = False,
    ) -> list[LLMProvider]:
        """
        List LLM providers with optional filtering.

        Args:
            provider_type: Filter by provider type
            enabled_only: Only return enabled providers
            include_disabled: Include disabled providers (overrides enabled_only)

        Returns:
            List of LLM providers
        """
        async with self._session_factory() as session:
            query = select(LLMProviderORM).order_by(
                LLMProviderORM.priority,
                LLMProviderORM.provider_name,
            )

            if provider_type:
                query = query.where(LLMProviderORM.provider_type == provider_type)

            if enabled_only and not include_disabled:
                query = query.where(LLMProviderORM.is_enabled)

            result = await session.execute(query)
            orm_providers = result.scalars().all()
            return [self._orm_to_pydantic(p) for p in orm_providers]

    async def get_default_llm_provider(self) -> LLMProvider | None:
        """Get the default LLM provider."""
        async with self._session_factory() as session:
            result = await session.execute(
                select(LLMProviderORM).where(
                    LLMProviderORM.is_default,
                    LLMProviderORM.is_enabled,
                )
            )
            return result.scalar_one_or_none()

    def _encrypt_extra_config(self, extra_config: dict[str, Any]) -> dict[str, Any]:
        """
        Encrypt sensitive fields in extra_config.

        Encrypts fields like 'api_key', 'auth_token', 'secret' etc.
        """
        if not extra_config:
            return {}

        sensitive_keys = {"api_key", "auth_token", "secret", "password", "credential"}
        encrypted_config = {}

        for key, value in extra_config.items():
            if any(sensitive in key.lower() for sensitive in sensitive_keys) and isinstance(value, str):
                encrypted_config[key] = self.encrypt_api_key(value)
            else:
                encrypted_config[key] = value

        return encrypted_config

    def _decrypt_extra_config(self, extra_config: dict[str, Any]) -> dict[str, Any]:
        """
        Decrypt sensitive fields in extra_config.
        """
        if not extra_config:
            return {}

        sensitive_keys = {"api_key", "auth_token", "secret", "password", "credential"}
        decrypted_config = {}

        for key, value in extra_config.items():
            if any(sensitive in key.lower() for sensitive in sensitive_keys) and isinstance(value, str):
                try:
                    decrypted_config[key] = self.decrypt_api_key(value)
                except ValueError:
                    # If decryption fails, return as-is (might not be encrypted)
                    decrypted_config[key] = value
            else:
                decrypted_config[key] = value

        return decrypted_config

    async def create_llm_provider(
        self,
        provider: LLMProviderCreate,
        changed_by: str | None = None,
    ) -> LLMProvider:
        """Create a new LLM provider."""
        async with self._session_factory() as session:
            # If setting as default, unset other defaults of same type
            if provider.is_default:
                await session.execute(
                    update(LLMProviderORM)
                    .where(
                        LLMProviderORM.provider_type == provider.provider_type,
                        LLMProviderORM.is_default,
                    )
                    .values(is_default=False)
                )

            # Encrypt API key in extra_config if present
            extra_config = self._encrypt_extra_config(provider.extra_config or {})

            # Also encrypt api_key if passed in extra_config
            if hasattr(provider, "api_key") and provider.api_key:
                extra_config["api_key"] = self.encrypt_api_key(provider.api_key)

            new_provider = LLMProviderORM(
                provider_name=provider.provider_name,
                provider_type=provider.provider_type,
                base_url=provider.base_url,
                api_key_hint=provider.api_key_hint,
                default_model=provider.default_model,
                available_models=provider.available_models or [],
                model_aliases=provider.model_aliases or {},
                supports_streaming=provider.supports_streaming,
                supports_function_calling=provider.supports_function_calling,
                supports_vision=provider.supports_vision,
                max_tokens=provider.max_tokens,
                max_context_length=provider.max_context_length,
                rate_limit_requests_per_minute=provider.rate_limit_requests_per_minute,
                rate_limit_tokens_per_minute=provider.rate_limit_tokens_per_minute,
                is_enabled=provider.is_enabled,
                is_default=provider.is_default,
                priority=provider.priority,
                extra_config=extra_config,
            )

            session.add(new_provider)
            await session.commit()
            await session.refresh(new_provider)

            # Log the change
            await self._log_change(
                session,
                "llm_provider",
                new_provider.id,
                "create",
                None,
                self._orm_to_pydantic(provider),
                changed_by,
            )

            logger.info("LLM provider created", name=new_provider.provider_name)
            return new_provider

    async def update_llm_provider(
        self,
        provider_id: UUID,
        update: LLMProviderUpdate,
        changed_by: str | None = None,
    ) -> LLMProvider | None:
        """Update an LLM provider."""
        async with self._session_factory() as session:
            result = await session.execute(
                select(LLMProviderORM).where(LLMProviderORM.id == provider_id)
            )
            provider = result.scalar_one_or_none()

            if not provider:
                return None

            old_value = self._orm_to_pydantic(provider)

            update_data = update.model_dump(exclude_unset=True)
            for field, value in update_data.items():
                if value is not None:
                    setattr(provider, field, value)

            # If setting as default, unset other defaults of same type
            if update.is_default:
                await session.execute(
                    select(LLMProviderORM).update()
                    .where(
                        LLMProviderORM.provider_type == provider.provider_type,
                        LLMProviderORM.id != provider_id,
                        LLMProviderORM.is_default,
                    )
                    .values(is_default=False)
                )

            provider.updated_at = datetime.now(UTC)

            await session.commit()
            await session.refresh(provider)

            # Log the change
            await self._log_change(
                session,
                "llm_provider",
                provider.id,
                "update",
                old_value,
                self._orm_to_pydantic(provider),
                changed_by,
            )

            logger.info("LLM provider updated", name=provider.provider_name)
            return provider

    async def delete_llm_provider(
        self,
        provider_id: UUID,
        changed_by: str | None = None,
    ) -> bool:
        """Delete an LLM provider."""
        async with self._session_factory() as session:
            result = await session.execute(
                select(LLMProviderORM).where(LLMProviderORM.id == provider_id)
            )
            provider = result.scalar_one_or_none()

            if not provider:
                return False

            old_value = self._orm_to_pydantic(provider)

            await session.execute(
                delete(LLMProvider).where(LLMProviderORM.id == provider_id)
            )
            await session.commit()

            # Log the change
            await self._log_change(
                session,
                "llm_provider",
                provider.id,
                "delete",
                old_value,
                None,
                changed_by,
            )

            logger.info("LLM provider deleted", name=provider.provider_name)
            return True

    def get_llm_provider_api_key(self, provider: LLMProvider) -> str | None:
        """
        Get the decrypted API key for an LLM provider.

        Args:
            provider: The LLM provider object

        Returns:
            Decrypted API key or None if not found
        """
        if not provider.extra_config:
            return None
        return self.decrypt_api_key(provider.extra_config.get("api_key", ""))

    # =========================================================================
    # Embedding Provider CRUD
    # =========================================================================

    async def get_embedding_provider(
        self,
        provider_id: UUID,
    ) -> EmbeddingProvider | None:
        """Get an embedding provider by ID."""
        async with self._session_factory() as session:
            result = await session.execute(
                select(EmbeddingProviderORM).where(
                    EmbeddingProviderORM.id == provider_id
                )
            )
            return result.scalar_one_or_none()

    async def get_embedding_provider_by_name(
        self,
        provider_name: str,
    ) -> EmbeddingProvider | None:
        """Get an embedding provider by name."""
        async with self._session_factory() as session:
            result = await session.execute(
                select(EmbeddingProviderORM).where(
                    EmbeddingProviderORM.provider_name == provider_name
                )
            )
            return result.scalar_one_or_none()

    async def list_embedding_providers(
        self,
        provider_type: str | None = None,
        enabled_only: bool = False,
    ) -> list[EmbeddingProvider]:
        """List embedding providers with optional filtering."""
        async with self._session_factory() as session:
            query = select(EmbeddingProviderORM).order_by(
                EmbeddingProviderORM.priority,
                EmbeddingProviderORM.provider_name,
            )

            if provider_type:
                query = query.where(EmbeddingProviderORM.provider_type == provider_type)

            if enabled_only:
                query = query.where(EmbeddingProviderORM.is_enabled)

            result = await session.execute(query)
            orm_results = result.scalars().all()
            return [self._orm_to_pydantic(r) for r in orm_results]

    async def get_default_embedding_provider(
        self,
    ) -> EmbeddingProvider | None:
        """Get the default embedding provider."""
        async with self._session_factory() as session:
            result = await session.execute(
                select(EmbeddingProviderORM).where(
                    EmbeddingProviderORM.is_default,
                    EmbeddingProviderORM.is_enabled,
                )
            )
            return result.scalar_one_or_none()

    async def create_embedding_provider(
        self,
        provider: EmbeddingProviderCreate,
        changed_by: str | None = None,
    ) -> EmbeddingProvider:
        """Create a new embedding provider."""
        async with self._session_factory() as session:
            # If setting as default, unset other defaults of same type
            if provider.is_default:
                await session.execute(
                    select(EmbeddingProvider).update()
                    .where(
                        EmbeddingProviderORM.provider_type == provider.provider_type,
                        EmbeddingProviderORM.is_default,
                    )
                    .values(is_default=False)
                )

            # Encrypt API key in extra_config if present
            extra_config = self._encrypt_extra_config(provider.extra_config or {})

            # Also encrypt api_key if passed in extra_config
            if hasattr(provider, "api_key") and provider.api_key:
                extra_config["api_key"] = self.encrypt_api_key(provider.api_key)

            new_provider = EmbeddingProvider(
                provider_name=provider.provider_name,
                provider_type=provider.provider_type,
                base_url=provider.base_url,
                api_key_hint=provider.api_key_hint,
                default_model=provider.default_model,
                available_models=provider.available_models or [],
                embedding_dimensions=provider.embedding_dimensions,
                supported_input_formats=provider.supported_input_formats or ["text"],
                max_batch_size=provider.max_batch_size,
                max_tokens_per_batch=provider.max_tokens_per_batch,
                is_enabled=provider.is_enabled,
                is_default=provider.is_default,
                priority=provider.priority,
                extra_config=extra_config,
            )

            session.add(new_provider)
            await session.commit()
            await session.refresh(new_provider)

            # Log the change
            await self._log_change(
                session,
                "embedding_provider",
                new_provider.id,
                "create",
                None,
                self._orm_to_pydantic(provider),
                changed_by,
            )

            logger.info("Embedding provider created", name=new_provider.provider_name)
            return new_provider

    async def update_embedding_provider(
        self,
        provider_id: UUID,
        update: EmbeddingProviderUpdate,
        changed_by: str | None = None,
    ) -> EmbeddingProvider | None:
        """Update an embedding provider."""
        async with self._session_factory() as session:
            result = await session.execute(
                select(EmbeddingProviderORM).where(
                    EmbeddingProviderORM.id == provider_id
                )
            )
            provider = result.scalar_one_or_none()

            if not provider:
                return None

            old_value = self._orm_to_pydantic(provider)

            update_data = update.model_dump(exclude_unset=True)
            for field, value in update_data.items():
                if value is not None:
                    setattr(provider, field, value)

            # If setting as default, unset other defaults of same type
            if update.is_default:
                await session.execute(
                    select(EmbeddingProvider).update()
                    .where(
                        EmbeddingProviderORM.provider_type == provider.provider_type,
                        EmbeddingProviderORM.id != provider_id,
                        EmbeddingProviderORM.is_default,
                    )
                    .values(is_default=False)
                )

            provider.updated_at = datetime.now(UTC)

            await session.commit()
            await session.refresh(provider)

            # Log the change
            await self._log_change(
                session,
                "embedding_provider",
                provider.id,
                "update",
                old_value,
                self._orm_to_pydantic(provider),
                changed_by,
            )

            logger.info("Embedding provider updated", name=provider.provider_name)
            return provider

    async def delete_embedding_provider(
        self,
        provider_id: UUID,
        changed_by: str | None = None,
    ) -> bool:
        """Delete an embedding provider."""
        async with self._session_factory() as session:
            result = await session.execute(
                select(EmbeddingProviderORM).where(
                    EmbeddingProviderORM.id == provider_id
                )
            )
            provider = result.scalar_one_or_none()

            if not provider:
                return False

            old_value = self._orm_to_pydantic(provider)

            await session.execute(
                delete(EmbeddingProvider).where(
                    EmbeddingProviderORM.id == provider_id
                )
            )
            await session.commit()

            # Log the change
            await self._log_change(
                session,
                "embedding_provider",
                provider.id,
                "delete",
                old_value,
                None,
                changed_by,
            )

            logger.info("Embedding provider deleted", name=provider.provider_name)
            return True

    def get_embedding_provider_api_key(self, provider: EmbeddingProvider) -> str | None:
        """
        Get the decrypted API key for an embedding provider.

        Args:
            provider: The embedding provider object

        Returns:
            Decrypted API key or None if not found
        """
        if not provider.extra_config:
            return None
        return self.decrypt_api_key(provider.extra_config.get("api_key", ""))

    # =========================================================================
    # Agent Configuration CRUD
    # =========================================================================

    async def get_agent_config(self, config_id: UUID) -> AgentConfig | None:
        """Get an agent configuration by ID."""
        async with self._session_factory() as session:
            result = await session.execute(
                select(AgentConfig).where(AgentConfig.id == config_id)
            )
            return result.scalar_one_or_none()

    async def get_agent_config_by_type(
        self,
        agent_type: str,
        agent_id: str | None = None,
    ) -> AgentConfig | None:
        """Get an agent configuration by type and optional agent ID."""
        async with self._session_factory() as session:
            query = select(AgentConfig).where(
                AgentConfig.agent_type == agent_type,
                AgentConfig.is_active,
            )

            if agent_id:
                query = query.where(AgentConfig.agent_id == agent_id)
            else:
                query = query.where(AgentConfig.is_default_for_type)

            result = await session.execute(query)
            return result.scalar_one_or_none()

    async def list_agent_configs(
        self,
        agent_type: str | None = None,
        active_only: bool = True,
    ) -> list[AgentConfig]:
        """List agent configurations with optional filtering."""
        async with self._session_factory() as session:
            query = select(AgentConfig).order_by(
                AgentConfig.agent_type,
                AgentConfig.config_name,
            )

            if agent_type:
                query = query.where(AgentConfig.agent_type == agent_type)

            if active_only:
                query = query.where(AgentConfig.is_active)

            result = await session.execute(query)
            orm_results = result.scalars().all()
            return [self._orm_to_pydantic(r) for r in orm_results]

    async def create_agent_config(
        self,
        config: AgentConfigCreate,
        changed_by: str | None = None,
    ) -> AgentConfig:
        """Create a new agent configuration."""
        async with self._session_factory() as session:
            # If setting as default for type, unset other defaults
            if config.is_default_for_type:
                await session.execute(
                    select(AgentConfig).update()
                    .where(
                        AgentConfig.agent_type == config.agent_type,
                        AgentConfig.is_default_for_type,
                    )
                    .values(is_default_for_type=False)
                )

            new_config = AgentConfig(
                agent_type=config.agent_type,
                agent_id=config.agent_id,
                config_name=config.config_name,
                config_data=config.config_data,
                llm_provider_id=config.llm_provider_id,
                embedding_provider_id=config.embedding_provider_id,
                is_active=config.is_active,
                is_default_for_type=config.is_default_for_type,
                description=config.description,
                tags=config.tags or [],
                created_by=changed_by,
            )

            session.add(new_config)
            await session.commit()
            await session.refresh(new_config)

            # Log the change
            await self._log_change(
                session,
                "agent_config",
                new_config.id,
                "create",
                None,
                self._orm_to_pydantic(config),
                changed_by,
            )

            logger.info("Agent config created", name=new_config.config_name)
            return new_config

    async def update_agent_config(
        self,
        config_id: UUID,
        update: AgentConfigUpdate,
        changed_by: str | None = None,
    ) -> AgentConfig | None:
        """Update an agent configuration."""
        async with self._session_factory() as session:
            result = await session.execute(
                select(AgentConfig).where(AgentConfig.id == config_id)
            )
            config = result.scalar_one_or_none()

            if not config:
                return None

            old_value = self._orm_to_pydantic(config)

            update_data = update.model_dump(exclude_unset=True)
            for field, value in update_data.items():
                if value is not None:
                    setattr(config, field, value)

            # If setting as default for type, unset other defaults
            if update.is_default_for_type:
                await session.execute(
                    select(AgentConfig).update()
                    .where(
                        AgentConfig.agent_type == config.agent_type,
                        AgentConfig.id != config_id,
                        AgentConfig.is_default_for_type,
                    )
                    .values(is_default_for_type=False)
                )

            config.updated_at = datetime.now(UTC)
            config.updated_by = changed_by

            await session.commit()
            await session.refresh(config)

            # Log the change
            await self._log_change(
                session,
                "agent_config",
                config.id,
                "update",
                old_value,
                self._orm_to_pydantic(config),
                changed_by,
            )

            logger.info("Agent config updated", name=config.config_name)
            return config

    async def delete_agent_config(
        self,
        config_id: UUID,
        changed_by: str | None = None,
    ) -> bool:
        """Delete an agent configuration."""
        async with self._session_factory() as session:
            result = await session.execute(
                select(AgentConfig).where(AgentConfig.id == config_id)
            )
            config = result.scalar_one_or_none()

            if not config:
                return False

            old_value = self._orm_to_pydantic(config)

            await session.execute(
                delete(AgentConfig).where(AgentConfig.id == config_id)
            )
            await session.commit()

            # Log the change
            await self._log_change(
                session,
                "agent_config",
                config.id,
                "delete",
                old_value,
                None,
                changed_by,
            )

            logger.info("Agent config deleted", name=config.config_name)
            return True

    # =========================================================================
    # Audit Logging
    # =========================================================================

    async def _log_change(
        self,
        session: AsyncSession,
        entity_type: str,
        entity_id: UUID,
        action: str,
        old_value: dict[str, Any] | None,
        new_value: dict[str, Any] | None,
        changed_by: str | None,
        reason: str | None = None,
    ) -> None:
        """Log a configuration change."""
        # Determine changed fields
        changed_fields = None
        if old_value and new_value:
            changed_fields = [
                k for k in old_value
                if k in new_value and old_value[k] != new_value[k]
            ]

        audit_log = ConfigAuditLog(
            entity_type=entity_type,
            entity_id=entity_id,
            action=action,
            old_value=old_value,
            new_value=new_value,
            changed_fields=changed_fields,
            changed_by=changed_by,
            change_reason=reason,
        )

        session.add(audit_log)

    async def get_audit_log(
        self,
        entity_type: str | None = None,
        entity_id: UUID | None = None,
        limit: int = 100,
    ) -> list[ConfigAuditLog]:
        """Get audit log entries."""
        async with self._session_factory() as session:
            query = select(ConfigAuditLog).order_by(
                ConfigAuditLog.changed_at.desc()
            ).limit(limit)

            if entity_type:
                query = query.where(ConfigAuditLog.entity_type == entity_type)

            if entity_id:
                query = query.where(ConfigAuditLog.entity_id == entity_id)

            result = await session.execute(query)
            orm_results = result.scalars().all()
            return [self._orm_to_pydantic(r) for r in orm_results]

    # =========================================================================
    # Import/Export
    # =========================================================================

    async def export_configurations(
        self,
        exported_by: str | None = None,
    ) -> ConfigurationExport:
        """Export all configurations."""
        async with self._session_factory() as session:
            # Get all configurations
            user_configs_result = await session.execute(
                select(UserConfigurationORM)
            )
            user_configs = list(user_configs_result.scalars().all())

            llm_providers_result = await session.execute(
                select(LLMProviderORM)
            )
            llm_providers = list(llm_providers_result.scalars().all())

            embedding_providers_result = await session.execute(
                select(EmbeddingProviderORM)
            )
            embedding_providers = list(embedding_providers_result.scalars().all())

            agent_configs_result = await session.execute(
                select(AgentConfig)
            )
            agent_configs = list(agent_configs_result.scalars().all())

            return ConfigurationExport(
                version="1.0",
                exported_at=datetime.now(UTC),
                exported_by=exported_by,
                user_configurations=user_configs,
                llm_providers=llm_providers,
                embedding_providers=embedding_providers,
                agent_configs=agent_configs,
            )

    async def import_configurations(
        self,
        import_data: ConfigurationImport,
        options: ImportOptions,
        changed_by: str | None = None,
    ) -> ImportResult:
        """Import configurations from a bundle."""
        result = ImportResult(success=True)

        try:
            # Import user configurations
            if options.import_user_configs and import_data.user_configurations:
                for config_data in import_data.user_configurations:
                    try:
                        config = UserConfigurationCreate(**config_data)
                        await self.create_config(config, changed_by)
                        result.imported_count["user_configurations"] = (
                            result.imported_count.get("user_configurations", 0) + 1
                        )
                    except Exception as e:
                        if options.skip_conflicts:
                            result.skipped_count["user_configurations"] = (
                                result.skipped_count.get("user_configurations", 0) + 1
                            )
                        else:
                            result.error_count["user_configurations"] = (
                                result.error_count.get("user_configurations", 0) + 1
                            )
                            result.errors.append(f"User config import error: {e}")

            # Import LLM providers
            if options.import_llm_providers and import_data.llm_providers:
                for provider_data in import_data.llm_providers:
                    try:
                        provider = LLMProviderCreate(**provider_data)
                        await self.create_llm_provider(provider, changed_by)
                        result.imported_count["llm_providers"] = (
                            result.imported_count.get("llm_providers", 0) + 1
                        )
                    except Exception as e:
                        if options.skip_conflicts:
                            result.skipped_count["llm_providers"] = (
                                result.skipped_count.get("llm_providers", 0) + 1
                            )
                        else:
                            result.error_count["llm_providers"] = (
                                result.error_count.get("llm_providers", 0) + 1
                            )
                            result.errors.append(f"LLM provider import error: {e}")

            # Import embedding providers
            if options.import_embedding_providers and import_data.embedding_providers:
                for provider_data in import_data.embedding_providers:
                    try:
                        provider = EmbeddingProviderCreate(**provider_data)
                        await self.create_embedding_provider(provider, changed_by)
                        result.imported_count["embedding_providers"] = (
                            result.imported_count.get("embedding_providers", 0) + 1
                        )
                    except Exception as e:
                        if options.skip_conflicts:
                            result.skipped_count["embedding_providers"] = (
                                result.skipped_count.get("embedding_providers", 0) + 1
                            )
                        else:
                            result.error_count["embedding_providers"] = (
                                result.error_count.get("embedding_providers", 0) + 1
                            )
                            result.errors.append(f"Embedding provider import error: {e}")

            # Import agent configs
            if options.import_agent_configs and import_data.agent_configs:
                for config_data in import_data.agent_configs:
                    try:
                        config = AgentConfigCreate(**config_data)
                        await self.create_agent_config(config, changed_by)
                        result.imported_count["agent_configs"] = (
                            result.imported_count.get("agent_configs", 0) + 1
                        )
                    except Exception as e:
                        if options.skip_conflicts:
                            result.skipped_count["agent_configs"] = (
                                result.skipped_count.get("agent_configs", 0) + 1
                            )
                        else:
                            result.error_count["agent_configs"] = (
                                result.error_count.get("agent_configs", 0) + 1
                            )
                            result.errors.append(f"Agent config import error: {e}")

        except Exception as e:
            result.success = False
            result.errors.append(f"Import failed: {e}")

        return result

    # =========================================================================
    # Validation
    # =========================================================================

    def _validate_config_value(
        self,
        value: Any,
        schema: dict[str, Any],
    ) -> None:
        """
        Validate a configuration value against a JSON schema.

        Args:
            value: The value to validate
            schema: JSON schema for validation

        Raises:
            ValueError: If validation fails
        """
        # Simple type validation
        expected_type = schema.get("type")
        if expected_type:
            type_map = {
                "string": str,
                "integer": int,
                "number": (int, float),
                "boolean": bool,
                "array": list,
                "object": dict,
            }

            expected_python_type = type_map.get(expected_type)
            if expected_python_type and not isinstance(value, expected_python_type):
                raise ValueError(
                    f"Expected type {expected_type}, got {type(value).__name__}"
                )

        # Min/max validation for numbers
        if isinstance(value, (int, float)):
            if "minimum" in schema and value < schema["minimum"]:
                raise ValueError(f"Value must be >= {schema['minimum']}")
            if "maximum" in schema and value > schema["maximum"]:
                raise ValueError(f"Value must be <= {schema['maximum']}")

        # Min/max length for strings
        if isinstance(value, str):
            if "minLength" in schema and len(value) < schema["minLength"]:
                raise ValueError(f"String length must be >= {schema['minLength']}")
            if "maxLength" in schema and len(value) > schema["maxLength"]:
                raise ValueError(f"String length must be <= {schema['maxLength']}")

        # Enum validation
        if "enum" in schema and value not in schema["enum"]:
            raise ValueError(f"Value must be one of: {schema['enum']}")

    # =========================================================================
    # Migration from .env
    # =========================================================================

    async def migrate_from_env(
        self,
        changed_by: str | None = "system",
    ) -> dict[str, Any]:
        """
        Migrate configuration from .env file to database.

        This method reads environment variables and creates corresponding
        database configurations. It's idempotent and safe to run multiple times.

        Returns:
            Migration result summary
        """
        migration_result = {
            "migrated": [],
            "skipped": [],
            "errors": [],
        }

        # Define environment variable mappings for configs
        config_mappings = [
            # Rate limiting
            ("RATE_LIMIT_ENABLED", "rate_limit.enabled", ConfigType.BOOLEAN),
            # Memory
            ("MEMORY_MAX_SIZE", "memory.max_size", ConfigType.INTEGER),
            ("MEMORY_DEFAULT_TTL", "memory.default_ttl", ConfigType.INTEGER),
            # Consciousness
            ("CONSCIOUSNESS_PHI_THRESHOLD", "consciousness.phi_threshold", ConfigType.FLOAT),
            # Consensus
            ("CONSENSUS_MIN_VOTES", "consensus.min_votes", ConfigType.INTEGER),
            ("CONSENSUS_CONFIDENCE_THRESHOLD", "consensus.confidence_threshold", ConfigType.FLOAT),
        ]

        for env_var, config_key, config_type in config_mappings:
            env_value = os.environ.get(env_var)

            if env_value is None:
                migration_result["skipped"].append(
                    f"{env_var} not set in environment"
                )
                continue

            try:
                # Convert value based on type
                if config_type == ConfigType.BOOLEAN:
                    converted_value = env_value.lower() in ("true", "1", "yes")
                elif config_type == ConfigType.INTEGER:
                    converted_value = int(env_value)
                elif config_type == ConfigType.FLOAT:
                    converted_value = float(env_value)
                else:
                    converted_value = env_value

                # Check if config already exists
                existing = await self.get_config(config_key)

                if existing:
                    migration_result["skipped"].append(
                        f"{config_key} already exists in database"
                    )
                    continue

                # Create new configuration
                config = UserConfigurationCreate(
                    config_key=config_key,
                    config_value=converted_value,
                    config_type=config_type,
                    description=f"Migrated from {env_var} environment variable",
                    category=config_key.split(".")[0] if "." in config_key else "general",
                )

                await self.create_config(config, changed_by)
                migration_result["migrated"].append(
                    f"Migrated {env_var} -> {config_key}"
                )

            except Exception as e:
                migration_result["errors"].append(
                    f"Error migrating {env_var}: {e}"
                )

        # Migrate LLM providers from environment variables
        llm_env_vars = {
            "OPENAI_API_KEY": os.environ.get("OPENAI_API_KEY"),
            "OPENAI_BASE_URL": os.environ.get("OPENAI_BASE_URL"),
            "LLM_MODEL": os.environ.get("LLM_MODEL"),
        }

        if any(llm_env_vars.values()):
            try:
                existing_llm = await self.get_llm_provider_by_name("openai_compatible")
                if existing_llm is None:
                    llm_provider = LLMProviderCreate(
                        provider_name="openai_compatible",
                        provider_type=LLMProviderType.OPENAI_COMPATIBLE,
                        base_url=os.environ.get("OPENAI_BASE_URL", "https://api.minimax.io/v1"),
                        api_key=os.environ.get("OPENAI_API_KEY"),
                        default_model=os.environ.get("LLM_MODEL", "MiniMax-M2.7"),
                        is_default=True,
                        is_enabled=True,
                        priority=1,
                    )
                    await self.create_llm_provider(llm_provider, changed_by)
                    migration_result["migrated"].append("LLM provider from OPENAI_* env vars")
                    logger.info("migrated_llm_provider_from_env")
                else:
                    migration_result["skipped"].append("LLM provider already exists")
            except Exception as e:
                migration_result["errors"].append(f"Error migrating LLM provider: {e}")

        # Migrate Embedding providers from environment variables
        embedding_env_vars = {
            "EMBEDDING_API_KEY": os.environ.get("EMBEDDING_API_KEY"),
            "EMBEDDING_BASE_URL": os.environ.get("EMBEDDING_BASE_URL"),
            "EMBEDDER_MODEL": os.environ.get("EMBEDDER_MODEL"),
        }

        if any(embedding_env_vars.values()):
            try:
                existing_embedding = await self.get_embedding_provider_by_name("openai_compatible")
                if existing_embedding is None:
                    embedding_provider = EmbeddingProviderCreate(
                        provider_name="openai_compatible",
                        provider_type=EmbeddingProviderType.OPENAI_COMPATIBLE,
                        base_url=os.environ.get("EMBEDDING_BASE_URL", "http://127.0.0.1:13305/api/v1"),
                        api_key=os.environ.get("EMBEDDING_API_KEY"),
                        model_name=os.environ.get("EMBEDDER_MODEL", "nomic-embed-text-v2-moe-GGUF"),
                        dimensions=int(os.environ.get("EMBEDDING_DIMENSIONS", "768")),
                        is_default=True,
                        is_enabled=True,
                        priority=1,
                    )
                    await self.create_embedding_provider(embedding_provider, changed_by)
                    migration_result["migrated"].append("Embedding provider from EMBEDDING_* env vars")
                    logger.info("migrated_embedding_provider_from_env")
                else:
                    migration_result["skipped"].append("Embedding provider already exists")
            except Exception as e:
                migration_result["errors"].append(f"Error migrating Embedding provider: {e}")

        logger.info("Environment migration complete", result=migration_result)
        return migration_result


# Global service instance (lazy initialization)
_config_service: ConfigurationService | None = None


def get_config_service() -> ConfigurationService:
    """Get or create the global configuration service instance."""
    global _config_service
    if _config_service is None:
        _config_service = ConfigurationService()
    return _config_service


async def initialize_config_service() -> None:
    """Initialize the global configuration service."""
    service = get_config_service()
    await service.initialize()


async def shutdown_config_service() -> None:
    """Shutdown the global configuration service."""
    global _config_service
    if _config_service:
        await _config_service.shutdown()
        _config_service = None
