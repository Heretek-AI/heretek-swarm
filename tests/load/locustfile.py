"""
Load testing framework for 1,000+ concurrent agents.

Agent Gamma - QA and Validation Lead
Uses Locust for scalable load testing of the Heretek Swarm system.

Run with:
    locust -f tests/load/locustfile.py --headless -u 1000 -r 50 -t 5m --host http://localhost:8000

Or with UI:
    locust -f tests/load/locustfile.py --host http://localhost:8000
"""

import json
import os
import random
import time
from dataclasses import dataclass
from typing import Any, Optional

from locust import HttpUser, between, events, task
from locust.runners import MasterRunner, WorkerRunner


# ============== CONFIGURATION ==============

CONCURRENT_AGENT_TARGET = 1000
MESSAGE_LATENCY_BASELINE_MS = 100
API_HOST = os.getenv("LOCUST_HOST", "http://localhost:8000")
API_KEY = os.getenv("HERETEK_API_KEY", "")


@dataclass
class AgentProfile:
    """Profile for load testing agent behavior."""
    agent_type: str
    message_rate: float  # messages per second
    task_complexity: str  # simple, medium, complex
    capabilities: list[str]


# Agent profiles matching the 23 agent types
AGENT_PROFILES = [
    AgentProfile("steward", 0.5, "complex", ["orchestration", "authorization"]),
    AgentProfile("alpha", 1.0, "complex", ["deliberation", "consensus"]),
    AgentProfile("beta", 1.0, "complex", ["critique", "analysis"]),
    AgentProfile("charlie", 1.0, "complex", ["validation", "arbitration"]),
    AgentProfile("historian", 2.0, "simple", ["memory", "retrieval"]),
    AgentProfile("metis", 1.0, "complex", ["planning", "strategy"]),
    AgentProfile("empath", 1.5, "medium", ["sentiment", "emotional"]),
    AgentProfile("perceiver", 2.0, "medium", ["sensing", "multimodal"]),
    AgentProfile("echo", 1.5, "simple", ["communication"]),
    AgentProfile("explorer", 2.0, "medium", ["discovery", "search"]),
    AgentProfile("examiner", 1.0, "medium", ["review", "audit"]),
    AgentProfile("dreamer", 0.5, "complex", ["creative", "generation"]),
    AgentProfile("coder", 0.5, "complex", ["code_generation", "refactoring"]),
    AgentProfile("sentinel", 3.0, "simple", ["monitoring", "alerting"]),
    AgentProfile("sentinel-prime", 2.0, "medium", ["security", "threat"]),
    AgentProfile("arbiter", 0.5, "medium", ["resolution", "judgment"]),
    AgentProfile("coordinator", 2.0, "medium", ["scheduling", "delegation"]),
    AgentProfile("nexus", 1.5, "medium", ["external", "integration"]),
    AgentProfile("catalyst", 1.0, "medium", ["change", "transition"]),
    AgentProfile("chronos", 2.0, "simple", ["temporal", "scheduling"]),
    AgentProfile("prism", 1.0, "complex", ["perspective", "multi"]),
    AgentProfile("habit-forge", 1.5, "medium", ["behavior", "pattern"]),
    AgentProfile("perceiver-plus", 1.0, "complex", ["analytics", "advanced"]),
]


class HeretekSwarmUser(HttpUser):
    """
    Simulated agent user for load testing.
    
    Each user represents one agent in the swarm, making requests
    at rates consistent with their agent profile.
    """
    
    abstract = True  # Don't instantiate directly
    host = API_HOST

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.agent_id: str = ""
        self.agent_profile: AgentProfile | None = None
        self.session_state: dict[str, Any] = {}

    def _get_headers(self) -> dict:
        """Get API headers."""
        headers = {"Content-Type": "application/json"}
        if API_KEY:
            headers["Authorization"] = f"Bearer {API_KEY}"
        return headers

    def on_start(self) -> None:
        """Initialize agent session."""
        # Select random agent profile
        self.agent_profile = random.choice(AGENT_PROFILES)
        self.agent_id = f"load-agent-{random.randint(1, 10000)}"
        
        # Set wait time based on profile message rate
        self.wait_time = between(
            0.5 / self.agent_profile.message_rate,
            2.0 / self.agent_profile.message_rate,
        )
        
        # Register agent
        self.register_agent()
    
    def register_agent(self) -> None:
        """Register this agent with the system."""
        try:
            with self.client.post(
                "/api/agents/register",
                json={
                    "agent_id": self.agent_id,
                    "agent_type": self.agent_profile.agent_type if self.agent_profile else "steward",
                    "capabilities": self.agent_profile.capabilities if self.agent_profile else [],
                },
                headers=self._get_headers(),
                catch_response=True,
            ) as response:
                if response.status_code in [200, 201]:
                    response.success()
                else:
                    response.failure(f"Registration failed: {response.status_code}")
        except Exception as e:
            # API might not be available, continue anyway
            pass

    def on_stop(self) -> None:
        """Clean up agent session."""
        try:
            self.client.post(
                f"/api/agents/{self.agent_id}/deregister",
                headers=self._get_headers(),
                catch_response=True,
            )
        except Exception:
            pass


