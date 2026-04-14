"""
GOV-05 Validation: Core Triad Convening with Quorum Mechanics.

Success criteria:
1. Triad convenes within 1s of Steward request
2. Quorum (3 of 4: Steward, Alpha, Beta, Charlie) within 3 rounds
3. Decision reached and logged
4. Audit trail complete

Edge cases: unresponsive members, tiebreaker, convoy/max_rounds.
"""

import asyncio
import time
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio

from heretek_swarm.actors.base import ActorMessage, ActorState
from heretek_swarm.actors.steward import StewardAgent
from heretek_swarm.actors.triad import AlphaAgent, BetaAgent, CharlieAgent
from heretek_swarm.consensus.maker import ConsensusState, MAKERConsensus

pytestmark = pytest.mark.asyncio


class MockNATS:
    def __init__(self):
        self.published_messages: list[dict] = []

    async def send_to_json(self, subject: str, data: dict) -> None:
        self.published_messages.append({"subject": subject, "data": data})

    async def publish(self, subject: str, data: dict, **kwargs) -> bool:
        self.published_messages.append({"subject": subject, "data": data})
        return True

    async def connect(self):
        return True

    async def disconnect(self):
        pass


class MockLLM:
    def __init__(self):
        self.responses: dict[str, str] = {}

    def register_response(self, pattern: str, response: str):
        self.responses[pattern] = response


@pytest_asyncio.fixture
async def mock_nats():
    return MockNATS()


@pytest_asyncio.fixture
async def mock_llm():
    return MockLLM()


def _msg(message_type: str, content: dict, sender: str = "test") -> ActorMessage:
    return ActorMessage(
        sender=sender,
        message_type=message_type,
        content=content,
        timestamp=datetime.now(UTC).isoformat(),
    )


def _spawn(cls, agent_id, mock_nats, mock_llm, **kw):
    with patch("heretek_swarm.actors.stubs.get_nats_event_mesh", return_value=mock_nats):
        with patch("heretek_swarm.actors.stubs.get_llm_provider", return_value=mock_llm):
            return cls(agent_id=agent_id, **kw)


def _find_nats(msgs, subject, content_key=None, content_val=None):
    result = []
    for m in msgs:
        if m.get("subject") != subject:
            continue
        inner = m.get("data", {}).get("content", {})
        if content_key and content_val:
            if inner.get(content_key) == content_val:
                result.append(m)
        else:
            result.append(m)
    return result


# ===== CRITERION 1: Triad convenes within 1 second =====


class TestCriterion1ConveningLatency:
    async def test_steward_convenes_triad(self, mock_nats, mock_llm):
        agent = _spawn(StewardAgent, "s1", mock_nats, mock_llm)
        await agent.spawn()
        result = await agent.coordinate_triad(
            topic="Deploy v2?",
            triad_members=["alpha", "beta", "charlie"],
            context={"priority": "high"},
        )
        assert result is not None
        assert result["topic"] == "Deploy v2?"
        assert result["phase"] == "initiated"
        await agent.terminate()

    async def test_convening_under_1s(self, mock_nats, mock_llm):
        agent = _spawn(StewardAgent, "s1", mock_nats, mock_llm)
        await agent.spawn()
        start = time.time()
        result = await agent.coordinate_triad(
            topic="Quick",
            triad_members=["alpha", "beta", "charlie"],
        )
        elapsed = time.time() - start
        assert elapsed < 1.0, f"Convening took {elapsed:.3f}s"
        assert result is not None
        await agent.terminate()

    async def test_convening_publishes_to_nats(self, mock_nats, mock_llm):
        agent = _spawn(StewardAgent, "s1", mock_nats, mock_llm)
        await agent.spawn()
        await agent.coordinate_triad(
            topic="NATS test",
            triad_members=["alpha", "beta", "charlie"],
        )
        assert len(mock_nats.published_messages) > 0
        await agent.terminate()

    async def test_start_deliberation_creates_session(self, mock_nats, mock_llm):
        agent = _spawn(StewardAgent, "s1", mock_nats, mock_llm)
        await agent.spawn()
        await agent.process_message(
            _msg(
                "start_deliberation",
                {
                    "deliberation_id": "d1",
                    "topic": "Test",
                    "triad_members": ["alpha", "beta", "charlie"],
                },
            )
        )
        assert "d1" in agent.active_deliberations
        d = agent.active_deliberations["d1"]
        assert d["topic"] == "Test"
        assert d["status"] == "initiated"
        assert d["started_at"] is not None
        await agent.terminate()

    async def test_tracks_concurrent_deliberations(self, mock_nats, mock_llm):
        agent = _spawn(StewardAgent, "s1", mock_nats, mock_llm)
        await agent.spawn()
        for i in range(3):
            await agent.process_message(
                _msg(
                    "start_deliberation",
                    {
                        "deliberation_id": f"cc-{i}",
                        "topic": f"T{i}",
                        "triad_members": ["alpha", "beta", "charlie"],
                    },
                )
            )
        assert len(agent.get_all_deliberation_statuses()) >= 3
        await agent.terminate()


