"""Unit tests for Triad agent analysis — ``_perform_analysis`` fallback and
``_handle_deliberation_request`` result storage.

Each agent in the Triad (Alpha, Beta, Charlie) inherits the same template
method ``_perform_analysis`` from ``TriadAgent``, but they override
``_get_analysis_prompt`` and ``_get_analysis_extras`` to inject
agent-specific keys into the result dict.  When no ``swarms_agent`` is
configured (which is the common unit-test scenario), the method returns a
fallback dict.

The ``_handle_deliberation_request`` handler on each agent calls
``_perform_analysis`` then stores the result in an agent-specific data
structure — ``analysis_history`` (Alpha, list),
``_analyses`` (Beta, dict keyed by ``deliberation_id``), or
``_challenges`` (Charlie, dict keyed by ``session_id``).

All handlers also call ``send()``, which is fire-and-forget in this context;
we mock it to avoid the event-mesh / actor-registry routing.
"""

from __future__ import annotations

from unittest.mock import AsyncMock

from heretek_swarm.actors.base.core import ActorMessage
from heretek_swarm.actors.triad.agent import AlphaAgent, BetaAgent, CharlieAgent

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_deliberation_message(
    deliberation_id: str | None = "delib-001",
    topic: str | None = "test-topic",
    agent_id: str = "steward-1",
) -> ActorMessage:
    """Build a ``deliberation_request``-type ``ActorMessage``."""
    return ActorMessage(
        sender=agent_id,
        message_type="deliberation_request",
        content={
            "deliberation_id": deliberation_id,
            "topic": topic,
        },
        timestamp="2026-04-29T22:00:00+00:00",
    )


def _make_alpha(agent_id: str = "test-alpha") -> AlphaAgent:
    """Create an ``AlphaAgent`` without a ``swarms_agent`` (fallback path)."""
    agent = AlphaAgent(agent_id=agent_id)
    agent.send = AsyncMock()  # fire-and-forget, we don't assert on send content
    return agent


def _make_beta(agent_id: str = "test-beta") -> BetaAgent:
    """Create a ``BetaAgent`` without a ``swarms_agent`` (fallback path)."""
    agent = BetaAgent(agent_id=agent_id)
    agent.send = AsyncMock()
    return agent


def _make_charlie(agent_id: str = "test-charlie") -> CharlieAgent:
    """Create a ``CharlieAgent`` without a ``swarms_agent`` (fallback path)."""
    agent = CharlieAgent(agent_id=agent_id)
    agent.send = AsyncMock()
    return agent


# ===================================================================
# AlphaAgent
# ===================================================================


class TestAlphaPerformAnalysis:
    """``AlphaAgent._perform_analysis`` fallback behaviour."""

    @staticmethod
    async def test_returns_fallback_dict_with_expected_keys() -> None:
        """The fallback dict contains ``decision``, ``confidence``,
        ``reasoning``, and ``depth``."""
        agent = _make_alpha()
        result = await agent._perform_analysis("some problem")

        assert isinstance(result, dict)
        assert "decision" in result
        assert "confidence" in result
        assert "reasoning" in result
        assert "depth" in result

    @staticmethod
    async def test_decision_contains_agent_class_name() -> None:
        """The fallback ``decision`` string includes the lowercased class
        name (``alphaagent``)."""
        agent = _make_alpha()
        result = await agent._perform_analysis("x")

        assert result["decision"] == "alphaagent_analysis_complete"

    @staticmethod
    async def test_depth_reflects_analysis_depth() -> None:
        """``depth`` comes from ``AlphaAgent.analysis_depth`` (default
        ``"deep"``)."""
        agent = _make_alpha()
        result = await agent._perform_analysis("x")

        assert result["depth"] == "deep"

    @staticmethod
    async def test_custom_depth_is_used() -> None:
        """An ``AlphaAgent`` constructed with ``analysis_depth="shallow"``
        returns ``depth="shallow"`` in the fallback."""
        agent = _make_alpha()
        agent.analysis_depth = "shallow"
        result = await agent._perform_analysis("x")

        assert result["depth"] == "shallow"
        assert result["confidence"] == 0.7
        assert result["reasoning"] == "Fallback analysis"


