"""Tests for memory/base.py — MemoryEntry dataclass."""

from heretek_swarm.memory.base import MemoryEntry


class TestMemoryEntry:
    def test_create_entry(self):
        entry = MemoryEntry(content="test message", agent_id="alpha")
        assert entry.content == "test message"
        assert entry.agent_id == "alpha"
        assert entry.id is not None

    def test_entry_created_at(self):
        entry = MemoryEntry(content="x", agent_id="a")
        assert entry.created_at is not None

    def test_entry_with_metadata(self):
        entry = MemoryEntry(content="data", agent_id="beta", metadata={"key": "value"})
        assert entry.metadata["key"] == "value"

    def test_entry_empty_content(self):
        entry = MemoryEntry(content="", agent_id="gamma")
        assert entry.content == ""

    def test_entry_default_content_type(self):
        entry = MemoryEntry(content="plain text", agent_id="delta")
        assert entry.content_type == "text/plain"

    def test_entry_auto_id_unique(self):
        e1 = MemoryEntry(content="a", agent_id="1")
        e2 = MemoryEntry(content="b", agent_id="2")
        assert e1.id != e2.id

    def test_entry_lineage_default(self):
        entry = MemoryEntry(content="x", agent_id="3")
        assert entry.lineage == []

    def test_entry_access_count_default(self):
        entry = MemoryEntry(content="y", agent_id="4")
        assert entry.access_count == 0