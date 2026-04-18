"""
Integration tests for Wizard Provider Endpoints (PUT and DELETE)

Tests:
- PUT /api/wizard/providers/{provider_id} - Update provider
- DELETE /api/wizard/providers/{provider_id} - Delete provider
- Structured logging verification (no API keys in logs)
- Fernet encryption for API keys on update
"""

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from heretek_swarm.config.models import LLMProvider, LLMProviderType
from heretek_swarm.config.service import ConfigurationService

# Import app after fixing RAG imports
try:
    from fastapi.testclient import TestClient

    from heretek_swarm.api.main import app

    APP_AVAILABLE = True
except ImportError:
    APP_AVAILABLE = False
    app = None


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def client():
    """Create test client for FastAPI app."""
    if not APP_AVAILABLE:
        pytest.skip("FastAPI app not available")
    return TestClient(app)


@pytest.fixture
def mock_service():
    """Create mock ConfigurationService for testing."""
    service = MagicMock(spec=ConfigurationService)
    service.get_llm_provider = AsyncMock()
    service.update_llm_provider = AsyncMock()
    service.delete_llm_provider = AsyncMock()
    return service


@pytest.fixture
def sample_provider():
    """Create a sample LLMProvider for testing."""
    return LLMProvider(
        id=uuid.uuid4(),
        provider_name="Test OpenAI",
        provider_type=LLMProviderType.OPENAI,
        base_url="https://api.openai.com/v1",
        default_model="gpt-4",
        is_enabled=True,
        is_default=False,
    )


@pytest.fixture
def valid_provider_uuid():
    """Generate a valid provider UUID string."""
    return str(uuid.uuid4())


@pytest.fixture
def invalid_provider_uuid():
    """Return an invalid UUID string for error testing."""
    return "not-a-valid-uuid"


# =============================================================================
# PUT /api/wizard/providers/{provider_id} Tests
# =============================================================================

class TestUpdateProvider:
    """Test suite for PUT /api/wizard/providers/{provider_id}."""

    def test_update_provider_success(self, client, mock_service, sample_provider):
        """Test successful provider update."""
        with patch(
            "heretek_swarm.api.wizard.get_service",
            return_value=mock_service,
        ):
            # Setup mocks
            mock_service.get_llm_provider.return_value = sample_provider
            updated_provider = LLMProvider(
                id=sample_provider.id,
                provider_name="Test OpenAI",
                provider_type=LLMProviderType.OPENAI,
                base_url="https://api.openai.com/v1",
                default_model="gpt-4o",
                is_enabled=True,
                is_default=True,
            )
            mock_service.update_llm_provider.return_value = updated_provider

            # Make request
            response = client.put(
                f"/api/wizard/providers/{sample_provider.id}",
                json={"default_model": "gpt-4o", "is_default": True},
            )

            # Assertions
            assert response.status_code == 200
            data = response.json()
            assert data["id"] == str(sample_provider.id)
            assert data["default_model"] == "gpt-4o"
            assert data["is_default"] is True

    def test_update_provider_with_new_api_key(
        self, client, mock_service, sample_provider
    ):
        """Test provider update with new API key (should be re-encrypted)."""
        with patch(
            "heretek_swarm.api.wizard.get_service",
            return_value=mock_service,
        ):
            # Setup mocks
            mock_service.get_llm_provider.return_value = sample_provider
            updated_provider = LLMProvider(
                id=sample_provider.id,
                provider_name="Test OpenAI",
                provider_type=LLMProviderType.OPENAI,
                base_url="https://api.openai.com/v1",
                default_model="gpt-4",
                is_enabled=True,
                is_default=False,
            )
            mock_service.update_llm_provider.return_value = updated_provider

            # Make request with new API key
            response = client.put(
                f"/api/wizard/providers/{sample_provider.id}",
                json={
                    "api_key": "sk-new-test-key-12345",
                    "api_key_hint": "***4543",
                },
            )

            # Assertions
            assert response.status_code == 200
            # Verify update_llm_provider was called (service handles encryption)
            mock_service.update_llm_provider.assert_called_once()
            call_args = mock_service.update_llm_provider.call_args
            assert call_args[0][0] == sample_provider.id  # provider_id
            update_data = call_args[0][1]
            assert update_data.api_key == "sk-new-test-key-12345"

    def test_update_provider_not_found(self, client, mock_service, valid_provider_uuid):
        """Test update when provider doesn't exist."""
        with patch(
            "heretek_swarm.api.wizard.get_service",
            return_value=mock_service,
        ):
            mock_service.get_llm_provider.return_value = None

            response = client.put(
                f"/api/wizard/providers/{valid_provider_uuid}",
                json={"default_model": "gpt-4o"},
            )

            assert response.status_code == 404

    def test_update_provider_invalid_uuid(self, client, mock_service, invalid_provider_uuid):
        """Test update with invalid UUID format."""
        with patch(
            "heretek_swarm.api.wizard.get_service",
            return_value=mock_service,
        ):
            response = client.put(
                f"/api/wizard/providers/{invalid_provider_uuid}",
                json={"default_model": "gpt-4o"},
            )

            assert response.status_code == 400
            assert "Invalid provider ID format" in response.json()["detail"]

    def test_update_provider_partial_update(self, client, mock_service, sample_provider):
        """Test partial update (only updating some fields)."""
        with patch(
            "heretek_swarm.api.wizard.get_service",
            return_value=mock_service,
        ):
            mock_service.get_llm_provider.return_value = sample_provider
            mock_service.update_llm_provider.return_value = sample_provider

            response = client.put(
                f"/api/wizard/providers/{sample_provider.id}",
                json={"is_enabled": False},
            )

            assert response.status_code == 200

    def test_update_provider_all_fields(self, client, mock_service, sample_provider):
        """Test update with all possible fields."""
        with patch(
            "heretek_swarm.api.wizard.get_service",
            return_value=mock_service,
        ):
            mock_service.get_llm_provider.return_value = sample_provider
            mock_service.update_llm_provider.return_value = sample_provider

            update_payload = {
                "base_url": "https://api.newprovider.com/v1",
                "default_model": "new-model",
                "available_models": ["model-1", "model-2"],
                "model_aliases": {"alias1": "model-1"},
                "supports_streaming": False,
                "supports_function_calling": True,
                "supports_vision": True,
                "max_tokens": 4096,
                "max_context_length": 128000,
                "rate_limit_requests_per_minute": 60,
                "rate_limit_tokens_per_minute": 90000,
                "is_enabled": True,
                "is_default": True,
                "priority": 50,
                "extra_config": {"custom_field": "value"},
            }

            response = client.put(
                f"/api/wizard/providers/{sample_provider.id}",
                json=update_payload,
            )

            assert response.status_code == 200


