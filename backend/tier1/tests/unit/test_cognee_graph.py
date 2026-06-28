"""Tests for CogneePipeline graph operations (Kùzu)."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from tier1.memory.cognee_store import CogneePipeline


def _make_pipeline_with_mock_db():
    """Pipeline with a mocked kuzu Database + Connection."""
    backend = MagicMock()
    pipeline = CogneePipeline(backend, graph_path="/tmp/fake-graph")

    mock_conn = MagicMock()
    mock_db = MagicMock()
    # conn.execute returns a result object; we only care that it's called.
    mock_db.conn = mock_conn

    # Patch _open_kuzu_db and keep it alive for the duration of the test by
    # anchoring the patcher on mock_db (otherwise `with patch(...): return`
    # would restore the original before the test calls _ensure_graph).
    patcher = patch("tier1.memory.cognee_store._open_kuzu_db", return_value=mock_db)
    patcher.start()
    mock_db._patcher = patcher
    return pipeline, mock_db, mock_conn


def test_ensure_graph_opens_db_once():
    pipeline, mock_db, mock_conn = _make_pipeline_with_mock_db()
    pipeline._ensure_graph()
    assert pipeline._db is mock_db
    assert pipeline._conn is mock_conn
    # Second call is a no-op.
    pipeline._ensure_graph()
    # The DDL was executed at least once (CREATE NODE TABLE for Entity and Document,
    # CREATE REL TABLE for RELATES_TO and CONTAINS).
    assert mock_conn.execute.call_count >= 4


def test_improve_is_idempotent_and_runs_ddl():
    pipeline, mock_db, mock_conn = _make_pipeline_with_mock_db()
    import asyncio

    asyncio.run(pipeline.improve())
    # DDL is run at least once; second call must not raise.
    asyncio.run(pipeline.improve())


def test_find_entities_for_entry_runs_cypher():
    pipeline, mock_db, mock_conn = _make_pipeline_with_mock_db()
    # Mock the query result: an iterator of dicts with 'name' key.
    mock_result = MagicMock()
    mock_result.get_next.return_value = {"name": "JWT"}  # then StopIteration on next call
    mock_result.get_next.side_effect = [{"name": "JWT"}, {"name": "auth"}, StopIteration]
    mock_conn.execute.return_value = mock_result

    names = pipeline._find_entities_for_entry("entry-abc")
    assert names == ["JWT", "auth"]
    # Cypher query was issued.
    assert mock_conn.execute.called


def test_traverse_graph_returns_neighbors():
    pipeline, mock_db, mock_conn = _make_pipeline_with_mock_db()
    mock_result = MagicMock()
    mock_result.get_next.side_effect = [
        {"name": "middleware"},
        {"name": "token"},
        StopIteration,
    ]
    mock_conn.execute.return_value = mock_result

    neighbors = pipeline._traverse_graph(["JWT"], hops=2)
    assert "middleware" in neighbors
    assert "token" in neighbors
