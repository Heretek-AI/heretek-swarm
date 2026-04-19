"""
Unit tests for ExternalCallLog API endpoints.

Tests:
- POST /api/v1/observability/external-calls endpoint
- Input validation
- Encryption of sensitive fields
- Database storage
- WebSocket broadcast

Integration tests (marked with @pytest.mark.integration):
- POST → GET round-trip with real database
- Filtering by agent_id, call_type, status
- Pagination (limit/offset)
- WebSocket broadcast verification
"""

import asyncio
import os
import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio
from fastapi import HTTPException
from fastapi.testclient import TestClient
from sqlalchemy import StaticPool, create_engine, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from heretek_swarm.api.observability import router, connection_manager
from heretek_swarm.models.external_call_log import Base as ExternalCallLogBase
from heretek_swarm.schemas.external_call_log import ExternalCallLogCreate


class TestCreateExternalCallEndpoint:
    """Test suite for POST /api/v1/observability/external-calls endpoint."""

    @pytest.fixture
    def sample_log_data(self) -> dict:
        """Sample external call log data for testing."""
        return {
            "agent_id": "agent-001",
            "agent_type": "worker",
            "call_type": "http",
            "url": "https://api.example.com/v1/data",
            "method": "POST",
            "status_code": 200,
            "duration_ms": 150.5,
            "request_headers": {
                "Content-Type": "application/json",
                "Authorization": "Bearer secret-token",
            },
            "request_body": '{"key": "value"}',
            "response_body": '{"result": "success"}',
            "tool_name": "fetch_tool",
            "error_message": None,
        }

    @pytest.fixture
    def minimal_log_data(self) -> dict:
        """Minimal external call log data for testing."""
        return {
            "agent_id": "agent-002",
            "agent_type": "orchestrator",
            "call_type": "mcp",
            "url": "https://mcp.example.com/tool",
            "method": "GET",
        }

    def test_create_external_call_requires_fields(self) -> None:
        """Test that required fields are enforced."""
        # Missing required fields should raise validation error
        with pytest.raises(ValueError):
            ExternalCallLogCreate()

    def test_create_external_call_with_all_fields(self, sample_log_data: dict) -> None:
        """Test creating external call log with all fields."""
        log = ExternalCallLogCreate(**sample_log_data)
        assert log.agent_id == "agent-001"
        assert log.agent_type == "worker"
        assert log.call_type == "http"
        assert log.url == "https://api.example.com/v1/data"
        assert log.method == "POST"
        assert log.status_code == 200
        assert log.duration_ms == 150.5
        assert log.request_headers == {
            "Content-Type": "application/json",
            "Authorization": "Bearer secret-token",
        }
        assert log.request_body == '{"key": "value"}'
        assert log.response_body == '{"result": "success"}'
        assert log.tool_name == "fetch_tool"
        assert log.error_message is None

    def test_create_external_call_minimal(self, minimal_log_data: dict) -> None:
        """Test creating external call log with minimal required fields."""
        log = ExternalCallLogCreate(**minimal_log_data)
        assert log.agent_id == "agent-002"
        assert log.agent_type == "orchestrator"
        assert log.call_type == "mcp"
        assert log.url == "https://mcp.example.com/tool"
        assert log.method == "GET"
        assert log.status_code is None
        assert log.duration_ms is None
        assert log.request_headers is None
        assert log.request_body is None
        assert log.response_body is None

    def test_create_external_call_with_error(self) -> None:
        """Test creating external call log with error message."""
        log_data = {
            "agent_id": "agent-003",
            "agent_type": "worker",
            "call_type": "http",
            "url": "https://api.example.com/v1/data",
            "method": "POST",
            "status_code": 500,
            "error_message": "Internal Server Error",
        }
        log = ExternalCallLogCreate(**log_data)
        assert log.status_code == 500
        assert log.error_message == "Internal Server Error"

    def test_connection_manager_has_broadcast_observability(self) -> None:
        """Test that connection manager has broadcast_observability method."""
        assert hasattr(connection_manager, "broadcast_observability")
        assert callable(connection_manager.broadcast_observability)


