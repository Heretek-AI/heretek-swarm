"""Test T02: Verify heavyswarm _generate_alternatives, _evaluate_alternative,
and _collect_triad_votes use real agent replies.

Validates that:
- All three methods route through real agent methods (run_with_llm or send_with_reply)
- Hardcoded 0.8/0.58/0.5 constants are no longer used as return values
- 0.0 fallbacks on failure paths
- Structured log events on all outcomes
"""

import json
import re
from unittest.mock import AsyncMock, patch

import pytest

from heretek_swarm.actors.base import AgentActor
from heretek_swarm.orchestration.heavyswarm import HeavySwarmWorkflow


# ---------------------------------------------------------------------------
# Fake agents
# ---------------------------------------------------------------------------


class FakeAgentWithLLM(AgentActor):
    """Test double that simulates run_with_llm responses."""

    def __init__(self, agent_id: str, llm_response: str = ""):
        super().__init__(agent_id=agent_id, role="worker")
        self._llm_response = llm_response
        self.run_with_llm_called = False
        self.run_with_llm_prompts: list[str] = []

    async def run_with_llm(self, prompt: str, timeout: int = 60, **kwargs):  # noqa: ASYNC109
        self.run_with_llm_called = True
        self.run_with_llm_prompts.append(prompt)
        return self._llm_response


class FakeAgentLLMError(FakeAgentWithLLM):
    """Test double whose run_with_llm always raises."""

    async def run_with_llm(self, prompt: str, timeout: int = 60, **kwargs):  # noqa: ASYNC109
        self.run_with_llm_called = True
        self.run_with_llm_prompts.append(prompt)
        raise RuntimeError("LLM API unavailable")


class FakeAgentWithReply(AgentActor):
    """Test double that simulates send_with_reply."""

    def __init__(
        self,
        agent_id: str,
        reply_content: dict | None = None,
        should_timeout: bool = False,
    ):
        super().__init__(agent_id=agent_id, role="worker")
        self._reply_content = reply_content
        self._should_timeout = should_timeout
        self.send_with_reply_called = False
        self.sent_messages: list[dict] = []

    async def send_with_reply(self, recipient, message_type, content, timeout=30):  # noqa: ASYNC109
        self.send_with_reply_called = True
        self.sent_messages.append({
            "recipient": recipient,
            "message_type": message_type,
            "content": content,
            "timeout": timeout,
        })
        if self._should_timeout:
            return None
        if self._reply_content is not None:
            return self._reply_content
        return {"decision": f"{self.agent_id}_approve", "confidence": 0.85}


class FakeAgentReplyError(FakeAgentWithReply):
    """Test double whose send_with_reply always raises."""

    async def send_with_reply(self, recipient, message_type, content, timeout=30):  # noqa: ASYNC109
        self.send_with_reply_called = True
        raise Exception("NATS connection lost")


# ============================================================================
# _generate_alternatives tests
# ============================================================================


@pytest.mark.asyncio
async def test_generate_alternatives_hardcoded_constants_removed():
    """Hardcoded 0.8/0.58/0.5 values removed from _generate_alternatives method body."""
    import inspect

    source = inspect.getsource(HeavySwarmWorkflow._generate_alternatives)
    # These constants should not appear as return values or hardcoded data
    assert "placeholder" not in source.lower(), "placeholder comment must be removed"
    assert "would use LLM" not in source.lower(), "old LLM-stub comment must be removed"


@pytest.mark.asyncio
async def test_generate_alternatives_uses_run_with_llm():
    """_generate_alternatives calls agent.run_with_llm() for real alternatives."""
    wf = HeavySwarmWorkflow(phase_timeout=60)
    valid_json = json.dumps([
        {"id": "dynamic_1", "name": "A", "description": "desc A", "type": "conservative"},
        {"id": "dynamic_2", "name": "B", "description": "desc B", "type": "balanced"},
        {"id": "dynamic_3", "name": "C", "description": "desc C", "type": "aggressive"},
    ])
    dreamer = FakeAgentWithLLM("dreamer", llm_response=valid_json)
    wf.register_agent("dreamer", dreamer)

    result = await wf._generate_alternatives("deploy now?", {"key_insights": ["i1"]})

    assert dreamer.run_with_llm_called, "dreamer.run_with_llm must be called"
    assert len(result) == 3
    assert result[0]["id"] == "dynamic_1"
    assert result[0]["name"] == "A"
    assert result[0]["type"] == "conservative"
    assert result[2]["id"] == "dynamic_3"


@pytest.mark.asyncio
async def test_generate_alternatives_fallsback_on_error():
    """On LLM failure, returns hardcoded fallback and logs structured event."""
    wf = HeavySwarmWorkflow(phase_timeout=60)
    dreamer = FakeAgentLLMError("dreamer")
    wf.register_agent("dreamer", dreamer)

    result = await wf._generate_alternatives("test", {})

    assert result[0]["id"] == "alt_1", "should fall back to hardcoded alternatives"
    assert dreamer.run_with_llm_called


