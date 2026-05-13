"""
Tests for Consciousness API — M010 S04 T02.

Verifies the data pipeline from live agent state → EnhancedConsciousnessPlugin
→ /api/consciousness/* endpoints is real (not stub data).

Four tests:
1. Statistics endpoint reads live agent count from the enhanced registry
2. Recording interactions flows through IIT calculator into statistics
3. Recording predictions and outcomes flows through FEP tracker into statistics
4. Full pipeline: register agents → record interactions → statistics reflects real data
"""

from __future__ import annotations

import os
from unittest.mock import patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

# Set a fixed API key BEFORE any auth module imports so both the fixture and
# verify_auth see the same value across all calls in the test session.
_TEST_API_KEY = "htsk_test_consciousness_api_key_000000000000"
os.environ["HERETEK_API_KEY"] = _TEST_API_KEY

from heretek_swarm.api import consciousness as consciousness_module  # noqa: E402
from heretek_swarm.api.consciousness import (  # noqa: E402
    router,
)
from heretek_swarm.runtime.registry_enhanced import (  # noqa: E402
    AgentInstance,
    AgentLifecycleState,
    AgentTypeMetadata,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def _reset_singletons():
    """Reset global plugin/tracker singletons between tests."""
    consciousness_module._consciousness_plugin = None
    consciousness_module._agency_tracker = None
    yield
    consciousness_module._consciousness_plugin = None
    consciousness_module._agency_tracker = None


@pytest.fixture
def app():
    """Create a minimal FastAPI app with the consciousness router."""
    _app = FastAPI()
    _app.include_router(router)
    return _app


@pytest.fixture
def client(app):
    """Synchronous test client."""
    return TestClient(app, raise_server_exceptions=False)


@pytest.fixture
def auth_headers():
    """Return headers with the fixed test Bearer token."""
    return {"Authorization": f"Bearer {_TEST_API_KEY}"}


def _make_instance(instance_id: str, agent_type: str = "TestAgent") -> AgentInstance:
    """Create a minimal AgentInstance for mocking the registry."""
    return AgentInstance(
        instance_id=instance_id,
        agent_type=agent_type,
        config={},
        state=AgentLifecycleState.RUNNING,
        actor=None,
        metadata=AgentTypeMetadata(
            type_name=agent_type,
            module_path="test",
            description="test agent",
        ),
    )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_statistics_reads_live_registry(client, auth_headers):
    """
    Verify /api/consciousness/statistics reads total_agents from the
    enhanced registry, not the plugin's internal (possibly empty) count.
    """
    # Mock the registry to return 3 running instances
    fake_instances = {
        "agent-alpha": _make_instance("agent-alpha"),
        "agent-beta": _make_instance("agent-beta"),
        "agent-gamma": _make_instance("agent-gamma"),
    }

    with patch("heretek_swarm.api.consciousness.get_enhanced_registry") as mock_registry:
        mock_registry.return_value.get_all_instances.return_value = fake_instances
        resp = client.get("/api/consciousness/statistics", headers=auth_headers)

    assert resp.status_code == 200
    data = resp.json()
    # total_agents must come from the registry (3), not the plugin (0)
    assert data["total_agents"] == 3
    assert data["active_connections"] == 3


def test_record_interaction_flows_to_iit(client, auth_headers):
    """
    Verify recording an agent interaction updates the IIT calculator,
    and the connectivity endpoint reflects the new interaction.
    """
    # Record an interaction
    resp = client.post(
        "/api/consciousness/record-interaction",
        json={"from_agent": "agent-a", "to_agent": "agent-b", "type": "message"},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "recorded"

    # Now the connectivity matrix should contain agent-a → agent-b
    resp = client.get("/api/consciousness/connectivity", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    connectivity = data["connectivity"]
    assert "agent-a" in connectivity
    assert connectivity["agent-a"].get("agent-b", 0) == 1.0


def test_record_prediction_and_outcome_flows_to_fep(client, auth_headers):
    """
    Verify recording a prediction followed by an outcome flows through
    the FEP tracker and updates agent FEP metrics.
    """
    # Record a prediction with explicit confidence
    resp = client.post(
        "/api/consciousness/record-prediction",
        json={
            "agent_id": "agent-fep",
            "predicted_outcome": {"result": "success", "value": 42},
            "confidence": 0.9,
        },
        headers=auth_headers,
    )
    assert resp.status_code == 200

    # Record a matching outcome (low surprise expected)
    resp = client.post(
        "/api/consciousness/record-outcome",
        json={
            "agent_id": "agent-fep",
            "actual_outcome": {"result": "success", "value": 40},
        },
        headers=auth_headers,
    )
    assert resp.status_code == 200

    # The FEP endpoint should now have metrics for this agent
    resp = client.get("/api/consciousness/agents/agent-fep/fep", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    metrics = data["metrics"]
    # Matching outcome → low surprise; value difference is small relative error
    assert metrics["surprise"] < 0.5
    assert metrics["prediction_accuracy"] > 0.5


def test_full_pipeline_register_interact_statistics(client, auth_headers):
    """
    Full pipeline: register agents in the plugin, record interactions,
    trigger IIT phi calculation, then verify statistics reflects real data.
    """
    # Mock the registry to report 2 live agents
    fake_instances = {
        "agent-x": _make_instance("agent-x"),
        "agent-y": _make_instance("agent-y"),
    }

    with patch("heretek_swarm.api.consciousness.get_enhanced_registry") as mock_registry:
        mock_registry.return_value.get_all_instances.return_value = fake_instances

        # Record cross-agent interactions (strengthens IIT connectivity)
        for _ in range(5):
            client.post(
                "/api/consciousness/record-interaction",
                json={"from_agent": "agent-x", "to_agent": "agent-y", "type": "task"},
                headers=auth_headers,
            )
            client.post(
                "/api/consciousness/record-interaction",
                json={"from_agent": "agent-y", "to_agent": "agent-x", "type": "response"},
                headers=auth_headers,
            )

        # Trigger IIT phi calculation via the connectivity matrix — this
        # calls plugin.iit_calculator.calculate_phi and populates history
        resp_iit = client.get("/api/consciousness/agents/agent-x/iit", headers=auth_headers)
        assert resp_iit.status_code == 200

        # Calculate consciousness metrics for each agent
        client.get("/api/consciousness/metrics/agent-x", headers=auth_headers)
        client.get("/api/consciousness/metrics/agent-y", headers=auth_headers)

        # Fetch statistics
        resp = client.get("/api/consciousness/statistics", headers=auth_headers)

    assert resp.status_code == 200
    data = resp.json()
    # Registry-supplied agent count
    assert data["total_agents"] == 2
    # IIT phi should be non-zero after interactions and explicit phi calculation
    assert data["average_phi"] > 0.0
