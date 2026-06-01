"""
Tests for CogneeMemoryReader — read-only Cognee client with graceful fallback.

Per M-arch PR #2: verify the reader's contract (never raises; empty list on
failure) so the Historian can safely use it as a supplemental source.
"""

from __future__ import annotations

import json
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import httpx
import pytest

from heretek_swarm.memory.cognee_reader import CogneeMemoryReader


def _mock_response(status_code: int, payload: Any | None = None) -> httpx.Response:
    """Build an httpx.Response with the given status code and JSON body."""
    request = httpx.Request("POST", "http://test/api/v1/search")
    if payload is None:
        return httpx.Response(status_code, request=request)
    return httpx.Response(status_code, json=payload, request=request)


class TestCogneeMemoryReader:
    """Behavioral tests for the CogneeMemoryReader class."""

    def test_default_disabled(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Reader defaults to disabled (opt-in via env)."""
        monkeypatch.delenv("COGNEE_ENABLED", raising=False)
        reader = CogneeMemoryReader()
        assert reader.enabled is False

    def test_enabled_via_env(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Reader can be enabled via COGNEE_ENABLED=true."""
        monkeypatch.setenv("COGNEE_ENABLED", "true")
        reader = CogneeMemoryReader()
        assert reader.enabled is True

    def test_api_url_default(self) -> None:
        """Default API URL is the in-network Cognee service."""
        reader = CogneeMemoryReader(enabled=True)
        assert reader.api_url == "http://cognee:8000"

    def test_api_url_trailing_slash_stripped(self) -> None:
        """Trailing slashes are stripped from the API URL."""
        reader = CogneeMemoryReader(api_url="http://cognee:8000/", enabled=True)
        assert reader.api_url == "http://cognee:8000"

    @pytest.mark.asyncio
    async def test_read_returns_empty_when_disabled(self) -> None:
        """Disabled reader returns [] without making any HTTP calls."""
        reader = CogneeMemoryReader(enabled=False)
        result = await reader.read("test query")
        assert result == []

    @pytest.mark.asyncio
    async def test_read_returns_empty_on_http_error(self) -> None:
        """HTTPError from Cognee is swallowed and returns []."""
        mock_client = AsyncMock(spec=httpx.AsyncClient)
        mock_client.post.side_effect = httpx.HTTPError("connection refused")
        reader = CogneeMemoryReader(enabled=True, client=mock_client)
        result = await reader.read("test query")
        assert result == []
        mock_client.post.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_read_returns_empty_on_timeout(self) -> None:
        """TimeoutException from Cognee is swallowed and returns []."""
        mock_client = AsyncMock(spec=httpx.AsyncClient)
        mock_client.post.side_effect = httpx.TimeoutException("timed out")
        reader = CogneeMemoryReader(enabled=True, client=mock_client)
        result = await reader.read("test query")
        assert result == []

    @pytest.mark.asyncio
    async def test_read_returns_empty_on_5xx(self) -> None:
        """5xx response is treated as a failure and returns []."""
        mock_client = AsyncMock(spec=httpx.AsyncClient)
        mock_client.post.return_value = _mock_response(500)
        reader = CogneeMemoryReader(enabled=True, client=mock_client)
        result = await reader.read("test query")
        assert result == []

    @pytest.mark.asyncio
    async def test_read_returns_results_on_success(self) -> None:
        """Successful 200 response with results is returned as a list of dicts."""
        mock_client = AsyncMock(spec=httpx.AsyncClient)
        mock_client.post.return_value = _mock_response(
            200,
            {
                "results": [
                    {
                        "content": "Some context",
                        "score": 0.92,
                        "dataset": "default",
                        "metadata": {"source": "doc1"},
                    }
                ]
            },
        )
        reader = CogneeMemoryReader(enabled=True, client=mock_client)
        result = await reader.read("test query", top_k=5)
        assert len(result) == 1
        assert result[0]["content"] == "Some context"
        assert result[0]["score"] == 0.92
        # Verify the payload was sent correctly
        call_kwargs = mock_client.post.call_args.kwargs
        assert call_kwargs["json"]["query"] == "test query"
        assert call_kwargs["json"]["top_k"] == 5

    @pytest.mark.asyncio
    async def test_read_includes_dataset_in_payload(self) -> None:
        """Dataset name is included in the search payload when provided."""
        mock_client = AsyncMock(spec=httpx.AsyncClient)
        mock_client.post.return_value = _mock_response(200, {"results": []})
        reader = CogneeMemoryReader(enabled=True, client=mock_client)
        await reader.read("test query", dataset="agents")
        payload = mock_client.post.call_args.kwargs["json"]
        assert payload["dataset"] == "agents"

    @pytest.mark.asyncio
    async def test_read_handles_unexpected_json_shape(self) -> None:
        """Unexpected JSON shape (e.g., list instead of dict) is handled gracefully."""
        mock_client = AsyncMock(spec=httpx.AsyncClient)
        mock_client.post.return_value = _mock_response(200, [])  # not a dict
        reader = CogneeMemoryReader(enabled=True, client=mock_client)
        result = await reader.read("test query")
        assert result == []

    @pytest.mark.asyncio
    async def test_health_returns_false_when_disabled(self) -> None:
        """Health check returns False when reader is disabled."""
        reader = CogneeMemoryReader(enabled=False)
        assert await reader.health() is False

    @pytest.mark.asyncio
    async def test_health_returns_true_on_200(self) -> None:
        """Health check returns True when Cognee returns 200."""
        mock_client = AsyncMock(spec=httpx.AsyncClient)
        mock_client.get.return_value = _mock_response(200)
        reader = CogneeMemoryReader(enabled=True, client=mock_client)
        assert await reader.health() is True

    @pytest.mark.asyncio
    async def test_health_returns_false_on_error(self) -> None:
        """Health check returns False on any exception."""
        mock_client = AsyncMock(spec=httpx.AsyncClient)
        mock_client.get.side_effect = httpx.HTTPError("nope")
        reader = CogneeMemoryReader(enabled=True, client=mock_client)
        assert await reader.health() is False

    @pytest.mark.asyncio
    async def test_close_closes_owned_client(self) -> None:
        """``close()`` closes the client only if we own it (not injected)."""
        mock_client = AsyncMock(spec=httpx.AsyncClient)
        mock_client.is_closed = False
        reader = CogneeMemoryReader(enabled=True, client=mock_client)
        await reader.close()
        # Injected client — we should NOT close it
        mock_client.aclose.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_repr_includes_key_state(self) -> None:
        """__repr__ exposes api_url and enabled for debugging."""
        reader = CogneeMemoryReader(api_url="http://x:1234", enabled=True)
        r = repr(reader)
        assert "http://x:1234" in r
        assert "enabled=True" in r
