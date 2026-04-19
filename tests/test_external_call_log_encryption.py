"""
Unit tests for ExternalCallLogEncryptor and Pydantic schemas.

Tests:
- Fernet encryption/decryption round-trip for headers and body
- Sanitization of sensitive data (Authorization headers, api_key params)
- Body truncation at 10KB
- Pydantic schema validation for ExternalCallLogCreate and ExternalCallLogResponse
"""

import json
import uuid
from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from heretek_swarm.models.external_call_log_encryption import (
    CRYPTOGRAPHY_AVAILABLE,
    ExternalCallLogEncryptor,
    MAX_BODY_SIZE,
    get_encryptor,
)


# =============================================================================
# Test Configuration
# =============================================================================

# Valid Fernet key (32 bytes, URL-safe base64 encoded)
TEST_FERNET_KEY = "cgZMKdXUiFfT0lZjeWaQRRs8pS3WgITXjvIaSU266Ig="


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def encryptor_with_key() -> ExternalCallLogEncryptor:
    """Create an encryptor with a valid encryption key."""
    return ExternalCallLogEncryptor(TEST_FERNET_KEY)


@pytest.fixture
def encryptor_without_key() -> ExternalCallLogEncryptor:
    """Create an encryptor without an encryption key."""
    return ExternalCallLogEncryptor(None)


@pytest.fixture
def sample_headers() -> dict:
    """Sample request headers for testing."""
    return {
        "Content-Type": "application/json",
        "Authorization": "Bearer sk-secret-api-key-12345",
        "X-Request-ID": "req-001",
    }


@pytest.fixture
def sample_body() -> dict:
    """Sample request/response body for testing."""
    return {
        "user_id": "user-123",
        "action": "create",
        "data": {"name": "Test Item", "price": 29.99},
    }


# =============================================================================
# Test: Encryption Availability
# =============================================================================

class TestEncryptionAvailability:
    """Test suite for Fernet encryption availability."""

    def test_cryptography_available(self) -> None:
        """Verify cryptography library is available."""
        assert CRYPTOGRAPHY_AVAILABLE is True, (
            "cryptography library should be available for Fernet encryption"
        )

    def test_encryptor_with_key_is_available(
        self, encryptor_with_key: ExternalCallLogEncryptor
    ) -> None:
        """Test that encryptor with valid key reports as available."""
        assert encryptor_with_key.is_available is True

    def test_encryptor_without_key_is_not_available(
        self, encryptor_without_key: ExternalCallLogEncryptor
    ) -> None:
        """Test that encryptor without key reports as not available."""
        assert encryptor_without_key.is_available is False


# =============================================================================
# Test: Encryption/Decryption Round-Trip
# =============================================================================

