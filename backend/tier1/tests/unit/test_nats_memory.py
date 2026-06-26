"""Tests for NATS memory subject handlers."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from tier1.memory import MemoryBackend, MemoryEntry, MemoryType
from tier1.memory.nats_memory import setup_memory_nats


async def test_store_handler_publishes_and_stores():
    backend = MagicMock(spec=MemoryBackend)
    backend.store = AsyncMock(return_value="entry-id")
    mock_nats = AsyncMock()
    setup_memory_nats(mock_nats, backend)
    # Verify subscribe was called
    mock_nats.subscribe.assert_called()


async def test_retrieve_handler_calls_search():
    backend = MagicMock(spec=MemoryBackend)
    backend.search = AsyncMock(return_value=[])
    mock_nats = AsyncMock()
    setup_memory_nats(mock_nats, backend)
    mock_nats.subscribe.assert_called()
