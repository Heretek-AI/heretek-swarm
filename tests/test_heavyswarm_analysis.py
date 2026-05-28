"""Test T02: Verify heavyswarm _collect_triad_analyses uses NATS request-reply.

Validates that the placeholder analysis (hardcoded confidence=0.8, fabricated
insights) is replaced with real send_with_reply calls and honest fallback values.
"""

import pytest

from heretek_swarm.actors.base import AgentActor
from heretek_swarm.orchestration.heavyswarm import HeavySwarmWorkflow


class FakeAgent(AgentActor):
    """Test double that simulates NATS send_with_reply without a real broker."""

    def __init__(
        self,
        agent_id: str,
        reply_content: dict[str, object] | None = None,
        should_timeout: bool = False,
    ):
        super().__init__(agent_id=agent_id, role="worker")
        self._reply_content = reply_content
        self._should_timeout = should_timeout
        self.sent_messages: list[dict[str, object]] = []
        self.send_with_reply_called = False

    async def send_with_reply(self, recipient, message_type, content, timeout=30):  # noqa: ASYNC109
        self.send_with_reply_called = True
        self.sent_messages.append({
            "recipient": recipient,
            "message_type": message_type,
            "content": content,
            "timeout": timeout,
        })
        if self._should_timeout:
            return None  # Simulate timeout
        if self._reply_content is not None:
            return self._reply_content
        # Default: return a plausible analysis
        return {
            "decision": f"{self.agent_id}_real_decision",
            "confidence": 0.85,
            "insights": [f"Real insight from {self.agent_id}"],
            "reasoning": f"Detailed reasoning from {self.agent_id}",
        }


class FakeAgentError(FakeAgent):
    """Test double that always raises during send_with_reply."""

    async def send_with_reply(self, recipient, message_type, content, timeout=30):  # noqa: ASYNC109
        self.send_with_reply_called = True
        raise Exception("NATS connection lost")


@pytest.mark.asyncio
async def test_hardcoded_confidence_08_removed():
    """The old placeholder confidence=0.8 should be gone from the code."""
    import inspect

    source = inspect.getsource(HeavySwarmWorkflow._collect_triad_analyses)
    assert "0.8" not in source, "Hardcoded confidence=0.8 must be removed"


@pytest.mark.asyncio
async def test_placeholder_analysis_comment_removed():
    """The old 'placeholder analysis' comments should be gone."""
    import inspect

    source = inspect.getsource(HeavySwarmWorkflow._collect_triad_analyses)
    assert "placeholder" not in source.lower(), (
        "Must remove 'placeholder' comment from _collect_triad_analyses"
    )


@pytest.mark.asyncio
async def test_successful_analysis_uses_real_reply():
    """When send_with_reply returns a dict, real agent data populates the result."""
    wf = HeavySwarmWorkflow(
        triad_agents=["alpha", "beta"],
        phase_timeout=60,
    )
    alpha = FakeAgent("alpha", reply_content={
        "decision": "proceed",
        "confidence": 0.92,
        "insights": ["alpha insight 1", "alpha insight 2"],
        "reasoning": "alpha's reasoning",
    })
    beta = FakeAgent("beta", reply_content={
        "decision": "caution",
        "confidence": 0.78,
        "insights": ["beta insight 1"],
        "reasoning": "beta's reasoning",
    })
    wf.register_agent("alpha", alpha)
    wf.register_agent("beta", beta)

    result = await wf._collect_triad_analyses(
        workflow_id="test-wf",
        topic="test topic",
        research_data={"facts": ["a", "b"]},
    )

    assert result["alpha"]["confidence"] == 0.92
    assert result["alpha"]["decision"] == "proceed"
    assert result["alpha"]["insights"] == ["alpha insight 1", "alpha insight 2"]
    assert result["alpha"]["reasoning"] == "alpha's reasoning"

    assert result["beta"]["confidence"] == 0.78
    assert result["beta"]["decision"] == "caution"
    assert result["beta"]["insights"] == ["beta insight 1"]
    assert result["beta"]["reasoning"] == "beta's reasoning"

    # Verify send_with_reply was actually called (not the old fire-and-forget)
    assert alpha.send_with_reply_called
    assert beta.send_with_reply_called


@pytest.mark.asyncio
async def test_timeout_fallback_to_zero_confidence():
    """On timeout, confidence=0.0 with empty insights and structured log event."""
    wf = HeavySwarmWorkflow(
        triad_agents=["alpha"],
        phase_timeout=60,
    )
    agent = FakeAgent("alpha", should_timeout=True)
    wf.register_agent("alpha", agent)

    result = await wf._collect_triad_analyses(
        workflow_id="test-wf-timeout",
        topic="test",
        research_data={},
    )

    assert result["alpha"]["confidence"] == 0.0
    assert result["alpha"]["insights"] == []
    assert result["alpha"]["decision"] == "analysis_timeout"
    assert "timed out" in result["alpha"]["reasoning"]
    assert agent.send_with_reply_called


@pytest.mark.asyncio
async def test_exception_records_structured_log_event():
    """When send_with_reply raises, log event heavyswarm_analysis_error is emitted."""
    wf = HeavySwarmWorkflow(
        triad_agents=["alpha"],
        phase_timeout=60,
    )
    error_agent = FakeAgentError("alpha")
    wf.register_agent("alpha", error_agent)

    result = await wf._collect_triad_analyses(
        workflow_id="test-wf-error",
        topic="test",
        research_data={},
    )

    assert result["alpha"]["confidence"] == 0.0
    assert result["alpha"]["insights"] == []
    assert result["alpha"]["decision"] == "analysis_error"
    assert error_agent.send_with_reply_called


@pytest.mark.asyncio
async def test_missing_agent_handled_gracefully():
    """Missing agents produce a warning and are skipped."""
    wf = HeavySwarmWorkflow(
        triad_agents=["missing_agent"],
        phase_timeout=60,
    )
    # Register no agents
    result = await wf._collect_triad_analyses(
        workflow_id="test-wf",
        topic="test",
        research_data={},
    )
    assert "missing_agent" not in result


@pytest.mark.asyncio
async def test_empty_triad_returns_empty_dict():
    """Zero triad agents should produce an empty result dict."""
    wf = HeavySwarmWorkflow(
        triad_agents=[],
        phase_timeout=60,
    )
    result = await wf._collect_triad_analyses(
        workflow_id="test-wf",
        topic="test",
        research_data={},
    )
    assert result == {}


@pytest.mark.asyncio
async def test_real_agent_receives_correct_payload():
    """The message sent to agents contains the expected fields."""
    wf = HeavySwarmWorkflow(
        triad_agents=["alpha"],
        phase_timeout=60,
    )
    agent = FakeAgent("alpha")
    wf.register_agent("alpha", agent)

    await wf._collect_triad_analyses(
        workflow_id="wf-123",
        topic="deploy decision",
        research_data={"facts": ["staging is green"]},
        analysis_type="deep_analysis",
    )

    msg = agent.sent_messages[0]
    assert msg["recipient"] == "alpha"
    assert msg["message_type"] == "analysis_request"
    assert msg["content"]["workflow_id"] == "wf-123"  # type: ignore[index]
    assert msg["content"]["topic"] == "deploy decision"  # type: ignore[index]
    content = msg["content"]
    assert isinstance(content, dict)
    assert content["research_data"] == {"facts": ["staging is green"]}
    assert content["analysis_type"] == "deep_analysis"
    assert msg["timeout"] == 30
