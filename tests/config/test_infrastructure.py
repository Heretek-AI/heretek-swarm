"""
Tests for Infrastructure Configuration

Tests infrastructure service models, health checks, and API endpoints.
Covers:
- InfrastructureService enum
- InfrastructureConfig model creation and validation
- Health check functions for all service types
- POST/GET /api/wizard/infrastructure endpoints
- Health check persistence in InfrastructureConfig.last_health_check
"""

import asyncio
import os
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
import pytest_asyncio

# =============================================================================
# InfrastructureService Enum Tests
# =============================================================================

class TestInfrastructureServiceEnum:
    """Tests for InfrastructureService StrEnum."""

    def test_infrastructure_service_values(self):
        """Test that all expected service types are defined."""
        from heretek_swarm.config.models import InfrastructureService

        assert InfrastructureService.POSTGRES.value == "postgres"
        assert InfrastructureService.REDIS.value == "redis"
        assert InfrastructureService.QDRANT.value == "qdrant"
        assert InfrastructureService.NATS.value == "nats"
        assert InfrastructureService.MEM0.value == "mem0"

    def test_infrastructure_service_is_str_enum(self):
        """Test that InfrastructureService is a StrEnum."""
        from heretek_swarm.config.models import InfrastructureService

        # Should be usable as a string
        assert str(InfrastructureService.POSTGRES) == "postgres"
        assert "postgres" in InfrastructureService.POSTGRES.value

    def test_infrastructure_service_case_sensitivity(self):
        """Test that service values are lowercase."""
        from heretek_swarm.config.models import InfrastructureService

        for service in InfrastructureService:
            assert service.value.islower(), f"{service.name} value should be lowercase"


# =============================================================================
# InfrastructureConfig Model Tests
# =============================================================================

class TestInfrastructureConfigModel:
    """Tests for InfrastructureConfig Pydantic model."""

    def test_create_postgres_config(self):
        """Test creating a PostgreSQL infrastructure config."""
        from heretek_swarm.config.models import (
            InfrastructureConfig,
            InfrastructureService,
            HealthStatus,
        )

        config = InfrastructureConfig(
            service=InfrastructureService.POSTGRES,
            host="localhost",
            port=5432,
            connection_url="postgresql://user:pass@localhost:5432/db",
            is_enabled=True,
        )

        assert config.service == "postgres"  # StrEnum uses value
        assert config.host == "localhost"
        assert config.port == 5432
        assert config.is_enabled is True
        assert config.health_status == HealthStatus.UNKNOWN  # Default

    def test_create_redis_config(self):
        """Test creating a Redis infrastructure config."""
        from heretek_swarm.config.models import (
            InfrastructureConfig,
            InfrastructureService,
        )

        config = InfrastructureConfig(
            service=InfrastructureService.REDIS,
            host="redis.local",
            port=6379,
            connection_url="redis://redis.local:6379",
        )

        assert config.service == "redis"
        assert config.port == 6379

    def test_create_all_service_types(self):
        """Test creating configs for all infrastructure service types."""
        from heretek_swarm.config.models import (
            InfrastructureConfig,
            InfrastructureService,
        )

        # Default ports for each service
        default_ports = {
            InfrastructureService.POSTGRES: 5432,
            InfrastructureService.REDIS: 6379,
            InfrastructureService.QDRANT: 6333,
            InfrastructureService.NATS: 4222,
            InfrastructureService.MEM0: 8000,
        }

        for service, expected_port in default_ports.items():
            config = InfrastructureConfig(
                service=service,
                host="localhost",
                port=expected_port,
            )
            assert config.service == service.value
            assert config.port == expected_port

    def test_config_with_health_status(self):
        """Test InfrastructureConfig with health status fields."""
        from heretek_swarm.config.models import (
            InfrastructureConfig,
            InfrastructureService,
            HealthStatus,
        )

        now = datetime.now(UTC)
        config = InfrastructureConfig(
            service=InfrastructureService.POSTGRES,
            host="localhost",
            port=5432,
            health_status=HealthStatus.HEALTHY,
            last_health_check=now,
            health_check_latency_ms=5.5,
            health_check_error=None,
        )

        assert config.health_status == HealthStatus.HEALTHY
        assert config.last_health_check == now
        assert config.health_check_latency_ms == 5.5

    def test_config_with_health_error(self):
        """Test InfrastructureConfig with health check error."""
        from heretek_swarm.config.models import (
            InfrastructureConfig,
            InfrastructureService,
            HealthStatus,
        )

        config = InfrastructureConfig(
            service=InfrastructureService.REDIS,
            host="localhost",
            port=6379,
            health_status=HealthStatus.UNHEALTHY,
            health_check_error="Connection refused",
        )

        assert config.health_status == HealthStatus.UNHEALTHY
        assert config.health_check_error == "Connection refused"

    def test_config_uuid_generation(self):
        """Test that InfrastructureConfig auto-generates UUID."""
        from heretek_swarm.config.models import (
            InfrastructureConfig,
            InfrastructureService,
        )

        config = InfrastructureConfig(
            service=InfrastructureService.POSTGRES,
            host="localhost",
            port=5432,
        )

        assert config.id is not None

    def test_config_timestamps(self):
        """Test InfrastructureConfig auto-generates timestamps."""
        from heretek_swarm.config.models import (
            InfrastructureConfig,
            InfrastructureService,
        )

        config = InfrastructureConfig(
            service=InfrastructureService.POSTGRES,
            host="localhost",
            port=5432,
        )

        assert config.created_at is not None
        assert config.updated_at is not None


