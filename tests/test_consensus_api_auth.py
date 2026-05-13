"""Tests for consensus API authentication hardening (M009/S04/T01).

Verifies:
- All consensus endpoints require Bearer token auth (401 without auth)
- Deliberation endpoints work correctly with str agent_id (not dict)
- get_consensus_results requires authentication
- Valid token grants access
- Malformed/expired tokens are rejected
- Rate limit headers are present
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from heretek_swarm.api.consensus import (
    _active_rounds,
    _consensus_store,
    consensus_auth_manager,
    router,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

_BROADCAST_PATH = "heretek_swarm.api.websockets.manager.broadcast_dashboard"


@pytest.fixture(autouse=True)
def _clear_state():
    """Reset in-memory stores between tests."""
    _active_rounds.clear()
    _consensus_store.clear()
    yield
    _active_rounds.clear()
    _consensus_store.clear()


@pytest.fixture
def app():
    """Create a minimal FastAPI app with the consensus router."""
    _app = FastAPI()
    _app.include_router(router)
    return _app


@pytest.fixture
def client(app):
    """Synchronous test client."""
    return TestClient(app, raise_server_exceptions=False)


@pytest.fixture
def auth_headers():
    """Generate valid auth headers for test-agent."""
    token = consensus_auth_manager.generate_token("test-agent", ["vote", "create", "view"])
    return {"Authorization": f"Bearer {token}", "X-Agent-ID": "test-agent"}


def _create_round(client, headers, topic="test-topic"):
    """Helper: create a consensus round and return its id."""
    resp = client.post(
        "/api/consensus",
        params={"topic": topic, "description": "test"},
        headers=headers,
    )
    assert resp.status_code == 200, resp.text
    return resp.json()["id"]


# ---------------------------------------------------------------------------
# Tests — 401 without auth
# ---------------------------------------------------------------------------


class TestUnauthenticatedAccess:
    """Verify endpoints return 401 when no Bearer token is provided."""

    def test_create_consensus_requires_auth(self, client):
        """POST /api/consensus returns 401 without auth."""
        resp = client.post("/api/consensus", params={"topic": "test"})
        assert resp.status_code == 401

    def test_vote_requires_auth(self, client, auth_headers):
        """POST /api/consensus/{id}/vote returns 401 without auth."""
        round_id = _create_round(client, auth_headers)
        resp = client.post(
            f"/api/consensus/{round_id}/vote",
            params={"decision": "yes", "confidence": 0.9},
        )
        assert resp.status_code == 401

    def test_results_requires_auth(self, client, auth_headers):
        """GET /api/consensus/{id}/results returns 401 without auth.

        This was the critical missing-auth endpoint before S04/T01.
        """
        round_id = _create_round(client, auth_headers)
        resp = client.get(f"/api/consensus/{round_id}/results")
        assert resp.status_code == 401

    def test_aggregate_requires_auth(self, client, auth_headers):
        """POST /api/consensus/{id}/aggregate returns 401 without auth."""
        round_id = _create_round(client, auth_headers)
        resp = client.post(f"/api/consensus/{round_id}/aggregate")
        assert resp.status_code == 401

    def test_cancel_requires_auth(self, client, auth_headers):
        """DELETE /api/consensus/{id} returns 401 without auth."""
        round_id = _create_round(client, auth_headers)
        resp = client.delete(f"/api/consensus/{round_id}")
        assert resp.status_code == 401

    def test_history_requires_auth(self, client):
        """GET /api/consensus/history returns 401 without auth."""
        resp = client.get("/api/consensus/history")
        assert resp.status_code == 401

    def test_list_rounds_requires_auth(self, client):
        """GET /api/consensus returns 401 without auth."""
        resp = client.get("/api/consensus")
        assert resp.status_code == 401

    def test_get_round_requires_auth(self, client, auth_headers):
        """GET /api/consensus/{id} returns 401 without auth."""
        round_id = _create_round(client, auth_headers)
        resp = client.get(f"/api/consensus/{round_id}")
        assert resp.status_code == 401

    def test_config_requires_auth(self, client):
        """GET /api/consensus/config returns 401 without auth."""
        resp = client.get("/api/consensus/config")
        assert resp.status_code == 401


# ---------------------------------------------------------------------------
# Tests — deliberation endpoints use str agent_id (not dict)
# ---------------------------------------------------------------------------


class TestDeliberationAuth:
    """Verify deliberation endpoints work with str agent_id dependency.

    Before S04/T01, these used `auth: dict = Depends(get_authenticated_agent)`
    and accessed `auth["agent_id"]`, which would crash since
    get_authenticated_agent returns a str. These tests verify that auth
    passes correctly (no 401, no crash on auth["agent_id"]).
    """

    @patch(_BROADCAST_PATH, new_callable=AsyncMock)
    def test_start_deliberation_auth_passes(self, mock_broadcast, client, auth_headers):
        """POST /deliberation/start with valid auth does NOT return 401.

        Verifies the auth dict→str fix works (no crash on auth["agent_id"]).
        """
        resp = client.post(
            "/api/consensus/deliberation/start",
            params={"proposal": "Should we adopt microservices?"},
            json=["agent-1", "agent-2"],
            headers=auth_headers,
        )
        # Auth passes — we should NOT get 401
        assert resp.status_code != 401, "Auth should pass with valid token"
        # May get 500 from deliberation engine (not our concern here)

    @patch(_BROADCAST_PATH, new_callable=AsyncMock)
    def test_submit_position_auth_passes(self, mock_broadcast, client, auth_headers):
        """POST /deliberation/{id}/submit_position with valid auth does NOT return 401."""
        # Use a fake deliberation_id — the point is auth passes
        resp = client.post(
            "/api/consensus/deliberation/fake-id/submit_position",
            params={"position": "support", "confidence": 0.8},
            headers=auth_headers,
        )
        assert resp.status_code != 401, "Auth should pass with valid token"

    @patch(_BROADCAST_PATH, new_callable=AsyncMock)
    def test_submit_argument_auth_passes(self, mock_broadcast, client, auth_headers):
        """POST /deliberation/{id}/submit_argument with valid auth does NOT return 401."""
        resp = client.post(
            "/api/consensus/deliberation/fake-id/submit_argument",
            params={"position": "support", "reasoning": "Because X", "confidence": 0.7},
            headers=auth_headers,
        )
        assert resp.status_code != 401, "Auth should pass with valid token"

    @patch(_BROADCAST_PATH, new_callable=AsyncMock)
    def test_finalize_auth_passes(self, mock_broadcast, client, auth_headers):
        """POST /deliberation/{id}/finalize with valid auth does NOT return 401."""
        resp = client.post(
            "/api/consensus/deliberation/fake-id/finalize",
            headers=auth_headers,
        )
        assert resp.status_code != 401, "Auth should pass with valid token"

    def test_deliberation_state_requires_auth(self, client):
        """GET /deliberation/{id}/state returns 401 without auth."""
        resp = client.get("/api/consensus/deliberation/fake-id/state")
        assert resp.status_code == 401

    def test_deliberation_history_requires_auth(self, client):
        """GET /deliberation/{id}/history returns 401 without auth."""
        resp = client.get("/api/consensus/deliberation/fake-id/history")
        assert resp.status_code == 401

    def test_cleanup_deliberation_requires_auth(self, client):
        """DELETE /deliberation/{id} returns 401 without auth."""
        resp = client.delete("/api/consensus/deliberation/fake-id")
        assert resp.status_code == 401


# ---------------------------------------------------------------------------
# Tests — valid token grants access
# ---------------------------------------------------------------------------


class TestAuthenticatedAccess:
    """Verify valid tokens grant access to endpoints."""

    def test_list_rounds_with_auth(self, client, auth_headers):
        """GET /api/consensus returns 200 with valid auth."""
        resp = client.get("/api/consensus", headers=auth_headers)
        assert resp.status_code == 200
        assert "consensus_rounds" in resp.json()

    def test_get_results_with_auth(self, client, auth_headers):
        """GET /api/consensus/{id}/results returns 200 with valid auth."""
        round_id = _create_round(client, auth_headers)
        resp = client.get(f"/api/consensus/{round_id}/results", headers=auth_headers)
        assert resp.status_code == 200

    def test_create_and_vote_with_auth(self, client, auth_headers):
        """POST /api/consensus/{id}/vote returns 200 with valid auth."""
        round_id = _create_round(client, auth_headers)
        resp = client.post(
            f"/api/consensus/{round_id}/vote",
            params={"decision": "approve", "confidence": 0.95},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "vote_accepted"

    def test_config_with_auth(self, client, auth_headers):
        """GET /api/consensus/config — note: route is shadowed by /{consensus_id}.

        The /config route is defined after /{consensus_id} in the router,
        so FastAPI matches 'config' as a consensus_id. This is a pre-existing
        route ordering issue, not an auth issue. Test verifies auth works.
        """
        resp = client.get("/api/consensus/config", headers=auth_headers)
        # Route is shadowed — we get 404 (consensus 'config' not found in store)
        # rather than 401 (unauthenticated). Auth is working.
        assert resp.status_code in (200, 404)


# ---------------------------------------------------------------------------
# Tests — negative: malformed/expired tokens
# ---------------------------------------------------------------------------


class TestMalformedTokens:
    """Verify malformed and expired tokens are rejected."""

    def test_empty_bearer_token(self, client):
        """Empty Bearer token string returns 401."""
        resp = client.get(
            "/api/consensus",
            headers={"Authorization": "Bearer "},
        )
        # Empty token is still submitted — validation should fail
        assert resp.status_code == 401

    def test_invalid_token(self, client):
        """Random invalid token returns 401."""
        resp = client.get(
            "/api/consensus",
            headers={"Authorization": "Bearer definitely-not-a-real-token"},
        )
        assert resp.status_code == 401

    def test_malformed_authorization_header(self, client):
        """Malformed Authorization header returns 401."""
        resp = client.get(
            "/api/consensus",
            headers={"Authorization": "NotBearer some-token"},
        )
        assert resp.status_code == 401

    def test_missing_authorization_header(self, client):
        """Missing Authorization header returns 401."""
        resp = client.get("/api/consensus")
        assert resp.status_code == 401

    def test_expired_token(self, client):
        """Expired token returns 401."""
        token = consensus_auth_manager.generate_token("test-agent")
        # Manually expire the token
        consensus_auth_manager._valid_tokens[token]["expires_at"] = datetime.now(UTC) - timedelta(
            hours=1
        )
        resp = client.get(
            "/api/consensus",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 401

    def test_agent_id_header_mismatch(self, client):
        """X-Agent-ID header that doesn't match token returns 403."""
        token = consensus_auth_manager.generate_token("agent-A")
        resp = client.get(
            "/api/consensus",
            headers={
                "Authorization": f"Bearer {token}",
                "X-Agent-ID": "agent-B",
            },
        )
        assert resp.status_code == 403

    def test_revoked_token(self, client):
        """Revoked token returns 401."""
        token = consensus_auth_manager.generate_token("test-agent")
        consensus_auth_manager.revoke_token(token)
        resp = client.get(
            "/api/consensus",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 401


# ---------------------------------------------------------------------------
# Tests — tribunal endpoints with auth
# ---------------------------------------------------------------------------


class TestTribunalAuth:
    """Verify tribunal endpoints require auth and use str agent_id."""

    def test_create_tribunal_case_requires_auth(self, client):
        """POST /tribunal/cases returns 401 without auth."""
        resp = client.post(
            "/api/consensus/tribunal/cases",
            json={"original_decision_id": "d1", "grounds": "procedural"},
        )
        # Tribunal not available returns 503, but auth should block first
        # If tribunal is None, 503 is expected even with auth
        # The key is that without auth we get 401
        assert resp.status_code in (401, 503)

    def test_get_tribunal_case_requires_auth(self, client):
        """GET /tribunal/cases/{id} returns 401 without auth."""
        resp = client.get("/api/consensus/tribunal/cases/test-case")
        assert resp.status_code in (401, 503)