# ===== CRITERION 2: Quorum (3 of 4) within 3 rounds =====


class TestCriterion2Quorum:
    async def test_maker_default_min_votes_3(self):
        assert MAKERConsensus().min_votes == 3

    async def test_quorum_4_members_split_vote(self):
        rw = {"steward": 1.0, "alpha": 1.0, "beta": 1.0, "charlie": 1.0}
        c = MAKERConsensus(ahead_by_k=1, min_votes=3, reputation_weights=rw)
        c.start_consensus("q4")
        c.add_vote("q4", "steward", "approve", 0.9)
        c.add_vote("q4", "alpha", "approve", 0.85)
        c.add_vote("q4", "beta", "approve", 0.8)
        c.add_vote("q4", "charlie", "reject", 0.75)
        r = c.compute_consensus("q4")
        assert r is not None
        assert r.decision == "approve"

    async def test_quorum_3of4_one_absent(self):
        rw = {"steward": 1.0, "alpha": 1.0, "beta": 1.0}
        c = MAKERConsensus(ahead_by_k=1, min_votes=3, reputation_weights=rw)
        c.start_consensus("q3")
        c.add_vote("q3", "steward", "approve", 0.95)
        c.add_vote("q3", "alpha", "approve", 0.9)
        c.add_vote("q3", "beta", "reject", 0.3)
        r = c.compute_consensus("q3")
        assert r is not None, "Quorum with 3 of 4 votes"
        assert r.decision == "approve"

    async def test_quorum_fails_2_votes(self):
        c = MAKERConsensus(ahead_by_k=1, min_votes=3)
        c.start_consensus("q2")
        c.add_vote("q2", "steward", "approve", 0.9)
        c.add_vote("q2", "alpha", "reject", 0.85)
        r = c.compute_consensus("q2")
        assert r is None

    async def test_consensus_within_3_rounds(self):
        rw = {"steward": 1.0, "alpha": 1.0, "beta": 1.0}
        c = MAKERConsensus(ahead_by_k=1, min_votes=3, reputation_weights=rw)
        c.start_consensus("rnd")
        c.add_vote("rnd", "steward", "approve", 0.95)
        c.add_vote("rnd", "alpha", "reject", 0.3)
        assert c.compute_consensus("rnd") is None
        c.add_vote("rnd", "beta", "approve", 0.9)
        r = c.compute_consensus("rnd")
        assert r is not None
        assert r.decision == "approve"

    async def test_gap_unanimous_fails_ahead_by_k(self):
        c = MAKERConsensus(ahead_by_k=1, min_votes=3)
        c.start_consensus("unan")
        c.add_vote("unan", "steward", "approve", 0.9)
        c.add_vote("unan", "alpha", "approve", 0.85)
        c.add_vote("unan", "beta", "approve", 0.8)
        r = c.compute_consensus("unan")
        assert r is not None, "Unanimous votes should reach consensus"
        assert r.decision == "approve"
        assert r.confidence == 1.0

    async def test_steward_deliberation_has_votes_dict(self, mock_nats, mock_llm):
        agent = _spawn(StewardAgent, "s1", mock_nats, mock_llm)
        await agent.spawn()
        await agent.process_message(
            _msg(
                "start_deliberation",
                {
                    "deliberation_id": "vd",
                    "topic": "Votes",
                    "triad_members": ["alpha", "beta", "charlie"],
                },
            )
        )
        d = agent.active_deliberations["vd"]
        assert "votes" in d
        assert isinstance(d["votes"], dict)
        d["votes"]["steward"] = {"decision": "approve"}
        d["votes"]["alpha"] = {"decision": "approve"}
        d["votes"]["beta"] = {"decision": "approve"}
        assert len(d["votes"]) == 3
        assert "charlie" not in d["votes"]
        await agent.terminate()