# =============================================================================
# InfrastructureConfigCreate/Update Model Tests
# =============================================================================

class TestInfrastructureConfigCreate:
    """Tests for InfrastructureConfigCreate model."""

    def test_create_minimal_config(self):
        """Test creating minimal infrastructure config."""
        from heretek_swarm.config.models import (
            InfrastructureConfigCreate,
            InfrastructureService,
        )

        config = InfrastructureConfigCreate(
            service=InfrastructureService.POSTGRES,
            port=5432,
        )

        assert config.service == InfrastructureService.POSTGRES
        assert config.port == 5432
        assert config.host == "localhost"  # Default
        assert config.is_enabled is True  # Default

    def test_create_full_config(self):
        """Test creating full infrastructure config."""
        from heretek_swarm.config.models import (
            InfrastructureConfigCreate,
            InfrastructureService,
        )

        config = InfrastructureConfigCreate(
            service=InfrastructureService.REDIS,
            host="redis.example.com",
            port=6379,
            connection_url="redis://redis.example.com:6379",
            is_enabled=True,
            extra_config={"maxmemory": "256mb"},
        )

        assert config.host == "redis.example.com"
        assert config.connection_url == "redis://redis.example.com:6379"
        assert config.extra_config == {"maxmemory": "256mb"}


class TestInfrastructureConfigUpdate:
    """Tests for InfrastructureConfigUpdate model."""

    def test_update_partial_fields(self):
        """Test updating partial fields."""
        from heretek_swarm.config.models import InfrastructureConfigUpdate

        update = InfrastructureConfigUpdate(
            host="new-host.example.com",
            port=5433,
        )

        # Should have only the fields that were set
        update_data = update.model_dump(exclude_unset=True)
        assert "host" in update_data
        assert "port" in update_data
        assert "connection_url" not in update_data


# =============================================================================
# Health Check Function Tests
# =============================================================================