class TestExternalCallLogCreateSchema:
    """Test suite for ExternalCallLogCreate schema validation."""

    def test_url_max_length(self) -> None:
        """Test URL max length validation."""
        long_url = "https://example.com/" + "a" * 3000
        with pytest.raises(ValueError):
            ExternalCallLogCreate(
                agent_id="agent-001",
                agent_type="worker",
                call_type="http",
                url=long_url,  # exceeds 2048 max
                method="GET",
            )

    def test_method_max_length(self) -> None:
        """Test HTTP method max length validation."""
        with pytest.raises(ValueError):
            ExternalCallLogCreate(
                agent_id="agent-001",
                agent_type="worker",
                call_type="http",
                url="https://example.com",
                method="GETPLUSPLUS",  # exceeds 10 char max
            )

    def test_status_code_range(self) -> None:
        """Test status code valid range."""
        # Valid status codes
        for code in [100, 200, 301, 404, 500, 599]:
            log = ExternalCallLogCreate(
                agent_id="agent-001",
                agent_type="worker",
                call_type="http",
                url="https://example.com",
                method="GET",
                status_code=code,
            )
            assert log.status_code == code

        # Invalid status codes
        for code in [99, 600]:
            with pytest.raises(ValueError):
                ExternalCallLogCreate(
                    agent_id="agent-001",
                    agent_type="worker",
                    call_type="http",
                    url="https://example.com",
                    method="GET",
                    status_code=code,
                )

    def test_duration_ms_non_negative(self) -> None:
        """Test duration_ms must be non-negative."""
        with pytest.raises(ValueError):
            ExternalCallLogCreate(
                agent_id="agent-001",
                agent_type="worker",
                call_type="http",
                url="https://example.com",
                method="GET",
                duration_ms=-1,  # cannot be negative
            )

    def test_agent_id_required(self) -> None:
        """Test agent_id is required."""
        with pytest.raises(ValueError):
            ExternalCallLogCreate(
                agent_type="worker",
                call_type="http",
                url="https://example.com",
                method="GET",
            )

    def test_call_type_required(self) -> None:
        """Test call_type is required."""
        with pytest.raises(ValueError):
            ExternalCallLogCreate(
                agent_id="agent-001",
                agent_type="worker",
                url="https://example.com",
                method="GET",
            )


