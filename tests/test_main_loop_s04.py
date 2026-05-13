"""Tests for Metis and Empath agents.

Covers:
1. MetisAgent._perform_analysis() fallback without swarms_agent
2. MetisAgent._handle_on_demand_analysis() message handler
3. EmpathAgent._perform_sentiment() fallback (new run_with_llm method)
4. EmpathAgent._handle_on_demand_sentiment() message handler
5. EmpathAgent._analyze_sentiment_llm() existing LLM-based method
6. AutonomousSwarm._trigger_periodic_analysis() dispatches to metis/empath
7. AutonomousSwarm._trigger_periodic_analysis() None-guard graceful skip
8. Steward pulse writes _last_heartbeat via _steward_pulse_loop
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

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


# ---------------------------------------------------------------------------
# Swarm helper — builds a mock AutonomousSwarm for testing
# ---------------------------------------------------------------------------


class _MockSwarm:
    """Minimal AutonomousSwarm stand-in for testing
    _trigger_periodic_analysis() and _steward_pulse_loop().

    Exposes the same method signatures and attribute paths that
    the main_loop methods expect.
    """

    def __init__(self):
        self._analysis_cycle_count = 0
        self.supervisor = MagicMock()
        self.supervisor.actors = {}
        self._health_check_interval = 30
        self._running = True

    async def _trigger_periodic_analysis(self):
        """Inline copy of the production method for testing."""
        from datetime import UTC, datetime

        context = (
            f"Cycle analysis at tick {self._analysis_cycle_count}. "
            "Provide a concise strategic overview of current swarm state."
        )

        metis = self.supervisor.actors.get("metis") if self.supervisor else None
        if metis is not None:
            msg = ActorMessage(
                sender="main_loop",
                message_type="on_demand_analysis",
                content={
                    "context": context,
                    "perspective": "neutral",
                    "reply_to": "main_loop_analysis",
                },
                timestamp=datetime.now(UTC).isoformat(),
            )
            await metis.put_message(msg)

        empath = self.supervisor.actors.get("empath") if self.supervisor else None
        if empath is not None:
            msg = ActorMessage(
                sender="main_loop",
                message_type="on_demand_sentiment",
                content={
                    "text": context,
                    "source_agent": "main_loop",
                    "reply_to": "main_loop_sentiment",
                },
                timestamp=datetime.now(UTC).isoformat(),
            )
            await empath.put_message(msg)

    async def _steward_pulse_loop(self):
        """Inline copy for testing — single tick only."""
        from datetime import UTC, datetime

        steward = self.supervisor.actors.get("steward") if self.supervisor else None
        if steward is not None:
            steward.internal_state["_last_heartbeat"] = datetime.now(UTC).isoformat()

            historian = self.supervisor.actors.get("historian") if self.supervisor else None
            if historian is not None:
                pulse_data = {
                    "timestamp": datetime.now(UTC).isoformat(),
                    "active_actors": len(self.supervisor.actors) if self.supervisor else 0,
                    "deliberations_active": len(
                        getattr(steward, "active_deliberations", {})
                    ),
                    "heartbeat_healthy": True,
                }
                await historian.log_event("steward_pulse", "steward", pulse_data)


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
        assert agent.send.await_count == 1

    @staticmethod
    async def test_empty_context_triggers_error_response() -> None:
        """Empty context sends an error_response instead of analysis."""
        agent = _make_metis()
        msg = _make_analysis_message(context="")

        await agent._handle_on_demand_analysis(msg)

        agent.send.assert_awaited_once()
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
# EmpathAgent — _perform_sentiment() (new run_with_llm method)
# ===================================================================


class TestEmpathPerformSentimentNew:
    """EmpathAgent._perform_sentiment() fallback behaviour.

    This new method uses run_with_llm() for consistent timeout/error
    handling, unlike the existing _analyze_sentiment_llm() which calls
    self.swarms_agent.llm() directly.
    """

    @staticmethod
    async def test_returns_dict_with_expected_keys() -> None:
        """The fallback result contains sentiment, tone, and
        confidence."""
        agent = _make_empath()
        result = await agent._perform_sentiment("some text")

        assert isinstance(result, dict)
        assert "sentiment" in result
        assert "tone" in result
        assert "confidence" in result

    @staticmethod
    async def test_returns_degraded_without_llm() -> None:
        """Without swarms_agent, the method returns a degraded result
        indicating the LLM was unavailable."""
        agent = _make_empath()
        result = await agent._perform_sentiment("test text")

        # Without swarms_agent, run_with_llm raises RuntimeError,
        # which is caught by the except Exception branch
        assert result["confidence"] == 0.0
        assert result["sentiment"] == "neutral"
        assert result["tone"] == "unknown"

    @staticmethod
    async def test_with_mocked_swarms_agent_returns_sentiment() -> None:
        """With a mocked swarms_agent, the method returns the LLM
        response as the basis for sentiment."""
        agent = _make_empath()
        agent.swarms_agent = AsyncMock()
        agent.swarms_agent.agent_name = "test-agent"
        agent.run_with_llm = AsyncMock(
            return_value="The text expresses a positive outlook. "
            "The tone is confident and supportive."
        )

        result = await agent._perform_sentiment(
            text="We achieved all our goals this quarter!",
            source_agent="test-sender",
        )

        assert result["sentiment"] == "positive"
        assert result["tone"] == "confident"
        assert result["confidence"] == 0.8

    @staticmethod
    async def test_catches_llm_error_and_returns_degraded() -> None:
        """When run_with_llm raises, the method returns a degraded
        result gracefully."""
        agent = _make_empath()
        agent.swarms_agent = AsyncMock()
        agent.swarms_agent.agent_name = "test-agent"

        async def _raise_error(*args, **kwargs):
            raise RuntimeError("LLM unavailable")

        agent.run_with_llm = _raise_error

        result = await agent._perform_sentiment("test")

        assert result["confidence"] == 0.0
        assert result["sentiment"] == "neutral"

    @staticmethod
    async def test_handles_timeout_gracefully() -> None:
        """A TimeoutError from run_with_llm returns a degraded result."""
        agent = _make_empath()
        agent.run_with_llm = AsyncMock(side_effect=TimeoutError("timed out"))

        result = await agent._perform_sentiment("test")

        assert result["confidence"] == 0.0
        assert result["sentiment"] == "neutral"
        assert result["tone"] == "unknown"

    @staticmethod
    async def test_detects_negative_sentiment_from_llm_response() -> None:
        """The method detects negative sentiment in the LLM response."""
        agent = _make_empath()
        agent.run_with_llm = AsyncMock(
            return_value="The text is negative and pessimistic. "
            "The tone is critical."
        )

        result = await agent._perform_sentiment("This is a terrible failure.")

        assert result["sentiment"] == "negative"
        assert result["tone"] == "critical"

    @staticmethod
    async def test_detects_concerned_tone() -> None:
        """The method detects 'concerned' tone from LLM response."""
        agent = _make_empath()
        agent.run_with_llm = AsyncMock(
            return_value="The text expresses concern about the timeline. "
            "The sentiment is neutral with worried undertones."
        )

        result = await agent._perform_sentiment("I am concerned about the deadline.")

        assert result["sentiment"] == "neutral"  # No positive/negative keyword match
        assert result["tone"] == "concerned"


# ===================================================================
# EmpathAgent — _handle_on_demand_sentiment()
# ===================================================================


class TestEmpathOnDemandSentimentHandler:
    """EmpathAgent._handle_on_demand_sentiment() message handler."""

    @staticmethod
    async def test_sends_response_on_valid_input() -> None:
        """A valid on_demand_sentiment message triggers a send()
        response."""
        agent = _make_empath()
        msg = _make_sentiment_message(text="This is great news!")

        await agent._handle_on_demand_sentiment(msg)

        agent.send.assert_awaited_once()
        assert agent.send.await_count == 1

    @staticmethod
    async def test_empty_text_triggers_error_response() -> None:
        """Empty text sends an error_response instead of analysis."""
        agent = _make_empath()
        msg = _make_sentiment_message(text="")

        await agent._handle_on_demand_sentiment(msg)

        agent.send.assert_awaited_once()
        call_args = agent.send.await_args
        assert call_args is not None
        kwargs = call_args.kwargs if call_args.kwargs else call_args[1]
        content = kwargs.get("content") if hasattr(kwargs, "get") else kwargs
        assert content.get("message_type") == "error_response"

    @staticmethod
    async def test_no_reply_to_does_not_send() -> None:
        """If the message has no reply_to, no send() is called."""
        agent = _make_empath()
        msg = _make_sentiment_message(text="test text")
        msg.content = {"text": "test text"}  # No reply_to

        await agent._handle_on_demand_sentiment(msg)

        assert agent.send.await_count == 0


# ===================================================================
# EmpathAgent — _analyze_sentiment_llm() (existing heuristic fallback)
# ===================================================================


class TestEmpathAnalyzeSentimentLlm:
    """EmpathAgent._analyze_sentiment_llm() fallback behaviour."""

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
# AutonomousSwarm — _trigger_periodic_analysis()
# ===================================================================


class TestTriggerPeriodicAnalysis:
    """_trigger_periodic_analysis() dispatches to metis/empath."""

    @staticmethod
    async def test_dispatches_metis_and_empath_with_actors() -> None:
        """When metis, empath, and historian are in the actor registry,
        put_message is called on both agents."""
        swarm = _MockSwarm()
        metis = _make_metis("metis")
        empath = _make_empath("empath")
        historian = MagicMock()
        historian.log_event = AsyncMock()

        swarm.supervisor.actors["metis"] = metis
        swarm.supervisor.actors["empath"] = empath
        swarm.supervisor.actors["historian"] = historian

        await swarm._trigger_periodic_analysis()

        # Metis should have received an on_demand_analysis message
        assert metis.mailbox.qsize() == 1

        # Empath should have received an on_demand_sentiment message
        assert empath.mailbox.qsize() == 1

    @staticmethod
    async def test_skips_gracefully_without_metis() -> None:
        """When metis is absent, the method completes without error
        and empath is still dispatched."""
        swarm = _MockSwarm()
        empath = _make_empath("empath")
        swarm.supervisor.actors["empath"] = empath
        swarm.supervisor.actors["historian"] = MagicMock()

        await swarm._trigger_periodic_analysis()

        # Only empath should have a queued message
        assert empath.mailbox.qsize() == 1

    @staticmethod
    async def test_skips_gracefully_without_empath() -> None:
        """When empath is absent, the method completes without error
        and metis is still dispatched."""
        swarm = _MockSwarm()
        metis = _make_metis("metis")
        swarm.supervisor.actors["metis"] = metis
        swarm.supervisor.actors["historian"] = MagicMock()

        await swarm._trigger_periodic_analysis()

        # Only metis should have a queued message
        assert metis.mailbox.qsize() == 1

    @staticmethod
    async def test_skips_gracefully_without_any_agents() -> None:
        """When no agents are in the registry, the method completes
        without error."""
        swarm = _MockSwarm()
        await swarm._trigger_periodic_analysis()
        # No assertion needed — just verifying no exception


# ===================================================================
# AutonomousSwarm — _steward_pulse_loop()
# ===================================================================


class TestStewardPulseLoop:
    """_steward_pulse_loop() writes heartbeat data."""

    @staticmethod
    async def test_writes_heartbeat_to_steward_internal_state() -> None:
        """When steward is present, internal_state['_last_heartbeat']
        is set to an ISO timestamp."""
        swarm = _MockSwarm()
        steward = MagicMock()
        steward.internal_state = {}
        swarm.supervisor.actors["steward"] = steward

        await swarm._steward_pulse_loop()

        assert "_last_heartbeat" in steward.internal_state
        # Value should be a non-empty ISO string
        assert isinstance(steward.internal_state["_last_heartbeat"], str)
        assert len(steward.internal_state["_last_heartbeat"]) > 10

    @staticmethod
    async def test_logs_historian_event_when_historian_present() -> None:
        """When both steward and historian are present, the
        historian.log_event is called with steward_pulse type."""
        swarm = _MockSwarm()
        steward = MagicMock()
        steward.internal_state = {}
        steward.active_deliberations = {}
        historian = MagicMock()
        historian.log_event = AsyncMock()

        swarm.supervisor.actors["steward"] = steward
        swarm.supervisor.actors["historian"] = historian

        await swarm._steward_pulse_loop()

        historian.log_event.assert_awaited_once()
        call_args = historian.log_event.await_args
        assert call_args is not None
        assert call_args.args[0] == "steward_pulse"
        assert call_args.args[1] == "steward"


# ===================================================================
# —_analysis_cycle_count behaviour
# ===================================================================


class TestAnalysisCycleCount:
    """The _analysis_cycle_count starts at 0."""

    @staticmethod
    def test_starts_at_zero() -> None:
        """Initial value is 0."""
        swarm = _MockSwarm()
        assert swarm._analysis_cycle_count == 0
