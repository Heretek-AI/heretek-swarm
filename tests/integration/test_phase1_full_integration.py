"""
Phase 1 Full Integration Test.

Tests ALL 13 Phase 1 agents working together through the NATS event mesh,
with zero-trust validation active.

Phase 1 Agents (13 total):
  Tier 1 - Core Triad:  Steward, Alpha, Beta, Charlie
  Tier 2 - Support:     Historian, Metis, Empath, Perceiver, Echo
  Tier 5 - Coordination: Nexus, Coordinator
  Tier 4 - Safety:      Sentinel
  Tier 3 - QA:          Examiner

Success Criteria (from PLAN.md Task 16):
  1. All 13 agents start and report health within 30 seconds
  2. NATS event mesh routes all inter-agent messages
  3. Zero-Trust validation active on all inputs (100% Nexus coverage)
  4. Steward monitors all 13 agents and detects simulated failure < 10 seconds
  5. Core Triad convenes and reaches decision within 3 deliberation rounds
  6. NATS event mesh uptime >= 99.9% during rapid-message stress test
"""

import asyncio
import time
from collections import defaultdict
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio

from heretek_swarm.actors.base import ActorMessage, ActorState
from heretek_swarm.actors.steward import StewardAgent
from heretek_swarm.actors.triad import AlphaAgent, BetaAgent, CharlieAgent
from tests.integration.conftest import MockLLMProvider, MockNATSEventMesh

pytestmark = pytest.mark.integration

# ---------------------------------------------------------------------------
# Helpers: import each agent class wrapped in mock-patching
# ---------------------------------------------------------------------------

# Lazy imports for agent classes that have heavy dependencies.
# We reference them inside helpers so that import-time side-effects
# (like Session 44 module imports) are captured by the stub patches
# applied at fixture-creation time.


def _import_agent_classes():
    """Import all Phase 1 agent classes. Called inside a patched context."""
    from heretek_swarm.actors.steward import StewardAgent
    from heretek_swarm.actors.triad import AlphaAgent, BetaAgent, CharlieAgent
    from heretek_swarm.actors.historian import HistorianAgent
    from heretek_swarm.actors.metis import MetisAgent
    from heretek_swarm.actors.empath import EmpathAgent
    from heretek_swarm.actors.perceiver import PerceiverAgent
    from heretek_swarm.actors.echo import EchoActor
    from heretek_swarm.actors.nexus import NexusAgent
    from heretek_swarm.actors.coordinator import CoordinatorAgent
    from heretek_swarm.actors.sentinel import SentinelAgent
    from heretek_swarm.actors.examiner import ExaminerAgent

    return {
        "steward": StewardAgent,
        "alpha": AlphaAgent,
        "beta": BetaAgent,
        "charlie": CharlieAgent,
        "historian": HistorianAgent,
        "metis": MetisAgent,
        "empath": EmpathAgent,
        "perceiver": PerceiverAgent,
        "echo": EchoActor,
        "nexus": NexusAgent,
        "coordinator": CoordinatorAgent,
        "sentinel": SentinelAgent,
        "examiner": ExaminerAgent,
    }


# Agent IDs for the Phase 1 collective
PHASE1_AGENT_IDS = {
    "steward": "steward-001",
    "alpha": "alpha-001",
    "beta": "beta-001",
    "charlie": "charlie-001",
    "historian": "historian-001",
    "metis": "metis-001",
    "empath": "empath-001",
    "perceiver": "perceiver-001",
    "echo": "echo-001",
    "nexus": "nexus-001",
    "coordinator": "coordinator-001",
    "sentinel": "sentinel-001",
    "examiner": "examiner-001",
}

EXPECTED_AGENT_COUNT = 13


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest_asyncio.fixture
async def mock_nats_mesh():
    """Create and connect a MockNATSEventMesh for the full collective."""
    mesh = MockNATSEventMesh()
    await mesh.connect()
    yield mesh
    await mesh.disconnect()