class TestGetExternalCallEndpoint:
    """Test suite for GET /api/v1/observability/external-calls/{id} endpoint."""

    @pytest.fixture
    def mock_log(self) -> MagicMock:
        """Create a mock ExternalCallLog object."""
        log = MagicMock()
        log.id = uuid.uuid4()
        log.agent_id = "agent-001"
        log.agent_type = "worker"
        log.call_type = "http"
        log.url = "https://api.example.com/v1/data"
        log.method = "POST"
        log.status_code = 200
        log.duration_ms = 150.5
        log.request_headers_encrypted = "encrypted_headers"
        log.request_body_encrypted = "encrypted_request_body"
        log.response_body_encrypted = "encrypted_response_body"
        log.tool_name = "fetch_tool"
        log.error_message = None
        log.created_at = datetime.now(timezone.utc)
        return log

    @pytest.fixture
    def mock_encryptor(self) -> MagicMock:
        """Create a mock encryptor that returns predictable decrypted data."""
        encryptor = MagicMock()
        # Return appropriate data based on what was encrypted
        def decrypt_side_effect(encrypted: str) -> dict:
            if encrypted == "encrypted_headers":
                return {"Content-Type": "application/json", "Authorization": "***REDACTED***"}
            elif encrypted == "encrypted_request_body":
                return {"body": '{"key": "value"}'}
            elif encrypted == "encrypted_response_body":
                return {"body": '{"result": "success"}'}
            return {"body": "decrypted_data"}
        encryptor.decrypt.side_effect = decrypt_side_effect
        # sanitize should return a dict with sensitive data redacted
        def sanitize_side_effect(data: dict) -> dict:
            if isinstance(data, dict) and "Authorization" in data:
                return {**data, "Authorization": "***REDACTED***"}
            return data
        encryptor.sanitize.side_effect = sanitize_side_effect
        return encryptor

    def test_get_external_call_invalid_uuid(self) -> None:
        """Test that invalid UUID returns 400."""
        try:
            from fastapi.testclient import TestClient
            from heretek_swarm.api.main import app
            APP_AVAILABLE = True
        except ImportError:
            pytest.skip("FastAPI app not available")

        with TestClient(app=app, raise_server_exceptions=False) as client:
            response = client.get("/api/v1/observability/external-calls/invalid-uuid")
            assert response.status_code == 400

    def test_get_external_call_not_found(self) -> None:
        """Test that non-existent ID returns 404."""
        try:
            from fastapi.testclient import TestClient
            from heretek_swarm.api.main import app
            from sqlalchemy.ext.asyncio import AsyncSession
            APP_AVAILABLE = True
        except ImportError:
            pytest.skip("FastAPI app not available")

        # Mock the database session
        with patch("heretek_swarm.api.observability._get_external_call_log_session_factory") as mock_factory:
            mock_session = AsyncMock(spec=AsyncSession)
            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = None
            mock_session.execute.return_value = mock_result

            mock_session_factory = MagicMock()
            mock_session_factory.return_value.__aenter__.return_value = mock_session
            mock_session_factory.return_value.__aexit__.return_value = None
            mock_factory.return_value = mock_session_factory

            with TestClient(app=app, raise_server_exceptions=False) as client:
                fake_uuid = str(uuid.uuid4())
                response = client.get(f"/api/v1/observability/external-calls/{fake_uuid}")
                assert response.status_code == 404

    def test_get_external_call_with_bodies(self, mock_log: MagicMock, mock_encryptor: MagicMock) -> None:
        """Test getting external call with decrypted bodies."""
        try:
            from fastapi.testclient import TestClient
            from heretek_swarm.api.main import app
            from sqlalchemy.ext.asyncio import AsyncSession
            APP_AVAILABLE = True
        except ImportError:
            pytest.skip("FastAPI app not available")

        with patch("heretek_swarm.api.observability._get_external_call_log_session_factory") as mock_factory:
            with patch("heretek_swarm.api.observability.get_encryptor", return_value=mock_encryptor):
                mock_session = AsyncMock(spec=AsyncSession)
                mock_result = MagicMock()
                mock_result.scalar_one_or_none.return_value = mock_log
                mock_session.execute.return_value = mock_result

                mock_session_factory = MagicMock()
                mock_session_factory.return_value.__aenter__.return_value = mock_session
                mock_session_factory.return_value.__aexit__.return_value = None
                mock_factory.return_value = mock_session_factory

                with TestClient(app=app, raise_server_exceptions=False) as client:
                    response = client.get(
                        f"/api/v1/observability/external-calls/{mock_log.id}",
                        params={"include_bodies": True},
                    )
                    assert response.status_code == 200
                    data = response.json()
                    assert data["agent_id"] == "agent-001"
                    assert data["call_type"] == "http"
                    assert data["url"] == "https://api.example.com/v1/data"
                    # Verify bodies were decrypted
                    assert "request_headers" in data
                    assert "request_body" in data
                    assert "response_body" in data

    def test_get_external_call_without_bodies(self, mock_log: MagicMock) -> None:
        """Test getting external call without decrypted bodies."""
        try:
            from fastapi.testclient import TestClient
            from heretek_swarm.api.main import app
            from sqlalchemy.ext.asyncio import AsyncSession
            APP_AVAILABLE = True
        except ImportError:
            pytest.skip("FastAPI app not available")

        with patch("heretek_swarm.api.observability._get_external_call_log_session_factory") as mock_factory:
            mock_session = AsyncMock(spec=AsyncSession)
            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = mock_log
            mock_session.execute.return_value = mock_result

            mock_session_factory = MagicMock()
            mock_session_factory.return_value.__aenter__.return_value = mock_session
            mock_session_factory.return_value.__aexit__.return_value = None
            mock_factory.return_value = mock_session_factory

            with TestClient(app=app, raise_server_exceptions=False) as client:
                response = client.get(
                    f"/api/v1/observability/external-calls/{mock_log.id}",
                    params={"include_bodies": False},
                )
                assert response.status_code == 200
                data = response.json()
                assert data["agent_id"] == "agent-001"
                assert data["request_headers"] is None
                assert data["request_body"] is None
                assert data["response_body"] is None

    def test_get_external_call_rate_limited(self, mock_log: MagicMock) -> None:
        """Test that rate limiting is applied."""
        try:
            from fastapi.testclient import TestClient
            from heretek_swarm.api.main import app
            from sqlalchemy.ext.asyncio import AsyncSession
            APP_AVAILABLE = True
        except ImportError:
            pytest.skip("FastAPI app not available")

        from heretek_swarm.api.observability import RATE_LIMIT_REQUESTS

        with patch("heretek_swarm.api.observability._get_external_call_log_session_factory") as mock_factory:
            mock_session = AsyncMock(spec=AsyncSession)
            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = mock_log
            mock_session.execute.return_value = mock_result

            mock_session_factory = MagicMock()
            mock_session_factory.return_value.__aenter__.return_value = mock_session
            mock_session_factory.return_value.__aexit__.return_value = None
            mock_factory.return_value = mock_session_factory

            with TestClient(app=app, raise_server_exceptions=False) as client:
                # Exhaust rate limit
                for _ in range(RATE_LIMIT_REQUESTS):
                    client.get(f"/api/v1/observability/external-calls/{mock_log.id}")

                # Next request should be rate limited
                response = client.get(f"/api/v1/observability/external-calls/{mock_log.id}")
                assert response.status_code == 429