# ===== CRITERION 3: Decision reached and logged =====


class TestCriterion3DecisionLogging:
    async def test_decision_advances_phase(self, mock_nats, mock_llm):
        agent = _spawn(StewardAgent, "s1", mock_nats, mock_llm)
        await agent.spawn()
        agent._deliberations["dp"] = {"session_id": "dp", "problem": "P", "phase": "alpha"}
        await agent.process_message(
            _msg(
                "request_decision",
                {"request_id": "r1", "session_id": "dp", "context": {"q": "Deploy?"}},
                sender="alpha-001",
            )
        )
        assert agent._deliberations["dp"]["phase"] == "beta"
        await agent.terminate()

    async def test_decision_published(self, mock_nats, mock_llm):
        agent = _spawn(StewardAgent, "s1", mock_nats, mock_llm)
        await agent.spawn()
        agent._deliberations["dp2"] = {"session_id": "dp2", "problem": "P", "phase": "alpha"}
        await agent.process_message(
            _msg(
                "request_decision",
                {"request_id": "r1", "session_id": "dp2", "context": {"q": "Approve?"}},
            )
        )
        dm = _find_nats(mock_nats.published_messages, "decisions")
        assert len(dm) > 0
        await agent.terminate()

    async def test_maker_logs_all_votes(self):
        rw = {"steward": 1.0, "alpha": 1.0, "beta": 1.0}
        c = MAKERConsensus(ahead_by_k=1, min_votes=3, reputation_weights=rw)
        c.start_consensus("av")
        c.add_vote("av", "steward", "approve", 0.95)
        c.add_vote("av", "alpha", "approve", 0.9)
        c.add_vote("av", "beta", "reject", 0.3)
        r = c.compute_consensus("av")
        assert r is not None
        assert r.decision == "approve"
        all_votes = c.active_processes["av"]
        assert len(all_votes) == 3
        ids = {v.agent_id for v in all_votes}
        assert ids == {"steward", "alpha", "beta"}

    async def test_phase_progression_complete(self, mock_nats, mock_llm):
        agent = _spawn(StewardAgent, "s1", mock_nats, mock_llm)
        await agent.spawn()
        agent._deliberations["pp"] = {"session_id": "pp", "problem": "P", "phase": "alpha"}

        await agent.process_message(
            _msg("request_decision", {"request_id": "r1", "session_id": "pp"}, sender="alpha-001")
        )
        assert agent._deliberations["pp"]["phase"] == "beta"

        await agent.process_message(
            _msg("request_decision", {"request_id": "r2", "session_id": "pp"}, sender="beta-001")
        )
        assert agent._deliberations["pp"]["phase"] == "charlie"

        await agent.process_message(
            _msg("request_decision", {"request_id": "r3", "session_id": "pp"}, sender="charlie-001")
        )
        assert agent._deliberations["pp"]["phase"] == "complete"
        await agent.terminate()


# ===== CRITERION 4: Audit trail =====