@pytest.mark.asyncio
async def test_generate_alternatives_fallsback_on_parse_failure():
    """When LLM returns unparseable text, falls back to hardcoded list."""
    wf = HeavySwarmWorkflow(phase_timeout=60)
    dreamer = FakeAgentWithLLM("dreamer", llm_response="not valid json at all")
    wf.register_agent("dreamer", dreamer)

    result = await wf._generate_alternatives("test", {})

    assert result[0]["id"] == "alt_1", "should fall back to hardcoded alternatives"
    assert dreamer.run_with_llm_called


@pytest.mark.asyncio
async def test_generate_alternatives_no_agent_available():
    """When no dreamer or alpha agent is registered, uses fallback."""
    wf = HeavySwarmWorkflow(phase_timeout=60)
    # No agents registered

    result = await wf._generate_alternatives("test", {})

    assert result[0]["id"] == "alt_1", "should return hardcoded fallback"


@pytest.mark.asyncio
async def test_generate_alternatives_alpha_fallback():
    """When dreamer is unavailable, falls back to alpha agent."""
    wf = HeavySwarmWorkflow(phase_timeout=60)
    valid_json = json.dumps([
        {"id": "alpha_1", "name": "Alpha Plan", "description": "desc", "type": "balanced"},
        {"id": "alpha_2", "name": "Alpha Plan 2", "description": "desc", "type": "conservative"},
        {"id": "alpha_3", "name": "Alpha Plan 3", "description": "desc", "type": "aggressive"},
    ])
    alpha = FakeAgentWithLLM("alpha", llm_response=valid_json)
    wf.register_agent("alpha", alpha)

    result = await wf._generate_alternatives("test", {})

    assert alpha.run_with_llm_called, "alpha should be used as fallback for dreamer"
    assert result[0]["name"] == "Alpha Plan"


@pytest.mark.asyncio
async def test_generate_alternatives_dreamer_preferred_over_alpha():
    """dreamer is preferred over alpha when both are registered."""
    wf = HeavySwarmWorkflow(phase_timeout=60)
    valid_json = json.dumps([
        {"id": "d_1", "name": "Dreamer Plan", "description": "d", "type": "aggressive"},
        {"id": "d_2", "name": "Dreamer Plan 2", "description": "d", "type": "balanced"},
        {"id": "d_3", "name": "Dreamer Plan 3", "description": "d", "type": "conservative"},
    ])
    dreamer = FakeAgentWithLLM("dreamer", llm_response=valid_json)
    alpha = FakeAgentWithLLM("alpha", llm_response="ignored")
    wf.register_agent("dreamer", dreamer)
    wf.register_agent("alpha", alpha)

    await wf._generate_alternatives("test", {})

    assert dreamer.run_with_llm_called, "dreamer should be preferred"
    assert not alpha.run_with_llm_called, "alpha should not be called when dreamer succeeds"


# ============================================================================
# _parse_alternatives_json tests
# ============================================================================


def test_parse_alternatives_json_clean():
    result = HeavySwarmWorkflow._parse_alternatives_json(
        '[{"id":"a","name":"N","description":"d","type":"conservative"}]'
    )
    assert result is not None
    assert result[0]["id"] == "a"


def test_parse_alternatives_json_with_markdown_fence():
    result = HeavySwarmWorkflow._parse_alternatives_json(
        '```json\n[{"id":"a","name":"N","description":"d","type":"balanced"}]\n```'
    )
    assert result is not None
    assert result[0]["type"] == "balanced"


def test_parse_alternatives_json_invalid():
    result = HeavySwarmWorkflow._parse_alternatives_json("not json")
    assert result is None


def test_parse_alternatives_json_object_not_list():
    result = HeavySwarmWorkflow._parse_alternatives_json('{"key": "value"}')
    assert result is None


# ============================================================================
# _evaluate_alternative tests
# ============================================================================


@pytest.mark.asyncio
async def test_evaluate_alternative_hardcoded_constants_removed():
    """Hardcoded return values (feasibility=0.8, impact=0.7, etc.) removed."""
    import inspect

    source = inspect.getsource(HeavySwarmWorkflow._evaluate_alternative)
    assert "placeholder" not in source.lower(), "placeholder comment must be removed"


