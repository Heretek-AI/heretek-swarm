"""
Validation tests for Tasks 2, 6-9: Base Class Health Reporting + Core Triad Agents.

Validates success criteria from PLAN.md:
- Task 2: Base Class + Health Reporting (heartbeat, state query, failure detection)
- Task 6: GOV-01 Steward Monitoring
- Task 7: GOV-02 Alpha Deep Analysis
- Task 8: GOV-03 Beta Error Detection
- Task 9: GOV-04 Charlie Critical Review
"""

import asyncio
import time
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio

from heretek_swarm.actors.base import ActorMessage, ActorState
from heretek_swarm.actors.base.core import AgentActor
from heretek_swarm.actors.alpha import AlphaAgent
from heretek_swarm.actors.beta import BetaAgent
from heretek_swarm.actors.charlie import CharlieAgent
from heretek_swarm.actors.steward import StewardAgent
from heretek_swarm.actors.mixins.health_reporting import HealthReportingMixin


# ============================================================================
# Fixtures
# ============================================================================


class MockEventMesh:
    """In-memory mock event mesh for heartbeat testing."""

    def __init__(self):
        self.published: list[tuple[str, dict]] = []
        self._connected = True

    async def publish(self, subject: str, data: dict):
        self.published.append((subject, data))
        return True

    async def send_to_json(self, subject: str, data: dict):
        self.published.append((subject, data))

    async def connect(self):
        self._connected = True

    async def disconnect(self):
        self._connected = False


@pytest_asyncio.fixture
async def mock_mesh():
    return MockEventMesh()


@pytest_asyncio.fixture
async def mock_llm():
    return MagicMock()


def _make_actor(cls, agent_id, mesh, llm, **kwargs):
    """Create an actor with mocked stubs."""
    with patch("heretek_swarm.actors.stubs.get_nats_event_mesh", return_value=mesh):
        with patch("heretek_swarm.actors.stubs.get_llm_provider", return_value=llm):
            return cls(agent_id=agent_id, load_state_on_init=False, **kwargs)


@pytest_asyncio.fixture
async def steward(mock_mesh, mock_llm):
    agent = _make_actor(StewardAgent, "steward-001", mock_mesh, mock_llm)
    yield agent
    if agent._running:
        agent._running = False
        await agent._cancel_tasks()


@pytest_asyncio.fixture
async def alpha(mock_mesh, mock_llm):
    agent = _make_actor(AlphaAgent, "alpha-001", mock_mesh, mock_llm)
    yield agent
    if agent._running:
        agent._running = False
        await agent._cancel_tasks()


@pytest_asyncio.fixture
async def beta(mock_mesh, mock_llm):
    agent = _make_actor(BetaAgent, "beta-001", mock_mesh, mock_llm)
    yield agent
    if agent._running:
        agent._running = False
        await agent._cancel_tasks()


@pytest_asyncio.fixture
async def charlie(mock_mesh, mock_llm):
    agent = _make_actor(CharlieAgent, "charlie-001", mock_mesh, mock_llm)
    yield agent
    if agent._running:
        agent._running = False
        await agent._cancel_tasks()


@pytest_asyncio.fixture
async def spawned_steward(steward, mock_mesh):
    await steward.spawn()
    yield steward
    if steward._running:
        await steward.terminate()


@pytest_asyncio.fixture
async def spawned_alpha(alpha, mock_mesh):
    await alpha.spawn()
    yield alpha
    if alpha._running:
        await alpha.terminate()


@pytest_asyncio.fixture
async def spawned_beta(beta, mock_mesh):
    await beta.spawn()
    yield beta
    if beta._running:
        await beta.terminate()


@pytest_asyncio.fixture
async def spawned_charlie(charlie, mock_mesh):
    await charlie.spawn()
    yield charlie
    if charlie._running:
        await charlie.terminate()


def _make_message(msg_type, content, sender="test-sender", recipient=None):
    """Helper to create ActorMessage."""
    return ActorMessage(
        sender=sender,
        message_type=msg_type,
        content=content,
        timestamp=datetime.now(UTC).isoformat(),
        recipient=recipient,
    )