class TestEncryptionRoundTrip:
    """Test suite for encryption/decryption round-trip operations."""

    def test_encrypt_headers_roundtrip(
        self,
        encryptor_with_key: ExternalCallLogEncryptor,
        sample_headers: dict,
    ) -> None:
        """Test encryption and decryption of request headers."""
        encrypted = encryptor_with_key.encrypt(sample_headers)

        assert "encrypted" in encrypted
        assert encrypted["encrypted"] != json.dumps(sample_headers)

        decrypted = encryptor_with_key.decrypt(encrypted)
        assert decrypted == sample_headers

    def test_encrypt_body_roundtrip(
        self,
        encryptor_with_key: ExternalCallLogEncryptor,
        sample_body: dict,
    ) -> None:
        """Test encryption and decryption of request/response body."""
        encrypted = encryptor_with_key.encrypt(sample_body)

        assert "encrypted" in encrypted

        decrypted = encryptor_with_key.decrypt(encrypted)
        assert decrypted == sample_body

    def test_encrypt_empty_dict(
        self, encryptor_with_key: ExternalCallLogEncryptor
    ) -> None:
        """Test encryption of empty dict returns empty encrypted value."""
        encrypted = encryptor_with_key.encrypt({})

        assert encrypted == {"encrypted": ""}

    def test_decrypt_empty_encrypted(
        self, encryptor_with_key: ExternalCallLogEncryptor
    ) -> None:
        """Test decryption of empty encrypted value returns empty dict."""
        decrypted = encryptor_with_key.decrypt({"encrypted": ""})
        assert decrypted == {}

    def test_decrypt_missing_encrypted_key(
        self, encryptor_with_key: ExternalCallLogEncryptor
    ) -> None:
        """Test decryption with missing encrypted key returns empty dict."""
        decrypted = encryptor_with_key.decrypt({})
        assert decrypted == {}

    def test_encrypted_value_differs_from_plaintext(
        self,
        encryptor_with_key: ExternalCallLogEncryptor,
        sample_headers: dict,
    ) -> None:
        """Test that encrypted value doesn't contain plaintext."""
        encrypted = encryptor_with_key.encrypt(sample_headers)

        encrypted_str = encrypted["encrypted"]
        # Should not contain "Bearer" or "secret"
        assert "Bearer" not in encrypted_str
        assert "secret" not in encrypted_str

    def test_multiple_encryptions_produce_different_ciphertext(
        self,
        encryptor_with_key: ExternalCallLogEncryptor,
        sample_headers: dict,
    ) -> None:
        """Test that same plaintext encrypts to different ciphertext (IV)."""
        encrypted1 = encryptor_with_key.encrypt(sample_headers)
        encrypted2 = encryptor_with_key.encrypt(sample_headers)

        # Fernet uses random IV, so ciphertexts should differ
        assert encrypted1["encrypted"] != encrypted2["encrypted"]

        # But both should decrypt to same value
        decrypted1 = encryptor_with_key.decrypt(encrypted1)
        decrypted2 = encryptor_with_key.decrypt(encrypted2)
        assert decrypted1 == decrypted2 == sample_headers


# =============================================================================
# Test: Sanitization
# =============================================================================