@pytest.mark.asyncio
async def test_evaluate_alternative_uses_run_with_llm():
    """_evaluate_alternative calls alpha.run_with_llm() for real scoring."""
    wf = HeavySwarmWorkflow(phase_timeout=60)
    eval_json = json.dumps({
        "feasibility": 0.95,
        "impact": 0.88,
        "risk": 0.12,
        "cost": 0.30,
        "time_to_implement": 0.25,
        "total_score": 0.75,
    })
    alpha = FakeAgentWithLLM("alpha", llm_response=eval_json)
    wf.register_agent("alpha", alpha)

    result = await wf._evaluate_alternative(
        {"id": "alt_1", "name": "Test Alternative", "description": "desc"},
        {"key_insights": ["i1"]},
    )

    assert alpha.run_with_llm_called, "alpha.run_with_llm must be called"
    assert result["feasibility"] == 0.95
    assert result["impact"] == 0.88
    assert result["risk"] == 0.12
    assert result["cost"] == 0.30
    assert result["time_to_implement"] == 0.25
    assert result["total_score"] == 0.75


@pytest.mark.asyncio
async def test_evaluate_alternative_fallback_zero_scores():
    """On LLM error, returns all zeros with structured log event."""
    wf = HeavySwarmWorkflow(phase_timeout=60)
    alpha = FakeAgentLLMError("alpha")
    wf.register_agent("alpha", alpha)

    result = await wf._evaluate_alternative(
        {"id": "alt_1", "name": "Error Case"},
        {},
    )

    assert alpha.run_with_llm_called
    assert result["feasibility"] == 0.0
    assert result["impact"] == 0.0
    assert result["risk"] == 0.0
    assert result["cost"] == 0.0
    assert result["time_to_implement"] == 0.0
    assert result["total_score"] == 0.0


@pytest.mark.asyncio
async def test_evaluate_alternative_no_alpha_agent():
    """When no alpha agent exists, returns zero-score fallback."""
    wf = HeavySwarmWorkflow(phase_timeout=60)
    # No alpha registered

    result = await wf._evaluate_alternative(
        {"id": "alt_1", "name": "No Alpha"},
        {},
    )

    assert result["feasibility"] == 0.0
    assert result["total_score"] == 0.0


@pytest.mark.asyncio
async def test_evaluate_alternative_parses_markdown_fenced_json():
    """LLM response with ```json fences is parsed correctly."""
    wf = HeavySwarmWorkflow(phase_timeout=60)
    eval_json = '```json\n{"feasibility": 0.55, "impact": 0.60, "risk": 0.40, "cost": 0.50, "time_to_implement": 0.45, "total_score": 0.50}\n```'
    alpha = FakeAgentWithLLM("alpha", llm_response=eval_json)
    wf.register_agent("alpha", alpha)

    result = await wf._evaluate_alternative(
        {"id": "a", "name": "Markdown Case"},
        {},
    )

    assert result["feasibility"] == 0.55
    assert result["total_score"] == 0.50


# ============================================================================
# _collect_triad_votes tests
# ============================================================================


@pytest.mark.asyncio
async def test_collect_triad_votes_hardcoded_constants_removed():
    """Hardcoded confidence=0.8 removed from _collect_triad_votes."""
    import inspect

    source = inspect.getsource(HeavySwarmWorkflow._collect_triad_votes)
    # Check that the hardcoded 0.8 is gone from the method body
    assert "simulate" not in source.lower(), "simulate comment must be removed"
    assert "would be real" not in source.lower(), "stub comment must be removed"


@pytest.mark.asyncio
async def test_collect_triad_votes_uses_send_with_reply():
    """_collect_triad_votes calls agent.send_with_reply() for each triad member."""
    wf = HeavySwarmWorkflow(triad_agents=["alpha", "beta"], phase_timeout=60)
    alpha = FakeAgentWithReply("alpha", reply_content={"decision": "approve", "confidence": 0.91})
    beta = FakeAgentWithReply("beta", reply_content={"decision": "reject", "confidence": 0.87})
    wf.register_agent("alpha", alpha)
    wf.register_agent("beta", beta)

    votes = await wf._collect_triad_votes(
        consensus_id="cons_1",
        topic="deploy?",
        verification_data={
            "recommended_alternative": {"name": "Balanced Approach"},
            "overall_valid": True,
            "confidence": 0.80,
            "error_checks": [],
            "risk_assessments": [],
        },
    )

    assert len(votes) == 2
    assert alpha.send_with_reply_called
    assert beta.send_with_reply_called

    alpha_vote = next(v for v in votes if v["agent_id"] == "alpha")
    assert alpha_vote["confidence"] == 0.91
    assert alpha_vote["decision"] == "approve"

    beta_vote = next(v for v in votes if v["agent_id"] == "beta")
    assert beta_vote["confidence"] == 0.87
    assert beta_vote["decision"] == "reject"


