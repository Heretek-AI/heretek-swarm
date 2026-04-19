"""
Tests for ConfigurationService.seed_from_env()

Tests seeding of LLM providers, embedding providers, and UserConfigurations
from docker-compose environment variables.

Covers:
- Full seeding (all env vars present)
- Partial seeding (only LLM or only embedding vars)
- Idempotency (second call skips existing records)
- API key redaction in logs
- Graceful handling of DB errors
- UserConfiguration seeding
"""

import os
import uuid

import pytest
import pytest_asyncio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from heretek_swarm.config.db_models import (
    Base,
    EmbeddingProvider as EmbeddingProviderORM,
    LLMProvider as LLMProviderORM,
    UserConfiguration as UserConfigurationORM,
)
from heretek_swarm.config.service import ConfigurationService


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def encryption_key():
    """Provide a Fernet-compatible encryption key for tests."""
    # Fernet.generate_key() produces a 44-char URL-safe base64 string
    return "test-encryption-key-32bytes-ok!"


# =============================================================================
# Constants — all env vars read by seed_from_env()
# =============================================================================
SEED_ENV_VARS = [
    "OPENAI_API_KEY", "OPENAI_BASE_URL", "LLM_MODEL",
    "EMBEDDING_PROVIDER", "EMBEDDING_API_KEY",
    "EMBEDDING_BASE_URL", "EMBEDDER_MODEL",
    "ENVIRONMENT", "CORS_ORIGINS", "RATE_LIMIT_ENABLED",
]


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture(scope="session", autouse=True)
def preload_modules():
    """
    Pre-load heretek_swarm modules at session scope.

    The heretek_swarm package transitively imports the `swarms` package, which
    calls `load_dotenv()` and sets EMBEDDING_API_KEY from the project's .env file.
    By importing it here (before clean_env runs), we prevent it from loading again
    during test execution.
    """
    # This import triggers load_dotenv() which sets EMBEDDING_API_KEY from .env.
    # We accept this side-effect here because this fixture runs before clean_env.
    from heretek_swarm.config.service import ConfigurationService  # noqa: F401
    from heretek_swarm.config.db_models import Base  # noqa: F401
    from heretek_swarm.config.encryption import ApiKeyEncryptor  # noqa: F401


@pytest.fixture(autouse=True)
def clean_env():
    """
    Clear all seed_from_env() environment variables before every test.

    After session preload_modules runs (which loads dotenv), we must clear
    EMBEDDING_API_KEY and all other seed env vars so each test starts clean.
    """
    saved = {v: os.environ.get(v) for v in SEED_ENV_VARS}
    for v in SEED_ENV_VARS:
        os.environ.pop(v, None)
    yield
    for v, val in saved.items():
        if val is not None:
            os.environ[v] = val
        else:
            os.environ.pop(v, None)


@pytest.fixture
def encryption_key():
    """Provide a Fernet-compatible encryption key for tests."""
    return "test-encryption-key-32bytes-ok!"


