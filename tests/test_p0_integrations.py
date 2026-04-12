"""
Unit tests for P0 integrations (NATS, Raft, Langroid)

Tests:
- NATS EventMesh
- Raft Consensus Leader Election
- Langroid Conversations
"""

import pytest

from src.heretek_swarm.actors.langroid_adapter import (
    AgentConversation,
    ConversationState,
    LangroidAgent,
)
from src.heretek_swarm.consensus.raft_election import (
    AppendEntriesRequest,
    RaftElection,
    RequestVoteRequest,
)
from src.heretek_swarm.gateway.nats_event_mesh import (
    ConnectionState,
    NATSEventMesh,
)

# ============== NATS EventMesh Tests ==============

class TestNATSEventMesh:
    """Test NATS EventMesh integration."""

    @pytest.mark.asyncio
    async def test_initialization(self):
        """Test NATSEventMesh initialization."""
        mesh = NATSEventMesh(
            servers=["nats://localhost:4222"],
            fallback=True,
        )

        assert mesh.servers == ["nats://localhost:4222"]
        assert mesh.fallback is True
        assert mesh._state == ConnectionState.DISCONNECTED

    @pytest.mark.asyncio
    async def test_connect_with_fallback(self):
        """Test connection with in-memory fallback."""
        mesh = NATSEventMesh(fallback=True)
        result = await mesh.connect()

        assert result is True
        assert mesh._state == ConnectionState.CONNECTED

    @pytest.mark.asyncio
    async def test_publish_fallback(self):
        """Test publish to fallback mesh."""
        mesh = NATSEventMesh(fallback=True)
        await mesh.connect()

        result = await mesh.publish("test.subject", {"message": "hello"})
        assert result is True

    @pytest.mark.asyncio
    async def test_subscribe_fallback(self):
        """Test subscribe to fallback mesh."""
        mesh = NATSEventMesh(fallback=True)
        await mesh.connect()

        received = []

        async def callback(mesh_obj, subject, data):
            received.append((subject, data))

        sid = await mesh.subscribe("test.>", callback)

        assert sid is not None
        assert mesh.client_count == 1

    @pytest.mark.asyncio
    async def test_disconnect(self):
        """Test disconnect."""
        mesh = NATSEventMesh(fallback=True)
        await mesh.connect()

        await mesh.disconnect()

        assert mesh._state == ConnectionState.DISCONNECTED


# ============== Raft Election Tests ==============

class TestRaftElection:
    """Test Raft consensus leader election."""

    @pytest.mark.asyncio
    async def test_initialization(self):
        """Test RaftElection initialization."""
        raft = RaftElection(
            node_id="node-1",
            peers=["node-2", "node-3"],
        )

        assert raft.node_id == "node-1"
        assert raft.peers == ["node-2", "node-3"]
        assert raft.is_follower
        assert raft.term == 0

    @pytest.mark.asyncio
    async def test_start_stop(self):
        """Test start and stop."""
        raft = RaftElection(node_id="node-1")

        await raft.start()
        assert raft._running

        await raft.stop()
        assert not raft._running

    @pytest.mark.asyncio
    async def test_request_vote(self):
        """Test RequestVote RPC."""
        raft = RaftElection(node_id="node-1")

        request = RequestVoteRequest(
            term=1,
            candidate_id="node-2",
            last_log_index=0,
            last_log_term=0,
        )

        response = await raft.request_vote(request)

        assert response.term == 1
        assert response.vote_granted

    @pytest.mark.asyncio
    async def test_append_entries_heartbeat(self):
        """Test AppendEntries heartbeat."""
        raft = RaftElection(node_id="node-1")

        request = AppendEntriesRequest(
            term=1,
            leader_id="node-2",
            prev_log_index=0,
            prev_log_term=0,
            entries=[],
            leader_commit=0,
        )

        response = await raft.append_entries(request)

        assert response.success is True
        assert raft.leader_id == "node-2"

    @pytest.mark.asyncio
    async def test_status(self):
        """Test status reporting."""
        raft = RaftElection(
            node_id="node-1",
            peers=["node-2"],
        )

        status = raft.get_status()

        assert status["node_id"] == "node-1"
        assert status["state"] == "follower"


# ============== Langroid Adapter Tests ==============

class TestLangroidAgent:
    """Test Langroid adapter."""

    @pytest.mark.asyncio
    async def test_initialization(self):
        """Test LangroidAgent initialization."""
        agent = LangroidAgent(
            agent_id="agent-1",
            name="TestAgent",
        )

        assert agent.agent_id == "agent-1"
        assert agent.name == "TestAgent"

    @pytest.mark.asyncio
    async def test_start_conversation(self):
        """Test start conversation."""
        agent = LangroidAgent(agent_id="agent-1")

        conv_id = await agent.start_conversation("user-1", "Hello")

        assert conv_id.startswith("conv_")

        conv = agent.get_conversation(conv_id)
        assert conv is not None
        assert conv.state == ConversationState.ACTIVE

    @pytest.mark.asyncio
    async def test_send_message(self):
        """Test send message."""
        agent = LangroidAgent(agent_id="agent-1")

        conv_id = await agent.start_conversation("user-1")
        response = await agent.send_message("Test message", conv_id)

        assert response is not None

    @pytest.mark.asyncio
    async def test_end_conversation(self):
        """Test end conversation."""
        agent = LangroidAgent(agent_id="agent-1")

        conv_id = await agent.start_conversation("user-1")
        await agent.end_conversation(conv_id)

        conv = agent.get_conversation(conv_id)
        assert conv.state == ConversationState.COMPLETED


class TestAgentConversation:
    """Test AgentConversation dataclass."""

    def test_initialization(self):
        """Test AgentConversation initialization."""
        conv = AgentConversation(
            conversation_id="conv-1",
            agent_id="agent-1",
        )

        assert conv.conversation_id == "conv-1"
        assert conv.agent_id == "agent-1"
        assert conv.state == ConversationState.IDLE

    def test_add_message(self):
        """Test add message."""
        conv = AgentConversation(
            conversation_id="conv-1",
            agent_id="agent-1",
        )

        conv.add_message("user", "Hello")

        assert len(conv.messages) == 1
        assert conv.messages[0]["role"] == "user"

    def test_get_last_message(self):
        """Test get last message."""
        conv = AgentConversation(
            conversation_id="conv-1",
            agent_id="agent-1",
        )

        conv.add_message("user", "Hello")

        last = conv.get_last_message()

        assert last is not None
        assert last["content"] == "Hello"


# ============== Integration Tests ==============

class TestIntegration:
    """Integration tests."""

    @pytest.mark.asyncio
    async def test_nats_raft_integration(self):
        """Test NATS and Raft working together."""
        mesh = NATSEventMesh(fallback=True)
        await mesh.connect()

        raft = RaftElection(node_id="node-1")
        await raft.start()

        assert mesh.is_connected
        assert raft.is_follower

        await raft.stop()
        await mesh.disconnect()

    @pytest.mark.asyncio
    async def test_all_three_integration(self):
        """Test all three integrations."""
        mesh = NATSEventMesh(fallback=True)
        await mesh.connect()

        raft = RaftElection(node_id="node-1")
        await raft.start()

        agent = LangroidAgent(agent_id="agent-1")

        assert mesh.is_connected
        assert raft.node_id == "node-1"
        assert agent.agent_id == "agent-1"

        await raft.stop()
        await mesh.disconnect()
