"""
M019 S01: Cognitive Observability Surface — Integration Tests

Tests the three wiring changes:
1. Agent message sending wires consciousness_plugin.record_interaction()
2. _consciousness_loop publishes real metrics from registry + plugin
3. Deliberation explain API returns structured why/whyNot/rollback_plan
4. Thinking stream API returns deliberation traces

These are integration tests — no external services required.
"""

import asyncio
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


class AsyncTestCase:
    """Base async test case."""

    @pytest.fixture(autouse=True)
    def setup_event_loop(self):
        """Ensure a fresh event loop per test."""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        yield loop
        loop.close()


class TestConsciousnessInteractionWiring(AsyncTestCase):
    """T01: Agent message sending wires record_interaction()."""

    @pytest.mark.asyncio
    async def test_record_agent_interaction_helper_exists(self):
        """AgentActorMessageHandling has _record_agent_interaction method."""
        from heretek_swarm.actors.base.message_handling import (
            AgentActorMessageHandling,
        )

        assert hasattr(AgentActorMessageHandling, "_record_agent_interaction")

    @pytest.mark.asyncio
    async def test_record_agent_interaction_calls_plugin(self):
        """_record_agent_interaction calls consciousness_plugin.record_interaction."""
        with patch(
            "heretek_swarm.api.consciousness.get_consciousness_plugin"
        ) as mock_get_plugin:
            mock_plugin = MagicMock()
            mock_plugin.record_interaction = MagicMock()
            mock_get_plugin.return_value = mock_plugin

            from heretek_swarm.actors.base.message_handling import (
                AgentActorMessageHandling,
            )

            class TestActor(AgentActorMessageHandling):
                def __init__(self):
                    self.agent_id = "agent-alpha"
                    self.error_count = 0
                    self.internal_state = {}

            actor = TestActor()
            actor._record_agent_interaction("agent-alpha", "agent-beta")

            mock_plugin.record_interaction.assert_called_once_with(
                "agent-alpha", "agent-beta"
            )

    @pytest.mark.asyncio
    async def test_record_agent_interaction_is_non_fatal(self):
        """Plugin failures in _record_agent_interaction do not propagate."""
        with patch(
            "heretek_swarm.api.consciousness.get_consciousness_plugin"
        ) as mock_get_plugin:
            mock_get_plugin.side_effect = RuntimeError("Plugin unavailable")

            from heretek_swarm.actors.base.message_handling import (
                AgentActorMessageHandling,
            )

            class TestActor(AgentActorMessageHandling):
                def __init__(self):
                    self.agent_id = "agent-alpha"
                    self.error_count = 0
                    self.internal_state = {}

            actor = TestActor()
            # Should not raise
            actor._record_agent_interaction("agent-alpha", "agent-beta")


class TestConsciousnessLoopRealData(AsyncTestCase):
    """T02: _consciousness_loop publishes real metrics from plugin + registry."""

    def test_consciousness_loop_patches_exist(self):
        """main_loop imports the consciousness plugin and registry getters."""
        # Verify the imports exist at the module level
        import heretek_swarm.runtime.main_loop as ml

        assert hasattr(ml, "get_consciousness_plugin")
        assert hasattr(ml, "get_enhanced_registry")

    def test_consciousness_loop_references_real_plugin_data(self):
        """_consciousness_loop uses plugin.get_statistics() for phi metric."""
        import inspect

        from heretek_swarm.runtime.main_loop import AutonomousSwarm

        source = inspect.getsource(AutonomousSwarm._consciousness_loop)
        # Verify the loop reads from the consciousness plugin
        assert "plugin.get_statistics()" in source
        assert "phi_metric" in source
        assert "workspace_coherence" in source
        assert "attention_distribution" in source


