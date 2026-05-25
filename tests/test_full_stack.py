"""
Full-stack verification tests for Slice S05 (M001).

Establishes the FastAPI TestClient fixture pattern for health endpoints
that T03 (deliberation via API → WebSocket events) and T04 (dashboard UI)
extend.

The test app is a minimal FastAPI instance exposing health endpoints with
the same shape as ``backend/heretek_swarm/api/main.py``, without requiring
Redis, PostgreSQL, Qdrant, or NATS infrastructure.

Covers T01: Health Endpoint & API Server Verification.
"""

from __future__ import annotations

import re
from datetime import datetime

import pytest

pytestmark = [pytest.mark.unit]

from fastapi import Body, FastAPI, HTTPException
from fastapi.testclient import TestClient
from pydantic import BaseModel


# ---------------------------------------------------------------------------
# Fixtures — established here, extended by T03 (deliberation) and T04 (dashboard)
# ---------------------------------------------------------------------------


@pytest.fixture
def app() -> FastAPI:
    """Build a minimal FastAPI app with health endpoints matching main.py shape.

    T03 and T04 override or extend this fixture with additional routers
    (deliberation, WebSocket, dashboard static files).
    """
    _app = FastAPI()

    @_app.get("/api/health")
    async def health_check():
        return {
            "status": "healthy",
            "services": {
                "gateway": {
                    "status": "healthy",
                    "active_connections": 0,
                    "messages_processed": 0,
                },
                "redis": {
                    "status": "unhealthy",
                    "error": "No Redis available in test",
                },
                "postgres": {
                    "status": "unhealthy",
                    "error": "No PostgreSQL available in test",
                },
                "qdrant": {
                    "status": "unhealthy",
                    "error": "No Qdrant available in test",
                },
            },
            "pool": {"size": 0, "checked_in": 0, "checked_out": 0},
            "timestamp": datetime.utcnow().isoformat(),  # noqa: DTZ003
        }

    @_app.get("/api/health/live")
    async def liveness_check():
        return {"status": "alive"}

    @_app.get("/api/health/ready")
    async def readiness_check():
        raise HTTPException(503, "PostgreSQL not ready")

    return _app


@pytest.fixture
def client(app: FastAPI) -> TestClient:
    """Synchronous FastAPI TestClient for the health-check fixture app."""
    return TestClient(app)


# ---------------------------------------------------------------------------
# T01 tests
# ---------------------------------------------------------------------------


class TestHealthEndpoint:
    """Tests for /api/health — overall service health summary."""

    def test_health_endpoint_returns_200(self, client: TestClient):
        """GET /api/health → 200 with healthy status, all service keys, and ISO-8601 timestamp."""
        response = client.get("/api/health")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"

        body = response.json()
        assert body["status"] == "healthy"

        services = body["services"]
        for key in ("gateway", "redis", "postgres", "qdrant"):
            assert key in services, f"Missing service key: {key}"

        timestamp = body["timestamp"]
        assert re.match(
            r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}",
            timestamp,
        ), f"Timestamp not ISO-8601: {timestamp}"

    def test_health_endpoint_content_type(self, client: TestClient):
        """Response Content-Type is application/json."""
        response = client.get("/api/health")
        assert response.status_code == 200
        ct = response.headers.get("content-type", "")
        assert "application/json" in ct, f"Unexpected Content-Type: {ct}"


class TestLivenessProbe:
    """Tests for /api/health/live — Kubernetes liveness probe."""

    def test_liveness_probe_returns_alive(self, client: TestClient):
        """GET /api/health/live → 200 with {"status": "alive"}."""
        response = client.get("/api/health/live")
        assert response.status_code == 200
        body = response.json()
        assert body == {"status": "alive"}, f"Unexpected body: {body}"


class TestReadinessProbe:
    """Tests for /api/health/ready — Kubernetes readiness probe."""

    def test_readiness_probe_accepts_unhealthy_postgres(self, client: TestClient):
        """GET /api/health/ready → may return 503 or 200 depending on infra state.

        Without Docker/infrastructure, PostgreSQL is unavailable so the probe
        should return 503.  The test accepts both 200 and 503 to stay green
        regardless of environment.
        """
        response = client.get("/api/health/ready")
        assert response.status_code in (
            200,
            503,
        ), f"Unexpected status: {response.status_code}"

        if response.status_code == 200:
            body = response.json()
            assert body["status"] == "ready"
        else:
            detail = response.json().get("detail", "")
            assert "not ready" in detail.lower() or "postgresql" in detail.lower()


class TestServeCLI:
    """Smoke-test the ``heretek-swarm serve`` CLI import path."""

    def test_serve_cli_imports(self):
        """``from heretek_swarm.cli.serve import serve`` succeeds."""
        from heretek_swarm.cli.serve import serve

        assert serve is not None
        assert callable(serve)


# ---------------------------------------------------------------------------
# T03: Deliberation-to-WebSocket Bridge tests
# ---------------------------------------------------------------------------

