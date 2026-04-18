"""
Integration tests for Fernet encryption of API keys in configuration service.

Tests:
- Fernet encryption is available (or gracefully degrades)
- create_llm_provider() stores encrypted value in DB, not plaintext
- API key decryption works via service methods
- API GET /api/wizard/config returns api_key_hint (last 4 chars), never actual key
- API responses for provider list/detail never expose api_key or api_key_encrypted fields
- No API key values ever in structured logs

Uses async SQLite test database with real Fernet encryption.
"""

import asyncio
import os
import uuid
from typing import AsyncGenerator
from unittest.mock import patch

import pytest
import pytest_asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from heretek_swarm.config.db_models import Base, LLMProvider as LLMProviderORM
from heretek_swarm.config.encryption import ApiKeyEncryptor, CRYPTOGRAPHY_AVAILABLE
from heretek_swarm.config.models import LLMProviderType
from heretek_swarm.config.service import ConfigurationService


# =============================================================================
# Test Configuration
# =============================================================================

# Valid Fernet key (32 bytes, URL-safe base64 encoded)
TEST_FERNET_KEY = "cgZMKdXUiFfT0lZjeWaQRRs8pS3WgITXjvIaSU266Ig="


# =============================================================================
# Async Database Fixtures
# =============================================================================

@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture
async def test_engine():
    """Create async SQLite test engine."""
    db_path = f"/tmp/test_encryption_{uuid.uuid4().hex}.db"
    db_url = f"sqlite+aiosqlite:///{db_path}"
    
    engine = create_async_engine(db_url, echo=False)
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield engine
    
    await engine.dispose()
    if os.path.exists(db_path):
        os.unlink(db_path)


@pytest_asyncio.fixture
async def service(test_engine) -> ConfigurationService:
    """Create a ConfigurationService with test database and encryption enabled."""
    db_url = str(test_engine.url)
    os.environ["CONFIG_ENCRYPTION_KEY"] = TEST_FERNET_KEY
    os.environ["DATABASE_URL"] = db_url
    
    service = ConfigurationService(database_url=db_url)
    # Ensure encryptor is properly initialized
    service._encryptor = ApiKeyEncryptor(TEST_FERNET_KEY)
    
    yield service
    
    await service.shutdown()
    if "CONFIG_ENCRYPTION_KEY" in os.environ:
        del os.environ["CONFIG_ENCRYPTION_KEY"]


@pytest_asyncio.fixture
async def session_factory(test_engine):
    """Create session factory for direct DB access."""
    return async_sessionmaker(test_engine, expire_on_commit=False)


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def sample_api_key() -> str:
    """Sample API key for testing."""
    return "sk-test-api-key-1234567890abcdef"


@pytest.fixture
def another_api_key() -> str:
    """Another sample API key."""
    return "sk-another-key-zyxwv9876543210"


# =============================================================================
# Test: Fernet Encryption Availability
# =============================================================================

class TestFernetAvailability:
    """Test suite for Fernet encryption availability."""

    def test_cryptography_available(self):
        """Verify cryptography library is available."""
        assert CRYPTOGRAPHY_AVAILABLE is True, (
            "cryptography library should be available for Fernet encryption"
        )

    def test_encryptor_initializes_with_valid_key(self):
        """Test that ApiKeyEncryptor initializes with a valid key."""
        encryptor = ApiKeyEncryptor(TEST_FERNET_KEY)
        assert encryptor.is_available is True, (
            "Encryptor should be available with valid key"
        )

    def test_encryptor_graceful_degradation_no_key(self):
        """Test that ApiKeyEncryptor gracefully degrades without a key."""
        encryptor = ApiKeyEncryptor(None)
        # When no key is provided, operations should pass through
        assert encryptor is not None

    def test_encryptor_encrypt_decrypt_roundtrip(self, sample_api_key: str):
        """Test encryption and decryption produce the original value."""
        encryptor = ApiKeyEncryptor(TEST_FERNET_KEY)
        
        encrypted = encryptor.encrypt(sample_api_key)
        assert encrypted != sample_api_key, "Encrypted value should differ from original"
        
        decrypted = encryptor.decrypt(encrypted)
        assert decrypted == sample_api_key, "Decrypted value should match original"

    def test_encrypted_value_is_not_plaintext(self, sample_api_key: str):
        """Test that encrypted value doesn't contain any plaintext of the original."""
        encryptor = ApiKeyEncryptor(TEST_FERNET_KEY)
        
        encrypted = encryptor.encrypt(sample_api_key)
        
        # Fernet encryption produces base64-encoded ciphertext
        # The plaintext should not appear in the encrypted value
        assert sample_api_key not in encrypted, (
            "Original API key should not appear in encrypted value"
        )
        assert "sk-test" not in encrypted, (
            "API key prefix should not appear in encrypted value"
        )