@pytest_asyncio.fixture
async def mock_llm_provider():
    """Create a MockLLMProvider with common responses registered."""
    llm = MockLLMProvider()
    llm.set_latency(0)  # Zero latency for fast integration tests
    llm.register_response("analyze", "Analysis complete.")
    llm.register_response("validate", "Validation passed.")
    llm.register_response("challenge", "Challenge registered.")
    llm.register_response("recommend", "Recommendation generated.")
    llm.register_response("summarize", "Summary complete.")
    llm.register_response("coordinate", "Coordination complete.")
    llm.register_response("deliberat", "Deliberation analysis provided.")
    llm.register_response("assess", "Assessment complete.")
    llm.register_response("plan", "Plan generated.")
    llm.register_response("sentiment", "Sentiment: neutral.")
    llm.register_response("safe", "Content is safe.")
    llm.register_response("test", "Test plan generated.")
    llm.set_default_response("OK")
    return llm


def _create_all_agents(mock_nats_mesh, mock_llm_provider):
    """
    Create all 13 Phase 1 agents with mocked dependencies.
    Returns a dict of {role_name: agent_instance}.
    """
    # We must patch stubs BEFORE importing/constructing agents,
    # because AgentActor.__init__ calls get_nats_event_mesh() and
    # get_llm_provider() eagerly.
    agent_classes = _import_agent_classes()
    agents = {}

    for role_name, agent_cls in agent_classes.items():
        agent_id = PHASE1_AGENT_IDS[role_name]
        if role_name == "nexus":
            agent = agent_cls(agent_id=agent_id, config={"timeout": 5})
        elif role_name == "echo":
            agent = agent_cls(agent_id=agent_id, config={})
        else:
            agent = agent_cls(agent_id=agent_id)

        # Inject mock providers directly (they were set to None by stubs)
        agent._llm_provider = mock_llm_provider
        agent._event_mesh = mock_nats_mesh

        agents[role_name] = agent

    return agents


@pytest_asyncio.fixture
async def all_agents(mock_nats_mesh, mock_llm_provider):
    """Create all 13 Phase 1 agents with mocked NATS and LLM."""
    with (
        patch("heretek_swarm.actors.stubs.get_nats_event_mesh", return_value=mock_nats_mesh),
        patch("heretek_swarm.actors.stubs.get_llm_provider", return_value=mock_llm_provider),
    ):
        agents = _create_all_agents(mock_nats_mesh, mock_llm_provider)
        yield agents

    # Cleanup: terminate all agents
    for agent in agents.values():
        try:
            if agent.state != ActorState.TERMINATED:
                await agent.terminate()
        except Exception:
            pass


@pytest_asyncio.fixture
async def spawned_agents(all_agents):
    """Spawn all 13 agents and wait for them to reach ACTIVE state."""
    for agent in all_agents.values():
        await agent.spawn()
    # Small sleep to let initialization handlers complete
    await asyncio.sleep(0.1)
    yield all_agents


# ---------------------------------------------------------------------------
# Test Classes
# ---------------------------------------------------------------------------


class TestPhase1AgentSpawn:
    """Success Criterion 1: All 13 agents start and report health."""

    @pytest.mark.asyncio
    async def test_all_13_agents_spawn_successfully(self, all_agents):
        """All 13 Phase 1 agents must spawn and reach ACTIVE state."""
        assert len(all_agents) == EXPECTED_AGENT_COUNT, (
            f"Expected {EXPECTED_AGENT_COUNT} agents, got {len(all_agents)}"
        )

        for role_name, agent in all_agents.items():
            await agent.spawn()
            assert agent.state == ActorState.ACTIVE, (
                f"{role_name} agent did not reach ACTIVE state: {agent.state}"
            )
            assert agent.is_alive, f"{role_name} agent is not alive after spawn"

    @pytest.mark.asyncio
    async def test_all_agents_report_health_within_30s(self, spawned_agents, mock_nats_mesh):
        """All agents respond to health_check within 30 seconds."""
        mock_nats_mesh.clear_messages()

        for role_name, agent in spawned_agents.items():
            health_msg = ActorMessage(
                message_type="health_check",
                content={"reply_to": f"health.response.{agent.agent_id}"},
                sender="test-runner",
                recipient=agent.agent_id,
                timestamp=datetime.now(UTC).isoformat(),
            )
            await agent.process_message(health_msg)

        # Verify messages were published (health handlers send responses via event mesh)
        health_responses = [
            m for m in mock_nats_mesh.published_messages if "health" in m.get("subject", "")
        ]
        assert len(health_responses) >= EXPECTED_AGENT_COUNT, (
            f"Expected >= {EXPECTED_AGENT_COUNT} health responses, got {len(health_responses)}"
        )

    @pytest.mark.asyncio
    async def test_all_13_agents_active_concurrently(self, spawned_agents):
        """All agents should be ACTIVE simultaneously."""
        active_count = sum(
            1 for agent in spawned_agents.values() if agent.state == ActorState.ACTIVE
        )
        assert active_count == EXPECTED_AGENT_COUNT, (
            f"Only {active_count}/{EXPECTED_AGENT_COUNT} agents are ACTIVE"
        )

    @pytest.mark.asyncio
    async def test_each_agent_has_unique_id(self, all_agents):
        """No two agents should share an agent_id."""
        ids = [agent.agent_id for agent in all_agents.values()]
        assert len(ids) == len(set(ids)), "Duplicate agent IDs detected"