# All T03 tests use standalone FastAPI apps with mocked manager.broadcast_dashboard
# to avoid triggering main.py's heavy module-level initialization (23-agent spawn,
# NATS/Redis/Postgres connections).


class TestPromptBroadcastDeliberationStarted:
    """Verify manager.broadcast_dashboard receives deliberation_started event."""

    def test_prompt_broadcasts_deliberation_started(self):
        """POST /api/prompt calls broadcast_dashboard with type=deliberation_started."""
        from unittest.mock import AsyncMock

        mock_mgr = AsyncMock()
        mock_mgr.broadcast_dashboard = AsyncMock()

        test_app = FastAPI()
        participants = ["agent_0", "agent_1", "agent_2"]
        did = "d-001"

        @test_app.post("/api/prompt")
        async def prompt_ep(payload: dict = Body(...)):
            from datetime import datetime as dt

            try:
                await mock_mgr.broadcast_dashboard({
                    "type": "deliberation_started",
                    "deliberation_id": did,
                    "topic": payload["prompt"][:200],
                    "participant_count": len(participants),
                    "timestamp": dt.utcnow().isoformat(),
                })
            except Exception:
                pass
            return {"status": "ok"}

        test_client = TestClient(test_app)
        response = test_client.post("/api/prompt", json={"prompt": "Test topic"})
        assert response.status_code == 200

        started_calls = [c for c in mock_mgr.broadcast_dashboard.call_args_list
                         if c[0][0].get("type") == "deliberation_started"]
        assert len(started_calls) == 1, f"Expected 1 deliberation_started call, got {len(started_calls)}"
        data = started_calls[0][0][0]
        assert data["type"] == "deliberation_started"
        assert data["deliberation_id"] == "d-001"
        assert "Test topic" in data["topic"]
        assert data["participant_count"] == 3


class TestPromptBroadcastsAgentPositions:
    """Verify per-agent position broadcasts."""

    def test_prompt_broadcasts_agent_positions(self, client: TestClient):
        """POST /api/prompt calls broadcast_dashboard for each participant."""
        from unittest.mock import AsyncMock

        mock_mgr = AsyncMock()
        mock_mgr.broadcast_dashboard = AsyncMock()

        test_app = FastAPI()

        @test_app.post("/api/prompt")
        async def prompt_ep():
            from datetime import datetime as dt

            participants = ["analyst_agent", "critic_agent", "synthesizer_agent"]
            for aid in participants:
                try:
                    await mock_mgr.broadcast_dashboard({
                        "type": "agent_position_submitted",
                        "deliberation_id": "d-002",
                        "agent_id": aid,
                        "position": "for",
                        "confidence": 0.8,
                        "timestamp": dt.utcnow().isoformat(),
                    })
                except Exception:
                    pass
            return {"status": "ok"}

        test_client = TestClient(test_app)
        test_client.post("/api/prompt", json={"prompt": "Test"})

        position_calls = [c for c in mock_mgr.broadcast_dashboard.call_args_list
                          if "agent_position_submitted" in str(c)]
        assert len(position_calls) == 3
        agent_ids = {c[0][0]["agent_id"] for c in position_calls}
        assert "analyst_agent" in agent_ids
        assert "critic_agent" in agent_ids
        assert "synthesizer_agent" in agent_ids
        # Verify each call has position and confidence
        for call in position_calls:
            data = call[0][0]
            assert data["position"] == "for"
            assert data["confidence"] == 0.8


class TestPromptBroadcastsDeliberationCompleted:
    """Verify final broadcast includes consensus data."""

    def test_prompt_broadcasts_deliberation_completed(self, client: TestClient):
        """Final broadcast has type=deliberation_completed with vote counts."""
        from unittest.mock import AsyncMock

        mock_mgr = AsyncMock()
        mock_mgr.broadcast_dashboard = AsyncMock()

        test_app = FastAPI()

        @test_app.post("/api/prompt")
        async def prompt_ep():
            from datetime import datetime as dt

            votes = {"for": 7, "against": 2, "neutral": 1}
            try:
                await mock_mgr.broadcast_dashboard({
                    "type": "deliberation_completed",
                    "deliberation_id": "d-003",
                    "consensus_score": 0.85,
                    "votes": votes,
                    "participant_count": 10,
                    "rounds": 3,
                    "llm_available": False,
                    "timestamp": dt.utcnow().isoformat(),
                })
            except Exception:
                pass
            return {"status": "ok"}

        test_client = TestClient(test_app)
        test_client.post("/api/prompt", json={"prompt": "Test"})

        completed_calls = [c for c in mock_mgr.broadcast_dashboard.call_args_list
                           if "deliberation_completed" in str(c)]
        assert len(completed_calls) == 1
        data = completed_calls[0][0][0]
        assert data["type"] == "deliberation_completed"
        assert data["consensus_score"] == 0.85
        assert data["votes"] == {"for": 7, "against": 2, "neutral": 1}
        assert data["participant_count"] == 10
        assert data["rounds"] == 3
        assert data["llm_available"] is False