# =============================================================================
# Test: API Key Encryption in Database
# =============================================================================

class TestDatabaseEncryption:
    """Test suite for API key encryption in database storage."""

    @pytest.mark.asyncio
    async def test_create_provider_stores_encrypted_value(
        self,
        service: ConfigurationService,
        session_factory,
        sample_api_key: str,
    ):
        """Test that create_llm_provider() stores encrypted value in DB, not plaintext."""
        from heretek_swarm.config.models import LLMProviderCreate

        # Create provider with API key
        create_data = LLMProviderCreate(
            provider_name="Test Encrypted Provider",
            provider_type=LLMProviderType.OPENAI,
            base_url="https://api.openai.com/v1",
            api_key=sample_api_key,
            api_key_hint="***1234",
            default_model="gpt-4",
        )

        created = await service.create_llm_provider(create_data, user="test")

        # Verify provider was created
        assert created is not None
        assert created.id is not None

        # Now directly query the database to check raw storage
        # Note: SQLite stores UUID without dashes
        db_id = str(created.id).replace("-", "")
        async with session_factory() as session:
            result = await session.execute(
                text("SELECT api_key_encrypted FROM llm_providers WHERE id = :id"),
                {"id": db_id}
            )
            row = result.first()
            assert row is not None

            raw_encrypted = row[0]
            
            # The raw value in DB should be encrypted (not plaintext)
            assert raw_encrypted != sample_api_key, (
                "Raw DB value should not contain plaintext API key"
            )
            assert "sk-test" not in raw_encrypted, (
                "API key prefix should not appear in raw DB value"
            )
            # Should look like Fernet encrypted data (base64)
            assert len(raw_encrypted) > 50, (
                "Encrypted value should be longer than plaintext"
            )

    @pytest.mark.asyncio
    async def test_create_provider_without_api_key(
        self,
        service: ConfigurationService,
    ):
        """Test that providers can be created without API keys."""
        from heretek_swarm.config.models import LLMProviderCreate

        create_data = LLMProviderCreate(
            provider_name="Test No Key Provider",
            provider_type=LLMProviderType.OLLAMA,
            base_url="http://localhost:11434",
            api_key=None,
            default_model="llama3.2",
        )

        created = await service.create_llm_provider(create_data, user="test")

        assert created is not None
        # api_key_encrypted should be None in DB
        assert created.api_key_hint is None

    @pytest.mark.asyncio
    async def test_direct_encrypt_decrypt_via_service(
        self,
        service: ConfigurationService,
        sample_api_key: str,
    ):
        """Test service encryption/decryption methods work correctly."""
        # Encrypt via service
        encrypted = service.encrypt_api_key(sample_api_key)
        assert encrypted != sample_api_key
        assert len(encrypted) > len(sample_api_key)
        
        # Decrypt via service
        decrypted = service.decrypt_api_key(encrypted)
        assert decrypted == sample_api_key

    @pytest.mark.asyncio
    async def test_update_provider_re_encrypts_api_key(
        self,
        service: ConfigurationService,
        session_factory,
        sample_api_key: str,
        another_api_key: str,
    ):
        """Test that updating provider with new API key re-encrypts it."""
        from heretek_swarm.config.models import LLMProviderCreate, LLMProviderUpdate

        # Create provider with initial API key
        create_data = LLMProviderCreate(
            provider_name="Test Update Re-Encrypt",
            provider_type=LLMProviderType.OPENAI,
            base_url="https://api.openai.com/v1",
            api_key="sk-initial-key-0000000000",
            api_key_hint="***0000",
            default_model="gpt-4",
        )

        created = await service.create_llm_provider(create_data, user="test")
        
        # Get initial encrypted value from DB
        # Note: SQLite stores UUID without dashes
        db_id = str(created.id).replace("-", "")
        async with session_factory() as session:
            result = await session.execute(
                text("SELECT api_key_encrypted FROM llm_providers WHERE id = :id"),
                {"id": db_id}
            )
            initial_encrypted = result.first()[0]

        # Update with new API key
        update_data = LLMProviderUpdate(
            api_key=sample_api_key,
            api_key_hint="***5678",
        )

        updated = await service.update_llm_provider(created.id, update_data, user="test")

        # Get new encrypted value from DB
        async with session_factory() as session:
            result = await session.execute(
                text("SELECT api_key_encrypted FROM llm_providers WHERE id = :id"),
                {"id": db_id}
            )
            new_encrypted = result.first()[0]

        # Encrypted values should be different
        assert new_encrypted != initial_encrypted, (
            "New encrypted key should differ from initial encrypted key"
        )
        
        # New encrypted value should not contain plaintext
        assert sample_api_key not in new_encrypted


