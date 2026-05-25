"""Contract tests for event mesh delivery tier logging.

Verifies the 3-tier message delivery logging contract that is the
verification surface for Slice S02 success criteria:

  Tier 1: "sent via event mesh to {topic}"     (event mesh present)
  Tier 2: "delivered directly to topic subscribers"  (registry fallback)
  Tier 3: "Message {id} queued"                (last resort)

These tests pin the observable behaviour so future changes don't
silently break the delivery tier logic.
"""

from __future__ import annotations

import asyncio
import uuid
from unittest.mock import MagicMock, patch

import pytest
import structlog
from structlog.testing import capture_logs

pytestmark = [pytest.mark.unit]

from heretek_swarm.actors import AgentActor
from heretek_swarm.actors.base.core import ActorMessage
from heretek_swarm.actors.stubs import StubEventMesh


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_actor(
    agent_id: str = "test-agent",
    *,
    event_mesh: StubEventMesh | None = None,
) -> AgentActor:
    """Create a minimal AgentActor with optional event mesh injection."""
    actor = AgentActor(agent_id=agent_id, event_mesh=event_mesh)
    return actor


def _make_message(
    sender: str = "sender-1",
    topic: str = "test.topic",
    content: dict | None = None,
) -> ActorMessage:
    return ActorMessage(
        sender=sender,
        message_type="test_msg",
        content=content or {"key": "value"},
        timestamp="2025-01-01T00:00:00Z",
    )


# ---------------------------------------------------------------------------
# Tier 1: _send_via_event_mesh return-value contract
# ---------------------------------------------------------------------------


class TestSendViaEventMeshReturns:
    """Contract: _send_via_event_mesh returns True when event mesh
    is present and send_to_json succeeds; False when mesh is None."""

    @staticmethod
    @pytest.mark.asyncio
    async def test_returns_true_when_event_mesh_present() -> None:
        """_send_via_event_mesh returns True when event mesh is
        injected and send_to_json succeeds."""
        mesh = StubEventMesh()
        actor = _make_actor(event_mesh=mesh)
        msg = _make_message()

        result = await actor._send_via_event_mesh(
            topic="test.topic",
            message=msg,
            message_id="msg-1",
            message_type="test",
        )
        assert result is True

    @staticmethod
    @pytest.mark.asyncio
    async def test_returns_false_when_event_mesh_is_none() -> None:
        """_send_via_event_mesh returns False when _event_mesh is None
        (no fallback stub creates one)."""
        actor = _make_actor(event_mesh=None)
        # Override the default-stub fallback in core.py
        actor._event_mesh = None  # noqa: SLF001
        msg = _make_message()

        result = await actor._send_via_event_mesh(
            topic="test.topic",
            message=msg,
            message_id="msg-1",
            message_type="test",
        )
        assert result is False

    @staticmethod
    @pytest.mark.asyncio
    async def test_returns_false_when_event_mesh_sentinel_is_none() -> None:
        """_send_via_event_mesh returns False when get_state('_event_mesh')
        returns None (state-based injection path)."""
        # This tests the `self._event_mesh or self.get_state("_event_mesh")` path.
        # We explicitly set _event_mesh=None and make sure get_state returns None.
        actor = _make_actor(event_mesh=None)
        actor._event_mesh = None  # noqa: SLF001
        # get_state for _event_mesh also returns None since we never set it
        msg = _make_message()

        result = await actor._send_via_event_mesh(
            topic="test.topic",
            message=msg,
            message_id="msg-2",
            message_type="test",
        )
        assert result is False


# ---------------------------------------------------------------------------
# Tier 1: send() with event mesh — published message inspection
# ---------------------------------------------------------------------------


