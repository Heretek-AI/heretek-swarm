"""
Tests for the code_graph_query tool.

Per M-arch PR #9: verify the code-review-graph query tool returns
correct results for each action and handles missing/corrupt DBs
gracefully.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from heretek_swarm.tools.base import ToolContext, ToolStatus
from heretek_swarm.tools.code_graph_query import (
    CodeGraphQueryTool,
    _query_callers,
    _query_callees,
    _query_imports,
    _query_inheritance,
    _query_node,
    _search_by_name,
)


def _make_test_db(tmp_path: Path) -> Path:
    """Create a small SQLite DB matching the code-graph schema."""
    db = tmp_path / "graph.db"
    with sqlite3.connect(str(db)) as conn:
        conn.executescript(
            """
            CREATE TABLE nodes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                kind TEXT NOT NULL,
                name TEXT NOT NULL,
                qualified_name TEXT NOT NULL UNIQUE,
                file_path TEXT NOT NULL,
                line_start INTEGER,
                line_end INTEGER,
                language TEXT,
                parent_name TEXT,
                params TEXT,
                return_type TEXT,
                modifiers TEXT,
                is_test INTEGER DEFAULT 0,
                file_hash TEXT,
                extra TEXT DEFAULT '{}',
                updated_at REAL NOT NULL
            );
            CREATE TABLE edges (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                kind TEXT NOT NULL,
                source_qualified TEXT NOT NULL,
                target_qualified TEXT NOT NULL,
                file_path TEXT NOT NULL,
                line INTEGER DEFAULT 0,
                extra TEXT DEFAULT '{}',
                confidence REAL DEFAULT 1.0,
                confidence_tier TEXT DEFAULT 'EXTRACTED',
                updated_at REAL NOT NULL
            );
            """
        )
        # Insert nodes
        conn.executemany(
            """INSERT INTO nodes (kind, name, qualified_name, file_path, language, updated_at)
               VALUES (?, ?, ?, ?, ?, ?)""",
            [
                ("File", "rag_pipeline.py", "backend/rag/rag_pipeline.py",
                 "backend/rag/rag_pipeline.py", "python", 1.0),
                ("Class", "RAGPipeline", "backend.rag.rag_pipeline.RAGPipeline",
                 "backend/rag/rag_pipeline.py", "python", 1.0),
                ("Function", "build_rag_pipeline", "backend.rag.rag_pipeline.build_rag_pipeline",
                 "backend/rag/rag_pipeline.py", "python", 1.0),
                ("Function", "rag_query", "backend.rag.rag_pipeline.rag_query",
                 "backend/rag/rag_pipeline.py", "python", 1.0),
            ],
        )
        # Insert edges
        conn.executemany(
            """INSERT INTO edges (kind, source_qualified, target_qualified, file_path, updated_at)
               VALUES (?, ?, ?, ?, ?)""",
            [
                ("CALLS", "backend.rag.rag_pipeline.rag_query",
                 "backend.rag.rag_pipeline.build_rag_pipeline",
                 "backend/rag/rag_pipeline.py", 1.0),
                ("IMPORTS_FROM", "backend.rag.rag_pipeline",
                 "rag.types", "backend/rag/rag_pipeline.py", 1.0),
                ("INHERITS", "backend.rag.rag_pipeline.SpecialPipeline",
                 "backend.rag.rag_pipeline.RAGPipeline",
                 "backend/rag/rag_pipeline.py", 1.0),
            ],
        )
    return db


@pytest.fixture
def ctx() -> ToolContext:
    return ToolContext(agent_id="coder-1", session_id="s1")


class TestQueryNode:
    def test_exact_match(self, tmp_path: Path) -> None:
        """Fetch a node by exact qualified_name."""
        db = _make_test_db(tmp_path)
        result = _query_node("backend.rag.rag_pipeline.RAGPipeline", db)
        assert result["name"] == "RAGPipeline"
        assert result["kind"] == "Class"

    def test_no_match_returns_empty(self, tmp_path: Path) -> None:
        """Non-existent name returns empty dict."""
        db = _make_test_db(tmp_path)
        assert _query_node("nonexistent", db) == {}


class TestCallersCallees:
    def test_callers(self, tmp_path: Path) -> None:
        """Callers of build_rag_pipeline includes rag_query."""
        db = _make_test_db(tmp_path)
        callers = _query_callers(
            "backend.rag.rag_pipeline.build_rag_pipeline", db
        )
        names = {c["name"] for c in callers}
        assert "rag_query" in names

    def test_callees(self, tmp_path: Path) -> None:
        """Callees of rag_query includes build_rag_pipeline."""
        db = _make_test_db(tmp_path)
        callees = _query_callees("backend.rag.rag_pipeline.rag_query", db)
        names = {c["name"] for c in callees}
        assert "build_rag_pipeline" in names


class TestImports:
    def test_imports_for_file(self, tmp_path: Path) -> None:
        """Imports for rag_pipeline.py includes rag.types."""
        db = _make_test_db(tmp_path)
        imports = _query_imports("backend/rag/rag_pipeline.py", db)
        targets = {e["target_qualified"] for e in imports}
        assert "rag.types" in targets


class TestInheritance:
    def test_inheritance_edges(self, tmp_path: Path) -> None:
        """Inheritance edges are returned."""
        db = _make_test_db(tmp_path)
        bases = _query_inheritance("backend.rag.rag_pipeline.SpecialPipeline", db)
        targets = {e["target_qualified"] for e in bases}
        assert "backend.rag.rag_pipeline.RAGPipeline" in targets


class TestSearchByName:
    def test_search_finds_matches(self, tmp_path: Path) -> None:
        """Name search finds partial matches."""
        db = _make_test_db(tmp_path)
        results = _search_by_name("RAG", db, limit=10)
        names = {r["name"] for r in results}
        assert "RAGPipeline" in names
        assert "rag_query" in names

    def test_search_respects_limit(self, tmp_path: Path) -> None:
        """Search respects the limit parameter."""
        db = _make_test_db(tmp_path)
        results = _search_by_name("rag", db, limit=1)
        assert len(results) == 1


class TestCodeGraphQueryTool:
    @pytest.mark.asyncio
    async def test_node_action(self, tmp_path: Path, ctx) -> None:
        """execute(action='node') returns the matching node."""
        db = _make_test_db(tmp_path)
        tool = CodeGraphQueryTool(db_path=db)
        result = await tool.execute(
            ctx, action="node", qualified_name="backend.rag.rag_pipeline.RAGPipeline"
        )
        assert result.status == ToolStatus.SUCCESS
        assert result.output["name"] == "RAGPipeline"

    @pytest.mark.asyncio
    async def test_callers_action(self, tmp_path: Path, ctx) -> None:
        """execute(action='callers') returns callers."""
        db = _make_test_db(tmp_path)
        tool = CodeGraphQueryTool(db_path=db)
        result = await tool.execute(
            ctx,
            action="callers",
            qualified_name="backend.rag.rag_pipeline.build_rag_pipeline",
        )
        assert result.status == ToolStatus.SUCCESS
        names = {h["name"] for h in result.output["hits"]}
        assert "rag_query" in names

    @pytest.mark.asyncio
    async def test_search_action(self, tmp_path: Path, ctx) -> None:
        """execute(action='search') returns matching nodes."""
        db = _make_test_db(tmp_path)
        tool = CodeGraphQueryTool(db_path=db)
        result = await tool.execute(ctx, action="search", pattern="Pipeline")
        assert result.status == ToolStatus.SUCCESS
        assert result.output["hits"]

    @pytest.mark.asyncio
    async def test_imports_action(self, tmp_path: Path, ctx) -> None:
        """execute(action='imports') returns import edges."""
        db = _make_test_db(tmp_path)
        tool = CodeGraphQueryTool(db_path=db)
        result = await tool.execute(
            ctx, action="imports", file_path="backend/rag/rag_pipeline.py"
        )
        assert result.status == ToolStatus.SUCCESS
        assert result.output["hits"]

    @pytest.mark.asyncio
    async def test_unknown_action_returns_failed(
        self, tmp_path: Path, ctx
    ) -> None:
        """Unknown action returns ToolStatus.FAILED with an error."""
        db = _make_test_db(tmp_path)
        tool = CodeGraphQueryTool(db_path=db)
        result = await tool.execute(ctx, action="bogus")
        assert result.status == ToolStatus.FAILED
        assert "Unknown action" in (result.error or "")

    @pytest.mark.asyncio
    async def test_missing_db_returns_failed(
        self, tmp_path: Path, ctx
    ) -> None:
        """Missing DB returns ToolStatus.FAILED with a clear error."""
        missing = tmp_path / "nope.db"
        tool = CodeGraphQueryTool(db_path=missing)
        result = await tool.execute(ctx, action="search", pattern="anything")
        assert result.status == ToolStatus.FAILED
        assert "code-graph DB unavailable" in (result.error or "")
        assert "nope.db" in (result.error or "")

    @pytest.mark.asyncio
    async def test_corrupt_db_returns_failed(
        self, tmp_path: Path, ctx
    ) -> None:
        """Corrupt DB returns ToolStatus.FAILED."""
        bad = tmp_path / "bad.db"
        bad.write_text("not a sqlite db")
        tool = CodeGraphQueryTool(db_path=bad)
        result = await tool.execute(ctx, action="search", pattern="x")
        assert result.status == ToolStatus.FAILED


class TestCodeGraphQueryToolDefaults:
    def test_default_db_path(self) -> None:
        """The default DB path is .code-review-graph/graph.db."""
        tool = CodeGraphQueryTool()
        assert tool._db_path.name == "graph.db"
        assert ".code-review-graph" in str(tool._db_path)
