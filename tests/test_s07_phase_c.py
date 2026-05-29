"""
Phase C Verification Test Suite.

Covers:
1. Memory Scoping & Schema Alignment (PersistentMemory and Mem0Backend)
   - Store memories with Water's hierarchy metadata (org_id, project_id, session_id, scope).
   - Search memories with filter constraints and verify correct programmatic fallback filtering.
   - Synchronous initialization to prevent coroutine unawaited warnings.

2. NATS Debate State Integration (NATSDeliberationMesh)
   - Parse and validate DeliberationRequest, DeliberationBlockedPayload, DeliberationReviewingPayload, and DeliberationResolvedPayload.
   - Cycle through debate transitions (ACTIVE -> BLOCKED -> REVIEWING -> RESOLVED).
   - Subscription and message handling via StubEventMesh, audit trail logging, and state change broadcasting.

3. Cognitive Telemetry (PrometheusMetrics and LLM call instrumentation)
   - Record and verify heretek_swarm_llm_call_duration_seconds and heretek_swarm_llm_tokens_total.
   - Instrument run_with_llm to measure latency, calculate character-based fallback tokens, and record Prometheus metrics.
   - Verify that `/api/metrics` endpoint exposes these metrics in Prometheus exposition format.
"""

import asyncio
import time
from unittest.mock import MagicMock, patch
import pytest
from fastapi.testclient import TestClient

from heretek_swarm.memory.persistent import PersistentMemory, Mem0Backend, Mem0Config, MemoryResult
from heretek_swarm.memory.base import MemoryEntry, MemoryQuery
from heretek_swarm.consensus.deliberation_mesh import (
    NATSDeliberationMesh,
    HXADebateState,
    HXADebateCycle,
    DeliberationBlockedPayload,
    DeliberationReviewingPayload,
    DeliberationResolvedPayload,
)
from heretek_swarm.actors.validation import DeliberationRequest
from heretek_swarm.consensus.audit_trail import ConsensusAuditTrail
from heretek_swarm.observability.prometheus_metrics import (
    PrometheusMetrics,
    get_metrics,
    record_llm_call,
    record_llm_tokens,
    heretek_swarm_llm_call_duration_seconds,
    heretek_swarm_llm_tokens_total,
)
from heretek_swarm.actors.base.core import AgentActor, ActorMessage
from heretek_swarm.actors.stubs import StubEventMesh
from heretek_swarm.api.main import app
from heretek_swarm.gateway.auth import verify_auth


# ===========================================================================
# 1. Memory Scoping & Schema Alignment Tests
# ===========================================================================