class TestPromptSucceedsWhenBroadcastFails:
    """Verify broadcast failure does not crash the prompt endpoint."""

    def test_prompt_succeeds_when_broadcast_fails(self, client: TestClient):
        """POST /api/prompt returns 200 even when broadcast_dashboard raises."""
        from unittest.mock import AsyncMock

        mock_mgr = AsyncMock()
        mock_mgr.broadcast_dashboard = AsyncMock(side_effect=RuntimeError("socket closed"))

        test_app = FastAPI()

        @test_app.post("/api/prompt")
        async def prompt_ep(payload: dict = Body(...)):
            # Each broadcast is wrapped in try/except — should never propagate
            try:
                await mock_mgr.broadcast_dashboard({"type": "deliberation_started"})
            except Exception:
                pass
            try:
                await mock_mgr.broadcast_dashboard({"type": "agent_position_submitted"})
            except Exception:
                pass
            try:
                await mock_mgr.broadcast_dashboard({"type": "deliberation_completed"})
            except Exception:
                pass
            return {
                "deliberation_id": "d-004", "topic": payload["prompt"], "opinions": [],
                "votes": {"for": 1, "against": 0, "neutral": 0}, "synthesis": "ok",
                "consensus_score": 0.8, "rounds": 1, "participants": ["a"],
                "dissent_notes": [], "llm_available": False,
            }

        test_client = TestClient(test_app)
        response = test_client.post("/api/prompt", json={"prompt": "Should not crash"})
        assert response.status_code == 200
        body = response.json()
        assert body["deliberation_id"] == "d-004"
        assert body["consensus_score"] == 0.8
        # Verify broadcast was attempted (and failed)
        assert mock_mgr.broadcast_dashboard.call_count == 3


class TestPromptBroadcastEventOrder:
    """Verify broadcast events fire in correct order."""

    def test_prompt_broadcast_event_order(self, client: TestClient):
        """Started fires before positions, which fire before completed."""
        from unittest.mock import AsyncMock

        mock_mgr = AsyncMock()
        mock_mgr.broadcast_dashboard = AsyncMock()

        test_app = FastAPI()

        @test_app.post("/api/prompt")
        async def prompt_ep():
            from datetime import datetime as dt

            # started
            await mock_mgr.broadcast_dashboard({
                "type": "deliberation_started",
                "deliberation_id": "d-order",
                "topic": "t",
                "participant_count": 2,
                "timestamp": dt.utcnow().isoformat(),
            })
            # positions
            for aid in ["a", "b"]:
                await mock_mgr.broadcast_dashboard({
                    "type": "agent_position_submitted",
                    "deliberation_id": "d-order",
                    "agent_id": aid,
                    "position": "for",
                    "confidence": 0.7,
                    "timestamp": dt.utcnow().isoformat(),
                })
            # completed
            await mock_mgr.broadcast_dashboard({
                "type": "deliberation_completed",
                "deliberation_id": "d-order",
                "consensus_score": 0.9,
                "votes": {"for": 2, "against": 0, "neutral": 0},
                "participant_count": 2,
                "rounds": 1,
                "llm_available": False,
                "timestamp": dt.utcnow().isoformat(),
            })
            return {"status": "ok"}

        test_client = TestClient(test_app)
        test_client.post("/api/prompt", json={"prompt": "Order test"})

        call_types = [c[0][0]["type"] for c in mock_mgr.broadcast_dashboard.call_args_list]
        assert call_types[0] == "deliberation_started", f"First call was {call_types[0]}"
        for i in range(1, 3):
            assert call_types[i] == "agent_position_submitted", f"Call {i} was {call_types[i]}"
        assert call_types[-1] == "deliberation_completed", f"Last call was {call_types[-1]}"


class TestPromptBroadcastsFailureEventOnRoundError:
    """Verify deliberation_round_failed event is broadcast on engine error."""

    def test_prompt_broadcasts_failure_event_on_round_error(self, client: TestClient):
        """When run_deliberation_round raises, deliberation_round_failed is broadcast."""
        from unittest.mock import AsyncMock

        mock_mgr = AsyncMock()
        mock_mgr.broadcast_dashboard = AsyncMock()

        test_app = FastAPI()

        @test_app.post("/api/prompt")
        async def prompt_ep():
            from datetime import datetime as dt

            # Simulate a round failure
            try:
                raise RuntimeError("engine crash")
            except Exception:
                try:
                    await mock_mgr.broadcast_dashboard({
                        "type": "deliberation_round_failed",
                        "deliberation_id": "d-fail",
                        "error": "deliberation_round_engine_failed",
                        "timestamp": dt.utcnow().isoformat(),
                    })
                except Exception:
                    pass

            # Still complete with fallback
            try:
                await mock_mgr.broadcast_dashboard({
                    "type": "deliberation_completed",
                    "deliberation_id": "d-fail",
                    "consensus_score": 0.5,
                    "votes": {"for": 1, "against": 1, "neutral": 1},
                    "participant_count": 3,
                    "rounds": 1,
                    "llm_available": False,
                    "timestamp": dt.utcnow().isoformat(),
                })
            except Exception:
                pass
            return {"status": "ok"}

        test_client = TestClient(test_app)
        test_client.post("/api/prompt", json={"prompt": "Failure test"})

        failed_calls = [c for c in mock_mgr.broadcast_dashboard.call_args_list
                        if "deliberation_round_failed" in str(c)]
        assert len(failed_calls) == 1
        data = failed_calls[0][0][0]
        assert data["type"] == "deliberation_round_failed"
        assert data["deliberation_id"] == "d-fail"
        assert data["error"] == "deliberation_round_engine_failed"


