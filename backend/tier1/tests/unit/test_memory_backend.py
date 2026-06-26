"""Tests for MemoryBackend facade."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from tier1.memory import MemoryBackend, MemoryEntry, MemoryType


@pytest.fixture()
def backend():
    qdrant = MagicMock()
    redis = MagicMock()
    postgres = MagicMock()
    return MemoryBackend(qdrant=qdrant, redis=redis, postgres=postgres)


async def test_store_writes_to_all_tiers(backend):
    entry = MemoryEntry(content="test", memory_type=MemoryType.episodic)
    backend.qdrant.store = AsyncMock()
    backend.redis.set = AsyncMock()
    backend.postgres.store = AsyncMock()
    result = await backend.store(entry)
    assert result == entry.id
    backend.qdrant.store.assert_called_once_with(entry)
    backend.redis.set.assert_called_once()
    backend.postgres.store.assert_called_once_with(entry)


async def test_store_survives_qdrant_failure(backend):
    entry = MemoryEntry(content="test", memory_type=MemoryType.episodic)
    backend.qdrant.store = AsyncMock(side_effect=Exception("qdrant down"))
    backend.redis.set = AsyncMock()
    backend.postgres.store = AsyncMock()
    result = await backend.store(entry)
    assert result == entry.id
    backend.postgres.store.assert_called_once()


async def test_search_calls_qdrant(backend):
    backend.qdrant.search = AsyncMock(return_value=[])
    results = await backend.search("query", top_k=3)
    backend.qdrant.search.assert_called_once_with("query", top_k=3)


async def test_get_history_calls_postgres(backend):
    backend.postgres.get_history = AsyncMock(return_value=[])
    results = await backend.get_history("did-1")
    backend.postgres.get_history.assert_called_once_with("did-1")


async def test_get_session_calls_redis(backend):
    backend.redis.get = AsyncMock(return_value=None)
    result = await backend.get_session("key")
    backend.redis.get.assert_called_once_with("key")
    assert result is None