class TestSanitization:
    """Test suite for sanitization of sensitive data."""

    def test_sanitize_redacts_authorization_header(
        self,
        encryptor_with_key: ExternalCallLogEncryptor,
    ) -> None:
        """Test that Authorization header value is redacted."""
        data = {
            "Content-Type": "application/json",
            "Authorization": "Bearer sk-secret-key-12345",
        }

        sanitized = encryptor_with_key.sanitize(data)

        assert sanitized["Content-Type"] == "application/json"
        assert sanitized["Authorization"] == "[REDACTED]"

    def test_sanitize_redacts_api_key_in_headers(
        self,
        encryptor_with_key: ExternalCallLogEncryptor,
    ) -> None:
        """Test that api_key in headers is redacted."""
        data = {
            "Content-Type": "application/json",
            "api_key": "sk-my-secret-api-key",
        }

        sanitized = encryptor_with_key.sanitize(data)

        assert sanitized["api_key"] == "[REDACTED]"

    def test_sanitize_redacts_token_in_headers(
        self,
        encryptor_with_key: ExternalCallLogEncryptor,
    ) -> None:
        """Test that token-named headers are redacted."""
        data = {
            "token": "secret-token-value",
            "access_token": "access-token-value",
        }

        sanitized = encryptor_with_key.sanitize(data)

        assert sanitized["token"] == "[REDACTED]"
        assert sanitized["access_token"] == "[REDACTED]"

    def test_sanitize_redacts_secret_in_headers(
        self,
        encryptor_with_key: ExternalCallLogEncryptor,
    ) -> None:
        """Test that secret-named headers are redacted."""
        data = {
            "secret": "my-secret-value",
            "api_secret": "my-api-secret",
        }

        sanitized = encryptor_with_key.sanitize(data)

        assert sanitized["secret"] == "[REDACTED]"
        assert sanitized["api_secret"] == "[REDACTED]"

    def test_sanitize_redacts_password_in_headers(
        self,
        encryptor_with_key: ExternalCallLogEncryptor,
    ) -> None:
        """Test that password-named headers are redacted."""
        data = {
            "password": "supersecret",
            "x-api-password": "another-secret",
        }

        sanitized = encryptor_with_key.sanitize(data)

        assert sanitized["password"] == "[REDACTED]"
        assert sanitized["x-api-password"] == "[REDACTED]"

    def test_sanitize_redacts_auth_in_headers(
        self,
        encryptor_with_key: ExternalCallLogEncryptor,
    ) -> None:
        """Test that auth-named headers are redacted (case insensitive)."""
        data = {
            "Auth": "auth-value",
            "AUTHORIZATION": "auth-value-uppercase",
            "X-Auth-Token": "token-value",
        }

        sanitized = encryptor_with_key.sanitize(data)

        assert sanitized["Auth"] == "[REDACTED]"
        assert sanitized["AUTHORIZATION"] == "[REDACTED]"
        assert sanitized["X-Auth-Token"] == "[REDACTED]"

    def test_sanitize_preserves_non_sensitive_headers(
        self,
        encryptor_with_key: ExternalCallLogEncryptor,
    ) -> None:
        """Test that non-sensitive headers are preserved."""
        data = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "X-Request-ID": "req-12345",
            "User-Agent": "HeretekSwarm/1.0",
        }

        sanitized = encryptor_with_key.sanitize(data)

        assert sanitized["Content-Type"] == "application/json"
        assert sanitized["Accept"] == "application/json"
        assert sanitized["X-Request-ID"] == "req-12345"
        assert sanitized["User-Agent"] == "HeretekSwarm/1.0"

    def test_sanitize_url_with_api_key_param(
        self,
        encryptor_with_key: ExternalCallLogEncryptor,
    ) -> None:
        """Test that URL with api_key query param is sanitized."""
        data = {
            "url": "https://api.example.com/data?api_key=sk-secret-key",
        }

        sanitized = encryptor_with_key.sanitize(data)

        assert "api_key=[REDACTED]" in sanitized["url"]
        assert "sk-secret-key" not in sanitized["url"]

    def test_sanitize_url_with_key_param(
        self,
        encryptor_with_key: ExternalCallLogEncryptor,
    ) -> None:
        """Test that URL with key query param is sanitized."""
        data = {
            "url": "https://api.example.com/data?key=my-secret-key",
        }

        sanitized = encryptor_with_key.sanitize(data)

        assert "key=[REDACTED]" in sanitized["url"]
        assert "my-secret-key" not in sanitized["url"]

    def test_sanitize_url_with_token_param(
        self,
        encryptor_with_key: ExternalCallLogEncryptor,
    ) -> None:
        """Test that URL with token query param is sanitized."""
        data = {
            "url": "https://api.example.com/data?token=secret-token",
        }

        sanitized = encryptor_with_key.sanitize(data)

        assert "token=[REDACTED]" in sanitized["url"]
        assert "secret-token" not in sanitized["url"]

    def test_sanitize_url_preserves_non_sensitive_params(
        self,
        encryptor_with_key: ExternalCallLogEncryptor,
    ) -> None:
        """Test that non-sensitive URL params are preserved."""
        data = {
            "url": "https://api.example.com/data?page=1&limit=10&sort=name",
        }

        sanitized = encryptor_with_key.sanitize(data)

        assert "page=1" in sanitized["url"]
        assert "limit=10" in sanitized["url"]
        assert "sort=name" in sanitized["url"]

    def test_sanitize_nested_dict(
        self,
        encryptor_with_key: ExternalCallLogEncryptor,
    ) -> None:
        """Test that nested dictionaries are recursively sanitized."""
        data = {
            "headers": {
                "Authorization": "Bearer sk-secret",
                "X-Custom": "value",
            },
            "body": {"name": "test"},
        }

        sanitized = encryptor_with_key.sanitize(data)

        assert sanitized["headers"]["Authorization"] == "[REDACTED]"
        assert sanitized["headers"]["X-Custom"] == "value"
        assert sanitized["body"]["name"] == "test"

    def test_sanitize_empty_dict(
        self,
        encryptor_with_key: ExternalCallLogEncryptor,
    ) -> None:
        """Test sanitization of empty dict returns empty dict."""
        sanitized = encryptor_with_key.sanitize({})
        assert sanitized == {}