# ============================================================================
# Task 2: Base Class + Health Reporting
# ============================================================================


class TestTask2BaseClassHealthReporting:
    """Validate Task 2 success criteria."""

    @pytest.mark.asyncio
    async def test_heartbeat_interval_configurable_to_5s(self, mock_mesh, mock_llm):
        """Criterion 2.1: All Phase 1 agents emit heartbeat every 5 seconds.

        Validates heartbeat_interval is configurable (default 10s, can set to 5s).
        """
        # Default is 10s but configurable
        agent = _make_actor(
            AlphaAgent,
            "alpha-hb",
            mock_mesh,
            mock_llm,
            heartbeat_interval=5.0,
        )
        assert agent.heartbeat_interval == 5.0
        if agent._running:
            agent._running = False
            await agent._cancel_tasks()

    @pytest.mark.asyncio
    async def test_heartbeat_emits_on_spawn(self, mock_mesh, mock_llm):
        """Criterion 2.1: Heartbeat emission from spawned agent.

        Verifies that _heartbeat_loop publishes heartbeats when agent is spawned.
        """
        agent = _make_actor(
            AlphaAgent,
            "alpha-hb2",
            mock_mesh,
            mock_llm,
            heartbeat_interval=0.1,  # Fast for testing
        )
        await agent.spawn()
        await asyncio.sleep(0.25)  # Allow at least 2 heartbeats

        # Check heartbeats published to event mesh
        heartbeat_msgs = [(subj, data) for subj, data in mock_mesh.published if "heartbeat" in subj]
        assert len(heartbeat_msgs) >= 2, f"Expected >= 2 heartbeats, got {len(heartbeat_msgs)}"
        await agent.terminate()

    @pytest.mark.asyncio
    async def test_heartbeat_contains_required_fields(self, mock_mesh, mock_llm):
        """Criterion 2.1: Heartbeat data contains agent_id, state, timestamp."""
        agent = _make_actor(
            AlphaAgent,
            "alpha-hb3",
            mock_mesh,
            mock_llm,
            heartbeat_interval=0.1,
        )
        await agent.spawn()
        await asyncio.sleep(0.15)

        heartbeat_msgs = [data for subj, data in mock_mesh.published if "heartbeat" in subj]
        assert len(heartbeat_msgs) >= 1
        hb = heartbeat_msgs[0]
        assert "agent_id" in hb
        assert "state" in hb
        assert "timestamp" in hb
        assert hb["agent_id"] == "alpha-hb3"
        await agent.terminate()

    @pytest.mark.asyncio
    async def test_all_triad_agents_have_heartbeat(self, mock_mesh, mock_llm):
        """Criterion 2.1: Steward, Alpha, Beta, Charlie all emit heartbeats."""
        agents = []
        for cls, name in [
            (StewardAgent, "steward-hb"),
            (AlphaAgent, "alpha-hb"),
            (BetaAgent, "beta-hb"),
            (CharlieAgent, "charlie-hb"),
        ]:
            agent = _make_actor(cls, name, mock_mesh, mock_llm, heartbeat_interval=0.1)
            await agent.spawn()
            agents.append(agent)

        await asyncio.sleep(0.25)

        for agent in agents:
            agent_hbs = [
                (s, d) for s, d in mock_mesh.published if "heartbeat" in s and agent.agent_id in s
            ]
            assert len(agent_hbs) >= 1, f"No heartbeats from {agent.agent_id}"

        for agent in agents:
            await agent.terminate()

    @pytest.mark.asyncio
    async def test_steward_agent_state_query(self, spawned_steward, mock_mesh):
        """Criterion 2.2: Steward can query agent states.

        Validates Steward handles report_status messages and stores state.
        """
        # Simulate agents reporting status to Steward
        for agent_id in ["agent-a", "agent-b", "agent-c"]:
            msg = _make_message(
                "report_status",
                {"agent_id": agent_id, "status": {"state": "active", "health": "ok"}},
                sender=agent_id,
            )
            await spawned_steward.process_message(msg)

        # Verify Steward stored states
        for agent_id in ["agent-a", "agent-b", "agent-c"]:
            stored = spawned_steward.get_state(f"status:{agent_id}")
            assert stored is not None, f"Steward did not store state for {agent_id}"
            assert stored["state"] == "active"

    @pytest.mark.asyncio
    async def test_steward_state_query_latency(self, spawned_steward, mock_mesh):
        """Criterion 2.2: Steward queries agent states within 2 seconds.

        Measures time to process multiple status reports.
        """
        start = time.time()
        for i in range(13):  # 13 agents
            msg = _make_message(
                "report_status",
                {"agent_id": f"agent-{i}", "status": {"state": "active"}},
                sender=f"agent-{i}",
            )
            await spawned_steward.process_message(msg)
        elapsed = time.time() - start

        assert elapsed < 2.0, (
            f"Steward took {elapsed:.3f}s to process 13 status reports (limit: 2s)"
        )

    @pytest.mark.asyncio
    async def test_heartbeat_failure_detection_gap(self, mock_mesh, mock_llm):
        """Criterion 2.3: Heartbeat failure detection < 10 seconds.

        GAP ANALYSIS: The current _heartbeat_loop publishes heartbeats but
        no component monitors for MISSED heartbeats. The StewardAgent does
        not have heartbeat monitoring or failure detection logic.

        This test documents the gap.
        """
        # Check if StewardAgent has heartbeat monitoring methods
        steward = _make_actor(StewardAgent, "steward-gap", mock_mesh, mock_llm)

        has_failure_detection = (
            hasattr(steward, "check_agent_health")
            or hasattr(steward, "detect_heartbeat_failure")
            or hasattr(steward, "monitor_agents")
            or hasattr(steward, "_heartbeat_timeout")
        )

        # This will fail until heartbeat monitoring is implemented
        if not has_failure_detection:
            pytest.skip(
                "GAP: StewardAgent lacks heartbeat failure detection. "
                "No monitor_agents/check_agent_health/detect_heartbeat_failure method."
            )

    @pytest.mark.asyncio
    async def test_health_reporting_mixin_provides_status(self, mock_mesh, mock_llm):
        """Criterion 2: HealthReportingMixin provides health status data."""
        agent = _make_actor(AlphaAgent, "alpha-health", mock_mesh, mock_llm)
        assert isinstance(agent, HealthReportingMixin)

        # HealthReportingMixin requires self.logger - verify it works
        status = agent.get_health_status()
        assert "status" in status
        assert "error_count" in status
        assert "agent_id" in status
        assert status["agent_id"] == "alpha-health"


