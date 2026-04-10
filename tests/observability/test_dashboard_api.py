"""
Test suite for Observability Dashboard API endpoints.

Tests cover:
- Swarm health endpoint
- Agent metrics endpoint
- Consciousness metrics endpoint
- Alerts endpoint
- Prometheus export endpoint
- WebSocket streaming endpoint
- Rate limiting
- Zero-trust validation
"""

import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient

from src.heretek_swarm.api.observability import (
    router,
    get_metrics_collector,
    get_metrics_stream,
    get_zero_trust,
    check_rate_limit,
    TraceEvent,
    ConnectionManager,
)


@pytest.fixture
def mock_collector():
    """Mock metrics collector."""
    collector = MagicMock()
    collector.collect_swarm_metrics.return_value = MagicMock(
        to_dict=lambda: {
            "total_agents": 5,
            "active_agents": 3,
            "idle_agents": 2,
            "total_tasks_completed": 100,
            "total_tasks_failed": 10,
            "overall_health_score": 75.0,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    )
    collector.collect_agent_metrics.return_value = MagicMock(
        to_dict=lambda: {
            "agent_id": "test-agent",
            "agent_type": "coordinator",
            "tasks_completed": 10,
            "tasks_failed": 2,
            "health_score": 80.0,
            "success_rate": 0.83,
        }
    )
    consciousness_mock = MagicMock()
    consciousness_mock.to_dict = lambda: {
        "phi_score": 0.75,
        "phi_avg": 0.65,
        "phi_max": 0.8,
        "phi_min": 0.5,
        "integration_level": "high",
        "differentiation_level": "moderate",
        "free_energy_avg": 0.3,
        "agent_phi_scores": {"agent-1": 0.8, "agent-2": 0.7},
        "agent_fep_scores": {"agent-1": 0.3, "agent-2": 0.4},
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    consciousness_mock.phi_score = 0.75
    consciousness_mock.phi_avg = 0.65
    consciousness_mock.phi_max = 0.8
    consciousness_mock.phi_min = 0.5
    consciousness_mock.integration_level = "high"
    consciousness_mock.differentiation_level = "moderate"
    consciousness_mock.free_energy_avg = 0.3
    consciousness_mock.agent_phi_scores = {"agent-1": 0.8, "agent-2": 0.7}
    consciousness_mock.agent_fep_scores = {"agent-1": 0.3, "agent-2": 0.4}
    collector.collect_consciousness_metrics.return_value = consciousness_mock
    collector.calculate_health_score.return_value = 75.0
    agent1_mock = MagicMock()
    agent1_mock.to_dict = lambda: {
        "agent_id": "agent-1",
        "agent_type": "coordinator",
        "health_score": 80.0,
        "tasks_completed": 10,
        "tasks_failed": 2,
        "error_count": 1,
        "success_rate": 0.83,
    }
    agent1_mock.health_score = 80.0
    agent1_mock.error_count = 1
    
    agent2_mock = MagicMock()
    agent2_mock.to_dict = lambda: {
        "agent_id": "agent-2",
        "agent_type": "explorer",
        "health_score": 70.0,
        "tasks_completed": 8,
        "tasks_failed": 3,
        "error_count": 2,
        "success_rate": 0.73,
    }
    agent2_mock.health_score = 70.0
    agent2_mock.error_count = 2
    
    collector.get_all_agent_metrics.return_value = {
        "agent-1": agent1_mock,
        "agent-2": agent2_mock,
    }
    collector.get_agent_health_scores.return_value = {"agent-1": 80.0, "agent-2": 70.0}
    return collector


class TestObservabilityAPI:
    """Test Observability API endpoints."""
    
    @pytest.fixture
    def app(self):
        """Create test FastAPI app."""
        app = FastAPI()
        app.include_router(router)
        return app
    
    @pytest.fixture
    def client(self, app):
        """Create test client."""
        return TestClient(app)
    @pytest.fixture
    def mock_stream(self):
        """Mock metrics stream."""
        stream = MagicMock()
        stream.get_metrics_snapshot.return_value = MagicMock(
            to_dict=lambda: {
                "swarm_metrics": {
                    "total_agents": 5,
                    "active_agents": 3,
                    "overall_health_score": 75.0,
                },
                "consciousness_metrics": {
                    "phi_avg": 0.65,
                    "free_energy_avg": 0.3,
                },
                "agent_metrics": {},
                "health_score": 75.0,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        )
        stream.export_prometheus_format.return_value = """# HELP heretek_swarm_health_score Overall swarm health score
# TYPE heretek_swarm_health_score gauge
heretek_swarm_health_score 75.0
# HELP heretek_agents_total Total number of agents
# TYPE heretek_agents_total gauge
heretek_agents_total 5
"""
        return stream
    
    def test_get_swarm_health(self, client, mock_collector):
        """Test GET /api/v1/observability/swarm endpoint."""
        with patch('src.heretek_swarm.api.observability.get_metrics_collector', return_value=mock_collector):
            response = client.get("/api/v1/observability/swarm")
            
            assert response.status_code == 200
            data = response.json()
            assert data["total_agents"] == 5
            assert data["active_agents"] == 3
            assert data["idle_agents"] == 2
            assert data["health_score"] == 75.0
    
    def test_get_agent_metrics(self, client, mock_collector):
        """Test GET /api/v1/observability/agents/{agent_id} endpoint."""
        with patch('src.heretek_swarm.api.observability.get_metrics_collector', return_value=mock_collector):
            response = client.get("/api/v1/observability/agents/test-agent")
            
            assert response.status_code == 200
            data = response.json()
            assert data["agent_id"] == "test-agent"
            assert data["agent_type"] == "coordinator"
            assert data["health_score"] == 80.0
    
    def test_get_all_agents(self, client, mock_collector):
        """Test GET /api/v1/observability/agents endpoint."""
        with patch('src.heretek_swarm.api.observability.get_metrics_collector', return_value=mock_collector):
            response = client.get("/api/v1/observability/agents")
            
            assert response.status_code == 200
            data = response.json()
            assert "agents" in data
            assert len(data["agents"]) == 2
            assert "agent-1" in data["agents"]
            assert "agent-2" in data["agents"]
    
    def test_get_consciousness_metrics(self, client, mock_collector):
        """Test GET /api/v1/observability/consciousness endpoint."""
        with patch('src.heretek_swarm.api.observability.get_metrics_collector', return_value=mock_collector):
            response = client.get("/api/v1/observability/consciousness")
            
            assert response.status_code == 200
            data = response.json()
            assert data["phi_score"] == 0.75
            assert data["phi_avg"] == 0.65
            assert data["integration_level"] == "high"
            assert "agent-1" in data["agent_phi_scores"]
    
    def test_get_agent_consciousness(self, client, mock_collector):
        """Test GET /api/v1/observability/consciousness/agent/{agent_id} endpoint."""
        with patch('src.heretek_swarm.api.observability.get_metrics_collector', return_value=mock_collector):
            response = client.get("/api/v1/observability/consciousness/agent/agent-1")
            
            assert response.status_code == 200
            data = response.json()
            assert data["agent_id"] == "agent-1"
            assert "phi_score" in data
            assert "fep_score" in data
    
    def test_stream_metrics(self, client, mock_collector, mock_stream):
        """Test GET /api/v1/observability/metrics/stream endpoint."""
        with patch('src.heretek_swarm.api.observability.get_metrics_collector', return_value=mock_collector):
            with patch('src.heretek_swarm.api.observability.get_metrics_stream', return_value=mock_stream):
                response = client.get("/api/v1/observability/metrics/stream")
                
                assert response.status_code == 200
                data = response.json()
                assert "swarm_metrics" in data
                assert "consciousness_metrics" in data
                assert "health_score" in data
    
    def test_get_alerts(self, client, mock_collector):
        """Test GET /api/v1/observability/alerts endpoint."""
        with patch('src.heretek_swarm.api.observability.get_metrics_collector', return_value=mock_collector):
            response = client.get("/api/v1/observability/alerts")
            
            assert response.status_code == 200
            data = response.json()
            assert "alerts" in data
            assert "total_alerts" in data
            assert isinstance(data["alerts"], list)
    
    def test_get_prometheus_metrics(self, client, mock_stream):
        """Test GET /api/v1/observability/metrics/prometheus endpoint."""
        with patch('src.heretek_swarm.api.observability.get_metrics_stream', return_value=mock_stream):
            response = client.get("/api/v1/observability/metrics/prometheus")
            
            assert response.status_code == 200
            assert "text/plain" in response.headers["content-type"]
            assert "heretek_swarm_health_score" in response.text
            assert "heretek_agents_total" in response.text
    
    def test_rate_limiting(self, client):
        """Test rate limiting on endpoints."""
        # Reset rate limit state
        from src.heretek_swarm.api.observability import _rate_limit_state
        _rate_limit_state.clear()
        
        # Make many requests quickly
        with patch('src.heretek_swarm.api.observability.RATE_LIMIT_REQUESTS', 5):
            for i in range(5):
                response = client.get("/api/v1/observability/swarm")
                assert response.status_code == 200
            
            # 6th request should be rate limited
            response = client.get("/api/v1/observability/swarm")
            assert response.status_code == 429
            assert "Rate limit exceeded" in response.json()["detail"]
    
    def test_input_validation(self, client):
        """Test zero-trust input validation."""
        # Test with invalid agent_id containing dangerous characters
        response = client.get("/api/v1/observability/agents/<script>alert('xss')</script>")
        
        # Should either validate or return 404, not crash
        assert response.status_code in [400, 404]
    
    def test_trace_event_creation(self):
        """Test TraceEvent class."""
        event = TraceEvent(
            event_type="llm_call",
            agent_id="test-agent",
            data={"prompt": "test", "completion": "result"},
            duration=150.0,
        )
        
        assert event.event_type == "llm_call"
        assert event.agent_id == "test-agent"
        assert event.duration == 150.0
        assert event.id.startswith("llm_call-test-agent-")
    
    def test_trace_event_to_dict(self):
        """Test TraceEvent serialization."""
        event = TraceEvent(
            event_type="tool_call",
            agent_id="agent-1",
            data={"tool": "search", "query": "test"},
        )
        
        result = event.to_dict()
        
        assert result["type"] == "tool_call"
        assert result["agent_id"] == "agent-1"
        assert "timestamp" in result
        assert "id" in result
    
    def test_connection_manager(self):
        """Test ConnectionManager class."""
        manager = ConnectionManager()
        mock_websocket = AsyncMock()
        
        # Test connect
        asyncio_run(manager.connect(mock_websocket, "agent-1"))
        assert "agent-1" in manager.active_connections
        
        # Test disconnect
        asyncio_run(manager.disconnect(mock_websocket, "agent-1"))
        assert "agent-1" not in manager.active_connections
    
    def test_get_traces(self, client):
        """Test GET /api/v1/observability/traces endpoint."""
        response = client.get("/api/v1/observability/traces")
        
        assert response.status_code == 200
        data = response.json()
        assert "events" in data
        assert "total" in data
    
    def test_get_trace_not_found(self, client):
        """Test GET /api/v1/observability/traces/{trace_id} with non-existent trace."""
        response = client.get("/api/v1/observability/traces/non-existent-trace")
        
        assert response.status_code == 200
        data = response.json()
        assert "error" in data
        assert data["error"] == "Trace not found"
    
    def test_clear_traces(self, client):
        """Test DELETE /api/v1/observability/traces/{agent_id} endpoint."""
        response = client.delete("/api/v1/observability/traces/test-agent")
        
        assert response.status_code == 200
        data = response.json()
        assert "agent_id" in data
        assert "cleared" in data
    
    def test_get_legacy_metrics(self, client):
        """Test GET /api/v1/observability/metrics/legacy endpoint."""
        response = client.get("/api/v1/observability/metrics/legacy")
        
        assert response.status_code == 200
        data = response.json()
        assert "total_events" in data
        assert "events_by_type" in data
        assert "events_by_agent" in data


def asyncio_run(coro):
    """Helper to run async code in tests."""
    import asyncio
    try:
        return asyncio.get_event_loop().run_until_complete(coro)
    except RuntimeError:
        # Create new event loop if needed
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        return loop.run_until_complete(coro)


class TestZeroTrustValidation:
    """Test zero-trust validation in API endpoints."""
    
    @pytest.fixture
    def app(self):
        """Create test FastAPI app."""
        app = FastAPI()
        app.include_router(router)
        return app
    
    @pytest.fixture
    def client(self, app):
        """Create test client."""
        return TestClient(app)
    
    def test_audit_logging(self, client, mock_collector):
        """Test that audit logging is performed."""
        with patch('src.heretek_swarm.api.observability.get_metrics_collector', return_value=mock_collector):
            with patch('src.heretek_swarm.api.observability.get_zero_trust') as mock_validator:
                mock_instance = MagicMock()
                mock_validator.return_value = mock_instance
                
                response = client.get("/api/v1/observability/swarm")
                
                assert response.status_code == 200
                # Verify audit_logger.log was called
                mock_instance.audit_logger.log.assert_called()
    
    def test_validator_initialization(self):
        """Test zero-trust validator initialization."""
        from src.heretek_swarm.security.zero_trust import ZeroTrustValidator
        
        validator = ZeroTrustValidator()
        assert validator is not None


class TestMetricsCollectorSingleton:
    """Test metrics collector singleton pattern."""
    
    def test_get_metrics_collector_singleton(self):
        """Test that get_metrics_collector returns singleton."""
        collector1 = get_metrics_collector()
        collector2 = get_metrics_collector()
        
        assert collector1 is collector2
    
    def test_get_metrics_stream_singleton(self, mock_collector):
        """Test that get_metrics_stream returns singleton."""
        with patch('src.heretek_swarm.api.observability._metrics_collector', mock_collector):
            stream1 = get_metrics_stream()
            stream2 = get_metrics_stream()
            
            assert stream1 is stream2


class TestRateLimiting:
    """Test rate limiting functionality."""
    
    def test_check_rate_limit_first_request(self):
        """Test that first request passes rate limit."""
        from src.heretek_swarm.api.observability import _rate_limit_state
        _rate_limit_state.clear()
        
        result = check_rate_limit("test-client")
        assert result is True
    
    def test_check_rate_limit_exceeded(self):
        """Test rate limit enforcement."""
        from src.heretek_swarm.api.observability import _rate_limit_state, RATE_LIMIT_REQUESTS
        _rate_limit_state.clear()
        
        # Make requests up to limit
        for i in range(RATE_LIMIT_REQUESTS):
            check_rate_limit("test-client-2")
        
        # Next request should be denied
        result = check_rate_limit("test-client-2")
        assert result is False
    
    def test_check_rate_limit_window_expiry(self):
        """Test that rate limit window expires."""
        from src.heretek_swarm.api.observability import _rate_limit_state
        from datetime import timedelta
        
        _rate_limit_state.clear()
        
        # Add old timestamps that should expire
        old_time = datetime.now(timezone.utc) - timedelta(seconds=120)
        _rate_limit_state["test-client-3"] = [old_time] * 200
        
        # Should pass because old entries expire
        result = check_rate_limit("test-client-3")
        assert result is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
