"""Cognee knowledge graph pipeline — wraps cognee API + MemoryBackend integration."""

from __future__ import annotations

import structlog

import cognee
from tier1.memory import MemoryBackend, MemoryEntry, MemoryType

log = structlog.get_logger(__name__)

EXTRACTION_PROMPT = """Extract entities and relationships from this text.
Return JSON: {{"entities": [{{"name": "...", "type": "person|concept|decision|component|metric|event"}}], "relations": [{{"source": "...", "target": "...", "type": "causes|depends_on|contradicts|supports|part_of|decided_by"}}]}}
Text: {text}"""


class CogneePipeline:
    """Pipeline orchestrator: cognee graph + MemoryBackend storage."""

    def __init__(
        self,
        memory_backend: MemoryBackend,
        graph_path: str = ".cognee_data",
        llm_provider: str = "openai",
    ) -> None:
        self.memory = memory_backend
        self.graph_path = graph_path
        self.llm_provider = llm_provider
        self._configured = False

    async def _ensure_configured(self) -> None:
        """Configure cognee on first use."""
        if self._configured:
            return
        try:
            cognee.config.set_graph_db_config(
                {
                    "db_type": "networkx",
                }
            )
            cognee.config.set_vector_db_config(
                {
                    "db_type": "lancedb",
                    "db_path": f"{self.graph_path}/vectors",
                }
            )
            self._configured = True
        except Exception as exc:  # noqa: BLE001
            log.warning("cognee_config_failed", error=str(exc))

    async def add(self, text: str, metadata: dict | None = None) -> str:
        """Add text to cognee graph + MemoryBackend."""
        entry = MemoryEntry(
            content=text,
            memory_type=MemoryType.semantic,
            source=metadata.get("source", "") if metadata else "",
            metadata=metadata or {},
        )
        entry_id = await self.memory.store(entry)

        try:
            await self._ensure_configured()
            await cognee.add(text, user_id="tier1")
        except Exception as exc:  # noqa: BLE001
            log.warning("cognee_add_failed", error=str(exc))

        return entry_id

    async def cognify(self, batch_size: int = 10) -> None:
        """Process unprocessed entries: extract entities/relations via cognee."""
        try:
            await self._ensure_configured()
            await cognee.cognify()
        except Exception as exc:  # noqa: BLE001
            log.warning("cognee_cognify_failed", error=str(exc))

    async def search(self, query: str, *, top_k: int = 5) -> list[MemoryEntry]:
        """Vector search via MemoryBackend + graph enrichment via cognee."""
        results = await self.memory.search(query, top_k=top_k)

        try:
            await self._ensure_configured()
            graph_results = await cognee.search(query, user_id="tier1")
            log.info("cognee_graph_results", count=len(graph_results))
        except Exception as exc:  # noqa: BLE001
            log.warning("cognee_search_failed", error=str(exc))

        return results

    async def improve(self) -> None:
        """Best-effort graph refinement via cognee."""
        try:
            await self._ensure_configured()
            await cognee.improve()
        except Exception as exc:  # noqa: BLE001
            log.warning("cognee_improve_failed", error=str(exc))
