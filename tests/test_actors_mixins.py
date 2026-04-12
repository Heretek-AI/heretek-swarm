"""
Tests for actors/mixins package.

Tests all four mixins:
- DeliberationMixin
- PatternMixin
- MemoryMixin
- LearningMixin

Version: 1.44.0
"""

import pytest

from heretek_swarm.actors.mixins import (
    DeliberationMixin,
    LearningMixin,
    MemoryMixin,
    PatternMixin,
)
from heretek_swarm.actors.mixins.learning import LearningState
from heretek_swarm.actors.mixins.memory import AccessTier


class MockActor:
    """Mock actor for testing mixins."""

    def __init__(self, agent_id: str = "test-agent"):
        self.agent_id = agent_id


class MockDeliberationActor(DeliberationMixin, MockActor):
    """Mock actor with DeliberationMixin."""


class MockPatternActor(PatternMixin, MockActor):
    """Mock actor with PatternMixin."""


class MockMemoryActor(MemoryMixin, MockActor):
    """Mock actor with MemoryMixin."""


class MockLearningActor(LearningMixin, MockActor):
    """Mock actor with LearningMixin."""


class MockAllMixinsActor(
    DeliberationMixin,
    PatternMixin,
    MemoryMixin,
    LearningMixin,
    MockActor,
):
    """Mock actor with all mixins."""


# Import the mixins
from heretek_swarm.actors.mixins import (
    DeliberationMixin,
    LearningMixin,
    MemoryMixin,
    PatternMixin,
)


class TestDeliberationMixin:
    """Tests for DeliberationMixin."""

    def test_init(self):
        """Test mixin initialization."""
        actor = MockDeliberationActor()
        assert actor.agent_id == "test-agent"
        assert actor._deliberation_active is False
        assert actor._deliberation_id is None
        assert actor._deliberation_position is None

    @pytest.mark.asyncio
    async def test_initiate_deliberation(self):
        """Test initiating a deliberation."""
        actor = MockDeliberationActor()
        deliberation_id = await actor._initiate_deliberation(
            topic="test-topic",
            options=["option1", "option2"],
        )
        assert deliberation_id.startswith("delib_")
        assert actor._deliberation_active is True
        assert actor._deliberation_id == deliberation_id

    @pytest.mark.asyncio
    async def test_submit_position(self):
        """Test submitting a deliberation position."""
        actor = MockDeliberationActor()
        deliberation_id = await actor._initiate_deliberation(topic="test")
        result = await actor._submit_deliberation_position(
            deliberation_id=deliberation_id,
            position={"vote": "yes"},
            rationale="Because it makes sense",
        )
        assert result is True
        assert actor._deliberation_position is not None

    @pytest.mark.asyncio
    async def test_submit_wrong_deliberation(self):
        """Test submitting to wrong deliberation ID."""
        actor = MockDeliberationActor()
        await actor._initiate_deliberation(topic="test")
        result = await actor._submit_deliberation_position(
            deliberation_id="wrong-id",
            position={"vote": "yes"},
        )
        assert result is False

    @pytest.mark.asyncio
    async def test_finalize_deliberation(self):
        """Test finalizing a deliberation."""
        actor = MockDeliberationActor()
        deliberation_id = await actor._initiate_deliberation(topic="test")
        await actor._submit_deliberation_position(
            deliberation_id, {"vote": "yes"}
        )
        result = await actor._finalize_deliberation(deliberation_id)
        assert result["success"] is True
        assert actor._deliberation_active is False

    def test_get_deliberation_status(self):
        """Test getting deliberation status."""
        actor = MockDeliberationActor()
        status = actor._get_deliberation_status()
        assert status["active"] is False
        assert status["deliberation_id"] is None

    def test_is_deliberating(self):
        """Test is_deliberating property."""
        actor = MockDeliberationActor()
        assert actor.is_deliberating is False