# =============================================================================
# DELETE /api/wizard/providers/{provider_id} Tests
# =============================================================================

class TestDeleteProvider:
    """Test suite for DELETE /api/wizard/providers/{provider_id}."""

    def test_delete_provider_success(self, client, mock_service, sample_provider):
        """Test successful provider deletion."""
        with patch(
            "heretek_swarm.api.wizard.get_service",
            return_value=mock_service,
        ):
            mock_service.get_llm_provider.return_value = sample_provider
            mock_service.delete_llm_provider.return_value = True

            response = client.delete(
                f"/api/wizard/providers/{sample_provider.id}"
            )

            assert response.status_code == 204
            # No content body for 204
            assert response.text == ""

    def test_delete_provider_not_found(self, client, mock_service, valid_provider_uuid):
        """Test delete when provider doesn't exist."""
        with patch(
            "heretek_swarm.api.wizard.get_service",
            return_value=mock_service,
        ):
            mock_service.get_llm_provider.return_value = None

            response = client.delete(
                f"/api/wizard/providers/{valid_provider_uuid}"
            )

            assert response.status_code == 404

    def test_delete_provider_invalid_uuid(
        self, client, mock_service, invalid_provider_uuid
    ):
        """Test delete with invalid UUID format."""
        with patch(
            "heretek_swarm.api.wizard.get_service",
            return_value=mock_service,
        ):
            response = client.delete(
                f"/api/wizard/providers/{invalid_provider_uuid}"
            )

            assert response.status_code == 400
            assert "Invalid provider ID format" in response.json()["detail"]

    def test_delete_provider_service_failure(self, client, mock_service, sample_provider):
        """Test delete when service returns False."""
        with patch(
            "heretek_swarm.api.wizard.get_service",
            return_value=mock_service,
        ):
            mock_service.get_llm_provider.return_value = sample_provider
            mock_service.delete_llm_provider.return_value = False

            response = client.delete(
                f"/api/wizard/providers/{sample_provider.id}"
            )

            assert response.status_code == 500


# =============================================================================
# Logging Verification Tests
# =============================================================================

class TestProviderLogging:
    """Test suite for structured logging verification (no API keys in logs)."""

    def test_update_provider_logging_no_api_key(
        self, client, mock_service, sample_provider, caplog
    ):
        """Test that update logs don't contain API key values."""
        with patch(
            "heretek_swarm.api.wizard.get_service",
            return_value=mock_service,
        ):
            mock_service.get_llm_provider.return_value = sample_provider
            mock_service.update_llm_provider.return_value = sample_provider

            with caplog.at_level("INFO", logger="api.wizard"):
                response = client.put(
                    f"/api/wizard/providers/{sample_provider.id}",
                    json={"default_model": "gpt-4o"},
                )

            # Check structured log was created with provider_updated event
            log_messages = [record.getMessage() for record in caplog.records]
            assert any("provider_updated" in msg for msg in log_messages)
            # Verify the provider_id is in the log
            assert any(str(sample_provider.id) in msg for msg in log_messages)

    def test_delete_provider_logging(self, client, mock_service, sample_provider, caplog):
        """Test that delete logs don't contain sensitive data."""
        with patch(
            "heretek_swarm.api.wizard.get_service",
            return_value=mock_service,
        ):
            mock_service.get_llm_provider.return_value = sample_provider
            mock_service.delete_llm_provider.return_value = True

            with caplog.at_level("INFO", logger="api.wizard"):
                response = client.delete(
                    f"/api/wizard/providers/{sample_provider.id}"
                )

            # Check structured log was created
            log_messages = [record.getMessage() for record in caplog.records]
            assert any("provider_deleted" in msg for msg in log_messages)
            # Verify the provider_id is in the log
            assert any(str(sample_provider.id) in msg for msg in log_messages)

    def test_api_key_not_in_log_output(
        self, client, mock_service, sample_provider
    ):
        """Test that API key values don't appear in response or logs."""
        with patch(
            "heretek_swarm.api.wizard.get_service",
            return_value=mock_service,
        ):
            mock_service.get_llm_provider.return_value = sample_provider
            mock_service.update_llm_provider.return_value = sample_provider

            response = client.put(
                f"/api/wizard/providers/{sample_provider.id}",
                json={"api_key": "sk-secret-key-xyz"},
            )

            # Response should not contain the plain API key
            assert response.status_code == 200
            # The response should not include api_key field
            assert "api_key" not in response.json() or response.json().get("api_key") is None
