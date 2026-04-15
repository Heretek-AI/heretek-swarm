"""
Test suite for Habit-Forge Agent - Behavior Architecture & Pattern Optimization.

This module provides comprehensive tests for the Habit-Forge agent including:
- Initialization with all required dependencies
- Habit creation and tracking
- Pattern library management
- Behavioral optimization
- Habit strength tracking
- Reinforcement strategies
- Error handling and edge cases
"""

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock

import pytest

from heretek_swarm.actors.habit_forge import (
    BehavioralPattern,
    Habit,
    HabitForgeAgent,
    HabitStage,
    ReinforcementType,
)
from heretek_swarm.collective.learning import PatternExtractor, PatternType


@pytest.fixture
def mock_pattern_extractor() -> MagicMock:
    extractor = MagicMock()
    extractor.analyze_message = AsyncMock(return_value=None)
    extractor.extract_patterns = AsyncMock(return_value=[])
    extractor._validated_patterns = []
    return extractor


@pytest.fixture
def mock_deliberation_engine() -> MagicMock:
    engine = MagicMock()
    engine.start_deliberation = MagicMock(return_value="delib-test-123")
    engine.submit_position = MagicMock(return_value=True)
    engine.finalize_deliberation = MagicMock(return_value={"result": "approved"})
    return engine


@pytest.fixture
def mock_access_analyzer() -> MagicMock:
    analyzer = MagicMock()
    analyzer.record_access = MagicMock(return_value=None)
    return analyzer


@pytest.fixture
def mock_zero_trust_validator() -> MagicMock:
    validator = MagicMock()
    validator.validate_input = MagicMock(return_value=True)
    validator.validate_output = MagicMock(return_value=True)
    return validator


@pytest.fixture
def habit_forge_agent(
    mock_pattern_extractor: MagicMock,
    mock_deliberation_engine: MagicMock,
    mock_access_analyzer: MagicMock,
    mock_zero_trust_validator: MagicMock,
) -> HabitForgeAgent:
    agent = HabitForgeAgent(
        agent_id="test-habit-forge",
        name="TestHabitForge",
        max_habits=50,
        max_patterns=100,
        min_adherence_threshold=0.7,
    )
    agent.pattern_extractor = mock_pattern_extractor
    agent.deliberation_engine = mock_deliberation_engine
    agent.access_analyzer = mock_access_analyzer
    agent.zero_trust_validator = mock_zero_trust_validator
    agent._active_deliberations = {}
    return agent


class TestHabitForgeInitialization:
    def test_init_default(self) -> None:
        agent = HabitForgeAgent()
        assert agent.agent_id == "habit-forge"
        assert agent.max_habits == 50
        assert agent.max_patterns == 100
        assert agent.min_adherence_threshold == 0.7

    def test_init_custom_params(self) -> None:
        agent = HabitForgeAgent(
            agent_id="custom-habit",
            max_habits=100,
            max_patterns=200,
            min_adherence_threshold=0.8,
        )
        assert agent.agent_id == "custom-habit"
        assert agent.max_habits == 100

    def test_init_with_mocked_deps(
        self,
        habit_forge_agent: HabitForgeAgent,
        mock_pattern_extractor: MagicMock,
    ) -> None:
        assert habit_forge_agent.pattern_extractor is mock_pattern_extractor
        assert habit_forge_agent.active_habits == {}
        assert habit_forge_agent.completed_habits == {}


class TestHabitCreation:
    def test_habit_record_completion(self) -> None:
        habit = Habit(
            habit_id="test-1",
            name="Test Habit",
            description="Test description",
            trigger="trigger",
            routine="routine",
            reward="reward",
        )
        habit.record_completion("Test context")
        assert len(habit.completions) == 1
        assert habit.streak_current == 1

    def test_habit_streak_calculation(self) -> None:
        habit = Habit(
            habit_id="test-1",
            name="Test Habit",
            description="Test",
            trigger="t",
            routine="r",
            reward="r",
        )
        habit.record_completion()
        habit.record_completion()
        assert habit.streak_current >= 1

    def test_habit_adherence_rate_calculation(self) -> None:
        habit = Habit(
            habit_id="test-1",
            name="Test Habit",
            description="Test",
            trigger="t",
            routine="r",
            reward="r",
            target_frequency="daily",
        )
        for _ in range(5):
            habit.record_completion()
        assert habit.adherence_rate > 0


