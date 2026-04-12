"""
Heretek Swarm Load Testing Framework - Locust

Performance benchmarking for the Heretek Swarm multi-agent system.
Target: p95 latency < 100ms for API endpoints

Usage:
    locust -f tests/load/locustfile.py --host=http://localhost:8000
    locust -f tests/load/locustfile.py --host=http://localhost:8000 --headless -u 100 -r 10 -t 60s
"""

import random
from uuid import uuid4

from locust import HttpUser, between, events, task

# =============================================================================
# Custom Load Shapes
# =============================================================================

class SpikeLoadShape:
    """
    Spike Load Test - Sudden increase in load
    
    Tests system behavior under sudden traffic surge.
    Expected: System should handle spike gracefully, recover after spike ends.
    """
    stages = [
        {"duration": 60, "users": 10, "spawn_rate": 2},    # Baseline
        {"duration": 120, "users": 100, "spawn_rate": 20},  # Spike
        {"duration": 180, "users": 100, "spawn_rate": 0},   # Hold
        {"duration": 240, "users": 10, "spawn_rate": -20},  # Recovery
        {"duration": 300, "users": 10, "spawn_rate": 0},    # Post-spike baseline
    ]


class EnduranceLoadShape:
    """
    Endurance Load Test - Sustained load over extended period
    
    Tests for memory leaks, resource exhaustion, degradation over time.
    Expected: Stable performance throughout test duration.
    """
    stages = [
        {"duration": 300, "users": 50, "spawn_rate": 5},    # Ramp up
        {"duration": 3600, "users": 50, "spawn_rate": 0},    # Hold for 1 hour
        {"duration": 3900, "users": 0, "spawn_rate": -10},   # Ramp down
    ]


class BreakingPointLoadShape:
    """
    Breaking Point Test - Find system limits
    
    Gradually increases load until system fails.
    Expected: Identify maximum sustainable load and failure mode.
    """
    stages = [
        {"duration": 120, "users": 10, "spawn_rate": 2},
        {"duration": 240, "users": 50, "spawn_rate": 5},
        {"duration": 360, "users": 100, "spawn_rate": 10},
        {"duration": 480, "users": 200, "spawn_rate": 20},
        {"duration": 600, "users": 500, "spawn_rate": 50},
        {"duration": 720, "users": 1000, "spawn_rate": 100},
    ]


class RecoveryLoadShape:
    """
    Recovery Test - System recovery after failure
    
    Tests system ability to recover after overload.
    Expected: System should recover and return to normal operation.
    """
    stages = [
        {"duration": 60, "users": 20, "spawn_rate": 5},     # Normal load
        {"duration": 180, "users": 500, "spawn_rate": 50},  # Overload
        {"duration": 240, "users": 20, "spawn_rate": -50},  # Recovery
        {"duration": 360, "users": 20, "spawn_rate": 0},    # Verify recovery
    ]


# =============================================================================
# Locust User Classes
# =============================================================================

class APIUser(HttpUser):
    """
    Simulates API client behavior
    
    Tests: Authentication, agent operations, memory operations, consensus
    """
    wait_time = between(0.5, 2)  # Realistic user think time
    host = "http://localhost:8000"

    # Test data
    test_agent_id = None
    test_memory_id = None
    auth_token = None

    def on_start(self):
        """Called when simulated user starts"""
        # Try to get auth token if available
        self.auth_token = self.client.get("/api/auth/token").json().get("token", None)

    @task(3)
    def health_check(self):
        """Test health endpoint - most common operation"""
        self.client.get("/api/health", name="Health Check")

    @task(2)
    def get_agents(self):
        """Test agents listing endpoint"""
        headers = {}
        if self.auth_token:
            headers["Authorization"] = f"Bearer {self.auth_token}"

        self.client.get("/api/agents", headers=headers, name="List Agents")

    @task(2)
    def get_agent_status(self):
        """Test individual agent status"""
        agent_id = f"agent-{random.randint(1, 23)}"
        headers = {}
        if self.auth_token:
            headers["Authorization"] = f"Bearer {self.auth_token}"

        self.client.get(f"/api/agents/{agent_id}/status", headers=headers, name="Agent Status")

    @task(1)
    def search_memory(self):
        """Test memory search endpoint"""
        headers = {}
        if self.auth_token:
            headers["Authorization"] = f"Bearer {self.auth_token}"

        queries = [
            "test query",
            "agent memory",
            "conversation history",
            "task context",
            "knowledge base"
        ]

        self.client.post(
            "/api/memory/search",
            json={"query": random.choice(queries), "limit": 10},
            headers=headers,
            name="Search Memory"
        )

    @task(1)
    def get_consciousness_metrics(self):
        """Test consciousness metrics endpoint"""
        agent_id = f"agent-{random.randint(1, 23)}"
        headers = {}
        if self.auth_token:
            headers["Authorization"] = f"Bearer {self.auth_token}"

        self.client.get(f"/api/agents/{agent_id}/consciousness", headers=headers, name="Consciousness Metrics")

    @task(1)
    def get_event_mesh_stats(self):
        """Test event mesh statistics"""
        headers = {}
        if self.auth_token:
            headers["Authorization"] = f"Bearer {self.auth_token}"

        self.client.get("/api/eventmesh/stats", headers=headers, name="Event Mesh Stats")