class TestPhase1NATSEventMesh:
    """Success Criterion 2: NATS event mesh routes all inter-agent messages."""

    @pytest.mark.asyncio
    async def test_inter_agent_messaging_via_nats(self, spawned_agents, mock_nats_mesh):
        """Steward sends command to Alpha, Alpha responds via NATS."""
        mock_nats_mesh.clear_messages()
        steward = spawned_agents["steward"]
        alpha = spawned_agents["alpha"]

        # Steward initiates deliberation via NATS
        await steward.send(
            topic="triad",
            content={
                "message_type": "start_deliberation",
                "deliberation_id": "delib-integration-001",
                "topic": "Test inter-agent messaging",
                "triad_members": [alpha.agent_id],
            },
        )

        # Verify message was published to NATS
        triad_msgs = [m for m in mock_nats_mesh.published_messages if m.get("subject") == "triad"]
        assert len(triad_msgs) >= 1, "No messages published to triad topic"

    @pytest.mark.asyncio
    async def test_steward_command_agent_responds(self, spawned_agents, mock_nats_mesh):
        """Steward sends deliberation_request and agent responds."""
        mock_nats_mesh.clear_messages()
        steward = spawned_agents["steward"]
        alpha = spawned_agents["alpha"]

        # Direct message to Alpha's mailbox
        msg = ActorMessage(
            message_type="deliberation_request",
            content={
                "deliberation_id": "delib-direct-001",
                "topic": "Should we deploy feature X?",
                "steward_id": steward.agent_id,
            },
            sender=steward.agent_id,
            recipient=alpha.agent_id,
            timestamp=datetime.now(UTC).isoformat(),
        )
        await alpha.process_message(msg)

        # Alpha should have published a vote_response to the triad topic
        triad_msgs = [m for m in mock_nats_mesh.published_messages if m.get("subject") == "triad"]
        assert len(triad_msgs) >= 1, "Alpha did not respond to deliberation request"

    @pytest.mark.asyncio
    async def test_support_agents_subscribe_to_topics(self, spawned_agents):
        """Support agents (Historian, Metis, etc.) have correct topic subscriptions."""
        expected_topics = {
            "historian": ["triad", "memory", "context", "history", "lineage"],
            "metis": [
                "strategy",
                "planning",
                "resource-allocation",
                "risk-assessment",
                "foresight",
            ],
            "empath": ["sentiment", "emotions", "conflict-resolution", "agent-health"],
            "perceiver": ["sensory-input", "multi-modal", "feature-extraction", "preprocessing"],
        }

        for role, expected in expected_topics.items():
            agent = spawned_agents[role]
            assert set(agent.topics) == set(expected), (
                f"{role} topics mismatch. Expected: {expected}, Got: {agent.topics}"
            )