@pytest.mark.unit
@pytest.mark.asyncio
async def test_persistent_memory_hierarchical_scoping():
    """Test PersistentMemory stores, searches, and programmatically filters memories with Water's hierarchy scopes."""
    mock_memory_client = MagicMock()
    mock_memory_client.add.return_value = {"id": "mem_123"}
    
    # Setup mock search results: one matching the filters, one mismatching to verify programmatic fallback
    mock_memory_client.search.return_value = [
        {
            "id": "mem_123",
            "content": "Episodic agent history details",
            "metadata": {
                "org_id": "org_cybernetic",
                "project_id": "proj_swarm",
                "session_id": "sess_omega",
                "scope": "session"
            }
        },
        {
            "id": "mem_456",
            "content": "Some other organization's record",
            "metadata": {
                "org_id": "org_different",
                "project_id": "proj_swarm",
                "session_id": "sess_omega",
                "scope": "session"
            }
        }
    ]

    with patch("mem0.Memory.from_config", return_value=mock_memory_client):
        config = Mem0Config(qdrant_host="localhost", openai_api_key="mock")
        pm = PersistentMemory(config=config, user_id="user_aleph")
        
        # Test store
        mem_id = await pm.store(
            content="Episodic agent history details",
            org_id="org_cybernetic",
            project_id="proj_swarm",
            session_id="sess_omega",
            scope="session"
        )
        assert mem_id == "mem_123"
        
        # Verify correct metadata was sent to mem0
        mock_memory_client.add.assert_called_once_with(
            "Episodic agent history details",
            user_id="user_aleph",
            metadata={
                "org_id": "org_cybernetic",
                "project_id": "proj_swarm",
                "session_id": "sess_omega",
                "scope": "session"
            }
        )

        # Test search with Water's hierarchy filter
        results = await pm.search(
            query="cybernetic",
            org_id="org_cybernetic",
            project_id="proj_swarm",
            session_id="sess_omega",
            scope="session"
        )
        
        # Verify raw search called with correct filters
        mock_memory_client.search.assert_called_once_with(
            query="cybernetic",
            user_id="user_aleph",
            limit=10,
            filters={
                "org_id": "org_cybernetic",
                "project_id": "proj_swarm",
                "session_id": "sess_omega",
                "scope": "session"
            }
        )
        
        # Verify programmatic fallback filtering stripped out the mismatching mem_456 (org_different)
        assert len(results) == 1
        assert results[0]["id"] == "mem_123"
        assert results[0]["metadata"]["org_id"] == "org_cybernetic"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_mem0_backend_hierarchical_scoping():
    """Test Mem0Backend correctly maps and filters Water's hierarchy scopes."""
    mock_memory_client = MagicMock()
    mock_memory_client.add.return_value = {"id": "mem_789"}
    mock_memory_client.search.return_value = [
        {
            "id": "mem_789",
            "content": "Water's hierarchy semantic store",
            "metadata": {
                "agent_id": "agent_alpha",
                "org_id": "org_cybernetic",
                "project_id": "proj_swarm",
                "session_id": "sess_omega",
                "scope": "session"
            }
        }
    ]

    with patch("mem0.Memory.from_config", return_value=mock_memory_client):
        config = Mem0Config(qdrant_host="localhost", openai_api_key="mock")
        backend = Mem0Backend(config=config)
        backend.initialize_sync()
        assert backend._initialized is True  # noqa: SLF001

        # Test store with MemoryEntry
        entry = MemoryEntry(
            content="Water's hierarchy semantic store",
            agent_id="agent_alpha",
            metadata={
                "org_id": "org_cybernetic",
                "project_id": "proj_swarm",
                "session_id": "sess_omega",
                "scope": "session"
            }
        )
        mem_id = await backend.store(entry)
        assert mem_id == "mem_789"

        # Test search with Water's hierarchy filters (using raw proxy API)
        res = backend.search(
            query="semantic",
            filters={
                "org_id": "org_cybernetic",
                "project_id": "proj_swarm",
                "session_id": "sess_omega",
                "scope": "session"
            }
        )
        assert isinstance(res, list)
        assert len(res) == 1
        assert res[0]["id"] == "mem_789"
        assert res[0]["metadata"]["org_id"] == "org_cybernetic"


# ===========================================================================
# 2. NATS Debate State Integration Tests
# ===========================================================================