class TestDeliberationExplainAPI(AsyncTestCase):
    """T03: Deliberation explain API returns structured explanation."""

    @pytest.mark.asyncio
    async def test_get_deliberation_explanation_returns_structured_data(self):
        """get_deliberation_explanation returns why/whyNot/rollback_plan."""
        from heretek_swarm.consensus.deliberation import DeliberationEngine

        engine = DeliberationEngine()

        # Start a deliberation
        deliberation_id = engine.start_deliberation(
            topic="Should we adopt the new policy?",
            participants=["alpha", "beta", "charlie"],
            domain="policy",
        )

        result = engine.get_deliberation_explanation(deliberation_id)

        assert result is not None
        assert result["deliberation_id"] == deliberation_id
        assert result["topic"] == "Should we adopt the new policy?"
        assert result["domain"] == "policy"
        assert "final_position" in result
        assert "consensus_score" in result
        assert "why" in result
        assert "why_not" in result
        assert "rollback_plan" in result
        assert "position_distribution" in result

    @pytest.mark.asyncio
    async def test_get_deliberation_explanation_returns_none_for_unknown_id(self):
        """Unknown deliberation_id returns None."""
        from heretek_swarm.consensus.deliberation import DeliberationEngine

        engine = DeliberationEngine()
        result = engine.get_deliberation_explanation("nonexistent-id")
        assert result is None

    @pytest.mark.asyncio
    async def test_rollback_plan_triggered_below_threshold(self):
        """Weak consensus (< threshold) triggers rollback_plan."""
        from heretek_swarm.consensus.deliberation import DeliberationConfig, DeliberationEngine

        config = DeliberationConfig(consensus_threshold=0.8)
        engine = DeliberationEngine(config=config)

        # Manually add a low-consensus deliberation
        deliberation_id = "test_del_rollback"
        engine.active_deliberations[deliberation_id] = {
            "topic": "test topic",
            "domain": "test",
            "participants": {"a1", "a2"},
            "arguments": [],
            "positions": {},
            "start_time": datetime.now(UTC).isoformat(),
        }
        engine.deliberation_states[deliberation_id] = "completed"
        engine.round_results[deliberation_id] = [
            MagicMock(
                consensus_score=0.3,  # Below threshold
                outcome=MagicMock(value="INCONCLUSIVE"),
            )
        ]

        result = engine.get_deliberation_explanation(deliberation_id)

        assert result is not None
        assert result["rollback_plan"] is not None
        assert "Consensus (0.30)" in result["rollback_plan"]


class TestThinkingStreamAPI(AsyncTestCase):
    """T04: Thinking stream API returns deliberation traces."""

    @pytest.mark.asyncio
    async def test_record_deliberation_round_append_to_stream(self):
        """record_deliberation_round() adds entry to _thinking_stream."""
        from heretek_swarm.plugins.consciousness_enhanced import EnhancedConsciousnessPlugin

        plugin = EnhancedConsciousnessPlugin()

        plugin.record_deliberation_round(
            deliberation_id="del_123",
            round_data={
                "topic": "test topic",
                "participant_agents": ["alpha", "beta"],
                "arguments": [],
                "counter_arguments": [],
                "consensus_score": 0.65,
                "outcome": "FOR",
            },
        )

        assert len(plugin._thinking_stream) == 1
        entry = plugin._thinking_stream[0]
        assert entry["deliberation_id"] == "del_123"
        assert entry["topic"] == "test topic"
        assert entry["consensus_score"] == 0.65
        assert entry["outcome"] == "FOR"

    @pytest.mark.asyncio
    async def test_thinking_stream_bounded_deque(self):
        """Thinking stream bounded to 1000 entries."""
        from heretek_swarm.plugins.consciousness_enhanced import EnhancedConsciousnessPlugin

        plugin = EnhancedConsciousnessPlugin()

        # Add 1005 entries
        for i in range(1005):
            plugin.record_deliberation_round(
                deliberation_id=f"del_{i}",
                round_data={
                    "topic": f"topic {i}",
                    "participant_agents": ["alpha"],
                    "arguments": [],
                    "counter_arguments": [],
                    "consensus_score": 0.5,
                    "outcome": "FOR",
                },
            )

        # Should be bounded to 1000
        assert len(plugin._thinking_stream) == 1000
        # Oldest entries should be dropped
        assert plugin._thinking_stream[0]["deliberation_id"] == "del_5"