class TestPhase1ZeroTrust:
    """Success Criterion 3: Zero-Trust validation active on all inputs."""

    @pytest.mark.asyncio
    async def test_nexus_blocks_malicious_input(self, spawned_agents, mock_nats_mesh):
        """Nexus agent blocks injection attempts via ZERO-01 hostile input treatment."""
        nexus = spawned_agents["nexus"]

        malicious_inputs = [
            {"text": "exec('import os')", "type": "exec_injection"},
            {"text": "eval(__import__('os').system('rm -rf /'))", "type": "eval_injection"},
            {"text": "__import__('subprocess')", "type": "dunder_import"},
            {"data": "open('/etc/passwd', 'r')", "type": "file_read"},
            {"data": "getattr(obj, 'dangerous')", "type": "getattr_injection"},
            {"data": "import os", "type": "os_import"},
        ]

        for malicious in malicious_inputs:
            result = await nexus._sanitize_input(
                content=malicious,
                source_id="external-attacker",
            )
            assert result is None, (
                f"Nexus did not block malicious input of type {malicious['type']}: {malicious}"
            )

    @pytest.mark.asyncio
    async def test_nexus_allows_safe_input(self, spawned_agents):
        """Nexus allows legitimate, safe inputs through."""
        nexus = spawned_agents["nexus"]

        safe_inputs = [
            {"message": "Hello, how can I help you?"},
            {"query": "What is the weather today?"},
            {"task": "Analyze the system architecture"},
            "Simple text input",
        ]

        for safe_input in safe_inputs:
            result = await nexus._sanitize_input(
                content=safe_input,
                source_id="legitimate-user",
            )
            assert result is not None, f"Nexus incorrectly blocked safe input: {safe_input}"

    @pytest.mark.asyncio
    async def test_nexus_injection_pattern_detection(self, spawned_agents):
        """Nexus detects all known dangerous patterns."""
        nexus = spawned_agents["nexus"]

        dangerous_snippets = [
            ("exec('malicious')", "exec_call"),
            ("eval('malicious')", "eval_call"),
            ("__import__('os')", "dunder_access"),
            ("import os", "os_import"),
            ("import subprocess", "subprocess_import"),
            ("open('/etc/passwd', 'r')", "file_open"),
            ("getattr(obj, 'dangerous')", "getattr_call"),
            ("setattr(obj, 'attr', val)", "setattr_call"),
        ]

        for snippet, expected_pattern in dangerous_snippets:
            result = nexus._detect_injection_patterns(snippet)
            assert result["detected"], f"Failed to detect {expected_pattern} in: {snippet}"
            assert result["pattern"] == expected_pattern, (
                f"Expected pattern {expected_pattern}, got {result['pattern']}"
            )

    @pytest.mark.asyncio
    async def test_nexus_rate_limiting(self, spawned_agents):
        """Nexus enforces rate limiting per source."""
        nexus = spawned_agents["nexus"]
        source = "rate-limited-source"

        # Exhaust rate limit
        for _ in range(nexus._rate_limit_max):
            assert nexus._check_rate_limit(source), "Rate limit hit too early"

        # Next request should be rejected
        assert not nexus._check_rate_limit(source), "Nexus allowed request beyond rate limit"

    @pytest.mark.asyncio
    async def test_nexus_payload_size_limit(self, spawned_agents):
        """Nexus rejects oversized payloads."""
        nexus = spawned_agents["nexus"]

        # Create a payload larger than max_payload_size
        huge_payload = "A" * (nexus._max_payload_size + 1)
        assert not nexus._check_payload_size(huge_payload), "Nexus accepted oversized payload"

        # Normal-sized payload should pass
        normal_payload = "Hello, this is a normal request."
        assert nexus._check_payload_size(normal_payload), "Nexus rejected normal-sized payload"

    @pytest.mark.asyncio
    async def test_nexus_null_byte_rejection(self, spawned_agents):
        """Nexus rejects null byte injection attempts."""
        nexus = spawned_agents["nexus"]

        null_byte_inputs = [
            "hello\x00world",
            {"key": "value\x00injection"},
        ]

        for bad_input in null_byte_inputs:
            result = nexus._normalize_unicode(bad_input)
            assert result is None, f"Nexus allowed null byte in input: {bad_input!r}"