class TestAlphaHandleDeliberationRequest:
    """``AlphaAgent._handle_deliberation_request`` storage behaviour."""

    @staticmethod
    async def test_send_was_called_once() -> None:
        """The fire-and-forget ``send`` is called exactly once with a
        ``vote_response`` message."""
        agent = _make_alpha()
        msg = _make_deliberation_message()

        await agent._handle_deliberation_request(msg)

        agent.send.assert_awaited_once()

    @staticmethod
    async def test_decision_count_incremented() -> None:
        """``decision_count`` is incremented after each deliberation
        request (``_handle_deliberation_request`` does not write to
        ``analysis_history`` — that happens in
        ``_handle_analysis_request``)."""
        agent = _make_alpha()
        assert agent.decision_count == 0

        msg = _make_deliberation_message()
        await agent._handle_deliberation_request(msg)

        assert agent.decision_count == 1


# ===================================================================
# BetaAgent
# ===================================================================


class TestBetaPerformAnalysis:
    """``BetaAgent._perform_analysis`` fallback behaviour."""

    @staticmethod
    async def test_returns_fallback_with_perspective_key() -> None:
        """The fallback dict contains ``perspective`` in addition to the
        standard keys."""
        agent = _make_beta()
        result = await agent._perform_analysis("some problem")

        assert "perspective" in result
        assert "decision" in result
        assert "confidence" in result
        assert result["perspective"] == "secondary"

    @staticmethod
    async def test_decision_contains_beta_class_name() -> None:
        agent = _make_beta()
        result = await agent._perform_analysis("x")

        assert result["decision"] == "betaagent_analysis_complete"


class TestBetaHandleDeliberationRequest:
    """``BetaAgent._handle_deliberation_request`` storage behaviour."""

    @staticmethod
    async def test_stores_result_in_analyses_dict() -> None:
        """The analysis is stored in ``_analyses`` dict keyed by
        ``deliberation_id``."""
        agent = _make_beta()
        msg = _make_deliberation_message(deliberation_id="d-002", topic="topic-y")

        await agent._handle_deliberation_request(msg)

        assert "d-002" in agent._analyses
        entry = agent._analyses["d-002"]
        assert entry["analysis"]["decision"] == "betaagent_analysis_complete"
        assert "timestamp" in entry

    @staticmethod
    async def test_send_was_called_once() -> None:
        agent = _make_beta()
        msg = _make_deliberation_message()

        await agent._handle_deliberation_request(msg)

        agent.send.assert_awaited_once()


# ===================================================================
# CharlieAgent
# ===================================================================


class TestCharliePerformAnalysis:
    """``CharlieAgent._perform_analysis`` fallback behaviour."""

    @staticmethod
    async def test_returns_fallback_with_challenges_key() -> None:
        """The fallback dict contains ``challenges`` in addition to the
        standard keys."""
        agent = _make_charlie()
        result = await agent._perform_analysis("some problem")

        assert "challenges" in result
        assert "decision" in result
        assert "confidence" in result
        assert isinstance(result["challenges"], list)

    @staticmethod
    async def test_decision_contains_charlie_class_name() -> None:
        agent = _make_charlie()
        result = await agent._perform_analysis("x")

        assert result["decision"] == "charlieagent_analysis_complete"


class TestCharlieHandleDeliberationRequest:
    """``CharlieAgent._handle_deliberation_request`` storage behaviour."""

    @staticmethod
    async def test_stores_result_in_challenges_dict() -> None:
        """The analysis is stored in ``_challenges`` dict keyed by
        ``session_id`` (derived from ``deliberation_id``)."""
        agent = _make_charlie()
        msg = _make_deliberation_message(deliberation_id="d-003", topic="topic-z")

        await agent._handle_deliberation_request(msg)

        assert "d-003" in agent._challenges
        entry = agent._challenges["d-003"]
        assert entry["analysis"]["decision"] == "charlieagent_analysis_complete"
        assert "challenges" in entry

    @staticmethod
    async def test_send_was_called_once() -> None:
        agent = _make_charlie()
        msg = _make_deliberation_message()

        await agent._handle_deliberation_request(msg)

        agent.send.assert_awaited_once()