class TestSendViaEventMeshPublished:
    """Contract: send() with StubEventMesh injects the message into
    mesh._published via send_to_json."""

    @staticmethod
    @pytest.mark.asyncio
    async def test_send_publishes_to_stub_event_mesh() -> None:
        """When an event mesh is injected, send() calls
        event_mesh.send_to_json and the message appears in _published."""
        mesh = StubEventMesh()
        actor = _make_actor(event_mesh=mesh)

        await actor.send(
            topic="agent.comm.alpha",
            content={"task": "greet"},
            message_type="greeting",
        )

        assert len(mesh._published) == 1
        published = mesh._published[0]
        assert published["subject"] == "agent.comm.alpha"
        assert published["data"]["type"] == "greeting"
        assert published["data"]["from"] == "test-agent"
        assert published["data"]["content"] == {"task": "greet"}

    @staticmethod
    @pytest.mark.asyncio
    async def test_send_multiple_messages_all_published() -> None:
        """Multiple send() calls all appear in _published in order."""
        mesh = StubEventMesh()
        actor = _make_actor(event_mesh=mesh)

        await actor.send(topic="a", content={"n": 1}, message_type="t1")
        await actor.send(topic="b", content={"n": 2}, message_type="t2")
        await actor.send(topic="c", content={"n": 3}, message_type="t3")

        assert len(mesh._published) == 3
        subjects = [p["subject"] for p in mesh._published]
        assert subjects == ["a", "b", "c"]


# ---------------------------------------------------------------------------
# Tier 1: send() — structured log signal verification
# ---------------------------------------------------------------------------


class TestSendLogSignals:
    """Contract: send() emits the correct structured log signal per
    delivery tier."""

    @staticmethod
    @pytest.mark.asyncio
    async def test_send_with_event_mesh_logs_tier1_signal() -> None:
        """send() with event mesh logs 'sent via event mesh to {topic}'."""
        mesh = StubEventMesh()
        actor = _make_actor(event_mesh=mesh)

        with capture_logs() as cap:
            await actor.send(
                topic="comm.events",
                content={"x": 1},
                message_type="event",
            )

        tier1_logs = [
            e for e in cap
            if "sent via event mesh to" in str(e.get("event", ""))
        ]
        assert len(tier1_logs) == 1
        assert "sent via event mesh to comm.events" in tier1_logs[0]["event"]

    @staticmethod
    @pytest.mark.asyncio
    async def test_send_without_event_mesh_logs_tier2_or_tier3() -> None:
        """send() without event mesh falls to Tier 2 (direct delivery)
        or Tier 3 (queued) — verifying the log signal is emitted."""
        actor = _make_actor(event_mesh=None)
        # Force _event_mesh to None so the default stub fallback
        # does not provide an in-memory mesh.
        actor._event_mesh = None  # noqa: SLF001

        with capture_logs() as cap:
            await actor.send(
                topic="direct.test",
                content={"fallback": True},
                message_type="fallback_test",
            )

        # Should NOT contain tier 1 log
        tier1 = [e for e in cap if "sent via event mesh to" in str(e.get("event", ""))]
        assert len(tier1) == 0

        # Should contain either tier 2 direct delivery or tier 3 queued
        tier2 = [e for e in cap if "delivered directly" in str(e.get("event", ""))]
        tier3 = [e for e in cap if "queued" in str(e.get("event", ""))]
        assert len(tier2) + len(tier3) >= 1, (
            f"Expected tier 2 or tier 3 log signal, got: {cap}"
        )

    @staticmethod
    @pytest.mark.asyncio
    async def test_send_with_event_mesh_does_not_log_tier2() -> None:
        """When event mesh is present, only Tier 1 log appears —
        no 'delivered directly' fallback log."""
        mesh = StubEventMesh()
        actor = _make_actor(event_mesh=mesh)

        with capture_logs() as cap:
            await actor.send(
                topic="exclusive.t1",
                content={"only": "mesh"},
                message_type="t1_only",
            )

        tier2 = [e for e in cap if "delivered directly" in str(e.get("event", ""))]
        assert len(tier2) == 0


# ---------------------------------------------------------------------------
# broadcast() contract
# ---------------------------------------------------------------------------