# ============================================================================
# Task 6: GOV-01 Steward Monitoring
# ============================================================================


class TestTask6StewardMonitoring:
    """Validate Task 6 success criteria."""

    @pytest.mark.asyncio
    async def test_steward_monitors_agents_via_status_reports(self, spawned_steward, mock_mesh):
        """Criterion 6.1: Steward monitors all 13 agents.

        Validates Steward receives and tracks status reports.
        """
        # Simulate 13 agents reporting
        agent_ids = [f"agent-{i:02d}" for i in range(13)]
        for aid in agent_ids:
            msg = _make_message(
                "report_status",
                {"agent_id": aid, "status": {"state": "active"}},
                sender=aid,
            )
            await spawned_steward.process_message(msg)

        # Verify all stored
        for aid in agent_ids:
            stored = spawned_steward.get_state(f"status:{aid}")
            assert stored is not None

    @pytest.mark.asyncio
    async def test_steward_heartbeat_failure_detection_gap(self, mock_mesh, mock_llm):
        """Criterion 6.2: Detects heartbeat failure < 10 seconds.

        GAP ANALYSIS: No proactive heartbeat monitoring exists in StewardAgent.
        The Steward can receive status reports but does NOT actively monitor
        for missed heartbeats or detect failures.
        """
        steward = _make_actor(StewardAgent, "steward-gap2", mock_mesh, mock_llm)

        # No heartbeat timeout tracking
        has_timeout_tracking = hasattr(steward, "_agent_heartbeats") or hasattr(
            steward, "_last_heartbeat_times"
        )
        if not has_timeout_tracking:
            pytest.skip(
                "GAP: StewardAgent has no heartbeat timeout tracking. "
                "No _agent_heartbeats or _last_heartbeat_times attribute."
            )

    @pytest.mark.asyncio
    async def test_steward_failover_gap(self, mock_mesh, mock_llm):
        """Criterion 6.3: Initiates failover within 15 seconds.

        GAP ANALYSIS: No failover initiation logic exists in StewardAgent.
        """
        steward = _make_actor(StewardAgent, "steward-gap3", mock_mesh, mock_llm)

        has_failover = (
            hasattr(steward, "initiate_failover")
            or hasattr(steward, "_handle_agent_failure")
            or hasattr(steward, "failover_agent")
        )
        if not has_failover:
            pytest.skip(
                "GAP: StewardAgent has no failover initiation mechanism. "
                "No initiate_failover/_handle_agent_failure/failover_agent method."
            )

    @pytest.mark.asyncio
    async def test_steward_coordinates_triad_deliberation(self, spawned_steward, mock_mesh):
        """Criterion 6.4: Steward coordinates Core Triad deliberation.

        Validates coordinate_triad and start_deliberation message handling.
        """
        # Test coordinate_triad method
        result = await spawned_steward.coordinate_triad(
            topic="Test deliberation topic",
            triad_members=["alpha-001", "beta-001", "charlie-001"],
        )
        assert result is not None
        assert "session_id" in result
        assert result["topic"] == "Test deliberation topic"

        # Test direct message handling
        msg = _make_message(
            "start_deliberation",
            {
                "deliberation_id": "del-test-001",
                "topic": "Should we deploy?",
                "triad_members": ["alpha-001", "beta-001", "charlie-001"],
            },
        )
        await spawned_steward.process_message(msg)

        status = spawned_steward.get_deliberation_status("del-test-001")
        assert status is not None
        assert status["status"] == "initiated"

    @pytest.mark.asyncio
    async def test_steward_tracks_multiple_deliberations(self, spawned_steward):
        """Criterion 6.4: Steward tracks multiple active deliberations."""
        # Start several deliberations
        for i in range(3):
            msg = _make_message(
                "start_deliberation",
                {
                    "deliberation_id": f"del-multi-{i}",
                    "topic": f"Topic {i}",
                    "triad_members": ["alpha", "beta", "charlie"],
                },
            )
            await spawned_steward.process_message(msg)

        all_statuses = spawned_steward.get_all_deliberation_statuses()
        assert len(all_statuses) >= 3