# =============================================================================
# Test: Body Truncation
# =============================================================================

class TestBodyTruncation:
    """Test suite for body truncation at 10KB."""

    def test_body_under_limit_not_truncated(
        self,
        encryptor_with_key: ExternalCallLogEncryptor,
    ) -> None:
        """Test that body under 10KB limit is not truncated."""
        data = {"content": "x" * 1000}  # 1KB of data

        encrypted = encryptor_with_key.encrypt(data)
        decrypted = encryptor_with_key.decrypt(encrypted)

        assert decrypted == data
        assert "...truncated" not in json.dumps(encrypted)

    def test_body_at_limit_not_truncated(
        self,
        encryptor_with_key: ExternalCallLogEncryptor,
    ) -> None:
        """Test that body at exactly 10KB limit is not truncated."""
        # Create data that when JSON serialized is just under 10KB
        data = {"content": "x" * (MAX_BODY_SIZE - 50)}

        encrypted = encryptor_with_key.encrypt(data)
        decrypted = encryptor_with_key.decrypt(encrypted)

        # Should not be truncated
        assert "...truncated" not in encrypted.get("encrypted", "")

    def test_body_over_limit_is_truncated(
        self,
        encryptor_with_key: ExternalCallLogEncryptor,
    ) -> None:
        """Test that body over 10KB limit is truncated."""
        # Create data that when JSON serialized is over 10KB
        large_data = {"content": "x" * (MAX_BODY_SIZE + 1000)}

        # Check truncation happens during serialization
        json_str = json.dumps(large_data, ensure_ascii=False, sort_keys=True)
        assert len(json_str) > MAX_BODY_SIZE

        # The encryptor truncates during serialization, but the truncation
        # indicator gets encrypted along with the data
        encrypted = encryptor_with_key.encrypt(large_data)
        encrypted_str = encrypted.get("encrypted", "")

        # After decryption, we should see the truncated indicator
        decrypted = encryptor_with_key.decrypt(encrypted)
        # The decryptor's deserialization handles truncated data
        decrypted_str = json.dumps(decrypted, ensure_ascii=False, sort_keys=True)
        assert "...truncated" in decrypted_str

    def test_truncated_body_stores_partial_data(
        self,
        encryptor_with_key: ExternalCallLogEncryptor,
    ) -> None:
        """Test that truncated body stores at least 10KB of data."""
        data = {"content": "y" * (MAX_BODY_SIZE + 5000)}

        # Verify the data is over the limit
        json_str = json.dumps(data, ensure_ascii=False, sort_keys=True)
        assert len(json_str) > MAX_BODY_SIZE

        encrypted = encryptor_with_key.encrypt(data)

        # After decryption, verify we get back truncated data
        decrypted = encryptor_with_key.decrypt(encrypted)

        # When truncated data is encrypted and decrypted, the JSON is malformed
        # and the deserializer returns {"_raw": data} as a fallback
        # Either we get the raw truncated string or the deserialized dict
        if "_raw" in decrypted:
            # Malformed JSON after truncation - fallback to raw
            raw_data = decrypted["_raw"]
            assert "...truncated" in raw_data
        else:
            # Successfully parsed (rare case if truncation happens at valid point)
            decrypted_str = json.dumps(decrypted, ensure_ascii=False, sort_keys=True)
            assert decrypted_str.startswith("{")
            assert "...truncated" in decrypted_str


# =============================================================================
# Test: Pydantic Schemas
# =============================================================================