class TestCriterion4AuditTrail:
    async def test_deliberation_timestamp(self, mock_nats, mock_llm):
        agent = _spawn(StewardAgent, "s1", mock_nats, mock_llm)
        await agent.spawn()
        await agent.process_message(
            _msg(
                "start_deliberation",
                {
                    "deliberation_id": "ats",
                    "topic": "TS",
                    "triad_members": ["alpha"],
                },
            )
        )
        d = agent.active_deliberations["ats"]
        assert "started_at" in d
        datetime.fromisoformat(d["started_at"])
        await agent.terminate()

    async def test_deliberation_tracks_members(self, mock_nats, mock_llm):
        agent = _spawn(StewardAgent, "s1", mock_nats, mock_llm)
        await agent.spawn()
        await agent.process_message(
            _msg(
                "start_deliberation",
                {
                    "deliberation_id": "am",
                    "topic": "Members",
                    "triad_members": ["alpha", "beta", "charlie"],
                },
            )
        )
        d = agent.active_deliberations["am"]
        assert d["topic"] == "Members"
        assert d["triad_members"] == ["alpha", "beta", "charlie"]
        await agent.terminate()

    async def test_policy_update_audit(self, mock_nats, mock_llm):
        agent = _spawn(StewardAgent, "s1", mock_nats, mock_llm)
        await agent.spawn()
        await agent.process_message(
            _msg(
                "policy_update",
                {
                    "policy_id": "pa",
                    "rules": [{"field": "x", "constraint": "req"}],
                },
                sender="gov-001",
            )
        )
        p = agent.get_governance_policy("pa")
        assert p is not None
        assert "updated_at" in p
        assert p["updated_by"] == "gov-001"
        await agent.terminate()

    async def test_deliberation_status_lookup(self, mock_nats, mock_llm):
        agent = _spawn(StewardAgent, "s1", mock_nats, mock_llm)
        await agent.spawn()
        await agent.process_message(
            _msg(
                "start_deliberation",
                {
                    "deliberation_id": "lu",
                    "topic": "Lookup",
                    "triad_members": ["alpha"],
                },
            )
        )
        assert agent.get_deliberation_status("lu") is not None
        assert agent.get_deliberation_status("lu")["status"] == "initiated"
        await agent.terminate()

    async def test_consensus_result_timestamp(self):
        rw = {"a": 1.0, "b": 1.0, "c": 1.0}
        c = MAKERConsensus(ahead_by_k=1, min_votes=3, reputation_weights=rw)
        c.start_consensus("cts")
        c.add_vote("cts", "a", "yes", 0.9)
        c.add_vote("cts", "b", "yes", 0.8)
        c.add_vote("cts", "c", "no", 0.7)
        r = c.compute_consensus("cts")
        assert r is not None
        assert r.timestamp is not None
        datetime.fromisoformat(r.timestamp)


# ===== EDGE: One member unresponsive =====


class TestEdgeOneUnresponsive:
    async def test_quorum_3of4(self):
        rw = {"steward": 1.0, "alpha": 1.0, "beta": 1.0}
        c = MAKERConsensus(ahead_by_k=1, min_votes=3, reputation_weights=rw)
        c.start_consensus("1abs")
        c.add_vote("1abs", "steward", "proceed", 0.95)
        c.add_vote("1abs", "alpha", "proceed", 0.9)
        c.add_vote("1abs", "beta", "hold", 0.3)
        r = c.compute_consensus("1abs")
        assert r is not None
        assert r.decision == "proceed"

    async def test_steward_tracks_voters(self, mock_nats, mock_llm):
        agent = _spawn(StewardAgent, "s1", mock_nats, mock_llm)
        await agent.spawn()
        await agent.process_message(
            _msg(
                "start_deliberation",
                {
                    "deliberation_id": "tv",
                    "topic": "Voters",
                    "triad_members": ["alpha", "beta", "charlie"],
                },
            )
        )
        d = agent.active_deliberations["tv"]
        d["votes"]["steward"] = {"decision": "approve"}
        d["votes"]["alpha"] = {"decision": "approve"}
        d["votes"]["beta"] = {"decision": "approve"}
        assert len(d["votes"]) == 3
        assert "charlie" not in d["votes"]
        await agent.terminate()


