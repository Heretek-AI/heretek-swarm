"""Cognee knowledge graph pipeline — Kùzu embedded graph + MemoryBackend integration.

This module replaces the earlier cognee + NetworkX implementation per
the approved 2026-06-28 Cognee -> Kuzu Rewrite design spec.
"""

from __future__ import annotations

import structlog
from typing import Any

from tier1.memory import MemoryBackend, MemoryEntry, MemoryType

log = structlog.get_logger(__name__)

EXTRACTION_PROMPT = """Extract entities and relationships from this text.
Return JSON: {{"entities": [{{"name": "...", "type": "person|concept|decision|component|metric|event"}}], "relations": [{{"source": "...", "target": "...", "type": "causes|depends_on|contradicts|supports|part_of|decided_by"}}]}}
Text: {text}"""

ENTITY_TYPES = {"person", "concept", "decision", "component", "metric", "event"}
RELATION_TYPES = {"causes", "depends_on", "contradicts", "supports", "part_of", "decided_by"}


def _open_kuzu_db(path: str):
    """Open a Kùzu database and return a ready-to-use Connection.

    Module-level so tests can patch it.
    """
    import kuzu

    db = kuzu.Database(path)
    return kuzu.Connection(db)


class CogneePipeline:
    """Pipeline orchestrator: Kùzu graph + MemoryBackend storage."""

    def __init__(
        self,
        memory_backend: MemoryBackend,
        graph_path: str = ".cognee_data",
        llm_provider: str = "minimax",
    ) -> None:
        self.memory = memory_backend
        self.graph_path = graph_path
        self.llm_provider = llm_provider
        self._conn: Any = None  # kuzu.Connection — typed as Any to avoid hard import

    def _ensure_graph(self) -> None:
        """Open the Kùzu database and create tables (idempotent)."""
        if self._conn is not None:
            return
        self._conn = _open_kuzu_db(self.graph_path)
        # DDL — kuzu raises if a table already exists, so wrap in try/except.
        ddl_statements = [
            (
                "CREATE NODE TABLE Entity("
                "id UUID, name STRING, type STRING, "
                "embedding FLOAT[1536], created_at TIMESTAMP, "
                "PRIMARY KEY(id))"
            ),
            (
                "CREATE NODE TABLE Document("
                "id UUID, content_hash STRING, processed BOOLEAN, "
                "created_at TIMESTAMP, PRIMARY KEY(id))"
            ),
            (
                "CREATE REL TABLE RELATES_TO("
                "FROM Entity TO Entity, "
                "relation_type STRING, weight FLOAT, created_at TIMESTAMP)"
            ),
            ("CREATE REL TABLE CONTAINS(FROM Document TO Entity)"),
        ]
        for stmt in ddl_statements:
            try:
                self._conn.execute(stmt)
            except Exception as exc:  # noqa: BLE001
                # Table already exists — expected on subsequent opens.
                log.debug("kuzu.ddl_skipped", statement=stmt[:40], error=str(exc))

    def _find_entities_for_entry(self, entry_id: str) -> list[str]:
        """Return entity names that mention the given memory entry's id."""
        self._ensure_graph()
        result = self._conn.execute(
            "MATCH (d:Document {id: $id})-[:CONTAINS]->(e:Entity) RETURN e.name AS name",
            {"id": entry_id},
        )
        names: list[str] = []
        while True:
            try:
                row = result.get_next()
            except StopIteration:
                break
            names.append(row["name"])
        return names

    def _traverse_graph(self, entity_names: list[str], hops: int = 2) -> list[str]:
        """Traverse RELATES_TO from the given entities up to `hops` deep."""
        self._ensure_graph()
        if not entity_names:
            return []
        result = self._conn.execute(
            "MATCH (e:Entity)-[r:RELATES_TO*1.." + str(hops) + "]->(n:Entity) "
            "WHERE e.name IN $names RETURN DISTINCT n.name AS name",
            {"names": entity_names},
        )
        names: list[str] = []
        while True:
            try:
                row = result.get_next()
            except StopIteration:
                break
            names.append(row["name"])
        return names

    async def add(self, text: str, metadata: dict | None = None) -> str:
        """Store raw text to MemoryBackend. Graph extraction is added in Task 2."""
        entry = MemoryEntry(
            content=text,
            memory_type=MemoryType.semantic,
            source="cognee",
            metadata=metadata or {},
        )
        return await self.memory.store(entry)

    async def cognify(self, batch_size: int = 10) -> int:
        """Process unprocessed entries. Stub in Task 1; full implementation in Task 3."""
        return 0

    async def search(self, query: str, *, top_k: int = 5) -> list[MemoryEntry]:
        """Vector search via MemoryBackend. Graph enrichment added in Task 3."""
        return await self.memory.search(query, top_k=top_k)

    async def improve(self) -> None:
        """Best-effort graph refinement: ensure schema exists. Failures logged."""
        try:
            self._ensure_graph()
        except Exception as exc:  # noqa: BLE001
            log.warning("cognee.improve_failed", error=str(exc), exc_info=True)