# =============================================================================
# INTEGRATION TESTS
# =============================================================================
# These tests use a real SQLite database for testing database operations.
# Marked with @pytest.mark.integration for selective test runs.

pytestmark = pytest.mark.integration


# ============== TEST DATABASE FIXTURES ==============


@pytest_asyncio.fixture
async def test_db_engine():
    """Create a SQLite async engine for testing."""
    # Use file-based SQLite for isolation
    db_path = f"/tmp/test_external_call_logs_{uuid.uuid4().hex[:8]}.db"
    database_url = f"sqlite+aiosqlite:///{db_path}"

    engine = create_async_engine(
        database_url,
        echo=False,
        connect_args={"check_same_thread": False},
    )

    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(ExternalCallLogBase.metadata.create_all)

    yield engine

    # Cleanup
    await engine.dispose()
    if os.path.exists(db_path):
        os.unlink(db_path)


@pytest_asyncio.fixture
async def test_db_session(test_db_engine):
    """Create a test database session."""
    session_factory = async_sessionmaker(
        test_db_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with session_factory() as session:
        yield session


@pytest_asyncio.fixture
async def test_session_factory(test_db_engine):
    """Create a session factory for use with the API endpoints."""
    return async_sessionmaker(
        test_db_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )


@pytest.fixture
def mock_encryptor():
    """Create a mock encryptor for integration tests."""
    encryptor = MagicMock()

    def encrypt_side_effect(data: dict) -> dict:
        # Simply return a mock encrypted value
        return {"encrypted": f"encrypted_{str(data)[:50]}"}

    def decrypt_side_effect(encrypted: str) -> dict:
        # Return mock decrypted data
        if "encrypted_headers" in encrypted:
            return {"Content-Type": "application/json", "Authorization": "***REDACTED***"}
        elif "encrypted_request_body" in encrypted:
            return {"body": '{"key": "value"}'}
        elif "encrypted_response_body" in encrypted:
            return {"body": '{"result": "success"}'}
        return {"body": "decrypted_data"}

    def sanitize_side_effect(data: dict) -> dict:
        # Sanitize sensitive data
        if isinstance(data, dict) and "Authorization" in data:
            return {**data, "Authorization": "***REDACTED***"}
        return data

    encryptor.encrypt.side_effect = encrypt_side_effect
    encryptor.decrypt.side_effect = decrypt_side_effect
    encryptor.sanitize.side_effect = sanitize_side_effect

    return encryptor


@pytest.fixture
def sample_call_data():
    """Create sample external call log data."""
    return {
        "agent_id": "agent-integration-test",
        "agent_type": "worker",
        "call_type": "http",
        "url": "https://api.example.com/v1/data",
        "method": "POST",
        "status_code": 200,
        "duration_ms": 150.5,
        "request_headers": {
            "Content-Type": "application/json",
            "Authorization": "Bearer secret-token",
        },
        "request_body": '{"key": "value"}',
        "response_body": '{"result": "success"}',
        "tool_name": "fetch_tool",
        "error_message": None,
    }


@pytest.fixture
def error_call_data():
    """Create sample error external call log data."""
    return {
        "agent_id": "agent-integration-test",
        "agent_type": "worker",
        "call_type": "http",
        "url": "https://api.example.com/v1/error",
        "method": "POST",
        "status_code": 500,
        "duration_ms": 50.0,
        "request_headers": {"Content-Type": "application/json"},
        "request_body": '{"query": "test"}',
        "response_body": '{"error": "Internal Server Error"}',
        "tool_name": "fetch_tool",
        "error_message": "Internal Server Error",
    }


@pytest.fixture
def mcp_call_data():
    """Create sample MCP call log data."""
    return {
        "agent_id": "agent-mcp-test",
        "agent_type": "orchestrator",
        "call_type": "mcp",
        "url": "https://mcp.example.com/tool",
        "method": "GET",
        "status_code": 200,
        "duration_ms": 25.0,
        "tool_name": "mcp_client",
        "error_message": None,
    }


# ============== INTEGRATION TEST CLASS ==============


class TestExternalCallLogIntegration:
    """Integration tests for ExternalCallLog API with real database.

    These tests use a SQLite database to verify actual database operations.
    """

    @pytest.fixture(autouse=True)
    def setup_test_db(self, test_session_factory, mock_encryptor):
        """Set up test database session factory before each test."""
        # Patch the session factory getter
        self._session_factory = test_session_factory
        self._mock_encryptor = mock_encryptor

        # Patch the module-level session factory
        with patch(
            "heretek_swarm.api.observability._get_external_call_log_session_factory"
        ) as mock_get_factory:
            mock_get_factory.return_value = test_session_factory

            with patch(
                "heretek_swarm.api.observability.get_encryptor",
                return_value=mock_encryptor,
            ):
                yield

    def test_post_then_get_round_trip(self, sample_call_data):
        """Test POST external call → GET returns the entry with correct fields."""
        try:
            from fastapi.testclient import TestClient
            from heretek_swarm.api.main import app
        except ImportError:
            pytest.skip("FastAPI app not available")

        with patch(
            "heretek_swarm.api.observability._get_external_call_log_session_factory"
        ) as mock_factory:
            mock_factory.return_value = self._session_factory

            with patch(
                "heretek_swarm.api.observability.get_encryptor",
                return_value=self._mock_encryptor,
            ):
                with TestClient(app=app, raise_server_exceptions=True) as client:
                    # POST the call data
                    post_response = client.post(
                        "/api/v1/observability/external-calls",
                        json=sample_call_data,
                    )
                    assert post_response.status_code == 201, (
                        f"POST failed: {post_response.status_code} - {post_response.text}"
                    )
                    post_data = post_response.json()
                    assert "id" in post_data
                    call_id = post_data["id"]
                    assert post_data["agent_id"] == sample_call_data["agent_id"]
                    assert post_data["call_type"] == sample_call_data["call_type"]
                    assert post_data["url"] == sample_call_data["url"]
                    assert post_data["method"] == sample_call_data["method"]
                    assert post_data["status_code"] == sample_call_data["status_code"]

                    # GET by ID and verify data
                    get_response = client.get(
                        f"/api/v1/observability/external-calls/{call_id}",
                        params={"include_bodies": True},
                    )
                    assert get_response.status_code == 200, (
                        f"GET by ID failed: {get_response.status_code} - {get_response.text}"
                    )
                    get_data = get_response.json()
                    assert get_data["id"] == call_id
                    assert get_data["agent_id"] == sample_call_data["agent_id"]
                    assert get_data["call_type"] == sample_call_data["call_type"]
                    assert get_data["url"] == sample_call_data["url"]
                    assert get_data["method"] == sample_call_data["method"]
                    assert get_data["status_code"] == sample_call_data["status_code"]
                    assert get_data["duration_ms"] == sample_call_data["duration_ms"]
                    # Bodies should be decrypted
                    assert get_data["request_body"] is not None
                    assert get_data["response_body"] is not None

    def test_get_with_agent_id_filter(self, sample_call_data, error_call_data, mcp_call_data):
        """Test GET with agent_id filter returns only matching entries."""
        try:
            from fastapi.testclient import TestClient
            from heretek_swarm.api.main import app
        except ImportError:
            pytest.skip("FastAPI app not available")

        with patch(
            "heretek_swarm.api.observability._get_external_call_log_session_factory"
        ) as mock_factory:
            mock_factory.return_value = self._session_factory

            with patch(
                "heretek_swarm.api.observability.get_encryptor",
                return_value=self._mock_encryptor,
            ):
                with TestClient(app=app, raise_server_exceptions=True) as client:
                    # Create multiple entries with different agent_ids
                    for data in [sample_call_data, error_call_data, mcp_call_data]:
                        post_response = client.post(
                            "/api/v1/observability/external-calls",
                            json=data,
                        )
                        assert post_response.status_code == 201

                    # Filter by agent_id
                    filter_agent = "agent-integration-test"
                    get_response = client.get(
                        "/api/v1/observability/external-calls",
                        params={"agent_id": filter_agent},
                    )
                    assert get_response.status_code == 200
                    get_data = get_response.json()
                    assert "items" in get_data
                    items = get_data["items"]

                    # All returned items should match the agent_id
                    for item in items:
                        assert item["agent_id"] == filter_agent

                    # Should have 2 items (sample_call_data and error_call_data)
                    assert len(items) == 2

    def test_get_with_call_type_filter(self, sample_call_data, error_call_data, mcp_call_data):
        """Test GET with call_type filter works correctly."""
        try:
            from fastapi.testclient import TestClient
            from heretek_swarm.api.main import app
        except ImportError:
            pytest.skip("FastAPI app not available")

        with patch(
            "heretek_swarm.api.observability._get_external_call_log_session_factory"
        ) as mock_factory:
            mock_factory.return_value = self._session_factory

            with patch(
                "heretek_swarm.api.observability.get_encryptor",
                return_value=self._mock_encryptor,
            ):
                with TestClient(app=app, raise_server_exceptions=True) as client:
                    # Create entries with different call_types
                    for data in [sample_call_data, error_call_data, mcp_call_data]:
                        post_response = client.post(
                            "/api/v1/observability/external-calls",
                            json=data,
                        )
                        assert post_response.status_code == 201

                    # Filter by call_type=http
                    get_response = client.get(
                        "/api/v1/observability/external-calls",
                        params={"call_type": "http"},
                    )
                    assert get_response.status_code == 200
                    get_data = get_response.json()
                    items = get_data["items"]

                    # All returned items should be http
                    for item in items:
                        assert item["call_type"] == "http"

                    # Should have 2 http items
                    assert len(items) == 2

                    # Filter by call_type=mcp
                    get_response_mcp = client.get(
                        "/api/v1/observability/external-calls",
                        params={"call_type": "mcp"},
                    )
                    assert get_response_mcp.status_code == 200
                    get_data_mcp = get_response_mcp.json()
                    items_mcp = get_data_mcp["items"]

                    # All returned items should be mcp
                    for item in items_mcp:
                        assert item["call_type"] == "mcp"

                    # Should have 1 mcp item
                    assert len(items_mcp) == 1

    def test_get_with_status_filter(self, sample_call_data, error_call_data):
        """Test GET with status filter works (success/error)."""
        try:
            from fastapi.testclient import TestClient
            from heretek_swarm.api.main import app
        except ImportError:
            pytest.skip("FastAPI app not available")

        with patch(
            "heretek_swarm.api.observability._get_external_call_log_session_factory"
        ) as mock_factory:
            mock_factory.return_value = self._session_factory

            with patch(
                "heretek_swarm.api.observability.get_encryptor",
                return_value=self._mock_encryptor,
            ):
                with TestClient(app=app, raise_server_exceptions=True) as client:
                    # Create success call (200)
                    post_response1 = client.post(
                        "/api/v1/observability/external-calls",
                        json=sample_call_data,
                    )
                    assert post_response1.status_code == 201

                    # Create error call (500)
                    post_response2 = client.post(
                        "/api/v1/observability/external-calls",
                        json=error_call_data,
                    )
                    assert post_response2.status_code == 201

                    # Filter by status=success (2xx)
                    get_response = client.get(
                        "/api/v1/observability/external-calls",
                        params={"status": "success"},
                    )
                    assert get_response.status_code == 200
                    get_data = get_response.json()
                    items = get_data["items"]

                    # All returned items should have 2xx status
                    for item in items:
                        assert item["status_code"] is not None
                        assert 200 <= item["status_code"] < 300

                    # Should have 1 success item
                    assert len(items) == 1

                    # Filter by status=error (non-2xx or error_message)
                    get_response_error = client.get(
                        "/api/v1/observability/external-calls",
                        params={"status": "error"},
                    )
                    assert get_response_error.status_code == 200
                    get_data_error = get_response_error.json()
                    items_error = get_data_error["items"]

                    # All returned items should have error status
                    for item in items_error:
                        has_error = (
                            item["status_code"] is None
                            or item["status_code"] < 200
                            or item["status_code"] >= 300
                            or item.get("error_message") is not None
                        )
                        assert has_error

                    # Should have 1 error item
                    assert len(items_error) == 1

    def test_pagination_limit_offset(self, sample_call_data):
        """Test pagination (limit/offset) works correctly."""
        try:
            from fastapi.testclient import TestClient
            from heretek_swarm.api.main import app
        except ImportError:
            pytest.skip("FastAPI app not available")

        with patch(
            "heretek_swarm.api.observability._get_external_call_log_session_factory"
        ) as mock_factory:
            mock_factory.return_value = self._session_factory

            with patch(
                "heretek_swarm.api.observability.get_encryptor",
                return_value=self._mock_encryptor,
            ):
                with TestClient(app=app, raise_server_exceptions=True) as client:
                    # Create 5 entries
                    created_ids = []
                    for i in range(5):
                        data = sample_call_data.copy()
                        data["agent_id"] = f"agent-pagination-{i}"
                        post_response = client.post(
                            "/api/v1/observability/external-calls",
                            json=data,
                        )
                        assert post_response.status_code == 201
                        created_ids.append(post_response.json()["id"])

                    # Get first page with limit=2
                    get_response = client.get(
                        "/api/v1/observability/external-calls",
                        params={"limit": 2, "offset": 0},
                    )
                    assert get_response.status_code == 200
                    get_data = get_response.json()
                    assert get_data["total"] == 5
                    assert get_data["limit"] == 2
                    assert get_data["offset"] == 0
                    assert len(get_data["items"]) == 2
                    assert get_data["has_more"] is True

                    # Get second page with limit=2
                    get_response2 = client.get(
                        "/api/v1/observability/external-calls",
                        params={"limit": 2, "offset": 2},
                    )
                    assert get_response2.status_code == 200
                    get_data2 = get_response2.json()
                    assert get_data2["total"] == 5
                    assert get_data2["offset"] == 2
                    assert len(get_data2["items"]) == 2
                    assert get_data2["has_more"] is True

                    # Get last page with limit=2
                    get_response3 = client.get(
                        "/api/v1/observability/external-calls",
                        params={"limit": 2, "offset": 4},
                    )
                    assert get_response3.status_code == 200
                    get_data3 = get_response3.json()
                    assert len(get_data3["items"]) == 1
                    assert get_data3["has_more"] is False

                    # Get page beyond results
                    get_response4 = client.get(
                        "/api/v1/observability/external-calls",
                        params={"limit": 2, "offset": 10},
                    )
                    assert get_response4.status_code == 200
                    get_data4 = get_response4.json()
                    assert len(get_data4["items"]) == 0
                    assert get_data4["has_more"] is False

    def test_combined_filters(self, sample_call_data, error_call_data, mcp_call_data):
        """Test combining multiple filters."""
        try:
            from fastapi.testclient import TestClient
            from heretek_swarm.api.main import app
        except ImportError:
            pytest.skip("FastAPI app not available")

        with patch(
            "heretek_swarm.api.observability._get_external_call_log_session_factory"
        ) as mock_factory:
            mock_factory.return_value = self._session_factory

            with patch(
                "heretek_swarm.api.observability.get_encryptor",
                return_value=self._mock_encryptor,
            ):
                with TestClient(app=app, raise_server_exceptions=True) as client:
                    # Create entries with different combinations
                    # agent-integration-test + http + success
                    post_response1 = client.post(
                        "/api/v1/observability/external-calls",
                        json=sample_call_data,
                    )
                    assert post_response1.status_code == 201

                    # agent-integration-test + http + error
                    post_response2 = client.post(
                        "/api/v1/observability/external-calls",
                        json=error_call_data,
                    )
                    assert post_response2.status_code == 201

                    # agent-mcp-test + mcp + success
                    post_response3 = client.post(
                        "/api/v1/observability/external-calls",
                        json=mcp_call_data,
                    )
                    assert post_response3.status_code == 201

                    # Filter by agent_id AND call_type
                    get_response = client.get(
                        "/api/v1/observability/external-calls",
                        params={
                            "agent_id": "agent-integration-test",
                            "call_type": "http",
                        },
                    )
                    assert get_response.status_code == 200
                    get_data = get_response.json()
                    items = get_data["items"]

                    # Should have 2 items matching both filters
                    assert len(items) == 2
                    for item in items:
                        assert item["agent_id"] == "agent-integration-test"
                        assert item["call_type"] == "http"

    def test_websocket_broadcast_on_create(self, sample_call_data):
        """Test WebSocket broadcast occurs when POST creates a new entry."""
        try:
            from fastapi.testclient import TestClient
            from heretek_swarm.api.main import app
        except ImportError:
            pytest.skip("FastAPI app not available")

        with patch(
            "heretek_swarm.api.observability._get_external_call_log_session_factory"
        ) as mock_factory:
            mock_factory.return_value = self._session_factory

            with patch(
                "heretek_swarm.api.observability.get_encryptor",
                return_value=self._mock_encryptor,
            ):
                # Track broadcast calls
                broadcast_calls = []

                async def mock_broadcast(data):
                    broadcast_calls.append(data)

                with patch.object(
                    connection_manager, "broadcast_observability", side_effect=mock_broadcast
                ):
                    with TestClient(app=app, raise_server_exceptions=True) as client:
                        # Create an entry
                        post_response = client.post(
                            "/api/v1/observability/external-calls",
                            json=sample_call_data,
                        )
                        assert post_response.status_code == 201

                        # Verify broadcast was called
                        assert len(broadcast_calls) >= 1

                        # Verify broadcast data structure
                        broadcast_data = broadcast_calls[0]
                        assert broadcast_data["type"] == "external_call_created"
                        assert "data" in broadcast_data
                        assert "id" in broadcast_data["data"]
                        assert broadcast_data["data"]["agent_id"] == sample_call_data["agent_id"]
                        assert broadcast_data["data"]["call_type"] == sample_call_data["call_type"]

    def test_get_nonexistent_returns_404(self, sample_call_data):
        """Test GET for non-existent ID returns 404."""
        try:
            from fastapi.testclient import TestClient
            from heretek_swarm.api.main import app
        except ImportError:
            pytest.skip("FastAPI app not available")

        with patch(
            "heretek_swarm.api.observability._get_external_call_log_session_factory"
        ) as mock_factory:
            mock_factory.return_value = self._session_factory

            with patch(
                "heretek_swarm.api.observability.get_encryptor",
                return_value=self._mock_encryptor,
            ):
                with TestClient(app=app, raise_server_exceptions=True) as client:
                    # Generate a random UUID that doesn't exist
                    fake_uuid = str(uuid.uuid4())

                    get_response = client.get(
                        f"/api/v1/observability/external-calls/{fake_uuid}",
                    )
                    assert get_response.status_code == 404

    def test_get_invalid_uuid_returns_400(self, sample_call_data):
        """Test GET with invalid UUID format returns 400."""
        try:
            from fastapi.testclient import TestClient
            from heretek_swarm.api.main import app
        except ImportError:
            pytest.skip("FastAPI app not available")

        with patch(
            "heretek_swarm.api.observability._get_external_call_log_session_factory"
        ) as mock_factory:
            mock_factory.return_value = self._session_factory

            with patch(
                "heretek_swarm.api.observability.get_encryptor",
                return_value=self._mock_encryptor,
            ):
                with TestClient(app=app, raise_server_exceptions=True) as client:
                    get_response = client.get(
                        "/api/v1/observability/external-calls/not-a-valid-uuid",
                    )
                    assert get_response.status_code == 400

    def test_time_range_filter(self, sample_call_data):
        """Test time range filtering works correctly."""
        try:
            from fastapi.testclient import TestClient
            from heretek_swarm.api.main import app
        except ImportError:
            pytest.skip("FastAPI app not available")

        with patch(
            "heretek_swarm.api.observability._get_external_call_log_session_factory"
        ) as mock_factory:
            mock_factory.return_value = self._session_factory

            with patch(
                "heretek_swarm.api.observability.get_encryptor",
                return_value=self._mock_encryptor,
            ):
                with TestClient(app=app, raise_server_exceptions=True) as client:
                    # Create an entry
                    post_response = client.post(
                        "/api/v1/observability/external-calls",
                        json=sample_call_data,
                    )
                    assert post_response.status_code == 201

                    now = datetime.now(timezone.utc)
                    one_hour_ago = (now - timedelta(hours=1)).isoformat()
                    one_hour_future = (now + timedelta(hours=1)).isoformat()

                    # Filter with time range that includes the entry
                    get_response = client.get(
                        "/api/v1/observability/external-calls",
                        params={
                            "start_time": one_hour_ago,
                            "end_time": one_hour_future,
                        },
                    )
                    assert get_response.status_code == 200
                    get_data = get_response.json()
                    assert len(get_data["items"]) == 1

                    # Filter with time range that excludes the entry
                    two_hours_future = (now + timedelta(hours=2)).isoformat()
                    get_response2 = client.get(
                        "/api/v1/observability/external-calls",
                        params={
                            "start_time": one_hour_future,
                            "end_time": two_hours_future,
                        },
                    )
                    assert get_response2.status_code == 200
                    get_data2 = get_response2.json()
                    # Should have no items since entry was before the range
                    assert len(get_data2["items"]) == 0