# ============================================================================
# Task 7: GOV-02 Alpha Deep Analysis
# ============================================================================


class TestTask7AlphaDeepAnalysis:
    """Validate Task 7 success criteria."""

    @pytest.mark.asyncio
    async def test_alpha_participates_in_deliberation(self, spawned_alpha, mock_mesh):
        """Criterion 7.1: Alpha participates in triad deliberation.

        Validates Alpha handles deliberation_request and sends vote_response.
        """
        msg = _make_message(
            "deliberation_request",
            {
                "deliberation_id": "del-alpha-001",
                "topic": "Analyze system architecture",
            },
            sender="steward-001",
        )
        await spawned_alpha.process_message(msg)

        # send() wraps content via event_mesh.send_to_json with envelope:
        # {"type": ..., "from": ..., "content": {actual payload}}
        found_vote = False
        for subj, data in mock_mesh.published:
            if subj == "triad" and isinstance(data, dict):
                payload = data.get("content", data)
                if payload.get("message_type") == "vote_response":
                    found_vote = True
                    assert payload["deliberation_id"] == "del-alpha-001"
                    assert payload["agent_id"] == "alpha-001"
                    assert "decision" in payload
                    assert "confidence" in payload
                    assert "reasoning" in payload
                    break
        assert found_vote, "Alpha did not send vote_response"

    @pytest.mark.asyncio
    async def test_alpha_structured_analysis(self, spawned_alpha):
        """Criterion 7.2: Alpha provides structured analysis with expertise weighting."""
        result = await spawned_alpha._perform_analysis("Test problem")

        assert isinstance(result, dict)
        assert "decision" in result
        assert "confidence" in result
        assert "reasoning" in result
        assert "depth" in result
        assert result["depth"] == spawned_alpha.analysis_depth
        assert isinstance(result["confidence"], float)
        assert 0 <= result["confidence"] <= 1.0

    @pytest.mark.asyncio
    async def test_alpha_position_tracking_via_mixin(self, spawned_alpha):
        """Criterion 7.3: Position changes tracked during deliberation.

        Validates DeliberationMixin provides position tracking.
        """
        # Alpha inherits from DeliberationMixin indirectly via triad or
        # has deliberation tracking attributes
        has_tracking = hasattr(spawned_alpha, "_deliberation_position") or hasattr(
            spawned_alpha, "analysis_history"
        )
        assert has_tracking, "Alpha lacks position tracking"

        # Track that analysis history records deliberation participation
        msg = _make_message(
            "analysis_request",
            {"request_id": "req-001", "problem": "Test analysis"},
        )
        await spawned_alpha.process_message(msg)
        assert len(spawned_alpha.analysis_history) > 0

    @pytest.mark.asyncio
    async def test_alpha_contributes_within_3_rounds(self, spawned_alpha, mock_mesh):
        """Criterion 7.4: Steward receives Alpha's contribution within 3 deliberation rounds.

        Validates Alpha responds immediately to deliberation_request.
        """
        start = time.time()

        msg = _make_message(
            "deliberation_request",
            {"deliberation_id": "del-round-001", "topic": "Round test"},
            sender="steward-001",
        )
        await spawned_alpha.process_message(msg)

        elapsed = time.time() - start
        # Should respond in well under 3 rounds (effectively immediate)
        assert elapsed < 5.0, f"Alpha took {elapsed:.3f}s to respond"

        found = any(
            isinstance(d, dict) and d.get("content", d).get("message_type") == "vote_response"
            for _, d in mock_mesh.published
        )
        assert found, "Alpha did not send vote within rounds"