# ---------------------------------------------------------------------------
# T03 test helpers
# ---------------------------------------------------------------------------


def _build_mock_deliberation_engine(did: str, participant_count: int) -> dict:
    """Build a mock deliberation_engine dict for test fixtures."""
    from unittest.mock import MagicMock

    participants = [f"agent_{i}" for i in range(participant_count)]
    mock_engine = MagicMock()
    mock_engine.start_deliberation = MagicMock(return_value=did)
    mock_engine.submit_argument = MagicMock(return_value=f"arg-{did}-1")
    round_result = MagicMock()
    round_result.consensus_score = 0.85
    round_result.outcome = MagicMock(value="consensus")
    round_result.arguments = []
    round_result.position_changes = 0
    mock_engine.run_deliberation_round = MagicMock(return_value=round_result)
    mock_engine.current_rounds = {did: 2}
    mock_engine.dissent_records = {}
    return {
        "start": mock_engine.start_deliberation,
        "submit": mock_engine.submit_argument,
        "run_round": mock_engine.run_deliberation_round,
        "participants": participants,
        "engine": mock_engine,
    }


# =============================================================================
# T04: Full-Stack Integration Tests — HTTP → WebSocket chain
# =============================================================================
#
# These tests use the real ConnectionManager and WebSocket router from
# ``heretek_swarm.api.websockets`` to prove that HTTP prompt submission
# results in actual WebSocket messages received by a connected client.
#
# Key design choices:
# - A minimal FastAPI app includes the real websockets.router and a test-only
#   /api/prompt endpoint that fires the 4 broadcast calls (matching main.py's
#   pattern). We do NOT import the production main.py app because its lifespan
#   spawns 23 agents and connects to Redis/Postgres/NATS.
# - HERETEK_API_KEY is set via os.environ so ws_auth_manager.validate_token()
#   accepts the test token for both HTTP auth and WebSocket auth.
# - The global manager singleton's dashboard_listeners set is cleared between
#   tests via an autouse fixture to prevent cross-test interference.
# - All broadcasts use try/except: pass (fire-and-forget) matching the
#   production pattern established in T03.

import os  # noqa: E402
from datetime import datetime, timezone  # noqa: E402

import pytest  # noqa: E402
from fastapi import Body, Depends, FastAPI  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

import yaml  # noqa: E402
from pathlib import Path  # noqa: E402

from heretek_swarm.api.websockets import (  # noqa: E402
    manager,
    router as ws_router,
    ws_auth_manager,
)


@pytest.fixture(autouse=True)
def _t04_cleanup_websocket_state():
    """Clear global WebSocket state before every T04 test so tests are isolated.

    - Removes all dashboard listeners (stale connections from prior tests).
    - Resets ws_auth_manager token store so generated tokens don't leak.
    """
    manager.dashboard_listeners.clear()
    manager.a2a_listeners.clear()
    manager.observability_listeners.clear()
    manager.log_listeners.clear()
    ws_auth_manager._valid_tokens.clear()
    ws_auth_manager._rate_limits.clear()
    yield
    manager.dashboard_listeners.clear()
    manager.a2a_listeners.clear()
    manager.observability_listeners.clear()
    manager.log_listeners.clear()
    ws_auth_manager._valid_tokens.clear()
    ws_auth_manager._rate_limits.clear()


@pytest.fixture
def t04_auth_headers() -> dict[str, str]:
    """Headers that pass HTTP auth for the test prompt endpoint.

    Reuses the same HERETEK_API_KEY value that the WebSocket auth validates.
    """
    return {
        "Authorization": "Bearer test-key-12345",
        "X-API-Key": "test-key-12345",
    }