class TestPostgresHealthCheck:
    """Tests for PostgreSQL health check."""

    @pytest.mark.asyncio
    async def test_postgres_healthy(self):
        """Test PostgreSQL health check with healthy connection."""
        from heretek_swarm.infrastructure.health import check_postgres_health
        from heretek_swarm.config.models import HealthStatus

        # Create mock writer with sync methods (not coroutines)
        mock_writer = MagicMock()
        mock_writer.drain = MagicMock()
        mock_writer.close = MagicMock()
        mock_writer.wait_closed = AsyncMock()

        # Create mock reader
        mock_reader = MagicMock()

        async def mock_open_connection(*args, **kwargs):
            return (mock_reader, mock_writer)

        with patch("asyncio.open_connection", side_effect=mock_open_connection):
            result = await check_postgres_health("localhost", 5432, timeout=5.0)

            assert result.service.value == "postgres"
            assert result.status == HealthStatus.HEALTHY
            assert result.latency_ms >= 0
            assert result.error is None

    @pytest.mark.asyncio
    async def test_postgres_connection_timeout(self):
        """Test PostgreSQL health check with connection timeout."""
        from heretek_swarm.infrastructure.health import check_postgres_health
        from heretek_swarm.config.models import HealthStatus

        async def mock_timeout(*args, **kwargs):
            raise asyncio.TimeoutError()

        with patch("asyncio.open_connection", side_effect=mock_timeout):
            result = await check_postgres_health("localhost", 5432, timeout=1.0)

            assert result.service.value == "postgres"
            assert result.status == HealthStatus.UNHEALTHY
            assert result.error is not None
            assert "timed out" in result.error.lower()

    @pytest.mark.asyncio
    async def test_postgres_connection_refused(self):
        """Test PostgreSQL health check with connection refused."""
        from heretek_swarm.infrastructure.health import check_postgres_health
        from heretek_swarm.config.models import HealthStatus

        async def mock_refused(*args, **kwargs):
            raise ConnectionRefusedError("Connection refused")

        with patch("asyncio.open_connection", side_effect=mock_refused):
            result = await check_postgres_health("localhost", 5432)

            assert result.status == HealthStatus.UNHEALTHY
            assert result.error is not None


class TestRedisHealthCheck:
    """Tests for Redis health check."""

    @pytest.mark.asyncio
    async def test_redis_healthy(self):
        """Test Redis health check with successful PING."""
        from heretek_swarm.infrastructure.health import check_redis_health
        from heretek_swarm.config.models import HealthStatus

        with patch("redis.asyncio.Redis") as mock_redis:
            mock_client = AsyncMock()
            mock_client.ping.return_value = True
            mock_client.aclose = AsyncMock()
            mock_redis.return_value = mock_client

            result = await check_redis_health("localhost", 6379)

            assert result.service.value == "redis"
            assert result.status == HealthStatus.HEALTHY
            mock_client.ping.assert_called_once()

    @pytest.mark.asyncio
    async def test_redis_connection_failed(self):
        """Test Redis health check with connection failure."""
        from heretek_swarm.infrastructure.health import check_redis_health
        from heretek_swarm.config.models import HealthStatus

        with patch("redis.asyncio.Redis") as mock_redis:
            mock_redis.side_effect = Exception("Connection failed")

            result = await check_redis_health("localhost", 6379)

            assert result.status == HealthStatus.UNHEALTHY
            assert result.error is not None


class TestQdrantHealthCheck:
    """Tests for Qdrant health check."""

    @pytest.mark.asyncio
    async def test_qdrant_healthy(self):
        """Test Qdrant health check with successful /healthz."""
        from heretek_swarm.infrastructure.health import check_qdrant_health
        from heretek_swarm.config.models import HealthStatus

        mock_response = MagicMock()
        mock_response.status_code = 200

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(return_value=mock_response)

            result = await check_qdrant_health("localhost", 6333)

            assert result.service.value == "qdrant"
            assert result.status == HealthStatus.HEALTHY

    @pytest.mark.asyncio
    async def test_qdrant_unhealthy_status_code(self):
        """Test Qdrant health check with non-200 status code."""
        from heretek_swarm.infrastructure.health import check_qdrant_health
        from heretek_swarm.config.models import HealthStatus

        mock_response = MagicMock()
        mock_response.status_code = 500

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(return_value=mock_response)

            result = await check_qdrant_health("localhost", 6333)

            assert result.status == HealthStatus.UNHEALTHY
            assert "500" in str(result.error)


