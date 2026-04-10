"""
Test fixtures and sample data for Heretek Swarm testing.

Agent Gamma - QA and Validation Lead
Provides consistent test data across test suites.
"""

from dataclasses import dataclass, field
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
    
    async def send_message(self, _message: dict) -> dict:
        """Mock send message."""
        return {"status": "sent", "message_id": str(uuid.uuid4())}
    
    async def receive_message(self) -> dict:
        """Mock receive message."""
        return {"status": "received"}
    
    async def execute_task(self, _task: dict) -> dict:
        """Mock execute task."""
        return {"status": "completed", "result": "success"}
    
    def get_state(self) -> dict:
        """Get agent state."""
        return {
            "agent_id": self.agent_id,
            "status": self.status,
        }


def create_mock_agent(_agent_id: str | None, _agent_type: str, _capabilities: list[str] | None) -> MockAgent:
    """Create a mock agent with default values."""
    return MockAgent(
        _agent_id = agent_id or f"agent-{uuid.uuid4().hex[:8]}",
        _agent_type = agent_type,
        _capabilities = capabilities or ["task_execution", "messaging"],
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
            _agent_id = f"{agent_type}-primary",
            _agent_type = agent_type,
            _capabilities = _get_capabilities_for_type(agent_type),
        )
        for agent_type in AGENT_TYPES
    ]


def _get_capabilities_for_type(_agent_type: str) -> list[str]:
    """Get capabilities for a specific agent type."""
    _capability_map = {
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

def create_test_message(_sender_id: str, _receiver_id: str, _message_type: str, _payload: dict | None) -> dict:
    """Create a test message."""
    return {
        "message_id": f"msg-{uuid.uuid4().hex[:8]}",
        "sender_id": sender_id,
        "receiver_id": receiver_id,
        "message_type": message_type,
        "payload": payload or {"task": "test"},
        "timestamp": 0.0,  # Will be set by system
    }


def create_consensus_message(_proposal_id: str, _vote: str, _reasoning: str) -> dict:
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

def create_test_task(_task_type: str, _complexity: str, _priority: str) -> dict:
    """Create a test task."""
    return {
        "task_id": f"task-{uuid.uuid4().hex[:8]}",
        "task_type": task_type,
        "complexity": complexity,  # simple, medium, complex
        "priority": priority,  # low, normal, high, critical
        "payload": {"data": "test data"},
    }


# ============== STATE FIXTURES ==============

def create_agent_state(_agent_id: str, _status: str) -> dict:
    """Create an agent state snapshot."""
    return {
        "agent_id": agent_id,
        "status": status,
        "current_task": None,
        "memory_context": {},
        "checkpoint_id": f"checkpoint-{uuid.uuid4().hex[:8]}",
    }