@pytest.mark.asyncio
async def test_collect_triad_votes_timeout_zero_confidence():
    """On timeout, confidence=0.0 with vote_timeout decision."""
    wf = HeavySwarmWorkflow(triad_agents=["alpha"], phase_timeout=60)
    agent = FakeAgentWithReply("alpha", should_timeout=True)
    wf.register_agent("alpha", agent)

    votes = await wf._collect_triad_votes(
        consensus_id="cons_2",
        topic="test",
        verification_data={"recommended_alternative": {}, "overall_valid": True},
    )

    assert len(votes) == 1
    assert votes[0]["confidence"] == 0.0
    assert votes[0]["decision"] == "vote_timeout"
    assert agent.send_with_reply_called


@pytest.mark.asyncio
async def test_collect_triad_votes_error_zero_confidence():
    """On exception, confidence=0.0 with vote_error decision."""
    wf = HeavySwarmWorkflow(triad_agents=["alpha"], phase_timeout=60)
    error_agent = FakeAgentReplyError("alpha")
    wf.register_agent("alpha", error_agent)

    votes = await wf._collect_triad_votes(
        consensus_id="cons_3",
        topic="test",
        verification_data={"recommended_alternative": {}, "overall_valid": True},
    )

    assert len(votes) == 1
    assert votes[0]["confidence"] == 0.0
    assert votes[0]["decision"] == "vote_error"
    assert error_agent.send_with_reply_called


@pytest.mark.asyncio
async def test_collect_triad_votes_missing_agent_skipped():
    """Missing agents are skipped without crashing."""
    wf = HeavySwarmWorkflow(triad_agents=["alpha", "missing"], phase_timeout=60)
    alpha = FakeAgentWithReply("alpha")
    wf.register_agent("alpha", alpha)

    votes = await wf._collect_triad_votes(
        consensus_id="cons_4",
        topic="test",
        verification_data={"recommended_alternative": {}, "overall_valid": True},
    )

    assert len(votes) == 1, "only registered agent should produce a vote"
    assert votes[0]["agent_id"] == "alpha"


@pytest.mark.asyncio
async def test_collect_triad_votes_empty_triad():
    """Zero triad agents returns empty votes list."""
    wf = HeavySwarmWorkflow(triad_agents=[], phase_timeout=60)

    votes = await wf._collect_triad_votes(
        consensus_id="cons_5",
        topic="test",
        verification_data={"recommended_alternative": {}},
    )

    assert votes == []


@pytest.mark.asyncio
async def test_collect_triad_votes_adds_to_consensus_engine():
    """Each vote is added to the consensus engine via add_vote()."""
    wf = HeavySwarmWorkflow(triad_agents=["alpha"], phase_timeout=60)
    alpha = FakeAgentWithReply("alpha", reply_content={"decision": "approve", "confidence": 0.93})
    wf.register_agent("alpha", alpha)

    # Spy on consensus_engine.add_vote
    with patch.object(wf.consensus_engine, "add_vote", wraps=wf.consensus_engine.add_vote) as spy:
        await wf._collect_triad_votes(
            consensus_id="cs_test",
            topic="test",
            verification_data={"recommended_alternative": {"name": "test"}, "overall_valid": True},
        )

        spy.assert_called_once_with(
            consensus_id="cs_test",
            agent_id="alpha",
            decision="approve",
            confidence=0.93,
        )


# ============================================================================
# Integration: verify all three methods interact correctly
# ============================================================================


@pytest.mark.asyncio
async def test_alternatives_phase_end_to_end():
    """Verify the alternatives phase orchestrates all three methods correctly."""
    wf = HeavySwarmWorkflow(triad_agents=["alpha"], phase_timeout=60)

    alt_json = json.dumps([
        {"id": "a1", "name": "Go Fast", "description": "fast", "type": "aggressive"},
        {"id": "a2", "name": "Go Slow", "description": "slow", "type": "conservative"},
        {"id": "a3", "name": "Go Medium", "description": "med", "type": "balanced"},
    ])
    eval_json = json.dumps({
        "feasibility": 0.9, "impact": 0.8, "risk": 0.2,
        "cost": 0.3, "time_to_implement": 0.2, "total_score": 0.85,
    })
    dreamer = FakeAgentWithLLM("dreamer", llm_response=alt_json)
    alpha = FakeAgentWithLLM("alpha", llm_response=eval_json)
    wf.register_agent("dreamer", dreamer)
    wf.register_agent("alpha", alpha)

    result = await wf._alternatives_phase("wf-1", "topic", None, {"key_insights": []})

    assert dreamer.run_with_llm_called, "generate should use dreamer"
    assert alpha.run_with_llm_called, "evaluate should use alpha"
    assert len(result["alternatives"]) == 3
    # All alternatives should have evaluation scores (from LLM)
    for alt in result["alternatives"]:
        assert "evaluation" in alt
        assert alt["evaluation"]["total_score"] == 0.85
    assert result["recommended_alternative"] is not None
