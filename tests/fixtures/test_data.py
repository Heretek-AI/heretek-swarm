"""
Test fixtures and sample data for Heretek Swarm testing.

Agent Gamma - QA and Validation Lead
Provides consistent test data across test suites.
"""

from dataclasses import dataclass, field
from typing import Any
import uuid


# ============== AGENT FIXTURES ==============

@dataclass
class MockAgent:
    """Mock agent for testing."""
    agent_id: str
    agent_type: str
    capabilities: list[str] = field(default_factory=list)
    reputation: float = 1.0
    status: str = "idle"
    
    async def send_message(self, message: dict) -> dict:
        """Mock send message."""
        return {"status": "sent", "message_id": str(uuid.uuid4())}
    
    async def receive_message(self) -> dict:
        """Mock receive message."""
        return {"status": "received"}
    
    async def execute_task(self, task: dict) -> dict:
        """Mock execute task."""
        return {"status": "completed", "result": "success"}
    
    def get_state(self) -> dict:
        """Get agent state."""
        return {
            "agent_id": self.agent_id,
            "status": self.status,
        }


def create_mock_agent(
    agent_id: str | None = None,
    agent_type: str = "worker",
    capabilities: list[str] | None = None,
) -> MockAgent:
    """Create a mock agent with default values."""
    return MockAgent(
        agent_id=agent_id or f"agent-{uuid.uuid4().hex[:8]}",
        agent_type=agent_type,
        capabilities=capabilities or ["task_execution", "messaging"],
    )


# ============== AGENT ROSTER ==============

# 22 agent types from the architecture
AGENT_TYPES = [
    "steward",  # Orchestrator
    "alpha",    # Triad - Leader
    "beta",     # Triad - Critic
    "charlie",  # Triad - Validator
    "historian",
    "oracle",
    "explorer",
    "coder",
    "sentinel",
    "examiner",
    "arbiter",
    "coordinator",
    "catalyst",
    "chronos",
    "dreamer",
    "echo",
    "empath",
    "habit_forge",
    "metis",
    "nexus",
    "perceiver",
    "prism",
]


def create_agent_roster() -> list[MockAgent]:
    """Create a full roster of 22 mock agents."""
    return [
        create_mock_agent(
            agent_id=f"{agent_type}-primary",
            agent_type=agent_type,
            capabilities=_get_capabilities_for_type(agent_type),
        )
        for agent_type in AGENT_TYPES
    ]


def _get_capabilities_for_type(agent_type: str) -> list[str]:
    """Get capabilities for a specific agent type."""
    capability_map = {
        "steward": ["orchestration", "final_authorization", "task_delegation"],
        "alpha": ["deliberation", "consensus", "leadership"],
        "beta": ["critique", "analysis", "consensus"],
        "charlie": ["validation", "arbitration", "consensus"],
        "historian": ["memory", "retrieval", "archival"],
        "oracle": ["prediction", "analysis", "forecasting"],
        "explorer": ["discovery", "search", "mapping"],
        "coder": ["code_generation", "refactoring", "debugging"],
        "sentinel": ["monitoring", "alerting", "security"],
        "examiner": ["review", "audit", "quality"],
        "arbiter": ["resolution", "judgment", "mediation"],
        "coordinator": ["scheduling", "delegation", "coordination"],
        "catalyst": ["acceleration", "optimization", "improvement"],
        "chronos": ["timing", "scheduling", "deadlines"],
        "dreamer": ["ideation", "creativity", "innovation"],
        "echo": ["feedback", "reflection", "iteration"],
        "empath": ["understanding", "sentiment", "communication"],
        "habit_forge": ["routine", "automation", "patterns"],
        "metis": ["wisdom", "strategy", "planning"],
        "nexus": ["connection", "networking", "integration"],
        "perceiver": ["perception", "observation", "awareness"],
        "prism": ["refraction", "analysis", "decomposition"],
    }
    return capability_map.get(agent_type, ["general"])


# ============== MESSAGE FIXTURES ==============

def create_test_message(
    sender_id: str = "sender-1",
    receiver_id: str = "receiver-1",
    message_type: str = "task_request",
    payload: dict | None = None,
) -> dict:
    """Create a test message."""
    return {
        "message_id": f"msg-{uuid.uuid4().hex[:8]}",
        "sender_id": sender_id,
        "receiver_id": receiver_id,
        "message_type": message_type,
        "payload": payload or {"task": "test"},
        "timestamp": 0.0,  # Will be set by system
    }


def create_consensus_message(
    proposal_id: str,
    vote: str,
    reasoning: str = "",
) -> dict:
    """Create a consensus vote message."""
    return {
        "message_id": f"consensus-{uuid.uuid4().hex[:8]}",
        "message_type": "deliberation_vote",
        "payload": {
            "proposal_id": proposal_id,
            "vote": vote,  # approve, reject, abstain
            "reasoning": reasoning,
        },
    }


# ============== TASK FIXTURES ==============

def create_test_task(
    task_type: str = "analysis",
    complexity: str = "medium",
    priority: str = "normal",
) -> dict:
    """Create a test task."""
    return {
        "task_id": f"task-{uuid.uuid4().hex[:8]}",
        "task_type": task_type,
        "complexity": complexity,  # simple, medium, complex
        "priority": priority,  # low, normal, high, critical
        "payload": {"data": "test data"},
    }


# ============== STATE FIXTURES ==============

def create_agent_state(
    agent_id: str,
    status: str = "idle",
) -> dict:
    """Create an agent state snapshot."""
    return {
        "agent_id": agent_id,
        "status": status,
        "current_task": None,
        "memory_context": {},
        "checkpoint_id": f"checkpoint-{uuid.uuid4().hex[:8]}",
    }
