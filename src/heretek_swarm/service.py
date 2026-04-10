"""
Configuration Service

Provides CRUD operations for configurations with caching and validation.
Supports migration from .env to database-backed configuration.
Features API key encryption using Fernet symmetric encryption.
"""


import base64
import os
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, TypeVar
from uuid import UUID

import structlog
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from .models import (
    UserConfiguration,
    UserConfigurationCreate,
    UserConfigurationUpdate,
    LLMProvider,
    LLMProviderCreate,
    LLMProviderUpdate,
    EmbeddingProvider,
    EmbeddingProviderCreate,
    EmbeddingProviderUpdate,
    AgentConfig,
    AgentConfigCreate,
    AgentConfigUpdate,
    ConfigAuditLog,
    ConfigCacheEntry,
    ConfigurationExport,
    ConfigurationImport,
    ImportOptions,
    ImportResult,
    ConfigType,
)

# Fernet encryption for API keys
try:
    from cryptography.fernet import Fernet
    CRYPTOGRAPHY_AVAILABLE = True
except ImportError:
    CRYPTOGRAPHY_AVAILABLE = False
    _Fernet = None

_logger = structlog.get_logger("config.service")

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

    def __init__(self, database_url: Optional[str]):
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
            _echo = False,
            _pool_pre_ping = True,
        )
        
        self._session_factory = async_sessionmaker(
            self._engine,
            _class_ = AsyncSession,
            _expire_on_commit = False,
        )
        
        # In-memory cache for frequently accessed configurations
        self._cache: Dict[str, ConfigCacheEntry] = {}
        self._cache_ttl = timedelta(minutes=5)
        
        # Initialize Fernet encryption for API keys
        self._fernet: Optional[Fernet] = None
        self._encryption_key = os.environ.get("CONFIG_ENCRYPTION_KEY")
        if self._encryption_key:
            self._initialize_encryption()
        else:
            logger.warning("CONFIG_ENCRYPTION_KEY not set - API keys will not be encrypted")
        
        logger.info("ConfigurationService initialized", database_url=self.database_url)

    def _initialize_encryption(self) -> None:
        """
        Initialize Fernet encryption for API keys.
        
        The encryption key should be a 32-byte URL-safe base64-encoded key.
        Generate with: Fernet.generate_key().decode()
        """
        if not CRYPTOGRAPHY_AVAILABLE:
            logger.error("cryptography package not installed - encryption disabled")
            return
        
        try:
            # Handle both raw keys and URL-safe base64 encoded keys
            if len(self._encryption_key) == 44 and self._encryption_key.endswith('='):
                # Already base64 encoded
                key = self._encryption_key.encode()
            else:
                # Raw key - encode it
                key = base64.urlsafe_b64encode(self._encryption_key.encode().ljust(32))
            
            self._fernet = Fernet(key)
            logger.info("API key encryption initialized")
        except Exception as e:
            logger.error("Failed to initialize encryption", error=str(e))
            self._fernet = None

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
        if not self._fernet:
            # Return as-is if encryption not configured (backward compatibility)
            return api_key
        
        try:
            _encrypted = self._fernet.encrypt(api_key.encode())
            return encrypted.decode()
        except Exception as e:
            logger.error("Failed to encrypt API key", error=str(e))
            raise ValueError(f"Encryption failed: {e}")

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
        if not self._fernet:
            # Return as-is if encryption not configured (backward compatibility)
            return encrypted_key
        
        try:
            _decrypted = self._fernet.decrypt(encrypted_key.encode())
            return decrypted.decode()
        except Exception as e:
            logger.error("Failed to decrypt API key", error=str(e))
            raise ValueError(f"Decryption failed: {e}")

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
                _result = await session.execute(
                    select(UserConfiguration).where(
                        UserConfiguration.category.in_(["system", "rate_limiting"])
                    )
                )
                _configs = result.scalars().all()
                
                for config in configs:
                    _cache_key = f"config:{config.config_key}"
                    self._cache[cache_key] = ConfigCacheEntry(
                        _cache_key = cache_key,
                        cache_value={"value": config.config_value, "type": config.config_type.value},
                        expires_at=datetime.utcnow() + self._cache_ttl,
                    )
        except Exception as e:
            logger.warning("cache_warmup_skipped", reason=str(e))

    def _get_cache_key(self, entity_type: str, key: str) -> str:
        """Generate a cache key for an entity."""
        return f"{entity_type}:{key}"

    def _invalidate_cache(self, entity_type: str, key: str) -> None:
        """Invalidate a cache entry."""
        _cache_key = self._get_cache_key(entity_type, key)
        if cache_key in self._cache:
            del self._cache[cache_key]

    def _set_cache(self, entity_type: str, key: str, value: Any, ttl: Optional[timedelta]) -> None:
        """Set a cache entry."""
        _cache_key = self._get_cache_key(entity_type, key)
        self._cache[cache_key] = ConfigCacheEntry(
            _cache_key = cache_key,
            cache_value={"value": value},
            expires_at=datetime.utcnow() + (ttl or self._cache_ttl),
        )

    def _get_cache(self, entity_type: str, key: str) -> Optional[Any]:
        """Get a cached value if available and not expired."""
        _cache_key = self._get_cache_key(entity_type, key)
        _entry = self._cache.get(cache_key)
        
        if entry is None:
            return None
        
        if entry.expires_at and datetime.utcnow() > entry.expires_at:
            del self._cache[cache_key]
            return None
        
        entry.access_count += 1
        entry.last_accessed_at = datetime.utcnow()
        return entry.cache_value.get("value")

    # =========================================================================
    # User Configuration CRUD
    # =========================================================================

    async def get_config(self, config_key: str) -> Optional[UserConfiguration]:
        """
        Get a configuration by key.
        
        Args:
            config_key: The configuration key
            
        Returns:
            Configuration if found, None otherwise
        """
        # Check cache first
        _cached = self._get_cache("config", config_key)
        if cached is not None:
            logger.debug("Cache hit for config", key=config_key)
            return UserConfiguration(**cached)
        
        async with self._session_factory() as session:
            _result = await session.execute(
                select(UserConfiguration).where(
                    UserConfiguration.config_key == config_key
                )
            )
            config = result.scalar_one_or_none()
            
            if config:
                self._set_cache("config", config_key, config.model_dump())
            
            return config

    async def get_config_value(self, config_key: str, default: Any) -> Any:
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

    async def list_configs(self, category: Optional[str], limit: int, offset: int) -> List[UserConfiguration]:
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
            _query = select(UserConfiguration)
            
            if category:
                _query = query.where(UserConfiguration.category == category)
            
            _query = query.order_by(UserConfiguration.config_key).offset(offset).limit(limit)
            
            _result = await session.execute(query)
            return list(result.scalars().all())

    async def create_config(self, config: UserConfigurationCreate, changed_by: Optional[str]) -> UserConfiguration:
        """
        Create a new configuration.
        
        Args:
            config: Configuration data
            changed_by: User making the change
            
        Returns:
            Created configuration
        """
        async with self._session_factory() as session:
            _new_config = UserConfiguration(
                config_key=config.config_key,
                config_value=config.config_value,
                _config_type = config.config_type,
                _description = config.description,
                _category = config.category,
                _is_sensitive = config.is_sensitive,
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
                new_config.model_dump(),
                changed_by,
            )
            
            # Invalidate cache
            self._invalidate_cache("config", new_config.config_key)
            
            logger.info("Configuration created", key=new_config.config_key)
            return new_config

    async def update_config(self, config_key: str, update: UserConfigurationUpdate, changed_by: Optional[str]) -> Optional[UserConfiguration]:
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
            _result = await session.execute(
                select(UserConfiguration).where(
                    UserConfiguration.config_key == config_key
                )
            )
            config = result.scalar_one_or_none()
            
            if not config:
                return None
            
            if not config.is_editable:
                raise ValueError(f"Configuration {config_key} is not editable")
            
            _old_value = config.model_dump()
            
            _update_data = update.model_dump(exclude_unset=True)
            for field, value in update_data.items():
                if value is not None:
                    setattr(config, field, value)
            
            # Validate if schema exists
            if config.validation_schema and update.config_value is not None:
                self._validate_config_value(
                    update.config_value,
                    config.validation_schema,
                )
            
            config.updated_at = datetime.utcnow()
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
                config.model_dump(),
                changed_by,
            )
            
            # Invalidate cache
            self._invalidate_cache("config", config_key)
            
            logger.info("Configuration updated", key=config_key)
            return config

    async def delete_config(self, config_key: str, changed_by: Optional[str]) -> bool:
        """
        Delete a configuration.
        
        Args:
            config_key: The configuration key
            changed_by: User making the change
            
        Returns:
            True if deleted, False if not found
        """
        async with self._session_factory() as session:
            _result = await session.execute(
                select(UserConfiguration).where(
                    UserConfiguration.config_key == config_key
                )
            )
            config = result.scalar_one_or_none()
            
            if not config:
                return False
            
            if not config.is_editable:
                raise ValueError(f"Configuration {config_key} is not deletable")
            
            _old_value = config.model_dump()
            
            await session.execute(
                delete(UserConfiguration).where(
                    UserConfiguration.config_key == config_key
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

    async def get_llm_provider(self, provider_id: UUID) -> Optional[LLMProvider]:
        """Get an LLM provider by ID."""
        async with self._session_factory() as session:
            _result = await session.execute(
                select(LLMProvider).where(LLMProvider.id == provider_id)
            )
            return result.scalar_one_or_none()

    async def get_llm_provider_by_name(self, provider_name: str) -> Optional[LLMProvider]:
        """Get an LLM provider by name."""
        async with self._session_factory() as session:
            _result = await session.execute(
                select(LLMProvider).where(
                    LLMProvider.provider_name == provider_name
                )
            )
            return result.scalar_one_or_none()

    async def list_llm_providers(self, provider_type: Optional[str], enabled_only: bool, include_disabled: bool) -> List[LLMProvider]:
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
            _query = select(LLMProvider).order_by(
                LLMProvider.priority,
                LLMProvider.provider_name,
            )
            
            if provider_type:
                _query = query.where(LLMProvider.provider_type == provider_type)
            
            if enabled_only and not include_disabled:
                _query = query.where(LLMProvider.is_enabled == True)
            
            _result = await session.execute(query)
            return list(result.scalars().all())

    async def get_default_llm_provider(self) -> Optional[LLMProvider]:
        """Get the default LLM provider."""
        async with self._session_factory() as session:
            _result = await session.execute(
                select(LLMProvider).where(
                    LLMProvider.is_default == True,
                    LLMProvider.is_enabled == True,
                )
            )
            return result.scalar_one_or_none()

    def _encrypt_extra_config(self, extra_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Encrypt sensitive fields in extra_config.
        
        Encrypts fields like 'api_key', 'auth_token', 'secret' etc.
        """
        if not extra_config:
            return {}
        
        _sensitive_keys = {'api_key', 'auth_token', 'secret', 'password', 'credential'}
        _encrypted_config = {}
        
        for key, value in extra_config.items():
            if any(sensitive in key.lower() for sensitive in sensitive_keys) and isinstance(value, str):
                encrypted_config[key] = self.encrypt_api_key(value)
            else:
                encrypted_config[key] = value
        
        return encrypted_config

    def _decrypt_extra_config(self, extra_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Decrypt sensitive fields in extra_config.
        """
        if not extra_config:
            return {}
        
        _sensitive_keys = {'api_key', 'auth_token', 'secret', 'password', 'credential'}
        _decrypted_config = {}
        
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

    async def create_llm_provider(self, provider: LLMProviderCreate, changed_by: Optional[str]) -> LLMProvider:
        """Create a new LLM provider."""
        async with self._session_factory() as session:
            # If setting as default, unset other defaults of same type
            if provider.is_default:
                await session.execute(
                    select(LLMProvider).update()
                    .where(
                        LLMProvider.provider_type == provider.provider_type,
                        LLMProvider.is_default == True,
                    )
                    .values(is_default=False)
                )
            
            # Encrypt API key in extra_config if present
            extra_config = self._encrypt_extra_config(provider.extra_config or {})
            
            # Also encrypt api_key if passed in extra_config
            if hasattr(provider, 'api_key') and provider.api_key:
                extra_config['api_key'] = self.encrypt_api_key(provider.api_key)
            
            _new_provider = LLMProvider(
                provider_name=provider.provider_name,
                provider_type=provider.provider_type,
                _base_url = provider.base_url,
                _api_key_hint = provider.api_key_hint,
                _default_model = provider.default_model,
                _available_models = provider.available_models or [],
                _model_aliases = provider.model_aliases or {},
                _supports_streaming = provider.supports_streaming,
                _supports_function_calling = provider.supports_function_calling,
                _supports_vision = provider.supports_vision,
                max_tokens=provider.max_tokens,
                _max_context_length = provider.max_context_length,
                _rate_limit_requests_per_minute = provider.rate_limit_requests_per_minute,
                _rate_limit_tokens_per_minute = provider.rate_limit_tokens_per_minute,
                _is_enabled = provider.is_enabled,
                is_default=provider.is_default,
                _priority = provider.priority,
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
                new_provider.model_dump(),
                changed_by,
            )
            
            logger.info("LLM provider created", name=new_provider.provider_name)
            return new_provider

    async def update_llm_provider(self, provider_id: UUID, update: LLMProviderUpdate, changed_by: Optional[str]) -> Optional[LLMProvider]:
        """Update an LLM provider."""
        async with self._session_factory() as session:
            _result = await session.execute(
                select(LLMProvider).where(LLMProvider.id == provider_id)
            )
            provider = result.scalar_one_or_none()
            
            if not provider:
                return None
            
            _old_value = provider.model_dump()
            
            _update_data = update.model_dump(exclude_unset=True)
            for field, value in update_data.items():
                if value is not None:
                    setattr(provider, field, value)
            
            # If setting as default, unset other defaults of same type
            if update.is_default:
                await session.execute(
                    select(LLMProvider).update()
                    .where(
                        LLMProvider.provider_type == provider.provider_type,
                        LLMProvider.id != provider_id,
                        LLMProvider.is_default == True,
                    )
                    .values(is_default=False)
                )
            
            provider.updated_at = datetime.utcnow()
            
            await session.commit()
            await session.refresh(provider)
            
            # Log the change
            await self._log_change(
                session,
                "llm_provider",
                provider.id,
                "update",
                old_value,
                provider.model_dump(),
                changed_by,
            )
            
            logger.info("LLM provider updated", name=provider.provider_name)
            return provider

    async def delete_llm_provider(self, provider_id: UUID, changed_by: Optional[str]) -> bool:
        """Delete an LLM provider."""
        async with self._session_factory() as session:
            _result = await session.execute(
                select(LLMProvider).where(LLMProvider.id == provider_id)
            )
            provider = result.scalar_one_or_none()
            
            if not provider:
                return False
            
            _old_value = provider.model_dump()
            
            await session.execute(
                delete(LLMProvider).where(LLMProvider.id == provider_id)
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

    def get_llm_provider_api_key(self, provider: LLMProvider) -> Optional[str]:
        """
        Get the decrypted API key for an LLM provider.
        
        Args:
            provider: The LLM provider object
            
        Returns:
            Decrypted API key or None if not found
        """
        if not provider.extra_config:
            return None
        return self.decrypt_api_key(provider.extra_config.get('api_key', ''))

    # =========================================================================
    # Embedding Provider CRUD
    # =========================================================================

    async def get_embedding_provider(self, provider_id: UUID) -> Optional[EmbeddingProvider]:
        """Get an embedding provider by ID."""
        async with self._session_factory() as session:
            _result = await session.execute(
                select(EmbeddingProvider).where(
                    EmbeddingProvider.id == provider_id
                )
            )
            return result.scalar_one_or_none()

    async def get_embedding_provider_by_name(self, provider_name: str) -> Optional[EmbeddingProvider]:
        """Get an embedding provider by name."""
        async with self._session_factory() as session:
            _result = await session.execute(
                select(EmbeddingProvider).where(
                    EmbeddingProvider.provider_name == provider_name
                )
            )
            return result.scalar_one_or_none()

    async def list_embedding_providers(self, provider_type: Optional[str], enabled_only: bool) -> List[EmbeddingProvider]:
        """List embedding providers with optional filtering."""
        async with self._session_factory() as session:
            _query = select(EmbeddingProvider).order_by(
                EmbeddingProvider.priority,
                EmbeddingProvider.provider_name,
            )
            
            if provider_type:
                _query = query.where(EmbeddingProvider.provider_type == provider_type)
            
            if enabled_only:
                _query = query.where(EmbeddingProvider.is_enabled == True)
            
            _result = await session.execute(query)
            return list(result.scalars().all())

    async def get_default_embedding_provider(self) -> Optional[EmbeddingProvider]:
        """Get the default embedding provider."""
        async with self._session_factory() as session:
            _result = await session.execute(
                select(EmbeddingProvider).where(
                    EmbeddingProvider.is_default == True,
                    EmbeddingProvider.is_enabled == True,
                )
            )
            return result.scalar_one_or_none()

    async def create_embedding_provider(self, provider: EmbeddingProviderCreate, changed_by: Optional[str]) -> EmbeddingProvider:
        """Create a new embedding provider."""
        async with self._session_factory() as session:
            # If setting as default, unset other defaults of same type
            if provider.is_default:
                await session.execute(
                    select(EmbeddingProvider).update()
                    .where(
                        EmbeddingProvider.provider_type == provider.provider_type,
                        EmbeddingProvider.is_default == True,
                    )
                    .values(is_default=False)
                )
            
            # Encrypt API key in extra_config if present
            extra_config = self._encrypt_extra_config(provider.extra_config or {})
            
            # Also encrypt api_key if passed in extra_config
            if hasattr(provider, 'api_key') and provider.api_key:
                extra_config['api_key'] = self.encrypt_api_key(provider.api_key)
            
            _new_provider = EmbeddingProvider(
                provider_name=provider.provider_name,
                provider_type=provider.provider_type,
                _base_url = provider.base_url,
                _api_key_hint = provider.api_key_hint,
                _default_model = provider.default_model,
                _available_models = provider.available_models or [],
                _embedding_dimensions = provider.embedding_dimensions,
                _supported_input_formats = provider.supported_input_formats or ["text"],
                _max_batch_size = provider.max_batch_size,
                _max_tokens_per_batch = provider.max_tokens_per_batch,
                _is_enabled = provider.is_enabled,
                is_default=provider.is_default,
                _priority = provider.priority,
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
                new_provider.model_dump(),
                changed_by,
            )
            
            logger.info("Embedding provider created", name=new_provider.provider_name)
            return new_provider

    async def update_embedding_provider(self, provider_id: UUID, update: EmbeddingProviderUpdate, changed_by: Optional[str]) -> Optional[EmbeddingProvider]:
        """Update an embedding provider."""
        async with self._session_factory() as session:
            _result = await session.execute(
                select(EmbeddingProvider).where(
                    EmbeddingProvider.id == provider_id
                )
            )
            provider = result.scalar_one_or_none()
            
            if not provider:
                return None
            
            _old_value = provider.model_dump()
            
            _update_data = update.model_dump(exclude_unset=True)
            for field, value in update_data.items():
                if value is not None:
                    setattr(provider, field, value)
            
            # If setting as default, unset other defaults of same type
            if update.is_default:
                await session.execute(
                    select(EmbeddingProvider).update()
                    .where(
                        EmbeddingProvider.provider_type == provider.provider_type,
                        EmbeddingProvider.id != provider_id,
                        EmbeddingProvider.is_default == True,
                    )
                    .values(is_default=False)
                )
            
            provider.updated_at = datetime.utcnow()
            
            await session.commit()
            await session.refresh(provider)
            
            # Log the change
            await self._log_change(
                session,
                "embedding_provider",
                provider.id,
                "update",
                old_value,
                provider.model_dump(),
                changed_by,
            )
            
            logger.info("Embedding provider updated", name=provider.provider_name)
            return provider

    async def delete_embedding_provider(self, provider_id: UUID, changed_by: Optional[str]) -> bool:
        """Delete an embedding provider."""
        async with self._session_factory() as session:
            _result = await session.execute(
                select(EmbeddingProvider).where(
                    EmbeddingProvider.id == provider_id
                )
            )
            provider = result.scalar_one_or_none()
            
            if not provider:
                return False
            
            _old_value = provider.model_dump()
            
            await session.execute(
                delete(EmbeddingProvider).where(
                    EmbeddingProvider.id == provider_id
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

    def get_embedding_provider_api_key(self, provider: EmbeddingProvider) -> Optional[str]:
        """
        Get the decrypted API key for an embedding provider.
        
        Args:
            provider: The embedding provider object
            
        Returns:
            Decrypted API key or None if not found
        """
        if not provider.extra_config:
            return None
        return self.decrypt_api_key(provider.extra_config.get('api_key', ''))

    # =========================================================================
    # Agent Configuration CRUD
    # =========================================================================

    async def get_agent_config(self, config_id: UUID) -> Optional[AgentConfig]:
        """Get an agent configuration by ID."""
        async with self._session_factory() as session:
            _result = await session.execute(
                select(AgentConfig).where(AgentConfig.id == config_id)
            )
            return result.scalar_one_or_none()

    async def get_agent_config_by_type(self, agent_type: str, agent_id: Optional[str]) -> Optional[AgentConfig]:
        """Get an agent configuration by type and optional agent ID."""
        async with self._session_factory() as session:
            _query = select(AgentConfig).where(
                AgentConfig.agent_type == agent_type,
                AgentConfig.is_active == True,
            )
            
            if agent_id:
                _query = query.where(AgentConfig.agent_id == agent_id)
            else:
                _query = query.where(AgentConfig.is_default_for_type == True)
            
            _result = await session.execute(query)
            return result.scalar_one_or_none()

    async def list_agent_configs(self, agent_type: Optional[str], active_only: bool) -> List[AgentConfig]:
        """List agent configurations with optional filtering."""
        async with self._session_factory() as session:
            _query = select(AgentConfig).order_by(
                AgentConfig.agent_type,
                AgentConfig.config_name,
            )
            
            if agent_type:
                _query = query.where(AgentConfig.agent_type == agent_type)
            
            if active_only:
                _query = query.where(AgentConfig.is_active == True)
            
            _result = await session.execute(query)
            return list(result.scalars().all())

    async def create_agent_config(self, config: AgentConfigCreate, changed_by: Optional[str]) -> AgentConfig:
        """Create a new agent configuration."""
        async with self._session_factory() as session:
            # If setting as default for type, unset other defaults
            if config.is_default_for_type:
                await session.execute(
                    select(AgentConfig).update()
                    .where(
                        AgentConfig.agent_type == config.agent_type,
                        AgentConfig.is_default_for_type == True,
                    )
                    .values(is_default_for_type=False)
                )
            
            _new_config = AgentConfig(
                agent_type=config.agent_type,
                _agent_id = config.agent_id,
                config_name=config.config_name,
                _config_data = config.config_data,
                _llm_provider_id = config.llm_provider_id,
                _embedding_provider_id = config.embedding_provider_id,
                _is_active = config.is_active,
                is_default_for_type=config.is_default_for_type,
                _description = config.description,
                _tags = config.tags or [],
                _created_by = changed_by,
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
                new_config.model_dump(),
                changed_by,
            )
            
            logger.info("Agent config created", name=new_config.config_name)
            return new_config

    async def update_agent_config(self, config_id: UUID, update: AgentConfigUpdate, changed_by: Optional[str]) -> Optional[AgentConfig]:
        """Update an agent configuration."""
        async with self._session_factory() as session:
            _result = await session.execute(
                select(AgentConfig).where(AgentConfig.id == config_id)
            )
            config = result.scalar_one_or_none()
            
            if not config:
                return None
            
            _old_value = config.model_dump()
            
            _update_data = update.model_dump(exclude_unset=True)
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
                        AgentConfig.is_default_for_type == True,
                    )
                    .values(is_default_for_type=False)
                )
            
            config.updated_at = datetime.utcnow()
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
                config.model_dump(),
                changed_by,
            )
            
            logger.info("Agent config updated", name=config.config_name)
            return config

    async def delete_agent_config(self, config_id: UUID, changed_by: Optional[str]) -> bool:
        """Delete an agent configuration."""
        async with self._session_factory() as session:
            _result = await session.execute(
                select(AgentConfig).where(AgentConfig.id == config_id)
            )
            config = result.scalar_one_or_none()
            
            if not config:
                return False
            
            _old_value = config.model_dump()
            
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

    async def _log_change(self, session: AsyncSession, entity_type: str, entity_id: UUID, action: str, old_value: Optional[Dict[str, Any]], new_value: Optional[Dict[str, Any]], changed_by: Optional[str], reason: Optional[str]) -> None:
        """Log a configuration change."""
        # Determine changed fields
        _changed_fields = None
        if old_value and new_value:
            _changed_fields = [
                k for k in old_value.keys()
                if k in new_value and old_value[k] != new_value[k]
            ]
        
        _audit_log = ConfigAuditLog(
            entity_type=entity_type,
            entity_id=entity_id,
            _action = action,
            _old_value = old_value,
            _new_value = new_value,
            _changed_fields = changed_fields,
            _changed_by = changed_by,
            _change_reason = reason,
        )
        
        session.add(audit_log)

    async def get_audit_log(self, entity_type: Optional[str], entity_id: Optional[UUID], limit: int) -> List[ConfigAuditLog]:
        """Get audit log entries."""
        async with self._session_factory() as session:
            _query = select(ConfigAuditLog).order_by(
                ConfigAuditLog.changed_at.desc()
            ).limit(limit)
            
            if entity_type:
                _query = query.where(ConfigAuditLog.entity_type == entity_type)
            
            if entity_id:
                _query = query.where(ConfigAuditLog.entity_id == entity_id)
            
            _result = await session.execute(query)
            return list(result.scalars().all())

    # =========================================================================
    # Import/Export
    # =========================================================================

    async def export_configurations(self, exported_by: Optional[str]) -> ConfigurationExport:
        """Export all configurations."""
        async with self._session_factory() as session:
            # Get all configurations
            _user_configs_result = await session.execute(
                select(UserConfiguration)
            )
            _user_configs = list(user_configs_result.scalars().all())
            
            _llm_providers_result = await session.execute(
                select(LLMProvider)
            )
            llm_providers = list(llm_providers_result.scalars().all())
            
            _embedding_providers_result = await session.execute(
                select(EmbeddingProvider)
            )
            embedding_providers = list(embedding_providers_result.scalars().all())
            
            _agent_configs_result = await session.execute(
                select(AgentConfig)
            )
            agent_configs = list(agent_configs_result.scalars().all())
            
            return ConfigurationExport(
                _version = "1.0",
                _exported_at = datetime.utcnow(),
                _exported_by = exported_by,
                user_configurations=user_configs,
                llm_providers=llm_providers,
                embedding_providers=embedding_providers,
                agent_configs=agent_configs,
            )

    async def import_configurations(self, import_data: ConfigurationImport, options: ImportOptions, changed_by: Optional[str]) -> ImportResult:
        """Import configurations from a bundle."""
        _result = ImportResult(success=True)
        
        try:
            # Import user configurations
            if options.import_user_configs and import_data.user_configurations:
                for config_data in import_data.user_configurations:
                    try:
                        _config = UserConfigurationCreate(**config_data)
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
                        _provider = LLMProviderCreate(**provider_data)
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
                        _provider = EmbeddingProviderCreate(**provider_data)
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
                        _config = AgentConfigCreate(**config_data)
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

    def _validate_config_value(self, value: Any, schema: Dict[str, Any]) -> None:
        """
        Validate a configuration value against a JSON schema.
        
        Args:
            value: The value to validate
            schema: JSON schema for validation
            
        Raises:
            ValueError: If validation fails
        """
        # Simple type validation
        _expected_type = schema.get("type")
        if expected_type:
            _type_map = {
                "string": str,
                "integer": int,
                "number": (int, float),
                "boolean": bool,
                "array": list,
                "object": dict,
            }
            
            _expected_python_type = type_map.get(expected_type)
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

    async def migrate_from_env(self, changed_by: Optional[str]) -> Dict[str, Any]:
        """
        Migrate configuration from .env file to database.
        
        This method reads environment variables and creates corresponding
        database configurations. It's idempotent and safe to run multiple times.
        
        Returns:
            Migration result summary
        """
        _migration_result = {
            "migrated": [],
            "skipped": [],
            "errors": [],
        }
        
        # Define environment variable mappings
        _env_mappings = [
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
        
        for env_var, config_key, config_type in env_mappings:
            _env_value = os.environ.get(env_var)
            
            if env_value is None:
                migration_result["skipped"].append(
                    f"{env_var} not set in environment"
                )
                continue
            
            try:
                # Convert value based on type
                if config_type == ConfigType.BOOLEAN:
                    _converted_value = env_value.lower() in ("true", "1", "yes")
                elif config_type == ConfigType.INTEGER:
                    _converted_value = int(env_value)
                elif config_type == ConfigType.FLOAT:
                    _converted_value = float(env_value)
                else:
                    _converted_value = env_value
                
                # Check if config already exists
                _existing = await self.get_config(config_key)
                
                if existing:
                    migration_result["skipped"].append(
                        f"{config_key} already exists in database"
                    )
                    continue
                
                # Create new configuration
                _config = UserConfigurationCreate(
                    _config_key = config_key,
                    _config_value = converted_value,
                    _config_type = config_type,
                    description=f"Migrated from {env_var} environment variable",
                    _category = config_key.split(".")[0] if "." in config_key else "general",
                )
                
                await self.create_config(config, changed_by)
                migration_result["migrated"].append(
                    f"Migrated {env_var} -> {config_key}"
                )
                
            except Exception as e:
                migration_result["errors"].append(
                    f"Error migrating {env_var}: {e}"
                )
        
        logger.info("Environment migration complete", result=migration_result)
        return migration_result


# Global service instance (lazy initialization)
_config_service: Optional[ConfigurationService] = None


def get_config_service() -> ConfigurationService:
    """Get or create the global configuration service instance."""
    global _config_service
    if _config_service is None:
        _config_service = ConfigurationService()
    return _config_service


async def initialize_config_service() -> None:
    """Initialize the global configuration service."""
    _service = get_config_service()
    await service.initialize()


async def shutdown_config_service() -> None:
    """Shutdown the global configuration service."""
    global _config_service
    if _config_service:
        await _config_service.shutdown()
        _config_service = None
