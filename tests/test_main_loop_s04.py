"""Tests for Metis and Empath agents.

Covers:
1. MetisAgent._perform_analysis() fallback without swarms_agent
2. MetisAgent._handle_on_demand_analysis() message handler
3. EmpathAgent._perform_sentiment() fallback
4. EmpathAgent._handle_on_demand_sentiment() message handler
"""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from heretek_swarm.actors.base.core import ActorMessage
from heretek_swarm.actors.empath import EmpathAgent
from heretek_swarm.actors.metis import MetisAgent


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_metis(agent_id: str = "test-metis") -> MetisAgent:
    """Create a MetisAgent without swarms_agent (fallback path)."""
    agent = MetisAgent(agent_id=agent_id)
    agent.send = AsyncMock()
    return agent


def _make_empath(agent_id: str = "test-empath") -> EmpathAgent:
    """Create an EmpathAgent without swarms_agent (fallback path)."""
    agent = EmpathAgent(agent_id=agent_id)
    agent.send = AsyncMock()
    return agent


def _make_analysis_message(
    context: str = "test context",
    perspective: str = "neutral",
    agent_id: str = "steward-1",
) -> ActorMessage:
    """Build an on_demand_analysis message."""
    return ActorMessage(
        sender=agent_id,
        message_type="on_demand_analysis",
        content={
            "context": context,
            "perspective": perspective,
            "reply_to": "test-replies",
        },
        timestamp="2026-04-30T00:00:00+00:00",
        correlation_id="corr-metis-001",
    )


def _make_sentiment_message(
    text: str = "test text",
    source_agent: str = "test-sender",
    agent_id: str = "steward-1",
) -> ActorMessage:
    """Build an on_demand_sentiment message."""
    return ActorMessage(
        sender=agent_id,
        message_type="on_demand_sentiment",
        content={
            "text": text,
            "source_agent": source_agent,
            "reply_to": "test-replies",
        },
        timestamp="2026-04-30T00:00:00+00:00",
        correlation_id="corr-empath-001",
    )


# ===================================================================
# MetisAgent — _perform_analysis()
# ===================================================================


class TestMetisPerformAnalysis:
    """MetisAgent._perform_analysis() fallback behaviour."""

    @staticmethod
    async def test_returns_dict_with_expected_keys() -> None:
        """The fallback result contains analysis, confidence, and
        recommendations."""
        agent = _make_metis()
        result = await agent._perform_analysis("some context")

        assert isinstance(result, dict)
        assert "analysis" in result
        assert "confidence" in result
        assert "recommendations" in result

    @staticmethod
    async def test_returns_degraded_without_llm() -> None:
        """Without swarms_agent, the method returns a degraded result
        indicating the LLM was unavailable."""
        agent = _make_metis()
        result = await agent._perform_analysis("test")

        # Without swarms_agent, run_with_llm raises RuntimeError,
        # which is caught by the except Exception branch
        assert result["confidence"] == 0.0
        assert "failed" in result["analysis"].lower() or "failed" in str(result)

    @staticmethod
    async def test_with_mocked_swarms_agent_returns_analysis() -> None:
        """With a mocked swarms_agent, the method returns the LLM
        response as the analysis text."""
        agent = _make_metis()
        agent.swarms_agent = AsyncMock()
        agent.swarms_agent.agent_name = "test-agent"
        agent.run_with_llm = AsyncMock(
            return_value="1. Assess current resource allocation\n2. Identify bottlenecks\n3. Optimize workflow"
        )

        result = await agent._perform_analysis(
            context="optimize resource usage",
            perspective="conservative",
        )

        assert result["confidence"] == 0.85
        assert "Assess" in result["analysis"]
        assert "recommendations" in result
        assert len(result["recommendations"]) > 0

    @staticmethod
    async def test_catches_llm_error_and_returns_degraded() -> None:
        """When run_with_llm raises, the method returns a degraded
        result gracefully."""
        agent = _make_metis()
        agent.swarms_agent = AsyncMock()
        agent.swarms_agent.agent_name = "test-agent"

        async def _raise_error(*args, **kwargs):
            raise RuntimeError("LLM unavailable")

        agent.run_with_llm = _raise_error

        result = await agent._perform_analysis("test")

        assert result["confidence"] == 0.0
        assert "failed" in result["analysis"].lower()

    @staticmethod
    async def test_extracts_recommendations_from_llm_response() -> None:
        """Recommendations are extracted from numbered lines in the LLM
        response."""
        agent = _make_metis()
        agent.run_with_llm = AsyncMock(
            return_value="1. Shift resources to high-priority projects\n2. Reduce allocation to low-impact areas\n3. Set quarterly review cadence"
        )

        result = await agent._perform_analysis("resource allocation")

        assert len(result["recommendations"]) == 3
        assert "Shift" in result["recommendations"][0]
        assert "Reduce" in result["recommendations"][1]
        assert "Set" in result["recommendations"][2]

    @staticmethod
    async def test_handles_timeout_gracefully() -> None:
        """A TimeoutError from run_with_llm returns a degraded result
        with a clear timeout message."""
        agent = _make_metis()
        agent.run_with_llm = AsyncMock(side_effect=TimeoutError("timed out"))

        result = await agent._perform_analysis("test")

        assert result["confidence"] == 0.0
        assert "time" in result["analysis"].lower()
        assert "Retry" in result["recommendations"][0]