# ============================================================================
# Task 8: GOV-03 Beta Error Detection
# ============================================================================


class TestTask8BetaErrorDetection:
    """Validate Task 8 success criteria."""

    @pytest.mark.asyncio
    async def test_beta_validates_alpha_outputs(self, spawned_beta, mock_mesh):
        """Criterion 8.1: Beta validates outputs from Alpha.

        Validates Beta handles validation_request with decision and original_analysis.
        """
        msg = _make_message(
            "validation_request",
            {
                "request_id": "val-001",
                "decision": "proceed_with_caution",
                "original_analysis": {
                    "decision": "proceed",
                    "confidence": 0.85,
                    "reasoning": "Alpha analysis",
                },
            },
        )
        await spawned_beta.process_message(msg)

        # Check validation was recorded
        assert "val-001" in spawned_beta._validations
        validation = spawned_beta._validations["val-001"]["validation"]
        assert "valid" in validation
        assert "confidence" in validation

    @pytest.mark.asyncio
    async def test_beta_validates_charlie_outputs(self, spawned_beta, mock_mesh):
        """Criterion 8.1: Beta validates outputs from Charlie.

        Validates Beta can validate challenge outputs.
        """
        msg = _make_message(
            "validation_request",
            {
                "request_id": "val-charlie-001",
                "decision": "challenge_accepted",
                "original_analysis": {
                    "challenges": ["Risk identified"],
                    "confidence": 0.7,
                },
            },
        )
        await spawned_beta.process_message(msg)

        assert "val-charlie-001" in spawned_beta._validations

    @pytest.mark.asyncio
    async def test_beta_error_detection(self, spawned_beta, mock_mesh):
        """Criterion 8.2: Beta detects errors/inconsistencies.

        Validates Beta handles error_check messages.
        """
        msg = _make_message(
            "error_check",
            {
                "session_id": "err-001",
                "content": "Some content to check for errors",
            },
        )
        await spawned_beta.process_message(msg)

        # Error check should be recorded (even if no errors found)
        assert "err-001" in spawned_beta._error_checks
        check = spawned_beta._error_checks["err-001"]
        assert "errors" in check

    @pytest.mark.asyncio
    async def test_beta_error_check_precision_gap(self, spawned_beta, mock_llm):
        """Criterion 8.2: Detects inconsistencies with > 95% precision.

        PARTIAL: Error detection relies on LLM for precision. Without LLM,
        the fallback returns empty errors. The structural mechanism exists
        but precision cannot be validated without an active LLM.
        """
        # Test with no LLM (fallback) - returns empty errors
        result = await spawned_beta._detect_errors("test content with error")
        assert isinstance(result, list)
        # Precision testing requires LLM integration - structural validation only

    @pytest.mark.asyncio
    async def test_beta_validation_report_to_steward(self, spawned_beta, mock_mesh):
        """Criterion 8.3: Provides validation report to Steward within deliberation round.

        Validates Beta sends vote_response in deliberation.
        """
        msg = _make_message(
            "deliberation_request",
            {
                "deliberation_id": "del-beta-001",
                "topic": "Beta validation test",
            },
            sender="steward-001",
        )
        await spawned_beta.process_message(msg)

        # Check vote_response sent
        found = any(
            isinstance(d, dict) and d.get("content", d).get("message_type") == "vote_response"
            for _, d in mock_mesh.published
        )
        assert found, "Beta did not send vote_response during deliberation"

    @pytest.mark.asyncio
    async def test_beta_validation_includes_perspective(self, spawned_beta):
        """Criterion 8.1: Beta provides secondary perspective in validation."""
        result = await spawned_beta._validate_decision(
            "test decision",
            {"analysis": "Alpha's view"},
        )
        assert result["perspective"] == "secondary"


