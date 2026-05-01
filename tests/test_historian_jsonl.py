"""Tests for ``HistorianAgent`` JSONL event log.

Covers five scenarios:

1. ``log_event()`` writes a valid JSON line to the configured path.
2. JSONL schema: all 5 fields present with correct types.
3. Multiple events append (not overwrite).
4. Writer drains queue on cleanup (last events are flushed).
5. Message handler responds with event_id.
"""

from __future__ import annotations

import asyncio
import json
import os
from pathlib import Path
from typing import Any

import pytest

from heretek_swarm.actors.historian import _HISTORIAN_FILE, HistorianAgent


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def tmp_jsonl_path(tmp_path: Path) -> Path:
    """Return a temporary path to use as the JSONL file so tests never
    touch the real ``.gsd/historian.jsonl``."""
    return tmp_path / "test_historian.jsonl"


@pytest.fixture
async def historian(tmp_jsonl_path: Path) -> HistorianAgent:
    """Build a ``HistorianAgent`` with a patched ``_HISTORIAN_FILE``
    constant and an ``initialize()`` that writes to the temp path."""
    from heretek_swarm.actors.historian import _HISTORIAN_FILE as _orig_file

    # Monkey-patch the module constant
    import heretek_swarm.actors.historian as _h_mod

    _h_mod._HISTORIAN_FILE = tmp_jsonl_path

    agent = HistorianAgent()
    await agent.initialize()

    yield agent

    # Cleanup
    if agent._writer_task is not None and not agent._writer_task.done():
        await agent._jsonl_queue.join()
        agent._writer_task.cancel()
        try:
            await agent._writer_task
        except asyncio.CancelledError:
            pass

    # Restore the original constant
    _h_mod._HISTORIAN_FILE = _orig_file


def _read_lines(path: Path) -> list[dict[str, Any]]:
    """Read and parse all JSON lines from *path*."""
    if not path.exists():
        return []
    raw = path.read_text(encoding="utf-8").strip()
    if not raw:
        return []
    return [json.loads(line) for line in raw.splitlines()]


# =========================================================================
# Contract 1 — A single event writes a valid JSON line
# =========================================================================


class TestSingleEvent:
    """``log_event()`` writes one valid JSON line to file."""

    @staticmethod
    async def test_writes_valid_json_line(historian: HistorianAgent, tmp_jsonl_path: Path) -> None:
        event_id = await historian.log_event(
            event_type="test_event",
            agent_id="alpha",
            payload={"key": "value"},
        )

        # Give the writer time to drain the queue
        await historian._jsonl_queue.join()

        lines = _read_lines(tmp_jsonl_path)
        assert len(lines) == 1, "expected exactly one JSON line"

        record = lines[0]
        assert record["event_id"] == event_id
        assert record["type"] == "test_event"
        assert record["agent_id"] == "alpha"
        assert record["payload"] == {"key": "value"}


# =========================================================================
# Contract 2 — JSONL schema: all 5 fields with correct types
# =========================================================================


class TestSchema:
    """Every event record contains the 5 required fields with the correct
    types."""

    @staticmethod
    async def test_all_schema_fields_present(historian: HistorianAgent, tmp_jsonl_path: Path) -> None:
        await historian.log_event(
            event_type="schema_check",
            agent_id="bravo",
            payload={"n": 42},
        )
        await historian._jsonl_queue.join()

        record = _read_lines(tmp_jsonl_path)[0]

        # Five top-level keys
        assert set(record) == {"event_id", "type", "timestamp", "agent_id", "payload"}

        # Type checks
        assert isinstance(record["event_id"], str)
        assert len(record["event_id"]) == 32  # uuid4().hex
        assert isinstance(record["type"], str)
        assert isinstance(record["timestamp"], str)
        # ISO-8601 timestamp should contain 'T' and 'Z' or '+'
        assert "T" in record["timestamp"]
        assert isinstance(record["agent_id"], str)
        assert isinstance(record["payload"], dict)
        assert record["payload"] == {"n": 42}


# =========================================================================
# Contract 3 — Multiple events append (not overwrite)
# =========================================================================


class TestAppend:
    """Multiple ``log_event()`` calls produce multiple lines (append)."""

    @staticmethod
    async def test_events_append_not_overwrite(historian: HistorianAgent, tmp_jsonl_path: Path) -> None:
        n_events = 5
        for i in range(n_events):
            await historian.log_event(
                event_type="append_test",
                agent_id="charlie",
                payload={"index": i},
            )
        await historian._jsonl_queue.join()

        lines = _read_lines(tmp_jsonl_path)
        assert len(lines) == n_events

        # Verify each event is distinct
        payloads = [r["payload"]["index"] for r in lines]
        assert payloads == list(range(n_events))


# =========================================================================
# Contract 4 — Writer drains the queue on cleanup
# =========================================================================


class TestCleanupDrain:
    """``cleanup()`` flushes pending events before finishing."""

    @staticmethod
    async def test_cleanup_drains_queue(tmp_jsonl_path: Path) -> None:
        # Use a *separate* agent so cleanup is the only flush path
        import heretek_swarm.actors.historian as _h_mod

        original = _h_mod._HISTORIAN_FILE
        _h_mod._HISTORIAN_FILE = tmp_jsonl_path

        agent = HistorianAgent()
        await agent.initialize()

        # Enqueue without waiting
        await agent.log_event(
            event_type="cleanup_test",
            agent_id="delta",
            payload={"flush": True},
        )

        # Do NOT await the queue — clean up should drain it
        await agent.cleanup()

        _h_mod._HISTORIAN_FILE = original

        lines = _read_lines(tmp_jsonl_path)
        assert len(lines) == 1, "cleanup should have flushed the pending event"


# =========================================================================
# Contract 5 — Message handler responds with event_id
# =========================================================================


class TestMessageHandler:
    """The ``"log_event"`` handler sends back an ``event_id``."""

    @staticmethod
    async def test_handler_responds_with_event_id(
        historian: HistorianAgent,
    ) -> None:
        from heretek_swarm.actors.base import ActorMessage
        from datetime import UTC, datetime

        msg = ActorMessage(
            sender="test-sender",
            message_type="log_event",
            content={
                "event_type": "handler_test",
                "agent_id": "echo",
                "payload": {"msg": "hello"},
                "reply_to": "test-replies",
            },
            timestamp=datetime.now(UTC).isoformat(),
            correlation_id="corr-001",
        )

        # Intercept the send() call
        sent: list[dict] = []
        original_send = historian.send

        async def _capture_send(topic, content, **kw):
            sent.append({"topic": topic, "content": content})
            return "captured-msg-id"

        historian.send = _capture_send  # type: ignore[method-assign]

        await historian._handle_log_event(msg)

        assert len(sent) == 1
        response = sent[0]
        assert response["topic"] == "test-replies"
        assert response["content"]["message_type"] == "log_event_response"
        assert isinstance(response["content"]["event_id"], str)
        assert len(response["content"]["event_id"]) == 32  # uuid4().hex

        # Restore
        historian.send = original_send