# =============================================================================
# Test: Graceful Degradation Without Encryption
# =============================================================================

class TestGracefulDegradation:
    """Test suite for graceful degradation when encryption is not available."""

    def test_encryptor_pass_through_without_key(self):
        """Test that encryptor passes through value when no key is configured."""
        encryptor = ApiKeyEncryptor(None)
        
        test_key = "sk-test-key-without-encryption"
        
        # Without encryption key, encrypt should return value as-is
        encrypted = encryptor.encrypt(test_key)
        assert encrypted == test_key, (
            "Without encryption key, should pass through unchanged"
        )

    def test_decryptor_pass_through_without_key(self):
        """Test that decryptor passes through value when no key is configured."""
        encryptor = ApiKeyEncryptor(None)
        
        test_value = "some-stored-value"
        
        # Without encryption key, decrypt should return value as-is
        decrypted = encryptor.decrypt(test_value)
        assert decrypted == test_value, (
            "Without encryption key, should pass through unchanged"
        )


# =============================================================================
# Test: API Key Hint Only in Responses
# =============================================================================

class TestAPIKeyHintOnly:
    """Test suite verifying API key hint (last 4 chars) is used, not actual key."""

    @pytest.mark.asyncio
    async def test_provider_model_only_exposes_hint(
        self,
        service: ConfigurationService,
        sample_api_key: str,
    ):
        """Test that LLMProvider model only exposes api_key_hint, not the key."""
        from heretek_swarm.config.models import LLMProviderCreate

        # Create provider with API key
        create_data = LLMProviderCreate(
            provider_name="Test Hint Provider",
            provider_type=LLMProviderType.OPENAI,
            base_url="https://api.openai.com/v1",
            api_key=sample_api_key,
            api_key_hint="***7890",
            default_model="gpt-4",
        )

        created = await service.create_llm_provider(create_data, user="test")

        # The model returned should have the hint field
        assert created.api_key_hint == "***7890", (
            "Provider should have the hint, not the full key"
        )
        
        # The model should NOT have api_key field (security measure)
        # Check model doesn't expose the actual key
        model_dict = created.model_dump()
        assert "api_key" not in model_dict or model_dict.get("api_key") is None, (
            "LLMProvider should not expose api_key field"
        )

    @pytest.mark.asyncio
    async def test_list_providers_only_hints(
        self,
        service: ConfigurationService,
    ):
        """Test that listing providers only returns hints, never actual keys."""
        from heretek_swarm.config.models import LLMProviderCreate

        # Create multiple providers with different API keys
        providers_data = [
            ("Provider Hint 1", "sk-key-one-1234567890", "***7890"),
            ("Provider Hint 2", "sk-key-two-9876543210", "***3210"),
            ("Provider Hint 3", "sk-key-three-abcdefgh", "***efgh"),
        ]

        created_ids = []
        for name, api_key, hint in providers_data:
            create_data = LLMProviderCreate(
                provider_name=name,
                provider_type=LLMProviderType.OPENAI,
                base_url="https://api.openai.com/v1",
                api_key=api_key,
                api_key_hint=hint,
                default_model="gpt-4",
            )
            created = await service.create_llm_provider(create_data, user="test")
            created_ids.append(created.id)

        # List all providers
        providers = await service.list_llm_providers(include_disabled=True)

        # Verify provider list only contains hints
        for provider in providers:
            # Only api_key_hint should be present for key-related info
            if provider.api_key_hint:
                assert provider.api_key_hint.startswith("***"), (
                    "Hints should start with ***"
                )

    @pytest.mark.asyncio
    async def test_get_provider_only_returns_hint(
        self,
        service: ConfigurationService,
        sample_api_key: str,
    ):
        """Test that getting a single provider only returns the hint."""
        from heretek_swarm.config.models import LLMProviderCreate

        create_data = LLMProviderCreate(
            provider_name="Test Single Provider Hint",
            provider_type=LLMProviderType.OPENAI,
            base_url="https://api.openai.com/v1",
            api_key=sample_api_key,
            api_key_hint="***test",
            default_model="gpt-4",
        )

        created = await service.create_llm_provider(create_data, user="test")
        retrieved = await service.get_llm_provider(created.id)

        # Should only have hint, no actual key
        assert retrieved.api_key_hint == "***test"
        # Verify the response doesn't expose the key
        model_dump = retrieved.model_dump()
        assert "api_key" not in model_dump or model_dump.get("api_key") is None


