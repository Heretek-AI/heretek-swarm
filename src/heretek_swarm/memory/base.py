import uuid, structlog
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple

_logger = structlog.get_logger("MemorySystem")

@dataclass
class MemoryEntry:
    id: str = ""
    content: Any = None
    embedding: Optional[List[float]] = None

@dataclass
class MemoryQuery:
    query_text: Optional[str] = None
    filters: Optional[Dict[str, Any]] = None
    limit: int = 10
    similarity_threshold: float = 0.7
    include_expired: bool = False

class MemorySystem(ABC):
    def __init__(self, name: Optional[str]) -> None:
        self.name = name or "MemorySystem"
        self._initialized = False

    @abstractmethod
    async def store(
        pass

    @abstractmethod
    async def query(self, query: MemoryQuery) -> List[MemoryEntry]:
        pass

    @abstractmethod
    async def delete(self, memory_id: str) -> bool:
        pass

    @abstractmethod
    async def close(self) -> None:
        pass

class EphemeralMemory(MemorySystem):
    def __init__(self, name: str, max_size: int, default_ttl: int) -> None:
        super().__init__(name)
        self.max_size = max_size
        self.default_ttl = default_ttl
        self._storage: Dict[str, MemoryEntry] = {}
        self._index: Dict[str, List[str]] = {}

    async def initialize(self) -> None:
        self._initialized = True
        _logger.info(f"[{self.name}] await self.initialize()
        _memory_id = str(uuid.uuid4())
        _now = datetime.now(timezone.utc)
        _ttl = ttl or self.default_ttl
        _expires_at = (_now + timedelta(seconds=_ttl)).isoformat()
        _entry = MemoryEntry(id=_memory_id, content=content, metadata=metadata or {}, created_at=_now.isoformat(), expires_at=_expires_at, lineage=lineage or [])
        if len(self._storage) >= self.max_size:
            await self._evict_oldest()
        self._storage[_memory_id] = _entry
        await self._update_indexes(_entry)
        _logger.debug(f"[{self.name}] Stored memory {_memory_id}")
        return _entry

    async def retrieve(self, memory_id: str) -> Optional[MemoryEntry]:
        entry = self._storage.get(memory_id)
        if entry:
            if self._is_expired(entry):
                await self.delete(memory_id)
                return None
        return entry

    async def query(self, query: MemoryQuery) -> List[MemoryEntry]:
        results = []
        for _entry in self._storage.values():
            if not query.include_expired and self._is_expired(_entry):
                continue
            if query.filters:
                if not self._matches_filters(_entry, query.filters):
                    continue
            if query.query_text:
                if not self._matches_text(_entry, query.query_text):
                    continue
            results.append(_entry)
            if len(results) >= query.limit:
                break
        return results

    async def delete(self, memory_id: str) -> bool:
        if memory_id not in self._storage:
            return False
        _entry = self._storage[memory_id]
        del self._storage[memory_id]
        await self._remove_from_indexes(_entry)
        _logger.debug(f"[{self.name}] Deleted memory {memory_id}")
        return True

    async def close(self) -> None:
        self._storage.clear()
        self._index.clear()
        self._initialized = False
        _logger.info(f"[{self.name}] Ephemeral memory closed")

    async def _evict_oldest(self) -> None:
        if not self._storage:
            return
        _oldest_id = min(self._storage.keys(), key=lambda k: self._storage[k].created_at)
        await self.delete(_oldest_id)

    def _is_expired(self, entry: MemoryEntry) -> bool:
        if not entry.expires_at:
            return False
        _expires_at = datetime.fromisoformat(entry.expires_at)
        return datetime.now(timezone.utc) > _expires_at

    def _matches_filters(self, entry: MemoryEntry, filters: Dict[str, Any]) -> bool:
        for _key, value in filters.items():
            _entry_value = entry.metadata.get(_key)
            if _entry_value != value:
                return False
        return True

    def _matches_text(self, entry: MemoryEntry, text: str) -> bool:
        _content_str = str(entry.content).lower()
        return text.lower() in _content_str

    async def _update_indexes(self, entry: MemoryEntry) -> None:
        _memory_type = entry.metadata.get("type", "default")
        if _memory_type not in self._index:
            self._index[_memory_type] = []
        self._index[_memory_type].append(entry.id)
        _agent_id = entry.metadata.get("agent_id")
        if _agent_id:
            _key = "agent:" + _agent_id
            if _key not in self._index:
                self._index[_key] = []
            self._index[_key].append(entry.id)

    async def _remove_from_indexes(self, entry: MemoryEntry) -> None:
        _memory_type = entry.metadata.get("type", "default")
        if _memory_type in self._index:
            try:
                self._index[_memory_type].remove(entry.id)
            except ValueError:
                pass
        _agent_id = entry.metadata.get("agent_id")
        if _agent_id:
            _key = "agent:" + _agent_id
            if _key in self._index:
                try:
                    self._index[_key].remove(entry.id)
                except ValueError:
                    pass

    def get_statistics(self) -> Dict[str, Any]:
        _expired_count = sum(1 for entry in self._storage.values() if self._is_expired(entry))
        return {"total_entries": len(self._storage), "expired_entries": _expired_count, "active_entries": len(self._storage) - _expired_count, "max_size": self.max_size, "utilization": len(self._storage) / self.max_size, "index_count": len(self._index)}



class PersistentMemory(MemorySystem):
    def __init__(self, name: str, connection_string: Optional[str]) -> None:
        super().__init__(name)
        self.connection_string = connection_string
        self._storage: Dict[str, MemoryEntry] = {}

    async def initialize(self) -> None:
        self._initialized = True
       ._initialized:
            await self.initialize()
        _memory_id = str(uuid.uuid4())
        _now = datetime.now(timezone.utc)
        _entry = MemoryEntry(id=_memory_id, content=content, metadata=metadata or {}, created_at=_now.isoformat(), expires_at=None, lineage=lineage or [])
        self._storage[_memory_id] = _entry
        _logger.debug(f"[{self.name}] Stored persistent memory {_memory_id}")
        return _entry

    async def retrieve(self, memory_id: str) -> Optional[MemoryEntry]:
        return self._storage.get(memory_id)

    async def query(self, query: MemoryQuery) -> List[MemoryEntry]:
        results = []
        for _entry in self._storage.values():
            if query.filters:
                if not self._matches_filters(_entry, query.filters):
                    continue
            results.append(_entry)
            if len(results) >= query.limit:
                break
        return results

    async def delete(self, memory_id: str) -> bool:
        if memory_id not in self._storage:
            return False
        del self._storage[memory_id]
        _logger.debug(f"[{self.name}] Deleted persistent memory {memory_id}")
        return True

    async def close(self) -> None:
        self._storage.clear()
        self._initialized = False
        _logger.info(f"[{self.name}] Persistent memory closed")

    def _matches_filters(self, entry: MemoryEntry, filters: Dict[str, Any]) -> bool:
        for _key, value in filters.items():
            _entry_value = entry.metadata.get(_key)
            if _entry_value != value:
                return False
        return True

    async def store_embedding(self, memory_id: str, embedding: List[float]) -> bool:
        if memory_id not in self._storage:
            return False
        self._storage[memory_id].embedding = embedding
        return True

    async def semantic_search(self, query_embedding: List[float], limit: int, threshold: float) -> List[Tuple[MemoryEntry, float]]:
        results = []
        for entry in self._storage.values():
            if entry.embedding:
                similarity = self._cosine_similarity(query_embedding, entry.embedding)
                if similarity >= threshold:
                    results.append((entry, similarity))
        results.sort(key=lambda x: x[1], reverse=True)
        return results[:limit]

    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        if len(vec1) != len(vec2):
            return 0.0
        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        norm1 = sum(a * a for a in vec1) ** 0.5
        norm2 = sum(b * b for b in vec2) ** 0.5
        if norm1 == 0 or norm2 == 0:
            return 0.0
        return dot_product / (norm1 * norm2)


class DualTierMemory:
    def __init__(self, ephemeral: Optional[EphemeralMemory] = None, persistent: Optional[PersistentMemory] = None) -> None:
        self.ephemeral = ephemeral or EphemeralMemory(name="default", max_size=1000, default_ttl=3600)
        self.persistent = persistent or PersistentMemory(name="default", connection_string=None)
        self._initialized = False

    async def initialize(self) -> None:
        await self.ephemeral.initialize()
        await self.persistent.initialize()
        self._initialized = True
        _logger.info("Dual-tier memory initialized")

    async if persistent or ttl is None:
            return await self.persistent.store(content, metadata, ttl, lineage)
        else:
            return await self.ephemeral.store(content, metadata, ttl, lineage)

    async def retrieve(self, memory_id: str) -> Optional[MemoryEntry]:
        entry = await self.ephemeral.retrieve(memory_id)
        if entry:
            return entry
        return await self.persistent.retrieve(memory_id)

    async def query(self, query_text: Optional[str] = None, filters: Optional[Dict[str, Any]] = None, limit: int = 10, include_persistent: bool = True) -> List[MemoryEntry]:
        mq = MemoryQuery(query_text=query_text, filters=filters, limit=limit)
        results = await self.ephemeral.query(mq)
        if include_persistent:
            persistent_results = await self.persistent.query(mq)
            results.extend(persistent_results)
        return results[:limit]

    async def close(self) -> None:
        await self.ephemeral.close()
        await self.persistent.close()
        self._initialized = False
        _logger.info("Dual-tier memory closed")

    def get_statistics(self) -> Dict[str, Any]:
        ephemeral_stats = self.ephemeral.get_statistics()
        persistent_stats = {"persistent_total": len(self.persistent._storage)}
        return {"ephemeral": ephemeral_stats, "persistent": persistent_stats, "combined_total": ephemeral_stats["total_entries"] + persistent_stats["persistent_total"]}
