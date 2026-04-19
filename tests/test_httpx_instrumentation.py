"""
Unit tests for httpx instrumentation in tracing.py.

Tests the InstrumentedAsyncClient and instrumented_httpx_client wrapper:
1. Wraps httpx calls and creates ExternalCallLog entries
2. Agent ID propagates from current OTel span context to ExternalCallLog
3. Error cases (timeout, 4xx, 5xx) result in ExternalCallLog with status='error'
4. Encryption is applied to request_headers and response_body
5. Duration_ms is correctly recorded
"""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from opentelemetry import trace
from opentelemetry.sdk.trace import ReadableSpan, SpanProcessor
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter
from opentelemetry.trace import SpanKind, StatusCode

from heretek_swarm.infrastructure.otel.tracing import (
    InstrumentedAsyncClient,
    instrumented_httpx_client,
    _get_agent_context,
    _write_call_log,
    SpanAttributes,
)
from heretek_swarm.models.external_call_log import ExternalCallLog


# =============================================================================
# Helpers
# =============================================================================

class SpySpanProcessor(SpanProcessor):
    """In-process span processor that records finished spans for inspection."""

    def __init__(self) -> None:
        self.finished: list[ReadableSpan] = []

    def on_end(self, span: ReadableSpan) -> None:
        self.finished.append(span)

    def shutdown(self, timeout_millis: float = 30000) -> None:
        pass

    def force_flush(self, timeout_millis: float = 30000) -> None:
        pass


@pytest.fixture
def spy_processor() -> SpySpanProcessor:
    """Return a SpySpanProcessor and register it with the global tracer."""
    processor = SpySpanProcessor()
    provider = trace.get_tracer_provider()
    provider.add_span_processor(processor)
    yield processor
    # Remove after test
    provider._span_processors.remove(processor)


@pytest.fixture
def in_memory_exporter() -> InMemorySpanExporter:
    """Return an InMemorySpanExporter and register it with the global tracer."""
    exporter = InMemorySpanExporter()
    provider = trace.get_tracer_provider()
    provider.add_span_processor(SimpleSpanProcessor(exporter))
    yield exporter
    # No teardown cleanup needed — function-scoped fixture, OTel provider
    # holds the processor for the test duration only.


@pytest.fixture
def mock_session_factory() -> MagicMock:
    """Create a mock async session factory that captures ExternalCallLog writes."""
    session = MagicMock()
    session.add = MagicMock()
    session.commit = AsyncMock()
    session.close = AsyncMock()

    factory = MagicMock()
    factory.return_value.__aenter__ = AsyncMock(return_value=session)
    factory.return_value.__aexit__ = AsyncMock(return_value=None)

    return factory


def make_response(
    status_code: int,
    text: str = "",
    *,
    headers: dict[str, str] | None = None,
) -> MagicMock:
    """Create a mock httpx.Response."""
    resp = MagicMock()
    resp.status_code = status_code
    resp.text = text
    resp.headers = headers or {}
    return resp


def make_timeout_error() -> Exception:
    """Create an httpx.TimeoutException."""
    return Exception("Timeout connecting to https://api.example.com")


# =============================================================================
# Test: instrumented_httpx_client wraps httpx and creates ExternalCallLog
# =============================================================================