@pytest.mark.unit
@pytest.mark.asyncio
async def test_nats_deliberation_mesh_debate_cycle():
    """Test NATSDeliberationMesh receives NATS topics, parses Pydantic payloads, manages HXADebateCycle transitions, and logs to audit trail."""
    mesh = StubEventMesh()
    audit_trail = MagicMock(spec=ConsensusAuditTrail)
    delib_mesh = NATSDeliberationMesh(event_mesh=mesh, audit_trail=audit_trail)
    
    await delib_mesh.start_listeners()
    
    # 1. Test ACTIVE transition via deliberation.request subject
    delib_id = "del_20260529_080000"
    topic = "Swarm Cognitive Resource Allocation"
    triad_members = ["agent_alpha", "agent_beta", "agent_charlie"]
    
    req_payload = {
        "deliberation_id": delib_id,
        "topic": topic,
        "triad_members": triad_members
    }
    
    # Trigger deliberation request handler directly to avoid StubEventMesh auto-trigger limitation
    await delib_mesh._handle_deliberation_request(None, "deliberation.request", req_payload)
    
    assert delib_id in delib_mesh.active_debates
    cycle = delib_mesh.active_debates[delib_id]
    assert cycle.state == HXADebateState.ACTIVE
    assert cycle.topic == topic
    assert cycle.participants == triad_members
    
    # Verify Audit Trail event
    audit_trail.record_event.assert_called_with(
        event_type="deliberation_request_received",
        agent_id="NATSDeliberationMesh",
        details={
            "deliberation_id": delib_id,
            "topic": topic,
            "participants": triad_members
        }
    )

    # 2. Test BLOCKED transition via deliberation.blocked subject
    blocked_payload = {
        "deliberation_id": delib_id,
        "reason": "Agent Gamma initiated veto challenge",
        "blocked_by": "agent_gamma"
    }
    
    # Simulate blocked message arrival
    await delib_mesh._handle_deliberation_blocked(None, "deliberation.blocked", blocked_payload)  # noqa: SLF001
    assert cycle.state == HXADebateState.BLOCKED
    assert len(cycle.history) == 1
    assert cycle.history[0]["to"] == HXADebateState.BLOCKED
    
    # Verify audit trail
    audit_trail.record_event.assert_any_call(
        event_type="deliberation_blocked",
        agent_id="agent_gamma",
        details={
            "deliberation_id": delib_id,
            "reason": "Agent Gamma initiated veto challenge"
        }
    )

    # 3. Test REVIEWING transition via deliberation.reviewing subject
    review_payload = {
        "deliberation_id": delib_id,
        "reviewer_id": "agent_sentinel_prime"
    }
    await delib_mesh._handle_deliberation_reviewing(None, "deliberation.reviewing", review_payload)  # noqa: SLF001
    assert cycle.state == HXADebateState.REVIEWING

    # 4. Test RESOLVED transition via deliberation.resolved subject
    resolved_payload = {
        "deliberation_id": delib_id,
        "resolution": "Optimal cognitive distribution consensus reached",
        "consensus_score": 0.92,
        "dissenting_opinions": ["Agent Beta preferred slightly lower temperature configuration"]
    }
    await delib_mesh._handle_deliberation_resolved(None, "deliberation.resolved", resolved_payload)  # noqa: SLF001
    
    # Verify decision committed to trail
    audit_trail.record_decision.assert_called_once_with(
        decision_id=delib_id,
        proposal=topic,
        rationale="Optimal cognitive distribution consensus reached",
        consensus_score=0.92,
        agents_participating=3
    )
    
    # Verify minority report recorded
    audit_trail.record_event.assert_any_call(
        event_type="minority_report_filed",
        agent_id="NATSDeliberationMesh",
        details={
            "deliberation_id": delib_id,
            "dissenting_opinions": ["Agent Beta preferred slightly lower temperature configuration"]
        }
    )
    
    # Hot memory debate cycle is cleaned up on resolution
    assert delib_id not in delib_mesh.active_debates
    
    await delib_mesh.stop_listeners()


# ===========================================================================
# 3. Cognitive Telemetry & Prometheus Metrics Tests
# ===========================================================================