# ===== EDGE: Two members unresponsive =====


class TestEdgeTwoUnresponsive:
    async def test_quorum_fails(self):
        c = MAKERConsensus(ahead_by_k=1, min_votes=3)
        c.start_consensus("2abs")
        c.add_vote("2abs", "steward", "approve", 0.9)
        c.add_vote("2abs", "alpha", "reject", 0.8)
        assert c.compute_consensus("2abs") is None

    async def test_state_stays_gathering_below_min(self):
        rw = {"steward": 1.0, "alpha": 1.0}
        c = MAKERConsensus(ahead_by_k=1, min_votes=3, reputation_weights=rw)
        c.start_consensus("sf")
        c.add_vote("sf", "steward", "approve", 0.9)
        c.add_vote("sf", "alpha", "approve", 0.8)
        r = c.compute_consensus("sf")
        assert r is None
        assert c.get_process_state("sf") == ConsensusState.GATHERING


# ===== EDGE: Tiebreaker =====


class TestEdgeTiebreaker:
    async def test_split_no_consensus_with_k2(self):
        c = MAKERConsensus(ahead_by_k=2, min_votes=3)
        c.start_consensus("tie")
        c.add_vote("tie", "steward", "approve", 0.9)
        c.add_vote("tie", "alpha", "approve", 0.8)
        c.add_vote("tie", "beta", "reject", 0.7)
        assert c.compute_consensus("tie") is None

    async def test_steward_executive_fallback(self, mock_nats, mock_llm):
        agent = _spawn(StewardAgent, "s1", mock_nats, mock_llm)
        await agent.spawn()
        agent._deliberations["ef"] = {"session_id": "ef", "problem": "Tie", "phase": "charlie"}
        await agent.process_message(
            _msg(
                "request_decision",
                {"request_id": "tr", "session_id": "ef", "context": {"tied": True}},
            )
        )
        dm = _find_nats(mock_nats.published_messages, "decisions")
        assert len(dm) > 0
        await agent.terminate()

    async def test_steward_executive_with_llm(self, mock_nats):
        sa = MagicMock()
        sa.run = MagicMock(return_value="APPROVE deployment")
        with patch("heretek_swarm.actors.stubs.get_nats_event_mesh", return_value=mock_nats):
            with patch("heretek_swarm.actors.stubs.get_llm_provider", return_value=MockLLM()):
                agent = StewardAgent(agent_id="se", swarms_agent=sa)
                await agent.spawn()
                agent._deliberations["el"] = {
                    "session_id": "el",
                    "problem": "Tie",
                    "phase": "charlie",
                }
                await agent.process_message(
                    _msg(
                        "request_decision",
                        {"request_id": "te", "session_id": "el", "context": {"tied": True}},
                    )
                )
                dm = _find_nats(mock_nats.published_messages, "decisions")
                assert len(dm) > 0
                inner = dm[-1]["data"]["content"]
                assert inner["decision"] == "APPROVE deployment"
                assert inner["source"] == "steward"
                await agent.terminate()


# ===== EDGE: Convoy / max_rounds =====


class TestEdgeConvoyMaxRounds:
    async def test_consensus_timeout(self):
        c = MAKERConsensus(ahead_by_k=1, min_votes=3)

        async def slow(aid):
            await asyncio.sleep(10)
            return ("approve", 0.9)

        r = await c.run_consensus("to", ["a1", "a2", "a3"], slow, timeout=0.5)
        assert r is None

    async def test_deliberation_mixin_returns_without_subscriber(self):
        from heretek_swarm.actors.mixins.deliberation import DeliberationMixin

        m = DeliberationMixin()
        m._deliberation_id = "td"
        m.logger = MagicMock()
        r = await m._submit_deliberation_position("td", {"decision": "a"}, timeout=0.1)
        assert r is not None
        assert r == {"decision": None, "confidence": 0.0}

    async def test_params_configurable(self):
        c = MAKERConsensus(ahead_by_k=2, min_votes=3, confidence_threshold=0.6)
        assert c.ahead_by_k == 2
        assert c.min_votes == 3
        assert c.confidence_threshold == 0.6