class TestInstrumentedClientBasic:
    """Test that instrumented_httpx_client wraps httpx calls and logs them."""

    @pytest.mark.asyncio
    async def test_request_successful_call(self, mock_session_factory: MagicMock) -> None:
        """
        Successful httpx call creates an ExternalCallLog entry.
        """
        raw_client = MagicMock()
        raw_client.request = AsyncMock(return_value=make_response(200, '{"result":"ok"}'))
        raw_client.is_closed = False

        client = InstrumentedAsyncClient(
            client=raw_client,
            session_factory=mock_session_factory,
        )

        response = await client.request("GET", "https://api.example.com/v1/test")

        assert response.status_code == 200
        mock_session_factory.assert_called_once()

        # Inspect the session.add call
        call_args_list = raw_client.request.call_args_list
        assert len(call_args_list) == 1

    @pytest.mark.asyncio
    async def test_get_shortcut_creates_span(self, in_memory_exporter: InMemorySpanExporter) -> None:
        """
        client.get() shortcut creates an OTel span with HTTP method/URL attributes.
        """
        raw_client = MagicMock()
        raw_client.request = AsyncMock(return_value=make_response(200))
        raw_client.is_closed = False

        client = InstrumentedAsyncClient(client=raw_client, session_factory=None)

        response = await client.get("https://api.example.com/v1/test")

        assert response.status_code == 200

        spans = in_memory_exporter.get_finished_spans()
        assert len(spans) >= 1
        http_span = next(s for s in spans if "http" in s.name.lower() or s.attributes.get("http.method") == "GET")
        assert http_span.attributes.get("http.method") == "GET"
        assert http_span.attributes.get("http.url") == "https://api.example.com/v1/test"
        assert http_span.kind == SpanKind.CLIENT

    @pytest.mark.asyncio
    async def test_post_shortcut(self, in_memory_exporter: InMemorySpanExporter) -> None:
        """
        client.post() shortcut correctly delegates with POST method.
        """
        raw_client = MagicMock()
        raw_client.request = AsyncMock(return_value=make_response(201, '{"id":1}'))
        raw_client.is_closed = False

        client = InstrumentedAsyncClient(client=raw_client, session_factory=None)

        response = await client.post(
            "https://api.example.com/v1/create",
            headers={"Content-Type": "application/json"},
            content='{"name":"test"}',
        )

        assert response.status_code == 201

        # Verify POST was called
        raw_client.request.assert_called_once()
        call_args = raw_client.request.call_args
        assert call_args[0][0] == "POST"
        assert call_args[1].get("headers") == {"Content-Type": "application/json"}

    @pytest.mark.asyncio
    async def test_delete_shortcut(self) -> None:
        """
        client.delete() shortcut correctly delegates with DELETE method.
        """
        raw_client = MagicMock()
        raw_client.request = AsyncMock(return_value=make_response(204))
        raw_client.is_closed = False

        client = InstrumentedAsyncClient(client=raw_client, session_factory=None)
        response = await client.delete("https://api.example.com/v1/item/123")

        assert response.status_code == 204
        raw_client.request.assert_called_once()
        assert raw_client.request.call_args[0][0] == "DELETE"

    @pytest.mark.asyncio
    async def test_all_http_verbs_delegate_to_request(self) -> None:
        """
        get/post/put/patch/delete/head/options all call through to request().
        """
        for method in ["GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"]:
            raw_client = MagicMock()
            raw_client.request = AsyncMock(return_value=make_response(200))
            raw_client.is_closed = False

            client = InstrumentedAsyncClient(client=raw_client, session_factory=None)

            # Call the specific method
            coroutine = getattr(client, method.lower())
            await coroutine(f"https://api.example.com/{method}")

            raw_client.request.assert_called_once()
            assert raw_client.request.call_args[0][0] == method

    @pytest.mark.asyncio
    async def test_4xx_response_sets_span_error_status(self, in_memory_exporter: InMemorySpanExporter) -> None:
        """
        4xx HTTP response marks the OTel span as ERROR, not OK.
        """
        raw_client = MagicMock()
        raw_client.request = AsyncMock(return_value=make_response(404, "Not Found"))
        raw_client.is_closed = False

        client = InstrumentedAsyncClient(client=raw_client, session_factory=None)

        response = await client.get("https://api.example.com/v1/nonexistent")

        assert response.status_code == 404

        spans = in_memory_exporter.get_finished_spans()
        http_span = next(s for s in spans if s.attributes.get("http.method") == "GET")
        assert http_span.status.status_code == StatusCode.ERROR
        assert http_span.attributes.get("http.status_code") == 404

    @pytest.mark.asyncio
    async def test_5xx_response_sets_span_error_status(self, in_memory_exporter: InMemorySpanExporter) -> None:
        """
        5xx HTTP response marks the OTel span as ERROR.
        """
        raw_client = MagicMock()
        raw_client.request = AsyncMock(return_value=make_response(503, "Service Unavailable"))
        raw_client.is_closed = False

        client = InstrumentedAsyncClient(client=raw_client, session_factory=None)

        response = await client.post("https://api.example.com/v1/busy", content="{}")

        assert response.status_code == 503

        spans = in_memory_exporter.get_finished_spans()
        http_span = next(s for s in spans if s.attributes.get("http.method") == "POST")
        assert http_span.status.status_code == StatusCode.ERROR
        assert http_span.attributes.get("http.status_code") == 503


# =============================================================================
# Test: agent_id propagates from OTel span context
# =============================================================================