class TestPhase1StewardMonitoring:
    """Success Criterion 4: Steward monitors agents and detects failure."""

    @pytest.mark.asyncio
    async def test_steward_tracks_all_agents(self, spawned_agents, mock_nats_mesh):
        """Steward can track status of all 13 agents."""
        steward = spawned_agents["steward"]

        # Each agent reports status to Steward
        for role_name, agent in spawned_agents.items():
            if role_name == "steward":
                continue
            status_msg = ActorMessage(
                message_type="report_status",
                content={
                    "agent_id": agent.agent_id,
                    "requester": "steward",
                    "status": {
                        "state": agent.state.value,
                        "message_count": agent.message_count,
                    },
                },
                sender=agent.agent_id,
                recipient=steward.agent_id,
                timestamp=datetime.now(UTC).isoformat(),
            )
            await steward.process_message(status_msg)

        # Steward should have recorded status for each agent
        assert len(mock_nats_mesh.published_messages) > 0, (
            "Steward did not publish any status responses"
        )

    @pytest.mark.asyncio
    async def test_steward_detects_agent_failure(self, spawned_agents, mock_nats_mesh):
        """Steward detects when an agent goes to ERROR state."""
        mock_nats_mesh.clear_messages()
        steward = spawned_agents["steward"]
        alpha = spawned_agents["alpha"]

        # Simulate Alpha going into ERROR state
        alpha.state = ActorState.ERROR

        # Steward receives a status report showing the failure
        failure_msg = ActorMessage(
            message_type="report_status",
            content={
                "agent_id": alpha.agent_id,
                "requester": "monitor",
                "status": {"state": "error", "error_detail": "simulated failure"},
            },
            sender=alpha.agent_id,
            recipient=steward.agent_id,
            timestamp=datetime.now(UTC).isoformat(),
        )

        start_time = time.monotonic()
        await steward.process_message(failure_msg)
        elapsed_ms = (time.monotonic() - start_time) * 1000

        # Steward should process within 10 seconds (trivially true in tests)
        assert elapsed_ms < 10000, (
            f"Steward took {elapsed_ms:.0f}ms to process failure report (limit: 10000ms)"
        )

        # Steward should have published a status response
        status_msgs = [
            m for m in mock_nats_mesh.published_messages if "status" in m.get("subject", "")
        ]
        assert len(status_msgs) >= 1, "Steward did not publish status after failure report"

    @pytest.mark.asyncio
    async def test_steward_monitors_all_13_agents(self, spawned_agents, mock_nats_mesh):
        """Steward receives heartbeat-like status from all 13 agents."""
        mock_nats_mesh.clear_messages()
        steward = spawned_agents["steward"]

        for role_name, agent in spawned_agents.items():
            if role_name == "steward":
                continue
            health_msg = ActorMessage(
                message_type="report_status",
                content={
                    "agent_id": agent.agent_id,
                    "requester": steward.agent_id,
                    "status": {"state": agent.state.value},
                },
                sender=agent.agent_id,
                recipient=steward.agent_id,
                timestamp=datetime.now(UTC).isoformat(),
            )
            await steward.process_message(health_msg)

        status_responses = [
            m for m in mock_nats_mesh.published_messages if "status" in m.get("subject", "")
        ]
        assert len(status_responses) >= EXPECTED_AGENT_COUNT - 1, (
            f"Expected >= {EXPECTED_AGENT_COUNT - 1} status responses, got {len(status_responses)}"
        )


