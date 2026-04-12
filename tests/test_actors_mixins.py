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

    async def _emit_pattern(self, pattern_type: str, data: dict) -> None:
        """Mock pattern emission for testing."""
        pass


class MockPatternActor(PatternMixin, MockActor):
    """Mock actor with PatternMixin."""


class MockMemoryActor(MemoryMixin, MockActor):
    """Mock actor with MemoryMixin."""


class MockLearningActor(LearningMixin, MockActor):
    """Mock actor with LearningMixin."""

    def __init__(self, agent_id: str = "test-agent"):
        super().__init__(agent_id)
        self._active_deliberations = {}


class MockAllMixinsActor(
    DeliberationMixin,
    PatternMixin,
    MemoryMixin,
    LearningMixin,
    MockActor,
):
    """Mock actor with all mixins."""


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
        deliberation_id = await actor._initiate_deliberation(
            topic="test",
            options=["a", "b"],
        )
        result = await actor._submit_deliberation_position(
            deliberation_id=deliberation_id,
            position={"vote": "yes"},
            rationale="Because it makes sense",
        )
        # Result is a dict with decision/confidence or None on timeout
        assert result is not False  # Should not fail ID check
        assert actor._deliberation_position is not None

    @pytest.mark.asyncio
    async def test_submit_wrong_deliberation(self):
        """Test submitting to wrong deliberation ID."""
        actor = MockDeliberationActor()
        await actor._initiate_deliberation(topic="test", options=["a"])
        result = await actor._submit_deliberation_position(
            deliberation_id="wrong-id",
            position={"vote": "yes"},
        )
        assert result is False

    @pytest.mark.asyncio
    async def test_finalize_deliberation(self):
        """Test finalizing a deliberation."""
        actor = MockDeliberationActor()
        deliberation_id = await actor._initiate_deliberation(
            topic="test",
            options=["a"],
        )
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
        # _pattern_emitted starts as None (not initialized)
        assert actor._pattern_emitted is None or actor._pattern_emitted == set()

    @pytest.mark.asyncio
    async def test_emit_pattern_no_extractor(self):
        """Test emitting pattern when no extractor present."""
        actor = MockPatternActor()
        # With no pattern_extractor, should return None gracefully
        await actor._emit_pattern(
            item_id="test-1",
            item_type="code",
            outcome="success",
            content={"action": "test"},
        )
        # No error means success in no-op mode

    @pytest.mark.asyncio
    async def test_consume_patterns_no_extractor(self):
        """Test consuming patterns when no extractor present."""
        actor = MockPatternActor()
        patterns = await actor._consume_patterns()
        assert patterns == []


class TestMemoryMixin:
    """Tests for MemoryMixin."""

    def test_init(self):
        """Test mixin initialization."""
        actor = MockMemoryActor()
        assert actor.access_analyzer is None

    @pytest.mark.asyncio
    async def test_track_memory_access_no_analyzer(self):
        """Test tracking memory access when no analyzer present."""
        actor = MockMemoryActor()
        # Should be no-op when no access_analyzer
        actor._track_memory_access("memory-key", "code", "read")
        # No error means success

    def test_get_memory_tier_no_analyzer(self):
        """Test getting memory tier when no analyzer present."""
        actor = MockMemoryActor()
        tier = actor._get_memory_tier("memory-key", "code")
        assert tier == AccessTier.COLD

    @pytest.mark.asyncio
    async def test_prefetch_relevant_no_analyzer(self):
        """Test prefetching when no analyzer present."""
        actor = MockMemoryActor()
        result = await actor._prefetch_relevant(agent_id="test", item_type="code")
        assert result == []


class TestLearningMixin:
    """Tests for LearningMixin."""

    def test_init(self):
        """Test mixin initialization."""
        actor = MockLearningActor()
        assert actor.pattern_extractor is None
        assert actor.deliberation_engine is None
        assert actor.access_analyzer is None

    def test_get_learning_status_no_engines(self):
        """Test getting learning status when no engines present."""
        actor = MockLearningActor()
        # Should return status without errors even with no engines
        status = actor.get_learning_status()
        assert status["agent_id"] == "test-agent"
        assert "collective_learning" in status
        assert "consensus" in status
        assert "memory_optimization" in status

    def test_learning_state_enum(self):
        """Test LearningState enum values."""
        assert LearningState.IDLE.value == "idle"
        assert LearningState.LEARNING.value == "learning"
        assert LearningState.CONVERGED.value == "converged"
        assert LearningState.STAGNANT.value == "stagnant"
        assert LearningState.DIVERGENT.value == "divergent"
        assert LearningState.UNKNOWN.value == "unknown"


class TestAllMixins:
    """Tests for actor with all mixins combined."""

    def test_init(self):
        """Test combined mixins initialize correctly."""
        actor = MockAllMixinsActor()
        assert actor.agent_id == "test-agent"
        assert actor._deliberation_active is False
        assert actor._deliberation_id is None
        assert actor.is_deliberating is False