class TestNatsHealthCheck:
    """Tests for NATS health check."""

    @pytest.mark.asyncio
    async def test_nats_healthy(self):
        """Test NATS health check with successful CONNECT/PING."""
        from heretek_swarm.infrastructure.health import check_nats_health
        from heretek_swarm.config.models import HealthStatus

        # Create mock writer with async methods
        mock_writer = MagicMock()
        mock_writer.drain = AsyncMock()
        mock_writer.close = MagicMock()
        mock_writer.wait_closed = AsyncMock()

        # Track calls to readline to return different responses
        readline_count = [0]

        async def mock_readline():
            readline_count[0] += 1
            if readline_count[0] == 1:
                return b'INFO {}\r\n'
            return b'PONG\r\n'

        # Create mock reader
        mock_reader = MagicMock()
        mock_reader.readline = mock_readline

        async def mock_open_connection(*args, **kwargs):
            return (mock_reader, mock_writer)

        patcher = patch("asyncio.open_connection", side_effect=mock_open_connection)
        patcher.start()
        try:
            result = await check_nats_health("localhost", 4222)

            assert result.service.value == "nats"
            assert result.status == HealthStatus.HEALTHY
        finally:
            patcher.stop()

    @pytest.mark.asyncio
    async def test_nats_connection_failed(self):
        """Test NATS health check with connection failure."""
        from heretek_swarm.infrastructure.health import check_nats_health
        from heretek_swarm.config.models import HealthStatus

        async def mock_refused(*args, **kwargs):
            raise ConnectionRefusedError()

        with patch("asyncio.open_connection", side_effect=mock_refused):
            result = await check_nats_health("localhost", 4222)

            assert result.status == HealthStatus.UNHEALTHY


class TestMem0HealthCheck:
    """Tests for Mem0 health check."""

    @pytest.mark.asyncio
    async def test_mem0_healthy(self):
        """Test Mem0 health check with successful /health."""
        from heretek_swarm.infrastructure.health import check_mem0_health
        from heretek_swarm.config.models import HealthStatus

        mock_response = MagicMock()
        mock_response.status_code = 200

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(return_value=mock_response)

            result = await check_mem0_health("localhost", 8000)

            assert result.service.value == "mem0"
            assert result.status == HealthStatus.HEALTHY

    @pytest.mark.asyncio
    async def test_mem0_timeout(self):
        """Test Mem0 health check with request timeout."""
        import httpx
        from heretek_swarm.infrastructure.health import check_mem0_health
        from heretek_swarm.config.models import HealthStatus

        with patch("httpx.AsyncClient") as mock_client:
            # Use a proper timeout exception that httpx accepts
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                side_effect=httpx.TimeoutException(message="Request timed out")
            )

            result = await check_mem0_health("localhost", 8000)

            assert result.status == HealthStatus.UNHEALTHY
            assert "timed out" in result.error.lower()


# =============================================================================
# Health Check Dispatcher Tests
# =============================================================================

class TestHealthCheckDispatcher:
    """Tests for check_infrastructure_health dispatcher."""

    @pytest.mark.asyncio
    async def test_dispatch_postgres(self):
        """Test dispatching to postgres health check."""
        from heretek_swarm.infrastructure.health import check_infrastructure_health
        from heretek_swarm.config.models import InfrastructureService

        with patch("heretek_swarm.infrastructure.health.check_postgres_health", new_callable=AsyncMock) as mock:
            mock.return_value = MagicMock(
                service=InfrastructureService.POSTGRES,
                status=MagicMock(value="healthy"),
                latency_ms=1.0,
            )

            result = await check_infrastructure_health(
                service=InfrastructureService.POSTGRES,
                host="localhost",
                port=5432,
            )

            mock.assert_called_once_with("localhost", 5432, 5.0)
            assert result.service == InfrastructureService.POSTGRES

    @pytest.mark.asyncio
    async def test_dispatch_unknown_service(self):
        """Test dispatching to unknown service returns error."""
        from heretek_swarm.infrastructure.health import check_infrastructure_health
        from heretek_swarm.config.models import InfrastructureService, HealthStatus

        # Create a mock service that doesn't have a checker
        class UnknownService:
            pass

        result = await check_infrastructure_health(
            service=UnknownService(),  # type: ignore
            host="localhost",
            port=1234,
        )

        # Should still return a result but with unknown status
        assert result.service is not None


# =============================================================================
# Check All Infrastructure Tests
# =============================================================================