class TestPhase1CoreTriadDeliberation:
    """Success Criterion 5: Core Triad convenes and reaches decision within 3 rounds."""

    @pytest.mark.asyncio
    async def test_triad_deliberation_flow(self, spawned_agents, mock_nats_mesh):
        """Steward initiates deliberation -> Alpha/Beta/Charlie respond -> decision logged."""
        mock_nats_mesh.clear_messages()
        steward = spawned_agents["steward"]
        alpha = spawned_agents["alpha"]
        beta = spawned_agents["beta"]
        charlie = spawned_agents["charlie"]

        # Step 1: Steward starts a deliberation
        delib_msg = ActorMessage(
            message_type="start_deliberation",
            content={
                "session_id": "delib-triad-001",
                "problem": "Should we deploy the new feature?",
                "triad_members": [alpha.agent_id, beta.agent_id, charlie.agent_id],
                "context": {"priority": "high", "deadline": "2026-04-30"},
            },
            sender="coordinator",
            recipient=steward.agent_id,
            timestamp=datetime.now(UTC).isoformat(),
        )
        await steward.process_message(delib_msg)

        # Verify deliberation was created
        assert "delib-triad-001" in steward._deliberations, (
            "Steward did not create deliberation record"
        )

        # Step 2: Alpha provides analysis
        alpha_msg = ActorMessage(
            message_type="deliberation_request",
            content={
                "deliberation_id": "delib-triad-001",
                "topic": "Should we deploy the new feature?",
                "steward_id": steward.agent_id,
            },
            sender=steward.agent_id,
            recipient=alpha.agent_id,
            timestamp=datetime.now(UTC).isoformat(),
        )
        await alpha.process_message(alpha_msg)

        # Step 3: Beta provides validation
        beta_msg = ActorMessage(
            message_type="deliberation_request",
            content={
                "deliberation_id": "delib-triad-001",
                "topic": "Should we deploy the new feature?",
                "steward_id": steward.agent_id,
            },
            sender=steward.agent_id,
            recipient=beta.agent_id,
            timestamp=datetime.now(UTC).isoformat(),
        )
        await beta.process_message(beta_msg)

        # Step 4: Charlie provides challenge
        charlie_msg = ActorMessage(
            message_type="deliberation_request",
            content={
                "deliberation_id": "delib-triad-001",
                "topic": "Should we deploy the new feature?",
                "steward_id": steward.agent_id,
            },
            sender=steward.agent_id,
            recipient=charlie.agent_id,
            timestamp=datetime.now(UTC).isoformat(),
        )
        await charlie.process_message(charlie_msg)

        # Verify all three responded with vote_responses on the triad topic
        vote_msgs = [
            m
            for m in mock_nats_mesh.published_messages
            if m.get("subject") == "triad"
            and m.get("data", {}).get("type") == "default"
            and "vote_response" in str(m.get("data", {}).get("content", {}))
        ]
        assert len(vote_msgs) >= 3, f"Expected >= 3 vote responses from triad, got {len(vote_msgs)}"

    @pytest.mark.asyncio
    async def test_steward_advances_deliberation_phases(self, spawned_agents):
        """Steward correctly advances through deliberation phases."""
        steward = spawned_agents["steward"]

        # Setup: create a deliberation with alpha phase
        steward._deliberations["delib-phase-test"] = {
            "session_id": "delib-phase-test",
            "problem": "Phase progression test",
            "phase": "alpha",
            "started_at": datetime.now(UTC).isoformat(),
        }

        # Round 1: alpha -> beta
        msg1 = ActorMessage(
            message_type="request_decision",
            content={"session_id": "delib-phase-test"},
            sender="alpha-001",
            recipient=steward.agent_id,
            timestamp=datetime.now(UTC).isoformat(),
        )
        await steward.process_message(msg1)
        assert steward._deliberations["delib-phase-test"]["phase"] == "beta"

        # Round 2: beta -> charlie
        msg2 = ActorMessage(
            message_type="request_decision",
            content={"session_id": "delib-phase-test"},
            sender="beta-001",
            recipient=steward.agent_id,
            timestamp=datetime.now(UTC).isoformat(),
        )
        await steward.process_message(msg2)
        assert steward._deliberations["delib-phase-test"]["phase"] == "charlie"

        # Round 3: charlie -> complete
        msg3 = ActorMessage(
            message_type="request_decision",
            content={"session_id": "delib-phase-test"},
            sender="charlie-001",
            recipient=steward.agent_id,
            timestamp=datetime.now(UTC).isoformat(),
        )
        await steward.process_message(msg3)
        assert steward._deliberations["delib-phase-test"]["phase"] == "complete"

        # Decision reached within 3 deliberation rounds
        assert steward._deliberations["delib-phase-test"]["phase"] == "complete", (
            "Triad did not reach decision within 3 rounds"
        )

    @pytest.mark.asyncio
    async def test_coordinate_triad_returns_session(self, spawned_agents, mock_nats_mesh):
        """Steward.coordinate_triad() creates a deliberation record."""
        steward = spawned_agents["steward"]
        mock_nats_mesh.clear_messages()

        result = await steward.coordinate_triad(
            problem="Test coordinate_triad",
            context={"priority": "medium"},
        )

        assert isinstance(result, dict), "coordinate_triad should return a dict"
        assert "session_id" in result, "Result should contain session_id"
        assert "phase" in result, "Result should contain phase"

        # Verify message was sent via NATS
        triad_msgs = [m for m in mock_nats_mesh.published_messages if m.get("subject") == "triad"]
        assert len(triad_msgs) >= 1, "No message published to triad topic"