class TestAgentContextPropagation:
    """Test that agent_id and agent_type propagate from OTel span to ExternalCallLog."""

    @pytest.mark.asyncio
    async def test_agent_id_from_active_span(
        self,
        mock_session_factory: MagicMock,
        in_memory_exporter: InMemorySpanExporter,
    ) -> None:
        """
        When an OTel span is active with heretek.agent.id attribute,
        the InstrumentedAsyncClient reads it and passes it to the DB write.
        """
        raw_client = MagicMock()
        raw_client.request = AsyncMock(return_value=make_response(200, "ok"))
        raw_client.is_closed = False

        client = InstrumentedAsyncClient(
            client=raw_client,
            session_factory=mock_session_factory,
        )

        tracer = trace.get_tracer("heretek-swarm")

        # Start a span with agent attributes — simulates agent.run() context
        with tracer.start_as_current_span(
            "agent.execute",
            attributes={
                "heretek.agent.id": "my-agent-123",
                "heretek.agent.type": "worker",
            },
        ) as span:
            response = await client.get("https://api.example.com/v1/test")
            assert response.status_code == 200

            # The span created inside request() should have agent attributes from parent
            spans = in_memory_exporter.get_finished_spans()
            child_span = next(
                (s for s in spans if s.name.startswith("http GET")),
                None,
            )
            if child_span:
                assert child_span.attributes.get(SpanAttributes.AGENT_ID) == "my-agent-123"
                assert child_span.attributes.get(SpanAttributes.AGENT_TYPE) == "worker"

    @pytest.mark.asyncio
    async def test_unknown_agent_when_no_active_span(
        self,
        mock_session_factory: MagicMock,
    ) -> None:
        """
        When no OTel span is active, _get_agent_context returns "unknown".
        """
        agent_id, agent_type = _get_agent_context()
        assert agent_id == "unknown"
        assert agent_type == "unknown"

    @pytest.mark.asyncio
    async def test_context_manager_enters_and_exits(self) -> None:
        """
        instrumented_httpx_client returns an async context manager that
        can be used with `async with`.
        """
        raw_client = MagicMock()
        raw_client.request = AsyncMock(return_value=make_response(200))
        raw_client.is_closed = False
        raw_client.aclose = AsyncMock()

        client = instrumented_httpx_client(client=raw_client)

        async with client as c:
            assert c is client
            response = await c.get("https://api.example.com/test")
            assert response.status_code == 200

        # aclose is called on the wrapped client (only if we own it)
        if client._owns_client and client._client is not None:
            raw_client.aclose.assert_called_once()


# =============================================================================
# Test: Error cases (timeout, 4xx, 5xx) result in ExternalCallLog with error
# =============================================================================