class MessageSendingUser(HeretekSwarmUser):
    """User that sends A2A messages."""
    
    abstract = True

    @task(10)
    def send_task_message(self) -> None:
        """Send a task-related message."""
        payload = {
            "sender_id": self.agent_id,
            "receiver_id": f"agent-{random.randint(1, 100)}",
            "message_type": "task_request",
            "payload": {
                "task": random.choice(["analyze", "execute", "query", "report"]),
                "priority": random.choice(["low", "medium", "high"]),
            },
        }

        with self.client.post(
            "/api/messages/send",
            json=payload,
            headers=self._get_headers(),
            catch_response=True,
        ) as response:
            elapsed_ms = response.elapsed.total_seconds() * 1000
            if response.status_code == 200:
                if elapsed_ms > MESSAGE_LATENCY_BASELINE_MS:
                    response.failure(f"Latency {elapsed_ms:.0f}ms exceeds baseline")
                else:
                    response.success()
            else:
                response.failure(f"Status {response.status_code}")

    @task(5)
    def send_consensus_message(self) -> None:
        """Send a consensus-related message (for triad agents)."""
        if self.agent_profile and self.agent_profile.agent_type in ["alpha", "beta", "charlie", "steward"]:
            payload = {
                "sender_id": self.agent_id,
                "message_type": "deliberation_vote",
                "payload": {
                    "proposal_id": f"prop-{random.randint(1, 1000)}",
                    "vote": random.choice(["approve", "reject", "abstain"]),
                },
            }
            self.client.post(
                "/api/consensus/vote",
                json=payload,
                headers=self._get_headers(),
                catch_response=True,
            )


class TaskExecutionUser(HeretekSwarmUser):
    """User that executes tasks."""
    
    abstract = True

    @task(8)
    def execute_simple_task(self) -> None:
        """Execute a simple task."""
        if self.agent_profile and self.agent_profile.task_complexity in ["simple", "medium"]:
            self.client.post(
                "/api/tasks/execute",
                json={
                    "task_type": "simple",
                    "agent_id": self.agent_id,
                },
                headers=self._get_headers(),
                catch_response=True,
            )

    @task(3)
    def execute_complex_task(self) -> None:
        """Execute a complex task (longer duration)."""
        if self.agent_profile and self.agent_profile.task_complexity == "complex":
            self.client.post(
                "/api/tasks/execute",
                json={
                    "task_type": "complex",
                    "agent_id": self.agent_id,
                },
                headers=self._get_headers(),
                catch_response=True,
            )


class MemoryOperationUser(HeretekSwarmUser):
    """User that performs memory operations."""
    
    abstract = True

    @task(5)
    def store_memory(self) -> None:
        """Store data in memory."""
        self.client.post(
            "/api/memory/store",
            json={
                "key": f"mem-{random.randint(1, 10000)}",
                "value": f"test-data-{time.time()}",
                "agent_id": self.agent_id,
            },
            headers=self._get_headers(),
            catch_response=True,
        )

    @task(10)
    def query_memory(self) -> None:
        """Query memory for retrieval."""
        self.client.get(
            f"/api/memory/query?agent_id={self.agent_id}",
            headers=self._get_headers(),
            catch_response=True,
        )


class ConsciousnessMetricsUser(HeretekSwarmUser):
    """User that queries consciousness metrics."""
    
    abstract = True

    @task(3)
    def get_consciousness_metrics(self) -> None:
        """Get consciousness metrics for agent."""
        self.client.get(
            f"/api/consciousness/metrics?agent_id={self.agent_id}",
            headers=self._get_headers(),
            catch_response=True,
        )


# ============== EVENT HANDLERS ==============

@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """Called when load test starts."""
    print(f"\n{'=' * 60}")
    print("HERETEK SWARM LOAD TEST")
    print(f"Target: {CONCURRENT_AGENT_TARGET}+ concurrent agents")
    print(f"Latency baseline: <{MESSAGE_LATENCY_BASELINE_MS}ms")
    print(f"Host: {API_HOST}")
    print(f"{'=' * 60}\n")


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """Called when load test stops."""
    print(f"\n{'=' * 60}")
    print("LOAD TEST COMPLETE")
    print(f"{'=' * 60}\n")
    
    # Check if we met the target
    if isinstance(environment.runner, MasterRunner):
        stats = environment.runner.stats
        print(f"Total requests: {stats.total.num_requests}")
        print(f"Total failures: {stats.total.num_failures}")
        print(f"Average response time: {stats.total.avg_response_time:.2f}ms")
        
        if stats.total.avg_response_time > MESSAGE_LATENCY_BASELINE_MS:
            print(f"\n⚠️  WARNING: Average response time exceeds {MESSAGE_LATENCY_BASELINE_MS}ms baseline")
            print("   FLAG FOR REFACTORING per Phase Directives")


# ============== CUSTOM SHAPE ==============

class SwarmLoadTestShape:
    """
    Custom load test shape for realistic agent scaling.
    
    Phases:
    1. Ramp-up: Gradually increase to 1000 users
    2. Sustained: Maintain 1000 users
    3. Spike: Brief spike to 1500 users
    4. Ramp-down: Gradually decrease
    """
    
    def tick(self):
        run_time = self.get_run_time()
        
        if run_time < 60:
            # Ramp up to 1000 users over 1 minute
            return (int(run_time / 60 * 1000), 50)
        elif run_time < 300:
            # Sustained load at 1000 users for 4 minutes
            return (1000, 10)
        elif run_time < 330:
            # Spike to 1500 users for 30 seconds
            return (1500, 100)
        elif run_time < 390:
            # Return to 1000 users
            return (1000, 50)
        else:
            # Ramp down
            remaining = max(0, 1000 - int((run_time - 390) / 30 * 200))
            return (remaining, 50) if remaining > 0 else None