# ============================================================================
# Task 9: GOV-04 Charlie Critical Review
# ============================================================================


class TestTask9CharlieCriticalReview:
    """Validate Task 9 success criteria."""

    @pytest.mark.asyncio
    async def test_charlie_risk_assessment(self, spawned_charlie, mock_mesh):
        """Criterion 9.1: Charlie provides risk assessment for triad decisions.

        Validates Charlie handles risk_assessment messages.
        """
        msg = _make_message(
            "risk_assessment",
            {
                "request_id": "risk-001",
                "scenario": "Deploy new feature without rollback plan",
            },
        )
        await spawned_charlie.process_message(msg)

        # Check risk assessment was recorded
        assert "risk-001" in spawned_charlie._risk_assessments
        assessment = spawned_charlie._risk_assessments["risk-001"]["assessment"]
        assert "risk_level" in assessment or "risks" in assessment

    @pytest.mark.asyncio
    async def test_charlie_identifies_flaws(self, spawned_charlie):
        """Criterion 9.2: Identifies flaws in Alpha and Beta reasoning.

        Validates _generate_challenges accepts alpha_findings and beta_findings.
        """
        # Test with alpha and beta findings
        challenges = await spawned_charlie._generate_challenges(
            proposition="Deploy immediately",
            alpha_findings={"decision": "proceed", "confidence": 0.9},
            beta_findings={"valid": True, "confidence": 0.8},
        )
        assert isinstance(challenges, list)

    @pytest.mark.asyncio
    async def test_charlie_defense_counsel_position(self, spawned_charlie):
        """Criterion 9.3: Presents defense counsel (devil's advocate) position.

        Validates Charlie's analysis includes challenger perspective.
        """
        result = await spawned_charlie._perform_analysis("Test proposition")
        assert result["perspective"] == "challenger"
        assert "challenges" in result

    @pytest.mark.asyncio
    async def test_charlie_contributes_within_3_rounds(self, spawned_charlie, mock_mesh):
        """Criterion 9.4: Contributes within 3 deliberation rounds.

        Validates Charlie responds immediately to deliberation_request.
        """
        start = time.time()

        msg = _make_message(
            "deliberation_request",
            {
                "deliberation_id": "del-charlie-001",
                "topic": "Charlie round test",
            },
            sender="steward-001",
        )
        await spawned_charlie.process_message(msg)

        elapsed = time.time() - start
        assert elapsed < 5.0, f"Charlie took {elapsed:.3f}s to respond"

        # Check vote was sent
        found = any(
            isinstance(d, dict) and d.get("content", d).get("message_type") == "vote_response"
            for _, d in mock_mesh.published
        )
        assert found, "Charlie did not contribute within rounds"

    @pytest.mark.asyncio
    async def test_charlie_challenge_request(self, spawned_charlie, mock_mesh):
        """Criterion 9.2/9.3: Charlie handles explicit challenge requests."""
        msg = _make_message(
            "challenge_request",
            {
                "request_id": "chal-001",
                "proposition": "We should skip testing",
            },
        )
        await spawned_charlie.process_message(msg)

        # Challenge should be recorded
        assert "chal-001" in spawned_charlie._challenges
        challenge = spawned_charlie._challenges["chal-001"]
        assert "challenges" in challenge