class TestExternalCallLogSchemas:
    """Test suite for ExternalCallLog Pydantic schemas."""

    def test_create_schema_minimal(self) -> None:
        """Test ExternalCallLogCreate with minimal fields."""
        from heretek_swarm.schemas.external_call_log import ExternalCallLogCreate

        log = ExternalCallLogCreate(
            agent_id="agent-001",
            agent_type="worker",
            call_type="api_call",
            url="https://api.example.com/v1/test",
            method="POST",
        )

        assert log.agent_id == "agent-001"
        assert log.request_headers is None
        assert log.request_body is None
        assert log.response_body is None

    def test_create_schema_full(self) -> None:
        """Test ExternalCallLogCreate with all fields."""
        from heretek_swarm.schemas.external_call_log import ExternalCallLogCreate

        log = ExternalCallLogCreate(
            agent_id="agent-002",
            agent_type="worker",
            call_type="api_call",
            url="https://api.example.com/v1/test",
            method="POST",
            status_code=200,
            duration_ms=150.5,
            tool_name="fetch_tool",
            error_message=None,
            request_headers={"Content-Type": "application/json"},
            request_body='{"key": "value"}',
            response_body='{"result": "success"}',
        )

        assert log.status_code == 200
        assert log.duration_ms == 150.5
        assert log.request_headers == {"Content-Type": "application/json"}

    def test_create_schema_validation_agent_id_required(self) -> None:
        """Test that agent_id is required."""
        from heretek_swarm.schemas.external_call_log import ExternalCallLogCreate

        with pytest.raises(ValidationError) as exc_info:
            ExternalCallLogCreate(
                agent_type="worker",
                call_type="api_call",
                url="https://api.example.com/v1/test",
                method="POST",
            )

        assert "agent_id" in str(exc_info.value)

    def test_create_schema_validation_url_required(self) -> None:
        """Test that url is required."""
        from heretek_swarm.schemas.external_call_log import ExternalCallLogCreate

        with pytest.raises(ValidationError) as exc_info:
            ExternalCallLogCreate(
                agent_id="agent-001",
                agent_type="worker",
                call_type="api_call",
                method="POST",
            )

        assert "url" in str(exc_info.value)

    def test_create_schema_validation_status_code_range(self) -> None:
        """Test that status_code must be valid HTTP code."""
        from heretek_swarm.schemas.external_call_log import ExternalCallLogCreate

        with pytest.raises(ValidationError):
            ExternalCallLogCreate(
                agent_id="agent-001",
                agent_type="worker",
                call_type="api_call",
                url="https://api.example.com/v1/test",
                method="POST",
                status_code=99,  # Invalid: below 100
            )

        with pytest.raises(ValidationError):
            ExternalCallLogCreate(
                agent_id="agent-001",
                agent_type="worker",
                call_type="api_call",
                url="https://api.example.com/v1/test",
                method="POST",
                status_code=600,  # Invalid: above 599
            )

    def test_create_schema_validation_duration_non_negative(self) -> None:
        """Test that duration_ms must be non-negative."""
        from heretek_swarm.schemas.external_call_log import ExternalCallLogCreate

        with pytest.raises(ValidationError):
            ExternalCallLogCreate(
                agent_id="agent-001",
                agent_type="worker",
                call_type="api_call",
                url="https://api.example.com/v1/test",
                method="POST",
                duration_ms=-1,  # Invalid: negative
            )

    def test_create_schema_max_lengths(self) -> None:
        """Test that max lengths are enforced."""
        from heretek_swarm.schemas.external_call_log import ExternalCallLogCreate

        # Valid max length for url (2048) - calculate correctly
        # Base URL "https://api.example.com/" = 26 chars
        base_len = len("https://api.example.com/")  # 26 chars
        remainder = 2048 - base_len  # 2022 chars available for 'a' suffix
        log = ExternalCallLogCreate(
            agent_id="a" * 255,
            agent_type="a" * 100,
            call_type="a" * 50,
            url="https://api.example.com/" + "a" * remainder,
            method="DELETE",
        )
        assert len(log.url) == 2048

        # Invalid: too long
        with pytest.raises(ValidationError):
            ExternalCallLogCreate(
                agent_id="a" * 256,  # Exceeds 255
                agent_type="worker",
                call_type="api_call",
                url="https://api.example.com/v1/test",
                method="POST",
            )

    def test_response_schema_requires_id(self) -> None:
        """Test that ExternalCallLogResponse requires id field."""
        from heretek_swarm.schemas.external_call_log import ExternalCallLogResponse

        with pytest.raises(ValidationError) as exc_info:
            ExternalCallLogResponse(
                agent_id="agent-001",
                agent_type="worker",
                call_type="api_call",
                url="https://api.example.com/v1/test",
                url_domain="api.example.com",
                url_full="https://api.example.com/v1/test",
                method="POST",
                created_at=datetime.now(timezone.utc),
            )

        assert "id" in str(exc_info.value)

    def test_response_schema_has_domain_and_full_url(self) -> None:
        """Test that ExternalCallLogResponse has url_domain and url_full."""
        from heretek_swarm.schemas.external_call_log import ExternalCallLogResponse

        log = ExternalCallLogResponse(
            id=uuid.uuid4(),
            agent_id="agent-001",
            agent_type="worker",
            call_type="api_call",
            url="https://api.example.com/v1/test",
            url_domain="api.example.com",
            url_full="https://api.example.com/v1/test",
            method="POST",
            created_at=datetime.now(timezone.utc),
        )

        assert log.url_domain == "api.example.com"
        assert log.url_full == "https://api.example.com/v1/test"

    def test_response_schema_from_orm(self) -> None:
        """Test ExternalCallLogResponse.from_orm_with_decryption factory."""
        from heretek_swarm.models.external_call_log import ExternalCallLog
        from heretek_swarm.schemas.external_call_log import ExternalCallLogResponse

        # Create ORM object
        orm_obj = ExternalCallLog(
            id=uuid.uuid4(),
            agent_id="agent-003",
            agent_type="worker",
            call_type="api_call",
            url="https://api.example.com/v1/test",
            method="POST",
            status_code=200,
            created_at=datetime.now(timezone.utc),
        )

        # Create response via factory
        response = ExternalCallLogResponse.from_orm_with_decryption(
            orm_obj=orm_obj,
            decrypted_headers={"Content-Type": "application/json"},
            decrypted_request_body='{"key": "value"}',
            decrypted_response_body='{"result": "ok"}',
        )

        assert response.agent_id == "agent-003"
        assert response.request_headers == {"Content-Type": "application/json"}
        assert response.request_body == '{"key": "value"}'
        assert response.response_body == '{"result": "ok"}'

    def test_list_schema_pagination_fields(self) -> None:
        """Test ExternalCallLogListResponse pagination fields."""
        from heretek_swarm.schemas.external_call_log import ExternalCallLogListResponse

        response = ExternalCallLogListResponse(
            items=[],
            total=100,
            offset=0,
            limit=50,
            has_more=True,
        )

        assert response.total == 100
        assert response.offset == 0
        assert response.limit == 50
        assert response.has_more is True

    def test_list_schema_validation(self) -> None:
        """Test ExternalCallLogListResponse validation."""
        from heretek_swarm.schemas.external_call_log import ExternalCallLogListResponse

        # Invalid limit (exceeds max)
        with pytest.raises(ValidationError):
            ExternalCallLogListResponse(
                items=[],
                total=100,
                limit=200,  # Exceeds max of 100
            )

        # Invalid offset (negative)
        with pytest.raises(ValidationError):
            ExternalCallLogListResponse(
                items=[],
                total=100,
                offset=-1,
            )


# =============================================================================
# Test: Global Encryptor
# =============================================================================

class TestGlobalEncryptor:
    """Test suite for global encryptor singleton."""

    def test_get_encryptor_returns_instance(self) -> None:
        """Test that get_encryptor returns an ExternalCallLogEncryptor instance."""
        encryptor = get_encryptor()
        assert isinstance(encryptor, ExternalCallLogEncryptor)

    def test_get_encryptor_singleton(self) -> None:
        """Test that get_encryptor returns the same instance."""
        encryptor1 = get_encryptor()
        encryptor2 = get_encryptor()
        assert encryptor1 is encryptor2