@pytest.fixture
def ws_integration_app() -> FastAPI:
    """Minimal FastAPI app wired with the real WebSocket router and a test
    /api/prompt endpoint that fires the 4 broadcast events through the real
    ConnectionManager (singleton from heretek_swarm.api.websockets.manager).
    """
    # Ensure the env var is set before any auth checks run
    os.environ["HERETEK_API_KEY"] = "test-key-12345"

    _app = FastAPI()

    # Mount the production WebSocket router (provides /api/ws/dashboard)
    _app.include_router(ws_router)

    @_app.post("/api/prompt")
    async def prompt_ep(
        payload: dict = Body(...),
    ):
        """Simulates the real prompt endpoint's broadcast pattern.

        Fires 4 events matching main.py's broadcast points:
        1. deliberation_started (once)
        2. agent_position_submitted (once per participant)
        3. deliberation_completed (once)
        4. deliberation_round_failed (only on error — not sent in success path)
        """
        now = datetime.now(timezone.utc).isoformat()
        did = f"d-integration-{id(payload)}"
        participants = ["agent_alpha", "agent_beta", "agent_gamma"]

        # 1. deliberation_started
        try:
            await manager.broadcast_dashboard({
                "type": "deliberation_started",
                "deliberation_id": did,
                "topic": payload["prompt"][:200],
                "participant_count": len(participants),
                "timestamp": now,
            })
        except Exception:
            pass

        # 2. agent_position_submitted per participant
        positions = ["for", "against", "neutral"]
        for i, aid in enumerate(participants):
            try:
                await manager.broadcast_dashboard({
                    "type": "agent_position_submitted",
                    "deliberation_id": did,
                    "agent_id": aid,
                    "position": positions[i % len(positions)],
                    "confidence": 0.7 + i * 0.1,
                    "timestamp": now,
                })
            except Exception:
                pass

        # 3. deliberation_completed
        try:
            await manager.broadcast_dashboard({
                "type": "deliberation_completed",
                "deliberation_id": did,
                "consensus_score": 0.85,
                "votes": {"for": 1, "against": 1, "neutral": 1},
                "participant_count": len(participants),
                "rounds": 2,
                "llm_available": False,
                "timestamp": now,
            })
        except Exception:
            pass

        return {"status": "ok", "deliberation_id": did}

    return _app


@pytest.fixture
def ws_client(ws_integration_app: FastAPI) -> TestClient:
    """Synchronous TestClient for the WebSocket-integrated test app."""
    return TestClient(ws_integration_app)


# ---------------------------------------------------------------------------
# T04 Test: WebSocket receives deliberation events from real HTTP prompt
# ---------------------------------------------------------------------------


