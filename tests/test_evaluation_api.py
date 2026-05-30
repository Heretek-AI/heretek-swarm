"""Tests for the evaluation API."""

import warnings
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import starlette.exceptions

warnings.filterwarnings("ignore", category=starlette.exceptions.StarletteDeprecationWarning)

from fastapi.testclient import TestClient

from heretek_swarm.api.main import app
from heretek_swarm.evaluation.evaluator import EvaluationMetric, TestCase as EvalTestCase, get_evaluator
from heretek_swarm.gateway.auth import verify_auth


@pytest.fixture
def client():
    app.dependency_overrides[verify_auth] = lambda: "tester"
    yield TestClient(app)
    app.dependency_overrides.pop(verify_auth, None)


@pytest.fixture(autouse=True)
def reset_evaluator():
    evaluator = get_evaluator()
    evaluator.test_cases.clear()
    evaluator._agent_summaries.clear()
    evaluator.results.clear()
    evaluator._evaluations.clear()
    yield


@pytest.mark.skip(reason="Requires clean app state without startup side-effects (OPENAI_API_KEY)")
def test_list_test_cases_requires_auth():
    # Save current overrides
    saved = dict(app.dependency_overrides)
    app.dependency_overrides.clear()
    try:
        with TestClient(app) as unauth_client:
            response = unauth_client.get("/api/evaluation/test-cases")
            assert response.status_code == 401
    finally:
        app.dependency_overrides.update(saved)


def test_create_and_list_test_cases(client):
    headers = {"Authorization": "Bearer test-token"}
    create = client.post(
        "/api/evaluation/test-cases",
        json={
            "name": "Smoke test",
            "input_data": {"query": "hello"},
            "evaluation_criteria": [EvaluationMetric.ACCURACY.value],
        },
        headers=headers,
    )
    assert create.status_code == 201

    listing = client.get("/api/evaluation/test-cases", headers=headers)
    assert listing.status_code == 200
    assert len(listing.json()["test_cases"]) == 1


def test_evaluate_agent_not_found(client):
    headers = {"Authorization": "Bearer test-token"}
    evaluator = get_evaluator()
    evaluator.load_test_cases(
        [
            EvalTestCase(
                id="tc1",
                name="Basic",
                input_data={"query": "ping"},
            )
        ]
    )

    with patch("heretek_swarm.actors.supervisor.get_supervisor", return_value=None):
        response = client.post(
            "/api/evaluation/agents/missing-agent/evaluate",
            headers=headers,
        )
        assert response.status_code == 404


def test_evaluate_agent_success(client):
    headers = {"Authorization": "Bearer test-token"}
    evaluator = get_evaluator()
    evaluator.load_test_cases(
        [
            EvalTestCase(
                id="tc1",
                name="Basic",
                input_data={"query": "ping"},
                expected_output={"ok": True},
            )
        ]
    )

    mock_agent = MagicMock()
    mock_agent.execute = AsyncMock(return_value={"ok": True})
    mock_supervisor = MagicMock()
    mock_supervisor.actors = {"agent-1": mock_agent}

    with patch("heretek_swarm.actors.supervisor.get_supervisor", return_value=mock_supervisor):
        response = client.post(
            "/api/evaluation/agents/agent-1/evaluate",
            headers=headers,
        )
        assert response.status_code == 201
        body = response.json()
        assert body["agent_id"] == "agent-1"
        assert len(body["executions"]) == 1
        assert body["executions"][0]["status"] == "passed"
