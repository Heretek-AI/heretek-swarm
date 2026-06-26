"""Tests for CogneePipeline."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from tier1.memory import MemoryBackend, MemoryEntry, MemoryType
from tier1.memory.cognee_store import CogneePipeline


@pytest.fixture()
def mock_memory():
    return MagicMock(spec=MemoryBackend)


@pytest.fixture()
def pipeline(mock_memory):
    return CogneePipeline(memory_backend=mock_memory, graph_path="/tmp/test_cognee")


async def test_add_stores_via_memory_backend(pipeline, mock_memory):
    mock_memory.store = AsyncMock(return_value="entry-id")
    with patch("tier1.memory.cognee_store.cognee") as mock_cognee:
        mock_cognee.add = AsyncMock()
        result = await pipeline.add("test content", metadata={"source": "test"})
        mock_memory.store.assert_called_once()
        assert result == "entry-id"


async def test_search_enriches_with_graph(pipeline, mock_memory):
    entry = MemoryEntry(content="test", memory_type=MemoryType.episodic, id="e1")
    mock_memory.search = AsyncMock(return_value=[entry])
    with patch("tier1.memory.cognee_store.cognee") as mock_cognee:
        mock_cognee.search = AsyncMock(return_value=[{"text": "related", "score": 0.9}])
        results = await pipeline.search("query", top_k=3)
        mock_memory.search.assert_called_once_with("query", top_k=3)
        assert len(results) >= 1


async def test_cognify_calls_cognee(pipeline):
    with patch("tier1.memory.cognee_store.cognee") as mock_cognee:
        mock_cognee.cognify = AsyncMock()
        await pipeline.cognify()
        mock_cognee.cognify.assert_called_once()


async def test_improve_calls_cognee(pipeline):
    with patch("tier1.memory.cognee_store.cognee") as mock_cognee:
        mock_cognee.improve = AsyncMock()
        await pipeline.improve()
        mock_cognee.improve.assert_called_once()


async def test_add_extracts_entities(pipeline, mock_memory):
    mock_memory.store = AsyncMock(return_value="entry-id")
    with patch("tier1.memory.cognee_store.cognee") as mock_cognee:
        mock_cognee.add = AsyncMock()
        result = await pipeline.add(
            "We decided to use JWT for authentication",
            metadata={"source": "deliberation"},
        )
        mock_cognee.add.assert_called_once()
        call_args = mock_cognee.add.call_args
        assert "JWT" in call_args[0][0] or "JWT" in str(call_args)


def test_extraction_prompt_format():
    from tier1.memory.cognee_store import EXTRACTION_PROMPT

    prompt = EXTRACTION_PROMPT.format(text="test content")
    assert "test content" in prompt
    assert "entities" in prompt
    assert "relations" in prompt
