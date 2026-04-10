"""Dual-tier memory system tests."""
import pytest
from heretek_swarm.memory.base import MemoryEntry, MemoryQuery
from heretek_swarm.memory import MemoryType, MemoryTier, DualTierMemorySystem
from heretek_swarm.memory.eliza_memory import ElizaMemoryEntry


class TestMemoryEntry:
    """Test memory entry model"""

    def test_create_memory_entry(self):
        """Test basic entry creation"""
        entry = MemoryEntry(
            content="Test memory content",
            metadata={"agent_id": "agent-1"}
        )

        assert entry.id is not None
        assert entry.metadata.get("agent_id") == "agent-1"
        assert entry.content == "Test memory content"
        assert entry.memory_type == MemoryType.EPISODIC
        assert entry.tier == MemoryTier.PERSISTENT
        assert entry.access_count == 0

    def test_entry_touch(self):
        """Test access tracking"""
        entry = MemoryEntry(content="Test")
        entry.touch()
        assert entry.access_count == 1
        assert entry.last_accessed_at is not None


class TestDualTierMemory:
    """Test dual-tier memory system"""

    def test_dual_tier_creation(self):
        """Test creating dual tier memory"""
        memory = DualTierMemorySystem()
        assert memory is not None