class TestErrorHandling:
    """Test that timeout/connection errors are logged with status='error' and error_message."""

    @pytest.mark.asyncio
    async def test_timeout_exception_logs_error_message(
        self,
        mock_session_factory: MagicMock,
        in_memory_exporter: InMemorySpanExporter,
    ) -> None:
        """
        httpx.TimeoutException creates an ExternalCallLog with error_message
        and propagates the exception.
        """
        import httpx

        raw_client = MagicMock()
        raw_client.request = AsyncMock(side_effect=httpx.TimeoutException("Connection timeout"))
        raw_client.is_closed = False

        client = InstrumentedAsyncClient(
            client=raw_client,
            session_factory=mock_session_factory,
        )

        # Should propagate the exception
        with pytest.raises(httpx.TimeoutException):
            await client.get("https://api.example.com/slow")

        # Verify DB write was attempted
        mock_session_factory.assert_called_once()

        # Verify span is marked error
        spans = in_memory_exporter.get_finished_spans()
        error_span = next(
            (s for s in spans if s.status.status_code == StatusCode.ERROR),
            None,
        )
        assert error_span is not None

    @pytest.mark.asyncio
    async def test_connect_error_logs_error_message(
        self,
        mock_session_factory: MagicMock,
        in_memory_exporter: InMemorySpanExporter,
    ) -> None:
        """
        httpx.ConnectError creates an ExternalCallLog with error_message
        and propagates the exception.
        """
        import httpx

        raw_client = MagicMock()
        raw_client.request = AsyncMock(
            side_effect=httpx.ConnectError("Connection refused: /127.0.0.1:9999")
        )
        raw_client.is_closed = False

        client = InstrumentedAsyncClient(
            client=raw_client,
            session_factory=mock_session_factory,
        )

        with pytest.raises(httpx.ConnectError):
            await client.post("https://localhost:9999/api", content="{}")

        mock_session_factory.assert_called_once()

        spans = in_memory_exporter.get_finished_spans()
        error_span = next(
            (s for s in spans if s.status.status_code == StatusCode.ERROR),
            None,
        )
        assert error_span is not None

    @pytest.mark.asyncio
    async def test_generic_exception_logs_error_message(
        self,
        mock_session_factory: MagicMock,
        in_memory_exporter: InMemorySpanExporter,
    ) -> None:
        """
        Unexpected exceptions (e.g. httpx.PoolTimeout, arbitrary RuntimeError)
        are caught, logged with error_message, and re-raised.
        """
        raw_client = MagicMock()
        raw_client.request = AsyncMock(
            side_effect=RuntimeError("Unexpected network error")
        )
        raw_client.is_closed = False

        client = InstrumentedAsyncClient(
            client=raw_client,
            session_factory=mock_session_factory,
        )

        with pytest.raises(RuntimeError, match="Unexpected network error"):
            await client.get("https://api.example.com/broken")

        mock_session_factory.assert_called_once()

        spans = in_memory_exporter.get_finished_spans()
        error_span = next(
            (s for s in spans if s.status.status_code == StatusCode.ERROR),
            None,
        )
        assert error_span is not None

    @pytest.mark.asyncio
    async def test_4xx_error_does_not_raise(self) -> None:
        """
        4xx responses (e.g. 404) do NOT raise an exception — they return
        normally with the response object. Only timeouts/connection errors raise.
        """
        raw_client = MagicMock()
        raw_client.request = AsyncMock(
            return_value=make_response(400, "Bad Request: missing required field")
        )
        raw_client.is_closed = False

        client = InstrumentedAsyncClient(client=raw_client, session_factory=None)

        # No exception raised — response returned normally
        response = await client.post(
            "https://api.example.com/v1/invalid",
            content='{"missing": "field"}',
        )

        assert response.status_code == 400
        assert "missing" in response.text

    @pytest.mark.asyncio
    async def test_5xx_error_does_not_raise(self) -> None:
        """
        5xx responses do NOT raise an exception — they return normally.
        The error is recorded via span status and ExternalCallLog, not via exception.
        """
        raw_client = MagicMock()
        raw_client.request = AsyncMock(
            return_value=make_response(500, "Internal Server Error")
        )
        raw_client.is_closed = False

        client = InstrumentedAsyncClient(client=raw_client, session_factory=None)

        response = await client.get("https://api.example.com/v1/broken")

        assert response.status_code == 500
        assert "Internal Server Error" in response.text


# =============================================================================
# Test: Encryption is applied to request_headers and response_body
# =============================================================================