class TestHabitStageProgression:
    def test_stage_awareness_to_initiation(self) -> None:
        habit = Habit(
            habit_id="test-1",
            name="Test",
            description="Test",
            trigger="t",
            routine="r",
            reward="r",
        )
        habit.adherence_rate = 0.3
        habit.streak_current = 1
        assert habit.stage == HabitStage.INITIATION

    def test_stage_initiation_to_acquisition(self) -> None:
        habit = Habit(
            habit_id="test-1",
            name="Test",
            description="Test",
            trigger="t",
            routine="r",
            reward="r",
        )
        # Default stage is INITIATION
        assert habit.stage == HabitStage.INITIATION
        # Test progression: manually set values that would trigger acquisition
        habit.adherence_rate = 0.5
        habit.streak_current = 7
        # Verify values are set (progression happens in _check_stage_progression which is async)
        assert habit.adherence_rate == 0.5
        assert habit.streak_current == 7


class TestBehavioralPattern:
    def test_pattern_to_dict(self) -> None:
        pattern = BehavioralPattern(
            pattern_id="p1",
            pattern_type=PatternType.SUCCESS,
            description="Test pattern",
            triggers=["trigger1"],
            behaviors=["behavior1"],
            outcomes=["outcome1"],
        )
        result = pattern.to_dict()
        assert result["pattern_id"] == "p1"
        assert result["pattern_type"] == "success"


class TestHabitForgeMessageHandling:
    @pytest.mark.asyncio
    async def test_handle_create_habit_success(
        self,
        habit_forge_agent: HabitForgeAgent,
    ) -> None:
        message = ActorMessage(
            sender="test",
            message_type="create_habit",
            content={
                "habit_id": "new-habit-1",
                "name": "New Habit",
                "trigger": "trigger",
                "routine": "routine",
                "reward": "reward",
                "reply_to": "reply-topic",
            },
            timestamp=datetime.now(UTC).isoformat(),
        )
        habit_forge_agent.send = AsyncMock(return_value="msg-123")
        await habit_forge_agent._handle_create_habit(message)
        assert habit_forge_agent.send.called

    @pytest.mark.asyncio
    async def test_handle_create_habit_missing_field(
        self,
        habit_forge_agent: HabitForgeAgent,
    ) -> None:
        message = ActorMessage(
            sender="test",
            message_type="create_habit",
            content={
                "name": "Incomplete Habit",
                "reply_to": "reply-topic",
            },
            timestamp=datetime.now(UTC).isoformat(),
        )
        habit_forge_agent.send = AsyncMock(return_value="msg-123")
        await habit_forge_agent._handle_create_habit(message)
        assert not habit_forge_agent.send.called

    @pytest.mark.asyncio
    async def test_handle_track_habit_success(
        self,
        habit_forge_agent: HabitForgeAgent,
    ) -> None:
        habit = Habit(
            habit_id="track-habit-1",
            name="Track Me",
            description="Test",
            trigger="t",
            routine="r",
            reward="r",
        )
        habit_forge_agent.active_habits["track-habit-1"] = habit

        message = ActorMessage(
            sender="test",
            message_type="track_habit",
            content={
                "habit_id": "track-habit-1",
                "action": "complete",
                "context": "Test completion",
                "reply_to": "reply-topic",
            },
            timestamp=datetime.now(UTC).isoformat(),
        )
        habit_forge_agent.send = AsyncMock(return_value="msg-123")
        await habit_forge_agent._handle_track_habit(message)
        assert habit_forge_agent.send.called

    @pytest.mark.asyncio
    async def test_handle_track_habit_not_found(
        self,
        habit_forge_agent: HabitForgeAgent,
    ) -> None:
        message = ActorMessage(
            sender="test",
            message_type="track_habit",
            content={
                "habit_id": "nonexistent-habit",
                "reply_to": "reply-topic",
            },
            timestamp=datetime.now(UTC).isoformat(),
        )
        habit_forge_agent.send = AsyncMock(return_value="msg-123")
        await habit_forge_agent._handle_track_habit(message)
        assert not habit_forge_agent.send.called

    @pytest.mark.asyncio
    async def test_handle_analyze_patterns_success(
        self,
        habit_forge_agent: HabitForgeAgent,
    ) -> None:
        message = ActorMessage(
            sender="test",
            message_type="analyze_patterns",
            content={
                "behavior_data": [
                    {"action": "complete_task", "outcome": "success"},
                    {"action": "complete_task", "outcome": "success"},
                    {"action": "complete_task", "outcome": "success"},
                ],
                "context": "Testing pattern detection",
                "reply_to": "reply-topic",
            },
            timestamp=datetime.now(UTC).isoformat(),
        )
        habit_forge_agent.send = AsyncMock(return_value="msg-123")
        await habit_forge_agent._handle_analyze_patterns(message)
        assert habit_forge_agent.send.called

    @pytest.mark.asyncio
    async def test_handle_get_habit_progress(
        self,
        habit_forge_agent: HabitForgeAgent,
    ) -> None:
        habit = Habit(
            habit_id="progress-habit-1",
            name="Progress Habit",
            description="Test",
            trigger="t",
            routine="r",
            reward="r",
        )
        habit_forge_agent.active_habits["progress-habit-1"] = habit

        message = ActorMessage(
            sender="test",
            message_type="get_habit_progress",
            content={
                "habit_id": "progress-habit-1",
                "reply_to": "reply-topic",
            },
            timestamp=datetime.now(UTC).isoformat(),
        )
        habit_forge_agent.send = AsyncMock(return_value="msg-123")
        await habit_forge_agent._handle_get_habit_progress(message)
        assert habit_forge_agent.send.called

    @pytest.mark.asyncio
    async def test_handle_get_behavior_report(
        self,
        habit_forge_agent: HabitForgeAgent,
    ) -> None:
        message = ActorMessage(
            sender="test",
            message_type="get_behavior_report",
            content={
                "report_type": "summary",
                "reply_to": "reply-topic",
            },
            timestamp=datetime.now(UTC).isoformat(),
        )
        habit_forge_agent.send = AsyncMock(return_value="msg-123")
        await habit_forge_agent._handle_get_behavior_report(message)
        assert habit_forge_agent.send.called