class TestPatternMixin:
    """Tests for PatternMixin."""

    def test_init(self):
        """Test mixin initialization."""
        actor = MockPatternActor()
        assert actor._emitted_patterns == []
        assert actor._consumed_patterns == {}
        assert actor._pattern_confidence_threshold == 0.7

    @pytest.mark.asyncio
    async def test_emit_pattern(self):
        """Test emitting a pattern."""
        actor = MockPatternActor()
        pattern_id = await actor._emit_pattern(
            pattern_type="success",
            pattern_data={"action": "test"},
            confidence=0.8,
        )
        assert pattern_id.startswith("pattern_")
        assert len(actor._emitted_patterns) == 1

    @pytest.mark.asyncio
    async def test_consume_patterns(self):
        """Test consuming patterns."""
        actor = MockPatternActor()
        patterns = await actor._consume_patterns(min_confidence=0.5)
        assert isinstance(patterns, list)

    def test_get_pattern_confidence(self):
        """Test getting pattern confidence."""
        actor = MockPatternActor()
        confidence = actor._get_pattern_confidence("nonexistent")
        assert confidence == 0.0

    @pytest.mark.asyncio
    async def test_update_pattern_relevance(self):
        """Test updating pattern relevance."""
        actor = MockPatternActor()
        await actor._update_pattern_relevance("test-pattern", 0.1)
        assert "test-pattern" in actor._consumed_patterns

    def test_get_pattern_stats(self):
        """Test getting pattern statistics."""
        actor = MockPatternActor()
        stats = actor._get_pattern_stats()
        assert "emitted_count" in stats
        assert stats["emitted_count"] == 0

    def test_pattern_counts(self):
        """Test pattern count properties."""
        actor = MockPatternActor()
        assert actor.pattern_emission_count == 0
        assert actor.pattern_consumption_count == 0


class TestMemoryMixin:
    """Tests for MemoryMixin."""

    def test_init(self):
        """Test mixin initialization."""
        actor = MockMemoryActor()
        assert actor._memory_access_count == {}
        assert actor._memory_last_access == {}
        assert actor._memory_tier_cache == {}

    @pytest.mark.asyncio
    async def test_track_memory_access(self):
        """Test tracking memory access."""
        actor = MockMemoryActor()
        await actor._track_memory_access("memory-key", "read")
        assert "memory-key" in actor._memory_access_count
        assert actor._memory_access_count["memory-key"] == 1

    @pytest.mark.asyncio
    async def test_get_memory_tier_hot(self):
        """Test HOT tier assignment."""
        actor = MockMemoryActor()
        # Access many times to reach HOT threshold
        for _ in range(15):
            await actor._track_memory_access("hot-key")
        tier = actor._get_memory_tier("hot-key")
        assert tier == AccessTier.HOT

    @pytest.mark.asyncio
    async def test_get_memory_tier_cold(self):
        """Test COLD tier assignment."""
        actor = MockMemoryActor()
        await actor._track_memory_access("cold-key")
        tier = actor._get_memory_tier("cold-key")
        assert tier in [AccessTier.COLD, AccessTier.ARCHIVE]

    @pytest.mark.asyncio
    async def test_prefetch_relevant(self):
        """Test prefetching relevant memories."""
        actor = MockMemoryActor()
        # Add some memories
        for i in range(5):
            await actor._track_memory_access(f"memory-{i}")
            actor._memory_tier_cache[f"memory-{i}"] = AccessTier.HOT

        prefetched = await actor._prefetch_relevant(
            context={"tags": ["test"]},
            limit=3,
        )
        assert len(prefetched) <= 3

    @pytest.mark.asyncio
    async def test_clear_memory_stats(self):
        """Test clearing memory statistics."""
        actor = MockMemoryActor()
        await actor._track_memory_access("test-key")
        actor._clear_memory_stats()
        assert actor._memory_access_count == {}

    def test_get_memory_stats(self):
        """Test getting memory statistics."""
        actor = MockMemoryActor()
        stats = actor._get_memory_stats()
        assert "total_memories_accessed" in stats
        assert stats["total_memories_accessed"] == 0

    def test_memory_access_count(self):
        """Test memory_access_count property."""
        actor = MockMemoryActor()
        assert actor.memory_access_count == 0

    def test_hot_memory_count(self):
        """Test hot_memory_count property."""
        actor = MockMemoryActor()
        assert actor.hot_memory_count == 0