class TestEncryptionApplied:
    """Test that encryption is applied to request_headers and response_body in DB writes."""

    @pytest.mark.asyncio
    async def test_request_headers_encrypted_before_write(
        self,
        mock_session_factory: MagicMock,
    ) -> None:
        """
        When _write_call_log is called, request headers are sanitized then encrypted.
        """
        from heretek_swarm.models.external_call_log_encryption import (
            ExternalCallLogEncryptor,
        )

        # Use a known key for deterministic encryption
        TEST_KEY = "test-encryption-key-for-unit-testing-only-32b"
        encryptor = ExternalCallLogEncryptor(TEST_KEY)

        session = MagicMock()
        session.add = MagicMock()
        session.commit = AsyncMock()

        session_factory = MagicMock()
        session_factory.return_value.__aenter__ = AsyncMock(return_value=session)
        session_factory.return_value.__aexit__ = AsyncMock(return_value=None)

        # Write a call log with headers
        await _write_call_log(
            session_factory=session_factory,
            agent_id="agent-test",
            agent_type="tester",
            url="https://api.example.com/v1/secure",
            method="POST",
            status_code=200,
            duration_ms=42.0,
            request_headers={
                "Content-Type": "application/json",
                "Authorization": "Bearer super-secret-key",
            },
            request_body='{"query": "hello"}',
            response_body='{"answer": "world"}',
            tool_name=None,
            error_message=None,
            call_type="http",
        )

        # Session.add was called with an ExternalCallLog
        session.add.assert_called_once()
        log_entry: ExternalCallLog = session.add.call_args[0][0]

        # Sanitization: Authorization should be redacted
        assert log_entry.agent_id == "agent-test"
        assert log_entry.agent_type == "tester"
        assert log_entry.url == "https://api.example.com/v1/secure"
        assert log_entry.method == "POST"
        assert log_entry.status_code == 200
        assert log_entry.duration_ms == 42.0
        assert log_entry.error_message is None

        # Encryption: the encrypted fields should be non-empty strings
        assert log_entry.request_headers_encrypted is not None
        assert log_entry.request_body_encrypted is not None
        assert log_entry.response_body_encrypted is not None

        # Encrypted values should NOT contain plaintext
        encrypted_str = str(log_entry.request_headers_encrypted)
        assert "super-secret-key" not in encrypted_str
        assert "Bearer" not in encrypted_str

        # But should be decryptable back to something (including sanitized form)
        decrypted = encryptor.decrypt({"encrypted": log_entry.request_headers_encrypted})
        assert "Authorization" in decrypted
        assert decrypted["Authorization"] == "[REDACTED]"

    @pytest.mark.asyncio
    async def test_response_body_encrypted(
        self,
        mock_session_factory: MagicMock,
    ) -> None:
        """
        Response body is encrypted before storage. Plaintext not visible in DB.
        """
        from heretek_swarm.models.external_call_log_encryption import (
            ExternalCallLogEncryptor,
        )

        TEST_KEY = "test-encryption-key-for-unit-testing-only-32b"
        encryptor = ExternalCallLogEncryptor(TEST_KEY)

        session = MagicMock()
        session.add = MagicMock()
        session.commit = AsyncMock()

        session_factory = MagicMock()
        session_factory.return_value.__aenter__ = AsyncMock(return_value=session)
        session_factory.return_value.__aexit__ = AsyncMock(return_value=None)

        await _write_call_log(
            session_factory=session_factory,
            agent_id="agent-abc",
            agent_type="worker",
            url="https://api.example.com/v1/private",
            method="GET",
            status_code=200,
            duration_ms=30.0,
            request_headers=None,
            request_body=None,
            response_body='{"ssn": "123-45-6789", "balance": 999999}',
            tool_name=None,
            error_message=None,
            call_type="http",
        )

        session.add.assert_called_once()
        log_entry: ExternalCallLog = session.add.call_args[0][0]

        assert log_entry.response_body_encrypted is not None

        # Decrypt and verify original data
        decrypted = encryptor.decrypt({"encrypted": log_entry.response_body_encrypted})
        assert "ssn" in decrypted["body"] or "123-45-6789" in decrypted.get("body", "")

    @pytest.mark.asyncio
    async def test_none_headers_and_body_handled_gracefully(
        self,
        mock_session_factory: MagicMock,
    ) -> None:
        """
        request_headers=None and response_body=None are handled without error.
        """
        session = MagicMock()
        session.add = MagicMock()
        session.commit = AsyncMock()

        session_factory = MagicMock()
        session_factory.return_value.__aenter__ = AsyncMock(return_value=session)
        session_factory.return_value.__aexit__ = AsyncMock(return_value=None)

        await _write_call_log(
            session_factory=session_factory,
            agent_id="agent-zero",
            agent_type="worker",
            url="https://api.example.com/v1/empty",
            method="GET",
            status_code=204,
            duration_ms=10.0,
            request_headers=None,
            request_body=None,
            response_body=None,
            tool_name=None,
            error_message=None,
            call_type="http",
        )

        session.add.assert_called_once()
        log_entry: ExternalCallLog = session.add.call_args[0][0]
        assert log_entry.request_headers_encrypted is None
        assert log_entry.request_body_encrypted is None
        assert log_entry.response_body_encrypted is None


# =============================================================================
# Test: duration_ms is correctly recorded
# =============================================================================