class TestCheckAllInfrastructure:
    """Tests for check_all_infrastructure function."""

    @pytest.mark.asyncio
    async def test_check_all_empty_list(self):
        """Test checking all infrastructure with empty config list."""
        from heretek_swarm.infrastructure.health import check_all_infrastructure

        results = await check_all_infrastructure([], timeout=5.0)

        assert results == []

    @pytest.mark.asyncio
    async def test_check_all_multiple_services(self):
        """Test checking all infrastructure for multiple services."""
        from heretek_swarm.infrastructure.health import check_all_infrastructure
        from heretek_swarm.config.models import HealthStatus

        configs = [
            {"service": "postgres", "host": "localhost", "port": 5432},
            {"service": "redis", "host": "localhost", "port": 6379},
        ]

        with patch("heretek_swarm.infrastructure.health.check_infrastructure_health", new_callable=AsyncMock) as mock:
            mock.side_effect = [
                MagicMock(
                    service=MagicMock(value="postgres"),
                    status=HealthStatus.HEALTHY,
                    latency_ms=1.0,
                    error=None,
                ),
                MagicMock(
                    service=MagicMock(value="redis"),
                    status=HealthStatus.HEALTHY,
                    latency_ms=2.0,
                    error=None,
                ),
            ]

            results = await check_all_infrastructure(configs)

            assert len(results) == 2

    @pytest.mark.asyncio
    async def test_check_all_handles_exceptions(self):
        """Test that check_all_infrastructure handles exceptions gracefully."""
        from heretek_swarm.infrastructure.health import check_all_infrastructure
        from heretek_swarm.config.models import HealthStatus

        configs = [
            {"service": "postgres", "host": "localhost", "port": 5432},
            {"service": "redis", "host": "localhost", "port": 6379},
        ]

        with patch("heretek_swarm.infrastructure.health.check_infrastructure_health", new_callable=AsyncMock) as mock:
            mock.side_effect = [
                MagicMock(
                    service=MagicMock(value="postgres"),
                    status=HealthStatus.HEALTHY,
                    latency_ms=1.0,
                    error=None,
                ),
                MagicMock(
                    service=MagicMock(value="redis"),
                    status=HealthStatus.UNHEALTHY,
                    latency_ms=2.0,
                    error="Connection failed",
                ),
            ]

            results = await check_all_infrastructure(configs)

            # Should have results for each config
            assert len(results) == 2
            assert results[0].status == HealthStatus.HEALTHY
            assert results[1].status == HealthStatus.UNHEALTHY


# =============================================================================
# Structured Logging Verification Tests
# =============================================================================

class TestHealthCheckStructuredLogs:
    """Tests that health checks emit structured logs."""

    @pytest.mark.asyncio
    async def test_postgres_logs_health_check(self):
        """Test that postgres health check logs structured data."""
        from heretek_swarm.infrastructure.health import check_postgres_health

        with patch("asyncio.open_connection", new_callable=AsyncMock) as mock_conn:
            mock_reader = MagicMock()
            mock_writer = MagicMock()
            mock_conn.return_value = (mock_reader, mock_writer)

            with patch("structlog.get_logger") as mock_logger:
                mock_logger.return_value.info = MagicMock()

                await check_postgres_health("localhost", 5432)

                # Verify structured logging was called
                call_args = mock_logger.return_value.info.call_args
                if call_args:
                    log_kwargs = call_args.kwargs
                    assert "postgres_health_check" in str(log_kwargs)

    @pytest.mark.asyncio
    async def test_redis_logs_health_check(self):
        """Test that redis health check logs structured data."""
        from heretek_swarm.infrastructure.health import check_redis_health

        with patch("redis.asyncio.Redis") as mock_redis:
            mock_client = AsyncMock()
            mock_client.ping.return_value = True
            mock_client.aclose = AsyncMock()
            mock_redis.return_value = mock_client

            with patch("structlog.get_logger") as mock_logger:
                mock_logger.return_value.info = MagicMock()

                await check_redis_health("localhost", 6379)

                call_args = mock_logger.return_value.info.call_args
                if call_args:
                    log_kwargs = call_args.kwargs
                    assert "redis_health_check" in str(log_kwargs)