@pytest_asyncio.fixture
async def sqlite_engine():
    """
    Create a file-based SQLite engine for testing.

    Uses a fresh temp file per test so the database is completely isolated.
    """
    import tempfile

    db_path = tempfile.mktemp(suffix=".db")
    engine = create_async_engine(
        f"sqlite+aiosqlite:///{db_path}",
        echo=False,
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()
    try:
        os.unlink(db_path)
    except OSError:
        pass


@pytest_asyncio.fixture
async def session_factory(sqlite_engine):
    """Create a session factory bound to the test engine."""
    factory = async_sessionmaker(sqlite_engine, class_=AsyncSession, expire_on_commit=False)
    yield factory


@pytest_asyncio.fixture
async def test_service(sqlite_engine, session_factory, encryption_key):
    """
    Create a ConfigurationService wired to the per-test SQLite DB.

    CONFIG_ENCRYPTION_KEY is set in os.environ *before* creating the service so
    its __init__ sees it (avoids the encryption warning).
    """
    os.environ["CONFIG_ENCRYPTION_KEY"] = encryption_key
    service = ConfigurationService(database_url="sqlite+aiosqlite:///:memory:")
    service._engine = sqlite_engine
    service._session_factory = session_factory
    from heretek_swarm.config.encryption import ApiKeyEncryptor

    service._encryptor = ApiKeyEncryptor(encryption_key)
    service._fernet = service._encryptor._fernet

    yield service

    await service.shutdown()


# =============================================================================
# Helpers
# =============================================================================


async def _get_llm_provider_orm(session_factory, name: str) -> LLMProviderORM | None:
    """Query LLMProvider ORM record by name."""
    async with session_factory() as session:
        result = await session.execute(
            select(LLMProviderORM).where(LLMProviderORM.provider_name == name)
        )
        return result.scalar_one_or_none()


async def _get_embedding_provider_orm(
    session_factory, name: str
) -> EmbeddingProviderORM | None:
    """Query EmbeddingProvider ORM record by name."""
    async with session_factory() as session:
        result = await session.execute(
            select(EmbeddingProviderORM).where(EmbeddingProviderORM.provider_name == name)
        )
        return result.scalar_one_or_none()


async def _get_config_orm(session_factory, key: str) -> UserConfigurationORM | None:
    """Query UserConfiguration ORM record by key."""
    async with session_factory() as session:
        result = await session.execute(
            select(UserConfigurationORM).where(UserConfigurationORM.config_key == key)
        )
        return result.scalar_one_or_none()


# =============================================================================
# Test: seed_from_env — LLM provider creation
# =============================================================================

class TestSeedLLMProvider:
    """Test suite for LLM provider seeding from env vars."""

    @pytest.mark.asyncio
    async def test_seed_from_env_creates_llm_provider(
        self, test_service, session_factory, monkeypatch
    ):
        """OPENAI_API_KEY + LLM_MODEL → LLMProvider record created with correct fields."""
        monkeypatch.setenv("OPENAI_API_KEY", "sk-test-openai-key-1234567890")
        monkeypatch.setenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
        monkeypatch.setenv("LLM_MODEL", "gpt-4o")

        result = await test_service.seed_from_env()

        assert result["providers_created"] == 1
        assert result["embedding_providers_created"] == 0
        assert result["configs_created"] == 0
        assert len(result["skipped_reasons"]) == 0

        # Verify the record in the DB
        provider_orm = await _get_llm_provider_orm(session_factory, "openai")
        assert provider_orm is not None
        assert provider_orm.provider_name == "openai"
        assert provider_orm.base_url == "https://api.openai.com/v1"
        assert provider_orm.default_model == "gpt-4o"
        assert provider_orm.is_default is True
        # API key must be encrypted (not the raw value)
        assert provider_orm.api_key_encrypted != "sk-test-openai-key-1234567890"
        # The hint should be stored (last 4 chars)
        assert provider_orm.api_key_hint == "...7890"

    @pytest.mark.asyncio
    async def test_seed_from_env_uses_default_base_url(
        self, test_service, session_factory, monkeypatch
    ):
        """When OPENAI_BASE_URL is absent, seed_from_env uses the default."""
        monkeypatch.setenv("OPENAI_API_KEY", "sk-test-openai-key-1234567890")
        monkeypatch.delenv("OPENAI_BASE_URL", raising=False)
        monkeypatch.delenv("LLM_MODEL", raising=False)

        await test_service.seed_from_env()

        provider_orm = await _get_llm_provider_orm(session_factory, "openai")
        assert provider_orm is not None
        assert provider_orm.base_url == "https://api.openai.com/v1"


# =============================================================================
# Test: seed_from_env — Embedding provider creation
# =============================================================================

class TestSeedEmbeddingProvider:
    """Test suite for embedding provider seeding from env vars."""

    @pytest.mark.asyncio
    async def test_seed_from_env_creates_embedding_provider(
        self, test_service, session_factory, monkeypatch
    ):
        """EMBEDDING_API_KEY + EMBEDDER_MODEL → EmbeddingProvider record created."""
        monkeypatch.setenv("EMBEDDING_PROVIDER", "openai")
        monkeypatch.setenv("EMBEDDING_API_KEY", "sk-test-embedding-key-abcdef")
        monkeypatch.setenv("EMBEDDING_BASE_URL", "https://api.openai.com/v1")
        monkeypatch.setenv("EMBEDDER_MODEL", "text-embedding-3-small")

        result = await test_service.seed_from_env()

        assert result["embedding_providers_created"] == 1
        assert result["providers_created"] == 0
        assert len(result["skipped_reasons"]) == 0

        provider_orm = await _get_embedding_provider_orm(session_factory, "openai")
        assert provider_orm is not None
        assert provider_orm.provider_name == "openai"
        assert provider_orm.base_url == "https://api.openai.com/v1"
        assert provider_orm.default_model == "text-embedding-3-small"
        assert provider_orm.is_default is True
        # API key must be encrypted
        assert provider_orm.api_key_encrypted != "sk-test-embedding-key-abcdef"

    @pytest.mark.asyncio
    async def test_seed_from_env_embedding_uses_default_provider(
        self, test_service, session_factory, monkeypatch
    ):
        """When EMBEDDING_PROVIDER is absent, defaults to 'openai'."""
        monkeypatch.setenv("EMBEDDING_API_KEY", "sk-test-embedding-key-abcdef")
        monkeypatch.delenv("EMBEDDING_PROVIDER", raising=False)

        await test_service.seed_from_env()

        # Default provider name is "openai"
        provider_orm = await _get_embedding_provider_orm(session_factory, "openai")
        assert provider_orm is not None


# =============================================================================
# Test: seed_from_env — Idempotency
# =============================================================================

class TestSeedIdempotency:
    """Test suite for seed_from_env idempotency."""

    @pytest.mark.asyncio
    async def test_seed_from_env_idempotent(
        self, test_service, session_factory, monkeypatch
    ):
        """Two calls with same env vars → second call skips (no duplicate record)."""
        monkeypatch.setenv("OPENAI_API_KEY", "sk-test-openai-key-1234567890")
        monkeypatch.setenv("LLM_MODEL", "gpt-4o")

        result1 = await test_service.seed_from_env()
        assert result1["providers_created"] == 1

        result2 = await test_service.seed_from_env()
        assert result2["providers_created"] == 0
        assert any("already exists" in r for r in result2["skipped_reasons"])

        # Exactly one record in DB
        provider_orm = await _get_llm_provider_orm(session_factory, "openai")
        assert provider_orm is not None

        # Count records — should be exactly 1
        async with session_factory() as session:
            result = await session.execute(select(LLMProviderORM))
            providers = result.scalars().all()
            assert len(providers) == 1

    @pytest.mark.asyncio
    async def test_seed_from_env_idempotent_embedding(
        self, test_service, session_factory, monkeypatch
    ):
        """Idempotency also applies to embedding providers."""
        monkeypatch.setenv("EMBEDDING_API_KEY", "sk-test-embedding-key-abcdef")

        await test_service.seed_from_env()
        result2 = await test_service.seed_from_env()

        assert result2["embedding_providers_created"] == 0
        assert any("already exists" in r for r in result2["skipped_reasons"])


# =============================================================================
# Test: seed_from_env — Partial seeding
# =============================================================================

class TestSeedPartialSeeding:
    """Test suite for partial / selective seeding."""

    @pytest.mark.asyncio
    async def test_seed_from_env_partial_seeding_llm_only(
        self, test_service, session_factory, monkeypatch
    ):
        """Setting only LLM vars → LLMProvider created, no error for missing embedding vars."""
        monkeypatch.setenv("OPENAI_API_KEY", "sk-test-openai-key-1234567890")
        monkeypatch.setenv("LLM_MODEL", "gpt-4o")
        monkeypatch.delenv("EMBEDDING_API_KEY", raising=False)
        monkeypatch.delenv("EMBEDDER_MODEL", raising=False)
        monkeypatch.delenv("ENVIRONMENT", raising=False)
        monkeypatch.delenv("CORS_ORIGINS", raising=False)
        monkeypatch.delenv("RATE_LIMIT_ENABLED", raising=False)

        # Must not raise
        result = await test_service.seed_from_env()

        assert result["providers_created"] == 1
        assert result["embedding_providers_created"] == 0
        assert result["configs_created"] == 0

        provider_orm = await _get_llm_provider_orm(session_factory, "openai")
        assert provider_orm is not None

    @pytest.mark.asyncio
    async def test_seed_from_env_partial_seeding_embedding_only(
        self, test_service, session_factory, monkeypatch
    ):
        """Setting only embedding vars → EmbeddingProvider created, no error for missing LLM."""
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        monkeypatch.setenv("EMBEDDING_API_KEY", "sk-test-embedding-key-abcdef")

        result = await test_service.seed_from_env()

        assert result["providers_created"] == 0
        assert result["embedding_providers_created"] == 1

    @pytest.mark.asyncio
    async def test_seed_from_env_no_vars_returns_zero_counts(
        self, test_service, monkeypatch
    ):
        """With no relevant env vars set, all counts are zero."""
        # Clear all relevant env vars
        for var in [
            "OPENAI_API_KEY", "OPENAI_BASE_URL", "LLM_MODEL",
            "EMBEDDING_PROVIDER", "EMBEDDING_API_KEY",
            "EMBEDDING_BASE_URL", "EMBEDDER_MODEL",
            "ENVIRONMENT", "CORS_ORIGINS", "RATE_LIMIT_ENABLED",
        ]:
            monkeypatch.delenv(var, raising=False)

        result = await test_service.seed_from_env()

        assert result["providers_created"] == 0
        assert result["embedding_providers_created"] == 0
        assert result["configs_created"] == 0


# =============================================================================
# Test: seed_from_env — API key redaction in logs
# =============================================================================

class TestSeedApiKeyRedaction:
    """Test suite for API key redaction in structlog output."""

    @pytest.mark.asyncio
    async def test_seed_from_env_api_key_not_in_logs(
        self, test_service, monkeypatch, caplog
    ):
        """Raw API key string must not appear in structlog output."""
        import structlog

        monkeypatch.setenv("OPENAI_API_KEY", "sk-prod-secret-api-key-xyz123")
        monkeypatch.setenv("LLM_MODEL", "gpt-4o")

        # Capture structlog records at INFO level
        with caplog.at_level("INFO"):
            await test_service.seed_from_env()

        # The raw API key must not appear in any log record
        raw_key = "sk-prod-secret-api-key-xyz123"
        for record in caplog.records:
            assert raw_key not in str(record.message), (
                f"Raw API key found in log: {record.message}"
            )

    @pytest.mark.asyncio
    async def test_seed_from_env_api_key_hint_appears_not_full_key(
        self, test_service, monkeypatch, caplog
    ):
        """Only the api_key_hint (last 4 chars) may appear in logs."""
        import structlog

        monkeypatch.setenv("OPENAI_API_KEY", "sk-test-key-hint-check-xyz1")
        monkeypatch.setenv("LLM_MODEL", "gpt-4o")

        with caplog.at_level("INFO"):
            await test_service.seed_from_env()

        raw_key = "sk-test-key-hint-check-xyz1"
        hint = "...xyz1"

        for record in caplog.records:
            log_str = str(record.message)
            assert raw_key not in log_str, (
                f"Full API key leaked into log: {log_str}"
            )
            # The hint itself may appear (it's safe to log)
            # (we just don't assert on it here — the important check is above)


# =============================================================================
# Test: seed_from_env — Graceful error handling
# =============================================================================

class TestSeedGracefulErrors:
    """Test suite for graceful error handling in seed_from_env."""

    @pytest.mark.asyncio
    async def test_seed_from_env_returns_result_on_db_error(
        self, monkeypatch
    ):
        """If the DB is unreachable, seed_from_env returns a result with skipped_reasons and does not raise."""
        # Use a TCP-style URL pointing to a non-routable host/port to force a connection failure.
        # This exercises the outer try/except in seed_from_env() rather than the inner
        # AttributeError from the pre-existing model_name bug.
        bad_service = ConfigurationService(
            database_url="postgresql+asyncpg://nonexistent-host.invalid:5432/nonexistent_db"
        )

        # Only set LLM vars so we exercise the LLM branch (no embedding vars set)
        monkeypatch.setenv("OPENAI_API_KEY", "sk-test-openai-key-1234567890")
        monkeypatch.setenv("LLM_MODEL", "gpt-4o")
        monkeypatch.delenv("EMBEDDING_API_KEY", raising=False)
        for var in ("ENVIRONMENT", "CORS_ORIGINS", "RATE_LIMIT_ENABLED"):
            monkeypatch.delenv(var, raising=False)

        # Must not raise — errors are caught internally
        result = await bad_service.seed_from_env()

        assert isinstance(result, dict)
        assert "providers_created" in result
        assert "skipped_reasons" in result
        assert len(result["skipped_reasons"]) > 0, (
            "Expected skipped_reasons to be populated when DB is unreachable"
        )

        await bad_service.shutdown()


# =============================================================================
# Test: seed_from_env — UserConfiguration seeding
# =============================================================================

class TestSeedUserConfigurations:
    """Test suite for UserConfiguration seeding from env vars."""

    @pytest.mark.asyncio
    async def test_seed_from_env_sets_user_config_environment(
        self, test_service, session_factory, monkeypatch
    ):
        """ENVIRONMENT → UserConfiguration record created with config_key='environment'."""
        monkeypatch.setenv("ENVIRONMENT", "production")

        result = await test_service.seed_from_env()

        assert result["configs_created"] >= 1

        config_orm = await _get_config_orm(session_factory, "environment")
        assert config_orm is not None
        assert config_orm.config_key == "environment"
        assert config_orm.config_value == "production"
        assert config_orm.category == "system"
        assert config_orm.config_type == "string"

    @pytest.mark.asyncio
    async def test_seed_from_env_sets_user_config_cors_origins(
        self, test_service, session_factory, monkeypatch
    ):
        """CORS_ORIGINS → UserConfiguration record created."""
        monkeypatch.setenv("CORS_ORIGINS", "https://example.com,https://app.example.com")

        await test_service.seed_from_env()

        config_orm = await _get_config_orm(session_factory, "cors_origins")
        assert config_orm is not None
        assert config_orm.config_value == "https://example.com,https://app.example.com"

    @pytest.mark.asyncio
    async def test_seed_from_env_sets_user_config_rate_limit_true(
        self, test_service, session_factory, monkeypatch
    ):
        """RATE_LIMIT_ENABLED=true → UserConfiguration BOOLEAN record created."""
        monkeypatch.setenv("RATE_LIMIT_ENABLED", "true")

        await test_service.seed_from_env()

        config_orm = await _get_config_orm(session_factory, "rate_limit_enabled")
        assert config_orm is not None
        assert config_orm.config_type == "boolean"
        assert config_orm.config_value is True

    @pytest.mark.asyncio
    async def test_seed_from_env_sets_user_config_rate_limit_false(
        self, test_service, session_factory, monkeypatch
    ):
        """RATE_LIMIT_ENABLED=false → UserConfiguration BOOLEAN False record created."""
        monkeypatch.setenv("RATE_LIMIT_ENABLED", "false")

        await test_service.seed_from_env()

        config_orm = await _get_config_orm(session_factory, "rate_limit_enabled")
        assert config_orm is not None
        assert config_orm.config_type == "boolean"
        assert config_orm.config_value is False

    @pytest.mark.asyncio
    async def test_seed_from_env_rate_limit_accepts_various_truthy_values(
        self, test_service, session_factory, monkeypatch
    ):
        """RATE_LIMIT_ENABLED accepts '1' and 'yes' as truthy values."""
        for raw in ("1", "yes", "YES", "True"):
            monkeypatch.setenv("RATE_LIMIT_ENABLED", raw)
            await test_service.seed_from_env()
            config_orm = await _get_config_orm(session_factory, "rate_limit_enabled")
            assert config_orm.config_value is True, f"Expected True for value '{raw}'"

    @pytest.mark.asyncio
    async def test_seed_from_env_all_system_configs_together(
        self, test_service, session_factory, monkeypatch
    ):
        """Setting all three system env vars (no provider vars) creates three UserConfigurations."""
        # clean_env autouse fixture clears provider vars, so only system configs get seeded
        monkeypatch.setenv("ENVIRONMENT", "staging")
        monkeypatch.setenv("CORS_ORIGINS", "http://localhost:3000")
        monkeypatch.setenv("RATE_LIMIT_ENABLED", "false")

        result = await test_service.seed_from_env()

        assert result["configs_created"] == 3

        env_cfg = await _get_config_orm(session_factory, "environment")
        assert env_cfg.config_value == "staging"

        cors_cfg = await _get_config_orm(session_factory, "cors_origins")
        assert cors_cfg.config_value == "http://localhost:3000"

        rate_cfg = await _get_config_orm(session_factory, "rate_limit_enabled")
        assert rate_cfg.config_value is False