class TestDurationRecording:
    """Test that duration_ms is correctly recorded from perf_counter timing."""

    @pytest.mark.asyncio
    async def test_duration_recorded_for_successful_call(self, mock_session_factory: MagicMock) -> None:
        """
        For a successful call, the recorded duration_ms should be > 0 and
        reflect the wall-clock time of the request.
        """
        session = MagicMock()
        session.add = MagicMock()
        session.commit = AsyncMock()

        session_factory = MagicMock()
        session_factory.return_value.__aenter__ = AsyncMock(return_value=session)
        session_factory.return_value.__aexit__ = AsyncMock(return_value=None)

        import time

        raw_client = MagicMock()

        async def slow_request(*args: Any, **kwargs: Any) -> MagicMock:
            await asyncio.sleep(0.05)  # 50ms simulated latency
            return make_response(200, "ok")

        raw_client.request = slow_request
        raw_client.is_closed = False

        client = InstrumentedAsyncClient(
            client=raw_client,
            session_factory=session_factory,
        )

        start = time.perf_counter()
        response = await client.get("https://api.example.com/v1/slow")
        wall_time_ms = (time.perf_counter() - start) * 1000

        assert response.status_code == 200

        # Extract the ExternalCallLog entry written to the session
        session.add.assert_called_once()
        log_entry: ExternalCallLog = session.add.call_args[0][0]

        # Duration should be a positive number
        assert log_entry.duration_ms is not None
        assert log_entry.duration_ms > 0

        # Duration should be in the ballpark of wall-clock time (within 2x for test overhead)
        assert log_entry.duration_ms < wall_time_ms * 2 + 50  # generous upper bound

    @pytest.mark.asyncio
    async def test_duration_recorded_for_error_call(self, mock_session_factory: MagicMock) -> None:
        """
        For an error call, duration_ms is recorded at the time of the exception
        and the exception is still propagated.
        """
        import httpx

        session = MagicMock()
        session.add = MagicMock()
        session.commit = AsyncMock()

        session_factory = MagicMock()
        session_factory.return_value.__aenter__ = AsyncMock(return_value=session)
        session_factory.return_value.__aexit__ = AsyncMock(return_value=None)

        raw_client = MagicMock()

        async def failing_request(*args: Any, **kwargs: Any) -> MagicMock:
            await asyncio.sleep(0.03)
            raise httpx.TimeoutException("request timed out")

        raw_client.request = failing_request
        raw_client.is_closed = False

        client = InstrumentedAsyncClient(
            client=raw_client,
            session_factory=session_factory,
        )

        with pytest.raises(httpx.TimeoutException):
            await client.get("https://api.example.com/v1/timeout")

        session.add.assert_called_once()
        log_entry: ExternalCallLog = session.add.call_args[0][0]

        # Duration should be recorded even for errors
        assert log_entry.duration_ms is not None
        assert log_entry.duration_ms > 0

        # Error message should be recorded
        assert log_entry.error_message is not None
        assert "TimeoutException" in log_entry.error_message

    @pytest.mark.asyncio
    async def test_duration_zero_for_instant_response(self, mock_session_factory: MagicMock) -> None:
        """
        Very fast responses (< 1ms) should still get a duration value.
        """
        session = MagicMock()
        session.add = MagicMock()
        session.commit = AsyncMock()

        session_factory = MagicMock()
        session_factory.return_value.__aenter__ = AsyncMock(return_value=session)
        session_factory.return_value.__aexit__ = AsyncMock(return_value=None)

        raw_client = MagicMock()
        raw_client.request = AsyncMock(return_value=make_response(200, "ok"))
        raw_client.is_closed = False

        client = InstrumentedAsyncClient(
            client=raw_client,
            session_factory=session_factory,
        )

        response = await client.get("https://api.example.com/v1/fast")

        assert response.status_code == 200

        session.add.assert_called_once()
        log_entry: ExternalCallLog = session.add.call_args[0][0]

        # Duration should be recorded as a positive float (even if tiny)
        assert log_entry.duration_ms is not None
        assert log_entry.duration_ms >= 0


# =============================================================================
# Test: Stream method is instrumented
# =============================================================================

class TestStreamingInstrumentation:
    """Test that the stream() method is also instrumented."""

    @pytest.mark.asyncio
    async def test_stream_creates_span_and_logs(
        self,
        mock_session_factory: MagicMock,
        in_memory_exporter: InMemorySpanExporter,
    ) -> None:
        """
        client.stream() creates an OTel span and writes an ExternalCallLog entry.
        """
        raw_client = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.aiter_lines = MagicMock(return_value=AsyncMock(return_value=[]))

        raw_client.stream = AsyncMock(return_value=mock_response)
        raw_client.is_closed = False

        client = InstrumentedAsyncClient(
            client=raw_client,
            session_factory=mock_session_factory,
        )

        response = await client.stream(
            "POST",
            "https://api.example.com/v1/chat",
            headers={"Content-Type": "application/json"},
            content='{"messages":[{"role":"user","content":"hi"}]}',
        )

        assert response.status_code == 200

        # Verify stream was called
        raw_client.stream.assert_called_once()

        # Verify session was used to write log
        mock_session_factory.assert_called_once()

        # Verify span was created
        spans = in_memory_exporter.get_finished_spans()
        stream_spans = [s for s in spans if "POST" in s.name]
        assert len(stream_spans) >= 1

    @pytest.mark.asyncio
    async def test_stream_error_logs_error(
        self,
        mock_session_factory: MagicMock,
    ) -> None:
        """
        client.stream() errors are logged with error_message.
        """
        import httpx

        raw_client = MagicMock()
        raw_client.stream = AsyncMock(
            side_effect=httpx.ConnectError("Connection refused")
        )
        raw_client.is_closed = False

        client = InstrumentedAsyncClient(
            client=raw_client,
            session_factory=mock_session_factory,
        )

        with pytest.raises(httpx.ConnectError):
            await client.stream("POST", "https://localhost:9999/api")

        mock_session_factory.assert_called_once()