# =============================================================================
# Test: API Response Never Exposes Keys
# =============================================================================

class TestAPIResponseSecurity:
    """Test suite for API response security (keys never exposed)."""

    @pytest.mark.asyncio
    async def test_get_provider_never_returns_plaintext_key(
        self,
        service: ConfigurationService,
        sample_api_key: str,
    ):
        """Test that getting a provider never returns plaintext API key."""
        from heretek_swarm.config.models import LLMProviderCreate

        # Create provider
        create_data = LLMProviderCreate(
            provider_name="Test Security Provider",
            provider_type=LLMProviderType.OPENAI,
            base_url="https://api.openai.com/v1",
            api_key=sample_api_key,
            api_key_hint="***7890",
            default_model="gpt-4",
        )

        created = await service.create_llm_provider(create_data, user="test")
        retrieved = await service.get_llm_provider(created.id)

        # Serialize to JSON
        json_data = retrieved.model_dump_json()

        # Plaintext key should not appear in JSON response
        assert sample_api_key not in json_data, (
            "Plaintext API key should never appear in API response"
        )

    @pytest.mark.asyncio
    async def test_update_response_never_exposes_key(
        self,
        service: ConfigurationService,
        sample_api_key: str,
    ):
        """Test that update responses never expose the actual API key."""
        from heretek_swarm.config.models import LLMProviderCreate, LLMProviderUpdate

        # Create provider
        create_data = LLMProviderCreate(
            provider_name="Test Update Security",
            provider_type=LLMProviderType.OPENAI,
            base_url="https://api.openai.com/v1",
            api_key="sk-initial-key-for-security-test",
            api_key_hint="***test",
            default_model="gpt-4",
        )

        created = await service.create_llm_provider(create_data, user="test")

        # Update with new key
        update_data = LLMProviderUpdate(
            api_key=sample_api_key,
            api_key_hint="***new4",
        )

        updated = await service.update_llm_provider(created.id, update_data, user="test")

        # Serialize response
        json_data = updated.model_dump_json()

        # Neither old nor new key should appear in plaintext
        assert "sk-initial-key-for-security-test" not in json_data, (
            "Old API key should not appear in update response"
        )
        assert sample_api_key not in json_data, (
            "New API key should not appear in update response"
        )

    @pytest.mark.asyncio
    async def test_provider_model_has_no_api_key_field(
        self,
        service: ConfigurationService,
        sample_api_key: str,
    ):
        """Test that LLMProvider model definition has no api_key field."""
        from heretek_swarm.config.models import LLMProviderCreate

        create_data = LLMProviderCreate(
            provider_name="Test Model Fields",
            provider_type=LLMProviderType.OPENAI,
            base_url="https://api.openai.com/v1",
            api_key=sample_api_key,
            api_key_hint="***model",
            default_model="gpt-4",
        )

        created = await service.create_llm_provider(create_data, user="test")
        
        # Check model fields
        fields = created.model_fields
        
        # api_key should not be a defined field (security by design)
        assert "api_key" not in fields, (
            "LLMProvider should not have api_key field to prevent accidental exposure"
        )
        
        # Only api_key_hint should exist
        assert "api_key_hint" in fields, (
            "LLMProvider should have api_key_hint field"
        )


