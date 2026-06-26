"""Tests for Mem0Backend."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from tier1.memory.mem0_store import Mem0Backend


def test_disabled_backend():
    backend = Mem0Backend(api_key=None)
    assert not backend._enabled


async def test_add_returns_none_when_disabled():
    backend = Mem0Backend(api_key=None)
    result = await backend.add("test", user_id="agent1")
    assert result is None


async def test_add_calls_client():
    backend = Mem0Backend(api_key="test-key")
    mock_client = MagicMock()
    mock_client.add = MagicMock(return_value={"id": "mem-123"})
    backend._client = mock_client
    result = await backend.add("test memory", user_id="agent1")
    mock_client.add.assert_called_once()
    assert result == "mem-123"


async def test_search_returns_empty_when_disabled():
    backend = Mem0Backend(api_key=None)
    result = await backend.search("query", user_id="agent1")
    assert result == []


async def test_delete_returns_false_when_disabled():
    backend = Mem0Backend(api_key=None)
    result = await backend.delete("mem-123")
    assert result is False