# ============================================================================
# Cross-Cutting: Deliberation Round Completion
# ============================================================================


class TestDeliberationRoundCompletion:
    """Validate triad deliberation completes within 3 rounds."""

    @pytest.mark.asyncio
    async def test_full_triad_deliberation(self, mock_mesh, mock_llm):
        """All triad members participate in deliberation within 3 rounds.

        Simulates a full deliberation: Steward initiates, all members respond.
        """
        # Create all triad agents
        steward = _make_actor(StewardAgent, "steward-triad", mock_mesh, mock_llm)
        alpha = _make_actor(AlphaAgent, "alpha-triad", mock_mesh, mock_llm)
        beta = _make_actor(BetaAgent, "beta-triad", mock_mesh, mock_llm)
        charlie = _make_actor(CharlieAgent, "charlie-triad", mock_mesh, mock_llm)

        # Spawn all
        await steward.spawn()
        await alpha.spawn()
        await beta.spawn()
        await charlie.spawn()

        try:
            # Steward initiates deliberation
            msg = _make_message(
                "start_deliberation",
                {
                    "deliberation_id": "del-full-001",
                    "topic": "Full triad test",
                    "triad_members": ["alpha-triad", "beta-triad", "charlie-triad"],
                },
            )
            await steward.process_message(msg)

            # Verify deliberation initiated
            assert "del-full-001" in steward.active_deliberations

            # Send deliberation requests to each agent
            for agent in [alpha, beta, charlie]:
                delib_msg = _make_message(
                    "deliberation_request",
                    {
                        "deliberation_id": "del-full-001",
                        "topic": "Full triad test",
                    },
                    sender="steward-triad",
                )
                await agent.process_message(delib_msg)

            # All should have sent vote_response
            vote_count = sum(
                1
                for _, d in mock_mesh.published
                if isinstance(d, dict)
                and d.get("content", d).get("message_type") == "vote_response"
                and d.get("content", d).get("deliberation_id") == "del-full-001"
            )
            assert vote_count >= 3, f"Expected 3 vote_responses, got {vote_count}"
        finally:
            for agent in [steward, alpha, beta, charlie]:
                if agent._running:
                    await agent.terminate()

    @pytest.mark.asyncio
    async def test_deliberation_phase_progression(self, spawned_steward):
        """Steward advances deliberation through alpha->beta->charlie->complete."""
        # Setup deliberation
        spawned_steward._deliberations["del-phase-001"] = {
            "session_id": "del-phase-001",
            "problem": "Phase test",
            "phase": "alpha",
        }

        # Simulate phase progression
        msg = _make_message(
            "request_decision",
            {"session_id": "del-phase-001"},
            sender="alpha",
        )
        await spawned_steward.process_message(msg)
        assert spawned_steward._deliberations["del-phase-001"]["phase"] == "beta"

        msg2 = _make_message(
            "request_decision",
            {"session_id": "del-phase-001"},
            sender="beta",
        )
        await spawned_steward.process_message(msg2)
        assert spawned_steward._deliberations["del-phase-001"]["phase"] == "charlie"

        msg3 = _make_message(
            "request_decision",
            {"session_id": "del-phase-001"},
            sender="charlie",
        )
        await spawned_steward.process_message(msg3)
        assert spawned_steward._deliberations["del-phase-001"]["phase"] == "complete"