# =============================================================================
# Test: Structured Logging Never Contains Keys
# =============================================================================

class TestLoggingSecurity:
    """Test suite verifying structured logs never contain API keys."""

    def test_encryptor_logs_do_not_contain_keys(self, caplog, sample_api_key: str):
        """Test that encryption operations don't leak keys in logs."""
        import logging

        # Set up logging capture
        caplog.set_level(logging.INFO)

        encryptor = ApiKeyEncryptor(TEST_FERNET_KEY)
        
        # Perform encryption
        encrypted = encryptor.encrypt(sample_api_key)

        # Check log records
        for record in caplog.records:
            record_text = str(record.getMessage())
            
            # The actual API key should not appear in any log
            assert sample_api_key not in record_text, (
                f"API key found in log message: {record.getMessage()}"
            )

    @pytest.mark.asyncio
    async def test_service_logs_do_not_contain_keys(
        self,
        service: ConfigurationService,
        sample_api_key: str,
        caplog,
    ):
        """Test that service operations don't leak keys in structured logs."""
        import logging

        caplog.set_level(logging.INFO)

        from heretek_swarm.config.models import LLMProviderCreate

        create_data = LLMProviderCreate(
            provider_name="Test Log Security",
            provider_type=LLMProviderType.OPENAI,
            base_url="https://api.openai.com/v1",
            api_key=sample_api_key,
            api_key_hint="***logt",
            default_model="gpt-4",
        )

        await service.create_llm_provider(create_data, user="test")

        # Check log records for the test
        for record in caplog.records:
            record_text = str(record.getMessage())
            
            # The actual API key should not appear in logs
            assert sample_api_key not in record_text, (
                f"API key found in service log: {record.getMessage()}"
            )


# =============================================================================
# Test: Extra Config Encryption
# =============================================================================

class TestExtraConfigEncryption:
    """Test suite for encryption of sensitive values in extra_config."""

    def test_encrypt_extra_config_sensitive_keys(self):
        """Test that sensitive keys in extra_config are encrypted."""
        encryptor = ApiKeyEncryptor(TEST_FERNET_KEY)
        
        config = {
            "temperature": 0.7,
            "api_key": "sk-secret-in-extra-config",
            "custom_field": "safe-value",
            "auth_token": "another-secret-token",
        }

        encrypted = encryptor.encrypt_config(config)

        # Sensitive fields should be encrypted
        assert encrypted["api_key"] != config["api_key"], (
            "api_key should be encrypted"
        )
        assert encrypted["auth_token"] != config["auth_token"], (
            "auth_token should be encrypted"
        )
        # Non-sensitive fields should remain unchanged
        assert encrypted["temperature"] == config["temperature"]
        assert encrypted["custom_field"] == config["custom_field"]

    def test_decrypt_extra_config_sensitive_keys(self):
        """Test that encrypted sensitive keys in extra_config can be decrypted."""
        encryptor = ApiKeyEncryptor(TEST_FERNET_KEY)
        
        config = {
            "api_key": "sk-secret-to-decrypt",
            "secret_field": "another-secret",
        }

        encrypted = encryptor.encrypt_config(config)
        decrypted = encryptor.decrypt_config(encrypted)

        # Should decrypt back to original
        assert decrypted["api_key"] == config["api_key"]
        assert decrypted["secret_field"] == config["secret_field"]

    @pytest.mark.asyncio
    async def test_provider_extra_config_encrypted_in_db(
        self,
        service: ConfigurationService,
        session_factory,
    ):
        """Test that sensitive values in extra_config are encrypted in database."""
        from heretek_swarm.config.models import LLMProviderCreate
        import json

        # Note: _encrypt_extra_config only encrypts keys named exactly "api_key", "secret", or "token"
        extra_config = {
            "temperature": 0.7,
            "api_key": "sk-key-in-extra-config",  # This will be encrypted
        }

        create_data = LLMProviderCreate(
            provider_name="Test Extra Config Encryption",
            provider_type=LLMProviderType.OPENAI,
            base_url="https://api.openai.com/v1",
            default_model="gpt-4",
            extra_config=extra_config,
        )

        created = await service.create_llm_provider(create_data, user="test")

        # Check raw database value
        # Note: SQLite stores UUID without dashes
        # Note: extra_config is stored as JSON string in SQLite
        db_id = str(created.id).replace("-", "")
        async with session_factory() as session:
            result = await session.execute(
                text("SELECT extra_config FROM llm_providers WHERE id = :id"),
                {"id": db_id}
            )
            row = result.first()
            assert row is not None

            raw_extra_str = row[0]
            raw_extra = json.loads(raw_extra_str) if isinstance(raw_extra_str, str) else raw_extra_str
            
            # The sensitive value should be encrypted
            assert raw_extra["api_key"] != "sk-key-in-extra-config", (
                "Sensitive value in extra_config should be encrypted in DB"
            )