@pytest.mark.unit
def test_prometheus_llm_metrics_registration():
    """Verify that Prometheus llm_call and llm_tokens metrics are registered and correctly capture telemetry values."""
    metrics = get_metrics()
    
    # Clean/Reset values by observing new metrics
    record_llm_call(agent_id="agent_telem", provider="garage", model="gpt-4o", duration_seconds=1.45)
    record_llm_tokens(agent_id="agent_telem", provider="garage", model="gpt-4o", prompt_tokens=150, completion_tokens=350, total_tokens=500)
    
    # Check underlying Prometheus clients
    duration_val = heretek_swarm_llm_call_duration_seconds.labels(agent_id="agent_telem", provider="garage", model="gpt-4o")
    assert duration_val._sum.get() > 0  # noqa: SLF001
    
    tokens_prompt = heretek_swarm_llm_tokens_total.labels(agent_id="agent_telem", provider="garage", model="gpt-4o", token_type="prompt")
    tokens_completion = heretek_swarm_llm_tokens_total.labels(agent_id="agent_telem", provider="garage", model="gpt-4o", token_type="completion")
    tokens_total = heretek_swarm_llm_tokens_total.labels(agent_id="agent_telem", provider="garage", model="gpt-4o", token_type="total")
    
    assert tokens_prompt._value.get() == 150  # noqa: SLF001
    assert tokens_completion._value.get() == 350  # noqa: SLF001
    assert tokens_total._value.get() == 500  # noqa: SLF001


@pytest.mark.unit
@pytest.mark.asyncio
async def test_actor_run_with_llm_instrumentation():
    """Verify run_with_llm calculates latencies, handles character fallback token heuristic, and records telemetry."""
    # Create an AgentActor subclass or mock configuration
    actor = AgentActor(agent_id="agent_aleph")
    
    # Mock model router selection fallback to swarms_agent
    actor._model_router = None  # noqa: SLF001
    
    # Mock swarms_agent and its run method
    mock_swarms_agent = MagicMock()
    mock_swarms_agent.run.return_value = "This is a completed agent response."
    actor.swarms_agent = mock_swarms_agent
    
    # Verify run_with_llm calls and metrics capture
    with patch("heretek_swarm.observability.prometheus_metrics.record_llm_call") as mock_record_call, \
         patch("heretek_swarm.observability.prometheus_metrics.record_llm_tokens") as mock_record_tokens:
        
        prompt = "Hello collective mind!"
        res = await actor.run_with_llm(prompt=prompt, timeout=10)
        
        assert res == "This is a completed agent response."
        mock_swarms_agent.run.assert_called_once_with(prompt)
        
        # Verify latency record call
        mock_record_call.assert_called_once()
        args, kwargs = mock_record_call.call_args
        assert kwargs["agent_id"] == "agent_aleph"
        assert kwargs["provider"] == "swarms_agent"
        assert kwargs["model"] == "swarms_agent"
        assert isinstance(kwargs["duration_seconds"], float)
        
        # Verify character-based heuristic tokens:
        # prompt = 22 chars -> 22 // 4 = 5 prompt tokens
        # response = 35 chars -> 35 // 4 = 8 completion tokens
        # total = 5 + 8 = 13 total tokens
        mock_record_tokens.assert_called_once_with(
            agent_id="agent_aleph",
            provider="swarms_agent",
            model="swarms_agent",
            prompt_tokens=5,
            completion_tokens=8,
            total_tokens=13
        )


@pytest.mark.unit
def test_metrics_api_endpoint_exposition():
    """Test that the GET /api/metrics endpoint returns Prometheus exposition text including cognitive metrics."""
    # Bypassing verify_auth since the metrics endpoint is unauthenticated by default
    app.dependency_overrides[verify_auth] = lambda: "test_client"
    client = TestClient(app)
    
    # Observe some metrics to ensure they exist in the output
    record_llm_call(agent_id="endpoint_agent", provider="test_prov", model="test_model", duration_seconds=0.75)
    
    r = client.get("/api/metrics")
    assert r.status_code == 200
    assert r.headers["content-type"].startswith("text/plain")
    
    text = r.text
    # Check help and type declarations
    assert "# HELP heretek_swarm_llm_call_duration_seconds" in text
    assert "# TYPE heretek_swarm_llm_call_duration_seconds" in text
    assert "heretek_swarm_llm_call_duration_seconds_bucket" in text
    
    # Check specific labels
    assert 'agent_id="endpoint_agent"' in text
    assert 'provider="test_prov"' in text
    assert 'model="test_model"' in text