class HeavyUser(HttpUser):
    """
    Simulates heavy API client behavior
    
    Tests: Complex operations, large payloads, multi-step workflows
    """
    wait_time = between(1, 5)  # Longer think time for complex operations
    host = "http://localhost:8000"

    auth_token = None

    def on_start(self):
        """Called when simulated user starts"""
        self.auth_token = self.client.get("/api/auth/token").json().get("token", None)

    @task(2)
    def create_agent(self):
        """Test agent creation - write operation"""
        headers = {}
        if self.auth_token:
            headers["Authorization"] = f"Bearer {self.auth_token}"

        agent_data = {
            "agent_id": f"test-agent-{uuid4()}",
            "agent_type": "worker",
            "character": {
                "name": f"Test Agent {random.randint(1, 100)}",
                "description": "Load test agent"
            }
        }

        self.client.post(
            "/api/agents",
            json=agent_data,
            headers=headers,
            name="Create Agent"
        )

    @task(2)
    def store_memory(self):
        """Test memory storage - write operation"""
        headers = {}
        if self.auth_token:
            headers["Authorization"] = f"Bearer {self.auth_token}"

        memory_data = {
            "agent_id": f"agent-{random.randint(1, 23)}",
            "content": f"Load test memory content {uuid4()}",
            "memory_type": "episodic",
            "tags": ["load-test", "automated"],
            "importance_score": random.uniform(0.1, 0.9)
        }

        self.client.post(
            "/api/memory/store",
            json=memory_data,
            headers=headers,
            name="Store Memory"
        )

    @task(1)
    def send_agent_message(self):
        """Test agent message sending - complex operation"""
        headers = {}
        if self.auth_token:
            headers["Authorization"] = f"Bearer {self.auth_token}"

        message_data = {
            "target_agent": f"agent-{random.randint(1, 23)}",
            "message_type": "request",
            "content": {
                "task": f"Process data batch {random.randint(1, 100)}",
                "priority": random.choice(["low", "medium", "high"]),
                "payload": {"data": list(range(random.randint(10, 100)))}
            }
        }

        self.client.post(
            "/api/agents/message",
            json=message_data,
            headers=headers,
            name="Send Agent Message"
        )

    @task(1)
    def initiate_consensus(self):
        """Test consensus initiation - multi-agent operation"""
        headers = {}
        if self.auth_token:
            headers["Authorization"] = f"Bearer {self.auth_token}"

        consensus_data = {
            "proposal_id": f"prop-{uuid4()}",
            "description": f"Load test consensus {random.randint(1, 100)}",
            "participants": [f"agent-{i}" for i in range(1, random.randint(4, 10))],
            "threshold": 0.7
        }

        self.client.post(
            "/api/consensus/initiate",
            json=consensus_data,
            headers=headers,
            name="Initiate Consensus"
        )


class WebSocketUser(HttpUser):
    """
    Simulates WebSocket client behavior
    
    Tests: Real-time communication, message streaming
    """
    wait_time = between(0.1, 1)  # Short wait time for real-time ops
    host = "ws://localhost:8000"

    @task
    def connect_and_listen(self):
        """Test WebSocket connection and message reception"""
        # Note: Locust WebSocket support requires locust-websocket package
        # This is a placeholder for WebSocket testing
        pass


# =============================================================================
# Event Handlers
# =============================================================================

@events.request.add_listener
def on_request(request_type, name, response_time, response_length, exception, **kwargs):
    """Log slow requests"""
    if response_time > 1000:  # > 1 second
        print(f"SLOW REQUEST: {name} took {response_time}ms")


@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """Called when load test starts"""
    print(f"Load test starting - Target host: {environment.host}")
    print(f"Performance targets: p95 < 100ms, p99 < 500ms")


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """Called when load test stops"""
    stats = environment.stats

    print("\n" + "=" * 60)
    print("LOAD TEST RESULTS")
    print("=" * 60)

    # Overall statistics
    total_requests = stats.total.num_requests
    total_failures = stats.total.num_failures
    failure_rate = (total_failures / total_requests * 100) if total_requests > 0 else 0

    print(f"Total Requests: {total_requests}")
    print(f"Total Failures: {total_failures}")
    print(f"Failure Rate: {failure_rate:.2f}%")

    # Latency percentiles
    print(f"\nLatency Percentiles:")
    print(f"  p50:  {stats.total.get_response_time_percentile(0.5):.2f}ms")
    print(f"  p95:  {stats.total.get_response_time_percentile(0.95):.2f}ms")
    print(f"  p99:  {stats.total.get_response_time_percentile(0.99):.2f}ms")
    print(f"  Avg:  {stats.total.avg_response_time:.2f}ms")

    # Performance assessment
    p95 = stats.total.get_response_time_percentile(0.95)
    p99 = stats.total.get_response_time_percentile(0.99)

    print(f"\nPerformance Assessment:")
    if p95 < 100 and p99 < 500:
        print("  ✅ PASS - All latency targets met")
    elif p95 < 200 and p99 < 1000:
        print("  ⚠️  WARNING - Latency targets exceeded but acceptable")
    else:
        print("  ❌ FAIL - Latency targets significantly exceeded")

    print("=" * 60 + "\n")


# =============================================================================
# Run Configuration
# =============================================================================

if __name__ == "__main__":
    import os
    os.system("locust -f tests/load/locustfile.py --host=http://localhost:8000")