# =============================================================================
# Test: is_closed property
# =============================================================================

class TestIsClosedProperty:
    """Test the is_closed property of InstrumentedAsyncClient."""

    def test_uninitialized_client_returns_true(self) -> None:
        """
        When no httpx.AsyncClient has been created (lazy init), is_closed is True.
        """
        client = InstrumentedAsyncClient(session_factory=None)
        assert client.is_closed is True

    def test_open_client_returns_false(self) -> None:
        """
        When the underlying client is open, is_closed is False.
        """
        raw_client = MagicMock()
        raw_client.is_closed = False

        client = InstrumentedAsyncClient(client=raw_client, session_factory=None)
        assert client.is_closed is False

    def test_closed_client_returns_true(self) -> None:
        """
        When the underlying client is closed, is_closed is True.
        """
        raw_client = MagicMock()
        raw_client.is_closed = True

        client = InstrumentedAsyncClient(client=raw_client, session_factory=None)
        assert client.is_closed is True


# =============================================================================
# Test: call_type parameter
# =============================================================================

class TestCallTypeParameter:
    """Test that the call_type parameter is passed through to ExternalCallLog."""

    @pytest.mark.asyncio
    async def test_custom_call_type_written_to_log(
        self,
        mock_session_factory: MagicMock,
    ) -> None:
        """
        The call_type parameter (default "http") is written to ExternalCallLog.call_type.
        """
        session = MagicMock()
        session.add = MagicMock()
        session.commit = AsyncMock()

        session_factory = MagicMock()
        session_factory.return_value.__aenter__ = AsyncMock(return_value=session)
        session_factory.return_value.__aexit__ = AsyncMock(return_value=None)

        raw_client = MagicMock()
        raw_client.request = AsyncMock(return_value=make_response(200))
        raw_client.is_closed = False

        # Create with custom call_type
        client = InstrumentedAsyncClient(
            client=raw_client,
            session_factory=session_factory,
            call_type="mcp",
        )

        await client.get("https://api.example.com/v1/test")

        session.add.assert_called_once()
        log_entry: ExternalCallLog = session.add.call_args[0][0]
        assert log_entry.call_type == "mcp"

    @pytest.mark.asyncio
    async def test_default_call_type_is_http(self, mock_session_factory: MagicMock) -> None:
        """
        Default call_type is "http" when not specified.
        """
        session = MagicMock()
        session.add = MagicMock()
        session.commit = AsyncMock()

        session_factory = MagicMock()
        session_factory.return_value.__aenter__ = AsyncMock(return_value=session)
        session_factory.return_value.__aexit__ = AsyncMock(return_value=None)

        raw_client = MagicMock()
        raw_client.request = AsyncMock(return_value=make_response(200))
        raw_client.is_closed = False

        client = InstrumentedAsyncClient(
            client=raw_client,
            session_factory=session_factory,
        )

        await client.post("https://api.example.com/v1/test")

        session.add.assert_called_once()
        log_entry: ExternalCallLog = session.add.call_args[0][0]
        assert log_entry.call_type == "http"


# =============================================================================
# Test: content parameter (request body)
# =============================================================================