class TestLearningMixin:
    """Tests for LearningMixin."""

    def test_init(self):
        """Test mixin initialization."""
        actor = MockLearningActor()
        assert actor._learning_state == LearningState.IDLE
        assert actor._adaptation_score == 0.5
        assert actor._performance_history == []

    @pytest.mark.asyncio
    async def test_get_learning_status(self):
        """Test getting learning status."""
        actor = MockLearningActor()
        status = await actor.get_learning_status()
        assert status["state"] == "idle"
        assert status["adaptation_score"] == 0.5
        assert status["agent_id"] == "test-agent"

    @pytest.mark.asyncio
    async def test_record_learning_signal(self):
        """Test recording a learning signal."""
        actor = MockLearningActor()
        signal_id = await actor.record_learning_signal(
            signal_type="reward",
            magnitude=0.5,
        )
        assert signal_id.startswith("signal_")
        assert len(actor._learning_signals) == 1

    @pytest.mark.asyncio
    async def test_update_adaptation(self):
        """Test updating adaptation."""
        actor = MockLearningActor()
        result = await actor.update_adaptation(performance_delta=0.2)
        assert "new_score" in result
        assert result["new_score"] != 0.5

    def test_get_performance_trend(self):
        """Test getting performance trend."""
        actor = MockLearningActor()
        trend = actor._get_performance_trend()
        assert trend == "insufficient_data"

    def test_get_convergence_status(self):
        """Test getting convergence status."""
        actor = MockLearningActor()
        status = actor._get_convergence_status()
        assert status == "unknown"

    @pytest.mark.asyncio
    async def test_get_performance_metrics(self):
        """Test getting performance metrics."""
        actor = MockLearningActor()
        metrics = await actor.get_performance_metrics()
        assert "adaptation_score" in metrics
        assert "total_updates" in metrics

    def test_reset_learning(self):
        """Test resetting learning state."""
        actor = MockLearningActor()
        actor._adaptation_score = 0.9
        actor._learning_state = LearningState.CONVERGED
        actor.reset_learning()
        assert actor._learning_state == LearningState.IDLE
        assert actor._adaptation_score == 0.5

    def test_is_converged(self):
        """Test is_converged property."""
        actor = MockLearningActor()
        assert actor.is_converged is False

    def test_is_learning(self):
        """Test is_learning property."""
        actor = MockLearningActor()
        assert actor.is_learning is False


class TestAllMixinsCombined:
    """Tests for actor with all mixins combined."""

    @pytest.mark.asyncio
    async def test_all_mixins_work_together(self):
        """Test all mixins work together on same actor."""
        actor = MockAllMixinsActor(agent_id="combo-agent")

        # Test DeliberationMixin
        await actor._initiate_deliberation(topic="test")
        assert actor.is_deliberating is True

        # Test PatternMixin
        await actor._emit_pattern(
            pattern_type="success",
            pattern_data={"test": "data"},
        )
        assert actor.pattern_emission_count == 1

        # Test MemoryMixin
        await actor._track_memory_access("test-memory")
        assert actor.memory_access_count == 1

        # Test LearningMixin
        await actor.record_learning_signal("reward", 0.5)
        assert actor._total_updates == 1

        # Get combined status
        status = {
            "deliberation": actor._get_deliberation_status(),
            "patterns": actor._get_pattern_stats(),
            "memory": actor._get_memory_stats(),
            "learning": await actor.get_learning_status(),
        }

        assert status["deliberation"]["agent_id"] == "combo-agent"
        assert status["patterns"]["agent_id"] == "combo-agent"
        assert status["memory"]["agent_id"] == "combo-agent"
        assert status["learning"]["agent_id"] == "combo-agent"