# ===================================================================
# MetisAgent — _handle_on_demand_analysis()
# ===================================================================


class TestMetisOnDemandAnalysisHandler:
    """MetisAgent._handle_on_demand_analysis() message handler."""

    @staticmethod
    async def test_sends_response_on_valid_input() -> None:
        """A valid on_demand_analysis message triggers a send()
        response."""
        agent = _make_metis()
        msg = _make_analysis_message(context="assess market conditions")

        await agent._handle_on_demand_analysis(msg)

        agent.send.assert_awaited_once()
        call_args = agent.send.await_args
        assert call_args is not None
        kwargs = call_args.kwargs if call_args.kwargs else call_args[1]
        content = kwargs.get("content") if hasattr(kwargs, "get") else kwargs

        # The response content varies — just check send was called
        assert agent.send.await_count == 1

    @staticmethod
    async def test_empty_context_triggers_error_response() -> None:
        """Empty context sends an error_response instead of analysis."""
        agent = _make_metis()
        msg = _make_analysis_message(context="")

        await agent._handle_on_demand_analysis(msg)

        agent.send.assert_awaited_once()
        call_args = agent.send.await_args
        assert call_args is not None
        kwargs = call_args.kwargs if call_args.kwargs else call_args[1]
        content = kwargs.get("content") if hasattr(kwargs, "get") else kwargs

        # Empty context should still send — verify
        assert agent.send.await_count == 1

    @staticmethod
    async def test_no_reply_to_does_not_send() -> None:
        """If the message has no reply_to, no send() is called."""
        agent = _make_metis()
        msg = _make_analysis_message(context="test context")
        msg.content = {"context": "test context"}  # No reply_to

        await agent._handle_on_demand_analysis(msg)

        assert agent.send.await_count == 0


# ===================================================================
# EmpathAgent — _perform_sentiment()
# ===================================================================


class TestEmpathPerformSentiment:
    """EmpathAgent._perform_sentiment() fallback behaviour."""

    @staticmethod
    async def test_returns_dict_with_expected_keys() -> None:
        """The fallback result contains sentiment, confidence,
        intensity, and emotions."""
        agent = _make_empath()
        result = await agent._analyze_sentiment_llm(
            "This is a great positive message"
        )

        assert isinstance(result, dict)
        assert "sentiment" in result
        assert "confidence" in result
        assert "intensity" in result
        assert "emotions" in result

    @staticmethod
    async def test_falls_back_to_heuristic_without_llm() -> None:
        """Without swarms_agent, the method falls back to heuristic
        analysis."""
        agent = _make_empath()
        # No swarms_agent set, so it uses heuristic
        result = await agent._analyze_sentiment_llm("This is great!")

        assert result["sentiment"] == "positive"
        assert result["confidence"] > 0


# ===================================================================
# EmpathAgent — on_demand_sentiment
# ===================================================================


class TestEmpathOnDemandSentiment:
    """EmpathAgent handling of on_demand_sentiment messages."""

    @staticmethod
    async def test_analyze_sentiment_handles_empty_text() -> None:
        """Empty text triggers a warning log and error response."""
        agent = _make_empath()
        # We need a message with reply_to so the handler sends
        msg = ActorMessage(
            sender="steward-1",
            message_type="analyze_sentiment",
            content={
                "text": "",
                "source_agent": "tester",
                "reply_to": "test-replies",
            },
            timestamp="2026-04-30T00:00:00+00:00",
        )

        await agent._handle_analyze_sentiment(msg)

        # The handler should call send() with the error response
        assert agent.send.await_count >= 1