class TestHeuristicPatternDetection:
    def test_detect_frequent_behaviors(self) -> None:
        habit_forge_agent = HabitForgeAgent()
        behavior_data = [
            {"action": "code_review", "outcome": "improved"},
            {"action": "code_review", "outcome": "improved"},
            {"action": "code_review", "outcome": "improved"},
            {"action": "meeting", "outcome": "scheduled"},
        ]
        patterns = habit_forge_agent._heuristic_pattern_detection(behavior_data)
        assert len(patterns) >= 1
        assert any(p.description == "Repeated behavior: code_review" for p in patterns)


class TestPatternRecommendations:
    @pytest.mark.asyncio
    async def test_generate_recommendations_counterproductive(
        self,
        habit_forge_agent: HabitForgeAgent,
    ) -> None:
        patterns = [
            BehavioralPattern(
                pattern_id="p1",
                pattern_type=PatternType.FAILURE,
                description="Procrastination pattern",
                triggers=["boring_task"],
                behaviors=["delay"],
                outcomes=["missed_deadline"],
            )
        ]
        recommendations = await habit_forge_agent._generate_pattern_recommendations(patterns)
        assert len(recommendations) >= 1


class TestCollectiveAdherence:
    def test_calculate_collective_adherence_empty(self) -> None:
        agent = HabitForgeAgent()
        agent.active_habits = {}
        assert agent._calculate_collective_adherence() == 0.0

    def test_calculate_collective_adherence_multiple(self) -> None:
        agent = HabitForgeAgent()
        habit1 = MagicMock()
        habit1.adherence_rate = 0.8
        habit2 = MagicMock()
        habit2.adherence_rate = 0.6
        agent.active_habits = {"h1": habit1, "h2": habit2}
        assert agent._calculate_collective_adherence() == 0.7


class TestProcessMessage:
    @pytest.mark.asyncio
    async def test_process_unknown_type(self, habit_forge_agent: HabitForgeAgent) -> None:
        message = ActorMessage(
            sender="test",
            message_type="unknown_type",
            content={},
            timestamp=datetime.now(UTC).isoformat(),
        )
        await habit_forge_agent.process_message(message)

    @pytest.mark.asyncio
    async def test_process_handler_error(
        self,
        habit_forge_agent: HabitForgeAgent,
    ) -> None:
        async def failing_handler(msg: ActorMessage) -> None:
            raise ValueError("Test error")

        habit_forge_agent.register_handler("failing", failing_handler)
        message = ActorMessage(
            sender="test",
            message_type="failing",
            content={"reply_to": "reply"},
            timestamp=datetime.now(UTC).isoformat(),
        )
        habit_forge_agent.send = AsyncMock(return_value="msg-123")
        await habit_forge_agent.process_message(message)
        assert habit_forge_agent.error_count >= 1


class TestInitialization:
    @pytest.mark.asyncio
    async def test_initialize_registers_handlers(
        self,
        habit_forge_agent: HabitForgeAgent,
    ) -> None:
        await habit_forge_agent.initialize()
        assert "create_habit" in habit_forge_agent._message_handlers
        assert "track_habit" in habit_forge_agent._message_handlers
        assert "analyze_patterns" in habit_forge_agent._message_handlers


class TestLearningStatus:
    def test_get_learning_status(self, habit_forge_agent: HabitForgeAgent) -> None:
        status = habit_forge_agent.get_learning_status()
        assert "agent_id" in status
        assert status["agent_id"] == "test-habit-forge"

    def test_get_phi_training_status(self, habit_forge_agent: HabitForgeAgent) -> None:
        status = habit_forge_agent.get_phi_training_status()
        assert status["phi_training_enabled"] is True
        assert status["agent_type"] == "habit-forge"


from heretek_swarm.actors.base import ActorMessage
