"""
Tests for the chat API endpoint.

Tests the POST /api/agents/{agent_id}/chat endpoint which routes messages
through the triad deliberation mechanism (alpha/beta/charlie) and returns
a synthesized response with per-agent contributions.
"""

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from heretek_swarm.actors.base.core import AgentActor
from heretek_swarm.api.agents.chat import (
    ChatRequest,
    ChatResponse,
    Contribution,
    _get_agent_role,
    _synthesize_response,
    router,
)

# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def mock_supervisor():
    """Create a mock supervisor with triad agents."""
    supervisor = MagicMock()
    supervisor.actors = {
        "steward": MagicMock(spec=AgentActor),
        "alpha": MagicMock(spec=AgentActor),
        "beta": MagicMock(spec=AgentActor),
        "charlie": MagicMock(spec=AgentActor),
    }
    # Make send_to_actor return successfully for triad agents
    for agent_id in ["alpha", "beta", "charlie"]:
        supervisor.actors[agent_id].send_to_actor = AsyncMock(return_value="msg-id-123")
    return supervisor


@pytest.fixture
def mock_supervisor_with_no_triad():
    """Create a mock supervisor with only steward (no triad)."""
    supervisor = MagicMock()
    supervisor.actors = {
        "steward": MagicMock(spec=AgentActor),
    }
    return supervisor


@pytest.fixture
def mock_auth():
    """Mock authentication dependency."""
    async def verify_auth():
        return "test-user"
    return verify_auth


@pytest.fixture
def test_client(mock_supervisor, mock_auth):
    """Create a test client with mocked dependencies."""
    from fastapi import FastAPI

    from heretek_swarm.api.agents_management import router as agents_router
    from heretek_swarm.gateway.auth import verify_auth

    app = FastAPI()
    app.include_router(agents_router)

    # Override dependencies
    from heretek_swarm.api.agents.chat import _get_supervisor

    app.dependency_overrides[_get_supervisor] = lambda: mock_supervisor
    app.dependency_overrides[verify_auth] = mock_auth

    from fastapi.testclient import TestClient
    return TestClient(app)


@pytest.fixture
def test_client_no_auth(mock_supervisor):
    """Create a test client without auth override (will return 401)."""
    from fastapi import FastAPI

    from heretek_swarm.api.agents_management import router as agents_router

    app = FastAPI()
    app.include_router(agents_router)

    # Override supervisor but NOT auth
    from heretek_swarm.api.agents.chat import _get_supervisor

    app.dependency_overrides[_get_supervisor] = lambda: mock_supervisor

    from fastapi.testclient import TestClient
    return TestClient(app)


# =============================================================================
# Test: Endpoint Registration (401 without auth)
# =============================================================================


class TestChatEndpointAuth:
    """Test authentication requirements for chat endpoint."""

    def test_endpoint_returns_401_without_auth(self, test_client_no_auth):
        """Verify that the endpoint returns 401 when authentication is missing."""
        response = test_client_no_auth.post(
            "/api/agents/steward/chat",
            json={"message": "Hello"},
        )
        # Should return 401 or 403 (auth error)
        assert response.status_code in [401, 403]


# =============================================================================
# Test: Unknown Agent (404)
# =============================================================================


class TestChatEndpointAgentLookup:
    """Test agent lookup behavior."""

    def test_returns_404_for_unknown_agent(self, test_client):
        """Verify that requesting chat with unknown agent returns 404."""
        response = test_client.post(
            "/api/agents/unknown-agent/chat",
            json={"message": "Hello"},
        )
        assert response.status_code == 404
        assert "unknown-agent" in response.json()["detail"]


# =============================================================================
# Test: Successful Chat Response
# =============================================================================


class TestChatEndpointResponse:
    """Test successful chat response structure."""

    def test_returns_response_and_contributions(self, test_client):
        """Verify that successful chat returns response and contributions."""
        # Mock the vote response collection to return contributions
        with patch(
            "heretek_swarm.api.agents.chat._collect_vote_responses",
            new_callable=AsyncMock,
            return_value=(
                [
                    Contribution(
                        agent_id="alpha",
                        role="Primary Analyst",
                        content="My analysis",
                        timestamp=datetime.now(UTC).isoformat(),
                    ),
                    Contribution(
                        agent_id="beta",
                        role="Secondary Analyst",
                        content="My critique",
                        timestamp=datetime.now(UTC).isoformat(),
                    ),
                ],
                False,  # timed_out
            ),
        ):
            response = test_client.post(
                "/api/agents/steward/chat",
                json={"message": "What is the meaning of life?"},
            )

        assert response.status_code == 200
        data = response.json()

        # Verify response structure
        assert "response" in data
        assert "contributions" in data
        assert "deliberation_id" in data
        assert "timeout" in data

        # Verify contributions structure
        assert isinstance(data["contributions"], list)
        assert len(data["contributions"]) == 2

        # Verify contribution fields
        for contrib in data["contributions"]:
            assert "agent_id" in contrib
            assert "role" in contrib
            assert "content" in contrib
            assert "timestamp" in contrib

        # Verify deliberation_id format
        assert data["deliberation_id"].startswith("chat_")

        # Verify no timeout
        assert data["timeout"] is False

    def test_sends_deliberation_request_to_triad(self, test_client, mock_supervisor):
        """Verify that deliberation requests are sent to triad agents."""
        with patch(
            "heretek_swarm.api.agents.chat._collect_vote_responses",
            new_callable=AsyncMock,
            return_value=([], False),
        ):
            test_client.post(
                "/api/agents/steward/chat",
                json={"message": "Test message"},
            )

        # Verify send_to_actor was called for each triad agent
        for agent_id in ["alpha", "beta", "charlie"]:
            mock_supervisor.actors[agent_id].send_to_actor.assert_called()
            call_args = mock_supervisor.actors[agent_id].send_to_actor.call_args
            assert call_args.kwargs["message_type"] == "deliberation_request"