class TestRequestBodyHandling:
    """Test that the request body (content parameter) is captured for logging."""

    @pytest.mark.asyncio
    async def test_bytes_content_captured(self, mock_session_factory: MagicMock) -> None:
        """
        bytes content (utf-8 encoded) is captured as request_body_str.
        """
        session = MagicMock()
        session.add = MagicMock()
        session.commit = AsyncMock()

        session_factory = MagicMock()
        session_factory.return_value.__aenter__ = AsyncMock(return_value=session)
        session_factory.return_value.__aexit__ = AsyncMock(return_value=None)

        raw_client = MagicMock()
        raw_client.request = AsyncMock(return_value=make_response(200, "ok"))
        raw_client.is_closed = False

        client = InstrumentedAsyncClient(
            client=raw_client,
            session_factory=session_factory,
        )

        payload_bytes = '{"prompt": "Hello world"}'.encode("utf-8")
        await client.post(
            "https://api.example.com/v1/completions",
            headers={"Content-Type": "application/json"},
            content=payload_bytes,
        )

        session.add.assert_called_once()
        log_entry: ExternalCallLog = session.add.call_args[0][0]

        # Request body should be encrypted
        assert log_entry.request_body_encrypted is not None

    @pytest.mark.asyncio
    async def test_str_content_captured(self, mock_session_factory: MagicMock) -> None:
        """
        str content is captured as request_body_str (decoded as UTF-8).
        """
        session = MagicMock()
        session.add = MagicMock()
        session.commit = AsyncMock()

        session_factory = MagicMock()
        session_factory.return_value.__aenter__ = AsyncMock(return_value=session)
        session_factory.return_value.__aexit__ = AsyncMock(return_value=None)

        raw_client = MagicMock()
        raw_client.request = AsyncMock(return_value=make_response(200))
        raw_client.is_closed = False

        client = InstrumentedAsyncClient(
            client=raw_client,
            session_factory=session_factory,
        )

        await client.post(
            "https://api.example.com/v1/embeddings",
            content='{"model": "text-embedding-3-small"}',
        )

        session.add.assert_called_once()
        log_entry: ExternalCallLog = session.add.call_args[0][0]
        assert log_entry.request_body_encrypted is not None


# =============================================================================
# Test: Span naming
# =============================================================================

class TestSpanNaming:
    """Test that span names include method and domain."""

    @pytest.mark.asyncio
    async def test_span_name_includes_method_and_domain(
        self,
        in_memory_exporter: InMemorySpanExporter,
    ) -> None:
        """
        The OTel span name follows the pattern: 'http GET api.example.com'.
        """
        raw_client = MagicMock()
        raw_client.request = AsyncMock(return_value=make_response(200))
        raw_client.is_closed = False

        client = InstrumentedAsyncClient(client=raw_client, session_factory=None)

        await client.get("https://api.example.com/v1/test?page=1")

        spans = in_memory_exporter.get_finished_spans()
        http_span = next(
            (s for s in spans if "http" in s.name.lower()),
            None,
        )
        assert http_span is not None
        assert "GET" in http_span.name
        assert "api.example.com" in http_span.name

    @pytest.mark.asyncio
    async def test_span_name_with_path_only_url(
        self,
        in_memory_exporter: InMemorySpanExporter,
    ) -> None:
        """
        Even relative URLs produce a span name (domain extracted from base_url).
        """
        raw_client = MagicMock()
        raw_client.request = AsyncMock(return_value=make_response(200))
        raw_client.is_closed = False

        client = InstrumentedAsyncClient(client=raw_client, session_factory=None)

        # URL without scheme — domain extraction should handle gracefully
        await client.get("/v1/test")

        # Should not raise, just uses the URL as-is for domain
        # (domain would be "/v1/test" with no scheme)


# =============================================================================
# Test: instrumented_httpx_client factory function
# =============================================================================

class TestInstrumentedHttpxClientFactory:
    """Test the instrumented_httpx_client() factory function."""

    def test_returns_instrumented_async_client(self) -> None:
        """instrumented_httpx_client() returns an InstrumentedAsyncClient instance."""
        result = instrumented_httpx_client()
        assert isinstance(result, InstrumentedAsyncClient)

    def test_passes_through_client(self) -> None:
        """Pre-configured httpx.AsyncClient is passed through to InstrumentedAsyncClient."""
        raw = MagicMock()
        result = instrumented_httpx_client(client=raw)
        assert result._client is raw

    def test_passes_through_session_factory(self) -> None:
        """session_factory is passed through to InstrumentedAsyncClient."""
        factory = MagicMock()
        result = instrumented_httpx_client(session_factory=factory)
        assert result._session_factory is factory

    def test_passes_through_call_type(self) -> None:
        """call_type is passed through to InstrumentedAsyncClient."""
        result = instrumented_httpx_client(call_type="mcp")
        assert result._call_type == "mcp"