class TestBroadcastContract:
    """Contract: broadcast() uses broadcast_json when event mesh is
    present."""

    @staticmethod
    @pytest.mark.asyncio
    async def test_broadcast_with_event_mesh_calls_broadcast_json() -> None:
        """broadcast() with StubEventMesh calls broadcast_json,
        storing a record with subject='__broadcast__'."""
        mesh = StubEventMesh()
        actor = _make_actor(event_mesh=mesh)

        await actor.broadcast(
            content={"announcement": "system_update"},
            message_type="system_announce",
        )

        assert len(mesh._published) == 1
        published = mesh._published[0]
        assert published["subject"] == "__broadcast__"
        assert published["data"]["type"] == "system_announce"
        assert published["data"]["from"] == "test-agent"
        assert published["data"]["content"] == {"announcement": "system_update"}

    @staticmethod
    @pytest.mark.asyncio
    async def test_broadcast_with_event_mesh_logs_signal() -> None:
        """broadcast() with event mesh logs 'Broadcast sent via event
        mesh' signal."""
        mesh = StubEventMesh()
        actor = _make_actor(event_mesh=mesh)

        with capture_logs() as cap:
            await actor.broadcast(
                content={"msg": "hello"},
                message_type="broadcast_msg",
            )

        broadcast_logs = [
            e for e in cap
            if "Broadcast sent via event mesh" in str(e.get("event", ""))
        ]
        assert len(broadcast_logs) >= 1

    @staticmethod
    @pytest.mark.asyncio
    async def test_broadcast_without_event_mesh_falls_back() -> None:
        """broadcast() without event mesh falls back to registry or
        topic-based delivery — does not crash."""
        actor = _make_actor(event_mesh=None)
        actor._event_mesh = None  # noqa: SLF001

        # Should not raise; may log registry fallback or topic broadcast
        await actor.broadcast(
            content={"fallback": True},
            message_type="fallback_bc",
        )


# ---------------------------------------------------------------------------
# _send_via_event_mesh exception handling
# ---------------------------------------------------------------------------


class TestSendViaEventMeshExceptionHandling:
    """Contract: _send_via_event_mesh returns False on error without
    propagating the exception."""

    @staticmethod
    @pytest.mark.asyncio
    async def test_returns_false_when_send_to_json_raises() -> None:
        """When send_to_json raises, _send_via_event_mesh returns False
        (so Tier 2/Tier 3 fallback engages)."""
        mesh = StubEventMesh()
        # Make send_to_json raise
        mesh.send_to_json = MagicMock(side_effect=RuntimeError("NATS down"))  # type: ignore[method-assign]
        actor = _make_actor(event_mesh=mesh)
        msg = _make_message()

        result = await actor._send_via_event_mesh(
            topic="broken.topic",
            message=msg,
            message_id="msg-exc",
            message_type="test",
        )
        assert result is False


# ---------------------------------------------------------------------------
# Message ID and metadata preservation
# ---------------------------------------------------------------------------


class TestMessageMetadataPreservation:
    """Contract: message metadata (correlation_id, reply_to, message_id)
    is preserved through the event mesh delivery path."""

    @staticmethod
    @pytest.mark.asyncio
    async def test_correlation_id_and_reply_to_preserved() -> None:
        """Correlation ID and reply_to fields survive the
        send_to_json serialisation round-trip."""
        mesh = StubEventMesh()
        actor = _make_actor(event_mesh=mesh)

        mid = await actor.send(
            topic="corr.test",
            content={"cmd": "fetch"},
            message_type="request",
            correlation_id="corr-abc-123",
            reply_to="reply.channel.xyz",
        )

        assert len(mesh._published) == 1
        data = mesh._published[0]["data"]
        assert data["correlation_id"] == "corr-abc-123"
        assert data["reply_to"] == "reply.channel.xyz"
        # The returned message_id should be a valid UUID
        assert uuid.UUID(mid)

    @staticmethod
    @pytest.mark.asyncio
    async def test_timestamp_preserved_in_published_data() -> None:
        """The ActorMessage timestamp is preserved in the published
        data payload."""
        mesh = StubEventMesh()
        actor = _make_actor(event_mesh=mesh)

        await actor.send(
            topic="ts.test",
            content={"a": 1},
            message_type="timestamp_test",
        )

        data = mesh._published[0]["data"]
        assert "timestamp" in data
        assert data["timestamp"] is not None