# =============================================================================
# Test: Graceful Timeout
# =============================================================================


class TestChatEndpointTimeout:
    """Test timeout behavior."""

    def test_times_out_gracefully(self, test_client):
        """Verify that the endpoint handles timeout gracefully."""
        with patch(
            "heretek_swarm.api.agents.chat._collect_vote_responses",
            new_callable=AsyncMock,
            return_value=([], True),  # timed_out = True
        ):
            response = test_client.post(
                "/api/agents/steward/chat",
                json={"message": "Timeout test"},
            )

        assert response.status_code == 200
        data = response.json()

        # Verify timeout flag is set
        assert data["timeout"] is True

        # Should still return a response (fallback synthesis)
        assert "response" in data

    def test_partial_contributions_on_timeout(self, test_client):
        """Verify that partial contributions are returned even on timeout."""
        with patch(
            "heretek_swarm.api.agents.chat._collect_vote_responses",
            new_callable=AsyncMock,
            return_value=(
                [
                    Contribution(
                        agent_id="alpha",
                        role="Primary Analyst",
                        content="Alpha's response",
                        timestamp=datetime.now(UTC).isoformat(),
                    ),
                ],
                True,  # timed_out = True (got partial response)
            ),
        ):
            response = test_client.post(
                "/api/agents/steward/chat",
                json={"message": "Partial timeout test"},
            )

        assert response.status_code == 200
        data = response.json()

        # Verify timeout flag is set
        assert data["timeout"] is True

        # Should still have one contribution
        assert len(data["contributions"]) == 1
        assert data["contributions"][0]["agent_id"] == "alpha"


# =============================================================================
# Test: Helper Functions
# =============================================================================


class TestHelperFunctions:
    """Test helper functions."""

    def test_get_agent_role(self):
        """Test agent role mapping."""
        assert _get_agent_role("alpha") == "Primary Analyst"
        assert _get_agent_role("beta") == "Secondary Analyst"
        assert _get_agent_role("charlie") == "Challenger"
        assert _get_agent_role("steward") == "Coordinator"
        assert _get_agent_role("unknown") == "unknown"

    def test_synthesize_response_empty(self):
        """Test response synthesis with no contributions."""
        result = _synthesize_response([], "Test message")
        assert "triad deliberation did not produce a response" in result
        assert "Test message" in result

    def test_synthesize_response_single(self):
        """Test response synthesis with single contribution."""
        contributions = [
            Contribution(
                agent_id="alpha",
                role="Primary Analyst",
                content="The answer is 42",
                timestamp=datetime.now(UTC).isoformat(),
            ),
        ]
        result = _synthesize_response(contributions, "What is the answer?")
        assert "42" in result

    def test_synthesize_response_multiple(self):
        """Test response synthesis with multiple contributions."""
        contributions = [
            Contribution(
                agent_id="alpha",
                role="Primary Analyst",
                content="Alpha thinks 42",
                timestamp=datetime.now(UTC).isoformat(),
            ),
            Contribution(
                agent_id="beta",
                role="Secondary Analyst",
                content="Beta agrees",
                timestamp=datetime.now(UTC).isoformat(),
            ),
            Contribution(
                agent_id="charlie",
                role="Challenger",
                content="Charlie challenges",
                timestamp=datetime.now(UTC).isoformat(),
            ),
        ]
        result = _synthesize_response(contributions, "Is it 42?")

        # Should contain synthesis header
        assert "3 agents" in result

        # Should contain all contributions
        assert "Alpha thinks 42" in result
        assert "Beta agrees" in result
        assert "Charlie challenges" in result


# =============================================================================
# Test: ChatRequest/ChatResponse Models
# =============================================================================


class TestModels:
    """Test Pydantic models."""

    def test_chat_request_validation(self):
        """Test ChatRequest model validation."""
        # Valid request
        req = ChatRequest(message="Hello, agent!")
        assert req.message == "Hello, agent!"

    def test_chat_response_model(self):
        """Test ChatResponse model."""
        contributions = [
            Contribution(
                agent_id="alpha",
                role="Primary",
                content="Test",
                timestamp="2024-01-01T00:00:00Z",
            ),
        ]
        response = ChatResponse(
            response="Test response",
            contributions=contributions,
            deliberation_id="chat_123",
            timeout=False,
        )
        assert response.response == "Test response"
        assert len(response.contributions) == 1
        assert response.timeout is False

    def test_contribution_model(self):
        """Test Contribution model."""
        contrib = Contribution(
            agent_id="beta",
            role="Secondary",
            content="Beta's analysis",
            timestamp="2024-01-01T00:00:00Z",
        )
        assert contrib.agent_id == "beta"
        assert contrib.role == "Secondary"
        assert contrib.content == "Beta's analysis"


# =============================================================================
# Test: Router Registration
# =============================================================================


class TestRouterRegistration:
    """Test that router is properly configured."""

    def test_router_has_chat_endpoint(self):
        """Verify the router includes the chat endpoint."""
        # Check that we have routes defined
        assert len(router.routes) > 0

        # Find the chat route - path is /{agent_id}/chat (prefix /api/agents added by router)
        chat_routes = [r for r in router.routes if "/chat" in str(r.path)]
        assert len(chat_routes) > 0

        # Verify it's a POST endpoint
        chat_route = chat_routes[0]
        assert hasattr(chat_route, "methods")
        assert "POST" in chat_route.methods
        # Full path will be /api/agents/{agent_id}/chat when included with prefix
        assert "/{agent_id}/chat" in str(chat_route.path)
