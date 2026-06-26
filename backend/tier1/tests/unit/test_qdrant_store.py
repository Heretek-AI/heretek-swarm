"""Tests for QdrantVectorStore."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from tier1.memory import MemoryEntry, MemoryType
from tier1.memory.qdrant_store import QdrantVectorStore


@pytest.fixture()
def store():
    return QdrantVectorStore(
        url="http://localhost:6333",
        collection="test_memory",
        embedding_model="test-model",
        embedding_dimensions=128,
    )


async def test_store_upserts_to_qdrant(store):
    entry = MemoryEntry(content="hello", memory_type=MemoryType.episodic)
    store._embed = AsyncMock(return_value=[0.1] * 128)
    store._upsert = AsyncMock()
    await store.store(entry)
    store._upsert.assert_called_once()
    assert entry.embedding == [0.1] * 128


async def test_search_embeds_and_queries(store):
    store._embed = AsyncMock(return_value=[0.1] * 128)
    store._query = AsyncMock(return_value=[])
    results = await store.search("test query", top_k=3)
    store._embed.assert_called_once_with("test query")
    store._query.assert_called_once_with([0.1] * 128, top_k=3)


async def test_delete_removes_by_id(store):
    store._delete = AsyncMock()
    await store.delete("test-id")
    store._delete.assert_called_once_with("test-id")


async def test_store_without_embedding(store):
    store._embed = AsyncMock(side_effect=Exception("embed failed"))
    store._upsert = AsyncMock()
    entry = MemoryEntry(content="test", memory_type=MemoryType.episodic)
    # Should not raise — graceful degradation
    await store.store(entry)
    assert entry.embedding is None
    store._upsert.assert_called_once()