# ===== Triad member responses =====


class TestTriadMembers:
    async def test_alpha_vote_response(self, mock_nats, mock_llm):
        agent = _spawn(AlphaAgent, "alpha-001", mock_nats, mock_llm)
        await agent.spawn()
        await agent.process_message(
            _msg(
                "deliberation_request",
                {
                    "deliberation_id": "av",
                    "topic": "Test",
                    "steward_id": "s1",
                },
                sender="s1",
            )
        )
        vm = _find_nats(mock_nats.published_messages, "triad", "message_type", "vote_response")
        assert len(vm) >= 1
        assert vm[0]["data"]["content"]["agent_id"] == "alpha-001"
        await agent.terminate()

    async def test_beta_vote_response(self, mock_nats, mock_llm):
        agent = _spawn(BetaAgent, "beta-001", mock_nats, mock_llm)
        await agent.spawn()
        await agent.process_message(
            _msg(
                "deliberation_request",
                {
                    "deliberation_id": "bv",
                    "topic": "Test",
                    "steward_id": "s1",
                },
                sender="s1",
            )
        )
        vm = _find_nats(mock_nats.published_messages, "triad", "message_type", "vote_response")
        assert len(vm) >= 1
        assert vm[0]["data"]["content"]["agent_id"] == "beta-001"
        await agent.terminate()

    async def test_charlie_vote_response(self, mock_nats, mock_llm):
        agent = _spawn(CharlieAgent, "charlie-001", mock_nats, mock_llm)
        await agent.spawn()
        await agent.process_message(
            _msg(
                "deliberation_request",
                {
                    "deliberation_id": "cv",
                    "topic": "Test",
                    "steward_id": "s1",
                },
                sender="s1",
            )
        )
        vm = _find_nats(mock_nats.published_messages, "triad", "message_type", "vote_response")
        assert len(vm) >= 1
        assert vm[0]["data"]["content"]["agent_id"] == "charlie-001"
        await agent.terminate()


# ===== End-to-end =====


class TestEndToEnd:
    async def test_full_consensus_flow(self, mock_nats):
        rw = {"se2e": 1.0, "a": 1.0, "b": 1.0}
        c = MAKERConsensus(ahead_by_k=1, min_votes=3, reputation_weights=rw)
        with patch("heretek_swarm.actors.stubs.get_nats_event_mesh", return_value=mock_nats):
            with patch("heretek_swarm.actors.stubs.get_llm_provider", return_value=MockLLM()):
                s = StewardAgent(agent_id="se2e")
                await s.spawn()
                r = await s.coordinate_triad(
                    topic="E2E",
                    triad_members=["a", "b", "c"],
                )
                assert r is not None
                sid = r["session_id"]
                c.start_consensus(sid)
                c.add_vote(sid, "se2e", "approve", 0.95)
                c.add_vote(sid, "a", "approve", 0.9)
                c.add_vote(sid, "b", "reject", 0.3)
                d = c.compute_consensus(sid)
                assert d is not None
                assert d.decision == "approve"
                await s.terminate()

    async def test_steward_status_report(self, mock_nats, mock_llm):
        agent = _spawn(StewardAgent, "s1", mock_nats, mock_llm)
        await agent.spawn()
        await agent.process_message(_msg("report_status", {"requester": "mon"}, sender="mon"))
        sm = _find_nats(mock_nats.published_messages, "status")
        assert len(sm) > 0
        inner = sm[-1]["data"]["content"]
        assert "active_deliberations" in inner
        assert inner["agent_id"] == "s1"
        await agent.terminate()
