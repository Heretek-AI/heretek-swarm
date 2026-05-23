"""Unit tests for ``StewardAgent.route_to_agent()`` and the ``route_task`` handler.

Tests two surfaces:
1. **TestRouteToAgent** — Verifies the public ``route_to_agent()`` dispatch
   method on ``StewardAgent``:
   - Successful dispatch: mock actor receives ``put_message`` with correct
     message type (``'route_task'``) and payload structure.
   - Missing actor: returns empty string (None-guard).
   - None registry: returns empty string (graceful degradation).

2. **TestRouteTaskHandler** — Verifies the default ``_handle_route_task``
   and ``_process_route_task`` methods on ``StewardAgent``:
   - Default ``_process_route_task`` returns ``{"status": "unhandled"}``.
   - ``_handle_route_task`` dispatches to ``_process_route_task`` correctly.
"""

from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch

from heretek_swarm.actors.base import ActorMessage
from heretek_swarm.actors.steward import StewardAgent

import pytest

pytestmark = [pytest.mark.unit]

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_mock_actor() -> MagicMock:
    """Build a ``MagicMock`` that looks like an ``AgentActor`` with an
    awaitable ``put_message`` method."""
    actor = MagicMock()
    actor.put_message = AsyncMock()
    return actor


# ---------------------------------------------------------------------------
# TestRouteToAgent
# ---------------------------------------------------------------------------


class TestRouteToAgent:
    """``StewardAgent.route_to_agent()`` dispatch behaviour."""

    # -- Happy path: successful dispatch --------------------------------

    @staticmethod
    async def test_successful_route_to_agent() -> None:
        """A call to ``route_to_agent`` with a valid target actor delivers
        a ``'route_task'`` message to that actor's mailbox."""
        steward = StewardAgent(agent_id="steward")
        target = _make_mock_actor()
        registry = {"coder": target}

        steward._get_actor_registry = MagicMock(return_value=registry)  # type: ignore[method-assign]

        message_id = await steward.route_to_agent(
            agent_name="coder",
            task_type="on_demand_analysis",
            task_data={"prompt": "hello"},
        )

        # A non-empty message ID was returned
        assert message_id, "Expected non-empty message ID on success"

        # put_message was called exactly once
        target.put_message.assert_awaited_once()

        # Inspect the ActorMessage passed to put_message
        sent_message: ActorMessage = target.put_message.call_args[0][0]
        assert sent_message.message_type == "route_task"

        # The payload wrapper has the standard envelope
        inner_content = sent_message.content
        assert inner_content["message_type"] == "route_task"

        payload = inner_content["content"]
        assert payload["target_agent"] == "coder"
        assert payload["task_type"] == "on_demand_analysis"
        assert payload["task_data"] == {"prompt": "hello"}
        assert payload["sender"] == "steward"
        assert "correlation_id" in payload
        assert "timestamp" in payload

    @staticmethod
    async def test_route_to_agent_accepts_correlation_id() -> None:
        """When ``correlation_id`` is provided, it propagates through the
        envelope and the ``send_to_actor`` call."""
        steward = StewardAgent(agent_id="steward")
        target = _make_mock_actor()
        registry = {"coder": target}

        steward._get_actor_registry = MagicMock(return_value=registry)  # type: ignore[method-assign]

        await steward.route_to_agent(
            agent_name="coder",
            task_type="review_code",
            task_data={},
            correlation_id="my-correlation-id",
        )

        sent_message: ActorMessage = target.put_message.call_args[0][0]
        payload = sent_message.content["content"]
        assert payload["correlation_id"] == "my-correlation-id"

    # -- None-guard: missing actor --------------------------------------

    @staticmethod
    async def test_missing_actor_returns_empty() -> None:
        """When the target actor is not in the registry, an empty string
        is returned (None-guard, not an exception)."""
        steward = StewardAgent(agent_id="steward")
        # Register a different actor so the registry exists but doesn't
        # contain our target
        registry = {"other_actor": _make_mock_actor()}

        steward._get_actor_registry = MagicMock(return_value=registry)  # type: ignore[method-assign]

        result = await steward.route_to_agent(
            agent_name="missing_actor",
            task_type="on_demand_analysis",
            task_data={},
        )

        assert result == ""

    @staticmethod
    async def test_none_registry_returns_empty() -> None:
        """When ``_get_actor_registry()`` returns ``None`` (supervisor not
        available), the method returns an empty string gracefully."""
        steward = StewardAgent(agent_id="steward")

        steward._get_actor_registry = MagicMock(return_value=None)  # type: ignore[method-assign]

        result = await steward.route_to_agent(
            agent_name="coder",
            task_type="on_demand_analysis",
            task_data={},
        )

        assert result == ""

    @staticmethod
    async def test_empty_registry_returns_empty() -> None:
        """When the registry is an empty dict, any target is reported
        as missing."""
        steward = StewardAgent(agent_id="steward")

        steward._get_actor_registry = MagicMock(return_value={})  # type: ignore[method-assign]

        result = await steward.route_to_agent(
            agent_name="coder",
            task_type="on_demand_analysis",
            task_data={},
        )

        assert result == ""


# ---------------------------------------------------------------------------
# TestRouteTaskHandler
# ---------------------------------------------------------------------------


class TestRouteTaskHandler:
    """Default ``_handle_route_task`` / ``_process_route_task`` behaviour."""

    @staticmethod
    async def test_default_process_returns_unhandled() -> None:
        """The base ``_process_route_task`` returns
        ``{"status": "unhandled"}`` when not overridden."""
        steward = StewardAgent(agent_id="steward")

        result = await steward._process_route_task(
            {"task_type": "unknown_task", "target_agent": "steward"}
        )

        assert result["status"] == "unhandled"
        assert result["task_type"] == "unknown_task"

    @staticmethod
    async def test_handle_route_task_invokes_process_route_task() -> None:
        """``_handle_route_task`` dispatches to ``_process_route_task``
        with the inner payload."""
        steward = StewardAgent(agent_id="steward")
        payload = {
            "target_agent": "steward",
            "task_type": "on_demand_analysis",
            "task_data": {"prompt": "hello"},
            "correlation_id": "test-cid",
        }
        message = ActorMessage(
            sender="sender-agent",
            message_type="route_task",
            content={
                "message_type": "route_task",
                "content": payload,
                "sender": "sender-agent",
            },
            timestamp=datetime.now(UTC).isoformat(),
            correlation_id="test-cid",
        )

        with patch.object(
            steward, "_process_route_task", wraps=steward._process_route_task
        ) as mock_process:
            await steward._handle_route_task(message)
            mock_process.assert_awaited_once_with(payload)