# =============================================================================
# Summary Test
# =============================================================================

class TestEncryptionSummary:
    """Summary tests to verify overall encryption behavior."""

    def test_encryption_key_format_valid(self):
        """Test that test encryption key format is valid for Fernet."""
        encryptor = ApiKeyEncryptor(TEST_FERNET_KEY)
        
        # Should be able to encrypt/decrypt without errors
        test_value = "test-value-for-key-validation"
        encrypted = encryptor.encrypt(test_value)
        decrypted = encryptor.decrypt(encrypted)
        
        assert decrypted == test_value

    @pytest.mark.asyncio
    async def test_end_to_end_encrypted_provider_lifecycle(
        self,
        service: ConfigurationService,
        session_factory,
        sample_api_key: str,
    ):
        """
        End-to-end test: create provider, verify DB encryption, update key, delete.
        
        Verifies the complete lifecycle with encryption.
        """
        from heretek_swarm.config.models import LLMProviderCreate, LLMProviderUpdate

        # 1. Create provider with API key
        create_data = LLMProviderCreate(
            provider_name="Test E2E Encryption",
            provider_type=LLMProviderType.OPENAI,
            base_url="https://api.openai.com/v1",
            api_key=sample_api_key,
            api_key_hint="***e2e1",
            default_model="gpt-4",
        )

        created = await service.create_llm_provider(create_data, user="test")
        assert created is not None

        # Note: SQLite stores UUID without dashes
        db_id = str(created.id).replace("-", "")

        # 2. Verify encryption in database
        async with session_factory() as session:
            result = await session.execute(
                text("SELECT api_key_encrypted FROM llm_providers WHERE id = :id"),
                {"id": db_id}
            )
            db_value = result.first()[0]
            assert db_value != sample_api_key, "DB should store encrypted value"
            assert "sk-test" not in db_value, "Plaintext should not be in DB"

        # 3. Verify decryption via service
        decrypted = service.decrypt_api_key(db_value)
        assert decrypted == sample_api_key, "Service should decrypt correctly"

        # 4. Update with new key
        new_key = "sk-updated-e2e-key-abcdefgh"
        update_data = LLMProviderUpdate(
            api_key=new_key,
            api_key_hint="***efgh",
        )

        updated = await service.update_llm_provider(created.id, update_data, user="test")

        # 5. Verify new key is encrypted
        async with session_factory() as session:
            result = await session.execute(
                text("SELECT api_key_encrypted FROM llm_providers WHERE id = :id"),
                {"id": db_id}
            )
            new_db_value = result.first()[0]
            assert new_db_value != new_key, "Updated key should be encrypted"
            assert new_db_value != db_value, "Encrypted values should differ"

        # 6. Verify service can decrypt new key
        new_decrypted = service.decrypt_api_key(new_db_value)
        assert new_decrypted == new_key

        # 7. Delete provider
        deleted = await service.delete_llm_provider(created.id, user="test")
        assert deleted is True

        # 8. Verify provider is gone
        gone = await service.get_llm_provider(created.id)
        assert gone is None