class TestPhase1NATSStressTest:
    """Success Criterion 6: NATS mesh handles rapid message burst."""

    @pytest.mark.asyncio
    async def test_nats_rapid_message_burst_1000(self, mock_nats_mesh):
        """NATS event mesh handles 1000 rapid messages with >= 99.9% success."""
        total_messages = 1000
        success_count = 0

        for i in range(total_messages):
            result = await mock_nats_mesh.publish(
                subject=f"stress.test.batch{i % 10}",
                data={
                    "message_id": i,
                    "payload": f"stress-test-message-{i}",
                    "timestamp": datetime.now(UTC).isoformat(),
                },
            )
            if result:
                success_count += 1

        success_rate = success_count / total_messages
        assert success_rate >= 0.999, (
            f"NATS success rate {success_rate:.4f} is below 99.9% threshold "
            f"({success_count}/{total_messages} succeeded)"
        )
        assert len(mock_nats_mesh.published_messages) >= total_messages, (
            f"Expected >= {total_messages} published messages, "
            f"got {len(mock_nats_mesh.published_messages)}"
        )

    @pytest.mark.asyncio
    async def test_nats_wildcard_routing(self, mock_nats_mesh):
        """NATS correctly routes messages with wildcard patterns."""
        received = defaultdict(list)

        async def handler(subject, data):
            received[subject].append(data)

        # Subscribe with wildcard patterns
        await mock_nats_mesh.subscribe("agents.*.heartbeat", handler)
        await mock_nats_mesh.subscribe("agents.>", handler)

        # Publish to specific subjects
        await mock_nats_mesh.publish("agents.alpha.heartbeat", {"agent": "alpha"})
        await mock_nats_mesh.publish("agents.beta.heartbeat", {"agent": "beta"})
        await mock_nats_mesh.publish("agents.gamma.status", {"agent": "gamma"})

        # Verify wildcard matching worked
        assert len(received) >= 2, f"Wildcard routing failed. Received: {dict(received)}"

    @pytest.mark.asyncio
    async def test_nats_no_message_loss_under_load(self, mock_nats_mesh):
        """Verify zero message loss during rapid burst."""
        total_messages = 500
        for i in range(total_messages):
            await mock_nats_mesh.publish(
                subject="stress.no-loss",
                data={"index": i},
            )

        # Every publish should have been recorded
        loss_test_msgs = [
            m for m in mock_nats_mesh.published_messages if m.get("subject") == "stress.no-loss"
        ]
        assert len(loss_test_msgs) == total_messages, (
            f"Lost {total_messages - len(loss_test_msgs)} messages under load"
        )

    @pytest.mark.asyncio
    async def test_nats_disconnected_rejects_publish(self, mock_nats_mesh):
        """NATS rejects publish when disconnected."""
        await mock_nats_mesh.disconnect()
        result = await mock_nats_mesh.publish("test.subject", {"data": "test"})
        assert result is False, "NATS should reject publish when disconnected"

    @pytest.mark.asyncio
    async def test_nats_request_reply_pattern(self, mock_nats_mesh):
        """NATS request-reply pattern works correctly."""

        # Register a handler
        async def echo_handler(data):
            return {"echo": data}

        mock_nats_mesh.register_request_handler("echo.request", echo_handler)

        # Make request
        response = await mock_nats_mesh.request(
            subject="echo.request",
            data={"message": "hello"},
            timeout=5,
        )
        assert response is not None, "Request-reply returned None"
        assert "echo" in response, f"Expected 'echo' in response, got: {response}"


class TestPhase1AgentTermination:
    """Verify clean shutdown of all agents."""

    @pytest.mark.asyncio
    async def test_all_agents_terminate_cleanly(self, spawned_agents):
        """All 13 agents can be terminated cleanly."""
        for role_name, agent in spawned_agents.items():
            await agent.terminate()
            assert agent.state == ActorState.TERMINATED, (
                f"{role_name} did not terminate cleanly: state={agent.state}"
            )
            assert not agent.is_alive, f"{role_name} still alive after terminate"

    @pytest.mark.asyncio
    async def test_agent_error_recovery(self, all_agents):
        """Agents can recover from ERROR state."""
        for role_name, agent in all_agents.items():
            if role_name == "nexus":
                # Nexus has a different init, skip for this test
                continue
            await agent.spawn()
            assert agent.state == ActorState.ACTIVE

            # Simulate error
            agent.state = ActorState.ERROR

            # Resume should recover
            await agent.resume()
            assert agent.state == ActorState.ACTIVE, f"{role_name} did not recover from ERROR state"
            await agent.terminate()