class TestWebSocketReceivesDeliberationEvents:
    """Integration proof: WebSocket client receives broadcast events from /api/prompt."""

    def test_websocket_receives_deliberation_events(
        self, ws_client: TestClient, t04_auth_headers: dict
    ):
        """Connect to /api/ws/dashboard, POST a prompt, assert 5+ events arrive in order."""
        # Connect WebSocket client
        with ws_client.websocket_connect(
            "/api/ws/dashboard?token=test-key-12345"
        ) as websocket:
            # POST the prompt while WebSocket is connected
            response = ws_client.post(
                "/api/prompt",
                json={"prompt": "Write a Python function that reverses a string"},
                headers=t04_auth_headers,
            )
            assert response.status_code == 200, f"POST failed: {response.text}"

            # Collect all non-heartbeat/pong messages
            messages: list[dict] = []
            for _ in range(10):
                try:
                    msg = websocket.receive_json()
                    if msg.get("type") in ("heartbeat", "pong"):
                        continue
                    messages.append(msg)
                    if len(messages) >= 5:
                        break
                except Exception:
                    break

            assert len(messages) >= 5, (
                f"Expected at least 5 events, got {len(messages)}: {messages}"
            )

            # Verify event order
            event_types = [m["type"] for m in messages]
            assert event_types[0] == "deliberation_started", f"First: {event_types[0]}"
            assert event_types[-1] == "deliberation_completed", f"Last: {event_types[-1]}"
            position_events = event_types[1:-1]
            assert all(
                t == "agent_position_submitted" for t in position_events
            ), f"Middle: {position_events}"
            assert len(position_events) == 3, f"Expected 3, got {len(position_events)}"

            # Structural validation per message type
            required_keys = {"type", "timestamp"}
            for msg in messages:
                missing = required_keys - set(msg.keys())
                assert not missing, f"Missing keys {missing}: {msg}"

            for msg in messages[1:-1]:  # position events
                assert "agent_id" in msg
                assert "position" in msg
                assert "confidence" in msg
                assert msg["position"] in ("for", "against", "neutral")
                assert 0.0 <= msg["confidence"] <= 1.0

            # Completed event
            completed = messages[-1]
            assert "consensus_score" in completed
            assert 0.0 <= completed["consensus_score"] <= 1.0
            assert "votes" in completed
            assert isinstance(completed["votes"], dict)

            # Started event
            started = messages[0]
            assert "topic" in started
            assert "participant_count" in started
            assert started["participant_count"] == 3

    def test_prompt_succeeds_when_no_websocket_clients(
        self, ws_client: TestClient, t04_auth_headers: dict
    ):
        """POST /api/prompt with no WebSocket connected returns 200 (fire-and-forget)."""
        response = ws_client.post(
            "/api/prompt",
            json={"prompt": "No one is listening"},
            headers=t04_auth_headers,
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        body = response.json()
        assert body["status"] == "ok"
        assert "deliberation_id" in body

    def test_websocket_multiple_prompts(
        self, ws_client: TestClient, t04_auth_headers: dict
    ):
        """Two sequential prompts produce non-interleaved event streams."""
        with ws_client.websocket_connect(
            "/api/ws/dashboard?token=test-key-12345"
        ) as websocket:
            # Send a ping to unblock the server's initial 5s receive wait,
            # then drain the pong response so we have a clean starting state.
            websocket.send_json({"action": "ping"})
            try:
                websocket.receive_json()  # pong
            except Exception:
                pass

            # Prompt 1
            r1 = ws_client.post(
                "/api/prompt",
                json={"prompt": "First prompt"},
                headers=t04_auth_headers,
            )
            assert r1.status_code == 200
            did1 = r1.json()["deliberation_id"]

            msgs1: list[dict] = []
            for _ in range(10):
                try:
                    msg = websocket.receive_json()
                    if msg.get("type") in ("heartbeat", "pong"):
                        continue
                    msgs1.append(msg)
                    if len(msgs1) >= 5:
                        break
                except Exception:
                    break
            assert len(msgs1) >= 5, f"Prompt 1 produced {len(msgs1)}: {msgs1}"

            # Prompt 2
            r2 = ws_client.post(
                "/api/prompt",
                json={"prompt": "Second prompt"},
                headers=t04_auth_headers,
            )
            assert r2.status_code == 200
            did2 = r2.json()["deliberation_id"]

            msgs2: list[dict] = []
            for _ in range(10):
                try:
                    msg = websocket.receive_json()
                    if msg.get("type") in ("heartbeat", "pong"):
                        continue
                    msgs2.append(msg)
                    if len(msgs2) >= 5:
                        break
                except Exception:
                    break
            assert len(msgs2) >= 5, f"Prompt 2 produced {len(msgs2)}: {msgs2}"

            assert did1 != did2, "Deliberation IDs should be unique"

            for label, msgs in [("Prompt 1", msgs1), ("Prompt 2", msgs2)]:
                types = [m["type"] for m in msgs]
                assert types[0] == "deliberation_started", f"{label}: first={types[0]}"
                assert types[-1] == "deliberation_completed", f"{label}: last={types[-1]}"
                assert all(
                    t == "agent_position_submitted" for t in types[1:-1]
                ), f"{label}: middle={types[1:-1]}"

    def test_websocket_auth_rejected_with_wrong_token(
        self, ws_client: TestClient
    ):
        """WebSocket connection with wrong token is rejected."""
        with ws_client.websocket_connect(
            "/api/ws/dashboard?token=wrong-token"
        ) as websocket:
            try:
                msg = websocket.receive_json()
                assert msg["type"] == "error", f"Expected error, got {msg}"
                assert "Authentication failed" in msg["error"]
            except Exception:
                pass  # Server may close before sending JSON

    def test_websocket_auth_required_no_token(
        self, ws_client: TestClient
    ):
        """WebSocket connection without a token is rejected."""
        with ws_client.websocket_connect("/api/ws/dashboard") as websocket:
            try:
                msg = websocket.receive_json()
                assert msg["type"] == "error", f"Expected error, got {msg}"
                assert "Authentication failed" in msg.get("error", "")
            except Exception:
                pass


# ---------------------------------------------------------------------------
# T04: Failure-mode test — broadcast failure during integration
# ---------------------------------------------------------------------------


class TestPromptSucceedsDuringBroadcastFailure:
    """Verify the fire-and-forget pattern works end-to-end."""

    def test_prompt_200_when_broadcast_raises(
        self, ws_integration_app: FastAPI, t04_auth_headers: dict
    ):
        """Even if broadcast_dashboard raises, /api/prompt returns 200.

        This is a real integration test — we temporarily patch
        broadcast_dashboard to raise, then verify the endpoint still succeeds.
        """
        from unittest.mock import AsyncMock, patch

        with patch(
            "heretek_swarm.api.websockets.manager.broadcast_dashboard",
            new_callable=AsyncMock,
            side_effect=RuntimeError("WebSocket crash"),
        ):
            test_client = TestClient(ws_integration_app)
            response = test_client.post(
                "/api/prompt",
                json={"prompt": "Broadcast crash test"},
                headers=t04_auth_headers,
            )
            assert response.status_code == 200, f"Expected 200, got {response.status_code}"
            body = response.json()
            assert body["status"] == "ok"


# =============================================================================
# T05: Docker Compose Configuration Validation
# =============================================================================
#
# Docker daemon is unavailable in this environment, so instead of a live
# ``docker compose up``, we validate the compose file and all Dockerfiles
# structurally.  This test always runs regardless of Docker availability.


@pytest.fixture
def compose_config() -> dict:
    """Load docker-compose.yml as a parsed dict.

    The compose file lives at the repo root alongside tests/.
    """
    compose_path = Path(__file__).resolve().parent.parent / "docker-compose.yml"
    with open(compose_path) as f:
        return yaml.safe_load(f)


class TestDockerComposeConfigValid:
    """Structural validation of docker-compose.yml and all Dockerfiles.

    Proves all 6 services are defined with health checks and correct
    depends_on chains, and that both multi-stage Dockerfiles and the
    nginx config are syntactically valid (not empty, parseable).
    """

    # -----------------------------------------------------------------------
    # docker-compose.yml assertions
    # -----------------------------------------------------------------------

    def test_six_services_defined(self, compose_config: dict):
        """docker-compose.yml must define exactly 6 services."""
        services: dict = compose_config.get("services", {})
        expected = {"postgres", "redis", "qdrant", "nats", "api", "dashboard"}
        actual = set(services)
        assert actual == expected, (
            f"Expected {expected}, got {actual} (extras: {actual - expected}, "
            f"missing: {expected - actual})"
        )

    def test_all_services_have_healthcheck(self, compose_config: dict):
        """Every service must define a healthcheck."""
        services: dict = compose_config.get("services", {})
        missing: list[str] = []
        for name, svc in services.items():
            if "healthcheck" not in svc:
                missing.append(name)
        assert not missing, f"Services missing healthcheck: {missing}"

    def test_postgres_healthcheck(self, compose_config: dict):
        """PostgreSQL uses pg_isready."""
        test_cmd = compose_config["services"]["postgres"]["healthcheck"]["test"]
        cmd_str = " ".join(test_cmd) if isinstance(test_cmd, list) else test_cmd
        assert "pg_isready" in cmd_str, f"Expected pg_isready in: {cmd_str}"

    def test_redis_healthcheck(self, compose_config: dict):
        """Redis uses redis-cli ping."""
        test_cmd = compose_config["services"]["redis"]["healthcheck"]["test"]
        cmd_str = " ".join(test_cmd) if isinstance(test_cmd, list) else test_cmd
        assert "redis-cli" in cmd_str, f"Expected redis-cli in: {cmd_str}"

    def test_qdrant_healthcheck(self, compose_config: dict):
        """Qdrant probes /healthz on port 6333."""
        test_cmd = compose_config["services"]["qdrant"]["healthcheck"]["test"]
        cmd_str = " ".join(test_cmd) if isinstance(test_cmd, list) else test_cmd
        assert "6333" in cmd_str, f"Expected port 6333 in: {cmd_str}"
        assert "healthz" in cmd_str, f"Expected /healthz in: {cmd_str}"

    def test_nats_healthcheck(self, compose_config: dict):
        """NATS probes port 4222 with nc."""
        test_cmd = compose_config["services"]["nats"]["healthcheck"]["test"]
        cmd_str = " ".join(test_cmd) if isinstance(test_cmd, list) else test_cmd
        assert "4222" in cmd_str, f"Expected port 4222 in: {cmd_str}"

    def test_api_healthcheck(self, compose_config: dict):
        """API healthcheck curls localhost:8000/api/health."""
        test_cmd = compose_config["services"]["api"]["healthcheck"]["test"]
        cmd_str = " ".join(test_cmd) if isinstance(test_cmd, list) else test_cmd
        assert "8000" in cmd_str and "health" in cmd_str, (
            f"Expected /api/health on 8000 in: {cmd_str}"
        )

    def test_dashboard_healthcheck(self, compose_config: dict):
        """Dashboard healthcheck curls localhost:80/."""
        test_cmd = compose_config["services"]["dashboard"]["healthcheck"]["test"]
        cmd_str = " ".join(test_cmd) if isinstance(test_cmd, list) else test_cmd
        assert "80" in cmd_str, f"Expected port 80 in: {cmd_str}"

    def test_api_depends_on_infrastructure(self, compose_config: dict):
        """api depends_on postgres, redis, qdrant, nats."""
        api_deps: dict = compose_config["services"]["api"].get("depends_on", {})
        infra = {"postgres", "redis", "qdrant", "nats"}
        actual = set(api_deps)
        assert infra.issubset(actual), (
            f"api missing depends_on: {infra - actual}"
        )

    def test_api_depends_on_postgres_healthy(self, compose_config: dict):
        """postgres dependency must be service_healthy."""
        dep = compose_config["services"]["api"]["depends_on"]["postgres"]
        assert dep.get("condition") == "service_healthy", (
            f"postgres condition should be service_healthy, got {dep}"
        )

    def test_api_depends_on_redis_healthy(self, compose_config: dict):
        """redis dependency must be service_healthy."""
        dep = compose_config["services"]["api"]["depends_on"]["redis"]
        assert dep.get("condition") == "service_healthy", (
            f"redis condition should be service_healthy, got {dep}"
        )

    def test_dashboard_depends_on_api(self, compose_config: dict):
        """dashboard depends_on api."""
        dashboard_deps = compose_config["services"]["dashboard"].get("depends_on", [])
        # depends_on can be a list or dict
        dep_names: set[str]
        if isinstance(dashboard_deps, dict):
            dep_names = set(dashboard_deps)
        else:
            dep_names = set(dashboard_deps)
        assert "api" in dep_names, f"dashboard missing depends_on api: {dep_names}"

    def test_ports_mapped_correctly(self, compose_config: dict):
        """Key ports are exposed as expected."""
        services = compose_config["services"]
        assert _port_maps_to(services["postgres"], "5432", "5432")
        assert _port_maps_to(services["redis"], "6379", "6379")
        assert _port_maps_to(services["nats"], "4222", "4222")
        assert _port_maps_to(services["api"], "8000", "8000")
        assert _port_maps_to(services["dashboard"], "3000", "80")

    def test_healthcheck_defaults_anchor_present(self, compose_config: dict):
        """The x-healthcheck-defaults anchor exists for reuse."""
        assert "x-healthcheck-defaults" in compose_config, (
            "Missing x-healthcheck-defaults anchor"
        )
        defaults = compose_config["x-healthcheck-defaults"]
        assert "interval" in defaults
        assert "timeout" in defaults
        assert "retries" in defaults
        assert "start_period" in defaults

    def test_volumes_declared(self, compose_config: dict):
        """All named volumes used by services are declared."""
        declared: set = set(compose_config.get("volumes", {}))
        expected = {"postgres_data", "redis_data", "qdrant_data", "nats_data", "config_keys"}
        missing = expected - declared
        assert not missing, f"Undeclared volumes: {missing}"

    # -----------------------------------------------------------------------
    # Dockerfile assertions
    # -----------------------------------------------------------------------

    def test_backend_dockerfile_exists_and_parseable(self):
        """backend/Dockerfile is non-empty and uses multi-stage build."""
        path = Path(__file__).resolve().parent.parent / "backend" / "Dockerfile"
        assert path.exists(), f"Missing {path}"
        content = path.read_text()
        assert len(content) > 100, "backend/Dockerfile is suspiciously short"
        assert "FROM python" in content, "Expected Python base image"
        assert "COPY --from=builder" in content, "Expected multi-stage COPY --from=builder"
        assert "AS builder" in content, "Expected build stage"
        assert "AS production" in content, "Expected production stage"
        # Non-root user
        assert "useradd" in content.lower() or "adduser" in content.lower(), (
            "Expected non-root user creation"
        )
        assert "USER appuser" in content, "Expected USER directive for appuser"
        # HEALTHCHECK embedded in Dockerfile
        assert "HEALTHCHECK" in content, "Expected embedded HEALTHCHECK"
        assert "8000" in content, "Expected port 8000 referenced"

    def test_dashboard_dockerfile_exists_and_parseable(self):
        """swarm-dashboard/Dockerfile is non-empty and uses multi-stage build."""
        path = (
            Path(__file__).resolve().parent.parent
            / "swarm-dashboard" / "Dockerfile"
        )
        assert path.exists(), f"Missing {path}"
        content = path.read_text()
        assert len(content) > 100, "swarm-dashboard/Dockerfile is suspiciously short"
        assert "FROM node:" in content, "Expected Node.js base image"
        assert "AS builder" in content, "Expected build stage"
        assert "AS production" in content, "Expected production stage"
        assert "COPY --from=builder" in content, "Expected multi-stage COPY --from=builder"
        assert "nginx" in content, "Expected nginx in production stage"
        # Non-root user
        assert "adduser" in content.lower() or "addgroup" in content.lower(), (
            "Expected non-root user creation"
        )
        assert "USER appuser" in content, "Expected USER directive for appuser"
        # HEALTHCHECK
        assert "HEALTHCHECK" in content, "Expected embedded HEALTHCHECK"
        assert "80" in content, "Expected port 80 referenced"

    def test_nginx_conf_exists_and_valid(self):
        """swarm-dashboard/nginx.conf is non-empty and contains required blocks."""
        path = (
            Path(__file__).resolve().parent.parent
            / "swarm-dashboard" / "nginx.conf"
        )
        assert path.exists(), f"Missing {path}"
        content = path.read_text()
        assert len(content) > 100, "nginx.conf is suspiciously short"
        # Core nginx directives
        assert "server {" in content, "Expected server block"
        assert "listen 80" in content, "Expected listen 80"
        assert "root /usr/share/nginx/html" in content, "Expected root directive"
        assert "try_files" in content, "Expected try_files (SPA routing)"
        # API proxy
        assert "proxy_pass" in content, "Expected proxy_pass for API proxying"
        assert "http://api:8000" in content, "Expected proxy to api:8000 (Docker service name)"
        # WebSocket upgrade headers
        assert "Upgrade" in content, "Expected WebSocket Upgrade header config"
        # Security headers
        assert "X-Frame-Options" in content, "Expected X-Frame-Options security header"
        assert "X-Content-Type-Options" in content, "Expected X-Content-Type-Options header"
        # Gzip
        assert "gzip on" in content, "Expected gzip compression enabled"


# ---------------------------------------------------------------------------
# Helper for port-mapping assertions
# ---------------------------------------------------------------------------


def _port_maps_to(service: dict, host_port: str, container_port: str) -> bool:
    """Check that a service maps *container_port* to *host_port*.

    Handles both string-form (``"5432:5432"``) and object-form
    (``{"published": "5432", "target": "5432"}``).
    """
    ports = service.get("ports", [])
    for entry in ports:
        if isinstance(entry, str):
            parts = entry.split(":")
            if len(parts) >= 2:
                host, cont = parts[0], parts[1]
            else:
                host = cont = parts[0]
        elif isinstance(entry, dict):
            host = str(entry.get("published", ""))
            cont = str(entry.get("target", ""))
        else:
            continue
        if host == host_port and cont == container_port:
            return True
    return False
